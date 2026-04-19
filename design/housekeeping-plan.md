# Housekeeping & Scale Plan

Target: a catalog that remains trustworthy and navigable at 10K+ archetypes. This plan captures the target state, the existing structures we're borrowing from, the architecture, and a phased build order.

This is a living plan. As we complete items, move them to **Done** and update the status.

---

## How to resume this plan in another session

**Invocation to paste at the start of a fresh session:**

> Execute Phase N of `design/housekeeping-plan.md`. Follow the recommended order listed at the bottom of the "Phase N" section. Mark each item complete by checking its box (`[ ]` → `[x]`) and moving it to the **Done** section at the bottom of the plan. Validate the outcome before marking done — for Phase 1, that means running the validator against the 7 existing archetypes and confirming they pass.

**Rules for the executing session:**
- Read this whole plan file first before starting. Context matters.
- Execute items in the order listed at the bottom of the target phase.
- After each item: edit this file to check the box and append a one-line note under the item describing what was built (file paths, key decisions).
- When a phase is complete, move the whole phase's checklist into **Done** and add a dated summary.
- If you hit a decision point the plan doesn't cover, stop and ask the user before inventing policy.
- Do not skip ahead to a later phase without checking in.

---

## Vision — what "good housekeeping" looks like at scale

At 10K archetypes, the catalog needs to hold these properties simultaneously:

1. **No silent drift** — every archetype conforms to the format; broken/malformed files can't sneak in
2. **No sneaky duplicates** — new archetypes either are meaningfully different from existing ones, or the overlap is explicit and intentional
3. **Controlled vocabulary stays coherent** — tags don't proliferate into synonyms; new tags get governance
4. **Low-friction contribution** — a thoughtful outsider can add an archetype in 10-20 minutes with high confidence it'll pass review
5. **Three navigation modes work** — query-driven (`/crew`), browse (dimensional filter), discover (related / trending / gap)
6. **Findability survives scale** — "who do I need for X?" returns a useful answer whether the catalog has 20 or 20K archetypes
7. **Provenance stays clean** — every archetype has a reviewed state, an origin story (manual vs. drafted via `/crew`), and a contribution trail

We're at ~7 archetypes today. We don't need all of this built now — but the architecture has to accommodate it.

---

## Existing structures we're borrowing from

The user asked explicitly: what prior art applies here? Thinking deeply — these are the structures that map directly onto this problem.

### 1. Faceted classification (S. R. Ranganathan's Colon Classification, 1933)

**What it is:** Instead of forcing items into a single hierarchy (like Dewey Decimal), describe each item by its position on multiple independent facets. Any item = a coordinate in a multi-dimensional space.

**What we're already doing:** Our 3-dimension schema (`expertise` / `function` / `approach`) is a faceted classification. Each archetype is a combination of facet values. This is why `/crew` can match on dimensions without a rigid hierarchy.

**What we should do more of:** Keep the facets orthogonal (each should answer a different question), keep each facet's vocabulary small, and resist the urge to add a 4th or 5th facet until empirically needed.

### 2. SKOS (Simple Knowledge Organization System, W3C)

**What it is:** An RDF-based standard for thesauri and controlled vocabularies. Each concept has `broader`, `narrower`, `related`, `altLabel`, `preferredLabel`. Used by the Library of Congress, UNESCO, NASA thesauri.

**Why it matters for us:** Our controlled vocabulary (`expertise` tags, `function` tags, `approach` tags) will grow. SKOS-style relationships would let us say `machine-learning` has broader `artificial-intelligence`, narrower `deep-learning`, related `statistics`. This lets:
- `/crew` suggest sibling or narrower tags when matching
- Contributors discover the right existing tag instead of inventing synonyms
- Queries at different granularities ("anything in AI" matches `machine-learning`, `deep-learning`, `reinforcement-learning`)

**Lightweight adoption:** A `vocab.yml` file per facet with `broader`/`narrower`/`related` relationships. No RDF, no triple store — just YAML.

### 3. Embedding-based semantic similarity (modern vector search)

