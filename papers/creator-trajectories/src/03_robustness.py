#!/usr/bin/env python3
"""
03_robustness.py  — robustness + scope checks for the consistency>volume finding.
INPUT : processed/analysis_merged.csv ; data/processed/gender_gap_panel_clean.csv ; processed/channel_trajectories.csv
OUTPUT: stdout log (captured to output/robustness_log.txt)
"""
import pandas as pd, numpy as np, statsmodels.formula.api as smf
pd.set_option("display.width",170); pd.set_option("display.max_columns",40)
ROOT="/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL"
df = pd.read_csv(f"{ROOT}/papers/creator-trajectories/processed/analysis_merged.csv", low_memory=False)
pan= pd.read_csv(f"{ROOT}/data/processed/gender_gap_panel_clean.csv", low_memory=False)
traj=pd.read_csv(f"{ROOT}/papers/creator-trajectories/processed/channel_trajectories.csv")

# ---- SCOPE CHECK: is the inventory really only individual-run channels? ----
print("===== SCOPE: runBy in full panel vs in trajectory-covered set =====")
print("full panel runBy:\n", pan.runBy.value_counts(dropna=False).to_string())
cov = pan[pan.channel_id.isin(traj.channel_id)]
print("\npanel rows WITH inventory coverage, runBy:\n", cov.runBy.value_counts(dropna=False).to_string())
print("\npanel rows WITHOUT inventory coverage, runBy:\n",
      pan[~pan.channel_id.isin(traj.channel_id)].runBy.value_counts(dropna=False).to_string())

# transforms
df["log_subs"]=np.log1p(df.subscriberCount); df["log_vpv"]=np.log1p(df.views_per_video)
df["log_nvid"]=np.log1p(df.inv_n_videos); df["log_recency"]=np.log1p(df.recency_days)
def wins(s,p=0.01):
    lo,hi=s.quantile(p),s.quantile(1-p); return s.clip(lo,hi)
for c in ["log_subs","log_vpv","consistency","active_share","back_load","log_nvid","age_years","log_recency"]:
    df[c+"_w"]=wins(df[c])

d=df.dropna(subset=["log_subs","log_nvid","consistency","active_share","back_load","age_years","log_recency"]).copy()
print("\nN analytic:", len(d))

# ---- R1: add recency control (kills 'still-active' artifact) ----
print("\n===== R1: consistency on log_subs, + recency control + winsor =====")
m = smf.ols("log_subs_w ~ log_nvid_w + age_years_w + consistency_w + active_share_w + back_load_w + log_recency_w", data=d).fit(cov_type="HC1")
print("R2=%.3f N=%d"%(m.rsquared,int(m.nobs)))
print(pd.concat([m.params.round(3),m.conf_int().round(3)],axis=1).to_string())

# ---- R2: category fixed effects (within-category) ----
print("\n===== R2: + Topic-1 fixed effects (within-category) =====")
d["cat"]=d["Topic 1"].fillna("none")
catn=d["cat"].value_counts(); d["cat2"]=np.where(d["cat"].isin(catn[catn>=50].index), d["cat"], "OTHER")
mfe = smf.ols("log_subs_w ~ log_nvid_w + age_years_w + consistency_w + active_share_w + back_load_w + log_recency_w + C(cat2)", data=d).fit(cov_type="HC1")
print("R2=%.3f N=%d  consistency coef=%.3f CI[%.3f,%.3f]"%(mfe.rsquared,int(mfe.nobs),
      mfe.params["consistency_w"], mfe.conf_int().loc["consistency_w",0], mfe.conf_int().loc["consistency_w",1]))

# ---- R3: between vs within category decomposition of consistency effect ----
print("\n===== R3: between/within decomposition =====")
# total variance in log_subs explained by category alone vs by consistency net of category
base=smf.ols("log_subs_w ~ C(cat2)",data=d).fit();
print("R2 category-only: %.3f"%base.rsquared)
withc=smf.ols("log_subs_w ~ C(cat2) + consistency_w + log_nvid_w + age_years_w",data=d).fit()
print("R2 category+consistency+vol+age: %.3f (delta from consistency block)"%withc.rsquared)

# ---- R4: sign stability across subsamples ----
print("\n===== R4: consistency coef across subsamples (DV=log_subs_w) =====")
def coef(sub):
    if len(sub)<150: return (np.nan,np.nan,len(sub))
    mm=smf.ols("log_subs_w ~ log_nvid_w + age_years_w + consistency_w + active_share_w + log_recency_w",data=sub).fit(cov_type="HC1")
    return (mm.params["consistency_w"], mm.bse["consistency_w"], len(sub))
d["aget"]=pd.qcut(d.age_years,3,labels=["young","mid","old"])
for g,sub in d.groupby("aget",observed=True):
    b,se,n=coef(sub); print(f"  age={g:5s} n={n:5d}  consistency b={b:.3f} se={se:.3f}")
for g in ["Lifestyle (sociology)","Society","Hobby","Knowledge","Entertainment"]:
    sub=d[d["Topic 1"]==g]; b,se,n=coef(sub); print(f"  cat={g[:20]:20s} n={n:5d}  consistency b={b:.3f} se={se:.3f}")
# gender as control only (confirm finding is not gender-driven)
print("\n===== R5: finding holds with gender control (gender NOT the question) =====")
dg=d[d.perceivedGender.isin(["man","woman"])].copy()
mg=smf.ols("log_subs_w ~ log_nvid_w + age_years_w + consistency_w + active_share_w + log_recency_w + C(perceivedGender)",data=dg).fit(cov_type="HC1")
print("consistency b=%.3f CI[%.3f,%.3f]  gender[woman] b=%.3f  N=%d"%(
  mg.params["consistency_w"], mg.conf_int().loc["consistency_w",0], mg.conf_int().loc["consistency_w",1],
  mg.params.get("C(perceivedGender)[T.woman]",np.nan), int(mg.nobs)))

# ---- effect size in human units ----
print("\n===== EFFECT SIZE (human units) =====")
p25,p75=d.consistency.quantile(.25),d.consistency.quantile(.75)
b=m.params["consistency_w"]
print(f"consistency p25={p25:.3f} p75={p75:.3f}; IQR move x b({b:.2f}) = {(p75-p25)*b:.3f} log pts = {100*(np.exp((p75-p25)*b)-1):.0f}% more subscribers")
bn=m.params["log_nvid_w"]
print(f"doubling volume (log2={np.log(2):.3f}) x b({bn:.2f}) = {np.log(2)*bn:.3f} log pts = {100*(np.exp(np.log(2)*bn)-1):.0f}% subs")
