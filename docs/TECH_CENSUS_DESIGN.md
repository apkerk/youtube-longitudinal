# Tech Census Stream: Design Document

## Purpose

Discover and track ~50,000 Technology-tagged YouTube channels created before January 2023 (pre-AI mainstream wave). This sample enables a staggered difference-in-differences study of gender differences in AI content adoption among established tech creators.

## Research Design Context

**Core question:** Among tech YouTubers who existed before the AI wave, do men and women differ in (a) when they begin covering AI topics, (b) how intensely they cover AI, and (c) the audience response they receive for AI content?

**Why a new sample:** The existing gender gap panel (9,760 channels from Infludata/Bailey's) has only 640 Technology-tagged channels, of which 74 are women. Too small for a staggered DiD with gender interaction. A dedicated tech census at 50K provides statistical power and a sample defined by tech content production, not influencer marketing.

**Pre-AI creation filter:** Channels must be created before January 1, 2023 (pre-ChatGPT mainstream adoption). This ensures we observe channels that were producing tech content BEFORE AI tools became widely available, establishing a clean pre-treatment baseline. Going back to at least 2010 captures forward-looking creators who may have covered AI/ML topics early.

**Identification strategy:** Staggered DiD (Callaway & Sant'Anna 2021). Treatment = first AI-related video (detected via keyword flagging on video titles/descriptions). Channels adopt at different times. Never-adopters within the tech sample serve as the comparison group. Gender interacted with treatment to estimate differential adoption rates and returns.

**Candidate theoretical mechanisms (to be developed at the analysis stage):**
- Gender-role congruity: tech and AI are male-typed domains; women face incongruity penalties for entering (Abraham 2020, Kanze 2018)
- Audience expectation effects: women tech creators may face different audience responses to AI pivots, discouraging adoption
- Differential access to AI communities and tools: gendered networks may route AI information faster to men
- Risk tolerance in content pivoting: adopting AI content is a strategic bet; gender differences in entrepreneurial risk-taking are well-documented

**Pre-analysis considerations (for the eventual research design, not this collection plan):**
- Parallel trends: verify via event study plots that treated and never-adopter channels had parallel engagement trajectories pre-adoption
- Never-adopter selection: channels that never adopt AI may differ systematically from eventual adopters (larger audience, more niche focus, different upload cadence). Pre-treatment channel characteristics (subscriber count, upload frequency, topic breadth, channel age) should be used as covariates or for coarsened exact matching to address this threat
- Robustness: test sensitivity to alternative pre-AI cutoff dates (2020, 2021, 2022-06, 2022-11)
- AI keyword validation: human-label a sample of ~500 flagged videos to estimate precision/recall of the 101-keyword list separately; minimum acceptable: precision >0.8, recall >0.6 (to be refined after validation). Distinguish "discussing AI" from "producing with AI" where possible
- Subcategory heterogeneity: analyze adoption patterns separately for hardware reviewers, programmers, and tech commentators

---

## Discovery Architecture: Three Methods

### Method 1: TopicId Discovery (primary volume)

**Approach:** Use YouTube search API with `topicId=/m/07c1v` (Technology) to find videos in the technology category, then extract unique channel IDs.

**Parameters:**
- topicId: `/m/07c1v` (Technology)
- Time windows: 24-hour windows across January 2015 through December 2022 (8 years)
  - ~2,920 windows total
  - Lesson learned from Stream A: 24h windows find 3.5x more unique channels than 48h windows (API caps results per query at ~500)
- Sort orders: `date`, `relevance`, `viewCount` (three passes per window for channel diversity)
- Max pages: 10 per query (500 results max per API response set)
- Region codes: rotate through 15 YouTube markets (US, IN, BR, GB, JP, DE, FR, RU, KR, MX, ID, CA, AU, IT, ES), one region per time window. Each window gets ONE region (cycling), not all 15. This matches the quota math below.
- Strategies: base, safesearch, regioncode (adapted from discover_intent.py pattern)

**Expected yield:** ~30,000-40,000 unique channels (before filtering)

**Quota cost:** ~2,920 windows × 3 sort orders × 10 pages × 100 units = ~8.76M units over ~9 days. Region cycling is built into the window rotation (each of 2,920 windows gets 1 of 15 regions), NOT multiplied by 15.

**Key advantage:** High volume, catches channels actively publishing tech content across the full pre-AI period.

### Method 2: Keyword Discovery (catches untagged channels)

**Approach:** Search for tech content using text keywords WITHOUT the topicId filter. Many tech channels are tagged only as "Knowledge" or "Entertainment" by YouTube's classifier. Keyword searches find them.

**Keywords (4 categories, ~35 terms):**

Programming/Development:
- "coding tutorial", "programming tutorial", "python tutorial", "javascript tutorial"
- "software development", "web development", "code review", "github"
- "developer", "full stack", "frontend backend"

Hardware/Gadgets:
- "tech review", "gadget review", "unboxing", "PC build", "laptop review"
- "smartphone review", "best tech", "tech comparison"

General Technology:
- "technology explained", "how it works", "software review", "app review"
- "tech news", "tech tips", "digital", "automation"

Multilingual tech terms:
- "tutoriel programmation" (FR), "tutorial de programacion" (ES)
- "テック レビュー" (JP), "технологии" (RU), "기술 리뷰" (KR)

**Time windows:** Same 24h windows across 2015-2022
**Sort orders:** date, relevance
**Max pages:** 5 per query (keywords are noisier than topicId)

**Expected yield:** ~15,000-25,000 unique channels (before filtering). High overlap with Method 1, but catches 5,000-10,000 channels that Method 1 misses.

**Post-hoc filter (two-stage):** After extracting channel IDs, apply a two-stage tech channel verification:
- Stage 1 (topic check): Channel has Technology, Software, Computer, or Gadget in any of topic_1/2/3. Channels passing Stage 1 are included.
- Stage 2 (content screen, for channels tagged Education, Entertainment, People & Blogs, Knowledge, Science, or How-to & Style): Sample 10 video titles per channel. If >30% contain tech keywords (from the Method 2 keyword list), include the channel. The 30% threshold will be calibrated via pilot on the 640 known tech channels in the gender gap panel; if sensitivity analysis suggests a different threshold, adjust before production. This catches real tech creators (e.g., MKBHD tagged Entertainment, Fireship tagged Education) that YouTube's topic classifier missed.
- Channels failing both stages are excluded.

### Method 3: Random Prefix Tech Filter (unbiased supplement)

**Approach:** Use EXISTING Stream C data (50,022 random channels, already collected) to extract an unbiased tech subsample.

**What we already have:**
- Stream C: 50,022 channels collected via random 3-character prefix search (no algorithmic bias)
- 46,338 have topic data
- 3,447 are Technology-tagged (6.9% of random sample = population base rate)
- 1,928 are Technology-tagged AND created before January 2023

**Action:** Filter Stream C output to Technology-tagged + pre-2023 channels. No new API calls needed.

**Additional random collection (optional):** If 1,928 channels is insufficient for the unbiased stratum, run additional random prefix searches. At 6.9% tech rate, collecting 50,000 more random channels would yield ~3,450 more tech channels. Cost: ~100K search units + ~1K channel detail units.

**Key advantage:** This subsample has NO algorithmic selection bias. It represents what "a random tech channel on YouTube" actually looks like. Essential for:
1. Benchmarking the subscriber count distribution of the full sample against the population
2. Testing whether results from Methods 1+2 (algorithmically biased toward larger channels) replicate in the unbiased subsample
3. Reporting the population base rate of tech channels (6.9%) and the representation of women within it

---

## Post-Discovery Pipeline

### Step 1: Dedup and Merge
- Combine channel IDs from all three methods
- Tag each channel with discovery method(s) for provenance
- Deduplicate on channel_id

### Step 2: Channel-Level Verification
- For channels from Methods 1 and 2 that don't already have full details: pull full channel metadata via channels.list API (1 unit per 50 channels)
- Apply two-stage tech channel definition:
  - Stage 1: channel has Technology, Software, Computer, or Gadget in any of topic_1/2/3
  - Stage 2: for channels tagged Education, Entertainment, People & Blogs, Knowledge, Science, or How-to & Style (without a Stage 1 tech topic), sample 10 video titles; include if >30% contain tech keywords (threshold to be calibrated on 640 known tech channels first)
- Verify: channel published_at < 2023-01-01
- Record channel subscriber count, view count, video count, country, topics, creation date

### Step 3: Filter and Finalize
- Apply both filters (two-stage tech definition + pre-2023 creation)
- Expected final sample: 50,000+ channels
- If below target: expand Method 2 keywords or run additional random prefix collection
- Save canonical channel_ids.csv and channel_metadata.csv to data/channels/tech_census/

### Step 4: Video Enumeration
- Full video history for all channels (every video ID + title + published_at)
- Uses existing enumerate_videos.py with checkpoint/resume
- Estimated scale: 50K channels x ~500 videos/channel (empirical rate from gender gap panel) = ~25M videos
- Runtime: ~3-4 weeks at current throughput via nightly launchd runs

### Step 5: Daily Stats Integration
- Add tech_census panel to daily channel stats collection
- Create launchd plist: com.youtube.tech-census-daily-channel-stats
- Schedule: after existing panels (3:20 AM EST)
- Quota: 50K / 50 per batch = 1,000 API calls = 1,000 units/day

### Step 6: AI Content Flagging
- Apply AI_FLAG_KEYWORDS (101 keywords in 6 categories) to all video titles and descriptions
- Flag each video as AI-related or not
- Compute per-channel: first AI video date, total AI videos, AI video share, AI adoption intensity over time
- This is a post-collection analysis step, no API calls needed

### Step 7: Gender Coding
- Katie's decision on method (human coders, automated, or hybrid)
- The 640 tech channels in the gender gap panel with hand-coded gender serve as a validation/training set
- Not blocked by data collection; can be done in parallel or after collection

---

## Scheduling and Quota

### Quota Budget

| Method | Unit Cost | Duration |
|--------|-----------|----------|
| Method 1 (TopicId) | ~8.76M units | ~9 days |
| Method 2 (Keywords) | ~3.5M units | ~4 days |
| Method 3 (Random filter) | 0 (already collected) | Immediate |
| Channel verification | ~20K units | <1 day |
| Video enumeration | ~200K units | ~10 days |
| Daily stats ongoing | ~1K units/day | Ongoing |

**Total discovery: ~12.3M units over ~13 days**
**Total including enumeration: ~12.5M units over ~23 days**

### Scheduling Constraints

Current daily quota: ~1,010,000 units
Current services consuming quota:
- Daily channel stats (gender gap + AI census): ~2,200 units at 3:05-3:12 AM
- Update inventory (both panels): ~3,000 units max at 3:30-3:35 AM
- Gender gap enumeration: variable (4:00-11:00 AM)
- Video stats chunks: ~48,000 units at 11:00 AM-1:00 PM
- Trending: ~200 units at 11:00 AM
- Stream A' discovery: variable (2:00-6:00 PM)

**Available window for tech census:** 6:00 PM to 3:00 AM EST (9 hours). After A' finishes and before daily stats start. The binding constraint is daily quota (~1M units), not window duration. After other services consume ~55K units, approximately 945K units remain available per day for tech census discovery.

**Approach:** Start Method 3 immediately (zero cost). Start Method 1 in the 6 PM-3 AM EST window now. Method 2 after Method 1 completes. Tech census runs concurrently with existing services in the evening/overnight window. One discovery script at a time (never concurrent with A').

---

## Validation Design

### Built-in validation sample
The 640 Technology-tagged channels in the gender gap panel (with hand-coded gender from Bailey's) serve as a benchmark:
- Accuracy validation for any automated gender coding
- Subscriber count distribution comparison with the tech census sample
- AI adoption rate comparison (are gender gap tech channels adopting AI at similar rates to the broader tech census?)

### Representativeness checks
- Compare subscriber count distribution of Methods 1+2 against Method 3 (unbiased)
- Report: median subscribers, interquartile range, share of channels above 100K subscribers
- If Methods 1+2 are significantly skewed toward large channels, weight or stratify in analysis

### Population base rate
- Stream C establishes: 6.9% of random YouTube channels are Technology-tagged
- Stream C establishes: X% of Technology-tagged channels are created pre-2023 (55.9% from our data: 1,928/3,447)
- These rates are citable population statistics for the paper

---

## Data Outputs

| Output | Path | Content |
|--------|------|---------|
| Channel IDs | data/channels/tech_census/channel_ids.csv | Canonical ID list |
| Channel metadata | data/channels/tech_census/channel_metadata.csv | Full CHANNEL_INITIAL_FIELDS |
| Discovery provenance | data/channels/tech_census/discovery_provenance.csv | channel_id, method, keyword, date |
| Video inventory | data/video_inventory/tech_census_inventory.csv | All video IDs + titles + dates |
| Daily channel stats | data/daily_panels/channel_stats/tech_census/YYYY-MM-DD.csv | Daily snapshots |
| AI flagging results | data/analysis/tech_census_ai_flags.csv | Per-video AI keyword matches |

---

## Open Decisions (require Katie's input)

1. **Gender coding method:** Human coders, automated (thumbnail/voice), or hybrid? Not blocking collection.
2. **Method 2 keyword list:** Final keyword selection (the 35 terms above are a starting point).
3. **Random prefix supplement:** Is the existing 1,928 from Stream C sufficient, or run more random collection?

## Resolved Decisions

- **Start timing:** Begin immediately. Run in the 6 PM-3 AM EST window alongside existing services. Start Method 3 (free) now, Method 1 tonight.
- **Topic strictness:** Two-stage definition. Stage 1: Technology/Software/Computer/Gadget topic tag. Stage 2: content screen for Education/Entertainment/People & Blogs channels (>30% tech keywords in sampled video titles).
- **Video enumeration estimate:** Revised to ~500 videos/channel (based on gender gap panel empirical rate of 507/channel), yielding ~25M videos over ~3-4 weeks.

---

## Risk Register

| Risk | Mitigation |
|------|-----------|
| Search API returns same popular channels repeatedly | Multiple sort orders + time windows + region codes |
| 50K target not reached | Expand keyword list, extend time range, run more random |
| Topic tags are sparse/missing for some channels | Method 2 catches untagged tech channels; verify via channel description keywords as fallback |
| Quota competition with existing services | Schedule in 6 PM-3 AM window; monitor quota dashboard |
| Gender coding introduces measurement error | Validate against 640 gold-standard channels; report accuracy |
| Pre-2023 filter loses channels that deleted early videos | Accept this limitation; document in methods section |
