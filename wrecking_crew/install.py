"""
Install/uninstall logic for the `crew` CLI.

Two install axes:
    --commands  Fan out the slash-command markdown files into each detected
                agentic tool's user-level commands directory.
    --catalog   Populate $CREW_HOME with the catalog data (personas/, vocab/,
                catalog.json, INDEX.md, embeddings.sqlite, graph.json).

Multi-tool fan-out detects which tools the user has installed by probing for
their config dirs. v0.1 supports Claude Code, Cursor, Codex CLI, and Windsurf
(all five markdown-command tools). VS Code Copilot is project-level only and
is handled separately by per-repo opt-in (not user-level fan-out).

Catalog install supports two source modes:
    1. --source <path>  Copy from a local directory (e.g. the maintainer's
       source repo, or an unpacked release tarball).
    2. (default)        Auto-detect the source repo from the running package's
       location. Falls back to error if neither is available.

A future v0.2 will add `--release <version>` to download a tarball from
GitHub Releases. Out of scope for v0.1.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from wrecking_crew import __version__
from wrecking_crew.paths import crew_home as _resolve_crew_home


COMMAND_NAMES = (
    "crew",
    "crew-review",
    "crew-browse",
    "crew-related",
    "crew-audit",
    "crew-review-archetype",
)

CATALOG_FILES = (
    "catalog.json",
    "INDEX.md",
    "embeddings.sqlite",
    "graph.json",
)

CATALOG_DIRS = (
    "personas",
    "vocab",
)


@dataclass
class ToolTarget:
    name: str
    probe: Path  # presence of this dir/file means the tool is installed
    commands_dir: Path  # where to write command files
    suffix: str = ".md"  # most use .md; Copilot uses .prompt.md (project-only, not here)


def _tool_targets() -> list[ToolTarget]:
    home = Path.home()
    return [
        ToolTarget(
            name="claude-code",
            probe=home / ".claude",
            commands_dir=home / ".claude" / "commands",
        ),
        ToolTarget(
            name="cursor",
            probe=home / ".cursor",
            commands_dir=home / ".cursor" / "commands",
        ),
        ToolTarget(
            name="codex",
            probe=home / ".codex",
            commands_dir=home / ".codex" / "prompts",
        ),
        ToolTarget(
            name="windsurf",
            probe=home / ".codeium" / "windsurf",
            commands_dir=home / ".codeium" / "windsurf" / "workflows",
        ),
    ]


def detect_tools() -> list[ToolTarget]:
    return [t for t in _tool_targets() if t.probe.exists()]


def _source_repo_root() -> Path | None:
    """Best-effort: find the source repo by walking up from this file."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (
            (candidate / "personas").is_dir()
            and (candidate / "vocab").is_dir()
            and (candidate / "wrecking_crew").is_dir()
        ):
            return candidate
    return None


def _commands_source_dir(source: Path) -> Path | None:
    """Locate the canonical commands source. Phase 4 promotes `commands/`;
    until then `.claude/commands/` is the source of truth."""
    for candidate in (source / "commands", source / ".claude" / "commands"):
        if candidate.is_dir():
            return candidate
    return None


def install_commands(targets: list[str] | None = None, dry_run: bool = False) -> dict:
    """Fan out the 6 command files into each detected tool's commands dir.

    Returns a result dict per tool: {tool_name: {written: [...], skipped: [...]}}.
    """
    source_repo = _source_repo_root()
    if source_repo is None:
        raise SystemExit(
            "crew install --commands: cannot locate the source repo "
            "(re-install via `uv tool install wrecking-crew` from a Release in v0.2)."
        )
    src_dir = _commands_source_dir(source_repo)
    if src_dir is None:
        raise SystemExit(
            f"crew install --commands: no commands directory found at "
            f"{source_repo / 'commands'} or {source_repo / '.claude' / 'commands'}"
        )

    detected = detect_tools()
    selected_names = set(targets) if targets else None
    if selected_names:
        detected = [t for t in detected if t.name in selected_names]
        missing = selected_names - {t.name for t in detected}
        if missing:
            raise SystemExit(
                f"crew install --commands: requested tool(s) not detected: "
                f"{', '.join(sorted(missing))}"
            )
    if not detected:
        raise SystemExit(
            "crew install --commands: no supported tools detected on this machine. "
            "Looked for ~/.claude, ~/.cursor, ~/.codex, ~/.codeium/windsurf."
        )

    result: dict = {}
    for target in detected:
        tool_result = {"commands_dir": str(target.commands_dir), "written": [], "skipped": []}
        if not dry_run:
            target.commands_dir.mkdir(parents=True, exist_ok=True)
        for name in COMMAND_NAMES:
            src = src_dir / f"{name}.md"
            if not src.is_file():
                tool_result["skipped"].append(f"{name}.md (source not found)")
                continue
            dst = target.commands_dir / f"{name}{target.suffix}"
            if dry_run:
                tool_result["written"].append(str(dst))
                continue
            shutil.copy2(src, dst)
            tool_result["written"].append(str(dst))
        result[target.name] = tool_result
    return result


