# Universal Research Project Template for AI-Assisted Workspaces

**Purpose:** A complete setup guide for creating consistent, well-documented research workspaces with AI assistance  
**Use Case:** Copy this document into a new workspace to set up the full documentation system  
**Adapts To:** Both quantitative and qualitative research projects  
**Created From:** Battle-tested system developed for PhD dissertation work

---

## 🚀 FIRST COMMAND FOR NEW AI AGENTS

**When you first open a new project workspace, give your AI agent this command:**

**For Cursor:**
```
Read MY_WORKFLOW.md, PROJECT_MASTER_PLAN.md, PROGRESS_LOG.md, and .cursorrules to understand this project's workflow, context, and documentation system. Then check if all required documentation files exist and help set up any missing ones.
```

**For Antigravity:**
```
Read MY_WORKFLOW.md, PROJECT_MASTER_PLAN.md, PROGRESS_LOG.md, and .agent/ANTIGRAVITY_RULES.md (or AI_RULES.md if that doesn't exist) to understand this project's workflow, context, and documentation system. Then check if all required documentation files exist and help set up any missing ones.
```

**For Claude or other AI tools:**
```
Read MY_WORKFLOW.md, PROJECT_MASTER_PLAN.md, PROGRESS_LOG.md, and AI_RULES.md to understand this project's workflow, context, and documentation system. Then check if all required documentation files exist and help set up any missing ones.
```

This single command will:
- ✅ Orient the agent to your workflow
- ✅ Load project context and priorities
- ✅ Understand recent activity
- ✅ Learn all safety rules
- ✅ Verify documentation completeness
- ✅ Help set up missing files

**After this command, the agent is ready to work with you.**

---

## Quick Start Checklist

When setting up a new research workspace:

1. [ ] **Initialize Git repository** (see Section 12 for Git setup)
2. [ ] Create `.gitignore` (copy from Section 12)
3. [ ] Create `.cursorrules` (copy from Section 1)
4. [ ] Create `AI_RULES.md` (identical to `.cursorrules`, except header)
5. [ ] **(Optional) Create `.agent/ANTIGRAVITY_RULES.md`** (if using Antigravity; see Section 13)
5. [ ] Create `PROJECT_MASTER_PLAN.md` (copy from Section 2)
6. [ ] Create `PROGRESS_LOG.md` (copy from Section 3)
7. [ ] Create `DECISION_LOG.md` (copy from Section 4)
8. [ ] Create `TECHNICAL_SPECS.md` (copy from Section 5)
9. [ ] **Copy `MY_WORKFLOW_STANDALONE_TEMPLATE.md` as `MY_WORKFLOW.md`** (or copy from Section 6)
10. [ ] Create `writing-patterns.md` (copy from Section 7)
11. [ ] Create `deck.md` (copy from Section 8)
12. [ ] Create folder structure: `code/`, `data/`, `output/`, `drafts/`, `archive/`
13. [ ] Connect to GitHub repository (see Section 12)
14. [ ] Customize each file for your specific project

**Note:** `MY_WORKFLOW.md` is also available as a standalone template file (`MY_WORKFLOW_STANDALONE_TEMPLATE.md`) that you can copy directly into any workspace.

---

# SECTION 1: .cursorrules (and AI_RULES.md)

Create both `.cursorrules` and `AI_RULES.md` with identical content (except for the header note). Cursor auto-reads `.cursorrules`; other AI tools (Claude, Antigravity, etc.) can reference `AI_RULES.md`.

**Note for Antigravity users:** Antigravity also supports `ANTIGRAVITY_RULES.md` in the `.agent/` directory. This can be based on `AI_RULES.md` but may include Antigravity-specific workflows (PLANNING/EXECUTION/VERIFICATION modes, artifact strategies, etc.). See Section 13 for Antigravity-specific setup.

