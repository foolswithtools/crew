# Round 1 — Journey Critiques

Raw independent critiques of the 6 draft user journeys in `DESIGN.md`. Four archetype personas, run as parallel subagents, no cross-contamination.

This is also a dogfood of the Wrecking Crew pattern itself — the personas used here should eventually be first-class entries in the catalog.

---

## The Jobs-to-be-Done Theorist (exemplars: Christensen, Ulwick)

**Top-line verdict:** These aren't journeys — they're tasks dressed up as journeys. You've described *what people do with the catalog*, not *what job they're hiring the catalog to do*. Until you articulate the underlying progress the user is trying to make, you'll optimize the wrong things.

**Per-journey reactions:**
- **J1 (Seeker):** "Who do I need?" is the task. The job is probably *"help me make a decision/ship an artifact I won't regret, when I suspect my own thinking is incomplete."* The emotional dimension is huge and missing: fear of looking stupid, fear of shipping a blind spot, imposter anxiety. The social dimension: being able to say "I pressure-tested this against X school of thought" to a boss, a board, a co-founder. Those are the hiring criteria — not "3-5 personas surfaced."
- **J2 (Reviewer):** Round 1 / Round 2 is mechanics, not progress. What does *success* feel like? My guess: "I changed my mind about something specific," or "I found the one objection I hadn't considered." If the user runs the workflow and their artifact is unchanged, did the product do its job? You haven't said.
- **J3 (Contributor):** What job is the contributor hiring *contribution* to do? Reputation? Paying it forward? Scratching their own itch? Different jobs with different hiring criteria and failure modes. Don't collapse them.
- **J4 (Maintainer):** The clearest *task* of the six and probably fine as framed. Sometimes a task is just a task. Own it.
- **J5 (Browser):** Suspicious. Is anyone actually hiring a catalog for serendipity, or is this a designer's fantasy? What's the competing hire? Probably "ask a smart friend" or "do nothing and ship anyway." Prove browse is a real job.
- **J6 (Calibrator):** The job is almost certainly emotional — *"restore my trust in this tool after it let me down."* Frame it that way and the design changes: acknowledgment and visible follow-through, not a form.

**Reframe / add / cut:** Rewrite each journey as a progress statement: *"When ___, I want to ___, so I can ___."* Add functional/emotional/social dimensions. Cut J5 unless you can name the competing hire it beats.

**Sharp question:** *What do your users do today, right now, when they don't have The Wrecking Crew — and what would have to be true for them to fire that and hire you instead?*

---

## The Continuous Discovery PM (exemplars: Torres, Cagan)

**Top-line verdict:** Six journeys, zero evidence. These read like imagined users doing imagined things — you've mapped outputs (catalog, workflow, contribution flow) without naming a single outcome or the risk each journey tests. Before critiquing the journeys, I'd ask: have you watched five people *actually* try to find critics for their work?

**Per-journey reactions:**
- **J1 (Seeker):** The only journey with a real outcome lurking inside — "user makes a better decision after critique." But "3-5 personas with why-this-one reasoning" is a solution, not a hypothesis. What's the behavioral change? Do Seekers currently fail, and how? If they're already getting critique from ChatGPT with a one-line prompt, this journey is testing *value* — and you have no evidence they want curation.
- **J2 (Reviewer):** Round 1 → Round 2 is a ceremony you invented. Where's the observation that users want synthesis vs. just picking their favorite critique? Prototype it in a Google Doc with three humans before you build orchestration.
- **J3 (Contributor):** Who is this person? Name one. If you can't, cut it until someone asks to contribute. Contributor journeys are where catalogs go to die — built for imagined community that never arrives.
- **J4 (Maintainer):** Worse. Governance for a catalog that hasn't proven anyone uses it. Viability risk you're pretending isn't there.
- **J5 (Browser):** Assumed behavior. Do people browse expert catalogs, or do they arrive with a problem (J1)? 10:1 Browser is vestigial.
- **J6 (Calibrator):** Only valuable if J1/J2 are generating "that felt off" moments at volume. Premature.

**Reframe / add / cut:**
- **Collapse to two:** Seeker (J1+J2 fused — the actual job) and Calibrator (feedback loop that makes the catalog learn).
- **Add the missing journey:** the *Skeptic* — the user who tried it once and didn't come back. That's your outcome signal.
- **Cut J3, J4, J5** until you have 20 Seekers using it weekly.

