#!/usr/bin/env python3
"""
Maintain `.crew/usage.log` — the append-only JSONL record of crew invocations.

Subcommands:
    append '<json>'  — append one JSON object as a line. Called from the slash
                       commands at the end of an invocation.
    compact          — roll up entries older than 90 days into monthly-aggregate
                       lines (one per month). Idempotent: running twice produces
                       the same file.
    signals          — derive `.crew/signals.json` (counts, last-invoked,
                       trending, new-this-month). Read by build-index.py.

Schema for raw entries (one JSON object per line):
    {
      "ts": "2026-04-18T14:22:00Z",
      "command": "crew-seek|crew-draft|crew-review|crew-review-archetype|crew-audit",
      "archetypes": ["slug-a", "slug-b"],
      "problem_hash": "<sha256-first-16>" | null,
      "saved_slug": "<slug>" | null,
      "flagged_bad_fit": ["slug-x"]
    }

Schema for aggregate entries (produced by compact):
    {
      "ts": "2026-01",
      "command": "aggregate",
      "counts": {"slug": N, ...},
      "pairs":  {"slug-a|slug-b": N, ...}
    }

Layer 2 artifact. Always regenerable-adjacent: raw entries are the source of
truth, signals.json is derived. Missing log file = empty-world, not an error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import Counter
from itertools import combinations
from pathlib import Path

from crew.paths import (
    REPO_ROOT,
    CREW_DIR,
    USAGE_LOG_PATH as LOG_PATH,
    SIGNALS_PATH,
)

COMPACT_CUTOFF_DAYS = 90
TRENDING_WINDOW_DAYS = 30
TRENDING_TOP_N = 5

VALID_COMMANDS = {
    "crew-seek",
    "crew-draft",
    "crew-review",
    "crew-review-archetype",
    "crew-audit",
}


def ensure_dir() -> None:
    CREW_DIR.mkdir(parents=True, exist_ok=True)


def read_entries() -> list[dict]:
    if not LOG_PATH.exists():
        return []
    entries: list[dict] = []
    with LOG_PATH.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"usage-log: malformed line {n} (skipping): {e}", file=sys.stderr)
    return entries


def parse_ts(raw: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def append(raw_json: str) -> int:
    try:
        entry = json.loads(raw_json)
    except json.JSONDecodeError as e:
        print(f"usage-log append: invalid JSON: {e}", file=sys.stderr)
        return 1
    if not isinstance(entry, dict):
        print("usage-log append: entry must be a JSON object", file=sys.stderr)
        return 1
    if "ts" not in entry:
        entry["ts"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    cmd = entry.get("command")
    if cmd not in VALID_COMMANDS:
        print(f"usage-log append: unknown command {cmd!r} (allowed: {sorted(VALID_COMMANDS)})", file=sys.stderr)
        return 1
    if not isinstance(entry.get("archetypes"), list):
        entry["archetypes"] = []
    ensure_dir()
    line = json.dumps(entry, sort_keys=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
    return 0


def compact() -> int:
    entries = read_entries()
    if not entries:
        return 0
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=COMPACT_CUTOFF_DAYS)

    raw_recent: list[dict] = []
    aggregates: dict[str, dict] = {}  # month_key -> {"counts": Counter, "pairs": Counter}

    for entry in entries:
        if entry.get("command") == "aggregate":
            month = entry.get("ts")
            if not isinstance(month, str):
                continue
            slot = aggregates.setdefault(month, {"counts": Counter(), "pairs": Counter()})
            for slug, n in (entry.get("counts") or {}).items():
                slot["counts"][slug] += int(n)
            for pair, n in (entry.get("pairs") or {}).items():
                slot["pairs"][pair] += int(n)
            continue

        ts = parse_ts(entry.get("ts", ""))
        if ts is None:
            raw_recent.append(entry)
            continue
        if ts >= cutoff:
            raw_recent.append(entry)
            continue
        month = ts.strftime("%Y-%m")
        slot = aggregates.setdefault(month, {"counts": Counter(), "pairs": Counter()})
        slugs = [s for s in entry.get("archetypes", []) if isinstance(s, str)]
        for slug in slugs:
            slot["counts"][slug] += 1
        for a, b in combinations(sorted(set(slugs)), 2):
            slot["pairs"][f"{a}|{b}"] += 1

    # Re-render deterministically: aggregates first (sorted by month), then raw
    # entries in chronological order.
    lines: list[str] = []
    for month in sorted(aggregates.keys()):
        slot = aggregates[month]
        agg = {
            "ts": month,
            "command": "aggregate",
            "counts": dict(sorted(slot["counts"].items())),
            "pairs": dict(sorted(slot["pairs"].items())),
        }
        lines.append(json.dumps(agg, sort_keys=True))

    raw_recent.sort(key=lambda e: e.get("ts", ""))
    for entry in raw_recent:
        lines.append(json.dumps(entry, sort_keys=True))

    new_text = "\n".join(lines) + ("\n" if lines else "")
    old_text = LOG_PATH.read_text(encoding="utf-8") if LOG_PATH.exists() else ""

    if new_text == old_text:
        print(f"usage-log compact: no changes ({len(raw_recent)} raw, {len(aggregates)} aggregate)")
        return 0

    ensure_dir()
    LOG_PATH.write_text(new_text, encoding="utf-8")
    print(f"usage-log compact: {len(raw_recent)} raw entr(ies), {len(aggregates)} monthly aggregate(s)")
    return 0


def signals() -> int:
    entries = read_entries()
    now = dt.datetime.now(dt.timezone.utc)
    window_start = now - dt.timedelta(days=TRENDING_WINDOW_DAYS)

    by_slug: dict[str, dict] = {}
    recent_counts: Counter = Counter()

    for entry in entries:
        if entry.get("command") == "aggregate":
            for slug, n in (entry.get("counts") or {}).items():
                slot = by_slug.setdefault(slug, {"invocations": 0, "last_invoked": None, "first_seen": None})
                slot["invocations"] += int(n)
                # Aggregate entries are older than TRENDING_WINDOW_DAYS by construction,
                # so they don't contribute to trending. But they do set first_seen.
                month = entry.get("ts")
                if isinstance(month, str):
                    if slot["first_seen"] is None or month < slot["first_seen"]:
                        slot["first_seen"] = month
            continue
        ts_raw = entry.get("ts", "")
        ts = parse_ts(ts_raw)
        slugs = [s for s in entry.get("archetypes", []) if isinstance(s, str)]
        for slug in slugs:
            slot = by_slug.setdefault(slug, {"invocations": 0, "last_invoked": None, "first_seen": None})
            slot["invocations"] += 1
            if ts_raw and (slot["last_invoked"] is None or ts_raw > slot["last_invoked"]):
                slot["last_invoked"] = ts_raw
            if ts_raw and (slot["first_seen"] is None or ts_raw < slot["first_seen"]):
                slot["first_seen"] = ts_raw
            if ts is not None and ts >= window_start:
                recent_counts[slug] += 1

    trending = [slug for slug, _ in recent_counts.most_common(TRENDING_TOP_N)]

    # new_this_month = archetypes whose persona file was added this month.
    # Use git log --follow to find the first commit per file; fall back to mtime.
    new_this_month: list[str] = []
    personas_dir = REPO_ROOT / "personas"
    current_month = now.strftime("%Y-%m")
    if personas_dir.exists():
        for path in sorted(personas_dir.glob("*.md")):
            slug = path.stem
            try:
                added = _first_commit_month(path)
            except Exception:
                added = None
            if added is None:
                added = dt.datetime.fromtimestamp(path.stat().st_mtime, tz=dt.timezone.utc).strftime("%Y-%m")
            if added == current_month:
                new_this_month.append(slug)

    payload = {
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "by_slug": dict(sorted(by_slug.items())),
        "trending": trending,
        "new_this_month": sorted(new_this_month),
    }

    ensure_dir()
    new_text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    SIGNALS_PATH.write_text(new_text, encoding="utf-8")
    print(
        f"usage-log signals: {len(by_slug)} slug(s) seen, "
        f"trending={len(trending)}, new_this_month={len(new_this_month)}"
    )
    return 0


def _first_commit_month(path: Path) -> str | None:
    """First-commit YYYY-MM for a file, via `git log --follow --diff-filter=A`."""
    import subprocess
    result = subprocess.run(
        ["git", "log", "--follow", "--diff-filter=A", "--format=%cI", "--", str(path)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    if result.returncode != 0:
        return None
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not lines:
        return None
    # --diff-filter=A gives the add commit; take the last one (oldest).
    added_iso = lines[-1]
    ts = parse_ts(added_iso)
    if ts is None:
        return None
    return ts.strftime("%Y-%m")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_append = sub.add_parser("append", help="append one JSONL line to .crew/usage.log")
    p_append.add_argument("json_blob", help="JSON object to append (one line)")

    sub.add_parser("compact", help="roll entries older than 90 days into monthly aggregates")
    sub.add_parser("signals", help="derive .crew/signals.json from the log")

    args = parser.parse_args(argv[1:])

    if args.cmd == "append":
        return append(args.json_blob)
    if args.cmd == "compact":
        return compact()
    if args.cmd == "signals":
        return signals()
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
