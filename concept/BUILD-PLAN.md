# Build Plan: `atlas` Phase 1

Sequenced plan for Phase 1 (months 1-3). The goal: a working personal `atlas` you've used for 6+ weeks of daily life by end of Phase 1.

This plan assumes the decisions in `DECISIONS.md` and the substrate strategy in `OVERLAP.md`.

---

## Pre-build (before Week 1)

These are framing tasks; do them before writing code.

1. **Read** `SPEC.md`, `OVERLAP.md`, `DECISIONS.md`, `CONVERSATION-CONTEXT.md` end-to-end.
2. **Read** `crux/docs/DATA_MODEL.md` and `crux/docs/TECH_SPEC.md` for schema/architecture lift.
3. **Read** `brok/docs/architecture.md` and `brok/docs/decisions.md` for the Three Pillars and Provider Registry patterns.
4. **Read** `crew/SCHEMA.md` and `crew/DESIGN.md` to confirm the persona contract.
5. **Read** `pwk/CLAUDE.md` and a few of the `.claude/commands/gpwk.*.md` files to see the action spec format you'll be porting.
6. **Pick a name** (see `NAMES.md`).
7. **Lock or revise** any decisions in `DECISIONS.md`.
8. **Decide package layout**: `crew/<name>/` vs `crew/src/<name>/`. Recommend `crew/src/atlas/` to match modern Python packaging.

Time: half a day of focused reading.

---

## Week 1 — Schema, migrations, core data-access library

**Goal:** SQLite schema running locally with the seven core entity types definable. A Python library that can read/write entities, relationships, sources, events.

### Tasks

1. **Create package skeleton.**
   - `crew/src/atlas/` (or chosen path)
   - `pyproject.toml` updated with `atlas` as a sub-package (or new `pyproject.toml` if separating)
   - `uv sync --extra dev` works
   - Base `cli.py` runs `atlas --version`

2. **Lift the schema.** Start from `crux/docs/DATA_MODEL.md` §3 DDL. Adapt:
   - Replace `domains`, `context_nodes`, `graph_edges` tables with `entities`, `relationships`, `events`, `sources`, `source_entities` (see `SPEC.md` §5).
   - Add `identity_id` column on `entities` and `sources` (D6).
   - Keep `access_role` on `entities` for future RBAC (Phase 2+).
   - Keep the audit/telemetry pattern.
   - Embed DDL with Go-style `embed` (Python: store as `.sql` files alongside, load with `importlib.resources`).

3. **Migration system.** Simple forward-only migrations. Use a `schema_migrations` table that records applied migrations. No need for Alembic in Phase 1; a few hand-rolled migration files is enough.

4. **Pydantic models for each entity type.** One model per type, validated against the entity spec in `_meta/entities/`. Models serialize to/from the `properties` JSON column.
   - `Person`, `Project`, `Task`, `Decision`, `Signal`, `Solution`, `Source`, `Note`, `Idea`, `Reminder`, `AgentRun`
   - Use Pydantic v2 (matches `brok`).
   - Each model has `to_db_row()` and `from_db_row()` helpers.

5. **Data-access layer.**
   - `atlas/store/sqlite.py` — connection management, WAL mode (lift from `crux/.claude/rules/sqlite.md`), prepared statements
   - `atlas/store/entities.py` — CRUD for entities
   - `atlas/store/relationships.py` — CRUD for relationships
   - `atlas/store/sources.py` — CRUD for sources
   - `atlas/store/events.py` — append-only event log
   - All methods take `context.Context`-equivalent (Python: pass explicit `connection` or use a context-manager pattern).

6. **Entity specs as markdown.** Write `_meta/entities/person.md`, `project.md`, `task.md`. Each defines required/optional properties, required sections, linking rules, agent rules (see `SPEC.md` §5 sketch).

7. **Three Pillars layout.** Adopt `brok`'s split:
   - `crew/src/atlas/` = Engine (code)
   - `~/atlas/<store-name>/` = Soul (per-store vault)
   - `~/atlas/<store-name>/workspace/` = Factory (transient inbox, checkpoints)

8. **CLI: `atlas init <store-name>`**. Scaffolds a new store directory with `store.yaml`, `_meta/` skeleton, empty SQLite DB.

9. **Testing.** Lift `crux/.claude/rules/testing.md` patterns (table-driven, in-memory SQLite). Get the data-access layer to 80% coverage.

