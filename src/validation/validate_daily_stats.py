"""
validate_daily_stats.py
-----------------------
Lightweight validator for daily channel stats panel files.

Runs after daily_stats.py completes. Checks row counts, schema,
impossible values, and day-over-day outliers.

Usage:
    python -m src.validation.validate_daily_stats --panel gender_gap [--date 2026-02-22]
    python -m src.validation.validate_daily_stats --panel ai_census [--date 2026-02-22]
    python -m src.validation.validate_daily_stats --panel gender_gap --test

Exit codes: 0=PASS, 1=WARNINGS, 2=ERRORS

Author: Katie Apker
Created: Feb 22, 2026
"""

import argparse
import csv
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Panel configuration
# ---------------------------------------------------------------------------

PANEL_CONFIG = {
    "gender_gap": {
        "expected_rows": 9760,
        "stats_dir": config.CHANNEL_STATS_DIR,
    },
    "ai_census": {
        "expected_rows": 50010,
        "stats_dir": config.CHANNEL_STATS_DIR / "ai_census",
    },
}

TOLERANCE = 0.01  # 1%
REQUIRED_FIELDS = config.CHANNEL_STATS_FIELDS
NUMERIC_FIELDS = ["view_count", "subscriber_count", "video_count"]
MAX_SUBSCRIBER_DROP_PCT = 0.50


# ---------------------------------------------------------------------------
# Validation result container
# ---------------------------------------------------------------------------

class ValidationResult(object):
    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"

    def __init__(self, name, status, message, details=None):
        # type: (str, str, str, Optional[Dict]) -> None
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}


# ---------------------------------------------------------------------------
# Core validation logic
# ---------------------------------------------------------------------------

