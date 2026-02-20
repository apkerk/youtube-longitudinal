"""
validate_expansion.py
---------------------
Validation pilot script for expansion strategies.

Runs baseline + strategy variant searches on test keywords to compute M1-M5
metrics and produce a GO/NO-GO recommendation per strategy.

Per the EXPANSION_VALIDATION_FRAMEWORK.md specification:
  - M1: Yield rate (unique new channels per 100 API units)
  - M2: Quality check (% passing date/activity/bot filters)
  - M3: Overlap with baseline (% of strategy channels already in baseline)
  - M4: Marginal new channel rate (% not in any existing stream CSV)
  - M5: Diminishing returns (per-partition yield curve for partitioned strategies)

Output:
  - CSV results to data/validation/expansion_pilots/{strategy}_{date}.csv
  - Log to data/logs/expansion_pilot_{strategy}_{date}.log
  - Summary table with GO/NO-GO printed to stdout

Usage:
    python -m src.validation.validate_expansion --strategy safesearch --dry-run
    python -m src.validation.validate_expansion --strategy topicid --keywords "My first video,gameplay"
    python -m src.validation.validate_expansion --strategy regioncode

Author: Katie Apker
Last Updated: Feb 19, 2026
"""

import argparse
import csv
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from youtube_api import (
    get_authenticated_service,
    search_videos_paginated,
    extract_channel_ids_from_search,
    get_channel_full_details,
    filter_channels_by_date,
)

logger = logging.getLogger(__name__)

# ── Default test keywords per strategy ───────────────────────────────────────

DEFAULT_KEYWORDS = {
    "safesearch": [
        ("GRWM", "English"),
        ("gameplay", "English"),
        ("tutorial", "English"),
        ("My first video", "English"),
    ],
    "topicid": [
        ("My first video", "English"),
        ("gameplay", "English"),
        ("Mi primer video", "Spanish"),
    ],
    "regioncode": [
        ("Bienvenidos a mi canal", "Spanish"),
        ("Meu primeiro vídeo", "Portuguese"),
        ("Mera pehla video", "Hindi"),
        ("awwal video", "Arabic"),
    ],
    "duration": [
        ("gameplay", "English"),
        ("tutorial", "English"),
        ("My first video", "English"),
    ],
    "relevance": [
        ("My first video", "English"),
        ("gameplay", "English"),
        ("tutorial", "English"),
    ],
    "windows": [
        ("gameplay", "English"),
        ("tutorial", "English"),
        ("recipe", "English"),
    ],
}

# ── Quota cost estimates per strategy (for --dry-run) ────────────────────────

QUOTA_ESTIMATES = {
    "safesearch": 12000,
    "topicid": 4800,
    "regioncode": 8500,
    "duration": 7500,
    "relevance": 13500,
    "windows": 24000,
}

# ── GO/NO-GO thresholds ─────────────────────────────────────────────────────

THRESHOLDS = {
    "safesearch": {
        "go_net_new_pct": 3.0,
        "nogo_legitimate_pct": 50.0,
    },
    "topicid": {
        "go_yield_multiplier": 1.5,
        "go_productive_topics": 6,
        "nogo_yield_multiplier": 1.2,
        "nogo_productive_topics": 4,
    },
    "regioncode": {
        "go_net_new_pct": 15.0,
        "nogo_net_new_pct": 5.0,
        "nogo_cross_overlap_pct": 70.0,
    },
    "duration": {
        "go_yield_multiplier": 1.5,
        "go_productive_slices": 2,
        "nogo_yield_multiplier": 1.2,
        "nogo_cross_overlap_pct": 40.0,
    },
    "relevance": {
        "go_overlap_pct": 60.0,
        "go_popularity_bias": 10.0,
        "go_survival_pct": 50.0,
        "nogo_overlap_pct": 80.0,
        "nogo_popularity_bias": 20.0,
        "nogo_survival_pct": 30.0,
    },
    "windows": {
        "go_improvement_pct": 30.0,
        "nogo_improvement_pct": 10.0,
    },
}


