# Overlap Analysis: Substrate Repos vs. `atlas` Spec

This document maps each of the four `foolswithtools` repos against the `atlas` specification and recommends how each should be used going forward (incorporate, depend on, port from, or treat as pattern-only reference).

---

## Summary table

| Repo | One-liner | Role in `atlas` | Code action | Spec coverage |
|---|---|---|---|---|
| **`crew`** | Catalog of archetype critics | Home repo + persona system | Build `atlas` inside this repo; persona contract is `crew`'s | §7 Persona system (full) |
| **`crux`** | Federated context graph with edge caching | Reference design for store/RBAC/cache | Lift schema and patterns into Python; rebuild within `atlas` | §4 Store model (full), §5 Ontology shape (partial), §10 Tech architecture (full) |
| **`pwk`/`gpwk`** | Activity-Driven personal work kit | Task kinetics reference | Port markdown slash-commands into `_meta/actions/` | §6 Kinetics — task verbs (full) |
| **`brok`** | Persona-driven content forge | Vault/Provider patterns | Pattern transfer only; no code shared | §10 Provider Registry, §4 Vault separation |

---

## `crew` — the home repo

### What it is

A catalog of **archetype critics** for pressure-testing work in agentic coding tools. Two journeys:
- `/crew` reads what you're working on, proposes 3-4 non-overlapping critics from the catalog (drafts one inline if missing)
- `/crew-review` launches the chosen crew as parallel subagents who critique independently

### What it brings to `atlas`

`atlas`'s `/evaluate-idea` action (SPEC.md §7) is exactly `/crew` + `/crew-review` invoked against an Idea entity with KB context. **The persona system is already built.** The work in `atlas` is wiring it: format the idea + context appropriately, invoke `crew`, capture the verdict as a Decision entity, schedule a 3-month review.

### Specific assets already in `crew`

