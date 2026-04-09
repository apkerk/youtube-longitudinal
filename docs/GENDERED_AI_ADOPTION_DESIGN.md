# Gendered AI Adoption: Research Design Document

**Purpose:** Research design specification for studying how tool characteristics shape gendered participation in AI content creation on YouTube.
**Created:** April 9, 2026
**Status:** Data infrastructure being built

---

## 1. Research Question

As AI tools diffuse from technically demanding, coded-masculine spaces (programming, prompt engineering) toward mainstream, accessible applications (design, video editing, writing), does the gender composition of AI content creators shift? Do tool characteristics causally predict WHO adopts?

**Core theoretical argument:** AI tools are not adopted uniformly across demographic groups. The gender composition of AI content creators is shaped by tool characteristics: how technically demanding they are and how gender-typed their user communities are. Tool launches create exogenous shocks that expand the choice set of AI capabilities, and the gendering of each new tool predicts who responds.

**Theoretical foundations:**
- Ridgeway & Correll (2004): gender beliefs activated by contextual cues (sex composition, gender-typed tasks)
- Abraham (2020): audience-based gender bias in male-typed domains
- Glick & Fiske (2001): benevolent sexism framework
- Wajcman (2004), Cockburn (1985): gendered technology adoption
- Extension: tool characteristics create the "contextual cues" that activate or deactivate gender schemas

---

## 2. Two Complementary Designs

### Design A: AI Adoption Among Established Creators (Within-Creator, Staggered DiD)

**Question:** Among established knowledge-economy creators, do women adopt AI tools at different rates depending on tool techiness?

**Population:** Knowledge Economy Census -- pre-2023 channels in 10 knowledge/strategy domains. NOT sampled on AI content. Channels discovered via domain-defining keywords (business tips, productivity, design tutorial, etc.) in pre-AI video content.

**Treatment:** First AI-related video (detected by keyword flagger, run AFTER collection). Treatment timing is staggered across creators.

**Identification:** Stacked event-study DiD around tool launches. Each major tool release is a natural experiment. The gender x post-launch interaction measures differential adoption. The gender x post-launch x tool-techiness triple interaction tests whether techier tools produce larger gender gaps.

**Key specification:**
```
Y_{i,t} = alpha_i + gamma_t + sum_k [beta_k + delta_k * Female_i] * 1{t - LaunchDate_j = k} + X_{i,t} * delta + epsilon_{i,t}
```

Where delta_k coefficients trace the gender gap in adoption week-by-week around each launch. Sort launches by techiness: high-techiness should show larger positive delta_k (bigger male advantage).

**Parallel trends assumption:** Testable via pre-period event-study coefficients. Must be flat.

**Strengths:** Within-creator variation, channel FE absorb unobservables, clean pre-treatment baseline, no selection on DV.

**Threats:** Category sorting (women in mainstream categories adopt mainstream tools). Defense: category FE + within-category analysis + three-way interaction.

### Design B: Gendered Entry Around Tool Launches (Temporal Cohorts)

**Question:** When a new AI tool launches, who creates new channels to cover it? Does the gender composition of new entrants shift as tools become more mainstream?

**Population:** Channels born in temporal windows around tool launches. Discovered via the SAME domain keywords as Design A, applied to time windows around each launch event. NOT sampled on AI content.

**Identification:** Quasi-regression-discontinuity. Channels born just before vs. just after a tool launch are exposed to different AI-tool environments. Compare AI content production rates and gender composition across treatment and control windows.

**For each of ~15-20 tool launches:**
- Treatment window: 4 weeks pre-launch through 12 weeks post-launch
- Control window: Same calendar weeks one year prior (controls for seasonality)
- Discovery: Domain keywords in each window, filter to channels CREATED during that window
- Measurement: AI flagger on all channels' videos (run AFTER collection)
- Outcome 1: Share producing AI content (extensive margin)
- Outcome 2: Gender composition of AI-content channels

**Strengths:** Zero selection on DV. Temporal sampling frame is clean. Complementary to Design A (entry vs. adoption).

**Threats:** Channels born in a "post-ChatGPT" window may differ from pre-launch channels on unobservables correlated with both gender and AI interest. Defense: control windows, seasonal matching, narrow bandwidth around launch date.

---

## 3. The Knowledge Economy: 10 Domains

The risk set spans all YouTube content domains where AI tools are topically relevant to creators' existing subject matter:

