---
name: update-best-practices-md
description: Extract universal best practices from the current coding session and existing codebase, then write them into `refs/PROJECT_BEST_PRACTICES.md`. Trigger when the user says "update best practices", "document lessons learned", or similar.
---

## Purpose
Universal best practices collection for future projects. Answers "What lessons were learned?", "What patterns should I reuse?".

Mine session conversations, changed files, skills, and plan files for reusable, universal lessons, then update or create `refs/PROJECT_BEST_PRACTICES.md`.

---

## Audience
- Developers starting new projects
- AI agents learning transferable patterns

---

## Invocation Modes

This skill supports two invocation modes. **Explicit** (default, standalone): follows the full Investigation Protocol below. **Implicit** (invoked by `update-docs` Phase 3): investigation is scoped to diff files from the caller. In implicit mode the full Investigation Protocol below is replaced by a delta scan — only analyze changed files against the current document. Graphify context is provided by `update-docs`; skip the Phase 0 graphify query.

---

## Content Rules

### Quality Gates
- **"Would a developer starting a new project miss this?" litmus test**
- **Universal applicability:** Strip project-specific names and details
- **Strict format compliance:** Every entry must have Context + Principle + Example + Why it matters
- **Conciseness check:** No multi-sentence stories

### Entry Format

```markdown
### X.Y Practice Name
**Context**: When/where this applies (1 line max)
**Principle**: The universal rule (2-3 lines max)
**Example**: Short code snippet or command
**Why it matters**: Impact on future work (1 line)
```

### What to Include

**Required categories (numbered sections, always present):**
- **§1 Modularization Techniques** — Module responsibility pattern, separation of concerns, leaf vs internal modules, frontend modularization (if applicable), module communication, when to split, documentation-driven design, surgical edit pattern, one logical change per edit
- **§2 Configuration** — Centralized config, server binding for browser access, portable config paths
- **§3 Error Handling** — Defense in depth, validation, graceful degradation
- **§4 State Management** — In-memory + persistent dual layer, recovery patterns
- **§5 Testing** — Test after every change, TestClient over live server, TDD tests are permanent, test references updated in same batch, test health audit, file existence checks
- **§6 Documentation** — One purpose per document, key differentiator, quality gates, routing table, boundary tensions, comments-first, lead line + bullets, strict subsection ordering, standalone cross-cutting sections, verify presence not absence, single canonical location, file description convention, project structure tree synced from source, documentation conciseness
- **§7 Session Lessons Learned** — Cross-cutting process meta-lessons: syntax verification, import discipline, API contract first, immediate verification, investigation priority order, inline constraints, merge pre/post verification, gap grilling, docs-first analysis, interactive walkthrough, presence check over re-probe, triage routing, preserve description comments, Windows shell quoting, matchmaking queue filter direction, TypedDict for structured state, thread safety, root pattern extraction, sequential numbering, skill rename protocol, workflow handoff, WebSocket accept once, skill audit after restructure, exhaustive section mapping, stale pattern audit, surgical edits over rewrites, three-layer verification, consistency pass
- **§8 Automation & Process Design** — Permission control, executable sources of truth, filename as stable key, preserve manual/regenerate auto, diff logging, cross-language extraction pattern, description headers in source only, one verb per skill, independent re-verification, stage gate pattern, batch by logical concern, persistent decision artifacts, dead code detection, batch conflict resolution, review-implementation expanded checks, non-interactive execution, orchestrator pattern, granular edits, step 0 convention, consistent process template, cross-phase deduplication, narrow-then-search pipeline, design-spec-to-config bridge, question tool mandate
- **§9 Version Control** — Commit discipline, commit by logical group, push per commit, auto-generate commit messages, detect renames via deleted + new pairs
- **§10 Code Review Checklist** — Syntax, imports, tests, errors, hardcoded values, docs
- **§11 Debugging Process** — Identify → Isolate → Read → Plan → Apply → Verify → Document
- **§12 Documentation Sync** — Per-batch approval for documentation changes

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

The skeleton below is used for every project's `PROJECT_BEST_PRACTICES.md`. Markers like `<!-- FILL: name -->` indicate where project-specific content is injected. The Entry Format (Context + Principle + Example + Why it matters) is fixed.

```markdown
# Universal Project Best Practices

> **Last verified:** [date]

> Derived from real-world development — applies to ALL projects

## 1. Modularization Techniques

### 1.X Practice Name
**Context**: When/where this applies
**Principle**: The universal rule
**Example**: Short code snippet or command
**Why it matters**: Impact on future work

<!-- FILL: sections-2-through-12 -->
## Key Takeaways
[Numbered list of all best practices at a glance — updated when a new entry is added]
```

