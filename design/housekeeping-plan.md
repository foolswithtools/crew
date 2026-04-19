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

All phases (1–4) are now complete. See the **Done** section at the bottom of this file for the completed checklist and outcomes.

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

1. **Fill the catalog** to exercise the Phase 3 + Phase 4 tooling. `/crew` drafting runs Jaccard/tag + semantic duplicate checks *and* the Librarian peer-review gate; the post-write hook rebuilds `catalog.json`, `INDEX.md`, `embeddings.sqlite`, `graph.json`, and `.crew/signals.json` on every persona write; `/crew-browse` and `/crew-related` are available for navigation (now with cross-facet SKOS suggestions); `/crew-review-archetype` promotes `reviewed: false` → `true` after peer critique; `/crew-audit <domain>` surfaces coverage gaps. The embedding ranker only meaningfully pre-filters once the catalog passes ~20 archetypes — until then, `/crew` still reads everything.
2. **Revisit the SKOS relationships (within- and cross-facet) periodically.** As new tags and archetypes land, `broader`/`narrower`/`related` and `cross_facet_related` drift away from observed co-occurrence. Re-derive `cross_facet_related` from `catalog.json` at threshold ≥ 2 when the catalog shape changes materially. Validator warns on asymmetry but doesn't fail.
3. **Let `.crew/usage.log` accumulate signal.** Every `/crew`, `/crew-review`, `/crew-review-archetype`, and `/crew-audit` invocation logs one line. After a few weeks of real use, `deadwood-report.py` surfaces genuinely unused archetypes, `signals.json` drives Trending, and `frequently_paired_with` edges surface real complements. Compact (`python3 scripts/usage-log.py compact`) opportunistically.

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

### Phase 3 — Real scale prep (at 8 archetypes, scaffolding for 500-5,000) — completed 2026-04-18

**Outcome:** semantic retrieval, semantic dedupe, and the relationship graph are live; discover mode works end-to-end via the two new navigation commands. The catalog hasn't yet strained Phase 2's Jaccard/tag tooling — the user deliberately landed P3 early so the scaffolding exists before the strain does. Layer 2 now has three derived artifacts (`catalog.json`, `embeddings.sqlite`, `graph.json`), all rebuilt automatically by the post-write hook. Phase 3 also introduced the first external Python deps: `requirements.txt` + a gitignored `venv/`, with a hook that re-execs itself through `venv/bin/python3` so the core P1/P2 flow still works without the deps installed.

- [x] **P3.1 — Embedding index**
  - `scripts/build-embeddings.py` embeds each archetype's prose into vectors (use a small, local model or API)
  - Store in `embeddings.sqlite` using `sqlite-vec`
  - Rebuilt on Write hook (incremental — only re-embed changed files)
  - Built. Uses `sentence-transformers/all-MiniLM-L6-v2` (384-dim, L2-normalised) stored in `archetype_vec` (sqlite-vec vec0 virtual table) with a companion `archetype_meta` table tracking slug → content_hash → vec_rowid. Modes: full reconcile, single-file upsert, `--check`. Skips re-embedding when content_hash matches. Validation: 8-file cold build, then a single whitespace edit to `data-honesty-skeptic.md` via Edit bumped only that slug's `embedded_at`; `--check` clean after revert.
- [x] **P3.2 — Embedding-based duplicate detection**
  - Replace Phase 2's Jaccard check with embedding similarity at draft time
  - Threshold starts at cosine > 0.85 = "likely duplicate, review"; 0.7-0.85 = "related, declare intentional difference"
  - Built `scripts/semantic-duplicate-check.py` — embeds the draft's prose body and dot-products against all vectors in `embeddings.sqlite` (vectors are L2-normalised, so dot = cosine). Emits JSON (top-5 matches + `max_cosine` + `trip_threshold` ∈ `{distinct, related, duplicate}`) with self-match filtering by display_name. Graceful degradation: missing deps or empty index → `embeddings_enabled: false`, caller falls back to Jaccard-only. Kept Jaccard/tag as the cheap first pass rather than replacing it: hybrid gives Jaccard a chance to catch exemplar-heavy duplicates even when the embedding index is unavailable, and the scored view in the reply now shows both signals. Updated `.claude/commands/crew.md`: added `Bash` to `allowed-tools`; added pre-flight check #5 that writes the draft to `.crew/draft-check.md`, runs the helper, surfaces the top-3 matches as visible lines, and blocks on `related` / `duplicate` verdicts until the drafter justifies. Validation: `.crew/test-forecasting-honesty-skeptic.md` — a disjoint-exemplar (Duke/Mellers/Makridakis) paraphrase of `data-honesty-skeptic` — scored cosine 0.83 (`related`), surfacing `data-honesty-skeptic` as the top match while every other archetype stayed ≤ 0.53 `distinct`. Jaccard on exemplars would have been 0 against data-honesty-skeptic; the semantic check caught the overlap the Jaccard check can't see.