**What it is:** Encode each document as a high-dimensional vector; similarity = cosine distance. Lib options: sqlite-vec, Chroma, FAISS, Pinecone. All lightweight enough to run locally on 10K+ items.

**Why it matters:** At scale, exact tag matching misses obvious duplicates. An archetype tagged `product-design` + `critique` is not visibly similar to one tagged `ux-review` + `evaluation` — but semantically they may be the same school. Embeddings catch semantic near-duplicates.

**Two specific uses:**
- **Draft-time duplicate detection:** when `/crew` drafts a new archetype, embed it and show the 5 most-similar existing archetypes with a similarity score. If the top match is above 0.85, flag it for human review ("is this a genuine new archetype, or should it merge with X?")
- **Semantic retrieval:** `/crew` can use embedding similarity on the *problem description* to find relevant archetypes, in addition to or instead of dimensional matching

### 4. The Backstage catalog pattern (Spotify's developer platform)

**What it is:** A service catalog where each entity has `kind`, `metadata`, `spec`, and `relations`. Entities reference each other via relations. The catalog is compiled from source YAML files into a queryable graph.

**What we borrow:** 
- Each archetype file is an **entity** with `kind: archetype` (leaves room for other kinds later — `team-pattern`, `decision-framework`, `common-pitfall`)
- Relations between archetypes are first-class: `not-to-be-confused-with` (contrasts), `shares-exemplar-with`, `frequently-paired-with` (from usage logs)
- The "catalog" is a build artifact — a compiled index derived from source files

### 5. dbt's compile + catalog pattern

**What it is:** You write source files (SQL + YAML); dbt compiles them into a `manifest.json` that contains every model's metadata, dependencies, tests. Downstream tools (CI, docs, lineage viewer) all consume the manifest, not the source.

**What we borrow:** 
- Source of truth is `personas/*.md` (markdown files in git)
- A build script (`scripts/build-index.py`) compiles the source into:
  - `catalog.json` — machine-readable manifest of every archetype's frontmatter + path + content hash
  - `INDEX.md` — human-readable, facet-grouped
  - `embeddings.sqlite` — vector index (later phase)
- `/crew` and `/crew-review` read from the compiled index for speed, not by re-scanning all source files every invocation

### 6. Graph of relationships (Neo4j / property graphs)

**What it is:** Nodes (archetypes) with typed edges (relations) between them. Lets you query "archetypes 2 hops from X via 'contrasts-with' edges" etc.

**Why it matters:** Our `not-to-be-confused-with` section is already graph data. Making it first-class unlocks:
- "Show me archetypes that contrast with X" (for finding a crew that deliberately disagrees)
- "Show me archetypes that frequently appear in the same crews as X" (for suggesting complements)
- "Which archetypes have no contrast edges?" (likely duplicates or isolated — candidates for review)

**Lightweight adoption:** no Neo4j. Just build `graph.json` from parsing the markdown `Not to be confused with` sections + any usage logs.

### 7. Usage signals / popularity (Netflix, Spotify)

**What it is:** Track which items get used, returned to, combined with others. Recommend based on co-occurrence and freshness.

**Why it matters for us:** Over time, the catalog will have stars and deadwood. Usage logs tell us:
- Which archetypes get invoked in crews most often (stars — probably covering common jobs)
- Which have never been invoked (deadwood — candidates for merge or deletion)
- Which pairs appear together frequently (complements — add `frequently-paired-with` edges)
- Which problems routinely trigger gaps (coverage needs)

**Lightweight adoption:** `/crew` and `/crew-review` append a JSON line to `.crew/usage.log` with timestamp, archetypes used, problem summary hash. Periodic compaction + derivation into signals.

### 8. MECE as a design discipline (Mutually Exclusive, Collectively Exhaustive — consulting)

**What it is:** A logical-completeness discipline. A set is MECE when every case fits exactly one bucket.

