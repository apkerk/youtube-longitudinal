#!/usr/bin/env python3
"""
05_survival_panel.py  — PROSPECTIVE, time-ordered survival/growth design.
PREDICTOR window: pre-2026 lifetime production history (channel_trajectories.csv, built from the
   video inventory scraped ~Feb 17 2026).  -> production reliability measured BEFORE the outcome.
OUTCOME window:  the gender_gap daily channel-stats panel, 2026-02-17 .. 2026-06-13 (95 days),
   independent of the predictor window.  -> survival (did it keep producing) + growth (subs accrual).
This escapes the cross-sectional tautology of v1: early reliability predicting LATER outcomes.

INPUT : /tmp/gg_panel/*.csv  (daily: channel_id, view_count, subscriber_count, video_count, scraped_at)
        processed/channel_trajectories.csv  (pre-2026 production-history features)
        data/processed/gender_gap_panel_clean.csv (covariates: gender/race as controls)
OUTPUT: processed/survival_analysis.csv + output/survival_log.txt (captured) + output/survival_numbers.json
"""
import pandas as pd, numpy as np, glob, json, statsmodels.formula.api as smf
pd.set_option("display.width",170); pd.set_option("display.max_columns",40)
ROOT="/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL"
PROJ=f"{ROOT}/papers/creator-trajectories"

# ---- build per-channel panel summary from 95 daily files ----
files=sorted(glob.glob("/tmp/gg_panel/*.csv"))
dates=[f.split("/")[-1].replace(".csv","") for f in files]
print(f"panel days: {len(files)}  {dates[0]} .. {dates[-1]}")
# stack minimal columns; keep memory light
frames=[]
for f,d in zip(files,dates):
    c=pd.read_csv(f, usecols=["channel_id","subscriber_count","video_count","view_count"])
    c["date"]=d; frames.append(c)
panel=pd.concat(frames, ignore_index=True)
panel["date"]=pd.to_datetime(panel["date"])
panel=panel.sort_values(["channel_id","date"])
print("panel rows:", len(panel), "channels:", panel.channel_id.nunique())

g=panel.groupby("channel_id")
first=g.first(); last=g.last(); nobs=g.size()
out=pd.DataFrame({
  "subs_first":first.subscriber_count, "subs_last":last.subscriber_count,
  "views_first":first.view_count, "views_last":last.view_count,
  "vc_first":first.video_count, "vc_last":last.video_count,
  "panel_days_obs":nobs}).reset_index()
out["videos_added"]=out.vc_last-out.vc_first
out["subs_delta"]=out.subs_last-out.subs_first
out["views_delta"]=out.views_last-out.views_first
# OUTCOMES
out["dormant_window"]=(out.videos_added<=0).astype(int)        # no net new uploads in 95 days = stalled
out["subs_growth_log"]=np.log1p(out.subs_last)-np.log1p(out.subs_first)   # prospective growth
out["views_growth_log"]=np.log1p(out.views_last)-np.log1p(out.views_first)
out["subs_growth_pct"]=np.where(out.subs_first>0, out.subs_delta/out.subs_first, np.nan)

# ---- join pre-2026 production reliability (predictor) ----
traj=pd.read_csv(f"{PROJ}/processed/channel_trajectories.csv")
cov=pd.read_csv(f"{ROOT}/data/processed/gender_gap_panel_clean.csv", low_memory=False)[["channel_id","perceivedGender","race","Topic 1"]]
df=out.merge(traj,on="channel_id",how="inner").merge(cov,on="channel_id",how="left")
print("merged (panel x history):", df.shape)

df["log_subs0"]=np.log1p(df.subs_first)        # baseline size control (start of window)
df["log_nvid"]=np.log1p(df.inv_n_videos)
df["age_years"]=df.age_days/365.25
def wins(s,p=0.01):
    return s.clip(s.quantile(p), s.quantile(1-p))
for c in ["subs_growth_log","views_growth_log","consistency","active_share","back_load","log_nvid","age_years","log_subs0"]:
    df[c+"_w"]=wins(df[c])

NUM={}
NUM["panel_days"]=len(files); NUM["panel_span"]=[dates[0],dates[-1]]
NUM["N_panel_channels"]=int(panel.channel_id.nunique())
NUM["N_merged"]=int(len(df))
NUM["dormant_rate_window"]=round(float(df.dormant_window.mean()),3)
NUM["median_subs_growth_pct"]=round(float(df.subs_growth_pct.median()),4)

