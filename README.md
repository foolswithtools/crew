# The Wrecking Crew

A catalog of **archetype critics** you can invoke mid-conversation with Claude to pressure-test whatever you're working on. Two commands, two journeys:

- **`/crew`** — reads what you've been working on, reflects the problem back sharper, proposes 3-4 non-overlapping critics from the catalog. If a needed archetype doesn't exist, Claude drafts one inline and saves it in 2 minutes.
- **`/crew-review`** — launches the chosen crew as parallel subagents who tear into your work independently (Round 1). Optional Round 2 synthesis where they compare notes without collapsing into mush.

Named after [The Wrecking Crew](https://en.wikipedia.org/wiki/The_Wrecking_Crew_(music)) — the LA studio musicians who quietly played on most of the hits of the 60s-70s. Skilled craftspeople who made the star's work better without taking the spotlight. That's the pattern here: a deep bench of on-call experts who make *your* work better.

## How it works

Each archetype in `personas/` is a **school of thought** exemplified by 2-5 real people whose philosophies genuinely align. Not named celebrities — the catalog would be too big, and "a finance expert" is meaningless when Buffett and Burry think in fundamentally incompatible ways.

- **The Value Investor** (Buffett / Munger / Graham) is one archetype
- **The Contrarian Short-Seller** (Burry / Chanos) is a different archetype

Each archetype has a specific *voice* (what they push on), explicit *blind spots* (what they miss), and a "not to be confused with" contrast against adjacent archetypes — so a crew of 4 attacks your work from genuinely different angles without blending into mush.

## Try it end-to-end

See [`examples/stock-ml-use-case.md`](examples/stock-ml-use-case.md) — paste the scenario, run `/crew` and `/crew-review`, and exercise every journey including the inline-draft flow when the catalog has a gap.

## Your own use

Any time you're working on something in Claude Code and want critics:

```
> [describe what you're working on, or just keep having the conversation]

/crew
```

Claude proposes a crew. Confirm or redirect. Then:

```
/crew-review
```

Round 1 runs. You read four independent critiques. Accept Round 2 if you want them to synthesize.

## Add your own archetype

Copy [`TEMPLATE.md`](TEMPLATE.md) into `personas/<slug>.md` and fill it in. Or let `/crew` draft one inline the next time it hits a gap in the catalog.

The format and the coherence test (the rule that keeps the catalog from turning into mush) are documented in [`SCHEMA.md`](SCHEMA.md).

## Design philosophy

- **Archetype over celebrity.** The catalog lists schools of thought, not famous people. The people are exemplars who calibrate the voice.
- **Coherence over coverage.** Exemplars must share ~80% of first principles. Incoherent blends produce generic critique.
- **Non-overlap is load-bearing.** A crew is useful because its members attack from different angles. Two similar critics is a waste.
- **Contribution is demand-driven.** Archetypes get added when `/crew` discovers a real gap, not by someone populating categories. The catalog grows where pull exists.
- **Folder of markdown, not a product.** No tracker, no governance, no workflow engine. Just files, git, and two prompts.

## Docs

- [`SCHEMA.md`](SCHEMA.md) — archetype file format and the coherence test
- [`TEMPLATE.md`](TEMPLATE.md) — copy-paste template for a new archetype
- [`DESIGN.md`](DESIGN.md) — the full design doc, including the dogfooding session that shaped the product
- [`design/`](design/) — round-1 / round-2 critiques, the Seeker journey spec, pre-redesign archive
