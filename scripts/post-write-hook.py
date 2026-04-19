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
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "personas"
VENV_PY = REPO_ROOT / "venv" / "bin" / "python3"


def maybe_reexec_with_venv() -> None:
    """If a repo-local venv exists and we're not already in it, re-exec.

    Phase 3 scripts need sentence-transformers / sqlite-vec, which live in
    the venv. Settings.json invokes this hook with plain `python3`, so we
    hop into the venv here when present. No-op if the venv is absent or we
    are already running from it.

    Uses `sys.prefix != sys.base_prefix` as the "inside a venv" signal —
    resolving VENV_PY through its symlinks lands on the base interpreter,
    which would falsely make an outside process look like the same target.
    """
    if not VENV_PY.exists():
        return
    if getattr(sys, "base_prefix", sys.prefix) != sys.prefix:
        return
    os.execv(str(VENV_PY), [str(VENV_PY), *sys.argv])


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, cwd=str(REPO_ROOT))


def main() -> int:
    maybe_reexec_with_venv()

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

    validate = run([sys.executable, str(REPO_ROOT / "scripts" / "validate.py"), str(file_path)])
    if validate.returncode != 0:
        sys.stderr.write(f"validator failed on {rel}:\n{validate.stdout}{validate.stderr}")
        return 2

    build = run([sys.executable, str(REPO_ROOT / "scripts" / "build-index.py")])
    if build.returncode != 0:
        sys.stderr.write(f"build-index failed after {rel}:\n{build.stdout}{build.stderr}")
        return 2

    # Derived artifacts beyond catalog.json — non-blocking. Failures here are
    # reported but do not reject the persona edit (embeddings + graph are
    # rebuildable from Layer 1 at any time).
    emb_script = REPO_ROOT / "scripts" / "build-embeddings.py"
    if emb_script.exists():
        emb = run([sys.executable, str(emb_script), str(file_path)])
        if emb.returncode != 0:
            sys.stderr.write(f"build-embeddings warning for {rel}:\n{emb.stdout}{emb.stderr}")

    graph_script = REPO_ROOT / "scripts" / "build-graph.py"
    if graph_script.exists():
        graph = run([sys.executable, str(graph_script)])
        if graph.returncode != 0:
            sys.stderr.write(f"build-graph warning for {rel}:\n{graph.stdout}{graph.stderr}")

    # Signals depend only on .crew/usage.log + git history, but INDEX.md's
    # Trending / New-this-month sections read the signals file — regenerate
    # it so INDEX.md stays fresh. Cheap and non-blocking.
    usage_log_script = REPO_ROOT / "scripts" / "usage-log.py"
    if usage_log_script.exists():
        sig = run([sys.executable, str(usage_log_script), "signals"])
        if sig.returncode != 0:
            sys.stderr.write(f"usage-log signals warning for {rel}:\n{sig.stdout}{sig.stderr}")
        else:
            # Signals may have changed INDEX.md's derived sections; rebuild.
            rebuild = run([sys.executable, str(REPO_ROOT / "scripts" / "build-index.py")])
            if rebuild.returncode != 0:
                sys.stderr.write(f"post-signals build-index warning for {rel}:\n{rebuild.stdout}{rebuild.stderr}")

    sys.stderr.write(f"post-write-hook: {rel} validated, catalog rebuilt\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
