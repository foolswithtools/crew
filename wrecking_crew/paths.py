"""
Locate the catalog data root ($CREW_HOME) and expose canonical paths.

Resolution order:
    1. $CREW_HOME environment variable (explicit override)
    2. Walk up from cwd looking for source-repo markers (author-side flow)
    3. Walk up from this file's location for the same markers (editable install)
    4. ~/.wrecking-crew/config.json (end-user install pointer)
    5. ~/.wrecking-crew (default)

The source-repo markers are `personas/`, `vocab/`, and `wrecking_crew/`. End
users have the first two in $CREW_HOME but not the third (the package code
lives in their site-packages), so the marker reliably distinguishes
"running inside the source repo" from "running against an installed catalog".

`REPO_ROOT` is exported as a backward-compat alias for scripts that imported
it from the old `validate.py`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


def _looks_like_source_repo(p: Path) -> bool:
    return (
        (p / "personas").is_dir()
        and (p / "vocab").is_dir()
        and (p / "wrecking_crew").is_dir()
    )


def crew_home() -> Path:
    env = os.environ.get("CREW_HOME")
    if env:
        return Path(env).expanduser().resolve()

    cwd = Path.cwd().resolve()
    for candidate in (cwd, *cwd.parents):
        if _looks_like_source_repo(candidate):
            return candidate

    here = Path(__file__).resolve()
    for candidate in here.parents:
        if _looks_like_source_repo(candidate):
            return candidate

    cfg = Path.home() / ".wrecking-crew" / "config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
            home = data.get("home")
            if isinstance(home, str) and home:
                return Path(home).expanduser().resolve()
        except (OSError, json.JSONDecodeError, KeyError):
            pass

    return Path.home() / ".wrecking-crew"


CREW_HOME = crew_home()
PERSONAS_DIR = CREW_HOME / "personas"
VOCAB_DIR = CREW_HOME / "vocab"
CATALOG_PATH = CREW_HOME / "catalog.json"
INDEX_PATH = CREW_HOME / "INDEX.md"
EMBEDDINGS_DB = CREW_HOME / "embeddings.sqlite"
GRAPH_PATH = CREW_HOME / "graph.json"
CREW_DIR = CREW_HOME / ".crew"
USAGE_LOG_PATH = CREW_DIR / "usage.log"
SIGNALS_PATH = CREW_DIR / "signals.json"

# Backward-compat alias for scripts that imported REPO_ROOT from validate.py.
REPO_ROOT = CREW_HOME
