---
name: update-readme-md
description: Analyze the current codebase and update `README.md` (project root) to be accurate, complete, and within its defined scope. Trigger when the user says "update readme", "sync readme", "readme is outdated", or similar.
---

## Purpose
User-facing entry point for anyone discovering the project. Answers "What is it?", "How do I use it?", "How do I run it?".

Mine the codebase and session history, then update or create `README.md` (project root) so new users and developers can understand, set up, and use the project.

---

## Audience
- End users (media analysts, researchers)
- New developers joining the project
- Anyone visiting the repository for the first time

---

## Invocation Modes

This skill supports two invocation modes. **Explicit** (default, standalone): follows the full Investigation Protocol below. **Implicit** (invoked by `update-docs` Phase 3): investigation is scoped to diff files from the caller. In implicit mode the full Investigation Protocol below is replaced by a delta scan — only analyze changed files against the current document. Graphify context is provided by `update-docs`; skip the Phase 0 graphify query.

---

## Content Rules

### Quality Gates
- **"Would a first-time visitor miss this?" litmus test**
- **User-facing language:** Describe benefits and outcomes, not implementation details
- **Accuracy against current project:** Every claim must be verifiable against actual codebase
- **Minimum necessary detail:** If a first-time visitor wouldn't care about it, it doesn't belong here

### What to Include

