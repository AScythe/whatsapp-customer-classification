---
name: generate-and-run-e2e-tests
description: '[Build mode — standalone] Generate or update docs/E2E_TESTING.md with project-specific E2E test scenarios, then run Playwright tests. Auto-detects Playwright config, spec files, package manager, and build command from the project. Short-circuits to running tests when no changes detected. Use when the user says "run e2e tests", "run e2e", "end to end", "playwright", "generate e2e doc", or similar.'
---

## What I do
> **Standalone skill** — not part of the core dev workflow. Invoke manually after any implementation that changes page behavior, form logic, or navigation flow.

- Introspect the project: detect Playwright config, spec files, package manager, build command
- Compute a content hash of the current Playwright config + spec file listing
- If `docs/E2E_TESTING.md` exists with a matching hash, skip regeneration and run tests directly
- If hash mismatches or doc is missing, regenerate the auto-generated section while preserving any manual content
- Install `@playwright/test` if missing
- Build the frontend SPA if a build command exists
- Run `npx playwright test`
- Report pass/fail per scenario
- Stop on any error

## Detection

### Playwright Config
Search for `playwright.config.ts` or `playwright.config.js` in the project root or common subdirectories (`frontend/`, `e2e/`, `tests/`). Once found:
- Extract `webServer.command`, `webServer.url`, `baseURL`
- Extract `testDir` for spec file location
- Generate section in docs/E2E_TESTING.md

### Spec Files
Scan `testDir` (from config) for `*.spec.ts` or `*.spec.js` files. For each file, parse `test.describe()` blocks as scenario categories.

### Package Manager
Detect lockfile priority: `pnpm-lock.yaml` → `yarn.lock` → `package-lock.json` → default to `npm`

### Build Command
Check `package.json` scripts for a `build` command. If absent, skip build step with notice.

## Doc Structure

`docs/E2E_TESTING.md` has two sections:

### Auto-Generated (top)
Fully rewritten on regeneration. Includes:
- Content hash (sha256 of Playwright config + spec file listing)
- Project info: package manager, build command
- WebServer config: command, URL, baseURL
- Test scenarios table: spec file → describe blocks → what they verify
- Run command

### Manual (bottom)
User-editable content. Preserved and carried forward across regenerations. The skill reads everything after a `## Manual` marker and writes it back.

## Workflow

### 1. Discover Project State
- Locate Playwright config file (search: `playwright.config.*` in cwd, `frontend/`, `e2e/`, `tests/`)
- Read config to extract: `testDir`, `webServer.command`, `webServer.url`, `baseURL`
- Detect package manager via lockfile
- Read `package.json` for build command
- Scan spec files in `testDir`
- Read `docs/E2E_TESTING.md` if it exists (extract stored hash, extract manual section)

### 2. Compute Content Hash
- Compute sha256 of: (config file content + sorted list of spec file relative paths)
- Compare with stored hash in existing `docs/E2E_TESTING.md`
- Match → skip to step 5 (no regeneration needed)
- Mismatch or no doc → proceed to step 3

### 3. Generate or Regenerate docs/E2E_TESTING.md
- Read manual section from existing doc (everything after `## Manual`), if any
- Build the auto section with current project state
- Append manual section (or create empty `## Manual` heading)
- Write to `docs/E2E_TESTING.md`

### 4. Install Playwright (if missing)
Check `node_modules/@playwright/test` (relative to frontend). If absent:
```bash
cd frontend && npm install -D @playwright/test && npx playwright install chromium
```

### 5. Build (if build command exists)
If `package.json` has a `build` script:
```bash
cd frontend && npm run build
```
If build fails, report the error and stop. Do not run tests against stale artifacts.

### 6. Run E2E Tests
```bash
cd frontend && npx playwright test
```
Playwright's `webServer` config handles:
- Starting the app with appropriate environment
- Waiting for the port to be ready
- Killing the server on exit

### 7. Report Results
- All tests pass → "✅ All E2E tests pass"
- Any test fails → report which scenario failed with error message
- Generation failure → stop, analyze, report
- Install/build failure → stop, report

## Edge Cases

- **No Playwright config found** — Generate a minimal `playwright.config.ts` at project root with chromium, default settings, and webServer pointing to the project's dev command
- **No spec files found** — Generate doc with empty scenarios table + notice: "No E2E spec files found. Create files in `tests/e2e/` with `*.spec.ts` extension."
- **No lockfile found** — Default to npm
- **No build command** — Skip build step with notice in doc
- **Existing doc missing hash** — Treat as content mismatch, regenerate
- **Existing doc has no manual section** — Create empty `## Manual` section
- **Port in use** — Playwright `webServer` reports the conflict; skill reports the failure
- **Chromium not installed** — Skill auto-installs via `npx playwright install chromium`
- **Tests already running** — `reuseExistingServer: !process.env.CI` allows reusing a running server in dev

## Output

Exit with clear pass/fail. If any test fails, the user should investigate before proceeding with other work.