**Sharp question:** What behavioral change in a Seeker — measurable in week three — tells you this catalog is worth maintaining, and what's the smallest prototype you can put in front of five real users *this week* to test it?

---

## The Contrarian Skeptic (exemplars: DHH, Jason Fried)

**Top-line verdict:** You're building a library management system before you've proven the library gets used. Four of these six journeys are catalog-maintenance overhead that only matters if the catalog is already succeeding — which you haven't established. Cut to J1 and J2. Ship that. Everything else is aesthetic.

**Per-journey reactions:**
- **J1 (Seeker):** The only journey that clearly earns its keep. But ask the honest question: is "3-5 personas with why-this-one reasoning" meaningfully better than pasting your artifact into a frontier model and asking "who would tear this apart?" If the LLM already nails 80% of this cold, your catalog's job is narrower — the curated 20%, not a full retrieval system.
- **J2 (Reviewer):** Real journey, real value. But watch the framework gravity — "independent critique then synthesis" is a process. Processes ossify. Keep it as a suggested pattern in the README, not a workflow engine.
- **J3 (Contributor):** How often does this actually happen? You're designing coherence tests for a problem you'll hit maybe forty times total. A human reviewing a PR handles this for free.
- **J4 (Maintainer):** The one I'd cut hardest. "Spot duplicates, catch drift, split blended personas" — curator LARP. With 44 personas, you can hold the catalog in your head.
- **J5 (Browser):** `ls personas/` already does this. A dimensional index is fine as a static file; don't build a browsing system.
- **J6 (Calibrator):** "File an improvement" implies a tracker, states, triage. Just edit the file. It's markdown in git.

**Reframe / cut:** Two journeys, not six. **Find** (J1) and **Run** (J2). J3 is "open a PR." J4 is "read your own catalog occasionally." J5 is `ls`. J6 is `git commit`. You don't have a catalog product — you have a folder of markdown, and that's the feature, not a limitation.

**Sharp question:** If tomorrow someone proved the frontier model, given only your README and naming conventions, produces critiques 90% as good as your full retrieval + round-robin system — would you still build the other four journeys? If yes, you're building for yourself, not users.

---

## The Information Architect (exemplars: Covert, Morville)

**Top-line verdict:** You've written six *tasks*, not six journeys, and you've done it before settling the vocabulary. "Persona," "archetype," "exemplar," "expert," "critic," "advisor" are all doing work in this brief — pick one controlled vocabulary or the catalog will ship the confusion.

**Per-journey reactions:**
- **J1 (Seeker):** "Which experts to ask" then "surfaces personas" — so is the object an expert or a persona? The Seeker's mental model is "who," your system's model is "archetype." That gap is the whole product. Where's the wayfinding that teaches the swap?
- **J2 (Reviewer):** Not a journey through the catalog — a *workflow on selected objects*. Belongs in a different plane. Don't let it smuggle structural claims (e.g., Round 1/Round 2 as baked-in rather than a consumer).
- **J3 (Contributor):** "Found a gap" — against what? A gap is only visible against a visible structure. If contributors can't see the dimensional shape of the catalog, they'll propose duplicates shaped like their favorite person. The coherence test is downstream; the *map* is upstream.
- **J4 (Maintainer):** The only journey that treats the catalog as a structured artifact. But "drift," "blend," "duplicate," "merge," "split" — name them. Make them first-class verbs with definitions, not folklore.
- **J5 (Browser):** Load-bearing and under-specified. *Which* dimensions? Who decided? Orthogonal or overlapping? This journey is where your facets live or die.
- **J6 (Calibrator):** "Felt off" is exactly the signal that a label or category is miscast. Feeds J4, not beside it. Calibration *is* maintenance.

**Reframe / add / cut:**
- **Add J0 — Orienteer:** "What kind of thing is this catalog, and what are its parts?" No journey works without this.
- **Cut J2** from this list — consumer of the catalog, not a journey through it.
- **Merge J6 into J4** as the feedback intake path.
- **Reframe J1 and J5** as the same journey seen from two entry points (known-need vs. unknown-need), both depending on the same facet system.

**Sharp question:** Before any of these journeys ship — what are the three to five **dimensions** along which personas are distinguishable, and can a new user name them after sixty seconds on the landing page? If not, J1 and J5 are fiction.