```markdown
# .cursorrules — AI Agent Instructions

> **Note:** This file is auto-read by Cursor. A copy exists as `AI_RULES.md` for compatibility with other AI tools.

> **🔴 CRITICAL:** `.cursorrules` and `AI_RULES.md` MUST remain identical (except for headers). When updating one, ALWAYS update the other.

---

# CRITICAL RULES (READ FIRST)

## Safety Constraints
- **NEVER** delete data files under any circumstances
- **NEVER** delete program files (.do, .py, .R, .tex, .md) under any circumstances
- **NEVER** overwrite existing analysis scripts when adding new analyses
  - INSTEAD: Create a new numbered file (e.g., `05-NEW-ANALYSIS.do`) OR append to end of existing file
  - Rationale: Preserves reproducibility and analysis history
- When reorganizing files, **COPY** to new locations (never move)
- **NEVER** navigate above or outside the project root directory
- All original files must be preserved; use `archive/` folder for retired files

## Session Startup Protocol
At the start of every new chat session:
1. Read this file (`.cursorrules`) — you're doing this now
2. Read `PROGRESS_LOG.md` for recent activity and current status
3. Read `PROJECT_MASTER_PLAN.md` for roadmap, context, and priorities
4. If the task involves writing: also read `writing-patterns.md`
5. If the task involves creating slide decks: also read `deck.md`
6. If the task involves data analysis: also read `TECHNICAL_SPECS.md`

## Session Completion Protocol

At the end of every chat session, update the following files:

### 1. PROGRESS_LOG.md (Required)
Add dated entry at TOP of current month with **timestamp format: "### [Month Day, Year — HH:MM AM/PM]"**
- **Session Focus:** One-line summary
- **Work Completed:** Bullet list of tasks
- **Key Findings:** Results or outputs (if applicable)
- **Decisions Made & Rationale:** Why choices were made, alternatives considered
- **Unexpected Insights:** What was learned, surprises, implications
- **Files Created/Modified:** List with brief purpose statements
- **Open Questions:** Distinguish by type:
  - **Methodological:** Analytical decisions pending
  - **Conceptual:** Theoretical questions
  - **Writing:** Presentation decisions
- **Next Steps (Immediate):** Priority queue with time estimates
- **Status:** Roadmap position

### 2. PROJECT_MASTER_PLAN.md (If Progress Made)
- Update "Current Marker" if roadmap progress made
- Update "Open Questions" section
- Update "Next Steps" with full priority queue

### 3. DECISION_LOG.md (If Analytical Decisions Made)
Add entry with:
- **Decision:** What was chosen
- **Rationale:** Why this approach
- **Alternatives Considered:** What else was evaluated
- **Rejected Because:** Why alternatives weren't chosen
- **Documented In:** Where decision is implemented

### 4. TECHNICAL_SPECS.md (If Specifications Changed)
Update if any changes to:
- Variable definitions
- Analysis specifications
- File paths
- Software versions

### 5. Current Status Section (Always Update)
Update PROGRESS_LOG.md "Current Status" at top

---

> **USER REMINDER:** At the end of sessions, prompt: "Update the logs with this session's work"

---

## Documentation File Management

**CRITICAL: Minimize new markdown file proliferation.**

### When to CREATE a new standalone markdown file:
✅ **Reports/Summaries/Walkthroughs:** Complex answers to specific questions that need detailed documentation

### When to UPDATE existing files instead:
❌ **Global rules/principles:** Add to `.cursorrules` or `AI_RULES.md`
❌ **Deck guidelines:** Add to `deck.md`
❌ **Analysis rules:** Add to `TECHNICAL_SPECS.md`
❌ **Workflow instructions:** Add to `MY_WORKFLOW.md`
❌ **Writing guidelines:** Add to `writing-patterns.md`
❌ **Open questions/next steps:** Add to `PROJECT_MASTER_PLAN.md`
❌ **Session work summary:** Add to `PROGRESS_LOG.md`
❌ **Analytical decisions:** Add to `DECISION_LOG.md`

---

# Coding Standards

## General Principles
- Use descriptive variable names
- Include clear section headers
- Comment complex procedures
- Export outputs with consistent formatting
- Always include sample sizes (N) in output
- Document data transformations explicitly

## Quantitative Projects (Stata/R/Python)
- Use robust standard errors when appropriate
- Export tables with consistent formatting
- Always report sample size changes from listwise deletion
- Set seeds for reproducibility
- Use global macros/variables for control sets

## Qualitative Projects (NVivo/Atlas.ti/MAXQDA)
- Document coding scheme iterations
- Track inter-rater reliability when applicable
- Keep audit trail of code development
- Export code frequencies and matrices consistently

## File Naming Conventions
- **Analysis files:** Numbered sequence with descriptive names (e.g., `03-THEME-ANALYSIS.R`)
- **Output:** Date-based or descriptive (e.g., `2026-02-02_interview_codes.csv`)
- **Drafts:** Include version or date (e.g., `chapter3_draft_v2.tex`)

---

# Deprecated Patterns

- **NEVER** leave placeholder comments like `* TODO: add later` — implement fully or document why not
- **NEVER** make causal claims beyond what the data support
- **DO NOT** overstate significance of small subsample findings
- **NEVER** skip robustness checks for key findings
- **DO NOT** create tables/figures without clear interpretation

---

# Error Handling

- Always check for missing data patterns before analysis
- Document listwise deletion decisions
- Test assumptions explicitly
- Use assertions to verify data integrity
- Log warnings for unexpected data patterns

---

# Agent Autonomy Guidelines

## Require User Approval For:
- Model/analysis specification choices
- Causal claims and interpretation
- Final results before presentation
- Major methodological decisions
- Sample restrictions or transformations

## Allow Autonomous Execution For:
- Data preprocessing within established rules
- Generating diagnostic plots
- Running standard robustness checks
- Producing descriptive statistics
- Creating formatted tables from output
- Running pre-specified analysis pipelines

## Error-Based Reflection
- Automatically detect and report anomalies
- Flag but do NOT auto-correct unexpected results
- Report discrepancies from expected patterns

---

# Academic Writing Phase

## General Principles
- Maintain academic rigor; do not overclaim
- Use precise language: "associated with" not "causes" (unless causal design)
- Report confidence intervals alongside point estimates
- Connect findings to theoretical framework
- Acknowledge alternative explanations

## Figure/Table Standards
- All figures must have clear captions
- Tables should be publication-ready
- Include sample sizes in all tables
- Use consistent variable labels across tables

---

# Code Review Checklist
- [ ] Analysis documented clearly
- [ ] Sample sizes documented
- [ ] Missing data handled explicitly
- [ ] Outputs formatted consistently
- [ ] Code is reproducible
- [ ] Limitations noted
```

