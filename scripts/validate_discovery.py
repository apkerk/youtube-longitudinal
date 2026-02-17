"""
validate_discovery.py
---------------------
Validate discovery output CSVs from new creator cohort streams.

Checks:
  1. Schema: all CHANNEL_INITIAL_FIELDS columns present
  2. Uniqueness: no duplicate channel_ids
  3. Completeness: no null channel_ids
  4. Provenance: stream_type matches expected stream
  5. Cohort dates: published_at >= cutoff (streams A/A' only)
  6. Distributions: subscriber/view count summary statistics

Usage:
    python scripts/validate_discovery.py INPUT_CSV --stream stream_b
    python scripts/validate_discovery.py INPUT_CSV --stream stream_d
"""

import argparse
import csv
import logging
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

COHORT_FILTERED_STREAMS = {"stream_a", "stream_a_prime"}

SUBSCRIBER_TIERS = [
    (0, 1_000, "<1K"),
    (1_000, 10_000, "1K-10K"),
    (10_000, 100_000, "10K-100K"),
    (100_000, 1_000_000, "100K-1M"),
    (1_000_000, float("inf"), ">1M"),
]


def load_csv(filepath: Path) -> List[Dict[str, str]]:
    """Load a discovery CSV."""
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def check_schema(rows: List[Dict[str, str]], filepath: Path) -> List[str]:
    """Verify all CHANNEL_INITIAL_FIELDS columns are present."""
    if not rows:
        return [f"ERROR: File is empty: {filepath}"]

    actual = set(rows[0].keys())
    expected = set(config.CHANNEL_INITIAL_FIELDS)
    errors = []

    missing = expected - actual
    if missing:
        errors.append(f"ERROR: Missing columns: {sorted(missing)}")

    extra = actual - expected
    if extra:
        # Extra columns are a warning, not an error
        logger.warning("Extra columns (not in schema): %s", sorted(extra))

    return errors


def check_duplicates(rows: List[Dict[str, str]]) -> List[str]:
    """Check for duplicate channel_ids."""
    seen: Dict[str, int] = {}
    for i, row in enumerate(rows, start=2):  # row 2 = first data row
        cid = row.get("channel_id", "").strip()
        if cid in seen:
            return [
                f"ERROR: Duplicate channel_id '{cid}' at rows {seen[cid]} and {i} "
                f"(total duplicates not enumerated; fix first occurrence)"
            ]
        if cid:
            seen[cid] = i

    # Full count
    all_ids = [r.get("channel_id", "").strip() for r in rows if r.get("channel_id", "").strip()]
    unique = set(all_ids)
    if len(all_ids) != len(unique):
        dupes = len(all_ids) - len(unique)
        return [f"ERROR: {dupes} duplicate channel_id(s) found"]

    return []


def check_null_ids(rows: List[Dict[str, str]]) -> List[str]:
    """Check for null/empty channel_id values."""
    nulls = sum(1 for r in rows if not r.get("channel_id", "").strip())
    if nulls:
        return [f"ERROR: {nulls} row(s) with null/empty channel_id"]
    return []


def check_stream_type(rows: List[Dict[str, str]], expected: Optional[str]) -> List[str]:
    """Verify stream_type matches expectation."""
    if not expected:
        return []

    mismatches = 0
    for row in rows:
        st = row.get("stream_type", "").strip()
        if st and st != expected:
            mismatches += 1

    if mismatches:
        return [f"WARNING: {mismatches} row(s) with stream_type != '{expected}'"]
    return []


def check_cohort_dates(
    rows: List[Dict[str, str]], cutoff: str, stream: Optional[str]
) -> List[str]:
    """Check published_at >= cutoff for cohort-filtered streams."""
    if stream and stream not in COHORT_FILTERED_STREAMS:
        logger.info(
            "Cohort date check skipped (stream %s has no date filter)", stream
        )
        return []

    violations = 0
    for row in rows:
        pub = row.get("published_at", "").strip()
        if pub and pub < cutoff:
            violations += 1

    if violations:
        return [
            f"WARNING: {violations} channel(s) with published_at before {cutoff}"
        ]
    return []


def compute_distributions(rows: List[Dict[str, str]]) -> str:
    """Compute subscriber/view count summary statistics."""
    lines = []

    for field in ("subscriber_count", "view_count", "video_count"):
        values = []
        for row in rows:
            raw = row.get(field, "").strip()
            if raw:
                try:
                    values.append(int(raw))
                except ValueError:
                    pass

        if not values:
            lines.append(f"  {field}: no valid data")
            continue

        values.sort()
        n = len(values)
        q1_idx = n // 4
        q3_idx = (3 * n) // 4

        lines.append(
            f"  {field} (n={n}): "
            f"min={values[0]:,}  p25={values[q1_idx]:,}  "
            f"median={statistics.median(values):,.0f}  "
            f"p75={values[q3_idx]:,}  max={values[-1]:,}  "
            f"mean={statistics.mean(values):,.0f}"
        )

    # Subscriber tier breakdown
    sub_values = []
    for row in rows:
        raw = row.get("subscriber_count", "").strip()
        if raw:
            try:
                sub_values.append(int(raw))
            except ValueError:
                pass

    if sub_values:
        lines.append("\n  Subscriber tiers:")
        for lo, hi, label in SUBSCRIBER_TIERS:
            count = sum(1 for v in sub_values if lo <= v < hi)
            pct = 100 * count / len(sub_values)
            lines.append(f"    {label:>8s}: {count:>6,} ({pct:5.1f}%)")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate discovery output CSVs"
    )
    parser.add_argument("input_csv", type=str, help="Path to discovery CSV")
    parser.add_argument(
        "--stream",
        type=str,
        default=None,
        help="Expected stream name (e.g., stream_b)",
    )
    parser.add_argument(
        "--cohort-cutoff",
        type=str,
        default="2026-01-01",
        help="Cohort cutoff date YYYY-MM-DD (default: 2026-01-01)",
    )
    args = parser.parse_args()

    filepath = Path(args.input_csv)
    if not filepath.is_absolute():
        filepath = PROJECT_ROOT / filepath

    if not filepath.exists():
        logger.error("File not found: %s", filepath)
        sys.exit(1)

    logger.info("Validating: %s", filepath.name)

    rows = load_csv(filepath)
    logger.info("Loaded %d rows", len(rows))

    errors: List[str] = []
    warnings: List[str] = []

    # Schema check
    schema_issues = check_schema(rows, filepath)
    errors.extend(i for i in schema_issues if i.startswith("ERROR"))

    # Duplicate check
    errors.extend(check_duplicates(rows))

    # Null ID check
    errors.extend(check_null_ids(rows))

    # Stream type check
    stream_issues = check_stream_type(rows, args.stream)
    warnings.extend(stream_issues)

    # Cohort date check
    date_issues = check_cohort_dates(rows, args.cohort_cutoff, args.stream)
    warnings.extend(date_issues)

    # Report
    print(f"\n{'='*60}")
    print(f"VALIDATION REPORT: {filepath.name}")
    print(f"{'='*60}")
    print(f"Rows: {len(rows)}")

    unique_ids = len(set(r.get('channel_id', '').strip() for r in rows if r.get('channel_id', '').strip()))
    print(f"Unique channel_ids: {unique_ids}")

    if args.stream:
        print(f"Expected stream: {args.stream}")

    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e}")
    else:
        print("\nNo errors found.")

    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  {w}")

    print(f"\nDistributions:")
    print(compute_distributions(rows))
    print(f"{'='*60}\n")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
