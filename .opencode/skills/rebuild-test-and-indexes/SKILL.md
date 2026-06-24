---
name: rebuild-test-and-indexes
description: 'Rebuild CocoIndex code index and Graphify knowledge graph. On explicit invocation does a full direct codebase scan to find and fix all stale/outdated/broken tests before rebuilding; when invoked as Phase 1b of review-implementation, uses git diff for delta updates. Use after any code change, or when the user says "rebuild test and indexes", "update tests", "reindex", or similar.'
---

## Purpose

Two invocation modes with fundamentally different detection strategies:

| Aspect | Explicit (standalone) | Implicit (Phase 1b of review-implementation) |
|--------|----------------------|----------------------------------------------|
| Detection | Full direct codebase scan — no git diff | git diff delta — only changed files |
| Scope | ALL stale/outdated/broken test refs | Only structural refs related to changed files |
| Pipeline | Audit → Test → Triage → Rebuild | Sync → Test → Triage → Rebuild |
| Index rebuild | Unconditional (codebase was verified clean) | Conditional (only if relevant source files changed) |
| Blocking | Yes — test failures halt rebuild | Non-blocking — failures warn but don't halt caller |

## Boundaries

- **Index/graph artifacts only** — never modifies source code. Rebuilds auto-generated files in `.cocoindex_code/` and `graphify-out/`.
- **Test files only** — only modifies test files during stale-fix triage. Never modifies source code.
- **Non-blocking in implicit mode** — failures produce warnings but do not halt the caller.
- **Blocking in explicit mode** — test failures halt rebuild and report the issue. Indexes are rebuilt only if all tests pass.

## Phase 0: Prerequisites

- [ ] Determine invocation mode — explicit (standalone "rebuild test and indexes") or implicit (Phase 1b of review-implementation)
- [ ] Confirm `git` is available
- [ ] Confirm `ccc` is installed (warn if not found — skip CocoIndex rebuild)
- [ ] Confirm `graphify` is installed (warn if not found — skip Graphify rebuild)
- [ ] If frontend tests are needed: confirm `frontend/node_modules/` exists (warn if not found — skip frontend tests)

---

## Explicit Path (standalone "rebuild test and indexes")

**Detection method:** Full direct codebase scan — no git diff. The entire filesystem is the source of truth. We scan test files, check their references against what actually exists on disk, and fix mismatches. This catches ALL stale references regardless of when they were introduced.

### Phase 1: Full Codebase Audit

**Purpose:** Scan the entire project to find every stale, outdated, or broken reference in test files. No git diff — we compare test content directly against the current filesystem.

**Detection:** Walk each test file's hardcoded references and check them against `os.path.exists()` against the live filesystem. Fix every mismatch found. Print delta.

#### Step 1: Audit Hardcoded File Paths

Scan test files for lists matching `file_structure|file_exist|SOURCE_PATHS|DIR_PATTERNS|COMMAND_TARGET_GROUPS|DOC_PATHS|AUTO_GENERATED_PATHS`. For each referenced path:

- Does it exist on disk?
- If not → update the reference or remove it
- If path type changed (file→dir or dir→file) → fix the type

Key target: `tests/test_agent_guidelines.py` — has SOURCE_PATHS, DIR_PATTERNS, COMMAND_TARGET_GROUPS, DOC_PATHS, UTILITY_SKILLS, AUTO_GENERATED_PATHS

#### Step 2: Audit Skill Names

Scan test files for hardcoded skill name lists (e.g., `UTILITY_SKILLS`, routing test cases). For each skill name:

- Does the directory `.opencode/skills/<name>/` exist?
- If not → update the reference to the correct name or remove it

#### Step 3: Audit Imports and References

Check that all imports in test files resolve to existing modules. Check for stale function names, class names, and variable references that no longer exist in source code.

#### Step 4: Audit Index Files

Check if `.cocoindex_code/` and `graphify-out/` exist. If missing, they will be rebuilt in Phase 3. Check if they're stale by comparing source file modification times vs index build times (optional — rebuilding is cheap).

#### Step 5: Apply Fixes

For every mismatch found in Steps 1-4:

