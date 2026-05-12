# Name Candidates

The user rejected "Lifebase" from the original conversation. This doc proposes alternatives. Pick one in the next session.

The `foolswithtools` naming pattern is **short, often 4-5 letters, slightly oblique, vaguely meaningful**: `brok`, `pwk`, `crux`, `crew`, `toolshed`. Candidates here aim for that voice.

The working name throughout this folder's docs is **`atlas`**. If you pick something different, do a find-and-replace across `concept/*.md` and rename references.

---

## Top picks

### 1. `atlas`

**Meaning:** A collection of maps. The Greek titan who held up the heavens (suggests "bears the weight of everything").

**Why it fits:** The ontology *is* a map of your world. Multiple stores = multiple maps. The atlas metaphor handles personal, side-gig, work as different maps in the same book. It is also short, evocative, and not domain-specific in a way that boxes you in.

**Why not:** Common name; Atlas is also an Anthropic product (Sky), a CSS framework, etc. Less unique than the foolswithtools house style.

**Working assumption: this is the default if the user doesn't pick something else.**

---

### 2. `cairn`

**Meaning:** A pile of stones marking a path. Built up over time. Each stone is small, the cumulative structure is meaningful.

**Why it fits:** Captures the *accumulative* nature of the system. Each captured signal, decision, person, event is a stone; the cairn is what you've built. Also nods to "wayfinding" — the system helps you orient.

**Why not:** Slightly archaic; not everyone knows the word; the metaphor might be too poetic for a working tool.

---

### 3. `kern`

**Meaning:** The central, essential part (cf. *kernel*). Also a printer's term for adjusting spacing between letters — the precise alignment of related things.

**Why it fits:** Short. Matches `foolswithtools` voice. Both meanings work: the *core* of your context, and the *precise alignment* of related entities.

**Why not:** Easily confused with "kernel" or "kern" in typography contexts; less self-explanatory than `atlas`.

---

### 4. `codex`

**Meaning:** A bound collection of pages. A systematic body of knowledge. Historically what a book *was* before printed books.

**Why it fits:** Speaks to "structured knowledge". Codex is also a common term in tabletop gaming and historical scholarship (lawcodes), suggesting governance and order. Plays well with the ontology framing.

**Why not:** GitHub's competing AI codename ("Codex" / "OpenAI Codex"); could be confusing. Longer than the rest.

---

### 5. `nave`

**Meaning:** The central body of a church; the main interior space. Also the hub of a wheel (Old English).

**Why it fits:** "Central space where everything converges" maps cleanly to the system. Short, slightly mysterious, hits the `foolswithtools` voice. The hub-of-a-wheel meaning is genuinely apt: many spokes (data sources, agents, surfaces) meet at the nave.

**Why not:** Less commonly known meaning; church association might feel weird.

---

## Other candidates worth considering

| Name | Meaning | Why it might work | Why probably not |
|---|---|---|---|
| `lodestone` | Magnetic stone that points north | The core that aligns everything | Two syllables, slightly long |
| `tessera` | A single tile in a mosaic | Each entity is a tessera, the system is the mosaic | Probably better as a name for an individual entity type |
| `gist` | The essential point | Short; captures "what matters" | Too informal; sounds like GitHub Gist |
| `stash` | Personal hidden cache | Captures personal use | Has criminal/illicit overtones |
| `loom` | Weaves threads | Captures the integration of disparate sources | Already used by Loom video software |
| `mesh` | A network of connections | Apt for the graph nature | Too generic; means many things in tech |
| `nub` | Small but central | Plays well with `foolswithtools` | Too informal/diminutive |
| `axis` | The line everything rotates around | Captures the centrality | Common word; less distinctive |
| `vault` | Secure personal storage | Apt; `brok` already uses internally | Bank metaphor feels off; conflict with `brok` |
| `kiln` | Where raw material is transformed | Matches the "structure raw data" idea | `brok` already uses forge metaphor |
| `reckoner` | One who counts/orders | Old word for someone who keeps accounts | Two syllables; archaic |

---

## Names probably to avoid

- **`brain`** — too generic, used by everyone
- **`mind`** — same
- **`memex`** — Bush's original term; carries baggage and is a museum piece
- **`forge`** — `brok` already uses
- **`hub`** — too generic
- **`fabric`** — descriptive but trendy buzzword
- **`spine`** — body metaphor is overdone in tech
- **`compass`** — overused

---

## How to pick

The five top picks each emphasize a different aspect:

- **`atlas`** — emphasizes the *map / multi-store* shape
- **`cairn`** — emphasizes *accumulation over time*
- **`kern`** — emphasizes *centrality and precision*
- **`codex`** — emphasizes *structured knowledge*
- **`nave`** — emphasizes *central convergence*

Pick the one that best matches what you want to *feel* when you use the tool. If you want the tool to feel like consulting a reference, `atlas` or `codex`. If you want it to feel like tending a personal practice, `cairn`. If you want it to feel like core machinery, `kern`. If you want it to feel like a place you go, `nave`.

If no clear winner: keep `atlas` as the default and move on. Names are easy to change in a 50-file codebase; hard to change in a million-file one. `atlas` is plausible everywhere.

---

## After picking

1. Update the folder name if you want (e.g., rename `concept/` → `atlas/` or `cairn/`)
2. Find-and-replace `atlas` in `concept/*.md` to your chosen name
3. Update `crew/README.md` to mention the new sibling package
4. Decide whether the package lives at `crew/<name>/` or `crew/src/<name>/`
