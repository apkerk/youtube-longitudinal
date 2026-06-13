#!/usr/bin/env python3
"""
04_exhibits.py — publication exhibits from analysis_merged.csv + channel_trajectories.csv
Outputs to papers/creator-trajectories/output/: table1..4 (txt+tex), fig1..3 (png+pdf), numbers.json
Every number here is the table-cell of record cited by the manuscript (ISC #1,#3,#19).
"""
import pandas as pd, numpy as np, json, statsmodels.formula.api as smf
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
ROOT="/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL"
OUT=f"{ROOT}/papers/creator-trajectories/output"
df=pd.read_csv(f"{ROOT}/papers/creator-trajectories/processed/analysis_merged.csv", low_memory=False)
NUM={}

# transforms
df["log_subs"]=np.log1p(df.subscriberCount); df["log_views"]=np.log1p(df.viewCount)
df["log_vpv"]=np.log1p(df.views_per_video); df["log_nvid"]=np.log1p(df.inv_n_videos)
df["log_recency"]=np.log1p(df.recency_days); df["abandoned"]=(df.recency_days>180).astype(int)
def wins(s,p=0.01):
    lo,hi=s.quantile(p),s.quantile(1-p); return s.clip(lo,hi)
W=["log_subs","log_vpv","consistency","active_share","back_load","log_nvid","age_years","log_recency"]
for c in W: df[c+"_w"]=wins(df[c])
d=df.dropna(subset=W).copy()
NUM["N_analytic"]=int(len(d)); NUM["N_total_inventory"]=9591
NUM["median_age_years"]=round(float(df.age_years.median()),1)
NUM["median_videos"]=int(df.inv_n_videos.median())
NUM["median_subs"]=int(df.subscriberCount.median())
NUM["abandoned_rate"]=round(float(df.abandoned.mean()),3)

# ---------- TABLE 1: descriptives ----------
desc_vars={"subscriberCount":"Subscribers","viewCount":"Total views","views_per_video":"Views per video",
  "inv_n_videos":"Videos uploaded (lifetime)","age_years":"Channel age (years)","upm_tenure":"Uploads/month (tenure)",
  "active_share":"Share of months active","consistency":"Posting consistency","back_load":"Back-loading (accel.)",
  "recency_days":"Days since last upload"}
t1=df[list(desc_vars)].rename(columns=desc_vars).describe(percentiles=[.25,.5,.75]).T[["mean","std","25%","50%","75%"]]
t1.to_csv(f"{OUT}/table1_descriptives.csv")
with open(f"{OUT}/table1_descriptives.txt","w") as f: f.write("TABLE 1. Descriptive statistics (N=%d solo creators)\n\n"%len(df)+t1.round(2).to_string())

# ---------- TABLE 2: correlations ----------
corrv={"log_subs":"1 log Subs","log_vpv":"2 log Views/video","consistency":"3 Consistency",
  "active_share":"4 Active share","back_load":"5 Back-load","log_nvid":"6 log Videos","age_years":"7 Age"}
t2=df[list(corrv)].rename(columns=corrv).corr().round(2)
t2.to_csv(f"{OUT}/table2_corr.csv")
with open(f"{OUT}/table2_corr.txt","w") as f: f.write("TABLE 2. Correlations\n\n"+t2.to_string())

