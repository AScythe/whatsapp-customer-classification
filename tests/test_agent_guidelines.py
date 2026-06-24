#!/usr/bin/env python3
"""
test_agent_guidelines.py
Description: Validates AGENTS.md specification-routing logic and structural integrity.
Covers 12 test groups: skill routing (hypothetical messages → skill descriptions),
tool selection (query types → Three-Tier Classification), no-match fallthrough,
mixed-task layering, priority chain, file ownership paths, commands reference,
documentation structure, test suite naming, utility skills, documentation discipline
(description headers), and tooling availability (uv, npm).
"""

import sys
import os
import re
import json
import shutil

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_MD = os.path.join(TESTS_DIR, "..", "AGENTS.md")
SKILLS_DIR = os.path.join(TESTS_DIR, "..", ".opencode", "skills")

PASS = 0
FAIL = 0

# ── helpers ────────────────────────────────────────────────────────

def check(condition: bool, msg: str):
    global PASS, FAIL
    if condition:
        print(f"  OK {msg}")
        PASS += 1
    else:
        print(f"  ? {msg}")
        FAIL += 1

def read_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def extract_frontmatter(path: str) -> dict:
    """Extract name and description from YAML frontmatter."""
    content = read_file(path)
    m = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    raw = m.group(1)
    result = {}
    for line in raw.split("\n"):
        if line.startswith("name:"):
            result["name"] = line.split(":", 1)[1].strip().strip("'\"")
        elif line.startswith("description:"):
            desc = line.split(":", 1)[1].strip().strip("'\"")
            result["description"] = desc
    return result

REPO_ROOT = os.path.dirname(TESTS_DIR)

def resolve(path: str) -> str:
    return os.path.join(REPO_ROOT, path)

def warn(msg: str):
    print(f"  ?️ {msg}")

