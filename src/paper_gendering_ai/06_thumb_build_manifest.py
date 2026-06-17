#!/usr/bin/env python3
"""06_thumb_build_manifest.py — KE thumbnail-gender pipeline step 1 (manifest).

Builds the image-fetch manifest for the Knowledge Economy (KE) Census gender measure.
Mirrors the validated dissertation pipeline (do-file 72) but, unlike that build, the KE
panel stores no per-slot thumbnail URLs in the channel file — only the channel AVATAR
(profile_picture_url). Video thumbnail URLs are therefore reconstructed deterministically
from the video inventory:  https://i.ytimg.com/vi/{video_id}/hqdefault.jpg .

SAMPLING RULE (Katie 2026-06-17, maximize face-bearing images):
  per channel = avatar + newest 5 + oldest 5 + random 5 video thumbnails.
  - "newest"/"oldest" by published_at; "random" sampled with a FIXED seed from the remaining
    videos (deduped against newest/oldest so a channel never re-codes the same video_id).
  - If a channel has < 15 videos, take all of them (still split into newest/oldest, no random).
  Validation shows reliability rises 92-95% -> 97% as more image-blocks carry a face, so the
  design deliberately front-loads face-bearing slots (avatar + many video thumbs).

The inventory is ~7 GB — it is STREAMED once, never loaded whole, never counted with wc -l.

INPUT : data/processed/ke_analysis_base.csv                 (channel universe; read-only)
        data/channels/knowledge_economy/ke_20260418.csv     (avatar urls; NUL-safe read)
        data/video_inventory/knowledge_economy_inventory.csv (video_id/channel_id/published_at)
OUTPUT: data/processed/ke_thumbnails/ke_thumb_manifest.csv
        columns: channel_id, image_role, slot, video_id, url
        image_role in {avatar, newest, oldest, random}; slot like 'avatar' / 'newest_1' / 'random_3'

Usage:
  python3 06_thumb_build_manifest.py                 # full
  python3 06_thumb_build_manifest.py --limit 20      # TEST (first 20 KE channels)
"""
from __future__ import annotations

import argparse
import csv
import io
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
BASE = REPO / "data" / "processed" / "ke_analysis_base.csv"
AVATARS = REPO / "data" / "channels" / "knowledge_economy" / "ke_20260418.csv"
INVENTORY = REPO / "data" / "video_inventory" / "knowledge_economy_inventory.csv"
OUT_DIR = REPO / "data" / "processed" / "ke_thumbnails"
OUT = OUT_DIR / "ke_thumb_manifest.csv"

RANDOM_SEED = 20260617          # FIXED seed, recorded here and printed at run time
N_NEWEST = 5
N_OLDEST = 5
N_RANDOM = 5
THUMB_URL = "https://i.ytimg.com/vi/{vid}/hqdefault.jpg"

logging.basicConfig(level=logging.INFO, format="[06] %(message)s")
log = logging.getLogger(__name__)


def nul_safe_dictreader(path: Path) -> csv.DictReader:
    """DictReader over a possibly-NUL-containing CSV (binary read, strip \\x00, decode)."""
    with open(path, "rb") as f:
        raw = f.read().replace(b"\x00", b"")
    return csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace")))


def load_base_channels(limit: Optional[int]) -> List[str]:
    """Ordered, deduped list of KE channel_ids (preserves file order for stable --limit)."""
    seen: Set[str] = set()
    ordered: List[str] = []
    for row in nul_safe_dictreader(BASE):
        cid = (row.get("channel_id") or "").strip()
        if cid and cid not in seen:
            seen.add(cid)
            ordered.append(cid)
    if limit is not None:
        ordered = ordered[:limit]
    return ordered


def load_avatars(channels: Set[str]) -> Dict[str, str]:
    """channel_id -> profile_picture_url for in-scope channels (NUL-safe)."""
    avatars: Dict[str, str] = {}
    for row in nul_safe_dictreader(AVATARS):
        cid = (row.get("channel_id") or "").strip()
        if cid in channels:
            url = (row.get("profile_picture_url") or "").strip()
            if url.lower().startswith("http"):
                avatars[cid] = url
    return avatars


