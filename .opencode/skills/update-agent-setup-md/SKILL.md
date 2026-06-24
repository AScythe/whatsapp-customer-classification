---
name: update-agent-setup-md
description: Analyze the current agent development environment (global + project state) and update `refs/AGENT_SETUP.md` to be accurate, complete, and within its defined scope. Trigger when the user says "update agent setup", "sync agent setup", "agent setup is outdated", or similar.
---

## Purpose

Agent development environment setup guide. Answers "How do I reproduce this project's AI coding assistant environment on any machine?"

Mine the global system state and the project codebase, then update or create `refs/AGENT_SETUP.md` so any developer can clone the repo and have the same OpenCode + MCP + skills experience on any device.

---

## Audience

- Developers setting up a new machine for this project
- AI agents needing tooling context to operate correctly
- Teams wanting consistent, reproducible development environments

---

## Invocation Modes

This skill supports two invocation modes. **Explicit** (default, standalone): follows the full Investigation Protocol below. **Implicit** (invoked by `update-docs` Phase 3): investigation is scoped to diff files from the caller. In implicit mode the full Investigation Protocol below is replaced by a delta scan — only analyze changed files against the current document. Graphify context is provided by `update-docs`; skip the Phase 0 graphify query.

---

## Content Rules

### Quality Gates

- **"Would a developer setting up a new machine miss this?" litmus test**
- **Verifiable against actual system state:** Every tool version, config path, and command must be verified
- **Cross-platform awareness:** Document platform-specific paths and commands
- **No secrets:** Never capture API keys, tokens, or credentials

### What to Include

**Universal (always present):**
- **Prerequisites** — foundational tools (language runtimes, package managers, AI assistant CLI) with install commands
- **Global tool installations** — MCP servers, AI assistant plugins, their install commands
- **PATH configuration** — where tool executables live, how to add to PATH per platform
- **Global config files** — AI assistant global permissions, tool-level global settings, any global custom commands or skills
- **Project config files** — AI assistant root config (`opencode.json`), plugin dependency manifests, skill directories
- **One-time global setup steps** — what must happen once per machine (install AI assistant, install MCP servers, configure global settings, register system-level configs)
- **Per-clone project setup steps** — dependency install, index/build initialization, MCP/server registration
- **First-time flow** — complete end-to-end sequence from blank machine to working setup
- **Verification steps** — commands to confirm each component works after setup (version checks, status commands, connectivity tests)
- **Troubleshooting** — common failures (tool not found, path issues, MCP errors, stale indexes) with actionable fixes
- **Replicating to Another Project** — copy instructions + post-copy setup steps for migrating tooling to a new repo

**Configuration reference (core — always present):**
- **Configuration files** — tables of global and project config files with purpose and check-in status
- **Gitignore configuration** — what's ignored and why per tool, tracked vs ignored files with rationale, nested gitignore files
- **Custom commands** — project-specific or global CLI commands with usage syntax and examples
- **Skill/workflow inventory** — list of all agent skills with phase mapping and descriptions, placed as a subsection within Configuration Reference

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
- Setup covers only the agent toolchain (opencode, AI assistant CLI, MCP servers, semantic search, knowledge graph, skills, /commands) — application dependencies (Python deps, env vars, run commands) belong in README.md

---

## Universal Template

The skeleton below is used for every project's `AGENT_SETUP.md`. Markers like `<!-- FILL: name -->` indicate where project-specific content is injected. Sections without markers are included verbatim.

```markdown
# [Project Name] Agent Setup

> **Last verified:** [date]

## What This Covers
| Layer | Tools |

## Prerequisites
| Tool | Version | Install |

## Global Setup (One-Time Per Machine)
[Steps that run once per machine — AI assistant CLI, MCP servers, config files, PATH]

## Project Setup (Per Repository Clone)
[Steps per clone — dependency install, index initialization, MCP registration]

## Configuration Reference
[Tables of global config files, global tool installations, and project config files with purpose and check-in status]

### Gitignore Configuration
[What's tracked vs ignored per tool with rationale, root + nested .gitignore files]

### Custom Commands
[Project-specific CLI commands (/scaffold) with usage syntax and examples]

## First-Time Flow From Scratch
[Complete end-to-end sequence from blank machine to working setup]

## Verification
[Commands to confirm each component works — version checks, index status, MCP connectivity]

## Troubleshooting
[Common failures — tool not found, path issues, MCP errors — with actionable fixes]

## Replicating to Another Project
[Copy instructions + post-copy setup steps for migrating tooling to a new repo]

<!-- FILL: optional-sections -->
```

> **Note:** Configuration Reference, Gitignore Configuration, and Custom Commands are CORE sections (not optional) — they appear between Project Setup and First-Time Flow. Skill/workflow inventory is a subsection within Configuration Reference.