# ---------- TABLE 3: nested OLS on log subscribers ----------
d["cat"]=d["Topic 1"].fillna("none"); cn=d.cat.value_counts(); d["cat2"]=np.where(d.cat.isin(cn[cn>=50].index),d.cat,"OTHER")
m1=smf.ols("log_subs_w ~ log_nvid_w + age_years_w", data=d).fit(cov_type="HC1")
m2=smf.ols("log_subs_w ~ log_nvid_w + age_years_w + consistency_w + active_share_w + back_load_w", data=d).fit(cov_type="HC1")
m3=smf.ols("log_subs_w ~ log_nvid_w + age_years_w + consistency_w + active_share_w + back_load_w + log_recency_w", data=d).fit(cov_type="HC1")
m4=smf.ols("log_subs_w ~ log_nvid_w + age_years_w + consistency_w + active_share_w + back_load_w + log_recency_w + C(cat2)", data=d).fit(cov_type="HC1")
def col(m,name):
    out={}
    for p in ["log_nvid_w","age_years_w","consistency_w","active_share_w","back_load_w","log_recency_w"]:
        if p in m.params:
            out[p]=f"{m.params[p]:.3f} ({m.bse[p]:.3f})"+("***" if m.pvalues[p]<.001 else "**" if m.pvalues[p]<.01 else "*" if m.pvalues[p]<.05 else "")
        else: out[p]="--"
    out["R2"]=f"{m.rsquared:.3f}"; out["N"]=f"{int(m.nobs)}"; out["CatFE"]="Yes" if "C(cat2)" in str(m.model.formula) else "No"
    return pd.Series(out,name=name)
t3=pd.concat([col(m1,"(1)"),col(m2,"(2)"),col(m3,"(3)"),col(m4,"(4)")],axis=1)
lab={"log_nvid_w":"log Videos uploaded","age_years_w":"Channel age (yrs)","consistency_w":"Posting consistency",
 "active_share_w":"Share months active","back_load_w":"Back-loading","log_recency_w":"log Days since last upload",
 "R2":"R-squared","N":"N","CatFE":"Category FE"}
t3.index=[lab.get(i,i) for i in t3.index]
t3.to_csv(f"{OUT}/table3_main.csv")
with open(f"{OUT}/table3_main.txt","w") as f:
    f.write("TABLE 3. OLS, DV = log(1+subscribers). HC1 robust SE in parentheses. *p<.05 **p<.01 ***p<.001\n\n"+t3.to_string())
NUM["consistency_b_full"]=round(float(m3.params["consistency_w"]),3)
NUM["consistency_ci_full"]=[round(float(m3.conf_int().loc["consistency_w",0]),3),round(float(m3.conf_int().loc["consistency_w",1]),3)]
NUM["consistency_b_catfe"]=round(float(m4.params["consistency_w"]),3)
NUM["logvid_b_full"]=round(float(m3.params["log_nvid_w"]),3)
NUM["R2_m1"]=round(float(m1.rsquared),3); NUM["R2_m2"]=round(float(m2.rsquared),3); NUM["R2_m4"]=round(float(m4.rsquared),3)

# ---------- TABLE 4: efficiency (views/video) + abandonment ----------
me=smf.ols("log_vpv_w ~ log_nvid_w + age_years_w + consistency_w + active_share_w + back_load_w + log_recency_w", data=d).fit(cov_type="HC1")
da=d.dropna(subset=["abandoned"]).copy()
ml=smf.logit("abandoned ~ log_nvid_w + age_years_w + consistency_w + upm_tenure", data=da).fit(disp=0)
with open(f"{OUT}/table4_efficiency_abandon.txt","w") as f:
    f.write("TABLE 4A. OLS DV=log(views/video)\n"+pd.concat([me.params.round(3),me.bse.round(3),me.conf_int().round(3)],axis=1).to_string())
    f.write("\n\nTABLE 4B. Logit DV=abandoned (no upload 180d)\n"+pd.concat([ml.params.round(3),ml.bse.round(3)],axis=1).to_string())
NUM["vpv_consistency_b"]=round(float(me.params["consistency_w"]),3)
NUM["vpv_logvid_b"]=round(float(me.params["log_nvid_w"]),3)
NUM["aband_consistency_b"]=round(float(ml.params["consistency_w"]),3)

# effect sizes
p25,p75=d.consistency.quantile(.25),d.consistency.quantile(.75)
NUM["consistency_p25"]=round(float(p25),3); NUM["consistency_p75"]=round(float(p75),3)
NUM["iqr_pct_subs"]=round(100*(np.exp((p75-p25)*m3.params["consistency_w"])-1),0)
NUM["double_vol_pct_subs"]=round(100*(np.exp(np.log(2)*m3.params["log_nvid_w"])-1),0)

