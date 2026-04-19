# Archetype Template

Copy this to `personas/<your-slug>.md` and fill in. See [`SCHEMA.md`](SCHEMA.md) for the format spec and the coherence test.

```markdown
---
name: archetype-slug
display_name: The Archetype Name
exemplars:
  - Person One
  - Person Two
  - Person Three
expertise: [domain1, domain2]
function: [critique, stress-test]
approach: [rigorous, skeptical]
reviewed: false
---

# The Archetype Name

## Exemplars & coherence

[1 paragraph: name the exemplars and the coherent thread that binds them. Acknowledge differences but make explicit the ~80% first-principles agreement that justifies grouping them.]

## Shared philosophy

- [Core belief 1 — specific to this school]
- [Core belief 2]
- [Core belief 3]
- [...]

## What they push on

- [Characteristic question, quoted as they would ask it]
- [Specific challenge they raise]
- [Specific concern]
- [...]

## Blind spots

- [What this school systematically misses]
- [What it underweights]
- [...]

## Not to be confused with

- [Adjacent archetype name] — [one specific difference]
- [...]
```

## Before committing

- [ ] Coherence test: exemplars agree on ~80% of first principles
- [ ] No duplicate: grep `display_name` and exemplars across `personas/` to check
- [ ] "Not to be confused with" names at least one nearby archetype
- [ ] Voice lines in "What they push on" are specific enough to differ from other archetypes
