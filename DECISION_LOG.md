# DECISION_LOG.md
# YouTube Longitudinal Data Collection

## 001. Adoption of "Triple-Stream" Sampling Design
**Date:** Feb 02, 2026
**Status:** IMPLEMENTED

### Context
We needed a sampling strategy to study "New Creator" virality.
- **Problem:** "Random" broad queries (e.g., "video", "a") return high-view content (Median ~600k views), missing the "long tail" of true new entrants.
- **Problem:** "Random Prefix" queries (e.g., "xyz") return true random content (Median ~20 views), but are too noisy and low-yield to find specific "entrepreneurial" creators.

### Decision
We adopted a **Triangulated (Triple-Stream) Design**:
1.  **Stream A (Intentional Cohort):** Targeted Keywords (`Welcome`, `Intro`) -> Captures the Treatment Group (New Entrepreneurs).
2.  **Stream B (Visible Market):** Vowel Rotation (`a`, `e`, `i`) -> Captures the Competitive Context (Active Market).
3.  **Stream C (Deep Random):** Random Prefix (`xyz`) -> Captures the Null Baseline (Survivorship Control).

### Rationale
- **Survivorship Bias Control:** Stream C proves we aren't ignoring failed channels.
- **Market Context:** Stream B proves whether our cohort is "beating the market."
- **Efficiency:** Stream A maximizes the N for our primary variable of interest.

### Alternatives Considered
- *Single Random Sample:* Rejected. Would either miss the long tail (if broadly queried) or be 99% garbage (if prefix queried).
- *Two-Stream (New + Random):* Rejected. "Random" was ambiguous. We split it into "Visible" vs. "Deep" to be precise.

### Impact
- **Quota:** daily usage increased to ~700k units (70%).
- **Complexity:** Requires managing 3 scripts (`discover_cohort.py`, `discover_visible.py`, `discover_deep_random.py`).
- **Validity:** dramatically increases the academic defensibility of the study.

## 002. Gender Gap Panel: Coded Channels Only (9,760 of 14,169)
**Date:** Feb 16, 2026
**Status:** DECIDED

### Context
Bailey's dataset has 14,169 unique channels, but ~4,100 have blank gender and ~4,100 have blank race (largely overlapping). Channels without coded gender/race lack an identifiable creator and are less analytically useful for the gender gap study. Full panel would require 370K API units/day and produce 1.2 GB/day of video stats.

### Decision
Restrict the longitudinal panel to the **9,760 channels with both gender AND race coded** (excluding blank and undetermined). This drops ~31% of channels but retains all analytically actionable observations.

### Rationale
- The gender gap analysis requires gender and race as key independent variables. Channels missing both can't contribute to any regression.
- Saves 35% on quota (240K vs 370K units/day) and storage (269 vs 416 GB/year).
- Uncoded channels can always be added back later if gender/race coding is completed.

### Alternatives Considered
- *Full 14,169 panel:* Rejected. 4,400 channels with no gender/race provide no analytical value for the core research question.
- *Gender-only filter (10,092 channels):* Considered. Decided to require both gender AND race since intersectional analysis is a key design goal.

## 003. Dual-Cadence Collection: Daily Channels, Weekly Videos
**Date:** Feb 16, 2026
**Status:** DECIDED

### Context
With 9,760 channels and ~12M videos, collecting all video-level stats daily would use ~240K API units/day and produce ~756 MB/day. Channel-level stats for the same channels cost only ~195 units/day and ~1.1 MB/day.

### Decision
**Daily** collection of channel stats (subscribers, total views, video count). **Weekly** collection of video-level stats (per-video views, likes, comments). Implemented via `--mode channel|video|both` flag in daily_stats.py.

### Rationale
- Channel-level metrics (subscriber growth, total view growth) change meaningfully day-to-day and are the primary outcome variables for the gender gap study.
- Video-level metrics change more slowly for most videos and weekly snapshots capture sufficient variation for the staggered DiD design.
- Reduces daily quota from 240K to ~195 units and daily storage from 756 MB to 1.1 MB. Weekly video collection adds ~240K units and ~756 MB once per week.
- Total weekly cost: ~241K units + 756 MB (vs. 1.68M units + 5.3 GB at daily cadence).

### Alternatives Considered
- *Daily video stats:* Rejected. 7x the cost for marginal analytical gain. Most video view counts don't change meaningfully day-to-day.
- *Biweekly video stats:* Considered but weekly is standard in panel studies and keeps options open for time-series analysis.

## 004. Four AI Research Designs (Expanded from Three)
**Date:** Feb 17, 2026
**Status:** DECIDED

### Context
Original plan had three AI research designs built on the gender gap panel: (1) AI Creator Census, (2) AI Adoption Diffusion, (3) Audience Response. During production deployment of the new creator cohort streams, realized the datasets enable a fourth design and the audience response design is cleaner with within-creator variation from the AI census.

