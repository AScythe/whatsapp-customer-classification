# Document Guidelines - IntroChat

> **Last verified:** 2026-05-31 20:15 EDT

> **Purpose:** Authoritative reference for document boundaries. Defines which content goes where, how each document is differentiated, and what to do when boundaries touch. Use this guide as the single source of truth for routing new content.

---

## Quick Reference Table

| Document | Routes content about | Audience | Update Trigger | Content Type |
|----------|---------------------|----------|----------------|--------------|
| **README.md** | User-facing setup, usage, features, benefits, installation | End users, new developers | Feature or setup change | User-facing, practical |
| **ARCHITECTURE.md** | Technical structure, modules, file tree, implementation, data flow, per-function detail | Developers, AI agents | Code structure change | Technical, implementation |
| **SPECIFICATIONS.md** | Product vision, user journey, problem statement, pitch, Out of Scope, privacy | Product owners, devs, AI agents, evaluators/stakeholders | Product scope change | Product, pitch, vision, spec, privacy |
| **DESIGN_SPEC.md** | Visual design spec, color system, typography, motion | Developers, designers, AI agents | Design or theme change | Visual, aesthetic |
| **AGENTS.md** | Agentic Workflow Rules by workflow phase, permissions, file ownership, operational constraints | AI agents (opencode) | File or command change | Operational, constraints |
| **PROJECT_BEST_PRACTICES.md** | Universal coding patterns, best practices, lessons learned | All developers, AI | After each session | Educational, guidelines |
| **AGENT_SETUP.md** | Tooling setup, env requirements, replicating to other projects | Developers, AI agents | Tooling or setup change | Operational, setup |
| **DOCUMENT_GUIDELINES.md** | Doc scope, content boundaries, governance | Developers, AI agents | New doc added | Meta, governance |

---

## 1. README.md

### Scope
User-facing entry point for anyone discovering the project. Answers "What is it?", "How do I use it?", "How do I run it?".

### Audience
- End users (event organizers, attendees)
- New developers joining the project
- Anyone visiting the repository for the first time

### Key Differentiator
**User-facing benefits over implementation.** Describe outcomes, not internals. If a non-technical first-time visitor wouldn't care about it, it doesn't belong here. This is the only document written for someone who may never write a line of code.

### What to Include
- **Project description and tagline** — what the project is and why it exists, in one paragraph
- **What is [Project Name]?** — one-paragraph description of what the project does and who it's for
- **Feature list** — user-facing benefits, not technical implementation. Describe what users can do, not how it works.
- **Quick start instructions** — install dependencies, run the app, minimum steps to get going
- **How to use** — step-by-step for each user type (organizer, attendee). Show the workflow from their perspective.
- **Technical details** — tech stack and simplified architecture. High-level only, max 2-3 paragraphs. Enough for a curious user to understand the stack, not enough to build from.
- **API endpoints** — one-line reference only ("See [ARCHITECTURE.md](../docs/ARCHITECTURE.md) for full endpoint table"). Do not duplicate the table here.
- **Testing instructions** — link to contributing guide; do not own full test documentation here
- **Deployment options** — how to deploy for production use
- **Privacy and security information** — user-facing summary only: what data is collected, what is not, and what users control. Implementation-level privacy rules go in SPECIFICATIONS.md.
- **Troubleshooting common issues** — problems users have encountered and how to resolve them
- **Contributing guidelines reference** — link to contributing guide, not the full content
- **License information** — what license the project uses

### What NOT to Include
- ❌ Detailed module descriptions or file trees — these go in ARCHITECTURE.md
- ❌ Implementation design decisions or trade-offs — these go in ARCHITECTURE.md
- ❌ Product vision, pitch, or user journey narrative — these go in SPECIFICATIONS.md
- ❌ Demo walkthrough or presentation steps — these go in DEMO_GUIDE.md
- ❌ AI agent permissions or operational rules — these go in AGENTS.md
- ❌ Best practices lessons or coding philosophy — these go in PROJECT_BEST_PRACTICES.md
- ❌ Data flow with endpoint names — this goes in ARCHITECTURE.md

