---
name: update-architecture-md
description: Analyze the current codebase and update `docs/ARCHITECTURE.md` to be accurate, complete, and within its defined scope. Trigger when the user says "update architecture", "sync architecture doc", "architecture is outdated", or similar.
---

## Purpose
Technical structure reference for the project. Answers "How is it built?", "What are the modules?", "How do I modify it?".

Analyze the codebase and session history, then update or create `docs/ARCHITECTURE.md` so developers and AI agents have an accurate technical reference.

---

## Audience
- Developers working on the codebase
- AI agents making code changes
- Technical reviewers evaluating the implementation

---

## Invocation Modes

This skill supports two invocation modes. **Explicit** (default, standalone): follows the full Investigation Protocol below. **Implicit** (invoked by `update-docs` Phase 3): investigation is scoped to diff files from the caller. In implicit mode the full Investigation Protocol below is replaced by a delta scan — only analyze changed files against the current document. Graphify context is provided by `update-docs`; skip the Phase 0 graphify query.

---

## Content Rules

### Quality Gates
- **"Would a developer or agent miss this?" litmus test:** Every line must answer "Would a developer or agent likely miss this without help?" If not, leave it out.
- **Technical accuracy:** Every claim must be verifiable against actual source code — not inferred from filenames alone.
- **Executable sources of truth:** Prefer configs, scripts, and code over prose documentation. If docs conflict with code, trust the code.
- **Conciseness:** File tree gets ~10-word descriptions; per-function entries are one-line-only. Full detail belongs in source docstrings, not here.

### What to Include

