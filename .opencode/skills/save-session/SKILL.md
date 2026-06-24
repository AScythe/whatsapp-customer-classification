---
name: save-session
description: 'Save the current session conversation (excluding thinking blocks) to a formatted timeline file in docs/sessions/. Invoked as a sub-step from implement-plan and review-implementation. Use after any write-phase skill, or when the user says "save session" or similar.'
---

## What I do

- Save the current user↔agent conversation to `docs/sessions/SESSION_YYYY_MM_DD_NNN.md`
- Exclude `thinking` blocks and system compaction summaries
- Truncate tool execution results to ~10 lines
- Use incremental append via a `.SESSION_*.meta` tracking file
- Maintain max 3 session files — oldest auto-archived to `archive/sessions/`
- Provide a **Session Continuity Check** step for re-reading session header on context recovery

## Boundaries

- **Archival with re-read support** — session files are saved for context restoration via the Session Continuity Check (reads header only, ~200 tokens)
- **Non-destructive** — never modifies source code, plan files, or skill files
- **Blocking on failure** — reports error and stops if save fails (but retryable/idempotent)

## Workflow

### Step 1: Create Directory

Ensure `docs/sessions/` exists. Create it if not:

```powershell
New-Item -ItemType Directory -Path "docs/sessions" -Force
```

Also ensure `archive/sessions/` exists (for archival rotation):

```powershell
New-Item -ItemType Directory -Path "archive/sessions" -Force
```

### Step 2: Determine Session File

Scan both `docs/sessions/` and `archive/sessions/` for the highest global NNN across all `SESSION_*.md` files.

**How to find highest NNN:**

```powershell
# List all SESSION_*.md files in both directories
$sessions = @(Get-ChildItem -Path "docs/sessions" -Filter "SESSION_*.md" -Name)
$archived = @(Get-ChildItem -Path "archive/sessions" -Filter "SESSION_*.md" -Name)
$all = $sessions + $archived
$highest = 0
foreach ($f in $all) {
    if ($f -match 'SESSION_\d{4}_\d{2}_\d{2}_(\d{3})\.md$') {
        $num = [int]$matches[1]
        if ($num -gt $highest) { $highest = $num }
    }
}
$nextNnn = "{0:D3}" -f ($highest + 1)
```

### Step 3: Gate — New File or Continue

Use the `question` tool to ask the user. Default: new plan = new file.

**If invoked from check-plan-readiness (new plan just finalized):**
- Default suggestion: new session file
- Ask: "**Start a new session file for this plan, or continue with the current one?**"
- Options: `"New file"`, `"Continue current"`, `"Cancel save"`

**If invoked from review-implementation (implementation just verified):**
- Check if `docs/sessions/` already has files
- If yes: ask "**Continue appending to current session file or start fresh?**"
- If no: treat as new file automatically

### Step 4: Read and Filter Conversation

Scan the current conversation context (all messages in the conversation). For each message:

**Include:**
- User messages (the user's question/input)
- Agent text responses (your natural language output)
- Tool call sections (truncated — see Step 5 formatting)

**Exclude:**
- `thinking` blocks — everything between `thinking` and the matching close `thinking`
- System compaction/summary messages (OpenCode's automatic context compression summaries)
- Any system-level status messages that aren't part of the user↔agent dialogue

**Detection approach:**
- Look for `thinking` markers in the raw message content. Remove text between `thinking` and the matching closing tag.
- System compaction messages typically begin with predictable markers (e.g., `[System:`, `*Compacted*`, summary blocks). Detect and skip these.

### Step 5: Format Timeline

**Generate a YAML frontmatter header** for every session file:

```yaml
---
session: <NNN>
date: YYYY-MM-DD
phase: <phase_at_save>
goal: <one-line goal>
plan: <PLAN_*.md> [omit if no active plan]
files: [list key files touched, omit if empty]
outcome: <what was achieved> [omit if first save]
next_step: <what to do next>
blockers: <known blockers> [omit if none]
---
```

Required: `session`, `date`, `phase`, `goal`, `next_step`. Conditional (omit if not applicable): `plan`, `files`, `outcome`, `blockers`.

- **phase**: one of `check-plan-readiness`, `implement-plan`, `review-implementation`, `modularize-and-clean`, `improve-architecture`
- **files**: detect via `git diff --name-only` against the most recent commit or plan baseline. Omit if git not available or no changed files.
- **outcome**: omit for first save in a session; for subsequent appends, summarize what was accomplished since last save.

The header is placed at the very top of the file, before the timeline.

Format each exchange as:

```markdown
## User YYYY-MM-DD HH:MM

<user message text>

## Assistant YYYY-MM-DD HH:MM

<agent response text>

[Tool: <tool name>] <truncated result — max ~10 lines>
[Tool: <tool name>] <truncated result — max ~10 lines>
```

**Truncation rules:**
- Tool output: show tool name and first 10 lines. Append `...` if truncated.
- File reads: show filename and first 10 lines.
- CLI output: show command and first 10 lines of stdout.
- grep/search results: show pattern and first 10 matches.
- If a section has no tool calls, omit the `[Tool: ...]` lines entirely.

### Step 6: Write or Append

**For new file (Step 3 chose "New file"):**
- Write the YAML frontmatter header followed by the full formatted conversation to `docs/sessions/SESSION_YYYY_MM_DD_<NNN>.md`
- Create companion meta file: `docs/sessions/.SESSION_YYYY_MM_DD_<NNN>.meta`
- Meta file content (JSON):
  ```json
  {"last_saved_at": "YYYY-MM-DDTHH:MM:SSZ", "message_count": <N>}
  ```

**For append (Step 3 chose "Continue current"):**
- Find the most recent session file in `docs/sessions/` (highest NNN)
- Read its companion `.SESSION_*.meta` file for `last_saved_at` timestamp and `message_count`
- Extract messages newer than `last_saved_at` from the current context
- Format only the new messages and append them to the existing session file
- Update the meta file with the new `last_saved_at` and `message_count`

**Idempotency:** If `last_saved_at` matches the current state exactly (no new messages), skip append and report "No new messages to save."

### Step 7: Rotate if >3 Files

Count `SESSION_*.md` files in `docs/sessions/` (not the meta files):

```powershell
$count = @(Get-ChildItem -Path "docs/sessions" -Filter "SESSION_*.md").Count
```

If `$count -gt 3`:
1. Find the oldest file (earliest date from filename — sort by `SESSION_YYYY_MM_DD_NNN`)
2. Move both the `.md` and `.meta` file to `archive/sessions/`:
   ```powershell
   Move-Item -Path "docs/sessions/$oldestFile" -Destination "archive/sessions/$oldestFile"
   Move-Item -Path "docs/sessions/.$metaFile" -Destination "archive/sessions/.$metaFile"
   ```
3. Confirm: "**Archived oldest session `<filename>` to `archive/sessions/`.**"

### Step 8: Report

Print a summary:
- **For new file:** "**Session saved. File: `docs/sessions/SESSION_YYYY_MM_DD_NNN.md` (<N> messages).**"
- **For append:** "**Session updated. Appended <N> new messages to `docs/sessions/SESSION_YYYY_MM_DD_NNN.md`.**"
- **For skip:** "**No new messages to save. Session is current.**"
- **On failure:** "**Save failed: [error message]. Please retry. No data was lost.**"

### Step 9: Session Continuity Check

This step is used by caller skills (Phase 0) to detect and recover from context loss after compaction.

**When to run:**
- At Phase 0 of any write-phase skill (brainstorm-and-plan, check-plan-readiness, implement-plan, review-implementation, modularize-and-clean, improve-architecture)
- When the user says "continue" after a compaction event

**Workflow:**

1. **Scan for session files:**

   ```powershell
   $files = @(Get-ChildItem -Path "docs/sessions" -Filter "SESSION_*.md" -Name)
   ```

2. **If none found:** Report "No session files found — starting fresh context." Skip.

3. **If files exist AND current context has < 3 user messages** (or user said "continue" after compaction):
   - Find the most recent session file (highest NNN):
     ```powershell
     $mostRecent = $files | Sort-Object -Descending | Select-Object -First 1
     ```
   - Read the YAML header only: `Read -Path "docs/sessions/$mostRecent" -Offset 1 -Limit 30`
   - Report the restored context:
     ```
     Restored context from {filename}: goal={goal}, phase={phase}, next_step={next_step}
     ```

4. **Policy:**
   - Header-only read (~200 tokens) — never read the full session body
   - Archived sessions (in `archive/sessions/`) are never auto-read
   - Sub-agent context: main agent extracts 1-3 relevant lines from header into Task prompt manually

## Outputs & Triggers

### Output
Session file created/appended at `docs/sessions/SESSION_*.md`. Meta file updated. Rotation performed if needed.

### Exit Declaration
State clearly: "**Session saved at `docs/sessions/SESSION_...`. <summary of what was done>**"

### Next Step
Return to the calling skill's workflow (implement-plan or review-implementation) and continue from where the save-session call was made.
