"""
test_checkpoint_behavior.py
---------------------------
Regression test for enumerate_videos.py checkpoint lifecycle.

Tests three exit modes to verify the invariant:
  - COMPLETE  → checkpoint deleted (all channels done)
  - MAX_RUNTIME → checkpoint retained (partial run, must resume)
  - QUOTA_EXHAUSTED → checkpoint retained (partial run, must resume)

Run with: python3 -m src.validation.test_checkpoint_behavior

Author: Katie Apker
Last Updated: 2026-03-11
"""

import csv
import json
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src/ to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from collection.enumerate_videos import enumerate_all_channels, save_checkpoint
from youtube_api import QuotaExhaustedError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_mock_youtube(videos_per_channel=3, raise_quota_on_channel=None):
    """
    Return a mock YouTube service whose get_all_video_ids yields fake videos.

    Args:
        videos_per_channel: Number of fake videos returned per channel.
        raise_quota_on_channel: If set, raises QuotaExhaustedError when
            that channel_id is requested (simulates mid-run quota hit).
    """
    def fake_get_videos(youtube, playlist_id, channel_id):
        if raise_quota_on_channel and channel_id == raise_quota_on_channel:
            raise QuotaExhaustedError("quota exhausted")
        videos = [
            {
                'video_id': f'vid_{channel_id}_{i}',
                'channel_id': channel_id,
                'published_at': '2026-01-01T00:00:00Z',
                'title': f'Video {i}',
            }
            for i in range(videos_per_channel)
        ]
        return videos, None

    return MagicMock(), fake_get_videos


def run_enumeration(channel_ids, output_path, checkpoint_path,
                    videos_per_channel=3, raise_quota_on=None,
                    max_runtime=None):
    """Invoke enumerate_all_channels with mocked API calls."""
    mock_yt, fake_get = make_mock_youtube(videos_per_channel, raise_quota_on)

    with patch('collection.enumerate_videos.get_all_video_ids', side_effect=fake_get):
        total = enumerate_all_channels(
            youtube=mock_yt,
            channel_ids=channel_ids,
            output_path=output_path,
            checkpoint_path=checkpoint_path,
            max_runtime=max_runtime,
        )
    return total


def load_checkpoint(checkpoint_path):
    if not checkpoint_path.exists():
        return None
    with open(checkpoint_path) as f:
        return json.load(f)


def count_csv_rows(path):
    if not path.exists():
        return 0
    with open(path) as f:
        return sum(1 for _ in csv.DictReader(f))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

PASS = "PASS"
FAIL = "FAIL"


def test_complete_clears_checkpoint():
    """When all channels finish, checkpoint must be deleted."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "inventory.csv"
        chk = Path(tmp) / ".enumerate_inventory_checkpoint.json"
        channels = ["UCaaa", "UCbbb", "UCccc"]

        run_enumeration(channels, out, chk)

        # All channels done → checkpoint should be gone
        if chk.exists():
            data = load_checkpoint(chk)
            return FAIL, f"checkpoint still exists with {len(data['completed_channels'])} channels after complete run"

        rows = count_csv_rows(out)
        if rows != len(channels) * 3:
            return FAIL, f"expected {len(channels)*3} video rows, got {rows}"

        return PASS, f"checkpoint deleted, {rows} videos written"


def test_max_runtime_retains_checkpoint():
    """When max_runtime fires mid-run, checkpoint must be retained for resume."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "inventory.csv"
        chk = Path(tmp) / ".enumerate_inventory_checkpoint.json"

        channels = [f"UC{i:03d}" for i in range(10)]

        # Patch time.time so it advances 2 seconds after the first channel,
        # triggering the max_runtime=1 guard on the second iteration.
        call_count = [0]
        base = time.time()

        def fake_time():
            call_count[0] += 1
            # First few calls (start_time capture + first-channel check): return base.
            # After channel 0 finishes, advance clock by 2s so runtime limit fires.
            if call_count[0] <= 3:
                return base
            return base + 2.0

        with patch('collection.enumerate_videos.time.time', side_effect=fake_time):
            run_enumeration(channels, out, chk, max_runtime=1)

        if not chk.exists():
            return FAIL, "checkpoint was deleted after max_runtime exit — bug still present"

        data = load_checkpoint(chk)
        n_done = len(data['completed_channels'])
        if n_done >= len(channels):
            return FAIL, f"checkpoint says all {n_done} channels done but max_runtime should have stopped early"

        return PASS, f"checkpoint retained with {n_done}/{len(channels)} channels done"


