# The Wrecking Crew — Design Doc

Living doc capturing the vision and design decisions. Updated as we go.

---

## Status — MVP built and validated end-to-end (2026-04-18)

**Shipped:**
- 7 seed archetypes in `personas/`: rigorous-quant-ml-researcher, regime-aware-macro-thinker, data-honesty-skeptic, jobs-to-be-done-theorist, contrarian-simplicity-skeptic, continuous-discovery-pm, information-architect
- 2 slash commands in `.claude/commands/`: `/crew` (Seeker) and `/crew-review` (Reviewer with Round 1 + optional Round 2 + orchestrator meta-synthesis)
- Format spec (`SCHEMA.md`) and template (`TEMPLATE.md`) rewritten for the archetype-based model
- End-to-end test walkthrough: `examples/stock-ml-use-case.md`
- 49 pre-redesign personas preserved in `design/pre-redesign-archive/`

**End-to-end validation (stock-ML use case):**
- `/crew`: reflection sharp, non-overlap held, voice quotes specific, alternative swap offered — ✓
- `/crew-review` Round 1: parallel subagents fired, distinct voices, no blending — ✓
- `/crew-review` Round 2: productive tension preserved (e.g., Macro Thinker vs. Quant on macro-as-conditioning vs. macro-as-leakage-surface) — ✓
- Orchestrator meta-synthesis: convergences + tensions + concrete next step — ✓
- **Inline-draft flow: not auto-triggered** — Claude chose a 3-archetype crew from the catalog instead of flagging a missing Chart-Reading Practitioner. Defensible and realistic; the flow exists and can be user-triggered ("add a pattern-reader archetype").

**Open / parked items (in rough priority):**
- **Housekeeping & scale** — detailed phased plan at [`design/housekeeping-plan.md`](design/housekeeping-plan.md). Phase 1 starts next: validator script, CONTRIBUTING.md, controlled-vocabulary files, strengthened `/crew` draft pre-flight. Architecture is 3-layer (source → derived indexes → tooling), targets 10K+ archetypes, borrows from faceted classification (Ranganathan), SKOS, dbt's compile pattern, Backstage catalog model, graph relationships, usage signals.
- Vocabulary: still calling files in `personas/` but content says "archetype." Rename directory or leave — not blocking.
- Dimensions IA raised: can a new user name the 3-5 dimensions archetypes vary along in 60 seconds?
- Demand-moment evidence: does "I want critics on this" recur often enough to be a real product?

**To resume cold:**
1. Read this Status block and "The simple version" below
2. For the validated Seeker spec: `design/journey-seeker.md`
3. For dogfood evidence the pattern works: `design/round1-journey-critiques.md` and `design/round2-journey-synthesis.md`
4. To see the MVP in action: `examples/stock-ml-use-case.md`

---

---

## The simple version (canonical)

*After Round 1, Round 2, and a grounded Seeker role-play, stepping back to the minimum product.*

**What this is:** a command that gets you good critics on demand while you're working in Claude.

**Two journeys. Two commands.**

### Journey 1 — Get the Crew (`/crew`)

Mid-conversation with Claude on something → run the command → Claude reads what you've been working on, tells you what it thinks you're trying to pressure-test, proposes 3-4 critics who'd push on it from non-overlapping angles. You say yes or redirect. If a critic doesn't exist, Claude drafts one in 2 minutes inline and it joins the crew.

Full spec: [`design/journey-seeker.md`](design/journey-seeker.md).

### Journey 2 — Run the Critique (`/crew review`)

The chosen critics tear into your work independently. You read the critiques. Optional synthesis round where they compare notes and propose a plan.

Spec: TBD.

### What's explicitly *not* a journey

- **Contribute** → inline inside Journey 1 when there's a gap. Not a separate flow.
- **Maintain** → edit/delete files, `git commit`. No system.
- **Browse** → `ls personas/`. No system.
- **Calibrate** → edit the file after a bad run. No system.
- **Orient** → Journey 1's reflection shows newcomers the catalog through their own problem. No tour.

### What we actually need to build

- `/crew` command — reflect + propose + optional inline draft
- `/crew review` command — Round 1 + optional Round 2
- A consistent archetype file format so both commands can read them
- A small seed set of archetypes to prove it works

Everything else is git and markdown.

---

## Name & inspiration

