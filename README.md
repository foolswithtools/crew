# The Wrecking Crew

A catalog of **archetype critics** you can invoke mid-conversation in your agentic coding tool to pressure-test whatever you're working on. Two commands, two journeys.

- **`/crew`** — reads what you've been working on, reflects the problem back sharper, proposes 3-4 non-overlapping critics from the catalog. If a needed archetype doesn't exist, it drafts one inline in 2 minutes and saves it.
- **`/crew-review`** — launches the chosen crew as parallel subagents who tear into your work independently (Round 1). Optional Round 2 synthesis where they hold their ground rather than collapse to consensus.

Named after [The Wrecking Crew](https://en.wikipedia.org/wiki/The_Wrecking_Crew_(music)) — the LA studio musicians who quietly played on most of the hits of the 60s-70s. Skilled craftspeople who made the star's work better without taking the spotlight. That's the pattern: a deep bench of on-call experts who make *your* work better.

---

## How it works

Each archetype in `personas/` is a **school of thought** exemplified by 2-5 real people whose philosophies genuinely align — not named celebrities. The catalog would be too big otherwise, and "a finance expert" is meaningless when Buffett and Burry think in fundamentally incompatible ways.

- **The Value Investor** (Buffett / Munger / Graham) is one archetype.
- **The Contrarian Short-Seller** (Burry / Chanos) is a different archetype.

Each archetype has a specific *voice* (what they push on), explicit *blind spots* (what they miss), and a "not to be confused with" contrast against adjacent archetypes — so a crew of 4 attacks your work from genuinely different angles without blending into mush.

---

## Install

The Wrecking Crew is a Python package that ships a CLI (`crew`), an MCP server (`crew-mcp`), and a multi-tool installer that fans the slash commands out into every supported agentic tool's user-level commands directory.

```bash
# 1. Install the package (uv recommended; works with pipx too)
uv tool install git+https://github.com/lugnut42/the-wrecking-crew.git
# or: pipx install git+https://github.com/lugnut42/the-wrecking-crew.git

# 2. Detect your tools and install commands + catalog + MCP instructions
crew install

# 3. Verify
crew doctor
```

`crew install` does three things:
- **--commands** writes the 6 slash commands into each detected tool's user dir (`~/.claude/commands/`, `~/.cursor/commands/`, `~/.codex/prompts/`, `~/.codeium/windsurf/workflows/`).
- **--catalog** populates `~/.wrecking-crew/` with the catalog (personas, vocab, indexes, embeddings, graph).
- **--mcp** prints per-tool registration instructions for the MCP server (Claude Code, Codex, Cursor, Windsurf, Antigravity, Cline, Copilot CLI, Zed).

Run individual flags (`crew install --commands` / `--catalog` / `--mcp`) if you want only one part. Use `crew install --target claude-code,cursor` to install for specific tools only.

To update later: `crew update` re-copies the catalog. To remove: `crew uninstall` removes commands; `crew uninstall --purge` also removes `~/.wrecking-crew/`.

### Supported tools

| Tool | Native `/crew` slash command? | How |
|---|---|---|
| Claude Code | yes | Plugin (`.claude-plugin/plugin.json`) + user commands at `~/.claude/commands/` |
| Cursor | yes | User commands at `~/.cursor/commands/` |
| Codex CLI | yes | Prompts at `~/.codex/prompts/` |
| Windsurf | yes | Workflows at `~/.codeium/windsurf/workflows/` |
| Antigravity, Cline, Copilot CLI, Zed | catalog reachable as MCP tool calls | MCP server (`crew-mcp`) registered with the tool |
| VS Code Copilot | partial | Drop `.github/prompts/*.prompt.md` per repo or use the MCP server |

---

## Use

Any time you're working on something and want critics:

```
> [describe what you're working on, or just keep having the conversation]

/crew
```

The agent proposes a crew. Confirm or redirect. Then:

```
/crew-review
```

Round 1 runs. You read 4 independent critiques. Accept Round 2 if you want them to synthesize.

### Other commands

- `/crew-browse` — facet-filtered table of contents (e.g., `function:critic`)
- `/crew-related <slug>` — explore from one archetype outward (contrasts, shared exemplars, semantic neighbors)
- `/crew-audit <domain>` — coverage audit; finds gaps in the catalog
- `/crew-review-archetype <slug>` — review an unreviewed archetype's coherence and quality

### Worked example

End-to-end walkthrough that exercises every journey, including the inline-draft flow when the catalog has a gap: [`examples/stock-ml-use-case.md`](examples/stock-ml-use-case.md).

---

## Contribute an archetype

Two paths:

1. **Let `/crew` draft it.** When `/crew` hits a gap during crew assembly, accept the inline draft. The file is created, validated, and joins the catalog automatically. Open a PR if you want the upstream catalog to have it too.
2. **Write it by hand.** Copy [`TEMPLATE.md`](TEMPLATE.md) into `personas/<slug>.md`, fill it in, run the validator, open a PR.

The format and the **coherence test** (the rule that keeps the catalog from turning into mush) are documented in [`SCHEMA.md`](SCHEMA.md). The full contribution guide is in [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## Design philosophy

- **Archetype over celebrity.** Schools of thought, not famous people. Exemplars calibrate the voice.
- **Coherence over coverage.** Exemplars must share ~80% of first principles. Incoherent blends produce generic critique.
- **Non-overlap is load-bearing.** A crew is useful because its members attack from different angles.
- **Contribution is demand-driven.** Archetypes get added when `/crew` discovers a real gap, not by populating categories.
- **Folder of markdown, not a product.** No tracker, no governance, no workflow engine. Just files, git, and a small set of commands.

---

## Docs

- [`SCHEMA.md`](SCHEMA.md) — archetype file format and the coherence test
- [`TEMPLATE.md`](TEMPLATE.md) — copy-paste template for a new archetype
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to add or improve an archetype
- [`DESIGN.md`](DESIGN.md) — vision, core principles, and decisions on record
- [`examples/stock-ml-use-case.md`](examples/stock-ml-use-case.md) — end-to-end worked example
