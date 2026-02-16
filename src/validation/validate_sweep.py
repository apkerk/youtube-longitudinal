"""
validate_sweep.py
-----------------
Data Validation Module

Performs automated quality checks on sweep data:
- Views monotonically increasing (flags anomalies)
- Subscriber drops > 50% (flags for review)
- Video count decreases (tracks deletions)
- Duplicate channel IDs (error)
- Missing required fields (error)
- Status transitions logged

Usage:
    python -m src.validation.validate_sweep --current sweep_20260202.csv --previous sweep_20260201.csv
    python -m src.validation.validate_sweep --directory data/channels/stream_a/

Author: Katie Apker
Last Updated: Feb 02, 2026
"""

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationReport:
    """Container for validation results."""
    
    def __init__(self):
        self.errors: List[Dict] = []
        self.warnings: List[Dict] = []
        self.info: List[Dict] = []
        self.stats: Dict = {}
        
    def add_error(self, check: str, channel_id: str, message: str, details: Dict = None):
        self.errors.append({
            'severity': 'ERROR',
            'check': check,
            'channel_id': channel_id,
            'message': message,
            'details': details or {}
        })
        
    def add_warning(self, check: str, channel_id: str, message: str, details: Dict = None):
        self.warnings.append({
            'severity': 'WARNING',
            'check': check,
            'channel_id': channel_id,
            'message': message,
            'details': details or {}
        })
        
    def add_info(self, check: str, channel_id: str, message: str, details: Dict = None):
        self.info.append({
            'severity': 'INFO',
            'check': check,
            'channel_id': channel_id,
            'message': message,
            'details': details or {}
        })
        
    def is_valid(self) -> bool:
        """Return True if no errors found."""
        return len(self.errors) == 0
        
    def summary(self) -> str:
        """Generate summary string."""
        lines = [
            "=" * 60,
            "VALIDATION REPORT",
            "=" * 60,
            f"Errors:   {len(self.errors)}",
            f"Warnings: {len(self.warnings)}",
            f"Info:     {len(self.info)}",
            "-" * 60,
        ]
        
        if self.stats:
            lines.append("STATISTICS:")
            for key, value in self.stats.items():
                lines.append(f"  {key}: {value}")
            lines.append("-" * 60)
            
        if self.errors:
            lines.append("ERRORS:")
            for e in self.errors[:10]:  # Limit displayed
                lines.append(f"  [{e['check']}] {e['channel_id']}: {e['message']}")
            if len(self.errors) > 10:
                lines.append(f"  ... and {len(self.errors) - 10} more errors")
            lines.append("-" * 60)
            
        if self.warnings:
            lines.append("WARNINGS:")
            for w in self.warnings[:10]:
                lines.append(f"  [{w['check']}] {w['channel_id']}: {w['message']}")
            if len(self.warnings) > 10:
                lines.append(f"  ... and {len(self.warnings) - 10} more warnings")
                
        lines.append("=" * 60)
        return "\n".join(lines)
        
    def save_to_csv(self, output_path: Path):
        """Save all findings to CSV."""
        all_findings = self.errors + self.warnings + self.info
        
        if not all_findings:
            logger.info("No findings to save")
            return
            
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['severity', 'check', 'channel_id', 'message', 'details']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for finding in all_findings:
                row = {
                    'severity': finding['severity'],
                    'check': finding['check'],
                    'channel_id': finding['channel_id'],
                    'message': finding['message'],
                    'details': str(finding['details'])
                }
                writer.writerow(row)
                
        logger.info(f"💾 Saved validation report to {output_path}")