### Content Boundaries
- **Features section:** Write in terms of user benefits, not technical implementation. "Users can join a room and chat anonymously" not "WebSocket connections are established on room join."
- **Technical details:** Maximum 2-3 paragraphs. Summarize the stack, don't document it.
- **API endpoints:** One-line cross-reference only. All endpoint and WebSocket event details live in ARCHITECTURE.md.
- **Privacy:** User-facing framing only ("we don't store messages"). Hard constraints and implementation-level rules go in SPECIFICATIONS.md.
- **Running the Application:** Quick-start only — minimum steps for a user to get going. Full technical startup sequence (env vars, configuration, dependencies) goes in ARCHITECTURE.md.

---

## 2. ARCHITECTURE.md

### Scope
Technical structure reference for the project. Answers "How is it built?", "What are the modules?", "How do I modify it?".

### Audience
- Developers working on the codebase
- AI agents making code changes
- Technical reviewers evaluating the implementation

### Key Differentiator
**Implementation over vision.** Describes internal structure, data flow, and design rationale. The "HOW" document — in contrast to SPECIFICATIONS.md which is the "WHY" document. If a reader needs to know how to add a route, extend a feature, or understand module boundaries, they come here.

### What to Include
- **Complete project file tree** — every directory and key file with a description of its role
- **Module descriptions** — internal logic of each module, what it owns, what it delegates. Not user benefits, not marketing language.
- **Data flow** — MUST include all API endpoints (method, path, purpose) and WebSocket events (event name, direction, payload). This is the authoritative data flow reference.
- **Key design decisions** — why certain patterns were chosen. Must include the *why*, not just the *what*.
- **Import structure and dependency graph** — how modules depend on each other, circular dependency prevention
- **Running the Application** — technical startup sequence, env vars, configuration. Full detail lives here; README gets a condensed quick-start that links here.
- **Modifying the Architecture** — how to add routes, events, extend functionality. The "if you need to add X, here's how" section.
- **Critical implementation details** — match expiry logic, cleanup thread behavior, in-memory state management, default rooms, any non-obvious runtime behavior
- **Per-function detail** — every function/class in every module with signature and one-line purpose (what it does for the system, not how it works internally). Data structure shapes with key-value descriptions; constants with values; table schemas with column types and constraints; initialization behavior (DOMContentLoaded wiring for UI state management). **This is a navigation map, not a manual** — implementation logic, parameters, return values, and edge cases belong in source docstrings/JSDoc.

### What NOT to Include
- ❌ User-facing benefits or marketing language — these go in README.md
- ❌ Product pitch, problem statement, or user journey — these go in SPECIFICATIONS.md

- ❌ AI agent file ownership tables or operational rules — these go in AGENTS.md
- ❌ Best practices philosophy or universal coding patterns — these go in PROJECT_BEST_PRACTICES.md

### Content Boundaries
- **Module descriptions:** Internal logic only. Describe what the module does in the system, not what users get from it.
- **Data flow:** Every endpoint and WebSocket event must include its actual name (e.g., `POST /api/events`, `join_room`). No placeholders.
- **Design decisions:** Always include the reasoning. "Why SQLite?" not just "Uses SQLite."
- **Language:** Technical throughout. Assume the reader knows what FastAPI, WebSocket, and SQLite are.
- **Per-function detail:** List every named function in source order. Include route context (method + path) for FastAPI handlers and event context for WebSocket handlers. For DOMContentLoaded wrappers, include a prose initialization note for non-trivial UI state wiring (button enable/disable, input validation). Keep descriptions to one line — purpose only, not implementation logic.
- **Initialization notes:** Use italic `*note*` format placed after the Functions list. Only document listeners that wire significant UI state — skip trivial wiring (console.log, focus calls).

---

## 3. SPECIFICATIONS.md

### Scope
Product specification and vision. Answers "Why does this exist?", "What problem does it solve?", "How does the user journey work?", "What features should I build that align with the vision?".

### Audience
- Product owners and managers
- Developers and AI agents needing product context to build features aligned with the vision
- Evaluators and stakeholders — hackathon judges, investors, or anyone assessing the product concept

