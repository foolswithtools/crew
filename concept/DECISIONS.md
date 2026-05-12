# Architectural Decisions

Decisions locked in during framing. Every one is **revisitable in the next session before code is written** — they're flagged here so the next session can challenge them deliberately rather than discover them as assumptions later.

If a decision is changed, the changes propagate. The "What changes if revisited" section on each is honest about that.

---

## D1 — Build `atlas` *inside* the `crew` repo

**Decision:** `atlas` is a new package within the `crew` repo, not a separate repo.

**Rationale:**
- `crew` is the persona system that `atlas`'s `/evaluate-idea` action requires. They are not adjacent components; they're the same thing.
- One person maintaining two coupled repos is harder than maintaining one repo with two packages.
- The Python ecosystem (`crew`, `brok` patterns) outweighs the Go substrate (`crux`) for the orchestrator.
- If `atlas` outgrows `crew`, splitting is a refactor, not an architectural change.

**What changes if revisited:**
- If split into own repo: package management gets thorny (`atlas` depends on `crew` as a library); shared CI; shared docs structure; harder to evolve the persona contract.
- The build plan in `BUILD-PLAN.md` Week 1 assumes the package layout `crew/atlas/` or `crew/src/atlas/`. Splitting means a different starter sequence.

**Status:** locked. Revisit if `atlas`'s install footprint conflicts with `crew`'s pip distribution.

---

## D2 — Dual MCP + CLI agent surface

**Decision:** `atlas` exposes both an MCP server (primary, for Claude Code and other MCP-compatible clients) and a thin CLI (for headless automation, cron jobs, and token-cheap invocation). Both wrap the same Python store/actions library.

**Rationale:**
- The Lifebase spec was MCP-first (Claude Code ergonomics).
- `crux` explicitly rejected MCP for token-cost reasons (MCP schema injection is 40k+ tokens).
- Both stances are right in their context:
  - MCP is ergonomic when the agent is already in an MCP-aware session (Claude Code) where the schema is amortized over many tool calls.
  - CLI is token-cheap when the agent invokes one action per session, or when the caller is a non-MCP system (cron, GitHub Action, etc.).
- A single source-of-truth library wrapped by both surfaces lets each be used where appropriate.

**What changes if revisited:**
- MCP-only: simpler codebase; loses headless automation efficiency; loses interop with non-MCP tools.
- CLI-only (match `crux`): worse Claude Code UX; agents must shell out for every action; loses MCP's first-class tool discovery.
- Both is more code to maintain. The wrapper layer must be thin or the surfaces drift.

**Status:** locked. Revisit if maintaining both becomes a burden.

---

## D3 — Python as the implementation language

**Decision:** `atlas` is written in Python.

**Rationale:**
- The home repo (`crew`) is Python.
- `brok` is Python; its patterns are directly liftable (Provider Registry, Pydantic models, Three Pillars layout).
- `pwk` slash commands are markdown — language-neutral.
- Only `crux` is Go. Its DDL is portable; the patterns are portable; only the implementation code is not. Lifting the schema into Python is straightforward.
- Python has the ecosystem `atlas` needs: Pydantic v2, FastAPI (if a web UI is built), sqlite-vec, pgvector, sentence-transformers, mbox parsers, Whisper bindings, MCP SDKs, the Anthropic SDK.
- `uv` makes Python feel close to Go's single-binary distribution for end users.

**What changes if revisited:**
- Go: gain single-binary distribution and `crux` reuse; lose `crew`/`brok` ecosystem interop; lose Python ML libraries for embeddings.
- Polyglot (Go store + Python orchestrator): pays for an extra process; harder to debug; nobody likes IPC.
- TypeScript/Node: not seriously considered. No ecosystem alignment.

**Status:** locked. Revisit only if Phase 1 reveals a Python-specific bottleneck.

---

## D4 — `crux` is inspire-only, not a dependency

**Decision:** `atlas` lifts `crux`'s DDL, ghost-routing pattern, edge-cache concept, and hierarchical-retrieval idea into Python — but does not depend on `crux` as a library, service, or fork.

**Rationale:**
- Language mismatch (Go vs Python) makes a dependency awkward.
- Schema scope mismatch (`crux` models *context documents*; `atlas` models *life entities*) means the schemas diverge in meaningful ways anyway.
- `crux`'s domain (enterprise context delivery) is genuinely different from `atlas`'s (personal data fabric); each is better as its own product.
- The patterns in `crux/docs/` are well-documented and easy to re-implement.

