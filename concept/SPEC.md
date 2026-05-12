# Product Specification: `atlas` (working name)

Version: 0.2 (Framing draft — pre-build)
Status: spec only, no code written

---

## 1. What this is

`atlas` is a **personal data fabric with an ontology spine**. It is a tool that lets one person (and optionally a small trusted group) capture, structure, retrieve, and reason over the information that flows through their life and work. It is not a note app, a database, a CRM, or an AI assistant. It is the thin coherent layer that knits those together, with AI as the most natural interface.

The architectural pattern is invariant across deployments: typed entities, governed relationships, action-based kinetics, identity-aware intelligence. The instances differ in scale, governance, and trust posture.

---

## 2. The core architectural insight

**One interface, many stores.**

An `atlas` deployment consists of two cleanly separated concerns:

- **The Interface**: agents, surfaces (CLI, web, MCP server, mobile capture), the reasoning layer. Holds no domain data of its own. Connects to one or more stores.
- **The Store**: a self-contained unit holding an ontology, structured data, raw sources, and a governance policy. Each store is independent. Stores never share data automatically. Cross-store queries are an explicit user action with an audit trail.

A user authenticates to one or more stores. The interface composes their view from connected stores while respecting their governance. Stores can be local (SQLite on a personal device), shared (Postgres for a small team), or institutional (a real company-owned brain with full RBAC). The interface treats them uniformly while respecting their governance.

This pattern handles every use case explored in framing without architectural change:

- Phase 1 personal use → one local store
- Phase 2 small team → a shared store, plus each user's personal store
- Future work-team brain → a fully separate institutional store with its own auth
- Future federation → stores expose APIs that other stores consume, with explicit user consent

---

## 3. Design principles (non-negotiable)

1. **Ontology-first.** Schema is defined in versioned markdown specs before any data is captured. The schema is the contract everything else honors.
2. **Provenance on everything.** Every fact has a source, a timestamp, a confidence level, and a path of how it got there. No exceptions.
3. **Append-only at the source layer.** Raw sources are immutable. Derived structured data can change; the record of how it came to be cannot.
4. **Kinetics as typed verbs.** All mutations happen through declared action types with validation, permissions, and audit. Agents and humans use the same kinetics through different surfaces.
5. **Decay is mandatory.** Signals, open loops, and time-sensitive entities have explicit lifecycles. The system surfaces aging entries and supports clean dismissal.
6. **External systems own their data.** `atlas` indexes and annotates external systems; it does not mirror them. References plus derived signal, not copies.
7. **Capture is frictionless; promotion is deliberate.** A capture is a low-confidence stub. Promotion to a typed, structured entity is an explicit step (manual or agent-proposed, human-approved).
8. **No automatic external action.** Drafts, suggestions, and proposals are always inspected by a human before any outbound communication or external state change.
9. **Stores never auto-merge.** Cross-store operations require explicit user invocation. Each crossing is logged.
10. **Reversibility.** Every agent action is reversible within a defined window. Git-backed where possible. Audit log otherwise.

---

## 4. The store model

A **store** is the unit of data sovereignty. Each store contains:

```
store_root/
├── _meta/
│   ├── store.yaml              # Store identity, owner, governance posture
│   ├── ontology.md             # Top-level ontology spec
│   ├── entities/               # One spec per entity type
│   ├── relationships.md        # Allowed relationship types
│   ├── domains/                # Controlled vocabularies for matching
│   ├── actions/                # Action specs (the kinetics layer)
│   ├── personas/               # Idea-evaluation critics (delegates to crew catalog)
│   └── policies/               # Notification policy, retention, decay
├── data/
│   ├── atlas.db                # SQLite (single-user) or connection config (multi-user)
│   └── raw/                    # Immutable source archives
│       ├── email/
│       ├── transcripts/
│       └── inbox/
├── notes/                      # Markdown narrative content
│   ├── people/
│   ├── projects/
│   ├── decisions/
│   └── reviews/
└── .git/                       # Version control for the whole store
```

Each store has a `store.yaml` that declares:

```yaml
store_id: ulid
name: "Personal"
type: personal | side_gig | team | institutional
owner: user_id_or_org_id
created: 2026-05-11
governance:
  multi_user: false
  auth_required: false
  audit_retention_days: 365
  external_action_approval: required
  cross_store_queries: prompt_each_time
integrations:
  - type: gmail
    account: you@personal.com
  - type: telegram
    bot_token_ref: keychain://atlas/personal/telegram
```

