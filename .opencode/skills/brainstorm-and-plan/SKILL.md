---
name: brainstorm-and-plan
description: 'Brainstorming and planning stage. Analyze requirements against project docs, surface ideas and assumptions, confirm direction with user, then produce an initial plan. Use at the beginning of any tasks, or triggered when the user says "brainstorm and plan", "analyze and plan", "analyze the requirements", or similar.'
---

## What I do
- Analyze requirements via layered doc→code reading; surface assumptions, ambiguities, and missing information explicitly
- Describe requirements back to the user for confirmation; block implementation until plan is accepted
- Produce an **initial broad-strokes plan** covering files, approach, testing strategy, and success criteria

## Boundaries (read-only phase)
- **No file writes** — including plans, analysis notes, or code changes.
- **No implementation** — understand and plan only.
- **Broad strokes only** — deep edge-case analysis handled by `grill-and-refine`.
- **Interactive** — Phase 2 requires user input. Do not produce final plan without walking through and confirming with the user.
- **Verbal output only** — formal plan documents written by `check-plan-readiness`.

## Phase 0: Prerequisites

- [ ] Check for context continuity — see AGENTS.md §Session Continuity Check for trigger conditions. Load and execute the check logic from `save-session` Step 9 if needed.
- [ ] Read the upstream problem description or prior plan document
- [ ] Run baseline tests — all must pass before analysis begins
- [ ] Classify task scope (Tier 1/2/3) per AGENTS.md §Codebase Exploration — determines depth of Phase 1 exploration

## Guidelines

### Phase 1: Analyze Requirements (agent only, read-only)
**Purpose:** Deeply understand the codebase, validate docs, and stress-test the proposed approach — all before surfacing anything to the user in Phase 2.

#### Step 1: Codebase Exploration
**Purpose:** Orient on the architecture and locate relevant code before reading docs or source files.

Apply the tier-based pipeline from AGENTS.md §Codebase Exploration. For planning tasks, prioritize orientation commands before narrowing:

- `graphify_god_nodes` — identify the project's most-connected modules to orient on key seams
- `graphify_query_graph "..."` — broad concept search scoped to the task (e.g. "which modules handle SRT processing")
- `graphify_get_community <id>` — see all files in a relevant dependency community
- `graphify_shortest_path "A" "B"` — trace the relationship between two modules when understanding data flow
- `cocoindex-code_search` — search by natural language intent when exact names are unknown; set `refresh_index: False` for consecutive queries
- `ast_grep_search` — verify structural patterns and entry points (e.g. `def main()`, `load_*_log($$$)`) after scoping with graphify

#### Step 2: Consult Docs
**Purpose:** Extract product and architectural context before reading source code — docs are cheaper and often sufficient.

Read only sections relevant to the task (Grep→Read pattern — grep for heading line number, Read with offset/limit). Do not read entire docs.

- Product context, user flow, feature scope, privacy → `SPECIFICATIONS.md` (read: "Problem", "Solution", "How It Works", "Core Features", "User Flow", "Out of Scope", "Hard Constraints")
- Module structure, data flow, API design → `docs/ARCHITECTURE.md` (read: "Project Structure", "Module Descriptions" relevant entries, "Import Structure", "Modifying Instructions")
- `PROJECT_BEST_PRACTICES.md` — excluded at this stage; coding patterns are implementation concerns, not planning concerns

#### Step 3: Spot-Check Doc Accuracy
**Purpose:** Confirm docs are not stale before trusting them for planning — a wrong doc is worse than no doc.

Ceiling: check ≤4 source files. If stale, examine ≤2 additional files, then proceed regardless — do not spiral.

- Use `cocoindex-code_search "<function name>"` to verify functions mentioned in docs still exist
- Use `graphify_query_graph "<module name>"` to verify documented module relationships match the graph
- If doc matches code → extract relevant info and proceed
- If doc is stale → note the gap explicitly, check ≤2 more files, then proceed

#### Step 4: Fallback — Direct Source Reading
**Purpose:** Only when no relevant docs exist or all docs are confirmed stale.

#### Step 5: Evaluate Design Approach

**Purpose:** Stress-test the proposed approach against design principles before presenting anything to the user. Surface concerns here, not during implementation.

Evaluate against these principles:

- **Deep modules** — simple public interface, complex logic hidden inside
- **Pure functions** — same input → same output, no side effects
- **Injected dependencies** — pass in DB clients, HTTP clients, clocks, RNG
- **Single responsibility** — each module or function does one thing
- **Minimal dependencies** — every dependency is a maintenance liability
- **Elegance and efficiency** — clean design is easier to optimize
- **Immutability** — create data once, never mutate
- **Strict type safety** — explicit types over dynamic typing
- **Idempotent operations** — same result whether run once or twice
- **Self-documenting names** — name reveals intent
- **Small functional footprint** — short functions are scannable and testable
- **Control flow clarity** — straightforward flow; convoluted logic is a design problem

### Phase 2: Interactive Walkthrough (with user)
**Purpose:** Confirm understanding and approach with the user before producing any plan output. This is a critical alignment step — do not skip or rush.

Follow the User Interaction Pattern in AGENTS.md — use the `question` tool with clickable selectable options for every user decision point. Provide `options` with `label` and `description` fields. Never use raw text prompts or unformatted "y/n" questions. Present one decision-point at a time, resolve, then present the next. Never present multiple items in a single message.

1. **Clarify understanding** — restate requirements back to the user. Do not proceed until confirmed.
2. **Surface ambiguities** — state unclear point one at a time. Present multiple interpretations if they exist for that point; do not pick silently. Resolve before moving to the next ambiguity.
3. **Discuss design approach** — present findings from Phase 1 evaluation (design principles, control flow). Discuss ONE trade-off or risk at a time. Push back on questionable approaches.
4. **Confirm direction** — ensure the user agrees with the approach before producing the plan.
5. **Document sources** — cite which docs/sections were consulted.

### Phase 3: Produce Initial Plan
**Produce an initial plan verbally.** The plan must specify:
- Approach and high-level design decisions
- Files to create, modify, or remove
- Testing strategy (framework, key scenarios)
- Success criteria (verifiable)
- Consulted docs (or note: no relevant docs existed)

## Hand-off
- Analysis complete, approach evaluated (Phase 1)
- Requirements, ambiguities, and design approach discussed and confirmed with user (Phase 2)
- Plan presented verbally, no file writes (Phase 3)
- Document sources cited

---

## Outputs & Triggers

### Output
Initial (broad-strokes) plan (verbal).

### Exit Declaration
State clearly: "**Initial plan ready. Want to grill the plan or check for readiness? Say 'grill' to trigger grilling the plan, or say 'check' to trigger checking the readiness of the plan. Remember to switch to Build mode when you check plan readiness.**"

### Next Step
User invokes `grill-and-refine` or `check-plan-readiness`.