**What changes if revisited:**
- Fork `crux` and extend: takes on Go maintenance burden in a Python project; awkward.
- Vendor `crux` as a sidecar (run the Go hub, `atlas` calls REST): adds a process; complicates deployment; loses the "single Python service" simplicity.
- Use `crux` enterprise-side when `atlas` Phase 3 institutional-store comes up: this is the *intended future state*; `crux` and `atlas` can be siblings indefinitely.

**Status:** locked. Revisit when Phase 3 begins — at that point, evaluating whether to plug a real `crux` hub in as the institutional-store backend is worth doing.

---

## D5 — `pwk` slash-commands ported as `atlas` actions

**Decision:** Port the markdown slash-command files from `pwk/gpwk/.claude/commands/gpwk.*.md` into `atlas`'s `_meta/actions/` directory, renamed without the `gpwk.` prefix.

**Rationale:**
- The action specs (markdown that doubles as prompts) for task management are already well-designed in `pwk`.
- The "Activity-Driven Development" philosophy is exactly what `atlas`'s SPEC.md §3 principles describe in different words.
- The task notation (`[P]`/`[AI]`, `!high`/`~deep`) is good — works with voice capture and matches `atlas`'s human-vs-agent distinction.
- Porting markdown is a half-day of work; designing equivalents from scratch is a week.

**What changes if revisited:**
- Designing fresh: more work, no clear benefit beyond stylistic alignment with the rest of `atlas`.
- Forking `pwk` and using it directly: `pwk`'s GitHub-Issues backend conflicts with `atlas`'s SQLite/Postgres store. Better to lift the prompts than the storage.

**Status:** locked. The port is a Week-2 task in `BUILD-PLAN.md`.

---

## D6 — Identity is a first-class concept from day 1

**Decision:** Every entity and source has an `identity_id` column from the very first schema, even in Phase 1 when there's only one identity (`personal`).

**Rationale:**
- The multi-identity stress-test scenario (CONVERSATION-CONTEXT.md scenario 5) showed that retrofitting identity scoping later is enormous work.
- The cost of adding the column from day 1 is one column.
- Defaulting `identity_id = 'personal'` everywhere in Phase 1 means it just works until Phase 2 needs it.

**What changes if revisited:**
- Skipping it now means a painful migration in Phase 2.
- No good reason to skip it.

**Status:** locked. No realistic challenge.

---

## D7 — Provenance is mandatory on all data

**Decision:** Every property of every entity carries `source`, `timestamp`, and `confidence`. Every modification to an entity writes an event to the `events` table.

**Rationale:**
- The birthday-recurring-reminder scenario (CONVERSATION-CONTEXT.md scenario 2) showed conflict detection is impossible without provenance.
- The signal-matching scenario showed that decay and trust scoring depend on provenance.
- Auditability of agent actions requires provenance.
- Without it, debugging "where did this fact come from?" becomes impossible after a month.

**What changes if revisited:**
- Skipping provenance saves table columns; loses every capability that depends on it.
- No good reason to skip it.

**Status:** locked.

---

## D8 — Capture is frictionless; promotion is deliberate

**Decision:** Captures (voice notes, web clips, inbox items) land as low-confidence stubs or in an unprocessed inbox. Promotion to typed, structured entities is a separate, deliberate step — either by an agent acting in scheduled mode or by the user explicitly approving.

**Rationale:**
- Voice capture in a walk-back-from-meeting scenario can't tolerate a "let me ask you 4 questions about that" interaction.
- Schema validation at capture time means rejecting captures or fabricating defaults; both are bad.
- The Karpathy LLM Wiki pattern works because raw sources are immutable and the wiki layer is what's curated.
- The "unstructured properties get promoted to typed properties after they appear repeatedly" pattern (CONVERSATION-CONTEXT.md scenario 2 fix) is the right way to evolve the schema from usage.

**What changes if revisited:**
- Strict-at-capture: more friction; loses the use case.
- Permissive-everywhere: rapid schema rot.

**Status:** locked.

---

## D9 — Reversibility via git for store contents

**Decision:** Every `atlas` store is also a git repository. Agent actions that modify markdown notes commit with a structured message. Database changes write to the `events` log. Reversibility window is 24 hours by policy.

**Rationale:**
- Karpathy LLM Wiki v2 pattern: provenance + reversibility + supersession of stale claims.
- Git is free and tools already understand it.
- For database changes, the event log is the audit trail; a separate "undo" action can replay inverse operations within the window.

**What changes if revisited:**
- Skip git: lose human-readable diff of changes; lose easy backup.
- Skip event log: lose ability to reverse DB changes.