def setup_logging(strategy):
    # type: (str) -> None
    """Configure logging for validation pilot."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / (
        "expansion_pilot_%s_%s.log" % (strategy, config.get_date_stamp())
    )

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file),
        ]
    )


def get_test_window():
    # type: () -> tuple
    """Get a single 24h test window (yesterday)."""
    now = datetime.utcnow()
    end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=1)
    return (start.isoformat() + 'Z', end.isoformat() + 'Z')


def get_multi_windows(n_days=4, window_hours=24):
    # type: (int, int) -> List[tuple]
    """Get multiple consecutive windows for testing."""
    windows = []
    now = datetime.utcnow()
    end = now.replace(hour=0, minute=0, second=0, microsecond=0)
    step = timedelta(hours=window_hours)

    for _ in range(n_days):
        start = end - step
        windows.append((start.isoformat() + 'Z', end.isoformat() + 'Z'))
        end = start

    return list(reversed(windows))


def run_search(youtube, keyword, language, window, max_pages=10, extra_params=None):
    # type: (...) -> List[Dict]
    """Run a single search and return raw results + channel details."""
    if extra_params is None:
        extra_params = {}

    relevance_lang = config.RELEVANCE_LANGUAGE_CODES.get(language)
    search_extra = dict(extra_params)
    if relevance_lang:
        search_extra["relevanceLanguage"] = relevance_lang

    order = search_extra.pop("order", "date")

    search_results = search_videos_paginated(
        youtube=youtube,
        query=keyword,
        published_after=window[0],
        published_before=window[1],
        max_pages=max_pages,
        order=order,
        **search_extra
    )

    if not search_results:
        return []

    channel_ids = extract_channel_ids_from_search(search_results)
    unique_ids = list(dict.fromkeys(channel_ids))  # preserve order, dedup

    if not unique_ids:
        return []

    channel_details = get_channel_full_details(
        youtube=youtube,
        channel_ids=unique_ids,
        stream_type="validation",
        discovery_language=language,
        discovery_keyword=keyword,
    )

    return channel_details


def compute_metrics(baseline_channels, strategy_channels, api_units_consumed):
    # type: (List[Dict], List[Dict], int) -> Dict
    """Compute M1-M4 metrics for a strategy variant vs baseline."""
    baseline_ids = set(ch["channel_id"] for ch in baseline_channels)
    strategy_ids = set(ch["channel_id"] for ch in strategy_channels)

    # M1: Yield rate (unique channels per 100 API units)
    unique_new = strategy_ids - baseline_ids
    m1_yield = (len(unique_new) / max(api_units_consumed, 1)) * 100

    # M2: Quality check (2026+ and not bot)
    passing = 0
    for ch in strategy_channels:
        published = ch.get("published_at", "")
        video_count = int(ch.get("video_count", 0) or 0)
        sub_count = int(ch.get("subscriber_count", 0) or 0)

        is_2026 = published >= "2026-01-01" if published else False
        has_videos = video_count >= 1
        not_bot = not (video_count <= 1 and sub_count == 0)

        if is_2026 and has_videos and not_bot:
            passing += 1

    m2_quality = (passing / max(len(strategy_channels), 1)) * 100

    # M3: Overlap with baseline
    overlap = strategy_ids & baseline_ids
    m3_overlap = (len(overlap) / max(len(strategy_ids), 1)) * 100

    # M4: Marginal new (not in baseline)
    m4_marginal = (len(unique_new) / max(len(strategy_ids), 1)) * 100

    return {
        "baseline_count": len(baseline_ids),
        "strategy_count": len(strategy_ids),
        "unique_new": len(unique_new),
        "overlap": len(overlap),
        "api_units": api_units_consumed,
        "m1_yield_per_100_units": round(m1_yield, 2),
        "m2_quality_pct": round(m2_quality, 1),
        "m3_overlap_pct": round(m3_overlap, 1),
        "m4_marginal_new_pct": round(m4_marginal, 1),
    }


def validate_safesearch(youtube, keywords):
    # type: (...) -> Dict
    """Validate safeSearch=none vs safeSearch=moderate."""
    window = get_test_window()
    all_moderate = []  # type: List[Dict]
    all_none = []  # type: List[Dict]
    units = 0

    for keyword, language in keywords:
        logger.info("  Testing '%s' (%s)...", keyword, language)

        moderate = run_search(youtube, keyword, language, window, max_pages=10,
                              extra_params={"safeSearch": "moderate"})
        units += 10 * 100  # 10 pages * 100 units/page

        none_results = run_search(youtube, keyword, language, window, max_pages=10,
                                  extra_params={"safeSearch": "none"})
        units += 10 * 100

        all_moderate.extend(moderate)
        all_none.extend(none_results)

        logger.info("    moderate: %d, none: %d", len(moderate), len(none_results))

    metrics = compute_metrics(all_moderate, all_none, units)

    # GO/NO-GO
    net_new_pct = metrics["m4_marginal_new_pct"]
    verdict = "GO" if net_new_pct >= THRESHOLDS["safesearch"]["go_net_new_pct"] else "NO-GO"
    metrics["verdict"] = verdict

    return metrics


def validate_topicid(youtube, keywords):
    # type: (...) -> Dict
    """Validate topicId partitioning."""
    window = get_test_window()
    all_baseline = []  # type: List[Dict]
    all_topic = []  # type: List[Dict]
    topic_counts = {}  # type: Dict[str, int]
    units = 0

    for keyword, language in keywords:
        logger.info("  Baseline search: '%s' (%s)...", keyword, language)
        baseline = run_search(youtube, keyword, language, window, max_pages=10)
        units += 10 * 100
        all_baseline.extend(baseline)

        baseline_ids = set(ch["channel_id"] for ch in baseline)

        for topic_id, topic_name in config.DISCOVERY_TOPIC_IDS.items():
            logger.info("  Topic '%s' (%s): '%s'...", topic_name, topic_id, keyword)
            topic_results = run_search(
                youtube, keyword, language, window, max_pages=5,
                extra_params={"topicId": topic_id}
            )
            units += 5 * 100
            all_topic.extend(topic_results)

            new_from_topic = set(ch["channel_id"] for ch in topic_results) - baseline_ids
            topic_counts[topic_name] = topic_counts.get(topic_name, 0) + len(new_from_topic)

    metrics = compute_metrics(all_baseline, all_topic, units)

    # M5: Diminishing returns by topic
    sorted_topics = sorted(topic_counts.items(), key=lambda x: -x[1])
    productive = sum(1 for _, count in sorted_topics if count > 0)
    metrics["productive_topics"] = productive
    metrics["topic_yields"] = dict(sorted_topics)

    # GO/NO-GO
    total_unique = metrics["unique_new"]
    baseline_n = max(metrics["baseline_count"], 1)
    yield_mult = (metrics["strategy_count"]) / baseline_n

    thresholds = THRESHOLDS["topicid"]
    if yield_mult >= thresholds["go_yield_multiplier"] and productive >= thresholds["go_productive_topics"]:
        verdict = "GO"
    elif yield_mult < thresholds["nogo_yield_multiplier"] or productive < thresholds["nogo_productive_topics"]:
        verdict = "NO-GO"
    else:
        verdict = "CONDITIONAL"
    metrics["yield_multiplier"] = round(yield_mult, 2)
    metrics["verdict"] = verdict

    return metrics


def validate_regioncode(youtube, keywords):
    # type: (...) -> Dict
    """Validate regionCode matched to language."""
    window = get_test_window()
    all_baseline = []  # type: List[Dict]
    all_region = []  # type: List[Dict]
    region_counts = {}  # type: Dict[str, int]
    units = 0

    for keyword, language in keywords:
        regions = config.LANGUAGE_REGION_MAP.get(language, [])
        if not regions:
            continue

        logger.info("  Baseline: '%s' (%s)...", keyword, language)
        baseline = run_search(youtube, keyword, language, window, max_pages=10)
        units += 10 * 100
        all_baseline.extend(baseline)

        baseline_ids = set(ch["channel_id"] for ch in baseline)

        for region in regions:
            logger.info("  Region %s: '%s'...", region, keyword)
            region_results = run_search(
                youtube, keyword, language, window, max_pages=5,
                extra_params={"regionCode": region}
            )
            units += 5 * 100
            all_region.extend(region_results)

            new_from_region = set(ch["channel_id"] for ch in region_results) - baseline_ids
            region_counts[region] = region_counts.get(region, 0) + len(new_from_region)

    metrics = compute_metrics(all_baseline, all_region, units)
    metrics["region_yields"] = dict(sorted(region_counts.items(), key=lambda x: -x[1]))

    # GO/NO-GO
    any_go = any(
        count / max(metrics["baseline_count"], 1) * 100 >= THRESHOLDS["regioncode"]["go_net_new_pct"]
        for count in region_counts.values()
    )
    metrics["verdict"] = "GO" if any_go else "NO-GO"

    return metrics


def validate_duration(youtube, keywords):
    # type: (...) -> Dict
    """Validate videoDuration partitioning."""
    window = get_test_window()
    all_baseline = []  # type: List[Dict]
    all_duration = []  # type: List[Dict]
    dur_counts = {}  # type: Dict[str, int]
    units = 0

    for keyword, language in keywords:
        logger.info("  Baseline: '%s' (%s)...", keyword, language)
        baseline = run_search(youtube, keyword, language, window, max_pages=10)
        units += 10 * 100
        all_baseline.extend(baseline)

        baseline_ids = set(ch["channel_id"] for ch in baseline)

        for dur in config.DISCOVERY_DURATIONS:
            logger.info("  Duration %s: '%s'...", dur, keyword)
            dur_results = run_search(
                youtube, keyword, language, window, max_pages=5,
                extra_params={"videoDuration": dur}
            )
            units += 5 * 100
            all_duration.extend(dur_results)

            new_from_dur = set(ch["channel_id"] for ch in dur_results) - baseline_ids
            dur_counts[dur] = dur_counts.get(dur, 0) + len(new_from_dur)

    metrics = compute_metrics(all_baseline, all_duration, units)
    metrics["duration_yields"] = dict(sorted(dur_counts.items(), key=lambda x: -x[1]))

    productive = sum(1 for _, count in dur_counts.items() if count > 0)
    metrics["productive_slices"] = productive

    baseline_n = max(metrics["baseline_count"], 1)
    yield_mult = metrics["strategy_count"] / baseline_n
    metrics["yield_multiplier"] = round(yield_mult, 2)

    thresholds = THRESHOLDS["duration"]
    if yield_mult >= thresholds["go_yield_multiplier"] and productive >= thresholds["go_productive_slices"]:
        verdict = "GO"
    elif yield_mult < thresholds["nogo_yield_multiplier"]:
        verdict = "NO-GO"
    else:
        verdict = "CONDITIONAL"
    metrics["verdict"] = verdict

    return metrics


def validate_relevance(youtube, keywords):
    # type: (...) -> Dict
    """Validate order=relevance second pass."""
    windows = get_multi_windows(n_days=3)
    all_date = []  # type: List[Dict]
    all_relevance = []  # type: List[Dict]
    units = 0

    for keyword, language in keywords:
        for window in windows:
            logger.info("  Date pass: '%s' window %s...", keyword, window[0][:10])
            date_results = run_search(youtube, keyword, language, window, max_pages=10)
            units += 10 * 100
            all_date.extend(date_results)

            logger.info("  Relevance pass: '%s' window %s...", keyword, window[0][:10])
            rel_results = run_search(
                youtube, keyword, language, window, max_pages=5,
                extra_params={"order": "relevance"}
            )
            units += 5 * 100
            all_relevance.extend(rel_results)

    metrics = compute_metrics(all_date, all_relevance, units)

    # Popularity bias check
    date_subs = [int(ch.get("subscriber_count", 0) or 0) for ch in all_date]
    rel_subs = [int(ch.get("subscriber_count", 0) or 0) for ch in all_relevance]

    date_median = sorted(date_subs)[len(date_subs) // 2] if date_subs else 0
    rel_median = sorted(rel_subs)[len(rel_subs) // 2] if rel_subs else 0

    popularity_bias = rel_median / max(date_median, 1)
    metrics["date_median_subs"] = date_median
    metrics["relevance_median_subs"] = rel_median
    metrics["popularity_bias_ratio"] = round(popularity_bias, 1)

    # 2026 survival rate
    rel_2026 = sum(1 for ch in all_relevance
                   if ch.get("published_at", "") >= "2026-01-01")
    metrics["survival_pct"] = round(rel_2026 / max(len(all_relevance), 1) * 100, 1)

    # GO/NO-GO
    thresholds = THRESHOLDS["relevance"]
    overlap_ok = metrics["m3_overlap_pct"] < thresholds["go_overlap_pct"]
    bias_ok = popularity_bias < thresholds["go_popularity_bias"]
    survival_ok = metrics["survival_pct"] >= thresholds["go_survival_pct"]

    if overlap_ok and bias_ok and survival_ok:
        verdict = "GO"
    elif (metrics["m3_overlap_pct"] > thresholds["nogo_overlap_pct"] or
          popularity_bias > thresholds["nogo_popularity_bias"] or
          metrics["survival_pct"] < thresholds["nogo_survival_pct"]):
        verdict = "NO-GO"
    else:
        verdict = "CONDITIONAL"
    metrics["verdict"] = verdict

    return metrics


def validate_windows(youtube, keywords):
    # type: (...) -> Dict
    """Validate 12h vs 24h windows."""
    windows_24h = get_multi_windows(n_days=4, window_hours=24)
    windows_12h = get_multi_windows(n_days=4, window_hours=12)

    all_24h = []  # type: List[Dict]
    all_12h = []  # type: List[Dict]
    units = 0

    for keyword, language in keywords:
        logger.info("  24h windows: '%s' (%d windows)...", keyword, len(windows_24h))
        for window in windows_24h:
            results = run_search(youtube, keyword, language, window, max_pages=10)
            units += 10 * 100
            all_24h.extend(results)

        logger.info("  12h windows: '%s' (%d windows)...", keyword, len(windows_12h))
        for window in windows_12h:
            results = run_search(youtube, keyword, language, window, max_pages=5)
            units += 5 * 100
            all_12h.extend(results)

    ids_24h = set(ch["channel_id"] for ch in all_24h)
    ids_12h = set(ch["channel_id"] for ch in all_12h)
    unique_from_12h = ids_12h - ids_24h

    improvement_pct = (len(unique_from_12h) / max(len(ids_24h), 1)) * 100

    metrics = {
        "channels_24h": len(ids_24h),
        "channels_12h": len(ids_12h),
        "unique_from_12h": len(unique_from_12h),
        "improvement_pct": round(improvement_pct, 1),
        "api_units": units,
    }

    thresholds = THRESHOLDS["windows"]
    if improvement_pct >= thresholds["go_improvement_pct"]:
        verdict = "GO"
    elif improvement_pct < thresholds["nogo_improvement_pct"]:
        verdict = "NO-GO"
    else:
        verdict = "CONDITIONAL"
    metrics["verdict"] = verdict

    return metrics


def save_results(strategy, metrics, output_dir):
    # type: (str, Dict, Path) -> Path
    """Save validation results to CSV."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / ("%s_%s.csv" % (strategy, config.get_date_stamp()))

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sorted(metrics.keys()))
        writer.writeheader()
        writer.writerow(metrics)

    return output_path