---

# SECTION 2: PROJECT_MASTER_PLAN.md

```markdown
# PROJECT MASTER PLAN: [Your Project Title]

**Purpose:** Comprehensive project context and roadmap  
**Primary Analyst:** [Your Name] ([Your Email])  
**Last Updated:** [Date]  
**Current Status:** [Brief status]

---

## How to Use This File

**At the start of each new chat:**
1. Open this roadmap to understand project context and current status
2. Check `PROGRESS_LOG.md` for recent activity
3. Identify the **Current Marker** (below) and pick one deliverable to work on

**At the end of each chat:**
1. Update `PROGRESS_LOG.md` with timestamped entry
2. Update the **Current Marker** below if roadmap progress was made
3. Update `DECISION_LOG.md` if analytical decisions were made

---

## Current Marker

**Now:** [Current phase/task]  
**Last Session:** [Date] — [What was accomplished]  
**Next:** [Immediate priority]

---

# PART 1: PROJECT CONTEXT

## Research Question and Objectives

**Primary Research Question:**  
[Your main research question]

**Secondary Questions:**
- [Secondary question 1]
- [Secondary question 2]

**Success Criteria:**
1. [Criterion 1]
2. [Criterion 2]
3. [Criterion 3]

## Theoretical Framework

**Core Theories:**
1. [Theory 1]
2. [Theory 2]

**Conceptual Model:**
[Describe or diagram your conceptual model]

## Data Infrastructure

**Primary Dataset:**
- **File:** [path/to/data]
- **N:** [sample size]
- **Sample:** [sample description]
- **Type:** [Quantitative/Qualitative/Mixed]

**Key Variables/Codes:**
| Variable/Code | Description |
|---------------|-------------|
| [var1] | [description] |
| [var2] | [description] |

## Key Findings (To Date)

| Finding | Evidence | Interpretation |
|---------|----------|----------------|
| [Finding 1] | [Statistic/Quote] | [Meaning] |

## Constraints and Limitations

**Methodological:**
- [Limitation 1]
- [Limitation 2]

**Data:**
- [Limitation 1]

---

# PART 2: ROADMAP

## Roadmap Overview (One-Line)

**[Phase 1] → [Phase 2] → [Phase 3] → [Phase 4] → [Final Deliverable]**

---

## Phase 1: [Name] ☐ [PENDING/IN PROGRESS/COMPLETE]
- **1.1:** [Task]
- **1.2:** [Task]

## Phase 2: [Name] ☐
- **2.1:** [Task]
- **2.2:** [Task]

## Phase 3: [Name] ☐
- **3.1:** [Task]
- **3.2:** [Task]

## Phase 4: [Name] ☐
- **4.1:** [Task]
- **4.2:** [Task]

---

# PART 3: KEY REFERENCE FILES

## Primary Files

| File | Purpose |
|------|---------|
| [path/to/file] | [purpose] |

## Documentation

| File | Purpose |
|------|---------|
| `PROGRESS_LOG.md` | Dated chronicle of all work |
| `DECISION_LOG.md` | Analytical decisions with rationale |
| `TECHNICAL_SPECS.md` | Technical specifications |

## Output Files

| File | Location |
|------|----------|
| [Output type] | [path] |

---

# PART 4: OPEN QUESTIONS & CONCERNS

## Methodological Questions
1. [Question 1]
2. [Question 2]

## Conceptual Questions
1. [Question 1]

## Writing/Presentation Questions
1. [Question 1]

## Requested Analyses/Tasks

### High Priority
1. [Task] — [Timeline]

### Medium Priority
1. [Task] — [Timeline]

### Future/Lower Priority
1. [Task] — [Timeline]

---

*This document combines project context and roadmap. Update the Current Marker as you progress.*
```

---

# SECTION 3: PROGRESS_LOG.md

