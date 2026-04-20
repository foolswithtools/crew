#!/usr/bin/env python3
"""
Compile the relationship graph between archetypes into `graph.json`.

Edge types:
    contrasts              — directed. Parsed from each persona's
                             `## Not to be confused with` section. Each bullet
                             `- **<Display Name>** — <reason>` becomes an edge
                             from the file's archetype to the named one.
    shares_exemplar        — undirected. Any pair of archetypes that share
                             ≥ 1 exemplar (case-normalised) get one edge.
    frequently_paired_with — undirected. Derived from `.crew/usage.log`: any
                             pair of archetype slugs that co-occur in the
                             same usage entry (or same monthly aggregate)
                             at least PAIR_THRESHOLD times. Missing log =
                             empty list, no error.

Usage:
    python3 scripts/build-graph.py
    python3 scripts/build-graph.py --check

`--check` rebuilds in memory and exits non-zero if the bytes on disk would
change — the same idempotency contract as build-index.py.

Output is gitignored. Always regenerable from personas/*.md.
"""

from __future__ import annotations

import datetime
import json
import re
import sys
from itertools import combinations
from pathlib import Path

from wrecking_crew.paths import REPO_ROOT, PERSONAS_DIR, GRAPH_PATH, USAGE_LOG_PATH
from wrecking_crew.validate import split_frontmatter
NOT_CONFUSED_HEADING = "## Not to be confused with"
PAIR_THRESHOLD = 2  # low threshold early; tune once the log has real volume

# - **Display Name** — reason text (em-dash or double-hyphen tolerated)
BULLET_RE = re.compile(
    r"^\s*-\s+\*\*(?P<name>.+?)\*\*\s*[—–\-]{1,2}\s*(?P<reason>.+?)\s*$",
    re.DOTALL,
)


def find_section(body: str, heading: str) -> str | None:
    """Return the body of a `## Heading` section (up to the next `## ` or EOF)."""
    idx = body.find(heading)
    if idx == -1:
        return None
    start = idx + len(heading)
    rest = body[start:]
    next_h = re.search(r"\n## ", rest)
    section = rest[: next_h.start()] if next_h else rest
    return section.strip()


def split_bullets(section: str) -> list[str]:
    """Split a section into one entry per `- ` bullet, preserving wraps."""
    lines = section.splitlines()
    bullets: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if re.match(r"^\s*-\s+", line):
            if current is not None:
                bullets.append(current)
            current = [line]
        elif current is not None and line.strip():
            current.append(line)
        elif current is not None:
            bullets.append(current)
            current = None
    if current is not None:
        bullets.append(current)
    return [" ".join(parts).strip() for parts in bullets]


def parse_archetype(path: Path) -> tuple[str | None, str | None, list[tuple[str, str]]]:
    """Return (slug, display_name, [(bold_name, reason), ...]) for one persona."""
    text = path.read_text(encoding="utf-8")
    meta, body, _ = split_frontmatter(text, path)
    if meta is None:
        return None, None, []
    slug = meta.get("name") if isinstance(meta.get("name"), str) else None
    display = meta.get("display_name") if isinstance(meta.get("display_name"), str) else None
    section = find_section(body, NOT_CONFUSED_HEADING)
    if section is None:
        return slug, display, []
    edges: list[tuple[str, str]] = []
    for bullet in split_bullets(section):
        m = BULLET_RE.match(bullet)
        if not m:
            continue
        name = m.group("name").strip()
        reason = re.sub(r"\s+", " ", m.group("reason").strip())
        edges.append((name, reason))
    return slug, display, edges


