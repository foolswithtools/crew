#!/usr/bin/env python3
"""
Claude Code PostToolUse hook — triggered on Write/Edit to any file.

If the edited file lives in `personas/`, re-run the validator on it and rebuild
`catalog.json` + `INDEX.md`. Otherwise pass through silently.

Exit codes follow Claude Code's hook protocol:
    0 — silent pass-through (ok)
    2 — blocking error; stderr is surfaced back to Claude so it can fix
    1 — non-blocking warning (unused here)

Docs: https://code.claude.com/docs/en/hooks.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "personas"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"post-write-hook: malformed stdin JSON: {e}", file=sys.stderr)
        return 1

    tool_input = payload.get("tool_input") or {}
    file_path_raw = tool_input.get("file_path")
    if not isinstance(file_path_raw, str):
        return 0

    try:
        file_path = Path(file_path_raw).resolve()
        file_path.relative_to(PERSONAS_DIR)
    except (ValueError, OSError):
        return 0

    if file_path.suffix != ".md":
        return 0

    rel = file_path.relative_to(REPO_ROOT)

    validate = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "validate.py"), str(file_path)],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if validate.returncode != 0:
        sys.stderr.write(f"validator failed on {rel}:\n{validate.stdout}{validate.stderr}")
        return 2

    build = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "build-index.py")],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if build.returncode != 0:
        sys.stderr.write(f"build-index failed after {rel}:\n{build.stdout}{build.stderr}")
        return 2

    sys.stderr.write(f"post-write-hook: {rel} validated, catalog rebuilt\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
