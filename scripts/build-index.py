#!/usr/bin/env python3
"""
Compile `personas/*.md` into two build artifacts:

    catalog.json — machine manifest (frontmatter + path + content hash)
    INDEX.md     — human browse, grouped by facet

Both are deterministic and diffable. Running this script twice back-to-back
produces byte-identical output (idempotency gate).

Usage:
    python3 scripts/build-index.py         # build both artifacts
    python3 scripts/build-index.py --check # rebuild and fail if bytes drift

Exit codes:
    0 — build succeeded (and, in --check mode, output was stable)
    1 — malformed archetype file, or (in --check mode) output drifted
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import REPO_ROOT, PERSONAS_DIR, VOCAB_DIR, split_frontmatter  # noqa: E402

CATALOG_PATH = REPO_ROOT / "catalog.json"
INDEX_PATH = REPO_ROOT / "INDEX.md"
SIGNALS_PATH = REPO_ROOT / ".crew" / "signals.json"

FACETS = ("expertise", "function", "approach")
FACET_HEADINGS = {
    "expertise": "Expertise",
    "function": "Function",
    "approach": "Approach",
}


def load_vocab_ordered(facet: str) -> list[tuple[str, dict]]:
    """Return (tag_slug, tag_dict) pairs in the order they appear in the YAML."""
    path = VOCAB_DIR / f"{facet}.yml"
    with path.open() as f:
        data = yaml.safe_load(f) or {}
    tags = data.get("tags") or {}
    return list(tags.items())


def content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_archetypes() -> list[dict]:
    archetypes: list[dict] = []
    for path in sorted(PERSONAS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, _body, findings = split_frontmatter(text, path)
        if meta is None:
            errs = "; ".join(f.message for f in findings)
            raise SystemExit(f"build failed: {path.relative_to(REPO_ROOT)} — {errs}")
        for field in ("name", "display_name", "exemplars", "expertise", "function", "approach", "reviewed"):
            if field not in meta:
                raise SystemExit(f"build failed: {path.relative_to(REPO_ROOT)} missing `{field}`")
        archetypes.append({
            "name": meta["name"],
            "display_name": meta["display_name"],
            "path": str(path.relative_to(REPO_ROOT)),
            "exemplars": list(meta["exemplars"]),
            "expertise": list(meta["expertise"]),
            "function": list(meta["function"]),
            "approach": list(meta["approach"]),
            "reviewed": bool(meta["reviewed"]),
            "content_hash": content_hash(path),
        })
    archetypes.sort(key=lambda a: a["name"])
    return archetypes


def render_catalog(archetypes: list[dict]) -> str:
    return json.dumps(archetypes, indent=2, sort_keys=True) + "\n"


def load_signals() -> dict:
    """Read `.crew/signals.json` if present; return {} on any failure."""
    if not SIGNALS_PATH.exists():
        return {}
    try:
        return json.loads(SIGNALS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def render_index(archetypes: list[dict]) -> str:
    by_name = {a["name"]: a for a in archetypes}
    lines: list[str] = []
    lines.append("# Catalog Index")
    lines.append("")
    lines.append(f"_Auto-generated from `personas/*.md` by `scripts/build-index.py`. Do not edit — this file is a build artifact._")
    lines.append("")
    lines.append(f"**{len(archetypes)} archetype(s)** across {len(FACETS)} facets.")
    lines.append("")

    signals = load_signals()
    trending = [s for s in (signals.get("trending") or []) if s in by_name]
    new_this_month = [s for s in (signals.get("new_this_month") or []) if s in by_name]
    by_slug_signals = signals.get("by_slug") or {}
    if trending or new_this_month:
        lines.append("## Signals")
        lines.append("")
        lines.append("_Derived from `.crew/usage.log` by `scripts/usage-log.py signals`. Missing = no invocations recorded yet._")
        lines.append("")
        if trending:
            lines.append("**Trending (30-day invocation count, top 5):**")
            for slug in trending:
                a = by_name[slug]
                count = (by_slug_signals.get(slug) or {}).get("invocations", "?")
                lines.append(f"- [{a['display_name']}]({a['path']}) — {count} invocation(s)")
            lines.append("")
        if new_this_month:
            lines.append("**New this month:**")
            for slug in sorted(new_this_month):
                a = by_name[slug]
                lines.append(f"- [{a['display_name']}]({a['path']})")
            lines.append("")

    for facet in FACETS:
        lines.append(f"## {FACET_HEADINGS[facet]}")
        lines.append("")
        vocab_entries = load_vocab_ordered(facet)
        for tag_slug, tag_meta in vocab_entries:
            label = tag_meta.get("label", tag_slug) if isinstance(tag_meta, dict) else tag_slug
            matching = [a for a in archetypes if tag_slug in a.get(facet, [])]
            matching.sort(key=lambda a: a["display_name"])
            lines.append(f"### {label} (`{tag_slug}`)")
            lines.append("")
            if not matching:
                lines.append("_(no archetypes yet)_")
                lines.append("")
                continue
            for a in matching:
                exemplars = ", ".join(a["exemplars"])
                lines.append(f"- [{a['display_name']}]({a['path']}) — exemplars: {exemplars}")
            lines.append("")

    unreviewed = [a for a in archetypes if not a["reviewed"]]
    unreviewed.sort(key=lambda a: a["display_name"])
    lines.append("## Unreviewed archetypes")
    lines.append("")
    lines.append("_Archetypes with `reviewed: false` — candidates for `/crew-review-archetype`._")
    lines.append("")
    if not unreviewed:
        lines.append("_(none — catalog fully reviewed)_")
    else:
        for a in unreviewed:
            lines.append(f"- [{a['display_name']}]({a['path']})")
    lines.append("")

    _ = by_name
    return "\n".join(lines).rstrip() + "\n"


def write_if_changed(path: Path, content: str) -> bool:
    existing = path.read_text(encoding="utf-8") if path.exists() else None
    if existing == content:
        return False
    path.write_text(content, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    check_mode = "--check" in argv[1:]

    archetypes = load_archetypes()
    catalog_text = render_catalog(archetypes)
    index_text = render_index(archetypes)

    if check_mode:
        current_catalog = CATALOG_PATH.read_text(encoding="utf-8") if CATALOG_PATH.exists() else ""
        current_index = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
        drifted = False
        if current_catalog != catalog_text:
            print(f"DRIFT  catalog.json  {len(current_catalog)} -> {len(catalog_text)} bytes", file=sys.stderr)
            drifted = True
        if current_index != index_text:
            print(f"DRIFT  INDEX.md      {len(current_index)} -> {len(index_text)} bytes", file=sys.stderr)
            drifted = True
        if drifted:
            return 1
        print(f"check ok — {len(archetypes)} archetype(s), no drift")
        return 0

    catalog_changed = write_if_changed(CATALOG_PATH, catalog_text)
    index_changed = write_if_changed(INDEX_PATH, index_text)

    print(f"built {len(archetypes)} archetype(s) — "
          f"catalog.json {'updated' if catalog_changed else 'unchanged'}, "
          f"INDEX.md {'updated' if index_changed else 'unchanged'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
