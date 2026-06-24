---
name: update-agents-md
description: 'Analyze the current codebase and update `AGENTS.md` to be accurate, complete, and within its defined scope. Trigger when the user says "update agents", "sync agents doc", "agents.md is outdated", or similar.'
---

## Purpose

Guide for updating `AGENTS.md` — the authoritative reference for agent behavioral rules, file ownership, commands, and operational constraints. This skill combines a **universal template** (sections identical across all projects) with **project-specific discovery** (extracted by analyzing the current project).

The result is a project-specific `AGENTS.md` that accurately reflects that project's file ownership, commands, test suite, and operational constraints — while sharing the common agentic workflow and cross-phase rules with all other projects.

---

## Audience

- AI agents (e.g., opencode)
- Developers setting up agent permissions

---

## Invocation Modes

This skill supports two invocation modes. **Explicit** (default, standalone): follows the full Investigation Protocol below. **Implicit** (invoked by `update-docs` Phase 3): investigation is scoped to diff files from the caller. In implicit mode the full Investigation Protocol below is replaced by a delta scan — only analyze changed files against the current document. Graphify context is provided by `update-docs`; skip the Phase 0 graphify query.

---

## Content Rules

### Quality Gates
- **"Would an agent or developer miss this?" litmus test:** Every line must answer "Would an agent or developer likely miss this without help?" If not, leave it out.
- **Executable sources of truth:** Prefer configs, scripts, and CI files over prose documentation. If docs conflict with executable sources, trust the executable source.
- **Conciseness:** Agents read the full file on every task — omit anything an agent could infer, redundant examples, or content that doesn't affect agent behavior.
- **Universal sections are fixed:** The universal template sections must not be modified per-project. If a rule doesn't apply to a project, omit it from the project-specific AGENTS.md rather than changing the general rule.

### What to Include
- **Scope** — brief definition of what AGENTS.md covers
- **File ownership table** — location, role, agent policy (⚠️ caution / ❌ forbidden). Include only files with non-default policies — omit ✅ safe files
- **Agentic Workflow Skills** — 9-phase table with skill name, trigger keywords (from skill frontmatter `description`), and ordering rules
- **Skill Loading Priority** — priority chain, Pre-Task gate, ambiguous/multiple/no-match resolution rules
- **Codebase Exploration** — question-type decision table + pipeline + tool discipline rules
- **Process Discipline** — Integrity (read-before-write, baseline tests), Execution (exit declarations, user approval gate, batch discipline), Hygiene (full test suite, source+tests one unit)
- **Failure Triage** — classification table with symptom, cause, action (import path, brittle test, behavioral regression, baseline failure, flaky)
- **Commands Reference** — exact CLI commands for common operations (build, run, test, lint, cleanup)
- **Test Suite Structure** — if the project has a `tests/` directory, document: naming convention, file-table with run commands, and policies
- **Utility Skills** — non-phase skills (rebuild-test-and-indexes, frontend-design+shadcn, generate-and-run-e2e-tests) as prose descriptions
- **Session Continuity Check** — trigger conditions (automatic heuristic, user "continue"), policy (header only, archived sessions, sub-agent context)
- **Documentation Structure table** — file-to-location map so agents know where each doc lives
- **Documentation Discipline** — cross-referencing, description headers, executable sources of truth
- **Tooling Rules** — behavioral rules for code index, knowledge graph, package manager
- **Agent Behavioral Rules** — ALWAYS/NEVER rules organized by category (Pipeline, Model Loading, Configuration, Server Lifecycle)

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

---

## Universal Template

The skeleton below is used for every project's `AGENTS.md`. Markers like `<!-- FILL: name -->` indicate where project-specific content is injected. Sections without markers are included verbatim.

