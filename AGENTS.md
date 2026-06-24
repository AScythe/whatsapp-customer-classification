# AGENTS.md

> **Last updated:** 2026-06-11 18:00 EDT

---

## Agentic Workflow Skills

**Rule:** Identify the current phase of your activity (or detect a trigger phrase in user input), then load the corresponding skill via `skill(name: ...)` before acting. Never execute phase work without it.

| Phase | Name | Skill | Trigger (user says...) |
|-------|------|-------|------------------------|
| 1 | Discovery, Analysis, and Planning | `brainstorm-and-plan` | "brainstorm and plan", "analyze and plan", "analyze the requirements" |
| 2 | Probing and Refinement of Plan | `grill-and-refine` | "grill the plan", "stress-test the plan", "interrogate the plan" |
| 3 | Checking for Readiness of Plan | `check-plan-readiness` | "finalize the plan", "check plan readiness", "is the plan ready?" |
| 4 | Implementing of Plan | `implement-plan` | "implement", "implement plan", "proceed" |
| 5 | Reviewing of Implementation | `review-implementation` | "review the implementation", "verify changes", "review and verify" |
| 6 | Improving Architecture | `improve-architecture` | "evaluate the architecture", "improve architecture", "review project structure" |
| 7 | Refactoring and Code Cleaning | `modularize-and-clean` | "modularize", "clean up", "refactor" |
| 8 | Improving Security | `improve-security` | "security review", "audit security", "improve security posture" |
| 9 | Syncing Documentation | `update-docs` | "sync docs", "update docs", "docs are outdated" |
| 10 | Rebuilding Indexes and Tests | `rebuild-test-and-indexes` | "rebuild test and indexes", "rebuild indexes", "update tests", "reindex" |
| 11 | Committing and Pushing | `push-to-git` | "push", "commit and push", "push to github" |

**Key ordering rules:**
- Phases 1–3 must complete before Phase 4. Never implement without a plan that passed all 7 gates.
- Phases 6, 7, and 8 are optional branches after a passing Phase 5. By default, offer all three combined (see combined execution sections in each skill). Do not default to only one or two.
- Phases 9–10 (sync docs and rebuild indexes) run in series after review is complete, before committing.
- Phase 11 runs at end of session.

---

## Skill Loading Priority

**Rule:** Before every response, scan all skill descriptions to determine if user input matches a skill's trigger keywords (`description` field in the skill's frontmatter). If a match is found, load that skill via the `skill` tool before proceeding.

