# Universal Project Best Practices

> **Last verified:** 2026-06-12 22:30 EDT

> Derived from real-world debugging - applies to ALL projects

**Conciseness Rule**: Keep all descriptions 50% shorter than verbose explanations.
- ❌ Bad: "We encountered a problem where the indentation was incorrect in the __init__.py file which caused a syntax error"
- ✅ Good: "Indentation errors in `__init__.py` — verify after edits"

---

## 1. Modularization Techniques

### 1.1 Module Responsibility Pattern
**Context**: From `app/` package structure (1 line per file)

**Principle**: 1 module = 1 responsibility. Leaf modules (state.py, database.py) export only, never import from internal modules.

**Example**:
```
app/
├── __init__.py           # Orchestrator ONLY: init, wire modules
├── state.py              # Shared state & constants ONLY (leaf module)
├── database.py           # DB schema ONLY (leaf module)
├── config.py             # Config constants ONLY (leaf module)
├── schemas.py            # Pydantic models ONLY (leaf module)
├── helpers.py            # Shared utility functions ONLY (leaf module)
├── prompts.py            # Static conversation prompt data ONLY (leaf module)
├── qr_utils.py           # QR code generation utility ONLY (leaf module)
├── websocket_handler.py  # WebSocket message handling ONLY
├── routes.py             # HTTP + WebSocket endpoints ONLY
├── connection_manager.py # WebSocket connection tracking ONLY (leaf module)
├── matchmaking.py        # Business logic ONLY
└── tasks.py              # Background jobs ONLY
```

**Why it matters**: Clear ownership, no mixed concerns, easy to navigate.

### 1.2 Separation of Concerns
**Context**: From debugging mixed-state-logic bugs

**Principle**: Separate by layer: config → state → logic → presentation → persistence.

**Example**:
```
Configuration  → config.py / state.py (constants)
State         → state.py / models.py (in-memory)
Logic         → services.py / matchmaking.py (business rules)
Presentation  → templates/ / UI layer
Persistence   → database.py / repository layer
```

**Why it matters**: Changes in one layer don't break others.

### 1.3 Frontend Modularization
**Context**: From `frontend/src/` React/TypeScript structure and large page monoliths

**Principle**: 1 module = 1 purpose. Shared utilities in `utils/`, stateful logic in `hooks/`, context providers in `context/`, reusable UI in `components/`, page entries in `pages/`.

**Example**:
```
frontend/src/
├── config/constants.ts  # App configuration ONLY (CHAT_DURATION)
├── utils/               # Pure utility functions ONLY (format, storage)
├── api/client.ts        # API calls ONLY
├── context/             # React context providers ONLY
├── hooks/               # Custom React hooks ONLY
├── components/          # Reusable UI components ONLY
│   ├── Timer.tsx        # Timer display ONLY
│   ├── PromptCard.tsx   # Prompt card display ONLY
│   ├── PersonCard.tsx   # Person profile card ONLY
│   ├── PeoplePageViews.tsx # PeoplePage sub-views ONLY
│   └── ChatPageViews.tsx   # ChatPage sub-views ONLY
├── pages/               # Page-level components ONLY
└── types/api.ts         # TypeScript type definitions ONLY
```

**Why it matters**: No monolith files, predictable location for any concern, easy to find and test.

### 1.4 Module Communication
**Context**: From fixing import errors and tracing import chains in `app/` package

**Principle**: Leaf module pattern — leaf modules export only, never import from internal modules. Internal modules import from leafs only, never sibling-to-sibling.

**Example**:
```python
# ✅ Good — leaf modules export, internal modules import from leafs
from .state import active_users      # Import from leaf
from .matchmaking import find_match  # Import from sibling

# ❌ Bad — sibling-to-sibling import causes circular errors
# from .routes import something
```
Dependency graph:
```
routes.py → imports from → state.py, schemas.py, connection_manager.py, config.py, matchmaking.py, helpers.py, qr_utils.py, websocket_handler.py
matchmaking.py → imports from → state.py, connection_manager.py, config.py, helpers.py
tasks.py → imports from → state.py, config.py
connection_manager.py → no internal imports (leaf module)
config.py → no internal imports (leaf module)
schemas.py → no internal imports (leaf module)
helpers.py → no internal imports (leaf module)
prompts.py → no internal imports (leaf module)
qr_utils.py → no internal imports (leaf module)
```

**Why it matters**: Predictable dependency graph with zero circular import errors.

### 1.5 When to Split a Module
**Context**: From debugging sessions with large files

**Principle**: Split triggers: >200 lines, mixed concerns, circular imports, parallel dev conflicts.

**Example**: Your `routes.py` (171 lines) stays single-purpose: HTTP endpoints ONLY. Business logic → `matchmaking.py`, WebSocket handling → `websocket_handler.py`, QR generation → `qr_utils.py`, shared helpers → `helpers.py`.

**Why it matters**: File stays maintainable, merge conflicts reduced.

### 1.6 Documentation-Driven Module Design
**Context**: From ARCHITECTURE.md auto-extraction requiring Description: headers in source code

**Principle**: After creating a new module, write its `# Description:` header before writing any logic. The description must state the module's single responsibility in one concise line. This ensures the auto-extraction pipeline (ARCHITECTURE.md) always has a source of truth.

**Example**:
```python
# matchmaking.py
# Description: Async match-finding algorithm that pairs available users in the same room

# ... rest of file
```

**Why it matters**: Description headers are the canonical source for ARCHITECTURE.md — they must be written while the purpose is still clear, not retrofitted later.

### 1.7 Surgical Edit Pattern
**Context**: From updating skill files and instruction documents — rewrites risk silently dropping context

**Principle**: When updating instruction files (skills, workflows, rulesets), prefer `oldString→newString` replacements over full file rewrites. Each edit is independently verifiable by `oldString` uniqueness. Instruction files contain branching workflows and nuanced edge case handling — rewriting risks dropping context not explicitly identified as problematic.

**Example**: Instead of rewriting a 386-line skill file, apply 12 targeted replacements — each verifiable by selecting for the old text.

**Why it matters**: A rewrite that drops a single behavioral rule changes agent behavior permanently. Surgical edits preserve everything not explicitly changed.

### 1.8 One Logical Change Per Edit
**Context**: From multi-edit batches where interleaved changes made verification difficult

**Principle**: When making multiple changes to a file, apply one logical change per edit call. Each edit is independently verifiable — if an edit fails (oldString not found), only that single change is affected. This also makes the audit trail easier to review.

**Example**:
```
Bad: One edit changes 3 different sections simultaneously
Good: 3 separate edits, each changing one section with a unique oldString
```

**Why it matters**: Independent edits can be verified, reverted, or reviewed in isolation.

---

## 2. Configuration
**Context**: From fixing hardcoded URLs in QR code generation

**Principle**: Centralize config. Never hardcode. Use config files, env vars.

**Example**:
```python
# ❌ Bad
qr.add_data(f"http://localhost:5000/room/{id}")
# ✅ Good
qr.add_data(f"http://localhost:{Config.PORT}/room/{id}")
```

**Why it matters**: Change once, apply everywhere.

### 2.1 Server Binding for Browser Access
**Context**: `0.0.0.0` works for listening but browsers can't navigate to it
**Principle**: Default server bind to `127.0.0.1` for local development so the URL is directly browser-accessible. Only use `0.0.0.0` when network access from other devices is needed.
**Example**:
```python
# ✅ Local dev — browser-ready
HOST = '127.0.0.1'
# ✅ Network access — other devices can connect
HOST = '0.0.0.0'
```
**Why it matters**: `localhost:5000` works in a browser; `0.0.0.0:5000` doesn't.

### 2.2 Portable Config Paths
**Context**: Hardcoded user home path (`C:\\Users\\Alvin\\.local\\bin\\ccc.exe`) broke cocoindex-code MCP on a machine with a different username
**Principle**: When writing config files committed to version control, use PATH-resolved commands (`ccc`) instead of hardcoded absolute paths (`C:\\Users\\<user>\\.local\\bin\\ccc.exe`). Absolute paths are machine-specific — they work on one device but break every clone on another.
**Example**: `["ccc", "mcp"]` ✅ vs `["C:\\Users\\<username>\\.local\\bin\\ccc.exe", "mcp"]` ❌
**Why it matters**: Portable configs survive machine migration, team checkout, and CI execution without per-machine edits.

---

## 3. Error Handling
**Context**: From debugging API failures

**Principle**: Defense in depth: Validate input → try/except → graceful degradation.

**Example**:
```python
if not input: return {'error': 'No data'}, 400
try: result = api_call()
except: return {'error': 'Service unavailable'}, 503
```

**Why it matters**: Users get clear errors, not 500 pages.

---

## 4. State Management
**Context**: From fixing 404 errors after server restart

**Principle**: In-memory (fast, volatile) + Persistent (survives restart). Always recover.

**Example**:
```python
if user_id not in active_users:
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    active_users[user_id] = user  # Restore
```

**Why it matters**: Zero data loss on restart.

---

## 5. Testing
**Context**: From catching syntax errors post-edit

**Principle**: Test after every change. Syntax check + test suite.

**Example**:
```bash
uv run python -c "from app import app"  # Syntax check
uv run pytest tests/ -v                 # Full suite
```

**Why it matters**: Catch errors before they reach production.

### 5.1 TestClient Over Live Server
**Context**: E2E test scripts hung against a live server with WatchFiles reloader (port contention, stale state, hanging requests)
**Principle**: Use the framework's in-process TestClient (e.g. `fastapi.testclient.TestClient`) for integration tests instead of running a live server process. TestClient avoids reloader conflicts, port fights, and hanging requests while producing the same HTTP responses.
**Example**:
```python
# ✅ Use TestClient — no server process needed
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)
resp = client.get('/')
assert resp.status_code == 200

# ❌ Don't start a real server for tests
# subprocess.Popen(['python', '-m', 'app'])  # hangs, port conflicts, reloader issues
```
**Why it matters**: TestClient tests are deterministic, fast, and don't require port management.

### 5.2 TDD Tests Are Permanent Regression Tests
**Context**: Migration where TDD tests were written but not saved to `tests/` permanently

**Principle**: Tests written during TDD are saved permanently in `tests/` as regression tests. They are never deleted after the batch passes. Only skip test creation for non-testable changes: config, renames, typo fixes, infrastructure with no observable behavior. When in doubt, write the test.

**Example**:
```
# ✅ Each TDD batch produces code AND a saved test
tests/test_endpoint.py  ← stays forever, runs on every pytest

# ❌ Wrong: write test to make code pass, then delete it
```

**Why it matters**: Deleted tests leave the code unwatched. The regression safety net has holes.

### 5.3 Test References Updated in Same Batch as Code Changes
**Context**: Renaming a function in source without updating its test references — tests broke silently in the next batch

**Principle**: When a batch modifies existing code (rename, signature change, behavioral change), update ALL test references to that code in the **same batch** — import paths, function names, mock setups, and assertion expectations. Source and tests are a single unit; never split them across batches.

**Example**:
```
✅ Same batch: rename getUser → fetchUser in source + update test_getUser test
❌ Split: rename in batch 1, fix tests in batch 2 (tests fail between batches)
```

**Why it matters**: Every batch must be independently testable. Stale test references mean the batch fails verification and breaks the pipeline.

### 5.4 Test Health Audit
**Context**: Test files had stale file paths, misleading comments, and coverage gaps — but all tests still passed, so the issues went unnoticed

**Principle**: Periodically audit test files for structural health beyond pass/fail. Check three things: (1) stale file paths — do file-existence checks reference files that no longer exist? (2) misleading comments — do inline comments accurately describe what the test actually verifies? (3) coverage gaps — are files tested for exports but missing from file-existence and code-quality checks? A passing test suite can still have stale references that erode confidence over time.

**Example**:
```
Test health audit findings:
- test_app.py: line 115 lists 'requirements.txt' (replaced by pyproject.toml)
- test_app.py: line 346 comment says "Returns empty list" but endpoint creates 8 rooms
- test_js_modules.py: useChatRequest.ts tested for exports but absent from existence check
```

**Why it matters**: Passing tests lull confidence. Stale references and coverage gaps grow silently — by the time they cause failures, the drift is significant. Catch them early.

### 5.5 File Existence Checks in Tests
**Context**: `test_file_structure()` in test_app.py had hardcoded file paths that drifted from the actual project structure — `requirements.txt` was deleted, `app/static/css/style.css` was relocated