```markdown
# AGENTS.md

> **Last updated:** [date]

## Agentic Workflow Skills
[Standard 9-phase table with Trigger column + 4 ordering rules]

## Skill Loading Priority
[Priority chain, Pre-Task gate, ambiguous/multiple/no-match rules]

## Codebase Exploration
[Question-type decision table + pipeline + tool discipline]

## Process Discipline
[Integrity | Execution | Hygiene]

### File Ownership
| Location | Role | Agent Policy |
|----------|------|--------------|
<!-- FILL: file-ownership-rows -->
<!-- BOILERPLATE: docs/PLAN_*.md, archive/, .opencode/skills/, opencode.json, .cocoindex_code/, graphify-out/ -->

## Failure Triage
[Classification table]
<!-- FILL: project-failure-triage -->

## Commands Reference
<!-- FILL: commands-section -->

## Test Suite Structure
<!-- FILL: test-suite-section -->

## Utility Skills
[Non-phase skill references — rebuild-test-and-indexes, frontend-design+shadcn, generate-and-run-e2e-tests]

## Session Continuity Check
[Trigger conditions: automatic heuristic (session files exist + <3 user messages), user "continue" after compaction. Policy: header only (~200 tokens), archived sessions never auto-read, sub-agent extracts 1-3 relevant lines]

## Documentation Structure
<!-- FILL: documentation-structure-section -->

## Documentation Discipline
[Cross-referencing, description headers, executable truth]

## Tooling Rules
<!-- FILL: tooling-section -->

### Agent Behavioral Rules (project-specific)
<!-- FILL: project-specific-rules -->
Project-specific imperative rules (ALWAYS/NEVER) organized by category (Pipeline Modifications, Model Loading, Configuration, Server Lifecycle).
```

---

## Phase 0: Prerequisites

- [ ] Verify that `graphify-out/graph.json` exists — if so, query it for architecture overview first
- [ ] Read the current `AGENTS.md` end-to-end if it exists
- [ ] Read project config files (e.g., `pyproject.toml`, `package.json`, `Cargo.toml`, `go.mod`) for test commands and structure
- [ ] Scan `tests/` directory for test files and conventions
- [ ] Scan `.opencode/skills/*/SKILL.md` for behavioral rules that appear in multiple skills (universalization candidates)
- [ ] Determine invocation mode — if implicit, skip full codebase walk and accept scope from caller (diff context)

---

## Workflow

> **Explicit mode only.** For implicit mode see Invocation Modes.
>
> **Investigation Protocol:** Investigation compares the current document against the current codebase — not against previous session changes. Pre-existing discrepancies (outdated file ownership, missing sections, wrong commands, stale behavioral rules) are gaps to flag regardless of when they were introduced.

### Phase 1: Investigate the Codebase
Read in priority order:
1. Project entry points and their sub-modules — extract behavioral patterns, modification constraints, resource management rules
2. Configuration files — extract constants, flags, environment variable bindings
3. Core infrastructure modules — extract loading/unloading or lifecycle patterns
4. Build, test, lint, CI configs — extract exact CLI commands
5. `.opencode/skills/*/SKILL.md` — extract behavioral rules that appear in multiple skills
6. Scan `tests/` for test files — note naming convention, approach per file, test count

For each **What to Include** item, collect the data. This fills the `<!-- FILL: -->` markers in the Universal Template:
- **File ownership** — files with ⚠️/❌ policies only; omit safe defaults
- **Commands** — install, run, build, test, lint, cleanup
- **Test Suite** — naming convention, file-to-module table with approach (Pure / `sys.modules` patch / mock), run command
- **Utility Skills** — scan `.opencode/skills/` for non-phase skills with `description` frontmatter
- **Session Continuity Check** — check if `docs/sessions/` directory exists and contains SESSION_*.md files; verify session archiving policy
- **Documentation Structure** — scan `docs/`, `refs/`, root for `.md` files
- **Documentation Discipline** — scan for description headers in source files; note any stale ones
- **Tooling** — knowledge graph, search index invocation and update commands
- **Failure Triage** — project-specific symptom→cause→action rows
- **Skill Loading Priority** — verify `skill` loading rules are present and accurate

### Phase 2: Read the Current Document
- Check if `AGENTS.md` exists at the project root — create if not
- Flag outdated or missing items

### Phase 3: Identify Gaps and Issues
For each **What to Include** item and each **Universal Template** marker: does it exist? Is it accurate?

**Cross-reference checks:**
- Does the file ownership table account for all files added or removed since last sync? Cross-reference every entry against current filesystem
- Does the test suite structure match actual test files on disk? Verify every entry in the test table exists in the filesystem

### Gate: User Confirmation