### Deliverables
- `atlas init personal` works
- `atlas list-entities --type=person` returns empty list
- `atlas add-person --name "Test User"` adds and returns the entity
- `pytest tests/` passes

---

## Week 2 — Action specs, slash commands, MCP server skeleton

**Goal:** The kinetics layer wired up. Slash commands port from `pwk`. MCP server exposes core tools.

### Tasks

1. **Port `pwk` slash commands** into `_meta/actions/` (D5):
   - `/capture` (from `/gpwk.capture`)
   - `/morning-brief` (from `/gpwk.plan today`)
   - `/process-inbox` (from `/gpwk.triage`)
   - `/close-task` (from `/gpwk.complete`)
   - `/weekly-review` (from `/gpwk.review`)
   - Adapt the task notation (`[P]`/`[AI]`, `!high`, `~deep`) — keep as-is.
   - These are markdown files; the agent reads them. No code yet.

2. **Action executor.** Python code that:
   - Reads an action spec from `_meta/actions/<name>.md`
   - Validates inputs
   - Records a `proposed_action` event
   - Returns a structured proposal to the caller
   - On `execute_action()`, runs the steps, validates output, records `executed_action` event, returns result

3. **First three executable actions:**
   - `add_person(name, relationship?, ...)`
   - `add_task(title, project?, owner?, ...)`
   - `log_interaction(person_id, summary, source?)`

4. **MCP server skeleton.** Use the official MCP Python SDK.
   - Tools exposed (per `SPEC.md` §8): `search_entities`, `get_entity`, `list_relationships`, `create_entity`, `propose_action`, `execute_action`
   - Configuration file (`~/.atlas/config.yaml`) declares which stores the server knows about
   - Server runs as a daemon (launchd plist on macOS, systemd unit on Linux)

5. **Claude Code integration.** Register the MCP server in `~/.claude/mcp.json`. Verify Claude Code can call `atlas`'s tools.

6. **Thin CLI for parity.** Each MCP tool has a corresponding `atlas <verb>` command. Both surfaces share the same Python library underneath.

### Deliverables
- In Claude Code: invoke `/atlas:capture "Met Marcus today, his birthday is May 20"` and see the entity created
- From terminal: `atlas search-entities --type=person --query=Marcus` returns the entity
- Both wrote identical event log rows

---

## Week 3 — Email ingestion pipeline

**Goal:** Years of Gmail backfilled into the personal store. Entity extraction running over the backlog. This is the single biggest piece of net-new work.

### Tasks

1. **Gmail Takeout export.** User runs Google Takeout, gets a folder of `.mbox` files. Decision: archive only, never two-way sync with Gmail.

2. **mbox parser.** Python's `mailbox.mbox` walks each file. For each message:
   - Extract headers (From, To, Cc, Subject, Date, Message-ID)
   - Extract body (text + HTML parts)
   - Save attachments to `~/atlas/<store>/data/raw/email/attachments/<message-id>/`
   - Insert into `sources` table with `type='email'`, `message_id`, full content, identity_visibilities, ingested_at

3. **Dedup.** RFC 5322 Message-ID handles multi-identity duplicates (the same email arriving at personal and side-gig accounts).

4. **Entity extraction agent.** A Python script that:
   - Pulls a batch of unprocessed sources from `sources` where `processed=0`
   - For each, prompts Haiku with: the email + the ontology spec + existing entity names that might match (for resolution)
   - Returns structured output: list of `EntityCandidate(type, name, properties, confidence, supporting_quote)` and list of `RelationshipCandidate`
   - Upserts entities (resolving against existing by name + context)
   - Inserts `source_entities` links with confidence and context quotes
   - Marks source `processed=1`
   - Logs cost and quality metrics

5. **Provider Registry.** Lift the pattern from `brok/src/brok/providers/`. Slim version: just `TEXT_GEN` capability, adapters for Anthropic (Haiku and Sonnet). Add OpenAI/Bedrock/Ollama later as needed.

6. **Embedding generation.** For each email, generate an embedding using sentence-transformers (default per `DECISIONS.md` D13). Store in `source_embeddings` (sqlite-vec). Skip emails under ~50 words or pure newsletter content (heuristic).

7. **FTS5 indexing.** Populate `sources_fts` for full-text search.