# volume quintile table for Fig1
df["volq"]=pd.qcut(df.inv_n_videos,5,labels=[1,2,3,4,5])
q=df.groupby("volq",observed=True).agg(med_subs=("subscriberCount","median"),med_vpv=("views_per_video","median"),
   med_upm=("upm_tenure","median"),aband=("abandoned","mean")).reset_index()
q.to_csv(f"{OUT}/fig1_quintiles.csv",index=False)
NUM["vq"]=q.to_dict("list")

# ---------- FIGURE 1: dissociation (subs up, views/video down across volume quintiles) ----------
fig,ax1=plt.subplots(figsize=(6.5,4.2))
x=q.volq.astype(int)
ax1.plot(x,q.med_subs/1000,"o-",color="#1f4e79",lw=2,label="Median subscribers (000s)")
ax1.set_xlabel("Upload-volume quintile (lifetime videos)"); ax1.set_ylabel("Median subscribers (000s)",color="#1f4e79")
ax1.tick_params(axis="y",labelcolor="#1f4e79"); ax1.set_xticks(x)
ax2=ax1.twinx()
ax2.plot(x,q.med_vpv/1000,"s--",color="#c00000",lw=2,label="Median views per video (000s)")
ax2.set_ylabel("Median views per video (000s)",color="#c00000"); ax2.tick_params(axis="y",labelcolor="#c00000")
plt.title("Volume buys subscribers but dilutes per-video attention")
fig.tight_layout(); fig.savefig(f"{OUT}/fig1_dissociation.png",dpi=200); fig.savefig(f"{OUT}/fig1_dissociation.pdf"); plt.close()

# ---------- FIGURE 2: consistency vs log subs binscatter (residualized on volume+age) ----------
d["res_subs"]=smf.ols("log_subs_w ~ log_nvid_w + age_years_w",data=d).fit().resid
d["cbin"]=pd.qcut(d.consistency,20,duplicates="drop")
b=d.groupby("cbin",observed=True).agg(x=("consistency","mean"),y=("res_subs","mean")).reset_index()
fig,ax=plt.subplots(figsize=(6.5,4.2))
ax.scatter(b.x,b.y,color="#1f4e79",s=28)
mm=np.polyfit(b.x,b.y,1); xs=np.linspace(b.x.min(),b.x.max(),50); ax.plot(xs,np.polyval(mm,xs),"-",color="#c00000",lw=2)
ax.set_xlabel("Posting consistency (steadiness of monthly cadence)")
ax.set_ylabel("Subscribers, residualized on volume & age (log)")
ax.set_title("Steadier producers scale, holding volume and age constant")
ax.axhline(0,color="grey",lw=.6); fig.tight_layout()
fig.savefig(f"{OUT}/fig2_consistency_binscatter.png",dpi=200); fig.savefig(f"{OUT}/fig2_consistency_binscatter.pdf"); plt.close()

# ---------- FIGURE 3: abandonment by volume quintile ----------
fig,ax=plt.subplots(figsize=(6.5,4.0))
ax.bar(x,q.aband*100,color="#1f4e79")
ax.set_xlabel("Upload-volume quintile"); ax.set_ylabel("% abandoned (no upload in 180 days)")
ax.set_xticks(x); ax.set_title("Low-volume creators stall; the gap is steadiness, not output")
for xi,yi in zip(x,q.aband*100): ax.text(xi,yi+0.3,f"{yi:.1f}%",ha="center",fontsize=9)
fig.tight_layout(); fig.savefig(f"{OUT}/fig3_abandonment.png",dpi=200); fig.savefig(f"{OUT}/fig3_abandonment.pdf"); plt.close()

json.dump(NUM, open(f"{OUT}/numbers.json","w"), indent=2)
print("EXHIBITS WRITTEN. Key numbers:"); print(json.dumps(NUM,indent=2))