def print_summary(strategy, metrics):
    # type: (str, Dict) -> None
    """Print formatted summary table."""
    print("\n" + "=" * 60)
    print("EXPANSION VALIDATION: %s" % strategy.upper())
    print("=" * 60)

    verdict = metrics.get("verdict", "UNKNOWN")
    verdict_marker = {
        "GO": "[PASS]",
        "NO-GO": "[FAIL]",
        "CONDITIONAL": "[COND]",
    }.get(verdict, "[????]")

    print("\nVerdict: %s %s" % (verdict_marker, verdict))
    print("")

    # Print key metrics
    skip_keys = {"verdict", "topic_yields", "region_yields", "duration_yields"}
    for key, val in sorted(metrics.items()):
        if key in skip_keys:
            continue
        print("  %-30s %s" % (key + ":", val))

    # Print partition breakdowns
    for partition_key in ["topic_yields", "region_yields", "duration_yields"]:
        partition_data = metrics.get(partition_key)
        if partition_data:
            print("\n  %s:" % partition_key)
            for name, count in sorted(partition_data.items(), key=lambda x: -x[1]):
                bar = "#" * min(count, 40)
                print("    %-20s %4d  %s" % (name, count, bar))

    print("\n" + "=" * 60)


# ── Strategy dispatcher ─────────────────────────────────────────────────────