### Decision
Expand to **four research designs** across two populations:

| Design | Population | Comparison | Question |
|--------|-----------|------------|----------|
| AI Creator Census (Longitudinal) | AI census channels | Panel DiD | How do AI creator tactics/success diverge by gender/demographics over time? |
| AI Adoption (Established) | Gender gap panel (9,760) | Within-panel, staggered DiD | Who among established creators adopts AI? |
| AI Adoption (New) | New cohort (Streams A/A'/D) | A vs A' vs D | Do new strategic creators adopt AI more than non-strategic? |
| Audience Response | AI census (within-creator) | AI vs non-AI videos, same channel | Does audience react differently to AI content by creator gender? |

### Rationale
- **AI Adoption (New)** — Stream A (intent) vs A' (non-intent) is a natural experiment: same entry cohort, different launch strategies. Stream D (casual) provides a non-strategic baseline. Tracks "born AI-native" adoption, complementing the established-creator pivot story.
- **Audience Response redesign** — Within-creator variation (AI vs non-AI videos from the same channel) is cleaner than cross-channel matching. Controls for all channel-level confounders. Each creator is their own control. Can interact with gender: does the AI engagement premium/penalty differ for men vs women?
- No new infrastructure required. The AI keyword flagger (`flag_ai_videos.py`) works on any channel's videos. Same treatment variable, different populations.

### AI Census as Longitudinal Panel
The AI census is NOT a one-time snapshot. It becomes a daily-tracked longitudinal panel (via `--panel-name ai_census` on Mac Mini). This enables:
- **DiD on success outcomes by tactics:** Compare creators who use different AI tools (Midjourney vs Sora vs ChatGPT), different content strategies (tutorials vs showcases vs reviews), by demographics and ascriptive characteristics (gender, race, country)
- **Within-creator trajectory analysis:** Track subscriber growth, view velocity, engagement rates over time as creators refine their AI content strategies
- **Cross-panel comparisons:** AI census channels tracked alongside gender gap panel and new cohort — same metrics, same cadence, different populations
- **Infrastructure:** `daily_stats.py --panel-name ai_census` already supported. Needs its own launchd plist on Mac Mini (deploy alongside new cohort plist).

### Alternatives Considered
- *Separate AI benchmark stream:* Not needed. Stream C (random, coming) provides population-level AI adoption rates. The AI census captures the visible ecosystem, which is the relevant comparison for gender dynamics.

## 005. Possible Additional Stream: 2020 Birth Cohort (AI Diffusion History)
**Date:** Feb 17, 2026
**Status:** PROPOSED — Needs Katie's decision

### Context
Current datasets capture AI adoption either cross-sectionally (AI census) or prospectively (new cohort from 2026, gender gap panel going forward). Neither captures the full historical diffusion arc: pre-ChatGPT (before Nov 2022) → early hype (2023) → mainstream adoption (2024-25) → saturation (2026).

### Proposal
Sample channels created around 2020 and collect their **full video history** (all videos since channel creation). This creates a retrospective birth cohort with ~6 years of video metadata spanning the entire AI diffusion curve.

### Why 2020
- Old enough to have substantial pre-AI video history (2020-2022 = baseline era)
- Young enough that many are still active (lower attrition than 2015 cohort)
- Created at the same time, so trajectories are comparable within the cohort (no age confounding)
- 2020 is pre-GPT-3 (June 2020), pre-DALL-E 2 (April 2022), pre-ChatGPT (Nov 2022) — clean pre-treatment period

### What it enables
- **Diffusion curves by gender:** When did men vs women start making AI content? How fast did adoption spread?
- **Adoption timing as treatment:** Staggered DiD with precise adoption dates visible in video history
- **Content evolution:** Track how individual creators' content mix changed as AI tools became available
- **Counterfactual baseline:** Channels that never adopted AI provide the untreated comparison

### Open questions
- **Sample size / sampling method:** Random prefix search filtered to 2020 creation dates? Or pull from an existing channel list?
- **Quota cost:** Full video history for N channels × avg videos per channel. Need to estimate.
- **Gender coding:** Would need to code gender for these channels (not in Bailey's dataset)

## 006. Abandon Freebase topicId for Discovery; Use videoCategoryId Instead
**Date:** Apr 7, 2026
**Status:** IMPLEMENTING

### Context
Topic-Stratified stream (designed Feb 18, 2026) used Freebase `topicId` parameter on `search.list` to discover channels across 62 topic categories. First production run (Apr 6) returned only 90 channels from 1 of 62 topics. Investigation revealed the `topicId` parameter returns near-zero results when used without a query string. Freebase is deprecated.

### Decision
Abandon Freebase `topicId` for all future discovery. Use YouTube's native `videoCategoryId` parameter on `search.list` instead (15 categories, integer IDs, confirmed working Apr 7 with 400K-1M+ results per category).

### YouTube's Three Category Systems (Reference)
1. **Freebase topicIds** (`topic_ids` field, e.g., `/m/04rlf`): DEPRECATED. From `channels.list(part=topicDetails)` → `topicDetails.topicIds`. Broken for search filtering. Do not use.
2. **Channel-level topicCategories** (`topic_1/2/3` fields, Wikipedia URLs): From `channels.list(part=topicDetails)` → `topicDetails.topicCategories`. Up to 3 per channel. **This is what the JMP gender gap paper uses** for its `bucketedGranularTopic` and `granularTopic_over_thirty` regression variables. The JMP bucketing logic (parent vs. granular priority, subtopic consolidation) is in `YT_v1/code/pre_cursor/1-Assign Granular Topic_Hobby as Parent.do`.
3. **Video-level videoCategoryId** (`categoryId`, integer): From `videos.list(part=snippet)` → `snippet.categoryId`. Set by creators per video upload. 15 categories. Works reliably as a search filter.

### Usage Rule
- **Discovery** (finding channels via search API): Use `videoCategoryId` (works as search filter)
- **Analysis** (category variable in regressions): Use `topic_1/2/3` (consistent with JMP)
- **Secondary/validation**: Modal `videoCategoryId` across a channel's videos provides a bottom-up category assignment
- Both are captured automatically: videoCategoryId during discovery, topic_1/2/3 when channels.list runs on discovered channels

### Rationale
- Freebase is officially deprecated; relying on it is fragile
- videoCategoryId is YouTube's native system, actively maintained
- topic_1/2/3 (channel-level topicCategories) ensures consistency with the JMP's existing category variable
- Having both systems captured enables cross-validation

## 007. Replace Topic-Stratified with Category Quota Sampler
**Date:** Apr 7, 2026
**Status:** IMPLEMENTING

### Context
Topic-Stratified (40K target, 62 Freebase topics, `topicId` filter) failed in production. Analysis of A' (110K channels) revealed apparent category breadth was inflated by multi-tagging: 48% of channels have multiple Freebase topic tags, and primary-category assignment collapses to 4 dominant categories (Lifestyle 33%, Gaming 20%, Entertainment 18%, Music 13%). Smaller categories (Sports, Society, Knowledge) have adequate marginal counts but thin cells when crossed with language (15) and eventually gender.

### Decision
Replace Topic-Stratified with a **Category Quota Sampler** that uses `videoCategoryId` and floor-based collection.

### Design
- 15 YouTube video categories (native integer IDs)
- For each category: `search.list(videoCategoryId=X, q=letter, order=date, publishedAfter=2026-01-01)`
- Cycle through letters a-z as query parameter (minimal-bias query diversification, borrowed from Stream C's random prefix logic)
- **Per-category floor target**: collect until each category has 3,000-5,000 unique channels
- Categories that are naturally abundant hit quota fast and stop; rare categories get more cycles
- Checkpoint per category (resume-safe for launchd)
- `--max-runtime` and `--reserve-quota` flags (standard hardening)

### Why Floor-Based, Not Proportional
- Proportional allocation wastes quota collecting more Lifestyle/Entertainment channels we already have in abundance
- Floor-based guarantees minimum viable sample sizes for category x language x gender subgroup analysis
- The algorithm adapts: rare categories get more search effort automatically

### Primary Category Assignment (Future)
- For analysis: use `topic_1/2/3` (channel-level topicCategories, consistent with JMP)
- For validation: modal `videoCategoryId` across channel's videos (requires video enumeration)
- `videoCategoryId` used for discovery is a strong initial proxy but NOT the analysis variable

### Alternatives Considered
- Fix Topic-Stratified by adding query strings alongside topicId: Rejected. Still relies on deprecated Freebase system. Would produce same multi-tagging noise.
- Category-specific keyword banks per topic: Rejected. Labor-intensive, introduces researcher priors about what keywords represent each category.
- Skip category expansion entirely (A' coverage is "good enough"): Rejected. Cell sizes too thin after crossing with language and gender. Future research flexibility requires guaranteed minimums.
- videoCategoryId + broad generic query (single approach): Adopted. Letter cycling provides query diversity without semantic bias.

### Impact
- Replaces `discover_topic_stratified.py` with `discover_category_quota.py`
- Same 2 PM EST launchd slot, same quota budget
- Expected yield: 45K-75K channels (15 categories x 3-5K floor)
- Clean discovery-category label per channel by construction
- **Feasibility:** Can the YouTube API filter search results by channel creation date?