```markdown
# Progress Log: [Your Project Title]

**Purpose:** Chronological record of all work completed on this project  
**Format:** Dated entries documenting decisions, findings, and changes  
**Update Instructions:** Add new entries at the TOP of each month's section

---

## Current Status (as of [Date])

**Phase:** [Current phase]  
**Roadmap Position:** [Where you are on roadmap]  
**Data Quality Status:** [Status]  
**Tomorrow's Priority:** [Next priority]  
**Next Steps:** 
1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## [Month Year]

### [Month Day, Year — HH:MM AM/PM]
**Session Focus:** [One-line description]

**Work Completed:**
- [Bullet point 1]
- [Bullet point 2]

**Key Findings:**
- [Finding 1]

**Decisions Made & Rationale:**
- **Decision:** [What was chosen]
- **Rationale:** [Why]
- **Alternatives Considered:** [What else]
- **Rejected Because:** [Why not]

**Unexpected Insights:**
- [Insight 1]

**Files Created/Modified:**
- **Created:** [file1], [file2]
- **Modified:** [file3]

**Open Questions:**
- **Methodological:** [Question]
- **Conceptual:** [Question]
- **Writing:** [Question]

**Next Steps (Immediate):**
1. [Step 1 with time estimate]
2. [Step 2 with time estimate]

**Status:** [Current roadmap position]

---

## How to Update This Log

**At the end of each chat session:**

1. Add a new entry at the TOP of the current month's section
2. Use timestamp format: "### [Month Day, Year — HH:MM AM/PM]"
3. Include all sections (even if brief)
4. Update the **Current Status** section at the top of this file

**Template:**

### [Month Day, Year — HH:MM AM/PM]
**Session Focus:** [One-line description]

**Work Completed:**
- [Bullet point 1]

**Key Findings:**
- [If applicable]

**Decisions Made & Rationale:**
- [If applicable]

**Unexpected Insights:**
- [If applicable]

**Files Created/Modified:**
- [List]

**Open Questions:**
- **Methodological:** [Question]
- **Conceptual:** [Question]
- **Writing:** [Question]

**Next Steps (Immediate):**
1. [Step with time estimate]

**Status:** [Roadmap position]
```

---

# SECTION 4: DECISION_LOG.md

```markdown
# Analytical Decision Log

**Purpose:** Systematic record of key analytical decisions, alternatives considered, and rationale  
**Format:** Most recent decisions at TOP  
**Use:** Reference when explaining methodology; ensure decisions are documented with justification

---

## [Month Year]

### [Month Day, Year]: [Decision Title]
**Decision:** [What was chosen]  
**Rationale:**
- [Reason 1]
- [Reason 2]

**Alternatives Considered:**
- [Alternative 1]
- [Alternative 2]

**Rejected Because:**
- [Reason 1]
- [Reason 2]

**Documented In:** [File names where decision is implemented]

---

## How to Use This Log

**When making new analytical decisions:**
1. Document decision clearly
2. Explain rationale (why this choice?)
3. List alternatives considered
4. State why alternatives were rejected
5. Note where decision is implemented (file names)

**When writing Methods section:**
- Reference this log for justifications
- Pull language directly from "Rationale" fields
- Cite alternatives considered to demonstrate rigor

**When responding to reviewers:**
- Show alternatives were considered systematically
- Demonstrate decisions were data-driven, not arbitrary

---

*This log is a living document. Add new decisions at the TOP of each month's section.*
```

---

# SECTION 5: TECHNICAL_SPECS.md

```markdown
# Technical Specifications — One-Stop Reference

**Purpose:** Centralized technical details for replication and onboarding  
**Last Updated:** [Date]  
**Use:** Reference when running analyses, writing methods, or onboarding collaborators

---

## PROJECT OVERVIEW

- **Project:** [Project name]
- **Type:** [Quantitative/Qualitative/Mixed Methods]
- **Primary Software:** [List main tools]

---

## DATA

### Primary Dataset
- **File:** [path/to/data]
- **Format:** [.dta/.csv/.xlsx/NVivo project/etc.]
- **N:** [Sample size or number of documents/interviews]
- **Unit of Analysis:** [What each row/case represents]
- **Time Period:** [When data collected/covers]
- **Geographic Scope:** [Where]

### Sample Characteristics
[Describe key sample characteristics]

---

## VARIABLE/CODE DEFINITIONS

### For Quantitative Projects

**Dependent Variable(s):**
| Variable | Definition | Source | Transformation |
|----------|------------|--------|----------------|
| [var1] | [definition] | [source] | [transformation] |

**Independent Variable(s):**
| Variable | Definition | Coding |
|----------|------------|--------|
| [var1] | [definition] | [coding scheme] |

**Control Variables:**
| Variable | Definition |
|----------|------------|
| [var1] | [definition] |

### For Qualitative Projects

**Code Book:**
| Code | Definition | Example |
|------|------------|---------|
| [code1] | [definition] | [example quote/instance] |

**Themes:**
| Theme | Constituent Codes | Description |
|-------|-------------------|-------------|
| [theme1] | [code1, code2] | [description] |

---

## ANALYSIS SPECIFICATIONS

### For Quantitative Projects

**Standard Model Specification:**
```
[Your standard model in appropriate syntax]
```

**Control Set:**
```
[Global macro or standard controls]
```

### For Qualitative Projects

**Coding Approach:** [Inductive/Deductive/Hybrid]
**Reliability Method:** [Inter-rater/Member checking/etc.]
**Analysis Method:** [Thematic analysis/Grounded theory/etc.]

---

## SOFTWARE & TOOLS

### Primary Software
- **Software:** [Name and Version]
- **Path:** [Installation path if relevant]
- **Key Packages/Plugins:** [List required packages]

### Secondary Tools
- [Tool 2]
- [Tool 3]

---

## FILE LOCATIONS

### Working Directory
```
[Full path to project root]
```

### Data Files
- **Raw data:** [path]
- **Processed data:** [path]

### Code/Analysis Files
- **Main analysis:** [path]
- **Utilities:** [path]

### Output Files
- **Tables/Exports:** [path]
- **Figures:** [path]
- **Logs:** [path]

### Documentation
- **Progress log:** `PROGRESS_LOG.md`
- **Project plan:** `PROJECT_MASTER_PLAN.md`
- **Decision log:** `DECISION_LOG.md`
- **Technical specs:** `TECHNICAL_SPECS.md` (this file)

### Writing Files
- **Main draft:** [path]
- **Bibliography:** [path]

---

## REPLICATION INSTRUCTIONS

### To Replicate Main Analysis

1. [Step 1]
2. [Step 2]
3. [Step 3]

---

## NAMING CONVENTIONS

### Variables/Codes
- [Convention 1]
- [Convention 2]

### Files
- [Convention 1]
- [Convention 2]

---

*This document is the single source of truth for all technical specifications. Update whenever specs change.*
```

