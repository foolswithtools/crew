#!/usr/bin/env python3
"""
Claude Code PostToolUse hook — triggered on Write/Edit to any file.

If the edited file lives in `personas/`, re-run the validator on it and rebuild
`catalog.json` + `INDEX.md`. Otherwise pass through silently.

Exit codes follow Claude Code's hook protocol:
    0 — silent pass-through (ok)
    2 — blocking error; stderr is surfaced back to Claude so it can fix
    1 — non-blocking warning (unused here)

Author-side. Venv re-exec is handled by the shim at `scripts/post-write-hook.py`
so this module assumes it's already running in the right interpreter.

Docs: https://code.claude.com/docs/en/hooks.md
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from wrecking_crew.paths import REPO_ROOT, PERSONAS_DIR


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))


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

    validate = run([sys.executable, "-m", "wrecking_crew.validate", str(file_path)])
    if validate.returncode != 0:
        sys.stderr.write(f"validator failed on {rel}:\n{validate.stdout}{validate.stderr}")
        return 2

    build = run([sys.executable, "-m", "wrecking_crew.build_index"])
    if build.returncode != 0:
        sys.stderr.write(f"build-index failed after {rel}:\n{build.stdout}{build.stderr}")
        return 2

    # Derived artifacts beyond catalog.json — non-blocking. Failures here are
    # reported but do not reject the persona edit (embeddings + graph are
    # rebuildable from Layer 1 at any time).
    emb = run([sys.executable, "-m", "wrecking_crew.build_embeddings", str(file_path)])
    if emb.returncode != 0:
        sys.stderr.write(f"build-embeddings warning for {rel}:\n{emb.stdout}{emb.stderr}")

    graph = run([sys.executable, "-m", "wrecking_crew.build_graph"])
    if graph.returncode != 0:
        sys.stderr.write(f"build-graph warning for {rel}:\n{graph.stdout}{graph.stderr}")

    # Signals depend only on .crew/usage.log + git history, but INDEX.md's
    # Trending / New-this-month sections read the signals file — regenerate
    # it so INDEX.md stays fresh. Cheap and non-blocking.
    sig = run([sys.executable, "-m", "wrecking_crew.usage_log", "signals"])
    if sig.returncode != 0:
        sys.stderr.write(f"usage-log signals warning for {rel}:\n{sig.stdout}{sig.stderr}")
    else:
        # Signals may have changed INDEX.md's derived sections; rebuild.
        rebuild = run([sys.executable, "-m", "wrecking_crew.build_index"])
        if rebuild.returncode != 0:
            sys.stderr.write(f"post-signals build-index warning for {rel}:\n{rebuild.stdout}{rebuild.stderr}")

    sys.stderr.write(f"post-write-hook: {rel} validated, catalog rebuilt\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
