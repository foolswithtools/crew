# Archetype File Format

Every file in `personas/` is an **archetype** — a coherent school of thought exemplified by 2-5 real people whose philosophies genuinely align. This file defines the format.

## The coherence test (first principle)

Before writing an archetype, apply this test to the proposed exemplars:

> Could these exemplars sit on a panel and agree on ~80% of first principles about *how* to approach their craft?

If yes, they form a coherent archetype. If no, split them into separate archetypes.

- **Coherent:** Warren Buffett + Charlie Munger + Benjamin Graham → one archetype (value-investing lineage).
- **Incoherent:** Warren Buffett + Michael Burry → two archetypes. One buys quality businesses forever; the other shorts frauds and bubbles. The philosophies don't cohere.

The point of the archetype is to preserve the *uniqueness* of a school of thought. Blending incompatible philosophies produces generic mush.

## File layout

One archetype per file, at `personas/<kebab-case-slug>.md`.

## Frontmatter (YAML)

```yaml
---
name: <kebab-case-slug>        # matches filename, e.g., data-honesty-skeptic
display_name: The <Name>       # human-readable, e.g., "The Data-Honesty Skeptic"
exemplars:                     # 2-5 real people whose thinking this archetype channels
  - Full Name 1
  - Full Name 2
  - Full Name 3
expertise: [tag1, tag2, ...]   # domains of knowledge
function: [tag1, tag2, ...]    # what they do (critique, stress-test, falsify, etc.)
approach: [tag1, tag2, ...]    # how they show up (rigorous, contrarian, empirical, etc.)
reviewed: true                 # false for inline-drafted archetypes awaiting review
---
```

### Controlled vocabulary

The full controlled vocabulary lives in three source files, one per facet:

- [`vocab/expertise.yml`](vocab/expertise.yml) — domains of knowledge
- [`vocab/function.yml`](vocab/function.yml) — what the archetype does (critique, stress-test, etc.)
- [`vocab/approach.yml`](vocab/approach.yml) — how the archetype shows up (rigorous, contrarian, etc.)

Each file lists the allowed tags with a definition for each. The validator (`scripts/validate.py`) reads these files as the source of truth. These tags help `/crew` match archetypes to problems.

Adding a new tag is a deliberate act — see [`CONTRIBUTING.md`](CONTRIBUTING.md) for the proposal flow. Reuse an existing tag whenever it fits; the vocab is intentionally small and stays small.

## Required prose sections

After the frontmatter, five sections in this order:

### `# The <Display Name>`

Top-level heading uses the display name.

### `## Exemplars & coherence`

One paragraph naming the exemplars and the coherent thread that binds them. Acknowledge where they differ; make explicit what they *share* that justifies grouping them. This section is where the coherence test gets argued.

### `## Shared philosophy`

3-7 bullets naming the core beliefs that define this school. These must be specific enough to differ from adjacent archetypes. Generic philosophy ("value users," "be rigorous") is a smell.

### `## What they push on`

3-7 bullets naming the questions, challenges, and concerns this archetype characteristically raises. These are the *voice lines* that make the archetype useful as a critic. Specific beats generic: `"What's your out-of-sample protocol?"` beats `"They would care about validation."`

### `## Blind spots`

2-4 bullets naming what this archetype systematically misses or underweights. Every school has blind spots — making them explicit is what keeps a crew of archetypes honest, since different archetypes cover each other's blind spots.

### `## Not to be confused with`

1-3 bullets contrasting this archetype with *adjacent* ones in the catalog. This is load-bearing: it prevents `/crew` from proposing two similar archetypes, and prevents contributors from accidentally duplicating existing coverage. Name the specific difference, not just "they're different."

## Minimal example

See [`TEMPLATE.md`](TEMPLATE.md) for a ready-to-copy template.
