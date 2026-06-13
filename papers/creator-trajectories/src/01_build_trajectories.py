#!/usr/bin/env python3
"""
01_build_trajectories.py
INPUT : data/video_inventory/gender_gap_inventory.csv  (video_id, channel_id, published_at, title, scraped_at)
OUTPUT: papers/creator-trajectories/processed/channel_trajectories.csv  (one row per channel)

Builds per-channel production-history features from the full video inventory.
Streaming/chunked so it never loads 1.6GB at once. Gentzkow-Shapiro: input-only here.
NO modification of source. Every output column documented in the data dictionary block below.
"""
import pandas as pd, numpy as np, sys
from collections import defaultdict

ROOT = "/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL"
INV  = f"{ROOT}/data/video_inventory/gender_gap_inventory.csv"
OUT  = f"{ROOT}/papers/creator-trajectories/processed/channel_trajectories.csv"

import os
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# Accumulators per channel
n_videos   = defaultdict(int)
min_pub    = {}                      # earliest upload (epoch seconds)
max_pub    = {}                      # latest upload
scraped    = {}                      # scrape time (epoch); ~constant per channel
# monthly posting counts -> for cadence regularity; store list of month-keys
months     = defaultdict(lambda: defaultdict(int))   # channel -> {YYYYMM: count}
bad_dates  = 0
total_rows = 0

CHUNK = 1_000_000
reader = pd.read_csv(INV, usecols=["channel_id","published_at","scraped_at"],
                     chunksize=CHUNK, dtype=str)
for ci, chunk in enumerate(reader):
    pub = pd.to_datetime(chunk["published_at"], errors="coerce", utc=True)
    scr = pd.to_datetime(chunk["scraped_at"], errors="coerce", utc=True)
    bad_dates += pub.isna().sum()
    chunk = chunk.assign(_pub=pub, _scr=scr)
    chunk = chunk.dropna(subset=["_pub"])
    pe = chunk["_pub"].view("int64") // 10**9   # epoch sec
    se = chunk["_scr"].view("int64") // 10**9
    ym = chunk["_pub"].dt.strftime("%Y%m")
    cid = chunk["channel_id"].values
    pev = pe.values; sev = se.values; ymv = ym.values
    for k, c in chunk["channel_id"].value_counts().items():
        n_videos[k] += int(c)
    # min/max/scraped via groupby for speed
    g = chunk.groupby("channel_id")
    gmin = (g["_pub"].min().view("int64")//10**9)
    gmax = (g["_pub"].max().view("int64")//10**9)
    gscr = (g["_scr"].max().view("int64")//10**9)
    for k,v in gmin.items():
        min_pub[k] = v if k not in min_pub else min(min_pub[k], v)
    for k,v in gmax.items():
        max_pub[k] = v if k not in max_pub else max(max_pub[k], v)
    for k,v in gscr.items():
        if pd.notna(v): scraped[k] = v if k not in scraped else max(scraped[k], v)
    # monthly counts
    mc = chunk.groupby(["channel_id", ym]).size()
    for (k, m), c in mc.items():
        months[k][m] += int(c)
    total_rows += len(chunk)
    print(f"  chunk {ci}: cum rows={total_rows:,}", file=sys.stderr)

rows = []
DAY = 86400.0
for k in n_videos:
    nv   = n_videos[k]
    mn   = min_pub.get(k, np.nan)
    mx   = max_pub.get(k, np.nan)
    sc   = scraped.get(k, mx)
    span_days   = (mx - mn)/DAY if (not np.isnan(mn) and not np.isnan(mx)) else np.nan
    age_days    = (sc - mn)/DAY if (not np.isnan(mn)) else np.nan          # channel age at scrape
    recency_days= (sc - mx)/DAY if (not np.isnan(mx)) else np.nan          # days since last upload
    mdict = months[k]
    # active months = distinct months with >=1 upload; tenure months = months from first to scrape
    active_months = len(mdict)
    tenure_months = max(1, round(age_days/30.44)) if not np.isnan(age_days) else np.nan
    # cadence: mean uploads per active month, and consistency (1 - CV across the tenure window)
    if not np.isnan(tenure_months) and tenure_months >= 1:
        # build full monthly series from first month to scrape month
        start = pd.Period(pd.to_datetime(mn, unit="s", utc=True), freq="M")
        end   = pd.Period(pd.to_datetime(sc, unit="s", utc=True), freq="M")
        idx = pd.period_range(start, end, freq="M")
        series = np.array([mdict.get(p.strftime("%Y%m"), 0) for p in idx], dtype=float)
        upm_tenure = series.mean()                         # uploads/month over full tenure (incl zeros)
        active_share = (series>0).mean()                   # fraction of months active
        cv = series.std()/series.mean() if series.mean()>0 else np.nan
        consistency = 1.0/(1.0+cv) if cv==cv else np.nan   # higher = steadier
        # front/back loading: share of videos in first half vs second half of tenure
        half = len(series)//2
        first_half = series[:half].sum(); second_half = series[half:].sum()
        tot = first_half+second_half
        back_load = (second_half/tot) if tot>0 else np.nan # >0.5 accelerating, <0.5 decelerating
    else:
        upm_tenure=active_share=consistency=back_load=np.nan
    upm_active = nv/active_months if active_months>0 else np.nan
    rows.append(dict(channel_id=k, inv_n_videos=nv,
        first_upload=pd.to_datetime(mn,unit="s",utc=True) if not np.isnan(mn) else pd.NaT,
        last_upload=pd.to_datetime(mx,unit="s",utc=True) if not np.isnan(mx) else pd.NaT,
        span_days=span_days, age_days=age_days, recency_days=recency_days,
        active_months=active_months, tenure_months=tenure_months,
        upm_tenure=upm_tenure, upm_active=upm_active,
        active_share=active_share, consistency=consistency, back_load=back_load))

out = pd.DataFrame(rows)
out.to_csv(OUT, index=False)
print(f"\nDONE. channels={len(out):,}  total videos kept={total_rows:,}  unparseable dates dropped={bad_dates:,}")
print(f"written: {OUT}")
print(out[["inv_n_videos","age_days","recency_days","upm_tenure","active_share","consistency","back_load"]].describe().to_string())
