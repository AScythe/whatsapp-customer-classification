---
name: update-docs
description: 'Analyze session changes and sync all project documentation by delegating to each doc-specific update skill. Trigger when a documentation sync phase completes, or when the user says "sync docs", "update docs", "docs are outdated", or similar.'
---

## What I do
- Review session changes to determine which docs need updating
- Match change types to docs via the Doc Sync Triggers table
- Update each doc in dependency order
- Verify cross-reference integrity across all project docs
- Route to push-to-git
- **Auto-execute update-docs (implicit) on success** — when invoked from review-implementation Phase 1a

## Purpose

Two invocation modes with fundamentally different detection strategies:

| Aspect | Explicit (standalone) | Implicit (Phase 1a of review-implementation) |
|--------|----------------------|----------------------------------------------|
| Detection | Full codebase + session history | git diff delta |
| Scope | ALL docs — full analysis | Only docs matching changed files |
| Investigation | Full: graphify + codebase walk + session | Light: graphify for context, skip full codebase walk |
| Proposal | Full per-doc proposals | Delta-only proposals via parallel sub-agents |
| Approval | Serial per-doc review (full diff display) | No approval — auto-apply from proposals |
| Apply | After approval per doc | Sequential apply by main agent (no user gate) |
| Verify | Cross-reference integrity | Moved to review-implementation Phase 6 (read-only) |
| Blocking | Yes — user must complete review | Non-blocking — failures warn but don't halt caller |

## Boundaries
- **Read-only analysis.** Review session changes and trigger syncs — do not create content for docs that had no changes.
- **One pass at end.** Sync all docs in one batch at end of session, not after every commit or phase.
- **Cross-reference integrity.** All `See ...` links must resolve after syncs complete.
- **Only doc files** — never modifies source code. Only updates files in `docs/` and `refs/`.
- **Non-blocking in implicit mode** — failures produce warnings but do not halt the caller.
- **Blocking in explicit mode** — user must complete the review before proceeding.

## Content Rules

### Quality Gates
- **Litmus test:** Would an agent miss this without running the sync? If not, leave it out.
- **Cross-reference integrity:** All links between documents must resolve to existing anchors.
- **Batch discipline:** All syncs in one pass — not per commit or phase.

### Scope
- Change inventory — which files were created, modified, or deleted
- Doc Sync Triggers consultation — match changes to the correct doc
- Cross-reference verification — ensure all `See ...` links resolve
- Hand-off instruction to `push-to-git`

## Phase 0: Prerequisites

- [ ] Determine invocation mode — explicit (standalone "sync docs") or implicit (Phase 1a of review-implementation)
- [ ] If explicit: review session changes — git diff, [FLAG] annotations, conversation history
- [ ] Match changes against Doc Sync Triggers table
- [ ] Read AGENTS.md doc sync triggers table

---

## Explicit Path (standalone "sync docs")

**Detection method:** Full codebase + session history — the entire project is the source of truth. Review all changes (git diff, flags, conversation) to determine which docs need updating. Used when invoked directly by the user.

### Phase 1: Inventory

1. **Review session changes** — session conversation, git diff, and `[FLAG]` annotations from prior phases

2. **Match against Doc Sync Triggers** — consult the table below:

   | Change type | Target document |
   |-------------|-----------------|
   | New/deleted/renamed file, module restructure, new endpoint, changed function signature | `docs/ARCHITECTURE.md` |
   | New feature, changed user journey, updated privacy, changed Out of Scope | `docs/SPECIFICATIONS.md` |
   | Design spec created/updated, color system, typography/motion changes, UI theme changes, frontend-design skill output | `docs/DESIGN_SPEC.md` |
    | Changed setup steps, new CLI command, new env var, new user-visible feature | `README.md` (project root) |
    | Changed behavioral rules, new file ownership entry, updated commands | `AGENTS.md` |
    | Changed server lifecycle/hosting, new subprocess management patterns | `AGENTS.md` |
   | Changed tooling setup, new MCP server, changed env requirements | `refs/AGENT_SETUP.md` |
   | Recurring pattern, new debugging lesson, new skill methodology insight | `refs/PROJECT_BEST_PRACTICES.md` |
   | New document added, document scope/boundary change, doc structure change | `refs/DOCUMENT_GUIDELINES.md` |

3. **List which docs to update** — for each change type that occurred, note the corresponding doc. If none match, skip to Phase 5.

### Phase 2: Propose (Parallel Analysis)

For each doc in the update list from Phase 1, launch a Task sub-agent to analyze and propose diffs. Each sub-agent is **read-only** — it investigates the codebase and returns a list of `oldString→newString` proposals, but does NOT apply any edits.

**Important:** Sub-agents must be instructed explicitly to return proposed diffs only, never to call `edit`, `write`, or `bash`. The `question` and `read` tools are permitted for analysis.

Launch all in parallel (no dependency ordering needed — analysis is independent):

1. `docs/ARCHITECTURE.md` → instruct sub-agent to load `skill(name: "update-architecture-md")` and return proposals
2. `docs/SPECIFICATIONS.md` → instruct sub-agent to load `skill(name: "update-specifications-md")` and return proposals
3. `AGENTS.md` → instruct sub-agent to load `skill(name: "update-agents-md")` and return proposals
4. `README.md` (project root) → instruct sub-agent to load `skill(name: "update-readme-md")` and return proposals
5. `refs/PROJECT_BEST_PRACTICES.md` → instruct sub-agent to load `skill(name: "update-best-practices-md")` and return proposals
6. `refs/AGENT_SETUP.md` → instruct sub-agent to load `skill(name: "update-agent-setup-md")` and return proposals
7. `refs/DOCUMENT_GUIDELINES.md` — inline analysis only (no dedicated skill)

