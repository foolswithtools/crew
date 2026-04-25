#!/usr/bin/env python3
"""Shim — see crew/embed_query.py for the implementation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from crew.embed_query import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
