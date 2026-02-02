# AI_RULES.md — Universal AI Agent Instructions
# Project: YouTube Longitudinal Data Collection

> **For AI Assistants:** This file contains critical rules and context for working on this project.
> Read this file at the start of every session. This is the same content as `.cursorrules`.

> **🔴 CRITICAL:** `.cursorrules` and `AI_RULES.md` MUST remain identical (except for headers). When updating one, ALWAYS update the other.

---

# CRITICAL RULES (THE TEN COMMANDMENTS)

## 1. Safety Constraints (NEVER BREAK THESE)
- **NEVER** delete data files (`.csv`, `.json`, `.db`) under any circumstances.
- **NEVER** delete program files (`.py`, `.sh`, `.yaml`) under any circumstances.
- **NEVER** overwrite existing Python scripts when trying a new approach.
  - INSTEAD: Create a new numbered/named script (e.g., `test_discovery_v2.py`).
- **NEVER** commit API Keys to version control or write them in non-ignored files.
- **NEVER** navigate outside the project root.
- **ALWAYS** check `config.yaml` for safety limits before running large jobs.

## 2. Session Protocols
- **Start:** Read `AI_RULES.md` and `task.md`.
- **End:** Update `task.md` with progress and next steps.
- **Logs:** Maintain `task.md` as the single source of truth for progress (replaces `PROGRESS_LOG.md` for this project).

## 3. Documentation Philosophy
- **Minimize Clutter:** Do not create new markdown files for every thought.
- **Use Artifacts:** Use the `task.md` file for checklists and status.
- **Technical Specs:** Keep `USAGE.md` or `README.md` updated with how to run scripts.

---

# Tech Stack & Standards

## Core Technologies
- **Python 3.12+** (Standard Environment)
- **YouTube Data API v3** (google-api-python-client)
- **Pandas** for data manipulation
- **PyYAML** for configuration

## Python Coding Standards
1.  **Type Hints:** All functions must have type hints.
2.  **Docstrings:** Google-style docstrings for every function.
3.  **Pathlib:** Use `pathlib` for file paths, never string concatenation.
4.  **Error Handling:**
    - ALWAYS handle `HttpError` for API calls.
    - Implement exponential backoff for 403/429 errors.
5.  **Quota Safety:**
    - Scripts must estimate quota usage *before* running.
    - Large pulls (>10k units) requires explicit user confirmation or `input()` check.

## Deprecated Patterns
- **DO NOT** use `print()` for logging in production scripts; use `logging` module.
- **DO NOT** hardcode API keys. Use `config.yaml`.
- **DO NOT** use default `open()` without encoding; always use `encoding='utf-8'`.

---

# Agent Autonomy Guidelines

## 🛑 REQUIRE USER APPROVAL FOR:
1.  **Spending Money/Quota:** Any action that could consume >10% of daily API quota.
2.  **Deleting/Overwriting:** Any file modification that destroys history (though you should generally *never* do this).
3.  **Scope Changes:** Changing the research design (e.g., sampling criteria).

## ✅ ALLOW AUTONOMOUS EXECUTION FOR:
1.  **Debugging:** Fixing syntax errors, `try/except` blocks.
2.  **Read-Only Operations:** searching, listing files, checking quota.
3.  **Safe Creation:** Creating new test scripts or config templates.

---

# Project Specifics: YouTube Longitudinal

## Directory Structure
- `src/`: Python source code
- `config/`: Configuration (gitignored)
- `data/raw/`: JSON/CSV dumps from API
- `data/processed/`: Cleaned CSVs for analysis
- `logs/`: Execution logs

## The "Three-Pronged" Strategy
1.  **Viable New Creators:** Jan 2026 Cohort (Hourly Search -> Video Count Filter).
2.  **Panel Study:** Daily tracking of 9,000 existing channels.
3.  **Random Sample:** Background validation.

---

> **USER REMINDER:** When in doubt, ASK. It is better to pause than to burn quota or lose data.