The interface reads `store.yaml` for every connected store and adjusts behavior accordingly.

---

## 5. The ontology (entity types)

Core entity types present in every store. Stores can extend with custom types via their entity specs.

| Entity | Purpose |
|---|---|
| **Person** | Human you have any meaningful relationship with. Identity-scoped contexts. |
| **Organization** | Companies, teams, schools, vendors, clients. |
| **Project** | Bounded effort with stakeholders, status, lifecycle phase. |
| **Task** | Discrete action with owner, status, optional due date. |
| **Event** | Point or span of time. Meetings, calls, deadlines, milestones. |
| **Decision** | Question, options considered, choice, rationale, impacts. |
| **Signal** | Observation worth matching across time (pain points, requirements, interests, capabilities). |
| **Solution** | Tool, vendor, or capability that may match a signal. |
| **Source** | Raw artifact (email, transcript, document, captured note) with metadata. |
| **Note** | Narrative content with frontmatter linking to other entities. |
| **Idea** | Captured concept pending evaluation. |
| **Reminder** | Future-dated nudge linked to an entity. |
| **AgentRun** | Automated action with input, output, outcome. |

Each entity type has a markdown spec in `_meta/entities/` defining required properties, optional properties, required sections (for narrative content), linking rules, agent rules.

### Schema (SQLite, lifted and adapted from `crux/docs/DATA_MODEL.md`)

```sql
-- Single entity table. Type-discriminated.
CREATE TABLE entities (
    id            TEXT PRIMARY KEY,          -- ULID
    type          TEXT NOT NULL,             -- person, project, task, etc.
    slug          TEXT NOT NULL,             -- human-readable id
    name          TEXT NOT NULL,
    identity_id   TEXT NOT NULL,             -- which identity this entity belongs to
    created_at    TEXT NOT NULL,             -- ISO 8601
    updated_at    TEXT NOT NULL,
    archived_at   TEXT,
    properties    TEXT NOT NULL,             -- JSON, type-specific fields
    note_path     TEXT,                      -- optional path to markdown narrative
    access_role   TEXT,                      -- RBAC tag (Phase 2+)
    UNIQUE(type, slug, identity_id)
);

-- Typed relationships between entities.
CREATE TABLE relationships (
    from_id       TEXT NOT NULL REFERENCES entities(id),
    to_id         TEXT NOT NULL REFERENCES entities(id),
    type          TEXT NOT NULL,             -- works_with, belongs_to, paid_to, etc.
    properties    TEXT,                      -- JSON
    created_at    TEXT NOT NULL,
    PRIMARY KEY (from_id, to_id, type)
);

-- Append-only event log. Every action writes here.
CREATE TABLE events (
    id            TEXT PRIMARY KEY,
    timestamp     TEXT NOT NULL,
    actor         TEXT NOT NULL,             -- user, agent:nightly_lint, etc.
    action        TEXT NOT NULL,             -- created, updated, linked, archived
    entity_id     TEXT,
    payload       TEXT                       -- JSON
);

-- Raw source documents (esp. emails).
CREATE TABLE sources (
    id            TEXT PRIMARY KEY,
    type          TEXT NOT NULL,             -- email, pdf, csv_row, transcript, web_clip
    message_id    TEXT,                      -- RFC 5322 for emails; enables dedup
    path          TEXT,
    content       TEXT,
    metadata      TEXT NOT NULL,             -- JSON
    identity_visibilities TEXT NOT NULL,     -- JSON array of identity_ids
    ingested_at   TEXT NOT NULL,
    processed     INTEGER DEFAULT 0
);

-- Links between sources and extracted entities.
CREATE TABLE source_entities (
    source_id     TEXT NOT NULL REFERENCES sources(id),
    entity_id     TEXT NOT NULL REFERENCES entities(id),
    confidence    REAL,                      -- agent's confidence in the link
    context       TEXT,                      -- snippet showing why
    PRIMARY KEY (source_id, entity_id)
);

-- FTS5 over source content.
CREATE VIRTUAL TABLE sources_fts USING fts5(content, metadata, content_rowid=rowid);

-- Vector embeddings (via sqlite-vec).
CREATE VIRTUAL TABLE source_embeddings USING vec0(
    source_id TEXT PRIMARY KEY,
    embedding FLOAT[1536]
);
```

Notes:
- Borrows the **type-discriminated entities + JSON properties** pattern from Palantir/Foundry and from `crux`'s nodes table.
- Borrows the **ghost-routing RBAC** pattern from `crux`: `access_role` is filtered at every level of any recursive query; unauthorized entities silently disappear, never 403.
- Borrows the **content-hash ETag** pattern from `crux` for an edge cache when stores are remote.
- `identity_id` everywhere from day 1, even if there's only one identity in Phase 1. Retrofitting this later is brutal.

