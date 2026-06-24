---
name: modularize-and-clean
description: 'Scan code-level quality — DRY violations, mixed concerns, naming, large files, dead code, type safety, idempotency, immutability, deep modules, and referential transparency — then apply cleanup in batches with [CLEANUP] flags. Use after review-implementation passes, or triggered when user says "modularize", "clean up", "refactor", or similar.'
---

## What I do
- Scan codebase for code-level issues across 11 scopes (imports, DRY, mixed concerns, naming, large files, dead code, deep modules, type safety, idempotency, immutability, referential transparency)
- Compile candidates with file:line references
- Present for user approval — never apply without sign-off
- Apply changes batch-by-batch with [CLEANUP] flags
- Write coverage tests for new modules, adapt test references
- Save approved findings to a plan document at `docs/PLAN_*.md`
- Route back to review-implementation

## Boundaries
- **Phase 1 is strictly read-only.**
- **Structural changes only.** No behavior changes, bug fixes, or new features.
- **Dead code requires user approval.** Evidence (zero imports/references) required.
- **Coverage tests required.** When extraction creates a new module.
- **Self-contained workflow.** Batch discipline, flag format, and test adaptation rules are documented below in the per-batch workflow.

## Phase 0: Prerequisites

- [ ] Check for context continuity — see AGENTS.md §Session Continuity Check for trigger conditions. Load and execute the check logic from `save-session` Step 9 if needed.
- [ ] Read the review pass findings (from review-implementation)
- [ ] Run baseline tests — all must pass


## Modularization and Cleanup Workflow

### Phase 1: Analyze (read-only)
**Purpose:** Understand the codebase's structure, scan all 11 quality scopes, and compile a candidate list — all before presenting anything to the user.

#### Step 1: Read Docs and Test Suite
**Purpose:** Establish the documented structure and understand existing test imports — imports will need adaptation during Phase 2.

- **`docs/ARCHITECTURE.md`**: "Project Structure", "Import Structure", relevant module descriptions
- Read the test suite — note import paths that will be adapted during cleanup

#### Step 2: Codebase Exploration
**Purpose:** Orient on the codebase's community structure and coupling before scanning individual scopes.

Apply the tier-based pipeline from AGENTS.md §Codebase Exploration:
- `graphify` community detection — identify strongly-connected components; same communities stay together, different communities are extraction candidates
- `graphify path "A" "B"` — assess coupling between two modules before splitting
- `ast_grep_search` — DRY analysis across files; `ast_grep_replace` with `dryRun: true` for rename preview
- `cocoindex-code_search` — find related functions with different naming conventions

#### Step 3: Scan 11 Scopes
**Purpose:** Systematically examine source files for structural quality issues. Prefer extractions that improve testability — separate pure logic from I/O. Follow the leaf module pattern (leafs export only, never import internal). Separate by layer (config → state → logic → persistence). Split triggers: >200 lines, mixed concerns, or circular imports.

- **Import structure** — circular/sibling-to-sibling imports
- **Shared code (DRY)** — duplicated logic across files
- **Mixed concerns** — config+logic, UI+API, persistence+business in the same file
- **Naming clarity** — unclear function/variable names
- **Large files (>~200 lines)** — clean seams for splitting
- **Dead code** — unused exports, orphaned files, unreachable code
- **Deep modules** — bloated public interfaces exposing implementation details
- **Type safety** — raw dicts, `Any`/`any` types, untyped signatures
- **Idempotency** — operations that change state differently on re-run
- **Immutability** — mutable defaults, shared mutable state, internal collections returned directly
- **Referential transparency** — I/O mixed with business logic, hidden state reads

#### Step 4: Compile Candidate List
**Purpose:** Organize findings for user review before any changes are applied.

Present findings categorized by scope with file:line references and proposed changes.

For dead code items, use this format:
```
[DEAD] <file:line> — <symbol> — <evidence> → Recommend: <Remove / Keep / Archive>
```

Recommendation guide:

| Category | Default Recommendation |
|----------|----------------------|
| Unused export (zero imports) | Remove |
| Entire unused file (zero imports) | Remove or Archive |
| Type-only export | Remove |
| Public API export | Keep — needs user confirmation |
| Orphaned test file | Remove |

### Gate: User Approval

Present the candidate list and use the `question` tool to ask for approval: **"Shall I proceed with these changes?"** Provide clickable `options` with `label` ("Proceed", "Skip item", "Cancel") and `description` fields. Rely on the auto-added "Type your own answer" for custom input.

Wait for explicit approval before Phase 2.

### Phase 1.5: Create Plan Document