**Universal sections** (present in every project's README.md):
- **Project description and tagline** — what it is and why it exists, in one paragraph
- **What is [Project Name]?** — one-paragraph description of what the project does and who it's for
- **Feature list** — user-facing benefits, not technical internals
- **Quick start instructions** — condensed: install dependencies, run the app, minimum steps to get going
- **How to use** — step-by-step for each user type. Show the workflow from their perspective
- **Technical Details** — high-level only: technology table (one-liner per entry, plus a simplified architecture diagram if applicable), max 2-3 paragraphs or a table
- **Testing instructions** — inline runnable commands for common test suites
- **Deployment options** — platform(s) with build and start commands
- **Privacy and security information** — user-facing summary: what data is collected, what is not, what users control
- **Troubleshooting common issues** — concrete error messages with actionable fixes
- **Why / Value proposition** — problem-solution format or benefit bullets showing what users gain
- **Success Metrics / Pitch** — user-facing outcomes and closing tagline (optional, specific to projects with a pitch angle)

**Optional sections** (include only if the project has them):
- **Table of Contents** — for longer READMEs (10+ sections), helps navigation
- **Shields/badges** — repo status badges below the title (license, Python version, framework)
- **Documentation links** — references to ARCHITECTURE.md, SPECIFICATIONS.md, etc.
- **Contributing** — fork/submit guidelines, dev setup reference
- **License** — what license the project uses
- **Requirements** — system dependencies, API keys, environment setup
- **Pipeline or stage breakdown** — table of processing steps (for pipeline-style projects)

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

**Anti-duplication:**
- One purpose per document — if content fits two documents, choose the PRIMARY purpose
- Cross-reference, don't copy — use `See <DOC>.md` links instead of duplicating
- If content belongs elsewhere, note it with `→ Redirect to <filename>` — do not include it in this document

**Boundary rules** (document-specific guardrails):
- Setup covers only the user-facing project setup (Python deps, env vars, run commands) — agent toolchain setup (opencode, AI assistant CLI, MCP servers, semantic search, knowledge graph, skills, /commands) belongs in AGENT_SETUP.md

---

## Universal Template

The skeleton below is used for every project's `README.md`. Markers like `<!-- FILL: name -->` indicate where project-specific content is injected. Sections without markers are included verbatim.

```markdown
# [Project Name]
<!-- FILL: shields-badges -->

[Project description and tagline]

<!-- FILL: table-of-contents -->

> **Last verified:** [date]

## What is [Project Name]?
[Brief one-paragraph description of what the project does and who it's for]

## Features
[User-facing benefits, not technical internals]

## Quick Start
[Prerequisites + install + run — minimum steps to get going]

## How to Use
[Step-by-step for each user type]

## Technical Details
[High-level: technology table with one-liner per entry; optionally include a simplified architecture diagram]

## Testing
[Inline runnable commands]

## Documentation
[Links to ARCHITECTURE.md, SPECIFICATIONS.md, etc.]

## Deployment
[Platform options with build + start commands]

## Privacy & Security
[User-facing summary: what's collected, what's not, user control]

## Contributing
[Fork/submit guidelines, dev setup reference → AGENT_SETUP.md]

## License
[What license the project uses]

## Troubleshooting
[Common issues with actionable fixes]

## Why / Value Proposition
[Problem-solution table or benefit bullets]

<!-- FILL: optional-section-success-metrics -->

<!-- FILL: optional-section-pitch -->

<!-- FILL: optional-sections -->
```

Optional sections (include only if applicable): Table of Contents, Shields/badges, Success Metrics (`## 📊 Success Metrics`), Pitch (`## 🎯 The Pitch`), Requirements (system dependencies, API keys), Pipeline stages.

---

## Phase 0: Prerequisites

- [ ] Run `graphify query_graph "readme / project overview"` — understand relationship context with app code, docs, and skills
- [ ] Verify source code and project state are current
- [ ] Read existing README.md — locate the canonical README file and understand current documented state
- [ ] Verify all setup instructions against actual environment
- [ ] Determine invocation mode — if implicit, skip full codebase walk and accept scope from caller (diff context)

## Workflow

> **Explicit mode only.** For implicit mode see Invocation Modes.
>
> **Investigation Protocol:** Investigation compares the current document against the current codebase — not against previous session changes. Pre-existing discrepancies (wrong setup steps, outdated feature claims, stale quick-start instructions) are gaps to flag regardless of when they were introduced.

### Phase 1: Investigate the Codebase
Read highest-value sources first:

1. `README*` (if it exists — check what needs updating)
2. Root config files
3. Source code entrypoints — what does the pipeline do end-to-end?
4. Existing `docs/ARCHITECTURE.md`

### Phase 2: Read the Current Document
- Check if `README.md` exists (project root) — create it if not
- Flag outdated content

### Phase 3: Identify Gaps and Issues
For each **What to Include** item: does it exist? Is it accurate?

**Cross-reference checks:**
- Does "How to Use" match actual app pages and navigation order? Map each step to a route/page — no skipped or merged steps
- Do all features in the feature list still exist in the app? Verify each against actual user-facing functionality
- Do auxiliary development scripts (`.bat`, `.sh`, etc.) that users might encounter have corresponding documentation in a troubleshooting or debugging section?

### Gate: User Confirmation

Present proposed oldString→newString diffs to the user for approval before applying any edits. Use the `question` tool with clickable options.

### Phase 4: Assemble or Update the Document

**If README.md doesn't exist (create from scratch):**
1. Start with the **Universal Template** from this skill
2. Replace `<!-- FILL: optional-sections -->` with any applicable optional sections
3. Fill in each section with discovered project-specific content
4. Update the `> **Last verified:**` line to today's date (YYYY-MM-DD HH:MM TZ format)

**If README.md already exists (surgical update):**
- For each universal section: compare against discovered data and update only what changed (description, features, quick start, how to use, tech stack, testing, deployment, privacy, troubleshooting, value proposition)
- For each optional section: add if applicable and missing, remove if no longer applicable, update if stale
- Never rewrite the whole file — use targeted edits on changed sections only
- Keep language user-facing
- Quick start steps must work based on actual project files
- Update the `> **Last verified:**` line to today's date (YYYY-MM-DD HH:MM TZ format) — always update, even if no other changes were needed

### Phase 5: Verify

**Integrity & Scope:**
- [ ] Every piece of content belongs in this document per the What NOT to Include table — redirect if it belongs elsewhere
- [ ] No content duplicated from another document — use `See <DOC>.md` cross-references instead
- [ ] All claims verified against the current codebase
- [ ] Every line passes the litmus test defined in Quality Gates
- [ ] Document omits everything a non-technical first-time visitor doesn't need — no speculative, aspirational, or unverifiable content

**Document-Specific Checks:**
- [ ] Features section describes user benefits, not technical internals
- [ ] Value proposition and success metrics written in user-facing language
- [ ] Pitch line is a one-sentence user-facing summary
- [ ] Technical details are high-level only (max 2-3 paragraphs or a table, one-liner per technology)
- [ ] Quick start is the canonical source for install/run commands — condensed and accurate
- [ ] Install and run steps work based on actual project files
- [ ] "How to Use" steps match actual app pages and navigation order — each step maps to a real route
- [ ] All feature list items verified against actual app — no removed or renamed features
- [ ] Deployment lists at least one platform with exact build + start commands
- [ ] Privacy & Security section is user-facing — no implementation detail
- [ ] Troubleshooting has concrete error messages with actionable fixes
- [ ] Why / Value Proposition uses problem-solution format or benefit bullets
- [ ] Documentation section lists cross-references to ARCHITECTURE.md, SPECIFICATIONS.md, etc.
- [ ] Contributing section references AGENT_SETUP.md for dev environment setup
- [ ] License section states the project's license
- [ ] Success Metrics / Pitch (if present) written in user-facing language
- [ ] If features were added/removed/renamed, verify README (benefits) and SPECS (rationale) are both synced
- [ ] Language is appropriate for a non-technical first-time visitor
- [ ] `> **Last verified:**` date is current — updated to today (YYYY-MM-DD HH:MM TZ)

## Hand-off
- Phase 1: Investigation complete — codebase scanned, feature list extracted, setup steps verified
- Phase 2: Current document read and compared against codebase
- Phase 3: Gaps and issues identified
- Gate: User confirmed proposed diffs
- Phase 4: Document assembled or updated
- Phase 5: Verification complete — all checks pass

## Outputs & Triggers

### Output
Updated `README.md` at project root.

### Exit Declaration
State clearly: "**README.md updated. All checks pass.**"

### Next Step
Return to `update-docs` orchestrator for cross-reference audit.