---

## 6. The kinetics (action types)

Action types live in `_meta/actions/` as markdown files. **Each is a markdown spec that doubles as the prompt for the action.** Pattern lifted from `pwk/gpwk` and from `crew`'s slash commands. Each defines inputs, steps, validation, trust level, audit requirements.

Many of these can be **ported directly from `pwk/gpwk`** (see `OVERLAP.md`).

### Capture and ingestion
- `/capture` — dump anything into the inbox; agent classifies and routes
- `/ingest-email` — process an email (one-off or batch from mbox)
- `/ingest-calendar` — process a calendar event
- `/ingest-transaction` — log a financial transaction
- `/process-inbox` — triage inbox items into typed entities

### Entity management
- `/add-person`, `/update-person`, `/merge-people`
- `/start-project`, `/update-project-phase`, `/archive-project`
- `/add-task`, `/close-task`, `/snooze-task`
- `/log-decision`
- `/log-interaction`

### Signal and matching (the killer use case)
- `/log-signal` — capture an observation (pain point, requirement, interest)
- `/log-solution` — capture a tool/vendor/capability
- `/find-matches` — explicit cross-time matching
- `/dismiss-signal`, `/refresh-signal`

### Synthesis and review
- `/morning-brief`
- `/weekly-review`
- `/find-context <topic>` — assemble relevant context across the graph
- `/evaluate-idea` — runs the persona pipeline (delegates to `crew`)

### Maintenance
- `/lint` — surface broken references, missing properties, stale entries
- `/refactor-ontology` — propose and execute schema changes
- `/doctor` — full health check across stores

### Cross-store (explicit)
- `/cross-query` — query across multiple connected stores, audit-logged
- `/promote-to-store <target>` — move or copy an entity from one store to another

---

## 7. The persona system

For idea evaluation and decision support. **Delegates to `crew`**: this repo already implements a coherent persona catalog with `/crew` (select 3-4 non-overlapping critics) and `/crew-review` (run them as parallel subagents).

`atlas`'s `/evaluate-idea` action:
1. Captures the idea as an Idea entity
2. Resolves context from the KB (related entities, prior similar ideas, prior decisions on the topic)
3. Invokes `crew` with the idea + context to get 3-4 archetype critics
4. Optionally runs `/crew-review` for the parallel critique
5. Persists the result as a Decision entity linked to the Idea
6. Schedules a 3-month review action to capture outcome

The persona contract is **`crew`'s schema** (see `crew/SCHEMA.md`). `atlas` does not maintain its own persona format.

Stores can extend `crew` with store-specific personas (the personal store might add personas tuned to personal decisions; the side-gig store might add personas tuned to business decisions).

---

## 8. The interface layer

The interface is a single client (with multiple surfaces) that connects to one or more stores.

### Surfaces

- **Primary: CLI via Claude Code.** The main daily-driver interface. Knows about all connected stores; defaults to the active store; supports `--store=<name>` for explicit scoping.
- **MCP server.** Exposes typed tools backed by the store(s). Consumed by Claude Code (and any other MCP-compatible client). See "MCP gateway" below.
- **Capture: Telegram bot.** Voice notes, text, photos. Drops into the inbox of the configured store (or asks if ambiguous). One bot per store, or one bot that routes by command prefix.
- **Browse: Datasette + a thin web UI.** Mobile-friendly browsing of structured data. Read-only for most views; explicit edit flows for known-safe operations.
- **Scheduled: cron/launchd.** Runs scheduled agents (lint, synthesis, etc.) against each store on its own schedule.

### MCP gateway (dual MCP+CLI strategy)

The intelligence layer is an MCP server that exposes typed tools backed by the store(s). This honors both:
- The Lifebase spec's MCP-first stance (Claude Code ergonomics)
- `crux`'s anti-MCP stance for cases where MCP schema injection costs are prohibitive

The architecture: a **single Python store/actions library** is the source of truth. Both the MCP server and a thin `atlas` CLI are wrappers over it. Agents in Claude Code call MCP tools; cron jobs and headless automation call the CLI for token-cheap invocation. Both paths produce identical events and audit logs.

Tools the MCP server exposes (initial set):

