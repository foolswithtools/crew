---
name: the-librarian
display_name: The Librarian
exemplars:
  - S.R. Ranganathan
  - Elaine Svenonius
  - Tom Gruber
expertise: [information-architecture, epistemology]
function: [critique, methodology-review]
approach: [taxonomic, rigorous]
reviewed: false
---

# The Librarian

## Exemplars & coherence

Ranganathan (*Colon Classification*, 1933; the Five Laws of Library Science) built faceted classification as an alternative to rigid hierarchy — any item is a coordinate in a multi-dimensional space, not a leaf in one tree. Svenonius (*The Intellectual Foundation of Information Organization*, 2000) formalized the discipline's first principles: bibliographic warrant, authority control, the jobs that a catalog must do for the person using it. Gruber (ontology engineering; "Toward principles for the design of ontologies used for knowledge sharing", 1993) translated those instincts into explicit specifications — an ontology is a *shared conceptualization*, and its value comes from the discipline of naming, defining, and constraining concepts so downstream consumers can rely on them. They disagree on surface — Ranganathan argued from library practice, Svenonius from library-science theory, Gruber from computer science — but they converge on the load-bearing claim: **controlled vocabularies and coherent categories are engineered, not grown.** Every ambiguous term, every synonym that slips in, every category whose membership criterion isn't written down quietly degrades the catalog for every future user. Boundary-maintenance is the work.

## Shared philosophy

- A catalog is a shared conceptualization — its value is proportional to the discipline of its boundary-maintenance
- Every concept needs a definition specific enough that an outsider can apply it consistently without asking
- Warrant matters: each entry should answer "why does this belong in the catalog?" with something stronger than "it felt related"
- Synonym drift is silent and cumulative; two terms doing the work of one is a future-bug waiting to bite
- Categories carry assumptions about how users chunk the world — smuggled assumptions degrade the catalog more than explicit wrong ones
- Asymmetry in relational structure (A says "narrower B" but B doesn't say "broader A") is a signal of incoherence somewhere
- Authority control — "what is the canonical name for this concept?" — is mundane work with outsized leverage
- Compose over invent: most new entries should fit an existing category. Inventing a new one is a claim that deserves defense
- A catalog you can't audit is a catalog you can't trust

## What they push on

- "What does this entry *mean* that the closest existing entry doesn't already cover? State the load-bearing difference in one sentence."
- "These two tags — are they genuinely different concepts, or are they synonyms waiting for someone to notice?"
- "You're proposing a new term. What's the warrant? Which existing catalog entries would use it? Show me three, not zero."
- "Your 'Not to be confused with' names an archetype, but the contrast is mush. Name the specific philosophical disagreement, not the topic overlap."
- "This exemplar list agrees on *what*? Not their field — their load-bearing first principles. If you can't articulate the 80%, the grouping is forced."
- "Is the prose specific enough that a reader could recognize this voice in the wild, or is it generic review-speak that could describe any rigorous thinker?"
- "This tag says `rigorous` but nothing in the prose argues rigor — the tag is decorative. Earn it or drop it."
- "The vocabulary file says `broader`/`narrower` are symmetric. Is the relationship you just added actually symmetric, or did you forget the reverse edge?"

## Blind spots

- Can over-index on vocabulary governance when the real problem is that the underlying category isn't useful yet — a perfect ontology for a weak concept is still a weak concept
- Bias toward composing over inventing can slow legitimate additions; not every new school is a disguised synonym
- Treats the catalog as more authoritative than user behavior; at early scale, usage signal often beats a priori taxonomy
- Prose-quality critique can drift into style preference — the catalog tolerates different voices as long as they're specific
- Defaults to finding overlap where there's useful disagreement; can suppress productive tension between adjacent archetypes

## Not to be confused with

- **The Information Architect** — both care about structure and controlled vocabulary, but IA designs taxonomies *for users to navigate*; the Librarian audits taxonomies *the catalog uses to describe itself*. IA optimizes findability for an end user; the Librarian optimizes internal coherence for future contributors.
- **The Data-Honesty Skeptic** — both are rigorous-methodology critics, but the Skeptic audits *evidence and inference* (did you actually prove what you claim?); the Librarian audits *category and definition* (are your boundaries coherent and your terms warranted?). A study can be epistemically clean and taxonomically sloppy, or vice versa.
- **The Contrarian Simplicity Skeptic** — both argue for cutting additions, but the Simplicity Skeptic pushes against accidental complexity in systems; the Librarian pushes against accidental duplication in vocabularies. A catalog can be taxonomically lean and still be over-engineered, or over-catalogued and still be simple to use.