Named after **The Wrecking Crew** — the LA studio musicians of the 60s-70s (Hal Blaine, Carol Kaye, Tommy Tedesco, Glen Campbell, and others) who played on an enormous share of the hits of that era, backing everyone from the Beach Boys to Sinatra to Sonny & Cher. Skilled, versatile craftspeople who worked *with* the famous name on the record — they weren't the face of the project, but they were the reason it hit.

That's the pattern this catalog aims for: a deep bench of on-call experts who make *your* work better, without taking the spotlight. Preserve in end-user README and repo framing.

---

## Vision

A catalog of **archetype personas** — coherent schools of thought, each exemplified by 2-5 real people whose philosophies genuinely align — that you can quickly query ("who do I need for this problem?") and invoke to critique, stress-test, and refine your work.

Archetypes, not celebrities. The exemplars calibrate the voice; they aren't brands to invoke.

---

## Core principles

1. **Coherence test.** Exemplars inside one persona must agree on ~80% of first principles about *how* to approach their craft. If not, split them into separate personas. (Buffett + Munger = one persona. Buffett + Burry = two.)

2. **Preserve uniqueness.** The catalog grows by *schools of thought*, not by famous people. A domain might have 4-6 personas, not 50. Each persona explicitly contrasts with adjacent ones so invocations don't blend them into mush.

3. **Retrieval is first-class.** The killer feature is "who do I need for this problem?" — answered quickly, with reasoning, suggesting a complementary mix rather than overlapping picks.

4. **Contribution-friendly, drift-resistant.** Anyone can add a persona via PR. A checklist + maintainer review prevents duplicates and catches personas that have drifted into incoherence.

---

## User journeys (DRAFT — to refine together)

### J1. Seeker — "Who do I need?"
I have a problem, question, plan, or artifact. I don't know which experts to ask. I want the catalog to surface 3-5 relevant personas with a one-line "why this one" for each, ideally suggesting a *complementary* mix (domain expert + critic + synthesizer) rather than three overlapping picks.

### J2. Reviewer — "Run the critique workflow"
I've picked personas (or accepted the suggestions). I want to run Round 1 (each gives independent critique in their voice, without blending) and Round 2 (they compare notes and converge on a plan or surface unresolved tensions).

### J3. Contributor — "Add a persona"
I've noticed a gap, or I have deep knowledge of a school of thought. I want to add a persona without accidentally duplicating an existing one, and I want the coherence test and format to be easy to follow.

### J4. Maintainer — "Keep the catalog healthy"
I review contributions. I need to spot duplicates, catch personas that have drifted (exemplars no longer cohere), split personas that have quietly blended two schools, and merge redundant ones.

### J5. Browser — "See what's here"
I want to skim the catalog by dimension (expertise, function, approach) to discover personas I didn't know I needed, or to understand the landscape of schools in a domain.

### J6. Calibrator — "Improve a persona"
I invoked a persona and the voice felt off — a blind spot was missing, an exemplar didn't fit, the contrast with a sibling persona wasn't sharp enough. I want to file a concrete improvement.

---

## Round 2 synthesis of the journeys (dogfood, continued)

Same four personas, each given all four Round 1 critiques. Full Round 2: [`design/round2-journey-synthesis.md`](design/round2-journey-synthesis.md).

### New convergences (all four, after seeing each other)

