---
name: frontend-design
description: 'Define the visual identity and design direction for a frontend page, view, or component. Produces a design spec (not code) covering aesthetic direction, color system, typography scale, motion principles, and layout philosophy. Use when starting a new page or component, making aesthetic decisions, or establishing visual identity. Triggered when the user says "design the UI", "improve the design", "redesign the app", "overall design", "make it look good", "layout design", or similar. For trivial mechanical changes where no design decision is needed, skip to shadcn directly.'
---

## What I Do

Produce a **design spec** — not code — covering aesthetic direction, color system, typography scale, motion principles, and layout philosophy. The spec feeds into the `shadcn` skill for implementation.

## Boundaries

- **Mode:** Plan — read-only. No files modified. Output is a design spec document only.
- **Ordering:** Always invoke before shadcn. Never use both simultaneously.
- **Design spec only** — no code, no HTML/CSS/JS output
- **No component decisions** — component selection and composition are owned by `shadcn`
- **No implementation** — stop at the spec; never write component code

## When to Use

Invoke this skill first when:
- Starting a new page, view, or component from scratch
- Making aesthetic decisions (colors, typography, spacing, motion, layout)
- Establishing or extending the visual identity of the project

**Trivial-change carveout:** For purely mechanical changes (e.g. moving an element a few pixels, changing a single text label) where no aesthetic decision is needed, the agent may skip this skill and go directly to `shadcn`.

## Design Thinking

Before writing the spec, commit to a bold aesthetic direction:

- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme — brutally minimal, maximalist, retro-futuristic, organic, luxury, playful, editorial, brutalist, etc.
- **Constraints**: Technical requirements (framework, performance, accessibility).
- **Differentiation**: What makes this unforgettable? The one thing someone will remember.

## Aesthetics Guidelines

### What to Avoid (Anti-Patterns)

These generic AI-aesthetic choices signal low-effort design. Actively avoid them:

- **Fonts:** Inter, Roboto, Arial, system-ui, Space Grotesk, Poppins — overused and characterless
- **Color schemes:** Purple gradients on white backgrounds, overly muted gray-on-gray, high-contrast blue links
- **Layouts:** Symmetrical card grids with no hierarchy, centered everything, predictable 12-column symmetry
- **Effects:** Generic fade-in, same easing for everything, overused blur backdrops without purpose

### What to Pursue

**Typography**
- Choose distinctive, characterful fonts. Pair a bold display font with a refined body font.
- Size/weight scale should feel intentional — not the same as every other site.

**Color & Theme**
- Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- Commit to a cohesive palette where every color has a semantic role.

**Motion**
- Focus on high-impact moments: one well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions.
- Use scroll-triggering and hover states that surprise.
- CSS-first; use Motion library for React when available.

**Spatial Composition**
- Consider asymmetry, overlap, diagonal flow, grid-breaking elements.
- Generous negative space OR controlled density — commit to one, never sit in between.

**Backgrounds & Visual Details**
- Create atmosphere beyond solid colors: gradient meshes, noise textures, geometric patterns, layered transparencies, grain overlays, dramatic shadows.
- Match texture to the tone — brutalist gets sharp geometric noise, organic gets soft gradients.

**Key principle:** Bold maximalism and refined minimalism both work — the key is intentionality, not intensity. Match the spec's complexity to the aesthetic vision.

## Design Spec Output

The spec must define:

### Aesthetic Direction
- One-sentence description of the visual direction
- Why this direction fits the purpose and tone

### Color System
- Dominant color(s), accent color, neutral palette
- Semantic role of each color (bg, text, border, interactive)
- Light vs dark mode if applicable

### Typography Scale
- Display font + body font choices (avoid generic fonts like Inter, Arial, Roboto)
- Size/weight scale: headings, body, small, caption
- Rationale for font pairings

### Motion Principles
- Key interaction moments (load, hover, transition, scroll)
- Timing, easing, and stagger patterns
- CSS vs library approach (CSS-first; use Motion library for React when available)

### Layout Philosophy
- Grid system, spacing scale, density preference
- Asymmetry, overlap, or grid-breaking elements
- Whitespace strategy (generous negative space vs controlled density)

## Design Token Mapping

Each spec element maps to a concrete implementation target. Include this mapping in the spec so the `shadcn` skill can directly read it without reinterpretation.

| Spec Element | Implementation Target | Example |
|-------------|----------------------|---------|
| Color palette | `tailwind.config.js` `theme.extend.colors` + CSS variables in `global.css` | `background: '#FDFBF7'` → `--background: #FDFBF7` |
| Font family | `tailwind.config.js` `theme.extend.fontFamily` | `'sora': ['Sora', 'sans-serif']` |
| Border radius | `tailwind.config.js` `theme.extend.borderRadius` | `'card': '16px'`, `'input': '12px'` |
| Spacing scale | `tailwind.config.js` `theme.extend.spacing` | `'card': '2rem'`, `'section': '2.5rem'` |
| Shadows | `tailwind.config.js` `theme.extend.boxShadow` | `'soft': '0 4px 20px rgba(0,0,0,0.06)'` |
| Container max-width | `tailwind.config.js` `theme.extend.maxWidth` or per-component | `'content': '660px'` |
| Motion timing | CSS variables in `global.css` | `--transition-duration: 0.4s` |
| Semantic token aliases | CSS variables in `global.css` referencing Tailwind colors | `--primary: theme('colors.sage');` |

**Rule:** Every color, font, radius, and shadow in the spec must appear in this table with its exact hex/value. The `shadcn` skill reads this table directly — no ambiguity about which value goes where.

## Conflict Resolution

When both `frontend-design` and `shadcn` are active:

| Owned by frontend-design | Owned by shadcn |
|---------------------------|-----------------|
| Color, typography, spacing, motion, aesthetics | Component selection, imports, composition, accessibility |
| Visual hierarchy and layout philosophy | API patterns, responsive breakpoints |
| Design tokens (CSS variable values) | Component structure and variant usage |

**Rule:** Never let shadcn's default variants/colors override an intentional design decision. The design spec wins for visual style; shadcn wins for API/composition patterns.

## Hand-off

- Design spec produced with all sections populated
- No code written
- Spec ready for `shadcn` implementation phase

---

## Outputs & Triggers

### Output
Design spec document with all sections populated (aesthetic direction, color system, typography scale, motion principles, layout philosophy, design token mapping).

### Exit Declaration
State clearly: "**Design spec ready. Say 'design' to trigger shadcn implementation, or re-run to revise the spec.**"

### Next Step
User invokes `shadcn`.