Write approved findings to `docs/PLAN_YYYY_MM_DD_XXX.md` (sequential numbering, check-plan-readiness template). For combined execution, write a single unified plan covering both skill findings.

### Phase 2: Apply (batch-by-batch)
**Purpose:** Apply the approved candidates in dependency-ordered batches, verifying after each one before proceeding.

> **Before applying:** run full test suite + lint. Flag pre-existing failures.

#### Batching Rules

Each batch = one logical structural change. Do NOT mix unrelated changes.

Valid batch examples:
- ✅ Fix circular import chain + adapt tests
- ✅ Extract shared utility + coverage tests + update callers
- ✅ Separate mixed concerns into dedicated modules
- ✅ Rename file + update all imports

**Conflict resolution:** When multiple candidates touch the same file, sort by dependency order. If ordering isn't possible, present the conflict with line ranges and a recommendation. Do NOT silently apply conflicting batches in sequence.

#### Per-Batch Workflow

For each approved candidate, in order:

1. **Apply the structural change**
   - Move functions, split files, rename symbols, fix imports
   - Do NOT change any behavior or logic
   - When moving/renaming files: preserve and update the Description: header. Never delete it.
   - Remove imports/variables/functions your changes made unused
   - Apply changes one logical unit at a time within each file

2. **Flag every changed line with `[CLEANUP]`**

3. **Write coverage tests for new modules** (only if extraction created a new file)
   - Verify extracted logic works independently
   - Match existing test conventions (NOT TDD — covers already-working behavior)
   - Add docstring to extracted shared utilities
   - Tests are permanent regression tests — never delete after batch passes

4. **Adapt existing test references**
   - Update import paths, function names, and references to match new source structure
   - Do NOT change test logic, assertions, or test names
   - Update every occurrence in the same batch — imports, calls, mocks

5. **Run full test suite** — all must pass. On failure: import path issue → fix and re-run. Any other cause → revert batch, skip, move to next.

6. **Proceed to next batch**

#### Change-Log (verbal)

After all batches, produce a verbal markdown change-log grouped by scope with `[CLEANUP]` `[file:line]` entries — coverage tests added and unsafe candidates skipped.

### Combined execution with improve-architecture and improve-security (default flow)

The default flow after a successful first-pass review runs `modularize-and-clean`, `improve-architecture`, and `improve-security` together. This is the primary workflow — not an optional sub-path. When the user triggers any combination of these skills:

**Step 1: Parallel Phase 1**
All participating skills run their Phase 1 independently — each scanning their defined scope without waiting for the others.

**Step 2: Merge into Plan Doc**
Combine all Phase 1 outputs into a unified plan document saved to `docs/`:

File: `docs/PLAN_YYYY_MM_DD_XXX.md` (sequential numbering, check-plan-readiness template)

Sections:
- **Modularize-and-clean findings** — candidates grouped by scope with file:line references
- **Improve-architecture findings** — P0/P1/P2 prioritized list with file:line references
- **Improve-security findings** — P0/P1/P2 prioritized list with file:line references
- **Conflicts** — items where multiple skills affect the same file; resolve before applying
- **Proposed batch order** — dependency-sorted sequence covering all finding sets

**Step 3: User Approval Gate**
Present the plan doc and use the `question` tool to get explicit approval. Wait for sign-off before applying any changes.

**Step 4: Apply Batches**
Apply in dependency order. Code-quality changes carry `[CLEANUP]` flags, structural changes carry `[ARCH]` flags, security changes carry `[SECURITY]` flags — never mix flags in the same batch.

**Step 5: Route to review-implementation**
After all batches pass, route to `review-implementation`.

## Hand-off
- Phase 1: All 11 scopes scanned, candidate list compiled
- Gate: User approved
- Phase 1.5: Plan document created at `docs/PLAN_...`
- Phase 2: Approved batches applied or explicitly skipped
- All changed lines carry [CLEANUP]
- Full test suite and lint pass
- Verbal change-log produced

### Abort Paths
If interrupted mid-phase: record current state in a TODO or pending list, offer to resume at the same point when re-invoked. Do NOT commit partial work.

---

## Outputs & Triggers

### Output
Plan document at `docs/PLAN_*.md` with candidates grouped by scope. Structural changes with [CLEANUP] flags. Updated test imports. Coverage tests for new modules.

### Exit Declaration
State clearly: "**Cleanup complete. Verbal change-log above. Review the changes? Say 'review' to trigger review of the changes.**"

### Next Step
User invokes `review-implementation` (combined clean-up/architecture/security pass) — switch to Plan mode before proceeding.