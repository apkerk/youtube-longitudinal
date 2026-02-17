"""
flag_ai_videos.py
-----------------
Flag videos in a video inventory whose titles match AI-related keywords.

Reads a video inventory CSV (from enumerate_videos.py), matches titles against
AI_FLAG_KEYWORDS from config.py, and outputs a flagged inventory with:
  - ai_flag (bool): does the title match any AI keyword?
  - ai_keywords_matched (str): which keywords matched (pipe-separated)
  - ai_category (str): broad category of AI content

This is the treatment variable for the adoption diffusion design:
"when did channel X first post an AI-flagged video?"

No API calls — pure offline title matching.

Usage:
    python -m src.analysis.flag_ai_videos \
        --input data/video_inventory/gender_gap_inventory.csv \
        --output data/processed/gender_gap_ai_flagged.csv

    # Or for AI census inventory:
    python -m src.analysis.flag_ai_videos \
        --input data/video_inventory/ai_census_inventory.csv \
        --output data/processed/ai_census_ai_flagged.csv
"""

import argparse
import csv
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def _build_keyword_patterns() -> List[Tuple[re.Pattern, str, str]]:
    """
    Build compiled regex patterns from AI_FLAG_KEYWORDS.

    Returns:
        List of (compiled_pattern, keyword_string, category) tuples.
        Patterns use word boundaries for precision.
    """
    patterns = []
    for category, keywords in config.AI_FLAG_KEYWORDS.items():
        for kw in keywords:
            # Escape special regex chars, then wrap in word boundaries
            escaped = re.escape(kw)
            pattern = re.compile(r'\b' + escaped + r'\b', re.IGNORECASE)
            patterns.append((pattern, kw, category))
    return patterns


def flag_title(title: str, patterns: List[Tuple[re.Pattern, str, str]]) -> Tuple[bool, str, str]:
    """
    Check a video title against all AI keyword patterns.

    Args:
        title: Video title to check
        patterns: Pre-compiled (pattern, keyword, category) tuples

    Returns:
        (ai_flag, keywords_matched, categories_matched) where:
        - ai_flag: True if any keyword matched
        - keywords_matched: pipe-separated matched keywords
        - categories_matched: pipe-separated matched categories (deduplicated)
    """
    matched_keywords: List[str] = []
    matched_categories: Set[str] = set()

    for pattern, kw, category in patterns:
        if pattern.search(title):
            matched_keywords.append(kw)
            matched_categories.add(category)

    if matched_keywords:
        return True, "|".join(matched_keywords), "|".join(sorted(matched_categories))
    return False, "", ""


def flag_inventory(input_path: Path, output_path: Path) -> Dict:
    """
    Read video inventory, flag AI-related titles, write flagged output.

    Args:
        input_path: Path to video inventory CSV (needs video_id, channel_id, title, published_at)
        output_path: Path to write flagged CSV

    Returns:
        Summary dict with counts
    """
    patterns = _build_keyword_patterns()
    logger.info(f"Built {len(patterns)} keyword patterns across {len(config.AI_FLAG_KEYWORDS)} categories")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    flagged = 0
    categories_count: Dict[str, int] = {}

    # Determine input fields by reading header
    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        input_fields = reader.fieldnames or []

    output_fields = list(input_fields) + ["ai_flag", "ai_keywords_matched", "ai_category"]

    with open(input_path, 'r', encoding='utf-8') as fin, \
         open(output_path, 'w', newline='', encoding='utf-8') as fout:

        reader = csv.DictReader(fin)
        writer = csv.DictWriter(fout, fieldnames=output_fields)
        writer.writeheader()

        for row in reader:
            total += 1
            title = row.get('title', '') or ''

            ai_flag, keywords_matched, categories_matched = flag_title(title, patterns)

            row['ai_flag'] = ai_flag
            row['ai_keywords_matched'] = keywords_matched
            row['ai_category'] = categories_matched

            if ai_flag:
                flagged += 1
                for cat in categories_matched.split("|"):
                    if cat:
                        categories_count[cat] = categories_count.get(cat, 0) + 1

            writer.writerow(row)

            if total % 500000 == 0:
                logger.info(f"  Processed {total:,} videos ({flagged:,} flagged)")

    logger.info(f"Flagging complete: {flagged:,} / {total:,} videos flagged ({flagged/total*100:.1f}%)" if total > 0 else "No videos processed")
    logger.info(f"Output: {output_path}")

    if categories_count:
        logger.info("Category breakdown:")
        for cat, count in sorted(categories_count.items(), key=lambda x: -x[1]):
            logger.info(f"  {cat}: {count:,}")

    return {
        'total_videos': total,
        'flagged_videos': flagged,
        'flag_rate': flagged / total if total > 0 else 0,
        'categories': categories_count,
        'output_path': str(output_path),
    }


def main():
    parser = argparse.ArgumentParser(description="Flag AI-related videos in a video inventory")
    parser.add_argument('--input', type=str, required=True,
                        help='Path to video inventory CSV')
    parser.add_argument('--output', type=str, required=True,
                        help='Path for flagged output CSV')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.is_absolute():
        input_path = config.PROJECT_ROOT / input_path
    if not output_path.is_absolute():
        output_path = config.PROJECT_ROOT / output_path

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("AI VIDEO FLAGGER")
    logger.info(f"Input:  {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info("=" * 60)

    summary = flag_inventory(input_path, output_path)

    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info(f"Total videos:   {summary['total_videos']:,}")
    logger.info(f"Flagged videos: {summary['flagged_videos']:,}")
    logger.info(f"Flag rate:      {summary['flag_rate']:.1%}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