def test_quota_exhausted_retains_checkpoint():
    """When quota is exhausted mid-run, checkpoint must be retained for resume."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "inventory.csv"
        chk = Path(tmp) / ".enumerate_inventory_checkpoint.json"

        channels = ["UCaaa", "UCbbb", "UCccc", "UCddd"]
        # Quota hits on the 3rd channel; first two should complete
        run_enumeration(channels, out, chk, raise_quota_on="UCccc")

        if not chk.exists():
            return FAIL, "checkpoint was deleted after quota exit"

        data = load_checkpoint(chk)
        completed = data['completed_channels']
        if "UCaaa" not in completed or "UCbbb" not in completed:
            return FAIL, f"expected UCaaa and UCbbb in checkpoint, got: {completed}"
        if "UCccc" in completed or "UCddd" in completed:
            return FAIL, f"UCccc/UCddd should not be checkpointed (quota hit before/at UCccc)"

        return PASS, f"checkpoint retained with {len(completed)}/4 channels done"


def test_resume_appends_not_overwrites():
    """A resumed run must append to existing CSV and skip completed channels."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "inventory.csv"
        chk = Path(tmp) / ".enumerate_inventory_checkpoint.json"

        channels = [f"UC{i:03d}" for i in range(6)]

        # First run: do 3 channels via checkpoint injection
        completed_first = channels[:3]
        save_checkpoint(chk, {'completed_channels': completed_first})

        # Write fake CSV with the first 3 channels already done (3 videos each)
        with open(out, 'w', newline='') as f:
            import csv as _csv
            writer = _csv.DictWriter(f, fieldnames=['video_id', 'channel_id', 'published_at', 'title', 'scraped_at'])
            writer.writeheader()
            for cid in completed_first:
                for i in range(3):
                    writer.writerow({'video_id': f'vid_{cid}_{i}', 'channel_id': cid,
                                     'published_at': '2026-01-01T00:00:00Z', 'title': f'V{i}',
                                     'scraped_at': '2026-01-01'})

        # Second run: completes remaining 3
        run_enumeration(channels, out, chk)

        # Checkpoint should be gone (all 6 done)
        if chk.exists():
            return FAIL, "checkpoint should be deleted after full completion"

        rows = count_csv_rows(out)
        expected = len(channels) * 3  # 18 total
        if rows != expected:
            return FAIL, f"expected {expected} rows after resume, got {rows} (duplicate or missing writes?)"

        return PASS, f"resume appended correctly, {rows} total rows, checkpoint deleted"


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

TESTS = [
    ("complete run clears checkpoint", test_complete_clears_checkpoint),
    ("max_runtime retains checkpoint", test_max_runtime_retains_checkpoint),
    ("quota exhausted retains checkpoint", test_quota_exhausted_retains_checkpoint),
    ("resume appends not overwrites", test_resume_appends_not_overwrites),
]


def main():
    print("=" * 60)
    print("enumerate_videos checkpoint regression tests")
    print("=" * 60)

    results = []
    for name, fn in TESTS:
        try:
            status, detail = fn()
        except Exception as e:
            status, detail = FAIL, f"exception: {e}"
        mark = "✓" if status == PASS else "✗"
        print(f"  {mark} {name}")
        if status == FAIL:
            print(f"      → {detail}")
        results.append(status)

    print()
    n_pass = results.count(PASS)
    n_fail = results.count(FAIL)
    print(f"Results: {n_pass}/{len(results)} passed", "— ALL GOOD" if n_fail == 0 else f"— {n_fail} FAILED")
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