Optional sections (include only if applicable): (none — all applicable sections are in the core template above)

---

## Phase 0: Prerequisites

- [ ] Run `graphify query_graph "agent setup / tooling"` — understand relationship context with skills, configs, and MCP servers
- [ ] Verify agent environment is accessible (global config, project config)
- [ ] Read existing AGENT_SETUP.md — understand current documented state
- [ ] Check for new tools/dependencies added since last sync
- [ ] Determine invocation mode — if implicit, skip full codebase walk and accept scope from caller (diff context)

## Workflow

> **Explicit mode only.** For implicit mode see Invocation Modes.
>
> **Investigation Protocol:** Investigation scans the current system and project state, then compares against the current document — not against previous session changes. Pre-existing discrepancies (stale tool versions, wrong PATH config, missing setup steps) are gaps to flag regardless of when they were introduced.

### Phase 1: Investigate

#### Scan Global State
Collect from the developer's system:
- OpenCode global config
- Global commands and skills
- cocoindex global settings
- Tool installations
- PATH check
- graphify platform install

#### Scan Project State
Read the project's committed files:
- `opencode.json`
- `.opencode/package.json`
- `.opencode/skills/`
- `.gitignore`
- `.cocoindex_code/settings.yml` (if present)
- `graphify-out/` (if present)

### Phase 2: Read the Current Document
- Check if `refs/AGENT_SETUP.md` exists
- Flag outdated content

### Phase 3: Identify Gaps and Issues
For each **What to Include** item: does it exist? Is it accurate?

### Gate: User Confirmation

Present proposed oldString→newString diffs to the user for approval before applying any edits. Use the `question` tool with clickable options.

### Phase 4: Assemble or Update the Document

**If AGENT_SETUP.md doesn't exist (create from scratch):**
1. Start with the **Universal Template** from this skill
2. Replace `<!-- FILL: optional-sections -->` with any applicable optional sections
3. Fill each universal section with discovered tool-specific content
4. Verify no `<!-- FILL:` markers remain
5. Update the `> **Last verified:**` line to today's date (YYYY-MM-DD format)
6. Write the result to `refs/AGENT_SETUP.md`

**If AGENT_SETUP.md already exists (surgical update):**
- For each universal section: compare against discovered system state and update only what changed (tool versions, commands, config paths, setup steps)
- For each optional section: add if applicable and missing, remove if no longer applicable, update if stale
- Never rewrite the whole file — use targeted edits on changed sections only
- Update the `> **Last verified:**` line to today's date (YYYY-MM-DD format) — always update, even if no other changes were needed

### Phase 5: Verify

**Integrity & Scope:**
- [ ] Every piece of content belongs in this document per the What NOT to Include table — redirect if it belongs elsewhere
- [ ] No content duplicated from another document — use `See <DOC>.md` cross-references instead
- [ ] All tool versions and commands verified against actual system state (global scan) or committed files (project scan)
- [ ] Every line passes the litmus test defined in Quality Gates
- [ ] Document omits everything a developer setting up doesn't need — no speculation, no aspirational content

**Document-Specific Checks:**
- [ ] Prerequisites section covers all foundational tools with install commands
- [ ] Global setup steps are clearly separated from project setup steps
- [ ] PATH configuration documented per platform with exact commands
- [ ] MCP server config shows both the config entry and the verification command
- [ ] Skill inventory is complete and matches `.opencode/skills/` directory
- [ ] Custom commands documented with usage syntax and examples
- [ ] Replicating to Another Project lists file-by-file copy instructions and post-copy setup steps
- [ ] First-time flow is a complete end-to-end sequence from blank machine
- [ ] Verification section has runnable commands for each component
- [ ] All configuration file paths are correct (global paths use `\~`, project paths are repo-relative)
- [ ] No secrets, API keys, or credentials captured anywhere
- [ ] Cross-references to README.md and other docs are accurate
- [ ] Gitignore rules are documented per tool — tracked vs ignored files explained with rationale
- [ ] `.opencode/.gitignore` nested config is documented — only `node_modules` and `bun.lock` ignored; `package.json` and `package-lock.json` tracked
- [ ] `> **Last verified:**` date is current — updated to today (YYYY-MM-DD)

## Hand-off
- Phase 1: Investigation complete — global system state and project state scanned
- Phase 2: Current document read and compared
- Phase 3: Gaps and issues identified
- Gate: User confirmed proposed diffs
- Phase 4: Document assembled or updated
- Phase 5: Verification complete — all checks pass

## Outputs & Triggers

### Output
Updated `refs/AGENT_SETUP.md` at `refs/AGENT_SETUP.md`.

### Exit Declaration
State clearly: "**AGENT_SETUP.md updated. All checks pass.**"

### Next Step
Return to `update-docs` orchestrator for cross-reference audit.