VALIDATORS = {
    "safesearch": validate_safesearch,
    "topicid": validate_topicid,
    "regioncode": validate_regioncode,
    "duration": validate_duration,
    "relevance": validate_relevance,
    "windows": validate_windows,
}


def main():
    parser = argparse.ArgumentParser(
        description="Validate expansion strategies for YouTube discovery scripts"
    )
    parser.add_argument(
        '--strategy', type=str, required=True,
        choices=sorted(VALIDATORS.keys()),
        help='Strategy to validate',
    )
    parser.add_argument(
        '--keywords', type=str, default=None,
        help='Comma-separated keywords to test (default: strategy-specific defaults)',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Print estimated API cost without executing',
    )
    args = parser.parse_args()

    setup_logging(args.strategy)

    # Parse custom keywords or use defaults
    if args.keywords:
        keywords = [(kw.strip(), "English") for kw in args.keywords.split(",")]
    else:
        keywords = DEFAULT_KEYWORDS.get(args.strategy, [])

    if not keywords:
        logger.error("No keywords configured for strategy '%s'", args.strategy)
        sys.exit(1)

    # Dry run: just print cost estimate
    if args.dry_run:
        estimated = QUOTA_ESTIMATES.get(args.strategy, 0)
        print("\n--- DRY RUN: %s ---" % args.strategy)
        print("Estimated API cost: ~%d units (%.1f%% of daily quota)" % (
            estimated, estimated / 10100
        ))
        print("Keywords: %d" % len(keywords))
        for kw, lang in keywords:
            print("  '%s' (%s)" % (kw, lang))
        print("Output: data/validation/expansion_pilots/%s_%s.csv" % (
            args.strategy, config.get_date_stamp()
        ))
        return

    # Production validation run
    logger.info("=" * 60)
    logger.info("EXPANSION VALIDATION: %s", args.strategy.upper())
    logger.info("=" * 60)
    logger.info("Keywords: %d", len(keywords))
    for kw, lang in keywords:
        logger.info("  '%s' (%s)", kw, lang)

    config.ensure_directories()

    youtube = get_authenticated_service()
    logger.info("Authenticated with YouTube API")

    validator = VALIDATORS[args.strategy]
    metrics = validator(youtube, keywords)

    # Save results
    output_dir = config.DATA_DIR / "validation" / "expansion_pilots"
    output_path = save_results(args.strategy, metrics, output_dir)
    logger.info("Results saved to %s", output_path)

    # Print summary
    print_summary(args.strategy, metrics)


if __name__ == "__main__":
    main()