- [x] **P3.3 — Embedding-based retrieval in `/crew`**
  - Embed the problem description; pre-filter archetypes by vector similarity (top-20 candidates) before LLM judgment. Scales `/crew` to catalogs where reading every archetype isn't feasible
  - Built `scripts/embed-query.py` — embeds problem text from stdin (or `--slug <name>` to query by a stored vector, which P3.6 uses) and ranks all archetypes by cosine. Defaults to top-20. Same graceful-degradation contract as the duplicate check. Updated `.claude/commands/crew.md` to gate on catalog size: ≤ 20 archetypes → Read everything (unchanged from P2); > 20 → pipe the Problem-I'm-hearing synthesis through `embed-query.py`, Read only top-20. Validation: a keyword-dense finance query ("backtest harness futures regime shift drawdown out-of-sample quant methodology") returns rigorous-quant-ml / data-honesty / regime-aware as the top 3; a looser natural-language version of the same question still lands the three finance archetypes in the top 4 (smaller signal is a quirk of the 8-archetype scale + MiniLM — at 50+ archetypes the ranking quality improves substantially).
- [x] **P3.4 — Graph of relationships (`graph.json`)**
  - Parse `Not to be confused with` into contrast edges
  - Derive `shares-exemplar` from frontmatter
  - Derive `frequently-paired-with` from `.crew/usage.log`
  - Built `scripts/build-graph.py`. Parses each persona's `## Not to be confused with` section via regex `- **<name>** — <reason>` (em-dash or double-hyphen tolerated, multi-line bullets joined), resolves bold names against catalog display_names, and emits `graph.json` with `nodes`, `edges.contrasts` (directed), `edges.shares_exemplar` (undirected, derived from frontmatter exemplar-overlap), and `edges.frequently_paired_with: []` (deferred to Phase 4 when usage logging lands). Unresolved bold names print `WARNING:` to stderr. `--check` mode compares a stable shape (with `generated_at` stripped) for idempotency. Wired into `scripts/post-write-hook.py` — runs after `build-index.py`, non-blocking on failure. Validation: 17 contrast edges (0 unresolved-name warnings); 0 shared-exemplar edges (archetypes are disjoint by design, which is itself a useful diagnostic); `classical-chartist` has 3 outgoing contrast edges as expected; `--check` clean after hook run.
- [x] **P3.5 — `/crew-browse` command**
  - Facet-filtered listing at scale
  - Usage: `/crew-browse expertise:machine-learning approach:rigorous`
  - Built `.claude/commands/crew-browse.md` (allowed-tools: Read). Parses `$ARGUMENTS` as `<facet>:<value[,value,…]>` tuples; AND across facets, OR within. No args → facet/tag table of contents, listing only tags with ≥ 1 archetype plus an unreviewed section. Reads `catalog.json` for the source of truth. Zero-match path prints the filter and offers a one-relaxation suggestion (the tightest facet drop). Validation (via direct filter simulation against catalog.json): `expertise:statistics` → 2 archetypes (data-honesty, rigorous-quant); `approach:rigorous` → 3 (data-honesty, information-architect, rigorous-quant); `expertise:product-design function:critique` → 4 (all four product archetypes); `expertise:machine-learning approach:contrarian` → 0 (expected). Command is registered (visible as `/crew-browse` in the skills list).