print("\n===== OUTCOME DESCRIPTIVES (prospective, 95-day window) =====")
print("dormant in window (no new uploads):", NUM["dormant_rate_window"])
print("subs growth pct: median {:.3f}  mean {:.3f}".format(df.subs_growth_pct.median(), df.subs_growth_pct.mean()))
print(df[["subs_delta","videos_added","subs_growth_log","views_growth_log"]].describe().to_string())

# winner-take-all in realized growth: share of total new subscribers captured by top decile
tot=df.subs_delta.clip(lower=0).sum()
dec=df.assign(d=pd.qcut(df.subs_first.rank(method="first"),10,labels=False)).groupby("d").subs_delta.apply(lambda x:x.clip(lower=0).sum())
top_decile_share=dec.iloc[-1]/tot if tot>0 else np.nan
NUM["top_decile_share_of_new_subs"]=round(float(top_decile_share),3)
print(f"\nWINNER-TAKE-ALL: top size-decile captured {100*top_decile_share:.0f}% of all net new subscribers in the window")

d=df.dropna(subset=["subs_growth_log_w","consistency_w","log_nvid_w","age_years_w","log_subs0_w"]).copy()

# ===== H1: early reliability -> SURVIVAL (dormancy in later window) =====
print("\n===== H1: SURVIVAL — logit(dormant in window) on pre-2026 reliability =====")
ds=df.dropna(subset=["dormant_window","consistency","log_nvid","age_years","log_subs0"]).copy()
ms=smf.logit("dormant_window ~ consistency + log_nvid + age_years + log_subs0", data=ds).fit(disp=0)
print(pd.concat([ms.params.round(3),ms.bse.round(3)],axis=1).to_string())
# odds ratio for IQR move in consistency
iqr=ds.consistency.quantile(.75)-ds.consistency.quantile(.25)
NUM["surv_consistency_b"]=round(float(ms.params["consistency"]),3)
NUM["surv_consistency_OR_iqr"]=round(float(np.exp(ms.params["consistency"]*iqr)),3)
print(f"IQR consistency -> dormancy odds x {NUM['surv_consistency_OR_iqr']}")

# ===== H2: early reliability -> GROWTH (subs accrual) net of baseline size =====
print("\n===== H2: GROWTH — OLS(subs_growth_log) on pre-2026 reliability, net of baseline size =====")
mg=smf.ols("subs_growth_log_w ~ consistency_w + active_share_w + back_load_w + log_nvid_w + age_years_w + log_subs0_w", data=d).fit(cov_type="HC1")
print("R2=%.3f N=%d"%(mg.rsquared,int(mg.nobs)))
print(pd.concat([mg.params.round(3),mg.conf_int().round(3)],axis=1).to_string())
NUM["growth_consistency_b"]=round(float(mg.params["consistency_w"]),3)
NUM["growth_consistency_ci"]=[round(float(mg.conf_int().loc["consistency_w",0]),3),round(float(mg.conf_int().loc["consistency_w",1]),3)]
NUM["growth_logvid_b"]=round(float(mg.params["log_nvid_w"]),3)

# ===== H2b: volume vs consistency horse race on growth (does volume collapse again, prospectively?) =====
mvol=smf.ols("subs_growth_log_w ~ log_nvid_w + age_years_w + log_subs0_w", data=d).fit(cov_type="HC1")
mboth=smf.ols("subs_growth_log_w ~ log_nvid_w + consistency_w + age_years_w + log_subs0_w", data=d).fit(cov_type="HC1")
NUM["growth_logvid_alone"]=round(float(mvol.params["log_nvid_w"]),3)
NUM["growth_logvid_withcons"]=round(float(mboth.params["log_nvid_w"]),3)
print(f"\nVolume coef on growth: alone={NUM['growth_logvid_alone']}  with consistency={NUM['growth_logvid_withcons']}  (consistency b={mboth.params['consistency_w']:.3f})")

# save
keep=["channel_id","subs_first","subs_last","subs_delta","videos_added","dormant_window","subs_growth_log",
      "views_growth_log","consistency","active_share","back_load","inv_n_videos","age_years","perceivedGender","race","Topic 1"]
df[keep].to_csv(f"{PROJ}/processed/survival_analysis.csv",index=False)
json.dump(NUM, open(f"{PROJ}/output/survival_numbers.json","w"), indent=2)
print("\nSAVED survival_analysis.csv + survival_numbers.json")
print(json.dumps(NUM,indent=2))