- Fix stale file paths → point to actual location or remove
- Fix stale skill names → update to actual name
- Fix broken imports → update to actual module paths
- Print each fix as: `[FIXED]: <file>:<reference> → <new-value>`

#### Phase 1 Completion

- All mismatches fixed → proceed to Phase 2
- Scan complete, nothing to fix → proceed to Phase 2

### Phase 2: Run Tests & Triage

**Purpose:** Run all test suites against the now-clean codebase. If tests fail, triage each failure (max 3 cycles). Distinguish stale assertions (fixable) from real regressions (blocking).

#### Step 1: Run All Test Suites

Run in order. If any fails, proceed to Step 2 (triage). If all pass, skip to Phase 3.

1. Backend tests: `python -m pytest` (discovers all Python tests)
2. Frontend tests: `cd frontend && npm test` (skip if node_modules/ not found)
3. Additional project-specific test suites (lint, typecheck, agent guidelines, etc.)

#### Step 2: Triage & Iterate (max 3 cycles)

Apply the Failure Triage table:

| Classification | Action |
|---------------|--------|
| `ImportError`, `ModuleNotFoundError` | Fix the import path |
| Stale reference (file path, skill name, export name) | Update the reference |
| Stale assertion (expected value changed) | Update the assertion to match current behavior |
| Behavioral regression (real source bug) | **STOP** — report to user. Do not rebuild. |
| Pre-existing failure (failed in baseline) | **STOP** — report to user. Do not proceed. |
| Flaky / intermittent | Re-run once; if fails again, flag as flaky and continue |

**Max iteration guard:** After 3 full cycles (fix → run → triage) without all tests passing, **STOP**. Report: "Tests still failing after 3 fix cycles. Aborting rebuild. Manual intervention required."

#### Phase 2 Completion

- All tests pass → proceed to Phase 3
- Real regression detected → STOP, report to user, do not rebuild
- Max cycles exhausted → STOP, report to user, do not rebuild

### Phase 3: Rebuild Indexes

**Purpose:** Rebuild CocoIndex and Graphify indexes unconditionally. Since Phases 1-2 confirmed the codebase is clean, we rebuild with confidence.

#### Step 1: Rebuild CocoIndex

```
ccc index
```

If settings.yml missing → first run `ccc init`, then `ccc index`.

- Success → continue
- Command not found → WARNING: "ccc not found — CocoIndex rebuild skipped"
- Timeout/failure → WARNING: "CocoIndex rebuild failed/timed out — search may return stale data"

#### Step 2: Clean and Rebuild Graphify

Run a clean rebuild from scratch (removes stale cache and metadata):

```powershell
Remove-Item -Recurse -Force graphify-out/
graphify .
```
or if no LLM available:

```powershell
Remove-Item -Recurse -Force graphify-out/
$env:PYTHONIOENCODING='utf-8'; graphify update .
```

(POSIX equivalent: `rm -rf graphify-out/ && graphify update .`)

- Success → continue to dedup step
- Command not found → WARNING: "graphify not found — Graphify rebuild skipped"
- Timeout/failure → WARNING: "Graphify rebuild failed/timed out — graph queries may return stale data"

#### Step 2.5: Deduplicate Graph Nodes

Run only if Step 2 succeeded:

```
uv run python agent_utility/dedup_graph_nodes.py
```

- Success → continue
- Script not found → WARNING: "dedup_graph_nodes.py not found — dedup skipped"
- Failure → WARNING: "Graph deduplication failed — graph may contain ghost nodes"

#### Step 3: Report

| Scenario | Output |
|----------|--------|
| Both rebuilt successfully, dedup ran | "Index and graph rebuilt successfully. Data is current." |
| Partial failure | "WARNING: [tool] failed. [Implications]." |

---

## Implicit Path (Phase 1b of review-implementation)

**Detection method:** git diff delta. Only files that changed in the current branch are relevant. We sync structural refs for changed files, run tests to confirm, triage failures (max 3 cycles), then rebuild indexes conditionally.

**Trust boundary:** Caller (`review-implementation` Phase 0) ran baseline tests before invoking this skill. Implicit mode further verifies by running tests after structural sync — this catches sync-induced issues without duplicating the baseline.