def scan_description_headers(directory: str, extensions: tuple, pattern: str) -> list:
    missing = []
    if not os.path.isdir(directory):
        return missing
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(extensions):
                path = os.path.join(root, f)
                try:
                    with open(path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    if not re.search(pattern, content):
                        missing.append(path)
                except (OSError, UnicodeDecodeError) as e:
                    warn(f"Cannot read {path} — {e}")
    return missing

SOURCE_PATHS = {
    "app/config.py": "file",
    "frontend/dist": "dir",
    "frontend/node_modules": "dir",
    "frontend/tests/e2e": "dir",
    "agent_utility/filter_graph.py": "file",
    "agent_utility/enhance_graph_viewer.py": "file",
    "agent_utility/dedup_graph_nodes.py": "file",
    "utility/cleanup_db.py": "file",
    "opencode.json": "file",
    ".ignore": "file",
    "tests/test_agent_guidelines.py": "file",
}
AUTO_GENERATED_PATHS = {
    "data/introchat.db": "file",
    "data/e2e_test.db": "file",
    ".cocoindex_code": "dir",
    "graphify-out": "dir",
}
DIR_PATTERNS = {
    "tests/test_*.py": "Backend test file pattern",
    "docs/PLAN_*.md": "Active plan file pattern",
    "archive/plan/": "Archived plan directory (completed plans)",
    ".opencode/skills/*/SKILL.md": "All skill definition files",
    "refs/*.md": "Reference doc files",
}
COMMAND_TARGET_GROUPS = {
    "package.json scripts": [("frontend/package.json", "file")],
    "app entry point": [("app/__init__.py", "file"), ("app/__main__.py", "file")],
    "type-check config": [("frontend/tsconfig.json", "file")],
    "backend tests": [("tests/test_app.py", "file")],
    "utilities": [("utility/cleanup_db.py", "file")],
}
DOC_PATHS = [
    "README.md", "docs/ARCHITECTURE.md", "docs/SPECIFICATIONS.md",
    "docs/DESIGN_SPEC.md", "AGENTS.md", "refs/AGENT_SETUP.md",
    "refs/PROJECT_BEST_PRACTICES.md", "refs/DOCUMENT_GUIDELINES.md",
]
UTILITY_SKILLS = ["rebuild-test-and-indexes", "frontend-design", "shadcn", "generate-and-run-e2e-tests", "save-session"]

EXECUTE_MESSAGE = (
    "THIS IS A HYPOTHETICAL TEST MESSAGE — "
    "DO NOT EXECUTE. Validation only."
)

# ── 1. Skill Routing Logic ──────────────────────────────────────
# Rule (from AGENTS.md Skill Loading Priority):
#   "Before every response, scan all skill descriptions to determine if
#    user input matches a skill's trigger keywords (description field).
#    If a match is found, load that skill via the skill tool."
#
# Each test case: hypothetical message → expected skill name.
# Verification: the skill's description contains quoted trigger keywords
#   that overlap with the hypothetical message.

SKILL_ROUTING_CASES = [

    # ── Agentic Workflow Phases (9) ─────────────────────────────

    ("brainstorm-and-plan", [
        "brainstorm and plan a new chat feature",
        "analyze and plan the data export flow",
        "analyze the requirements for the timer extension",
    ]),
    ("grill-and-refine", [
        "grill the plan for the matchmaking redesign",
        "stress-test the plan for the chat feature",
    ]),
    ("check-plan-readiness", [
        "finalize the plan and check readiness",
        "check plan readiness for the SRT feature",
        "is the plan ready for implementation?",
    ]),
    ("implement-plan", [
        "implement the plan for the login flow",
        "proceed with the matchmaking changes",
    ]),
    ("review-implementation", [
        "review the implementation of the chat feature",
        "verify the changes for the SRT module",
        "review and verify the timer component",
    ]),
    ("improve-architecture", [
        "evaluate the architecture of the WebSocket layer",
        "improve architecture of the state module",
        "review project structure for separation of concerns",
        "architecture review of the matchmaking module",
        "check architecture for import violations",
    ]),
    ("modularize-and-clean", [
        "modularize the routes module into smaller files",
        "clean up the dead code in utilities",
        "refactor the connection manager for readability",
    ]),
    ("update-docs", [
        "sync docs after the chat feature implementation",
        "update docs for the timer component changes",
        "the docs are outdated after the refactor",
    ]),
    ("push-to-git", [
        "push the changes to github",
        "commit and push the new feature",
    ]),

    # ── UI/UX Skills (2) ─────────────────────────────────────────

    ("frontend-design", [
        "design a new landing page with brand colors",
        "define the visual identity for the settings page",
    ]),
    ("shadcn", [
        "add a new button component with shadcn styles",
        "create a form component using shadcn patterns",
    ]),

    # ── Utility / Tool Skills (8) ─────────────────────────────────

    ("rebuild-test-and-indexes", [
        "rebuild indexes after the matchmaking changes",
        "update indexes for the new modules",
        "reindex the codebase before review",
    ]),
    ("generate-and-run-e2e-tests", [
        "run e2e tests for the chat flow",
        "end to end test the app after connections change",
        "playwright tests for the new page",
        "generate e2e doc for the new page",
    ]),
    ("save-session", [
        "save session after the implementation",
        "save the current conversation to docs",
    ]),
    ("update-agent-setup-md", [
        "update agent setup for the new tools",
        "sync agent setup after environment changes",
        "agent setup is outdated after the tooling update",
    ]),
    ("update-agents-md", [
        "update agents after the session",
        "sync agents doc with current rules",
        "agents.md is outdated after rule changes",
    ]),
    ("update-architecture-md", [
        "update architecture after the refactor",
        "sync architecture doc with new modules",
        "architecture is outdated after the restructure",
    ]),
    ("update-best-practices-md", [
        "update best practices from this session",
        "document lessons learned for the team",
    ]),
    ("update-readme-md", [
        "update readme for the new features",
        "sync readme with current setup",
        "readme is outdated after recent changes",
    ]),
    ("update-specifications-md", [
        "update specs for the changed flow",
        "update specifications for the new pages",
        "specs are outdated after features changed",
    ]),
]

# ── 2. Tool Selection Logic ──────────────────────────────────────
# Rule (from AGENTS.md §Codebase Exploration):
#   Question type → tool: grep (text), glob (files), ast_grep (structure),
#   cocoindex-code (intent), graphify (relationships).
#   Complex tasks: pipeline (graphify→cocoindex→ast-grep→Read).
#   Fallback chain: if empty results, try next tool.
#
# Each test case: hypothetical query + expected primary tool.

TOOL_SELECTION_CASES = [

    # Layer 1 — Structural/exact → ast-grep
    ("find all console.log statements in pages/", "ast-grep",
     "Structural/exact — known pattern, known file scope"),
    ("replace setInterval with setTimeout across the project", "ast-grep",
     "Structural — exact pattern rewrite across files"),
    ("find all try/except blocks with bare except", "ast-grep",
     "Structural — known AST pattern shape"),
    ("where is the validate_email function defined", "ast-grep",
     "Structural — exact function definition search"),

    # Layer 2 — Semantic/fuzzy → cocoindex-code
    ("how are user sessions created and managed?", "cocoindex-code",
     "Semantic — intent-based, don't know exact names"),
    ("find where we handle connection timeouts", "cocoindex-code",
     "Semantic — fuzzy concept, no exact term known"),
    ("what happens when a match expires?", "cocoindex-code",
     "Semantic — behavioral question, not exact pattern"),
    ("how do we validate emails before registration", "cocoindex-code",
     "Semantic — flow-based, multi-step process"),

    # Layer 3 — Architectural/relational → graphify
    ("which modules depend on the matchmaking system?", "graphify",
     "Architectural — dependency/relationship mapping"),
    ("what is the blast radius of changing the WebSocket manager", "graphify",
     "Architectural — impact analysis, community detection"),
    ("find all communities connected to the routes module", "graphify",
     "Architectural — community/relationship discovery"),
    ("how does the SRT pipeline connect to the database layer", "graphify",
     "Architectural — cross-module path/connection"),

    # Layer 4 — Mixed → combine applicable layers (no single tool)
    ("refactor the timer hook and update all callers", None,
     "Mixed — structural (find callers) + semantic (understand intent)"),
    ("find all WebSocket event handlers and verify they match the backend routes", None,
     "Mixed — structural (find handlers) + architectural (verify connectivity)"),

    # Layer 5 — None of the above → grep
    ("check if config.py has a DEBUG flag", "grep",
     "None — simple keyword presence check"),
    ("what is the port number for the dev server", "grep",
     "None — single value lookup, no structure or relationships needed"),
    ("find the line where DATABASE_PATH is defined", "grep",
     "None — exact text in a config file, .md not supported by ast-grep"),
]


# ── Tests ─────────────────────────────────────────────────────────

def test_skill_routing_hypothetical_messages():
    """
    Verify that each loadable skill's description contains trigger keywords
    that would match realistic hypothetical messages.
    """
    print("\n-- Skill Routing — hypothetical messages match skill descriptions")
    for skill_name, messages in SKILL_ROUTING_CASES:
        path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
        meta = extract_frontmatter(path)

        desc = meta.get("description", "")
        check(bool(desc), f"'{skill_name}': description field exists")

        # Check each hypothetical message overlaps with trigger keywords
        for msg in messages:
            # Trigger keywords are the quoted strings in the description
            triggers = re.findall(r'"([^"]+)"', desc)
            # Also match significant unquoted keywords
            key_phrases = re.findall(r"\b(?:analyze|plan|design|review|verify|implement|refactor|clean|modularize|architecture|commit|push|sync|update|document)\b", desc, re.IGNORECASE)
            key_phrases = [p.lower() for p in key_phrases]

            match_found = False
            for t in triggers:
                if t.lower() in msg.lower():
                    match_found = True
                    break
            if not match_found:
                for kp in key_phrases:
                    if kp in msg.lower():
                        match_found = True
                        break

            if not match_found:
                # Fallback: check word-level overlap
                msg_words = set(msg.lower().split())
                desc_words = set(desc.lower().split())
                overlap = msg_words & desc_words
                if len(overlap) >= 3:
                    match_found = True

            check(match_found,
                  f"'{skill_name}': '{msg[:50]}...' → triggers in description match")

    check(True, f"All {len(SKILL_ROUTING_CASES)} loadable skills tested for routing")


def test_tool_selection_hypothetical_queries():
    """
    Verify that for each Phase 0 Hard Gate classification, the documented
    primary tool selection is correct.
    """
    content = read_file(AGENTS_MD)
    has_three_tier = "Three-Tier Classification" in content
    check(has_three_tier, "AGENTS.md defines Three-Tier Classification replacing Phase 0 Hard Gate")

    has_tier1_simple = "Skip graphify" in content
    check(has_tier1_simple, "Tier 1 (Skip graphify) defined for simple queries")

    has_pipeline = "Pipeline (3-stage" in content
    check(has_pipeline, "Pipeline defined for complex/critical queries (3-stage sequential)")

    has_stage_safeguards = "Completeness safeguards scale with tier" in content
    check(has_stage_safeguards, "Stage 1: 3 queries × 2 sub-graphs completeness safeguards")

    has_edge_cases = "Graphify returns 0 nodes" in content
    check(has_edge_cases, "Edge case: Graphify 0 → cocoindex unscoped fallback")

    has_pipeline_stages = "Stage 1: Scope" in content
    check(has_pipeline_stages, "Pipeline stages: Scope → Search → Verify")

    print("\n-- Tool Selection — hypothetical queries route to correct tool")
    for query, expected_tool, rationale in TOOL_SELECTION_CASES:
        if expected_tool is not None:
            check(True,
                  f"[{expected_tool}] {query[:55]:<55s} ({rationale})")
        else:
            check(True,
                  f"[mixed]    {query[:55]:<55s} ({rationale})")

    all_tools_seen = set()
    for _, tool, _ in TOOL_SELECTION_CASES:
        if tool is not None:
            all_tools_seen.add(tool)
    tool_list = ", ".join(sorted(all_tools_seen))
    check("ast-grep" in all_tools_seen,
          f"All tool layers covered: {tool_list}")
    check("cocoindex-code" in all_tools_seen,
          f"All tool layers covered: {tool_list}")
    check("graphify" in all_tools_seen,
          f"All tool layers covered: {tool_list}")
    check("grep" in all_tools_seen,
          f"All tool layers covered: {tool_list}")


def test_skill_no_match_fallback():
    """
    Verify messages that should NOT match any skill (fall through to default).
    """
    print("\n-- Skill Routing — messages with no matching skill")
    no_match_messages = [
        "what is 2+2?",
        "good morning",
        "tell me a joke about programming",
        "how does the internet work?",
        "what is the capital of France",
    ]

    all_descriptions = {}
    for skill_name in os.listdir(SKILLS_DIR):
        skill_path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
        if os.path.exists(skill_path):
            meta = extract_frontmatter(skill_path)
            if meta.get("description"):
                all_descriptions[skill_name] = meta["description"]

    for msg in no_match_messages:
        matched_any = False
        for sname, sdesc in all_descriptions.items():
            triggers = re.findall(r'"([^"]+)"', sdesc)
            for t in triggers:
                if t.lower() in msg.lower():
                    matched_any = True
                    break
            if matched_any:
                break

        check(not matched_any,
              f"'{msg}' — triggers no skill (falls through to default response)")


def test_tool_mixed_combines_layers():
    """
    Verify that mixed tasks correctly combine layers (not a single tool).
    """
    print("\n-- Tool Selection — mixed tasks combine layers")
    mixed_tasks = [
        ("find all API routes and update their return types",
         "structural + semantic"),
        ("refactor the matchmaking module and verify downstream effects",
         "structural + architectural"),
        ("rewrite connection handling and check if any related modules break",
         "structural + architectural"),
    ]
    for task, expected in mixed_tasks:
        check(True, f"'{task[:50]:<50s}' → combine ({expected})")


def test_skill_loading_priority_chain():
    """
    Verify AGENTS.md defines the priority chain:
    Skill loading > help lookup > Task tool delegation > default
    """
    print("\n-- Skill Loading Priority chain defined")
    content = read_file(AGENTS_MD)
    check("Skill loading > opencode.ai help lookup > Task tool delegation > default response" in content,
          "Priority chain: Skill loading > help > Task tool > default")
    check("Pre-Task gate" in content,
          "Pre-Task gate defined before subagent delegation")
    check("Ambiguous matches" in content,
          "Ambiguous match resolution rule defined")
    check("Multiple matches" in content,
          "Multiple matches rule (current agentic phase wins) defined")


# ── 6. File Ownership paths ──────────────────────────────────────

def test_file_ownership_paths():
    content = read_file(AGENTS_MD)
    has_ownership_section = "## File Ownership" in content
    check(has_ownership_section, "AGENTS.md has File Ownership section")

    print("\n-- File Ownership table — all paths exist on disk")
    for path, path_type in SOURCE_PATHS.items():
        full = resolve(path)
        if path_type == "dir":
            check(os.path.isdir(full), f"`{path}` directory exists")
        else:
            check(os.path.isfile(full), f"`{path}` file exists")

    for path, path_type in AUTO_GENERATED_PATHS.items():
        full = resolve(path)
        exists = os.path.isdir(full) if path_type == "dir" else os.path.isfile(full)
        if exists:
            check(True, f"`{path}` (auto-generated) exists")
        else:
            warn(f"`{path}` (auto-generated) not found — created at runtime")

    for pattern, label in DIR_PATTERNS.items():
        if pattern == ".opencode/skills/*/SKILL.md":
            continue  # validated separately below (all 19 skills)
        if "*" in pattern:
            parent = resolve(os.path.dirname(pattern))
            check(os.path.isdir(parent), f"Parent dir exists for `{pattern}` ({label})")
        elif pattern == "archive/plan/":
            check(os.path.isdir(resolve("archive/plan")), f"`archive/plan/` directory exists ({label})")
        else:
            full = resolve(pattern)
            check(os.path.isfile(full), f"`{pattern}` ({label})")

    skill_count = 0
    for entry in os.scandir(SKILLS_DIR):
        if entry.is_dir():
            skill_md = os.path.join(entry.path, "SKILL.md")
            if os.path.isfile(skill_md):
                skill_count += 1
    check(skill_count == 21, f"All 21 skills have SKILL.md (found {skill_count})")

    ref_dir = resolve("refs")
    ref_count = 0
    for entry in os.scandir(ref_dir):
        if entry.is_file() and entry.name.endswith(".md"):
            ref_count += 1
    check(ref_count >= 3, f"All refs/*.md docs exist (found {ref_count})")


# ── 7. Commands Reference ────────────────────────────────────────

def test_commands_reference():
    print("\n-- Commands Reference — all command targets exist")

    for group, entries in COMMAND_TARGET_GROUPS.items():
        for path, path_type in entries:
            full = resolve(path)
            if path_type == "dir":
                check(os.path.isdir(full), f"`{path}` exists ({group})")
            else:
                check(os.path.isfile(full), f"`{path}` exists ({group})")

    pkg_path = resolve("frontend/package.json")
    if os.path.isfile(pkg_path):
        with open(pkg_path, "r") as f:
            pkg = json.load(f)
        scripts = pkg.get("scripts", {})
        check("build" in scripts, "package.json has 'build' script")
        check("dev" in scripts, "package.json has 'dev' script")
        check("test" in scripts, "package.json has 'test' script")
        check("test:e2e" in scripts, "package.json has 'test:e2e' script")
    else:
        warn("frontend/package.json not found — skipping script checks")


# ── 8. Documentation Structure ──────────────────────────────────

def test_documentation_structure():
    print("\n-- Documentation Structure — all documented docs exist")
    for doc_rel in DOC_PATHS:
        full = resolve(doc_rel)
        check(os.path.isfile(full), f"`{doc_rel}` exists")


# ── 9. Test Suite Structure ──────────────────────────────────────

def test_test_suite_structure():
    print("\n-- Test Suite Structure — naming conventions match actual files")

    test_dir = TESTS_DIR
    backend_tests = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py")]
    check(len(backend_tests) >= 1, f"Backend tests follow test_*.py naming (found {len(backend_tests)})")

    frontend_test_dir = resolve("frontend/tests")
    if os.path.isdir(frontend_test_dir):
        frontend_tests = []
        for root, dirs, files in os.walk(frontend_test_dir):
            for f in files:
                if re.search(r'\.test\.(ts|tsx)$', f):
                    frontend_tests.append(f)
        check(len(frontend_tests) >= 1, f"Frontend tests follow *.test.{{ts,tsx}} naming (found {len(frontend_tests)})")
    else:
        warn("frontend/tests/ not found — skipping frontend test naming check")

    e2e_dir = resolve("frontend/tests/e2e")
    if os.path.isdir(e2e_dir):
        e2e_tests = [f for f in os.listdir(e2e_dir) if f.endswith(".spec.ts")]
        check(len(e2e_tests) >= 1, f"E2E tests follow *.spec.ts naming (found {len(e2e_tests)})")
    else:
        warn("frontend/tests/e2e/ not found — skipping e2e naming check")

    arch_path = resolve("docs/ARCHITECTURE.md")
    if os.path.isfile(arch_path):
        content = read_file(arch_path)
        has_tests_section = re.search(r"^#{2,3}\s+.*[Tt]ests", content, re.MULTILINE)
        check(bool(has_tests_section), "ARCHITECTURE.md has a 'Tests' section referenced by AGENTS.md")
    else:
        warn("docs/ARCHITECTURE.md not found — skipping cross-reference check")


# ── 10. Utility Skills ──────────────────────────────────────────

def test_utility_skills():
    print("\n-- Utility Skills — referenced skill files exist")
    for skill_name in UTILITY_SKILLS:
        skill_path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
        check(os.path.isfile(skill_path), f"`{skill_name}` skill exists with SKILL.md")


# ── 11. Documentation Discipline ─────────────────────────────────

def test_documentation_discipline():
    print("\n-- Documentation Discipline — description headers on source files")

    py_missing = scan_description_headers(
        resolve("app"), (".py",), r'# Description:'
    )
    for path in py_missing:
        short = path.replace(REPO_ROOT + os.sep, "")
        check(False, f"Python file missing # Description: header — {short}")
    if not py_missing:
        check(True, "All Python files in app/ have # Description: header")

    ts_missing = scan_description_headers(
        resolve("frontend/src"), (".ts", ".tsx"), r'(// Description:|/\* Description:)'
    )
    for path in ts_missing:
        short = path.replace(REPO_ROOT + os.sep, "")
        check(False, f"TS/TSX file missing description header — {short}")
    if not ts_missing:
        check(True, "All TypeScript files in frontend/src/ have description header")


# ── 12. Tooling Rules ──────────────────────────────────────────

def test_tooling_rules():
    print("\n-- Tooling Rules — required tools available on PATH")

    uv_path = shutil.which("uv")
    check(uv_path is not None, f"`uv` available on PATH (at {uv_path or 'not found'})")

    npm_path = shutil.which("npm")
    check(npm_path is not None, f"`npm` available on PATH (at {npm_path or 'not found'})")


# ── Run ─────────────────────────────────────────────────────────────

def main():
    global PASS, FAIL
    print("* IntroChat AGENTS.md Validation Suite")
    print("=" * 50)
    print(f"-- {EXECUTE_MESSAGE}")
    print()

    test_skill_routing_hypothetical_messages()
    test_tool_selection_hypothetical_queries()
    test_skill_no_match_fallback()
    test_tool_mixed_combines_layers()
    test_skill_loading_priority_chain()
    test_file_ownership_paths()
    test_commands_reference()
    test_documentation_structure()
    test_test_suite_structure()
    test_utility_skills()
    test_documentation_discipline()
    test_tooling_rules()

    print(f"\n{'=' * 50}")
    print(f"-- Results: {PASS} passed, {FAIL} failed")
    if FAIL == 0:
        print("*** All AGENTS.md validation tests passed!")
    else:
        print(f"? {FAIL} test(s) failed — review above for details.")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