- **Cut J3/J4/J5/J6 as standalone journeys.** Uniform agreement. Speculative governance for an unproven catalog.
- **Add a "Skeptic/Bouncer" shadow journey** (PM's idea, adopted by JTBD and Skeptic) — instrument who tried once and didn't return. That's the honest outcome signal.
- **The Round 1/Round 2 critique workflow is not a journey through the catalog** — it's a usage pattern on selected archetypes. Belongs in a different plane (IA, Skeptic) or as a prompt template, not a workflow engine (Skeptic).
- **The "persona" object needs a better name.** Every voice wrestled with it. IA called it out as "archetypal critic" — persona has a UX meaning already.

### Productive tensions (not resolved — these are the real design choices)

1. **Vocabulary-first vs. prototype-first.** IA: you cannot test findability on a set whose members aren't comparable — smuggled taxonomies are worse than absent ones. CDPM: you settle vocabulary by watching five users fumble the words, not in a doc. Skeptic: 44 is small enough to scroll, no map needed yet. **Which of three FIRST moves?**
   - IA: name the 3-5 dimensions, retrofit all 44 files
   - CDPM: 5 switch interviews this week, no prototype
   - Skeptic: run 3 real decisions through the catalog manually in a Google Doc this afternoon
   - JTBD: 5 JTBD interviews with people who shipped something they later regretted
2. **Is the catalog meaningfully better than raw LLM?** Skeptic's "raw nails 80% cold." JTBD's counter (strong): attribution and the *social* job — "I pressure-tested against the Christensen school, not just 'an AI'" — is part of the hire, not frosting. The felt authority, not the words, is the value. Partial resolution: catalog's differentiation may be *provenance* not *critique quality*.
3. **Is the demand moment real and recurring?** (CDPM, Skeptic, JTBD all circle this.) If "my thinking is incomplete, seek critics" happens 2×/year per user, there is no product — regardless of quality. The real competitor is "ship it and hope."
4. **Does the archetype abstraction survive contact?** Skeptic's remaining concern: users may actually want *named individuals* (DHH, Christensen). The archetype layer may be the abstraction future-you pays for. Untested.
5. **J0 Orienteer: job, task, or baked-into-Seeker?** IA wants it standalone, JTBD folds it in, Skeptic and CDPM cut it.

### Converged revised journey set (where agreement is strong)

With tensions held open:

- **Seeker (core)** — *When I suspect my thinking has a blind spot before a decision I'll have to live with, I want to hire 2-4 archetypes to pressure-test it, so I can ship with earned confidence and name who I pressure-tested against.* (JTBD framing adopted; IA wants dimensional filtering inside, CDPM wants "48-hour material-decision change" as the outcome KPI, Skeptic wants it to ship as "search + pick.")
- **Critiquer / Reviewer (usage pattern, not journey)** — Round 1/Round 2 as a prompt template, not a workflow engine.
- **Bouncer / Skeptic (instrumented shadow journey, research-only)** — catch non-returners; the kill/keep signal.
- **Calibrator (fold J4+J6)** — sharpen or retire an archetype that underperformed. Deferred until Seeker has volume, but name the operations (split, merge, drift, gap) per IA.

**J0 Orienteer** remains a live question.

### My (orchestrator) read

The four are pointing at the same cliff from different sides. Vocabulary, evidence, simplicity, and jobs-to-be-done all compound — they don't force a single first move, but they *do* rule out "start building retrieval." The cheapest informative move combines elements of all four recommendations: pick 2-3 real decisions you've faced recently, manually run Seeker + Round 1/Round 2 against the current 44 personas in a Google Doc (Skeptic + CDPM), while writing down what vocabulary you had to invent on the fly (IA) and whether you felt dread-reduction (JTBD). One afternoon, exits with evidence on demand, vocabulary, and pattern value simultaneously.

---

## Round 1 critique of the journeys (dogfood)

Ran four archetype personas as parallel subagents against the 6 draft journeys. Full critiques: [`design/round1-journey-critiques.md`](design/round1-journey-critiques.md).

**Archetypes used:** JTBD Theorist (Christensen, Ulwick) · Continuous Discovery PM (Torres, Cagan) · Contrarian Skeptic (DHH, Fried) · Information Architect (Covert, Morville).

**Convergence across all four voices:**
1. **These are tasks, not journeys.** All four flagged it. The drafts describe *what users do with the catalog*, not the underlying job/progress/outcome. Each journey should be rewritten as a progress statement with functional + emotional + social dimensions.
2. **J1 (Seeker) and J2 (Reviewer) are the core.** J3, J4, J5, J6 are variously called "catalog-maintenance LARP," "built for imagined community," "premature governance," "vestigial." Strong case to defer or cut until the core is proven.
3. **Vocabulary is unsettled.** "Persona," "archetype," "exemplar," "expert," "critic," "advisor" all doing work. Must pick a controlled vocabulary *before* journeys can be finalized.
4. **The catalog's job vs. raw LLM is undefended.** If a frontier model given a README produces 80-90% as good a critique cold, what exactly is this adding? Needs an explicit answer.

**Sharpest unique points (one per voice, preserved because they don't blend):**
- *JTBD:* The real job is emotional — "I suspect my thinking is incomplete and I don't want to ship a blind spot." Current drafts miss this entirely. Add the social dimension too ("I pressure-tested this against X").
- *Discovery PM:* Zero evidence. Prototype the workflow in a Google Doc with three humans before building retrieval. Define the week-3 behavioral change that signals this is worth maintaining.
- *Skeptic:* You have a folder of markdown, not a catalog product — that's a feature, not a limitation. J3 = PR. J4 = read your own catalog. J5 = `ls`. J6 = `git commit`.
- *IA:* Add **J0 — Orienteer**: "What kind of thing is this catalog and what are its parts?" Nothing else works without this. Dimensions are upstream of every other journey — name them first.

**Implications:**
- Likely revise to a smaller journey set: J0 (Orienteer), J1 (Seeker), J2 (Reviewer), with Calibrator folded into contribution/maintenance.
- Vocabulary lock-in precedes journey finalization.
- Need an explicit statement of what the catalog adds over raw LLM prompting.
- Round 2 (synthesis) can stress-test these implications before we commit.

---

## Open decisions

- [ ] **FIRST move** — pick one (or hybrid): IA vocabulary-first, CDPM switch interviews, Skeptic manual Google Doc test, JTBD regret-shipping interviews. My read: hybrid manual-test captures all four signals cheapest.
- [ ] **Rename "persona"** — "archetype" (IA) or something else. Current term collides with UX usage. Needs deciding before docs stabilize.
- [ ] **What this adds over raw LLM** — current strongest answer: *provenance* and the *social/emotional job*, not critique quality. Confirm or revise.
- [ ] **Is the demand moment recurring?** Needs evidence — informs whether this is a product or a one-off pattern.
- [ ] **J0 Orienteer** — standalone journey (IA), folded into Seeker (JTBD), or cut (Skeptic/CDPM)?
- [ ] **Does the archetype abstraction earn its keep** vs. named individuals (Skeptic's remaining concern)?
- [ ] Persona/archetype file format (the atomic unit — highest-leverage decision)
- [ ] Schema / controlled vocabulary for dimensions (IA flagged as upstream of J1/J5)
- [ ] Retrieval mechanism (INDEX.md structure + slash command shape)
- [ ] Seed set — which 5-10 archetypes to build first to stress-test the format
- [ ] Invocation workflow docs (Round 1 / Round 2)
- [ ] Contribution rules (coherence test, duplicate check, split/merge criteria)

---

## Decisions made

- **Two journeys, not six.** Get the Crew + Run the Critique. Everything else (contribute, maintain, browse, calibrate, orient) is either an inline sub-step, a filesystem operation, or falls out of the two real journeys. See "The simple version" above.
- **Contribution is demand-driven, not speculative.** Adding an archetype happens inline inside Journey 1 when a gap is detected during crew assembly — the moment user motivation is highest. Not its own journey.
- **Seeker journey grounded and validated** via role-play against a concrete example (stock-chart ML idea). Full spec: [`design/journey-seeker.md`](design/journey-seeker.md). Key shape: **Capture → Read → Reflect → Confirm/Redirect.** The Reflect step does double duty — proves understanding *and* sharpens the problem before critique even starts. Fixed crew of ~4 non-overlapping archetypes with one named alternative swap.

---

## Pattern validation notes (meta)

From dogfooding the Wrecking Crew pattern on the journey design itself:
- **Round 1 stayed distinct.** The four critiques do not blend — each reads as its claimed archetype. First real evidence the archetype-with-exemplars format produces differentiated critique.
- **Subagents work well** for Round 1 — natural parallelism, no cross-contamination, each stays in voice.
- The persona prompt shape that worked: *name + exemplars + shared philosophy + what they push on + blind spots + stay-in-character instruction*. These fields may be the seed of the archetype format.
- **Round 2 did NOT degrade to mush.** All four held their ground on specific points, engaged others' arguments directly, and produced concrete revised proposals. Tensions visible and productive (vocabulary-first vs. prototype-first; raw LLM vs. provenance value). Evidence the pattern's synthesis phase works when the archetypes are well-differentiated to start.
- **The explicit "stay in character, don't capitulate to seem reasonable" instruction mattered.** Without it, Round 2 likely collapses toward consensus.
- **The Round 2 output structure that worked:** *agree (genuine) / hold ground (and why) / revised proposal / first move / one remaining concern.* Structure forces productive disagreement and a concrete takeaway.
- The orchestrator (the main assistant) still needs to do a final meta-synthesis. Four distinct proposals ≠ a plan. Worth capturing in the invocation workflow docs later.