### Step 1: Detect Changed Files

On POSIX:

```bash
git diff --name-only "$(git merge-base HEAD main)" HEAD
```

On PowerShell:

```powershell
git diff --name-only $(git merge-base HEAD main) HEAD
```

If this fails (e.g., no commits yet), fall back to `git status --porcelain`.

### Step 2: Delta Structural Update

**Purpose:** Update only the structural test references related to changed files. Not a full scan — we know exactly what changed from the diff.

For each changed file:
- If the changed file was added/removed/renamed → update file-existence lists in test files that reference it
- If the changed file is a skill → update skill name lists and routing test cases
- If the changed file is a module → update import references in test files

Skip test files unrelated to the diff. Do not touch business-logic tests.

### Step 3: Run All Test Suites (Parallel)

Run test suites concurrently:

| Parallel call | Command |
|---------------|---------|
| 1 | `python -m pytest` (discovers all Python tests) |
| 2 | `cd frontend && npm test` (skip if node_modules/ not found) |

Wait for both to complete. Then run additional project-specific test suites (lint, typecheck, agent guidelines, etc.) sequentially.

If all pass → proceed to Step 5 (Conditional Rebuild).
If any fail → proceed to Step 4 (Triage).

### Step 4: Triage Failures (max 3 cycles)

Apply the same Failure Triage table as Explicit Phase 2 Step 2. The key difference from explicit mode:

| Classification | Action |
|---------------|--------|
| Stale reference from renamed/removed file | Fix the reference |
| `ImportError` from changed module path | Fix the import |
| Stale assertion (expected value changed) | Update the assertion |
| Real regression from the diff | **STOP** — report to user. Non-blocking: warn and continue |
| Pre-existing failure (unrelated to diff) | Warn and continue — it's a baseline issue |
| Flaky / intermittent | Re-run once; if still fails, flag and continue |

**Max iteration guard:** After 3 full cycles (fix → run → triage), **STOP**. Report: "Tests still failing after 3 fix cycles. Manual intervention required." Continue to Step 5 anyway (non-blocking).

**Implicit mode is non-blocking** — failures produce warnings but do not halt the caller. The caller (review-implementation) will independently verify test health in later phases.

### Step 5: Conditional Rebuild (Parallel)

Filter changed files against indexed file types:

```
.py, .ts, .tsx, .js, .jsx, .css, .json, .html, .toml
```

**If any changed file matches** → rebuild CocoIndex and Graphify concurrently:

| Parallel call | Command |
|---------------|---------|
| 1 | `ccc index` (same as Explicit Phase 3 Step 1) |
| 2 | `graphify update .` (same as Explicit Phase 3 Step 2; PowerShell: `$env:PYTHONIOENCODING='utf-8'; graphify update .`) |

Wait for both. Then run dedup sequentially (depends on graphify output):
- `uv run python agent_utility/dedup_graph_nodes.py`

**If none match** (only .md, lock files, .gitignore, etc.) → skip. Report: "No source files changed — index/graph is current. Skipping rebuild."

### Step 6: Report

| Scenario | Output |
|----------|--------|
| All tests pass, indexes rebuilt | "Implicit rebuild complete. Structural sync applied, all tests passing, indexes rebuilt." |
| Tests pass, no index rebuild needed | "Implicit rebuild complete. No source file changes — indexes are current." |
| Tests had issues (non-blocking) | "Implicit rebuild complete. [N] test issue(s) flagged (non-blocking). Indexes rebuilt/skipped." |
| Max triage cycles reached | "Implicit rebuild complete but [N] test(s) still failing after 3 cycles. Manual review needed." |

---

## Outputs & Triggers

### Output
Verbal report: audit/rebuild result + any warnings.

### Exit Declaration
- **Explicit path**: "**Explicit rebuild complete. Full codebase audit passed, all tests passing, indexes rebuilt.**" (or detail failures)
- **Implicit path**: "**Implicit rebuild complete. [delta summary].**"

### Next Step
- **Explicit path**: Done.
- **Implicit path**: Return to `review-implementation` Phase 2 (Inspect Changes) and continue the review workflow.
