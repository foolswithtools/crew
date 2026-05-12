# concept/

This folder frames out a new app that builds on the substrates already in the `foolswithtools` ecosystem (`crew`, `crux`, `pwk`, `brok`). It is the handoff from a long architecture conversation into a fresh build session.

**Working name: `atlas`** — provisional. See `NAMES.md` for alternatives and pick one in the next session.

**Status:** spec/framing only. No code has been written. The next session should read everything in this folder, settle on the name and any deferred decisions, and then begin Phase 1 of the build inside this repo.

---

## What this is

`atlas` (working name) is a **personal data fabric with an ontology spine**. It captures, structures, retrieves, and reasons over the information that flows through one person's life and work — emails, tasks, decisions, signals from conversations, projects, finances, and the relationships between them. AI agents (Claude Code primarily) are the most natural interface to it; the data and structure are the actual product.

The architectural insight that distinguishes it from every other personal-AI tool: **one interface, many stores**. The agents and surfaces (CLI, MCP, web) are a thin client that connects to one or more independent stores (personal, side-gig, team). Each store has its own ontology, governance, and data. Cross-store operations are explicit and audited. This pattern scales cleanly from a single user to a small team to (eventually) an institutional brain — without architectural changes.

The pattern is the same one Palantir's Ontology uses at enterprise scale, the same one Karpathy's LLM Wiki proposes for personal use, and the same one Jack Dorsey's "Single Brain" framing implies for company-wide intelligence. `atlas` is the personal/small-team instantiation of it.

---

## How to read this folder

In order:

1. **`CONVERSATION-CONTEXT.md`** — the *why*. Distilled summary of the long architecture conversation that produced this. Read first to ground yourself in the design intent.

2. **`SPEC.md`** — the *what*. Full product specification: ontology, store model, kinetics, persona system, surfaces, phase plan, hard constraints. Refined from the conversation, with `atlas`-specific references to the substrate repos.

3. **`OVERLAP.md`** — the *with what*. Per-repo mapping showing which parts of `crew`, `crux`, `pwk`, and `brok` cover which sections of the spec, and what each repo's role is going forward (incorporate, depend on, inspire from).

4. **`DECISIONS.md`** — the *with what trade-offs*. Architectural decisions locked in during framing, with rationale and the open questions still to settle. Every decision is flagged as revisitable.

5. **`BUILD-PLAN.md`** — the *how*. Phase 1 sequence: what to write first, leveraging what already exists, and where the new code goes.

6. **`NAMES.md`** — what to call this. Five name candidates with reasoning; pick one in the next session.

7. **`SPEC.md` appendix sections** — entity types, action types, persona system contract — read on demand when implementing those pieces.

---

## How `atlas` relates to the existing repos

| Repo | Role | Action |
|---|---|---|
| **`crew`** (this repo) | Home + persona system | `atlas` is built **inside** this repo, in a new package, alongside the persona catalog |
| **`crux`** | Reference design for store/RBAC/cache | Lift schema and patterns into Python; `crux` stays as the Go enterprise alternative |
| **`pwk`/`gpwk`** | Reference for task kinetics | Port the slash-command markdown files into `atlas`'s actions layer; rename namespace |
| **`brok`** | Reference for vault separation + Provider Registry | Pattern transfer only; no code shared |

Detail in `OVERLAP.md`.

---

## What the next session should do first

1. Read `CONVERSATION-CONTEXT.md` and `SPEC.md` end-to-end.
2. Pick a name (see `NAMES.md`).
3. Review the locked decisions in `DECISIONS.md` — flag anything to revise *before* code is written, since some decisions propagate everywhere.
4. Start Phase 1 from `BUILD-PLAN.md`. Week 1 is the SQLite schema and the core Python data-access library, lifted from `crux/docs/DATA_MODEL.md`.

---

## Why this lives in the `crew` repo

The conversation decided that `crew` is the home for `atlas` rather than a sibling repo because:

- `crew` *is* the persona system that `atlas`'s `/evaluate-idea` action requires. They are not adjacent; they are the same thing.
- The Python ecosystem (`crew`, `brok`) outweighs the Go substrate (`crux`) for the orchestrator. Keeping `atlas` in the same repo as `crew` keeps the persona contract first-class.
- A single repo is easier for one person to maintain than two coupled repos.

If `atlas` outgrows `crew` later, the split is a refactor, not an architectural change.

---

## Hard constraints (carried forward from the spec)

These are the rules the build must honor. They are restated in `SPEC.md` §12 with rationale.

1. Stores never auto-merge. Cross-store operations are explicit and audited.
2. External actions (email send, ticket create, payment) require explicit human approval.
3. Provenance is mandatory. No data without a source.
4. Schema evolution is versioned. No silent drift via agent behavior.
5. Local-first for the personal store. No cloud dependency for daily personal use.
6. The architecture must support a hard-walled work instance later, even though Phase 2 (small team) prioritizes ease over walls.

---

## Out of scope (do not build these in Phase 1)

- A messaging-app assistant in the style of OpenClaw/NanoClaw
- A 50-channel integration list
- Pure vector RAG over raw documents (the point is structured ontology with derived embeddings)
- A consumer product or SaaS positioning
- Auto-sending external communications
- A replacement for systems of record (Gmail, GitHub, banks, etc.)
