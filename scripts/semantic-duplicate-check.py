#!/usr/bin/env python3
"""Shim — see crew/semantic_duplicate_check.py for the implementation."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from crew.semantic_duplicate_check import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv))
