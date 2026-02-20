"""
discover_intent.py
------------------
Stream A: Intent Creators Collection

Discovers new YouTube channels created in 2026 that are intentionally starting
their creator journey. Uses intent keywords across 15 languages to find channels
that explicitly introduce themselves ("Welcome to my channel", "My first video").

Supports 6 expansion strategies to break the ~500-result-per-query ceiling:
  - safeSearch=none (global param swap, zero quota cost)
  - topicId partitioning (12 topics, additive passes)
  - regionCode matched to language (23 regions, additive passes)
  - videoDuration partitioning (short/medium/long, additive passes)
  - order=relevance second pass (conditional on capped queries)
  - 12h windows (A' only, not used in this script)

Supports checkpoint/resume: progress is saved after each search pass so
interrupted runs can continue without re-consuming API quota.

Target: 200,000 channels
Languages: Hindi, English, Spanish, Japanese, German, Portuguese, Korean, French,
           Arabic, Russian, Indonesian, Turkish, Vietnamese, Thai, Bengali
Filter: Channel created >= Jan 1, 2026

Usage:
    python -m src.collection.discover_intent [--test] [--limit N] [--skip-first-video]
    python -m src.collection.discover_intent --strategies base,safesearch,topicid
    python -m src.collection.discover_intent --days-back 1 --strategies base,safesearch

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


def setup_logging() -> None:
    """Configure logging with file and stream handlers."""
    config.ensure_directories()
    log_file = config.LOGS_DIR / f'discover_intent_{config.get_date_stamp()}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )

CHECKPOINT_PATH = config.STREAM_DIRS["stream_a"] / ".discovery_checkpoint.json"


def load_checkpoint(output_path: Path) -> tuple:
    """
    Load discovery checkpoint and rebuild state from partial CSV.

    Returns:
        Tuple of (completed_keyword_keys, channels_by_id)
    """
    completed_keywords: Set[str] = set()
    channels_by_id: Dict[str, Dict] = {}

    if not CHECKPOINT_PATH.exists():
        return completed_keywords, channels_by_id

    with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
        ckpt = json.load(f)

    completed_keywords = set(ckpt.get("completed_keywords", []))

    # Rebuild channel state from partial output CSV
    saved_path = Path(ckpt.get("output_path", ""))
    if saved_path.exists() and saved_path == output_path:
        with open(saved_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row.get('channel_id', '').strip()
                if cid:
                    channels_by_id[cid] = row

    logger.info(
        f"Resumed from checkpoint: {len(channels_by_id)} channels, "
        f"{len(completed_keywords)} keywords completed"
    )
    return completed_keywords, channels_by_id


def save_checkpoint(completed_keywords: Set[str], output_path: Path, channel_count: int) -> None:
    """Save discovery checkpoint."""
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump({
            "completed_keywords": list(completed_keywords),
            "output_path": str(output_path),
            "channel_count": channel_count,
            "timestamp": datetime.utcnow().isoformat(),
        }, f)


def clear_checkpoint() -> None:
    """Remove checkpoint file after successful completion."""
    if CHECKPOINT_PATH.exists():
        CHECKPOINT_PATH.unlink()
        logger.info("Checkpoint cleared")


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

    safeSearch=none is NOT a separate pass — it modifies ALL passes when
    'safesearch' is in the strategy set.
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

    # topicId passes — each topic gets its own ~500-result ceiling
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

    # regionCode passes — language-matched regions
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

    # videoDuration passes — short/medium/long each get own ceiling
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

    # NOTE: relevance pass is handled separately in the main loop
    # because it's conditional on which queries hit the result cap.
    return passes


def discover_intent_channels(
    youtube,
    target_count=200000,  # type: int
    test_mode=False,  # type: bool
    output_path=None,  # type: Optional[Path]
    window_hours=24,  # type: int
    strategies=None,  # type: Optional[Set[str]]
    days_back=None,  # type: Optional[int]
):  # type: (...) -> List[Dict]
    """
    Discover intent-signaling new creators across 15 languages.

    Iterates over keywords, and for each keyword generates search passes based
    on the enabled expansion strategies. Each pass is checkpointed independently
    so interrupted runs resume at the pass level.

    Args:
        youtube: Authenticated YouTube API service
        target_count: Target number of channels to collect
        test_mode: If True, uses reduced targets for testing
        output_path: Path to write CSV output (required)
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

    # Load checkpoint or start fresh
    completed_passes, channels_by_id = load_checkpoint(output_path)
    seen_channel_ids = set(channels_by_id.keys())  # type: Set[str]

    # If fresh start, write CSV header
    if not completed_passes:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
            writer.writeheader()

    # Generate time windows and keywords
    time_windows = generate_time_windows(window_hours=window_hours, days_back=days_back)
    intent_keywords = config.get_all_intent_keywords()

    per_keyword_target = max(10, target_count // len(intent_keywords))

    logger.info("Target: %d channels", target_count)
    logger.info("Strategies: %s", ", ".join(sorted(strategies)))
    logger.info("Keywords: %d across %d languages", len(intent_keywords), len(config.INTENT_KEYWORDS))
    logger.info("Time windows: %d x %dh%s",
                len(time_windows), window_hours,
                " (last %d days)" % days_back if days_back else "")
    logger.info("Per-keyword target: %d", per_keyword_target)
    logger.info("Already collected: %d channels", len(channels_by_id))

    for idx, (keyword, language) in enumerate(intent_keywords):
        if len(channels_by_id) >= target_count:
            logger.info("Reached target of %d channels", target_count)
            break

        # Look up ISO 639-1 code for relevanceLanguage parameter
        relevance_lang = config.RELEVANCE_LANGUAGE_CODES.get(language)
        expansion_wave = config.get_keyword_wave(language, keyword)

        # Generate all search passes for this keyword
        search_passes = generate_search_passes(language, strategies)

        logger.info("[%d/%d] Keyword: '%s' (%s, %d passes, wave=%s)",
                    idx + 1, len(intent_keywords), keyword, language,
                    len(search_passes), expansion_wave)

        # Track which windows hit the result cap (for relevance pass)
        capped_windows = set()  # type: Set[tuple]

        for search_pass in search_passes:
            pass_key = "%s|%s|%s" % (keyword, language, search_pass["name"])

            # Backward compat: also skip if old-format key exists
            old_key = "%s|%s" % (keyword, language)
            if pass_key in completed_passes or (search_pass["name"] == "base" and old_key in completed_passes):
                continue

            batch_new_channels = []  # type: List[Dict]
            pass_max_pages = 3 if test_mode else search_pass["max_pages"]

            for window_start, window_end in time_windows:
                if len(channels_by_id) >= target_count:
                    break

                try:
                    # Build extra params: merge pass params + relevanceLanguage
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

                    # Track capped windows for optional relevance pass
                    if search_pass["name"] == "base":
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
                        stream_type="stream_a",
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

            # Checkpoint after each pass
            completed_passes.add(pass_key)
            save_checkpoint(completed_passes, output_path, len(channels_by_id))

        # Relevance second pass — conditional on capped queries (Tier 3)
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
                            stream_type="stream_a",
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
        days_back: If set, only generate windows for the last N days
            (for daily discovery service). If None, uses COHORT_CUTOFF_DATE.

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


def enrich_with_first_video(youtube, channels: List[Dict]) -> List[Dict]:
    """
    Enrich channel data with first video information.

    Note: This is expensive (1 API call per channel minimum).
    Only run for initial collection, not sweeps.

    Args:
        youtube: Authenticated YouTube API service
        channels: List of channel dictionaries

    Returns:
        Channels with first_video_date/id/title populated
    """
    logger.info(f"Enriching {len(channels)} channels with first video data...")

    enriched = 0
    for idx, channel in enumerate(channels):
        if idx % 100 == 0:
            logger.info(f"  Progress: {idx}/{len(channels)}")

        uploads_playlist = channel.get('uploads_playlist_id')
        if uploads_playlist:
            oldest = get_oldest_video(youtube, uploads_playlist)
            if oldest:
                channel['first_video_date'] = oldest.get('first_video_date')
                channel['first_video_id'] = oldest.get('first_video_id')
                channel['first_video_title'] = oldest.get('first_video_title')
                enriched += 1

    logger.info(f"Enriched {enriched} channels with first video data")
    return channels


def save_channels_to_csv(channels: List[Dict], output_path: Path) -> None:
    """
    Save channel data to CSV file (full write, overwrites existing).

    Args:
        channels: List of channel dictionaries
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=config.CHANNEL_INITIAL_FIELDS)
        writer.writeheader()

        for channel in channels:
            row = {field: channel.get(field) for field in config.CHANNEL_INITIAL_FIELDS}
            writer.writerow(row)

    logger.info(f"Saved {len(channels)} channels to {output_path}")


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
    """Main entry point for Stream A collection."""
    parser = argparse.ArgumentParser(description="Stream A: Intent Creators Collection")
    parser.add_argument('--test', action='store_true', help='Run in test mode (100 channels)')
    parser.add_argument('--limit', type=int, default=200000, help='Target channel count')
    parser.add_argument('--skip-first-video', action='store_true',
                        help='Skip first video enrichment (saves API quota)')
    parser.add_argument('--window-hours', type=int, default=24,
                        help='Time window size in hours (default 24). Smaller = more channels found.')
    parser.add_argument('--days-back', type=int, default=None,
                        help='Only search the last N days (for daily discovery service)')
    parser.add_argument('--strategies', type=str, default='base,safesearch',
                        help='Comma-separated expansion strategies: %s (default: base,safesearch)'
                             % ",".join(sorted(config.EXPANSION_STRATEGIES)))
    parser.add_argument('--output', type=str, default=None,
                        help='Output CSV path (default: auto-generated with date stamp)')
    args = parser.parse_args()

    setup_logging()
    config.ensure_directories()

    # Parse strategies
    strategies = parse_strategies(args.strategies)

    logger.info("=" * 60)
    logger.info("STREAM A: INTENT CREATORS COLLECTION")
    logger.info("=" * 60)

    try:
        youtube = get_authenticated_service()
        logger.info("Authenticated with YouTube API")

        # Determine output path upfront (needed for checkpoint)
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = config.get_output_path("stream_a", "initial")

        # Discover channels (writes incrementally with checkpoint)
        channels = discover_intent_channels(
            youtube=youtube,
            target_count=args.limit,
            test_mode=args.test,
            output_path=output_path,
            window_hours=args.window_hours,
            strategies=strategies,
            days_back=args.days_back,
        )

        if not channels:
            logger.warning("No channels discovered!")
            return

        # Optionally enrich with first video (requires full CSV rewrite)
        if not args.skip_first_video:
            channels = enrich_with_first_video(youtube, channels)
            save_channels_to_csv(channels, output_path)

        # Summary
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
