#!/usr/bin/env python3
"""
Score a proposed archetype draft against the existing embedding index.

Usage:
    python3 scripts/semantic-duplicate-check.py <path/to/draft.md>

Embeds the prose body of the draft with the same model as
`build-embeddings.py` (all-MiniLM-L6-v2, 384-dim, L2-normalised) and
reports the top similar existing archetypes as JSON on stdout:

    {
      "query": "<display_name from draft or 'unknown'>",
      "query_path": "<path>",
      "top_matches": [
        {"slug": "...", "display_name": "...", "cosine": 0.xx, "verdict": "duplicate|related|distinct"},
        ...  // up to 5
      ],
      "max_cosine": 0.xx,
      "trip_threshold": "duplicate|related|distinct",
      "embeddings_enabled": true
    }

Thresholds:
    cosine > 0.85 → "duplicate"  (stop, ask for justification)
    0.70 .. 0.85 → "related"     (declare intentional difference)
    < 0.70      → "distinct"

If embedding deps aren't available or `embeddings.sqlite` is missing,
emit a minimal JSON result with `embeddings_enabled: false` and exit 0
so /crew can fall back to the P2 Jaccard/tag check without failing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from crew.paths import REPO_ROOT, EMBEDDINGS_DB as DB_PATH
from crew.validate import split_frontmatter
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384
TOP_K = 5

DUPLICATE_T = 0.85
RELATED_T = 0.70


def verdict_for(score: float) -> str:
    if score > DUPLICATE_T:
        return "duplicate"
    if score >= RELATED_T:
        return "related"
    return "distinct"


def disabled_result(path: Path, reason: str) -> dict:
    return {
        "query": "unknown",
        "query_path": str(path),
        "top_matches": [],
        "max_cosine": None,
        "trip_threshold": "distinct",
        "embeddings_enabled": False,
        "disabled_reason": reason,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: semantic-duplicate-check.py <path/to/draft.md>", file=sys.stderr)
        return 1

    draft_path = Path(argv[1]).resolve()
    if not draft_path.exists():
        print(f"file not found: {draft_path}", file=sys.stderr)
        return 1

    try:
        import numpy as np
        import sqlite_vec
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        name = getattr(e, "name", str(e))
        print(
            json.dumps(disabled_result(draft_path, f"missing dep: {name}"), indent=2)
        )
        return 0

    if not DB_PATH.exists():
        print(
            json.dumps(
                disabled_result(draft_path, "embeddings.sqlite not found — run scripts/build-embeddings.py"),
                indent=2,
            )
        )
        return 0

    text = draft_path.read_text(encoding="utf-8")
    meta, body, _ = split_frontmatter(text, draft_path)
    if meta is None:
        # Draft may not have full frontmatter yet — embed whole file.
        body = text
        display = "unknown"
    else:
        display = meta.get("display_name") or "unknown"

    model = SentenceTransformer(MODEL_NAME)
    q_vec = model.encode(body, normalize_embeddings=True)
    q_vec = np.asarray(q_vec, dtype=np.float32)

    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    rows = list(
        conn.execute(
            "SELECT m.slug, m.display_name, v.embedding "
            "FROM archetype_meta m "
            "JOIN archetype_vec v ON m.vec_rowid = v.rowid"
        )
    )
    conn.close()

    if not rows:
        print(
            json.dumps(
                disabled_result(draft_path, "embeddings.sqlite has no archetypes yet"),
                indent=2,
            )
        )
        return 0

    scored = []
    for slug, dname, emb_bytes in rows:
        v = np.frombuffer(emb_bytes, dtype=np.float32)
        # Vectors are L2-normalised, so dot product == cosine similarity.
        cos = float(np.dot(q_vec, v))
        scored.append((slug, dname, cos))
    scored.sort(key=lambda r: r[2], reverse=True)

    # Exclude self-match: any stored archetype with a name equal to the draft's
    # display name should be skipped (it'd be the file itself if re-running).
    if display != "unknown":
        scored = [r for r in scored if r[1] != display]

    top = scored[:TOP_K]
    matches = [
        {
            "slug": slug,
            "display_name": dname,
            "cosine": round(cos, 4),
            "verdict": verdict_for(cos),
        }
        for slug, dname, cos in top
    ]
    max_cos = top[0][2] if top else 0.0
    result = {
        "query": display,
        "query_path": str(draft_path.relative_to(REPO_ROOT)) if draft_path.is_relative_to(REPO_ROOT) else str(draft_path),
        "top_matches": matches,
        "max_cosine": round(max_cos, 4),
        "trip_threshold": verdict_for(max_cos),
        "embeddings_enabled": True,
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
