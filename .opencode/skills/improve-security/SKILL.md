---
name: improve-security
description: 'Scan security architecture — secrets, input validation, CORS, rate limiting, WebSocket security, insecure deserialization, injection risks, XSS, and secure config — then apply fixes in TDD-backed batches with [SECURITY] flags. Use after review-implementation (first pass), or triggered when the user says "security review", "audit security", "improve security posture", or similar.'
---

## What I do
- Scan security architecture across 9 dimensions (secrets, deserialization, injection, XSS, input validation, CORS, secure config, WS security, rate limiting)
- Produce a prioritized plan document at `docs/PLAN_*.md` (P0–P2) with file:line references
- After user approval, apply security fixes in TDD-backed batches with [SECURITY] flags
- Route back to review-implementation

## Boundaries
- **Phase 1 is strictly read-only.** No file writes, no code changes, no notes files.
- **Phase 2 is security-only changes.** No general cleanup, no feature additions, no behavior changes unrelated to the finding.
- **No dependency vulnerability scanning.** CVEs and supply-chain issues are out of scope.
- **Self-contained TDD.** TDD principles, test oracle approach, and non-determinism injection patterns are documented below in the Phase 2 workflow.

## Phase 0: Prerequisites

- [ ] Check for context continuity — see AGENTS.md §Session Continuity Check for trigger conditions. Load and execute the check logic from `save-session` Step 9 if needed.
- [ ] Read the review pass findings (from review-implementation)
- [ ] Run baseline tests — all must pass
- [ ] Apply Codebase Exploration per task type (see AGENTS.md §Codebase Exploration)
- [ ] Read ARCHITECTURE.md for current documented structure

## Documents to Read

- **`docs/ARCHITECTURE.md`** — "Project Structure", "Module Descriptions", "Import Structure"
- **Source files** — read key files per scan area to verify documented structure matches actual codebase
- **`docs/SPECIFICATIONS.md`** — "Out of Scope" to confirm no auth/accounts work

## Security Improvement Workflow

### Phase 1: Evaluate (Read-Only)

Scan all 9 areas in order. Priority definitions:
- **P0** — Must fix: exploitable vulnerability, data exposure, or safety risk
- **P1** — Should fix: defense-in-depth, hardening, or config improvement
- **P2** — Nice to fix: noisy logging, missing headers, or minor hardening

**Codebase Exploration:** See AGENTS.md §Codebase Exploration. Use **graphify** community detection to identify data-flow boundaries (untrusted input crossing layers). Use **ast_grep_search** to find dangerous patterns (eval, unsafe deserialization, raw queries) in one pass. Use **cocoindex-code** to discover all places where user input enters the system and trace where it flows.

| # | Area | What to Check | Priority Guide |
|---|---|---|---|
| 1 | **Secrets management** | Hardcoded API keys, passwords, tokens, or connection strings in source files | P0 = plaintext secret in source, P1 = secret in config default, P2 = secret in comments |
| 2 | **Unsafe deserialization** | `pickle`, `eval()`, `yaml.load()` without `Loader=yaml.SafeLoader`, `json.loads()` on untrusted input without schema validation | P0 = eval/pickle on untrusted data, P1 = unsafe yaml.load, P2 = unvalidated json.loads |
| 3 | **SQL / NoSQL injection** | Raw string interpolation in queries, unsanitized input reaching database layer | P0 = raw query with user input interpolated, P1 = lightly sanitized, P2 = missing parameterization on internal queries |
| 4 | **Cross-site scripting (XSS)** | User content rendered as HTML without escaping, `dangerouslySetInnerHTML`/`v-html` | P0 = unsanitized user content rendered, P1 = missing Content-Security-Policy, P2 = permissive inline script config |
| 5 | **Input validation** | Missing or inadequate validation at API boundaries, overly permissive type coercion | P0 = no validation on write endpoint, P1 = insufficient type constraints, P2 = missing boundary check |
| 6 | **CORS configuration** | Overly permissive `Access-Control-Allow-Origin: *`, missing `Access-Control-Allow-Credentials` checks | P0 = wildcard origin with credentials, P1 = wildcard without credentials but sensitive data, P2 = permissive methods |
| 7 | **Secure config** | `secure` and `httpOnly` cookie flags, HTTPS enforcement, CSP headers, HSTS | P0 = missing secure flag on session cookies, P1 = no CSP/HSTS, P2 = permissive cookie domain |
| 8 | **WebSocket security** | Origin validation on WS upgrade, message size limits, rate limiting on WS messages, message type validation | P0 = no origin check on WS, P1 = no message size limit, P2 = missing type validation |
| 9 | **Rate limiting** | Missing or inadequate rate limiting on API endpoints, especially auth-like operations | P0 = no limit on write endpoints, P1 = per-client limit too generous, P2 = missing on read endpoints |

