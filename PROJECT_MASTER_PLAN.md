# PROJECT MASTER PLAN: YouTube Longitudinal Data Collection

**Purpose:** Comprehensive project context and roadmap  
**Last Updated:** Feb 02, 2026  
**Current Status:** Implementation Phase (Script Creation)

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

**Now:** Phase 3: Validation & Dry Run  
**Last Session:** Feb 02, 2026 — Finalized Discovery Suite (Steam A/B/C) & Consolidated Documentation  
**Next:** Execute 24-Hour Dry Run & Verify Quotas

---

# PART 1: PROJECT CONTEXT

## Research Question and Objectives

**Primary Research Question:**  
What are the early-stage drivers of distinctiveness and virality for new cultural producers?

**Objectives:**
1.  **Capture Phase:** Track a cohort of "New Intentional Creators" (Jan 2026) from Day 0.
2.  **Compare Phase:** Contrast their trajectory with a "Visible Market" baseline and a "Deep Random" survivorship control.
3.  **Analyze Phase:** Measure distinctiveness (text/visual) and strategic choices (frequency, categories) over time.

## Data Infrastructure (Triple-Stream Design)

**Stream A: The "Intentional Cohort" (Treatment)**
- **Target:** New Entrepreneurs (Vloggers, etc.)
- **Method:** Targeted Keywords (`Welcome`, `Intro`) -> Filter for Creation Date >= Jan 1, 2026.
- **Yield:** ~17,000/day.

**Stream B: The "Visible Market" (Control)**
- **Target:** Active Ecosystem (What people see).
- **Method:** Vowel Rotation (`a`, `e`, `i`) -> Filter for Active channels.
- **Yield:** ~50,000/day.

**Stream C: The "Deep Random" (Survivorship)**
- **Target:** The "Dark Matter" (Hidden long tail).
- **Method:** Random Prefix (`xyz`) -> Unbiased sample.
- **Yield:** ~2,500/day.

## Key Findings (To Date)

| Finding | Evidence | Interpretation |
|---------|----------|----------------|
| **Rank Bias** | Vowel search med. views = 652k | "Random" searches find popular content. |
| **Dark Matter** | Prefix search med. views = 22 | True random sampling finds invisible content. |
| **New Creators** | Targeted search yield = 6.3% | Finding new creators requires intent signals. |

---

# PART 2: ROADMAP

## Roadmap Overview
**[Phase 1: Planning] → [Phase 2: Implementation] → [Phase 3: Validation] → [Phase 4: Longitudinal Tracking]**

---

## Phase 1: Planning (Completed) ☑
- **1.1:** Research Design Evaluation (Done)
- **1.2:** Bias Diagnostic & Sampling Strategy (Done)
- **1.3:** Tech/File Structure Setup (Done)

## Phase 2: Implementation (Completed) ☑
- **2.1:** Script: `discover_cohort.py` (Stream A) [Done]
- **2.2:** Script: `discover_visible.py` (Stream B) [Done]
- **2.3:** Script: `discover_deep_random.py` (Stream C) [Done]
- **2.4:** Data Storage & Schema Design [Pending - using CSV for now]

## Phase 3: Validation & Dry Run (In Progress) ☐
- **3.1:** 24-Hour Full-Scale Test
- **3.2:** Quota Consumption Audit
- **3.3:** Bias Verification on full dataset

## Phase 4: Longitudinal Tracking ☐
- **4.1:** Automated Daily Scheduling (launchd)
- **4.2:** Video History Monitoring
- **4.3:** Comment Collection

---

# PART 3: KEY REFERENCE FILES

## Documentation
| File | Purpose |
|------|---------|
| `PROGRESS_LOG.md` | Dated chronicle of all work |
| `DECISION_LOG.md` | Analytical decisions with rationale |
| `TECHNICAL_SPECS.md` | Technical specifications (Sampling details) |
| `AI_RULES.md` | Agent rules & Ten Commandments |

---

# PART 4: OPEN QUESTIONS

## Methodological
1.  **Quota Sustainability:** Will 700k units/day trigger any secondary rate limits?
2.  **Storage:** Do we need a database (SQL) immediately, or can we stick to partitioned CSVs for the first month?

## Conceptual
1.  **"Intent" definition:** Are keywords like "Welcome" sufficient proxy for entrepreneurial intent? (Validated by visual inspection so far).