---

# SECTION 6: MY_WORKFLOW.md

```markdown
# My Cursor Workflow — Quick Reference

**Your daily workflow for [Project Name]**  
**Updated:** [Date]

---

## 🌅 START OF SESSION

### 1️⃣ (Optional) Pull Latest from Git
```bash
git pull origin main
```

---

### 2️⃣ Start Working in Cursor
**You do:** Just start chatting with Cursor. No special prompt needed.

**Cursor automatically:**
- ✅ Reads `.cursorrules` (knows all protocols)
- ✅ Reads `PROGRESS_LOG.md` (sees recent work)
- ✅ Reads `PROJECT_MASTER_PLAN.md` (knows context)

**You don't need to:**
- ❌ Copy/paste any protocols
- ❌ Remind Cursor of the rules
- ❌ Tell Cursor what files to read

---

## 💻 DURING SESSION

**You:** Work normally — ask questions, run analyses, write, make decisions

**Cursor:** Helps you work and mentally notes what to document at the end

---

## 🌙 END OF SESSION

### 1️⃣ Update All Documentation
**Prompt Cursor with ONE sentence:**

```
Update the logs with this session's work
```

**OR the full version:**
```
Update the progress log, project master plan, and decision log with this session's work
```

**Cursor will automatically:**
- ✅ Update `PROGRESS_LOG.md` (what, why, insights, next steps)
- ✅ Update `PROJECT_MASTER_PLAN.md` (if roadmap progress)
- ✅ Update `DECISION_LOG.md` (if decisions made)
- ✅ Update `TECHNICAL_SPECS.md` (if specs changed)
- ✅ Update "Current Status" section

---

### 2️⃣ (Optional) Push to Git
```bash
git add -A
git commit -m "Session: [brief description]"
git push origin main
```

---

## 📊 VISUAL WORKFLOW

```
Session Start:
┌─────────────────────────────────────────┐
│  Start chatting with Cursor             │  ← No special prompt needed
│  (Cursor auto-reads .cursorrules)       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Work normally                          │  ← Ask, analyze, write, decide
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  "Update the logs with this             │  ← One sentence prompt
│   session's work"                       │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Cursor updates 2-4 files automatically │  ← Documentation complete
└─────────────────────────────────────────┘

Session complete!
```

---

## ⏱️ TIME PER SESSION

| Task | Time | What You Do |
|------|------|-------------|
| **Start working** | 0 seconds | Just start chatting |
| **Working** | Variable | Normal work |
| **Documentation** | 5 seconds | "Update the logs" |

**Total overhead:** ~5 seconds per session

---

## 🎯 KEY REMINDERS

### What's AUTOMATIC (Cursor does without asking):
- ✅ Reads `.cursorrules` at session start
- ✅ Reads `PROGRESS_LOG.md` and `PROJECT_MASTER_PLAN.md`
- ✅ Knows the documentation protocol
- ✅ Updates all relevant files when you prompt at end

### What YOU need to do:
- ☑️ Work normally during session
- ☑️ "Update the logs" at end (5 sec)

---

## 🆘 TROUBLESHOOTING

**Cursor seems to have forgotten context**  
→ Prompt: "Read the progress log and project master plan"

**Not sure what to work on next**  
→ Look at `PROGRESS_LOG.md` "Next Steps" section (top of file)

**Need to understand a past decision**  
→ Check `DECISION_LOG.md`

---

## 💡 ALTERNATE END-OF-SESSION PROMPTS

Any of these will trigger the full update:

- "Update the logs with this session's work" ✅ **Shortest**
- "Update the progress log, project master plan, and decision log with this session's work" ✅ Most explicit
- "Document this session" ✅ Alternative
- "Follow the session completion protocol" ✅ Formal

---

*This is your ONE workflow reference.*
```

---

# SECTION 7: writing-patterns.md