**Status:** locked.

---

## D10 — External actions require explicit human approval

**Decision:** No agent may send email, post to Slack, create a ticket, make a payment, or otherwise change external state without an explicit human approval step. Drafts are always allowed; sends never auto-execute.

**Rationale:**
- The OpenClaw / Lemonade Insurance cautionary tale (CONVERSATION-CONTEXT.md): an agent autonomously started an adversarial exchange with an insurance company based on a misinterpreted instruction.
- The blast radius of an autonomous external action is large and often irreversible.
- The benefit of approval is small (one tap) compared to the cost of a wrong send.

**What changes if revisited:**
- Auto-send for "safe" actions: defining "safe" is the hard part. Skip.

**Status:** locked. Hard constraint, not a default.

---

## D11 — `_meta/actions/` are markdown files, not code

**Decision:** Action specs live as markdown files in `_meta/actions/`. Each file describes inputs, steps, validation rules, trust level, and audit requirements. The Python store/actions library *reads* these and executes them; the markdown is the canonical contract.

**Rationale:**
- Markdown actions are git-diffable, reviewable, and modifiable by humans without recompiling.
- Symphony's "the workflow is in the repo" pattern works for the same reason.
- `pwk`'s slash commands work this way; `crew`'s slash commands work this way; `atlas` should be consistent.
- Agents (Claude Code) can author and refine action specs without writing code.

**What changes if revisited:**
- Actions-as-Python: more rigid; harder to version with the data; loses the "skill markdown" pattern.

**Status:** locked.

---

## D12 — `crew` is the persona system; `atlas` does not maintain its own

**Decision:** `atlas`'s `/evaluate-idea` action invokes `crew`. Personas authored for `atlas`-style evaluations go in `crew/personas/` following `crew/SCHEMA.md`. No `atlas`-specific persona format.

**Rationale:**
- `crew` already has a coherent persona catalog with the coherence test enforced, validation scripts, derived artifacts, embeddings, and multi-tool installation.
- Building a parallel persona system in `atlas` would be wasted effort and create drift.
- The `crew` schema is good — it's the right level of structure for this purpose.

**What changes if revisited:**
- `atlas`-specific personas: more flexibility; double-maintenance; eventual drift.

**Status:** locked.

---

## D13 — Sentinel for the unsolved problems (deferred decisions)

Things the framing **deliberately did not decide**, to be settled in the next session before the relevant code is written:

| Question | When it needs an answer | Default if forced |
|---|---|---|
| Specific Postgres host for Phase 2 | Phase 2 kickoff | Self-hosted on small VPS (Hetzner/DigitalOcean) |
| Embedding model | Week 3 (entity extraction needs embeddings) | sqlite-vec + `sentence-transformers/all-MiniLM-L6-v2` (matches `crew`) |
| Transcription approach | Week 4 (Telegram bot needs transcription) | Local Whisper via `faster-whisper` (matches `brok`); API fallback |
| Auth library for Phase 2 | Phase 2 kickoff | passkeys via `webauthn` library |
| Web UI framework | Phase 1 Week 5 if a web UI is built | Datasette first (free); FastAPI + HTMX if more needed |
| Action spec format | Week 1 | Markdown with YAML frontmatter; consider Anthropic Skill format later |
| `crew/atlas/` vs `crew/src/atlas/` package layout | Week 1 | `crew/src/atlas/` (matches modern Python packaging) |
| Whether MCP server is `atlas-mcp` separate command or merged into `crew-mcp` | Week 2 | Separate command, both shipped from this repo |
| Whether to vendor `pwk` slash-commands or port them | Week 2 | Port (D5 above) |
| Telegram bot framework | Week 4 | `python-telegram-bot` |

---

## Style decisions (locked)

These are small but propagate everywhere.

- **No em-dashes or en-dashes in code or docs.** Lifted from `brok/CLAUDE.md`. Use hyphens in prose, colons in labels. Hard rule for `atlas`. *(This document follows the rule. The substrate-repo docs vary.)*
- **`uv` for package management, `ruff` for lint/format, `pytest` for testing.** Matches `brok`/`crew` conventions.
- **Pydantic v2 for all data models.** Matches `brok`.
- **Type hints everywhere.** Strict mode.
- **Commit style matches `crew` repo convention.** Includes `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` trailer on AI-assisted commits, mirroring the existing `crew` history.

---

## Updates log

| Date | Change |
|---|---|
| 2026-05-12 | Initial framing decisions captured by Claude in handoff session |
