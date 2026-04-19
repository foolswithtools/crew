---
description: Browse the archetype catalog by facet filter. No args = facet/tag table of contents; `facet:value` filters return matching archetypes. Supports AND across facets and OR within a facet (comma-separated values).
argument-hint: [facet:value[,value]]* — e.g. `expertise:statistics approach:rigorous`
allowed-tools: Read
---

# /crew-browse — Faceted catalog browse

You are the orchestrator for catalog navigation. The user wants to see what's in the catalog at a given slice.

## Your task

### 1. Parse `$ARGUMENTS`

Each argument is `<facet>:<value>` or `<facet>:<v1>,<v2>,<v3>`. Valid facets: `expertise`, `function`, `approach`. Values are tag slugs (kebab-case). Examples:

- `$ARGUMENTS = ""` → no filter; produce the table of contents (step 3a).
- `$ARGUMENTS = "expertise:statistics"` → one facet, one value.
- `$ARGUMENTS = "expertise:statistics,forecasting approach:skeptical"` → two facets; within `expertise` it's OR, across facets it's AND.

Normalise each value to kebab-case. If an argument isn't `facet:value` shape, or the facet isn't one of the three, stop and tell the user the syntax you expected.

### 2. Load the catalog

`Read catalog.json`. It's an array of archetype entries, each with `name`, `display_name`, `exemplars`, `expertise`, `function`, `approach`, `reviewed`.

If `catalog.json` is absent, tell the user to run `python3 scripts/build-index.py` and stop.

### 3. Produce the browse view

#### 3a. No filter (table of contents)

If `$ARGUMENTS` is empty, group by facet and count archetypes per tag. Use this shape:

```
**Catalog — {N} archetypes across 3 facets.**

**Expertise** ({total unique tags used})
- `<tag>` ({count}) — {display_name}, {display_name}, …
- ...

**Function** ({total unique tags used})
- `<tag>` ({count}) — …

**Approach** ({total unique tags used})
- `<tag>` ({count}) — …

**Unreviewed:** {display_name}, …   (or "none" if every archetype has `reviewed: true`)

_Filter: `/crew-browse facet:tag` to narrow._
```

Only list tags that have ≥ 1 archetype — don't enumerate empty vocab entries.

#### 3b. With a filter

An archetype passes if, for every facet in the filter, at least one of the facet's filter values appears in the archetype's facet list. (AND across facets, OR within.) Return:

```
**Filter:** expertise ∈ {statistics, forecasting}, approach ∈ {skeptical}
**Matches (N):**

- **{display_name}** ({exemplars, comma-separated}) — {facet}: {matching tag(s)}; {other relevant facet}: {tag(s)}
- ...
```

Sort matches by `display_name`. For each match, show the exemplars (to help the user picture the school) and the tag(s) that matched in each filter facet, plus the other-facet tags so the user can see the full classification at a glance.

If zero matches, say so and suggest a relaxation — drop the strictest facet and show what would match:

```
**Filter:** expertise ∈ {machine-learning}, approach ∈ {contrarian} — no matches.
Dropping `approach:contrarian` would yield: {display_name} ({exemplars}).
```

### 4. Suggest a next step

End with one line pointing at the next useful command:

- If the user is browsing wide, suggest `/crew-related <slug>` on a match.
- If they filtered down to 1-2 archetypes, suggest `/crew` to actually bring them into a crew for a specific problem.

## Rules

- **Facet names are literal.** `expertise`, `function`, `approach` — nothing else. If someone writes `domain:` or `topic:`, stop and map it back to one of the three or ask.
- **Tag values are kebab-case slugs.** Strip surrounding whitespace; lowercase; accept `machine-learning` not `Machine Learning`.
- **Don't fabricate tags.** Only surface tags that actually appear in `catalog.json`. If a user filters on a tag no archetype has, report 0 matches and suggest the nearest-spelled existing tag.
- **Be diffable, not chatty.** This command answers the question; no preamble about what browsing is.