- [x] **P3.6 — `/crew-related <slug>` command**
  - Shows contrasts, complements, narrower/broader, exemplar-overlap
  - Useful for navigation and for contributors checking non-duplication
  - Built `.claude/commands/crew-related.md` (allowed-tools: Read, Bash). Resolves the target by slug first, then case-insensitive display_name; suggests the 3 closest candidates on miss rather than guessing. Produces four sections: **Contrasts** (directed; reads `graph.json` for outgoing/incoming edges, surfaces the verbatim "Not to be confused with" reason rather than paraphrasing — paraphrasing loses the load-bearing distinction), **Shared exemplars** (from `graph.json`; "none" when disjoint is kept as a diagnostic), **Semantic neighbors** (via `scripts/embed-query.py --slug <target> --top 5` — this is what the `--slug` mode was added for), **Vocab neighbors** (loads `vocab/*.yml` + `catalog.json`, walks each target tag's broader/narrower/related to find other archetypes sharing any related tag, prefers narrower/broader in the top-5 cap). Every section degrades gracefully on missing inputs. Validation via direct graph/embedding inspection for `rigorous-quant-ml-researcher`: 2 outgoing contrasts (data-honesty, regime-aware), 3 incoming contrasts (classical-chartist, data-honesty, regime-aware) — all 5 edges verbatim with reasons; 0 shared exemplars (expected); top-5 semantic neighbors include all three finance archetypes (data-honesty 0.53, regime-aware 0.46, classical-chartist 0.40); vocab paths through `critique → narrower` and `statistics → narrower` populate the SKOS section. Command registered (visible as `/crew-related`).

**Repo shape after Phase 3:**
- Layer 1 (source): `personas/*.md`, `vocab/*.yml`, `SCHEMA.md`, `TEMPLATE.md`, `CONTRIBUTING.md` (now with setup stanza), `requirements.txt` (new)
- Layer 2 (build artifacts, gitignored): `catalog.json`, `INDEX.md`, `embeddings.sqlite` (new), `graph.json` (new)
- Layer 3 (tooling): `scripts/validate.py`, `scripts/build-index.py`, `scripts/post-write-hook.py` (extended to run embeddings + graph and re-exec into venv), `scripts/build-embeddings.py` (new), `scripts/semantic-duplicate-check.py` (new), `scripts/embed-query.py` (new), `scripts/build-graph.py` (new), `.claude/settings.json`, `.claude/commands/{crew (extended),crew-review,crew-review-archetype,crew-browse (new),crew-related (new)}.md`
- Dev env: repo-local `venv/` (gitignored) with PyYAML + sentence-transformers + sqlite-vec + numpy; hook hops into it automatically when present

### Phase 4 — Mature catalog scaffolding (at 8 archetypes, scaffolding for 5,000+) — completed 2026-04-18

**Outcome:** the catalog now generates signals about itself, audits its own coverage on demand, peer-reviews its own additions at draft time, and carries cross-facet SKOS relationships that unlock richer navigation. Same pattern as Phase 3: land the scaffolding before the scale strains it. `.crew/usage.log` is the foundation — every `/crew` / `/crew-review` / `/crew-review-archetype` / `/crew-audit` invocation appends a JSONL line; raw entries compact into monthly aggregates past 90 days. Derived artifacts (`.crew/signals.json`, `graph.json` `frequently_paired_with` edges, `INDEX.md` Trending section) fall out automatically. The Librarian closes the draft-time peer-review loop as a 9th archetype. `/crew-audit <domain>` runs the catalog's own critics against its coverage. Cross-facet SKOS (empirically derived from catalog co-occurrence at threshold ≥ 2) flows into `/crew-related` and `/crew-browse`. Catalog: 8 → 9 archetypes; graph edges: 17 → 20 contrasts.

- [x] **P4.1 — Usage-signal-driven deadwood detection**
  - Archetypes never invoked in N months → flag for archive
  - Archetypes consistently underperforming (user flagged as bad fit in crews) → flag for review
  - Built `scripts/usage-log.py` (append / compact / signals subcommands) and `scripts/deadwood-report.py`. `.crew/usage.log` is JSONL; raw entries compact into monthly aggregates past 90 days (idempotent — second compact is a no-op). Wired logging into `.claude/commands/crew.md` (seek-it step 6, draft-it post-Write), `.claude/commands/crew-review.md` (step 9, after synthesis), `.claude/commands/crew-review-archetype.md` (step 7, after synthesis). Extended `scripts/build-graph.py` to read `.crew/usage.log` and emit `edges.frequently_paired_with` at `count ≥ 2` threshold — validated with 4 synthetic pair edges surviving compaction via the monthly-aggregate `pairs` map. `deadwood-report.py --months 3` correctly surfaces both never-invoked (1) and stale (1) candidates from the test log.
- [x] **P4.4 — Trending / freshness signals**
  - Popularity by invocation count; recency by last-invoked; new-this-month highlights
  - `scripts/usage-log.py signals` emits `.crew/signals.json` (by_slug counts + last_invoked + first_seen, trending top 5 in last 30 days, new_this_month via git first-add commit). `scripts/build-index.py` reads the signals file and injects a "Signals" block at the top of `INDEX.md` with Trending + New this month subsections. `scripts/post-write-hook.py` runs `usage-log.py signals` after `build-graph.py` and re-runs `build-index.py` so INDEX.md stays in sync. `.claude/commands/crew-browse.md` now surfaces a one-line trending hint when called with no args. Idempotency preserved — `build-index.py --check` clean after the new section lands.
- [x] **P4.3 — The Librarian archetype (recursive)**
  - A meta-archetype whose job is to review new archetype drafts
  - Auto-invoked by `/crew` during drafting: the drafted archetype is passed to the Librarian, who runs a coherence / overlap / vocabulary critique before save
  - The Wrecking Crew polices its own roster
  - Wrote `personas/the-librarian.md` by hand (Ranganathan / Svenonius / Gruber — three whose writings converge on "controlled vocabularies are engineered, not grown"). Validates clean (0 errors, 0 warnings); post-write hook regenerated catalog + embeddings + graph (20 contrast edges; the Librarian picked up 3 new contrasts against Information Architect, Data-Honesty Skeptic, Contrarian Simplicity Skeptic). Wired the Librarian as pre-flight check #6 in `.claude/commands/crew.md` draft-it path: subagent is launched with full persona + draft + top-5 semantic neighbors + all three vocab files, produces PROMOTE/EDIT/REJECT + per-axis notes. PROMOTE proceeds to Save; EDIT and REJECT require explicit user direction before save. Graceful skip if `personas/the-librarian.md` is missing (bootstrap path).
- [x] **P4.2 — Coverage audit command**
  - `/crew-audit <domain>` runs a Round-1-style critique *on the catalog itself* for a domain: "what major schools of thought are missing?"
  - Built `.claude/commands/crew-audit.md`. Candidate set = union of (a) `embed-query.py --top 30` with cosine ≥ 0.30 and (b) tag/display-name keyword overlap against the domain words. Launches 3 parallel meta-critics (domain expert / MECE disciplinarian / contrarian), each seeing the full candidate bodies. Orchestrator synthesizes a coverage map (schools named → covered/partial/missing) + 1–3 concrete next-archetype recommendations with proposed name, exemplars, and dimensions. Empty-candidate case handled gracefully. Logs a `crew-audit` entry to `.crew/usage.log`. Command registered in the skills list; pre-filter validated against `quantitative finance` (3 finance archetypes at cosines 0.29–0.41; tag-keyword pass in 2b backstops the semantic threshold for terms like `regime-aware-macro-thinker`).
- [x] **P4.5 — SKOS-vocabulary web (not just per-facet)**
  - Relationships across facets (e.g., `expertise:machine-learning` implies `function:methodology-review` is often relevant)
  - Added `cross_facet_related:` field to every tag in `vocab/expertise.yml`, `vocab/function.yml`, `vocab/approach.yml`. Values keyed by target facet; populated empirically from catalog co-occurrence at threshold ≥ 2 (computed from the current 9-archetype catalog). Extended `scripts/validate.py:check_vocab_relationships()` with same-facet self-ref check, unknown-facet / unknown-tag checks, and cross-facet symmetry enforcement (asymmetry = WARNING, matching the within-facet convention). Verified asymmetry detection by injecting a one-sided ref — validator surfaced it correctly. Updated `.claude/commands/crew-related.md` to walk cross-facet neighbors alongside within-facet (cap at 5, priority narrower > broader > related > cross_facet). Updated `.claude/commands/crew-browse.md` filtered-output mode to add "Related in other facets" section with ≤ 3 refinement suggestions. Documented the `cross_facet_related` field in `SCHEMA.md`. Final pipeline check: validator clean, build-index idempotent, build-graph idempotent, build-embeddings idempotent.

**Recommended order followed:** P4.1 (usage log foundation) → P4.4 (trending/freshness piggybacks on the log) → P4.3 (Librarian draft-time review) → P4.2 (coverage audit) → P4.5 (cross-facet SKOS). Usage log landed first because it's the foundation P4.4 and `graph.json`'s `frequently_paired_with` edges both depend on.

**Repo shape after Phase 4:**
- Layer 1 (source): `personas/*.md` (9 archetypes including The Librarian), `vocab/*.yml` (now with `cross_facet_related` on every tag), `SCHEMA.md` (documents cross-facet SKOS), `TEMPLATE.md`, `CONTRIBUTING.md`, `requirements.txt`
- Layer 2 (build artifacts, gitignored): `catalog.json`, `INDEX.md` (now with Signals section), `embeddings.sqlite`, `graph.json` (now populates `frequently_paired_with`), `.crew/usage.log` (new, JSONL), `.crew/signals.json` (new)
- Layer 3 (tooling): all prior scripts, plus `scripts/usage-log.py` (new), `scripts/deadwood-report.py` (new). `.claude/commands/crew-audit.md` (new). `.claude/commands/crew.md` (extended with Librarian step + usage logging). `.claude/commands/crew-review.md`, `crew-review-archetype.md` (extended with usage logging). `.claude/commands/crew-related.md`, `crew-browse.md` (extended with cross-facet SKOS). `scripts/validate.py` (extended with cross-facet checks). `scripts/build-index.py` (extended with Signals section). `scripts/build-graph.py` (extended to read usage log). `scripts/post-write-hook.py` (extended to run `usage-log.py signals` + rebuild index).