**Our adoption:** Archetypes don't need to be *mutually* exclusive (a problem may need multiple). But within a domain, the set of archetypes should approach *collective* exhaustion of the load-bearing schools of thought. A periodic "coverage audit" — for a given domain, can we name the 3-5 major schools, and do we have archetypes for each? Flags gaps explicitly.

### What we're NOT borrowing (and why)

- **Dewey Decimal / rigid hierarchy** — archetypes belong to multiple places (an archetype can be about both `product-design` and `user-research`); a single-parent tree is the wrong shape
- **Folksonomies / uncontrolled free tags** — we need quality, not quantity. Controlled vocab wins
- **Heavy CMS / database (Drupal, Wagtail, Contentful)** — overkill for markdown-in-git, and loses the low-friction contribution story
- **ElasticSearch-as-primary-store** — the source of truth stays markdown files. Search is derived, not canonical

---

## Target architecture (3 layers)

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 3 — Tooling & Commands                                │
│   /crew, /crew-review, /crew-draft, /crew-browse,           │
│   /crew-lint, /crew-audit                                   │
│   scripts/build-index.py, scripts/validate.py               │
│   Claude Code hooks (pre-write validation)                  │
└─────────────────────────────────────────────────────────────┘
                           ↕ reads
┌─────────────────────────────────────────────────────────────┐
│ Layer 2 — Derived indexes (build artifacts, git-ignored)    │
│   INDEX.md         — human, facet-grouped                   │
│   catalog.json     — machine manifest (frontmatter + paths) │
│   embeddings.sqlite— vector index (phase 3)                 │
│   graph.json       — contrasts, exemplar-overlap, pairs     │
│   .crew/usage.log  — invocation history                     │
└─────────────────────────────────────────────────────────────┘
                           ↕ compiled from