class SweepValidator:
    """
    Validates sweep data for quality and consistency.
    """
    
    def __init__(self, thresholds: Dict = None):
        """
        Initialize validator.
        
        Args:
            thresholds: Optional custom thresholds (uses config defaults if not provided)
        """
        self.thresholds = thresholds or config.VALIDATION_THRESHOLDS
        
    def validate_single_sweep(self, sweep_data: List[Dict]) -> ValidationReport:
        """
        Validate a single sweep file (standalone checks).
        
        Args:
            sweep_data: List of channel data dictionaries
            
        Returns:
            ValidationReport with findings
        """
        report = ValidationReport()
        
        # Check for duplicates
        self._check_duplicates(sweep_data, report)
        
        # Check for missing required fields
        self._check_required_fields(sweep_data, report)
        
        # Calculate basic stats
        report.stats['total_channels'] = len(sweep_data)
        report.stats['active'] = sum(1 for ch in sweep_data if ch.get('status') == 'active')
        report.stats['not_found'] = sum(1 for ch in sweep_data if ch.get('status') == 'not_found')
        
        return report
        
    def validate_sweep_pair(
        self,
        current_sweep: List[Dict],
        previous_sweep: List[Dict]
    ) -> ValidationReport:
        """
        Validate current sweep against previous sweep.
        
        Args:
            current_sweep: Current sweep data
            previous_sweep: Previous sweep data
            
        Returns:
            ValidationReport with findings
        """
        report = self.validate_single_sweep(current_sweep)
        
        # Build lookup for previous data
        previous_by_id = {ch['channel_id']: ch for ch in previous_sweep}
        
        for current in current_sweep:
            channel_id = current['channel_id']
            previous = previous_by_id.get(channel_id)
            
            if not previous:
                report.add_info(
                    check='new_channel',
                    channel_id=channel_id,
                    message='Channel not in previous sweep (new addition)'
                )
                continue
                
            # Skip if channel not found
            if current.get('status') == 'not_found':
                report.add_warning(
                    check='channel_missing',
                    channel_id=channel_id,
                    message='Channel no longer accessible'
                )
                continue
                
            # View count validation
            self._check_view_count(current, previous, report)
            
            # Subscriber validation
            self._check_subscriber_count(current, previous, report)
            
            # Video count validation
            self._check_video_count(current, previous, report)
            
            # Policy flag changes
            self._check_policy_changes(current, previous, report)
            
        return report
        
    def _check_duplicates(self, data: List[Dict], report: ValidationReport):
        """Check for duplicate channel IDs."""
        seen = set()
        for ch in data:
            cid = ch.get('channel_id')
            if cid in seen:
                report.add_error(
                    check='duplicate',
                    channel_id=cid,
                    message='Duplicate channel ID found'
                )
            else:
                seen.add(cid)
                
    def _check_required_fields(self, data: List[Dict], report: ValidationReport):
        """Check for missing required fields."""
        required = ['channel_id', 'scraped_at']
        
        for ch in data:
            for field in required:
                if not ch.get(field):
                    report.add_error(
                        check='missing_field',
                        channel_id=ch.get('channel_id', 'UNKNOWN'),
                        message=f'Missing required field: {field}'
                    )
                    
    def _check_view_count(self, current: Dict, previous: Dict, report: ValidationReport):
        """Check view count for anomalies."""
        curr_views = int(current.get('view_count', 0) or 0)
        prev_views = int(previous.get('view_count', 0) or 0)
        
        # Views should never decrease (unless data error)
        if curr_views < prev_views:
            report.add_warning(
                check='view_decrease',
                channel_id=current['channel_id'],
                message=f'View count decreased from {prev_views} to {curr_views}',
                details={'previous': prev_views, 'current': curr_views}
            )
            
    def _check_subscriber_count(self, current: Dict, previous: Dict, report: ValidationReport):
        """Check subscriber count for anomalies."""
        curr_subs = int(current.get('subscriber_count', 0) or 0)
        prev_subs = int(previous.get('subscriber_count', 0) or 0)
        
        if prev_subs > 0:
            drop_pct = (prev_subs - curr_subs) / prev_subs
            
            if drop_pct > self.thresholds['max_subscriber_drop_pct']:
                report.add_warning(
                    check='subscriber_drop',
                    channel_id=current['channel_id'],
                    message=f'Subscriber count dropped {drop_pct:.1%} ({prev_subs} → {curr_subs})',
                    details={'previous': prev_subs, 'current': curr_subs, 'drop_pct': drop_pct}
                )
                
    def _check_video_count(self, current: Dict, previous: Dict, report: ValidationReport):
        """Check video count for deletions."""
        curr_videos = int(current.get('video_count', 0) or 0)
        prev_videos = int(previous.get('video_count', 0) or 0)
        
        if curr_videos < prev_videos:
            deleted_count = prev_videos - curr_videos
            report.add_info(
                check='video_deleted',
                channel_id=current['channel_id'],
                message=f'{deleted_count} video(s) deleted/removed',
                details={'previous': prev_videos, 'current': curr_videos}
            )
            
    def _check_policy_changes(self, current: Dict, previous: Dict, report: ValidationReport):
        """Check for policy flag changes."""
        # made_for_kids change
        curr_mfk = current.get('made_for_kids')
        prev_mfk = previous.get('made_for_kids')
        
        if curr_mfk != prev_mfk:
            report.add_info(
                check='made_for_kids_changed',
                channel_id=current['channel_id'],
                message=f'made_for_kids changed from {prev_mfk} to {curr_mfk}',
                details={'previous': prev_mfk, 'current': curr_mfk}
            )


def load_csv(filepath: Path) -> List[Dict]:
    """Load CSV file into list of dictionaries."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def find_sweep_files(directory: Path) -> List[Path]:
    """Find all sweep files in a directory, sorted by date."""
    return sorted(directory.glob("sweep_*.csv"))


def main():
    """Main entry point for validation."""
    parser = argparse.ArgumentParser(description="Sweep Data Validation")
    parser.add_argument('--current', type=str, help='Current sweep CSV file')
    parser.add_argument('--previous', type=str, help='Previous sweep CSV file')
    parser.add_argument('--directory', type=str, 
                        help='Directory to validate all sweeps')
    parser.add_argument('--output', type=str, help='Output CSV for findings')
    args = parser.parse_args()
    
    config.ensure_directories()
    validator = SweepValidator()
    
    if args.current and args.previous:
        # Compare two specific files
        current = load_csv(Path(args.current))
        previous = load_csv(Path(args.previous))
        
        report = validator.validate_sweep_pair(current, previous)
        print(report.summary())
        
        if args.output:
            report.save_to_csv(Path(args.output))
            
    elif args.directory:
        # Validate all sweep pairs in directory
        directory = Path(args.directory)
        sweep_files = find_sweep_files(directory)
        
        if len(sweep_files) < 2:
            logger.warning("Need at least 2 sweep files for comparison")
            if sweep_files:
                current = load_csv(sweep_files[0])
                report = validator.validate_single_sweep(current)
                print(report.summary())
            return
            
        # Compare consecutive sweeps
        for i in range(1, len(sweep_files)):
            previous_file = sweep_files[i-1]
            current_file = sweep_files[i]
            
            logger.info(f"Comparing {previous_file.name} → {current_file.name}")
            
            previous = load_csv(previous_file)
            current = load_csv(current_file)
            
            report = validator.validate_sweep_pair(current, previous)
            print(report.summary())
            
            if args.output:
                output_path = Path(args.output).parent / f"validation_{current_file.stem}.csv"
                report.save_to_csv(output_path)
                
    elif args.current:
        # Validate single file
        current = load_csv(Path(args.current))
        report = validator.validate_single_sweep(current)
        print(report.summary())
        
        if args.output:
            report.save_to_csv(Path(args.output))
            
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