```markdown
# Writing Patterns: Academic Writing Conventions

**Project:** [Your Project Title]  
**Last Updated:** [Date]  
**Purpose:** Academic writing conventions for this project

---

## Document Structure

[Customize based on your discipline and document type]

### Standard Chapter/Paper Structure
1. Introduction
2. Literature Review / Theoretical Background
3. Methods / Data
4. Results / Findings
5. Discussion
6. Conclusion
7. References

---

## Statistical Reporting (Quantitative Projects)

### Basic Format
The analysis reveals a significant effect ($\beta = X.XX$, $SE = X.XX$, $p < 0.001$).

### With Confidence Intervals
The effect persists ($\beta = X.XX$, 95% CI $[X.XX, X.XX]$, $p < 0.001$).

### Effect Sizes
Report effect sizes alongside significance tests when possible.

---

## Qualitative Reporting (Qualitative Projects)

### Quote Integration
Use quotes to illustrate themes. Always include participant identifier.

**Format:**
> "Quote text here" (Participant 3, Interview)

### Theme Reporting
When reporting themes, include:
- Theme name and definition
- Prevalence (how many participants/documents)
- Representative quotes
- Variation within theme

---

## Causal Language

**❌ AVOID (unless causal design):**
- "causes"
- "leads to"
- "results in"

**✅ USE INSTEAD:**
- "is associated with"
- "predicts"
- "is related to"
- "suggests"

---

## Reporting Sample Sizes

**Always include N:**
The analysis includes $N = X,XXX$ [units].

---

## Punctuation Preferences

### Em-Dashes
**Avoid em-dashes in text content.** Instead, use:
- **Commas** for parenthetical asides
- **Parentheses** for explanatory clauses
- **Colons** for elaborations
- **Semicolons** where appropriate

---

## Citation Patterns

[Customize based on your citation style]

### In-Text
Single author: (Smith, 2020)
Multiple authors: (Smith & Jones, 2020)
Author-year: Smith (2020) argues...

---

## Common Errors to Avoid

- Use "causes" for cross-sectional data → Use "is associated with"
- Overstate significance → Report p-values precisely
- Forget sample sizes → Always include N
- Inconsistent formatting → Use templates

---

## Checklist for Final Draft

### Content
- [ ] All key findings reported
- [ ] Limitations acknowledged
- [ ] Alternative explanations considered

### Formatting
- [ ] Consistent notation throughout
- [ ] All tables/figures included and referenced
- [ ] Citations formatted correctly

### Language
- [ ] Appropriate causal language
- [ ] Academic tone throughout
- [ ] Clear transitions between sections

---

*Update this document as writing conventions evolve.*
```

---

# SECTION 8: deck.md

```markdown
# The Rhetoric of Decks

## What This Document Is

Tacit knowledge for effective slide presentations — the unwritten rules that govern what makes a deck work.

---

## The Fundamental Tension

A deck exists between two failure modes:

1. **The document pretending to be slides**: Walls of text. Speaker becomes redundant.
2. **The mystery slides**: So sparse they're meaningless without the speaker.

A good deck is *incomplete on purpose* but *structured enough* to scaffold understanding.

---

## Core Principles

### 1. One Idea Per Slide
Each slide is one idea. Not one topic. One *idea*.

Test: Can you state the slide's idea in one sentence?

### 2. Titles Are Assertions, Not Labels

**Weak**: "Results"  
**Strong**: "Women receive 18% fewer views on average"

If someone reads only your slide titles, they should understand your argument.

### 3. The Pyramid Principle
Lead with the conclusion. Then support it.

Structure:
1. Here's what I'm going to tell you (the claim)
2. Here's the evidence for it
3. Here's why it matters

### 4. Visual Hierarchy Is Meaning
What's big is important. What's first is important.

Use size, position, and space to do cognitive work for the audience.

### 5. Bullets Are a Confession of Defeat
Usually there's a structure hiding in your bullets:
- A sequence (first, then, finally)
- A contrast (on one hand, on the other)
- A hierarchy (main point, supporting details)
- A causal chain (because of X, we see Y)

Find the structure. Make it visible.

### 6. Tables and Figures Carry the Weight
- Highlight the one or two key results
- Use color or boxes to draw the eye
- The figure should be readable from the back of the room

### 7. Repetition Is Structure
Tell them what you'll tell them. Tell them. Tell them what you told them.

### 8. Transitions Are Invisible Architecture
"So we've established X. Now the question is Y."

### 9. The Audience Is Not You
They need:
- The main point, stated clearly
- Enough evidence to believe it
- A reason to care

The deck is the trailer, not the movie.

### 10. Anxiety Makes Decks Worse
Dense slides are harder to present. Sparse slides force you to know your material.

---

## Technical Excellence

### Preventing LaTeX Errors
- Test figure sizes explicitly (use `width=0.85\textwidth` or smaller)
- Break long lines explicitly
- Test table column widths

### Design Standards
- Figures fit completely within slide boundaries
- Text readable from back of room (minimum 12pt)
- Consistent font sizes for similar content
- Sufficient color contrast

---

## Progress Decks (Internal Documentation)

**Universal Rule:** Show what you've found AND what you've ruled out.

For each major finding, include:
1. What we found (positive result)
2. What we ruled out (alternatives tested)
3. What's still open (remaining questions)

---

## Quality Checklist

- [ ] No overfull box warnings
- [ ] All figures fit within boundaries
- [ ] All text readable
- [ ] Consistent formatting
- [ ] Professional appearance

---

*These are patterns, not rules — defaults to deviate from intentionally.*
```