**Priority chain:** Skill loading > opencode.ai help lookup > Task tool delegation > default response
**Pre-Task gate:** Before using the Task tool or delegating to a subagent, verify that no skill matches the user's intent. Skills have priority over subagent delegation.
**Ambiguous matches:** When uncertain whether a skill matches, err on the side of loading it. Loading an irrelevant skill wastes context; missing a needed skill breaks workflow compliance.
**Multiple matches:** If user input matches multiple skills, load the skill corresponding to the current [agentic phase](#agentic-workflow-skills). If none corresponds, ask the user which skill to use.
**No match:** If no skill matches, proceed with the default response.

---

## Codebase Exploration

**Rule:** Before every edit, run `graphify query_graph "<task scope>"` first — mandatory blast-radius check. Knowing the exact file paths is not enough; graphify reveals relationship context you might miss. This is the first step, not a fallback. The only exception is Tier 1 (known exact files, see below).

### Three-Tier Classification

Classify your task scope **before** touching any tool. The tier determines the depth of exploration:

| Tier | When to use | Required steps |
|------|-------------|----------------|
| **Tier 1 — Tiny** | 1-2 exact files known, trivial bug fix (typo, missing line, prop change) with zero ambiguity about location | Skip graphify. Read only the target files with `offset/limit`. One `edit` and done. |
| **Tier 2 — Moderate** | Known area but exact files or root cause unclear; touches 2-5 files across a single community | graphify query_graph (1 query) → cocoindex-code (semantic search) → ast-grep (pinpoint locations) → Read(offset/limit) |
| **Tier 3 — Complex** | Unknown scope entirely; multiple communities; new feature; cross-module change | Full Pipeline (graphify 3 variations × 2 sub-graphs → cocoindex-code → ast-grep → Read) |

### Tool Reference

| If you need to... | Use | Token cost (1-5) |
|---|---|---|
| Find text/regex patterns by exact match | `grep` | 1 (cheapest) |
| Find files by name | `glob` | 1 |
| Find code by meaning / intent when you don't know the exact names | `cocoindex-code_search` | 2-3 |
| Find code structures (classes, functions, call sites) — structural, no false positives in strings | `ast_grep_search` | 2-3 |
| Map relationships, dependencies, blast radius | `graphify` | 3-5 |

**Selection rule:** Before running `grep`, ask: *"Do I know the exact text to search for?"* If no, use `cocoindex-code` or `ast-grep` instead — grepping 20 blind patterns costs more tokens than one semantic search. After any of these three locate specific line numbers, switch to `Read(path, offset=<line>, limit=~20)`.

### Pipeline (3-stage — Tier 3 only, Tier 2 skips to stages 2-3)

```
Stage 1: Scope — graphify query_graph (see Tier rules above)
Stage 2: Search — cocoindex-code (semantic search within scope)
Stage 3: Verify — ast-grep (structural pattern confirmation) → Read (exact lines)
```

**Fallback:** If current tool returns nothing relevant, try the next in order. Edge case: if **Graphify returns 0 nodes**, run cocoindex-code unscoped, then ast-grep.

### Discipline

- **Default to offset/limit:** `Read(path, offset=<line>, limit=~20)` for pinpointed locations. Full-file reads only when file ≤ 50 lines or first-time exploration of a new file. Exception: if the file's line count is needed (e.g., to verify nothing follows), read with `limit=0` first to get the count, then `offset/limit` for content.
- **Batch reads in parallel:** When multiple files need reading, send one message with concurrent `Read` calls — never read files one-at-a-time in separate messages.
- **Run `ast_grep_search` before reading:** A structural pattern pinpoints exact line numbers, then `Read(offset=line, limit=20)` avoids reading the entire file. Never read a 200+ line file to find 5 lines of code.
- Avoid low-signal files: `frontend/dist/`, `archive/`, `.cocoindex_code/`, `graphify-out/cache/`, `uv.lock`
- After each phase: state which tools you used and why you skipped the others. If you used `grep` when a smarter tool was applicable, flag it proactively.
- For search across 3+ files: prefer `cocoindex-code` (one search matches across all files) over sequential `grep` calls.

### graphify specifics

- Query tools: `graphify query_graph` (broad), `graphify shortest_path` (relationships), `graphify get_community` (all files in a group)
- Sub-graphs: MCP serves full graph; CLI with `--graph graphify-out/graph-code.json` (code) or `graphify-out/graph-document.json` (docs)
- Completeness safeguards scale with tier: Tier 2 = 1 query per relevant sub-graph (if ≤3 nodes, switch to cocoindex-code); Tier 3 = query 3 variations × 2 sub-graphs = 6 queries (if ≤4 files or low confidence, expand to include all files in returned communities)

---

## Process Discipline

**Integrity:** Read-before-write, baseline tests, and failure triage.
- **Plan mode = zero file modifications** — no Edit, Write, bash file manipulation, or any system change. Enforced by global config `agent.plan.permission`: edit/write = `"deny"`, bash = `"ask"`.
- **Read before write** — planning phases never modify files. See plan-mode guard rule above.
- **Baseline before changes** — run tests before starting; pre-existing failures block proceed.
- **Failure triage** — classify via the [table](#failure-triage); never auto-revert.

**Execution:** How to work across phases.
- **Exit declarations** — every phase states output, verification, next step.
- **User approval gate** — before every file modification, show the user the exact diff (old → new lines) and wait for explicit sign-off. Bullet-point summaries of changes do not count — the actual line-level diff must be presented.
- **Propose-Review-Apply pipeline for delegated work** — when delegating to sub-agents via Task tool, use a three-phase pattern:
  1. **Propose (parallel):** Sub-agents analyze and return `oldString→newString` proposals only — they are read-only, never call `edit`/`write`/`bash`
  2. **Review (serial):** Main agent collects all proposals, presents them to the user one batch at a time for approval
  3. **Apply (serial):** Main agent applies approved edits only after user sign-off
  This preserves parallelism for analysis while ensuring every change is reviewed before application.
- **No scope creep** — only what the phase specifies; no speculative additions.
- **Batch discipline + granular edits** — one logical change per edit, one concern per batch.
- **Surgical edits** — prefer `oldString→newString` over full-file rewrites.
- **Non-interactive execution** — never pipe to stdin or omit `-m`/`-y`.
- **User Interaction Pattern** — all agent-to-user questions and decision points MUST use the built-in `question` tool with clickable selectable options. This is the sole mechanism for gathering user input — never use raw text prompts, free-form "ask before proceeding", or unformatted "y/n" questions.
  - Always provide `options` with both `label` (short option name) and `description` (explanatory hint) fields.
  - Rely on the tool's auto-added "Type your own answer" option for free-form input when no offered option fits.
  - Walk through decision-points ONE AT A TIME — never present multiple items in a single message. Resolve before moving to the next.
  - Within each topic, follow the structured sequential walkthrough: (1) state finding concisely, (2) present options via `question` tool, (3) resolve before moving to the next topic.
  - To determine which topics need discussion: present only topic NAMES upfront — do not describe their contents or list items within them. The agent chooses the order and walks through sequentially.
- **`question` tool blocks mode transitions — NEVER use for mode switches.** The `question` tool creates a modal widget that prevents the user from toggling Plan↔Build mode. While `question` is active, the user cannot switch modes. This creates a dead end: they select "proceed" but edits are denied (plan mode). Therefore:
  1. **End of plan phase = plain text only.** Never use `question` to ask "shall I proceed?" or "ready to implement?" — the user must switch modes externally. Last line must be: "Plan ready. Switch to build mode and I'll execute."
  2. **End of build phase = plain text only.** Never use `question` to ask "switch to review mode?" Last line: "Build complete. Switch to plan mode for review."
  3. **Skill-to-skill handoffs within the same mode** — may use `question` for intermediate decisions (e.g., "which approach?"), but the final "handing off to skill X" statement must be plain text.
  4. **During an active build session**, `question` is fine for diff approvals, preference questions, etc. — because no mode switch is needed. The prohibition is specifically on asking the user *to change modes* via `question`.

**Hygiene:** Quality and cross-cutting checks.
- **Run full test suite after every change** — all suites, not just new tests.
- **Source and tests are one unit** — update all test references in the same batch as source changes.
- **Periodic test health audit** — inspect test files for stale file paths, misleading comments, and coverage gaps (files tested for exports but missing from existence checks). A passing test suite can still have stale references.
- **Audit after restructure/migration** — update owning skills; grep for stale patterns.
- **Consistency pass** — after multi-file changes, read affected files end-to-end.
- **Keep index/graph current** — always run `rebuild-test-and-indexes` before review verification (handled by Phase 0 of `review-implementation`). If querying graph/index mid-implementation, rebuild manually. Phase 9 (rebuild) and Phase 10 (sync docs) run together after review.

---

## File Ownership

**Rule:** Consult this table before editing any file. Every file has a defined agent policy — respect ⚠️ (caution) and ❌ (forbidden). Files not listed are safe to edit by default.

| Location | Role | Agent Policy |
|----------|------|--------------|
| `app/config.py` | Server config and env var bindings | ⚠️ Edit only for config changes — verify all consumers after change |
| `frontend/dist/` | Built output — auto-generated by `npm run build` | ❌ Never edit manually — rebuild instead |
| `frontend/node_modules/` | NPM dependencies | ❌ Never edit — managed by npm |
| `frontend/tests/e2e/` | Playwright E2E test scenarios | ⚠️ Edit only when adding new user flows — verify all tests pass |
| `agent_utility/filter_graph.py` | Graph sub-type filter — generates graph-code.json and graph-document.json | ⚠️ Re-run after every graph rebuild |
| `utility/cleanup_db.py` | Database cleanup — deduplicates events, rooms, users, matches | ⚠️ Re-run after E2E tests or manual test user creation |
| `agent_utility/enhance_graph_viewer.py` | Enhanced graph viewer — post-processes graph.json for interactive HTML | ⚠️ Re-run after every graph rebuild |
| `agent_utility/dedup_graph_nodes.py` | Graph node deduplication — merges ghost nodes that differ only by import path representation | ⚠️ Run after every graphify rebuild (auto-invoked by rebuild-test-and-indexes skill) |
| `data/introchat.db` | Persistent data store | ⚠️ Never delete without explicit user confirmation |
| `data/e2e_test.db` | E2E test temporary data store | ⚠️ Never delete without explicit user confirmation |
| `tests/test_*.py` | Regression tests | ⚠️ Run only — do not modify unless explicitly asked. Exception: structural validation tests (file-existence checks, export/import references, code-quality scan targets) updated by `review-implementation` Phase 0 to match project structure |
| `docs/PLAN_*.md` | Active plan (during implementation/review) | ⚠️ Read-only — only `check-plan-readiness`, `modularize-and-clean`, and `improve-architecture` write these; moved to `archive/plan/` after review |
| `archive/plan/PLAN_*.md` | Completed/reviewed plan artifacts | ⚠️ Archived — moved here after successful review; in `.ignore` to avoid context waste |
| `opencode.json` | Plugin and MCP server configuration | ⚠️ Edit only for plugin/MCP config changes — verify JSON validity |
| `.cocoindex_code/` | CocoIndex code index (auto-generated) | ❌ Never edit manually — rebuild via `ccc index` |
| `graphify-out/` | Graphify knowledge graph outputs (auto-generated) | ⚠️ Commit graph.json/GRAPH_REPORT.md for team sharing; gitignored: manifest.json, cost.json |
| `.ignore` | Context ignore rules (avoids low-signal files) | ⚠️ Edit when adding/removing low-signal file patterns |
| `.opencode/skills/*/SKILL.md` | agentic workflow skill definitions | ⚠️ Replicable — copy to new projects (see [AGENT_SETUP.md](refs/AGENT_SETUP.md#replicating-to-another-project)) |
| `refs/*.md` | Reference docs — agent guidelines, best practices | ⚠️ Replicable — copy to new projects (see [AGENT_SETUP.md](refs/AGENT_SETUP.md#replicating-to-another-project)) |
| `tests/test_agent_guidelines.py` | Agent guideline compliance tests | ⚠️ Replicable — copy to new projects (see [AGENT_SETUP.md](refs/AGENT_SETUP.md#replicating-to-another-project)) |

---

## Failure Triage

**Rule:** When a test fails after a change, classify before acting. Never auto-revert.

| Symptom | Classification | Action |
|---------|---------------|--------|
| `ImportError`, `ModuleNotFoundError` | Import path issue | Fix the import — do not revert the source change |
| Test assertion fails but logic is correct | Brittle test | Update the test to match new expected behavior |
| Test fails and the change breaks intended behavior | Behavioral regression | Revert or skip the change — report to user |
| Pre-existing failure (failed before your change) | Baseline failure | Flag it — do not proceed until user resolves |
| Intermittent, not tied to change | Flaky / environment issue | Re-run once; if it fails again, flag as flaky — do not revert |

---

## Commands Reference

**Rule:** Use these exact commands for common operations. Run from the project root unless specified otherwise. Do not deviate — they are the canonical, tested commands.

| Operation | Command | Notes |
|-----------|---------|-------|
| Build frontend | `cd frontend ; npm run build` | Required after any frontend change |
| Run app (dev) | `uv run python -m app` | Serves on `localhost:5000` |
| Run frontend dev server | `cd frontend ; npm run dev` | Vite on port 3000, proxies to backend |
| Run all backend tests | `uv run python tests/test_app.py` | |
| Run frontend unit tests | `cd frontend ; npm test` | Vitest runner |
| Run E2E tests | `cd frontend ; npm run test:e2e` | Playwright — auto-installs Chromium, builds SPA, starts app with temp DB |
| Type-check frontend | `cd frontend ; npx tsc --noEmit` | TypeScript strict mode |
| Clean up database duplicates | `uv run python utility/cleanup_db.py` | Removes User_* test users; run after E2E tests |

---

## Test Suite Structure

**Rule:** Run the full test suite after every change. Backend tests run standalone; frontend tests require `cd frontend` first. E2E tests auto-build the SPA before running.

See [Test Structure in ARCHITECTURE.md](docs/ARCHITECTURE.md#tests) for per-file breakdown and function-level detail.

| Location | Naming convention | Run command |
|----------|------------------|-------------|
| `tests/test_*.py` | `test_<topic>.py` — Python unittest | `uv run python tests/<file>.py` |
| `frontend/tests/**/*.test.{ts,tsx}` | `<Module>.test.{ts,tsx}` — Vitest per-component | `npm test` (from `frontend/`) |
| `frontend/tests/e2e/*.spec.ts` | `<flow>.spec.ts` — Playwright E2E | `npm run test:e2e` (from `frontend/`) |

**Policies:**
- Backend test files (`tests/test_*.py`) — **run only**, do not modify unless explicitly asked
- Frontend test files — **update in same batch** as source changes per source-and-tests rule
- E2E tests — **edit only** when adding new user flows; verify all tests pass

---

## Utility Skills

**Rule:** Non-phase skills are invoked as sub-steps within agentic phases or on-demand — never as standalone top-level phases. Load via `skill(name: "<skill-name>")` when their task is needed.

- **Rebuild tests and indexes:** Before review verification (Phase 0 of `review-implementation`), or standalone request — see `rebuild-test-and-indexes` skill.
- **Frontend/UIUX work:** For UI/UX frontend tasks, use `frontend-design` (design spec) then `shadcn` (implementation) sequentially — see each skill for full behavioral rules.
- **End-to-end tests:** Run Playwright E2E tests standalone — auto-installs Chromium, builds SPA, starts app with temp DB — see `generate-and-run-e2e-tests` skill.
- **Save session:** Save conversation timeline to `docs/sessions/` at workflow transitions — see `save-session` skill. Session files include a YAML frontmatter header (~200 tokens) and are re-readable via Session Continuity Check.
- **Update docs:** Sync documentation after code changes — delegates to `update-architecture-md`, `update-readme-md`, `update-agent-setup-md`, `update-specifications-md`, `update-agents-md`, and `update-best-practices-md` skills. **Dual mode:** explicit (standalone) performs full codebase + session scan; implicit (auto-called by `review-implementation` Phase 3) uses git diff delta for lightweight sync.

## Session Continuity Check

**Rule:** At Phase 0 of every write-phase skill (brainstorm-and-plan, check-plan-readiness, implement-plan, rebuild-test-and-indexes, review-implementation, modularize-and-clean, improve-architecture, improve-security), check for context continuity.

**Trigger conditions:**
1. **Automatic (heuristic):** If `docs/sessions/` has `SESSION_*.md` files AND the current context has < 3 user messages, read the most recent session header (offset=1, limit=30) to restore context.
2. **On user "continue":** After compaction, always read the most recent session header.

**Policy:**
- Header only — ~200 tokens, never the full session body
- Archived sessions (`archive/sessions/`) never auto-read
- Sub-agent context: main agent extracts 1-3 relevant lines from header into Task prompt manually

---

## Documentation Structure

**Rule:** This table maps every documentation file to its purpose and location. Use it to find the right doc — never duplicate content across files. See [Quick Reference Table in DOCUMENT_GUIDELINES.md](refs/DOCUMENT_GUIDELINES.md#quick-reference-table) for document scope boundaries.

| Document | Location | Purpose |
|----------|----------|---------|
| README | `README.md` | User-facing setup, features, quick-start |
| ARCHITECTURE | `docs/ARCHITECTURE.md` | Technical module reference, data flow |
| SPECIFICATIONS | `docs/SPECIFICATIONS.md` | Product vision, user journey, privacy |
| DESIGN_SPEC | `docs/DESIGN_SPEC.md` | Visual design spec, color system, typography, motion |
| AGENTS.md | `AGENTS.md` | Agent behavioral rules, file ownership |
| AGENT_SETUP | `refs/AGENT_SETUP.md` | Tooling setup, env requirements, replicating to other projects |
| PROJECT_BEST_PRACTICES | `refs/PROJECT_BEST_PRACTICES.md` | Universal coding patterns, lessons learned |
| DOCUMENT_GUIDELINES | `refs/DOCUMENT_GUIDELINES.md` | Document scope governance |

---

## Documentation Discipline

- **Cross-reference, don't duplicate:** Use `[See ...](...)` links instead of copying content from other docs into this one.
- **New files must have description headers:** Every new file must include a file-level description comment: `# Description:` for Python, `// Description:` for TS/TSX, `/* Description: */` for CSS. This is required for auto-extraction into ARCHITECTURE.md.
- **Preserve source description comments:** File-level `# Description:` headers are the canonical source for ARCHITECTURE.md auto-extraction. Update them when behavior changes. Never delete them.
- **Executable sources of truth:** When documentation conflicts with code, configs, scripts, or CI files, trust the executable source. Prose is aspirational — code is truth.

---

## Tooling Rules

- **Code index & knowledge graph:** Auto-generated — rebuild via `rebuild-test-and-indexes` skill. ❌ Never edit manually.
- **Package manager:** `uv` for Python, `npm` for frontend. Never use pip or yarn directly.