def validate_panel(panel_name, date_str):
    # type: (str, str) -> List[ValidationResult]
    """Run all validation checks on a daily stats file."""

    panel = PANEL_CONFIG[panel_name]
    stats_dir = panel["stats_dir"]
    expected_rows = panel["expected_rows"]

    file_path = stats_dir / "{}.csv".format(date_str)
    results = []  # type: List[ValidationResult]

    # ------------------------------------------------------------------
    # Check 1: File exists
    # ------------------------------------------------------------------
    if not file_path.exists():
        results.append(ValidationResult(
            "file_exists", ValidationResult.ERROR,
            "File not found: {}".format(file_path),
        ))
        return results

    # ------------------------------------------------------------------
    # Read the file
    # ------------------------------------------------------------------
    rows = []  # type: List[Dict[str, str]]
    header = []  # type: List[str]
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            header = reader.fieldnames or []
            for row in reader:
                rows.append(row)
    except Exception as e:
        results.append(ValidationResult(
            "file_readable", ValidationResult.ERROR,
            "Failed to read file: {}".format(e),
        ))
        return results

    row_count = len(rows)

    # ------------------------------------------------------------------
    # Check 2: Row count within ±1% of expected
    # ------------------------------------------------------------------
    lower = int(expected_rows * (1 - TOLERANCE))
    upper = int(expected_rows * (1 + TOLERANCE))
    if lower <= row_count <= upper:
        results.append(ValidationResult(
            "row_count", ValidationResult.PASS,
            "{} rows (expected {} +/-1%)".format(row_count, expected_rows),
        ))
    else:
        severity = ValidationResult.WARNING if row_count > 0 else ValidationResult.ERROR
        results.append(ValidationResult(
            "row_count", severity,
            "{} rows, expected [{}, {}]".format(row_count, lower, upper),
            {"actual": row_count, "expected": expected_rows},
        ))

    # ------------------------------------------------------------------
    # Check 3: Required columns present
    # ------------------------------------------------------------------
    missing_cols = set(REQUIRED_FIELDS) - set(header)
    if missing_cols:
        results.append(ValidationResult(
            "schema_columns", ValidationResult.ERROR,
            "Missing columns: {}".format(sorted(missing_cols)),
        ))
    else:
        results.append(ValidationResult(
            "schema_columns", ValidationResult.PASS,
            "All {} required columns present".format(len(REQUIRED_FIELDS)),
        ))

    # ------------------------------------------------------------------
    # Check 4: No null/empty channel_ids
    # ------------------------------------------------------------------
    null_ids = sum(1 for r in rows if not r.get("channel_id", "").strip())
    if null_ids > 0:
        results.append(ValidationResult(
            "null_channel_ids", ValidationResult.ERROR,
            "{} rows with null/empty channel_id".format(null_ids),
        ))
    else:
        results.append(ValidationResult(
            "null_channel_ids", ValidationResult.PASS,
            "No null channel_ids",
        ))

    # ------------------------------------------------------------------
    # Check 5: No negative counts
    # ------------------------------------------------------------------
    negative_count = 0
    negative_examples = []  # type: List[str]
    for r in rows:
        for field in NUMERIC_FIELDS:
            val = r.get(field, "")
            if val and val.strip():
                try:
                    if int(val) < 0:
                        negative_count += 1
                        if len(negative_examples) < 3:
                            negative_examples.append(
                                "{}: {}={}".format(r.get("channel_id", "?"), field, val)
                            )
                except (ValueError, TypeError):
                    pass

    if negative_count > 0:
        results.append(ValidationResult(
            "negative_values", ValidationResult.ERROR,
            "{} negative values found".format(negative_count),
            {"examples": negative_examples},
        ))
    else:
        results.append(ValidationResult(
            "negative_values", ValidationResult.PASS,
            "No negative count values",
        ))

    # ------------------------------------------------------------------
    # Check 6: Schema dtypes — counts numeric, timestamps parseable
    # ------------------------------------------------------------------
    non_numeric = 0
    non_numeric_examples = []  # type: List[str]
    for r in rows:
        for field in NUMERIC_FIELDS:
            val = r.get(field, "")
            if val and val.strip():
                try:
                    int(val)
                except (ValueError, TypeError):
                    non_numeric += 1
                    if len(non_numeric_examples) < 3:
                        non_numeric_examples.append(
                            "{}: {}='{}'".format(r.get("channel_id", "?"), field, val)
                        )

    unparseable_dates = 0
    for r in rows:
        scraped_at = r.get("scraped_at", "")
        if scraped_at and scraped_at.strip():
            try:
                # Python 3.9 doesn't have datetime.fromisoformat for all formats;
                # our timestamps are like 2026-02-22T18:01:48.958759 which works fine.
                datetime.fromisoformat(scraped_at)
            except (ValueError, TypeError):
                unparseable_dates += 1

    dtype_issues = non_numeric + unparseable_dates
    if dtype_issues > 0:
        msg_parts = []
        if non_numeric:
            msg_parts.append("{} non-numeric count values".format(non_numeric))
        if unparseable_dates:
            msg_parts.append("{} unparseable timestamps".format(unparseable_dates))
        results.append(ValidationResult(
            "schema_dtypes", ValidationResult.WARNING,
            "; ".join(msg_parts),
            {"non_numeric_examples": non_numeric_examples},
        ))
    else:
        results.append(ValidationResult(
            "schema_dtypes", ValidationResult.PASS,
            "All counts numeric, all timestamps parseable",
        ))

    # ------------------------------------------------------------------
    # Check 7: Subscriber drops >50% vs previous day
    # ------------------------------------------------------------------
    prev_date = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    prev_path = stats_dir / "{}.csv".format(prev_date)

    if prev_path.exists():
        prev_subs = {}  # type: Dict[str, int]
        try:
            with open(prev_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for r in reader:
                    cid = r.get("channel_id", "").strip()
                    sub = r.get("subscriber_count", "")
                    if cid and sub and sub.strip():
                        try:
                            prev_subs[cid] = int(sub)
                        except (ValueError, TypeError):
                            pass
        except Exception:
            prev_subs = {}

        big_drops = []  # type: List[str]
        for r in rows:
            cid = r.get("channel_id", "").strip()
            sub_str = r.get("subscriber_count", "")
            if cid and cid in prev_subs and sub_str and sub_str.strip():
                try:
                    curr_sub = int(sub_str)
                    prev_sub = prev_subs[cid]
                    if prev_sub > 0 and curr_sub < prev_sub * (1 - MAX_SUBSCRIBER_DROP_PCT):
                        drop_pct = (prev_sub - curr_sub) / prev_sub * 100
                        big_drops.append(
                            "{}: {} -> {} (-{:.1f}%)".format(cid, prev_sub, curr_sub, drop_pct)
                        )
                except (ValueError, TypeError):
                    pass

        if big_drops:
            results.append(ValidationResult(
                "subscriber_drops", ValidationResult.WARNING,
                "{} channels with >50% subscriber drop".format(len(big_drops)),
                {"examples": big_drops[:5]},
            ))
        else:
            results.append(ValidationResult(
                "subscriber_drops", ValidationResult.PASS,
                "No extreme subscriber drops vs previous day",
            ))
    else:
        results.append(ValidationResult(
            "subscriber_drops", ValidationResult.PASS,
            "No previous day file ({}) -- skipping day-over-day check".format(prev_date),
        ))

    return results


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def format_report(panel_name, date_str, results):
    # type: (str, str, List[ValidationResult]) -> str
    """Format validation results as a text report."""

    pass_count = sum(1 for r in results if r.status == ValidationResult.PASS)
    warn_count = sum(1 for r in results if r.status == ValidationResult.WARNING)
    err_count = sum(1 for r in results if r.status == ValidationResult.ERROR)

    if err_count > 0:
        overall = "ERRORS"
    elif warn_count > 0:
        overall = "WARNINGS"
    else:
        overall = "PASS"

    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    lines = [
        "=" * 60,
        "  DAILY STATS VALIDATION  |  {}  |  {}".format(overall, ts),
        "  Panel: {}  |  Date: {}".format(panel_name, date_str),
        "=" * 60,
        "",
        "  {} PASS  |  {} WARNING  |  {} ERROR".format(pass_count, warn_count, err_count),
        "",
        "-" * 60,
    ]

    badges = {
        ValidationResult.PASS: "[PASS  ]",
        ValidationResult.WARNING: "[ WARN ]",
        ValidationResult.ERROR: "[ERROR!]",
    }

    for r in results:
        lines.append("  {}  {}".format(badges[r.status], r.name))
        lines.append("           {}".format(r.message))
        if r.details and r.status != ValidationResult.PASS:
            for k, v in r.details.items():
                if isinstance(v, list):
                    for item in v[:5]:
                        lines.append("             - {}".format(item))
                else:
                    lines.append("             {}: {}".format(k, v))
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def overall_exit_code(results):
    # type: (List[ValidationResult]) -> int
    """Return exit code: 0=PASS, 1=WARNINGS, 2=ERRORS."""
    statuses = [r.status for r in results]
    if ValidationResult.ERROR in statuses:
        return 2
    if ValidationResult.WARNING in statuses:
        return 1
    return 0


def save_report(report_text, panel_name, date_str):
    # type: (str, str, str) -> Path
    """Save report to data/logs/."""
    config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
    date_compact = date_str.replace("-", "")
    output_path = config.LOGS_DIR / "daily_stats_validation_{}_{}.log".format(
        panel_name, date_compact
    )
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)
    return output_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    # type: () -> None
    parser = argparse.ArgumentParser(
        description="Validate daily channel stats panel files"
    )
    parser.add_argument(
        "--panel", required=True, choices=list(PANEL_CONFIG.keys()),
        help="Panel to validate: gender_gap or ai_census",
    )
    parser.add_argument(
        "--date", type=str, default=None,
        help="Date to validate (YYYY-MM-DD). Defaults to today UTC.",
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Test mode: run validation but don't save report file",
    )
    args = parser.parse_args()

    # Resolve date
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            print("Error: --date must be YYYY-MM-DD format", file=sys.stderr)
            sys.exit(2)
        date_str = args.date
    else:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Validate
    results = validate_panel(args.panel, date_str)

    # Report
    report = format_report(args.panel, date_str, results)
    print(report)

    if not args.test:
        output_path = save_report(report, args.panel, date_str)
        logger.info("Report saved to %s", output_path)

    sys.exit(overall_exit_code(results))


if __name__ == "__main__":
    main()
