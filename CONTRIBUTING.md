# Contributing to The Wrecking Crew

This catalog only stays useful if every archetype is a coherent school of thought, not a stretched group of people who happen to share a tag. The format is simple, but the bar is real. This document is the bar.

> **Two flows, same destination.** If you're a maintainer with this repo cloned, edit `personas/` directly — the post-write hook validates and rebuilds derived artifacts on every save. If you're an end user (catalog installed at `~/.wrecking-crew/`), let `/crew` draft inline when it hits a gap; the file lands in `~/.wrecking-crew/personas/<slug>.md` and the slash command rebuilds your local catalog. Either way, opening a PR with the new persona file lands it in the upstream catalog.

## Who this is for

You should be contributing to this catalog if:

- You hit a real gap during `/crew` and want to fill it for next time
- You're a practitioner in a domain currently missing from the catalog
- You want to refine an existing archetype because the voice lines aren't sharp enough yet

You should *not* be contributing if you're trying to add your favorite famous person, build out a category for completeness, or import a list of "important thinkers" from somewhere. The catalog grows where pull exists.

## One-time setup (maintainer flow only)

End users don't need this — `crew install` handles their setup. For maintainers cloning the repo to add or edit archetypes:

```bash
uv venv venv --python 3.12
uv pip install -e . --python venv/bin/python3
```

This creates a repo-local venv, installs the `wrecking_crew` package editable (giving you `crew` and `crew-mcp` on the venv's PATH), and pulls in the embedding deps. The `venv/` directory is gitignored. The post-write hook in `.claude/settings.json` re-execs through `venv/bin/python3` when present; if the venv is absent, the core flow (validator, index, Jaccard dedupe) still works — just the embedding-related steps gracefully degrade.

## How to add an archetype by hand

There are two paths. Both end at the same validator.

### Path A — let `/crew` draft it

Use the catalog normally. When `/crew` says "Missing: …", reply `draft it`. `/crew` will propose the frontmatter, write all five prose sections, save it, and run the validator. Edit the file, re-run the validator, open a PR.

### Path B — write it yourself

1. **Copy the template.** `cp TEMPLATE.md personas/<your-slug>.md`. Slug is kebab-case, matches the `name` field.
2. **Apply the coherence test before you start writing.** Pick 2-5 real exemplars. Ask: *could these people sit on a panel and agree on ~80% of first principles about how to approach their craft?* If you hesitate, the archetype is incoherent — split it. See [`SCHEMA.md`](SCHEMA.md) for the test in detail.
3. **Fill in the frontmatter.** Pick tags only from the controlled vocabulary in [`vocab/expertise.yml`](vocab/expertise.yml), [`vocab/function.yml`](vocab/function.yml), and [`vocab/approach.yml`](vocab/approach.yml). If nothing fits, see "Proposing a new tag" below.
4. **Write all five prose sections** with real specificity, not placeholders. The format is in [`SCHEMA.md`](SCHEMA.md).
5. **Run the validator.** `crew validate personas/<your-slug>.md` (maintainer flow inside the source repo) or `crew validate $(crew home)/personas/<your-slug>.md` (end-user flow). Exit code 0 = pass. Fix any errors; warnings are advisory but worth investigating.
6. **Open a PR.** See "Review criteria" below for what reviewers will look at.

## The coherence test (non-negotiable)

> *Could these exemplars sit on a panel and agree on ~80% of first principles about how to approach their craft?*

This is the single rule that keeps the catalog from turning into mush. The point of an archetype is to preserve the *uniqueness* of a school of thought. Blending incompatible philosophies produces generic critique that doesn't help anyone.

- **Coherent:** Buffett + Munger + Graham → one archetype (value investing).
- **Incoherent:** Buffett + Burry → two archetypes. One buys quality forever; the other shorts frauds and bubbles. The philosophies don't cohere.

Your "Exemplars & coherence" section is where you argue this in prose. Acknowledge where exemplars differ; make explicit what they *share*.

## The non-duplication expectation

Before you write, check that you're not duplicating an existing archetype:

1. **Skim the existing display names.** `grep display_name personas/*.md`.
2. **Skim the existing exemplars.** `grep -A 5 exemplars personas/*.md`. If your proposed exemplars overlap heavily with an existing archetype's, you're probably about to write a duplicate.
3. **Read the closest existing archetype's "Not to be confused with" section.** It often already names the contrast you'd be drawing.

Then, in your own "Not to be confused with" section, name at least one adjacent archetype from the catalog and explain the *specific* difference. Not "they're different" — what is the load-bearing distinction?

The validator catches the easy cases (duplicate `name`, fully-contained exemplar lists). It can't catch a thoughtful-but-redundant archetype. That's the reviewer's job.

## Review criteria for PRs

Reviewers will check:

- **Validator passes.** `crew validate` returns 0 with no errors. Warnings are explained in the PR description.
- **Coherence test holds.** The "Exemplars & coherence" paragraph genuinely argues the ~80% agreement, doesn't paper over a real philosophical split.
- **Voice lines are specific.** "What they push on" reads as something *this archetype* would say, not something any rigorous person would say. `"What's your out-of-sample protocol?"` beats `"They would care about validation."`
- **Blind spots are honest.** Every school misses something. If you can't name what this one misses, you don't understand it well enough yet.
- **"Not to be confused with" is load-bearing.** Names ≥ 1 existing adjacent archetype with a specific contrast.
- **Tags reuse existing vocab.** New vocab proposals are in a separate PR or clearly justified inline (see below).
- **`reviewed: false` for hand-drafted archetypes** until a maintainer reviews. `/crew` drafts default to `false` automatically.

## Proposing a new controlled-vocab tag

The vocabulary is intentionally small. Most contributions should reuse what's there. If you genuinely need a new tag:

1. **Confirm nothing fits.** Read [`vocab/expertise.yml`](vocab/expertise.yml), [`vocab/function.yml`](vocab/function.yml), and [`vocab/approach.yml`](vocab/approach.yml) end to end. Most "I need a new tag" moments dissolve here.
2. **Write a one-sentence definition.** If you can't define cleanly what falls inside vs. outside the new tag, it isn't a tag yet — it's a fuzzy intuition.
3. **Add the tag to the right vocab file** with `label`, `definition`, and empty `broader` / `narrower` / `related` stubs (these get filled in Phase 2). Keep the entry in alphabetical-ish order with adjacent peers.
4. **Justify it in the PR.** One sentence: what archetype needs this tag, and why no existing tag covers it. Reviewers will push back if a near-synonym already exists.

A new tag should land in the same PR as the archetype that needs it, so the cost and the value are visible in the same diff.

## When in doubt

Open a draft PR and ask. The cost of a half-baked archetype landing in the catalog is much higher than the cost of a conversation before merging.
