---
name: grill-and-refine
description: 'Interview relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree, then produce a fool-proof revised plan with no gaps. Use when user wants to stress-test a plan/design, after brainstorm-and-plan, or triggered when the user says "grill the plan", "stress-test the plan", "interrogate the plan", or similar.'
---

## What I do
- Interrogate the plan across all seven dimensions (assumptions, edge cases, alternatives, dependencies, risks, consistency, code discovery)
- Walk through each dimension interactively — present findings as options, gather input, resolve before moving on
- After all branches resolved, produce a fool-proof revised plan with no gaps

## Boundaries (read-only phase)
- **No file writes** — including plans, analysis notes, or code changes.
- **No implementation** — grill and refine only.
- **Deep scrutiny** — full examination of every edge case and risk. Unlike `brainstorm-and-plan`.
- **Interactive** — Phase 2 requires user input. Do not produce revised plan without walking through unresolved dimensions.
- **Verbal output only** — formal plan documents written by `check-plan-readiness`.

## Phase 0: Prerequisites

- [ ] Read the upstream plan (from brainstorm-and-plan) — all sections
- [ ] Verify the plan has all required sections (approach, files, testing, success criteria)
- [ ] Classify task scope (Tier 1/2/3) per AGENTS.md §Codebase Exploration — determines depth of Phase 1 exploration

## How to Grill

### Phase 1: Analyze (agent only, read-only)
**Purpose:** Explore the codebase to validate and challenge every aspect of the plan — all before involving the user in Phase 2. Complete all three steps before Phase 2; do not surface findings mid-analysis.

Use Grep→Read pattern (grep for heading line number, Read with offset/limit). Do not read entire docs.

- **`docs/ARCHITECTURE.md`** — "Project Structure", "Module Descriptions" (relevant), "Data Flow", "Key Design Decisions", "Import Structure", "Critical Implementation Details"
- **`SPECIFICATIONS.md`** — "Hard Constraints", "Out of Scope"

#### Step 2: Codebase Exploration
**Purpose:** Verify the plan's scope is complete — discover code the plan may have missed before probing individual dimensions.

Apply the tier-based pipeline from AGENTS.md §Codebase Exploration. Run broadly first to establish scope, then narrow per dimension:

- `graphify query_graph "..."` — broad concept search across the plan's scope; `graphify path "X" "Y"` for blast radius between modules
- `cocoindex-code_search` — find functions by natural language intent when the plan's key terms may not match code names
- `ast_grep_search` — validate structural assumptions (e.g. all `try/except` blocks, all calls to a deprecated function)
- `grep / read` — fallback for exact-text details uncovered by tools above

#### Step 3: Probe Each Dimension
**Purpose:** For each of the 7 dimensions, gather concrete findings to bring into the user walkthrough.

**Gap grilling method** — when comparing two sources (template vs implementation, spec vs code), test each gap against four questions before acting on it:

1. Is it truly additive?
2. Does it affect output or methodology?
3. Which document owns it?
4. What's the cost/benefit?

Only act on gaps that survive all four questions.

| Dimension | What to probe |
|-----------|--------------|
| **Assumptions** | Validated by code? |
| **Edge cases** | Empty, null, boundary, or unexpected input? |
| **Alternatives** | Simpler or safer approach? New dependency worth the cost? |
| **Dependencies** | Breaks anything? Order-dependent? Injected or hardcoded? |
| **Risks** | Blast radius? Error strategy defined? Performance implications? |
| **Consistency** | Conflicts with existing patterns? Straightforward control flow? |
| **Code Discovery** | Plan missed related concepts? `graphify path "X" "Y"` for blast radius between planned and missed modules. |

**Testability probe — run during Dependencies:**

- **AP1: Non-determinism** — clocks, RNG, or network calls make tests non-repeatable?
- **AP2: Untestable I/O fusion** — a function that reads external state AND contains decision logic based on that state?
- **AP3: Tight coupling** — mocking 3+ collaborators to test one unit?
- **AP4: Shared mutable state** — global state modified by multiple tests causes order-dependent flaky tests?
- **AP5: Missing seams** — no place to substitute behavior without patching internals?
- **AP6: Type ambiguity** — `Any`/`any` types, untyped dicts, or missing schemas in function signatures?
- **AP7: Non-idempotent writes** — running the same write operation twice produces different state?
- **AP8: Mutable outputs** — function returns a list/dict the caller can accidentally mutate?

