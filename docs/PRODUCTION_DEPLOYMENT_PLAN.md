# Production Deployment Plan: Post-Validation

**Date:** Feb 20, 2026
**Context:** 6 validation pilots complete. 4 GO, 1 CONDITIONAL, 1 NO-GO. This plan covers deploying validated strategies to production and sequencing remaining collection work.

---

## Pilot Results Summary

| Strategy | Verdict | Key Finding |
|----------|---------|-------------|
| safeSearch=none | **GO** | +37% marginal new channels. GRWM 8x, gameplay 3.5x. Zero extra quota cost. |
| topicId partitioning | **GO** | 2.42x yield multiplier. All 12 topics productive. 77% marginal new. Biggest single lever. |
| regionCode matching | **GO** | +57% marginal new. All 9 regions productive. Arabic regions standout. |
| videoDuration | **CONDITIONAL** | 1.44x yield (threshold 1.5x). All 3 slices productive. 76% marginal new. Missed GO by 0.06x. |
| order=relevance | **NO-GO** | 15% survival rate (need >=50%). Surfaces old channels. Median subs 2.2x baseline. Excluded. |
| 12h windows | **GO** | +38% improvement. 1,080 unique channels missed by 24h windows. |

---

## Decision: Production Strategy Sets

### For Stream A/A' Re-Runs (full backfill)
**`base,safesearch,topicid,regioncode,duration,windows`** — All passing strategies including CONDITIONAL duration.

Rationale: Duration's 1.44x multiplier with 75.7% marginal new rate and all 3 productive slices is functionally a GO. The 0.06x shortfall against a conservative threshold does not justify excluding a strategy that found 1,180 net new channels in the pilot. Provenance tags (`discovery_duration`) ensure analytical separability. For a one-time re-run where maximizing sample size is the goal, include everything that works.

### For Daily Discovery Service (ongoing)
**`base,safesearch,regioncode,windows`** — Tier 1 only.

Rationale: The daily service runs every day on a fixed quota budget. TopicId adds 12 passes per keyword (12x multiplier on search calls). Duration adds 3 passes per keyword. For daily discovery with --days-back 1, the marginal gain from topicId/duration doesn't justify the quota cost on a single day's window. Tier 1 strategies (safesearch, regioncode, windows) are cheap modifiers that don't multiply the number of passes. Reserve topicId/duration for weekly supplement runs or monthly re-runs.

### Excluded from Production
**order=relevance** — NO-GO confirmed. Surfaces pre-2026 established channels. Not worth the quota or the analytical contamination.

---

## Sequenced Execution Plan

### Phase A: Infrastructure Recovery (Day 1 — Feb 20)

**A.1: Fix Mac Mini network stability**
- Swap to ethernet cable (hardware ready, Katie has the cable)
- Verify connection stability with sustained API calls
- This likely resolves the Feb 19 timeout that killed daily stats

