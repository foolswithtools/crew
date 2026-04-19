# Example: pressure-testing a stock-ML idea

Walk through this scenario to exercise every journey end-to-end: **Seeker** (propose crew) → **inline Contributor** (draft a missing archetype) → **Reviewer Round 1** (independent critique) → **Reviewer Round 2** (synthesis) → **meta-synthesis**.

## The scenario (paste into Claude)

Copy the block below into a Claude Code session in this repo, then run `/crew`.

> I've been kicking around an idea for a while. I want to take a bunch of historic stock data and create a bunch of small charts — little slices of 30 to 60 days across a broad universe of stocks — and then classify each one as to whether the stock went up 5%, down 5%, or neither over the next five trading days. The hypothesis is that I can use ML image classification to do chart pattern matching, since so many traders use charts to decide whether a stock is going up or down.
>
> The twist I've been thinking about: traders don't just read the chart. They carry context in their head — is the Fed easing or tightening? What's the market regime — bullish, bearish, choppy? How long has the current trend been running? So I'm thinking I might codify some of that context and include it as features alongside the chart images.
>
> I want to pressure-test this before I sink time into building it. Is the hypothesis real, or am I about to build something that overfits a backtest and dies in live trading?

## Expected flow

### Step 1 — run `/crew`

Claude should:

- Reflect the problem back, surfacing the quieter question (is this hypothesis real, or dressed-up technical analysis that will overfit?)
- Name 3-5 angles that matter for *this* problem (hypothesis soundness, experimental rigor, regime dependence, edge vs. known factors)
- Propose a crew of 4 archetypes from the catalog — but only 3 actually exist:
  - **The Rigorous Quant-ML Researcher** (Lopez de Prado / Chan / Carver) — methodology, labels, purged CV
  - **The Regime-Aware Macro Thinker** (Druckenmiller / Dalio / Soros) — regimes in the training window
  - **The Data-Honesty Skeptic** (Silver / Taleb / Tetlock) — nulls, overfitting, out-of-sample
  - **Missing: The Chart-Reading Practitioner** — exemplars like William O'Neil, Stan Weinstein, Jesse Livermore — "is the hypothesis even right? Which patterns actually carry signal?"
- Offer three forks: proceed without, stretch match, or draft inline

### Step 2 — reply `draft it`

Claude should:

- Propose exemplars + shared philosophy + stance + blind spots + "not to be confused with" for the Chart-Reading Practitioner
- Write `personas/chart-reading-practitioner.md` with `reviewed: false` in frontmatter
- Confirm the crew is complete and ready for `/crew-review`

### Step 3 — reply `go` (or any confirmation)

Just tells Claude the crew is confirmed. No tool calls yet.

### Step 4 — run `/crew-review`

Claude should:

- Confirm: "Launching 4 parallel Round 1 critiques with [list]. Proceeding."
- Fire **4 Agent tool calls in a single message** (parallelism visible in the tool-use pane)
- Present 4 critiques under headings, each in the archetype's voice:
  - Chart-Reading Practitioner reads about patterns, volume, stage analysis
  - Data-Honesty Skeptic reads about nulls, multiple comparisons, out-of-sample
  - Quant-ML Researcher reads about triple-barrier labels, purged CV, point-in-time universes
  - Macro Thinker reads about regimes, liquidity, what breaks when the joint distribution shifts
- Ask about Round 2

### Step 5 — reply `yes`

Claude should:

- Fire **4 parallel Round 2 Agent tool calls**, each archetype receives all four Round 1 outputs
- Present 4 synthesis outputs using the structure: genuine agreement · where I hold ground · revised proposal · first move · remaining concern
- Tensions should be visible (e.g., pattern-reader vs. skeptic on whether charts carry signal; methodology-focused quant vs. regime-aware macro on what's load-bearing)
- Write a brief orchestrator meta-synthesis: convergences · productive tensions · one recommended next step

### Step 6 — verify

- `personas/chart-reading-practitioner.md` exists on disk
- Voices in both rounds are genuinely distinct (not homogenized into "a thoughtful critic")
- Round 2 did not collapse into smooth consensus — real disagreements were preserved

## What this validates

- **Seeker:** problem reflection, non-overlapping crew proposal, explicit gap flagging
- **Inline Contributor:** drafting a new archetype mid-flow without breaking momentum
- **Reviewer Round 1:** parallel independent critique with distinct voices
- **Reviewer Round 2:** synthesis that preserves tension
- **Meta-synthesis:** orchestrator identifies convergences + tensions + next step

If all five validate, the MVP works. If any fail, the failure mode is usually recoverable by strengthening the stay-in-character / non-overlap / gap-honesty instructions in the slash command prompts.

## After you run it

Try your own problem. Run `/crew` mid-conversation on something real you're working on. Gaps you hit are opportunities to grow the catalog — draft inline, and the archetype is there for the next use.
