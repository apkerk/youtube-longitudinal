#!/usr/bin/env python3
"""08_thumb_deepface_gender.py — KE thumbnail-gender pipeline step 3 (FREE DeepFace pass).

Runs DeepFace gender analysis over every fetched KE thumbnail/avatar (step 07) and aggregates
to one row per channel. This is the free, local, no-API gender signal that becomes the working
gender measure for papers/gendering-ai-expertise until the (gated) Gemini pass refines it.

Per image (DeepFace.analyze, actions=['gender'], detector_backend='opencv',
enforce_detection=True, silent=True):
  - face_present (bool): True iff a face was detected (enforce_detection=True raises otherwise)
  - dominant_gender: 'Man' / 'Woman' (None if no face)
  - gender_woman_conf / gender_man_conf: DeepFace confidence percentages (0-100)

Per channel (aggregate):
  - n_images           : images attempted for the channel
  - n_face_images      : images where a face was detected
  - deepface_female_share : share of DETECTED faces reading Woman
  - deepface_label     : 'woman' if female_share > 0.5 else 'man'  (only if n_face_images >= 1)
  - confidence_tier    : keyed to n_face_images, mirroring the validated 75% -> 97% reliability
                         ladder:  0 faces -> 'none'; 1 -> 'tier1'; 2 -> 'tier2'; 3 -> 'tier3';
                         >=4 -> 'tier4plus' (highest reliability bucket).

Parallel workers; checkpoint per channel so a re-run resumes. Image files are RETAINED (read
only, never deleted) so the gated Gemini pass can reuse them.

INPUT : data/processed/ke_thumbnails/ke_thumb_fetch_log.csv  (which images are 'ok')
        data/processed/ke_thumbnails/images/{channel_id}/{slot}.jpg
OUTPUT: data/processed/ke_thumb_deepface_raw.csv             (1 row per image)
        data/processed/ke_thumb_gender_channel.csv           (1 row per channel)
        data/processed/ke_thumbnails/.deepface_checkpoint.json (resume state)

Usage:
  python3 08_thumb_deepface_gender.py --limit 20    # TEST
  python3 08_thumb_deepface_gender.py --workers 6   # full run
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import logging
import threading
import time
import warnings
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

warnings.filterwarnings("ignore")

REPO = Path(__file__).resolve().parents[2]
THUMB_DIR = REPO / "data" / "processed" / "ke_thumbnails"
FETCH_LOG = THUMB_DIR / "ke_thumb_fetch_log.csv"
IMG_DIR = THUMB_DIR / "images"
RAW_OUT = REPO / "data" / "processed" / "ke_thumb_deepface_raw.csv"
CHAN_OUT = REPO / "data" / "processed" / "ke_thumb_gender_channel.csv"
CHECKPOINT = THUMB_DIR / ".deepface_checkpoint.json"

DEFAULT_WORKERS = 6
RAW_FIELDS = ["channel_id", "slot", "video_id", "face_present", "dominant_gender",
              "gender_woman_conf", "gender_man_conf", "error"]
CHAN_FIELDS = ["channel_id", "n_images", "n_face_images", "deepface_female_share",
               "deepface_label", "confidence_tier"]

logging.basicConfig(level=logging.INFO, format="[08] %(message)s")
log = logging.getLogger(__name__)
_LOCK = threading.Lock()

# Import DeepFace once at module load (model weights cached after first call).
from deepface import DeepFace  # noqa: E402


def img_path(channel_id: str, slot: str) -> Path:
    return IMG_DIR / channel_id.replace("/", "_") / f"{slot}.jpg"


def load_ok_images(limit_channels: Optional[int]) -> Dict[str, List[Tuple[str, str]]]:
    """channel_id -> [(slot, video_id)] for images with fetch status 'ok' (NUL-safe read)."""
    by_chan: "defaultdict[str, List[Tuple[str, str]]]" = defaultdict(list)
    if not FETCH_LOG.exists():
        raise SystemExit(f"[08] fetch log missing: {FETCH_LOG} (run step 07 first)")
    with open(FETCH_LOG, "rb") as fb:
        raw = fb.read().replace(b"\x00", b"")
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace")))
    for r in reader:
        if (r.get("status") or "") == "ok":
            by_chan[r["channel_id"]].append((r["slot"], r.get("video_id", "")))
    if limit_channels is not None:
        keep = list(by_chan.keys())[:limit_channels]
        by_chan = defaultdict(list, {c: by_chan[c] for c in keep})
    return by_chan


def load_checkpoint() -> Set[str]:
    if CHECKPOINT.exists():
        try:
            return set(json.loads(CHECKPOINT.read_text()).get("completed_channels", []))
        except (json.JSONDecodeError, OSError):
            return set()
    return set()


def save_checkpoint(completed: Set[str]) -> None:
    with _LOCK:
        tmp = CHECKPOINT.with_suffix(".json.tmp")
        tmp.write_text(json.dumps({"completed_channels": sorted(completed)}))
        tmp.replace(CHECKPOINT)


def analyze_image(path: Path) -> dict:
    """Return per-image gender result. face_present False when no face / detection fails."""
    if not path.exists():
        return {"face_present": False, "dominant_gender": None,
                "gender_woman_conf": None, "gender_man_conf": None, "error": "missing_file"}
    try:
        res = DeepFace.analyze(img_path=str(path), actions=["gender"],
                               detector_backend="opencv", enforce_detection=True, silent=True)
        r0 = res[0] if isinstance(res, list) else res
        gd = r0.get("gender", {}) or {}
        return {"face_present": True,
                "dominant_gender": r0.get("dominant_gender"),
                "gender_woman_conf": float(gd.get("Woman")) if gd.get("Woman") is not None else None,
                "gender_man_conf": float(gd.get("Man")) if gd.get("Man") is not None else None,
                "error": ""}
    except ValueError:
        # enforce_detection=True raises ValueError when no face is found — the expected no-face path.
        return {"face_present": False, "dominant_gender": None,
                "gender_woman_conf": None, "gender_man_conf": None, "error": "no_face"}
    except Exception as exc:  # noqa: BLE001 — log + continue, never silently drop
        return {"face_present": False, "dominant_gender": None,
                "gender_woman_conf": None, "gender_man_conf": None,
                "error": f"{type(exc).__name__}:{str(exc)[:80]}"}


def confidence_tier(n_face: int) -> str:
    if n_face <= 0:
        return "none"
    if n_face == 1:
        return "tier1"
    if n_face == 2:
        return "tier2"
    if n_face == 3:
        return "tier3"
    return "tier4plus"


def aggregate_channel(channel_id: str, image_rows: List[dict]) -> dict:
    n_images = len(image_rows)
    faces = [r for r in image_rows if r["face_present"]]
    n_face = len(faces)
    if n_face >= 1:
        n_woman = sum(1 for r in faces if (r["dominant_gender"] or "").lower() == "woman")
        female_share = n_woman / n_face
        label = "woman" if female_share > 0.5 else "man"
    else:
        female_share = None
        label = None
    return {"channel_id": channel_id, "n_images": n_images, "n_face_images": n_face,
            "deepface_female_share": (round(female_share, 4) if female_share is not None else None),
            "deepface_label": label, "confidence_tier": confidence_tier(n_face)}


def main() -> None:
    ap = argparse.ArgumentParser(description="DeepFace gender over KE thumbnails.")
    ap.add_argument("--limit", type=int, default=None,
                    help="TEST: only the first N channels (fetch-log order).")
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args = ap.parse_args()

    by_chan = load_ok_images(args.limit)
    completed = load_checkpoint()
    # On a fresh run (--limit test) ignore checkpoint channels not in scope; resume otherwise.
    channels = [c for c in by_chan if c not in completed]
    log.info("channels with ok images: %s | already done: %s | to process: %s | workers=%d",
             f"{len(by_chan):,}", f"{len(completed & set(by_chan)):,}",
             f"{len(channels):,}", args.workers)
    if not channels:
        log.info("nothing to do (all channels checkpointed).")
        return

    raw_header = not RAW_OUT.exists()
    chan_header = not CHAN_OUT.exists()
    raw_fh = open(RAW_OUT, "a", newline="", encoding="utf-8")
    chan_fh = open(CHAN_OUT, "a", newline="", encoding="utf-8")
    raw_w = csv.DictWriter(raw_fh, fieldnames=RAW_FIELDS)
    chan_w = csv.DictWriter(chan_fh, fieldnames=CHAN_FIELDS)
    if raw_header:
        raw_w.writeheader()
    if chan_header:
        chan_w.writeheader()

    t0 = time.time()
    n_done = 0
    n_images_total = 0
    n_faces_total = 0

    def process_channel(cid: str) -> Tuple[str, List[dict], dict]:
        rows: List[dict] = []
        for slot, video_id in by_chan[cid]:
            res = analyze_image(img_path(cid, slot))
            rows.append({"channel_id": cid, "slot": slot, "video_id": video_id, **res})
        return cid, rows, aggregate_channel(cid, rows)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_channel, c): c for c in channels}
        for fut in as_completed(futs):
            cid, rows, chan_row = fut.result()
            with _LOCK:
                for r in rows:
                    raw_w.writerow(r)
                chan_w.writerow(chan_row)
                raw_fh.flush()
                chan_fh.flush()
                completed.add(cid)
                n_done += 1
                n_images_total += len(rows)
                n_faces_total += chan_row["n_face_images"]
            if n_done % 100 == 0 or n_done == len(channels):
                save_checkpoint(completed)
                elapsed = time.time() - t0
                ch_rate = n_done / elapsed if elapsed else 0
                img_rate = n_images_total / elapsed if elapsed else 0
                log.info("%s/%s chans | %s imgs | %s faces | %.1f ch/s | %.1f img/s",
                         f"{n_done:,}", f"{len(channels):,}", f"{n_images_total:,}",
                         f"{n_faces_total:,}", ch_rate, img_rate)

    save_checkpoint(completed)
    raw_fh.close()
    chan_fh.close()
    log.info("DONE: %s channels | %s images | %s faces", f"{n_done:,}",
             f"{n_images_total:,}", f"{n_faces_total:,}")
    log.info("per-image  -> %s", RAW_OUT)
    log.info("per-channel-> %s", CHAN_OUT)


if __name__ == "__main__":
    main()
