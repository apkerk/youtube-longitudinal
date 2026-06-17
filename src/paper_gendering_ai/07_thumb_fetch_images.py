#!/usr/bin/env python3
"""07_thumb_fetch_images.py — KE thumbnail-gender pipeline step 2 (free image fetch).

Downloads the images listed in the manifest (step 06) to a local on-disk cache. Free:
plain HTTPS GET against i.ytimg.com and the avatar CDN; no API, no quota, no money.
Resumable, parallel (ThreadPoolExecutor), logs every dead/placeholder URL as item
nonresponse (never silently dropped). Images are RETAINED on disk — the DeepFace pass
(step 08) and the gated Gemini pass (step 10) both reuse the same files. Re-running
resumes from the fetch log; already-fetched (channel_id, slot) pairs are skipped.

Mirrors the validated do-file 73 structure (placeholder detection <1200 bytes, status
taxonomy ok/dead/placeholder/error, buffered log flush).

INPUT : data/processed/ke_thumbnails/ke_thumb_manifest.csv   (step 06)
OUTPUT: data/processed/ke_thumbnails/images/{channel_id}/{slot}.jpg
        data/processed/ke_thumbnails/ke_thumb_fetch_log.csv  (channel_id, slot, video_id, status, http, bytes, error)

Usage:
  python3 07_thumb_fetch_images.py --limit 50      # TEST
  python3 07_thumb_fetch_images.py --workers 10    # full run
"""
from __future__ import annotations

import argparse
import csv
import io
import logging
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO = Path(__file__).resolve().parents[2]
THUMB_DIR = REPO / "data" / "processed" / "ke_thumbnails"
MANIFEST = THUMB_DIR / "ke_thumb_manifest.csv"
IMG_DIR = THUMB_DIR / "images"
FETCH_LOG = THUMB_DIR / "ke_thumb_fetch_log.csv"

DEFAULT_WORKERS = 10
TIMEOUT = 20
PLACEHOLDER_BYTES = 1200          # YouTube serves a tiny grey placeholder for missing thumbs
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

logging.basicConfig(level=logging.INFO, format="[07] %(message)s")
log = logging.getLogger(__name__)
_LOG_LOCK = threading.Lock()


def img_path(channel_id: str, slot: str) -> Path:
    safe = channel_id.replace("/", "_")
    return IMG_DIR / safe / f"{slot}.jpg"


def append_log(rows: List[dict]) -> None:
    with _LOG_LOCK:
        write_header = not FETCH_LOG.exists()
        with open(FETCH_LOG, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["channel_id", "slot", "video_id",
                                              "status", "http", "bytes", "error"])
            if write_header:
                w.writeheader()
            for r in rows:
                w.writerow(r)


def load_done() -> Set[Tuple[str, str]]:
    """(channel_id, slot) pairs already attempted (any status) — resume support."""
    done: Set[Tuple[str, str]] = set()
    if FETCH_LOG.exists():
        with open(FETCH_LOG, "rb") as fb:
            raw = fb.read().replace(b"\x00", b"")
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8", errors="replace")))
        for r in reader:
            done.add(((r.get("channel_id") or ""), (r.get("slot") or "")))
    return done


def read_manifest(limit_channels: int | None) -> List[dict]:
    rows: List[dict] = []
    seen_channels: List[str] = []
    seen_set: Set[str] = set()
    with open(MANIFEST, "r", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            cid = r["channel_id"]
            if cid not in seen_set:
                seen_set.add(cid)
                seen_channels.append(cid)
            rows.append(r)
    if limit_channels is not None:
        keep = set(seen_channels[:limit_channels])
        rows = [r for r in rows if r["channel_id"] in keep]
    return rows


def fetch_one(channel_id: str, slot: str, video_id: str, url: str) -> dict:
    out = img_path(channel_id, slot)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
            code = resp.getcode()
    except urllib.error.HTTPError as e:
        return {"channel_id": channel_id, "slot": slot, "video_id": video_id,
                "status": "dead", "http": e.code, "bytes": 0, "error": f"http_{e.code}"}
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        return {"channel_id": channel_id, "slot": slot, "video_id": video_id,
                "status": "error", "http": "", "bytes": 0, "error": str(e)[:120]}
    if len(data) < PLACEHOLDER_BYTES:
        return {"channel_id": channel_id, "slot": slot, "video_id": video_id,
                "status": "placeholder", "http": code, "bytes": len(data),
                "error": "too_small/placeholder"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    return {"channel_id": channel_id, "slot": slot, "video_id": video_id,
            "status": "ok", "http": code, "bytes": len(data), "error": ""}


def main() -> None:
    ap = argparse.ArgumentParser(description="Fetch KE thumbnail images from the manifest.")
    ap.add_argument("--limit", type=int, default=None,
                    help="TEST: only the first N channels (manifest order).")
    ap.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    args = ap.parse_args()

    if not MANIFEST.exists():
        raise SystemExit(f"[07] manifest missing: {MANIFEST} (run step 06 first)")
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    rows = read_manifest(args.limit)
    done = load_done()
    todo = [r for r in rows if (r["channel_id"], r["slot"]) not in done]
    total = len(todo)
    log.info("manifest rows: %s | already attempted: %s | to fetch: %s | workers=%d",
             f"{len(rows):,}", f"{len(done):,}", f"{total:,}", args.workers)
    if total == 0:
        log.info("nothing to do.")
        return

    counts: Dict[str, int] = {}
    counts_lock = threading.Lock()
    buf: List[dict] = []
    t0 = time.time()
    done_n = 0

    def work(r: dict) -> dict:
        return fetch_one(r["channel_id"], r["slot"], r.get("video_id", ""), r["url"])

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(work, r) for r in todo]
        for fut in as_completed(futs):
            res = fut.result()
            with counts_lock:
                counts[res["status"]] = counts.get(res["status"], 0) + 1
                buf.append(res)
                done_n += 1
                i = done_n
                if len(buf) >= 100:
                    flush, buf[:] = buf[:], []
                else:
                    flush = None
            if flush:
                append_log(flush)
            if i % 200 == 0 or i == total:
                elapsed = time.time() - t0
                rate = i / elapsed if elapsed else 0
                log.info("%s/%s ok=%s dead=%s ph=%s err=%s %.1f img/s",
                         f"{i:,}", f"{total:,}", f"{counts.get('ok',0):,}",
                         f"{counts.get('dead',0):,}", f"{counts.get('placeholder',0):,}",
                         f"{counts.get('error',0):,}", rate)

    if buf:
        append_log(buf)
    log.info("DONE this run: %s", counts)
    log.info("images -> %s", IMG_DIR)
    log.info("log -> %s", FETCH_LOG)


if __name__ == "__main__":
    main()