---

# SECTION 9: Folder Structure

Create these folders in your project root:

```
[project_root]/
├── .git/                     ← Git repository (created by `git init`)
├── .agent/                   ← Antigravity configuration (optional)
│   └── ANTIGRAVITY_RULES.md  ← Antigravity-specific rules
├── .gitignore                ← Git ignore rules (copy from Section 12)
├── .cursorrules              ← AI rules (auto-read by Cursor)
├── AI_RULES.md               ← Same as .cursorrules (for other AI tools)
├── PROJECT_MASTER_PLAN.md    ← Roadmap and context
├── PROGRESS_LOG.md           ← Chronological work log
├── DECISION_LOG.md           ← Analytical decisions
├── TECHNICAL_SPECS.md        ← Technical specifications
├── MY_WORKFLOW.md            ← Daily workflow reference
├── writing-patterns.md       ← Writing conventions
├── deck.md                   ← Presentation guidelines
├── README.md                 ← (Optional) Project overview
│
├── code/                     ← Analysis scripts
│   └── [analysis files]
│
├── data/                     ← Data files
│   ├── raw/                  ← Original, untouched data
│   └── processed/            ← Cleaned/transformed data
│
├── output/                   ← Analysis outputs
│   ├── tables/               ← Exported tables
│   ├── figures/              ← Generated figures
│   └── logs/                 ← Analysis logs
│
├── drafts/                   ← Writing
│   ├── [main draft files]
│   └── documentation/        ← Methods documentation, etc.
│
└── archive/                  ← Retired/superseded files
```

---

# SECTION 10: Customization Guide

## For Quantitative Projects

1. **TECHNICAL_SPECS.md**: Fill in variable definitions, model specifications, software versions
2. **writing-patterns.md**: Add statistical reporting conventions specific to your discipline
3. **.cursorrules**: Add discipline-specific coding standards (Stata, R, Python)

## For Qualitative Projects

1. **TECHNICAL_SPECS.md**: Fill in code book, theme definitions, analysis approach
2. **writing-patterns.md**: Add qualitative reporting conventions
3. **.cursorrules**: Add software-specific rules (NVivo, Atlas.ti, MAXQDA)

## For Mixed Methods Projects

1. Include sections for both quantitative and qualitative in TECHNICAL_SPECS.md
2. Add conventions for integrating findings in writing-patterns.md
3. Consider separate analysis folders for qual and quant

---

# SECTION 11: Quick Reference Card

## First Time Setup (New Project or New Agent)
**Give this command to your AI agent:**
```
Read MY_WORKFLOW.md, PROJECT_MASTER_PLAN.md, PROGRESS_LOG.md, and .cursorrules to understand this project's workflow, context, and documentation system. Then check if all required documentation files exist and help set up any missing ones.
```

## Session Start
Just start chatting. Cursor reads `.cursorrules` automatically.

## Session End
Prompt: **"Update the logs with this session's work"**

## Key Files
| File | Purpose | Update Frequency |
|------|---------|-----------------|
| `.cursorrules` | AI rules | Rarely |
| `PROJECT_MASTER_PLAN.md` | Roadmap | When progress made |
| `PROGRESS_LOG.md` | Work chronicle | Every session |
| `DECISION_LOG.md` | Decision rationale | When decisions made |
| `TECHNICAL_SPECS.md` | Technical details | When specs change |

## Safety Rules
- ❌ NEVER delete data or code files
- ✅ ALWAYS copy, don't move
- ✅ ALWAYS preserve originals
- ✅ Use `archive/` for retired files

## Git Setup
- ✅ Initialize Git repository for new projects
- ✅ Create `.gitignore` before first commit
- ✅ Connect to GitHub repository
- ✅ Commit documentation files first

---

# SECTION 12: Git Repository Setup

## Initialize Git Repository

**For a new project, always initialize a Git repository:**

```bash
# Navigate to your project root directory
cd /path/to/your/project

# Initialize Git repository
git init

# Create initial commit with documentation files
git add .cursorrules AI_RULES.md PROJECT_MASTER_PLAN.md PROGRESS_LOG.md DECISION_LOG.md TECHNICAL_SPECS.md MY_WORKFLOW.md writing-patterns.md deck.md .gitignore
git commit -m "Initial commit: Project documentation setup"
```

## Connect to GitHub Repository

**After creating a repository on GitHub:**

```bash
# Add remote repository (replace with your GitHub URL)
git remote add origin https://github.com/yourusername/your-repo-name.git

# Or if using SSH:
git remote add origin git@github.com:yourusername/your-repo-name.git

# Push initial commit
git branch -M main
git push -u origin main
```

**Note:** Replace `yourusername` and `your-repo-name` with your actual GitHub username and repository name.