- `search_entities(store, type, query, limit)`
- `get_entity(store, id)` → entity + relationships + recent sources
- `list_relationships(store, entity_id, type?)`
- `search_sources(store, query, type?, date_range?, semantic?)`
- `create_entity(store, type, properties)` (subject to action validation)
- `find_matches(store, signal_or_solution)`
- `cross_query(stores, query)` (explicit, audit-logged)
- `propose_action(store, action_type, params)` (returns proposal, does not execute)
- `execute_action(store, proposal_id, approval_token)` (requires explicit approval)

The MCP server runs as a daemon (launchd/systemd). One MCP server per machine, configured with the stores it knows about and the credentials for each.

### Store connection model

A user "connects" to a store by providing credentials (a local file path for personal stores, OAuth or username/password for shared stores, SSO for institutional stores). Connected stores appear in the interface. Disconnecting a store immediately removes it from the active view.

The active store at any moment is either:
- Explicit (user said `--store=sidegig1` or selected it in the UI)
- Inferred from context (capture from the side-gig Telegram bot defaults to that store)
- The user's default (set in client config)

The client never makes implicit cross-store queries. Cross-store operations are always explicit and audited.

---

## 9. Phase plan

### Phase 1: Personal Store (months 1-3)

**Goal:** One person (the user), one store, real daily use, full ontology established.

**Scope:**
- Personal store with full ontology
- Email ingestion (years of Gmail backfill, ongoing IMAP)
- Calendar integration (read-only)
- Web Clipper for inbox
- Telegram bot for voice/text/photo capture
- CLI via Claude Code
- MCP server (covering the tools above)
- Datasette for browsing
- Core action types (capture, person, project, task, decision)
- Nightly lint agent
- Weekly synthesis agent
- The signal/solution matching system (even if sparsely populated initially)
- Persona system via `crew` (`/evaluate-idea` invokes it)

**Explicitly out of scope:**
- Multi-user anything
- Sharing
- Web UI beyond Datasette
- Mobile app beyond Telegram

**Success criteria:**
- Email backfill complete
- 30+ days of daily use without abandoning
- At least one "I forgot about this" moment where the system surfaces something genuinely useful
- The ontology has stabilized (no schema changes in the final 2 weeks)

### Phase 2: Side-Gig Store (months 4-6)

**Goal:** Add a side-gig store, used by you and up to 4 partners. Shared but trusted-internal. Ease of use over walls.

**Scope additions:**
- A second store, hosted on a small VPS or cloud Postgres
- Auth: simple shared-team auth (passkeys or per-user tokens; no enterprise SSO needed)
- Multi-user support: who created/modified each entity, basic activity feed
- Interface seamlessly handles connection to both stores; user toggles or queries both
- Partners install the same client (CLI, Telegram bot, web UI) and connect only to the side-gig store
- Side-gig-specific ontology extensions (clients, prospects, contracts, invoices)
- Team-shared Slack bot for capture into the side-gig store
- Light governance: ontology changes require PR review by you and one partner

**Trust model:**
- All 5 users trust each other fully
- Data isolation between stores is enforced (personal store never visible to partners)
- Within the side-gig store, all 5 users see everything
- No row-level security; coarse-grained access

**Explicitly out of scope:**
- External customer access to the side-gig store
- Selling the tool to others
- Enterprise compliance, regulatory features
- Real RBAC

### Phase 3: Optional Future Stores (deferred)

The architecture supports additional stores without changes to the interface. Candidates:
- A second side gig as another store (zero new architecture)
- A work team brain as a separately governed store with SSO and full audit
- A family/household store shared with spouse
- A board/volunteer store for an organization you serve

Add them when the use case is real, not before.

---

## 10. Technical architecture

### Storage
- **Personal store:** SQLite file plus filesystem for raw and notes. Lives in `~/atlas/personal/`. Encrypted at rest via filesystem (FileVault, LUKS, etc.).
- **Side-gig store:** Postgres on a VPS (or managed Postgres) plus an S3-compatible object store for raw sources. Connection details in client config. Encrypted in transit and at rest.
- **Both:** `sqlite-vec` (SQLite) or `pgvector` (Postgres) for embeddings. FTS5 (SQLite) or built-in (Postgres) for full-text search.

### Schema
The minimal core schema in §5 is identical across both substrates. Identity scoping handled via an `identity_id` column on entities and sources (defaults to the store's primary identity if there's only one).

For the side-gig store, additional columns track user attribution: `created_by`, `modified_by`, `modified_at`. The `events` table becomes a full activity feed.