Present proposed oldString→newString diffs to the user for approval before applying any edits. Use the `question` tool with clickable options.

### Phase 4: Assemble or Update the Document

**If AGENTS.md doesn't exist (create from scratch):**
1. Start with the **Universal Template** from this skill
2. Replace each `<!-- FILL: name -->` marker with discovered project-specific content
3. Omit markers for sections that don't apply (no tests → remove `<!-- FILL: test-suite-section -->`)
4. Verify no `<!-- FILL:` markers remain
5. Update the `> **Last updated:**` line to today's date (YYYY-MM-DD HH:MM TZ format)
6. Write the result to `AGENTS.md`

**If AGENTS.md already exists (surgical update):**
- For each `<!-- FILL: -->` section in the Universal Template: replace the corresponding section in AGENTS.md with freshly discovered data (e.g., replace the Commands block, update the Test Suite table, refresh File Ownership rows)
- Keep universal template sections as-is — they're identical across projects and should not drift
- Remove sections that no longer apply, add any that are missing
- Never rewrite the whole file — use targeted edits on changed sections only
- Update the `> **Last updated:**` line to today's date (YYYY-MM-DD HH:MM TZ format) — always update, even if no other changes were needed

### Phase 5: Verify

**Integrity & Scope:**
- [ ] Every piece of content belongs in this document per the What NOT to Include table — redirect if it belongs elsewhere
- [ ] No content duplicated from another document — use `See <DOC>.md` cross-references instead
- [ ] All claims verified against executable sources (code, config, workflows), not just docs
- [ ] Every line passes the litmus test — "Would an agent miss this?"
- [ ] Document omits everything an agent doesn't need — no speculative, aspirational, or unverifiable content
- [ ] No `<!-- FILL:` markers remain in the final output
- [ ] Universal template sections are unmodified from the skill's template (only project-specific sections differ)

**Section Structure:**
- [ ] Section order follows priority: Scope → Agentic Workflow Skills → Skill Loading Priority → File Ownership → Codebase Exploration → Process Discipline → Failure Triage → Commands → Test Suite → Utility Skills → Session Continuity Check → Documentation Structure → Documentation Discipline → Tooling
- [ ] Agentic Workflow Skills table has Trigger column — keywords match skill frontmatter `description` exactly
- [ ] Skill Loading Priority section exists — priority chain, Pre-Task gate, ambiguous/multiple/no-match rules
- [ ] Utility Skills section uses prose descriptions, not a table — each non-phase skill has `**Header:** description — see skill` pattern

**Document-Specific Checks:**
- [ ] File ownership table covers all files with non-default policies (⚠️ / ❌) — accurate and complete
- [ ] File ownership table cross-referenced against current filesystem — no missing entries for new files, no stale entries for removed files
- [ ] Test suite structure matches actual test files on disk — every test file entry in the table verified against filesystem
- [ ] All commands are accurate and runnable with exact syntax
- [ ] Agent behavioral rules are imperative — "always/never", not "consider" or "try to"
- [ ] Universal sections not duplicated in phase-specific skill files
- [ ] Failure Triage table reflects actual project failure patterns (use generic symptom categories, not tool names)
- [ ] Test Suite section includes: file naming convention, file-to-module table with approach per file, test conventions, and run command
- [ ] Documentation Structure table lists all project docs with correct relative paths
- [ ] Documentation Discipline rules present — cross-referencing, description headers, executable sources of truth
- [ ] Tooling conventions documented as behavioral rules, not tool names
- [ ] Cross-references between documents are accurate (use relative paths)
- [ ] `> **Last updated:**` date is current — updated to today (YYYY-MM-DD HH:MM TZ)

## Hand-off
- Phase 1: Investigation complete — codebase scanned, behavioral rules extracted, file ownership mapped
- Phase 2: Current document read and compared against codebase
- Phase 3: Gaps and issues identified
- Gate: User confirmed proposed diffs
- Phase 4: Document assembled or updated
- Phase 5: Verification complete — all checks pass

## Outputs & Triggers

### Output
Updated `AGENTS.md` at `AGENTS.md`.

### Exit Declaration
State clearly: "**AGENTS.md updated. All checks pass.**"

### Next Step
Return to `update-docs` orchestrator for cross-reference audit.
