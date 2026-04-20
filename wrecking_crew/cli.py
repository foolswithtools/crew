"""
`crew` CLI entry point.

Subcommand surface:
    home              Print $CREW_HOME (used by slash commands)
    doctor            Verify $CREW_HOME state + tool detection
    install           Bootstrap commands and/or catalog data
    update            Re-install catalog data (alias for `install --catalog --force`)
    uninstall         Remove installed commands; --purge also removes $CREW_HOME
    validate          Run the validator (wrapper for wrecking_crew.validate)
    build             Rebuild catalog/INDEX/embeddings/graph
    embed-query       Rank archetypes by similarity (wrapper)
    semantic-dedupe   Score a draft against the embedding index (wrapper)
    usage-log         Maintain .crew/usage.log (wrapper)

Wrappers delegate to the existing module's `main()` so behavior stays
identical to invoking `python -m wrecking_crew.<module>` directly.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _format_doctor(report: dict) -> str:
    lines = []
    lines.append(f"$CREW_HOME: {report['crew_home']}")
    if report.get("config"):
        cfg = report["config"]
        if "_error" in cfg:
            lines.append(f"  config.json: {cfg['_error']}")
        else:
            lines.append(
                f"  config.json: version={cfg.get('version', '?')}, "
                f"installed_at={cfg.get('installed_at', '?')}"
            )
    else:
        lines.append("  config.json: not present (source-repo mode or uninstalled)")
    lines.append("")
    lines.append("Catalog:")
    for check in report["catalog"]:
        marker = "ok " if check["ok"] else "MISSING"
        lines.append(f"  [{marker}] {check['label']}")
    lines.append("")
    lines.append(f"Tools detected: {', '.join(report['tools_detected']) or '(none)'}")
    lines.append(f"Tools supported: {', '.join(report['tools_supported'])}")
    return "\n".join(lines)


def _format_install_commands(result: dict) -> str:
    lines = []
    for tool, payload in result.items():
        lines.append(f"[{tool}] -> {payload['commands_dir']}")
        for w in payload["written"]:
            lines.append(f"  + {w}")
        for s in payload["skipped"]:
            lines.append(f"  - {s}")
    return "\n".join(lines)


def _format_install_catalog(result: dict) -> str:
    if result.get("noop"):
        return f"no-op: {result.get('reason')}"
    lines = [f"$CREW_HOME: {result['crew_home']}", f"source: {result['source']}", ""]
    for w in result["written"]:
        lines.append(f"  + {w}")
    for s in result.get("skipped", []):
        lines.append(f"  - {s}")
    return "\n".join(lines)


def _format_uninstall_commands(result: dict) -> str:
    lines = []
    for tool, payload in result.items():
        lines.append(f"[{tool}] {payload['commands_dir']}")
        for r in payload["removed"]:
            lines.append(f"  - {r}")
        for m in payload["missing"]:
            lines.append(f"  (not present: {m})")
    return "\n".join(lines) or "(no installed commands found)"


def cmd_home(args: argparse.Namespace) -> int:
    from wrecking_crew.paths import CREW_HOME
    print(CREW_HOME)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    from wrecking_crew.install import doctor
    report = doctor()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(_format_doctor(report))
    all_ok = all(check["ok"] for check in report["catalog"])
    return 0 if all_ok else 1


def cmd_install(args: argparse.Namespace) -> int:
    from wrecking_crew.install import install_commands, install_catalog, mcp_instructions

    any_flag = args.commands or args.catalog or args.mcp
    do_commands = args.commands or not any_flag
    do_catalog = args.catalog or not any_flag
    do_mcp = args.mcp or not any_flag

    rc = 0
    if do_catalog:
        result = install_catalog(
            source=Path(args.source).expanduser().resolve() if args.source else None,
            dry_run=args.dry_run,
        )
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("# install --catalog")
            print(_format_install_catalog(result))
            print()

    if do_commands:
        targets = [t.strip() for t in args.target.split(",")] if args.target else None
        try:
            result = install_commands(targets=targets, dry_run=args.dry_run)
        except SystemExit as e:
            print(str(e), file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(result, indent=2, sort_keys=True))
        else:
            print("# install --commands")
            print(_format_install_commands(result))

    if do_mcp and not args.json:
        print()
        print("# install --mcp")
        print(mcp_instructions())

    return rc


def cmd_update(args: argparse.Namespace) -> int:
    from wrecking_crew.install import install_catalog
    result = install_catalog(
        source=Path(args.source).expanduser().resolve() if args.source else None,
        dry_run=args.dry_run,
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(_format_install_catalog(result))
    return 0


def cmd_uninstall(args: argparse.Namespace) -> int:
    from wrecking_crew.install import uninstall_commands, uninstall_catalog
    targets = [t.strip() for t in args.target.split(",")] if args.target else None
    result = uninstall_commands(targets=targets, dry_run=args.dry_run)
    if args.json:
        out: dict = {"commands": result}
    else:
        print("# uninstall --commands")
        print(_format_uninstall_commands(result))

    if args.purge:
        catalog_result = uninstall_catalog(dry_run=args.dry_run)
        if args.json:
            out["catalog"] = catalog_result
        else:
            print()
            print("# uninstall --purge (catalog)")
            if catalog_result.get("noop"):
                print(f"no-op: {catalog_result.get('reason')}")
            elif catalog_result.get("would_remove"):
                print(f"would remove: {catalog_result['crew_home']}")
            elif catalog_result.get("removed"):
                print(f"removed: {catalog_result['crew_home']}")

    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    from wrecking_crew.validate import main as _main
    return _main(["validate", *args.paths])


def cmd_build(args: argparse.Namespace) -> int:
    from wrecking_crew.build_index import main as build_index_main
    from wrecking_crew.build_embeddings import main as build_embeddings_main
    from wrecking_crew.build_graph import main as build_graph_main

    extra = ["--check"] if args.check else []
    rc = build_index_main(["build-index", *extra])
    if rc != 0:
        return rc
    rc = build_embeddings_main(["build-embeddings", *extra])
    if rc != 0:
        return rc
    rc = build_graph_main(["build-graph", *extra])
    return rc


def cmd_embed_query(args: argparse.Namespace) -> int:
    from wrecking_crew.embed_query import main as _main
    forward = ["embed-query"]
    if args.slug:
        forward.extend(["--slug", args.slug])
    if args.top is not None:
        forward.extend(["--top", str(args.top)])
    if args.text:
        forward.append(args.text)
    saved = sys.argv
    sys.argv = forward
    try:
        return _main()
    finally:
        sys.argv = saved


def cmd_semantic_dedupe(args: argparse.Namespace) -> int:
    from wrecking_crew.semantic_duplicate_check import main as _main
    return _main(["semantic-dedupe", args.path])


def cmd_usage_log(args: argparse.Namespace) -> int:
    from wrecking_crew.usage_log import main as _main
    forward = ["usage-log", args.subcmd]
    if args.subcmd == "append":
        forward.append(args.json_blob)
    return _main(forward)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="crew",
        description="The Wrecking Crew CLI — manage the catalog and slash-command install across agentic tools.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("home", help="print $CREW_HOME").set_defaults(func=cmd_home)

    p_doctor = sub.add_parser("doctor", help="verify catalog and tool state")
    p_doctor.add_argument("--json", action="store_true", help="emit JSON")
    p_doctor.set_defaults(func=cmd_doctor)

    p_install = sub.add_parser("install", help="install commands and/or catalog")
    p_install.add_argument("--commands", action="store_true", help="install slash commands into detected tools")
    p_install.add_argument("--catalog", action="store_true", help="copy catalog data into $CREW_HOME")
    p_install.add_argument("--mcp", action="store_true", help="print MCP server registration instructions per tool")
    p_install.add_argument("--target", help="comma-separated tool names to install for (default: all detected)")
    p_install.add_argument("--source", help="path to source repo or unpacked tarball (catalog mode)")
    p_install.add_argument("--dry-run", action="store_true", help="report planned actions without writing")
    p_install.add_argument("--json", action="store_true", help="emit JSON")
    p_install.set_defaults(func=cmd_install)

    p_update = sub.add_parser("update", help="re-copy catalog data into $CREW_HOME")
    p_update.add_argument("--source", help="path to source or unpacked tarball")
    p_update.add_argument("--dry-run", action="store_true")
    p_update.add_argument("--json", action="store_true")
    p_update.set_defaults(func=cmd_update)

    p_uninstall = sub.add_parser("uninstall", help="remove installed slash commands")
    p_uninstall.add_argument("--target", help="comma-separated tool names (default: all detected)")
    p_uninstall.add_argument("--purge", action="store_true", help="also remove $CREW_HOME")
    p_uninstall.add_argument("--dry-run", action="store_true")
    p_uninstall.add_argument("--json", action="store_true")
    p_uninstall.set_defaults(func=cmd_uninstall)

    p_validate = sub.add_parser("validate", help="run the persona validator")
    p_validate.add_argument("paths", nargs="*", help="optional file paths (default: all personas)")
    p_validate.set_defaults(func=cmd_validate)

    p_build = sub.add_parser("build", help="rebuild catalog.json + INDEX.md + embeddings + graph")
    p_build.add_argument("--check", action="store_true", help="fail if any artifact would change")
    p_build.set_defaults(func=cmd_build)

    p_embed = sub.add_parser("embed-query", help="rank archetypes by semantic similarity")
    p_embed.add_argument("--slug", help="rank against an archetype's stored vector")
    p_embed.add_argument("--top", type=int, help="max matches to return")
    p_embed.add_argument("text", nargs="?", help="prose query (omit to read stdin)")
    p_embed.set_defaults(func=cmd_embed_query)

    p_dedupe = sub.add_parser("semantic-dedupe", help="score a draft against the embedding index")
    p_dedupe.add_argument("path", help="path to draft.md")
    p_dedupe.set_defaults(func=cmd_semantic_dedupe)

    p_usage = sub.add_parser("usage-log", help="maintain .crew/usage.log")
    p_usage.add_argument("subcmd", choices=["append", "compact", "signals"])
    p_usage.add_argument("json_blob", nargs="?", help="JSON object (append only)")
    p_usage.set_defaults(func=cmd_usage_log)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
