# Expansion Strategy Implementation Plan

## Context

The YouTube discovery scripts (`discover_intent.py`, `discover_non_intent.py`) currently search with a single strategy: `order=date` per keyword per time window. This hits the ~500-result-per-query ceiling, capping Stream A at 26K and A' at 11K unique channels. Six expansion strategies were evaluated by a 5-expert API panel and a 3-round academic /plan-eval (scoring 81.5/100). These strategies break the ceiling by adding orthogonal search dimensions. This plan implements all six strategies in the discovery scripts, adds `--days-back` for the daily discovery service, and builds the validation pilot script.

## Files to Modify

1. **`src/config.py`** — Add config constants and schema updates
2. **`src/collection/discover_intent.py`** — Expansion strategies + `--days-back`
3. **`src/collection/discover_non_intent.py`** — Same changes (scripts are near-identical)
4. **`src/validation/validate_expansion.py`** — New file: validation pilot script

## Design Decisions

### Strategy categorization

The 6 strategies fall into 3 types that get handled differently in the search loop:

| Type | Strategy | How it works |
|------|----------|-------------|
| **Global param swap** | safeSearch=none | Applied to ALL searches. Not a separate pass. |
| **Additive passes** | topicId, regionCode, videoDuration | Each creates additional searches per keyword×window |
| **Conditional pass** | order=relevance | Only re-runs queries that hit the ~500-result cap |
| **Window modification** | 12h windows (A' only) | Changes window generation, not search params |

### Search loop architecture

Current loop:
```
for keyword in keywords:
  for window in windows:
    search(keyword, window, order=date)
```

New loop:
```
for keyword in keywords:
  for search_pass in generate_search_passes(keyword, language, enabled_strategies):
    for window in windows:
      search(keyword, window, safeSearch=none, **search_pass.params)
      → tag channels with search_pass.provenance
```

A "search pass" is a named combination of API parameters. For a single keyword with all strategies enabled:
- **base**: `{order: date}` — the existing search, now with safeSearch=none
- **topicid_Music**: `{order: date, topicId: /m/04rlf}` — one pass per topic (12 topics)
- **regioncode_MX**: `{order: date, regionCode: MX}` — one pass per mapped region
- **duration_short**: `{order: date, videoDuration: short}` — one per duration (3)
- **relevance**: `{order: relevance}` — only if base pass was capped

### Checkpoint granularity

Keep keyword-level checkpoints (current behavior). Within a keyword, iterate through search passes. If interrupted mid-keyword, the global `seen_channel_ids` set prevents duplicate channel writes on resume. The cost of re-running a few API calls for one keyword is negligible vs. the complexity of sub-keyword checkpointing.

**Change:** Checkpoint key becomes `keyword|language|pass_name` so that completed passes within a keyword are skipped on resume. This is finer-grained than today's `keyword|language` key but avoids wasted API calls.

### Strategy enablement (CLI)

New flag: `--strategies base,safesearch,regioncode,topicid,duration,relevance,windows`
- Default: `base,safesearch` (minimal, Tier 1 base)
- Tier 1 production: `base,safesearch,regioncode,windows`
- Tier 2 production: `base,safesearch,regioncode,topicid,duration,windows`
- Tier 3 (sensitivity): all six

`safeSearch=none` is applied whenever `safesearch` is in the strategy list (modifies ALL calls, not a separate pass).

### Page depth per pass

Additive passes (topicId, regionCode, duration) use fewer pages than the base pass to save quota:
- Base pass: `max_pages=10` (current default)
- Additive passes: `max_pages=5` (each pass targets different result sets, deep pagination less useful)
- Relevance pass: `max_pages=5` (only run on capped queries)

---

## Step 1: config.py additions

### 1a. DISCOVERY_TOPIC_IDS (12 topics)

```python
DISCOVERY_TOPIC_IDS: Dict[str, str] = {
    "/m/04rlf": "Music",
    "/m/0bzvm2": "Gaming",
    "/m/02jjt": "Entertainment",
    "/m/019_rr": "Lifestyle",
    "/m/07c1v": "Technology",
    "/m/01k8wb": "Knowledge",
    "/m/098wr": "Society",
    "/m/06ntj": "Sports",
    "/m/09kqc": "Humor",
    "/m/027x7n": "Fitness",
    "/m/02wbm": "Food",
    "/m/05qjc": "Performing arts",
}
```

These are the 12 highest-coverage parent topics from the existing `YOUTUBE_PARENT_TOPICS` mapping.

### 1b. LANGUAGE_REGION_MAP (15 languages → 23 regions)

```python
LANGUAGE_REGION_MAP: Dict[str, List[str]] = {
    "Hindi": ["IN"],
    "English": ["US", "GB", "AU"],
    "Spanish": ["MX", "ES", "AR", "CO"],
    "Japanese": ["JP"],
    "German": ["DE", "AT"],
    "Portuguese": ["BR", "PT"],
    "Korean": ["KR"],
    "French": ["FR"],
    "Arabic": ["SA", "EG"],
    "Russian": ["RU"],
    "Indonesian": ["ID"],
    "Turkish": ["TR"],
    "Vietnamese": ["VN"],
    "Thai": ["TH"],
    "Bengali": ["BD"],
}
```

### 1c. EXPANSION_STRATEGIES constant

```python
# Valid expansion strategy names
EXPANSION_STRATEGIES = {"base", "safesearch", "regioncode", "topicid", "duration", "relevance", "windows"}
DEFAULT_STRATEGIES = {"base", "safesearch"}
```

### 1d. New provenance fields in CHANNEL_INITIAL_FIELDS

Add 8 fields after `expansion_wave` and before `scraped_at`:
```python
"discovery_method",        # base, topicid, regioncode, duration, relevance
"discovery_topic_id",      # /m/04rlf etc. (topicId strategy only)
"discovery_topic_name",    # Music, Gaming etc. (topicId strategy only)
"discovery_region_code",   # MX, BR etc. (regionCode strategy only)
"discovery_order",         # date, relevance
"discovery_safesearch",    # moderate, none
"discovery_duration",      # any, short, medium, long
"discovery_window_hours",  # 24, 12
```

### 1e. DISCOVERY_DURATIONS constant

```python
DISCOVERY_DURATIONS: List[str] = ["short", "medium", "long"]
```

---

## Step 2: discover_intent.py changes

### 2a. New CLI arguments

```python
parser.add_argument('--days-back', type=int, default=None,
                    help='Only search the last N days (for daily discovery service)')
parser.add_argument('--strategies', type=str, default='base,safesearch',
                    help='Comma-separated expansion strategies to use')
```

### 2b. Modify generate_time_windows()

Add `days_back` parameter:
```python
def generate_time_windows(window_hours: int = 24, days_back: int = None) -> List[tuple]:
    now = datetime.utcnow()
    if days_back is not None:
        cutoff = now - timedelta(days=days_back)
    else:
        cutoff = datetime.fromisoformat(config.COHORT_CUTOFF_DATE)
    # ... rest unchanged
```

### 2c. New function: generate_search_passes()

```python
def generate_search_passes(
    keyword: str,
    language: str,
    strategies: Set[str],
) -> List[Dict]:
    """
    Generate search pass configurations for a keyword.

    Each pass is a dict with:
      - name: str (unique pass identifier)
      - extra_params: dict (API params beyond the base query)
      - provenance: dict (fields to tag on discovered channels)
    """
    passes = []
    use_safesearch_none = "safesearch" in strategies
    safe_val = "none" if use_safesearch_none else "moderate"

    # Base pass (always runs)
    passes.append({
        "name": "base",
        "extra_params": {"safeSearch": safe_val},
        "provenance": {
            "discovery_method": "base",
            "discovery_order": "date",
            "discovery_safesearch": safe_val,
            "discovery_duration": "any",
        },
        "max_pages": 10,
    })

    # topicId passes
    if "topicid" in strategies:
        for topic_id, topic_name in config.DISCOVERY_TOPIC_IDS.items():
            passes.append({
                "name": f"topicid:{topic_id}",
                "extra_params": {"safeSearch": safe_val, "topicId": topic_id},
                "provenance": {
                    "discovery_method": "topicid",
                    "discovery_topic_id": topic_id,
                    "discovery_topic_name": topic_name,
                    "discovery_order": "date",
                    "discovery_safesearch": safe_val,
                    "discovery_duration": "any",
                },
                "max_pages": 5,
            })

    # regionCode passes
    if "regioncode" in strategies:
        regions = config.LANGUAGE_REGION_MAP.get(language, [])
        for region in regions:
            passes.append({
                "name": f"regioncode:{region}",
                "extra_params": {"safeSearch": safe_val, "regionCode": region},
                "provenance": {
                    "discovery_method": "regioncode",
                    "discovery_region_code": region,
                    "discovery_order": "date",
                    "discovery_safesearch": safe_val,
                    "discovery_duration": "any",
                },
                "max_pages": 5,
            })

    # videoDuration passes
    if "duration" in strategies:
        for dur in config.DISCOVERY_DURATIONS:
            passes.append({
                "name": f"duration:{dur}",
                "extra_params": {"safeSearch": safe_val, "videoDuration": dur},
                "provenance": {
                    "discovery_method": "duration",
                    "discovery_duration": dur,
                    "discovery_order": "date",
                    "discovery_safesearch": safe_val,
                },
                "max_pages": 5,
            })

    # relevance second pass (runs after base, only on capped queries)
    # This is handled separately in the main loop — not generated here.
    # See the "relevance pass" section in the main loop.

    return passes
```

### 2d. Modified main discovery loop

The inner loop changes from a simple window iteration to a pass × window iteration:

```python
for idx, (keyword, language) in enumerate(intent_keywords):
    # ... existing target/skip checks ...

    search_passes = generate_search_passes(keyword, language, strategies)
    capped_windows = set()  # track which windows hit the result cap

    for search_pass in search_passes:
        pass_key = f"{keyword}|{language}|{search_pass['name']}"
        if pass_key in completed_keywords:
            continue

        batch_new_channels = []

        for window_start, window_end in time_windows:
            # ... existing search call, but using search_pass['extra_params'] ...
            # ... search_pass['max_pages'] instead of hardcoded 10 ...

            # Track capped queries for relevance pass
            if search_pass['name'] == 'base' and len(search_results) >= search_pass['max_pages'] * 50:
                capped_windows.add((window_start, window_end))

            # Tag channels with provenance
            for channel in new_channels:
                channel.update(search_pass['provenance'])
                channel['discovery_window_hours'] = window_hours

        # Append batch to CSV + checkpoint after each pass
        completed_keywords.add(pass_key)
        save_checkpoint(...)

    # Relevance second pass (Tier 3, conditional on capped queries)
    if "relevance" in strategies and capped_windows:
        pass_key = f"{keyword}|{language}|relevance"
        if pass_key not in completed_keywords:
            for window_start, window_end in capped_windows:
                # ... search with order=relevance ...
                # Tag: discovery_method=relevance, discovery_order=relevance
            completed_keywords.add(pass_key)
            save_checkpoint(...)
```

### 2e. Window modification for 12h (A' only, handled in discover_non_intent.py)

In `discover_non_intent.py`, when `"windows"` is in strategies, detect capped keywords and re-run them with 12h windows. Implementation: after the base pass for a keyword, if >50% of windows were capped, re-run the entire keyword with 12h windows as an additional pass.

---

## Step 3: discover_non_intent.py changes

Same as Step 2, except:
- Uses `NON_INTENT_KEYWORDS`
- Stream type = `stream_a_prime`
- The `"windows"` strategy adds 12h window re-runs (A'-specific)
- Includes the existing `--exclude-list` arg for cross-dedup

---

## Step 4: validate_expansion.py (new file)

Location: `src/validation/validate_expansion.py`

Key features per the EXPANSION_VALIDATION_FRAMEWORK.md:
- `--strategy {safesearch,topicid,regioncode,duration,relevance,windows}` flag
- `--keywords` to override default test keywords
- `--dry-run` to estimate API cost
- Runs baseline + strategy variant for test keywords × 1 window
- Computes M1-M5 metrics (yield, quality, overlap, marginal new, diminishing returns)
- Writes results to `data/validation/expansion_pilots/{strategy}_{date}.csv`
- Prints summary table with GO/NO-GO verdict
- ~500-13,500 units per strategy (all 6 fit in 70K units, ~7% daily quota)

---

## Step 5: Backward compatibility

- `--strategies base,safesearch` (the default) produces identical behavior to the current scripts except safeSearch changes from moderate to none. No new passes, no extra quota.
- All new provenance fields default to sensible values ("base", "date", "none"/"moderate", "any", 24)
- Checkpoint format change: old checkpoints use `keyword|language` keys. New code checks for both old-format and new-format keys, so an interrupted old run can resume.
- Output CSV schema gains 8 new columns. Old CSVs lack these columns. The DictWriter handles this gracefully (missing fields → empty).

---

## Verification

1. **Syntax check:** `python -c "from src import config"` — confirms config.py imports
2. **Keyword count verification:** `python -c "from src.config import verify_keyword_counts; verify_keyword_counts()"` — confirms no keywords were lost
3. **Schema check:** Verify CHANNEL_INITIAL_FIELDS has the 8 new provenance fields
4. **Dry run:** `python -m src.collection.discover_intent --test --limit 5 --strategies base,safesearch` — should behave like current script
5. **Expansion dry run:** `python -m src.collection.discover_intent --test --limit 5 --strategies base,safesearch,topicid` — should run base + 12 topic passes
6. **Days-back test:** `python -m src.collection.discover_intent --test --limit 5 --days-back 1` — should only search yesterday
7. **Validation pilot:** `python -m src.validation.validate_expansion --strategy safesearch --dry-run` — should print estimated cost
8. **Python 3.9 compat:** No walrus operators, no `str | None` union syntax, no match/case. All typing uses `Optional`, `Dict`, `List`, `Set` from typing module.