Present findings as: `[P0/P1/P2] file:line — finding → Recommend: action`

### Gate: User Approval

Present findings and use the `question` tool to ask: **"Shall I apply these security fixes?"** Provide clickable `options` with `label` ("Apply all", "Select items", "Skip") and `description` fields. Rely on the auto-added "Type your own answer" for custom input.

Wait for explicit approval before Phase 2. If zero findings, report **"Security evaluation complete — no issues found."**

### Phase 1.5: Create Plan Document

Write approved findings to `docs/PLAN_YYYY_MM_DD_XXX.md` (sequential numbering, check-plan-readiness template). For combined execution, write a single unified plan covering all skill findings.

### Phase 2: Improve (Write)

#### TDD Principles

Security fixes must not break existing behavior. Test discipline is about preserving existing behavior while closing vulnerabilities.

**Test oracle approach** — for every item:
1. If an existing test covers this code, use it as the oracle (test passes before and after)
2. If no test covers it, write a regression test capturing current behavior first — save to `tests/`, confirm it passes
3. Apply the security fix
4. Run all tests — same count, all passing
5. If count changes (tests broke), flag and explain

**Test double discipline** — use the simplest substitute:
- **Stub** — return canned data, no assertions
- **Fake** — in-memory/lightweight real implementation
- **Spy** — record calls, assert after the fact
- **Mock** — assert specific interaction (use sparingly)

**Non-determinism injection** — inject clocks, RNG, network, and filesystem as parameters:
```python
def create_session(now=None, new_id=None):
    return {"id": str(new_id or uuid4()), "created_at": now or datetime.now()}
```

For each approved item (P0 → P1 → P2 order):

1. **Baseline** — Run full test suite. All must pass.
2. **TDD oracle** — Apply the test oracle approach above.
3. **Apply fix** — Add validation, escape output, add headers, harden config. Do NOT change unrelated behavior or fix non-security bugs. Apply changes one logical unit at a time within each file.
4. **Flag every changed line with `[SECURITY]`**
5. **Update test references** in same batch as source change.
6. **Verify** — Run full test suite. Compare to baseline counts:
   - Same count, all passing ✅
   - Count changed → flag and explain
   - Failure → see Conflict Resolution below

#### Conflict Resolution
When multiple approved items touch the same file or directory, sort by dependency order. If ordering isn't possible, present the conflict with a recommendation. Do NOT silently apply conflicting changes in sequence.

#### Failure Handling

| Symptom | Action |
|---------|--------|
| Import path error | Fix the import |
| Change correct but test brittle | Fix the test, re-verify |
| Change breaks intended behavior | Revert the batch, skip item |
| Any failure without diagnosing | Review before deciding |

#### Partial Completion & Staleness
- **Partial:** Track done items in-conversation. On resume, pick up at first undone item.
- **Stale evaluation:** If codebase changed significantly since Phase 1, re-run Phase 1 before continuing.

### Combined execution with improve-architecture and modularize-and-clean

When the user triggers `improve-security`, `improve-architecture`, and `modularize-and-clean` together (the default flow after first-pass review):

1. **Phase 1 runs in parallel** — each skill independently scans its defined scope (security vs structure vs code-level quality)
2. **Create Unified Plan Document**: All three pass findings to a merge-and-synchronize phase that produces a single unified plan at `docs/PLAN_YYYY_MM_DD_XXX.md` (sequential numbering, check-plan-readiness template)
3. **Unified plan** covers all findings from all skills, deduplicated and re-prioritized with P0–P2 labels per skill
4. **User approval**: Present the unified plan for approval
5. **Apply batches**: Security changes carry `[SECURITY]` flags, structural changes carry `[ARCH]` flags, code-quality changes carry `[CLEANUP]` flags — never mix flags in the same batch
6. **Review**: Route to `review-implementation`

## Hand-off
- Phase 1: All 9 areas evaluated, findings presented with priorities
- Gate: User approved (or selected specific items)
- Phase 1.5: Plan document created at `docs/PLAN_...`
- Phase 2: All approved items applied or explicitly skipped (with reason)
- Full test suite passes with same or documented test count change
- Every changed line carries `[SECURITY]` flag — zero non-SECURITY flags

### Abort Paths
If interrupted mid-phase: record current state in a TODO or pending list, offer to resume at the same point when re-invoked. Do NOT commit partial work.

---

## Outputs & Triggers

### Output
Plan document at `docs/PLAN_*.md` with prioritized findings (P0–P2) and file:line references. Security fixes with [SECURITY] flags, updated test imports, regression tests, summary of applied/skipped items.

### Exit Declaration
State clearly: "**Security improvements complete. Review implementation? Say 'review' to trigger review of the implementation.**"

### Next Step
User invokes `review-implementation` — recommend to switch to Plan mode before proceeding.