def collect_videos(channels: Set[str]) -> Dict[str, List[Tuple[str, str]]]:
    """Stream the 7 GB inventory once; collect (published_at, video_id) per in-scope channel.

    Returns channel_id -> list of (published_at, video_id). Memory is bounded by the number of
    videos belonging ONLY to in-scope channels (full run = all KE channels, ~30M rows total but
    we hold tuples only for KE channels, which we want anyway). For --limit test runs this is tiny.
    """
    by_chan: Dict[str, List[Tuple[str, str]]] = {c: [] for c in channels}
    n_rows = 0
    with open(INVENTORY, "rb") as fb:
        # Stream decode line-buffered to avoid loading 7 GB into memory.
        text = io.TextIOWrapper(fb, encoding="utf-8", errors="replace")
        reader = csv.DictReader(_nul_strip_lines(text))
        for row in reader:
            n_rows += 1
            if n_rows % 5_000_000 == 0:
                log.info("  streamed %s inventory rows...", f"{n_rows:,}")
            cid = (row.get("channel_id") or "").strip()
            if cid in by_chan:
                vid = (row.get("video_id") or "").strip()
                pub = (row.get("published_at") or "").strip()
                if vid:
                    by_chan[cid].append((pub, vid))
    log.info("  inventory rows streamed total: %s", f"{n_rows:,}")
    return by_chan


def _nul_strip_lines(text_iter):
    """Generator yielding NUL-stripped lines for csv.reader (inventory has embedded NULs)."""
    for line in text_iter:
        if "\x00" in line:
            line = line.replace("\x00", "")
        yield line


def select_slots(videos: List[Tuple[str, str]], rng: random.Random) -> List[Tuple[str, str, str]]:
    """Return [(image_role, slot, video_id)] for one channel's video thumbnails.

    Sort by published_at ascending. newest = last N by date, oldest = first N by date,
    random = N sampled (fixed seed) from whatever remains after removing newest+oldest video_ids.
    Dedup on video_id so the same video is never coded twice. <15 videos -> take all, no random.
    """
    # Sort by published_at (string ISO dates sort chronologically); blank dates sort first.
    ordered = sorted(videos, key=lambda pv: pv[0] or "")
    vids_in_order = [v for _, v in ordered]
    # Dedup preserving order.
    seen: Set[str] = set()
    unique: List[str] = []
    for v in vids_in_order:
        if v not in seen:
            seen.add(v)
            unique.append(v)

    slots: List[Tuple[str, str, str]] = []
    used: Set[str] = set()

    oldest = unique[:N_OLDEST]
    for i, v in enumerate(oldest, 1):
        slots.append(("oldest", f"oldest_{i}", v))
        used.add(v)

    newest = [v for v in reversed(unique) if v not in used][:N_NEWEST]
    for i, v in enumerate(newest, 1):
        slots.append(("newest", f"newest_{i}", v))
        used.add(v)

    remaining = [v for v in unique if v not in used]
    if remaining:
        k = min(N_RANDOM, len(remaining))
        chosen = rng.sample(remaining, k)
        for i, v in enumerate(chosen, 1):
            slots.append(("random", f"random_{i}", v))
            used.add(v)
    return slots


def main() -> None:
    ap = argparse.ArgumentParser(description="Build KE thumbnail URL manifest.")
    ap.add_argument("--limit", type=int, default=None,
                    help="TEST: only the first N KE channels (file order).")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log.info("random seed = %d (FIXED, recorded)", RANDOM_SEED)

    channels = load_base_channels(args.limit)
    chan_set = set(channels)
    log.info("KE channels in scope: %s", f"{len(channels):,}")

    avatars = load_avatars(chan_set)
    log.info("channels with avatar url: %s", f"{len(avatars):,}")

    log.info("streaming inventory (7 GB) — never loaded whole, never wc -l...")
    by_chan = collect_videos(chan_set)
    n_with_vids = sum(1 for c in channels if by_chan.get(c))
    log.info("channels with >=1 video in inventory: %s", f"{n_with_vids:,}")

    rng = random.Random(RANDOM_SEED)
    n_rows = 0
    role_counts: Dict[str, int] = {"avatar": 0, "newest": 0, "oldest": 0, "random": 0}
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        w.writerow(["channel_id", "image_role", "slot", "video_id", "url"])
        for cid in channels:
            av = avatars.get(cid)
            if av:
                w.writerow([cid, "avatar", "avatar", "", av])
                role_counts["avatar"] += 1
                n_rows += 1
            vids = by_chan.get(cid, [])
            if vids:
                for role, slot, vid in select_slots(vids, rng):
                    w.writerow([cid, role, slot, vid, THUMB_URL.format(vid=vid)])
                    role_counts[role] += 1
                    n_rows += 1

    log.info("manifest rows written: %s", f"{n_rows:,}")
    for role in ("avatar", "newest", "oldest", "random"):
        log.info("  %-7s : %s", role, f"{role_counts[role]:,}")
    log.info("wrote -> %s", OUT)


if __name__ == "__main__":
    main()