**Principle**: When tests check file existence with hardcoded path lists, update those lists in the same batch as the corresponding file rename, deletion, or relocation. Alternatively, use glob-based discovery instead of hardcoded lists so the check stays current automatically.

**Example**:
```python
# ❌ Hardcoded list — drifts from reality
required_files = ['app/static/css/style.css', 'requirements.txt']

# ✅ Glob-based — always current
import glob
all_py_files = glob.glob('app/**/*.py', recursive=True)

# ✅ Or: update the list in the same batch as the file change
```

**Why it matters**: Hardcoded file lists in tests are documentation — they become misleading the moment the file structure changes. A single missed update creates noise in test output that trains developers to ignore it.

---

## 6. Documentation

### 6.1 One Purpose Per Document
**Context**: From confusion about where content belongs and duplicate content across docs

**Principle**: One document = one purpose. Define each document by the questions it answers and the purpose it serves. If content answers a different question than the document's purpose, it belongs elsewhere. Move content to `/docs/` if README exceeds ~250 lines.

**Example**:
| Document | Answers | Purpose |
|----------|---------|---------|
| README.md | "What is it?", "How do I use it?" | User-facing: what, how, quick start |
| ARCHITECTURE.md | "How is it built?", "How do I modify it?" | Technical: *how* it's structured |
| SPECIFICATIONS.md | "Why does it exist?", "What problem does it solve?" | Product vision, user journey, why it exists |
| AGENTS.md | "What can agents touch?", "What commands do they use?" | Agent context: *what* agents work on |
| PROJECT_BEST_PRACTICES.md | "What lessons were learned?", "What patterns should I reuse?" | Universal coding patterns & lessons |
| DOCUMENT_GUIDELINES.md | "Where does this content go?" | Governance: doc scope & boundaries |

**Why it matters**: Clear purpose prevents content overlap. If two documents answer the same question, one is redundant. A purpose column makes the distinction actionable.

### 6.2 Key Differentiator Per Document
**Context**: From designing boundaries for a 7-doc documentation set

**Principle**: Every document needs a one-line "Key Differentiator" that captures what makes it unique. Bold it. Contrast it against its closest sibling document to prevent ambiguity.

**Example**:
- ARCHITECTURE.md = "**Implementation over vision**" (contrasts with SPECIFICATIONS.md which is "**Vision over implementation**")
- AGENTS.md = "**Operational constraints over technical structure**" (contrasts with ARCHITECTURE.md)
- README.md = "**User-facing benefits over implementation**" (contrasts with ARCHITECTURE.md)
- PROJECT_BEST_PRACTICES.md = "**Universal over project-specific**" (contrasts with every other doc)

**Why it matters**: When documents have similar scope, a single bold differentiator removes all ambiguity about where content goes.

### 6.3 Quality Gates Before Content
**Context**: From restructuring 6 skill files that lacked inclusion filters

**Principle**: Define "What qualifies for inclusion?" before writing any content. Four universal gates apply to most documentation:

1. **Litmus test**: "Would an agent or developer miss this without explicit documentation?" — filters noise. If they'd get it right anyway, leave it out.
2. **Executable truth**: "Can I verify this against code/config/scripts?" — filters speculation
3. **Conciseness**: "Can I say this in half the words?" — filters fluff
4. **Ownership filter**: "Does this concept belong to exactly one file or module?" — prevents fragmentation. One concept lives in exactly one place.

**Example**:
```markdown
# Before applying gates (would be rejected):
We decided to use FastAPI because it's a popular Python ASGI framework.

# After applying gates:
Tech stack: FastAPI + Uvicorn. Why FastAPI? Native WebSockets, async support.
```
The "popular" claim is speculative (gate 2), and the sentence is fluff (gate 3).

**Why it matters**: Prevents documentation bloat before it happens. Easier to filter upfront than edit later.

### 6.4 Routing Table Over Decision Tree
**Context**: From replacing text-based decision trees in 6 skill files with a single table

**Principle**: A routing table with a "Routes content about" column is more scannable and actionable than a text-based decision tree. Readers scan tables faster than nested trees, and the "about" column is directly actionable — you match your content to the description.

**Example**:
| Document | Routes content about |
|----------|---------------------|
| README.md | User-facing setup, usage, features, benefits, installation |
| ARCHITECTURE.md | Technical structure, modules, file tree, implementation, data flow |
| SPECIFICATIONS.md | Product vision, user journey, problem statement, pitch |
| AGENTS.md | AI agent permissions, rules, file ownership, operational constraints |

**Why it matters**: Faster routing decisions. One table replaces multiple decision trees and is easier to update.

### 6.5 Document Boundary Tensions
**Context**: From discovering 7 overlap points between documents that could confuse content routing

**Principle**: When documents touch, explicitly document the tension and its resolution. Don't let "this could go in either place" ambiguity persist — it causes inconsistent documentation.

**Example**:
```
Tension: API endpoints in AGENTS.md vs ARCHITECTURE.md
Resolution: AGENTS.md gets a reference table (method, path, purpose) for quick agent lookup.
           ARCHITECTURE.md gets the data flow context — how endpoints interact,
           request/response details, event sequences.

Tension: Product decisions in SPECIFICATIONS.md vs Design decisions in ARCHITECTURE.md
Resolution: SPECIFICATIONS.md = vision rationale ("why anonymous?")
           ARCHITECTURE.md = technical rationale ("why SQLite?")
```

**Why it matters**: Removes decision paralysis. Anyone can resolve the routing question in seconds.

### 6.6 Comments-First Documentation
**Context**: From syncing ARCHITECTURE.md lead lines with source code headers

**Principle**: Write standardized `Description:` headers in source code as the canonical description for each file. Auto-extract into documents rather than authoring descriptions separately in both places.

**Example**:
```python
# database.py
# Description: SQLite database initialization creating events, users, rooms, and matches tables with migration handling
# ====
```
Then ARCHITECTURE.md extracts the lead line from the comment — no manual duplication.

**Why it matters**: Single source of truth. Descriptions stay accurate because they live next to the code they describe.

### 6.7 Lead Line + Bullets Split
**Context**: From designing Module Descriptions in ARCHITECTURE.md

**Principle**: In module reference docs, split each entry into two parts: an auto-generated 1-sentence lead line (extracted from source comments) and manually maintained bullet points (implementation details not in code headers). Never regenerate bullets — they contain context that can't be inferred from code alone.

**Example**:
```markdown
### `app/routes.py` (HTTP Routes + WebSocket)
[auto-generated lead line from source]
- `router = APIRouter()` — defines all route handlers  [manually maintained]
- Endpoints: /, /join/<event_id>, ...                          [manually maintained]
```

**Why it matters**: Prevents automation from overwriting hard-won implementation context while keeping the headline always in sync.

### 6.8 Strict Subsection Ordering
**Context**: From fixing Frontend Modules ordering in ARCHITECTURE.md

**Principle**: Within each doc subsection, define explicit ordering (dependency → utility → user flow) rather than alphabetical or arbitrary. Prevents ordering chaos when auto-generating or adding entries.

**Example**:
```
Python Modules: __init__ → state → database → config → schemas → helpers → prompts → qr_utils → websocket_handler → routes → connection_manager → matchmaking → tasks → __main__
Frontend Pages: HomePage → UserInfoPage → RoomPage → PeoplePage → ChatPage → ConnectPage
Frontend Core: config → utils → api → types → context → hooks → components → pages
```

**Why it matters**: Entries stay logical and navigable regardless of how many times the section is regenerated.

### 6.9 Standalone Cross-Cutting Sections
**Context**: From finding Critical Implementation Details nested inside Module Descriptions

**Principle**: Don't nest cross-cutting content (configuration notes, critical implementation details, operational constraints) inside auto-generated sections. Make them standalone sections that live beside, not inside, the auto-generated content. This prevents structural corruption on regeneration.

**Example**:
```
❌ ## Module Descriptions (auto-generated)
     ### app/routes.py
     ### Critical Implementation Details  ← nested, will be lost on regen
     ### app/matchmaking.py

✅ ## Module Descriptions (auto-generated)
     ### app/routes.py
     ### app/matchmaking.py
   ## Critical Implementation Details (standalone)
```

**Why it matters**: Auto-generated sections will overwrite anything nested inside them. Standalone sections survive regeneration.

### 6.10 Verify Presence and Quality, Not Absence
**Context**: From simplifying the update-agents-md skill's Verify section — removed specific negative boundary checks in favor of a routing catch-all

**Principle**: A Verify checklist should check what the document contains and whether it's correct (positive correctness), not what it should NOT contain (negative boundaries). Routing rules (What NOT to Include) and Anti-duplication handle negative enforcement upstream. The single "No excluded content remains" catch-all catches stragglers. Avoid specific absence checks — they duplicate routing rules and bloat the checklist.

**Example**:
```
✅ Keep: "Content's PRIMARY purpose identified and routed to the correct document"
✅ Keep: "Every line passes the 'Would someone miss this?' litmus test"
❌ Remove: "No API endpoint tables — belongs in ARCHITECTURE.md" (covered by routing + catch-all)
❌ Remove: "No product constraints" (covered by routing + catch-all)
```

**Why it matters**: Keeps Verify checklists lean and focused on quality. Routing correctness is enforced earlier; the final step only verifies what IS there.

### 6.11 Single Canonical Location for Artifacts
**Context**: Plan files existed in both `.opencode/plans/` and `archive/` causing numbering confusion

**Principle**: Each type of persistent artifact has exactly one canonical directory. Never create copies or variants in alternate locations. One step owns creation of that artifact; all others read-only.

**Example**:
```
# ✅ All archive plan files in archive/plan/
archive/plan/PLAN_2026_05_12_001.md
archive/plan/PLAN_2026_05_12_002.md

# ❌ Orphan artifact in .opencode/plans/ creates conflicts
```

**Why it matters**: Two locations for the same artifact type breaks numbering, confuses agents, and fragments decision history.

### 6.12 File Description Convention Across All Languages
**Context**: Frontend TS/TSX files had no file-level descriptions while Python files had consistent `# Description:` headers — inconsistency made ARCHITECTURE.md auto-extraction incomplete

**Principle**: Every code file across all languages must have a file-level description header following the same two-line pattern, adapted to the language's comment syntax. The description states the module's single responsibility in one concise line.

**Example**:
```typescript
// Timer.tsx
// Description: Timer display component showing MM:SS with warning/danger visual states

// ... rest of file
```
```python
# matchmaking.py
# Description: Async match-finding algorithm that pairs available users in the same room

# ... rest of file
```
```css
/* style.css */
/* Description: Global stylesheet for IntroChat — reset, layout, component styles, and responsive rules */
```
Comment syntax by language: `#` for Python, `//` for TS/TSX/JS, `/* */` for CSS.

**Why it matters**: Single source of truth for auto-extraction into ARCHITECTURE.md. Descriptions stay accurate because they live next to the code they describe. New contributors and AI agents can understand each file's purpose at a glance.

### 6.13 ARCHITECTURE.md Project Structure Tree Synced from Source
**Context**: After adding description headers to 45 frontend files, the Project Structure tree in ARCHITECTURE.md still showed the old generic descriptions — only Module Descriptions were auto-synced

**Principle**: The inline `# ` descriptions in the Project Structure ASCII tree must be synced from source file `Description:` headers, not just Module Descriptions lead lines. Both the tree and the module entries are auto-extracted from the same source-of-truth headers.

**Example**:
```
Before: │   ├── format.ts      # formatTime() — seconds to MM:SS
After:  │   ├── format.ts      # Utility functions for formatting values (time, display strings)
```

**Why it matters**: The file tree is the first thing readers see. If its descriptions are manual, they drift from reality. Syncing both tree and module entries from the same source headers keeps the entire document internally consistent.

---

### 6.14 Documentation Conciseness & Anti-Bloat
**Context**: From reducing AGENTS.md 186→99 lines while preserving all core rules — pattern extends to skill files, which face the same context-window pressure

**Principle**: Apply six surgical reductions before adding or revising any document or skill file:

1. **Prune safe defaults** — Omit entries describing normal/expected behavior. Document only exceptions, constraints, and non-obvious rules. In tables, remove rows marked ✅ — keep only ⚠️ and ❌.
2. **Cut trailing noise** — If bold/emphasized text already carries the meaning, drop restatements that follow. Do not explain what the bold text already conveys.
3. **Merge overlapping siblings** — Combine bullets that say the same thing from different angles. The merged version must be *shorter* than either original — not a longer superset.
4. **Group under scan headers** — Flat lists of 8+ bullets get 3–5 group headers so readers find what applies without reading every bullet.
5. **One canonical location per fact** — Every fact lives in exactly one place. If two sections overlap, pick the primary owner and replace duplicates with `[See ...](...)` using specific section anchors (e.g., `file.md#heading`).
6. **Imperative over advisory** — Write direct instructions ("Run full test suite"), not suggestions ("Agents should consider running the full test suite").

**Example**:
| Dimension | Before (AGENTS.md) | After |
|-----------|-------------------|-------|
| Total lines | 186 | 99 |
| File Ownership rows | 21 (every file with ✅/⚠️/❌) | 9 (only ⚠️ and ❌) |
| Process Discipline bullets | 15 flat bullets | 3 group headers (Integrity / Execution / Hygiene) with concise bullets |
| Routing info | Scope blockquote + Cross-References section (duplicate) | Scope blockquote only (upgraded with precise anchors) |

Every core rule preserved — zero content loss.

**Why it matters**: Documents and skill files are read under context-window pressure. Every bloat token wastes the reader's limited context. A lean document with the same signal is strictly better — faster to scan, cheaper to read, and equally correct.

---

## 7. Session Lessons Learned

### 7.1 Syntax Verification
**Context**: Indentation errors hidden until runtime

**Principle**: Verify Python syntax after edits.

**Example**:
```bash
uv run python -m py_compile **/*.py
uv run python -c "from app import app"
```

**Why it matters**: Catch errors before testing.

### 7.2 Import Discipline
**Context**: Wrong import in `matchmaking.py`

**Principle**: Use `import sqlite3`, relative imports (`from .state import`).

**Example**:
```python
# ✅ import sqlite3; from .state import active_users
# ❌ from .database import sqlite3  # Wrong!
```

**Why it matters**: Avoids circular imports, clear dependency chain.

### 7.3 API Contract First
**Context**: Had to add 5 missing endpoints mid-development

**Principle**: Define all API endpoints before frontend expects them.

**Why it matters**: No mid-development surprises.

### 7.4 Immediate Verification
**Context**: From debugging multiple issues at once

**Principle**: Test after every single fix. One change = one verification.

**Why it matters**: Isolate problems, faster debugging.

### 7.5 Investigation Priority Order
**Context**: From designing investigation workflows across 6 different document update skills

**Principle**: Always define the priority order for what to read first. Different document types need different priorities. Don't read randomly — read the highest-signal source first.

**Example**:
- For technical docs (ARCHITECTURE): code → configs → CI → existing doc
- For best practices (PROJECT_BEST_PRACTICES): existing doc → session conversation → code
- For product docs (SPECIFICATIONS): existing doc → code (features only) → README

**Why it matters**: Prevents reading low-signal files first. The right priority order can cut investigation time in half.

### 7.6 Inline Constraints With Items
**Context**: From removing separate "Content Boundaries" sections across 6 skill files

**Principle**: Don't separate "what to include" from "how to format it." Inline formatting/constraint rules directly into the inclusion item. One concept, one place.

**Example**:
- ❌ Two sections: Section A says "Include API endpoints." Section B says "Summary table only."
- ✅ One item: "API endpoints — summary table only, no request/response examples."

**Why it matters**: No need to cross-reference sections. The constraint lives with the item it constrains.

### 7.7 Merge Pre-Verification With Post-Verification
**Context**: From merging "Checklist Before Adding Content" with "Step 5: Verify" across 6 skill files

**Principle**: A checklist before writing and a verification step after writing serve the same purpose. Merge them into one comprehensive verification step instead of maintaining two separate lists that half-overlap.

**Example**:
- Before: "Checklist" (6 items: check purpose, check routing, check duplications) + "Step 5: Verify" (8 items: check purpose, check routing, check duplications, check formatting...)
- After: One "Verify" step with all 8 items — the first 3 address pre-write thinking, the remaining 5 address post-write checking.

**Why it matters**: Eliminates duplicate maintenance. One list to update, one place to look.

### 7.8 Gap Grilling Methodology
**Context**: From comparing /init template against update-agents-md skill

**Principle**: When comparing two sources (template vs implementation, spec vs code), don't just list differences. Test each gap against four questions: (1) Is it truly additive (not already covered)? (2) Does it affect output or methodology? (3) Which document owns it? (4) What's the cost/benefit? Only act on gaps that survive the grill.

**Example**:
```
Gap found: "Prefer wiring files over leaf files"
Grill: (1) Not currently explicit — additive ✓
       (2) Investigation methodology only — affects skill, not output ✓
       (3) Belongs in update-agents-md skill ✓
       (4) Low cost — one sentence addendum ✓
Decision: ✅ Add
```

**Why it matters**: Prevents scope creep. Most gaps fail one of the four questions and can be safely skipped.

### 7.9 Docs-First Analysis Pipeline
**Context**: From revising brainstorm-and-plan skill to prefer docs over full codebase parsing

**Principle**: Before analyzing requirements against a codebase, consult existing docs first. Docs are compact, structured, and token-efficient. Only fall back to full source code examination when the docs don't cover what's needed. Spot-check 1-2 key source files to confirm docs aren't stale — "trust but verify."

**Example**:
```
Task: Add a new API endpoint
1. Read SPECIFICATIONS.md (product context) and ARCHITECTURE.md (existing endpoints)
2. Spot-check app/routes.py to confirm the endpoint table is accurate
3. Only read full codebase if neither doc covers the needed detail
```

**Why it matters**: Saves tokens, builds on existing knowledge, catches stale docs cheaply.

### 7.10 Interactive Walkthrough — One Item at a Time, Names Only
**Context**: From revising brainstorm-and-plan and grill-and-refine interaction models; user enforced "one item at a time" discipline after being presented 6 assumptions in one message

**Principle**: When probing a plan or design with a user, never present multiple items in a single message. Walk through decision-points ONE AT A TIME. For skip confirmation: present only dimension NAMES upfront — do not describe their contents or list items within them. The agent chooses the order and walks through sequentially. Within each dimension, present one finding at a time, offer concrete options, accept free-form input, resolve before moving to the next.

**Example**:
```
✅ One item at a time:
  You: "Assumption #1 — UserInfoPage button. Options: Green or Gray?"
  User: "Green"
  You: "Resolved. Next: Assumption #2 — HomePage two CTAs..."

❌ Before (dumps all):
  You: "6 assumptions to resolve... [lists all 6 with options in one message]"
  User: "Stop, walk me through one by one"
```

**Why it matters**: Dumping multiple items in one message overwhelms the user and forces them to re-teach the agent how to interact. One-at-a-time keeps the conversation structured and efficient.

### 7.11 Presence Check Over Re-Probe
**Context**: From reframing readiness-check as document verifier instead of deep analyzer

**Principle**: When verifying a document against a set of criteria, check that each criterion is **explicitly addressed** in the document — don't re-analyze the underlying content from scratch. The document's author already did the analysis; the verifier's job is to confirm coverage. This is faster than re-probing and avoids duplicating the author's work.

**Example**:
```
✅ Presence check: "Does the plan state confirmed assumptions?" → reads the plan, finds "## Grill Outcomes" with assumption notes
❌ Re-probe: "Are these assumptions valid? Let me check the codebase again..."
```
Exception: Soundness verification requires active assessment — "does the plan hold together?" — not just presence.

**Why it matters**: Eliminates rework. The author probes, the verifier checks coverage. Not the other way around.

### 7.12 Triage Routing
**Context**: From designing failure handling in readiness-check and review-implementation

**Principle**: When a verification step finds a failure, don't attempt deep resolution in the verification step. Instead, triage: minor gaps (missing documentation, unclear wording) get a quick fix in-place; significant gaps (unresolved assumptions, soundness risks, failing tests) route backward to the owning stage. Each stage knows when to fix and when to escalate.

**Example**:
```
readiness-check finds:
- Missing doc reference → minor: fix in-place, update plan file, re-check
- Unresolved assumption → significant: route back to grill-and-refine

review-implementation finds:
- Lint issue → minor: fix the formatting, re-run lint
- Test failure → significant: route back to implement-plan
```

**Why it matters**: Prevents verification steps from duplicating the work of earlier stages. Clear ownership of each fix type.

### 7.13 Preserve File Description Comments
**Context**: During implementation, agents deleted the `# Description:` comment block at the top of code files when rewriting them
**Principle**: Never remove file-level description comments (the docstring or comment block at the top of a file describing its purpose). You may edit them to improve accuracy or align with actual functionality after changes, but do not delete them. These are the canonical source of truth for what the file does — other docs (ARCHITECTURE.md) auto-extract from them.
**Example**:
```python
# ✅ Preserve and update
# Description: HTTP routes for event creation, user management, matchmaking, and WebSocket connections

# ❌ Never delete — this comment is the canonical source for ARCHITECTURE.md
```
**Why it matters**: Deleting them breaks the single-source-of-truth chain between code and documentation. They're referenced by auto-extraction scripts.

### 7.14 Windows Shell Quoting Workaround
**Context**: PowerShell mangled Python f-strings with double quotes in inline `uv run python -c "..."` commands. Scripts timed out or produced syntax errors.
**Principle**: On Windows PowerShell, write complex Python scripts to `.py` files instead of inline strings in `uv run python -c "..."`. Use `$env:PYTHONIOENCODING='utf-8'` before running scripts that output emoji or Unicode.
**Example**:
```powershell
# ❌ PowerShell mangles embedded double quotes in f-strings
uv run python -c "print(f'Hello {name}')"  # ← broken

# ✅ Write to a file and run it
uv run python script.py

# ✅ Encoding fix for emoji in PowerShell
$env:PYTHONIOENCODING='utf-8'; uv run python test_suite.py
```
**Why it matters**: Cross-platform shell differences cause silent failures. Writing to a file avoids quoting issues entirely.

