---
description: Show everything related to a single archetype — contrasts, shared exemplars, semantic neighbors, and vocab (SKOS) neighbors. Use to explore from one archetype outward; also useful before drafting to confirm non-duplication.
argument-hint: <slug-or-display-name>
allowed-tools: Read, Bash
---

# /crew-related — Show archetypes related to one

You are the orchestrator for "discover mode" navigation. The user named one archetype; show the neighborhood around it.

## Catalog location

All catalog files live under `$CREW_HOME`. Run `crew home` once at the start to get the absolute path. Throughout this command body, every reference to `catalog.json`, `graph.json`, `embeddings.sqlite`, or `vocab/` means **the path under `$CREW_HOME`** — use the absolute path when calling Read or Bash. If `crew home` fails, the catalog isn't installed; tell the user to run `crew install --catalog`.

## Your task

### 1. Resolve the target

`$ARGUMENTS` is either a kebab-case slug (e.g. `rigorous-quant-ml-researcher`) or a display name (e.g. `The Rigorous Quant-ML Researcher`). `Read catalog.json` and match in this order:

1. Exact `name` match against a catalog entry's `name` field.
2. Exact `display_name` match (case-insensitive) against a catalog entry's `display_name` field.
3. If neither: print the closest 3 candidates by string similarity and stop. Do not guess.

Once resolved, you have `target_slug` and `target_display_name`.

### 2. Gather the four neighborhoods

You'll assemble four sections. For each, note whether its underlying data is present and skip gracefully if not.

#### 2a. Contrasts (directed, from `graph.json`)

`Read graph.json`. Collect:
- **Outgoing:** every `edges.contrasts` entry with `from == target_slug`.
- **Incoming:** every `edges.contrasts` entry with `to == target_slug`.

If `graph.json` is absent, note "run `crew build` to populate contrasts" and skip 2a + 2b.

#### 2b. Shared exemplars (from `graph.json`)

Look at `edges.shares_exemplar` for any entry where `archetypes` contains `target_slug`. Extract the other archetype + the shared exemplar names. Show `target vs. other — shares: <names>`.

If nothing is shared, say so explicitly — it's a useful diagnostic that the catalog's exemplar sets are disjoint. Do not fabricate "most archetypes tend to share…" filler.

#### 2c. Semantic neighbors (from `embeddings.sqlite`)

Run via `Bash`:

```
crew embed-query --slug <target_slug> --top 5
```

The JSON's `ranked` list is already sorted by cosine similarity and excludes the target itself. If the output has `"embeddings_enabled": false`, say "embeddings not available (run `crew build`)" and skip this section.

Present each match as `- **<display_name>** — cosine {0.xx}`.

#### 2d. Vocab neighbors (SKOS — within- and cross-facet)

Read `vocab/expertise.yml`, `vocab/function.yml`, `vocab/approach.yml`. Walk two kinds of relationships:

**Within-facet (broader / narrower / related):**
1. For each tag in the target's facet list, collect the tag's `broader`, `narrower`, and `related` lists from the vocab (same-facet).
2. Find other archetypes in `catalog.json` whose facet list contains any of those related tags.
3. Record which SKOS relationship (broader / narrower / related) and which tag connected them.

**Cross-facet (`cross_facet_related`):**
1. For each tag in the target's facet list, read its `cross_facet_related` map. Keys are target facets; values are lists of tag slugs in that facet.
2. For each cross-facet tag found, find archetypes in `catalog.json` whose relevant facet list contains it.
3. Record the provenance as `cross_facet {neighbor_facet}:{neighbor_tag}` (the neighbor is in a *different* facet from the target's originating tag).

Present as: `- **<display_name>** — via {facet}:{target_tag} → {rel} {neighbor_tag}` for within-facet, or `- **<display_name>** — via {facet}:{target_tag} → cross_facet {neighbor_facet}:{neighbor_tag}` for cross-facet. Cap the section at 5 entries total, preferring in this priority order: narrower > broader > related > cross_facet.

### 3. Produce the reply

```
**{target_display_name}** (`{target_slug}`)
Exemplars: {ex1, ex2, …}
Facets: expertise {…} · function {…} · approach {…}

### Contrasts ({N} edges — M outgoing, K incoming)
**Outgoing** (this archetype pushes against):
- **{other_display_name}** — {reason, trimmed to ~140 chars}
- …
**Incoming** (these push against this archetype):
- **{other_display_name}** — {reason}
- …

### Shared exemplars ({N} pairs)
- {other_display_name} — shares: {exemplars}
  (…or "none — exemplar sets are disjoint.")

### Semantic neighbors (top 5 by cosine)
- **{other_display_name}** — cosine {0.xx}
- …

### Vocab neighbors (SKOS — within- and cross-facet)
- **{other_display_name}** — via expertise:{tag} → narrower {other_tag}
- **{other_display_name}** — via expertise:{tag} → cross_facet function:{other_tag}
- …

**Next:** `/crew-browse {inferred useful filter based on target's tags}` or `/crew "{one-line sketch problem this archetype would pressure-test}"`.
```

If a section has zero entries, include the heading with `_(none)_` rather than skipping it — users should see the structure even when an edge type is sparse.

## Rules

- **Don't invent edges.** If a relationship doesn't exist in `graph.json` or `vocab/*.yml`, don't fabricate one. Zero-count sections are fine and informative.
- **Trim reasons, don't paraphrase them.** Contrast reasons come from the `## Not to be confused with` sections; surface them verbatim (truncated with `…` if long). They are the load-bearing distinction text — paraphrasing loses the signal.
- **Semantic neighbors are signal, not ground truth.** Cosine is a rough distance; a neighbor with low cosine can still be the right complement or the wrong one. Present the scores and let the user decide; don't pre-rank by "most related" in prose.
- **Skip gracefully.** Missing `graph.json`, missing `embeddings.sqlite`, or a missing persona file should degrade the section, not fail the command.