**Universal sections** (present in every project's ARCHITECTURE.md):
- **Project file tree** — concise (1-line) descriptions per directory and key file for quick navigation
- **Module Descriptions** — organized into subsections matching the project's directory structure (e.g., Python backend modules, frontend modules by layer). Each entry: 1-sentence lead line from source file's description header, bullet points for key responsibilities, and a `#### Functions` per-function detail subsection
- **Tests** — per-file function descriptions with signature + one-line purpose (navigation map per test module)
- **Maintenance Scripts** — utility scripts with purpose and exact run command
- **Critical Implementation Details** — non-obvious runtime behavior: resource management, match expiry, WebSocket config, frontend module rules, demo mode guards
- **Data flow** — describe the main data path through the system (processing pipeline, request lifecycle, or event flow) via a numbered flow, plus REST API Endpoints table (method, path, purpose) and WebSocket Events table (event name, direction, payload)
- **SPA Serving** — how the SPA is served: route, assets mount, catch-all handler — standalone section, not nested inside Data Flow
- **Import structure and dependency graph** — how modules depend on each other
- **Key design decisions** — include the *why*, not just the *what*. Technical rationale only
- **Running Instructions** — full technical startup sequence: environment setup, dependencies, configuration, commands
- **Modifying Instructions** — how to add modules, extend functionality, change providers or configuration
- **Per-function detail** — every named function/class in every module (embedded inside its Module Description entry as `#### Functions` subsections) with signature and one-line purpose (navigation map, not a manual)

**Optional sections** (include only if the project has them):
- **API/WebSocket endpoint tables** — for web servers or APIs with documented endpoints
- **Pipeline stage diagrams** — for multi-stage data processing pipelines
- **Sub-architecture references** — links to specialized architecture docs for subsystems

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

The skeleton below is used for every project's `ARCHITECTURE.md`. Markers like `<!-- FILL: name -->` indicate where project-specific content is injected. Sections without markers are included verbatim.

```markdown
# Architecture - [Project Name]

> **Last verified:** [date]

## Project Structure
[Complete file tree with descriptions]

## Module Descriptions
[Organized by directory/subsystem; each entry: lead line, bullets, per-function detail]

## Tests
[Per-file function descriptions with signature + one-line purpose — navigation map per test module]

## Maintenance Scripts
[Utility scripts with purpose and exact run command]

## Critical Implementation Details
[Non-obvious runtime behavior: resource management, match expiry, WebSocket config, frontend module rules]

## Data Flow
[Numbered main data path, REST API Endpoints table, WebSocket Events table]

### REST API Endpoints
[Method, path, purpose — authoritative endpoint reference]

### WebSocket Events
[Event name, direction, payload — authoritative event reference]

## SPA Serving
[How the SPA is served: route, assets mount, catch-all handler]

## Import Structure
[Dependency graph showing how modules depend on each other]

## Key Design Decisions
[Technical rationale — why, not just what]

## Running Instructions
[Startup sequence: env, dependencies, config, commands]

## Modifying Instructions
[How to add modules, extend functionality, change configuration]

<!-- FILL: optional-sections -->
```

Optional sections (include only if applicable): sub-architecture reference links, pipeline stage diagrams.

> **Note:** REST API Endpoints and WebSocket Events tables are required for user-facing web server projects only — internal subprocess servers (e.g., vLLM) don't need them. The tables live inside the Data Flow section, not as separate optional sections.

---

## Phase 0: Prerequisites

- [ ] Run `graphify query_graph "architecture / module structure"` — understand relationship context with all source modules, imports, and docs
- [ ] Verify source code exists and matches current project state
- [ ] Read existing ARCHITECTURE.md — understand current documented structure
- [ ] Run codebase search for new modules added since last sync
- [ ] Consult README.md (project root) for project overview
- [ ] Determine invocation mode — if implicit, skip full codebase walk and accept scope from caller (diff context)

## Workflow

> **Explicit mode only.** For implicit mode see Invocation Modes.
>
> **Investigation Protocol:** Investigation compares the current document against the current codebase — not against previous session changes. Pre-existing discrepancies (stale paths, outdated descriptions, missing sections, incorrect claims) are gaps to flag regardless of when they were introduced.

### Phase 1: Investigate the Codebase
Read highest-value sources first in this priority order:

1. Source code files — entry points, modules, all source files in the project's main directories
2. Configuration and constants files
3. Core infrastructure modules (e.g., caches, utility layers)
4. `README*`, root manifests (`package.json`, `pyproject.toml`, etc.), lockfiles
5. Build, test, lint, typecheck configs
6. Existing architecture document and any sub-architecture design docs
7. OpenCode plugin/config files (if present)

For each source, extract:
- What modules exist and what does each do?
- What is the main data flow or processing pipeline?
- What are the import dependencies between modules?
- What critical implementation details exist (resource constraints, schema patterns, lifecycle rules)?
- What design decisions are visible in the code structure?
- What is the full technical startup sequence (env, config, commands)?

**Check session history for design rationale:** Review the current conversation for explanations of *why* a pattern was chosen, trade-offs discussed, and decisions made during debugging that reveal architectural intent. Capture only rationale — not session-specific debugging details.

#### Extract Descriptions from Source Files

For every source file in the project's main source directories:

```
Scan first 10 lines for pattern matching the project's description convention:
- `/Description: (.+)/` for languages with `//` or `#` line comments
- docstring patterns for languages with block documentation (Python `"""`, JS `/** */`)
```

**For each file, record:**
- `filename`: relative path from project root
- `lead_line`: extracted description text
- `status`: `ok` (found), `missing` (no header)

**Group into categories matching the project's directory structure** (e.g., by subsystem: entry points, core lib, config, tests).

**Cross-reference against current Module Descriptions section:**
- File exists in both → mark for lead line update
- File exists in codebase but not in architecture doc → mark as `new`
- File exists in architecture doc but not in codebase → mark for removal
- File has no description header → mark as `missing`

#### Extract Per-Function Details

For every source file that contains functions/classes:

**Parse function/class declarations** using patterns matching the project's language:

| Language | Patterns to match |
|----------|------------------|
| Python | `def func_name(params):`, `async def func_name(params):`, `class ClassName:` |
| JavaScript/TypeScript | `function funcName(params) {`, `const funcName = (...) => {`, `export function`, `class ClassName {` |

- Skip: constructors (`__init__`), dunder/private methods, inline callbacks
- Include: named functions, class definitions, exported functions, `main()` or entry points

**Check each declaration for description:**
- Scan for docstrings or description comments immediately preceding the declaration
- If the project uses a `// Description:` or `# Description:` convention, scan the line above

**Record for each function:**
- `filename`: relative path
- `function_name`: exact name from declaration
- `params`: parameter list as written in source
- `description`: extracted description first line (or `⚠️ missing`)

**Entry format for architecture doc:**
```
- `function_name(params)` — one-line purpose (what it does for the system)
```

### Phase 2: Read the Current Document
- Check if `docs/ARCHITECTURE.md` exists — create it if not
- Read existing content section by section
- Flag anything outdated (wrong file tree, missing modules, stale descriptions)
- Flag missing items from **What to Include**
- Flag content that violates the boundary rules

### Phase 3: Identify Gaps and Issues

**From Investigation:**
- Files marked `new` → need entries added in Module Descriptions
- Files marked `missing` → flag for manual fix or generate fallback entry
- Files marked for removal → remove their entries
- Files with stale lead lines → update lead line from extraction

**From document review:**
- Is the file tree current? Are all directories described?
- Does the data flow reflect all current pipeline stages?
- Does the running instructions section cover the full startup sequence?
- Are design decisions up to date?
- Is the project tree complete compared to actual filesystem listing? Compare every directory and file in the tree against actual filesystem entries — no phantom entries (documented but deleted) and no missing entries (exist but undocumented)
- Are all numeric claims (file counts, page export counts, test file counts, etc.) verified against actual source? Cross-reference each number against the real codebase
- Are cross-references between files in the tree and their documented descriptions accurate? Every file path in the tree must correspond to an actual existing file
- For renamed files: have all references been updated across all sections (project tree, module descriptions, tests table)? A renamed file often leaves stale entries under its old name in multiple sections.
- Are configuration-driven version constants verifiable against the source files they reference (e.g., YAML prompt files, JSON configs, TOML manifests)? Every version constant must have a corresponding entry in its referenced source.

### Gate: User Confirmation

Present proposed oldString→newString diffs to the user for approval before applying any edits. Use the `question` tool with clickable options.

### Phase 4: Assemble or Update the Document

**If ARCHITECTURE.md doesn't exist (create from scratch):**
1. Start with the **Universal Template** from this skill
2. Replace `<!-- FILL: optional-sections -->` with any applicable optional sections
3. Fill in each section with discovered project-specific content
4. Update the `> **Last verified:**` line to today's date (YYYY-MM-DD HH:MM TZ format)

**If ARCHITECTURE.md already exists (surgical update):**
- For each universal section: compare against discovered data and update only what changed (file tree, module descriptions, data flow, import structure, etc.)
- **Import structure:** Re-generate the import graph when dependencies change. For Python, scan `import`/`from` statements across source files or use the project's graph tool (e.g., `graphify`). For TypeScript/JavaScript, scan `import`/`require` statements.
- For each optional section: add if applicable and missing, remove if no longer applicable, update if stale
- Never rewrite the whole file — use targeted edits on changed sections only
- Update the `> **Last verified:**` line to today's date (YYYY-MM-DD HH:MM TZ format) — always update, even if no other changes were needed

**Module Descriptions — lead line replacement:**
For each entry in the Module Descriptions section, match by filename:
- Replace the lead line with the extracted description from the source file
- Preserve existing bullet points below — they contain implementation details not present in code headers

**Per-function subsections — auto-generation:**
For each module entry that has functions extracted in Step 1.75, insert or replace the per-function detail subsection:
1. Insert after the last bullet point in the entry
2. List every function in source file order (top to bottom)
3. One-line purpose only — no implementation logic

### Phase 5: Verify

**Integrity & Scope:**
- [ ] Every piece of content belongs in this document per the What NOT to Include table — redirect if it belongs elsewhere
- [ ] No content duplicated from another document — use `See <DOC>.md` cross-references instead
- [ ] All claims verified against executable sources (code, config, workflows), not just docs
- [ ] Document omits everything a developer or agent doesn't need — no speculative, aspirational, or unverifiable content

**Content checks:**
- [ ] File tree cross-referenced against actual filesystem entries — no missing or phantom entries
- [ ] All numeric claims verified against actual source (file counts, export counts, test counts) — use `python -m pytest tests/ --collect-only` (Python) or equivalent for other languages to get exact test count
- [ ] File tree is current and complete — all source directories and key files described
- [ ] Data flow reflects the current system — numbered flow + REST API Endpoints table + WebSocket Events table — this is the authoritative reference
- [ ] SPA Serving section documents how the SPA is served (route, assets mount, catch-all handler) — standalone section, not nested inside Data Flow
- [ ] Module Descriptions section organized by directory/subsystem with accurate lead lines — includes Frontend Modules subsection if the project has a frontend directory
- [ ] Tests section has per-file function detail for every test module — function signatures with one-line purpose
- [ ] Maintenance Scripts section lists each utility script with purpose and exact run command
- [ ] Critical Implementation Details covers all non-obvious runtime behavior (match expiry, WS config, frontend module rules, demo mode)
- [ ] Design decisions include the *why* (technical rationale only)
- [ ] Running the Application section covers full startup sequence (env, config, dependencies, commands)
- [ ] Modifying the Architecture section is accurate for the current codebase
- [ ] Every source file with functions has a per-function detail subsection
- [ ] Function entries are one-line purpose only — no implementation logic
- [ ] Missing descriptions are flagged with `⚠️` marker — never invent descriptions
- [ ] `> **Last verified:**` date is current — updated to today (YYYY-MM-DD HH:MM TZ)

## Hand-off
- Phase 1: Investigation complete — codebase scanned, descriptions extracted, per-function detail collected
- Phase 2: Current document read and compared against codebase
- Phase 3: Gaps and issues identified
- Gate: User confirmed proposed diffs
- Phase 4: Document assembled or updated
- Phase 5: Verification complete — all checks pass

## Outputs & Triggers

### Output
Updated `docs/ARCHITECTURE.md` at `docs/ARCHITECTURE.md`.

### Exit Declaration
State clearly: "**ARCHITECTURE.md updated. All checks pass.**"

### Next Step
Return to `update-docs` orchestrator for cross-reference audit.