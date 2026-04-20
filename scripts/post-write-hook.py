#!/usr/bin/env python3
"""Shim — re-execs into the repo-local venv if present, then invokes
`wrecking_crew.post_write_hook`. The real implementation lives there.

Author-side hook: validates and rebuilds derived artifacts when a persona
file is written or edited. End users do not need this script."""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENV_PY = REPO_ROOT / "venv" / "bin" / "python3"

if VENV_PY.exists() and getattr(sys, "base_prefix", sys.prefix) == sys.prefix:
    os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])

sys.path.insert(0, str(REPO_ROOT))
from wrecking_crew.post_write_hook import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