def build_graph() -> tuple[dict, list[str]]:
    warnings: list[str] = []
    archetypes: list[dict] = []
    raw_contrasts: list[tuple[str, str, str]] = []  # (from_slug, bold_name, reason)
    exemplars_by_slug: dict[str, set[str]] = {}

    for path in sorted(PERSONAS_DIR.glob("*.md")):
        slug, display, bullets = parse_archetype(path)
        if not slug or not display:
            warnings.append(f"{path.relative_to(REPO_ROOT)}: missing name/display_name")
            continue
        archetypes.append({"slug": slug, "display_name": display})
        for name, reason in bullets:
            raw_contrasts.append((slug, name, reason))
        # Collect exemplars for shares_exemplar
        text = path.read_text(encoding="utf-8")
        meta, _body, _ = split_frontmatter(text, path)
        if meta and isinstance(meta.get("exemplars"), list):
            normalized = {
                e.strip().lower()
                for e in meta["exemplars"]
                if isinstance(e, str)
            }
            if normalized:
                exemplars_by_slug[slug] = normalized

    display_to_slug = {a["display_name"]: a["slug"] for a in archetypes}

    contrasts: list[dict] = []
    for from_slug, bold_name, reason in raw_contrasts:
        to_slug = display_to_slug.get(bold_name)
        if to_slug is None:
            warnings.append(
                f"{from_slug}: 'Not to be confused with' references unknown archetype '{bold_name}'"
            )
            continue
        contrasts.append({"from": from_slug, "to": to_slug, "reason": reason})

    # Deterministic order: sort edges so the output is diffable.
    contrasts.sort(key=lambda e: (e["from"], e["to"]))

    shares_exemplar: list[dict] = []
    slugs = sorted(exemplars_by_slug.keys())
    for a, b in combinations(slugs, 2):
        common = exemplars_by_slug[a] & exemplars_by_slug[b]
        if common:
            shares_exemplar.append({
                "archetypes": [a, b],
                "exemplars": sorted(common),
            })
    shares_exemplar.sort(key=lambda e: tuple(e["archetypes"]))

    known_slugs = {a["slug"] for a in archetypes}
    pair_counts = count_pair_cooccurrences(known_slugs)
    frequently_paired_with: list[dict] = []
    for (a, b), count in sorted(pair_counts.items()):
        if count < PAIR_THRESHOLD:
            continue
        frequently_paired_with.append({
            "archetypes": [a, b],
            "count": count,
        })

    archetypes.sort(key=lambda a: a["slug"])
    graph = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "nodes": archetypes,
        "edges": {
            "contrasts": contrasts,
            "shares_exemplar": shares_exemplar,
            "frequently_paired_with": frequently_paired_with,
        },
    }
    return graph, warnings


def count_pair_cooccurrences(known_slugs: set[str]) -> dict[tuple[str, str], int]:
    """Parse `.crew/usage.log` and count pair co-occurrences per entry.

    Raw entries contribute +1 per pair of slugs present. Aggregate entries
    (produced by `scripts/usage-log.py compact`) carry a `pairs` map with
    pre-counted pairs; those counts are added verbatim. Pairs involving
    slugs not in the current catalog are dropped silently (archetypes may
    have been renamed or removed).
    """
    pairs: dict[tuple[str, str], int] = {}
    if not USAGE_LOG_PATH.exists():
        return pairs
    with USAGE_LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("command") == "aggregate":
                for pair_str, n in (entry.get("pairs") or {}).items():
                    if "|" not in pair_str:
                        continue
                    a, b = pair_str.split("|", 1)
                    if a not in known_slugs or b not in known_slugs:
                        continue
                    key = tuple(sorted((a, b)))
                    pairs[key] = pairs.get(key, 0) + int(n)
                continue
            slugs = [
                s for s in (entry.get("archetypes") or [])
                if isinstance(s, str) and s in known_slugs
            ]
            for a, b in combinations(sorted(set(slugs)), 2):
                key = (a, b)
                pairs[key] = pairs.get(key, 0) + 1
    return pairs


def render(graph: dict) -> str:
    # Strip generated_at from the idempotency comparison by making it part
    # of the payload but deterministic — use UTC date only for --check sanity.
    # Simpler: include the timestamp, accept that it differs run-to-run, and
    # compare the rest via a canonical form in --check.
    return json.dumps(graph, indent=2, sort_keys=True) + "\n"


def stable_shape(graph: dict) -> dict:
    """Return the graph with `generated_at` removed for idempotency checks."""
    copy = {k: v for k, v in graph.items() if k != "generated_at"}
    return copy


def main(argv: list[str]) -> int:
    check = "--check" in argv[1:]
    graph, warnings = build_graph()

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)

    new_text = render(graph)

    if check:
        if not GRAPH_PATH.exists():
            print("DRIFT  graph.json  missing on disk", file=sys.stderr)
            return 1
        try:
            current = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"DRIFT  graph.json  existing file is not valid JSON: {e}", file=sys.stderr)
            return 1
        if stable_shape(current) != stable_shape(graph):
            print("DRIFT  graph.json  content would change", file=sys.stderr)
            return 1
        print(f"check ok — {len(graph['nodes'])} node(s), "
              f"{len(graph['edges']['contrasts'])} contrast edge(s), "
              f"{len(graph['edges']['shares_exemplar'])} shared-exemplar edge(s), "
              f"{len(graph['edges']['frequently_paired_with'])} pair edge(s)")
        return 0

    existing_shape = None
    if GRAPH_PATH.exists():
        try:
            existing_shape = stable_shape(json.loads(GRAPH_PATH.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            existing_shape = None
    new_shape = stable_shape(graph)

    changed = existing_shape != new_shape
    if changed or not GRAPH_PATH.exists():
        GRAPH_PATH.write_text(new_text, encoding="utf-8")

    print(
        f"built graph — {len(graph['nodes'])} node(s), "
        f"{len(graph['edges']['contrasts'])} contrast edge(s), "
        f"{len(graph['edges']['shares_exemplar'])} shared-exemplar edge(s), "
        f"{len(graph['edges']['frequently_paired_with'])} pair edge(s) — "
        f"graph.json {'updated' if changed or not existing_shape else 'unchanged'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
