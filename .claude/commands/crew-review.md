---
description: Run Round 1 independent critique with your chosen crew, followed by optional Round 2 synthesis. Launches each archetype as a parallel subagent so voices stay distinct.
argument-hint: [optional comma-separated archetype slugs — if omitted, uses the crew from the most recent /crew output]
allowed-tools: Read, Glob
---

# /crew-review — Run critique with the chosen crew

You are the orchestrator for **The Wrecking Crew**'s critique workflow. The user has a chosen crew (from a prior `/crew` call in this conversation, or passed as arguments) and an artifact to critique.

## Your task

### 1. Identify the crew and the artifact

- **Crew:** if `$ARGUMENTS` contains archetype names (comma or space-separated, matching files in `personas/`), use those. Otherwise, look back through the conversation for the most recent `/crew` output and use the archetypes the user confirmed.
- **Artifact:** what the user has been working on — the code, plan, idea, or document being pressure-tested. Infer from conversation. If ambiguous, ask the user before proceeding.

Load each crew member's full archetype file from `personas/<slug>.md` using `Read`. You will paste the *full content* into each subagent's prompt — do not summarize.

### 2. Brief the user before launching

Say something like: "About to launch [N] parallel Round 1 critiques with [list of display names]. Each will produce ~400 words of independent critique. Proceeding."

### 3. Launch Round 1 — parallel subagents

**In a single message, use the Agent tool N times** (one per crew member) so they run in parallel. Do NOT launch them sequentially.

Each agent call:
- `subagent_type: general-purpose`
- `description`: `[Archetype name] Round 1 critique`
- `prompt`: assembled from the template below

**Round 1 prompt template** (one per archetype):

```
You are **[Display Name]** ([exemplar names]).

[PASTE THE FULL CONTENTS of personas/<slug>.md here — frontmatter through all five sections]

---

**Context:** The user is working on the following, and has asked for your critique.

[Concise summary of the artifact — code, plan, idea, etc. If it's a document or longer artifact, paste it verbatim or the most load-bearing excerpt.]

---

**Your task:** Critique this in character. Stay firmly in voice — do NOT hedge or cover all angles. Give your characteristic take. This is Round 1 *independent* critique; a synthesis round with other archetypes comes later, but your job right now is to sound like [Display Name] and no one else.

**Output format (under 400 words):**
- **Top-line verdict** (1-2 sentences)
- **Specific critique points** (bullets — where this artifact is weak or missing something, in voice)
- **One sharp question** you'd ask the user before they ship this

Stay in character. Don't capitulate to seem reasonable.
```

### 4. Present Round 1 outputs

For each agent output, present it under a clear markdown heading:

```
## Round 1 — [Display Name]

[agent output verbatim]
```

**Do not editorialize between archetype outputs.** You are the orchestrator, not a voice. The user reads the raw critiques.

### 5. Offer Round 2

After all Round 1 outputs are presented, ask:

> Round 1 complete. Run Round 2 synthesis? Each archetype will see all four critiques and produce their convergence/tension response. (yes / no / skip)

Wait for user response.

### 6. If user says yes — launch Round 2

**In a single message, use the Agent tool N times again, in parallel.** Each agent:
- Same archetype identity (re-paste the full file contents)
- Receives ALL Round 1 outputs (including their own)
- Produces a synthesis in voice using the Round 2 output structure

**Round 2 prompt template** (one per archetype):

```
You are **[Display Name]** ([exemplar names]).

[PASTE THE FULL CONTENTS of personas/<slug>.md]

---

**Context:** You just ran Round 1 — independent critique — alongside three other archetype critics. Below are all four Round 1 outputs, including yours. Read them, then produce your Round 2 synthesis.

---

### Round 1 — [Display Name A]
[paste Round 1 output A verbatim]

### Round 1 — [Display Name B]
[paste Round 1 output B verbatim]

### Round 1 — [Display Name C] (YOU)
[paste your own Round 1 output verbatim]

### Round 1 — [Display Name D]
[paste Round 1 output D verbatim]

---

**Your task — Round 2 synthesis, in voice:**

1. **Where you genuinely agree** with the others — be honest, don't manufacture agreement
2. **Where you hold your ground** — don't capitulate to seem reasonable; explain *why* from your philosophy
3. **Your proposed revised recommendation** — concrete, not abstract
4. **What the team should do FIRST** — one move, not a roadmap
5. **One remaining concern** you don't think anyone nailed

Stay firmly in character. The value of Round 2 is productive tension plus a concrete proposal, not smooth consensus.

**Output under 500 words.**
```

### 7. Present Round 2 outputs

Same format:

```
## Round 2 — [Display Name]

[agent output verbatim]
```

### 8. Meta-synthesis (your job as orchestrator)

After all Round 2 outputs are presented, write a brief orchestrator synthesis as the main Claude (not a subagent). Section:

```
## Orchestrator synthesis

**Convergences (all N agree):**
- [bullet]
- [bullet]

**Productive tensions (real disagreements worth preserving):**
- [tension 1: who holds what, and why it's worth holding open]
- [tension 2]

**Recommended next step (one):**
[one concrete move, informed by the full critique — not a roadmap]
```

Keep this section under 250 words. You're summarizing, not adding another voice.

## Rules

- **Always launch subagents in parallel.** Single message, multiple Agent tool uses. Sequential is wrong.
- **Paste full archetype content into each subagent prompt.** Do not summarize. The differentiation comes from specificity.
- **Stay in character is load-bearing.** Every subagent prompt must explicitly say "stay firmly in character" and "don't capitulate to seem reasonable."
- **Orchestrator doesn't critique.** You do not add your own voice to Round 1 or Round 2. You only write the final meta-synthesis.
- **Match Round 2 participants to Round 1.** If Round 1 had 4 archetypes, Round 2 has the same 4. Don't add or drop archetypes between rounds.
