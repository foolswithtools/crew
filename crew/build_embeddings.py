#!/usr/bin/env python3
"""
Build/update the embedding index at `embeddings.sqlite`.

Modes:
    python3 scripts/build-embeddings.py                 # full reconcile
    python3 scripts/build-embeddings.py personas/x.md   # single-file upsert
    python3 scripts/build-embeddings.py --check         # fail if hashes drift

Uses sentence-transformers/all-MiniLM-L6-v2 (384-dim, L2-normalised) with
sqlite-vec for vector storage. Graceful degradation: if sentence_transformers
or sqlite_vec can't import, prints one stderr line and exits 0 so the core
P1/P2 validator + build-index flow stays unblocked.

Layer 2 artifact — gitignored; always regenerable from personas/*.md.
"""

from __future__ import annotations

import datetime
import hashlib
import sqlite3
import sys
from pathlib import Path

from crew.paths import REPO_ROOT, PERSONAS_DIR, EMBEDDINGS_DB as DB_PATH
from crew.validate import split_frontmatter
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBED_DIM = 384


def content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def try_import():
    try:
        import numpy as np
        import sqlite_vec
        from sentence_transformers import SentenceTransformer
        return sqlite_vec, SentenceTransformer, np
    except ImportError as e:
        name = getattr(e, "name", str(e))
        print(
            f"embeddings disabled — missing dep: {name} "
            f"(run: source venv/bin/activate && pip install -r requirements.txt)",
            file=sys.stderr,
        )
        return None


