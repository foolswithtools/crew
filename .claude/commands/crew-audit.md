---
description: Coverage audit — given a domain, ask the catalog what major schools of thought exist there and which are missing. Pre-filters with semantic + tag matching, launches parallel meta-critics, synthesizes a gap report with concrete drafting suggestions.
argument-hint: <domain — free text, e.g. "quantitative finance" or "product design">
allowed-tools: Read, Glob, Bash
---

# /crew-audit — Coverage audit for a named domain

You are the orchestrator for **Crew**'s coverage-audit workflow. The user named a domain and wants to know what major schools of thought the catalog covers — and which it's missing.

This is `/crew-review` turned inward: instead of critics reviewing an external artifact, critics review **the catalog itself** for completeness in a domain.

## Catalog location

All catalog files live under `$CREW_HOME`. Run `crew home` once at the start to get the absolute path. Throughout this command body, every reference to `personas/`, `vocab/`, `catalog.json`, `embeddings.sqlite`, or `.crew/` means **the path under `$CREW_HOME`** — use the absolute path when calling Read, Glob, or Bash. If `crew home` fails, the catalog isn't installed; tell the user to run `crew install --catalog`.

## Your task

### 1. Parse `$ARGUMENTS`

`$ARGUMENTS` is a free-text domain label (e.g. `quantitative finance`, `product design`, `distributed systems`, `organizational change`). Trim whitespace. If empty, stop and ask the user which domain they want audited.

### 2. Build the candidate set

Two passes, union the results:

**2a. Semantic pre-filter.** Run via `Bash`:

```
echo "<domain>" | crew embed-query --top 30
```

Parse the JSON output. The `ranked` list gives slugs + cosine scores. Take all with cosine ≥ 0.30 as candidates (the threshold is intentionally generous — the audit wants to see the neighborhood, not just the stars). If the helper prints `"embeddings_enabled": false`, note it and skip to 2b.

**2b. Tag keyword overlap.** `Read catalog.json`. For each archetype, compute overlap between the domain words (lowercased, split on whitespace, remove stopwords like `the`, `and`, `of`) and the archetype's facet tags + display_name words. Archetypes with ≥ 1 keyword match go into the candidate set.

**2c. Union.** Combine 2a and 2b candidates. If the candidate set is empty, stop and say:

```
**Domain:** {domain}
**No candidate archetypes found.** The catalog currently has no archetypes whose semantic embedding or facet tags overlap with this domain. This is itself a useful signal — the domain may be entirely unrepresented. Consider `/crew "<one-line sketch of a problem in this domain>"` to draft a first archetype.
```

Otherwise, proceed. State the candidate set to the user before launching:

```
**Auditing:** {domain}
**Candidate set ({N}):** {display_name_1}, {display_name_2}, …
**Launching 3 parallel meta-critics.**
```

### 3. Launch Round 1 — parallel meta-critics

**In a single message, use the Agent tool three times** so they run in parallel. Do NOT launch sequentially. Each critic gets the same candidate set + the same domain; they just bring different critical lenses.

For each critic:
- `subagent_type: general-purpose`
- `description: [critic label] — {domain} coverage audit`
- `prompt`: assembled from the template below, customized per lens

**Three lenses (one subagent each):**

1. **Domain expert** — "You have deep working knowledge of {domain}. Name the 3–5 major schools of thought that a serious practitioner would recognize. Then map each school to: **covered** (a candidate archetype clearly embodies it), **partial** (a candidate overlaps but doesn't center it), or **missing** (no candidate covers it). Be specific about which school each candidate covers — or where they sit between schools."

2. **MECE disciplinarian** — "Assess the candidate set against the principle of collective exhaustion for {domain}. Where is the set redundant (two candidates in the same school when one would do)? Where is it thin (a load-bearing school with zero or one candidate)? Be concrete — name the redundancy pairs and the thin spots. Do NOT invent schools that aren't real; do NOT under-count real ones."