### Key Differentiator
**Vision over implementation.** Describes purpose, user journey, and product rationale. The "WHY" document — in contrast to ARCHITECTURE.md which is the "HOW" document. No endpoint names, no module internals, no implementation details. If a decision involves trade-offs about what to build and why, it belongs here.

### What to Include
- **Problem statement and context** — what pain point exists, who experiences it, why it matters
- **Solution description and pitch** — what the product does at a high level, why it solves the problem
- **User journey / core logic flow** — product-focused steps in plain language. "User scans QR code, selects a room, gets matched." No endpoint names, no technical sequence.
- **Feature descriptions with purpose and rationale** — what each feature does and WHY it exists. Every feature needs a reason.
- **Architecture overview** — 2-4 paragraph high-level system design in product terms. Describes frontend/backend/data model for stakeholders. No implementation detail.
- **Product decisions and rationale** — why certain approaches were chosen (e.g., "Why 30 seconds?", "Why anonymous?", "Why no accounts?")
- **Target user personas** — who the product serves, why they benefit. Not user stories or acceptance criteria — archetypes.
- **Feature priority and status** — what's implemented vs. planned, to guide what to build next
- **Product constraints / Out of Scope** — what the product explicitly does NOT do and why. Honest boundaries prevent scope creep.
- **Privacy First** — user-facing framing of how privacy works, plus hard constraints (non-negotiable implementation-level rules).
- **Problem-solution pairs** — why target users benefit from each feature
- **Tech stack with rationale** — include a "Why?" column alongside each technology choice. Not detailed module descriptions.
- **Sample user flow** — narrative story of a user experiencing the product. Readable by a non-technical evaluator.
- **Value proposition for evaluators** — what judges, investors, or stakeholders should understand about the product's value *(phase-specific: remove or archive post-launch)*
- **Future enhancements / bonus features** — clearly marked as not yet implemented
- **Final pitch line** — the one-sentence summary of what this product is *(phase-specific: remove or archive post-launch)*
- **Brief demo setup** — 2-3 lines so an evaluator can run it independently.

### What NOT to Include
- ❌ Endpoint names, route definitions, or any implementation-level detail — these go in ARCHITECTURE.md
- ❌ Module descriptions, file trees, or import structure — these go in ARCHITECTURE.md
- ❌ Installation or setup instructions — these go in README.md

- ❌ AI agent rules, file permissions, or operational constraints — these go in AGENTS.md
- ❌ Best practices or universal coding patterns — these go in PROJECT_BEST_PRACTICES.md
- ❌ Data flow with endpoint names — this goes in ARCHITECTURE.md

### Content Boundaries
- **User journey / core logic flow:** Product-focused only. Describe steps in plain language. No `POST /api/events`, no `join_room` — those belong in ARCHITECTURE.md.
- **Feature descriptions:** Product purpose and user benefit. Not implementation mechanism.
- **Product decisions:** Vision rationale ("anonymous chats prevent social anxiety"), not technical trade-offs ("we chose not to store messages to save disk space").
- **Target personas:** Who the user is and why they benefit. Not user stories, not acceptance criteria.
- **Feature priority / status:** What state each feature is in. Not implementation timeline.
- **Tech stack:** Include a "Why?" rationale column. Not detailed module descriptions.
- **Brief demo setup:** Enough for a judge to run it independently.
- **Privacy:** User-facing table covering identity, location, data, and control — followed by a "Hard Constraints" sub-section with non-negotiable implementation-level rules.
- **Out of Scope:** Standalone section listing explicitly forbidden implementations. Not aspirational — each item is a hard boundary.

**Context for developers:**
- Need **product context** (what to build and why) → SPECIFICATIONS.md
- Need **implementation context** (how to build it, endpoints, modules) → ARCHITECTURE.md

**Context for agents:**
- Need **product context** (what should I build and why, what is the product vision) → SPECIFICATIONS.md
- Need **operational context** (what files can I touch, what commands can I run) → AGENTS.md

---

## 4. DEMO_GUIDE.md (Archived)