8. **Progress tracking.** A `atlas ingest-email --batch=500` command shows progress (X / Y messages processed, $ spent, % complete). Resumable. Can be interrupted.

9. **Test on a small sample first.** Process 100 emails, manually review the extracted entities. Tune the prompt. Then run on the full backlog.

### Deliverables
- `~/atlas/personal/data/raw/email/` contains the mbox archives
- `sources` table has one row per email
- `entities` table is populated with people, projects, organizations extracted from the mail
- `source_entities` links each extracted entity to the supporting email(s)
- Embeddings populated
- Cost summary: total $ spent on backfill

### Realistic cost
- 100K emails at ~$0.003 per email with Haiku ≈ $300 one-time
- Cheaper with batching and careful prompting

---

## Week 4 — Telegram capture + Whisper transcription

**Goal:** Voice notes, text, photos drop into the inbox from your phone. The `/capture` action processes them.

### Tasks

1. **Telegram bot.** Use `python-telegram-bot`. Bot does:
   - Receives voice notes → saves to `~/atlas/personal/data/raw/inbox/<timestamp>-voice.ogg`
   - Receives text → saves to `~/atlas/personal/data/raw/inbox/<timestamp>-text.md`
   - Receives photos → saves to `~/atlas/personal/data/raw/inbox/<timestamp>-photo.jpg`
   - Replies "Captured, processing"
   - Per-store bots (one bot for personal, separate bot for side-gig later)

2. **Whisper transcription.** Use `faster-whisper` with local model. Transcribes voice notes; saves transcript next to the audio.

3. **Inbox watcher daemon.** Watches `~/atlas/personal/data/raw/inbox/`. For each new file:
   - If audio: transcribe
   - Classify intent (idea, fact, task, signal, capture-only) with Haiku
   - Invoke the appropriate action (`/log-idea`, `/add-task`, `/log-signal`, or just `/capture` if generic)
   - Move processed files to `~/atlas/personal/data/raw/inbox/processed/`

4. **Bot reply with classification.** After processing, the bot replies: "Logged as Idea: 'Chrome extension for paywalls.' Reply to refine or `/reclassify` to change."

5. **Disambiguation flow.** When an entity name is ambiguous (3 Marcuses), the bot asks one question with quick-reply buttons.

### Deliverables
- Telegram bot running
- Voice note → entity creation works end-to-end
- The `/capture` action handles all four media types

---

## Week 5 — Scheduled agents (nightly lint) + Datasette

**Goal:** First scheduled agent runs nightly. Datasette running for browsing.

### Tasks

1. **Scheduled agent container.** Docker image with the `atlas` Python package and credentials.
   - One container per agent type per store
   - Mounts `~/atlas/personal/` read-write (or read-only for read-only agents)
   - Logs to `~/atlas/personal/logs/<agent>/<date>.log`

2. **Nightly lint agent.** Runs at 2 AM:
   - Find entities missing required properties
   - Find broken wikilinks in notes
   - Find one-way relationships missing their inverse
   - Find Projects marked "active" with no activity in 30 days
   - Find Tasks past their due date
   - Write findings to `_meta/lint-<date>.md`
   - Do NOT auto-fix. Surface for review.

3. **Datasette setup.**
   - `datasette serve ~/atlas/personal/data/atlas.db --metadata=<config>`
   - Custom metadata: pretty table names, useful default queries
   - Available on `localhost:8001`
   - Mobile-friendly browsing via Tailscale or local network

4. **Useful Datasette queries (saved):**
   - All people, sortable by last_interaction
   - Active projects with their phase and next action
   - Open tasks by domain
   - Recent decisions
   - Signals matching by domain
   - Sources by month

### Deliverables
- `crontab` or `launchd` schedules the lint agent
- First lint report exists in `_meta/`
- Datasette renders the store
- Phone can browse via Tailscale

---

## Week 6 — Signal/Solution + matching

**Goal:** The killer use case — signals captured today match against solutions captured tomorrow, and vice versa.

### Tasks

1. **Signal/Solution entity specs.** Write `_meta/entities/signal.md` and `solution.md`.
   - Signal: `kind` (pain_point | requirement | interest | objection | budget_indicator | timing_indicator), `domain`, `source_person`, `source_org`, `specifics`, `intensity` (low/medium/high), `date`, `status` (open/matched/acted_on/stale/dismissed), `match_threshold`
   - Solution: `name`, `vendor`, `domain`, `description`, `pricing_tier`, `fit_notes`, `your_evaluation`