### 7.15 Matchmaking Queue Filter Direction
**Context**: A bug where `uid not in waiting_queue` was used instead of `uid in waiting_queue`, causing the queue to exclude the very users it should match
**Principle**: When implementing matchmaking or queue-based matching, double-check the filter direction. The queue should look for users IN the queue (they're waiting for a match), not exclude them. Test the happy path with two users to confirm the flow works end-to-end.
**Example**:
```python
# ✅ Find users who ARE waiting for a match
if uid in waiting_queue:
    available_users.append(uid)

# ❌ This excludes the very users waiting to be matched
if uid not in waiting_queue:
    available_users.append(uid)
```
**Why it matters**: Inverted boolean logic in queues is a classic bug that looks plausible in review but silently breaks the entire matching flow.

### 7.16 TypedDict for Structured In-Memory State
**Context**: In-memory state used plain dicts with string keys (`active_users[uid] = {...}`) — key typos and undocumented shapes caused bugs during matchmaking and connection exchange refactoring

**Principle**: Use `TypedDict` (or equivalent typed structures) for in-memory state dicts that are accessed across multiple modules. This documents the expected shape in one place, catches key-name typos statically, and makes the data contract visible without tracing runtime usage.

**Example**:
```python
from typing import TypedDict

class UserData(TypedDict):
    event_id: str
    username: str
    room_id: str | None
    linkedin_url: str
    slack_handle: str
    is_available: bool
    last_seen: str | None
```

**Why it matters**: TypedDict serves as executable documentation — the shape is checked statically and visible without reading initialization code. Plain dicts hide their structure; every consumer must infer keys from usage patterns.

### 7.17 Thread Safety for Shared Mutable State
**Context**: Background thread (`tasks.py`) and async HTTP handlers both mutated `active_matches` dict — race conditions caused phantom matches and lost cleanup events

**Principle**: When shared mutable state is accessed by background threads and async event handlers concurrently, protect ALL mutation points with a `threading.Lock`. Every `read → modify → write` cycle must happen inside the same lock scope. Never add state mutations outside the lock — one missed site creates a race condition.

**Example**:
```python
# state.py
active_matches: dict[str, MatchData] = {}
active_matches_lock = threading.Lock()

# tasks.py — background cleanup
with active_matches_lock:
    for match_id, match in active_matches.items():
        ...

# routes.py — HTTP handler
with active_matches_lock:
    if match_id not in active_matches:
        raise HTTPException(status_code=404)
```

**Why it matters**: Race conditions in shared state are intermittent and hard to reproduce. A single missing lock site can corrupt data silently. Wrapping every mutation in the same lock is the only reliable defense.

### 7.18 Root Pattern Extraction
**Context**: From revising the update-best-practices-md skill to push for root cause over symptom

**Principle**: When extracting lessons from a session, distinguish the symptom (what happened) from the root cause (why it happened). The root pattern is the universally applicable form — it transfers to other projects. If the root becomes too abstract to be useful, step back one level. Guard: a pattern passes if a developer on an unrelated project would still find it valuable.

**Example**:
```
Symptom: "Don't accept a WebSocket twice."
Root:     "When extracting helper functions, check for duplicated lifecycle calls
           between handler and helper — one lifecycle action should live in exactly
           one caller, not split across both."

Symptom: "AES-GCM: don't reuse nonces."
Root:     "Always derive cryptographic nonces from a deterministic counter or a
           CSPRNG, never from user-controlled input or timestamps."
```

**Why it matters**: Symptom-level lessons only fix this one case. Root-level lessons prevent entire categories of bugs.

### 7.25 Sequential Numbering for Plan Files
**Context**: Numbering collision when migrating plan files between directories — `.opencode/plans/PLAN_001` and `archive/plan/PLAN_001` both existed

**Principle**: When artifacts use sequential numbering, the number must be globally unique across ALL locations. Before assigning a new number, scan the canonical directory for existing files and pick the next available. Never reuse a number from an alternative directory that was later merged.

**Example**:
```
# ✅ docs/ has 001, 002 → next is 003
# ❌ Bringing in an artifact numbered 001 from elsewhere creates a duplicate
```

**Why it matters**: Duplicate numbers create ambiguity about which artifact is the real one — the chain of decision history breaks.

### 7.26 Skill Rename Protocol
**Context**: Renaming `grill-plan-and-refine` → `grill-and-refine` and `plan-readiness` → `check-plan-readiness`

**Principle**: Renaming any component with cross-references follows this protocol: (1) create new directory, (2) copy file contents, (3) delete old directory, (4) update the component's internal name field, (5) update every cross-reference across all files that reference the old name. Use `replaceAll` for bulk updates. Verify zero stale refs survive.

**Example**:
```
# After rename, verify with:
grep -r "old-name" --include="*.md"    # should return nothing
```

**Why it matters**: A single stale reference can break the workflow chain silently — the skill becomes unloadable or routes to the wrong destination.

### 7.19 Workflow Handoff with Outputs & Triggers + Hand-off Checklists
**Context**: The 5-step analyze→grill→check→implement→review pipeline lacked structured connectivity between stages; later extended to 9 phases

**Principle**: Every workflow stage defines four things: (1) what it produces (Output), (2) a pre-exit **Hand-off checklist** with verifiable completion criteria, (3) how it signals completion (Exit Declaration), (4) which stage runs next (Next Step). This creates an explicit handoff contract — verify, then signal. Never let a stage finish without proving readiness and making the next step obvious.

**Example**:
```
improve-architecture
  ## Hand-off
  - All approved items applied or skipped (with reason)
  - Full test suite passes
  - Every changed line carries [ARCH] flag
  ---
  Exit: "Architecture improvements complete. Review implementation?"
  → review-implementation knows it's next
```

**Why it matters**: Without a verifiable pre-exit checklist, stages can declare completion without proving it. The checklist catches incomplete work before handoff.

### 7.20 WebSocket Accept Once
**Context**: "Expected ASGI message websocket.send or websocket.close, but got websocket.accept"
**Principle**: Call `accept()` on a WebSocket exactly once. Accept in the route handler, not in nested connection managers. The connection manager should assume the WebSocket is already accepted.
**Example**:
```python
# ✅ Route handler accepts, manager only registers
@router.websocket('/ws')
async def ws_endpoint(websocket: WebSocket):
    await websocket.accept()       # ← accept here
    await manager.connect(ws, uid) # ← manager does NOT accept again

# connection_manager.py
async def connect(self, ws, uid):
    # ❌ await ws.accept() — already accepted
    self.connections[uid] = ws
```
**Why it matters**: Double-accept raises a runtime error that kills the WebSocket connection.

### 7.21 Skill Audit After Content Restructure
**Context**: When content from one document moves to other documents (e.g., AGENTS.md content transferred to README.md, ARCHITECTURE.md, PROJECT_BEST_PRACTICES.md), the owning skills have stale "What to Include" rules
**Principle**: After moving content between documents, update each target document's owning skill in the same batch. The skill's "What to Include" must match what the document actually contains, not what it used to contain. If you skip the skill update, the next time the skill runs it regenerates old boundaries — the document fix is temporary, but the skill fix is permanent.
**Example**: Removed "Templates" from `update-architecture-md`'s module categories; added venv activation + path-drift warning to `update-readme-md`'s Quick Start rules; added State Management category to `update-best-practices-md`
**Why it matters**: A stale owning skill undoes the document fix on next run. Fixing both in the same batch prevents regression.

### 7.22 Exhaustive Section Mapping
**Context**: From comparing 3 documents against their owning skills section by section and finding drift in every one
**Principle**: When comparing two related files (doc↔owning skill, spec↔implementation), read both end-to-end and map every section explicitly. Don't infer gaps from section headings alone — inference misses silent drift where a doc section has no corresponding skill rule. Create a two-column table: "Doc section" | "Skill has it?" for the full comparison.
**Example**: Doc's §4 "State Management" had no corresponding category in the skill's "What to Include" — caught only by exhaustive mapping, not by heading scanning.
**Why it matters**: Section-heading inference is fast but unreliable. Exhaustive mapping catches every gap and prevents iterative "find one fix one" cycles.

### 7.23 Stale Pattern Audit After Migration
**Context**: SocketIO decorator extraction logic, DOMContentLoaded wrappers, and Jinja2 conventions survived in skill files after Flask→FastAPI, SocketIO→WebSocket, and Jinja2→React migrations
**Principle**: After a framework migration, grep all skill and instruction files for the old technology's specific patterns. They survive in multiple subsections — decorator extraction examples, per-function formatting rules, verify checklists — far from where the migration source code changed. Search broadly: technology names (SocketIO, Jinja2), framework-specific constructs (DOMContentLoaded, socketio.on), and old file globs (app/static/js/*).
**Example**: After Jinja2→React migration, "Jinja2 conventions" still existed in `update-best-practices-md`; `@socketio.on(...)` still existed in `update-architecture-md`'s decorator extraction section; DOMContentLoaded extraction logic still existed in `update-architecture-md`'s per-function detail step.
**Why it matters**: A single stale reference in a skill can corrupt the entire section when the skill regenerates the document. Skills are instruction sets — one wrong instruction produces wrong output.

### 7.24 Consistency Pass as Final Cross-Cutting Step
**Context**: After standardizing Hand-off sections across 9 workflow skills — individual edits were correct but collectively inconsistent (mismatched heading names, missing sections, inconsistent prefixes)

**Principle**: After completing a cross-cutting change across multiple files, run a dedicated consistency pass rather than assuming each individually correct edit produces a coherent whole. Read every affected file end-to-end once more, checking for: naming consistency, section structure uniformity, and coverage completeness. Fix all inconsistencies in one batch.

**Example**:
```
Individual edits: added Hand-off sections to 9 skills
Consistency pass found:
- 4 skills missing Hand-off entirely
- 2 skills had wrong heading level (#### vs ##)
- 3 skills missing "State clearly:" prefix
All fixed in one pass.
```

**Why it matters**: Individual correctness ≠ collective consistency. The consistency pass catches structural drift that individual edits miss.

### 7.27 Surgical Edits Over File Rewrites
**Context**: 23 targeted edits across 3 skill files preserved all existing context while fixing every gap identified by exhaustive mapping
**Principle**: When updating instruction files (skills, workflows, rulesets), prefer oldString→newString replacements over file rewrites. Instruction files contain branching workflows, nuanced edge case handling, and manually maintained rules — rewriting them risks silently dropping context that wasn't explicitly identified as problematic. Each edit is independently verifiable by oldString uniqueness.
**Example**: Instead of rewriting `update-architecture-md/SKILL.md` (386 lines), 12 targeted replacements were applied — each verifiable by selecting for the old text.
**Why it matters**: A rewrite that drops a single behavioral rule changes agent behavior permanently. Surgical edits preserve everything not explicitly changed.

### 7.28 Three-Layer Verification After Bulk Edits
**Context**: After 23 edits across 3 skill files, three separate verification layers each caught a different class of issue
**Principle**: After a batch of surgical edits, verify at three layers: (1) grep for stale patterns that should have been removed, (2) grep for additions that should have been added, (3) read the critical sections of each file for structural correctness. Layer 1 catches what you missed removing, Layer 2 catches what you missed adding, Layer 3 catches structural breakage (empty subsections, orphaned references, broken formatting). Never skip layer 3.
**Example**: Layer 1 caught `@socketio.on()` still surviving after SocketIO→WebSocket rename; Layer 2 confirmed `ENV=production` was present in both skills; Layer 3 would catch an empty "Where to place the subsection" section.
**Why it matters**: Each layer catches what the others miss. Layer 1 and 2 are grep-fast; Layer 3 requires reading but catches silent structural breaks that no regex can find.

### 7.29 Edge Case First Testing
**Context**: Tests only covered happy paths; edge cases discovered post-deployment
**Principle**: Before implementing body logic, enumerate boundary conditions. Write one edge-case test per new feature. Edge cases include: empty/null inputs, max boundaries, type mismatches, concurrent access, and failure modes.
**Example**:
```python
def test_matchmaking_empty_queue():
    result = find_match(waiting_queue=[])
    assert result is None
```
**Why it matters**: Catches design flaws before they're baked into the implementation. Edge cases first forces thinking about contracts before code.

### 7.30 Structured Audit Over Vague Assessment
**Context**: "Performance audit" was too vague to produce actionable results
**Principle**: When a review asks for an audit (performance, security, dependency), replace the subjective request with concrete, enumerable checks. Each check must be answerable with a yes/no and have a pass/fail criterion.
**Example**:
```
❌ Vague: "Audit performance"
✅ Concrete: (1) Check stale closures in useEffect deps, (2) Check unnecessary memoization, (3) Check bundle impact >10KB gzipped, (4) Check sync I/O in async handlers, (5) Check N+1 queries, (6) Check memory leaks in cleanup functions
```
**Why it matters**: Vague audit requests produce shallow, inconsistent results. Concrete checks produce the same thorough answer every time.

### 7.31 Happy-Path-Only Coverage as Anti-Pattern
**Context**: Test suites consistently lacked edge case coverage
**Principle**: Flag when a test suite only covers the happy path without any edge-case tests. Require at least one edge-case test per new feature (empty state, error state, boundary value, or failure mode). A test suite without edge cases gives false confidence.
**Example**:
```
✅ Pass review if: function has 1 happy-path test + 1 edge-case test
❌ Flag if: function has 5 happy-path tests but 0 edge-case tests
```
**Why it matters**: Happy-path-only testing is the most common testing gap. Explicitly requiring edge-case coverage prevents the "all green, shipped broken" pattern.

### 7.32 Dependency Audit Protocol
**Context**: Dependencies were added without structured evaluation
**Principle**: Before adding a dependency, run a structured audit: (1) Justification — what specific problem does it solve that existing code doesn't? (2) Size — what's the bundle/install size impact? (3) Transitive damage — how many sub-dependencies does it pull in? (4) Version pinning — is the version pinned to a specific release? (5) Duplicate risk — does another dependency already solve this need?
**Example**:
```
Dependency audit: lodash@4.17.21
- Justification: deepMerge utility — stdlib has no equivalent ✓
- Size: 24KB min (7KB gzipped) ✓
- Transitive: 0 sub-deps ✓
- Pinned: yes ✓
- Duplicate: no existing solution ✓
→ Approved
```
**Why it matters**: Dependencies are permanent liabilities — each must be scrutinized with a repeatable evaluation, not gut feel.

### 7.33 Component Merge via Mode/Type Prop
**Context**: Two UI components sharing 80%+ of layout but differing in specific content or behavior
**Principle**: Instead of maintaining separate components (which drift apart over time), merge them with a `mode` or `variant` prop. Use conditional rendering only for the divergent parts — the shared layout renders identically across modes.
**Example**: Removed `ExtendedView` component and merged its behavior into `ChattingView` with `mode='initial' | 'timed' | 'indefinite'`. The duration text block differs between modes, but the prompt card, next-prompt button, and overall card layout are shared:
```tsx
{mode === 'indefinite' ? (
  <p>indefinite time to connect and chat</p>
) : (
  <p>{formatDuration(CONFIG.CHAT_DURATION)} to connect and chat</p>
)}
```
**Why it matters**: Eliminates layout duplication, prevents drift between "identical" copies, reduces test surface.

### 7.34 Build Production Dist for Backend-Served SPA
**Context**: Frontend SPA built to `dist/` and served by a Python/backend server in production
**Principle**: After any frontend change, rebuild the production bundle (`npm run build`). The dev server (`npm run dev`) serves from memory — only the `dist/` directory is served by the production backend. A stale `dist/` = stale JS bundles reaching users.
**Example**:
```bash
cd frontend && npm run build
uv run python -m app
# Now http://localhost:5000 serves the updated SPA
```
**Why it matters**: Dev-only workflow (Vite dev server) masks stale production assets. Production server serves `dist/` — must be rebuilt every time.

### 7.35 Shared Context for Cross-Page Resource Lifecycle
**Context**: A resource (WebSocket, connection pool) that must survive route changes across multiple pages
**Principle**: Place the resource in a shared context provider that persists across navigation. Each page connects on mount — but does NOT disconnect on unmount. The context owns lifecycle management; individual pages are just consumers that ensure the resource is active when needed.
**Example**: PeoplePage, ChatPage, and ConnectPage all call `socket.connect(userId)` on mount with no cleanup. SocketContext provides a single persistent WebSocket that survives route changes:
```tsx
useEffect(() => {
  if (user?.userId) socket.connect(user.userId);
}, [user?.userId]);  // No cleanup — context manages persistence
```
**Why it matters**: Prevents connection loss during page transitions; avoids complex disconnect/reconnect logic on every navigation; consistent pattern across all pages.

### 7.36 Unicode Encoding for Windows PowerShell
**Context**: Running Python scripts on Windows that output emoji or Unicode characters (test headers, progress bars)
**Principle**: Set `$env:PYTHONIOENCODING='utf-8'` before Python commands to prevent `UnicodeEncodeError: 'charmap' codec can't encode character`. The default Windows terminal encoding (cp1252) cannot encode characters outside its code page.
**Example**:
```powershell
# ❌ UnicodeEncodeError: emoji in test output header
uv run python tests/test_app.py

# ✅ Works: forces UTF-8 encoding for Python stdout
$env:PYTHONIOENCODING='utf-8'; uv run python tests/test_app.py
```
**Why it matters**: Test suites using Unicode in output (status icons, emoji section markers) fail silently on Windows without this. Cost: one env var per command.

### 7.37 Functional Updater for Interval Timers
**Context**: Using `setInterval` in React hooks (especially with fake timers in tests)
**Principle**: Always use the functional updater form `(prev) => newValue` in `setInterval` callbacks. This ensures the timer always reads the latest state regardless of when the interval fires — critical when `vi.useFakeTimers()` runs intervals synchronously while real browsers run them asynchronously.
**Example**:
```tsx
// ✅ Always reads latest count — works with both fake and real timers
setCount((prev) => prev - 1);

// ❌ Stale closure — count value is captured at interval creation
setCount(count - 1);
```
**Why it matters**: Stale closure bugs in timers are notoriously hard to reproduce (only appear under specific timing conditions). The functional updater is immune by design.

### 7.38 Production-Gated Security Features

**Context**: CORS restrictions and rate-limiting middleware broke development testing — the TestClient doesn't have a real `request.client.host`, and rate limits throttle test POST requests. Gating behind `ENV=production` solved both.

**Principle**: When adding security features (CORS restrictions, rate limiting, HTTPS-only cookies, Content Security Policy) that would interfere with development or testing, gate them behind an environment variable check (`ENV=production`). Never comment them out or toggle them manually — env var gating is deterministic, testable, and survives commits.

**Example**:
```python
is_production = os.environ.get("ENV", "").lower() == "production"

if is_production:
    app.add_middleware(CORSMiddleware, allow_origins=["https://app.example.com"], ...)
    app.add_middleware(RateLimitMiddleware, max_requests=30, window_seconds=60)
```

**Why it matters**: Dev and prod have different security needs. An unrestricted CORS policy is fine for `localhost`; the same policy in production is a vulnerability. Gating by env var keeps both environments correct without manual toggling.

### 7.39 Post-Consolidation Import Audit

**Context**: After moving `import random` from inside a function body to the top of the file, the duplicate import at the original location was not removed — the code compiled fine but carried dead baggage.

**Principle**: After consolidating imports (moving function-scoped imports to module level, removing duplicate imports across files), run a targeted grep for the moved module name at the old locations to confirm no redundant copies survived. The Python import system silently ignores redundant imports — they won't cause errors, but they signal incomplete cleanup.

**Example**:
```bash
# After moving import random from inside request_chat() to module top:
grep -n "import random" app/routes_api.py
# Expect: 1 match (top-level import only)
# If 2nd match found at line 374 → dead import survived
```

**Why it matters**: Redundant imports are invisible to tests — they compile, they don't change behavior, and no linter catches them by default. They accumulate silently and erode code quality over time. A targeted grep after any import consolidation catches them immediately.

### 7.40 Cross-Platform Encoding Defense

**Context**: Test output on Windows PowerShell (CP1252 encoding) crashed on emoji characters. The same tests ran fine on macOS/Linux (UTF-8). Two-layer fix: replaced emoji with ASCII equivalents, added `sys.stdout.reconfigure` as fallback for remaining Unicode.

**Principle**: In cross-platform projects, avoid non-ASCII characters (emoji, fancy Unicode symbols) in CLI output and test logs. Use pure ASCII equivalents: `OK`/`?` instead of ✅/❌, `--` instead of decorative icons, `***` instead of fancy headers. As a second line of defense, add `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` at module level in all test files.

**Example**:
```python
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Use ASCII output markers:
print("OK test passed")
print("? test missing")
print("-- Starting tests")
```

**Why it matters**: A test suite that crashes on output encoding is worse than a failing test — it reports no results at all. Windows PowerShell defaults to CP1252, and emoji in test output is the #1 cause of encoding crashes on that platform. Preempting it with ASCII output + reconfigure fallback makes the test suite robust across all platforms.

### 7.41 Import-Before-Use Guard

**Context**: Added `sys.stdout.reconfigure(...)` to a test file but forgot to add `import sys` at the top — the test crashed with `NameError: name 'sys' is not defined`.

**Principle**: When adding a code block that references any module, verify the `import` statement exists at the top of the file as the very next action — before writing the usage code. "Add usage first, add import when it breaks" is the wrong order. The correct order is: identify the needed module, confirm or add the import, then write the usage code.

**Example**:
```python
# Step 1: Check/Add import (DO THIS FIRST)
import sys

# Step 2: Write usage
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
```

**Why it matters**: This catches a class of bug that produces a hard crash (NameError at module load time) before any test runs — zero results returned. Adding the import before the usage is a zero-cost habit that prevents complete test-suite failures.

---

## 8. Automation & Process Design

### 8.1 Permission Control
**Context**: From maintaining control during automated edits

**Principle**: Set `"ask"` for edit/write/bash in `.opencode/opencode.json`.

**Example**:
```json
{"agent":{"build":{"permission":{"edit":"ask","write":"ask","bash":"ask"}}}}
```

**Why it matters**: You approve every change.

### 8.2 Executable Sources of Truth
**Context**: From discovering doc/script conflicts during codebase investigation

**Principle**: When documentation conflicts with code, configs, scripts, or CI files, trust the executable source. Prose is aspirational — code is truth.

**Example**:
- README says "run `python app.py`" but `pyproject.toml` shows the entrypoint is `uv run python -m app` → trust the code and fix the docs
- ARCHITECTURE.md describes an old module structure that no longer exists in the actual file tree → update ARCHITECTURE.md to match the code

**Why it matters**: Outdated docs are worse than no docs — they actively mislead. Verifying against executable sources keeps documentation accurate.

### 8.3 Filename as Stable Key
**Context**: From designing auto-update matching for ARCHITECTURE.md

**Principle**: When auto-updating document entries, match by `` `path/file.ext` `` in the section heading as the stable key, not by sequential position or content heuristics. Filenames survive reordering, insertions, and lead line changes.

**Example**:
```markdown
### `app/routes.py` (HTTP Routes)   ← match on `app/routes.py`
Existing entry → update lead line
Missing entry → insert at correct position in ordering
```

**Why it matters**: Sequential position breaks when entries are added or reordered. Filename matching is idempotent.

### 8.4 Preserve Manual, Regenerate Auto
**Context**: From separating auto-extracted lead lines from manually authored bullet points in ARCHITECTURE.md

**Principle**: When automating document updates, clearly split content that has a verifiable source of truth (regenerate automatically) from content that requires human judgment (preserve untouched). Never regenerate what you can't verify against an authoritative source.

**Example**:
```markdown
### `app/routes.py` (HTTP Routes)
[lead line] ← auto-regenerated from source code # Description: header
[bullet points] ← preserved — no source-of-truth exists for these
```

**Why it matters**: Prevents automation from silently deleting human-authored nuance that can't be reconstructed from code alone.

### 8.5 Diff Logging for Automation
**Context**: From building safe auto-update workflows for documentation

**Principle**: Every automated content change should log its action with a clear tag: `[diff]` for content changes, `[REMOVED]` for deletions, `[MISSING]` for unfindable sources. This gives the user a reviewable audit trail and builds trust in the automation.

**Example**:
```
[diff] app/routes.py: 'Old lead line' → 'New lead line'
[REMOVED] app/obsolete.py — entry deleted (file no longer exists)
[MISSING] app/new_file.py has no Description: header — please add one
```

**Why it matters**: Silent automation erodes trust. Logged diffs let the user verify changes at a glance.

### 8.6 Cross-Language Extraction Pattern
**Context**: From extracting file descriptions across Python, JS, HTML in a single codebase

**Principle**: When you need to extract structured metadata from source files across multiple languages, design a uniform header format (`Description: ...`) and a single regex that works across all comment syntaxes. Avoid per-language extraction logic.

**Example**:
```regex
/Description: (.+)/   ← matches all of:
# Description: ...    (Python # comments)
// Description: ...   (JS // comments)
{# Description: ... #} (Jinja2 HTML comments)
"""Description: ...""" (Python docstrings)
```

**Why it matters**: One regex, one extraction function, no per-language maintenance. Simple, correct, and easy to extend to new file types.

### 8.7 Description Headers Go in Source Code Only

**Context**: From finding a `// Description:` comment in `opencode.json` (invalid JSON) and `refs/AGENT_SETUP.md` (not a source file).

**Principle**: File-level `Description:` headers belong only in source code files where the comment syntax is valid:
- `# Description:` → Python (`.py`)
- `// Description:` → TypeScript/TSX (`.ts`, `.tsx`)

Do NOT add description headers to:
- **Config files** — JSON, YAML, TOML don't universally support comments. A `// Description:` in a JSON file breaks parsing for any JSON parser that doesn't accept comments.
- **Documentation files** — Markdown (`.md`) files. Description headers are for auto-extraction into `ARCHITECTURE.md`; docs don't need to extract from themselves.
- **Generated/auto files** — `package.json`, `package-lock.json`, `tsconfig.json`, etc. Their purpose is self-evident from the filename.

**Why it matters**: Invalid JSON breaks tooling (`ConvertFrom-Json`, schema validators, linters). Cross-file consistency means the extraction regex only needs to look in Python and TS/TSX files, keeping the pattern simple and reliable.

### 8.8 One Verb Per Skill
**Context**: From separating implement-plan (TDD+code) from review-implementation (verify+sign-off) into two distinct skills

**Principle**: Each skill or component should do exactly one thing. If a skill description uses "and" to connect distinct responsibilities ("creates plans AND verifies them"), split it. One verb per skill prevents overlap, makes the pipeline obvious, and forces clear stage boundaries.

**Example**:
```
❌ implement-guide: "Code, test, debug, verify, and document"
✅ implement-plan: "TDD + code + flag changes"
✅ review-implementation: "Diff review + test/lint verification + sign-off"

The pipeline: analyze → grill → check → implement → review
Each step has exactly one verb.
```

**Why it matters**: No ambiguity about what each component owns. No overlap between adjacent stages. Clear routing on failure — you always know which door to knock on.

### 8.16 Independent Re-Verification
**Context**: From designing review-implementation to run tests/lint independently instead of trusting implement-plan's self-check

**Principle**: The reviewer runs the same checks independently and does NOT trust the implementer's "I already tested this." Run the full test suite, run lint, read every diff line, check every flag — from scratch. During review, only find problems — never fix them. Fixing belongs to the implementer.

**Example**:
```
implement-plan: codes, tests locally per batch, hands off "Ready for review"
review-implementation: ignores self-test results, re-runs everything from scratch
  - Read full diff → flag check ✅
  - Run all tests → pass ✅
  - Run lint → pass ✅
  - Verify criteria from plan file → met ✅
  - Sign off → "All checks pass. Implementation verified."
```

**Why it matters**: Self-verification is not verification. Independent re-runs catch what the implementer missed.

### 8.9 Stage Gate Pattern
**Context**: From the 5-skill pipeline with explicit go/no-go between every phase

**Principle**: Between every major phase, insert an explicit gate that must pass before the next phase starts. The gate asks "Are we ready to proceed?" and someone (user or automated check) must answer yes. No implicit progression. No phase approving its own output.

**Example**:
```
Phase                          Gate                                               Next phase
brainstorm-and-plan →             "Plan created. Shall I present it?"              → user approves → grill-and-refine
grill-and-refine →             "Grill complete. Here is the plan."              → user accepts   → check-plan-readiness
check-plan-readiness →         "All gates pass. Ready to implement?"            → user says go   → implement-plan
implement-plan →               "Ready for review."                              → user triggers  → review-implementation
review-implementation (1st) →  "All checks pass. Proceed to cleanup or done?"   → user chooses   → modularize-and-clean / DONE
modularize-and-clean →         "Cleanup complete. Change-log ready."            → user triggers  → review-implementation (2nd)
review-implementation (2nd) →  "All checks pass. Verified."                     → DONE
```

**Why it matters**: Prevents skipping stages. Every handoff requires explicit confirmation.

### 8.10 Batch by Logical Concern, Not Line Count
**Context**: From specifying batching rules for implement-plan

**Principle**: When splitting implementation into reviewable batches, define each batch by its logical completeness — one complete feature, one bug fix, one refactoring — not by lines of code. A batch is complete when its tests pass independently. Never split a single logical change across multiple batches just to make each batch "smaller."

**Example**:
```
✅ Good batch: "Add POST /api/users endpoint + its test" (3 files, ~60 lines)
✅ Good batch: "Fix null pointer in matchmaking + regression test" (2 files, ~15 lines)
❌ Bad batch: "Write test for /api/users + part 1 of the implementation" (incomplete, can't test)
❌ Bad batch: "Write lines 1-30 of the POST handler, continue in next batch" (artificial split)
```

**Why it matters**: Each batch is independently verifiable. Reviewers see a complete change, not a fragment. No "to be continued" across batches.

### 8.11 Persistent Decision Artifacts
**Context**: From saving plans as timestamped, numbered files for all downstream stages to consume

**Principle**: Save finalized decisions as persistent files — not just conversation context. Use a consistent naming scheme (PLAN_YYYY_MM_DD_XXX.md) with auto-incrementing numbers. Each downstream stage reads from the artifact file directly, not from memory or chat history. This makes decisions reviewable, auditable, and independent of conversation context. Move completed plans to `archive/` after successful review to keep `docs/` clean.

**Example**:
```
docs/
├── PLAN_2026_05_15_001.md   ← active (during implementation/review)
└── ... 
archive/
├── PLAN_2026_05_12_001.md   ← completed (after review)
└── ...
```
plans/
├── PLAN_2026_05_11_001.md   ← created by plan-readiness, consumed by implement-plan
└── .gitkeep

The file contains:
- Requirements, Solution, Implementation Plan
- Grill Outcomes (resolved dimensions)
- Readiness Gate Results (pass/fail per gate)

implement-plan opens the latest PLAN_*.md, never relies on "as we discussed earlier."
```

**Why it matters**: No hidden state between stages. A plan survives conversation context loss, and any stage can be re-run against the same artifact.

### 8.12 Dead Code Detection Protocol
**Context**: Cleanup passes removed dead imports and orphaned files, but some were removed without evidence or user approval — causing rework

**Principle**: Dead code must be detected with evidence (grep showing zero imports/references), assigned a recommendation (remove/keep/archive), and presented for user approval before removal. Never remove dead code silently.

**Example**:
```
[DEAD] frontend/src/hooks/useCountdown.ts — useCountdown — zero imports across codebase → Recommend: Remove
```

**Why it matters**: Not all unused code is safe to delete — some are public API exports, type-only re-exports, or intentionally kept for future use. Evidence-based approval prevents accidental deletions.

### 8.13 Batch Conflict Resolution
**Context**: During a cleanup pass, two approved candidates modified the same file sequentially — the second overwrote the first's changes silently

**Principle**: When multiple approved candidates touch the same file, sort them by dependency order before applying. If direct line overlap is unavoidable, present the conflict to the user — do NOT silently apply conflicting batches in sequence.

**Example**:
```
Conflict: [frontend/src/pages/ChatPage.tsx:80-95] — candidate A (extract timer logic)
+ candidate B (inline mock data) both modify this section
→ Recommend: merge into one batch, or apply A first and skip B
```

**Why it matters**: Silent sequential application of overlapping batches causes data loss. The second batch overwrites the first's changes with no warning.

### 8.14 Review-Implementation Expanded Checks
**Context**: review-implementation only checked diff + tests + lint — missed git status changes, test count drift, and production build failures

**Principle**: A full implementation review must include: (1) read diff + check flags, (2) check git status for unexpected files, (3) run all test suites with test count diff reporting, (4) run production build, (5) run lint/typecheck, (6) verify against plan document success criteria, (7) sign off or route. Non-CLEANUP flags found during a cleanup review route to implement-plan (not back to modularize-and-clean) — behavioral changes during cleanup mean the fix belongs in implementation, not restructuring.

**Example**:
```
Step 3 — Test count diff:
  test_app.py: 20 → 20 (no change) ✅
  vitest: 83 → 83 (no change) ✅
  test_js_modules.py: 45 → 45 (no change) ✅
```

**Why it matters**: A narrow review (diff + tests only) misses production regressions, scope creep, and broken builds. The expanded checklist catches all failure modes before sign-off.

### 8.15 Non-Interactive Execution
**Context**: From running agent-driven commands in headless CI and non-interactive shell environments

**Principle**: All commands must run without stdin prompts. If a command requires user input (e.g., confirmation prompts, package install questions), use flags to suppress them (e.g., `--yes`, `-y`, `--non-interactive`) or pre-configure via environment variables. Never assume an interactive terminal is available.

**Example**:
- `npm install --yes` or set `npm config set yes true`
- `uv sync` (non-interactive by default)
- `git commit -m "msg"` (never `git commit` without `-m`)

**Why it matters**: A command that blocks waiting for stdin will hang indefinitely in a headless or agent-driven session, causing timeouts and false failures.

### 8.17 Orchestrator Pattern for Convergent Pipeline Paths
**Context**: The agentic workflow had 3 exit paths from review-implementation (modularize-and-clean, improve-architecture, update-docs) — all needing documentation sync as their final step before git push

**Principle**: When a workflow has multiple exit paths that all converge at the same downstream step, introduce an orchestrator as the single entry point rather than duplicating logic across each route. The orchestrator owns the routing decision and produces a single handoff. This prevents scattered routing logic, makes the pipeline self-documenting, and ensures consistent pre-flight checks.

**Example**:
```
review-implementation (1st pass)
    ├──→ modularize-and-clean → review-implementation (clean up) → update-docs
    ├──→ improve-architecture → review-implementation (arch) → update-docs
    └──→ update-docs (skip cleanup/arch, proceed directly)

update-docs: single orchestrator, routes to push-to-git
```

**Why it matters**: Without an orchestrator, each branch independently decides when and how to trigger the shared step — leading to inconsistent setups, duplicated cleanup logic, and missed edge cases.

### 8.18 Granular Edits Within Batches
**Context**: From skill restructuring where large multi-change diffs were hard to review independently

**Principle**: Within a change batch, apply changes one logical unit at a time. Each unit should touch one function, one section, or one test case — never multiple unrelated concerns in a single operation. Each unit produces one independently reviewable diff.

**Example**: Adding 3 new API endpoints requires 3 separate edit calls (one per endpoint + one per test) instead of one large edit that rewrites the file in its entirety.

**Why it matters**: Each change is independently reviewable and approvable. No "wall of diffs" that must be approved wholesale — the reviewer can accept one unit and request changes on another.

### 8.19 Step 0 Convention
**Context**: From adding guardrails to a per-batch workflow without renumbering existing numbered steps

**Principle**: Use "Step 0" for widely-applicable pre-conditions that apply across all workflow entries. This keeps existing step numbering (1, 2, 3…) unchanged while inserting universal guardrails before the main sequence begins.

**Example**: A deployment checklist "1. Build → 2. Test → 3. Deploy" gets Step 0: "Verify all environment variables are set." No steps need renumbering.

**Why it matters**: Adding guardrails does not require renumbering existing steps. The convention signals "this condition applies to everything that follows."

### 8.20 Consistent Process Template
**Context**: From restructuring all 9 workflow skills for predictable section ordering

**Principle**: Every process or workflow document should follow the same section template. This creates predictable navigation — readers know exactly where to find purpose, boundaries, inputs/outputs, prerequisites, step-by-step instructions, verification criteria, and handoff protocol.

**Example**: Skill files follow: Description → Boundaries → Pipeline Position (I/O table) → Documents to Read → Workflow (phased) → General Methodology → Hand-off → Outputs & Triggers. Every skill uses the same sections in the same order.

**Why it matters**: Predictable structure saves time. No "is there a dependencies section?" guesswork across documents.

### 8.21 Cross-Phase Deduplication
**Context**: From finding the same rule duplicated across 5 independent skill files — the flag format `[PREFIX]: short_reason — what/why` appeared in every one

**Principle**: When the same rule appears in multiple instruction files, extract it to a shared governance document and replace duplicates with cross-references. The canonical copy is the only one maintained; each file keeps only its phase-specific rules.

**Example**: Flag format was in 5 skills. Extracted to AGENTS.md as the single canonical source. Each skill replaced its flag table with "[See Flag Annotation Convention in AGENTS.md](../AGENTS.md)." One update to AGENTS.md propagates to all consumers.

**Why it matters**: One source of truth. No drift across copied rules. Update one location, all consumers benefit.

### 8.22 Narrow-Then-Search Pipeline
**Context**: From evolving the Three-Tier Code Exploration Classification (graphify → cocoindex → ast-grep) into a formal pipeline with I/O contracts, tiered classification rules, and completeness safeguards

**Principle**: For complex queries, run a 3-stage sequential pipeline instead of picking one tool. Stage 1 (graphify) narrows scope via 3 query variations × 2 sub-graphs. Stage 2 (cocoindex-code) searches within that scope by intent. Stage 3 (ast-grep) verifies structural patterns. For Tier 1 (Tiny) tasks with known exact files, skip the pipeline and use grep or a single read. For Tier 2 (Moderate), use 1-2 stages (cocoindex → read). For Tier 3 (Complex), run full 3-stage pipeline.

**I/O Contracts:**

| Stage | Input | Action | Output |
|-------|-------|--------|--------|
| 1 — Scope | User query | 3 phrases × 2 sub-graphs (code + doc), community expansion if ≤4 files | `scope: [...], communities: [...], confidence: high/medium/low` |
| 2 — Search | Scope from Stage 1 + refined query | Semantic search with `paths=scope` | `chunks: [(file, line, content, score)], uncovered_aspects: [...]` |
| 3 — Verify | Specific pattern from Stage 2 | Structural match in identified files | `exact_matches: [(file, line, pattern)], verified_files: [...]` |

**Three-Tier Table:**

| Tier | Scope | Tools | Example |
|------|-------|-------|---------|
| Tier 1 — Tiny | 1-2 exact files known | grep/Read | "Fix typo in line 42 of matchmaking.py" → read + edit |
| Tier 2 — Moderate | Known area, exact files unclear | graphify + cocoindex | "How is email validated?" → cocoindex + ast-grep |
| Tier 3 — Complex | Unknown scope, multiple communities | Full 3-stage pipeline | "How does matchmaking work?" → graphify × 6 queries → cocoindex → ast-grep |

**Example — full pipeline trace:**
```
Query: "How does matchmaking work?"
Stage 1: graphify query "match queue" (code) + "match flow" (doc) + "user pairing" (code) → scope: [matchmaking.py, connection_manager.py, state.py, routes.py], confidence: high
Stage 2: cocoindex-code search with paths=[matchmaking.py, ...] → chunks: find_match(), waiting_queue, _try_match()
Stage 3: ast-grep search for "def find_match($$$)" → exact definition at matchmaking.py:42
→ Read targeted code: matchmaking.py:42-85
```

**Why it matters**: The pipeline catches what single-tool searches miss. Graphify narrows scope before cocoindex searches, preventing token waste on 126+ files. Ast-grep verifies structural correctness that semantic search can't guarantee. The tier classification prevents over-engineering: Tier 1 costs ~1k tokens, Tier 2 ~5k, Tier 3 ~10k+.

### 8.23 Design-Spec-to-Config Bridge
**Context**: The frontend-design skill produces a design spec (colors, typography, spacing, motion) but neither frontend-design nor shadcn explicitly owned translating those tokens into `tailwind.config.js` and `global.css` — the bridge step existed only as implicit agent knowledge

**Principle**: Every design spec element must explicitly map to its implementation target before coding begins. Define a Design Token Mapping table in the spec that shows the exact hex/value for each token and where it goes: `tailwind.config.js` `theme.extend.{colors,fontFamily,borderRadius,spacing,boxShadow,maxWidth}` for config tokens, CSS variables in `global.css` for semantic token aliases. The implementation skill reads this table directly — no ambiguity about which value goes where.

**Example**:
```
Spec element           → Implementation target               → Example value
Color palette         → tailwind.config.js colors            → background: '#FDFBF7'
Font family           → tailwind.config.js fontFamily        → sora: ['Sora', 'sans-serif']
Border radius (card)  → tailwind.config.js borderRadius      → card: '16px'
Semantic alias        → CSS variable in global.css           → --primary: theme('colors.sage')
```

**Why it matters**: Without an explicit mapping, the implementation skill must reinterpret the spec — introducing ambiguity and potential drift between what was designed and what was built.

### 8.24 question Tool Mandate for All User Interaction
**Context**: From enforcing consistent user interaction across all phase skills — previously some skills used raw "ask before proceeding" text prompts while others used the `question` tool

**Principle**: The built-in `question` tool with clickable selectable options (`label` + `description`, free-form fallback) is the sole mechanism for all agent-to-user questions and decision points. Raw text prompts ("ask before proceeding"), unformatted "y/n" questions, and bullet-option lists in prose are prohibited. Each decision point is walked through one at a time — never present multiple items in a single message.

**Example**:
```
question(
  questions=[{
    header: "Interaction style",
    question: "How should the agent ask questions?",
    options: [
      {label: "question tool", description: "Clickable selectable options"},
      {label: "free-form text", description: "Raw text prompts"}
    ]
  }]
)
```

**Why it matters**: The `question` tool provides structured, clickable options that eliminate ambiguity. By mandating `label` + `description` fields and a free-form "Type your own answer" fallback, every user choice is clearly framed while remaining open to unexpected input. Walking through decisions one at a time prevents cognitive overload.

**CRITICAL LIMITATION — Never `question` for mode transitions:** The `question` tool creates a modal widget that prevents the user from toggling Plan↔Build mode. While `question` is active, the user physically cannot switch modes. This produces a dead end: they click "proceed" but edits are denied (plan mode). Therefore, mode transition prompts must **never** use `question` — only plain text:
- End of plan: "Plan ready. Switch to build mode and I'll execute."
- End of build: "Build complete. Switch to plan mode for review."
- Mode-switch requests are also forbidden within `question` (e.g., asking "ready for review?" at end of build).

**Why the carve-out exists**: The `question` tool is designed for decisions *within the current mode* where the user can act on the outcome. Mode transitions are a meta-operation the user performs outside the chat UI — they cannot be embedded in a question widget.

---

## 9. Version Control

### 9.1 Commit Discipline
**Context**: From recovering lost work

**Principle**: .gitignore binaries, pin versions, descriptive commits.

**Example**:
```bash
git commit -m "Fix: Resolve 404 on user room"
# Pin: fastapi==0.115.0 (never fastapi without version)
```

**Why it matters**: Reproducible builds, clean history.

### 9.2 Commit by Logical Group
**Context**: From designing push-to-git skill workflow

**Principle**: Group changes into commits by logical concern, not by file count or directory boundary. A commit should tell one complete story — one feature, one fix, one refactoring. Files from multiple directories can belong to the same commit if they serve the same purpose.

**Example**:
```
✅ One commit: "Add input validation to matchmaking + regression tests"
   (2 dirs: app/ + tests/, 1 logical concern)
❌ Bad: "Update app files" + "Update test files" 
   (2 commits for 1 logical change — fragments the story)
```

**Why it matters**: Logical commits are reviewable and revertible. File-boundary commits fragment the story.

### 9.3 Push Per Commit
**Context**: From refining push-to-git skill during session (original design batched pushes)

**Principle**: Push after every commit, not after a batch of commits. If a push fails, only one commit is affected and needs rework. The remote stays in sync after each logical change.

**Example**:
```
✅ Per-commit push: commit → push → commit → push → commit → push
❌ Batched push: commit → commit → commit → push (one failure blocks all 3)
```

**Why it matters**: Isolates risk. A failed push only blocks one commit, not a whole batch.

### 9.4 Auto-Generate Commit Messages from Change Type
**Context**: From building commit message generation in push-to-git skill

**Principle**: Generate commit messages based on the nature of the changes. New files → "Create", modified only → "Update", format-only additions → "Add ... to all ...", mixed modifications and renames → "Revise". Always present the message for user editing before committing.

**Example**:
```
Change type → Generated prefix
New skill file → "Create push-to-git skill: logical grouping..."
Description headers → "Add Description: headers to all Python source files"
Modified existing skills → "Update doc maintenance skills: agents, architecture..."
Renamed + modified → "Revise core skill pipeline: analyze, grill, readiness..."
```

**Why it matters**: Consistent, descriptive messages with less effort. User approval prevents auto-generated nonsense from polluting history.

### 9.5 Detect Renames via Deleted + New Untracked Pairs
**Context**: From handling implementation-guide → implement-plan rename in push-to-git

**Principle**: When a file or directory is renamed outside of git, it appears as a deletion + an untracked addition. To preserve rename history, detect these pairs by matching old and new paths, and stage both in the same commit so git can detect the rename via content similarity.

**Example**:
```
git status shows:
  deleted: .opencode/skills/old-name/SKILL.md
  untracked: .opencode/skills/new-name/SKILL.md

→ Stage both in one commit
→ Git detects: renamed old-name/SKILL.md → new-name/SKILL.md
```

**Why it matters**: Preserves rename history. Without pairing, git shows a deletion and a new file — the connection is lost and blame history breaks.

---

## 10. Code Review Checklist
**Context**: From shipping bugs to production

**Principle**: Check: syntax, imports, tests, errors, hardcoded values, docs.

**Example**:
```bash
uv run python -m py_compile          # Syntax
uv run pytest tests/ -v              # Tests
```

**Why it matters**: Catch issues before merge.

---

## 11. Debugging Process
**Context**: From fixing 404 on `/api/users/xxx/room`

**Principle**: Identify → Isolate → Read → Plan → Apply → Verify → Document.

**Example**: Error: 404 → Cause: state cleared → Fix: restore from DB → Verify: test.

**Why it matters**: Systematic approach, no guesswork.

## 12. Documentation Sync

### 12.1 Per-Batch Approval for Documentation Changes
**Context**: From update-docs phase applying all changes at once without per-edit approval — user reverted everything

**Principle**: When making documentation changes, present proposed edits one batch at a time with exact old→new diff. Get user sign-off before applying. Never batch all doc changes into a single unapproved update. This applies even when the changes are well-scoped and the user has already agreed in principle.

**Example**:
```
Batch 1: README.md (5 surgical edits) → show diff → user approves → apply → verify
Batch 2: SPECIFICATIONS.md (2 edits) → show diff → user approves → apply → verify
```

**Why it matters**: Documentation changes affect the developer/agent interface — even small wording changes can alter how tools are used. Per-batch approval prevents the "everything changed at once" surprise that breaks trust.

## 13. vLLM

Consolidated in [`docs/BATCH FILE AUTO SERVER START PLAN.md`](docs/BATCH FILE AUTO SERVER START PLAN.md) — single source of truth for all vLLM findings: memory budget formula, EngineCore crash debugging, CUDA context overhead, tuning heuristics, FlashInfer JIT, ZMQ port conflicts, and server debugging.

## Key Takeaways
1. **Modular > Monolithic**
2. **Config > Hardcode**
3. **Test Continuously**
4. **Document as You Go**
5. **Distinct Docs** — one purpose per document, defined by the questions it answers
6. **Key Differentiator** — every doc needs a bold one-line uniqueness statement
7. **Boundary Tensions** — when docs overlap, document the resolution
8. **Quality Gates** — filter content before including it (litmus test, executable truth, conciseness, ownership filter)
9. **Inline Constraints** — don't separate "what" from "how"; keep formatting rules with their items
10. **Merge Verification** — one comprehensive verify step, not separate pre/post checklists
11. **Recover State** — always handle in-memory state recovery
12. **Verify Immediately** — one change, one verification
13. **Update Practices** — use `update-best-practices-md` skill after every significant session
14. **Source Comments > Doc Duplication** — write `Description:` headers in code as canonical source; auto-extract into docs
15. **Auto Headline, Manual Detail** — auto-generate lead lines from code, manually preserve bullet points
16. **Logical > Alphabetical Ordering** — order entries by dependency flow (dependency → utility → user), not alphabetically
17. **Standalone > Nested for Regenerated Sections** — keep cross-cutting content in standalone sections, not nested inside auto-generated blocks
18. **Grill Gaps Before Acting** — test every template-vs-implementation gap against 4 questions before deciding to act
19. **Filename Keys for Auto-Updates** — match by `path/file.ext` in section headings, not by position or content
20. **Preserve Manual, Regenerate Auto** — only regenerate content with a verifiable source of truth; preserve the rest
21. **Log All Automated Diffs** — tag every automated change as `[diff]`, `[REMOVED]`, or `[MISSING]` for auditability
22. **One Regex Across Languages** — use a single uniform header format + regex across Python, JS, HTML instead of per-language extraction
23. **Merge via Mode Prop** — merge duplicate UI components with a mode/variant prop instead of maintaining separate views
24. **Rebuild Dist for Production** — after any frontend change, rebuild `dist/` before running the production server (dev server serves from memory)
25. **Shared Context for Persistence** — put cross-page resources (WebSocket) in a shared context; pages connect on mount without explicit disconnect
26. **Functional Updater for Timers** — always use `(prev) => prev +/- 1` in setInterval to avoid stale closures with fake/async timers
23. **Docs-First Analysis** — consult docs before raw codebase parsing; spot-check against 1-2 files for accuracy
24. **Structured Walkthrough** — probe one dimension at a time with options; confirm skippable items upfront
25. **Presence Check Over Re-Probe** — verify documents check coverage, don't re-analyze from scratch
26. **Triage Routing** — minor gaps fix in-place, significant gaps route to owning stage
27. **One Verb Per Skill** — each component does exactly one thing; no "and" in descriptions
28. **Independent Re-Verification** — reviewer re-runs all checks from scratch; never trusts self-checks
29. **Stage Gate Pattern** — explicit go/no-go between every phase
30. **Batch by Logical Concern** — one complete feature per batch, not measured by lines of code
31. **Persistent Decision Artifacts** — save finalized plans as timestamped, numbered files for all downstream stages
32. **Commit by Logical Group** — group by concern, not by file count or directory; one story per commit
33. **Push Per Commit** — push after each commit, not batch; isolate failure risk
34. **Auto-Generate Commit Messages** — generate from change type, present for editing, never push unapproved
35. **Detect Renames via Deleted + New Pairs** — pair deleted and untracked files with similar paths to preserve git rename history
36. **127.0.0.1 for Browser Access** — bind to `127.0.0.1` for local dev, not `0.0.0.0` which browsers can't navigate to
37. **WebSocket Accept Once** — call `accept()` in the route handler, not in nested connection managers
38. **TestClient Over Live Server** — use in-process TestClient for integration tests instead of a real server process
39. **Preserve File Description Comments** — never delete the `# Description:` block; it's the canonical source for docs
40. **Windows Shell Quoting** — write complex Python to `.py` files instead of inline PowerShell strings
41. **Queue Filter Direction** — matchmaking queues should look for users IN the queue, not exclude them
42. **Verify Presence, Not Absence** — Verify checks what the document contains (positive correctness), not absence checks which belong upstream in routing rules
43. **Root Pattern Extraction** — extract root causes not symptoms; guard by asking if a developer on an unrelated project would find it valuable
44. **TDD Tests Are Permanent** — tests written during TDD live in `tests/` forever as regression tests; only skip for truly non-testable changes
45. **Single Canonical Location** — each artifact type lives in exactly one directory; one step creates, all others read
46. **Sequential Numbering for Plan Files** — numbers are globally unique across all directories; no reuse
47. **Skill Rename Protocol** — create dir → copy → delete old → update name → update all refs; verify zero stale refs
48. **Workflow Handoff with Outputs & Triggers + Hand-off Checklist** — every stage defines Output + Hand-off checklist + Exit Declaration + Next Step; verify before signaling
49. **File Descriptions Across All Languages** — every file gets a `filename + Description:` header matching its comment syntax; canonical source for ARCHITECTURE.md
50. **Test References in Same Batch** — rename, signature, or behavioral change updates all test references in the same batch; source and tests are a single unit
51. **Full Review Pipeline** — review must include git status, test count diff, production build, exact lint commands, and escalation routing for non-CLEANUP flags
52. **Skill Audit After Restructure** — update owning skills in same batch as document content moves; a stale skill regenerates old boundaries
53. **Exhaustive Section Mapping** — compare doc↔skill by reading both end-to-end with a two-column table, not by section-heading inference
54. **Stale Pattern Audit After Migration** — grep skill files broadly for old technology names after any framework migration
55. **Surgical Edits Over Rewrites** — replace targeted text, not whole files, when updating instruction documents
56. **Three-Layer Verification** — grep removals, grep additions, read-test critical sections — each layer catches what others miss
57. **Consistency Pass** — after cross-cutting changes, run a dedicated consistency pass across all affected files

## 14. GPU Subprocess Lifecycle

### 14.1 Batch-File Boundary for GPU Subprocess Isolation
**Context**: vLLM engine crashed with `No available memory for the cache blocks` when spawned as a direct child of a pipeline process that had imported `torch` and loaded/unloaded 4 models. The same subprocess command worked when started from a separate terminal or batch file.

**Principle**: On Windows WDDM, spawning a GPU-heavy subprocess (vLLM, training job) as a direct child of a process with an active CUDA context reduces the child's visible GPU memory budget. Insert an intermediate shell boundary (batch file, `cmd.exe`) to fully isolate the child's CUDA context view. This applies to any GPU subprocess that shows memory errors despite `nvidia-smi` reporting sufficient free VRAM.

**Example**:
```python
# ❌ Direct subprocess — inherits parent's CUDA context, reduced GPU budget
proc = subprocess.Popen(cmd, env=env)

# ✅ Batch-file boundary — clean CUDA context
proc = subprocess.Popen(["start_vllm.bat"], env=env)
```
The batch file (`start_vllm.bat`) launches a fresh Python process via `start "" /B python -m vllm.entrypoints.openai.api_server ...` — `cmd.exe` is the immediate child, not the Python process.

**Why it matters**: The direct-subprocess crash is deterministic on Windows WDDM (16 GiB GPU) when the parent has imported torch. The batch-file boundary is a zero-cost fix that resolves it entirely.

### 14.2 Cross-Process Shared Activity File for Subprocess Lifecycle
**Context**: vLLM server needed to survive individual Python process exits and be shared across multiple orchestrator processes. The idle watchdog (7-min timeout) also needed cross-process coordination — a process-local `_last_activity_time` doesn't work when different processes manage the same server.

**Principle**: When a long-lived subprocess (server, worker pool) is shared across multiple parent processes, use a file in `tempfile.gettempdir()/project_name/` as the cross-process coordination primitive. Each process writes a timestamp on activity, the watchdog reads the shared file instead of local state, and any process can detect stale orphans. Use last-writer-wins for concurrent writes (catch-and-ignore errors).

**Example**:
```python
import os
import tempfile
import time

_ACTIVITY_DIR = os.path.join(tempfile.gettempdir(), "taskai")
_ACTIVITY_FILE = os.path.join(_ACTIVITY_DIR, "server_last_activity.txt")

def _write_activity_timestamp() -> None:
    os.makedirs(_ACTIVITY_DIR, exist_ok=True)
    try:
        with open(_ACTIVITY_FILE, "w") as f:
            f.write(str(time.time()))
    except OSError:
        pass  # last-writer-wins

def _read_activity_timestamp() -> float:
    try:
        with open(_ACTIVITY_FILE) as f:
            return float(f.read().strip())
    except (OSError, ValueError):
        return 0.0
```

**Why it matters**: Process-local state cannot coordinate across OS process boundaries. Tempfiles are per-user, survive crashes, and need no cleanup — they're naturally ephemeral. The pattern extends to any multi-process shared resource lifecycle.

### 14.3 Port-Based Process Killing with Self-Kill Guard
**Context**: vLLM orphan detection needed to kill processes holding port 8000 before starting a new server. `netstat -ano` finds the PID, `taskkill /F /PID` kills it — but the guard against killing the current process's own PID is critical.

**Principle**: When implementing port-based process cleanup, always include a `pid == os.getpid()` guard to prevent self-termination. The generic pattern: `netstat -ano` → parse `LISTENING` lines for target port → extract PID → skip own PID → `taskkill /F /PID`. This is a fallback when the managed process reference (`subprocess.Popen` object) is lost or stale.

**Example**:
```python
import os
import subprocess

_PORT = 8000

def _kill_process_on_port(port: int) -> None:
    result = subprocess.run(
        ["netstat", "-ano"], capture_output=True, text=True, timeout=10
    )
    for line in result.stdout.splitlines():
        if "LISTENING" in line and f"127.0.0.1:{port}" in line:
            pid = int(line.strip().split()[-1])
            if pid == os.getpid():
                continue  # ← CRITICAL: don't self-terminate
            subprocess.run(
                ["taskkill", "/F", "/PID", str(pid)],
                capture_output=True, timeout=5,
            )
```

**Why it matters**: Without the self-kill guard, a health check that connects to the port then runs cleanup could kill the checking process itself. Port-based kill is inherently imprecise — the guard limits the blast radius.

### 14.4 Double-Check Locking with `_starting` Guard for Concurrent Auto-Start
**Context**: `ensure_vllm_server()` needed to start vLLM on demand from multiple threads (and eventually multiple processes). Without a `_starting` guard, concurrent entries cause a thrashing cascade — each thread kills the other's booting server via orphan cleanup.

**Principle**: When implementing auto-start for a shared resource, use a `_starting` boolean inside the same lock acquisition as the health check. The pattern: `lock → check healthy → check _starting → set _starting = True → unlock → start → lock → set _starting = False`. Never release the lock between checking for an existing resource and setting the starting flag — this creates a TOCTOU race.

**Example**:
```python
_starting: bool = False
_lock = threading.RLock()

def ensure_server():
    global _starting
    with _lock:
        if _is_healthy():
            return
        if _starting:
            return
        _starting = True
    try:
        start_server()  # Outside lock — startup may take minutes
    finally:
        with _lock:
            _starting = False
```

**Why it matters**: Two patterns fail: (1) releasing the lock between checks creates a TOCTOU window where a healthy server gets killed; (2) no `_starting` flag at all causes all concurrent callers to start simultaneously, each killing the previous one's process. The double-check lock + flag pattern is the minimal correct solution.

### 14.5 Stderr Streaming During Server Wait Loops
**Context**: vLLM startup takes 60-600s. Without periodic stderr reads, a timeout produces zero diagnostics — the debugger sees "server did not become ready within 300s" with no clue why.

**Principle**: In any wait-for-ready loop (server startup, test runner, batch job), periodically read the subprocess's stderr file every N attempts (e.g., every 60s) and log the progressively accumulated output. This transforms a silent timeout into a real-time diagnostic window showing model loading progress, tokenizer errors, or memory warnings.

**Example**:
```python
def _wait_for_server(proc, stderr_path):
    for attempt in range(1, max_retries + 1):
        if proc.poll() is not None:
            raise RuntimeError(f"Server exited with code {ret}")
        if _is_healthy():
            return
        if attempt % 12 == 0:  # Every 60s with 5s delay
            stderr = _read_stderr(stderr_path)
            logger.info(f"Still waiting... stderr so far:\n{stderr[:2000]}")
        time.sleep(5)
```

**Why it matters**: Without progressive stderr logging, diagnosing a failed server start requires: (1) noticing the timeout, (2) finding the stderr temp file before cleanup, (3) reading it. With streaming, the diagnostics arrive in the log automatically before the timeout fires. Highest-ROI debugging investment for server startup code.

### 14.6 CUDA Cache Clearing Before GPU Subprocess Spawn
**Context**: Starting vLLM as a subprocess from a parent that had loaded/unloaded multiple GPU models on the same GPU. Residual cached allocations in the parent process reduce the child's available GPU memory budget on Windows WDDM.

**Principle**: Before spawning a GPU-intensive subprocess from a CUDA-using parent, call `gc.collect()` followed by `torch.cuda.empty_cache()` to free residual GPU memory. This is especially important on Windows WDDM where the parent's CUDA context affects the child's visible memory budget. This is a best-effort operation — wrap in try/except since torch may not be imported in all code paths.

**Example**:
```python
def _free_parent_gpu_memory():
    """Try to free GPU memory in parent before spawning child subprocess."""
    try:
        import gc
        gc.collect()
        import torch
        torch.cuda.empty_cache()
    except Exception:
        pass
```

**Why it matters**: On Windows WDDM, the parent's torch state is not fully cleaned by model unload alone. Residual cached allocations occupy GPU pages visible to the child. A garbage collection + CUDA cache clear before spawn maximizes the child's available budget. On Linux (CUDA Linux), this matters less because subprocesses have independent GPU memory views.
58. **Hand-off Checklist** — every stage needs a verifiable pre-exit checklist before declaring completion
59. **Orchestrator for Convergent Paths** — when multiple pipeline paths share a final step, insert an orchestrator as single entry point
60. **Granular Edits Within Batches** — one logical unit per edit call; each produces an independently reviewable diff
61. **Step 0 Convention** — universal pre-conditions go at step 0, not mixed into the main step sequence
62. **Consistent Process Template** — every workflow document follows the same section template for predictable navigation
63. **Cross-Phase Deduplication** — extract duplicated rules to a shared governance document; replace copies with cross-references
64. **Three-Tier Classification** — Classify tasks before exploring: Tier 1 (Tiny, known files) / Tier 2 (Moderate, known area) / Tier 3 (Complex, unknown scope). Each tier has a defined tool set and completeness safeguard.
65. **Test Health Audit** — periodically audit tests for stale file paths, misleading comments, and coverage gaps; pass/fail alone isn't enough
66. **Design-Spec-to-Config Bridge** — every design spec token maps explicitly to its implementation target (tailwind.config.js, CSS variables); no ambiguity
67. **File Existence Checks in Tests** — update hardcoded file lists in the same batch as file changes, or use glob-based discovery instead
68. **question Tool Mandate** — the built-in `question` tool is the sole mechanism for agent-to-user questions; no raw text prompts, unformatted "y/n", or prose option lists
69. **Edge Case First Testing** — enumerate boundary conditions before implementing body; write one edge-case test per new feature
70. **Structured Audit Over Vague Assessment** — replace subjective audit requests with concrete, enumerable checks; each must be yes/no answerable
71. **Happy-Path-Only Coverage as Anti-Pattern** — flag test suites with zero edge-case tests; require at least one per feature
72. **Dependency Audit Protocol** — evaluate each dependency against 5 checks (justification, size, transitive damage, version pinning, duplicate risk) before adding
73. **Production-Gated Security** — gate security features behind env vars (`ENV=production`); never comment out
74. **Post-Consolidation Import Audit** — after consolidating imports, grep the moved module name at old locations for surviving duplicates
75. **Cross-Platform Encoding Defense** — avoid emoji in cross-platform test output; add `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` as fallback
76. **Import-Before-Use Guard** — verify the import exists before writing the usage code, not after