| # | Domain | Why at risk | Example keywords |
|---|--------|------------|-----------------|
| 1 | Business / Entrepreneurship | AI writing, automation, strategy tools | business tips, startup advice, business strategy |
| 2 | Marketing / SEO | AI content generation, ad optimization | marketing strategy, SEO tutorial, digital marketing |
| 3 | Productivity / Workflow | AI assistants, automation tools | productivity tips, workflow optimization, notion tutorial |
| 4 | Tech Reviews / Software | Direct coverage of AI tools | software tutorial, app review, tech tutorial |
| 5 | Design / Creative Tools | AI image/video generation | graphic design tutorial, photoshop tutorial, video editing |
| 6 | Education / Online Teaching | AI tutoring, course creation | online teaching, education technology, online course |
| 7 | Freelancing / Consulting | AI augmenting service delivery | freelancing tips, consulting business, remote work |
| 8 | Finance / Investing | AI trading, financial planning tools | investing strategy, personal finance, cryptocurrency |
| 9 | Programming / Web Dev | AI coding assistants | web development tutorial, python tutorial, coding tutorial |
| 10 | Content Creation Meta | AI for content production itself | how to grow on youtube, content creation tips, podcasting |

**Critical sampling constraint:** NO AI-specific keywords in the discovery phase. All keywords are domain-defining (describe the channel's pre-AI subject matter). The AI flagger runs AFTER collection to identify adoption. Clean separation between sampling frame and outcome measurement.

---

## 4. Tool Launch Calendar

Each tool launch is characterized by:
- launch_date (public availability)
- tool_category (coding / image_video / audio_music / content_creation / general_ai)
- techiness_score (1-10 composite: interface type, coding required, install complexity, community origin)
- target_audience (developer / creative_professional / general_public)
- keyword_subcategory (maps to AI_FLAG_KEYWORDS tool-specific keys)

**Illustrative launches (not exhaustive):**

| Tool | Date | Category | Techiness | Audience |
|------|------|----------|-----------|----------|
| GitHub Copilot GA | Jun 2022 | coding | 9 | developer |
| Stable Diffusion open source | Aug 2022 | image_video | 8 | developer |
| ChatGPT launch | Nov 30, 2022 | general_ai | 2 | general_public |
| Midjourney V5 | Mar 2023 | image_video | 5 | creative_professional |
| GPT-4 | Mar 14, 2023 | general_ai | 3 | general_public |
| Runway Gen-2 | Jun 2023 | image_video | 4 | creative_professional |
| DALL-E 3 (in ChatGPT) | Oct 2023 | image_video | 2 | general_public |
| Suno V3 | Mar 2024 | audio_music | 3 | general_public |
| Sora announcement | Feb 2024 | image_video | 4 | creative_professional |
| Claude Code | Jan 2026 | coding | 8 | developer |
| Cursor AI growth | 2024-2025 | coding | 7 | developer |
| Canva AI features | Rolling 2023-2024 | content_creation | 1 | general_public |
| CapCut AI features | Rolling 2023-2024 | content_creation | 1 | general_public |
| ElevenLabs TTS | Early 2023 | audio_music | 4 | creative_professional |

Full calendar with exact dates: data/processed/tool_launch_calendar.csv (to be constructed)

---

## 5. Category Dimension: Mainstream-to-Techy Continuum

**For tools:** Techiness is a composite of observable characteristics:
1. Interface type (1=embedded in existing app, 2=web GUI, 3=desktop, 4=Discord, 5=CLI, 6=API-only, 7=local model hosting)
2. Required technical knowledge (binary: does documentation assume coding?)
3. Installation complexity (1=none, 2=simple, 3=environment setup, 4=GPU config)
4. Community of origin (1=consumer app store, 2=creative professional, 3=dev tools, 4=ML research)

Validate with independent expert survey (5-10 raters, compute ICR).

**For content categories:** Use baseline female share (from gender-coded panels, pre-AI) as the category-level gender-typing measure. Categories range from Science & Technology (low female share) to Howto & Style (higher female share).

**The three-way interaction:** gender x tool_techiness x category_gender_typing. Prediction: women adopt fastest when BOTH the tool AND the category are low-techiness/mainstream.

---

## 6. Gender Coding Strategy

**Approach:** Hybrid algorithmic + validation.

**Primary method:** FairFace (Karkkainen & Joo 2021) on channel profile photos and video thumbnails.
- Open source, balanced training set across 7 racial groups
- Provides gender + race predictions with confidence scores
- Validate against 9,760 hand-coded Gender Gap Panel channels (ground truth)
- Target: >90% accuracy on binary male/female, <5pp differential accuracy

**Supplementary:** Name-based inference (Genderize.io/NamSor) for no-face channels.
**Manual review:** Low-confidence + no-face flagged for RA coding.

**Ethical framing:** "Perceived gender presentation" (consistent with JMP and with the theoretical mechanism, which is about how audiences process gender cues).

**Key citations:** Karkkainen & Joo 2021 (FairFace), Buolamwini & Gebru 2018 (Gender Shades), Keyes 2018 (Misgendering Machines), Schwemmer et al. 2020 (face detection in media research)

**Critical note:** Gender coding should NOT limit data collection ambition. Tools are improving rapidly. Collect data now, code gender later. (See also: Frieman et al. on automated gender detection for YouTube creators.)

---

## 7. Data Infrastructure

### Existing (already collecting):
| Panel | N | Daily stats? | Video inventory? | Gender? |
|-------|---|-------------|-----------------|---------|
| Gender Gap Panel | 9,760 | Yes (since Mar 5) | Yes (11.7M) | Yes (hand-coded) |
| Tech Census | 63,728 | Yes (since Apr 6) | **No (needs enumeration)** | No |
| AI Census | 50,010 | Yes (since Mar 5) | Yes (5.3M, 80%) | No |
| Category Quota | 73,508 | Yes (since Apr 8) | **No** | No |
| New Cohort (A+A') | 135,977 | Yes (since Apr 9) | No | No |
| April Cohort | 22,594+ | Yes (since Apr 9) | No | No |

### New streams needed:
| Stream | Target N | Pre-2023? | Sampled on AI? | Design served |
|--------|----------|-----------|---------------|---------------|
| **Knowledge Economy Census** | 100K+ | Yes | **No** | Design A (adoption DiD) |
| **Entry Cohort Discovery** | 50-100K | No (temporal windows) | **No** | Design B (gendered entry) |

### Processing pipeline:
1. Run AI flagger on all video inventories (Gender Gap DONE: 40,355 flagged / 11.8M)
2. Enumerate Tech Census + KE Census + Entry Cohorts (video inventories needed for flagger)
3. Gender code all panels (FairFace + validation)
4. Construct tool launch calendar
5. Extend AI_FLAG_KEYWORDS with tool-specific subcategories
6. Merge analysis dataset: channel metadata + gender + AI flags + daily stats + tool calendar

---

## 8. Threats to Identification + Defenses

| Threat | Design | Defense |
|--------|--------|---------|
| Selection on DV | A | KE Census uses domain keywords, not AI keywords. Flagger runs post-collection. |
| Selection on DV | B | Entry cohorts use domain keywords + temporal windows. No AI keywords. |
| Category sorting | A | Category FE + within-category analysis + three-way interaction |
| Endogenous tool launches | A, B | Dates driven by product dev timelines, not YouTube demographics. Falsification: no pre-trend effects. |
| Gender coding error | A, B | Validate against 9,760 hand-coded. Report confusion matrix. Robustness to hand-coded subsample. |
| Parallel trends violation | A | Event-study pre-period coefficients. Rambachan & Roth (2023) sensitivity. |
| Keyword flagger measurement error | A, B | Validate on human-coded sample. Non-differential by gender (attenuates, doesn't bias). |
| Seasonality confounds in entry | B | Control windows one year prior. Calendar-week matching. |

---

## 9. Research Questions Answerable from This Infrastructure

### From Design A (Adoption, within-creator):
1. Do women adopt AI content at different rates than men, conditional on being in the same content category?
2. Does the gender gap in adoption widen for techier tools (coding AI) vs. shrink for mainstream tools (ChatGPT, Canva AI)?
3. Among adopters, do women produce different types of AI content (subcategory distribution)?
4. Does AI adoption differentially affect subscriber growth for men vs. women?
5. Do the earliest adopters within a category look different (gender, channel size, content focus) than later adopters?

### From Design B (Entry, temporal cohorts):
6. When a new AI tool launches, does the gender composition of new knowledge-economy channel founders shift?
7. Is the shift larger for mainstream tools (Canva AI, ChatGPT) than techy tools (Copilot, Claude Code)?
8. Do new entrants around tool launches have different survival rates by gender?
9. Does the overall female share of knowledge-economy YouTube increase as AI tools become more accessible?

### From combining A + B:
10. Is the gendered adoption pattern among EXISTING creators mirrored in the entry pattern of NEW creators?
11. Do "born AI-native" channels (created post-tool-launch) grow faster than channels that adopted AI later?
12. Does the AI adoption gap between men and women narrow over the 2022-2026 arc as tools mainstream?

### Future extensions (using this data):
13. Audience response to gendered AI content (Design 4 from SAMPLING_ARCHITECTURE, using within-creator video-level variation)
14. AI adoption cascades: does seeing same-gender creators use AI tools increase adoption? (network/exposure design, requires comment/subscription data)
15. Cross-platform comparison if comparable TikTok/Instagram data becomes available

---

## 10. Pre-Registration Plan

**Register AFTER descriptive statistics (Step 2) but BEFORE running event studies.**

Pre-register:
- Tool launch calendar (specific tools, dates, techiness ratings)
- Regression specifications (interactions, FE, controls)
- Gender coding methodology and validation protocol
- AI keyword list
- Primary outcome variables and predicted effect directions
- Minimum sample size thresholds per event study

**Where:** OSF or AsPredicted. ASQ and OS increasingly value pre-registration.