---

## Phase 0: Prerequisites

- [ ] Review session conversation for new lessons learned
- [ ] Review changed files for observable patterns
- [ ] Read existing PROJECT_BEST_PRACTICES.md — understand current practices
- [ ] Read skills directory for methodology patterns
- [ ] Determine invocation mode — if implicit, skip full codebase walk and accept scope from caller (diff context)

## Workflow

> **Explicit mode only.** For implicit mode see Invocation Modes.
>
> **Investigation Protocol:** Investigation compares the current document against the current codebase and session — not just against previous session changes. Pre-existing discrepancies (missing practices, stale entries, format violations) are gaps to flag regardless of when they were introduced. Session changes are one source, not the only trigger.

### Phase 1: Investigate

Read sources in this priority order:

1. Existing `PROJECT_BEST_PRACTICES.md` — compare every section against current codebase reality
2. Session conversation — extract new lessons
3. Skills directory — extract methodology patterns
4. Plan files — design rationale
5. Changed files — observable patterns

### Phase 2: Read the Current Document

Check if `refs/PROJECT_BEST_PRACTICES.md` exists — create it if not.

### Phase 3: Identify Gaps and Issues

For each **What to Include** category and each existing entry: is it still accurate? Are there missing entries? Are existing entries stale?

#### Present Candidates

Present identified gaps and proposed changes to the user.

### Gate: User Confirmation

### Phase 4: Assemble or Update the Document

**If PROJECT_BEST_PRACTICES.md doesn't exist (create from scratch):**
1. Start with the **Universal Template** from this skill
2. Replace `<!-- FILL: sections-2-through-12 -->` with applicable sections from **What to Include**
3. For each category, add entries following the **Entry Format** (Context + Principle + Example + Why it matters)
4. Verify no `<!-- FILL:` markers remain
5. Update the `> **Last verified:**` line to today's date (YYYY-MM-DD HH:MM TZ format)
6. Write the result to `refs/PROJECT_BEST_PRACTICES.md`

**If PROJECT_BEST_PRACTICES.md already exists (surgical update):**
- For each changed category: update only the entries that changed — add new, remove stale, improve existing
- For each of the 12 sections: add if missing, remove or merge if no longer accurate
- Never rewrite the whole file — use targeted edits on changed entries only
- Follow the triage: existing entries get improved (merged or tightened) over creating duplicates
- Update the `> **Last verified:**` line to today's date (YYYY-MM-DD HH:MM TZ format) — always update, even if no other changes were needed

### Phase 5: Verify

**Integrity & Scope:**
- [ ] Every piece of content belongs in this document per the What NOT to Include table — redirect if it belongs elsewhere
- [ ] No content duplicated from another document — use `See <DOC>.md` cross-references instead
- [ ] All claims traceable to session or codebase evidence — not inferred
- [ ] Every entry passes the litmus test defined in Quality Gates
- [ ] Document omits everything a developer on a new project doesn't need — no speculative, aspirational, or unverifiable content

**Document-Specific Checks:**
- [ ] All new entries follow the Entry Format (Context + Principle + Example + Why it matters)
- [ ] Conciseness applied — no multi-sentence stories, each entry is a tight rule
- [ ] **Universality check** — the principle works on any project, framed generically
- [ ] No duplication with existing entries — improve existing instead of creating new
- [ ] If content spans multiple sections, assigned to the PRIMARY section
- [ ] **§7 Session Lessons Learned** contains only genuinely cross-cutting lessons — not overflow from other sections
- [ ] `> **Last verified:**` date is current — updated to today (YYYY-MM-DD HH:MM TZ)

#### Route Skill Improvements
If this session identified improvements to `update-best-practices-md/SKILL.md` itself:

- **Minor gaps** (wording, format tweaks, missing edge cases) → fix in-place, list the changes in your output
- **Significant gaps** (structural changes, missing phases, broken workflow) → do not fix in-place. Present as candidates in the Gate summary so the user can decide.

## Hand-off
- Phase 1: Investigation complete — codebase scanned, sessions mined for lessons
- Phase 2: Current document read and compared
- Phase 3: Gaps and issues identified
- Gate: User confirmed proposed diffs
- Phase 4: Document assembled or updated
- Phase 5: Verification complete — all checks pass

## Outputs & Triggers

### Output
Updated `refs/PROJECT_BEST_PRACTICES.md` at `refs/PROJECT_BEST_PRACTICES.md`.

### Exit Declaration
State clearly: "**PROJECT_BEST_PRACTICES.md updated. All checks pass.**"

### Next Step
Return to `update-docs` orchestrator for cross-reference audit.