Each sub-agent returns: a list of `{filePath, oldString, newString, reason}` objects. No edits are applied.

### Phase 3: Review (Serial Approval)

Collect all proposals from Phase 2. Present each document's proposed diffs to the user **one doc at a time** using the `question` tool.

For each doc that has proposals:
1. Show the proposed oldString→newString diffs (use `read` to display context)
2. Ask user: approve all, reject all, or review individual edits
3. Collect the user's decision before moving to the next doc

Only proceed to Phase 4 after all documents have been reviewed.

### Phase 4: Apply

Apply approved proposals from Phase 3 using the `edit` tool. Apply one doc at a time — run full test suite before moving to the next doc.

If a user rejected or modified a proposal, skip or adjust accordingly.

### Phase 5: Verify

- [ ] All `See <DOC>.md` links between documents resolve to existing headings
- [ ] No dead anchor references — every `#section-name` target exists in the target doc
- [ ] No orphaned sections — every section in each doc is reachable from another doc or from the doc's own TOC
- [ ] No stale redirects — `→ Redirect to <filename>` markers are removed if the target document no longer exists

---

## Implicit Path (Phase 1a of review-implementation)

**Detection method:** git diff delta — only files that changed. Determine which docs need updating by matching change types against Doc Sync Triggers. No full codebase scan. Used when auto-invoked by `review-implementation` Phase 1a.

**Trust boundary:** Caller ran baseline tests before invoking. Doc deltas are derived from the same git diff the implementer already tested — auto-apply is safe.

### Step 1: Detect Changed Files

```
git diff --name-only $(git merge-base HEAD main) HEAD
```

PowerShell fallback:
```powershell
git diff --name-only $(git merge-base HEAD main) HEAD
```

### Step 2: Match Against Doc Sync Triggers

Match changed files against the Doc Sync Triggers table (same as explicit path).

If no triggers match → Step 4 (Report: "No doc updates needed").

### Step 3: Propose and Apply (Parallel Sub-Agents, Sequential Apply)

For each triggered doc, launch a Task sub-agent (read-only, returns `{filePath, oldString, newString, reason}` proposals). Each sub-agent loads the doc-specific skill with `mode="implicit"` and diff context. Run all sub-agents in parallel.

Launch all sub-agents in parallel:

1. `docs/ARCHITECTURE.md` → instruct sub-agent to load `skill(name: "update-architecture-md")` with `mode="implicit"` and diff context
2. `docs/SPECIFICATIONS.md` → instruct sub-agent to load `skill(name: "update-specifications-md")` with `mode="implicit"` and diff context
3. `AGENTS.md` → instruct sub-agent to load `skill(name: "update-agents-md")` with `mode="implicit"` and diff context
4. `README.md` (project root) → instruct sub-agent to load `skill(name: "update-readme-md")` with `mode="implicit"` and diff context
5. `refs/PROJECT_BEST_PRACTICES.md` → instruct sub-agent to load `skill(name: "update-best-practices-md")` with `mode="implicit"` and diff context
6. `refs/AGENT_SETUP.md` → instruct sub-agent to load `skill(name: "update-agent-setup-md")` with `mode="implicit"` and diff context
7. `refs/DOCUMENT_GUIDELINES.md` — inline analysis with diff context (no dedicated skill)

Collect all proposals. Main agent applies edits sequentially via `edit` tool. **No Quick Approval gate.**

### Step 4: Report

| Scenario | Output |
|----------|--------|
| N docs updated | "Implicit doc sync complete. [N] doc(s) updated: [list]." |
| No triggers matched | "Implicit doc sync complete. No doc updates needed." |
| Sub-agent or edit failure | "WARNING: [detail]. Non-blocking." |

## Hand-off
- Explicit mode: Phase 1 (Inventory) → Phase 2 (Propose via sub-agents) → Phase 3 (Review & Approve) → Phase 4 (Apply) → Phase 5 (Verify cross-references)
- Implicit mode: Step 1 (Detect) → Step 2 (Match) → Step 3 (Propose & Apply — auto, no user gate) → Step 4 (Report)
- Cross-reference verification moved to review-implementation Phase 6 (read-only)

### Abort Paths
If interrupted mid-phase: record current state in a TODO or pending list, offer to resume at the same point when re-invoked. Do NOT commit partial work.

---

## Outputs & Triggers

### Output
All applicable docs updated. Cross-references verified in explicit mode only (implicit mode cross-ref check handled by review-implementation Phase 6).

### Exit Declaration
- **Explicit mode:** State clearly: "**Documentation sync complete. All applicable syncs run, cross-references verified. Proceed to push-to-git? Say 'push' to trigger pushing the changes to git.**"
- **Implicit mode:** State clearly: "**Implicit doc sync complete. [N] doc(s) updated.**" (or "No doc updates needed.")

### Next Step
- **Explicit mode:** User invokes `push-to-git` (Build mode — same mode, no switch needed).
- **Implicit mode:** Control returns to `review-implementation` — proceeds to Phase 1b (rebuild-test-and-indexes).