def open_db(sqlite_vec_mod) -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.enable_load_extension(True)
    sqlite_vec_mod.load(conn)
    conn.enable_load_extension(False)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS archetype_meta (
          slug          TEXT PRIMARY KEY,
          content_hash  TEXT NOT NULL,
          display_name  TEXT NOT NULL,
          embedded_at   TEXT NOT NULL,
          vec_rowid     INTEGER NOT NULL UNIQUE
        );
        """
    )
    conn.execute(
        f"CREATE VIRTUAL TABLE IF NOT EXISTS archetype_vec "
        f"USING vec0(embedding FLOAT[{EMBED_DIM}])"
    )
    return conn


def read_meta_and_body(path: Path) -> tuple[str, str, str]:
    text = path.read_text(encoding="utf-8")
    meta, body, findings = split_frontmatter(text, path)
    if meta is None:
        errs = "; ".join(f.message for f in findings)
        raise SystemExit(f"build-embeddings: malformed {path.relative_to(REPO_ROOT)} — {errs}")
    slug = meta.get("name")
    display = meta.get("display_name")
    if not isinstance(slug, str) or not isinstance(display, str):
        raise SystemExit(
            f"build-embeddings: {path.relative_to(REPO_ROOT)} missing name/display_name"
        )
    return slug, display, body


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def pack_vec(np, vec) -> bytes:
    return np.asarray(vec, dtype=np.float32).tobytes()


def encode(model, np, text: str):
    vec = model.encode(text, normalize_embeddings=True)
    return np.asarray(vec, dtype=np.float32)


def upsert(conn: sqlite3.Connection, model, np, path: Path) -> str:
    slug, display, body = read_meta_and_body(path)
    h = content_hash(path)
    row = conn.execute(
        "SELECT content_hash, vec_rowid FROM archetype_meta WHERE slug = ?",
        (slug,),
    ).fetchone()
    if row is not None and row[0] == h:
        return "skipped"
    vec_bytes = pack_vec(np, encode(model, np, body))
    now = now_iso()
    if row is None:
        cur = conn.execute(
            "INSERT INTO archetype_vec(embedding) VALUES (?)",
            (vec_bytes,),
        )
        vec_rowid = cur.lastrowid
        conn.execute(
            "INSERT INTO archetype_meta "
            "(slug, content_hash, display_name, embedded_at, vec_rowid) "
            "VALUES (?, ?, ?, ?, ?)",
            (slug, h, display, now, vec_rowid),
        )
        return "inserted"
    vec_rowid = row[1]
    conn.execute(
        "UPDATE archetype_vec SET embedding = ? WHERE rowid = ?",
        (vec_bytes, vec_rowid),
    )
    conn.execute(
        "UPDATE archetype_meta "
        "SET content_hash = ?, display_name = ?, embedded_at = ? WHERE slug = ?",
        (h, display, now, slug),
    )
    return "updated"


def delete_missing(conn: sqlite3.Connection, present: set[str]) -> int:
    rows = list(conn.execute("SELECT slug, vec_rowid FROM archetype_meta"))
    removed = 0
    for slug, vec_rowid in rows:
        if slug not in present:
            conn.execute("DELETE FROM archetype_vec WHERE rowid = ?", (vec_rowid,))
            conn.execute("DELETE FROM archetype_meta WHERE slug = ?", (slug,))
            removed += 1
    return removed


def scan_personas() -> dict[str, tuple[Path, str]]:
    """Return {slug: (path, content_hash)} for every persona file."""
    out: dict[str, tuple[Path, str]] = {}
    for path in sorted(PERSONAS_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        meta, _body, _ = split_frontmatter(text, path)
        if meta and isinstance(meta.get("name"), str):
            out[meta["name"]] = (path, content_hash(path))
    return out


def full_reconcile(conn, model_factory, np) -> int:
    scan = scan_personas()
    stored = {
        row[0]: row[1]
        for row in conn.execute("SELECT slug, content_hash FROM archetype_meta")
    }
    pending_paths = [p for slug, (p, h) in scan.items() if stored.get(slug) != h]

    inserted = updated = skipped = 0
    if pending_paths:
        model = model_factory()
        for path in pending_paths:
            result = upsert(conn, model, np, path)
            if result == "inserted":
                inserted += 1
            elif result == "updated":
                updated += 1
            else:
                skipped += 1
    else:
        skipped = len(scan)

    removed = delete_missing(conn, set(scan.keys()))
    conn.commit()
    print(
        f"built {len(scan)} archetype(s) — "
        f"inserted {inserted}, updated {updated}, skipped {skipped}, removed {removed}"
    )
    return 0


def single_file(conn, model_factory, np, path: Path) -> int:
    if not path.exists():
        print(f"file not found: {path}", file=sys.stderr)
        return 1
    slug, _display, _body = read_meta_and_body(path)
    h = content_hash(path)
    row = conn.execute(
        "SELECT content_hash FROM archetype_meta WHERE slug = ?", (slug,)
    ).fetchone()
    if row is not None and row[0] == h:
        print(f"{path.relative_to(REPO_ROOT)}: skipped")
        return 0
    model = model_factory()
    result = upsert(conn, model, np, path)
    conn.commit()
    print(f"{path.relative_to(REPO_ROOT)}: {result}")
    return 0


def check_mode(conn) -> int:
    scan = scan_personas()
    stored_hash = {
        row[0]: row[1]
        for row in conn.execute("SELECT slug, content_hash FROM archetype_meta")
    }
    drifted = False
    for slug, (_path, h) in scan.items():
        if stored_hash.get(slug) != h:
            shown = stored_hash.get(slug, "<missing>")[:12]
            print(f"DRIFT  {slug}  stored={shown} actual={h[:12]}", file=sys.stderr)
            drifted = True
    for slug in stored_hash.keys() - scan.keys():
        print(f"STALE  {slug}  in DB but not in personas/", file=sys.stderr)
        drifted = True
    orphans = conn.execute(
        "SELECT m.slug FROM archetype_meta m "
        "LEFT JOIN archetype_vec v ON m.vec_rowid = v.rowid "
        "WHERE v.rowid IS NULL"
    ).fetchall()
    for (slug,) in orphans:
        print(f"ORPHAN {slug}  archetype_meta row has no vector", file=sys.stderr)
        drifted = True
    if drifted:
        return 1
    print(f"check ok — {len(scan)} archetype(s), no drift")
    return 0


def main(argv: list[str]) -> int:
    imported = try_import()
    if imported is None:
        return 0
    sqlite_vec_mod, SentenceTransformer, np = imported

    args = argv[1:]
    check = "--check" in args
    files = [a for a in args if a != "--check"]

    conn = open_db(sqlite_vec_mod)
    try:
        if check:
            if files:
                print("--check does not accept file arguments", file=sys.stderr)
                return 1
            return check_mode(conn)

        def model_factory():
            return SentenceTransformer(MODEL_NAME)

        if files:
            for f in files:
                rc = single_file(conn, model_factory, np, Path(f).resolve())
                if rc != 0:
                    return rc
            return 0

        return full_reconcile(conn, model_factory, np)
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
