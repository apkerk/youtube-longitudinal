"""
discover_non_intent.py
----------------------
Stream A': Non-Intent Creators Collection

Discovers new YouTube channels created in 2026 that began uploading without
explicitly signaling intent. Uses content keywords (gameplay, tutorial, recipe)
across 15 languages to find channels that jumped straight into content creation.

This serves as a comparison group for Stream A (Intent Creators) for causal
inference about the effects of intentional channel launching.

Supports 6 expansion strategies to break the ~500-result-per-query ceiling:
  - safeSearch=none (global param swap, zero quota cost)
  - topicId partitioning (12 topics, additive passes)
  - regionCode matched to language (23 regions, additive passes)
  - videoDuration partitioning (short/medium/long, additive passes)
  - order=relevance second pass (conditional on capped queries)
  - 12h windows (A'-specific: re-runs capped keywords with halved windows)

Supports checkpoint/resume: progress is saved after each search pass so
interrupted runs can continue without re-consuming API quota.

Target: 200,000 channels
Languages: Hindi, English, Spanish, Japanese, German, Portuguese, Korean, French,
           Arabic, Russian, Indonesian, Turkish, Vietnamese, Thai, Bengali
Filter: Channel created >= Jan 1, 2026

Usage:
    python -m src.collection.discover_non_intent [--test] [--limit N] [--skip-first-video]
    python -m src.collection.discover_non_intent --strategies base,safesearch,topicid
    python -m src.collection.discover_non_intent --days-back 1 --strategies base,safesearch,windows

Author: Katie Apker
Last Updated: Feb 19, 2026
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from youtube_api import (
    get_authenticated_service,
    search_videos_paginated,
    extract_channel_ids_from_search,
    get_channel_full_details,
    get_oldest_video,
    filter_channels_by_date,
)
import config

logger = logging.getLogger(__name__)


def setup_logging():
    # type: () -> None
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / ("discover_non_intent_%s.log" % config.get_date_stamp())

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

CHECKPOINT_PATH = config.STREAM_DIRS["stream_a_prime"] / ".discovery_checkpoint.json"


def load_checkpoint(output_path):
    # type: (Path) -> tuple
    """Load discovery checkpoint and rebuild state from partial CSV."""
    completed_passes = set()  # type: Set[str]
    channels_by_id = {}  # type: Dict[str, Dict]

    if not CHECKPOINT_PATH.exists():
        return completed_passes, channels_by_id

    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    completed_passes = set(ckpt.get("completed_keywords", []))

    saved_path = Path(ckpt.get("output_path", ""))
    if saved_path.exists() and saved_path == output_path:
        with open(saved_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('channel_id', '').strip()
                if cid:
                    channels_by_id[cid] = row

    logger.info(
        "Resumed from checkpoint: %d channels, %d passes completed",
        len(channels_by_id), len(completed_passes)
    )
    return completed_passes, channels_by_id


def save_checkpoint(completed_passes, output_path, channel_count):
    # type: (Set[str], Path, int) -> None
    """Save discovery checkpoint."""
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "completed_keywords": list(completed_passes),
            "output_path": str(output_path),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint():
    # type: () -> None
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")


def load_exclude_list(exclude_path):
    # type: (Path) -> Set[str]
    """Load channel IDs to exclude (e.g., Stream A channels for cross-dedup)."""
    exclude_ids = set()  # type: Set[str]
    if not exclude_path.exists():
        logger.warning("Exclude list not found: %s", exclude_path)
        return exclude_ids

    with open(exclude_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get('channel_id', '').strip()
            if cid:
                exclude_ids.add(cid)

    logger.info("Loaded %d channel IDs to exclude from %s", len(exclude_ids), exclude_path)
    return exclude_ids


def generate_search_passes(
    language,  # type: str
    strategies,  # type: Set[str]
):  # type: (...) -> List[Dict]
    """
    Generate search pass configurations for a keyword.

    Each pass is a dict with:
      - name: str (unique pass identifier, used as checkpoint key component)
      - extra_params: dict (API params beyond the base query)
      - provenance: dict (fields to tag on discovered channels)
      - max_pages: int (page depth for this pass)

    safeSearch=none is NOT a separate pass -- it modifies ALL passes.
    The "windows" strategy is handled separately in the main loop.
    """
    passes = []
    use_safesearch_none = "safesearch" in strategies
    safe_val = "none" if use_safesearch_none else "moderate"

    # Base pass (always present)
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
                "name": "topicid:%s" % topic_id,
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
                "name": "regioncode:%s" % region,
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
                "name": "duration:%s" % dur,
                "extra_params": {"safeSearch": safe_val, "videoDuration": dur},
                "provenance": {
                    "discovery_method": "duration",
                    "discovery_duration": dur,
                    "discovery_order": "date",
                    "discovery_safesearch": safe_val,
                },
                "max_pages": 5,
            })

    # NOTE: relevance and windows passes are handled separately in the main loop.
    return passes


def _run_search_pass_over_windows(
    youtube,
    keyword,  # type: str
    language,  # type: str
    time_windows,  # type: List[tuple]
    search_pass,  # type: Dict
    test_mode,  # type: bool
    expansion_wave,  # type: str
    window_hours,  # type: int
    channels_by_id,  # type: Dict[str, Dict]
    seen_channel_ids,  # type: Set[str]
    target_count,  # type: int
):  # type: (...) -> List[Dict]
    """
    Run a single search pass across all time windows.

    Returns list of newly discovered channels (already added to channels_by_id
    and seen_channel_ids in-place).
    """
    relevance_lang = config.RELEVANCE_LANGUAGE_CODES.get(language)
    pass_max_pages = 3 if test_mode else search_pass["max_pages"]
    batch_new = []  # type: List[Dict]

    for window_start, window_end in time_windows:
        if len(channels_by_id) >= target_count:
            break

        try:
            search_extra = dict(search_pass["extra_params"])
            if relevance_lang:
                search_extra["relevanceLanguage"] = relevance_lang

            search_results = search_videos_paginated(
                youtube=youtube,
                query=keyword,
                published_after=window_start,
                published_before=window_end,
                max_pages=pass_max_pages,
                order=search_pass.get("order", "date"),
                **search_extra
            )

            if not search_results:
                continue

            channel_ids = extract_channel_ids_from_search(search_results)
            new_channel_ids = [
                cid for cid in channel_ids
                if cid not in seen_channel_ids
            ]

            if not new_channel_ids:
                continue

            channel_details = get_channel_full_details(
                youtube=youtube,
                channel_ids=new_channel_ids,
                stream_type="stream_a_prime",
                discovery_language=language,
                discovery_keyword=keyword
            )

            new_channels = filter_channels_by_date(
                channels=channel_details,
                cutoff_date=config.COHORT_CUTOFF_DATE
            )

            for channel in new_channels:
                cid = channel["channel_id"]
                if cid not in channels_by_id:
                    channel["expansion_wave"] = expansion_wave
                    channel["discovery_window_hours"] = window_hours
                    channel.update(search_pass["provenance"])
                    channels_by_id[cid] = channel
                    seen_channel_ids.add(cid)
                    batch_new.append(channel)

        except Exception as e:
            logger.error("  Error in pass '%s' window %s: %s",
                         search_pass["name"], window_start[:10], e)
            continue

    return batch_new


def discover_non_intent_channels(
    youtube,
    target_count=200000,  # type: int
    test_mode=False,  # type: bool
    output_path=None,  # type: Optional[Path]
    exclude_ids=None,  # type: Optional[Set[str]]
    window_hours=24,  # type: int
    strategies=None,  # type: Optional[Set[str]]
    days_back=None,  # type: Optional[int]
):  # type: (...) -> List[Dict]
    """
    Discover content-focused new creators (no explicit intent signaling).

    Iterates over keywords, and for each keyword generates search passes based
    on the enabled expansion strategies. Each pass is checkpointed independently.

    The "windows" strategy (A'-specific) re-runs keywords with 12h windows when
    >50% of the base pass windows hit the ~500-result cap.

    Args:
        youtube: Authenticated YouTube API service
        target_count: Target number of channels to collect
        test_mode: If True, uses reduced targets for testing
        output_path: Path to write CSV output (required)
        exclude_ids: Set of channel IDs to skip (for cross-stream dedup)
        window_hours: Time window size in hours (default 24)
        strategies: Set of expansion strategy names to enable
        days_back: Only search the last N days (for daily discovery service)

    Returns:
        List of channel data dictionaries
    """
    if strategies is None:
        strategies = config.DEFAULT_STRATEGIES

    if test_mode:
        target_count = min(target_count, 100)
        logger.info("TEST MODE: Limited to 100 channels")

    if exclude_ids is None:
        exclude_ids = set()

    # Load checkpoint or start fresh
    completed_passes, channels_by_id = load_checkpoint(output_path)
    seen_channel_ids = set(channels_by_id.keys()) | exclude_ids  # type: Set[str]

    if exclude_ids:
        logger.info("Cross-dedup: excluding %d channels from other streams", len(exclude_ids))

    # If fresh start, write CSV header
    if not completed_passes:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
            writer.writeheader()

    time_windows = generate_time_windows(window_hours=window_hours, days_back=days_back)
    non_intent_keywords = config.get_all_non_intent_keywords()

    per_keyword_target = max(10, target_count // len(non_intent_keywords))

    logger.info("Target: %d channels", target_count)
    logger.info("Strategies: %s", ", ".join(sorted(strategies)))
    logger.info("Keywords: %d across %d languages", len(non_intent_keywords), len(config.NON_INTENT_KEYWORDS))
    logger.info("Time windows: %d x %dh%s",
                len(time_windows), window_hours,
                " (last %d days)" % days_back if days_back else "")
    logger.info("Per-keyword target: %d", per_keyword_target)
    logger.info("Already collected: %d channels", len(channels_by_id))

    for idx, (keyword, language) in enumerate(non_intent_keywords):
        if len(channels_by_id) >= target_count:
            logger.info("Reached target of %d channels", target_count)
            break

        relevance_lang = config.RELEVANCE_LANGUAGE_CODES.get(language)
        expansion_wave = config.get_keyword_wave(language, keyword)

        search_passes = generate_search_passes(language, strategies)

        logger.info("[%d/%d] Keyword: '%s' (%s, %d passes, wave=%s)",
                    idx + 1, len(non_intent_keywords), keyword, language,
                    len(search_passes), expansion_wave)

        # Track capped windows for relevance + windows passes
        capped_windows = set()  # type: Set[tuple]
        total_base_windows = 0

        for search_pass in search_passes:
            pass_key = "%s|%s|%s" % (keyword, language, search_pass["name"])

            # Backward compat: also skip if old-format key exists
            old_key = "%s|%s" % (keyword, language)
            if pass_key in completed_passes or (search_pass["name"] == "base" and old_key in completed_passes):
                continue

            pass_max_pages = 3 if test_mode else search_pass["max_pages"]
            batch_new_channels = []  # type: List[Dict]

            for window_start, window_end in time_windows:
                if len(channels_by_id) >= target_count:
                    break

                try:
                    search_extra = dict(search_pass["extra_params"])
                    if relevance_lang:
                        search_extra["relevanceLanguage"] = relevance_lang

                    search_results = search_videos_paginated(
                        youtube=youtube,
                        query=keyword,
                        published_after=window_start,
                        published_before=window_end,
                        max_pages=pass_max_pages,
                        order="date",
                        **search_extra
                    )

                    if not search_results:
                        continue

                    # Track capped windows (base pass only)
                    if search_pass["name"] == "base":
                        total_base_windows += 1
                        if len(search_results) >= pass_max_pages * 50:
                            capped_windows.add((window_start, window_end))

                    channel_ids = extract_channel_ids_from_search(search_results)
                    new_channel_ids = [
                        cid for cid in channel_ids
                        if cid not in seen_channel_ids
                    ]

                    if not new_channel_ids:
                        continue

                    channel_details = get_channel_full_details(
                        youtube=youtube,
                        channel_ids=new_channel_ids,
                        stream_type="stream_a_prime",
                        discovery_language=language,
                        discovery_keyword=keyword
                    )

                    new_channels = filter_channels_by_date(
                        channels=channel_details,
                        cutoff_date=config.COHORT_CUTOFF_DATE
                    )

                    for channel in new_channels:
                        cid = channel["channel_id"]
                        if cid not in channels_by_id:
                            channel["expansion_wave"] = expansion_wave
                            channel["discovery_window_hours"] = window_hours
                            channel.update(search_pass["provenance"])
                            channels_by_id[cid] = channel
                            seen_channel_ids.add(cid)
                            batch_new_channels.append(channel)

                except Exception as e:
                    logger.error("  Error in pass '%s' window %s: %s",
                                 search_pass["name"], window_start[:10], e)
                    continue

            # Append this pass's new channels to CSV
            if batch_new_channels:
                with open(output_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                    for ch in batch_new_channels:
                        row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                        writer.writerow(row)
                logger.info("  Pass '%s': +%d new channels (total: %d)",
                            search_pass["name"], len(batch_new_channels), len(channels_by_id))

            completed_passes.add(pass_key)
            save_checkpoint(completed_passes, output_path, len(channels_by_id))

        # Relevance second pass (Tier 3, conditional on capped queries)
        if "relevance" in strategies and capped_windows:
            rel_pass_key = "%s|%s|relevance" % (keyword, language)
            if rel_pass_key not in completed_passes:
                safe_val = "none" if "safesearch" in strategies else "moderate"
                rel_provenance = {
                    "discovery_method": "relevance",
                    "discovery_order": "relevance",
                    "discovery_safesearch": safe_val,
                    "discovery_duration": "any",
                }
                rel_batch = []  # type: List[Dict]
                rel_max_pages = 3 if test_mode else 5

                logger.info("  Relevance pass: %d capped windows", len(capped_windows))

                for window_start, window_end in sorted(capped_windows):
                    if len(channels_by_id) >= target_count:
                        break
                    try:
                        search_extra = {"safeSearch": safe_val}
                        if relevance_lang:
                            search_extra["relevanceLanguage"] = relevance_lang

                        search_results = search_videos_paginated(
                            youtube=youtube,
                            query=keyword,
                            published_after=window_start,
                            published_before=window_end,
                            max_pages=rel_max_pages,
                            order="relevance",
                            **search_extra
                        )

                        if not search_results:
                            continue

                        channel_ids = extract_channel_ids_from_search(search_results)
                        new_channel_ids = [
                            cid for cid in channel_ids
                            if cid not in seen_channel_ids
                        ]

                        if not new_channel_ids:
                            continue

                        channel_details = get_channel_full_details(
                            youtube=youtube,
                            channel_ids=new_channel_ids,
                            stream_type="stream_a_prime",
                            discovery_language=language,
                            discovery_keyword=keyword
                        )

                        new_channels = filter_channels_by_date(
                            channels=channel_details,
                            cutoff_date=config.COHORT_CUTOFF_DATE
                        )

                        for channel in new_channels:
                            cid = channel["channel_id"]
                            if cid not in channels_by_id:
                                channel["expansion_wave"] = expansion_wave
                                channel["discovery_window_hours"] = window_hours
                                channel.update(rel_provenance)
                                channels_by_id[cid] = channel
                                seen_channel_ids.add(cid)
                                rel_batch.append(channel)

                    except Exception as e:
                        logger.error("  Error in relevance pass: %s", e)
                        continue

                if rel_batch:
                    with open(output_path, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                        for ch in rel_batch:
                            row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                            writer.writerow(row)
                    logger.info("  Relevance pass: +%d new channels (total: %d)",
                                len(rel_batch), len(channels_by_id))

                completed_passes.add(rel_pass_key)
                save_checkpoint(completed_passes, output_path, len(channels_by_id))

        # 12h window re-run (A'-specific "windows" strategy)
        # Triggers when >50% of base-pass windows hit the ~500-result cap.
        if "windows" in strategies and total_base_windows > 0:
            cap_ratio = len(capped_windows) / total_base_windows
            win_pass_key = "%s|%s|windows_12h" % (keyword, language)

            if cap_ratio > 0.5 and win_pass_key not in completed_passes:
                safe_val = "none" if "safesearch" in strategies else "moderate"
                logger.info("  12h window pass: %.0f%% of windows capped (%d/%d), re-running with 12h",
                            cap_ratio * 100, len(capped_windows), total_base_windows)

                # Generate 12h windows for the same date range
                windows_12h = generate_time_windows(window_hours=12, days_back=days_back)
                win_provenance = {
                    "discovery_method": "base",
                    "discovery_order": "date",
                    "discovery_safesearch": safe_val,
                    "discovery_duration": "any",
                }
                win_batch = []  # type: List[Dict]
                win_max_pages = 3 if test_mode else 5

                for window_start, window_end in windows_12h:
                    if len(channels_by_id) >= target_count:
                        break
                    try:
                        search_extra = {"safeSearch": safe_val}
                        if relevance_lang:
                            search_extra["relevanceLanguage"] = relevance_lang

                        search_results = search_videos_paginated(
                            youtube=youtube,
                            query=keyword,
                            published_after=window_start,
                            published_before=window_end,
                            max_pages=win_max_pages,
                            order="date",
                            **search_extra
                        )

                        if not search_results:
                            continue

                        channel_ids = extract_channel_ids_from_search(search_results)
                        new_channel_ids = [
                            cid for cid in channel_ids
                            if cid not in seen_channel_ids
                        ]

                        if not new_channel_ids:
                            continue

                        channel_details = get_channel_full_details(
                            youtube=youtube,
                            channel_ids=new_channel_ids,
                            stream_type="stream_a_prime",
                            discovery_language=language,
                            discovery_keyword=keyword
                        )

                        new_channels = filter_channels_by_date(
                            channels=channel_details,
                            cutoff_date=config.COHORT_CUTOFF_DATE
                        )

                        for channel in new_channels:
                            cid = channel["channel_id"]
                            if cid not in channels_by_id:
                                channel["expansion_wave"] = expansion_wave
                                channel["discovery_window_hours"] = 12
                                channel.update(win_provenance)
                                channels_by_id[cid] = channel
                                seen_channel_ids.add(cid)
                                win_batch.append(channel)

                    except Exception as e:
                        logger.error("  Error in 12h window pass: %s", e)
                        continue

                if win_batch:
                    with open(output_path, 'a', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
                        for ch in win_batch:
                            row = {field: ch.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
                            writer.writerow(row)
                    logger.info("  12h window pass: +%d new channels (total: %d)",
                                len(win_batch), len(channels_by_id))

                completed_passes.add(win_pass_key)
                save_checkpoint(completed_passes, output_path, len(channels_by_id))
            elif cap_ratio <= 0.5 and win_pass_key not in completed_passes:
                logger.info("  12h window pass: skipped (only %.0f%% capped, threshold 50%%)",
                            cap_ratio * 100)

    clear_checkpoint()

    channels = list(channels_by_id.values())
    logger.info("Discovery complete: %d total channels", len(channels))
    return channels


def generate_time_windows(window_hours=24, days_back=None):
    # type: (int, Optional[int]) -> List[tuple]
    """
    Generate non-overlapping time windows from cutoff to now.

    Smaller windows yield more unique channels because the YouTube Search API
    caps results per query (~500). Tested: 24h windows find 3.5x more channels
    than 48h windows over the same period.

    Args:
        window_hours: Size of each time window in hours (default 24)
        days_back: If set, only generate windows for the last N days.
            If None, uses COHORT_CUTOFF_DATE.

    Returns:
        List of (start_iso, end_iso) tuples in chronological order
    """
    windows = []
    now = datetime.utcnow()
    if days_back is not None:
        cutoff = now - timedelta(days=days_back)
    else:
        cutoff = datetime.fromisoformat(config.COHORT_CUTOFF_DATE)
    step = timedelta(hours=window_hours)

    window_end = now
    while window_end > cutoff:
        window_start = window_end - step
        if window_start < cutoff:
            window_start = cutoff
        windows.append((
            window_start.isoformat() + 'Z',
            window_end.isoformat() + 'Z'
        ))
        window_end = window_start

    return list(reversed(windows))


def enrich_with_first_video(youtube, channels):
    # type: (..., List[Dict]) -> List[Dict]
    """Enrich channel data with first video information."""
    logger.info("Enriching %d channels with first video data...", len(channels))

    enriched = 0
    for idx, channel in enumerate(channels):
        if idx % 100 == 0:
            logger.info("  Progress: %d/%d", idx, len(channels))

        uploads_playlist = channel.get('uploads_playlist_id')
        if uploads_playlist:
            oldest = get_oldest_video(youtube, uploads_playlist)
            if oldest:
                channel['first_video_date'] = oldest.get('first_video_date')
                channel['first_video_id'] = oldest.get('first_video_id')
                channel['first_video_title'] = oldest.get('first_video_title')
                enriched += 1

    logger.info("Enriched %d channels with first video data", enriched)
    return channels


def save_channels_to_csv(channels, output_path):
    # type: (List[Dict], Path) -> None
    """Save channel data to CSV file (full write, overwrites existing)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
        writer.writeheader()

        for channel in channels:
            row = {field: channel.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
            writer.writerow(row)

    logger.info("Saved %d channels to %s", len(channels), output_path)


def parse_strategies(strategies_str):
    # type: (str) -> Set[str]
    """Parse and validate a comma-separated strategy string."""
    requested = set(s.strip() for s in strategies_str.split(",") if s.strip())
    invalid = requested - config.EXPANSION_STRATEGIES
    if invalid:
        raise argparse.ArgumentTypeError(
            "Unknown strategies: %s. Valid: %s" % (
                ", ".join(sorted(invalid)),
                ", ".join(sorted(config.EXPANSION_STRATEGIES)),
            )
        )
    return requested


def main():
    """Main entry point for Stream A' collection."""
    parser = argparse.ArgumentParser(description="Stream A': Non-Intent Creators Collection")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=200000, help='Target channel count')
    parser.add_argument('--skip-first-video', action='store_true',
                        help='Skip first video enrichment')
    parser.add_argument('--exclude-list', type=str, default=None,
                        help='Path to CSV of channel_ids to exclude (e.g., Stream A)')
    parser.add_argument('--window-hours', type=int, default=24,
                        help='Time window size in hours (default 24). Smaller = more channels found.')
    parser.add_argument('--days-back', type=int, default=None,
                        help='Only search the last N days (for daily discovery service)')
    parser.add_argument('--strategies', type=str, default='base,safesearch',
                        help='Comma-separated expansion strategies: %s (default: base,safesearch)'
                             % ",".join(sorted(config.EXPANSION_STRATEGIES)))
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    # Parse strategies
    strategies = parse_strategies(args.strategies)

    logger.info("=" * 60)
    logger.info("STREAM A': NON-INTENT CREATORS COLLECTION")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        # Load exclusion list if provided
        exclude_ids = set()  # type: Set[str]
        if args.exclude_list:
            exclude_ids = load_exclude_list(Path(args.exclude_list))

        output_path = config.get_output_path("stream_a_prime", "initial")

        channels = discover_non_intent_channels(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test,
            output_path=output_path,
            exclude_ids=exclude_ids,
            window_hours=args.window_hours,
            strategies=strategies,
            days_back=args.days_back,
        )

        if not channels:
            logger.warning("No channels discovered!")
            return

        if not args.skip_first_video:
            channels = enrich_with_first_video(youtube, channels)
            save_channels_to_csv(channels, output_path)

        logger.info("=" * 60)
        logger.info("COLLECTION SUMMARY")
        logger.info("=" * 60)
        logger.info("Total channels: %d", len(channels))

        by_language = {}  # type: Dict[str, int]
        for ch in channels:
            lang = ch.get('discovery_language', 'Unknown')
            by_language[lang] = by_language.get(lang, 0) + 1

        for lang, count in sorted(by_language.items(), key=lambda x: -x[1]):
            logger.info("  %s: %d", lang, count)

        # Summary by discovery method
        by_method = {}  # type: Dict[str, int]
        for ch in channels:
            method = ch.get('discovery_method', 'unknown')
            by_method[method] = by_method.get(method, 0) + 1
        if len(by_method) > 1:
            logger.info("By discovery method:")
            for method, count in sorted(by_method.items(), key=lambda x: -x[1]):
                logger.info("  %s: %d", method, count)

    except Exception as e:
        logger.error("Collection failed: %s", e)
        raise


if __name__ == "__main__":
    main()