2. **Domain vocabulary.** Write 5-10 domain files in `_meta/domains/` for the user's most relevant areas:
   - `identity_management.md` (synonyms: SSO, IAM, access control, federation)
   - `cloud_security.md`
   - `data_engineering.md`
   - `developer_productivity.md`
   - `observability.md`
   - Each file has synonyms, related terms, example matches

3. **Matching engine.** When a new Signal or Solution is created:
   - Find candidate matches (signal→solution or solution→signal) using:
     - Semantic similarity (embedding distance)
     - Lexical (FTS5 keyword search)
     - Entity-typed (recent Signals/Solutions regardless of similarity)
     - Graph (one hop from linked entities)
   - Get ~30 candidates
   - Cheap LLM call (Haiku) ranks for actual relevance to the specific entity
   - Keep top 5-8 as match candidates
   - Insert into a `matches` table with confidence and rationale

4. **`/log-signal`, `/log-solution`, `/find-matches` actions** wired into MCP and CLI.

5. **Match aggregation.** When multiple matches exist for one new entity, surface as one notification with ranked candidates, not multiple notifications.

6. **Match notifications.** Surface matches in the next `/morning-brief` (not real-time push — see SPEC.md scenario 3).

### Deliverables
- Manually log a Signal (e.g., a colleague's pain point)
- Manually log a Solution (e.g., a vendor you evaluated)
- Run `/find-matches` and see them connected
- Run automatic matching on Signal/Solution creation

---

## Week 7 — Decision entity + `/evaluate-idea` via `crew`

**Goal:** Wire the persona system. Idea evaluation works end-to-end.

### Tasks

1. **Decision entity spec.** Write `_meta/entities/decision.md`:
   - `question`, `options_considered`, `choice`, `rationale`, `related_entities`, `outcome` (filled in later via 3-month review), `personas_consulted`, `confidence`

2. **`/evaluate-idea` action.** Markdown spec in `_meta/actions/`. Steps:
   - Capture the idea as an Idea entity
   - Resolve context: search KB for related Ideas, Projects, Decisions, people in domain
   - Format idea + context as input for `crew`
   - Invoke `crew` (via its MCP server or slash commands depending on how `atlas`'s MCP server can chain)
   - Capture the persona verdicts
   - Create a Decision entity linked to the Idea
   - Schedule a 3-month review action

3. **3-month review action.** `_meta/actions/review-decision.md`:
   - Surface decisions made 90 days ago
   - Ask "what happened?"
   - Update Decision.outcome
   - Feed outcome back into a "persona accuracy" metric over time

4. **Persona accuracy tracking.** A simple table that records how often each persona's verdict aligned with the actual outcome. Surface this in `/weekly-review`.

5. **Test integration with `crew`.** Verify `atlas` can invoke `crew`'s `/crew` and `/crew-review` programmatically and capture the results. If `crew`'s current API doesn't support programmatic invocation cleanly, add a `crew evaluate <idea-file>` CLI to `crew` and call it from `atlas`.

### Deliverables
- `/evaluate-idea` end-to-end: voice note in → Idea + Decision out, with persona verdicts attached
- 3-month review action fires for old decisions
- `crew` and `atlas` work together cleanly

---

## Week 8 — Weekly synthesis + calendar + morning brief

**Goal:** Compounding intelligence. The system surfaces patterns you didn't notice.

### Tasks

1. **Weekly synthesis agent.** Runs Sunday morning:
   - Read everything that changed this week (git log)
   - Produce `notes/reviews/<week>.md` summarizing
   - Identify patterns: "you mentioned [person] three times this week, want to upgrade to active contact?"
   - Flag stale projects, neglected people, accumulated decisions
   - Surface aging signals approaching staleness
   - Suggest next-week focus
   - Save as Note entity linked to all referenced entities

2. **Calendar integration (read-only).** Google Calendar API with read scope.
   - Pull next 7 days of events
   - Resolve attendees to Person entities
   - Surface in morning brief: "Today: meeting with X (last interaction 2 weeks ago, open signal from May 12)"
   - Do NOT auto-create Event entities for every calendar item; only when explicitly referenced

3. **`/morning-brief` action.** Composes from:
   - Today's calendar with enriched context
   - Yesterday's processed inbox items
   - Open matches surfaced overnight
   - Aging signals
   - Stale tasks
   - Birthdays/anniversaries
   - Decisions awaiting 3-month review
   - Optional: weather, anything else useful
   - Returns a structured brief; the user reads it in Claude Code or via Datasette

### Deliverables
- Sunday morning: a real weekly synthesis exists
- Every weekday morning: a morning brief renders
- Calendar context enriches every interaction

---

## Weeks 9-12 — Use it, fix what breaks, refine

**Goal:** 30+ days of real daily use without abandoning the system.

### Tasks

1. **Use it.** Every day. Capture everything. Run morning briefs. Process the inbox. Make decisions in `atlas`. Don't skip days.

2. **Fix what breaks.** Real use reveals what the framing missed. Common patterns to watch for:
   - Disambiguation that should be smoother
   - Entity types that need new properties
   - Action specs that need adjustment
   - Performance issues at real scale
   - LLM cost surprises

3. **Refine the ontology.** When you find unstructured properties recurring, promote them to typed properties. Run the migration. Update entity specs.

4. **Backfill more email** if Week 3 didn't get everything.

5. **Iterate on personas via `crew`.** When `/evaluate-idea` gives unhelpful verdicts, refine personas or add new ones following `crew/SCHEMA.md`.

6. **Tune scheduled agents.** Adjust nightly lint thresholds, weekly synthesis style, morning brief content.

### End-of-Phase-1 success criteria
- 30+ days of daily use
- Email backfill complete (years of context, not just recent)
- Ontology stable: no schema changes in the final 2 weeks
- At least one "I forgot about this" moment where `atlas` surfaced something genuinely useful you wouldn't have found otherwise
- At least one match (Signal ↔ Solution) that turned into action
- At least one Decision that, on 3-month review, you can evaluate honestly

---

## What Phase 2 looks like (preview)

Once Phase 1 is stable for ~2 months, Phase 2 starts the side-gig store:

- Postgres on a small VPS
- Simple multi-user auth (passkeys)
- Same interface, second connected store
- Side-gig partners install the same client
- Side-gig-specific entity extensions (Client, Prospect, Contract, Invoice)
- Light governance: ontology changes via PR with two-reviewer approval
- Cross-store sanity: confirm personal store is invisible to partners

Phase 2 is **not** a SaaS pivot. It is one more store with the same architecture.

---

## What Phase 3 looks like (preview)

Phase 3 is when the architecture's "many stores" claim is fully validated:

- A work team brain at the employer (separate store with SSO and full audit)
- A family/household store (shared with spouse)
- Or the user shifts careers and starts another side gig

The architecture must handle all of these without significant rework. If it doesn't, Phase 1-2 didn't fully implement the federation pattern and that's a debug job for Phase 3.

---

## What to avoid (failure modes worth naming)

1. **Building all of Phase 1 before using any of it.** Use Week 1's CLI before writing Week 2's MCP server. Use Week 2 before writing Week 3's ingestion. The system has to be useful incrementally.

2. **Over-engineering the ontology before there's enough data.** Five entity types max for Phase 1 Week 1. Add more only when the lack is felt.

3. **Skipping the lint agent.** Without it, schema drift and broken links accumulate invisibly.

4. **Letting email ingestion become a multi-week side quest.** If it's not done in 2 weeks, scope it down. Process 2 years instead of 10. Skip difficult formats.

5. **Building a web UI before Datasette proves insufficient.** Datasette gives you 80% of browsing value for 5% of the work.

6. **Treating `atlas` as a hobby project.** It has to become daily-driver to pay back the build cost. If you skip it for a week, the system stops compounding.

7. **Confusing capture with processing.** Capture must always be frictionless. Processing can take 24 hours.

8. **Saying yes to scope creep.** Mobile native app, web app, SaaS pivot, multi-user from day 1, "what if I also" — all rejected. Phase 1 is one person.

---

## Estimated total effort

- Pre-build reading + decisions: 0.5 day
- Weeks 1-8 of focused build: 8 weeks of evening/weekend effort, probably 10-15 hours/week
- Weeks 9-12 of use and refinement: 5 hours/week of build + ongoing daily use

Total to Phase-1 success: ~3 months part-time, or 4-6 weeks full-time.

This is honest. It is not a weekend project.
