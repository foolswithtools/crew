#!/usr/bin/env python3
"""
Report archetypes that haven't been invoked in the last N months.

Reads `.crew/usage.log` (raw + aggregate entries) and `catalog.json`.
Archetypes present in the catalog but missing from the log, or whose most
recent invocation is older than the cutoff, are flagged as deadwood
candidates.

Usage:
    python3 scripts/deadwood-report.py
    python3 scripts/deadwood-report.py --months 6
    python3 scripts/deadwood-report.py --json

Exit codes:
    0 — report rendered (even if the deadwood list is empty)
    1 — catalog.json missing; cannot report
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from crew.paths import REPO_ROOT, CATALOG_PATH, USAGE_LOG_PATH as LOG_PATH


def parse_ts(raw: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def last_invoked_per_slug() -> dict[str, dt.datetime]:
    last: dict[str, dt.datetime] = {}
    if not LOG_PATH.exists():
        return last
    with LOG_PATH.open(encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("command") == "aggregate":
                month = entry.get("ts")
                if not isinstance(month, str):
                    continue
                # Use the last day of the month as a pessimistic stand-in.
                try:
                    year, mo = (int(p) for p in month.split("-"))
                    # Pick the first of the following month minus 1 day.
                    if mo == 12:
                        end = dt.datetime(year + 1, 1, 1, tzinfo=dt.timezone.utc) - dt.timedelta(days=1)
                    else:
                        end = dt.datetime(year, mo + 1, 1, tzinfo=dt.timezone.utc) - dt.timedelta(days=1)
                except ValueError:
                    continue
                for slug in (entry.get("counts") or {}).keys():
                    if slug not in last or end > last[slug]:
                        last[slug] = end
                continue
            ts = parse_ts(entry.get("ts", ""))
            if ts is None:
                continue
            for slug in entry.get("archetypes", []):
                if not isinstance(slug, str):
                    continue
                if slug not in last or ts > last[slug]:
                    last[slug] = ts
    return last


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--months", type=int, default=6, help="cutoff in months (default: 6)")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of markdown")
    args = parser.parse_args(argv[1:])

    if not CATALOG_PATH.exists():
        print("deadwood-report: catalog.json missing — run `python3 scripts/build-index.py` first", file=sys.stderr)
        return 1

    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    now = dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(days=args.months * 30)

    last_seen = last_invoked_per_slug()

    never_invoked: list[dict] = []
    stale: list[dict] = []
    for entry in catalog:
        slug = entry["name"]
        display = entry["display_name"]
        ts = last_seen.get(slug)
        if ts is None:
            never_invoked.append({"slug": slug, "display_name": display})
        elif ts < cutoff:
            stale.append({
                "slug": slug,
                "display_name": display,
                "last_invoked": ts.isoformat(timespec="seconds").replace("+00:00", "Z"),
                "days_since": (now - ts).days,
            })

    never_invoked.sort(key=lambda e: e["display_name"])
    stale.sort(key=lambda e: e["days_since"], reverse=True)

    payload = {
        "generated_at": now.isoformat(timespec="seconds").replace("+00:00", "Z"),
        "cutoff_months": args.months,
        "never_invoked": never_invoked,
        "stale": stale,
    }

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    print(f"# Deadwood report — {args.months}-month cutoff")
    print()
    print(f"_Generated {payload['generated_at']} from `.crew/usage.log` + `catalog.json`._")
    print()
    print(f"**Never invoked ({len(never_invoked)}):**")
    if not never_invoked:
        print("- _(none — every archetype has been used at least once)_")
    else:
        for e in never_invoked:
            print(f"- **{e['display_name']}** (`{e['slug']}`)")
    print()
    print(f"**Stale — not invoked in ≥ {args.months} months ({len(stale)}):**")
    if not stale:
        print("- _(none)_")
    else:
        for e in stale:
            print(f"- **{e['display_name']}** (`{e['slug']}`) — last invoked {e['last_invoked']} ({e['days_since']} days ago)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
