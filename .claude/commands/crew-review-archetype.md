---
description: Review an unreviewed archetype for coherence, uniqueness, vocab alignment, and prose quality. Launches 3 existing archetypes as parallel critics of the target archetype itself, then synthesizes a promote / edit / reject recommendation.
argument-hint: <archetype-slug>  (e.g., classical-chartist)
allowed-tools: Read, Glob, Edit, Bash
---

# /crew-review-archetype — Promote an archetype from `reviewed: false` to `reviewed: true`

You are the orchestrator for **The Wrecking Crew**'s *archetype* review flow. The user wants an existing archetype file scrutinized by its peers before promotion.

This is the mirror of `/crew-review`: there, archetype critics critique *an external artifact*. Here, they critique *another archetype's file* for catalog quality.

## Your task

### 1. Identify the target

`$ARGUMENTS` is the kebab-case slug of the archetype under review (e.g., `classical-chartist`). Verify `personas/<slug>.md` exists; if not, stop and ask the user to name an existing archetype. `Read` the full file — you will paste its contents into every critic's prompt.

### 2. Pick 3 critic archetypes

Read `catalog.json` (fall back to `Glob` on `personas/*.md` if the artifact is missing). Pick **3 existing archetypes other than the target** as critics, prioritizing:

- **Diversity of approach** — spread across `approach` tags (e.g., one `rigorous`, one `contrarian`, one `pragmatic`). Three rigorous critics is a mistake.
- **Adjacency, not duplication** — archetypes the target archetype *mentions in "Not to be confused with"*, or that share 1-2 tags, are especially useful (they know the neighborhood).
- **Prefer `reviewed: true` critics** — they've been pressure-tested themselves.

State your picks with a one-line reason each before launching, so the user can redirect:

```
Picking as critics (say "swap X for Y" before I launch if you want different):
- The Data-Honesty Skeptic — rigorous + epistemology, reviews methodological coherence
- The Contrarian Simplicity Skeptic — contrarian + skeptical, pushes on whether this is really distinct
- The Information Architect — taxonomic + rigorous, reviews vocab alignment and prose clarity
```

If the user doesn't object, proceed.

### 3. Launch Round 1 — parallel subagents

**In a single message, use the Agent tool 3 times** (one per critic) so they run in parallel. Do NOT launch sequentially.

Each agent call:
- `subagent_type: general-purpose`
- `description`: `[Critic display name] reviews [target display name]`
- `prompt`: assembled from the template below

**Round 1 prompt template** (one per critic):

```
You are **[Critic Display Name]** ([exemplar names]).

[PASTE THE FULL CONTENTS of the CRITIC's personas/<slug>.md here — frontmatter through all five sections]

---

**Your task:** Another archetype in the catalog needs peer review before promotion from `reviewed: false` to `reviewed: true`. Read the candidate below in full, then critique it IN VOICE on four axes.

### Candidate under review

[PASTE THE FULL CONTENTS of the TARGET archetype's file here — frontmatter through all five sections]

---

**Review axes (all four, in order):**

1. **Coherence** — do the exemplars genuinely share ~80% of first principles, or is the grouping forced? Argue from the exemplars' actual public positions. Name specific tensions if any, and say whether they're tactical (ok) or foundational (split the archetype).
2. **Uniqueness** — does this archetype cover ground that existing archetypes don't? Name the closest neighbor you know of and the load-bearing philosophical difference. If the difference is just vocabulary, call that out.
3. **Vocab alignment** — do the `expertise` / `function` / `approach` tags actually match what the prose argues? Flag any tag that feels tacked on or missing.
4. **Prose quality** — are the "What they push on" bullets specific, in-voice, and falsifiable? Or are they generic ("they would care about rigor")? Same test for "Blind spots" and "Not to be confused with."

**Output format (under 400 words):**
- **Verdict in one word:** PROMOTE / EDIT / REJECT
- **Per-axis notes** — one short paragraph per axis (coherence, uniqueness, vocab, prose). For EDIT verdicts, name the specific edits that would flip it to PROMOTE.
- **One sharp question** you'd want answered before promotion.

Stay firmly in your own character. You are critiquing an archetype file *as yourself* — bring your philosophy to bear on catalog quality, not the candidate's take on external problems. Do NOT capitulate to seem reasonable.
```

### 4. Present Round 1 outputs

For each critic's output, present it under a markdown heading:

```
## Round 1 review — [Critic Display Name]

[agent output verbatim]
```

Do not editorialize between outputs.

### 5. Orchestrator synthesis + recommendation

After all three Round 1 outputs, write a synthesis as the main Claude (not a subagent):

```
## Orchestrator synthesis

**Verdict tally:** [e.g., 2× PROMOTE, 1× EDIT]

**Convergences (all 3 agree):**
- [bullet]

**Productive tensions (real disagreements):**
- [tension]

**Recommendation:** PROMOTE / EDIT / REJECT
- **If PROMOTE:** one sentence on why the crew converged.
- **If EDIT:** list the specific, minimal edits needed to unlock PROMOTE. Be concrete: "rewrite the third 'Blind spots' bullet to be specific instead of generic" not "improve prose."
- **If REJECT:** name the load-bearing reason (typically coherence or duplication). Suggest either splitting or merging with a named existing archetype.
```

Keep synthesis under 250 words.

### 6. If recommendation is PROMOTE — offer the flip

Ask:

> Flip `reviewed: false` → `reviewed: true` on `personas/<slug>.md` now? (yes / no)

If the user says yes, use `Edit` to change exactly the `reviewed: false` line to `reviewed: true` in `personas/<slug>.md`. Confirm the post-write hook will re-run the validator and rebuild the catalog automatically.

If the recommendation is EDIT or REJECT, do NOT offer the flip. Summarize the required edits (for EDIT) or the merge/split path (for REJECT) and hand back to the user.

### 7. Log the review

After the synthesis is in your reply (regardless of PROMOTE / EDIT / REJECT), append one JSONL entry to `.crew/usage.log` capturing the target and the critic trio. Run via `Bash`:

```
python3 scripts/usage-log.py append '{"command":"crew-review-archetype","archetypes":["<target-slug>","<critic1-slug>","<critic2-slug>","<critic3-slug>"],"problem_hash":null}'
```

Put the target first; the three critic slugs follow. This step is bookkeeping; do not narrate it unless the command fails.

## Rules

- **Always launch critics in parallel.** Single message, three Agent tool uses. Sequential is wrong.
- **Paste full archetype content for both the critic and the target.** The value comes from specificity — don't summarize either.
- **Critics stay in voice.** Each critic prompt must explicitly tell the agent to critique *as themselves*, not as a generic reviewer.
- **Only promote on a clear PROMOTE recommendation.** A split verdict (e.g., 1× PROMOTE, 1× EDIT, 1× REJECT) is an EDIT — the user should address concerns first.
- **Never flip `reviewed: true` → `reviewed: false`.** That's a different flow (demotion after an incident), out of scope here.
