# Journey: Seeker

The core journey. Validated against a concrete example (stock-chart ML classification idea) via role-play.

## Progress statement

*When I suspect my thinking on something I'm working on has blind spots I can't see, I want to brain-dump the idea and have a command reflect it back to me — sharpened — along with a proposed crew of archetypes who would pressure-test it from non-overlapping angles, so I can confirm the framing and kick off a critique with earned confidence.*

## The 4 sub-steps

1. **Capture** — user has been in conversation with Claude. At some point invokes a command (working name: `/crew`) to pivot from exploration into critique-setup. The input is the conversation so far, or a pasted/spoken brain-dump. Messy is expected.

2. **Read** — the command synthesizes a *problem framing* from the dump. Not keyword matching. It infers: what is the user actually trying to solve? What are the angles that matter for *this specific problem*? Which dimensions of the catalog are in play?

3. **Reflect** — the command outputs (format validated in role-play):
   - **Problem I'm hearing** — one paragraph restating the problem sharper than the user wrote it, with the underlying quieter question surfaced
   - **Where pressure-testing matters most at this stage** — 3-5 bulleted angles, specific to the problem (not generic)
   - **Suggested crew** — typically 4 archetypes, intentionally non-overlapping, each with a one-line "what they'd push on" quote
   - **Alternative swap** — one persona that didn't make the cut + *why* (named tradeoff, not hidden)
   - **Confirm or redirect** prompts — 2-3 explicit questions

4. **Confirm or redirect** — user replies conversationally. Either: "yes, go" (→ flows to Reviewer journey / Round 1) or "no, actually the real question is X" (→ reflection regenerates) or "swap person Y for Z" (→ crew adjusts).

## What's load-bearing (from the role-play)

- **Reflection is doing two jobs, not one.** It proves the system understood (trust), *and* it gives the user a first sharpening before critique even starts (the restated problem is itself a critique).
- **"Non-overlapping" is the key property of the crew.** A menu of 8 overlapping quants is useless; 4 archetypes chosen to attack from different angles is the product.
- **Specific beats generic.** "Your training window spans how many regimes?" is load-bearing. "A quant would look at your statistical assumptions" is noise. Archetype voices need to be specific enough that the preview *already* surfaces real concerns.
- **Named tradeoffs.** Showing the alternative swap with rationale respects the user — they can accept the editor's call or override it. Hiding rejected candidates is worse than surfacing them.
- **Exit on confirmation, not commitment.** The journey ends when the user confirms the framing. Running Round 1 is the Reviewer journey. Keep the boundary clean.

## Open sub-questions within Seeker

- **Reflection-wrong handling:** conversational refinement ("no, more like X") vs. direct edit of the reflection text? Current instinct: conversational — user is already in chat.
- **Team vs. menu:** role-play proposed a fixed crew of 4 with one swap option. Does this hold, or should there be a "menu of 8, pick 4" mode for users who want more agency? Current instinct: fixed crew is better UX, swap option handles the long tail.
- **How many archetypes:** 4 felt right for a meaty problem. Might be 3 for something narrower. Command should probably decide based on the problem, not default.
- **Where does retrieval actually happen:** in the role-play I invented archetypes. In a real run, the command needs to pull from `personas/` and match on dimensions. Does reflection happen before or after retrieval? Probably: read problem → pull candidate set → write reflection that uses the retrieved candidates as material.
- **Handoff to Reviewer:** "ready for Round 1?" — is this a separate command (`/crew review`) or a "yes" that flows into it? Current instinct: separate command so the user can pause and do something else between.

## Validated output format (for later codification)

```
Problem I'm hearing:
  [1 paragraph: restate sharper, surface the quieter question]

Where pressure-testing matters most at this stage:
  - [angle 1, specific to problem]
  - [angle 2]
  - [angle 3-5]

Suggested crew — N archetypes, intentionally non-overlapping:
  1. [Archetype] (school: exemplars) — "[voice line: what they'd push on]"
  2. [Archetype] (school: exemplars) — "[voice line]"
  ...

Alternative swap: [Archetype] (school: exemplars) — [why they didn't make the cut, what would bring them in]

Confirm or redirect:
  - Is the problem framed right?
  - Is this the right crew, or swap someone?
  - Ready for Round 1, or refine first?
```

## Example (from role-play)

User's input: idea for classifying 30-60 day stock chart images against forward 5-day returns (±5%/neither), augmented with macro/regime features (fed policy, trend age).

Problem I heard: not "can I build this" — rather, *is the hypothesis real or a dressed-up version of technical analysis that'll look great in backtest and die in live trading?* With the quieter question: *what do experienced traders actually "see" that I'd need to encode for this to be worth pursuing at all?*

Crew proposed:
1. The Chart-Reading Practitioner (O'Neil / Weinstein / Livermore) — "which patterns actually carry signal?"
2. The Rigorous Quant-ML Researcher (Lopez de Prado / Chan) — "triple-barrier labels? purged CV? point-in-time universe?"
3. The Regime-Aware Macro Thinker (Druckenmiller / Dalio) — "how many regimes in your training window?"
4. The Data-Honesty Skeptic (Silver / Taleb / Tetlock) — "what's your null?"

Swap offered: Factor-Explanation Quant (Fama / Asness) — "is this just momentum?" — held for post-prototype once there are returns to decompose.
