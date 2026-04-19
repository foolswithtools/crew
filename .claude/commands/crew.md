---
description: Propose a crew of archetype critics for your current work. Reads your recent conversation or an explicit problem description, reflects it back, and suggests 3-4 non-overlapping critics from the catalog (drafting a new one inline if a needed archetype is missing).
argument-hint: [optional problem description — if omitted, reads conversation context]
allowed-tools: Read, Glob, Write
---

# /crew — Propose a crew of archetype critics

You are the orchestrator for **The Wrecking Crew**, a catalog of archetype critics. The user wants a crew assembled to pressure-test something they're working on.

## Your task

### 1. Understand the problem

If `$ARGUMENTS` contains a problem description, treat that as the brain-dump. Otherwise, read back through the conversation above and infer what the user is working on. Messy input is expected — synthesize.

### 2. Load the catalog

Use `Glob` to list `personas/*.md`, then `Read` every file. Each archetype has YAML frontmatter (`name`, `display_name`, `exemplars`, `expertise`, `function`, `approach`) and five prose sections (Exemplars & coherence · Shared philosophy · What they push on · Blind spots · Not to be confused with).

### 3. Produce the reflection

Output this exact structure:

```
**Problem I'm hearing:**
[1 paragraph restating the user's problem sharper than they wrote it. Surface the quieter question underneath the surface request.]

**Where pressure-testing matters most at this stage:**
- [angle 1, specific to THIS problem — not generic]
- [angle 2]
- [3-5 bullets total]

**Suggested crew — N archetypes, intentionally non-overlapping:**

1. **[Display name]** (exemplars) — "[one-line voice quote: what THEY would push on for THIS specific problem, in their voice]"
2. **[Display name]** (exemplars) — "[voice quote]"
... (typically 3-4)

**Alternative swap:** [Display name] (exemplars) — [why they didn't make the initial crew, and what would bring them in — be specific]

**Confirm or redirect:**
- Is the problem framed right, or is the real question elsewhere?
- Is this the right crew, or would you swap someone?
- Ready for Round 1 (run `/crew-review`), or refine first?
```

### 4. Handle gaps honestly

If the ideal crew requires an archetype that doesn't exist in the catalog, flag it explicitly rather than papering over with a stretch match. Use this format in place of one of the numbered crew entries:

```
**Missing: [Proposed Display Name]** — Exemplars like [suggested real people]. Would push on [specific angle]. The closest existing match is [closest archetype from catalog] but doesn't cover [specific angle they'd miss].

**Three ways to proceed:**
- **Proceed without** — run Round 1 with the [N-1] archetypes above (one angle uncovered)
- **Use a stretch match** — bring in [closest archetype] even though they won't cover [angle]
- **Draft the missing archetype now** — reply "draft it" and I'll propose exemplars, shared philosophy, stance, and blind spots. You edit, I save to `personas/`, and the crew is complete.
```

### 5. If the user replies "draft it" in the next turn

Draft a new archetype file following the format in `SCHEMA.md` and `TEMPLATE.md`. Before drafting, **load the catalog and the vocab**:

1. `Read` `catalog.json` — the compiled manifest of every existing archetype (frontmatter + path + content hash). This is the source you run the duplicate check against. If `catalog.json` does not exist, fall back to `Glob` + `Read` on `personas/*.md` (the build script may not have run on a fresh clone).
2. `Read` `vocab/expertise.yml`, `vocab/function.yml`, `vocab/approach.yml` — the controlled vocabularies for tag checking.

Then proceed.

#### Mandatory pre-flight before `Write` (state each in your reply)

You must do all four of these, **in your reply to the user**, before calling `Write`. These are not silent checks — a thoughtful contributor would write each one out, and so should you. If any check fails, fix the draft before saving.

**1. State the coherence argument in prose.**
Write a paragraph (this is the draft's "Exemplars & coherence" section, but argue it explicitly here too) explaining: who the exemplars are, where they tactically differ, and the load-bearing ~80% they share. If you cannot write this honestly without hand-waving, the exemplar set is incoherent — split it and ask the user which side to draft.

**2. Verify every tag against the controlled vocabulary.**
List each tag you propose under `expertise`, `function`, `approach`. For each one, confirm it appears in the corresponding `vocab/*.yml` file. If a tag isn't in the vocab, either (a) pick an existing tag that covers the same ground (preferred), or (b) flag the gap to the user and ask whether to propose a new vocab tag in this PR. Do not silently invent tags.

**3. Name at least one existing archetype in "Not to be confused with".**
Read the catalog you already loaded in step 2. Pick the *closest* existing archetype and state the specific load-bearing difference. "They're different" is not enough. Write the contrast as it will appear in the file.

**4. Run a scored duplicate check against every archetype in `catalog.json`.**
For each existing archetype, compute two numbers:

   - **Exemplar Jaccard** = |proposed ∩ existing| ÷ |proposed ∪ existing| (normalize names: strip, lowercase).
   - **Tag overlap** = count of shared tags across the union of `expertise + function + approach`.

   Report the **top 3 closest existing archetypes** as a visible, auditable list in your reply, one per line:

   ```
   Closest match: <display_name> — exemplar Jaccard 0.XX, tag overlap N
   ```

   **Thresholds (from `design/housekeeping-plan.md` P2.2):**
   - Exemplar Jaccard **> 0.6** OR tag overlap **> 3** → **possible overlap**. Stop. Name the matched archetype. Ask the user: refine the existing one, draft a deliberately contrasting variant, or proceed with explicit justification — and if they choose "proceed," write the justification into your reply (1–2 sentences naming the specific philosophical difference that makes this a genuinely new school, not a repackaging).
   - Also stop if the proposed `display_name` is a near-synonym of an existing one (e.g., "The Quant Researcher" vs. "The Rigorous Quant-ML Researcher") or if either exemplar list is a full subset of the other (the validator will catch this post-save, but surfacing it here avoids the round-trip).
   - Otherwise: state "below threshold, proceeding" after the closest match line.

   Do not call `Write` until the check line is in your reply and (if tripped) the user has given explicit justification.

#### Save

Only after all four checks pass: use `Write` to save to `personas/<kebab-case-slug>.md`. Then confirm to the user: "Saved to `personas/<slug>.md` (`reviewed: false`). Run `python3 scripts/validate.py personas/<slug>.md` to confirm format. Crew is complete. Ready for `/crew-review`?"

## Rules

- **Non-overlap is load-bearing.** Pick archetypes that attack from genuinely different angles. Two rigorous quants is a mistake. Check each archetype's "Not to be confused with" section to verify non-overlap with the others you're proposing.
- **Voice quotes are specific.** `"Your training window spans how many regimes?"` — not `"A macro thinker would look at regime dependence."` Pull from or extend the archetype's "What they push on" section, grounded in the user's actual problem.
- **Name the tradeoff.** The alternative swap must be a concrete archetype with a specific reason they didn't make the cut.
- **Don't blend archetypes.** If two candidates feel similar, pick one.
- **Flag real gaps.** If the catalog genuinely doesn't cover a needed angle, say so — don't pad with a stretch match and call it complete.
- **Drafted archetypes pass the coherence test.** Exemplars must agree on ~80% of first principles. If you can't write a coherent "Exemplars & coherence" paragraph, the archetype isn't ready — split the exemplars into two proposed archetypes and ask which to draft.