### MCP Server
- Single MCP server per machine
- Configuration file declares which stores it knows about and how to connect to each
- Each tool call carries store scope; defaults are explicit in the call signature
- All tool calls audit-logged to the store they affect

### Agents
- Scheduled agents run in containers (Docker on Linux, Apple Container on macOS) with explicit filesystem mounts and minimum credentials. Pattern borrowed from NanoClaw.
- One container per agent type per store (the personal lint agent and the side-gig lint agent are different containers)
- Agents never have access to credentials for stores they don't operate on
- All agent actions go through the same store/actions library as human actions

### Capture
- Telegram bot per store (or one bot with explicit `/store` commands)
- Whisper for transcription (local model preferred; API fallback)
- Light classifier for intent (idea, fact, task, signal, capture-only) using Haiku

### Cost controls
- Tiered models: Haiku for classification, retrieval ranking, lint. Sonnet for synthesis, persona evaluation, complex extraction. Opus only when explicitly invoked.
- Rate limits per store
- Budget tracking with monthly summaries
- Email backfill done in batches with progress visible

---

## 11. The persona of substrate repos

| Repo | Role in `atlas` |
|---|---|
| **`crew`** (this repo) | Home + persona system. `atlas` is built inside this repo. `/evaluate-idea` delegates to `crew`. |
| **`crux`** | Reference design for store schema, ghost-routing RBAC, edge cache, hierarchical retrieval, plugin connectors. Schema is lifted into Python; `crux` itself stays as the standalone Go enterprise option. |
| **`pwk`/`gpwk`** | Reference for task kinetics. Slash-command markdown files are ported into `_meta/actions/`. The "capture first, carryover not carry burden, hybrid execution" philosophy carries forward verbatim. |
| **`brok`** | Pattern reference for vault/workspace separation (the Three Pillars), Provider Registry for multi-LLM, Memory Ledger correction pairs. Pattern transfer only; no code shared. |

Details in `OVERLAP.md`.

---

## 12. Hard constraints (must be honored)

1. **Stores never auto-merge.** Any data movement between stores is explicit, user-initiated, audit-logged.
2. **External actions require approval.** No autonomous email-sending, ticket-creating, payment-making.
3. **Provenance is mandatory.** No data without a source.
4. **The ontology evolves through versioned changes.** No schema drift via silent agent behavior.
5. **Local-first for the personal store.** No cloud dependency for daily personal use.
6. **The architecture supports a hard-walled work instance later.** Even though Phase 2 prioritizes ease over walls, the pattern must remain capable of true isolation when a work store is added.

---

## 13. Open questions for the build session

These are decisions deferred until build:

- Specific Postgres host for Phase 2 (managed vs. self-hosted VPS)
- Specific embedding model (local via Ollama vs. API)
- Specific transcription approach (Whisper local vs. API)
- Authentication library for Phase 2 (passkeys vs. magic links vs. tokens)
- Web UI framework (FastAPI + HTMX vs. Datasette + custom plugins vs. Next.js)
- Whether to use Anthropic's Skill format directly for action specs, or a custom format
- Whether to expose `atlas` as an MCP server consumable by Claude.ai (in addition to Claude Code) or keep it Claude-Code-only
- Whether `atlas` lives inside `crew/atlas/` (sub-package) or grows into its own top-level package in this repo

---

## 14. Build sequence (Phase 1, week by week)

See `BUILD-PLAN.md` for the full sequence. Headlines:

- **Week 1:** SQLite schema (lifted from `crux/docs/DATA_MODEL.md`), migrations, core Python data-access library. Entity specs for Person, Project, Task.
- **Week 2:** MCP server skeleton with core tools. CLI for adding/listing/updating entities. Manual use.
- **Week 3:** Email ingestion pipeline. Gmail Takeout parsing, batch loading. Entity extraction agent (Haiku) on backlog.
- **Week 4:** Telegram bot for capture. Whisper. `/capture` action. Inbox processor.
- **Week 5:** Nightly lint agent in a container. First scheduled agent. Datasette running.
- **Week 6:** Signal and Solution entity types. `/log-signal`, `/log-solution`, `/find-matches`. Domain vocabulary files for 5-10 common domains.
- **Week 7:** Decision entity type. `/evaluate-idea` delegates to `crew`'s persona system.
- **Week 8:** Weekly synthesis agent. Calendar integration (read-only). `/morning-brief`.
- **Weeks 9-12:** Use it. Fix what breaks. Refine the ontology based on real friction. Backfill more email. Iterate.

End of Phase 1: a working personal `atlas` you've used for 6+ weeks of daily life.
