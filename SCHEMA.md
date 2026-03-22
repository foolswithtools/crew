# Persona Schema

The Wrecking Crew uses a dimensional tagging system that serves two purposes:
1. **Finding** the right pre-built persona for a roundtable or review
2. **Assembling** a new persona on demand when no pre-built one fits

## Dimensions

### `expertise`
What knowledge do they bring? Their domains of deep competence.

Examples: `urban-design`, `product-management`, `construction`, `enterprise-security`, `couples-therapy`, `algebra`, `freight-logistics`

### `context`
The environments, audiences, and cultural frames they understand.

- **audience**: Who they serve or deeply understand — `teenagers`, `enterprise-CTOs`, `city-governments`, `elderly-patients`, `founders`, `homeowners`
- **cultural**: Cultural or regional context — `caribbean`, `silicon-valley`, `corporate`, `blue-collar`, `academic`
- **setting**: Where they operate — `startup`, `enterprise`, `government`, `home`, `clinical`, `urban`, `rural`

### `function`
What you'd call on them to do in a roundtable.

Examples: `review`, `brainstorm`, `critique`, `coach`, `teach`, `persuade`, `build`, `troubleshoot`, `validate`, `stress-test`

### `approach`
How they show up — their style of thinking and communicating.

Examples: `visionary`, `pragmatic`, `provocative`, `empathetic`, `analytical`, `scrappy`, `methodical`, `direct`, `patient`, `culturally-sensitive`

## Frontmatter Format

```yaml
---
name: "Full Name"
slug: "lowercase-hyphenated"
type: real | archetype
expertise: ["domain1", "domain2"]
context:
  audience: ["who-they-serve"]
  cultural: ["cultural-context"]
  setting: ["where-they-operate"]
function: ["what-they-do-for-you"]
approach: ["how-they-show-up"]
---
```

## Finding a Persona

Query by any combination of dimensions:

- "I need a business idea review" → `function: review` + `expertise: startups`
- "Help my son with algebra" → `function: teach` + `context.audience: teenagers` + `approach: patient`
- "Critique my city infrastructure plan" → `function: critique` + `expertise: urban-design` + `context.setting: government`

If no pre-built persona matches, use the dimensions as a spec to assemble one.