## .gitignore File

**Create `.gitignore` in your project root with the following content:**

```gitignore
# Large data files - should not be in git
*.dta
*.csv
*.xlsx
*.xls
*.sav
*.sas7bdat
*.rdata
*.rda

# LaTeX compiled outputs
*.pdf
*.aux
*.log
*.bbl
*.blg
*.fdb_latexmk
*.fls
*.synctex.gz
*.out
*.toc
*.nav
*.snm

# OS files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
Thumbs.db

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/
venv/
env/

# R
.Rhistory
.RData
.Ruserdata
*.Rproj.user/

# Stata
*.smcl
*.log

# Statistical software outputs
*.spv
*.spo

# Qualitative analysis software
*.nvp
*.hpr
*.mx1

# Temporary files
*.tmp
*.temp
*~
*.swp
*.swo

# Google Drive files
*.gdoc
*.gsheet

# IDE/Editor files
.vscode/
.idea/
*.sublime-project
*.sublime-workspace

# Jupyter Notebook checkpoints
.ipynb_checkpoints/

# Environment variables and secrets
.env
.env.local
config/secrets.yaml

# Large output files
output/figures/*.png
output/figures/*.jpg
output/tables/*.pdf
output/logs/*.smcl

# Archive folder (optional - you may want to track some archived files)
# Uncomment if you want to ignore everything in archive/
# archive/*
```

**Customize for your project:**
- Add file extensions specific to your analysis software
- Add paths to large datasets that should never be committed
- Adjust output folder exclusions based on your needs
- Consider whether you want to track some files in `archive/` or ignore them all

**Important:** The `.gitignore` file should be committed to your repository so all collaborators use the same ignore rules.

---

# SECTION 13: Antigravity-Specific Setup

## Antigravity Rules File

**Antigravity** (Google's AI coding assistant) uses `ANTIGRAVITY_RULES.md` in the `.agent/` directory as its equivalent to `.cursorrules`.

### Setup Instructions

1. **Create `.agent/` directory** (if it doesn't exist):
   ```bash
   mkdir -p .agent
   ```

2. **Create `ANTIGRAVITY_RULES.md`** based on `AI_RULES.md`:
   - Copy `AI_RULES.md` as a starting point
   - Add Antigravity-specific sections (see below)
   - Place in `.agent/ANTIGRAVITY_RULES.md`

### Antigravity-Specific Additions

Add these sections to your `ANTIGRAVITY_RULES.md`:

```markdown
# ANTIGRAVITY-SPECIFIC WORKFLOWS

## Task Mode Usage
- **PLANNING Mode:** Use when researching codebase, understanding requirements, or designing approach
  - Create `implementation_plan.md` artifact in brain directory
  - Request user review via `notify_user` before proceeding
- **EXECUTION Mode:** Use when actively writing code or making changes
  - Update `task.md` artifact to track progress
  - Switch to PLANNING if unexpected complexity arises
- **VERIFICATION Mode:** Use when testing changes, validating correctness
  - Create `walkthrough.md` artifact documenting results
  - Include terminal output, test results, visual evidence

## Artifact Strategy
- **task.md**: Detailed checklist broken down by component-level items
- **implementation_plan.md**: Technical plans during PLANNING mode requiring user review
- **walkthrough.md**: Post-work summary with screenshots/recordings of verification
- Store all artifacts in Antigravity brain directory (auto-created)

## Command Execution Guidelines
- Use `SafeToAutoRun: true` for read-only commands (ls, cat, grep)
- Use `SafeToAutoRun: false` for any analysis scripts, data processing, or file modifications
- For statistical analysis: Always propose commands, never auto-run
- For data processing: Require user approval before execution

## Antigravity Tool Usage Guidelines

### File Operations
- Use `view_file` to read existing code/data files
- Use `find_by_name` and `grep_search` to explore codebase structure
- Use `write_to_file` for new files, `replace_file_content`/`multi_replace_file_content` for edits
- Always use absolute paths in Antigravity tools

### Terminal Commands
- Propose analysis commands with `run_command` (SafeToAutoRun: false)
- For data processing scripts: require user approval before execution
- Use `read_terminal` to capture output for analysis
- Document terminal session results in walkthrough.md

### Artifact Formatting
- Use GitHub Flavored Markdown for all artifacts
- Embed code using fenced blocks with language tags
- Use diff blocks to show changes
- Link to files: `[basename](file:///absolute/path)` 
- Embed images/recordings: `![caption](/absolute/path)`
- Use alerts (NOTE, IMPORTANT, WARNING, CAUTION) strategically
```

### File Location

```
[project_root]/
├── .agent/
│   └── ANTIGRAVITY_RULES.md    ← Antigravity-specific rules
├── .cursorrules                ← Cursor rules (auto-read)
└── AI_RULES.md                 ← Universal rules (for Claude, etc.)
```

**Note:** All three files should contain the same core rules, with Antigravity's file including additional Antigravity-specific workflows.

---

*This template was developed through extensive use in PhD dissertation research. Customize for your specific needs while maintaining the core documentation workflow.*

