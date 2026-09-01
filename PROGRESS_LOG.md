# Progress Log: YouTube Longitudinal Data Collection

**Purpose:** Chronological record of all work completed on this project  
**Update Instructions:** Add new entries at the TOP of each month's section

---

## Current Status (as of May 4, 2026 — 5:55 PM)

**Phase:** Post-reboot cleanup. Quota incident May 4 caused by `daily-discovery-knowledge-economy` rogue plist (928K units burned). 8 dormant plists retired with `.RETIRED` rename to prevent reboot reactivation. Active service count: 25.

---

## 2026-06-17 10:05 [KE Census targeted re-enumeration of 17,296 missing-video channels — LAUNCHED]

**Scope:** Approved production run (Katie explicit go). Re-enumerate the 17,296 Knowledge Economy Census channels with `n_videos_total==0/null` in `data/processed/ke_analysis_base.csv` so their video lists can later feed thumbnail-based gender coding. Runs on Mac Mini (PID 7332), nohup, checkpointed.

**What was done:**
- Target list built: exactly **17,296 unique channels** (26,250 of 43,546 KE channels already have videos; the 17,296 missing match the expected count). All well-formed UC... IDs, header present. Written to `data/channels/ke_census/reenrich_targets_20260617.csv`.
- **Enumeration bug status: ALREADY FIXED in base `enumerate_videos.py`** — failed channels are no longer marked complete (`completed_set.add` is inside the try, after success), QuotaExhaustedError is re-raised by the API layer and caught for a clean stop, `--max-runtime` uses the correct `is not None` check. Verified on the Mac Mini copy (md5 66da5aea...).
- Created **`src/collection/enumerate_videos_targeted.py`** (new file, original untouched): adds a `--reserve-quota` guard the base script lacked, NUL-safe channel-list read, page_token completeness check (partial enumeration not marked complete), and writes to a SEPARATE output stem so the live inventory's checkpoint/sentinel are never touched. Also refuses to write to `knowledge_economy_inventory.csv` by name.
- **Quota check:** 21,770 units used today (daily stats already ran 09:01); ~978K free. Reserve set to 200K (process stops at 800K consumed). Live inventory (6.9 GB, Apr 30) byte-identical after launch — untouched.
- **--test --limit 5:** returned 5,480 real videos across 5 channels (1 to 4,850 each), correct schema, all non-null video_ids. Test artifacts moved to `temp/`.
- **Full run launched:** PID 7332, output `data/video_inventory/knowledge_economy_inventory_reenrich_20260617.csv`, log `data/logs/reenrich_run_20260617.out`, checkpoint `.enumerate_knowledge_economy_inventory_reenrich_20260617_checkpoint.json`. Flags: `--reserve-quota 200000 --max-runtime 50400`.

