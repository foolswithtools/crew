# The Wrecking Crew — Design Doc

Living doc capturing the vision and the principles that constrain the catalog. Updated as the shape changes; trimmed of historical deliberation that is now resolved.

---

## Status (last updated 2026-04-19)

**Shipped on `origin/main`:**
- **Catalog:** 9 archetypes in `personas/` — rigorous-quant-ml-researcher, regime-aware-macro-thinker, data-honesty-skeptic, classical-chartist, jobs-to-be-done-theorist, contrarian-simplicity-skeptic, continuous-discovery-pm, information-architect, the-librarian (meta-archetype for catalog hygiene)
- **Commands** in `.claude/commands/`: `/crew`, `/crew-review`, `/crew-review-archetype`, `/crew-browse`, `/crew-related`, `/crew-audit`
- **Scripts** in `scripts/`: `validate.py`, `build-index.py`, `build-embeddings.py`, `build-graph.py`, `semantic-duplicate-check.py`, `embed-query.py`, `usage-log.py`, `deadwood-report.py`, `post-write-hook.py`
- **Source-of-truth docs:** `SCHEMA.md`, `TEMPLATE.md`, `CONTRIBUTING.md`, `vocab/{expertise,function,approach}.yml` (SKOS within-facet + cross-facet)
- **Automation:** `.claude/settings.json` PostToolUse hook validates and rebuilds all derived artifacts on every persona Write/Edit
- **External deps:** `requirements.txt` (PyYAML, sentence-transformers, sqlite-vec, numpy) + gitignored `venv/`; hook re-execs through venv

**Derived artifacts (gitignored, auto-rebuilt):**
- `catalog.json` — machine manifest with content hashes
- `INDEX.md` — human browse, facet-grouped, with Trending / New / Unreviewed sections
- `embeddings.sqlite` — 384-dim MiniLM vectors via sqlite-vec
- `graph.json` — contrast edges, shared-exemplar edges, frequently-paired-with edges (from usage log)
- `.crew/usage.log` — JSONL invocation log (compacts to monthly aggregates past 90 days)
- `.crew/signals.json` — by-slug counts + last-invoked + trending top-5 + new-this-month

**In flight (Apr 2026):** distribution refactor — making the commands installable from any repo across Claude Code, Cursor, Codex, Windsurf, VS Code Copilot, plus an MCP server for Antigravity / Cline / Copilot CLI / Zed. Catalog data moves to `~/.wrecking-crew/`. Plan: `/Users/t/.claude/plans/read-plan-md-curious-hamster.md`.

---

## The simple version

**What this is:** a command that gets you good critics on demand while you're working in an agentic coding tool.

**Two journeys. Two commands.**

### Journey 1 — Get the Crew (`/crew`)

Mid-conversation with the agent on something → run the command → it reads what you've been working on, tells you what it thinks you're trying to pressure-test, proposes 3-4 critics who'd push on it from non-overlapping angles. You say yes or redirect. If a critic doesn't exist, the agent drafts one in 2 minutes inline and it joins the crew.

### Journey 2 — Run the Critique (`/crew-review`)

The chosen critics tear into your work independently (Round 1). You read the critiques. Optional Round 2 synthesis where they compare notes and propose a plan, holding their ground rather than collapsing to consensus.

### Supporting commands

- `/crew-browse` — facet-filtered table of contents
- `/crew-related <slug>` — explore from one archetype outward (contrasts, shared exemplars, semantic neighbors)
- `/crew-audit <domain>` — coverage audit; finds gaps in the catalog
- `/crew-review-archetype <slug>` — review an unreviewed archetype's coherence and quality

---

## Name & inspiration

Named after **The Wrecking Crew** — the LA studio musicians of the 60s-70s (Hal Blaine, Carol Kaye, Tommy Tedesco, Glen Campbell, and others) who played on an enormous share of the hits of that era, backing everyone from the Beach Boys to Sinatra to Sonny & Cher. Skilled, versatile craftspeople who worked *with* the famous name on the record — they weren't the face of the project, but they were the reason it hit.