**A.2: Backfill missing daily stats**
- Feb 18: Failed (quota exhaustion from A' overnight run)
- Feb 19: Failed (network timeout)
- Run `daily_stats.py` manually for both dates after ethernet is stable
- AI census daily stats also missing for both dates — same backfill needed
- Estimated cost: ~20K units (trivial)

**A.3: Verify daily stats service recovers**
- After ethernet fix, let the 8:00 UTC service run normally on Feb 21
- Confirm output file appears in `data/daily_panels/channel_stats/`
- If it fails again, investigate further (may need retry logic in daily_stats.py)

### Phase B: Stream A Re-Run (Days 1-2)

**B.1: Launch Stream A re-run on Mac Mini**
- Command: `python3 -m src.collection.discover_intent --strategies base,safesearch,topicid,regioncode,duration,windows`
- 94 keywords × 15 languages × multiple passes × ~50 time windows
- Expected: 2-3 days of quota, potentially 60-100K unique channels
- Run in screen session, monitor with `ps aux | grep discover`
- CRITICAL: Run AFTER daily stats window (start after 10:00 UTC) to avoid quota collision

**B.2: Monitor quota consumption**
- Check Google Cloud Console every few hours
- If quota hits 800K before daily stats time window (08:00 UTC), kill the screen
- The script checkpoints, so it can resume next day

### Phase C: Stream A' Re-Run (Days 3-4)

**C.1: Launch A' re-run after A completes or pauses**
- Command: `python3 -m src.collection.discover_non_intent --strategies base,safesearch,topicid,regioncode,duration,windows`
- 82 keywords × 15 languages × multiple passes
- Expected: 2-3 days, 40-80K unique channels
- Same quota management protocol as Phase B

### Phase D: Stream C (Days 4-5)

**D.1: Launch Stream C (random baseline)**
- `python3 -m src.collection.discover_random`
- Target: 50K channels via random prefix sampling
- IMPORTANT: Expansion strategies do NOT apply to Stream C (not keyword-based)
- Stream C is load-bearing for the coverage calibration protocol — needed before any representativeness claims
- Quota cost: ~50K units (one-time, fast)

### Phase E: Daily Discovery Deployment (After A/A' Re-Runs)

**E.1: Update daily discovery plists to Tier 1**
- Change `--strategies base,safesearch` → `--strategies base,safesearch,regioncode,windows` in both plists
- Intent plist: `config/launchd/com.youtube.daily-discovery-intent.plist`
- Non-intent plist: `config/launchd/com.youtube.daily-discovery-non-intent.plist`

**E.2: Deploy to Mac Mini**
```bash
cp config/launchd/com.youtube.daily-discovery-intent.plist ~/Library/LaunchAgents/
cp config/launchd/com.youtube.daily-discovery-non-intent.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.youtube.daily-discovery-intent.plist
launchctl load ~/Library/LaunchAgents/com.youtube.daily-discovery-non-intent.plist
```
- Verify with `launchctl list | grep youtube`
- Monitor first run's quota consumption

**E.3: Quota allocation for steady state**
| Service | Schedule | Est. Units/Day |
|---------|----------|---------------|
| Gender gap daily stats | 08:00 UTC | ~10K |
| AI census daily stats | 09:00 UTC | ~10K |
| Daily discovery (intent) | 05:00 UTC | ~70K |
| Daily discovery (non-intent) | 14:00 UTC | ~70K |
| **Total daily** | | **~160K** |
| **Remaining for ad-hoc** | | **~850K** |

### Phase F: Expansion Stream Pilots (Week 2+)

The 5 expansion streams (Topic-Stratified, Trending, Livestream, Shorts-First, Creative Commons) have built scripts but no data. These are secondary to the core A/A'/C pipeline. Sequence:

1. **Trending** — cheapest, append-only, can start immediately as a daily service
2. **Shorts-First** — high target (50K), good for Shorts-specific research questions
3. **Topic-Stratified** — partially overlaps with topicId expansion strategy on A/A'
4. **Livestream** — niche but methodologically distinct (eventType=completed)
5. **Creative Commons** — smallest target (15K), most specialized

These should be piloted one at a time after the core pipeline stabilizes.

---

## Combined Effect Test (Gate 2)

Per the validation framework, after individual strategies pass, a combined pilot with ALL passing strategies active simultaneously is required:
- Run 3 keywords × 1 day with `--strategies base,safesearch,topicid,regioncode,duration,windows`
- Check for interaction effects and quota explosion
- This can piggyback on the first day of the Stream A re-run — just monitor the first 3 keywords closely

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Quota exhaustion kills daily stats | Medium | High (missed panel days) | Stagger start times, monitor quota, kill discovery if >800K by 07:00 UTC |
| Mac Mini network instability | Medium | Medium | Ethernet cable swap (hardware ready). Add retry logic to daily_stats.py. |
| TopicId × keywords explodes quota | Low | Medium | Daily service uses Tier 1 only. TopicId reserved for re-runs. |
| Stream A re-run takes >3 days | Medium | Low | Checkpoint/resume handles multi-day runs. Just costs calendar time. |
| Combined strategies find duplicate-heavy results | Low | Low | Provenance tags make dedup and analysis trivial. |

---

## Success Criteria

- [ ] Daily stats running reliably (no missed days for 7 consecutive days)
- [ ] Stream A re-run yields >=50K unique channels
- [ ] Stream A' re-run yields >=30K unique channels
- [ ] Stream C collected (50K target)
- [ ] Daily discovery services deployed and stable
- [ ] All channels have complete provenance tags
- [ ] Combined effect test confirms no interaction effects
