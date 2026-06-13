#!/usr/bin/env python3
"""
02_eda_surprise.py
INPUT : processed/channel_trajectories.csv  +  data/processed/gender_gap_panel_clean.csv
OUTPUT: papers/creator-trajectories/output/eda_log.txt (captured by caller), merged analysis file
Surprise-hunting EDA. Headline question is NON-gender (creator production strategy -> scaling).
Gender enters only as a control. Every printed number is the analysis log of record.
"""
import pandas as pd, numpy as np, statsmodels.formula.api as smf, statsmodels.api as sm
pd.set_option("display.width", 160); pd.set_option("display.max_columns", 40)

ROOT = "/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL"
traj = pd.read_csv(f"{ROOT}/papers/creator-trajectories/processed/channel_trajectories.csv")
pan  = pd.read_csv(f"{ROOT}/data/processed/gender_gap_panel_clean.csv", low_memory=False)

print("traj:", traj.shape, "panel:", pan.shape)
df = pan.merge(traj, on="channel_id", how="inner")
print("merged:", df.shape)

# ---- outcomes & transforms ----
for c in ["subscriberCount","viewCount","videoCount","followers"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df["views_per_video"] = df["viewCount"]/df["videoCount"].replace(0,np.nan)
df["subs_per_video"]  = df["subscriberCount"]/df["videoCount"].replace(0,np.nan)
df["log_subs"]  = np.log1p(df["subscriberCount"])
df["log_views"] = np.log1p(df["viewCount"])
df["log_vpv"]   = np.log1p(df["views_per_video"])
df["log_nvid"]  = np.log1p(df["inv_n_videos"])
df["age_years"] = df["age_days"]/365.25
df["abandoned"] = (df["recency_days"]>180).astype(int)   # no upload in 6mo at scrape

print("\n===== OUTCOME DISTRIBUTIONS =====")
print(df[["subscriberCount","viewCount","views_per_video","inv_n_videos","age_years","upm_tenure","consistency","active_share","back_load","recency_days"]].describe().to_string())
print("\nabandoned (no upload 180d):", df["abandoned"].mean().round(3))

# ===== Q1: DOES VOLUME PAY? raw vs efficiency =====
print("\n===== Q1: VOLUME vs REACH =====")
print("corr log_nvid ~ log_subs :", df[["log_nvid","log_subs"]].corr().iloc[0,1].round(3))
print("corr log_nvid ~ log_vpv  :", df[["log_nvid","log_vpv"]].corr().iloc[0,1].round(3), "(views PER video vs volume)")
# quintiles of volume -> median subs and median views_per_video
df["volq"] = pd.qcut(df["inv_n_videos"], 5, labels=[1,2,3,4,5])
print(df.groupby("volq", observed=True).agg(n=("channel_id","size"),
      med_subs=("subscriberCount","median"), med_vpv=("views_per_video","median"),
      med_upm=("upm_tenure","median")).to_string())

# ===== Q2: CONSISTENCY vs VOLUME (partial) — quality-of-rhythm hypothesis =====
print("\n===== Q2: CONSISTENCY/RHYTHM controlling volume & age =====")
d2 = df.dropna(subset=["log_subs","log_nvid","consistency","active_share","age_years","upm_tenure","back_load"]).copy()
m1 = smf.ols("log_subs ~ log_nvid + age_years", data=d2).fit(cov_type="HC1")
m2 = smf.ols("log_subs ~ log_nvid + age_years + consistency + active_share + back_load", data=d2).fit(cov_type="HC1")
print("M1 R2=%.3f  M2 R2=%.3f  N=%d"%(m1.rsquared, m2.rsquared, int(m2.nobs)))
print(m2.params.round(3).to_string())
print("M2 ci:\n", m2.conf_int().round(3).to_string())

# ===== Q3: VIEWS-PER-VIDEO (efficiency) ~ production strategy =====
print("\n===== Q3: EFFICIENCY (log views/video) ~ strategy =====")
d3 = df.dropna(subset=["log_vpv","log_nvid","consistency","active_share","age_years","back_load"]).copy()
m3 = smf.ols("log_vpv ~ log_nvid + age_years + consistency + active_share + back_load", data=d3).fit(cov_type="HC1")
print("R2=%.3f N=%d"%(m3.rsquared,int(m3.nobs)))
print(m3.params.round(3).to_string())

# ===== Q4: ORGANIZATIONAL FORM (runBy) =====
print("\n===== Q4: runBy (organizational form) =====")
print(df.groupby("runBy").agg(n=("channel_id","size"), med_subs=("subscriberCount","median"),
      med_vpv=("views_per_video","median"), med_upm=("upm_tenure","median"),
      med_consistency=("consistency","median"), aband=("abandoned","mean")).to_string())

# ===== Q5: CONTENT CATEGORY sorting =====
print("\n===== Q5: TOP TOPIC categories by reach =====")
if "Topic 1" in df.columns:
    t = df.groupby("Topic 1").agg(n=("channel_id","size"), med_subs=("subscriberCount","median"),
        med_vpv=("views_per_video","median"), med_upm=("upm_tenure","median")).query("n>=50").sort_values("med_subs",ascending=False)
    print(t.to_string())

# ===== Q6: ABANDONMENT — who stalls? =====
print("\n===== Q6: ABANDONMENT correlates =====")
da = df.dropna(subset=["abandoned","log_nvid","age_years","upm_tenure","consistency"]).copy()
ma = smf.logit("abandoned ~ log_nvid + age_years + upm_tenure + consistency", data=da).fit(disp=0)
print(ma.params.round(3).to_string())
print("abandoned rate by volq:\n", df.groupby("volq",observed=True)["abandoned"].mean().round(3).to_string())

# save merged analysis file
OUTM = f"{ROOT}/papers/creator-trajectories/processed/analysis_merged.csv"
keep = ["channel_id","perceivedGender","race","runBy","subscriberCount","viewCount","videoCount",
        "views_per_video","inv_n_videos","age_years","upm_tenure","upm_active","active_share",
        "consistency","back_load","recency_days","abandoned","Topic 1","followers"]
df[keep].to_csv(OUTM, index=False)
print("\nwritten merged:", OUTM, "shape:", df[keep].shape)
