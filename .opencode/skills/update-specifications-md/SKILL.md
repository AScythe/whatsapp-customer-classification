---
name: update-specifications-md
description: Analyze the current product state and update `docs/SPECIFICATIONS.md` to be accurate, complete, and within its defined scope. Trigger when the user says "update specs", "update specifications", "specs are outdated", or similar.
---

## Purpose
Product specification and vision document. Answers "Why does this exist?", "What problem does it solve?", "How does the pipeline work?".

Mine the codebase and session history, then update or create `docs/SPECIFICATIONS.md` so product owners, developers, and stakeholders share a clear understanding of the product vision.

---

## Audience
- Product owners and managers
- Developers and AI agents needing product context
- Evaluators and stakeholders

---

## Invocation Modes

This skill supports two invocation modes. **Explicit** (default, standalone): follows the full Investigation Protocol below. **Implicit** (invoked by `update-docs` Phase 3): investigation is scoped to diff files from the caller. In implicit mode the full Investigation Protocol below is replaced by a delta scan — only analyze changed files against the current document. Graphify context is provided by `update-docs`; skip the Phase 0 graphify query.

---

## Content Rules

### Quality Gates
- **"Would a product owner, developer, or evaluator miss this?" litmus test**
- **Product-focused language:** Describe purpose, vision, and user experience — not implementation details
- **Actionable for development:** Feature descriptions must include purpose and rationale

### What to Include

