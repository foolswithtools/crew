# The Wrecking Crew

A library of personas you can call on to review, stress-test, and refine ideas.

Named after the legendary LA session musicians of the 60s-70s — skilled craftspeople working behind the scenes who could play any genre and adapt to any situation. They weren't the face of the project, but they were the reason it hit.

## How It Works

The Wrecking Crew is two things:

1. **A roster** of pre-built personas — real people and archetypes with known expertise, thinking styles, and blind spots
2. **A persona engine** — a dimensional schema that lets you assemble the right advisor on demand when no pre-built persona fits

### Using a pre-built persona
> "Review this idea as Janette Sadik-Khan. What would she push back on? What would she greenlight?"

### Assembling a persona on the fly
> "I need someone who can advise me on persuading an elderly Jamaican man to take his medication."
>
> → Assembles: healthcare communication + cultural competency (Caribbean) + elderly patients + persuasion/coaching

## Finding the Right Persona

Personas are tagged across four dimensions (see [SCHEMA.md](SCHEMA.md) for full details):

| Dimension | What it answers | Examples |
|-----------|----------------|---------|
| **expertise** | What do they know? | `urban-design`, `enterprise-security`, `freight-logistics` |
| **context** | Who/where/what culture? | audience: `founders`, setting: `government`, cultural: `silicon-valley` |
| **function** | What do you need them to do? | `review`, `critique`, `teach`, `brainstorm`, `persuade` |
| **approach** | How do they show up? | `visionary`, `scrappy`, `empathetic`, `provocative`, `analytical` |

All personas live in [`personas/`](personas/) as flat markdown files with dimensional frontmatter.

## Persona Format

Each persona is a markdown file with structured frontmatter. See [TEMPLATE.md](TEMPLATE.md) for the format and [SCHEMA.md](SCHEMA.md) for the dimensional tagging system.

## Contributing

Add personas via PR. Use the template format. The best personas capture not just *what* someone knows, but *how they think* — their decision-making frameworks, biases, and blind spots.
