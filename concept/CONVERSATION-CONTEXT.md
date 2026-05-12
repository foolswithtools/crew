# Conversation Context

This is a distilled summary of the long architecture conversation that produced this folder. Read it before `SPEC.md` so the spec's structure makes sense. Read it before changing any decisions in `DECISIONS.md` so you know which decisions are load-bearing.

---

## The arc of the conversation

The conversation started with a question about Palantir's Ontology and how the same architectural pattern (typed entities, governed relationships, action-based kinetics, identity-aware intelligence) shows up at three scales: enterprise (Palantir), personal (Karpathy's LLM Wiki, the Second Brain movement), and team (Dorsey's "Single Brain" framing). The insight is that **these are the same architecture instantiated at different scopes** — the differences are governance and trust posture, not the underlying model.

From there, the conversation walked through a series of pressure tests of a personal version of that architecture, then expanded scope upward through side-gig, team, and institutional deployments.

---

## The architectural insight that emerged

The single most important idea, articulated near the end of the conversation:

**One interface, many stores.**

- The **interface** is the agents, surfaces (CLI, web, voice, mobile capture), MCP server, reasoning layer. It holds no domain data.
- A **store** is a self-contained unit: ontology spec + structured data + raw sources + governance policy. Stores are independent. They never share data automatically.
- A user authenticates to one or more stores. The interface composes their view from connected stores while respecting each store's governance.

This pattern handles every use case without architectural change:
- One person, one store → personal use
- A small trusted team → a shared store (plus each person's personal store)
- A regulated workplace → an institutional store with full RBAC, completely walled from personal stores
- A federated network → stores expose APIs that other stores can consume, with explicit user consent

It also gives a clean answer to the personal-vs-work-vs-side-gig problem: same client, separate stores, no leakage, no rebuild.

---

## The five stress-test scenarios

The architecture was validated against five scenarios that exposed different failure modes:

### 1. Voice idea capture → multi-persona evaluation → evening verdict

Tested: ingestion latency vs. user availability; persona engineering vs. persona-as-label theater; the "evaluate against the KB" pattern; the feedback loop (review verdicts 3 months later).

**Key takeaway:** matching against the existing KB ("the 4th time you've had this idea, here's what you said before") is the killer feature, not the personas themselves. Personas are the surface; the KB is the substance.

### 2. Voice-captured fact → recurring reminder ("Marcus's birthday is May 20")

Tested: disambiguation across multiple people with the same name; partial dates; recurring vs one-time reminders; property provenance and conflict resolution; ontology evolution from capture; privacy posture toward people in the database.

**Key takeaway:** capture is not the same as schema update. Captures should land softly (stubs, unstructured properties, low-confidence claims); promotion to typed properties happens in review, not in capture. Provenance is mandatory, not optional. The "reminder" pattern is three patterns: intrinsic recurring (birthday → property of the entity), extrinsic recurring (rent due → Reminder entity), one-time (Task entity). Conflating them produces a mess.

### 3. Signal matching across time (Jennifer's identity-management pain ↔ Truss demo two weeks later)

Tested: the ontology's need for typed Signal and Solution entities with controlled vocabularies; bidirectional matching; aggregation when multiple matches exist; timing of match notifications; capture friction (most signals go uncaptured); decay (signals stale out); when matches *shouldn't* be made.

**Key takeaway:** this is the killer use case. The ontology needs typed Signal and Solution entities as first-class types from day 1. Controlled vocabularies (curated domain taxonomies) are unavoidable for precision matching; pure semantic similarity is too noisy. Decay is not optional. The system's value is structurally lopsided in the user's favor — be explicit about that.

### 4. GitHub CI failure on a Symphony-style auto-attempt → smart notification

Tested: relationship with external systems of record; notification policy as data; capturing resolutions for future similar problems; partner-relationship signal (Devon's filed-issues pattern); pipeline self-improvement; pre-launch lifecycle context; draft-response traps.

**Key takeaway:** `atlas` is not a notification system, it's a context system. External systems own their data; `atlas` indexes and annotates. Notification policy is declarative configuration, not embedded logic. Capturing resolutions (Decision entities) is the multiplier — without it, the system can't help with similar problems later.

### 5. Multi-identity (personal email + day-job email + 2 side-gig emails)

Tested: day-job email as a legal landmine (no ingest, ever); partner-owned business email; one database vs many; people existing across identities; identity-scoped cross-references; OAuth/credential management; same email arriving at multiple identities; cross-identity queries and their dangers; identity lifecycle (creation, archival, dissolution).

**Key takeaway:** identity is a first-class concept, not a tag. Every entity, source, and action has identity scope. Day-job email is excluded by policy, not technology — the technical capability to ingest it should not exist by default. People are canonical; their relationships are identity-scoped (one Person entity, multiple identity contexts). Source dedup at ingestion, processing per identity.

### Sixth scenario: small-business growth (the side gig hires 3 employees)

Tested: when a personal tool grows beyond personal.

**Key takeaway:** `atlas` has a natural size (one person to ~5 trusted peers). When the work scales beyond that, the right move is to **extract knowledge into team-appropriate tools** (Notion, Linear, Slack, an actual CRM) — not to scale `atlas` into a SaaS. `atlas` then becomes more valuable, not less, because it becomes the founder's personal synthesis layer over the team systems.

### Seventh scenario: dual deployment (work team brain + home personal brain)

Tested: a 30-person Engineering Excellence team brain at a regulated financial-services employer, in parallel with a personal brain at home.

**Key takeaway:** these are operationally, legally, and trust-wise *completely separate systems* that happen to share an architecture. Treat them as cousins, not siblings. The "one interface, many stores" pattern handles this cleanly: each is a store with its own governance. No code, data, credentials, or configuration crosses the boundary. Have the conversation with your employer about IP and scope *before* writing any code that overlaps.

---

## The architectural references that landed

The conversation surfaced several reference systems and the lessons each contributed.

| Reference | What `atlas` borrowed |
|---|---|
| **Palantir Ontology** (Foundry, AIP) | Typed entities + relationships + kinetics (verbs) + identity-aware intelligence; the four-component model of an operational decision (data, logic, action, security) |
| **Karpathy's LLM Wiki** | The pattern of LLM-maintained markdown KB with raw/wiki/schema layers; the 24-hour reversibility rule on agent actions; provenance with confidence and supersession |
| **NicholasSpisak/second-brain, SwarmVault** | Obsidian-compatible markdown maintenance by agents; the personal-scale instantiation of LLM Wiki |
| **OpenAI Symphony** | SPEC.md as the agent steering doc rather than code; one agent per task; "the workflow is in the repo" |
| **OpenClaw / NanoClaw** | The Gateway pattern (separate orchestration from model); container isolation for agents; skills-as-markdown for extensions; the "agent started a fight with Lemonade Insurance" cautionary tale (NEVER auto-send external comms) |
| **Jack Dorsey "Single Brain"** | Company-wide ontology with continuous ingestion; the four-layer stack (Hardware → World Model → Intelligence → Surfaces); the framing of personal nodes as first-class consumers of an institutional brain |
| **Microsoft Fabric IQ / Databricks Unity / Google's new semantic layer** | Validation that ontology-as-substrate is the dominant 2026 architecture for AI agents in the enterprise |

---

## The category `atlas` is in

Across all the scenarios, the conversation kept circling back to a category name:

**Personal data fabric with an ontology spine.**

Not a notes app. Not a database. Not a CRM. Not an AI assistant. Not a knowledge base. The thin coherent layer that knits external systems of record together for the person using it, with typed entities, governed relationships, action-based kinetics, and an LLM as the most natural interface.

The closest commercial analog is **Palantir Foundry for one person, with LLM-mediated capture and curation replacing the forward-deployed-engineer team that normally builds and maintains the ontology**.

---

## The hard-won principles

These came out of the stress tests and made it into `SPEC.md` §3. Listed here briefly for context:

1. **Ontology-first.** Schema is defined in versioned markdown specs before any data is captured.
2. **Provenance on everything.** Every fact has a source, timestamp, confidence.
3. **Append-only at the source layer.** Raw sources are immutable.
4. **Kinetics as typed verbs.** All mutations go through declared action types with validation, permissions, and audit.
5. **Decay is mandatory.** Signals and open loops have explicit lifecycles.
6. **External systems own their data.** `atlas` indexes and annotates; it doesn't mirror.
7. **Capture is frictionless; promotion is deliberate.** Captures are low-confidence stubs; promotion to typed entities is an explicit step.
8. **No automatic external action.** Drafts only. Human approves every outbound communication or external state change.
9. **Stores never auto-merge.** Cross-store operations are explicit and audited.
10. **Reversibility.** Every agent action is reversible within a defined window.

---

## What was deliberately not designed

The conversation explicitly punted on several things to avoid premature commitment. These are not omissions; they're open questions:

- **Specific Postgres host for Phase 2** (managed vs self-hosted VPS)
- **Specific embedding model** (local via Ollama vs API)
- **Specific transcription approach** (Whisper local vs API)
- **Authentication library for Phase 2** (passkeys vs magic links vs tokens)
- **Web UI framework** (FastAPI+HTMX vs Datasette+plugins vs Next.js)
- **Whether to use Anthropic's Skill format directly for action specs, or a custom format**
- **Whether to expose `atlas` as an MCP server consumable by Claude.ai (in addition to Claude Code) or keep it Claude-Code-only**

All deferred to the build session, listed in `SPEC.md` §13.

---

## The Lifebase name was rejected

The conversation used "Lifebase" as a placeholder. The user explicitly does not want that name. `NAMES.md` proposes alternatives.

---

## What the build is NOT trying to be

To prevent scope creep at start, this was made explicit:

- Not a messaging assistant (OpenClaw/NanoClaw pattern is the wrong shape for this)
- Not a 50-channel integrator
- Not a vector-only RAG system
- Not a consumer product
- Not a system of record (Gmail, GitHub, banks remain authoritative)
- Not an auto-action agent

`atlas` is a *thin, opinionated, personal* layer. Its leverage comes from typing and structure, not from breadth of integrations or flashy automation.