def install_catalog(
    source: Path | None = None,
    crew_home: Path | None = None,
    dry_run: bool = False,
) -> dict:
    """Populate $CREW_HOME with personas/, vocab/, and built artifacts.

    If `source` is omitted, auto-detects the source repo from this file's
    location. If `crew_home` is omitted, resolves via the standard chain.

    Refuses to overwrite an existing $CREW_HOME unless the existing one
    looks empty or is the source repo itself (idempotent in source-repo mode).
    """
    if source is None:
        source = _source_repo_root()
        if source is None:
            raise SystemExit(
                "crew install --catalog: no --source given and source repo not found"
            )
    source = source.resolve()
    if crew_home is None:
        crew_home = _resolve_crew_home()
    crew_home = crew_home.resolve()

    if crew_home == source:
        # Maintainer flow — nothing to copy; CREW_HOME already IS the source.
        return {
            "crew_home": str(crew_home),
            "source": str(source),
            "noop": True,
            "reason": "$CREW_HOME and --source are the same directory",
        }

    written: list[str] = []
    skipped: list[str] = []

    if not dry_run:
        crew_home.mkdir(parents=True, exist_ok=True)

    for d in CATALOG_DIRS:
        src = source / d
        dst = crew_home / d
        if not src.is_dir():
            skipped.append(f"{d}/ (source missing)")
            continue
        if dry_run:
            written.append(str(dst))
            continue
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
        written.append(str(dst))

    for f in CATALOG_FILES:
        src = source / f
        dst = crew_home / f
        if not src.is_file():
            skipped.append(f"{f} (source missing)")
            continue
        if dry_run:
            written.append(str(dst))
            continue
        shutil.copy2(src, dst)
        written.append(str(dst))

    if not dry_run:
        config_path = crew_home / "config.json"
        config = {
            "home": str(crew_home),
            "source": str(source),
            "version": __version__,
            "installed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
        written.append(str(config_path))

    return {
        "crew_home": str(crew_home),
        "source": str(source),
        "written": written,
        "skipped": skipped,
    }


def uninstall_commands(targets: list[str] | None = None, dry_run: bool = False) -> dict:
    """Remove the 6 command files from each detected tool's commands dir."""
    detected = detect_tools()
    selected_names = set(targets) if targets else None
    if selected_names:
        detected = [t for t in detected if t.name in selected_names]

    result: dict = {}
    for target in detected:
        tool_result = {"commands_dir": str(target.commands_dir), "removed": [], "missing": []}
        for name in COMMAND_NAMES:
            dst = target.commands_dir / f"{name}{target.suffix}"
            if not dst.exists():
                tool_result["missing"].append(name)
                continue
            if dry_run:
                tool_result["removed"].append(str(dst))
                continue
            dst.unlink()
            tool_result["removed"].append(str(dst))
        result[target.name] = tool_result
    return result


def uninstall_catalog(crew_home: Path | None = None, dry_run: bool = False) -> dict:
    """Remove the entire $CREW_HOME directory. Refuses if it looks like the
    source repo (presence of `wrecking_crew/` package dir)."""
    if crew_home is None:
        crew_home = _resolve_crew_home()
    crew_home = crew_home.resolve()

    if (crew_home / "wrecking_crew").is_dir():
        raise SystemExit(
            f"crew uninstall --purge: refusing to delete {crew_home} — "
            "it looks like the source repo (contains wrecking_crew/)"
        )

    if not crew_home.exists():
        return {"crew_home": str(crew_home), "noop": True, "reason": "does not exist"}

    if dry_run:
        return {"crew_home": str(crew_home), "would_remove": True}

    shutil.rmtree(crew_home)
    return {"crew_home": str(crew_home), "removed": True}


MCP_INSTRUCTIONS = """\
The Wrecking Crew MCP server (`crew-mcp`) exposes the catalog as read-only
tools. Register it once per tool — the same server binary serves all of them.

[Claude Code]
    claude mcp add wrecking-crew --scope user -- crew-mcp

[Codex CLI]
    codex mcp add wrecking-crew -- crew-mcp

[Cursor]
    Edit ~/.cursor/mcp.json and add under "mcpServers":
        "wrecking-crew": { "command": "crew-mcp" }

[Windsurf]
    Settings -> Cascade -> MCP Servers -> Add Server
        Name: wrecking-crew
        Command: crew-mcp

[Antigravity]
    Edit ~/.gemini/antigravity/mcp_config.json and add under "mcpServers":
        "wrecking-crew": { "command": "crew-mcp" }
    Or use the in-editor MCP Store and add a custom server with command: crew-mcp

[Cline]
    Cline panel -> MCP Servers -> Edit -> add:
        "wrecking-crew": { "command": "crew-mcp" }

[GitHub Copilot CLI]
    /mcp add wrecking-crew -- crew-mcp

[Zed]
    Edit ~/.config/zed/settings.json under "context_servers":
        "wrecking-crew": { "command": { "path": "crew-mcp" } }

If `crew-mcp` is not on PATH, replace it with the absolute path returned by
`which crew-mcp` (or `uvx --from wrecking-crew crew-mcp` if running via uv).
"""


def mcp_instructions() -> str:
    return MCP_INSTRUCTIONS


def doctor(crew_home: Path | None = None) -> dict:
    """Report on the catalog state at $CREW_HOME and tool detection."""
    if crew_home is None:
        crew_home = _resolve_crew_home()
    crew_home = crew_home.resolve()

    catalog_checks = []
    for label, path in [
        ("$CREW_HOME", crew_home),
        ("personas/", crew_home / "personas"),
        ("vocab/", crew_home / "vocab"),
        ("catalog.json", crew_home / "catalog.json"),
        ("INDEX.md", crew_home / "INDEX.md"),
        ("embeddings.sqlite", crew_home / "embeddings.sqlite"),
        ("graph.json", crew_home / "graph.json"),
    ]:
        catalog_checks.append({"label": label, "path": str(path), "ok": path.exists()})

    config_path = crew_home / "config.json"
    config = None
    if config_path.is_file():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            config = {"_error": "config.json present but unreadable"}

    detected = detect_tools()
    return {
        "crew_home": str(crew_home),
        "config": config,
        "catalog": catalog_checks,
        "tools_detected": [t.name for t in detected],
        "tools_supported": [t.name for t in _tool_targets()],
    }