- `personas/` — 9 archetype critics with the coherence test enforced
- `SCHEMA.md` — the archetype file format
- `TEMPLATE.md` — copy-paste template for new archetypes
- `vocab/{expertise,function,approach}.yml` — controlled vocab for facet filtering (this is also the seed of `atlas`'s domain taxonomy)
- `scripts/build-index.py`, `build-embeddings.py`, `build-graph.py` — derived-artifact builders
- `.claude/settings.json` PostToolUse hook that validates and rebuilds derived artifacts
- An MCP server (`crew-mcp`) for tools that don't speak slash commands
- A multi-tool installer for Claude Code / Cursor / Codex / Windsurf

### Decision: BUILD `atlas` INSIDE `crew`

`atlas` is built as a new package within the `crew` repo. The persona contract is `crew`'s — `atlas` does not maintain its own persona format. New personas authored for evaluation in `atlas` go into `crew/personas/` following `crew/SCHEMA.md`.

The two are not separate things that integrate. They are the same thing.

### Anything to refactor in `crew`?

Likely yes, after Phase 1 is running:
- `crew`'s `vocab/` files are the seed of `atlas`'s `_meta/domains/` controlled vocabularies for signal matching. Decide whether to share the vocab files between the two or keep them separate.
- `crew`'s sqlite-vec embeddings infrastructure should be lifted into `atlas`'s store; today it's only used over personas.
- If `atlas` grows large, refactor the directory layout so `crew` (the persona catalog) and `atlas` (the app) are clear sibling packages.

---

## `crux` — the store design reference

### What it is

A context-delivery system for AI agents. Single source of truth that serves enterprise knowledge to any AI agent in the most token-efficient way possible. Hierarchical retrieval (Index → Summary → Full Document), edge-cached, RBAC via ghost routing, telemetry, plugin connectors. Two Go binaries (`hub`, `cx`) + SQLite/Postgres.

### What it brings to `atlas`

`crux` has **already designed and built** the store layer `atlas` needs:

| `atlas` need | `crux` provides |
|---|---|
| Single-schema dual-runtime (SQLite personal, Postgres team) | Yes, with documented compatibility differences |
| Type-discriminated entities + JSON properties | Yes (`nodes` table with `node_type` discriminator) |
| Typed relationships in adjacency list | Yes (`edges` table with `relationship` type) |
| Recursive graph traversal | Yes (`WITH RECURSIVE` CTEs, documented in `docs/DATA_MODEL.md` §5) |
| RBAC | Yes (ghost routing — `access_role` filtered at every level, no 403) |
| Edge cache with ETag/content hash | Yes (in `cx` CLI, `~/.crux/cache.db`) |
| FTS5 + vector search | Yes |
| Telemetry / audit log | Yes (append-only `agent_telemetry` and `agent_reports` tables) |
| Plugin architecture for external sources | Yes (Git, SharePoint, ServiceNow, Archer) |
| Self-healing background jobs | Yes |

### Architectural conflicts to resolve

| Topic | `crux` stance | `atlas` stance |
|---|---|---|
| MCP vs CLI | Rejected MCP (token cost); CLI-only | Dual MCP + CLI (see DECISIONS.md) |
| Language | Go (single binary, no CGO) | Python (matches ecosystem) |
| Schema scope | Context documents (Index/Summary/Full) | Life entities (Person/Project/Signal/Task/etc.) |

### Decision: INSPIRE-ONLY (lift schema, rebuild in Python)

`atlas` does **not** depend on `crux`. The schema and patterns are too valuable not to lift, but the language mismatch and the schema-scope mismatch mean a rebuild is cleaner than a fork.

What to lift, in order of priority:

1. **The DDL.** `crux/docs/DATA_MODEL.md` §3 is the starting point for `atlas`'s schema. Adapt for `atlas`'s entity types (Person, Project, Signal, etc. instead of Index/Summary/Full).
2. **Ghost routing.** `access_role` filtered at every recursion level. Lift the SQL pattern directly.
3. **Edge cache with ETag.** When `atlas`'s side-gig store is remote, the personal `atlas` CLI/MCP server caches locally with content-hash invalidation.
4. **Hierarchical retrieval.** For long-form Note content, store Index/Summary/Full tiers so agents drill down only when needed. This is the same token-economics insight crux is built on.
5. **Plugin architecture.** When `atlas` integrates with external sources (Gmail, calendar, GitHub, banks), the plugin-with-sync-tick pattern from `crux/internal/plugin/` is the right shape.
6. **OpenTelemetry from day 1.** `crux` has it. Don't bolt observability on later.
7. **Test patterns.** `crux/.claude/rules/testing.md` is gold — table-driven tests with in-memory SQLite. Steal verbatim (translated to pytest).
8. **`docs/BUILDING_WITH_CLAUDE_CODE.md`** describes how `crux` was built with Claude Code. Read before starting `atlas`.

What to NOT lift:
- The Go code itself
- The CLI-only stance (`atlas` has dual MCP + CLI)
- The hierarchical Index/Summary/Full as the *primary* entity model — `atlas`'s primary entities are typed (Person, Project, etc.). Hierarchical retrieval is an *optional* refinement for long-form notes.
- The web portal for domain owners — single-user `atlas` doesn't need it; multi-user `atlas` might.

### `crux` stays as a standalone repo

`crux` continues to exist as the Go-based enterprise context-delivery system. If the user (or anyone else) needs a real institutional Single Brain at scale, `crux` is the substrate to deploy. `atlas` and `crux` are siblings, not parent/child.

---

## `pwk` / `gpwk` — the kinetics reference

### What it is

Two productivity systems for Claude Code built on **Activity-Driven Development**: captured activities become the source of truth for planning, breakdown, execution.
- **PWK**: local markdown, single-device, offline
- **GPWK**: GitHub Issues backend, multi-device, hybrid

Both share a slash-command set: `/capture`, `/plan`, `/triage`, `/breakdown`, `/delegate`, `/complete`, `/search`, `/review`, `/carryover`, `/principles`.

### What it brings to `atlas`

`pwk` is **most of `atlas`'s kinetics layer for tasks**, already designed and battle-tested with a coherent philosophy:

- **Capture First** — log activities as they happen, process later → matches `atlas`'s "Capture is frictionless; promotion is deliberate" principle (SPEC.md §3.7)
- **Carryover, Not Carry Burden** — unfinished work flows forward → matches `atlas`'s decay/lifecycle approach for open loops
- **Breakdown for Clarity** — complex work becomes actionable through decomposition → directly relevant to Project/Task entity relationships
- **Hybrid Execution** — `[P]` (personal) vs `[AI]` (AI-delegatable) tasks → maps to `atlas`'s human-vs-agent action distinction
- **Principles Over Productivity** — user's work style governs, not external dogma

### Decision: PORT THE SLASH-COMMAND MARKDOWN INTO `atlas`'s `_meta/actions/`

The action specs (markdown that doubles as prompts) for the task-management subset of `atlas`'s kinetics are mostly already written. Port:

| `pwk` command | `atlas` action |
|---|---|
| `/gpwk.capture` | `/capture` |
| `/gpwk.plan today\|week` | `/morning-brief` (rename, expand) |
| `/gpwk.triage` | `/process-inbox` |
| `/gpwk.breakdown` | (part of `/start-project`) |
| `/gpwk.delegate` | (used internally by agent layer) |
| `/gpwk.complete` | `/close-task` |
| `/gpwk.search` | (handled by MCP search tools) |
| `/gpwk.review` | `/weekly-review` |
| `/gpwk.carryover` | (handled by nightly lint agent) |
| `/gpwk.principles` | (lives in `_meta/policies/`) |

The **task notation** (`[P]`/`[AI]` markers, `!high`/`!medium`/`!low` priority, `~deep`/`~shallow`/`~quick` energy) is good — adopt as-is, it works with voice capture.

The **knowledge capture workflow** (`pwk:ai` + `pwk:knowledge` labels → WebSearch + structured doc creation) is a useful pattern for `atlas`'s `/find-context` and for "fill in the gaps in the KB" agent runs.

The **`pwk:c1/c2/c3` carryover labels** (tracks incomplete-task duration) are the same idea as `atlas`'s signal decay — same pattern, different entity type. Reuse.

### What to NOT port from `pwk`

- GitHub Issues as the storage backend. `atlas`'s storage is its own SQLite/Postgres. `pwk`/`gpwk` users coming to `atlas` should think of it as a richer evolution, not a refactor.
- The strict GPWK split between local logs and remote tasks — `atlas` has identity-scoped stores that handle both concerns more cleanly.
- The PWK-only and GPWK-only variants — `atlas` has the architectural pattern (`one interface, many stores`) that subsumes both modes.

### `pwk` stays as a standalone repo

`pwk` continues to serve the simpler use case: lightweight task management in any Claude Code project. People who don't want a full ontology stack can use it. `atlas` is the next level up for people who do.

---

## `brok` — the pattern reference

### What it is

A terminal-based engine that transmutes raw content (video, audio, documents, notes) into persona-perfect output. Universal Intake → semantic chunks → Persona Refiner → deterministic Linter → TUI review → output assembly. Three Pillars architecture: **Engine** (installed package) / **Soul** (`vault/`) / **Factory** (`workspace/`).

### What it brings to `atlas`

`brok` is **not directly reused** but contains several patterns `atlas` should adopt:

1. **Three Pillars separation.** Engine (code) / Soul (user data) / Factory (transient). Maps directly to `atlas`:
   - `atlas` code = Engine (installed Python package)
   - Store directory = Soul (per-store vault with ontology, data, notes)
   - Inbox / scratch / checkpoint files = Factory
   The separation makes deployment, upgrades, and exit clean.

2. **Provider Registry pattern.** `brok/src/brok/providers/` has a capability-based routing system (`TEXT_GEN`, `IMAGE_GEN`, `TRANSCRIPTION`) with thin adapters (~50-100 lines each) for Anthropic, OpenAI, Google, Bedrock, Ollama, Whisper local/cloud. Provider SDKs are optional extras — only what's configured is installed. **`atlas` needs the same abstraction** (tiered models for cost control: Haiku for classification, Sonnet for synthesis, transcription for capture). Lift the pattern; rewrite slim.

3. **Memory Ledger with correction pairs.** `brok/src/brok/memory/ledger.py` captures user corrections, retrieves them at refinement time, auto-promotes patterns. This is conceptually `atlas`'s "promote from stub to typed entity" loop. The pattern is similar but the data is different; the *idea* of typed correction pairs that the system learns from is what `atlas` should adopt for ontology evolution.

4. **Pydantic v2 for all data models.** `brok` uses Pydantic for the entire data layer. `atlas` should do the same — it gives free validation, JSON serialization, and schema documentation. Aligns with the `_meta/entities/` markdown specs.

5. **Persona profile YAML.** `brok` distinguishes:
   - **Voice persona** (the writing style — `vault/personas/{name}/profile.yaml`)
   - vs. `crew`'s **critic persona** (the evaluative archetype)
   These are different things and `atlas` should keep them distinct. `atlas`'s `/evaluate-idea` uses `crew` personas. Future `atlas` features that *generate* content in the user's voice (e.g., draft a reply to a colleague) would use `brok`-style voice personas. **Don't conflate them.**

6. **Textual TUI for review flows.** `brok`'s Director's Gate uses Textual. If `atlas` builds an interactive review flow (e.g., for `/process-inbox`), Textual is the right choice. But probably not Phase 1.

7. **`uv` for package management, `ruff` for lint/format.** `atlas` should adopt the same conventions for consistency across the `foolswithtools` Python codebases.

8. **No em-dashes rule.** `brok/CLAUDE.md` enforces no em-dashes (—) or en-dashes (–) anywhere in code or docs. This is a strong stylistic choice that matches the `foolswithtools` voice; `atlas` should adopt it.

### Decision: PATTERN TRANSFER ONLY

`atlas` does not depend on `brok`. The patterns above are lifted as design choices, not as code. `brok`'s pipeline (intake → atomic parse → persona refiner → linter → assembly) is specific to *content generation* and is not what `atlas` does.

### `brok` stays as a standalone repo

If the user ever wants to generate persona-perfect content from `atlas`'s KB (e.g., "draft a blog post from these decisions"), `brok` is the tool to invoke. The integration is "atlas exports a structured input to brok and brok produces the artifact." Not in scope for Phase 1.

---

## Cross-cutting overlaps

### Personas: `brok` (voice) vs `crew` (critic) — KEEP SEPARATE

These are genuinely different concepts that share a word. `atlas` references both:
- **`crew` personas** = critics for `/evaluate-idea`
- **`brok` personas** = voice for content generation (not Phase 1)

Don't unify the formats. Both repos have good schemas for their respective purposes.

### Controlled vocabularies: `crew/vocab/` vs `atlas/_meta/domains/`

`crew/vocab/` has SKOS (Simple Knowledge Organization System) within-facet + cross-facet vocabs for `expertise`, `function`, `approach`. These are facets for filtering personas.

`atlas/_meta/domains/` would have controlled vocabs for matching signals to solutions (e.g., `identity_management`, `cloud_security`).

These serve different purposes. **Keep separate** but use the same file format and tooling. Possibly share the `validate.py` / `build-index.py` scripts between them.

### Audit logging: `crux/agent_telemetry`, `crew/.crew/usage.log`, `atlas/events`

All three have an append-only event/usage log. Lift `crux`'s schema for `atlas/events` since it's the most general-purpose. Keep `crew`'s usage log specific to persona invocation (it has its own analytics).

### CLI vs MCP

| Repo | Surface | Reason |
|---|---|---|
| `crux` | CLI only | Token cost of MCP schema injection |
| `crew` | Both (CLI commands + `crew-mcp`) | Different tools have different capabilities |
| `pwk` | Slash commands (which are MCP-adjacent in Claude Code) | Native Claude Code integration |
| `brok` | CLI only | Standalone tool |
| `atlas` | **Both** (MCP primary, CLI for headless/automation) | Best of both — see DECISIONS.md |

### Provider abstraction

| Repo | Provider abstraction |
|---|---|
| `brok` | Full Provider Registry with capability routing |
| `crux` | None (it doesn't call LLMs directly) |
| `crew` | None (relies on the host agent's LLM) |
| `pwk` | None (slash commands run in host agent) |
| `atlas` | **Needs one** — lift pattern from `brok` |

---

## What's still uncovered (gaps `atlas` must fill from scratch)

1. **Email ingestion pipeline at scale.** Nothing in the four repos does this. Gmail Takeout parse → batch load → entity extraction → embedding generation. The single biggest piece of net-new work in Phase 1.

2. **Signal ↔ Solution matching across time.** `crux` has the graph substrate, `crew` has matching for personas, but the cross-time match-and-notify pattern for life signals doesn't exist anywhere.

3. **Telegram capture + Whisper transcription.** No surface for voice in any of the repos.

4. **Multi-store federation in the interface.** "One interface, many stores" doesn't exist anywhere. `crux` has multi-tenancy but for one hub.

5. **Decay/lifecycle on signals and open loops.** `crux` has staleness for context nodes; `pwk` has `c1/c2/c3` for tasks. Neither has it for signals.

6. **Identity scoping.** No repo has the multi-identity model. Has to be designed from day 1.

7. **`/morning-brief` synthesis.** Cross-entity, cross-source daily synthesis. Pattern is novel.

8. **Conflict detection on entity property updates.** "This person's birthday was 1986-08-14; you're now saying May 20." No repo does this.

---

## TL;DR for the next session

- **Build `atlas` inside `crew`.** Don't make a new repo.
- **Port `pwk`'s slash-command markdown** into `atlas`'s actions layer on day 1. ~½ day of work.
- **Read `crux/docs/DATA_MODEL.md` and `crux/docs/TECH_SPEC.md`** before writing the schema. Lift the SQL.
- **Use `crew` directly** for persona-driven `/evaluate-idea`. No need to build another persona system.
- **Adopt `brok`'s Three Pillars naming** for vault/workspace separation and the Provider Registry pattern.
- The gaps (email ingestion, signal matching, multi-identity, decay) are the genuine net-new work and where Phase 1's design effort should concentrate.