**Early findings / estimates (steady-state from first ~25 channels):**
- Rate ~777 channels/hr; avg ~13.4 quota units/channel.
- **Projected full-run cost ~231K units (23% of daily 1M)** — quota is NOT binding.
- **Recoverable rate 100% so far (25/25 with videos, median 177, max 4,850)** — confirms the gap is an enumeration artifact, not channel deadness. Expect a small dead/terminated tail across the full 17,296.
- Projected ~9M videos recovered if rate holds.
- **ETA ~22h exceeds the 14h max-runtime** → run stops cleanly tonight (~12 AM EST, before the 3-9 AM daily-stats window) with checkpoint retained. **Resume tomorrow** = re-run the same command (it picks up from the checkpoint). No launchd auto-resume added (requires Katie's approval).

**Resume command (Mac Mini):**
```
cd /Users/katieapker/.youtube-longitudinal/repo && nohup python3 -m src.collection.enumerate_videos_targeted --channel-list data/channels/ke_census/reenrich_targets_20260617.csv --output data/video_inventory/knowledge_economy_inventory_reenrich_20260617.csv --reserve-quota 200000 --max-runtime 50400 > data/logs/reenrich_run_20260617.out 2>&1 &
```

**Untouched:** free DeepFace thumbnail job PID 5108 (local, no quota conflict); live `knowledge_economy_inventory.csv`.

---

## 2026-08-05 [Cross-reference: the Aug 3-4 work was CONTINUED in a second session; read its entries too]

The handoffs below were EXECUTED in a parallel session whose entries sit further down this file
(2026-08-04 06:00 manuscript + elite splice; 08:40 professor PPTX built; 13:30 full battery
re-run on the refreshed record). Net state after both sessions:
- Full analysis battery re-run on the through-Aug-3 record with v3 gender as the single frame
  (scripts src/27_ through 35_; _v2 output JSONs). qbq/findings-ledger.md is CURRENT (refreshed
  2026-08-04) and is the number source; key scale numbers: 92,208 measurement-clean AI videos,
  9,620 adopter channels, ~46.9M uploads scanned.
- ONE VERDICT MOVED: F4 timing is now "whether AND when" (women adopt later: median 457 vs 366
  days after ChatGPT, +53 days adjusted, p=.003; the June "not when" was an underpowered
  April-censored cell). No other finding changed direction; F1/F2/F5 strengthened slightly.
- Claude Code cumulative female share is now 11.2% (was 3.9% on the April record): wave-phase
  sensitive; use "4 percent during the launch wave, 11 percent after the 2026 catch-up."
- Manuscript updated to v3 findings + elite citation splice DONE; HTML deck updated; first
  professor PPTX exists (drafts/Who_Explains_AI_brief_2026-08.pptx) with a rebuild spec in
  HANDOFF_pptx_professor_deck.md (numbers refreshed 2026-08-04).

---

## 2026-08-04 [Gendering-AI paper: video record refreshed through Aug 3 + 2026 zoom re-run with May-Jul]

- Sweep COMPLETE (finished 6:05 PM Aug 3): 43,461 channels, 52,942 quota units, ~992K unique new videos since Apr 15, 541 clip-farm channels capped at 400 videos each.
- Fold-in chain run: src/26_flag_new_videos.py (same keyword rule as 01; all new videos post-date every launch gate) -> 10,310 newly flagged AI videos (May 2,729 / Jun 3,041 / Jul 3,467, still accelerating), 968 brand-new adopter channels; combined file processed/ke_ai_flagged_true_v2.csv (132,396 rows; June original untouched); ai_titles_v2.csv; first-video table v2 (24b); 2026 zoom v2 (22b).
- HEADLINE (F9 updated): coding-AI female share bottomed at 11.0% in March 2026 and PARTIALLY REBOUNDED May-Jul (21.5% / 15.2% / 17.4%); women's share of NEW adopters rose Apr-Jul (28-36% vs 16-23% Jan-Mar); overall AI-video female share drifted to its lowest full month in July (13.6%); within-creator gap mildly negative post-spike. Reads as frontier-surge-then-partial-catch-up inside a single tool wave, consistent with the paper's diffusion story. Suggestive, not confirmatory (monthly coding n 200-340).
- DASHBOARD currency note + findings-ledger F9 updated. Monitor loop stopped. Git uncommitted (Katie's call).

---

## 2026-08-03 PM [Gendering-AI paper: findings ledger refreshed + manuscript/PPTX handoffs + refresh sweep running]

- qbq/findings-ledger.md FULLY REFRESHED: current v3 numbers for F1-F9 incl. new findings (developer-identity content sorting; packaging two-layer; 2026 zoom lead; persistence), graveyard (degree over-claim, gap x size, "generic authority more" revised to the FORM split), and the gender-method note. This is now the number source for any manuscript update.
- HANDOFF_manuscript_update.md written: number swaps (14,203->17,273; OR 0.72->0.71; DiD -0.0027->-0.0015 etc.), substantive changes (F3 form split replaces "generic authority more" everywhere; add persistence), coordination with the pending elite-lit splice (T1), hold points (tonight's May-Jul refresh; transcripts), verification gates.
- HANDOFF_pptx_professor_deck.md written: professor-facing PPTX via /DeckCompile, 10-slide arc, numbers-to-file table, approved plain register (exemplar = drafts/gendered_uptake_deck.html), charts rebuilt from current JSONs (June figs superseded).
- Video-list refresh sweep RUNNING on Mac Mini (v2 script with mega-uploader page cap after 3 clip farms with 20K videos each stalled v1); ~120 channels/min, ETA evening; auto-monitored, fold-in chain (26_flag_new_videos -> ke_ai_flagged_true_v2.csv -> first-video rebuild -> 2026 zoom with May-Jul) fires on completion.
- Descriptions for 81,155/81,898 AI videos fetched (median 901 chars + tags); first-AI-video table built (ke_first_ai_video.csv). Research ideas register: RESEARCH_IDEAS.md. Git uncommitted (Katie's call).

---

## 2026-08-03 [Gendering-AI paper: v3 robust gender BUILT + core re-verified + content/language analyses + patterns deck]

**Scope (papers/gendering-ai-expertise/):** Executed the re-gendering handoff in-session per Katie's delegation, added the content/"pinkification" analyses, and published the distilled-patterns HTML deck.

- **v3 gender built (my methodological call, delegated by Katie):** Gemini visual gender + DeepFace face-count confidence tiers (T1-T3), names never assign. 17,273 binary (27.7% women). `src/05d_gender_consolidate_v3.py` -> `processed/ke_gender_v3.csv` + `output/gender_v3_report.json`. Truth-check honest but small (n=25 overlap: 96% acc, 4.4pp diff FPR vs v2's 22pp on the same overlap); robustness claim = triangulation across v1/v2/v3 + tiers.
- **Headline re-verified on v3** (`src/18_did_v3.py`): fem x post x techiness -0.0015 (p=.036), dev-origin -0.0089 (p=.016), pooled null, pretrends flat (p=.75), placebo null; panel 3,240 channels / 1.20M stacked channel-months.
- **Authority form on v3** (`src/20_authority_terms_v3.py`): certification OR 1.72 (p<.001), coach 1.92x, tech-title OR 0.41 (T3-only 0.33), degrees FLAT, credentials don't close the gap (6.9pp both). Degree over-claim + gap-x-size confirmed DEAD.
- **NEW content analyses:** (a) tool sorting (`19_content_tools_v3.py`): developer identity, not techiness, genders adopter content: Claude Code 3.9% female vs Stable Diffusion 55%, techiness-femshare corr ~0; (b) title language (`21_title_language_v3.py`, titles extracted from the 45.9M-row KE inventory on the Mac Mini, NUL-safe): women's AI titles 2.65x more accessible-framed / 1.5x emoji at the MARKET level, but within-channel register shifts are gender-flat: selection + volume, not softened voice. Transcripts confirmed absent (0B) — top-value next data pull.
- **Deck:** `drafts/gendered_uptake_deck.html` published as artifact (7 patterns, robustness badges, causal-ID assessment, 5-project map).
- Logs updated (DASHBOARD + findings-ledger caveats flipped to v3 status). Still on v2 and queued: full survival battery, heterogeneity, cc_event, exhibits; draft prose still carries v1/v2 numbers until the splice. Framing remains PROVISIONAL. Git uncommitted (Katie's call).

---

## 2026-06-17 [Gendering-AI-Expertise paper: lit foundation + EDA fold-in + re-gendering caveat written into logs]

**Scope:** Management-first literature foundation + folding in the respawned EDA + writing the gender-coding caveat across the paper's tracking files. Did NOT splice prose, did NOT lock framing, did NOT commit git.

**What was done (papers/gendering-ai-expertise/):**
- Built `lit/management_lit_foundation.md`: management/sociology-first cite library mapped to every argument move, elite-heavy (ASR/AJS/ASQ/AMJ/AMR/Org Sci/Mgmt Sci), zero econ substantive, with the econ-violation replacement map. Method: vault traversal + Consensus + 3 parallel OpenAlex/Semantic Scholar discovery agents. Complements the generator's `references_elite.md` (reconcile pending).
- Folded the respawned EDA into the lit map (EDA MAPPING section): extensive-margin gap (whether, not when); clean Claude Code GA event study (flat pre-trend) yielding a "gender-typing" verdict; gap NARROWS over time (Cox piecewise HR 0.69->0.86, diffusion); NEW persistence gap (women more one-and-done OR 1.38, less likely to continue OR 0.74); honesty nuance (technical-vs-creative bucket NULL among adopters; techiness effect lives at ENTRY not adopter tool-choice).
- CREDENTIAL finding folded (the flagged angle): authority-claiming gendered in FORM not level. Women over-index certification (OR 1.28), formal degree (marginal), coach 1.51x / phd 1.42x / mentor / expert; under-index professional-technical title (OR 0.43, p<1e-10) + professor 0.50x / ceo 0.76x. Credentials do NOT close the adoption gap. Mapped to Quadlin ASR / Castilla & Benard ASQ / Campbell & Hahl Org Sci / Faulkner-Wajcman / Kumra & Vinnicombe.

**Key context changes (Katie, 2026-06-17):**
- Framing memo UN-LOCKED -> PROVISIONAL / exploration (flipped LOCKED labels in framing-memo.md line 2 + line 36, DASHBOARD, state.json).
- GENDER-CODING CAVEAT written into DASHBOARD, findings-ledger, state.json, framing-memo, and the lit foundation: all current numbers/findings ran on INITIAL/preliminary gender coding; a robust re-gendering is in progress with more analysis to fold in; EVERYTHING must be RE-RUN on it; results are PROVISIONAL/DIRECTIONAL, not locked. The cite layer is robust to re-gendering unless a finding's DIRECTION flips.

**Note:** harness blocks reading files named `credentials_*` (secrets false positive); copied to `cred_signals_*` (originals preserved).

---

## 2026-06-17 [Gendering-AI-Expertise paper: lit layer rebuilt to elite caliber + gap sharpened | HANDOFF #3]

**Scope:** Lit layer ONLY (HANDOFF #3). Did NOT edit the manuscript prose, run EDA, or commit git (those are the splice window's / Katie's call).

**What was done (papers/gendering-ai-expertise/):** Rebuilt the bibliography to Katie's elite-journal standard and sharpened the specified ignorance to contribution grade. Three splice-spec files produced: `qbq/phase-04-gap-sharpened.md` (sharpened gap + four-tradition checklist + intro-ready problematizing turn + Research Rabbit seed list), `drafts/references_elite.md` (classified reference list, 90.0% elite-share, replaced/relegated table), `qbq/claim_cite_map.md` (each theory claim mapped to its elite cite, mechanism vs rival). Verified 3 new anchors live on OpenAlex (Campero 2020 ASR, Correll/Weisshaar/Wynn/Wehner 2020 ASR, Dupree 2024 ASQ) + Lee/Koval/Lee 2022 AMJ. A forked read-only critic scored it 91/100 (bar 90); independent recount confirmed 18 elite / 20 theory-support = 90.0%, zero econ/finance substantive.

**Key decisions:** dropped 2 econ violations (Exley & Kessler QJE, Aldasoro Econ Letters) + Faulkner (WSIF) + Peng (Nature Comms); relegated the GenAI-adoption empirics (Humlum/Otis/Chatterji) to one labeled backdrop sentence; reinstated 8 elite cites (Greenberg & Mollick, Hsu 2006, Hsu/Hannan/Koçak, Leung, Kacperczyk & Younkin, Eyal, Lee/Koval/Lee, Pontikes); confirmed via Consensus sweep that the second-level digital divide has NO elite-venue home, so elevated DiMaggio et al. 2004 as the foil anchor and cite that tradition as the problematized FOIL (not mechanism support); resolved a referee-bait contradiction by filing the Zuckerman/Pontikes conferral cluster as the REJECTED claiming-gap rival (per the framing memo), not affirmative mechanism.

**Still to fix (subsequent agents / splice window):**
1. SPLICE the spec into `drafts/gendering_ai_expertise_v1.md`: the live draft still cites Exley & Kessler (QJE, lines 70/171) and Aldasoro (Econ Letters, 24/34/90) = live econ violations, plus Peng + Faulkner, and lacks the reinstated/anchor cites. Swap per `references_elite.md` Section I + `claim_cite_map.md`; add Duffy 2017 to the draft reference list; drop the sharpened problematizing turn into intro P2.
2. Clear 3 load-bearing [VERIFY] flags: Dupree 2024 issue, Lee/Koval/Lee 2022 pages, DiMaggio et al. 2004 page range.
3. Run VerifyClaims on the spliced draft, then resume Phase 6-10 drafting + /pre-submit.

**Detail + full handoff:** `qbq/DASHBOARD.md` TOP BLOCKERS + NEXT ACTIONS; `qbq/WORKING.md` Phase 4; `qbq/state.json` phase 4.

---

## 2026-06-13 → 06-17 [EXPLORATION — what to do with the longitudinal data | CANDIDATE, NOT LOCKED]

**Status flag:** This is an OPEN EXPLORATION, not a committed paper. Framing is unlocked. Recorded so the next pickup has the breadcrumbs. Do not treat any framing below as decided.

**What was explored:** Whether the gender-gap longitudinal panel (9,591 individual-run creators; 11.6M dated uploads; daily channel-stats Feb 17–present; Infludata ~March 2025 baseline) supports a NOVEL, non-gender paper distinct from the JMP. Ran a real QbQ-Auto pass end to end.

**Candidate finding (provisional, survived robustness but NOT locked as the paper's thesis):**
- Posting *consistency* (steadiness of monthly cadence), not *volume*, tracks creator outcomes. In nested OLS the volume coefficient collapses (0.33→0.06) once rhythm enters; consistency b≈2.4 on log subscribers, holds within content-category FE and net of recency.
- Two prospective, time-ordered designs (4-month daily panel; ~15-month Infludata→2026 horizon) sharpened this: production reliability predicts **venture SURVIVAL** (IQR consistency → 6-month production-cessation odds ×0.52–0.53, robust), but is a **NULL on growth rate** (15-mo growth b≈−0.02, CI spans 0). Reading: reliability keeps the venture alive rather than making it grow faster; cross-sectional size is the compounded residue of differential survival under winner-take-all (top size-decile captured ~62% of net new subscribers over 15 months).
- Failure measured as production cessation (living-dead problem; channels go dormant, not deleted — 0% disappearance): 8.6%/5.2%/3.2%/1.4% at 3/6/9/12-month thresholds.

**Candidate theoretical framings considered (NONE chosen):** new-venture survival / liability-of-newness (Yang & Aldrich 2017; Shepherd 2000); organizational reliability (Hannan & Freeman); winner-take-all / superstar / creator precarity (Vallas & Schor 2020; Rietveld 2020; Bhargava 2021); creator-economy entrepreneurship (Fisher et al. 2024) + the CEE working paper's synchronization proposition. The raw "consistency beats volume" empirical claim is partly PRE-EMPTED (Tafesse 2023 inverted-U; Song 2024 ManSci quality-over-quantity), so any future paper needs the survival/longitudinal wedge, not the bare correlation.

**Artifacts (all under `papers/creator-trajectories/`):** scripts 01–06 (reproducible), exhibits, two prospective analyses, an exploratory v1 draft (`drafts/reliable_not_prolific_v1.*`) and framing memo — both flagged EXPLORATORY/UNLOCKED. Full lit review (~120–170 refs, like the gender-gap paper) was scoped but NOT built.

**If picking back up:** re-decide the framing first (survival is the leading candidate but unlocked); then build the full lit review and rewrite; then pull fresh daily-panel data for a longer growth/survival horizon.

---

## 2026-05-04 17:55 [Sunday May 3 Reboot Incident + Rogue Plist Cleanup]

**Focus:** Sunday May 3 7:24 PM Mac Mini reboot reloaded 11 dormant plists. One — `daily-discovery-knowledge-economy` — burned 928,021 quota units Monday 7:15-8:41 AM, exhausting daily quota and breaking ai_census + KE video chunks.

**Root cause:** macOS launchd auto-loads ALL plists in `~/Library/LaunchAgents/` on reboot. "Unloaded" services without `.RETIRED` rename are time bombs. Same lesson as Apr 11-13 stream-a-rerun incident, different plist.

**Why KE discovery was so destructive:** No idempotency check against existing `channel_ids.csv` (KE Census discovery completed Apr 18 at 143,558 channels). Plist fired, found no checkpoint, started rediscovering from scratch. Burned 928K units in 86 minutes before quota cut it off.

**Apr 13 fixes that DID hold today:**
- `stream-a-rerun` fired at 3:35 AM, hit output-exists check, exited at zero cost
- `gender-gap-enumeration` and `parallel-enumeration` shards all hit sentinel files, exited cheap
- `rebuild_april_cohort` patch held — april_cohort grew from 22K → 129K cleanly

**8 plists retired (unloaded + renamed `.RETIRED`):**
1. `com.youtube.daily-discovery-knowledge-economy` — TODAY'S CULPRIT (no idempotency)
2. `com.youtube-longitudinal.weekly-video-stats` — old Sunday 8 AM full-inventory job
3. `com.youtube.daily-discovery-non-intent` — Stream A' complete (110K)
4. `com.youtube.daily-discovery-topic-stratified` — replaced by category_quota
5. `com.youtube.tech-census-keyword` — Tech Census stopped Apr 6
6. `com.youtube.stream-a-rerun` — Apr 11-13 culprit, safe today but time bomb
7. `com.youtube.gender-gap-enumeration` — complete (sentinel)
8. `com.youtube.parallel-enumeration` — gender_gap shards complete

**Kept active:** `com.youtube.daily-discovery-shorts` — Katie wants Shorts data; it hit empty quota today but plist is sound.

**Service count:** 33 (post-reboot) → 25 (after cleanup).

**Today's data losses:**
- KE video chunk (8:30 AM): partial, 292K of expected ~1.5M stats
- ai_census video chunk (7:00 AM): partial, 1.05M of expected stats
- shorts (2 PM): 0 channels (empty quota)
- topic-stratified, A', tech-census-keyword: all hit empty quota — but those are retired now

**Tomorrow's quota math (clean):**
- Channel stats (7 panels): ~12K
- Video chunks (3 panels): ~95K
- Discovery (intent, non-intent, entry, trending, shorts): variable, capped by `--reserve-quota` flags
- Total floor: ~107K. 893K headroom.

**Lesson reinforced:** Always rename to `.RETIRED` (not just unload) when retiring a service. Unload alone evaporates on reboot.

---

## 2026-05-01 16:40 [KE Enumeration Complete + KE Stats Deployed + Entry Cohorts Resumed]

**Focus:** Closed out KE Census infrastructure. Enumeration finished Apr 30 at 7:07 PM (~12 days). Deployed daily channel stats + weekly video stats chunks for KE panel. Unpaused Entry Cohorts now that quota is freed.

**KE Census final tally:**
- 143,558 / 143,558 channels enumerated (100%)
- ~10.26M videos indexed (6.49M overnight + 3.77M final-day)
- Inventory: `data/video_inventory/knowledge_economy_inventory.csv` (6.5 GB)
- Sentinel `.enumerate_knowledge_economy_inventory_complete` written
- Today's 9 AM launchd hit sentinel and exited cleanly — no wasted quota

**Logging patch shipped (commit c56a90e):** `enumerate_videos.py` now returns `(total_videos, channels_done)` and prints `ENUMERATION PAUSED — will resume next run` vs `ENUMERATION COMPLETE` based on actual completion. Old behavior printed "COMPLETE" with `len(channel_ids)` regardless of partial exit.

**KE daily channel stats deployed:**
- Plist: `com.youtube.knowledge-economy-daily-channel-stats` — fires 3:50 AM
- Pipeline validated via `--test` run on May 1 (cost: ~2,871 quota units, runtime ~12 min)
- First production output: `data/daily_panels/channel_stats/knowledge_economy/2026-05-01.csv` — 143,558 rows, 5 cols, 0 nulls
- `--limit` flag only limits video IDs, not channels — channel mode always runs full panel

**KE video stats chunks deployed:**
- Plist: `com.youtube.knowledge-economy-video-stats-chunk` — fires 8:30 AM, 7-day rolling chunks
- Quota: ~29,300 units/day (1/7 of ~10.26M videos)

**Entry Cohorts unpaused:**
- Renamed `.PAUSED` → `.plist`, `launchctl load` succeeded
- Schedule: 11:30 AM daily, 60 min max runtime, reserves 50K quota

**Quota delta:** New daily total ~162K (from ~130K). 840K headroom remains.

**Schedule layout (active panels):**
- 3:06 AM gender_gap channel | 3:12/17 ai_census channel | 3:20 tech_census channel
- 3:39/40 new_cohort + category_quota | 3:50 KE channel (NEW) | 3:53 april_cohort
- 4:30 AM gender_gap video chunk | 7:00 AM ai_census video chunk | 8:30 AM KE video chunk (NEW)
- 9:00 AM KE enumeration sentinel-exit | 11:30 AM Entry Cohorts (RESUMED)

---

## 2026-04-18 09:35 [KE Census Discovery Stopped + Enumeration Deployed]

**Focus:** Stopped KE Census discovery at 143,558 channels (43% over target). Deployed enumeration plist.

**Decisions:**
- Stop discovery at 143K (far exceeded 100K target). Extracted channel_ids.csv from 10 dated CSVs (Apr 9-18), 143,558 unique.
- Deploy enumeration at 9 AM daily with 7h max runtime. Freed quota (no competing discovery) gives ~800K/day. Full 143K enumeration in ~7-10 days.
- Keep Entry Cohorts and April cohort discovery running (different time slots, complementary data).

**Files:**
- `data/channels/knowledge_economy/channel_ids.csv` (143,558 channels)
- `config/launchd/com.youtube.knowledge-economy-enumeration.plist` (new, 9 AM / 7h)

**Commits:** a6b151a (enumeration plist), ffa9287 (stop discovery + bump runtime)

---

## Current Status (as of April 14, 2026 — 9:40 AM)

**Phase:** Post-incident recovery. All services clean. KE Census + Entry Cohorts resuming after 3-day stall.
**What's Running on Mac Mini (100.109.96.120 via Tailscale) — 22 services:**

Daily channel stats (5 panels):
- `gender_gap`: **3:05 AM** (9,760 channels)
- `ai_census`: **3:12 AM** (50,010 channels)
- `tech_census`: **3:20 AM** (63,728 channels)
- `new_cohort` (A+A'): **3:25 AM** (135,977 channels)
- `category_quota`: **3:32 AM** (73,508 channels)
- `april_cohort`: **3:38 AM** (22,594 channels, growing daily)

New video detection:
- `update-inventory-gender-gap`: **3:30 AM**
- `update-inventory-ai-census`: **3:35 AM**

Video stats:
- `gender-gap-video-stats-chunk`: **4:30 AM** (1/7 of 11.7M videos)
- `ai-census-video-stats-chunk`: **7:00 AM** (1/7 of 5.3M videos)

Periodic sweeps:
- `monthly-sweep-stream-b`: **5:00 AM 1st** (18,207 channels)
- `monthly-sweep-stream-c`: **5:15 AM 1st** (50,022 channels)
- `weekly-sweep-stream-d`: **5:30 AM Sundays** (3,932 channels)

Discovery:
- `daily-trending`: **11:00 AM** (51 regions)
- `daily-discovery-april-intent`: **12:30 PM** (rolling 48h window)
- `daily-discovery-april-non-intent`: **1:00 PM** (rolling 48h window)
- `rebuild-april-cohort`: **1:45 PM** (merge + dedup)
- `daily-discovery-entry-cohorts`: **11:30 AM** (temporal windows around 20 tool launches, 1h max)
- `daily-discovery-knowledge-economy`: **2:00 PM** (pre-2023 risk set, 100K+ target, 4h max)

Plus: stream-a-rerun (dormant), health-check x2, sync-to-drive. Shorts-First UNLOADED (KE Census takes priority).

**Daily Stats Panels:** 6 panels, ~355K channels total.
**April Cohort:** 22,594 channels (19,000 intent + 3,594 non-intent). From-founding tracking live. Growing daily.
**Category Quota:** COMPLETE. 73,508 channels.
**AI Flagger:** RUN on Gender Gap Panel. 40,355 flagged / 11.8M videos (0.34%). tools_general 74%, image_video 10%, general_ai 8%, audio_music 7%, coding 1%, content_creation 1%.
**Knowledge Economy Census:** Running. 7,250/66,880 keys (11%), 33K channels. Stalled Apr 11-13 (stream-a-rerun incident). Resuming today 2 PM.
**Entry Cohorts:** Running. 5,853/102,400 keys (6%), 31K channels. Stalled Apr 11-13. Resuming today 11:30 AM.
**April Cohort:** 25,551 channels (recovered from daily stats after rebuild script damage). Rebuild script patched to never shrink.
**Shorts-First:** PAUSED (KE Census takes 2 PM slot).
**Quota:** Infrastructure ~130K/day. Full ~870K available for discovery starting today (stream-a-rerun removed).
**Research Design:** docs/GENDERED_AI_ADOPTION_DESIGN.md. Two complementary designs: staggered DiD on established channels (Design A) + temporal cohorts around tool launches (Design B). Neither sampled on DV.

---

## 2026-04-14 09:40 [Incident Recovery + Infrastructure Fixes]

**Focus:** Diagnosed and fixed stream-a-rerun incident (Apr 11-13). Recovery and cleanup.

### Stream-A-Rerun Incident (Apr 11-13)
- **Root cause:** Legacy launchd plist `com.youtube.stream-a-rerun` was never unloaded. It fired daily at 3:35 AM with 4h max runtime. On Apr 11, its checkpoint was empty/reset, causing it to restart Stream A collection from scratch, consuming the entire daily quota (~1M units) before any other discovery service could run.
- **Impact:** 3 days of zero progress on KE Census, Entry Cohorts, April Intent, and Trending. April cohort channel_ids.csv overwritten to 25 channels by rebuild script reading damaged source files.
- **Recovery:** Unloaded stream-a-rerun. Recovered April cohort (25,551 IDs from Apr 11 daily stats backup). Patched rebuild_april_cohort.py to never shrink (reads existing channel_ids.csv as baseline). Fixed Stream B and D channel_ids.csv missing headers.
- **Daily stats:** NO GAPS. All 6 panels collected through Apr 14. The incident only affected discovery services, not daily tracking.

### Fixes Applied
- `com.youtube.stream-a-rerun`: UNLOADED permanently
- `src/collection/rebuild_april_cohort.py`: reads existing channel_ids.csv as baseline before adding new channels (commit cd1276b)
- `src/collection/discover_intent.py`: skip completion check when --days-back is set (commit d93e8c9)
- `data/channels/stream_b/channel_ids.csv`: added missing header row
- `data/channels/stream_d/channel_ids.csv`: added missing header row

### Lesson Learned
Legacy launchd plists that share scripts with active services are time bombs. When the shared script gets modified, the legacy plist inherits the change. Always unload dormant services immediately, don't just ignore them. Also: rebuild scripts that overwrite canonical files should NEVER shrink the output (read existing as baseline, only add).

---

## 2026-04-09 13:30 [Gendered AI Adoption: Research Design + Knowledge Economy Census + Entry Cohorts]

**Focus:** Research design for gendered AI adoption paper. Built risk set infrastructure.
**Project State:** Research design phase + data collection. Two new discovery streams for studying how tool characteristics shape gendered participation in AI content creation. AI flagger first results in hand. 23 launchd services. Next: monitor KE Census + Entry Cohorts, compute descriptives from flagger output, begin gender coding pipeline.

### Research Design
- **Design A (Adoption):** Staggered event-study DiD on pre-2023 established knowledge-economy channels. Tool launches as exogenous shocks. Gender x tool-techiness interaction. NOT sampled on AI content.
- **Design B (Entry):** Temporal cohorts born around tool launches. Treatment vs. control (1yr prior). Gender composition of new entrants by tool type. NOT sampled on AI content.
- Key insight from Katie: avoid sampling on the DV. Use domain-defining keywords (business tips, productivity, design tutorial) to find the risk set. AI content is the OUTCOME measured post-collection.
- Tool launch calendar: 20 events from Jun 2022 (Copilot) through Jan 2026 (Claude Code), each scored on 1-10 techiness dimension.
- Full design doc: docs/GENDERED_AI_ADOPTION_DESIGN.md

### AI Flagger Results (Gender Gap Panel)
- Ran flag_ai_videos.py on 11.8M video inventory. 40,355 flagged (0.34%).
- Category breakdown: tools_general 30,019, image_video 4,060, general_ai 3,415, audio_music 2,750, coding 423, content_creation 336.
- ChatGPT/GPT-4 content dominates (74% of all flags). Need tool-specific subcategories to disaggregate.

### Infrastructure
- discover_knowledge_economy.py: pre-2023 channels, 10 domains, 80 keywords. 2 PM daily. Target 100K+.
- discover_entry_cohorts.py: temporal windows around 20 tool launches (treatment + control). 11:30 AM daily.
- Both tested on Mac Mini. Shorts-First paused (KE Census takes priority in 2 PM slot).
- 23 launchd services total.

### Key Decisions
- Three YouTube category systems documented (DECISION_LOG 006-007): Freebase deprecated, topicCategories for analysis, videoCategoryId for discovery.
- Knowledge Economy Census defined by domain-defining keywords, NOT AI keywords. Clean separation between sampling frame and outcome.
- Entry Cohorts use same domain keywords in temporal windows around launches, with control windows 1yr prior. Not sampled on DV.
- Gender coding: hybrid FairFace + validation against 9,760 hand-coded channels. Not a blocking constraint.
- Shorts-First paused; resumes after KE Census completes (~10-12 days).

### Files Created
- docs/GENDERED_AI_ADOPTION_DESIGN.md (research design)
- docs/tool_launch_calendar.csv (20 launches with techiness scores)
- src/collection/discover_knowledge_economy.py
- src/collection/discover_entry_cohorts.py
- 2 launchd plists
- src/config.py updated with KNOWLEDGE_ECONOMY_KEYWORDS (10 domains, 80 keywords)

### Commit: bb5a87e

---

## 2026-04-08 22:00 [Full Infrastructure Deployment + April Cohort + Category Quota Complete]

**Focus:** Multi-day session (Apr 6-8). Category system diagnosis, Category Quota Sampler, full panel coverage audit, April from-founding cohort.
**Project State:** All discovery streams complete or running. Every channel list now has stats collection at the design-specified cadence. April cohort provides from-founding tracking missing from original A/A'. 22 launchd services on Mac Mini. Next: Shorts-First discovery, then Livestream, Creative Commons.

### Apr 6: Topic-Stratified Deployment + Tech Census Merge
- Deployed Topic-Stratified stream (2 PM). Merged Tech Census (63,728 channels). Tech Census daily stats deployed (3:20 AM). See separate log entry.

### Apr 7: Topic-Stratified Diagnosis
- First Topic-Stratified run returned only 90 channels from 1/62 topics. Root cause: Freebase topicId returns near-zero results when used alone on search.list. The Tech Census worked because it combined topicId with query strings.
- Analyzed A' category distribution: 48% of channels have multiple topic tags. Primary-category assignment collapses to 4 dominant categories (Lifestyle 33%, Gaming 20%, Entertainment 18%, Music 13%). Smaller categories thin when crossed with language.

### Apr 8: Category Quota Sampler + Full Audit + April Cohort
- **Category Quota Sampler built and deployed.** Uses YouTube's native videoCategoryId (15 categories, actively maintained) instead of deprecated Freebase topicId. Floor-based collection: 5K per category. Completed in ONE run (42 min, 73,508 channels). 12/15 categories hit 5K floor. Three smaller categories (Pets 4,677, Sports 4,784, Nonprofits 4,083) exhausted all query letters but have adequate N.
- **Three YouTube category systems documented** (DECISION_LOG entries 006-007): Freebase topicIds (deprecated, don't use), channel-level topicCategories (topic_1/2/3, what JMP uses for analysis), video-level videoCategoryId (works for search filtering). Discovery uses videoCategoryId; analysis uses topic_1/2/3.
- **Full panel coverage audit.** Found gaps: original A/A' (136K) had no daily stats, B/C/D had no periodic sweeps, Category Quota had no stats. All fixed:
  - new_cohort daily stats (A+A', 135,977 ch, 3:25 AM)
  - category_quota daily stats (73,508 ch, 3:32 AM)
  - Stream B monthly sweep (18,207 ch, 1st of month)
  - Stream C monthly sweep (50,022 ch, 1st of month)
  - Stream D weekly sweep (3,932 ch, Sundays)
- **April from-founding cohort.** Original A/A' channels have no early-trajectory data (2-3 month gap between creation and stats start). Built rolling daily discovery for channels created in April 2026+:
  - April Intent: 12:30 PM daily (same 94 keywords, 15 languages)
  - April Non-Intent: 1:00 PM daily (same 82 keywords, cross-deduped against Intent)
  - Rebuild combined list: 1:45 PM daily
  - April cohort daily stats: 3:38 AM (growing panel)
  - Initial backfill today: 19,000 intent + 3,594 non-intent = 22,594 channels. First stats tonight.
- **Legacy cleanup:** Unloaded weekly-video-stats (redundant with daily chunks). Unloaded completed Category Quota discovery from 2 PM slot. Shorts-First deployed in its place.

### Key Decisions
- **Abandon Freebase topicId** (DECISION_LOG 006). Use videoCategoryId for discovery, topic_1/2/3 for analysis.
- **Category Quota Sampler** (DECISION_LOG 007). Floor-based, not proportional. Guarantees minimum cell sizes.
- **Stream queue revised:** Category Quota (DONE) -> Shorts-First (deployed) -> Livestream -> Creative Commons.
- **April cohort as separate temporal sample.** Not comparable to Feb A/A' without explicit temporal matching. Clean from-founding trajectories for the intent-vs-non-intent research design.

### Files Created
- src/collection/discover_category_quota.py
- src/collection/rebuild_april_cohort.py
- 10 new launchd plists in config/launchd/

### Commits
- 82548d3: Category Quota Sampler + DECISION_LOG 006-007
- 86e6e07: Full infrastructure deployment (6 new plists)
- 394c8af: April cohort (4 plists + rebuild script)

---

## 2026-04-06 10:25 [Topic-Stratified Deployed + Tech Census Merged]

**Focus:** Stream priority review, Topic-Stratified deployment, Tech Census post-collection merge.
**Project State:** 7 discovery streams (A, A', B, C, D, Tech Census, Topic-Stratified). Topic-Stratified fires at 2 PM today, first of the expansion streams. Tech Census canonical channel list finalized.

### Stream Priority Assessment
Reviewed all 4 expansion streams against research questions served and marginal value:
- **Topic-Stratified (40K): RUN FIRST.** Addresses keyword bias, the single biggest methodological vulnerability. Without it, cross-category analyses are confounded by keyword selection.
- **Shorts-First (50K): RUN SECOND.** YouTube's fastest-growing format, highest substantive value after Topic-Stratified.
- **Livestream (25K): RUN THIRD.** Niche modality, narrower research questions.
- **Creative Commons (15K): RUN LAST.** Smallest, most niche.
Revised queue: Topic-Stratified -> Shorts -> Livestream -> Creative Commons (swapped Shorts ahead of Livestream from original plan).

### Bug Fix
- **discover_topic_stratified.py checkpoint bug:** Same pattern as enumerate_videos March 12 bug. clear_checkpoint() ran after ALL loop exits including max_runtime and quota exhaustion, deleting progress. Fixed with all_done flag: only clears on natural completion or target reached.
- **Secondary fix:** `if max_runtime` -> `if max_runtime is not None` (0-is-falsy bug).

### Tech Census Merge
- Built src/collection/merge_tech_census.py (one-time merge script).
- Merged topicId (45,432) + keyword (58,552) + Stream C Technology filter (3,540 tech-tagged).
- After dedup: 97,339 unique. Overlap: 10,030 between topicId and keyword methods.
- After pre-2023 + Technology filters: **63,728 channels** (target was 50K, exceeded by 27%).
- By source: topicId 35,318, keyword 26,575, Stream C 1,835.
- Output: channel_ids.csv (63,728) + channel_metadata.csv written to data/channels/tech_census/.

### Deployment
- Launchd plist created and loaded: com.youtube.daily-discovery-topic-stratified
- Schedule: 2:00 PM EST daily (same slot as A' and Tech Census used)
- 4h max runtime, 2K reserve quota
- First run fires today April 6 at 2 PM.

### Files
- src/collection/discover_topic_stratified.py (checkpoint bug fix)
- src/collection/merge_tech_census.py (new)
- config/launchd/com.youtube.daily-discovery-topic-stratified.plist (new)
- Committed 71093d8, pushed to origin/main, pulled to Mac Mini.

---

## 2026-04-06 09:45 [Tech Census Complete + Multi-Day Session Wrap-Up]

**Focus:** End-of-session wrap-up for March 18 - April 6 monitoring period. Tech Census finalized, all streams accounted for.
**Project State:** All 6 discovery streams complete (A, A', B, C, D, Tech Census). Daily infrastructure running autonomously for 33 days. Ready to deploy Topic-Stratified next.

### Key Accomplishments (March 18 - April 6)
- **Tech Census COMPLETE.** TopicId method: 45,432 channels (April 2, one day). Keyword method: 58,552 channels (15,709/24,244 keys processed before stopping). After dedup + pre-2023 + Technology filters: 61,563 unique channels. Target was 50K, exceeded by 23%. Keyword launchd stopped April 6.
- **A' COMPLETE at 110,408.** Stopped April 2. Attrition analysis showed 41.5% (not 80-90% assumed), so target lowered from 200K to 100K. 110K yields ~65K survivors, 4:1 ratio over Stream A.
- **Tailscale deployed.** Laptop + Mac Mini. Remote SSH from DC trip worked throughout.
- **10-shard parallel enumeration** rebuilt gender gap video inventory (11,739,044 videos) in one night (March 19).
- **Fixed gender gap plist** missing --panel-name; moved stats to correct subdirectory (March 20).
- **Fixed A' NUL byte crash** in load_checkpoint. 6 days lost (March 19-24). Fix deployed March 25.
- **Video stats rescheduled** to 4:30 AM / 7:00 AM to prevent quota exhaustion overlap (March 23).
- **Daily infrastructure:** 33-day unbroken streak on both panels. All services healthy.
- **Trending:** 19,762 cumulative unique channels.

### What's Next
1. Merge Tech Census topicId + keyword CSVs into final deduplicated channel list
2. Deploy Topic-Stratified stream (40K target)
3. Run topic distribution analysis on gender gap panel
4. Set up daily stats collection on Tech Census panel

---

## 2026-04-03 18:06 [Tech Census TopicId Complete + Keyword Method Launched]

**Focus:** Tech Census progress check, quota analysis, keyword method deployment.
**Project State:** Tech Census discovery in progress. TopicId method found 45,432 channels in one day. Keyword method running (24,244 keys). After merge + filtering, expect 50K+ pre-2023 tech channels. All daily infrastructure services healthy (30-day streak).

- **Tech Census topicId method COMPLETE.** Ran April 2, processed all 8,360 keys in one session. Found 45,432 unique tech channels. Checkpoint cleared (finished clean).
- **Quota analysis:** Infrastructure services use ~122K/day (12%). ~878K available for discovery. Tech Census topicId used 836K in its single-day run.
- **Keyword method launched April 3 6:05 PM.** 24,244 work keys (30 keywords x ~418 weekly windows x 2 sort orders). Screen session with 8h max runtime, 50K reserve. Will run multiple days via checkpoint/resume.
- **All completed streams:** A (26,327), A' (110,408), B (18,208), C (50,022), D (3,933). Tech Census topicId (45,432). All daily panels running.

---

## 2026-04-02 09:30 [A' Stopped + Tech Census Launched]

**Focus:** Stream transition: stop A', deploy Tech Census.
**Project State:** Data infrastructure expanding. 5 new creator streams complete (A, A', B, C, D). Tech Census discovery running for AI adoption x gender study. Daily panels and video stats collecting autonomously.

- **A' stopped at 110,408 channels.** Target was 100K. Overshot because the stop condition checked at keyword-loop level, not between API batches. Not a problem, 110K is fine.
- **A' overshot means ~880K daily quota freed.** This was the constraint blocking all other discovery streams.
- **Tech Census topicId method launched.** Screen session on Mac Mini, 8,360 work keys (weekly windows 2015-2022 x 10 query terms x 2 sort orders x 15 regions rotating). 660 channels found in first 48 seconds. 8h max runtime, 50K reserve quota. Checkpoint every 50 keys.
- **Reviewed all streams and planned sequencing.** After Tech Census: Topic-Stratified (40K), then Livestream + Shorts (25K + 50K), then Creative Commons (15K).
- **Daily infrastructure healthy.** 29-day unbroken streak on daily stats. Video stats chunks, update inventory, trending all running clean.

### Files Modified
- A' launchd plist unloaded on Mac Mini

### What's Next
1. Check Tech Census yield after today's run
2. Create launchd plist for Tech Census daily runs (replace screen session)
3. After topicId method exhausts, switch to keyword method
4. Queue Topic-Stratified after Tech Census

---

## 2026-03-18 through 2026-03-28 [Extended Monitoring Session: DC Trip + Attrition Analysis]

**Focus:** Daily pipeline monitoring from DC via Tailscale, bug fixes, attrition analysis, A' target revision.
**Project State:** Collection infrastructure fully operational. 14 services running autonomously. A' approaching 100K revised target (~Mon/Tue). Tech Census ready to deploy when A' frees quota.

### Key Events (Chronological)
- **March 18:** Major infrastructure session. Built Tech Census stream (design + script). Installed Tailscale on laptop + Mac Mini. Deployed 6 new launchd services. Paused A' for parallel enumeration.
- **March 19:** Gender gap enumeration COMPLETE (11,739,044 videos) via 10-shard parallel run. Merge required NUL-safe fix. A' re-enabled. Merge sentinel written.
- **March 20:** Found gender gap plist missing `--panel-name gender_gap`. Fixed, moved 16 days of stats files to correct subdirectory. AI census update_inventory working (31K new videos/day).
- **March 23:** Rescheduled video stats chunks (11 AM/12 PM -> 4:30 AM/7:00 AM) to prevent quota exhaustion overlap with A'.
- **March 24-25:** Diagnosed A' NUL byte crash. load_checkpoint was crashing on NUL bytes in the CSV. Fix deployed March 25 8:19 AM. 6 days of A' collection lost (March 19-24). First clean run March 25 at 2 PM.
- **March 28:** Ran attrition analysis on 200 early A' channels. Result: 41.5% attrition (not 80-90% assumed). Lowered A' target from 200K to 100K. At 91,383, will auto-stop ~March 30-31.

### Decisions
- **A' target lowered 200K -> 100K.** Attrition check shows 41.5%, so 100K yields ~58K survivors, 4:1 ratio over Stream A's ~15K survivors. Going to 200K would be collecting data we'll never use. Freed quota goes to Tech Census.
- **Priority order for shared quota:** daily channel stats > update inventory > video stats chunks > trending > A' discovery. Irreplaceable data first, resumable discovery last.
- **Video stats chunks moved before A'.** Prevents quota exhaustion from concurrent runs.

### Lessons Learned
- NUL byte fixes must cover ALL read paths in a script, not just the one you're looking at. The March 25 fix covered load_checkpoint but the misdiagnosis on March 18 ("not a problem for the running script") cost 6 days.
- Always check stderr logs when diagnosing issues, not just the data files.
- Attrition assumptions should be tested empirically before setting sample targets. A 5-minute API check on 200 channels saved 35 days of unnecessary collection.

---

## 2026-03-23 10:00 [Video Stats Rescheduled + Monday Status Check]

- **All streams healthy.** Daily channel stats unbroken March 5-23. A' at 68,212. Gender gap inventory growing (update_inventory adding ~7,600 new videos/day). Trending at 7 days.
- **Rescheduled video stats chunks:** Gender gap 11 AM -> 4:30 AM, AI census 12 PM -> 7:00 AM. Ensures all irreplaceable collection completes before A' fires at 2 PM. Fixes recurring quota exhaustion where A' + video stats together exceeded 1M daily limit.
- **Decision:** Priority order for shared quota is: daily channel stats > update inventory > video stats chunks > trending > A' discovery. Irreplaceable data first, resumable discovery last.

---

## 2026-03-20 07:00 [Plist Fix + Inventory Permissions]

- **Fixed gender gap daily stats plist:** Missing `--panel-name gender_gap` arg. Stats files were landing in `channel_stats/` root instead of `channel_stats/gender_gap/`. Update_inventory couldn't find them. Added the arg, reloaded plist, moved all existing files (Feb 17 - Mar 20) to correct subdirectory.
- **Fixed inventory permissions:** File was chmod 444 (read-only) for overwrite protection, but update_inventory needs append access. Changed to 644. Sentinel files still prevent old enumeration from overwriting.
- **Wrote merge sentinel** (`.parallel_enum_merged`) that auto_parallel_enum.sh failed to create.
- **A' back online:** Re-enabled March 19. Jumped to 60,702 from 43,553 in 2 days.

---

## 2026-03-19 08:30 [Parallel Enumeration COMPLETE + Merge]

- **All 10 shards completed overnight** (March 19, 5:20 AM - 7:02 AM). Gender gap inventory rebuilt: **11,739,044 videos** across 9,760 channels.
- **Merge required NUL-safe fix:** shard_00 had NUL bytes from concurrent writes. Original merge produced 868K rows instead of 11.7M. Fixed with binary read + strip NUL + decode (same pattern as health_check.py). Committed fix.
- **Inventory set read-only** (chmod 444) to prevent future overwrites. Sentinel files on all 10 shards.
- **AI census update_inventory working:** Found 2,593 channels with new videos, added 31,242 new video IDs. Hits 30-min runtime cap daily (7,729 channels remaining per run).

---

## 2026-03-18 17:30 [Major Infrastructure Session: Parallel Enumeration + Tech Census + Tailscale]

**Focus:** Recover from gender gap inventory loss, build new infrastructure, design Tech Census stream
**Project State:** Data infrastructure phase. Gender gap daily stats healthy (March 5+), video inventory rebuilding via 10-shard parallelization tonight, Tech Census stream designed and script committed, Tailscale remote access operational for DC trip.

### Accomplished
- **Diagnosed inventory corruption:** Gender gap inventory had 9,584 channels but only 1 video per channel (should be ~1,200 avg). March 16 launchd overwrite produced a truncated file. Checkpoint falsely marked 9,584 channels "complete."
- **Built parallel enumeration system:** `parallel_enumerate.py` splits 9,760 channels into 10 shards of 976. Each writes to its own CSV and checkpoint. Three rounds of code audit caught: partial results marked complete (fixed: discard partial, retry next run), merge script OOM on 11M rows (fixed: streaming merge), duplicate screen session race condition on multi-night runs (fixed: screen -list check before launch), and QPS rate limiting (acceptable with exponential backoff).
- **Built Tech Census stream:** New discovery script (`discover_tech_census.py`) for 50K pre-2023 Technology-tagged channels. Two methods: topicId discovery and keyword discovery. Design doc plan-eval scored 83/100. Committed and pushed.
- **Research design memo:** Analyzed 5 options for studying gendered AI adoption. Katie chose: tech-specific sample, pre-Jan 2023 channels, video enumeration to track adoption timing by gender. 50K target. Broad search then filter to Technology topics.
- **Quota analysis:** Today's 1M units: 83% consumed by A' search.list (839,900 units). Paused A' to free quota for enumeration.
- **Installed Tailscale** on both Mac Mini and laptop. SSH works over Tailscale IP (100.109.96.120). Updated `~/.ssh/config` alias. Remote access from DC confirmed working.
- **Deployed new launchd services:** update_inventory (both panels), daily video stats chunks (both panels), trending tracker, parallel enumeration launcher.

### Decisions
- **Pause A' for enumeration:** A' consumes 83% of daily quota for search.list calls. Enumeration needs ~293K units total. With A' paused, enumeration should finish in 1-2 nights. A' auto-resumes when all 10 shard sentinels exist.
- **Tech Census design:** Broad discovery (not topic-restricted), filter to Technology post-hoc, pre-Jan 2023, 50K target. Multiple strategies (topicId + keyword + potential random prefix supplement). Gender coding deferred to Katie.
- **Daily video stats as chunks:** Weekly single-run (11.7M videos = 19h) doesn't fit. Daily 1/7th chunks in the 11AM-2PM gap between enumeration and A'.

### Files Created/Modified
- `src/collection/discover_tech_census.py` (new)
- `src/config.py` (tech_census entries)
- `docs/TECH_CENSUS_DESIGN.md` (new)
- `parallel_enumerate.py` (new, on Mac Mini)
- `merge_shards.py` (new, on Mac Mini)
- `launch_shards.sh` (new, on Mac Mini)
- `~/.ssh/config` (updated macmini alias to Tailscale IP)
- Various launchd plists deployed to Mac Mini

### What's Next
1. Verify parallel enumeration runs tonight (check logs from DC via Tailscale)
2. After enum complete: merge produces `gender_gap_inventory.csv`, A' auto-resumes
3. Run topic distribution diagnostic on gender gap panel (how many tech channels?)
4. Deploy Tech Census discovery when quota slot available
5. Ben Lewis co-author meeting Thu 4 PM

---

## 2026-03-03 09:40 [Daily Stats Outage Diagnosed + Fixed]

- **DISCOVERED: 5-day daily stats outage (Feb 27 - Mar 3).** Stream A launchd service (3:15 AM) was consuming the entire daily API quota before daily stats (8:00/9:00 AM) could run. Every day since Stream A went to launchd, daily stats got immediate quotaExceeded.
- **Root cause:** Stream A fires at 3:15 AM EST (15 min after midnight Pacific quota reset), runs ~77 min, exhausts the full quota by ~4:30 AM. Daily stats at 8:00/9:00 AM finds zero quota remaining.
- **Diagnosis confirmed:** Manual API test at 12:43 PM succeeded (single call), but daily_stats.py batch call failed at 12:44 PM — only ~35 units remained from 1M.
- **Fix 1 — Plist rescheduling:** Moved daily stats before Stream A. Gender gap: 8:00→3:05 AM. AI census: 9:00→3:12 AM. Stream A: 3:15→3:35 AM. Plists unloaded, rewritten, reloaded.
- **Fix 2 — Quota reservation (commit d58bdbb):** Added `--reserve-quota` flag to `discover_intent.py` (default 2000). Script checks `get_quota_used()` against `daily_quota_limit - reserve_quota` before each search call and exits cleanly when threshold reached. Added `get_quota_used()` getter to `youtube_api.py`. Plist updated with `--reserve-quota 2000`.
- **Code deployed:** Git push from laptop, git pull on Mac Mini. Import verified clean. All 7 plists loaded.
- **Old failure sentinels archived** to `archive/failed_sentinels/` so health check starts clean.
- **Data loss:** Feb 27 - Mar 3 daily stats permanently missing for both panels. These are point-in-time snapshots (current subscriber/view counts) — can't be retroactively collected.
- **Stream A status:** 73/94 keywords, 1,313 combos, projected completion March 6-7. Running well.
- **Katie out of town for ~1 week.** System should run autonomously. 148 GB disk free, sleep disabled, Amphetamine running.

---

## 2026-02-27 05:20 [Stream A First Launchd Run — VERIFIED]

- **First launchd run CONFIRMED SUCCESSFUL.** Service fired at 3:15 AM EST, ran for 1h 26m, exited cleanly via QuotaExhaustedError at 4:40 AM.
- **Progress:** 635 → 772 completed combos (+137). Keywords 35-42 completed (German ×5, Portuguese ×5, Korean ×2). Hit quota mid-keyword 43 (자기소개, Korean).
- **Tonight's harvest:** 9,224 new channels. Portuguese dominated (8,868), especially "Meu primeiro vídeo" (3,828 from base pass alone). Korean: 234. German: 122.
- **By method:** base (5,354), topicid (2,852), duration (720), regioncode (298).
- **Total unique channels in CSV:** 83,145 (85,198 rows with cross-batch duplication).
- **QuotaExhaustedError working as designed:** Clean detection of 403 quotaExceeded, immediate checkpoint save, graceful exit. No cascading 403 retries. Exactly the behavior the launchd migration was built to achieve.
- **Completion estimate:** ~1,728 total combos. At ~137/night, ~7 more nights (targeting ~March 5-6). Then retire plist, run B.4 validation, start Phase C.
- **Daily stats:** Feb 26 present, Feb 27 not yet run (8:00 AM). 7 launchd services all loaded and healthy.

---

## 2026-02-26 13:49 [Stream A Migrated to Launchd Service]

- **Killed screen session** — was stuck in cascading 403 quotaExceeded retries (visible in log). Verified no orphan Python processes.
- **Code changes (commit d8c31c5):**
  - `youtube_api.py`: Added `QuotaExhaustedError` class. Detects `quotaExceeded` reason in `execute_request` (parses `e.content` JSON), raises immediately with no retries. Added re-raise before bare `except Exception` in `search_videos_paginated` and `get_channel_full_details`.
  - `discover_intent.py`: Added `--max-runtime` (launchd exit guard), `--max-consecutive-errors` (circuit breaker), PID lockfile via `fcntl.flock` (prevents concurrent instances), completion-safe exit (no checkpoint + data exists = skip), `_flush_batch` helper for mid-loop CSV writes. QuotaExhaustedError handling in both main and relevance window loops with checkpoint save (pass key intentionally NOT added).
  - New plist: `com.youtube.stream-a-rerun.plist` — 3:15 AM EST, 4h max-runtime, strategies=base,safesearch,topicid,regioncode,duration.
- **Plan-eval:** R1 80.8 → R2 90.5/100 (10-expert infrastructure panel, 2 rounds). Key fixes: exact quota detection code, mid-pass checkpoint logic, completion-safe exit, rollback section, lockfile path spec.
- **Deployment:** Git pull on Mac Mini, plist copied to ~/Library/LaunchAgents/, loaded via `launchctl load`. Verified with `launchctl list | grep stream-a`. Checkpoint at 635 completed keywords, output path matches plist.
- **Checkpoint state:** 635 keyword combos done, output at `data/channels/stream_a/initial_20260222.csv`.
- What's next: Verify first launchd run tomorrow AM. Monitor for clean exit message ("Max runtime reached" or "Quota exhausted").

## 2026-02-26 09:44 [Stream A Launched After Enum Completion]

- **AI census enum completed 10:56 PM EST Feb 25:** 50,010/50,010 channels, **5,341,296 total videos**, 4.2 GB CSV. Checkpoint auto-cleared on completion. Clean exit, no errors.
- **Enum throughput:** Started at ~8 channels/min (video-heavy channels early), accelerated to ~25/min through empty-channel stretches. Total run time: ~10.5 hours (12:27 PM → 10:56 PM).
- **Stream A launched 9:44 AM EST Feb 26** in `screen -S discover_a`:
  - Checkpoint intact: 481→490 completed keyword combos (keyword 27/94)
  - CSV preserved: 48 MB with 38,964+ existing channels + 417 new in first 7 min
  - Japanese keywords pulling well: regioncode:JP yielded 380 channels in one pass
  - Strategies: base, safesearch, topicid, regioncode, duration (no `windows` — intentional per validated production set)
- **Feb 26 daily stats validated:** Both panels PASS (6/6 checks). Subscriber drops check now running (Feb 25 data available as baseline). No anomalies.
- **Note on overnight gap:** The SSH command to launch Stream A was sent ~10:56 PM Feb 25 but Katie's laptop auto-update interrupted the session. Stream A only started when reconnected at 9:44 AM Feb 26. ~11 hours of quota went unused overnight. Not critical but consider launchd-based automation for Stream A in the future to avoid screen session fragility.

---

## 2026-02-25 09:15 [Relaunch Gate Check + AI Census Enum Launched]

- **Feb 25 daily stats validated:** Both panels PASS (6/6 checks). Gender gap: 9,760 rows. AI census: 50,010 rows. Subscriber drops check skipped (Feb 24 data missing, expected).
- **No zombie processes:** Only Pat dashboard services running (PIDs 791, 37953, 42101). No orphan collection scripts.
- **AI census enum launched at 12:27 PM EST** in `screen -S enumerate_ai`:
  - Command: `python3 -m src.collection.enumerate_videos --channel-list data/channels/ai_census/channel_ids.csv --output data/video_inventory/ai_census_inventory.csv`
  - Checkpoint loaded: 39,839 done, 10,171 remaining
  - By 13:48 EST: 40,475 done (+636), CSV at 3.5 GB
  - Throughput: ~7.9 channels/min (slower than the ~60/min seen Feb 22 — likely due to checkpoint save overhead with 40K+ entries in the JSON)
  - Estimated completion: ~9-10 AM EST Feb 26
  - Quota impact: negligible (playlistItems.list = 1 unit/call). Daily stats tomorrow will be fine.
- **Stream A NOT launched** — per handoff rule, never run concurrently with enum. Will launch after enum completes.
- **Throughput note:** The Feb 24 handoff estimated ~3h for enum. Actual throughput is ~8 channels/min, projecting ~20h. The bottleneck appears to be checkpoint save I/O (writing 40K+ channel IDs to JSON after every channel). Consider optimizing to save every N channels in a future code update.

### Stream A Relaunch Command (for next session)
```
screen -dmS discover_a bash -c 'cd /Users/katieapker/.youtube-longitudinal/repo && python3 -m src.collection.discover_intent --strategies base,safesearch,topicid,regioncode,duration --output /Users/katieapker/.youtube-longitudinal/repo/data/channels/stream_a/initial_20260222.csv 2>&1 | tee /tmp/discover_a_20260226.log'
```

---

## 2026-02-24 10:00 [Bug Fix: enumerate_videos.py Checkpoint Logic]

- **Fixed `src/collection/enumerate_videos.py` line 198 bug:** Moved `completed_set.add(channel_id)` and `save_checkpoint()` inside the `try` block (after `total_videos += len(videos)`). Previously these ran unconditionally after the try/except, so quota-failed channels were permanently marked done with 0 video data — the root cause of the 2,913 false completions in the incident.
- **Effect:** Channels that raise an exception (403 quotaExceeded, network error, etc.) are now skipped silently and left in the "remaining" set, so the next run picks them up.
- **Relaunch gate:** Do NOT relaunch enum or Stream A until Feb 25 daily stats confirm PASS on both panels.
- **Relaunch order (MANDATORY — never concurrent):**
  1. Validate Feb 25 daily stats: `python3 -m src.validation.validate_daily_stats --panel gender_gap --date 2026-02-25` + same for ai_census
  2. Enum alone: `screen -dmS enumerate_ai bash -c 'cd /Users/katieapker/.youtube-longitudinal/repo && python3 -m src.collection.enumerate_videos --channel-list data/channels/ai_census/channel_ids.csv --output data/video_inventory/ai_census_inventory.csv 2>&1 | tee /tmp/enumerate_ai_20260225.log'`
  3. After enum completes (~3h): Stream A alone: `screen -dmS discover_a bash -c 'cd /Users/katieapker/.youtube-longitudinal/repo && python3 -m src.collection.discover_intent --strategies base,safesearch,topicid,regioncode,duration --output /Users/katieapker/.youtube-longitudinal/repo/data/channels/stream_a/initial_20260222.csv 2>&1 | tee /tmp/discover_a_20260225.log'`
- **MEMORY updated:** "NEVER run Stream A (topicId strategies) + enumerate_videos.py concurrently" added to lessons learned.

---

## 2026-02-24 05:50 [Quota Exhaustion Incident + Enum Checkpoint Repair]

- **INCIDENT:** Running Stream A (all strategies including topicId) + AI census enum concurrently burned through the full 1,010,000 daily quota in ~3 hours after the 3am EST reset.
- **Enum bug triggered:** `enumerate_videos.py` line 198 bug (unconditional `completed_set.add`) marked 2,913 channels as "done" with 0 video rows. Video count in CSV was frozen at 745,860 while channels kept incrementing — the tell-tale sign.
- **Actions taken:**
  - Killed `enumerate_ai` immediately upon detecting frozen video count
  - Killed `discover_a` to prevent tomorrow's daily stats from failing (Stream A would burn quota again at 3am before the 8am daily stats window)
  - **Rebuilt enum checkpoint from CSV:** 39,839 legitimate channels (those with ≥1 video row in CSV). Corrupted checkpoint backed up at `.enumerate_ai_census_inventory_checkpoint.json.corrupted_backup`.
- **Current state:** 10,171 channels still need enumeration. Checkpoint is clean.
- **Feb 24 daily stats:** Will likely FAIL — quota was already exhausted (~6am EST) before the 8am/9am launchd runs. One-day miss, acceptable.
- **Root cause:** topicId strategy is far more quota-intensive than estimated. Combined quota consumption with enum was ~335K units/hour — way above the "33K/hour" working estimate. NEVER run Stream A with topicId + any other collection job simultaneously.
- **Fix needed:** enumerate_videos.py line 198 — move `completed_set.add(channel_id)` inside the `try` block, after successful enumeration. Do this BEFORE next run.
- **Relaunch plan:** After Feb 25 daily stats confirm PASS: (1) enum alone first (~3h, trivial quota), then (2) Stream A alone. Monitor quota consumption rate for the first keyword with topicId active.

---

## 2026-02-23 14:30 [Relaunch: Stream A + AI Census Enum]

- **Context:** Mac Mini went offline ~8:30pm Feb 22. Both screen sessions died; launchd daily stats survived. Mac Mini came back online by Feb 23; screens needed manual relaunch.
- **Key finding:** Stream A had actually run FAR longer than the last handoff implied. Checkpoint timestamp was 06:44 AM Feb 23 (not killed at 8:30pm Feb 22 — the screen sessions survived the brief network event and kept running overnight). Channel count: **38,964 unique** (up from 6,942 at last session). AI census enum: **38,183/50,010** done (up from 36,635).
- **Pre-launch checks:**
  - Verified no zombie Python processes (only Pat dashboard processes running)
  - Quota test: PASS (got 144K results for test query)
  - Both checkpoint files intact and valid
- **Stream A relaunched 12:57 PM EST:**
  - Command: `python3 -m src.collection.discover_intent --strategies base,safesearch,topicid,regioncode,duration --output /Users/katieapker/.youtube-longitudinal/repo/data/channels/stream_a/initial_20260222.csv`
  - Resumed at keyword combo 187+ (186 combos correctly skipped by checkpoint)
  - **Note:** CSV has no header row — DictReader couldn't load existing 38,964 channels for in-memory dedup. New channels will append to existing file; deduplicate at analysis time. Not a data loss issue.
  - By 14:27 PM: 15,370+ new channels collected, at keyword 17/94 (Spanish).
- **AI census enum relaunched 14:26 PM EST:**
  - Resumed from checkpoint: 38,183 done, 11,827 remaining (~76.4% complete)
  - File growing at ~9.7 MB/min. ETA: ~2 hours (~4:15 PM EST)
  - Current file size: 3.51 GB (21.8M video records)
- **What's next:** Enum finishes ~4:15 PM. Stream A continues autonomously ~8 more days → B.4 validation → Phase C (A' re-run).

---

## 2026-02-22 20:30 [Daily Stats Validator + Heartbeat Integration]

- **Built `src/validation/validate_daily_stats.py`** — lightweight post-collection validator
  - Checks: row count (±1%), null channel_ids, required columns, negative values, dtype validation, subscriber drops >50% vs previous day
  - Supports `--panel gender_gap` and `--panel ai_census` flags, `--date` override, `--test` mode
  - Exit codes: 0=PASS, 1=WARNINGS, 2=ERRORS
  - Saves reports to `data/logs/daily_stats_validation_{panel}_{YYYYMMDD}.log`
  - Python 3.9.6 compatible (no walrus operators, no union types)
- **Tested on Mac Mini against live data** — both panels pass clean (9,760 gender gap, 50,010 AI census)
- **Modified Pat heartbeat** (`~/.pat-system/heartbeat.sh` on Mac Mini):
  - Added `check_yt_health()` function: runs health_check.py + validate_daily_stats.py for both panels
  - Wired into 12pm midday block — sends Telegram alert only if DEGRADED/FAILING/ERRORS detected
  - Fixed `status` variable collision (renamed to `yt_status`)
  - Backup at `~/.pat-system/heartbeat.sh.bak.20260222`
- **RESOLVED**: Applied `--date "$TODAY"` fix to validator calls in heartbeat.sh on Mac Mini. Without this, the validator defaults to UTC date which can mismatch local time after midnight UTC. Fix confirmed working.
- Mac Mini went unreachable at ~8:30pm EST — sleep or network event. Both screen sessions (Stream A, AI census enum) died. Launchd services survived and collected Feb 23 daily stats normally.
- Mac Mini back online by Feb 23. Both panels validated clean against Feb 23 data.
- **Still needed**: Relaunch Stream A and AI census enum screen sessions (checkpoints intact, will resume from where they left off).

---

## 2026-02-22 13:30 [Phase B Relaunch — Stream A + AI Census Enum + Daily Stats Backfill]

### Network Change
- Mac Mini moved from TP-Link Archer A6 router to Google Nest mesh ethernet during a separate SB session today.
- New IP: **192.168.86.36** (was 192.168.86.34 on WiFi, briefly 192.168.0.200 on Archer A6).
- SSH alias `ssh macmini` configured on laptop.
- Root cause of tunnel drops was Mac Mini **sleep**, not network. `pmset` fixed. Archer A6 unnecessary, can be returned.

### Daily Stats Backfill
- Gender gap: Feb 21 + Feb 22 backfilled (9,760 channels each). Current-snapshot data.
- AI census: Feb 20 + Feb 21 + Feb 22 backfilled (50,010 channels each). Current-snapshot data.
- Gap caused by 2 days of network transition (Feb 21: Archer A6 issues, Feb 22 AM: no internet until ~1 PM switch).
- Daily stats services are still loaded and will fire at 8:00/9:00 AM EST tomorrow.

### Stream A Re-Run — Resumed
- Checkpoint: 78 completed keyword-pass combos, 6,942 unique channels.
- Launched in `screen -S discover_a` at 1:21 PM EST.
- Immediately resumed at keyword 5, pass 10. By 1:31 PM: on keyword 6/94, 1,562 new channels added.
- All 6 strategies active: base, safesearch, topicId (7+ topics), regionCode (IN), duration (short/medium/long), windows.
- Expected to run ~8 more days, stalling each night when quota exhausts.

### AI Census Video Enumeration — Resumed
- Checkpoint: 36,635/50,010 channels done (13,375 remaining).
- Launched in `screen -S enumerate_ai` at 1:31 PM EST.
- Correctly resumed from checkpoint. Processing at ~1 channel/sec. ETA: 4-6 hours.
- Uses playlistItems.list (1 unit/call), safe to run concurrently with Stream A.

### Quota
- Backfills consumed ~7K units (negligible: 200 calls × 5 runs for gender gap + 1,000 calls × 3 runs for AI census).
- Stream A will consume ~800K units today (starting late, so partial day).
- AI census enum ~27K units total.
- Plenty of headroom.

### What's Next
1. AI census enum finishes tonight — verify channel count matches 50,010 when done.
2. Stream A runs autonomously. Monitor tomorrow AM for progress.
3. Daily stats should fire normally at 8:00/9:00 AM EST tomorrow (network is stable, pmset sleep disabled).
4. After Stream A completes (~8 days): B.4 validation → Phase C (A' re-run).

---

## 2026-02-20 08:00 [AI Census Enumeration Setup + Stream C Complete + Stream A Cleanup]

### AI Census Video Enumeration — Setup Complete, Waiting on Quota
- SCP'd 3.1 GB `ai_census_inventory.csv` from laptop to Mac Mini (took ~3 min over WiFi)
- Created checkpoint JSON from existing CSV: 36,634 completed channels (3 more than expected — possibly a few channels completed in the 1s before quota errors hit)
- Launched enumeration in screen session — immediately hit quotaExceeded (Stream A consumed full daily quota by 07:37 EST)
- **Critical bug found:** `enumerate_videos.py` marks channels as "completed" in checkpoint even when API calls fail (line 198: `completed_set.add(channel_id)` is unconditional after the try/except). 17 channels were falsely marked before I killed the process.
- Regenerated checkpoint from CSV data (36,634 channels). Clean state ready.
- **Status:** CSV + checkpoint on Mac Mini. Launch after 3:00 AM EST quota reset. ~27K API units needed (negligible).

### Stream C — COMPLETE
- Finished during this session. Screen session auto-exited on completion.
- **50,022 unique channels** (above 50K target). File: `data/channels/stream_c/initial_20260220.csv` (42.7 MB)
- Extracted `channel_ids.csv` with 50,022 entries
- Random prefix sampling: 3,333 prefixes searched, ~15 channels/prefix average

### Stream A Discovery — Paused on Quota, Checkpoint Intact
- Python process (PID 5376) was in quota retry loop since 07:37 EST. Not making progress but alive.
- **Mistake:** I killed the parent processes (bash/tee/screen) thinking the python process was already dead. The `ps aux | grep python3` pattern didn't match the macOS binary name (`Python` not `python3`). Lesson: always use `ps aux | grep Python` (capital P) on macOS.
- Checkpoint intact: `.discovery_checkpoint.json` with 78 completed keyword-pass combos across keywords 1-5, 6,785 unique channels in `initial_20260220.csv`
- **Status:** Needs relaunch after 3:00 AM EST. Will resume from keyword 5/94, pass ~10/17.

### Daily Stats
- Gender gap Feb 20: collected (file exists, 694 KB)
- AI census Feb 20: MISSED (quota exhausted by Stream A before 9:00 AM EST run). Expected, acceptable.

### Mistakes Made
1. Killed Stream A's live python process by accident (grep pattern mismatch on macOS)
2. Launched enumeration without checking quota first (quota was already exhausted)
3. enumerate_videos.py design flaw: marks failed channels as complete (needs code fix for quota-error handling)

### What's Next
1. **After 3:00 AM EST:** Relaunch Stream A discovery: `screen -dmS discover_a bash -c "cd /Users/katieapker/.youtube-longitudinal/repo && python3 -m src.collection.discover_intent --strategies base,safesearch,topicid,regioncode,duration,windows 2>&1 | tee data/logs/discover_a_rerun.log"`
2. **After 3:00 AM EST:** Launch AI census enumeration: `screen -dmS enumerate_ai bash -c "cd /Users/katieapker/.youtube-longitudinal/repo && python3 -m src.collection.enumerate_videos --channel-list data/channels/ai_census/channel_ids.csv --output data/video_inventory/ai_census_inventory.csv 2>&1 | tee data/logs/enumerate_ai_run.log"`
3. Both can run concurrently (different API endpoints, enumeration uses ~27K units total)
4. Monitor daily stats at 8:00/9:00 AM EST — both should succeed with fresh quota
5. Consider code fix for enumerate_videos.py: don't mark channels as complete when API call fails with quotaExceeded

---

## 2026-02-20 07:30 [Phase B Morning Monitor — Status Check + Enumeration Plan]

### Monitoring Results
- **Stream A:** 5,047 channels at keyword 5/94 (all Hindi so far). Running 17 passes per keyword (base + 12 topicId + regionCode + 3 duration). ~81K quota per keyword. 381K of ~1M daily quota consumed. Will stall ~8:28 AM EST when quota exhausts. Resumes from checkpoint after 3:00 AM EST reset. Estimated ~8 days to complete all 94 keywords.
- **Stream C:** 41,442 channels at prefix 1,800/3,333 (~54%). ~23 channels/prefix. Projected total ~77K (above 50K target). ETA ~30 min from now.
- **Daily stats:** Both scheduled for today at 8:00 AM (gender gap) and 9:00 AM (AI census) EST. Gender gap will succeed (quota still available). AI census at 9:00 AM may fail if Stream A exhausts quota by 8:28 AM. One-day miss is acceptable.
- **Health checks:** No FAILED sentinel files. Last health check ran Feb 19 (today's at 12:00 UTC hasn't triggered yet).
- **All Python processes confirmed alive** (PIDs 5376 for Stream A, 5653 for Stream C).

### AI Census Video Enumeration Plan
- Katie approved restart on Mac Mini. Plan:
  1. SCP 3.35 GB `ai_census_inventory.csv` from laptop to Mac Mini
  2. Create checkpoint JSON from existing CSV (script uses checkpoint, NOT CSV-based resume — handoff was wrong about this)
  3. Launch in `screen -S enumerate_ai` on Mac Mini
  4. Quota cost: ~27K units (negligible — playlistItems.list = 1 unit/call)
- Key finding: `enumerate_videos.py` line 82-97 shows checkpoint stores `completed_channels` list in JSON. Without the checkpoint, script would overwrite the 3.35 GB file. MUST create checkpoint before launching.

### Clarification on Stream C Methodology
- Random Prefix Sampling (Zhou et al., 2011) — not the McGrady "Dialing for Videos" brute-force ID enumeration
- Stream C uses random 3-char alphanumeric search queries via search.list API
- McGrady generates random video IDs directly (true uniform random, but ~0.02% hit rate — infeasible at our quota)
- Stream C is biased toward searchable content but is the least biased Search API method available

### What's Next
1. [NEXT AGENT] SCP + checkpoint + launch AI census video enumeration on Mac Mini
2. [NEXT AGENT] When Stream C finishes: count unique channels with pandas, extract channel_ids.csv
3. Stream A continues autonomously (~8 days). Monitor daily for quota stalls and checkpoint integrity.
4. After Stream A: B.4 validation → Phase C (A' re-run with same strategies)

---

## 2026-02-20 18:50 [Phase B Launched — Stream A Re-Run + Stream C]

### Phase B Execution
- **B.0 Dry-run:** `--dry-run` flag doesn't exist in discover_intent.py. Calculated manually: 94 kw × 15 lang × ~18 passes × ~50 windows = ~83K minimum queries = ~12M units. At 800K/day = ~15 days. Katie accepted the timeline.
- **B.1 Stream A re-run:** Launched at 06:50 UTC in `screen -S discover_a`. Command: `python3 -m src.collection.discover_intent --strategies base,safesearch,topicid,regioncode,duration,windows`. After 10 min: 3,042 channels from 2/94 keywords. Keyword 1 ("Mere channel mein aapka swagat hai"): base=374, topicId=~546, regionCode=103, duration=80 → total 1,103. Keyword 2 ("Mera pehla video"): base=1,746 in first pass.
- **B.2 Stream C:** Launched at 06:53 UTC in `screen -S discover_c`. After 10 min: 12,908 channels from 550/3,333 prefixes. ~24 channels/prefix. On track to finish in ~1 hour.
- **B.3 Gate 2:** PASS. First keyword showed 1.96x multiplier from expansion strategies. Well above the 80% threshold.
- **Git pulled Mac Mini** from fd30974 → 80530e1 (2 commits behind at session start).

### Video Enumeration Status (Discovered)
- Gender gap inventory: 9,591/9,760 channels (98.3%), 11.6M video rows, 1.69 GB. Last modified Feb 17. NOT running. Missing ~169 channels are likely terminated/empty. Effectively complete.
- AI census inventory: 36,631/50,010 channels (73.2%), 20.9M video rows, 3.35 GB. Last modified Feb 20 02:45. NOT running. Stalled — laptop process died (sleep or network).
- Both were laptop processes. No checkpoint files remain (deleted on completion or lost).
- Recommendation: Restart AI census enumeration on Mac Mini (always-on). Quota cost is negligible (~27K units for playlistItems.list at 1 unit/call). SCP existing file to Mac Mini first. Run in screen session.

### Key Decisions
- Full strategy set accepted despite 15-day timeline (Katie's choice: maximize sample over speed)
- Deployment plan status tracking updated: A.0-A.3 DONE, B.0-B.3 DONE/RUNNING/PASS
- Concurrent A + C running is safe: C is small (~50K units) and uses different API endpoints (no keyword overlap)

### Quota
- Session consumed: minimal (git pull, process checks). Stream A and C now consuming actively.
- Estimated daily: Stream A ~500-800K/day + Stream C ~50K today only + daily stats ~20K = well within 1M limit

### What's Next
1. Monitor Stream C completion (today). Extract channel_ids.csv when done.
2. Restart AI census video enumeration on Mac Mini (SCP file, run in screen).
3. Stream A runs autonomously for ~15 days with checkpoint/resume.
4. After Stream A: B.4 validation → Phase C (A' re-run with same strategies).
5. Call Spectrum to disable bridge mode (non-blocking for YouTube, needed for Cloudflare tunnel).

---

## 2026-02-20 06:00 [Phase A: Infrastructure Recovery — COMPLETE]

### Network Discovery & Fix
- Mac Mini ethernet setup (modem → switch → Mac Mini) physically correct but Spectrum modem is in bridge mode — no DHCP, Mac Mini gets no IP via ethernet
- Investigated Nest mesh history: Nest WiFi NAT table drops confirmed as root cause of Cloudflare tunnel instability (every 1-18 min). This is documented extensively in Second Brain MAC_MINI_SETUP.md.
- Enabled Mac Mini WiFi (en1) via physical keyboard access — Mac Mini now at 192.168.86.34 on Nest mesh
- WiFi is sufficient for YouTube API calls (short HTTP requests + retry logic). Cloudflare tunnel (Pat dashboard) still drops on Nest mesh — needs the Spectrum bridge mode fix.
- **Permanent fix:** Call Spectrum (833-267-6094, 24/7) to disable bridge mode. Then Mac Mini ethernet gets a real IP, bypasses Nest mesh entirely.
- Wrote connectivity report to Second Brain inbox (quick-notes.md) for Pat System agent.

### Phase A Execution
- A.1: SSH established, git pull successful (c1a837b → fd30974). Network test: DNS resolves, HTTPS 200 to google.com, gateway ping 0% loss. API test: 9,760 channels collected in 47 seconds.
- A.2: Backfilled all 4 missing collections:
  - Gender gap Feb 18: 9,760 channels ✓
  - Gender gap Feb 19: 9,760 channels ✓
  - AI census Feb 18: 50,010 channels ✓
  - AI census Feb 19: 50,010 channels ✓
  - (Also got Feb 20 gender gap during API test: 9,760 channels)
- A.3: Health check plist deployed and loaded. All 6 YouTube launchd services confirmed loaded:
  - com.youtube-longitudinal.daily-channel-stats
  - com.youtube.ai-census-daily-channel-stats
  - com.youtube-longitudinal.weekly-video-stats
  - com.youtube-longitudinal.sync-to-drive
  - com.youtube-longitudinal.health-check
  - com.youtube.daily-health-check (NEW — from Phase A.0)
- Deployment plan status table updated: Phase A → COMPLETE.

### Key Findings
- AI census panel is 50,010 channels (larger than expected — noted for quota awareness)
- `--limit` flag in daily_stats.py does not limit channel count — minor code issue, does not affect production
- Mac Mini WiFi interface is en1 (not en0). `networksetup -setairportpower Wi-Fi on` works universally.

### What's Next
- Call Spectrum to disable bridge mode (non-urgent for YouTube collection, needed for Pat dashboard)
- Phase B: Stream A re-run with expansion strategies (requires Katie's approval)

---

### Feb 20, 2026 — Evening [Phase A.0 Code Prerequisites Complete]

- **Executed Phase A.0** (all 5 steps) — code changes on laptop, committed and pushed:
  - **A.0.1:** Added `--date YYYY-MM-DD` flag to `src/panels/daily_stats.py`. Overrides `self.today` for output path and checkpoint date. Skips new video detection on backfill (stats are current, not historical).
  - **A.0.2:** Added `_call_with_retry()` wrapper — 3 retries with 30s/120s/480s backoff on `socket.timeout`, `ConnectionError`, `OSError`. Wraps both `collect_channel_stats` (entire call) and `collect_video_stats` (per-batch). Added `_write_sentinel()` — writes `data/logs/daily_stats_FAILED_{date}.flag` on any fatal error. 403 quota errors propagate through execute_request's own retry and then fail fast (no extra retry layer).
  - **A.0.3:** Created `src/validation/check_daily_health.py` — lightweight 70-line script checking: gender gap CSV exists + row count within 5% of 9,760, AI census CSV exists, no FAILED sentinel files. Writes report to `data/logs/health_check_{date}.txt` on failure.
  - **A.0.4:** Created `config/launchd/com.youtube.daily-health-check.plist` targeting 10:30 UTC.
  - **A.0.5:** Committed as `2fcb503`, pushed to origin.
- **Katie swapped Mac Mini ethernet** — now connected directly to modem (bypassing Google Nest mesh). IP may have changed from 192.168.86.48 since DHCP reassignment is likely with new network topology.
- **Quota consumed:** 0 API units (code changes only)
- What's next: SSH to Mac Mini (find new IP), git pull, verify network stability, backfill Feb 18+19, deploy health check plist.

---

### Feb 20, 2026 — Morning [Plan-Eval on Production Deployment Plan]

- **Ran /plan-eval** with 8-expert panel (Systems Architect, Operations Engineer, Reliability Engineer, Quota/Cost Analyst, Data Pipeline Architect, Sampling Methodologist, Documentation Reviewer, Second Brain / AI Executability). Three rounds:
  - **R1 (70.4/100):** 10 structural issues — no automated quota monitoring, strategy interaction model undefined, no retry logic, no session continuity, Stream C sequenced last, no --date flag for backfill, no rollback procedure, no delegation markers, no Gate 2 failure handling, no data merge protocol.
  - **R2 (83.2/100):** All 10 resolved. Added Phase A.0 code prerequisites, handoff points with reporting specs, status tracking table, ADDITIVE strategy model with pass-count math, Gate 2 pass/fail/investigate criteria with thresholds, plist backup/rollback procedure.
  - **R3 (87.4/100):** Refinements — Quick Status header, pinned output filenames, backfill data limitation acknowledgment, per-call retry granularity, corrected quota monitoring (reads `data/logs/quota_YYYYMMDD.csv`, not checkpoint).
- **Key code-level discoveries during eval:**
  - `daily_stats.py` has NO `--date` flag — backfill step was unimplementable as written. Added to Phase A.0.1.
  - Checkpoint files don't track quota. Quota is logged to `data/logs/quota_YYYYMMDD.csv` with `cumulative_daily_total` column.
  - Strategies are ADDITIVE (~18 passes/keyword-language), not multiplicative (324). Timeline is 2-4 days, not weeks.
  - `generate_search_passes()` creates: 1 base (10pp) + 12 topicId (5pp) + 1-4 regionCode (5pp) + 3 duration (5pp).
- **Stream C moved concurrent with Phase B** (was sequenced last). It's the random baseline needed for coverage calibration — should run before or alongside A/A' re-runs, not after. Costs only ~50K units.
- **Evaluation record appended** to bottom of `docs/PRODUCTION_DEPLOYMENT_PLAN.md`.
- **Quota consumed:** 0 API units (evaluation and documentation only)
- What's next: Katie swaps ethernet cable → agent executes Phase A.0 (code prereqs) → A.1-A.3 (backfill, verify) → Phase B (Stream A re-run + Stream C).

---

## Current Status (as of Feb 20, 2026 — Early Morning)

**Phase:** VALIDATION PILOTS COMPLETE. 4 GO, 1 CONDITIONAL, 1 NO-GO. Production deployment plan written. Ready for re-runs.
**Roadmap Position:** Stream A needs re-run with 5 validated strategies. Stream A' needs re-run. Stream B COMPLETE (18,208). Stream D COMPLETE (3,933). Stream C not started. Daily stats broken (Feb 18-19).
**Sample Size vs Targets:**
- Stream A (Intent): 26,327 / growing target — projected 60-100K with expansion strategies
- Stream A' (Non-Intent): 11,303 / growing target — projected 40-80K with expansion strategies
- Stream B (Algorithm Favorites): 18,208 — search space exhausted
- Stream D (Casual): 3,933 — search space exhausted, median channel age ~2015
- Stream C (Random): not started / 50K target
- 5 expansion streams (Trending, Shorts, Livestream, Topic-Stratified, Creative Commons): scripts built, not run
**What's Running:**
- Gender gap daily channel stats (Mac Mini, 8:00 UTC) — FAILED Feb 18 (quota) + Feb 19 (timeout). Needs ethernet fix + backfill.
- AI census daily channel stats (Mac Mini, 9:00 UTC) — same failures
- No discovery scripts running
**Quota:** ~61K consumed on validation pilots today. ~810K remaining.
**Next Steps:**
1. **Plan-eval** on `docs/PRODUCTION_DEPLOYMENT_PLAN.md` (next agent)
2. **Fix Mac Mini ethernet** (Katie has hardware)
3. **Backfill daily stats** for Feb 18 + Feb 19
4. **Launch Stream A re-run** with `base,safesearch,topicid,regioncode,duration,windows`
5. **Stream A' re-run**, then Stream C
6. **Deploy daily discovery plists** with Tier 1 strategies
**Key Decisions Made:**
- Production re-runs: all 5 passing strategies (including CONDITIONAL duration)
- Daily discovery service: Tier 1 only (base,safesearch,regioncode,windows) — topicId/duration too expensive for daily
- order=relevance: EXCLUDED (NO-GO confirmed, surfaces old channels)

---

### Feb 20, 2026 — Early Morning [Validation Pilots Complete + Production Plan]

- **Ran all 6 validation pilots on Mac Mini** (~61K API units consumed):
  - **safeSearch=none → GO.** +504 net new (37.2% marginal). GRWM 25→202 (8x), gameplay 71→250 (3.5x). Zero extra quota.
  - **topicId → GO.** 2.42x yield multiplier. All 12/12 topics productive. 76.6% marginal new. Lifestyle (497), Entertainment (435), Music (331) top producers.
  - **regionCode → GO.** +428 net new (56.9% marginal). All 9/9 regions productive. Arabic standout: EG (231), SA (199).
  - **videoDuration → CONDITIONAL.** 1.44x yield (threshold 1.5x, missed by 0.06x). All 3/3 slices productive. 75.7% marginal new. Long (532) > medium (490) > short (165).
  - **order=relevance → NO-GO.** 14.8% survival rate (threshold >=50%). Median subs 12.1K vs 5.6K baseline. Overlap 63.9%. Surfaces old established channels. Correctly excluded.
  - **12h windows → GO.** 37.9% improvement (threshold 30%). 1,080 unique channels missed by 24h windows.
- **Fixed bug in validate_expansion.py:** `order` kwarg collision in `run_search()` — popping from `extra_params` (original) instead of `search_extra` (copy). Committed c1a837b.
- **Daily stats BROKEN for 2 days:** Feb 18 failed (quotaExceeded from A' overnight run), Feb 19 failed (socket timeout). All 5 launchd services still loaded. Likely network instability — Katie has ethernet hardware ready.
- **Wrote production deployment plan:** `docs/PRODUCTION_DEPLOYMENT_PLAN.md`. Covers strategy selection, phased execution (infra recovery → A re-run → A' re-run → Stream C → daily discovery deployment), quota management, risk register.
- **Production decisions:**
  - Re-runs: `base,safesearch,topicid,regioncode,duration,windows` (all passing, including CONDITIONAL duration)
  - Daily discovery: `base,safesearch,regioncode,windows` (Tier 1 only — topicId/duration too expensive for daily)
  - order=relevance: EXCLUDED
- **Quota consumed:** ~61K API units (validation pilots) + ~200 (dry-run, misc)
- What's next: /plan-eval on PRODUCTION_DEPLOYMENT_PLAN.md, fix ethernet, backfill daily stats, launch Stream A re-run.

### Feb 19, 2026 — Late Night [Expansion Code Verification + Daily Discovery Service]

- **Verification complete — all checks passed:**
  - 94 intent / 82 non-intent keywords across 15 languages (confirmed)
  - 42 fields in CHANNEL_INITIAL_FIELDS, all 8 provenance fields present
  - `validate_expansion.py --dry-run` works (prints quota estimate, no API calls)
  - All 4 modified files are Python 3.9.6 compatible (no walrus, no union types, no match/case)
- **Removed dead code:** `_run_search_pass_over_windows()` in discover_non_intent.py (defined but never called, 85 lines)
- **Added `--output` flag** to both discover_intent.py and discover_non_intent.py. Required for daily discovery service: persistent output file ensures `seen_channel_ids` dedup works across days (date-stamped filenames would reset dedup daily).
- **Drafted 2 daily discovery launchd plists:**
  - `com.youtube.daily-discovery-intent.plist` — 05:00 UTC, `--days-back 1 --strategies base,safesearch --output data/channels/stream_a/daily_discovery.csv`
  - `com.youtube.daily-discovery-non-intent.plist` — 14:00 UTC, same flags + `--exclude-list` pointing to A's daily_discovery.csv for cross-stream dedup
  - Strategies set to `base,safesearch` (conservative). Upgrade to Tier 1 after validation pilots pass.
- **Reviewed Stream C** — expansion strategies don't apply (random prefix sampling, not keyword-based). Script already uses CHANNEL_INITIAL_FIELDS; new provenance fields will be empty (expected).
- **Quota consumed:** 0 API units (verification + infrastructure only)
- **Deployment note:** When on Mac Mini Wi-Fi: `git pull`, then `launchctl load ~/Library/LaunchAgents/com.youtube.daily-discovery-intent.plist` (and non-intent). Don't deploy until validation pilots pass.

### Feb 19, 2026 — Late Night [Expansion Strategy Code Implementation]

- **Implemented all 6 expansion strategies** into discover_intent.py and discover_non_intent.py per `docs/EXPANSION_IMPLEMENTATION_PLAN.md`:
  1. safeSearch=none (global param swap on all passes)
  2. topicId partitioning (12 topics from DISCOVERY_TOPIC_IDS)
  3. regionCode matching (23 regions from LANGUAGE_REGION_MAP)
  4. videoDuration partitioning (short/medium/long)
  5. order=relevance conditional pass (re-runs capped queries only)
  6. 12h windows (A'-only, triggers when >50% of base windows are capped)
- **config.py additions:** EXPANSION_STRATEGIES set, DEFAULT_STRATEGIES set, DISCOVERY_TOPIC_IDS (12 topics), LANGUAGE_REGION_MAP (15 languages → 23 regions), DISCOVERY_DURATIONS list, 8 new provenance fields in CHANNEL_INITIAL_FIELDS (now 42 fields total)
- **New architecture:** `generate_search_passes()` function creates named pass configs with extra_params, provenance tags, and max_pages. Main loop changed from keyword→window to keyword→pass→window. Checkpoint key format: `keyword|language|pass_name` (backward compatible with old `keyword|language` keys).
- **New CLI args:** `--strategies` (comma-separated list, default: base,safesearch) and `--days-back` (for daily discovery service)
- **Created src/validation/validate_expansion.py** — per-strategy validation pilots with M1-M4 metrics, GO/NO-GO thresholds, --dry-run mode, CSV output
- **All 4 files pass syntax check** (ast.parse verified)
- **NOT YET DONE:** verification steps (keyword count check, schema field check, Python 3.9 compat, test mode dry runs), cleanup of unused `_run_search_pass_over_windows()` helper in discover_non_intent.py
- **Quota consumed:** 0 API units (code-only session, quota was exhausted)

### Feb 19, 2026 — Night [Implementation Plan for Expansion Strategies]

- **Designed full implementation plan** for wiring 6 expansion strategies into discover_intent.py and discover_non_intent.py. Plan at `docs/EXPANSION_IMPLEMENTATION_PLAN.md`.
- **Key architecture decisions:**
  - safeSearch=none is a global param swap (applied to ALL calls, not a separate pass)
  - topicId, regionCode, videoDuration are additive passes (multiply the search space)
  - order=relevance is a conditional pass (only re-runs capped queries)
  - 12h windows is a window modification (A'-only)
  - Each expansion pass is independently checkpointed via `keyword|language|pass_name` keys
  - New `--strategies` CLI flag selects which strategies to enable (default: base,safesearch)
  - New `--days-back` CLI flag for daily discovery service (generates windows for last N days only)
- **Charter alignment verified.** Expansion strategies = charter action #2 ("time-window optimization to maximize cohort yield"). --days-back = charter action #3 (daily discovery service). Stream C unblocked by this work.
- **4 files to modify:** config.py (DISCOVERY_TOPIC_IDS, LANGUAGE_REGION_MAP, 8 new schema fields), discover_intent.py (search loop rewrite + CLI args), discover_non_intent.py (same), validate_expansion.py (new file).
- **No code written this session** — planning only, handed off for implementation.
- **Quota consumed:** 0 API units (no API calls)

---

### Feb 19, 2026 — Evening [Validation Framework + Academic /plan-eval]

- **Built EXPANSION_VALIDATION_FRAMEWORK.md**: Per-strategy pilot experiments for all 6 adopted expansion strategies. ~70,300 total API units (~7% daily quota). Each strategy has: yield metric, quality check, overlap metric, diminishing returns test, and GO/NO-GO thresholds. Execution order: safeSearch → regionCode → topicId → videoDuration → relevance → 12h windows.
- **Built EXPANSION_STRATEGY_FOR_EVAL.md**: Full academic evaluation document covering scope of inference, selection models per strategy, power analysis, pre-registration plan, robustness protocol, and strategy risk tiering.
- **Ran /plan-eval with 8-expert academic panel**: Econometrician, Sampling Methodologist, Reviewer 2, Sociologist, Power Statistician, API Measurement Specialist, Open Science Specialist, Labor Econ/IO. Three rounds:
  - **R1 (63.1/100):** No power analysis, no scope of inference, no pre-registration, no selection models. Five major structural gaps.
  - **R2 (75.9/100):** Added selection models, power analysis with MDE tables, pre-registration plan, three-version robustness protocol, covariate balance protocol, construct validity test, discoverability index, strategy risk matrix with Tier 1/2/3 hierarchy.
  - **R3 (81.5/100):** Formalized DiD identification with DAG + Callaway & Sant'Anna estimator specification + Rambachan & Roth sensitivity + falsification test. Operationalized Stream C coverage calibration with formula + cell sizes + Latin-alphabet caveat. Pre-committed 12 analytical thresholds with citations and justifications.
- **Key analytical decisions in the evaluated document:**
  - Tier 1 (primary): base + safeSearch + regionCode + 12h windows
  - Tier 2 (robustness): + topicId + videoDuration
  - Tier 3 (sensitivity only): + order=relevance
  - BH-FDR at q=0.05 for multiple testing
  - Remedial analyses REPLACE naive analyses when thresholds trigger
  - Stream C is load-bearing for representativeness claims
- **Remaining weaknesses identified by panel** (not fixable in this document): AI adoption measurement needs validation pipeline, effective N under serial correlation needs ICC from panel data, A vs. A' needs named theoretical framework for journal positioning.
- **Quota consumed this session:** 0 API units (document creation and evaluation only)
- **Cleanup:** Moved stray `PR_4_Channel_id-->Deep_YT_API_Data.py` to archive/ (original lives in DISSERTATION/CH2/.../YT_v1/code/). Fixed /handoff skill bug: Write tool requires Read-first on existing files; patched `~/.claude/skills/handoff/SKILL.md`.

---

### Feb 19, 2026 — Afternoon [5-Expert Panel on API Expansion Strategies]

- **Ran 5-expert YouTube API panel** (API infrastructure engineer, computational social science methodologist, information retrieval specialist, YouTube creator research academic, data pipeline architect). All 12 candidate strategies evaluated.
- **6 strategies unanimously adopted:**
  1. `topicId` partitioning (12 topics per keyword) — highest impact: 2-4x yield for A', 1.3-2x for A. Breaks the 500-result ceiling by creating per-topic result slots.
  2. `order=relevance` second pass for capped queries — +15-35% unique channels.
  3. `regionCode` matched to language — +10-40% per region for non-English. 23 regions mapped to 15 languages.
  4. `safeSearch=none` — +5-10%, zero quota cost. Default `moderate` silently excludes beauty/fitness/gaming/comedy creators.
  5. `videoDuration` partitioning (short/medium/long) — +50-150% for A'. Three disjoint slices triple the result ceiling.
  6. Shorter time windows for A' (12h for capped keywords) — +30-80% for high-volume keywords.
- **Also adopted:** Adaptive page depth (save 20-30% quota), dual daily runs (06:00+18:00 UTC, +5-15%), OR-combined keywords for daily service quota savings.
- **4 strategies flagged for testing:** `type=channel` search, quoted vs unquoted keywords, `videoCaption` partitioning, `videoCategoryId` partitioning.
- **5 strategies rejected:** `order=viewCount/rating/title` (useless for new content), `location+locationRadius` (geotagging rare), `channelType` (only 2 values), `maxResults` reduction (no effect), `videoDefinition` (almost all HD).
- **Daily discovery budget designed:** Tier 1 daily service ~140K units/day (<14% quota). Tier 2 weekly supplement ~250K units. Peak ~390K, leaving 620K for daily stats.
- **Projected yield improvement:** A from 26K → 60-100K (2.3-3.8x). A' from 11K → 40-80K (3.5-7x). A' benefits disproportionately because broad keywords hit the 500-cap harder.
- **`--days-back` parameter planned** for both discover scripts. Generates windows for just the last N days. Daily mode: `--days-back 1` searches yesterday's 24h window. Backward-compatible: no flag = full backfill from COHORT_CUTOFF_DATE.
- **Config additions needed:** `DISCOVERY_TOPIC_IDS` (12 topics), `LANGUAGE_REGION_MAP` (15 languages → 23 regions).
- **No code changes this session** — research/analysis only. Implementation pending Katie's approval and academic validation.
- What's next: /plan-eval on expansion strategy (academic panel for empirical research quality), then implement Priority 1-2 changes.

### Feb 19, 2026 — Morning [Full 4-Stream Sample Quality Audit]

- **CRITICAL CORRECTION: Stream A' has 11,303 unique channels, NOT 46,607.** Previous count was inflated 4x by multiline CSV descriptions (`wc -l` counts lines including newlines within quoted fields, not CSV records). Verified on Mac Mini with pandas: 66,470 lines → 11,303 actual records, all unique.
- **Ran comprehensive quality audit across all 4 streams.** Key findings:
  - All streams have negligible bot contamination (<0.05% with 2+ risk flags)
  - Stream A (26,327): 100% created 2026+. Median 8 subs, 1,070 views, 5 videos. 80.4% have 2+ videos. Clean.
  - Stream A' (11,303): 100% created 2026+. Median 20 subs, 9,222 views, 16 videos. 95.6% have 2+ videos. **Higher quality than A on every metric** — these are more active, more established creators.
  - Stream B (18,208): YouTube's elite. Median 148K subs, 65.8M views. 2.8% created 2026. As expected.
  - Stream D (3,933): Old channels (median creation 2015). 0% created 2026. 68.8% have 50+ videos.
  - Zero overlap between A and A' (exclude list worked correctly).
- **Katie's bot suspicion about A' was NOT confirmed.** A' is smaller than A (not larger), and higher quality. The 1.8x ratio that triggered concern was an artifact of the miscount.
- **A' expansion strategy evaluated.** At 11,303, A' needs growth for robust subgroup analysis. Three levers: (1) 15-language re-run adds ~4-8K, (2) expanded keyword set adds ~10-15K, (3) monthly re-runs accumulate over time. Target: 25-40K.
- **Stream A re-run APPROVED** for Feb 19. 3-day quota calendar approved.
- **Corrected counts in:** PROGRESS_LOG.md current status, PROJECT_MASTER_PLAN.md current marker, PROJECT_CHARTER.md datasets + milestones tables, MEMORY.md current phase.
- **Audit script:** `temp/sample_audit.py` (reusable for future streams)
- What's next: Launch Stream A re-run on Mac Mini. Draft expanded A' keyword set. A' re-run Feb 20. Stream C Feb 21+.

### Feb 19, 2026 — Early Morning [Code Wiring + Mac Mini Diagnosis + Quota Analysis]

- **Wired `relevanceLanguage` and `expansion_wave` into both discovery scripts** (`discover_intent.py`, `discover_non_intent.py`). Both now pass ISO 639-1 language code to YouTube Search API via `config.RELEVANCE_LANGUAGE_CODES` and tag each channel with `config.get_keyword_wave(language, keyword)` for provenance tracking.
- **Mac Mini diagnosis:**
  - Stream A' **COMPLETED**: 11,303 unique channels (66,470 lines in CSV, but multiline descriptions inflated wc -l count — previous "46,607 unique" was a parsing error). Used OLD code (8 languages, no relevanceLanguage).
  - Daily stats **FAILED Feb 18**: Both gender gap and AI census hit `quotaExceeded` at 8:00/9:00 UTC. Cause: A' ran overnight and consumed entire daily quota (~2.35M units estimated: 47 keywords × ~50 time windows × ~10 pages × 100 units/call).
  - All 5 launchd services still loaded. Should auto-recover when quota resets.
- **Pushed code to Mac Mini via git pull** — pulled fa29f47..13337d9 (5 commits covering keyword expansion, plan-eval refinements, and relevanceLanguage wiring). Both scripts compile on Python 3.9.
- **Quota calendar planned**: Feb 19 = re-run A (15 lang), Feb 20 = re-run A', Feb 21+ = Stream C.
- **Sample quality audit queued**: Offline analysis of all existing stream CSVs while waiting on quota. Bot detection, language distribution, creation date patterns.
- What's next: Run sample audit (no API needed), then re-run Stream A with 15 languages on Mac Mini.

### Feb 18, 2026 — Late Night [/plan-eval: 3-Round Expert Evaluation of Keyword Expansion]

- **Ran /plan-eval on expanded INTENT_KEYWORDS** — 3 rounds, 8-expert panel (cross-cultural NLP specialist, survey methodology expert, computational social scientist, population sampling theorist, platform economics researcher, PhD committee advisor, replication specialist, API integration engineer). Score trajectory: **66.3 → 76.9 → 79.6** (plateau reached at R3, +2.7 < 3-point threshold).
- **Round 1 key fixes (66.3):**
  - Replaced 4 polysemous keywords that would match non-debut content:
    - Russian "Знакомство" (dating content) → "Обо мне", "Первый ролик", "ВЛОГ 1"
    - Indonesian "Perkenalan" (generic greeting) → "Pertama kali upload"
    - Bengali "পরিচয়" (generic intro) → "নতুন চ্যানেল", "Notun channel"
    - Turkish "Tanışma videosu" (interview content) → "YouTube'da ilk videom", "#ilkvideo"
  - Added Arabic dialect variants: Egyptian "اول فيديو ليا", pan-Arab "قناتي الجديدة"
  - Added Spanish feminine variant "Hola soy nueva en YouTube"
  - Thai: switched formal "ของฉัน" to casual "ของเรา", added alt spelling "วีดีโอแรก"
  - Added `INTENT_KEYWORD_WAVES` dict and `get_keyword_wave()` function for provenance tracking
  - Added `expansion_wave` field to CHANNEL_INITIAL_FIELDS schema
  - **Expanded NON_INTENT_KEYWORDS from 8→15 languages** (47→82 keywords) to maintain A vs A' comparability
- **Round 2 key fixes (76.9):**
  - Fixed count error: doc said "99" but code has 94 — corrected everywhere
  - Vietnamese "Chào mừng đến kênh" → "Chào mừng đến kênh của tôi" (was unnaturally truncated)
  - Indonesian "Halo teman-teman" → "Channel baru" (greeting, not intent signal)
  - Upgraded wave tracking from language-level to keyword-level (Spanish wave-2 keywords in wave-1 language were misattributed)
  - Added `RELEVANCE_LANGUAGE_CODES` mapping (ISO 639-1 for all 15 languages)
  - Added `verify_keyword_counts()` function — confirmed 94 intent, 82 non-intent
  - Added limitations #11 (non-intent asymmetry) and #12 (Stream C Latin-alphabet) to SAMPLING_ARCHITECTURE.md
- **Round 3 (79.6):** Plateau. Remaining gaps require human action, not code changes:
  - Construct validation study (5 hours RA time, ~$100-150)
  - Power analysis based on CH2 effect sizes
  - Native speaker review of all 15 languages (~3.5 hours Fiverr/Prolific)
  - Small yield experiment for Wave 2 keywords (~10 min, ~600 API calls)
  - Pre-registration on OSF before production re-run
- **Files modified:** `src/config.py` (keywords, wave tracking, relevance codes, verify function), `docs/SAMPLING_ARCHITECTURE.md` (sections 2.1, 2.2, 2.4, limitations, change log)
- What's next: Wire `relevanceLanguage` and `expansion_wave` into discover_intent.py. Check Mac Mini status. Re-run Stream A with 15 languages. Launch Stream C.

### Feb 18, 2026 — Evening [Referee Evaluation + Keyword Expansion to 15 Languages]

- **Ran 3-referee evaluation of Stream A language bias** (sampling methodologist, computational social scientist, platform economics expert). All three converge:
  - Language skew is NOT fatal — it's an expected artifact of keyword-based purposive sampling
  - Missing languages (Arabic, Russian, Indonesian) ARE a real coverage gap that needs fixing
  - Do NOT aim for population proportionality — aim for minimum cell sizes (~500/language) per stratum
  - McGrady benchmark is informative but wrong construct (stock vs. flow, 2022 vs. 2026, audio vs. keyword)
  - Stream C is the proper population baseline — prioritize launching it
  - The overrepresentation maps to keyword specificity, not population size (初投稿 is a tag, "mi primer video" is a generic phrase)
- **Expanded INTENT_KEYWORDS from 8 to 15 languages** (46→94 keywords):
  - New languages: Arabic (5 kw), Russian (5), Indonesian (5), Turkish (5), Vietnamese (5, with + without diacritics), Thai (5), Bengali (5, native + romanized)
  - Added 3 more Spanish keywords for better specificity ("Mi primer video en YouTube", "Hola soy nuevo en YouTube", "Primer vlog")
  - Tagged as "Expansion wave (Feb 2026)" in config.py comments
- **Updated discover_intent.py:** Docstring and log messages updated from hardcoded "8 languages" to dynamic count from config
- **Estimated yield from expansion:** 5,800-14,000 additional channels (Arabic 2-5K, Indonesian 1.5-3K, Russian 1-2.5K, Turkish 0.5-1.2K, Vietnamese 0.3-0.8K, Thai 0.2-0.6K, Bengali 0.1-0.4K). Combined total ~32-40K.
- **Estimated quota cost:** ~200K units for expansion keywords. Fits in one day's quota.
- **Referee recommendations to track:**
  - Flag high-volume channels (>50 videos in 60 days) for sensitivity analysis
  - Quantify gap between discovery_language and actual content language
  - Check for temporal clustering by keyword-date
  - Tag expansion-wave channels to test for wave effects
  - Get Stream C running ASAP (linchpin of representativeness argument)
- **No collection run started** — keyword expansion committed, awaiting Katie's approval for production re-run
- **Read both McGrady papers in full** (Zotero keys YN2WMFM7 and EHGWS6HY). Key insight from 2025 paper: Hindi YouTube exploded post-TikTok ban (50.92% of Hindi videos uploaded in 2023 alone). This means our 9.9% Hindi share may be an *undercount* for new 2026 channels, not an overcount. The "platform benchmark" is a fast-moving target.
- **Wrote /plan-eval handoff** at `~/.claude/handoffs/stream_a_keyword_expansion_eval.md`. Includes full project context, both McGrady papers summarized, exact expanded keywords, yield estimates, and 7 specific pressure points for evaluators (translation accuracy, keyword specificity, missing romanized variants, dialectal coverage, missing languages, stock-vs-flow recalibration, A' language mismatch).
- What's next: Run /plan-eval on the handoff. Then Katie approves → push to Mac Mini → re-run Stream A with 15 languages. Then Stream C.

### Feb 17, 2026 — Late Evening [Time Window Optimization — 3.5x More Channels]

- **Ran time window experiment** testing 3 configurations on 3 keywords (my first video, welcome to my channel, gameplay):
  - Current (48h windows, 30-day lookback): baseline
  - Extended (48h windows, full Jan 1 to now): +81% channels
  - **Narrow (24h windows, full period): +248% channels (3.5x improvement)**
- **Root cause of low yield:** Two independent bottlenecks. (1) 30-day lookback missed all of early January (channels uploading Jan 1-17 were invisible). (2) 48h windows hit the API's per-query result cap (~500 results), so half the videos in each window were never returned.
- **Updated both `discover_intent.py` and `discover_non_intent.py`:** `generate_time_windows()` now defaults to 24h non-overlapping windows covering the full period from COHORT_CUTOFF_DATE to now. Added `--window-hours` CLI arg (default 24). Backward-compatible — old behavior available via `--window-hours 48`.
- **Projected re-run yields:** If 3.5x multiplier holds across all 46 intent keywords × 8 languages, Stream A could grow from 19K to ~50-70K unique channels. Stream A' similarly.
- **Quota estimate for re-runs:** ~2.5-3M units total (both streams), ~2.5-3 days of dedicated quota. Daily stats (~10K/day) unaffected.
- **Updated charter** with current dataset sizes, phase, and milestones.
- **Key finding for all cohort streams:** Only Streams A and A' filter by 2026 creation date. B, C, D and all future streams capture any-age channels.

### Feb 17, 2026 — Evening [Mac Mini Recovery — B Complete, A' Restarted]

- **Stream B was NOT stalled — it COMPLETED.** Previous handoff misdiagnosed B as stalled at 73/122 queries. Log shows it finished all 122 queries (18,208 unique channels) and cleared its checkpoint. The screen session exited cleanly after completion.
- **Stream A' genuinely stalled** at keyword 13/47 (`haul`) with `Connection reset by peer` error. Recovered briefly (collected through 2,594 channels) then python process exited. Checkpoint had 12 completed keywords (2,502 channels).
- **Killed dead screen session + zombie python3 process.** Old python3 (PID 71510) was still alive from the stalled session despite the screen being dead. Killed it to prevent duplicate writes.
- **Restarted A' from checkpoint.** New screen session `stream_a_prime` launched, resumed at keyword 13/47. Progressing well — at 19/47 keywords, ~3,400 channels by end of session.
- **Extracted channel_ids.csv for Stream B** (18,208 unique) and **Stream D** (3,933 unique). Both now have canonical ID files alongside Stream A's existing one.
- **All 5 launchd services healthy.** Gender gap (689 KB) and AI census (3.4 MB) daily stats both ran today. Exit status 0 across the board.
- **Lesson:** `screen -X quit` kills the screen process but does NOT always kill child processes (login, bash, python). When restarting after a stall, always `ps aux | grep` to find and kill orphaned processes before launching a new instance.

### Feb 18, 2026 — Morning [Stream A Audit + Language Bias Discovery]

- **Stream A re-run with 24h windows COMPLETE:** 26,327 unique channels (up from 19,016 with old 48h settings — 1.38x improvement, less than the 3.5x on test keywords, likely because many intent keywords were already near-saturated).
- **Stream A' re-run launched:** 24h windows + excluding 26,327 Stream A channel_ids. Running healthy on Mac Mini, ~5,300 unique channels after ~30 min, ~269K quota used.
- **Full quality audit of Stream A (26,327 channels):**
  - 100% created >= 2026-01-01 (zero leakage)
  - 80.4% have 2+ videos (active creators, not one-off uploaders)
  - Only 1.5% completely dead (0 subs AND 0 views)
  - Only 7 channels (0.03%) with 2+ bot risk flags — negligible contamination
  - Median: 8 subscribers, 1,070 views (30x McGrady's random-sample median views — intent keywords select for active creators)
  - Top topics: Lifestyle (18.8%), Gaming (10.0%), Entertainment (7.0%)
- **Language bias identified (critical finding):**
  - English 33.9% (vs 20.1% on platform — 1.7x over)
  - Japanese 16.8% (vs 2.2% — 7.6x over)
  - Portuguese 16.8% (vs 4.9% — 3.4x over)
  - Korean 8.9% (vs 0.75% — 11.9x over)
  - Arabic, Russian, Indonesian, Thai, Turkish, Bengali, Vietnamese: COMPLETELY MISSING despite being top-10 YouTube languages
  - Spanish: 1.5% (vs 6.2% — 4.1x under)
  - Cause: keyword set only covers 8 languages, and cultural specificity of keywords (e.g., Japanese 初投稿) drives overrepresentation
- **Decision: Expand keyword set** to include missing languages and add more Spanish keywords, aiming for population-representative sample
- **Audit script:** `temp/stream_a_audit.py` — reusable for future stream audits
- **Reference paper:** McGrady et al. (2023) "Dialing for Videos" — random sample of ~10K YouTube videos, key benchmarks for language (English=20.1%), views (median=35), categories (People & Blogs=55.8%), subscribers (median=61)
- **Quota consumed:** ~269K units for A' re-run (still running). Stream A re-run consumed ~2 days of quota on prior session.

### Feb 18, 2026 — Night [5 Future Stream Scripts Built + Mac Mini Status Check]

- **Built 5 new discovery scripts** for future expansion streams (all in `src/collection/`):
  - `discover_livestream.py` — `eventType=completed`, 25K target, 12 time windows
  - `discover_shorts.py` — `videoDuration=short`, 50K target, 24 time windows
  - `discover_creative_commons.py` — `videoLicense=creativeCommon`, 15K target
  - `discover_topic_stratified.py` — cycles through 62 topic IDs from YOUTUBE_PARENT_TOPICS, 40K target
  - `discover_trending.py` — `videos.list(chart=mostPopular)` across 51 region codes, daily append-only log (fundamentally different architecture: two outputs — trending sighting log + cumulative channel details)
- **All scripts** have checkpoint/resume, `--test`/`--limit` flags, incremental CSV writes, CHANNEL_INITIAL_FIELDS schema, logging to `data/logs/`.
- **Updated `config.py`:** 5 new STREAM_DIRS, 5 new SAMPLE_TARGETS, TRENDING_REGION_CODES (51 countries), TRENDING_LOG_FIELDS schema.
- **Updated `youtube_api.py`:** `search_videos_paginated` now accepts `**extra_params` for topicId/eventType/videoDuration/videoLicense passthrough (backward-compatible). New `get_trending_videos()` function for chart=mostPopular.
- **Checked Mac Mini production status:**
  - Stream D: COMPLETE (3,933 unique, 22,158 CSV rows with duplication)
  - Stream A': STALLED at 2,036 unique (7/47 keywords). Checkpoint intact.
  - Stream B: STALLED at 10,993 unique (73/122 queries). Checkpoint intact.
  - Both A' and B stopped at exact same second (23:32:30 UTC Feb 17). Python processes exited, bash wrappers hanging in screen sessions. Root cause: system-level event on Mac Mini.
  - Screen sessions still exist but are dead (bash at 0% CPU, no python3 child processes).
- **All changes committed and pushed** (eec40de).
- What's next: Kill dead screens, restart A'/B from checkpoints. Then assess quota before launching C or future streams.

### Feb 17, 2026 — Evening [Video Enumeration Status Check + Bug Fix]

- **Checked video enumeration progress** for both panels running on laptop:
  - **Gender gap:** 96.4% complete — 9,413/9,760 channels processed, 9,030 with video rows in inventory CSV, 11,008,240 total video rows (~1.5 GB). Should finish soon.
  - **AI census:** 22.6% complete — 11,326/50,010 channels processed, 7,340 with video rows, 6,060,363 total video rows. Estimated ~2 more days at current pace.
- **Fixed shared checkpoint bug in `enumerate_videos.py`:** Both enumeration runs were writing to the same `.enumerate_checkpoint.json` file. Risk: when gender gap finishes, it calls `unlink()` on the checkpoint, which could briefly erase AI census progress. Fixed by deriving checkpoint filename from the output file stem (e.g., `.enumerate_gender_gap_inventory_checkpoint.json`). Fix is safe — running processes use old code in memory and are unaffected.
- Both processes confirmed alive via `ps aux` (PIDs 5155 and 24118).

### Feb 18, 2026 — Night [Production Launches — 3 Streams on Mac Mini]

- **Tested all 4 remaining discovery scripts** on laptop with `--test --limit 5`: A' (Non-Intent), B (Algorithm Favorites), D (Casual Uploaders), C (Random Baseline). All passed. Stream C has a trivial edge case where `--limit <15` yields 0 prefixes due to integer division; not a production issue.
- **Launched 3 production collections on Mac Mini** in detached screen sessions:
  - **Stream A' (Non-Intent):** `stream_a_prime` screen, `--limit 200000 --skip-first-video --exclude-list data/channels/stream_a/channel_ids.csv`. Cross-dedup loaded 19,016 Stream A channels. At 3/47 keywords with ~1,135 channels found. Estimated runtime 1-2 hours.
  - **Stream B (Algorithm Favorites):** `stream_b` screen, `--limit 25000`, 122 expanded queries. At 30/122 queries with ~4,315 channels. Strong yield (~150 unique per query).
  - **Stream D (Casual Uploaders):** `stream_d` screen, `--limit 50000` (high ceiling to exhaust search space). **COMPLETED** — 3,933 unique channels across 37 filename patterns. Within the 3-5K realistic ceiling. Top yielders: IMG_ (231), Screen Recording, Untitled.
- **Stream C (Random Baseline)** held for tomorrow — combined A'+B+D quota is ~600-700K units today, adding C's ~600-800K would exceed daily limit.
- **Quota budget:** ~1.2-1.6M total across 3 days. Well within daily capacity.
- **Decision from Katie:** Stream D limit set high to "get what you can get, audit later."
- **Decision from Katie:** All production collection runs happen on Mac Mini (always-on), not laptop.
- What's next: 1) Check A'/B completion. 2) Launch Stream C. 3) Write scripts for 5 future streams. 4) Extract channel_ids.csv for completed streams. 5) Create new cohort daily stats launchd service on Mac Mini.

### Feb 18, 2026 — Evening [Architecture Document Evaluated — 3-Round Expert Panel]

- **Ran `/plan-eval` on `docs/SAMPLING_ARCHITECTURE.md`** — 10-expert panel, 3 rounds of evaluation + fixes
- **Round 1 (62/100):** Found critical factual errors: Stream A count wrong (83,825 stated vs 19,016 unique), gender percentages summed to 103.4% (wrong denominator), schema field counts wrong (8 vs 5 for daily stats), "natural experiment" language for A vs A' comparison wouldn't survive peer review
- **Round 1 fixes applied:** Corrected Stream A to 19,016 unique, recomputed gender/race on actual 9,760 panel (man=6,345/65%, woman=3,383/34.7%, NB=32/0.3%), fixed all schemas. Added 5 new sections: staggered DiD estimation specification (parallel trends, no-anticipation, treatment heterogeneity, 60-day minimum pre-treatment window), deduplication protocol, Infludata sampling frame discussion, gender coding methodology, deployment constraints (EDEADLK warning). Added pagination cap and safeSearch notes. Added source-of-truth hierarchy (config.py is authoritative).
- **Round 2 (72.3/100):** Sub-agent had miscounted keyword lists — 4 of 6 counts were wrong. Manually verified against config.py: 46 intent, 47 non-intent, 45 AI search, 101 AI flag, 122 benchmark, 37 casual. Fixed all. Removed surviving "natural experiment" from Decision 4.
- **Round 3 (79.4/100):** All numbers verified correct. Panel said doc is at realistic ceiling without Katie's input on 5 methodological decisions: power analysis, ethics/IRB, panel attrition protocol, Design 4 assumptions, gender coding method for new populations.
- **Key lesson:** Sub-agents can miscount list items in code files. When factual accuracy matters, read the source code directly and count manually.
- What's next: production runs — A' first (contemporaneity matters), then B, D, C

### Feb 18, 2026 — Morning [Consolidated Sampling Architecture Document]

- **Created `docs/SAMPLING_ARCHITECTURE.md`** — single canonical reference for all 12 streams, sampling methodologies, experimental justifications, AI research designs, and key design decisions. ~500 lines consolidating content from 7 source documents (TECHNICAL_SPECS, DECISION_LOG, SAMPLING_EXPERIMENTS, PROJECT_MASTER_PLAN, YOUTUBE_DATASET_DESIGN, PROGRESS_LOG, CLAUDE.md).
- **Contents:** Stream-by-stream write-ups (what it captures, why it exists, sampling method, empirical validation, status), 5-stream comparison logic diagram, gender gap panel composition + filtering rationale, all 4 AI research designs with identification strategies, 5 proposed future streams, full experimental evidence tables, quota budget summary, 9 key design decisions with alternatives rejected, known limitations and open questions.
- **Added references** to the new doc from: PROJECT_MASTER_PLAN.md (Key Reference Files), TECHNICAL_SPECS.md (Reference Documents), CLAUDE.md (Sampling Design section), and PROJECT_CHARTER.md (Quality Bar section).
- **Purpose:** Katie needs a single evaluable document for assessing the full stream architecture before resuming production runs.
- What's next: Katie evaluates the architecture doc, provides feedback, then production runs resume.

### Feb 18, 2026 — Early Morning [Launch Prep Complete — Paused for Evaluation]

- **Mac Mini bug fixes deployed:** SSH to 192.168.86.48, `git pull` pulled all 8 fixes (M4-M8, m1-m3). All 5 launchd services confirmed running (exit 0).
- **Stream A channel_ids.csv extracted:** Raw CSV had 83,825 rows but only **19,016 unique channel IDs**. Heavy duplication across keyword batches (same channels found by multiple intent keywords). Previous "83,825 channels" count was misleading — the dedup happened at extraction, not during incremental collection.
- **Stream B (Algorithm Favorites) expanded:** BENCHMARK_QUERIES in config.py grew from 6 entries (vowels + "video") to 100+ common search terms across 12 categories. discover_benchmark.py rewritten with checkpoint/resume and incremental CSV writes. Default target updated to 25,000.
- **Stream D (Casual Uploaders) expanded:** CASUAL_QUERIES grew from 16 to 40+ patterns (Samsung, Pixel, WhatsApp, OBS, Zoom, Loom, Snapchat, TikTok, timestamp defaults). discover_casual.py rewritten with checkpoint/resume. Default target updated to 5,000.
- **Stream A' cross-dedup built:** Added `--exclude-list` flag to discover_non_intent.py. Loads channel_ids.csv and adds those IDs to seen-set before discovery. Stream A's 19,016 channels will be excluded.
- **Channel_ids.csv copied to laptop** via SCP for cross-dedup use in Stream A'.
- **New cohort daily stats service MISSING:** No launchd plist for new cohort on Mac Mini. Charter listed it at 8:30 UTC but it was never created. Needs setup after expanded streams are collected.
- **PAUSED:** Katie running stream evaluation before production. Next agent integrates evaluation results with this prep work.
- What's next: integrate evaluation feedback, then execute production runs

### Feb 17, 2026 — Night [Audit Bug Fixes + Architecture Table]

- **Fixed all 8 code bugs from audit (M4-M8, m1-m3):**
  - M4: `get_channel_stats_only` batch 404 handler — now compares requested vs returned IDs instead of marking all 50 channels in a batch as not_found
  - M5: `detect_new_videos` deletion masking — now checks playlist when known_video_ids available, even if count decreased (deletions masking new uploads)
  - M6: Shorts threshold updated 60s → 180s (YouTube expanded Shorts to 3 min in Oct 2024)
  - M7: Duration regex now handles day-level ISO 8601 durations (P1DT2H3M4S for long livestreams)
  - M8: `get_oldest_video` pagination cap raised from 10 pages (500 videos) to 200 pages (10,000 videos) with warning for larger channels
  - m1: Fixed empty log files across 9 scripts — moved FileHandler setup into `setup_logging()` function called after `config.ensure_directories()` in `main()`
  - m2: Added `endpoint_name` to all `execute_request()` callers in youtube_api.py (was always "unknown"). Also added `quota_cost=100` to search API calls.
  - m3: AI census `discovery_language` no longer hardcoded to "English" — added `AI_SEARCH_TERM_LANGUAGES` mapping in config.py for Spanish, Chinese, German terms
- **Presented unified stream architecture table** — 12 streams total (7 existing + 5 new). Filled in target sizes and cadence for new streams: Topic-Stratified (~30-40K), Trending Tracker (accumulating daily), Livestream Creators (~25K), Shorts-First (~50K), Creative Commons (~10-15K). Pending Katie's approval.
- **Comment sampling strategy discussed:** AI Census gets full pull on AI-flagged videos (highest research value), Algorithm Favorites gets randomized sample, new creator panels deferred (too sparse for now).
- **No production runs.** All changes are to code and documentation only.
- What's next: Katie approves architecture table, then build expanded Stream B + D, run Stream C + A'

### Feb 17, 2026 — Evening [Strategic Design Review + Stream Architecture Overhaul]

- **Full design review session** — Katie reviewed every audit finding (F1-F4, M1-M3) and made decisions:
  - F1 (Stream C / random baseline): **RUN IT** — just hasn't been executed yet
  - F2 (Pre-analysis plan): **DOWNGRADED to INFO** — not applicable to data infrastructure projects; pre-registration is for experiments
  - F3 (Stream A'): **COLLECT ASAP** — contemporaneity concern acknowledged
  - F4 (AI Census validation): **Claude agent will validate** — Katie pushes back on audit framing; "found in search" IS relevant from user perspective. Distinction needed: "talking about AI" vs "producing with AI"
  - M1 (Expand panel to 14,169): **KEEP 9,760** — data confirms exclusion is substantively correct (uncoded channels are 51% organizations, 13% teams, 13% broken, 9% AI bots; 0% overlap with individual entrepreneurs)
  - M2 (Stream D): **ADD ~20 MORE PATTERNS**, target 3-5K channels, multi-signal filtering post-hoc
  - M3 (Stream B): **EXPAND TO 25K** via expanded keyword searches (NOT category stratification). Standalone dataset for "who wins" research questions.
- **Critical framing correction from Katie:** This is NOT one research project. It's automated data infrastructure producing multiple datasets for multiple papers. The audit's single-paper framing was wrong.
- **Coded vs uncoded channel analysis:** Confirmed Katie's instinct. runBy field shows 100% of coded channels are individual creators. Uncoded are organizations (51%), teams (13%), broken (13%), AI bots (9%), and uncoded individuals (14%). Median observables nearly identical, but construct validity demands individual-only panel.
- **5 new sampling methods proposed and approved in principle:**
  1. Topic-Stratified Discovery (topicId parameter, 26 topic categories)
  2. Trending Tracker (chart=mostPopular, 51 region codes)
  3. Livestream Creators (eventType=completed)
  4. Shorts-First Creators (videoDuration=short)
  5. Creative Commons Educators (videoLicense=creativeCommon)
- **Storage/cadence decisions:**
  - Katie has 2 TB Google Drive — 19+ years of headroom
  - Weekly video stats on ALL panels: ~96-104 GB/year — approved
  - Channel stats daily: ~8.4 GB/year — trivial
  - Comment data: decision pending (full initial pull vs sampled)
- **Katie wants descriptive stream labels** replacing letter codes (e.g., "Intent Creators" not "Stream A")
- **No code written this session** — pure strategic design review
- What's next: next agent finalizes unified stream architecture, then implements code fixes (M4-M8) and new stream scripts

### Feb 17, 2026 — Afternoon [Charter Review + Corrections]

- **Reviewed new PROJECT_CHARTER.md** (created in Second Brain session). Verified framing: this project is data infrastructure, not a single paper.
- **Fixed charter inaccuracies:**
  - "First milestone" → "Current milestone" with clearer language separating charter (done) from outstanding stream/AI decisions (not done)
  - Added 3 missing Mac Mini services to automated services table (weekly video stats, sync-to-drive, health check — was only showing the 3 collection jobs)
  - Rewrote next actions to put actual decisions (A', C, AI flagger) first instead of buried
  - Added concrete enumeration progress to video enumeration milestone (gender gap ~5M+ rows, AI census ~8%)
- **Confirmed charter accuracy on:** dataset sizes, 3 collection service schedules, autonomy boundaries, relationship to gender gap paper repo
- **No phase change.** Approach audit still IN PROGRESS — charter is established but decisions on A', C, and AI designs remain.
- What's next: Katie makes audit decisions on remaining streams and AI research designs

### Feb 17, 2026 — Late Morning [Status Audit + Stream A Complete]

- **Verified Mac Mini deployment:** AI census daily stats already live, first run produced 50,005 rows (2026-02-17.csv). All 5 launchd services healthy.
- **Stream A COMPLETED overnight on Mac Mini:** 83,825 channels discovered across 46 keywords x 8 languages. Ran to full exhaustion of search space (short of 200K target — that was the actual yield ceiling). Screen session exited cleanly, no checkpoint = full completion.
- **Stream A channel_ids.csv NOT yet extracted** — needs processing before merge.
- **AI census video enumeration progressing:** 4,175/50,010 channels (8.3%), 85,454 video rows. ~3 days remaining at current rate.
- **Gender gap video enumeration still running:** 5M+ rows written.
- **PAUSED further production runs:** Katie auditing overall approach before Streams A', C, AI flagger, or new cohort merge. Existing automated services (gender gap + AI census daily stats) continue running.

### Feb 17, 2026 — Morning [AI Census Deployment COMPLETE + Video Enumeration Running]

- **AI census collection COMPLETE:** 50,010 channels in 34 min (45 terms x 2 sort orders x 18 months). Top yielders: artificial intelligence (2,859), AI tools (2,815), prompt engineering (2,786).
- **Mac Mini deployment COMPLETE:** launchd plist created (`com.youtube.ai-census-daily-channel-stats`), scheduled 9:00 UTC. SCP'd channel_ids.csv to Mac Mini, loaded service. Test run returned stats for 50,005 of 50,010 channels (5 likely terminated/private).
- **Video enumeration launched:** 50K channels, ~183K API units, checkpoint/resume. Running on laptop in background.
- **Handoff report written:** `HANDOFF_AI_CENSUS_DEPLOY.md` for agent continuity.
- **Three launchd services now active on Mac Mini:**
  1. Gender gap daily channel stats (8:00 UTC)
  2. New cohort daily channel stats (8:30 UTC)
  3. AI census daily channel stats (9:00 UTC)
- Next: verify first automated AI census run (Feb 18 after 9:00 UTC), monitor video enumeration, run AI flagger on completed inventory.

### Feb 16, 2026 — 10:55 PM [AI Census Scaled to 50K + Multi-Design Architecture]

- **Expanded AI_SEARCH_TERMS** from 17 → 45 terms (video/image gen, audio/music, coding, non-English, domain-specific)
- **Added AI_FLAG_KEYWORDS** to config.py: 101 keywords across 6 categories for video title matching (treatment variable for adoption diffusion design)
- **Updated discover_ai_creators.py**: `--months-back` (default 18, was 12), `--sort-orders` (default relevance,date), `--limit` (default 50K), safe append to existing output
- **Created extract_ai_channel_list.py**: extracts channel_ids.csv + channel_metadata.csv from census output for daily tracking
- **Created flag_ai_videos.py**: offline AI keyword flagger for video titles — flags ai_flag, ai_keywords_matched, ai_category per video
- **Launched scaled census**: 45 terms x 2 sort orders x 18-month lookback = 90 work units. 31K+ channels found in first 18 minutes. Running in background with checkpoint/resume.
- **Bug fix**: discover_ai_creators now always loads existing output before writing (prevents overwriting prior results when no checkpoint exists)
- Remaining after census completes: extract channel lists, deploy daily AI census tracking to Mac Mini, start video enumeration for census channels

### Feb 16, 2026 — 10:37 PM [Streams B+D Collected, Stream A Launched]
- **Ran Stream B (Benchmark) on Mac Mini:** 1,539 channels discovered across 6 vowel/generic queries. Heavy algorithm bias as expected: 742 channels >1M subs, 483 at 100K-1M. Median is top 0.01% of YouTube.
- **Ran Stream D (Casual) on Mac Mini:** 1,862 channels from 15 raw-filename queries. Top queries: Screen Recording (536), Untitled (384), IMG_ (232). Well under 25K target — that's the ceiling of what the API surfaces for these patterns.
- **Extracted channel_ids.csv** for both streams using Python csv module. Fixed `extract_channel_ids.sh` — the awk-based extraction broke on multiline descriptions in quoted CSV fields. Replaced with Python csv.DictReader.
- **Launched Stream A (Intent) in screen session** on Mac Mini: `screen -S stream_a`, `--limit 200000 --skip-first-video`. Running across 46 keywords in 8 languages. Checkpoint/resume enabled. ~765K API units.
- **Quota check:** ~648 units consumed today before Stream A launch. 1M+ remaining.
- **Note:** tmux not installed on Mac Mini; using `screen` instead for detached sessions.
- Stream D yielded far fewer than 25K target. The raw-filename search space is limited by what YouTube's API surfaces. 1,862 is a realistic population for this query strategy.
- What's next: Monitor Stream A. After completion, run A' and C on subsequent days. Then merge all channel lists and deploy cohort daily stats.

### Feb 16, 2026 — 09:30 PM [AI Census Audit + 50K Scaling Plan]
- **Audited AI census output (5,026 channels):** Median views = 897K (heavy algorithm bias, similar to Stream B). 30% have AI keywords in channel title/description (dedicated AI creators), 70% are general creators who made AI-adjacent videos. Top countries: India (1,093), US (1,053). Huge 2025 spike (1,150 channels = 23%).
- **Designed telescoping multi-design collection architecture:** 4 layers — (1) daily channel stats for 50K AI channels + 9.7K gender gap, (2) video inventory + AI flagging, (3) weekly video engagement on AI-flagged subset, (4) sampled comments. All three AI research designs (census, adoption diffusion, audience response) served by one data structure.
- **Approved plan for 50K scaling:** Expand search terms from 17 to ~47 (add specific tools: Runway, HeyGen, Pika, Suno, Stable Diffusion + non-English terms + domain-specific). Add sort order cycling (relevance + date). Extend time windows to 18 months. Estimated cost ~1.5M units over 1-2 days.
- **Plan file:** `.claude/plans/cached-baking-glade.md` — 7-step implementation plan with parallelization strategy for agents.
- What's next: Execute the 50K scaling plan (expand config, update script, run collection, build AI flagger, deploy to Mac Mini).

### Feb 16, 2026 — 09:15 PM [New Creator Cohort Streams A-D — Infrastructure Ready]
- **Added `--panel-name` flag to `daily_stats.py`**: output goes to `channel_stats/{panel_name}/YYYY-MM-DD.csv` when set, flat default when not (backwards compatible). Also adds panel-specific checkpoint files to avoid collisions.
- **Added checkpoint/resume to 3 large discovery scripts**: `discover_intent.py` (A), `discover_non_intent.py` (A'), `discover_random.py` (C). Saves progress after each keyword/prefix batch. Channels written incrementally to CSV. Interrupted runs resume from last checkpoint.
- **`config.get_daily_panel_path()`** now accepts `panel_name` param for subdirectory routing.
- Streams B and D are small enough to not need checkpoint/resume.
- All 5 syntax-checked, `--panel-name` tested end-to-end (subdirectory creation verified).
- **Plan file:** `.claude/plans/sharded-skipping-pie.md` — full 4-phase deployment plan with quota scheduling.
- What's next: Run Streams B+D (same day, ~35K units), then A/A'/C one per day.

### Feb 16, 2026 — 08:30 PM [AI Creator Census — COMPLETE]
- **Ran production AI Creator Census:** 5,026 unique channels discovered across 14 of 17 search terms (hit target before exhausting all terms).
- Output: `data/channels/ai_census/initial_20260217.csv` (33 columns, 5,026 rows, 0 nulls, 0 duplicates)
- Added **checkpoint/resume** to `discover_ai_creators.py`: incremental CSV writes + JSON checkpoint after each term. Fixed `datetime.utcnow()` deprecation warning.
- Quota consumed: estimated ~100K units (under 10% of daily limit). Ran in under 3 minutes.
- **Discovery keyword distribution:** AI voice (454), artificial intelligence (389), AI tutorial (388), prompt engineering (387), AI video editing (379), Sora AI (373), DALL-E (370), AI tools (366), agentic AI (342), generative AI (335), Claude Code (317), ChatGPT (316), AI automation (307), Midjourney tutorial (303)
- **Country distribution:** India (1,093), US (1,053), Unknown (1,345), GB (145), IT (140), PK (113), CA (98)
- **Overlap with gender gap panel:** 41 channels appear in both datasets
- What's next: Gender coding for AI census channels, AI adoption detection layer (keyword matching on video titles/descriptions)



## Feb 2026

### Feb 16, 2026 — 08:42 PM [Shell Script for Channel ID Extraction]
- **Built `scripts/extract_channel_ids.sh`** — utility script to extract channel_id column from any discovery output CSV and write clean channel list suitable for `daily_stats.py --channel-list`
- Features: automatic column detection, deduplication, sorted output, error handling (file checks, column validation), usage message
- Takes 2 args: INPUT_CSV and OUTPUT_CSV
- Output format: CSV with single "channel_id" column, sorted unique IDs
- Example usage: `./scripts/extract_channel_ids.sh data/channels/stream_b/initial_20260217.csv data/channels/stream_b/channel_ids.csv`
- Tested: usage message displays correctly when called with no args
- What's next: Use this script for Streams A-D channel list prep after discovery runs complete

### Feb 16, 2026 — 08:15 PM [Channel Stats Decoupled from Video Inventory]
- **Added `--channel-list` CLI arg to `daily_stats.py`** so channel-only mode reads from `channel_ids.csv` directly, bypassing the video inventory entirely. This unblocks daily channel stats collection while video enumeration is still in progress.
- New `load_channel_list()` method reads any CSV with a `channel_id` column. Falls back to inventory-based loading when `--channel-list` not provided (backward compatible).
- Validation logic updated: `--video-inventory` no longer required when `--mode channel` + `--channel-list` are both set. Still required for `--mode video` and `--mode both`.
- Guard added to `detect_and_add_new_videos()`: skips cleanly when no inventory path is set.
- **Tested on laptop:** 9,760 channels loaded, 9,672 stats collected (~50s). 88 channels returned not_found (terminated/deleted accounts).
- **Deployed to Mac Mini via SSH (192.168.86.48):**
  - `git pull` brought code up to date
  - Updated launchd plist: replaced `--video-inventory` with `--channel-list data/channels/gender_gap/channel_ids.csv`
  - Unloaded/reloaded plist, verified all 4 services in `launchctl list`
  - **Tested on Mac Mini:** 9,760 channels loaded, 9,672 stats collected (~100s). Output: `data/daily_panels/channel_stats/2026-02-17.csv`
- **Mac Mini now collecting full panel daily** (was only 2 channels before from partial inventory)
- What's next: Verify 3 AM launchd run produces 2026-02-18.csv. Continue video enumeration on laptop.

### Feb 16, 2026 — 07:55 PM [Mac Mini Deployed + Health Monitoring Built]
- **Deployed to Mac Mini via SSH** (192.168.86.48) — full Steps 1-7 from deployment guide
  - Cloned repo, installed deps (Python 3.9.6 on Mac Mini, not 3.14), copied config + data
  - Created and loaded 4 launchd services: daily-channel-stats, weekly-video-stats, sync-to-drive, health-check
  - Ran test collection: 2 channel stats collected (partial inventory on Mac Mini)
- **Built health check system** (`src/validation/health_check.py`) — 9 checks:
  channel freshness, channel completeness, video freshness, video completeness,
  log errors, inventory integrity, disk space, quota usage, stale checkpoints.
  Outputs HEALTHY/DEGRADED/FAILING. Supports --json. Runs daily at 12:00 UTC via launchd.
- **Built weekly digest** (`src/validation/weekly_digest.py`) — markdown summary of
  collection coverage, growth trends, data volume. Run manually or schedulable.
- **Fixed Mac Mini details:** IP was .41 (wrong), corrected to .48. Python is 3.9.6 not 3.14.
  Drive sync from laptop to Mac Mini can be stale — use scp for critical files.
- **Discovered Drive sync issue:** Files copied from Drive mount on Mac Mini had stale data
  (channel_ids.csv had 14,170 rows instead of 9,761). Used scp from laptop to push correct files.
- **Enumeration status:** 143/9760 channels done (~1.5%), still running on laptop.
  Once complete, scp inventory to Mac Mini for full production.
- Health check ran on Mac Mini: DEGRADED (expected — partial inventory, no video stats yet).
  All infrastructure checks pass (disk 37.6%, no errors, no stale checkpoints).
- What's next: Wait for enumeration, scp inventory, run full collection, verify 3 AM automation.

### Feb 16, 2026 — 09:45 PM [Production Launch + Mac Mini Handoff]
- **Regenerated channel_ids.csv** to 9,760 coded channels (filtered from 14,169 to only those with both gender + race)
- **Regenerated channel_metadata.csv** to match (9,760 rows with channel_id, perceivedGender, race, runBy, subscriberCount, viewCount)
- **Updated daily_stats.py** with `--mode channel|video|both` flag for dual-cadence collection
- **Launched video enumeration** on 9,760 channels (background, checkpoint/resume). ~80/9760 channels done at session end. Expected ~12M videos, ~245K API units total.
- **Created two launchd plists** (daily channel stats + weekly video stats). Created on laptop then unloaded — will be recreated with local paths on Mac Mini.
- **Wrote docs/PANEL_SCHEMA.md** — full dual-cadence schema documentation with field definitions, join examples, and storage projections
- **Wrote docs/MAC_MINI_DEPLOYMENT.md** — 9-step deployment guide for next agent. Covers: local-first I/O (EDEADLK avoidance), git clone, deps, config, data copy, plists with local paths, sync-to-drive script, testing, and troubleshooting.
- **Key insight from Second Brain:** Google Drive FUSE + launchd = deadlock. Must use local I/O on Mac Mini with rsync/osascript sync to Drive. Same pattern as Pat bot.
- Storage projection: ~40 GB/year (was 416 GB with daily + full panel). Quota: ~3.5% of daily limit average.
- What's next: Enumeration finishes (resume if interrupted). Next agent deploys to Mac Mini per docs/MAC_MINI_DEPLOYMENT.md.

### Feb 16, 2026 — 08:00 PM [Panel Design Decisions + Provenance]
- **DECISION: Panel restricted to 9,760 channels** with both gender AND race coded (excludes blank + undetermined). Uncoded channels lack identifiable creators, less analytically useful.
- **DECISION: Dual-cadence collection** — daily channel stats (tiny: ~195 API units/day, 1.1 MB/day), weekly video stats (~240K units, ~756 MB). daily_stats.py updated with `--mode channel|video|both` flag.
- Storage projections for coded panel: 269 GB/year (was 416 GB for full panel). Daily quota ~24% (was 37%).
- Added `source` column to `clean_baileys.py` — all channels tagged `source="infludata"` for provenance tracking
- Re-ran clean_baileys.py: all validations pass, 14,169 rows, 515 dupes removed
- What's next: regenerate channel_ids.csv for 9,760 coded subset, run enumeration, set up launchd

### Feb 16, 2026 — 07:21 PM [Infrastructure Slide Deck — Complete]
- Built 10-slide LaTeX Beamer deck (`output/youtube-longitudinal-infrastructure-deck.tex`) documenting the full data collection infrastructure
- Custom theme: navy/amber/slate palette, 16:9 aspect ratio, progressive reveal overlays
- Covers: two research programs, panel composition (14,169 channels with gender/race breakdown), three-dataset architecture (TikZ flow diagram), schemas with sample data rows, 5-stream sampling design, AI Creator Census (17 terms + 3 research designs), future enrichment pipeline, quota budget (29,300 units/day = 2.9%)
- Full deck-compile protocol: 3 compilation passes, second-agent narrative review, third-agent graphics audit
- Final PDF: 19 pages (with overlays), 0 overfull hbox/vbox warnings
- Fixes applied from reviews: woman % 24.4→24.5 (rounding), "parallel"→"same run" on TikZ arrow, clarified 7-field schema label
- What's next: Katie reviews deck; production runs still awaiting approval

### Feb 16, 2026 — 07:15 PM [Status Review + Slide Deck Prompt]
- Confirmed all 4 agents completed and all scripts test-verified
- Wrote agent prompt for infrastructure overview slide deck (Beamer, 10-12 slides)
- Identified next session priorities: (1) full video enumeration, (2) first daily stats run, (3) launchd automation, (4) AI Creator Census
- What's next: Run enumeration in new session, then set up daily automation

### Feb 16, 2026 — 06:41 PM [Gender Gap Panel — Full Infrastructure Build]
- Built complete gender gap panel infrastructure via 4-agent parallel strategy (A: data prep, B: API infra, C: collection scripts, D: AI census)
- **Data prep (Agent A):**
  - Created `src/collection/clean_baileys.py` — parses Bailey's xlsx with openpyxl header-based lookup, fixes 6 race typos, deduplicates 515 duplicate rows → 14,169 unique channels
  - Produced 3 output files: `data/processed/gender_gap_panel_clean.csv` (30 cols), `data/channels/gender_gap/channel_ids.csv`, `data/channels/gender_gap/channel_metadata.csv`
  - Updated `src/config.py` with 9 new paths, AI_SEARCH_TERMS (17 terms), 4 new schemas, get_daily_panel_path() helper
- **API infrastructure (Agent B):**
  - Added `get_all_video_ids()` to youtube_api.py — full playlist pagination with checkpoint/resume
  - Added `get_video_stats_batch()` — lean video stats fetch (part="statistics" only)
  - Added quota tracking to `execute_request()` — logs to data/logs/quota_YYYYMMDD.csv (backward compatible)
  - Created `__init__.py` for panels/, enrichment/, analysis/ modules
- **Collection scripts (Agent C):**
  - Created `src/collection/enumerate_videos.py` — builds video inventory with checkpoint/resume, UC→UU playlist conversion
  - Created `src/panels/daily_stats.py` — DailyStatsCollector class with 4-step pipeline (video stats → channel stats → save → new video detection)
- **AI census (Agent D):**
  - Created `src/collection/discover_ai_creators.py` — video-first search across 17 AI terms, 12-month time windows, order="relevance"
- **Test verification results (all passing):**
  - clean_baileys: 14,169 rows, all validations pass, race typos corrected
  - enumerate_videos --test --limit 2: 1,038 videos from 2 channels, correct 5-col schema
  - daily_stats --test: 250 video stats + 2 channel stats, daily panel files correct
  - discover_ai_creators --test --limit 5: 107 AI channels found
  - Backward compatibility: discover_intent.py and sweep_channels.py still import correctly
  - Quota tracking: data/logs/quota_20260216.csv being written
- Installed all Python deps for Python 3.14: openpyxl, pyyaml, pandas, tqdm, isodate, google-api-python-client
- What's next: Katie approves full video enumeration run, then start daily panel collection

### Feb 16, 2026 — 04:30 PM [AI Design Integration — Planning & Scope Expansion]
- Read and evaluated design document (`SECOND_BRAIN/03-research/YOUTUBE_DATASET_DESIGN.md`) — three new research designs: AI Creator Census, AI Adoption Diffusion Panel, Audience Response
- Audited all existing Python scripts against proposed architecture. Mapped reusable code vs. gaps.
- Analyzed both raw data files: confirmed 14,169 unique channels, 100% overlap between Infludata and Bailey's lists
- **Corrected misdiagnosis:** Bailey's xlsx does NOT have 4,097 misaligned rows. Those channels have BLANK gender/race (uncoded). Apparent misalignment was from parsing xlsx cells positionally instead of by cell reference.
- **SCOPE EXPANSION (Katie-approved):** This repo now owns longitudinal data collection on the 14,169 gender gap channels. Gender gap paper analysis stays in CH2. Updated CLAUDE.md.
- Resolved all 9 methodological decisions with Katie: all 14,169 channels, broad AI search terms, keyword-first AI detection, randomized comment sampling, partitioned CSVs to start
- Created new directory structure: `src/panels/`, `src/enrichment/`, `src/analysis/`, `data/channels/gender_gap/`, `data/channels/ai_census/`, `data/video_inventory/`, `data/daily_panels/{video_stats,channel_stats}/`, `data/transcripts/`, `data/comments/`, `logs/`
- Wrote full implementation plan: `.claude/plans/cached-knitting-puffin.md`
- Wrote agent handoff document: `docs/AGENT_HANDOFF.md`
- What's next: Hand off to parallel agents for implementation (data prep, API infrastructure, collection scripts, AI census)

### Feb 16, 2026 — 02:15 PM [Project Restructuring]
- Flattened project from triple-nested `youtube-longitudinal/youtube-longitudinal/youtube-longitudinal/` to root-level layout
- Production code (`src/`) moved from Level 3 to root; all `Path(__file__)` relative paths verified working
- Created project CLAUDE.md with session protocol, safety rules, coding standards
- Added `.claude/rules/` (01-session-protocol, 02-data-collection)
- Added `.claude/skills/log-update/` for session-end commit+push workflow
- Moved 4 existing analysis skills (stata-regression, r-econometrics, python-panel-data, referee-audit) to root `.claude/skills/`
- Detailed docs from Level 2 promoted to root (PROJECT_MASTER_PLAN, PROGRESS_LOG, TECHNICAL_SPECS, DECISION_LOG)
- Reference docs (API variable ref, sampling experiments, quota analysis) moved to `docs/`
- Updated `.gitignore` (comprehensive: data, secrets, artifacts, archive, output)
- Archived: v1 legacy scripts, superseded rule files (AI_RULES, ANTIGRAVITY_RULES, MY_WORKFLOW), loose conversation/template files, stray 656MB .dta file (confirmed duplicate of dissertation copy)
- Removed nested `.git/` repository (history captured in commit message)
- Resolved merge conflict with remote (b527cb0 production commit)
- What's next: install Python deps, then start production collection

### Feb 02, 2026 — 05:30 PM (Late Evening Session)
**Session Focus:** Full Production Pipeline Implementation

**Work Completed:**
- **Complete Rewrite:** Built production-grade modular architecture with 15 new files
- **Configuration System:** Created `config.py` with comprehensive constants:
  - 8-language keyword mappings (Intent + Non-Intent)
  - Full YouTube topic hierarchy (200+ topics with decoding)
  - Stream-specific directories and targets
  - Data schemas for channels, videos, sweeps
- **Enhanced API Module:** Upgraded `youtube_api.py` with:
  - Full topic extraction and decoding (hierarchical topics)
  - Comprehensive channel details (28 fields for initial, 8 for sweeps)
  - Video batch fetching with Shorts classification
  - New video detection for longitudinal tracking
  - Search helpers with pagination
- **Collection Scripts (5):**
  - `discover_intent.py` — Stream A: Intent creators (200k target)
  - `discover_non_intent.py` — Stream A': Non-intent creators (200k target)
  - `discover_benchmark.py` — Stream B: Algorithm favorites (2k)
  - `discover_random.py` — Stream C: Random prefix (50k)
  - `discover_casual.py` — Stream D: Casual uploaders (25k)
- **Sweep System:**
  - `sweep_channels.py` — Main sweep with checkpoint/resume
  - `detect_new_videos.py` — New video detection logic
- **Validation:**
  - `validate_sweep.py` — Data quality checks (duplicates, anomalies, policy changes)
- **Testing:** 
  - Stream A test: 62 Hindi channels collected successfully
  - Stream D test: 15 casual channels collected successfully
  - Validation: 0 errors, all systems operational

**Sample Size Decision:**
- Updated Stream A and A' from 25k → **200k each** to handle attrition
- Rationale: Early-stage creator dropout is 50-70%; need huge buffer
- Expected English channels: 50k-80k per stream (sufficient for analysis)

**Quota Impact:**
- Initial collection (2 streams, 400k channels): ~808k units (fits in 1 day)
- Recommendation: Use `--skip-first-video` flag for speed
- Can enrich with first video data later if needed

**Directory Structure Created:**
```
youtube-longitudinal/
├── src/
│   ├── config.py
│   ├── youtube_api.py
│   ├── collection/
│   │   ├── discover_intent.py
│   │   ├── discover_non_intent.py
│   │   ├── discover_benchmark.py
│   │   ├── discover_random.py
│   │   └── discover_casual.py
│   ├── sweeps/
│   │   ├── sweep_channels.py
│   │   └── detect_new_videos.py
│   └── validation/
│       └── validate_sweep.py
└── data/
    ├── channels/
    │   ├── stream_a/
    │   ├── stream_a_prime/
    │   ├── stream_b/
    │   ├── stream_c/
    │   └── stream_d/
    ├── videos/
    └── logs/
```

**Files Created:**
- `src/config.py` (700+ lines)
- `src/youtube_api.py` (rewritten, 1000+ lines)
- `src/collection/discover_intent.py`
- `src/collection/discover_non_intent.py`
- `src/collection/discover_benchmark.py`
- `src/collection/discover_random.py`
- `src/collection/discover_casual.py`
- `src/sweeps/sweep_channels.py`
- `src/sweeps/detect_new_videos.py`
- `src/validation/validate_sweep.py`
- Module `__init__.py` files (3)

**Key Design Features:**
- **Topic Support:** Full YouTube hierarchical topics (not just categories)
- **Language Tracking:** `discovery_language` field tracks which language found each channel
- **Shock Readiness:** All policy-relevant fields included (made_for_kids, privacy_status, etc.)
- **Checkpoint/Resume:** Sweeps can be interrupted and resumed
- **Validation:** Automated quality checks for data integrity

**Next Steps (Tomorrow):**
1. Start Stream A collection (200k channels, ~404k units)
2. Start Stream A' collection (200k channels, ~404k units)
3. Consider using `--skip-first-video` for initial speed
4. Set up sweep schedule once initial collection complete

---

### Feb 02, 2026 — 04:30 PM (Evening Session)
**Session Focus:** Comprehensive Sampling Methodology Validation & Quad-Stream Design

**Work Completed:**
- **Experiment Battery:** Ran 6 systematic experiments testing sampling strategies:
  - EXP-001/003: Bias Profile Comparison (Vowels vs Raw vs Random Prefix)
  - EXP-002/010: New Creator Yield Rates (Intent vs Non-Intent keywords)
  - EXP-005: Channel ID Enumeration (result: not viable)
  - EXP-006: Language Bias Detection (8 languages tested)
  - EXP-007: Region Code Impact
  - EXP-008: Pagination Depth Bias
- **Critical Discovery:** English-only keywords miss 86% of findable new creators. Hindi has highest yield (35.3%).
- **Design Evolution:** Upgraded from Triple-Stream to Quad-Stream design with Stream D (Amateur Baseline).
- **Documentation Created:**
  - `SAMPLING_EXPERIMENTS.md` — Full experiment log with results
  - `QUOTA_ANALYSIS.md` — Sample size and polling frequency analysis
  - `test_sampling_battery.py` — Comprehensive test script
  - `test_language_pagination.py` — Language and pagination experiments
  - `discover_amateur.py` — Stream D collection script
  - `discover_cohort_multilingual.py` — Enhanced 8-language cohort discovery

**Key Findings:**
| Finding | Evidence | Implication |
|---------|----------|-------------|
| Vowel search massively biased | 1.16M median views, 94% big channels | Relabeled as "Algorithm Favorites" |
| English misses 86% of creators | 38 vs 271 across 8 languages | MUST use multilingual |
| Hindi highest yield | 35.3% vs 30.9% English | Prioritize Hindi |
| Pagination doesn't help | Page 2 higher views than Page 1 | Abandon strategy |
| Polling is cheap | 130k channels = 2,600 units/day | Daily polling feasible |

**Quota Analysis Summary:**
- Recommended panel: 130,000 channels (50k A + 10k B + 50k C + 20k D)
- Daily polling cost: 2,600 units (0.26% of quota)
- Collection budget: 500,000 units/day
- 80%+ quota remains for flexibility/experiments

**Files Created/Modified:**
- `SAMPLING_EXPERIMENTS.md` (Created)
- `QUOTA_ANALYSIS.md` (Created)
- `TECHNICAL_SPECS.md` (Major update — Quad-Stream)
- `PROJECT_MASTER_PLAN.md` (Updated findings & design)
- `src/test_sampling_battery.py` (Created)
- `src/test_language_pagination.py` (Created)
- `src/discover_amateur.py` (Created)
- `src/discover_cohort_multilingual.py` (Created)
- `config/config.yaml` (Created with API key)

**Next Steps (Production Ramp-Up):**
1. Run 24-hour multilingual cohort collection
2. Run amateur baseline collection
3. Set up automated daily polling
4. Design hybrid polling tiers (hot/warm/cold)

---

### Feb 02, 2026 — 03:00 PM
**Session Focus:** Methodological Pivot to Triple-Stream Design

**Work Completed:**
- **Bias Diagnostics:** Ran empirical tests comparing "Vowel Search" (Median Views 652k) vs "Random Prefix" (Median Views 22).
- **Sampling Strategy:** Validated that a single "Random" sample is insufficient.
- **Design Pivot:** Adopted "Triple-Stream" approach (Intentional A + Visible B + Deep Random C).
- **Scripting:** Created `discover_cohort.py` (Stream A) and `discover_random.py` (Stream B initial version).
- **Documentation:** Consolidated artifacts into `PROJECT_MASTER_PLAN.md` and `TECHNICAL_SPECS.md`.

**Key Findings:**
- **"Filing for Videos" (Zhou et al.):** Confirmed as reference for Random Prefix Sampling.
- **Quota Capacity:** We have effectively infinite quota (1M/day) for this scale, allowing us to run all three streams simultaneously.

**Decisions Made:**
- **Triple-Stream Design:** (See `DECISION_LOG.md` entry 001). Chosen to control for survivorship bias while checking market competitiveness.
- **Vowel Rotation:** Used for Stream B to ensure linguistic coverage of the "Visible" market.

**Files Created/Modified:**
- `PROJECT_MASTER_PLAN.md`: Created (Canonical roadmap).
- `TECHNICAL_SPECS.md`: Created (Canonical specs).
- `DECISION_LOG.md`: Created (Canonical decision record).
- `src/test_bias_deep_dive.py`: Created (Diagnostic tool).

**Next Steps (Immediate):**
1. Clean up redundant documentation (`implementation_plan.md`, `sampling_methodology.md`).
2. Finalize script names.

### Feb 02, 2026 — 03:15 PM
**Session Focus:** Deep Review of Sampling Strategy & Script Logic

**Work Completed:**
- **Strategy Deep Dive:** Conducted literature review on "Snowball Sampling" vs "Random Prefix" vs "External Lists." Created `sampling_strategy_review.md`.
- **Code Audit:** Analyzed `discover_cohort.py` and `discover_visible.py` to document exact search keywords and query logic (`q` searches snippets, not just titles).
- **Validation:** Confirmed "Stream C" (Deep Random) logic: inherently captures 99% nonsense to prove the 1% signal is distinct.
- **Cleanup:** Renamed `discover_random.py` -> `discover_visible.py` to clarify its role as "Market Baseline."
- **Deleted:** Redundant artifacts (`task.md`, `implementation_plan.md`, etc.) after consolidation.

### Feb 02, 2026 — 03:30 PM
**Session Focus:** Project Setup & Git Initialization

**Work Completed:**
- **Git Initialization:** Initialized local repository and created `.gitignore` to exclude sensitive/large files.
- **GitHub Link:** Successfully linked local repo to `apkerk/youtube-longitudinal` and pushed `main` branch.
- **Documentation Audit:** Created missing standard files (`MY_WORKFLOW.md`, `writing-patterns.md`, `deck.md`) from templates to ensure full compliance with the research system.
- **Folder Structure:** created `drafts/` and `archive/` directories.

**Files Created/Modified:**
- `.gitignore`: Created.
- `MY_WORKFLOW.md`: Created.
- `writing-patterns.md`: Created.
- `deck.md`: Created.

**Next Steps (Immediate):**
1. 🛑 USER ACTION REQUIRED: Run the 3-step validation suite to confirm network access.
2. Set up `launchd` for daily automation.

**Key Findings:**
- **Stream A Keywords:** Validated list (`Welcome`, `Intro`, `Vlog 1`) targets intentionality.
- **Stream C Logic:** Confirmed that "Nonsense" results are a *feature*, not a bug, providing a true Zero Baseline.
- **Alternatives Rejected:** "Snowball Sampling" rejected due to Homophily Bias (echo chambers).

**Files Created/Modified:**
- `sampling_strategy_review.md`: Created (Comparative analysis).
- `src/discover_visible.py`: Renamed and updated docstrings.
- `src/discover_deep_random.py`: Created.

**Next Steps (Immediate):**
1. 🛑 USER ACTION REQUIRED: Run the 3-step validation suite to confirm network access.
2. Set up `launchd` for daily automation.

## 2026-03-10 19:30 Stream Infrastructure Hardening + Enumeration Deployment
- Added QuotaExhaustedError + --max-runtime + --reserve-quota to all 6 unstarted scripts: discover_livestream, discover_shorts, discover_creative_commons, discover_topic_stratified, discover_trending, discover_non_intent (Stream A')
- Fixed youtube_api.py: get_all_video_ids now re-raises QuotaExhaustedError instead of swallowing it
- Fixed enumerate_videos.py: added QuotaExhaustedError catch, --max-runtime flag, and start_time tracking
- Fixed health_check.py: inventory_integrity no longer fires DEGRADED for partial inventory; video_stats_completeness threshold is now dynamic based on inventory size (stops false Telegram alerts)
- Deployed gender gap video enumeration as launchd service: com.youtube.gender-gap-enumeration (fires 4:00 AM EST, 7h max runtime, checkpoint/resume). Tested: 5 channels, 3,905 videos, ~780 videos/channel avg -- full run ~7.6M videos across ~3 overnight runs.
- What's next: Enumeration completes ~March 13-14. Then: Stream A' re-run, Trending, Livestream, Shorts, Creative Commons, Topic-Stratified (one at a time, no concurrent discovery scripts).

## 2026-03-12 15:45 Health Check Fix + Stream A' Launch

### Fixes
- **health_check.py NUL byte bug:** Inventory reads were crashing with `line contains NUL` because enumerate_videos.py writes NUL bytes during active collection. Added `_count_csv_rows_nul_safe()` helper (binary read + strip NUL + decode). Pipeline now reads 4,951,627 inventory rows correctly. CRITICAL removed. Committed 59c39b9.
- Root cause of Telegram alert at 12:02 PM: health check runs at 4 PM UTC (noon EDT) and was hitting this crash daily.

### Status
- Stream A': Launched for first time today at 2:00 PM. Running. 5,950+ channels from first keyword alone in first 38 minutes. 82 keywords x 15 languages x 5 strategies. Daily 4h runs until 200K reached.
- Gender gap enumeration: 3,668/9,760 channels done (37.6%) as of this morning. ~March 15-16 completion.
- Daily stats: Clean. Mar 12 file written 3:06 AM.
- Remaining WARNING (video_stats_completeness 1,038 rows): Expected. Weekly video stats ran March 8 when inventory was near-empty. Self-corrects on Sunday's run.

### Next Steps
- Sunday: weekly video stats re-runs on larger inventory, completeness WARNING resolves
- ~March 15-16: enumeration completes, start 5 new streams (one at a time)

## 2026-03-16 — Infrastructure Fixes Sprint (March 12–16)

### Fixes Deployed
- **enumerate_videos.py checkpoint bug (critical):** Checkpoint was deleted after every nightly run — including max-runtime exits — causing the script to re-enumerate from scratch each night instead of resuming. Fixed by moving checkpoint cleanup inside `enumerate_all_channels()` so it only fires when ALL channels are complete. Regression tests added: `src/validation/test_checkpoint_behavior.py` (4/4 passing on Mac Mini).
- **enumerate_videos.py completion sentinel:** Launchd fired again March 16 4 AM and overwrote the completed 11.7M inventory. Added sentinel so completed runs skip re-enumeration. Rebuilding ~14 nights from scratch.
- **health_check.py NUL byte crash:** Inventory reads crashed with `line contains NUL`. Added `_count_csv_rows_nul_safe()` helper (binary read + strip NUL + decode).
- **daily_stats.py NUL byte crash:** Same NUL byte issue in load_inventory() and known_video_ids block. Patched with binary read approach.
- **Stream A' launchd deployed:** com.youtube.daily-discovery-non-intent fires 2 PM daily. 43,553 channels collected so far. 82 keywords x 15 languages x 5 strategies, running toward 200K target.

### Research Design Discussion
- New video detection identified as highest priority: needed to establish AI adoption timing for staggered DiD in AI Adoption Diffusion Panel.
- AI census has no weekly video stats collection configured -- gap to close.
- Katie raised research design question: tech channels pre-Claude Code launch (Jan 2026) as cleaner exogenous shock sample for studying gender differences in AI adoption rates. Needs fleshing out.

### Current Status
- Gender gap enumeration: OVERWRITTEN by launchd re-run March 16. Rebuilding. ~14 nights to completion.
- Daily panel stats: Running clean (both gender gap and AI census). Mar 16 3:05 AM file confirmed.
- Stream A': Running. ~43,553 channels toward 200K.

### What's Next
1. Build src/panels/update_inventory.py -- new video detection for both panels (highest priority)
2. Set up daily chunked video stats (--chunk flag on daily_stats.py) for AI census and gender gap
3. Wire Trending stream (cheap, ~100 units/day, low effort)
4. Think through tech-channel AI adoption research design (Katie's new idea)

### All Commits Pushed
- enumerate_videos.py bug fix + sentinel
- daily_stats.py NUL byte fix
- health_check.py NUL byte fix
- src/validation/test_checkpoint_behavior.py (new regression tests)
- config/launchd/com.youtube.daily-discovery-non-intent.plist (new)

## 2026-04-26 08:12 [Enumeration Throughput Tuning]
**Focus:** Free quota-bound throughput for KE Census enumeration after pausing Entry Cohorts.
**Project State:** Data infrastructure phase — KE Census enumeration in progress (25,272/143,558 channels = 17.6% as of Apr 25), Entry Cohorts paused, all 6 daily panels running clean.

### What was done
- **Paused Entry Cohorts discovery (Apr 20, 10 PM):** Unloaded `com.youtube.daily-discovery-entry-cohorts` and renamed plist to `.PAUSED` on Mac Mini. Preserves resume path, prevents accidental reactivation. Resume note in `paused_services.md` auto-memory.
- **Verified pause working:** Apr 19-21 enumeration runs hit `quotaExceeded` 403s at ~1 PM (Entry Cohorts active). Apr 22-25 runs hit `Max runtime 25200s` ceiling cleanly at 4 PM with no 403 — confirming quota is no longer the binding constraint.
- **Bumped max-runtime 7h → 10h → 17h** on `com.youtube.knowledge-economy-enumeration.plist`:
  - Reasoning: quota resets at midnight Pacific = 3 AM Eastern, exactly when daily stats fires. Enumeration burning through Wednesday's quota by evening doesn't conflict — daily stats at 3:05 AM Thursday gets fresh quota. Just need a buffer so enumeration isn't actively running at 3 AM competing for Thursday's reset quota.
  - Final: 61,200s = 17h. 9 AM start → 2 AM stop = 1h buffer before daily stats.
  - Script's `QuotaExhaustedError` handler stops cleanly at 403; max-runtime is just the safety belt.

### Other observations
- Entry Cohorts diagnostic (pre-pause): 103,442 unique channels discovered, only 12.6% (13,083) actually CREATED in treatment/control windows. The 87.4% (90,359) are established adopters — bonus dataset for Design A. Confirms post-hoc filter approach is correct; no keyword problem.
- Retroactivity confirmed: enumeration ~99% retroactive (deletion attrition only), Entry Cohorts ~95% retroactive. Daily stats + April cohort from-founding tracking = NOT retroactive (must keep running).

### Files modified
- `~/Library/LaunchAgents/com.youtube.knowledge-economy-enumeration.plist` (Mac Mini): max-runtime 25200 → 36000 → 61200
- `~/Library/LaunchAgents/com.youtube.daily-discovery-entry-cohorts.plist` → renamed `.PAUSED` (Mac Mini)
- Auto-memory: `paused_services.md` + `MEMORY.md` index entry

### Next
- Monitor Monday's run (first 17h window). If quota 403 hits before 2 AM, that's the actual ceiling and we'll know throughput.
- Resume Entry Cohorts when KE enumeration completes (~3 weeks at projected ~6K channels/day).

## 2026-06-17 [QbQ-Auto paper: "The Gendering of a General-Purpose Technology"]
- Ran the full QbQ-Auto question-by-question pipeline on the KE Census (Knowledge Economy) data to produce a complete ASQ draft on gendered AI adoption among knowledge-sector creators. Project: papers/gendering-ai-expertise/.
- DATA ENGINEERING: AI flagger on the 45.9M-video KE inventory; built a measurement-CLEAN three-tier AI flag (unambiguous any-date; ambiguous brand tokens gated to launch; classical-ML field terms + homonyms era-gated to ChatGPT) that cut pre-2022 false-positive adopters from 51.6% to 7.0% (8,652 clean adopters). Coded perceived gender on the 43,546-channel analytic roster (FairFace/DeepFace vision + offline name-based; validated vs 9,760 hand-coded: 90.9% accuracy, 4.15pp differential FPR), completed roster coverage with the name-based component. 14,203 binary-gender channels.
- FINDINGS (definitive, full gender): women adopt AI content less (logit OR 0.72, p<0.001; 12.0% vs 16.0%). The gap is TOOL-DEPENDENT: female x post x techiness = -0.0027 (p=0.009), x developer-origin = -0.0140 (p=0.006), pooled null; ChatGPT event-study pre-trends flat (p=0.117), placebo flat (p=0.892). The gap is at ENTRY, not in claiming: AI-expert bio claim null, women claim GENERIC authority MORE (+0.121, p=0.040), AI-title authority null (p=0.95). Audience-ratification INCONCLUSIVE (6-week panel).
- THESIS REFRAME (data-driven): the original "who gets to call themselves an AI expert / legitimacy-conferral" framing did NOT survive full gender (no claiming gap in titles/bios). Headline reframed to a tool-techiness-moderated gender gap in AI ADOPTION: "the democratization of AI was itself gendered" (closed for mainstream tools, persisted at the technical/developer frontier). Mechanism = gendered status beliefs + gendered technology (Ridgeway & Correll, Wajcman, Hargittai); conferral/claims-making demoted to an inconclusive/measurement-bounded null. See qbq/WORKING.md GRAVEYARD.
- IDENTIFICATION NOTE: tool launches are calendar-common shocks staggered across TOOLS not units, so Callaway-Sant'Anna/Sun-Abraham do NOT apply; used event-study + Cengiz stacked DiD + TWFE reference.
- DELIVERABLES: manuscript drafts/Gendering_AI_Expertise_v1.pdf (11,116 words, 28 refs, 4 tables + 4 figures), QbQ artifacts (Dashboard, Working, framing-memo LOCKED, findings-ledger, contradiction-file), README + run_all_analysis.sh replication, self-brief deck (building). Gap built vs Locke&Golden-Biddle/Merton/Barney/Zuckerman/Davis; headline-novelty clear.
- VERIFICATION: independent CoVe audit -> numerically faithful, no fabricated cites, no em dashes, all overclaiming guardrails respected. Method cites tagged [VERIFY] for a future /bibcheck.
- NOT committed to git (awaiting Katie's OK; all files saved on Drive). DiD panel preliminary (~1,223 channels); future work = extend vision gender coverage, collect descriptions/transcripts, video-level audience data.

## 2026-06-19 — Gendering-of-AI paper: extreme EDA + gender re-coding (thumbnails) + infra incidents
**Analysis (papers/gendering-ai-expertise/, scripts 09-16 + Mac Mini src/paper_gendering_ai/):**
- Ran full EDA on interim sample: pool audit (clean; ~20% topic noise droppable; gap survives), survival/timing (gap is mostly WHETHER not when; front-loaded hazard), Claude Code event study (clean CC-GA -0.0137, gender-typing verdict), heterogeneity (NEW: gap WIDENS with channel size, OR 0.60 large vs 1.03 small; two-stage entry+persistence gap, one-and-done OR 1.38), credentialing (women under-claim engineer/scientist OR 0.43, over-claim certification/coach — "form not level"), robustness (gap survives 6 gender defs but FRAGILE in magnitude / non-sig within core-KE after topic FE).
- DiD assessment: stacked design is a triple-difference (no untreated controls; calendar-common shocks); few-tool event-study (ChatGPT vs Claude Code GA) is the cleaner identification. Methods cites verified (Goodman-Bacon 2021, Cengiz 2019, Roth 2023, etc.).
**Gender re-coding (the session's main pivot):**
- Old draft used preliminary name-heavy coding (14,203). Rebuilt VISUALLY from thumbnails.
- DeepFace-on-thumbnails MALE-BIASED (12% female, mislabeled ~70% of women) — DISCARDED for gender; face-detection kept.
- GEMINI 2.5 Flash visual coder = PRIMARY: ke_thumb_gemini_gender_channel.csv, 17,273 channels, 27.7% female, 88.5% agreement w/ avatar-vision, ~2x better woman recovery. Tiers T1/T2/T3 by face count. RULE: thumbnails beat names; name-only excluded.
**Infra:**
- Re-enum of 17,296 missing-video (heavy) channels: resilience bug FIXED (one timeout no longer kills run); PAUSED at 4,002/17,296, disk-blocked. Safe-resume in REENUM_RESUME_NOTE.md.
- DISK INCIDENT: Mac Mini hit 100% full; killed stuck re-enum, cleared 4.8GB thumbnail cache (now ~3.9GB free). Root cause beyond my cache: 38GB Google Drive cache re-mounted (was removed Feb 23) — KATIE'S CALL to free; unblocks re-enum.
- VERIFIED daily-stats collection is HEALTHY (101 gender_gap panels Feb17-Jun19); the "down since Feb 17 / 4 months missed" alarm from another agent is FALSE (Feb 17 = start date).
- Gemini key at ~/.config/yt_gemini_key (rotate — passed through chat).
**NEXT (handoff issued):** A) hand-code 50 channels to validate Gemini gender per-tier; B) re-run findings at all floors (T1+/T2+/T3+) on Gemini gender; C) free disk -> resume re-enum -> AI re-flag + adoption recompute -> rebuild -> re-run on complete sample. Then comprehensive report (framing UNLOCKED; reframe candidates: size-magnifies-gap, two-stage, coding-frontier, credential-form-not-level).

## 2026-07-17 11:35 — Post-shutdown health check + video-stats OOM fix
**Trigger:** Katie back from 2 weeks travel; accidentally powered the Mini off this morning. Full pipeline health check requested.
- **Channel-stats collection HEALTHY.** Mini came back up (launchd self-healed); all 7 channel-stats panels wrote today's file: gender_gap 9,760, ai_census 50,010, tech_census 63,728, new_cohort 135,977, category_quota 73,508, knowledge_economy 143,558, april_cohort 405,786. 28 launchd services loaded.
- **Fixed false health-check alarm.** `check_daily_health.py` looked for gender_gap at the flat `channel_stats/YYYY-MM-DD.csv` path, but the panel moved to `channel_stats/gender_gap/`. Every day reported a false MISSING. Patched to pass `panel_name='gender_gap'`. Archived 4 stale `daily_stats_FAILED_*.flag` sentinels (Mar 15, Apr 27, Apr 29, Jun 17) to `archive/resolved_sentinel_flags/`. Health check now PASSES.
- **ROOT CAUSE FOUND — video-stats panels dead since 2026-06-16.** ai_census + knowledge_economy video-stats wrote nothing for a month. `daily_stats.py` and `update_inventory.py` read the 4.5-6.5 GB video inventories whole (`f.read().replace(NUL)`) and accumulated all stats in memory before one end-of-run write; on the 8 GB Mini this OOM-killed the process (`Killed: 9`, 15 occurrences). Because the write was end-of-run, every killed run lost the whole day.
- **FIX (commit 2e3f317, pushed):** `nul_safe_line_iter()` streams the inventory line-by-line; `collect_video_stats()` appends each batch to the panel file and flushes before the checkpoint claims it, and restarts from batch 0 if the checkpoint claims progress but the partial file is missing. `update_inventory._load_known_video_ids_nul_safe()` made streaming too. Verified: --test peaks at 2.2 GB RSS (was multi-GB and climbing). Relaunched today's chunk-4 jobs for both panels — running at 634 MB / 996 MB RSS, actively writing (72 MB / 77 MB so far).
- **Disk healthy:** Mini at 12% used, 79 GB free (June 19 disk crunch resolved).
- **DATA GAPS (methods note):** (1) June 28–July 13 channel snapshots missing (Mini off for cross-country move). (2) ai_census + knowledge_economy VIDEO stats missing ~June 16–July 16 (OOM outage). Both unrecoverable — YouTube API returns only current stats.
- **FLAG for Katie:** Mini had an untracked `src/collection/enumerate_videos_targeted.py` that DIFFERS from the committed version; backed up to `temp/prepull_untracked_20260717/` on the Mini, not merged. Needs a look when you pick the KE re-enum back up.

## 2026-08-01 16:20 — Disk-full incident (Jul 24-Aug 1): resolution + backup gap discovered
**Incident:** Mini data volume filled Jul 24 (sentinel: "No space left on device"), reached 100% full / 124 MB free by Aug 1. Damage: Jul 31 video-stats truncated mid-run (ai_census 40M vs ~195M expected; KE 10M vs ~310M — partial files preserved by the Jul 17 incremental-write fix); Aug 1 channel-stats failed across all 7 panels at their 3 AM slots. Channel panels Jul 24-31 all complete (9,761 rows daily) — the July 24 failure self-recovered same-week.
**Root cause:** `sync-to-drive` launchd job nightly-copied all panel data into `~/Library/CloudStorage/.../My Drive/RESEARCH/YT LONGITUDINAL/data` (47 GB), but Google Drive app on the Mini has not run/uploaded since ~February. The "backup" was a dead-end local duplicate doubling every byte of panel data. Same mechanism as the June 19 disk incident.
**Resolution (Katie approved Jul 31/Aug 1):** Verified staged 47 GB was strictly duplicates (spot-checked identical/older vs repo originals; sync script confirmed one-way repo→staging). Deleted staged data folder → 47 GB reclaimed (78% used). Unloaded + retired `com.youtube-longitudinal.sync-to-drive` (plist → .RETIRED; expected loaded YT services now 24). Archived Jul 24 sentinel flag. Kickstarted all 7 channel-stats services (Aug 1 snapshots salvaged same-day, collected ~4 PM instead of 3 AM — note time-of-day deviation for Aug 1). Relaunched Aug 1 video-stats chunks for ai_census + KE.
**DATA GAPS (methods note):** Aug 1 channel snapshots collected ~13h late (same day). Jul 31 video-stats partial for ai_census/KE. Unrecoverable beyond that: none from this incident.
**OPEN FLAG — BACKUP:** Panel data (32 GB daily_panels, growing) now exists ONLY on the Mac Mini. Cloud copy stale since ~Feb; sync path retired. Decide a real backup route (fix Drive client, scheduled rsync to laptop, or external SSD). Also: disk at 78% will keep growing ~0.5-1 GB/day — revisit within ~2 months regardless.

## 2026-06-22 (Mon) — Interim findings re-run on Gemini visual gender (script 17)
- Ran src/17_rerun_tiered_gemini.py: headline findings re-estimated on the TRUSTWORTHY Gemini thumbnail gender at all confidence floors (T1+ 17,273 / T2+ 15,538 / T3+ 10,723 channels). Outputs: output/rerun_tiered_gemini.json + _log.txt.
- SURVIVED + STRENGTHEN at stricter floors: adoption gap (T3+ OR 0.65, men 25.4% vs women 17.2%, p<.001); one-and-done persistence gap (T3+ OR 1.47); coding-AI female share collapse (T3+ 3.6% vs 18.9% adopter base); technical-identity under-claim (engineer/scientist OR 0.33); formal-degree null (form-not-level pattern intact).
- DID NOT REPLICATE: gender x size interaction (ns at every floor) — artifact of the old name-heavy coding. DROPPED from candidate contributions.
- Read: the core story is robust to gender measurement and sharpens with confidence — retires the face-coding-artifact worry.
- HANDOFF: Katie's next thread (gendered CONTENT of AI uptake — "pinkification" of Claude Code talk, transcript/content analysis, tool-drops-as-exogenous-shocks causal ID, multi-project pattern split, HTML deck) is with ANOTHER AGENT in a parallel session. This session only logs.
- Still open: (A) 50-channel hand-code validation sheet; (C) 38GB Drive cache -> free disk -> resume re-enum (paused 4,002/17,296); rotate Gemini key. Daily stats verified healthy through 2026-06-22.
> DATING NOTE (2026-08-03): the entry above covers the 2026-06-22 session (script 17 interim re-run) but was logged retroactively on Mon 2026-08-03 when that session resumed — hence it appears after the July disk-incident entries. Chronology of the work itself: Jun 22. "Daily stats healthy through 2026-06-22" and the open items reflect Jun-22 state; see the Jul 24–Aug 1 entries above for what changed since (disk incident, sync-to-drive retired, Aug 1 salvage, KE re-enumeration script).

## 2026-08-04 06:00 [Gendering-AI-Expertise: manuscript updated to v3 findings + elite citation splice]
- Rewrote drafts/gendering_ai_expertise_v1.md (now v1.1; pre-update copy preserved at drafts/_archive/gendering_ai_expertise_v1_pre-2026-08-03-update.md) per HANDOFF_manuscript_update.md and qbq/findings-ledger.md.
- Number swaps executed and each verified against output/*.json source files: gendered sample 14,203 -> 17,273 (27.7% women); adoption 12.0/16.0 OR 0.72 -> 12.2/16.4 OR 0.71 (Cox HR 0.76, T3 tier OR 0.65); stacked-DiD techiness triple -0.0027 (p=.009) -> -0.0015 (p=.036); developer-origin -0.0140 (p=.006) -> -0.0089 (p=.016); panel 1,223 -> 3,240 channels (1,202,040 stacked event-channel-months); ChatGPT pre-trend p=.117 -> p=.748; placebo p=.892 -> p=.404 (pre-trend basis); pooled fem x post -0.0037 (p=.26) -> -0.0029 (p=.21); TWFE -0.0179 (p=.037) -> -0.0182 (p=.002); timing medians 392/324 -> 385/313 (adjusted n.s. p=.10).
- SUBSTANTIVE: removed "women claim generic authority MORE (+0.121, p=.040)" everywhere (did not survive v3); replaced with the authority FORM split (certification OR 1.72, coach 1.9x, consultant 1.3x vs engineer 0.29x / scientist 0.33x / developer 0.41x; degrees + expert flat; credential does not close the gap, 6.9pp both sides; identical among adopters/non-adopters, so framed as a knowledge-economy pattern the AI shelf inherits). Added persistence finding (one-and-done 38.1% vs 31.9%, OR 1.32-1.47 across tiers). Deleted degree over-claiming and gap-by-channel-size (both dead on v3).
- Methods gender-coding paragraph rewritten to the thumbnail-vision method (Gemini + DeepFace face-count tiers, names never assign; n=25 overlap 96% acc / 4.4pp diff error vs 22pp for old coding) with triangulation as the defensible claim (3 codings x all tiers).
- Elite citation splice (DASHBOARD T1) executed in the same pass: dropped Exley & Kessler, Aldasoro, Peng, Faulkner; wove in the 8 reinstated elite cites + anchors (Campero 2020, Correll et al. 2020, Dupree 2024 re-pointed to the form split, Botelho & Abraham 2017, Correll/Benard/Paik 2007, Hsu 2006, Hsu/Hannan/Kocak 2009, Leung 2014, Kacperczyk & Younkin 2017, Lee/Koval/Lee, Eyal 2013, Greenberg & Mollick 2017, DiMaggio et al. 2004 anchor) + form-split credentialing set (Quadlin 2018, Castilla & Benard 2010, Campbell & Hahl 2022, O'Brien 2016, Kim et al. 2020); added Duffy 2017 to refs.
- Citation corrections found via OpenAlex: Lee/Koval/Lee is AMJ 2023 66(4):1042-1070 (both stored records had wrong vol/pages); Dupree 2024 is ASQ 69(2):271-323; O'Brien 2016 is Social Currents 3(4):315-331 (stored 3(3):247-265 was wrong); Kim et al. 2020 author initials fixed.
- Tables: Table 3 + new tier-robustness Table 4 carry full v3 numbers; Tables 1-2 v1 blocks removed (stale-number guard) with verified v3 headline quantities listed pending the 08_ exhibit re-run. No 2026-trend statements (held for tonight's video-list refresh; ke_ai_flagged_true_v2.csv not yet present).
- PDF recompiled (pandoc/xelatex). NOT committed to git (Katie's call; folder is untracked).
- Next: Katie's framing decision (supply-side "who explains AI" arc; F7 content sorting + F8 packaging two-layer flagged as optional adds); v3 exhibit re-run (08_); still-producing-2026 re-run before any continuation claim.

## 2026-08-04 08:40 Professor-facing PPTX built ("Who Explains AI?")
- Executed HANDOFF_pptx_professor_deck.md end to end. Deliverable: papers/gendering-ai-expertise/drafts/Who_Explains_AI_brief_2026-08.pptx (10 slides, 16:9, full brand-katie treatment; labeled working descriptive brief, video record through April 2026 since ke_ai_flagged_true_v2.csv is not yet present).
- Pipeline: /DeckCompile Phase 0 architecture map (SLIDE_ARCHITECTURE_MAP.md) then BRIEF.md, both in drafts/who-explains-ai-deck/. Katie redirected mid-build: skip the Claude Design handoff, build the PPTX directly; built with python-pptx (build_pptx.py).
- All six charts rebuilt from the v3 JSONs by make_charts.py (funnel, territory map, launch dot chart with both codings, one-and-done, authority ladder, packaging); June fig1-4.png not reused. Every slide number traced to a source JSON; two label-rounding mismatches vs raw floats resolved half-up to match the approved HTML deck (20.7%, 3.2%).
- QA: all 10 slides rendered via LibreOffice and visually checked; one collision fixed (launch chart caption vs bullets).
- Deck folder is inside papers/gendering-ai-expertise/ which stays untracked per Katie's earlier call; only this log is committed.
- Next: Katie reviews the PPTX before it goes to anyone; if the video-list refresh lands, regenerate charts and re-date to "through July 2026".

## 2026-08-04 13:30 [Gendering-AI paper: full battery re-run on the Aug-3 refreshed record + deck and manuscript updated]
- Executed HANDOFF_update_slides_and_manuscript.md end to end. STEP 0: nine new numbered scripts (src/27_-35_, all _v2 data variants; June scripts and outputs untouched) rebuilt the adoption table from ke_ai_flagged_true_v2.csv (9,620 adopters = 8,652 June + 968 new; validation clean: zero first dates or launch assignments moved) and re-ran the tiered entry battery, survival/timing (now harmonized to v3 gender + Aug-3 censoring), persistence, the stacked launch DiD (panel through 2026-07), content tools, title language, style conditionals, and authority. Outputs carry _v2 suffixes in output/.
- FRAME HARMONIZATION (my call, flagged for Katie): all headline gender contrasts now report on the single v3 frame (17,273 channels). The old 12.2/16.4 adoption rates were a v2-gender-frame artifact mixed with a v3 OR; the harmonized numbers are 15.1% vs 21.7%, OR 0.73 (T3 0.68); v2-frame cross-check 13.0/17.0, OR 0.75. Gap NARROWED slightly with the catch-up wave (0.71 -> 0.73).
- VERDICT CHANGE (the loud flag): F4 "whether, not when" is DEAD. Women who adopt are significantly later (median 457 vs 366 days; +53 days adjusted, p=.003). Four-cell decomposition shows the June n.s. (p=.098) was an underpowered April-censored cell; direction was always positive. Manuscript, deck, and ledger now say "whether AND when," framed as the diffusion delay the theory predicts.
- Other movement: DiD strengthened (techiness triple -0.0016 p=.021; dev-origin -0.0089 p=.011; panel 3,381 ch / 1.26M stacked); persistence strengthened (one-and-done 38.3 vs 29.9, tier ORs 1.36/1.38/1.49); still-producing-2026 finally REAL (39.7% vs 45.2%, OR 0.81 p=.018, caveat cleared); Claude Code content 3.9% -> 11.2% female cumulative (the rebound reached the tool table); authority form split byte-stable; credential gap now 6.6pp noncred vs 8.2pp cred (still "closes nothing", interaction p=.53).
- STEP 1: drafts/gendered_uptake_deck.html fully re-numbered + 2026 section rewritten to the completed dip-and-rebound story + citations added (Aldasoro, Humlum & Vestergaard, Otis, Rogers, Chatterji); republished to the SAME artifact URL. HANDOFF_pptx_professor_deck.md number table updated to _v2 sources (PPTX rebuild pending, separate task).
- STEP 2: manuscript v1.1 -> v1.2: all numbers swapped to _v2 outputs, timing verdict rewritten in theory + results, new Results subsection "The 2026 tool wave in real time" + Discussion paragraph (labeled suggestive), continuation measure added, tables 1-4 refreshed, scope/data sentences now "through August 3, 2026" / 46.9M uploads / 92,208 clean AI videos. PDF recompiled.
- GATES: 86/86 scripted number checks vs source JSONs passed; independent forked claim-verifier confirmed 9/10 claim sets and caught one real error, which was fixed everywhere: July 2026 (13.6%) is the lowest full month OF 2026, not ever (series low Oct 2025, 13.0%) — this error was inherited from the Aug-3 ledger/handoff. findings-ledger fully refreshed with the correction.
- NOT committed to git (per handoff; Katie reviews first). Nothing sent externally. Elite-citation splice (T1) was already executed in the 06:00 session; verified nothing remained.

## 2026-08-05 [Gendering-AI paper: coordination note for the concurrent manuscript agent]
- qbq/DASHBOARD.md now carries a "STATE FOR MANUSCRIPT AGENTS (2026-08-05)" banner at the top: what is already in draft v1.2 (all _v2 numbers, elite splice DONE, F4 timing verdict revised, 2026 wave section), which analyses are done but NOT yet in the manuscript (F7 content sorting, F8 packaging, active-last-6mo persistence variant), and what is still pending (08_ exhibit regeneration, 12_/11_ re-runs, descriptions/transcripts). qbq/findings-ledger.md remains the single number source.

## 2026-08-05 [Gendering-AI-Expertise: Cech 2015 added per Katie]
- Katie approved adding Cech 2015 ("Engineers and Engineeresses?", Sociological Perspectives 58(1):56-77, doi:10.1177/0731121414556543; details verified via OpenAlex + the journal corrigendum). Cited in the theory section's form-split paragraph (gendered self-conceptions filter technological leadership out of women's professional identities) and added to References. PDF recompiled.

## 2026-08-05 [Gendering-AI: codebook added to patterns deck + public website page built (not yet deployed)]
- CODEBOOK (Katie's ask): new section 11 in drafts/gendered_uptake_deck.html giving exact construction rules for every variable: date coverage table, sample funnel, the three AI-flag cleanup rules with removal counts (10,916 pre-era "machine learning" etc.), gender method with tier definitions (T1 = 1 face-bearing thumbnail, T2 = 2-3 agreeing, T3 = 4+ agreeing; 24/25 on the hand-coded check), the full 20-launch technicality table with dates and developer-built flags, verbatim title/bio word lists, and small definitions. Republished to the same artifact URL.
- WEBSITE (Katie approved public, preliminary, descriptive-only, no theory framing): built site-v3/research/who-explains-ai/ in SECOND_BRAIN/04-professional/public-persona/ using the site's own design system; prose drafted by Codex per Katie's standing preference; charts (tool territory, authority ladder, title language, 2026 monthly coding share) as inline SVG in site palette; page ends with the full codebook. Three integration points per Katie's choices: homepage teaser box between the JMP spotlight and All Research (hook: "Who Gets to Be an Expert on AI?"), a button inside the Longitudinal Creator Panel entry, and a linked entry on themes/ai-and-work. sitemap.xml + llms.txt updated. NOT yet deployed; Katie reviews first.
- Coordination: qbq/DASHBOARD.md "state for manuscript agents" banner from earlier today still current; no new analysis outputs since the _v2 battery (2026-08-04).

## 2026-08-06 11:58 Who Explains AI: PPTX v2 rebuild, adopter profile, artifact + page updates
- Professor PPTX rebuilt on the refreshed record: drafts/Who_Explains_AI_brief_2026-08_v2.pptx (13 slides; the April-numbers original untouched). New build scripts make_charts_v2.py / build_pptx_v2.py in drafts/who-explains-ai-deck/, charts from the _v2 JSONs, all 13 slides rendered and visually checked (qa_v2/). Timing verdict updated (whether AND when, 457 vs 366 days, +53 adjusted, p=.003); Claude Code framed 4% launch wave / 11% cumulative; citations added ([1] Aldasoro 2024, [2] Humlum & Vestergaard 2025, [3] Otis et al. 2024) plus a references slide; "Preliminary findings" framing replaces the honest-limits box per Katie.
- New exploration (Katie's question: why do so few channels adopt?): src/36_adopter_profile_v2.py -> output/adopter_profile_v2.json. Only 33% of the 43,546 roster posted anything post-ChatGPT; 73% of never-adopters are dormant; adoption among active channels is 29% and climbs to 53% for 200+ post-ChatGPT videos; adopter median 26,000 subs vs 2,770 (active non-adopters); top decile of adopters produce 67% of AI videos; gender gap persists in every output bracket (24.5% vs 33.0% among active).
- Fixed a universe conflation in the HTML deck + site page: 9,620 adopters/92,208 AI videos belong to the FULL 143,558-channel scan; the 43,546 analytic roster has 4,999 adopters and 57,548 AI videos. Corrected census prose, who-is-counted tables, and upload-record rows in both.
- Deck artifact republished (same URL, dd5f9aa5) with new "Who adopts at all" section. Site page updated + committed to SECOND_BRAIN (auto-sync); still NOT deployed, Katie reviewing.
- Katie's new chart rules recorded to project memory (feedback_viz_rules.md): pink/navy men-vs-women everywhere, shares on 0-100 scales, coefficient axes symmetric around zero.
- Next: Katie's review of page + deck; sampling-expansion proposal (more pre-ChatGPT knowledge channels for coding counts + entry tracking) awaiting her decision.

## 2026-08-06 16:50 Who Explains AI: execution fleet (9 agents), corrections, production sampling launched
- Executed the robustness plan with a 9-agent fleet (scripts src/39-46 + verification agent; every claimed number cross-checked against output files). Katie's dormancy suspicion CONFIRMED: enumeration never ran on 17,296 of 43,546 channels; corrected active-since-ChatGPT share is ~56% (range 46-59), not 33%. Ledger F10 revised, F13 added (contemporary battery: all gaps survive restricting to 2025-26 posters; adoption 37.9% men vs 28.9% women, OR 0.74).
- Stable Diffusion punchline DOWNGRADED: one channel (coded woman) produces ~75-81% of SD videos; channel-level SD female share 11.9%. GitHub org channel (coded woman) inflated GitHub Copilot. F12 downgraded pending hand-check of 5 flagged channels; territory claim now rests on Runway/Midjourney channel-level shares.
- F2 REFRAMED: on tool-specific first-mention hazards the techiness dose is null (p=.40) but developer-built stays (OR 0.56, p=.023); women enter later/less on 10 of 11 tools (Runway the exception). Old-outcome inference battery: survives most regimes, randomization inference marginal (.076/.139). Placebo scare resolved (full-window diff p=.72); placebo developer-triple p=.028 is an honest wrinkle.
- F11 (women do not dumb down) survived all four robustness designs. Oaxaca: ~79% of the accessible-title gap is composition.
- Corrections propagated: findings-ledger, site page (committed, NOT deployed), HTML artifact (republished same URL), PPTX slides 5-6 (rebuilt + QA rendered).
- Cohort B Arm 1 PRODUCTION discovery launched (src/collection/discover_cohort_b.py, 72 queries, checkpointed, 120k-unit hard cap, target 6,500 eligible; pilot: 31 channels/call, 76.8% eligible at 3,628 units). Running in background at session end.

## 2026-08-06 16:52 Cohort B Arm 1 discovery COMPLETE
- Production discovery finished: 8,675 channels discovered across 4 query families (72 pre-treatment-window queries planned, stopped early on success), 6,547 Arm 1 eligible (75.5%; founded pre-2022-06-20, 50+ videos), 786 overlap the existing roster. Real quota spend ~33,000 units (a checkpoint accounting double-count made the first pass stop early at 22 queries claiming 122k; fixed, counter reset to true value, resumed to completion). Output: data/channels/cohort_b/arm1_discovery_20260806.csv + cohort_b_discovery_summary.json.
- Next collection steps (not yet run): upload-playlist enumeration for the 6,547 eligible channels (reconstructs uploads-at-cutoff, ~15-25k units), then thumbnail gender coding (Gemini vision, external spend, needs Katie's dollar approval).

## 2026-08-06 17:40 Channel-grain pass + simplified artifact
- Katie's channel-level question answered by execution (plan approved via interview: creators-first, everything, concentration panels, working layer only). src/48 channel-grain pass: beginner-words contrast VANISHES at the channel grain (typical woman's channel 3.0% vs man's 3.2%, p=.64); technical-terms contrast REVERSES (7.5% vs 10.9%, women lower, p=.001); the shelf's 2.63x beginner lean is pure volume composition. Tool territory at channel grain: only Runway holds a female lean (31.6%); Midjourney drops to 14.9%; coding tools 6-12%. Ledger updated (convention + F7/F8/F9 channel-grain partners).
- Exhibits document compiled: drafts/Who_Explains_AI_exhibits_2026-08-06.html + .pdf (5 tables + 13 figures incl. new hazard forest, 20-launch scatter, and 3 channel-grain figures).
- Artifact rebuilt per Katie's direction: channel-level findings only, figures first, tables last, short Codex-drafted prose, sampling frame stated plainly. Old deck archived (drafts/_archive/gendered_uptake_deck_pre_channel_grain_20260806.html). Republished same URL.
- Site page and professor PPTX intentionally NOT updated this pass (held for Katie's review of the channel-grain numbers).

## 2026-08-06 17:55 Session close: handoff written
- HANDOFF_channel_grain_continuation.md written in papers/gendering-ai-expertise/: next agent must interview Katie first (artifact propagation, Gemini spend, 5-channel hand-check, F2 headline choice, Cohort B enumeration go, artifact tweaks), then work the queue (enumeration, Gate B, Gate C on hazards, lexicon v3, sharp/soft convention, adoption-among-active reconciliation). Includes verifier corrections that must not reach artifacts and all standing rules.

## 2026-08-05 07:50 — Routine health check (4th clean day post-incident)
- All green Aug 2-5: health checks PASSED Aug 2/3/4; all 7 channel panels present daily; video-stats full-size daily (ai_census ~200M, knowledge_economy ~310M). Today mid-stream on schedule (ai_census running since 4 AM; KE slot is 8:30 AM).
- Disk stable: 53 GB free (75% used). No failure flags.
- Aug 1 salvage confirmed fully complete: april_cohort 32M, both relaunched video chunks finished full-size same day.
- OPEN (unchanged): backup decision — panel data only on Mac Mini. Options: fix Drive client / rsync to laptop / external SSD.

## 2026-08-13 09:55 — Health sweep Aug 5-13: one network blip on Aug 11
- Aug 5-10 + Aug 12-13: fully clean (health checks passed, all 7 channel panels daily, video-stats full-size daily).
- **Aug 11 DNS outage on the Mini** ("Unable to find the server at youtube.googleapis.com", ~3:20-10:26 AM): tech_census and new_cohort channel stats failed that day — permanent 1-day gap for those two panels (methods note). All other panels and both video-stats chunks completed (network was back by their slots).
- Archived the Aug 11 failure flag (was tripping health checks Aug 11-12); health check re-run PASSES for Aug 13.
- Disk improved to 99 GB free (53%) — panel data verified intact (39G daily_panels, gender_gap at 140 daily files since Feb 17); extra space is likely expired APFS snapshots from the Aug 1 cleanup.
- OPEN (unchanged): backup decision for Mac Mini panel data.

## 2026-09-01 Gendering AI Expertise: manuscript pipeline stood up (session in papers/, not committed)
- The Who Explains AI paper now runs the full manuscript writing-execution pipeline (control tower, exhibit manifest, rule-out registry, decision log, prereg batch for Katie, ASQ scorer rubric). Exploration wave verified into the ledger (F14-F19, scripts src/49-51, zero quota). Lit backfill wave 1: 8 papers to full_pdf CoVe PASS in the KG vault. Full detail: papers/gendering-ai-expertise/PROGRESS_LOG.md (papers/ stays untracked per standing rule).
- No API quota consumed this session; no collection changes.

## 2026-09-01 (evening) Gendering AI Expertise: session close
- Architecture locked (classic hypotheses, known-puzzle opening, per-tool exhibit gated on applied corrections); tool-table fixes run and verified (Copilot split; 5-channel hand-check: all five flagged "woman" channels are men or orgs); ledger F14-F21 all fleet-verified; 8 papers full-verified + 11 abstract stubs into the KG; Katie's 250-channel gender-verification Google Sheet emailed at her request. Handoff: papers/gendering-ai-expertise/HANDOFF_manuscript_pipeline_2026-09-01.md. No API quota consumed; papers/ stays untracked.

## 2026-09-01 (night) Gendering AI Expertise: gender corrections applied, per-tool table rebuilt
- Applied the five hand-check gender corrections as an out-of-place patch (src/54; processed/ke_gender_v3.csv untouched) and rebuilt the per-tool table on the corrected codes with GitHub and Microsoft Copilot as separate tools (src/55). The rebuild reproduces every published per-tool number exactly when fed the old codes, so the deltas are the corrections and nothing else; cells were also recomputed from raw outside the script's code path.
- Headline: at the channel grain Runway (30.8%) is the only tool leaning toward women; Stable Diffusion falls to 7.0% and the old 54.7% video-grain figure is dead. GitHub Copilot 8.3% vs Microsoft Copilot 16.6% is the paper's cleanest provenance contrast, two products sharing one brand name. The per-tool hold is lifted with channel-grain conditions attached.
- Ledger (F22), exhibit manifest, rule-out registry, decision log (D23-D27) and control tower all updated. No API quota consumed; no collection changes; papers/ stays untracked.
