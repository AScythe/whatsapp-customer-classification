# Agent Development Environment Setup

> **Last verified:** 2026-06-11

This document captures every global and project-level configuration needed to reproduce this project's AI coding assistant environment on any device.

---

## Table of Contents

- [What This Covers](#what-this-covers)
- [Prerequisites](#prerequisites)
- [Global Setup (One-Time Per Machine)](#global-setup-one-time-per-machine)
- [Project Setup (Per Repository Clone)](#project-setup-per-repository-clone)
- [Configuration Reference](#configuration-reference)
- [Gitignore Configuration](#gitignore-configuration)
- [Custom Commands](#custom-commands)
- [First-Time Flow From Scratch](#first-time-flow-from-scratch)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## What This Covers

| Layer | Tools |
|-------|-------|
| AI Assistant | OpenCode CLI |
| Code Search | cocoindex-code (semantic), ast-grep (structural) |
| Knowledge Graph | graphify (project map) |
| Workflow | Agentic pipeline skills (discovered from `.opencode/skills/`) |
| Scaffolding | `/scaffold` command for generating skills and commands |

---

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | >= 3.10 | [python.org](https://python.org) |
| Node.js | >= 18 | [nodejs.org](https://nodejs.org) |
| npm | >= 10 | (ships with Node.js) |
| uv | >= 0.5 | `powershell -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| OpenCode CLI | >= 1.14 | See below |

---

## Global Setup (One-Time Per Machine)

These steps run **once per machine** — not per repo. They configure your AI coding assistant and MCP tooling globally.

### 1. Install OpenCode CLI

```powershell
npm install -g opencode-ai
```

Verify:

```powershell
opencode --version
```

### 2. Configure OpenCode Global Permissions

Create `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "lsp": true,
  "agent": {
    "build": {
      "permission": {
        "edit": "ask",
        "write": "ask",
        "bash": "ask"
      }
    },
    "plan": {
      "permission": {
        "edit": "deny",
        "write": "deny",
        "bash": "ask"
      }
    }
  }
}
```

- Build-mode: asks before editing, writing, or running shell commands.
- Plan-mode: edit and write are **denied** (physically blocked); bash prompts for approval.

### 3. Install MCP Servers

**cocoindex-code** (semantic code search):

```powershell
uv tool install 'cocoindex-code[full]'
```

The `[full]` extra bundles local sentence-transformers embeddings (no API key required). The `ccc` CLI is provided by this package.

**graphify** (knowledge graph):

```powershell
pip install 'graphifyy[mcp]'
```

> Note: The PyPI package is `graphifyy` (double-y). The import module is `graphify`. Use `pip install` (not `uv tool install`) so the module is importable by `python -m graphify.serve`.

### 4. Add uv Tool Binaries to PATH

Both `ccc` and `graphify` executables are installed to `~/.local/bin/` by uv, but this directory is not on PATH by default on Windows.

```powershell
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";$env:USERPROFILE\.local\bin",
    "User"
)
```

Open a **new terminal** for this to take effect. Verify:

```powershell
ccc --help
graphify --help
```

### 5. Set Default Embedding Model for cocoindex-code

The file `~/.cocoindex_code/global_settings.yml` is auto-created by `ccc init`. Recommended config (local embeddings, no API key):

```yaml
embedding:
  provider: sentence-transformers
  model: sentence-transformers/all-MiniLM-L6-v2
```

To switch models, edit this file and run `ccc doctor` to verify.

---

## Project Setup (Per Repository Clone)

These steps run for **each clone** of the project.

### 1. Clone Repository

```powershell
git clone <repository-url>
cd [project-name]
```

### 2. Install OpenCode Plugin Dependencies

```powershell
cd .opencode
npm install
cd ..
```

This installs `@opencode-ai/plugin` and `opencode-ast-grep` — the AST-based structural search and rewrite tool.

### 3. Create `opencode.json` (Project MCP & Plugin Config)

If the file doesn't exist at the project root, create it with the standard MCP server and plugin configuration. The config registers both cocoindex-code and graphify as MCP servers.

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["opencode-ast-grep"],
  "permission": {
    "skill": {
      "*": "allow"
    }
  },
  "mcp": {
    "cocoindex-code": {
      "type": "local",
      "command": ["ccc", "mcp"]
    },
    "graphify": {
      "type": "local",
      "command": ["python", "-m", "graphify.serve", "graphify-out/graph.json"]
    }
  }
}
```

> **Why this matters:** Without `opencode.json`, OpenCode won't start the MCP servers for semantic search (cocoindex-code) or knowledge graph queries (graphify), and the ast-grep plugin won't load. Restart your OpenCode session after creating/editing this file.

### 4. Initialize cocoindex-code Index

```powershell
ccc init
ccc index
```

- `ccc init` creates `.cocoindex_code/settings.yml` with file patterns for indexing
- `ccc index` builds the semantic search index (incremental after first build)
- `.cocoindex_code/` is gitignored — rebuild on each clone
- `graphify-out/*.json`, `GRAPH_REPORT.md`, and `graph.html` are excluded from cocoindex's `exclude_patterns` — graph data is queried via the graphify MCP server, not semantic search

### 5. Build the Knowledge Graph

```powershell
graphify update .
```

This creates `graphify-out/` with:
- `graph.json` — full knowledge graph data
- `graph.html` — interactive visualization
- `GRAPH_REPORT.md` — architecture insights

### 6. Verify MCP Configuration

If `opencode.json` existed before cloning (checked in), MCP servers are already registered — no action needed. If you created it in step 3, the first time you restart OpenCode both MCP servers should connect automatically.

> The `graphify opencode install` command exists but is not needed — it creates an optional plugin reminder that is redundant with AGENTS.md rules.

---

## Configuration Reference

### Global Configuration Files

| File | Purpose |
|------|---------|
| `~/.config/opencode/opencode.json` | OpenCode global config: permissions (build: edit/write/bash = ask; plan: edit/write = deny, bash = ask), lsp enabled |
| `.opencode/commands/scaffold.md` | Custom `/scaffold` command for generating skills and commands (project-level) |
| `~/.cocoindex_code/global_settings.yml` | Default embedding model for semantic search |

### Global Tool Installations

| What | Command | Provides |
|------|---------|----------|
| OpenCode CLI | `npm install -g opencode-ai` | `opencode` command |
| cocoindex-code | `uv tool install 'cocoindex-code[full]'` | `ccc`, `cocoindex-code` commands |
| graphifyy | `pip install 'graphifyy[mcp]'` | `graphify` command, `graphify` Python module |

### Project Configuration Files

| File | Purpose | Checked In? |
|------|---------|-------------|
| `opencode.json` | Plugins (`opencode-ast-grep`) and MCP servers (`ccc mcp`, `python -m graphify.serve`) | Yes |
| `.opencode/package.json` | Plugin npm dependencies | Yes |
| `.opencode/skills/` | Agentic workflow skill definitions | Yes |
| `.cocoindex_code/settings.yml` | File patterns for code indexing (auto-generated by `ccc init`) | No (gitignored) |
| `graphify-out/graph.json` | Project knowledge graph | Yes |
| `graphify-out/GRAPH_REPORT.md` | Graph report | Yes |
| `graphify-out/graph.html` | Interactive visualization | Yes |
| `graphify-out/manifest.json` | Cache metadata (not shared) | No (gitignored) |
| `graphify-out/cost.json` | API cost tracking (not shared) | No (gitignored) |
| `graphify-out/cache/` | AST extraction cache | No (gitignored) |
| `graphify-out/.graphify_labels.json` | Internal metadata (regenerated on rebuild) | No (gitignored) |
| `graphify-out/.graphify_root` | Internal metadata (regenerated on rebuild) | No (gitignored) |
| `.gitignore` | Ignores for tool-generated files | Yes |
| `.graphifyignore` | Graphify exclusion rules — filters low-signal files (caches, deps, archives) from the knowledge graph | Yes |
| `agent_utility/` | Agent maintenance scripts — graph utilities (filter, dedup, enhance) | Yes |

### opencode.json (Project Root)

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["opencode-ast-grep"],
  "permission": {
    "skill": {
      "*": "allow"
    }
  },
  "mcp": {
    "cocoindex-code": {
      "type": "local",
      "command": ["ccc", "mcp"]
    },
    "graphify": {
      "type": "local",
      "command": ["python", "-m", "graphify.serve", "graphify-out/graph.json"]
    }
  }
}
```

> **Permissions:** The project-level `opencode.json` controls plugins, MCP servers, and skill permissions. Build-mode permissions (edit/write/bash) are set globally at `~/.config/opencode/opencode.json` (see [§2](#2-configure-opencode-global-permissions)). To override per-project, add an `agent.build.permission` block to the root `opencode.json`.

### Agentic Workflow Skills

The `.opencode/skills/` directory contains 21 skills implementing an Agentic Development pipeline:

| Phase | Skill | Mode |
|-------|-------|------|
| 1 | `brainstorm-and-plan` | Plan |
| 2 | `grill-and-refine` | Plan |
| 3 | `check-plan-readiness` | Build |
| 4 | `implement-plan` | Build |
| 5 | `review-implementation` | Build |
| 6 | `improve-architecture` | Build |
| 7 | `modularize-and-clean` | Build |
| 8 | `improve-security` | Build |
| 9 | `update-docs` | Build |
| 10 | `rebuild-test-and-indexes` | Build |
| 11 | `push-to-git` | Build |
| — | `generate-and-run-e2e-tests` | Build |
| — | `update-agent-setup-md` | Build |
| — | `update-agents-md` | Build |
| — | `update-architecture-md` | Build |
| — | `update-best-practices-md` | Build |
| — | `update-readme-md` | Build |
| — | `update-specifications-md` | Build |
| — | `save-session` | Build |
| — | `frontend-design` | Plan |
| — | `shadcn` | Build |

Skills are auto-loaded by OpenCode when the task description matches their `name` and `description` fields.

---

### Gitignore Configuration

**Principle:** Track what's essential for setup (configs, dependencies, manifests). Ignore what's regeneratable (build output, caches, indexes, internal metadata).

#### Root `.gitignore` — Tool-Related Rules

| Rule | Tool | Why Ignored |
|------|------|-------------|
| `.opencode/node_modules/` | OpenCode plugins | Regeneratable via `npm install` in `.opencode/` |
| `/.cocoindex_code/` | cocoindex-code | Platform-specific index tied to local Python env; recreated by `ccc init && ccc index` |
| `graphify-out/manifest.json` | graphify | mtime-based cache metadata — breaks after git clone |
| `graphify-out/cost.json` | graphify | Local API cost tracking — not shareable across machines |
| `graphify-out/cache/` | graphify | AST extraction cache — regenerated by `graphify update .` |
| `graphify-out/.graphify_labels.json` | graphify | Internal metadata — regenerated on rebuild |
| `graphify-out/.graphify_root` | graphify | Internal metadata — regenerated on rebuild |

> **Note:** `graphify-out/graph.json`, `graphify-out/GRAPH_REPORT.md`, and `graphify-out/graph.html` are **tracked** (shared across machines). Only caches and metadata are ignored. These graph output files are also excluded from cocoindex-code's semantic index (via `settings.yml` `exclude_patterns`) — graph queries use the graphify MCP server, not vector search.

#### Nested `.opencode/.gitignore`

```gitignore
node_modules
bun.lock
```

Only `node_modules` and `bun.lock` are ignored here. The files `package.json` and `package-lock.json` are **tracked** — they define the exact plugin dependency versions so every clone gets identical OpenCode plugin behavior.

#### Why Not Commit Generated Files

- `.cocoindex_code/` is tied to your Python environment and absolute file paths — an index built on Windows won't work on Mac or Linux. Run `ccc init && ccc index` on each machine instead.
- `graphify-out/cache/` and metadata files (`.graphify_labels.json`, `.graphify_root`) are AST extraction artifacts unique to the local environment. The committed graph (`graph.json`, `GRAPH_REPORT.md`, `graph.html`) is the shareable output.
- `graphify-out/manifest.json` stores mtime-based hashes that change after clone — committing it would cause false rebuilds.

---

## Custom Commands

### `/scaffold`

Creates new OpenCode skills and commands from templates. Defined at `.opencode/commands/scaffold.md` (project-level).

Usage:

| Command | Creates | Location |
|---------|---------|----------|
| `/scaffold skill <name>` | Skill definition | `.opencode/skills/<name>/SKILL.md` |
| `/scaffold command <name>` | Command prompt | `.opencode/commands/<name>.md` |
| `/scaffold global-skill <name>` | Global skill | `~/.config/opencode/skills/<name>/SKILL.md` |
| `/scaffold global-command <name>` | Global command | `~/.config/opencode/commands/<name>.md` |

Each template includes frontmatter (`name`, `description`) and a base workflow structure. After generation, the file can be edited to customize behavior.

---

## First-Time Flow From Scratch

Complete end-to-end setup on a new machine:

### Step 1: Install System Prerequisites

```powershell
# Install Python 3.10+ from https://python.org
# Install Node.js 18+ from https://nodejs.org

# Install uv
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install OpenCode CLI
npm install -g opencode-ai

# Reload PATH
$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
```

### Step 2: Set Up MCP Servers

```powershell
uv tool install 'cocoindex-code[full]'
pip install 'graphifyy[mcp]'

# Add uv tool bin directory to PATH
[Environment]::SetEnvironmentVariable("Path", "$env:Path;$env:USERPROFILE\.local\bin", "User")

# Open a NEW terminal for PATH change to take effect
```

### Step 3: Install OpenCode Global Config

Create `~/.config/opencode/opencode.json` (see [section 2](#2-configure-opencode-global-permissions) above).

### Step 4: Clone and Set Up Project

```powershell
git clone <repository-url>
cd [project-name]

# Create opencode.json if it doesn't exist (MCP server config)
# See "Project Setup" → step 3 for the full config content

# OpenCode plugin dependencies
cd .opencode
npm install
cd ..
```

If `opencode.json` is not checked into the repository (e.g. scaffolded from scratch), **create it now** — see [step 3 of Project Setup](#3-create-opencodejson-project-mcp--plugin-config) above. Without this file, MCP servers won't start.

### Step 5: Initialize Tooling

```powershell
ccc init
ccc index
graphify update .
```

### Step 6: Restart OpenCode

Restart your OpenCode session. Both MCP servers should connect automatically.

---

## Replicating to Another Project

To reuse this project's agent development environment in a **new project**, manually copy the following files and folders from a source project that already has them set up.

### Files to Copy

#### 1. Skills & Commands (`.opencode/`)

```
.opencode/skills/<name>/SKILL.md   — all skill definitions
.opencode/commands/<name>.md       — all command definitions
.opencode/package.json             — plugin dependency manifest
.opencode/package-lock.json        — locked plugin versions
```

#### 2. Agent Guidelines (`AGENTS.md`)

Copy `AGENTS.md` to the new project root.

> ⚠️ **Must edit:** Update file paths, command targets, doc references, skill list, and test references to match the new project. Every path in the File Ownership table, Commands Reference, Documentation Structure, and Test Suite Structure sections should point to real files in the new project.

#### 3. Reference Documents (`refs/`)

```
refs/AGENT_SETUP.md
refs/PROJECT_BEST_PRACTICES.md
refs/DOCUMENT_GUIDELINES.md
```

#### 4. Agent Utilities (`agent_utility/`)

Copy the entire `agent_utility/` directory:

```
agent_utility/filter_graph.py
agent_utility/enhance_graph_viewer.py
agent_utility/dedup_graph_nodes.py
```

These graph maintenance scripts are invoked by the `rebuild-test-and-indexes` skill.

#### 5. Agent Guideline Tests

```
tests/test_agent_guidelines.py
```

> ⚠️ After copying, update the `SOURCE_PATHS` dict and `COMMAND_TARGET_GROUPS` at the top of the file to match the new project's layout.

#### 6. Project Config Files

| File | Purpose |
|------|---------|
| `opencode.json` | MCP servers, plugins, skill permissions — create from scratch if the source project didn't have one (see [step 3 of Project Setup](#3-create-opencodejson-project-mcp--plugin-config) for content); if copying, verify MCP format |
| `.graphifyignore` | Low-signal file filters for knowledge graph |
| `.gitignore` (append) | Add tool-related rules below |

Gitignore rules to append:

```gitignore
.opencode/node_modules/
/.cocoindex_code/
graphify-out/manifest.json
graphify-out/cost.json
graphify-out/cache/
graphify-out/.graphify_labels.json
graphify-out/.graphify_root
```

---

### Post-Copy Verification Gate

After copying all files, run this checklist to confirm nothing was missed:

```
[ ] .opencode/skills/ — all source skill folders present
[ ] .opencode/commands/ — all command .md files present
[ ] AGENTS.md — present and edited for new project
[ ] refs/ — all reference .md files present
[ ] agent_utility/ — all graph scripts present
[ ] tests/test_agent_guidelines.py — present and paths updated
[ ] opencode.json — present, MCP format verified
[ ] .graphifyignore — present
[ ] .gitignore — tool-related rules added
```

Then run the guideline test as a final check:

```powershell
uv run python tests/test_agent_guidelines.py
```

Expected: failing tests for any file paths that still reference the old project. Each ❌ points to exactly what needs updating in `AGENTS.md`. Iterate until all pass.

---

### Post-Copy Setup

After all files are copied and verified, **let the agent read and execute `refs/AGENT_SETUP.md`** — it will walk through the full tool initialization (install dependencies, init CocoIndex, build Graphify). Alternatively, follow the [Project Setup](#project-setup-per-repository-clone) steps manually.

---

## Verification

After setup, confirm each component works:

```powershell
# OpenCode
opencode --version

# cocoindex-code (semantic search)
ccc mcp --help

# graphify (knowledge graph) via CLI
graphify --version

# graphify (knowledge graph) via MCP
python -m graphify.serve graphify-out/graph.json &

# cocoindex index status
ccc status
```

In OpenCode itself, verify:
- The ast-grep plugin is loaded (structural search works)
- Both MCP servers connect without errors on startup
- Skills are listed (skills matching current task description are suggested)

---

## Troubleshooting

### `ccc` or `graphify` command not found

The uv tool binaries are in `~/.local/bin/` but this directory is not on PATH by default on Windows.

**Fix:** Run once:

```powershell
[Environment]::SetEnvironmentVariable("Path", "$env:Path;$env:USERPROFILE\.local\bin", "User")
```

Then open a **new terminal**.

### `python -m graphify.serve` fails with ModuleNotFoundError

graphifyy was installed via `uv tool install` instead of `pip install`. The `uv tool install` isolates the package from system Python.

**Fix:**

```powershell
pip install 'graphifyy[mcp]'
```

### `ccc mcp` fails on OpenCode startup

**Cause:** OpenCode was started before `~/.local/bin` was added to PATH. Child processes inherit the parent's environment, so even if the user PATH is set in the registry, already-running processes and their children won't see it.

**Fix:** Run `ccc --help` in a new terminal. If it works, the PATH is correct — restart your OpenCode host (Cursor, VS Code, terminal) so it picks up the new environment. If `ccc --help` fails, re-run the PATH setup step in [§4](#4-add-uv-tool-binaries-to-path) and open a fresh terminal.

If you genuinely cannot modify PATH (restricted machine), fall back to an absolute path in `opencode.json`:
```json
"cocoindex-code": {
  "type": "local",
  "command": ["C:\\Users\\<YOUR_USERNAME>\\.local\\bin\\ccc.exe", "mcp"]
}
```
But note: absolute paths are **machine-specific** — they break when the same repository is cloned on a different device. Prefer bare `"ccc"` (PATH-based) for portability.

### Graph is stale or has no data

Run:

```powershell
graphify update .
```

This re-extracts the project and rebuilds the knowledge graph.

### Graphify on Windows

**`UnicodeEncodeError` when running `graphify` commands**

```powershell
$env:PYTHONIOENCODING='utf-8'; graphify update .
```

This affects PowerShell 5.1 on Windows where stdout defaults to the system code page (e.g., cp1252).

**Graphify runs fine locally but CI reports `graphify: command not found`**

CI environments typically don't have graphifyy installed. This is expected — graphify is used for *human-guided* architecture review, not automated CI checks. The committed graph (`graph.json`) is the shareable artifact.

### CocoIndex on Windows

**`ccc doctor` fails with `UnicodeEncodeError`**

Same fix:

```powershell
$env:PYTHONIOENCODING='utf-8'; ccc doctor
```

Prepend `$env:PYTHONIOENCODING='utf-8'` before `ccc doctor` on Windows PowerShell to resolve `UnicodeEncodeError`.

### `.cocoindex_code/settings.yml` doesn't exist

Run `ccc init` in the project root to create it, then `ccc index` to build the index.

---

*Maintain this file when adding, removing, or upgrading any agent development tooling.*
