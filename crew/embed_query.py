#!/usr/bin/env python3
"""
Rank archetypes by semantic similarity to a problem description or to
an existing archetype's stored vector.

Usage:
    echo "my problem description" | python3 scripts/embed-query.py
    python3 scripts/embed-query.py --top 5
    python3 scripts/embed-query.py --slug rigorous-quant-ml-researcher

Emits JSON to stdout:

    {
      "query_preview": "first 120 chars…",
      "mode": "prose" | "slug",
      "ranked": [
        {"slug": "...", "display_name": "...", "cosine": 0.xx},
        ...
      ],
      "embeddings_enabled": true
    }

In `--slug` mode, the target archetype is excluded from the output and
its stored vector is looked up in `embeddings.sqlite` (no model load).

If the embedding deps aren't importable or the index is missing, the
script emits a minimal JSON result with `embeddings_enabled: false` and
exits 0. Callers (notably `/crew` and `/crew-related`) are expected to
treat this as an optional pre-filter and fall back to reading files.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crew.paths import REPO_ROOT, EMBEDDINGS_DB as DB_PATH
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def disabled_result(mode: str, query_preview: str, reason: str) -> dict:
    return {
        "query_preview": query_preview,
        "mode": mode,
        "ranked": [],
        "embeddings_enabled": False,
        "disabled_reason": reason,
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Rank archetypes by cosine similarity.")
    p.add_argument("--slug", help="Rank against an existing archetype's stored vector")
    p.add_argument("--top", type=int, default=20, help="Max number of matches to return (default 20)")
    p.add_argument("text", nargs="?", help="Problem text; omit to read from stdin (use '-' for stdin explicitly)")
    return p.parse_args()


def read_prose(args) -> str:
    if args.text and args.text != "-":
        return args.text
    data = sys.stdin.read()
    return data


def main() -> int:
    args = parse_args()

    if args.slug:
        query_preview = f"<slug:{args.slug}>"
        mode = "slug"
    else:
        prose = read_prose(args).strip()
        if not prose:
            print("no query text provided (stdin empty and no text arg)", file=sys.stderr)
            return 1
        query_preview = prose[:120].replace("\n", " ")
        mode = "prose"

    try:
        import numpy as np
        import sqlite_vec
    except ImportError as e:
        name = getattr(e, "name", str(e))
        print(json.dumps(disabled_result(mode, query_preview, f"missing dep: {name}"), indent=2))
        return 0

    if not DB_PATH.exists():
        print(json.dumps(
            disabled_result(mode, query_preview, "embeddings.sqlite not found — run scripts/build-embeddings.py"),
            indent=2,
        ))
        return 0

    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    rows = list(conn.execute(
        "SELECT m.slug, m.display_name, v.embedding "
        "FROM archetype_meta m "
        "JOIN archetype_vec v ON m.vec_rowid = v.rowid"
    ))

    if not rows:
        conn.close()
        print(json.dumps(
            disabled_result(mode, query_preview, "embeddings.sqlite has no archetypes yet"),
            indent=2,
        ))
        return 0

    if args.slug:
        match = next((r for r in rows if r[0] == args.slug), None)
        if match is None:
            conn.close()
            print(json.dumps(
                disabled_result(mode, query_preview, f"slug not found in embeddings.sqlite: {args.slug}"),
                indent=2,
            ))
            return 0
        q_vec = np.frombuffer(match[2], dtype=np.float32).copy()
        exclude = args.slug
    else:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as e:
            conn.close()
            name = getattr(e, "name", str(e))
            print(json.dumps(disabled_result(mode, query_preview, f"missing dep: {name}"), indent=2))
            return 0
        model = SentenceTransformer(MODEL_NAME)
        q_vec = model.encode(prose, normalize_embeddings=True)
        q_vec = np.asarray(q_vec, dtype=np.float32)
        exclude = None

    conn.close()

    scored = []
    for slug, dname, emb_bytes in rows:
        if exclude is not None and slug == exclude:
            continue
        v = np.frombuffer(emb_bytes, dtype=np.float32)
        cos = float(np.dot(q_vec, v))
        scored.append((slug, dname, cos))
    scored.sort(key=lambda r: r[2], reverse=True)
    top = scored[: max(1, args.top)]

    result = {
        "query_preview": query_preview,
        "mode": mode,
        "ranked": [
            {"slug": slug, "display_name": dname, "cosine": round(cos, 4)}
            for slug, dname, cos in top
        ],
        "embeddings_enabled": True,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