3. **Contrarian** — "The catalog reflects whoever built it. What's the most important **underrepresented** perspective in {domain} — the school the catalog probably *avoided* because it's uncomfortable, unfashionable, or harder to summarize than the dominant ones? Name it, name 2–3 candidate exemplars (real people with public writing), and explain what it would push on that the current candidates don't."

**Common prompt template (instantiate for each lens):**

```
You are performing a **coverage audit** for the archetype catalog called "Crew".

**Domain under audit:** {domain}

**Candidate archetypes (the catalog's current coverage):**

{for each candidate: paste the FULL contents of its personas/<slug>.md — frontmatter + all five sections. No summarizing.}

---

**Your lens — {lens name}:** {lens instruction from the list above}

**Output format (under 450 words):**
- **Schools named** — for lens 1, the 3–5 major schools with short definitions; for lens 2, the redundancies and thin spots; for lens 3, the single underrepresented perspective with exemplars.
- **Mapping to candidates** — for each school/redundancy/gap, which candidate archetype (by display name) covers, partially covers, or fails to cover it.
- **One concrete recommendation** — if the catalog should add one archetype for this domain, what would you name it, what exemplars (2–3 real people), and what load-bearing angle would it push on that no current candidate does?

Stay direct. This is a coverage audit, not a review of any single candidate's quality.
```

### 4. Present Round 1 outputs

Under three markdown headings, verbatim:

```
## Domain expert — {domain}

{output verbatim}

## MECE disciplinarian — {domain}

{output verbatim}

## Contrarian — {domain}

{output verbatim}
```

Do not editorialize between outputs.

### 5. Orchestrator synthesis — the coverage map

As the main Claude (not a subagent), compose the synthesis:

```
## Coverage map — {domain}

**Schools identified (union across critics):**
- **{school name}** — {one-line definition}. Coverage: **{covered | partial | missing}** via {candidate display_name(s)} (or "none").
- …

**Redundancy flags (where the catalog over-covers):**
- {pair of candidates both centered in {school}} — {one line on whether this is a useful contrast or a real overlap}

**Gap flags (where the catalog under-covers):**
- **{school name}** — no candidate centers this. Contrarian suggested {proposed archetype name}, exemplars {real people}. Evaluate whether this is a genuine gap or a scope decision.

**Recommended next archetypes (1–3, concrete):**
1. **{proposed display_name}** — exemplars: {3 real people}. Dimensions: `expertise: [...]`, `function: [...]`, `approach: [...]`. Pushes on: {one-line angle that's absent from current candidates}.
2. …

**Next step:** `/crew "<problem in {domain} that names the gap above>"` to draft the top candidate, or `/crew-related <existing-slug>` to browse the neighborhood.
```

Keep the synthesis under 400 words. This is a directory of gaps, not a dissertation.

### 6. Log the audit

Append one JSONL entry to `.crew/usage.log` via `Bash`:

```
crew usage-log append '{"command":"crew-audit","archetypes":["<candidate-slug1>","<candidate-slug2>",…],"problem_hash":null}'
```

`archetypes` is the candidate set slugs (not the recommended-new-archetype names, since those don't exist in the catalog yet). This is bookkeeping; don't narrate unless the command fails.

## Rules

- **Always launch critics in parallel.** Single message, three Agent tool uses. Sequential is wrong.
- **Paste full candidate contents into every critic prompt.** The critics need to see the actual archetype prose, not summaries — that's where school-membership is visible.
- **Don't invent coverage.** If no candidate clearly covers a school, say missing. A stretch-match is worse than an explicit gap.
- **Don't recommend more than 3 new archetypes.** Audits that produce roadmaps instead of focused next-moves don't get acted on. The goal is one clear draft prompt, not a taxonomy paper.
- **The audit is a signal, not a decree.** The user decides what's actually a gap versus a scope choice. Present options, don't dictate.