**Universal sections** (present in every project's SPECIFICATIONS.md):
- **Problem statement and context** — what pain point exists, who experiences it, why it matters
- **Solution description and pitch** — what the product does at a high level, why it solves the problem
- **User journey / core logic flow** — numbered product-focused steps in plain language, each describing a distinct user-facing action, readable by a non-technical evaluator
- **Feature descriptions** — with purpose and rationale: what each feature does and **why** it exists
- **Privacy First** — user-facing table (identity, location, data, control) plus a "Hard Constraints" sub-section
- **Product constraints / Out of Scope** — standalone section listing what the product explicitly does NOT do and why
- **Tech stack with rationale** — Architecture Overview (2-6 lines describing frontend/backend/data model for stakeholders) plus a "Why?" column table for each technology, plus a Product Decisions table (decision + rationale)
- **Product decisions and rationale** — why certain approaches were chosen (vision rationale, not technical trade-offs)

**Optional sections** (include only if the project has them):
- **Target user personas** — who the product serves and why they benefit
- **Feature priority and status** — what's implemented vs. planned, to guide what to build next
- **Future enhancements / bonus features** — clearly marked as not yet implemented
- **Sample user flow** — narrative walkthrough showing the product in action
- **Value proposition / why users will love it** — problem-solution table (❌ problem → ✅ how it's solved) or benefit bullets
- **Final Pitch Line** — one-sentence user-facing summary of what the product is, placed as closing callout
- **Demo setup instructions** — runnable steps for judges or evaluators to demo the product

### What NOT to Include

| Document | Scope | Audience | Content Type | Canonical Source Of |
|----------|-------|----------|--------------|-------------------|
| **README.md** | User-facing setup, usage, features, installation | End users, new developers | User-facing | Install/run commands, user-facing features, quick-start |
| **ARCHITECTURE.md** | Technical structure, modules, file tree, implementation, data flow | Developers, AI agents | Technical | Module descriptions, import graph, design decisions (technical) |
| **SPECIFICATIONS.md** | Product vision, user journey, problem statement, Out of Scope | Product owners, devs, AI agents | Product / Vision | Product vision, user journey, feature rationale, Out of Scope |
| **DESIGN_SPEC.md** | Visual design spec, color system, typography, motion | Developers, designers, AI agents | Visual / Aesthetic | Design system, color tokens, typography scale, motion principles |
| **AGENTS.md** | Agent behavioral rules, file ownership, operational constraints | AI agents | Operational | Agent behavioral rules, file ownership table, commands, failure triage, test suite conventions |
| **AGENT_SETUP.md** | Agent development environment setup and configuration | Developers, AI agents | Setup / Operational | Tool dependencies, MCP config, skill files, PATH, global and project config |
| **PROJECT_BEST_PRACTICES.md** | Universal coding patterns, best practices, lessons learned | All developers, AI agents | Educational | Universal coding practices, skill methodologies |
| **DOCUMENT_GUIDELINES.md** | Doc scope, content boundaries, governance | Developers, AI agents | Governance | Document metadata, content boundaries |

**Boundary rules** (additional document-specific guardrails):
- Architecture Overview = 2-6 line high-level summary describing frontend/backend/data model — no implementation detail, no internal module names
- Tech stack Technology Table uses 3 columns (Layer, Technology, Why?) — rationale for each choice. The README has the simpler "what is used" table. Do not duplicate README content here
- Product Decisions table uses 2 columns (Decision, Why?) — vision rationale, not technical trade-offs

**Anti-duplication:**
- One purpose per document — if content fits two documents, choose the PRIMARY purpose
- Cross-reference, don't copy — use `See <DOC>.md` links instead of duplicating
- If content belongs elsewhere, note it with `→ Redirect to <filename>` — do not include it in this document

---

## Universal Template

The skeleton below is used for every project's `SPECIFICATIONS.md`. Markers like `<!-- FILL: name -->` indicate where project-specific content is injected. Sections without markers are included verbatim.

```markdown
# Specifications — [Project Name]

> **Last verified:** [date]

> **Emoji heads-up:** Section headings in this template use emoji prefixes as a visual convention (e.g., `## 💡 Problem`). These are entirely optional — replace or remove them for other projects.

## 💡 Problem
[What pain point exists, who experiences it, why it matters]

## 🎯 Solution
[What the product does at a high level, why it solves the problem]

## ✅ How It Works
[Numbered steps in plain language — each step describes a distinct user-facing action, readable by a non-technical evaluator]

## Core Features
[Feature descriptions with purpose and rationale]

## 🔒 Privacy First
[User-facing table: identity, location, data, control — plus Hard Constraints sub-section]

## 🚫 Out of Scope
[What the product explicitly does NOT do and why]

## 🎯 Why Users Love It
[Problem-solution table: pain point → how the product solves it]

## 🛠️ Tech Stack
### Architecture Overview
[Brief description of frontend/backend/data model structure — 2-6 lines, no implementation detail]

### Technology Table
[Layer, Technology, Why? — rationale column for each technology choice]

### Product Decisions
[Decision + rationale — vision rationale, not technical trade-offs]

<!-- FILL: optional-section-sample-user-flow -->

<!-- FILL: optional-section-why-users-will-love-it -->

<!-- FILL: optional-section-bonus-features -->

## 📣 Final Pitch Line
[One-sentence closing callout]

<!-- FILL: optional-section-demo-setup -->
```

Optional sections (include only if applicable): Target user personas, Feature priority and status, Future enhancements / bonus features, Sample user flow (`<!-- FILL: optional-section-sample-user-flow -->`), Why users will love it (benefit bullets — `<!-- FILL: optional-section-why-users-will-love-it -->`), Bonus features (`<!-- FILL: optional-section-bonus-features -->`), Demo setup instructions (`<!-- FILL: optional-section-demo-setup -->`).

---

## Phase 0: Prerequisites

- [ ] Run `graphify query_graph "specifications/project scope"` — understand relationship context with other docs, skills, and code
- [ ] Verify source code and product state are current
- [ ] Read existing SPECIFICATIONS.md — understand current scope boundaries
- [ ] Consult docs/ARCHITECTURE.md and AGENTS.md for cross-reference integrity
- [ ] Determine invocation mode — if implicit, skip full codebase walk and accept scope from caller (diff context)

## Workflow

> **Explicit mode only.** For implicit mode see Invocation Modes.
>
> **Investigation Protocol:** Investigation compares the current document against the current codebase — not against previous session changes. Pre-existing discrepancies (stale descriptions, missing features, incorrect scope boundaries) are gaps to flag regardless of when they were introduced.

### Phase 1: Investigate the Codebase
Read highest-value sources first:

1. Existing product spec document
2. Source code entry points — extract high-level features and user-facing behavior
3. `README*` for feature descriptions
4. Architecture document — to know what NOT to duplicate

**Review session history** as supplementary context — capture any feature decisions, rationale, or scope discussions that occurred during conversation. Do not limit investigation to session changes.

### Phase 2: Read the Current Document
- Check if `docs/SPECIFICATIONS.md` exists — create it if not
- Flag outdated content
- Flag content that violates the boundary rules above

### Phase 3: Identify Gaps and Issues
For each **What to Include** item: does it exist? Is it accurate?
For each existing section: does it belong here per **What NOT to Include**? If not → redirect.

**Cross-reference checks:**
- Map every step in "How It Works" to an actual code flow path — each step must correspond to real pages/routes/user-facing behavior
- For the sample user flow narrative (if present), verify each scene corresponds to an actual page/route/state in the app — no fictional or deprecated scenes

### Gate: User Confirmation

Present proposed oldString→newString diffs to the user for approval before applying any edits. Use the `question` tool with clickable options.

### Phase 4: Assemble or Update the Document

**If SPECIFICATIONS.md doesn't exist (create from scratch):**
1. Start with the **Universal Template** from this skill
2. Replace `<!-- FILL: optional-sections -->` with any applicable optional sections
3. Fill in each section with discovered project-specific content
4. Update the `> **Last verified:**` line to today's date (YYYY-MM-DD HH:MM TZ format)

**If SPECIFICATIONS.md already exists (surgical update):**
- For each universal section: compare against discovered data and update only what changed (problem, solution, flow, features, privacy, scope, tech stack, decisions)
- For each optional section: add if applicable and missing, remove if no longer applicable, update if stale
- Never rewrite the whole file — use targeted edits on changed sections only
- Keep language product-focused — benefits and outcomes, not implementation
- Feature descriptions must state purpose and benefit
- Architecture Overview must be 2-6 lines — high-level, no implementation detail or internal module names
- Update the `> **Last verified:**` line to today's date (YYYY-MM-DD HH:MM TZ format) — always update, even if no other changes were needed

### Phase 5: Verify

**Integrity & Scope:**
- [ ] Every piece of content belongs in this document per the What NOT to Include table — redirect if it belongs elsewhere
- [ ] No content duplicated from another document — use `See <DOC>.md` cross-references instead
- [ ] All claims verified against the current product state and codebase
- [ ] Every line passes the litmus test defined in Quality Gates
- [ ] Document omits everything a product owner or evaluator doesn't need — no speculative, aspirational, or unverifiable content

**Document-Specific Checks:**
- [ ] Problem statement is clear and compelling
- [ ] User journey described in plain language — no endpoint names
- [ ] Every step in "How It Works" maps to an actual user-facing page or route — no fictional or merged steps
- [ ] Sample user flow narrative (if present) matches actual app page flow — each scene verified against real pages/states
- [ ] Feature descriptions include purpose/rationale suitable for guiding development decisions
- [ ] Product decisions capture vision rationale (not technical trade-offs)
- [ ] Privacy section includes both user-facing table and Hard Constraints sub-section
- [ ] Tech Stack has Architecture Overview (2-6 lines), Technology Table with "Why?" column, and Product Decisions table
- [ ] Demo setup instructions (if present) list runnable steps, not architecture detail
- [ ] Final Pitch Line (if present) is a one-sentence user-facing closing callout
- [ ] Out of Scope lists hard boundaries only — no aspirational items
- [ ] No endpoint names, route definitions, or implementation-level detail anywhere
- [ ] If features were added/removed/renamed, verify SPECS (rationale) and README (benefits) are both synced
- [ ] Language appropriate for product owners, developers, and evaluators — not end users
- [ ] `> **Last verified:**` date is current — updated to today (YYYY-MM-DD HH:MM TZ)

## Hand-off
- Phase 1: Investigation complete — codebase scanned, product features mapped, user journey extracted
- Phase 2: Current document read and compared against codebase
- Phase 3: Gaps and issues identified
- Gate: User confirmed proposed diffs
- Phase 4: Document assembled or updated
- Phase 5: Verification complete — all checks pass

## Outputs & Triggers

### Output
Updated `docs/SPECIFICATIONS.md` at `docs/SPECIFICATIONS.md`.

### Exit Declaration
State clearly: "**SPECIFICATIONS.md updated. All checks pass.**"

### Next Step
Return to `update-docs` orchestrator for cross-reference audit.