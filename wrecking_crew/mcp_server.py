"""
MCP server exposing the catalog as read-only tools.

Tool surface (all read-only):
    list_archetypes()           -> list of archetypes with display_name + tags
    get_archetype(slug)         -> full markdown body
    search(query, top_k=10)     -> ranked archetypes by cosine similarity
    related(slug, top_k=5)      -> contrast/shared/paired neighbors + semantic
    vocab(facet)                -> parsed vocab/<facet>.yml
    signals()                   -> trending + new-this-month

Transport: stdio (default for FastMCP). Designed for tools without a
markdown slash-command surface (Antigravity, Cline, Copilot CLI, Zed) so
the catalog stays reachable as tool calls. Markdown-command tools (Claude
Code, Cursor, Codex, Windsurf) can also use it but typically won't need to.

Embedding-aware tools (search, related's semantic edges) gracefully degrade
to {"embeddings_enabled": false} if sentence-transformers / sqlite-vec are
absent — same contract as the CLI.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

import yaml
from mcp.server.fastmcp import FastMCP

from wrecking_crew.paths import (
    CATALOG_PATH,
    EMBEDDINGS_DB,
    GRAPH_PATH,
    PERSONAS_DIR,
    SIGNALS_PATH,
    VOCAB_DIR,
)


mcp = FastMCP("wrecking-crew")


def _load_catalog() -> list[dict]:
    if not CATALOG_PATH.is_file():
        return []
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


@mcp.tool()
def list_archetypes() -> list[dict]:
    """List every archetype in the catalog with its display name, exemplars, and facet tags.

    Use this first to see the full catalog. Each entry has:
        slug, display_name, exemplars, expertise, function, approach, reviewed.
    """
    catalog = _load_catalog()
    return [
        {
            "slug": a["name"],
            "display_name": a["display_name"],
            "exemplars": a["exemplars"],
            "expertise": a["expertise"],
            "function": a["function"],
            "approach": a["approach"],
            "reviewed": a["reviewed"],
        }
        for a in catalog
    ]


@mcp.tool()
def get_archetype(slug: str) -> str:
    """Return the full markdown body of one archetype (frontmatter + prose sections).

    Use after `list_archetypes` or `search` to read a specific archetype's voice,
    blind spots, and contrasts. Slug is the kebab-case name (e.g. "rigorous-quant-ml-researcher").
    """
    path = PERSONAS_DIR / f"{slug}.md"
    if not path.is_file():
        raise ValueError(f"archetype not found: {slug}")
    return path.read_text(encoding="utf-8")


@mcp.tool()
def search(query: str, top_k: int = 10) -> dict:
    """Rank archetypes by semantic similarity to a problem description.

    Use this to surface 3-5 candidate critics for a given problem. Returns
    {"ranked": [{slug, display_name, cosine}, ...], "embeddings_enabled": bool}.
    If embeddings aren't available, returns embeddings_enabled=false and an empty
    list — caller should fall back to reading list_archetypes and judging by tags.
    """
    try:
        import numpy as np
        import sqlite_vec
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        return {
            "ranked": [],
            "embeddings_enabled": False,
            "disabled_reason": f"missing dep: {getattr(e, 'name', str(e))}",
        }

    if not EMBEDDINGS_DB.is_file():
        return {
            "ranked": [],
            "embeddings_enabled": False,
            "disabled_reason": "embeddings.sqlite not found — run `crew build`",
        }

    conn = sqlite3.connect(str(EMBEDDINGS_DB))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)

    rows = list(
        conn.execute(
            "SELECT m.slug, m.display_name, v.embedding "
            "FROM archetype_meta m JOIN archetype_vec v ON m.vec_rowid = v.rowid"
        )
    )
    conn.close()
    if not rows:
        return {"ranked": [], "embeddings_enabled": True, "note": "index empty"}

    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    q_vec = np.asarray(
        model.encode(query, normalize_embeddings=True), dtype=np.float32
    )

    scored: list[tuple[str, str, float]] = []
    for slug, dname, emb_bytes in rows:
        v = np.frombuffer(emb_bytes, dtype=np.float32)
        scored.append((slug, dname, float(np.dot(q_vec, v))))
    scored.sort(key=lambda r: r[2], reverse=True)

    return {
        "ranked": [
            {"slug": s, "display_name": d, "cosine": round(c, 4)}
            for s, d, c in scored[: max(1, top_k)]
        ],
        "embeddings_enabled": True,
    }


def _semantic_neighbors(slug: str, top_k: int = 5) -> dict:
    try:
        import numpy as np
        import sqlite_vec
    except ImportError as e:
        return {
            "neighbors": [],
            "embeddings_enabled": False,
            "disabled_reason": f"missing dep: {getattr(e, 'name', str(e))}",
        }
    if not EMBEDDINGS_DB.is_file():
        return {
            "neighbors": [],
            "embeddings_enabled": False,
            "disabled_reason": "embeddings.sqlite not found",
        }

    conn = sqlite3.connect(str(EMBEDDINGS_DB))
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    rows = list(
        conn.execute(
            "SELECT m.slug, m.display_name, v.embedding "
            "FROM archetype_meta m JOIN archetype_vec v ON m.vec_rowid = v.rowid"
        )
    )
    conn.close()

    target = next((r for r in rows if r[0] == slug), None)
    if target is None:
        return {"neighbors": [], "embeddings_enabled": True, "note": f"slug not in index: {slug}"}
    q_vec = np.frombuffer(target[2], dtype=np.float32).copy()

    scored: list[tuple[str, str, float]] = []
    for s, d, emb in rows:
        if s == slug:
            continue
        v = np.frombuffer(emb, dtype=np.float32)
        scored.append((s, d, float(np.dot(q_vec, v))))
    scored.sort(key=lambda r: r[2], reverse=True)
    return {
        "neighbors": [
            {"slug": s, "display_name": d, "cosine": round(c, 4)}
            for s, d, c in scored[: max(1, top_k)]
        ],
        "embeddings_enabled": True,
    }


@mcp.tool()
def related(slug: str, top_k: int = 5) -> dict:
    """Return graph neighbors of an archetype: contrasts, shared exemplars,
    frequently paired-with archetypes, and top semantic neighbors by cosine.

    Use to explore from one archetype outward — for non-duplication checks
    when drafting, or to widen a crew with adjacent voices.
    """
    if not GRAPH_PATH.is_file():
        return {"error": "graph.json not found — run `crew build`"}
    graph = json.loads(GRAPH_PATH.read_text(encoding="utf-8"))

    contrasts = [e for e in graph["edges"]["contrasts"] if e["from"] == slug or e["to"] == slug]
    shared = [
        e for e in graph["edges"]["shares_exemplar"] if slug in e["archetypes"]
    ]
    paired = [
        e for e in graph["edges"]["frequently_paired_with"] if slug in e["archetypes"]
    ]
    semantic = _semantic_neighbors(slug, top_k=top_k)

    return {
        "slug": slug,
        "contrasts": contrasts,
        "shares_exemplar": shared,
        "frequently_paired_with": paired,
        "semantic_neighbors": semantic,
    }


@mcp.tool()
def vocab(facet: str) -> dict:
    """Return the SKOS controlled vocabulary for one facet.

    Valid facets: "expertise", "function", "approach". Each entry has label,
    definition, and broader/narrower/related/cross_facet_related links.
    """
    if facet not in {"expertise", "function", "approach"}:
        raise ValueError(f"unknown facet: {facet} (expected expertise/function/approach)")
    path = VOCAB_DIR / f"{facet}.yml"
    if not path.is_file():
        raise ValueError(f"vocab file missing: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data


@mcp.tool()
def signals() -> dict:
    """Return derived usage signals: trending archetypes (30-day) and new-this-month.

    Empty if the catalog hasn't been invoked yet (.crew/signals.json absent).
    """
    if not SIGNALS_PATH.is_file():
        return {"trending": [], "new_this_month": [], "by_slug": {}, "note": "no signals yet"}
    return json.loads(SIGNALS_PATH.read_text(encoding="utf-8"))


def main() -> int:
    """Entry point — runs the FastMCP stdio server."""
    mcp.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