┌─────────────────────────────────────────────────────────────┐
│ Layer 1 — Canonical source (git-tracked)                    │
│   personas/*.md           — archetype files                 │
│   vocab/expertise.yml     — controlled vocab per facet,     │
│   vocab/function.yml        with SKOS-style relationships   │
│   vocab/approach.yml                                        │
│   SCHEMA.md, TEMPLATE.md  — format spec                     │
│   CONTRIBUTING.md         — how to contribute               │
└─────────────────────────────────────────────────────────────┘
```

Layer 1 is the source of truth. Layer 2 is rebuilt from Layer 1. Layer 3 reads from Layer 2 for speed, and the hooks regenerate Layer 2 on relevant changes.

---

## Three navigation modes (target UX)

1. **Query-driven** (already working) — user has a problem. `/crew` reads conversation + problem, proposes archetypes. At scale, uses embedding similarity on the problem to narrow candidates before LLM judgment.

2. **Browse** — user wants to see what's there. `INDEX.md` (human) or `/crew-browse [facet] [value]` (command) returns archetypes grouped by facet. "Show me all `contrarian` + `product-design` archetypes."

3. **Discover** — user explores from one archetype outward. `/crew-related <archetype>` returns: contrasts (from `not-to-be-confused-with` edges), complements (from usage log pairings), narrower/broader (from SKOS-style vocab), exemplar-overlap (shares ≥ 1 person with this archetype).

---

## Phased build order

Each phase is small enough to complete in one session.

### Phase 3 — Real scale (500-5,000 archetypes)

**Goal:** semantic retrieval; discover mode works; deadwood gets pruned.

- [ ] **P3.1 — Embedding index**
  - `scripts/build-embeddings.py` embeds each archetype's prose into vectors (use a small, local model or API)
  - Store in `embeddings.sqlite` using `sqlite-vec`
  - Rebuilt on Write hook (incremental — only re-embed changed files)
- [ ] **P3.2 — Embedding-based duplicate detection**
  - Replace Phase 2's Jaccard check with embedding similarity at draft time
  - Threshold starts at cosine > 0.85 = "likely duplicate, review"; 0.7-0.85 = "related, declare intentional difference"
- [ ] **P3.3 — Embedding-based retrieval in `/crew`**
  - Embed the problem description; pre-filter archetypes by vector similarity (top-20 candidates) before LLM judgment. Scales `/crew` to catalogs where reading every archetype isn't feasible
- [ ] **P3.4 — Graph of relationships (`graph.json`)**
  - Parse `Not to be confused with` into contrast edges
  - Derive `shares-exemplar` from frontmatter
  - Derive `frequently-paired-with` from `.crew/usage.log`
- [ ] **P3.5 — `/crew-browse` command**
  - Facet-filtered listing at scale
  - Usage: `/crew-browse expertise:machine-learning approach:rigorous`
- [ ] **P3.6 — `/crew-related <slug>` command**
  - Shows contrasts, complements, narrower/broader, exemplar-overlap
  - Useful for navigation and for contributors checking non-duplication

### Phase 4 — Mature catalog (5,000+)

**Goal:** self-maintaining; coverage-aware; authoritative.

- [ ] **P4.1 — Usage-signal-driven deadwood detection**
  - Archetypes never invoked in N months → flag for archive
  - Archetypes consistently underperforming (user flagged as bad fit in crews) → flag for review
- [ ] **P4.2 — Coverage audit command**
  - `/crew-audit <domain>` runs a Round-1-style critique *on the catalog itself* for a domain: "what major schools of thought are missing?"
- [ ] **P4.3 — The Librarian archetype (recursive)**
  - A meta-archetype whose job is to review new archetype drafts
  - Auto-invoked by `/crew` during drafting: the drafted archetype is passed to the Librarian, who runs a coherence / overlap / vocabulary critique before save
  - The Wrecking Crew polices its own roster
- [ ] **P4.4 — Trending / freshness signals**
  - Popularity by invocation count; recency by last-invoked; new-this-month highlights
- [ ] **P4.5 — SKOS-vocabulary web (not just per-facet)**
  - Relationships across facets (e.g., `expertise:machine-learning` implies `function:methodology-review` is often relevant)

---

## Current inventory

Live today (as of 2026-04-18):

- `personas/` — 7 archetype files
- `SCHEMA.md` — format spec (needs updating when Phase 1 lands)
- `TEMPLATE.md` — copy-paste template (checklist is unenforced)
- `.claude/commands/crew.md` — Seeker command
- `.claude/commands/crew-review.md` — Reviewer command
- `examples/stock-ml-use-case.md` — end-to-end walkthrough
- `DESIGN.md` — canonical design doc
- `design/*` — journey specs, round 1 / round 2 critiques, pre-redesign archive

Nothing from Phase 1 / 2 / 3 / 4 exists yet. No validator, no vocab files, no build script, no indexes, no hooks, no CONTRIBUTING.md.

---

## Immediate next actions

Pick up from here:

1. **Phase 3 trigger is empirical, not time-based.** Do not start P3 (embeddings, semantic retrieval, graph) until the catalog actually strains Phase 2's tooling — roughly 50+ archetypes, or when duplicate detection starts missing semantic near-duplicates the Jaccard check can't see.
2. **Fill the catalog** until that strain shows up. Use `/crew` to draft new archetypes; the post-write hook now validates and rebuilds automatically, and `/crew-review-archetype` promotes `reviewed: false` → `reviewed: true` once peer-reviewed.
3. **Revisit the SKOS relationships periodically.** As new tags get added, keep the `broader`/`narrower`/`related` mappings current; the validator will warn on asymmetry but won't fail.

---

## Done

### Phase 1 — Immediate (at 7 archetypes, preventing bad habits early) — completed 2026-04-18

**Outcome:** validator runs clean against all 8 archetype files (note: catalog has 8, not 7 as the old "Current inventory" claimed). No broken files, no silent duplicates, clear contribution path. Layer 1 source of truth now includes `vocab/*.yml` alongside the persona files; Layer 3 has its first script (`scripts/validate.py`).

- [x] **P1.4 — Controlled vocabulary as source files** (`vocab/*.yml`)
  - Built `vocab/expertise.yml` (13 tags), `vocab/function.yml` (9 tags), `vocab/approach.yml` (10 tags). Each tag has `label`, `definition`, and empty `broader` / `narrower` / `related` stubs ready for Phase 2 (P2.3).
  - Updated `SCHEMA.md` to reference the three vocab files instead of inlining the lists; pointed contributors at `CONTRIBUTING.md` for the new-tag proposal flow.
- [x] **P1.1 — Validator script** (`scripts/validate.py`)
  - Built. Reads `vocab/*.yml` as the source of truth for tag checking. Errors on: malformed frontmatter, missing required fields, filename/`name` mismatch, exemplar count outside 2-5, missing required sections, missing display-name H1, duplicate `name`, fully-contained exemplar lists. Warns on unknown tags. Supports both whole-catalog (`python3 scripts/validate.py`) and per-file (`python3 scripts/validate.py personas/<file>.md`) modes; cross-file checks (duplicate names, exemplar containment) only run in whole-catalog mode.
- [x] **P1.3 — `CONTRIBUTING.md`**
  - Written. Covers: who should contribute, the two paths (let `/crew` draft vs. write by hand), the coherence test, the non-duplication expectation (with concrete grep recipes), review criteria for PRs, and the new-vocab-tag proposal flow.
- [x] **P1.2 — Strengthen `/crew` draft pre-flight**
  - Updated `.claude/commands/crew.md`. The "draft it" branch now requires the command to read the three `vocab/*.yml` files first, then state in its reply (before calling `Write`): (1) the coherence argument in prose, (2) tag-by-tag verification against the loaded vocab, (3) the closest existing archetype + the load-bearing contrast for "Not to be confused with", (4) a duplicate check against existing display names and exemplar lists with explicit thresholds. Also instructs the command to point the user at `python3 scripts/validate.py` after save.

**Validator run against existing archetypes:**
- Initial run surfaced 1 warning: `personas/data-honesty-skeptic.md` had `probabilistic` listed under `expertise`, but `probabilistic` is an `approach` tag (and was already correctly listed under `approach` in the same file — the expertise entry was a duplicate). Fixed by removing it from the `expertise` list.
- Final run: 8 files checked, 0 errors, 0 warnings. Per-file mode and an injected broken case both behave correctly (broken case: 7 errors + 1 warning, exit 1).

**Side effect:** the "Current inventory" section above still says "7 archetype files" — leaving it as-is for now since we don't track inventory in this plan beyond a snapshot, but flagging the discrepancy here.

### Phase 2 — Scale prep (building for 50-500 archetypes) — completed 2026-04-18

**Outcome:** Layer 2 (derived indexes) is live: `scripts/build-index.py` compiles `personas/*.md` into `catalog.json` + `INDEX.md`, both gitignored and idempotent. `/crew`'s draft flow now runs a numeric Jaccard/tag-overlap duplicate check against the catalog before `Write`. SKOS `broader`/`narrower`/`related` mappings are populated within each facet, and the validator enforces symmetry + intra-facet references as warnings. The Claude Code PostToolUse hook validates and rebuilds on every write to `personas/*.md`. A `/crew-review-archetype` command flips `reviewed: false` → `reviewed: true` after parallel peer critique, and `INDEX.md` surfaces all unreviewed archetypes. Layer 3 now reads from Layer 2.

- [x] **P2.1 — Build script** (`scripts/build-index.py`)
  - Built. Imports `split_frontmatter` and `REPO_ROOT`/`PERSONAS_DIR`/`VOCAB_DIR` from `validate.py` (no parser duplication). Emits `catalog.json` sorted by `name` with `content_hash` (sha256) and `INDEX.md` grouped by facet in vocab-file order, archetypes sorted by `display_name` under each tag, empty tags shown as `_(no archetypes yet)_`. `python3 scripts/build-index.py --check` is the idempotency gate — exits non-zero if a rebuild would change bytes. `.gitignore` created and lists `catalog.json`, `INDEX.md`, `embeddings.sqlite`, `graph.json`, `.crew/`.
  - Validation: `python3 scripts/build-index.py && python3 scripts/build-index.py --check` shows `catalog.json unchanged, INDEX.md unchanged` / `check ok — 8 archetype(s), no drift`.
- [x] **P2.2 — Tag-based duplicate detection in `/crew` draft flow**
  - Updated `.claude/commands/crew.md`. The draft-it path now reads `catalog.json` first (fallback to `Glob`+`Read` if missing), and pre-flight check #4 requires computing exemplar Jaccard + tag overlap against every existing archetype and surfacing the top-3 closest matches as an auditable line in the reply. Thresholds: Jaccard > 0.6 OR tag overlap > 3 → must stop and demand explicit written justification before `Write`.
  - Validation: simulated a deliberate near-duplicate ("The Forecasting Honesty Skeptic" with exemplars Silver/Taleb/Tetlock/Kahneman and overlapping tags) — scored Jaccard 0.75, tag overlap 8 against The Data-Honesty Skeptic, threshold tripped as expected.
- [x] **P2.3 — SKOS-style vocabulary relationships**
  - Populated `broader`/`narrower`/`related` in all three `vocab/*.yml` files, within-facet only (cross-facet is P4.5 scope). Load-bearing hierarchies: `statistics` is broader than `forecasting` and `time-series`; `critique` is broader than `stress-test`, `falsify`, `methodology-review`. Relateds lean conservative — only populated where the definitions support the link.
  - Extended `scripts/validate.py` with `check_vocab_relationships()` — verifies every reference exists in the same facet and that `broader`/`narrower` are symmetric (asymmetry is a WARNING, not a hard block). Confirmed the check catches both asymmetry and unknown-tag references via an injected broken fixture.
  - Validation: `python3 scripts/validate.py` clean (0 errors, 0 warnings).
- [x] **P2.4 — Claude Code PostToolUse hook**
  - Built `.claude/settings.json` with a `PostToolUse` hook matching `Write|Edit`. The command is `python3 "$CLAUDE_PROJECT_DIR/scripts/post-write-hook.py"` — a Python wrapper (not shell) that parses stdin JSON reliably. The hook only acts on `.md` files under `personas/`; other writes are silent no-ops. On validator failure it exits 2 (Claude Code's blocking-error code per the hooks docs) so stderr surfaces back to Claude for inline fixing; on success it rebuilds `catalog.json` + `INDEX.md`.
  - Validation: three scenarios tested via piped mock payloads — non-persona write (exit 0, silent), valid persona write (exit 0, `post-write-hook: <path> validated, catalog rebuilt`), malformed persona write (exit 2 with validator error in stderr). All three behave as specified.
- [x] **P2.5 — Review-state promotion flow**
  - Built `.claude/commands/crew-review-archetype.md`. Mirrors `/crew-review`'s parallel-subagent pattern but points the critics *at the archetype file itself*, reviewing coherence / uniqueness / vocab alignment / prose quality. Each critic returns a one-word verdict (PROMOTE/EDIT/REJECT) plus per-axis notes. Orchestrator synthesizes a combined recommendation; on PROMOTE it offers to `Edit` the `reviewed: false` line to `reviewed: true`.
  - Audit view already covered by `scripts/build-index.py` — `INDEX.md` has an "Unreviewed archetypes" section at the bottom listing every `reviewed: false` archetype (currently just The Classical Chartist).
  - Validation: command file registered by Claude Code (visible in the skills list as `/crew-review-archetype`); INDEX.md section present and populated.

**Repo shape after Phase 2:**
- Layer 1 (source): `personas/*.md`, `vocab/*.yml` (now with SKOS), `SCHEMA.md`, `TEMPLATE.md`, `CONTRIBUTING.md`
- Layer 2 (build artifacts, gitignored): `catalog.json`, `INDEX.md`
- Layer 3 (tooling): `scripts/validate.py` (extended), `scripts/build-index.py` (new), `scripts/post-write-hook.py` (new), `.claude/settings.json` (new), `.claude/commands/{crew,crew-review,crew-review-archetype}.md`