> **Archived:** Content moved to [Appendix: Archived Documents](#appendix-archived-documents) at the end of this file.

---

## 5. AGENTS.md

### Scope
Agentic Workflow Rules and operational guidelines. Answers "How should I think, plan, implement, and verify?" and "What can I touch?", "What commands do I use?".

### Audience
- AI agents (e.g., opencode)
- Developers setting up agent permissions

### Key Differentiator
**Agentic Workflow Rules + operational constraints over technical structure.** Organized by workflow phase, each phase mapping to the skill that owns it. AGENTS.md = how to behave and what to touch; ARCHITECTURE.md = implementation and data flow. If an agent needs to know "what's the right way to approach this task?" or "can I edit this file?", it's here.

### What to Include
- **Scope definition** — what this document covers and how it relates to other guidance (e.g., skill files)
- **File ownership table** — every location an agent might touch, with explicit policy: ✅ safe to edit, ⚠️ caution required, ❌ forbidden
- **Agentic Workflow Rules** — organized by 11 workflow phases (Discovery Analysis & Planning → Probing & Refinement → Checking for Readiness → Implementing → Reviewing Implementation → Improving Architecture → Refactoring & Code Cleaning → Improving Security → Syncing Documentation → Rebuilding Indexes & Tests → Committing & Pushing), each phase mapping to its skill. Rules are imperative — explicit always/never directives, no "consider" or "try to". Verification requirements are embedded within each phase's rules rather than a separate section.
- **Codebase Exploration** — Three-Tier classification: Tier 1 (Tiny, known exact files) / Tier 2 (Moderate, known area) / Tier 3 (Complex, unknown scope). Each tier has required steps, completeness safeguards, and a tool guidance table with token costs.
- **Documentation Discipline** — cross-referencing (not duplicating), file-level description comments, executable sources of truth (code > prose)
- **Process Discipline** — read-before-write, baseline tests before changes, exit declarations, user approval gate (line-level diffs), batch discipline with granular edits, source+tests as one unit, non-interactive execution, periodic test health audit
- **Failure Triage** — classification table for test failures (import path issue, brittle test, behavioral regression, pre-existing, flaky) with prescribed action for each type
- **Architecture overview** — 3-5 lines so agents can navigate the project structure. Full detail (module descriptions, file tree, data flow) stays in ARCHITECTURE.md.
- **Cross-references** — to ARCHITECTURE.md, SPECIFICATIONS.md, DOCUMENT_GUIDELINES.md, and skill files

For project context, product description, and key functionalities → [SPECIFICATIONS.md](../docs/SPECIFICATIONS.md) and [README.md](../README.md).  
For architecture summary and tech stack → [ARCHITECTURE.md](../docs/ARCHITECTURE.md).  
For setup commands and test commands → [README.md §Quick Start](../README.md#quick-start) and [README.md §Testing](../README.md#testing).  
For agent-specific operational requirements (non-interactive execution, venv setup) → [PROJECT_BEST_PRACTICES.md §8.15](PROJECT_BEST_PRACTICES.md#815-non-interactive-execution) and [README.md §Quick Start](../README.md#quick-start).

### What NOT to Include
- ❌ API endpoint tables or WebSocket event tables — these go in ARCHITECTURE.md (Data Flow section)
- ❌ Out of scope or product constraints — these go in SPECIFICATIONS.md
- ❌ Privacy hard requirements or trust model — these go in SPECIFICATIONS.md
- ❌ Detailed module descriptions or file trees — these go in ARCHITECTURE.md
- ❌ User-facing setup instructions or benefit descriptions — these go in README.md
- ❌ Product pitch, vision, or user journey — these go in SPECIFICATIONS.md
- ❌ Best practices philosophy or universal coding patterns — these go in PROJECT_BEST_PRACTICES.md

### Content Boundaries
- **File ownership:** Every entry must include a policy column (✅ safe, ⚠️ caution, ❌ forbidden). File names alone are not enough.
- **Agentic Workflow Rules:** Organized by workflow phase. Each phase header names the skill(s) it maps to. Rules are imperative sentences, one per bullet. Cross-reference the skill file for full detail.
- **Verification:** No standalone verification section — verification requirements are embedded in each phase's behavioral rules (e.g., Phase 4: "Verify locally per batch", "Run full test suite + lint before hand-off").
- **Cross-references:** Point to SPECIFICATIONS.md for product boundaries and privacy, ARCHITECTURE.md for endpoints and data flow, README.md for commands and setup. Do not duplicate content from other documents.

---

## 6. PROJECT_BEST_PRACTICES.md

### Scope
Universal development best practices derived from real sessions on this project. Answers "What lessons were learned?", "What patterns should I reuse in future projects?", "How should I approach common problems?".

### Audience
- Developers starting new projects
- AI agents learning transferable patterns

### Key Differentiator
**Universal over project-specific.** Not about this project — patterns proven here that apply elsewhere. This is the only document whose value extends beyond this repo. Every other document describes this project specifically. This one captures what any project can learn from. If a lesson mentions a specific module name or route from this project, it hasn't been properly generalized.

### What to Include
Practices are organized into 6 category clusters:

**Code Structure**
- **Modularization** — responsibility patterns, circular import prevention, leaf vs internal module design
- **Architecture Decisions** — universal patterns only (e.g., "separate I/O from business logic"). Project-specific decisions go in ARCHITECTURE.md.

**Quality**
- **Error Handling** — error types encountered, fix strategies, prevention patterns
- **Testing** — syntax checks, unit tests, integration tests, verification steps that caught real bugs

**Operations**
- **Configuration** — tool config patterns, environment setup practices
- **Version Control** — commit discipline, branching strategies, what to never commit

**Process**
- **Debugging Process** — how issues were isolated, tools and commands that worked
- **Documentation** — doc structure principles, scope distinctions, cross-referencing patterns
- **Skills Methodology** — skill architecture (one verb per skill, stage gates, triage routing), workflow patterns (interactive walkthrough, docs-first analysis), handoff patterns (persistent artifacts, file-based stage communication)
- **AI-Assisted Development** — prompting patterns that worked, skill usage, agent behavior insights

**UI**
- **Frontend Practices** — UI patterns, JS module organization, template conventions

**Meta**
- **Session Lessons Learned** — process meta-lessons that are genuinely cross-cutting and don't fit any named category above. **Do not use this as an overflow bin.** Categorize at entry time; only lessons that span multiple categories or describe the development process itself belong here.

### Entry Format

Every entry **must** follow this structure. No exceptions.

```
**[Practice Name]**
Context: [1 line — what situation triggers this]
Principle: [2-3 lines — the generalized rule, no project-specific names]
Example: [short snippet or scenario — project names allowed here for context]
Why it matters: [1 line]
```

### What NOT to Include
- ❌ Project-specific architecture decisions or module designs — these go in ARCHITECTURE.md
- ❌ User-facing instructions or setup steps — these go in README.md
- ❌ Product vision, user journey, or pitch — these go in SPECIFICATIONS.md
- ❌ Demo scripts or presentation steps — these go in DEMO_GUIDE.md
- ❌ AI agent file permissions or operational rules — these go in AGENTS.md

### Content Boundaries
- **Entry format:** Follow the Entry Format structure above without exception.
- **Project-specific names** are stripped from the Principle and kept only in the Example field for context.
- **One practice per entry.** If a lesson spans multiple categories, pick the PRIMARY category.
- **No duplicates.** If an entry already covers a principle, improve the existing entry instead of creating a new one.
- **Conciseness required.** Turn "We encountered a problem where indentation was incorrect in `__init__.py` which caused a syntax error" into "Indentation errors in `__init__.py` — verify after every edit."

---

## 7. AGENT_SETUP.md

### Scope
Agent development environment setup guide. Answers "How do I reproduce this project's AI coding assistant environment on any machine?"

### Audience
- Developers setting up a new machine for this project
- AI agents needing tooling context to operate correctly
- Teams wanting consistent, reproducible development environments

### Key Differentiator
**Setup over behavior.** Describes external tool dependencies, MCP server configuration, and environment requirements — not what the agent should do. AGENTS.md tells the agent how to behave; AGENT_SETUP.md tells the developer how to set up the machine so the agent can work.

### What to Include
- **Global environment prerequisites** — Python version, Node version, OpenCode/CLI installation, environment variables
- **Project-level dependencies** — package managers (uv, npm), MCP servers (graphify, cocoindex), project config
- **MCP server configuration** — opencode.json format, required servers with command arrays, verification steps
- **Skills and commands setup** — .opencode/skills/ and .opencode/commands/ structure
- **Code index and knowledge graph setup** — CocoIndex and Graphify initialization
- **Replication instructions** — step-by-step for copying this environment to another project
- **Post-copy verification** — checklist and test to confirm the environment works

### What NOT to Include
- ❌ Agent behavioral rules, workflow phases, or operational constraints — these go in AGENTS.md
- ❌ Project architecture or module descriptions — these go in ARCHITECTURE.md
- ❌ Coding best practices or lessons learned — these go in PROJECT_BEST_PRACTICES.md
- ❌ User-facing instructions — these go in README.md

### Content Boundaries
- **Environment-only focus.** Describe what must be installed and configured, not how the agent uses the tools.
- **Replicable steps.** Every instruction must produce the same result on a clean machine.
- **Cross-reference AGENTS.md** for agent behavioral rules that depend on tooling setup.
- **Keep opencode.json examples current** — the MCP server format changes with OpenCode versions.

---

## 8. DOCUMENT_GUIDELINES.md (this document)

### Scope
Meta-governance for all project documentation. Answers "Where does this content go?", "What belongs in each document?", "How do I add a new document?".

### Audience
- Developers and AI agents deciding where to write new content
- Anyone maintaining or extending the project's documentation

### Key Differentiator
**Meta over content.** Does not contain project content — it describes where project content lives. This is the only document about documents. If you are unsure where something belongs, start here. If you are adding a new document, update this file first.

### What to Include
- **Quick Reference Table** — one-row-per-document summary of audience, purpose, routing, update trigger, and content type
- **Per-document differentiation sections** — for each doc: scope, audience, key differentiator, what to include, what not to include, content boundaries
- **Boundary Tensions** — known overlap points between documents with explicit resolution guidance
- **Anti-Duplication Rules** — principles for avoiding content overlap across documents
- **Workflow-to-Document Dependency** — which documents each workflow step reads and writes, with section-level grep targets
- **Checklist** — verification steps before adding content to any document

### What NOT to Include
- ❌ Actual content from any document. Describe boundaries, don't duplicate content.
- ❌ Project-specific implementation details. Reference the document that owns them.
- ❌ Agent operational rules — these go in AGENTS.md.

### Content Boundaries
- **Never copy** content from other documents. Reference them.
- **Update this file** whenever a new document is added — add a table row and a new differentiation section.
- **Keep the checklist current** — it should reflect the actual decision process for routing content.

---

## Anti-Duplication Rules

1. **One purpose per document** — If content fits two documents, choose the PRIMARY purpose. Don't split the same content across multiple docs.

2. **Cross-reference, don't copy** — Use `[See ARCHITECTURE.md](ARCHITECTURE.md)` instead of pasting sections from one document into another. A reference is better than a duplicate.

3. **Summary here, details there** — Documents at the top of the funnel (README.md) get summary tables and navigation-level overviews. Documents deeper in (ARCHITECTURE.md, AGENTS.md) get the full detail. AGENTS.md gets high-level Agentic Workflow Rules with cross-references to detail docs. ARCHITECTURE.md gets the authoritative data flow with endpoint tables. Example: `routes.py` — file tree gets "HTTP route handlers" (5 words), Module Descriptions gets lead line + endpoint list, `#### Functions` gets every handler with method/path + one-line purpose. Each level adds detail without duplicating.

4. **Audience-first** — If audience overlaps, choose the document with the MOST RELEVANT audience. A developer reading about architecture doesn't need the same content as a user reading the README.

5. **Update this guide** — If you add a new document, add a row to the Quick Reference Table and a new numbered section following the same structure: Scope, Audience, Key Differentiator, What to Include, What NOT to Include, Content Boundaries.

---

## 9. Workflow-to-Document Dependency

This section defines which documents each workflow step should read, and which specific sections (via Grep→Read) to minimize context waste.

### Reading Pattern
Use Grep→Read to read specific sections: grep for the section heading line number, then `Read(offset=line, limit=~20)`. Do not read entire documents unless specified as "(full)".

### Core Pipeline

The pipeline branches after `review-implementation` (1st pass):

```
review-implementation (1st pass)
    ├──→ improve-architecture → review-implementation (architecture pass) → update-docs
    ├──→ modularize-and-clean → review-implementation (clean up pass) → update-docs
    ├──→ improve-security → review-implementation (security pass) → update-docs
    └──→ update-docs
```

| Step | Documents to READ | Specific Sections | Documents to WRITE |
|------|-------------------|-------------------|--------------------|
| **brainstorm-and-plan** | `SPECIFICATIONS.md`, `ARCHITECTURE.md`, `AGENTS.md` | SPECS: task-dependent (product vision, user flow, Out of Scope). ARCHITECTURE: "Project Structure", "Module Descriptions" (relevant entries), "Import Structure", "Modifying Instructions". AGENTS: "File Ownership", "Failure Triage", "Codebase Exploration" | nothing (verbal) |
| **grill-and-refine** | `ARCHITECTURE.md` | "Project Structure", "Module Descriptions" (relevant), "Data Flow", "Key Design Decisions", "Import Structure", "Critical Implementation Details" | nothing (verbal only — this step produces no artifact; if issues require a revised plan, loop back to check-plan-readiness) |
| **check-plan-readiness** | *(none — gates 1-4, 6-7 are presence-checks on plan; gate 5 soundness validated by grill)* | — | `docs/PLAN_*.md` |
| **implement-plan** | `docs/PLAN_*.md`, `AGENTS.md`, `ARCHITECTURE.md`, `SPECIFICATIONS.md` | PLAN: all. AGENTS: "File Ownership", "Failure Triage", "Codebase Exploration". SPECS: "Out of Scope". ARCHITECTURE: "Project Structure", "Import Structure", "Modifying Instructions", relevant module descriptions only | Source code, tests |
| **review-implementation** (1st pass) | `docs/PLAN_*.md`, `ARCHITECTURE.md` | PLAN: all. ARCHITECTURE: "Import Structure", relevant module descriptions (verify diff fits system) | nothing (verbal) |
| **improve-architecture** | `ARCHITECTURE.md`, source files | ARCHITECTURE: "Project Structure", "Import Structure", relevant module descriptions | Source code (`[ARCH]`), regression tests |
| **improve-security** | `ARCHITECTURE.md`, `SPECIFICATIONS.md`, source files | ARCHITECTURE: "Project Structure", "Module Descriptions", "Import Structure". SPECS: "Out of Scope". Source: key files per security scan area | Source code (`[SECURITY]`), regression tests |
| **modularize-and-clean** | `ARCHITECTURE.md`, test suite | ARCHITECTURE: "Project Structure", "Import Structure", relevant module descriptions. Test suite: note import paths for adaptation | Source code (`[CLEANUP]`), coverage tests, change-log |
| **review-implementation** (clean up pass — after modularize-and-clean) | `docs/PLAN_*.md` | PLAN only — change-log from modularize-and-clean suffices | nothing (verbal) |
| **review-implementation** (architecture pass — after improve-architecture) | `improve-architecture` Phase 1 output (verbal, session context) | — | nothing (verbal) |
| **review-implementation** (security pass — after improve-security) | `docs/PLAN_*.md` | PLAN only — security findings from improve-security | nothing (verbal) |
| **update-docs** | `update-docs/SKILL.md` (Doc Sync Triggers), session diff, prior phase output | Doc Sync Triggers table in update-docs SKILL.md | nothing (orchestrates update-* skills) |
| **push-to-git** | *(none — git status only)* | — | Git commits |

### Doc Sync Steps (Post-Implementation)

| Step | Documents to READ | Documents to WRITE |
|------|-------------------|--------------------|
| **update-docs** (orchestrator) | Session diff, `update-docs/SKILL.md` (Doc Sync Triggers table) | nothing (orchestrates update-* skills below) |
| **update-architecture-md** | `ARCHITECTURE.md` (full), `README.md`, all source files | `ARCHITECTURE.md` |
| **update-agents-md** | `AGENTS.md` (full), `ARCHITECTURE.md`, `SPECIFICATIONS.md`, `README.md` | `AGENTS.md` |
| **update-specifications-md** | `SPECIFICATIONS.md` (full), `README.md` | `SPECIFICATIONS.md` |
| **update-readme-md** | `README.md` (full) | `README.md` |
| **update-agent-setup-md** | `AGENT_SETUP.md` (full), global env state, project config files, `tests/test_agent_guidelines.py` | `AGENT_SETUP.md` |
| **update-best-practices-md** | `PROJECT_BEST_PRACTICES.md` (full), `.opencode/skills/*/SKILL.md`, `docs/PLAN_*.md`, session history, changed files only (not full codebase) | `PROJECT_BEST_PRACTICES.md` |

---

## Checklist Before Adding Content

Before adding content to any document, verify:

- [ ] I've identified the PRIMARY purpose of the content (what question does it answer?)
- [ ] I've checked the Quick Reference Table to find which document routes this type of content
- [ ] I've reviewed the target document's "What NOT to Include" section for disqualifiers
- [ ] I've checked the Boundary Tensions table if the content could fit multiple documents
- [ ] I've verified the content doesn't already exist in another document
- [ ] If content spans multiple purposes, I've split it appropriately across documents
- [ ] I've added cross-references instead of duplicating content
- [ ] I've written for the target document's specific audience, not a general audience

---

## Appendix: Archived Documents

### DEMO_GUIDE.md (Archived)

> **Archived:** This guide was preserved from the active document set. It is kept here for reference but is no longer actively maintained.

#### Scope
Practical demo execution guide. Answers "How do I demonstrate this?", "What should I highlight?", "What are the test scenarios?".

#### Audience
- Presenters demonstrating the app
- Evaluators and reviewers assessing the demo (judges, stakeholders, technical reviewers)

#### Key Differentiator
**Action over description.** Not what the product does — exactly what to click, what to say, what to expect at each step. Written for a presenter under pressure who needs to deliver a smooth demo. Every step must have a clear expected result. If it can't be demonstrated, it doesn't belong here.

#### What to Include
- **Document header** — "Last verified: [date] against [version/commit]". Demo guides go stale fast; currency must be explicit.
- **Prerequisites** — what must be running before the demo starts (services running, env vars set, data pre-loaded)
- **Quick start walkthrough** — ordered steps to reach a working demo state from scratch
- **Key features to demonstrate** — what to highlight and in what order for maximum impact
- **Testing scenarios** — discrete flows with exact actions and expected results. "Click X, expect Y to appear."
- **UI highlights** — what the runner should point to on screen at each stage
- **Technical features to highlight** — for technical evaluators who care about implementation
- **Demo tips** — separate guidance for different audience types (what technical evaluators care about vs. what general users care about)
- **Fallback options** — what to do if something breaks live. Must be actionable ("if X breaks, do Y"), not vague reassurance.
- **Reset instructions** — how to restore demo state after a run so it can be shown again
- **Success signals** — what the audience should feel or see at the end. Not technical metrics.

#### What NOT to Include
- ❌ Product vision, problem statement, or pitch — these go in SPECIFICATIONS.md
- ❌ Technical architecture or module descriptions — these go in ARCHITECTURE.md
- ❌ Full API endpoint tables — summaries go in README.md, detailed data flow goes in ARCHITECTURE.md
- ❌ AI agent permissions or operational rules — these go in AGENTS.md
- ❌ Best practices or coding philosophy — these go in PROJECT_BEST_PRACTICES.md
- ❌ Installation or setup instructions — these go in README.md

#### Content Boundaries
- **Testing scenarios:** Step-by-step actions with expected results. Not technical implementation.
- **Demo tips:** Must have separate sections for technical evaluators vs. general users. They care about different things.
- **Fallback options:** Must be actionable. "If the QR code doesn't load, refresh the page and try again." Not "try again later."
- **Success signals:** How the audience feels or what they see. Not technical metrics.
- **Language:** Presenter-focused throughout. Assume the reader is on stage with people watching.
- **Currency:** Always include a header: "Last verified: [date] against [version/commit]." Update this on every demo flow change.

---

> **Good documentation is invisible.** When in doubt, ask: "Who needs this information?" and "What action will they take after reading it?"