That's the pattern this catalog aims for: a deep bench of on-call experts who make *your* work better, without taking the spotlight.

---

## Vision

A catalog of **archetype personas** — coherent schools of thought, each exemplified by 2-5 real people whose philosophies genuinely align — that you can quickly query ("who do I need for this problem?") and invoke to critique, stress-test, and refine your work.

Archetypes, not celebrities. The exemplars calibrate the voice; they aren't brands to invoke.

---

## Core principles

1. **Coherence test.** Exemplars inside one persona must agree on ~80% of first principles about *how* to approach their craft. If not, split them into separate personas. (Buffett + Munger = one persona. Buffett + Burry = two.)

2. **Preserve uniqueness.** The catalog grows by *schools of thought*, not by famous people. A domain might have 4-6 personas, not 50. Each persona explicitly contrasts with adjacent ones so invocations don't blend into mush.

3. **Retrieval is first-class.** The killer feature is "who do I need for this problem?" — answered quickly, with reasoning, suggesting a complementary mix rather than overlapping picks.

4. **Non-overlap is load-bearing.** A crew is useful because its members attack from different angles. Two similar critics is a waste. Round 2 synthesis is valuable because the critics held their ground in Round 1.

5. **Contribution is demand-driven.** Archetypes get added when `/crew` discovers a real gap during crew assembly, not by someone populating categories. The catalog grows where pull exists.

6. **Folder of markdown, not a product.** No tracker, no governance, no workflow engine. Just files, git, and a small set of commands.

---

## Decisions on record

These were decided through a dogfooding session that had four archetypes critique an earlier draft journey set. The raw deliberation is no longer load-bearing; the outcomes are:

- **Two journeys, not six.** Get the Crew + Run the Critique. Contribute, maintain, browse, calibrate, and orient are either inline sub-steps, filesystem operations, or fall out of the two real journeys.
- **Contribution is inline.** Adding an archetype happens inside Journey 1 when a gap is detected during crew assembly — the moment user motivation is highest. Not its own journey.
- **Seeker shape: Capture → Read → Reflect → Confirm/Redirect.** The Reflect step does double duty — proves understanding *and* sharpens the problem before critique starts. Fixed crew of ~4 non-overlapping archetypes with one named alternative swap.
- **Round 2 holds ground rather than collapsing.** The explicit "stay in character, don't capitulate to seem reasonable" instruction is what keeps synthesis productive. Without it, Round 2 collapses to consensus.
- **Provenance is part of the value.** The catalog's differentiation vs. raw LLM is partly *who you pressure-tested against* — felt authority and traceable schools of thought, not just critique quality.

---

## Pattern validation notes

From dogfooding the Wrecking Crew pattern on its own design:

- Round 1 stayed distinct. The four critiques did not blend — each read as its claimed archetype. First evidence the archetype-with-exemplars format produces differentiated critique.
- Round 2 did NOT degrade to mush. All four held their ground on specific points, engaged others' arguments directly, and produced concrete revised proposals. Tensions remained visible and productive.
- Subagents work well for Round 1 — natural parallelism, no cross-contamination, each stays in voice.
- Persona prompt shape that worked: name + exemplars + shared philosophy + what they push on + blind spots + stay-in-character instruction. These fields became the archetype format.

---

## Pointers

- **Format and coherence test:** [`SCHEMA.md`](SCHEMA.md)
- **Copy-paste template:** [`TEMPLATE.md`](TEMPLATE.md)
- **Contribute an archetype:** [`CONTRIBUTING.md`](CONTRIBUTING.md)
- **Worked example, end-to-end:** [`examples/stock-ml-use-case.md`](examples/stock-ml-use-case.md)
- **Distribution refactor plan:** `/Users/t/.claude/plans/read-plan-md-curious-hamster.md`