**Test fragility probe — run during Risks:**

- **Brittle assertions** — testing type rather than value?
- **Test doubles confusion** — mocking when a stub or fake would do?

### Phase 2: Interactive Walkthrough (with user)
**Purpose:** To identify and resolve any gaps in the plan through a structured conversation with the user. This is a critical alignment step — do not skip or rush. However, not all dimensions require user discussion — non-critical dimensions are decided by the agent using best practices and project logic.

Follow the User Interaction Pattern in AGENTS.md — use the `question` tool with clickable selectable options for every user decision point. Provide `options` with `label` and `description` fields. Never use raw text prompts or unformatted "y/n" questions. Present one decision-point at a time, resolve, then present the next.

1. **Before starting:** classify each dimension as CRITICAL (needs user discussion) or NON-CRITICAL (agent decides based on best practices and project logic) — do not describe contents or items within dimensions. Present the classification list to the user for confirmation before proceeding.

   **Critical dimensions** (always require user discussion):
   - **Assumptions** — validated against user's intent? Any unstated assumptions
   - **Risks & Race Conditions** — blast radius, error strategy, concurrency concerns
   - **Edge Cases** — empty, null, boundary, or unexpected input

   **Non-critical dimensions** (agent decides automatically):
   - **Alternatives** — simpler or safer approach? Agent evaluates using best practices (simplicity first, surgical changes), picks the least complex option
   - **Dependencies** — breaks anything? Order-dependent? Agent verifies using graphify/cocoindex/path queries
   - **Consistency** — conflicts with existing patterns? Agent checks codebase conventions and aligns with established patterns
   - **Code Discovery** — plan missed related concepts? Agent probes via graphify path queries after walkthrough

   Edge case: if the user explicitly asks about a non-critical dimension, reclassify it as critical and walk through it.

2. Walk through each CRITICAL dimension in order. For each:
   - State ONE finding and recommendation at a time
   - Use the `question` tool with concrete options (e.g., "server-side, client-side, or something else")
   - Rely on the auto-added "Type your own answer" for free-form input beyond offered options
   - Resolve before moving to the next item within this dimension — do not revisit

3. After CRITICAL dimensions are resolved, decide NON-CRITICAL dimensions:
   - Agent uses best practices (simplicity first, surgical changes), project logic, and codebase findings from Phase 1 to auto-decide each non-critical dimension
   - Format each decision as a ready-to-copy block (same template as Phase 3)

4. Show ALL dimension decisions (critical + non-critical) to the user for final confirmation in one batch. Use the `question` tool with a single multiple-choice: "All decisions look correct" / "Need to discuss some dimensions" — do not walk through individual dimensions again.

5. After all dimensions confirmed, produce revised plan (Phase 3).

### Phase 3: Produce the Revised Plan
**Purpose:** Compile a revised plan that incorporates all confirmed decisions from the walkthrough, formatted as copy-ready blocks for the next stage.

**Copy-ready outputs** — format resolved dimensions as blocks the next stage can paste directly into the plan document. Use this template for each:

```
### Dimension: [name]
- Decision: [what was decided]
- Rationale: [why this choice]
- Impact: [how it affects the plan]
```

After all dimensions, produce the full revised plan summary. Must be:

- **Complete** — approach, design decisions, files, resolved dimensions, testing strategy, success criteria
- **Gap-free** — no unresolved questions or skipped branches
- **Logically sound** — straightforward control flow
- **Error strategy defined** — what can fail and how
- **Testable** — specific test cases; core logic testable without external systems

## Hand-off
- All seven dimensions probed and resolved (Phase 1)
- CRITICAL dimensions walked through interactively, NON-CRITICAL dimensions auto-decided by agent (Phase 2)
- Revised plan compiled with copy-ready blocks, quality criteria met (Phase 3)
- No file writes occurred

---

## Outputs & Triggers

### Output
Revised plan (verbal) formatted as a ready-to-copy code block.

### Exit Declaration
State clearly: "**Grill complete. Check for plan readiness? Say 'check' to trigger checking the readiness of the plan. Remember to switch to Build mode**"

### Next Step
User invokes `check-plan-readiness`.