#!/usr/bin/env python3
"""
06_long_horizon.py — ~15-month prospective design (Katie's 1-year idea).
PREDICTOR window: each channel's upload reliability measured over its history UP TO the 2025 baseline
   (split at 2025-03-01), from the video inventory. Measured BEFORE the outcome window.
OUTCOME window: 2025 baseline -> June 2026 (~15 months):
   (a) SURVIVAL  = production cessation (time since last upload as of latest inventory scrape),
                   failure flagged at 3/6/9/12-month thresholds.
   (b) GROWTH    = subscriber change from Infludata 2025 baseline to June 2026 panel.
INPUT : data/video_inventory/gender_gap_inventory.csv ; data/processed/gender_gap_panel_clean.csv ;
        /tmp/gg_panel/2026-06-13.csv
OUTPUT: processed/long_horizon.csv ; output/long_horizon_log.txt ; output/long_horizon_numbers.json
"""
import pandas as pd, numpy as np, json, statsmodels.formula.api as smf
from collections import defaultdict
pd.set_option("display.width",170); pd.set_option("display.max_columns",40)
ROOT="/Users/katieapker/Library/CloudStorage/GoogleDrive-apker.katie@gmail.com/My Drive/RESEARCH/YT LONGITUDINAL"
PROJ=f"{ROOT}/papers/creator-trajectories"
INV=f"{ROOT}/data/video_inventory/gender_gap_inventory.csv"
CUT=pd.Timestamp("2025-03-01",tz="UTC")

# ---- build PRE-baseline reliability (predictor) + POST-baseline production (survival) from inventory ----
pre_months=defaultdict(lambda: defaultdict(int))   # ch -> {YYYYMM: count} for uploads BEFORE cut
pre_first={}; pre_last={}; pre_n=defaultdict(int)
post_n=defaultdict(int); last_upload={}; scraped={}
for ch in pd.read_csv(INV, usecols=["channel_id","published_at","scraped_at"], chunksize=2_000_000, dtype=str):
    p=pd.to_datetime(ch["published_at"],errors="coerce",utc=True)
    s=pd.to_datetime(ch["scraped_at"],errors="coerce",utc=True)
    ch=ch.assign(p=p,s=s).dropna(subset=["p"])
    for cid,pp,ss in zip(ch.channel_id, ch.p, ch.s):
        if pd.notna(ss): scraped[cid]=max(scraped.get(cid,ss),ss)
        if cid not in last_upload or pp>last_upload[cid]: last_upload[cid]=pp
        if pp<CUT:
            pre_n[cid]+=1; pre_months[cid][pp.strftime("%Y%m")]+=1
            if cid not in pre_first or pp<pre_first[cid]: pre_first[cid]=pp
            if cid not in pre_last or pp>pre_last[cid]: pre_last[cid]=pp
        else:
            post_n[cid]+=1

# pre-baseline reliability features
rows=[]
for cid in pre_n:
    if pre_n[cid]<3: continue                      # need minimal pre-history to define reliability
    f=pre_first[cid]; l=pre_last[cid]
    start=pd.Period(f,freq="M"); end=pd.Period(CUT,freq="M")
    idx=pd.period_range(start,end,freq="M")
    series=np.array([pre_months[cid].get(p.strftime("%Y%m"),0) for p in idx],dtype=float)
    cv=series.std()/series.mean() if series.mean()>0 else np.nan
    consistency=1.0/(1.0+cv) if cv==cv else np.nan
    active_share=(series>0).mean()
    upm=series.mean()
    age_pre=(CUT-f).days/365.25
    # SURVIVAL: days from baseline to last upload (cessation timing); censor at scrape
    sc=scraped.get(cid, last_upload[cid])
    days_to_last=(last_upload[cid]-CUT).days        # >0 = produced after baseline this many days until last upload
    days_since_last=(sc-last_upload[cid]).days       # gap at scrape
    rows.append(dict(channel_id=cid, pre_consistency=consistency, pre_active_share=active_share,
        pre_upm=upm, pre_nvid=pre_n[cid], pre_age_years=age_pre,
        post_nvid=post_n.get(cid,0), days_to_last=days_to_last, days_since_last=days_since_last,
        last_upload=last_upload[cid]))
pred=pd.DataFrame(rows)
print("channels with usable pre-2025 history:",len(pred))

# ---- OUTCOME: subscriber growth Infludata(2025) -> June 2026 ----
clean=pd.read_csv(f"{ROOT}/data/processed/gender_gap_panel_clean.csv",low_memory=False)[["channel_id","subscriberCount","perceivedGender","race","Topic 1"]].rename(columns={"subscriberCount":"subs_2025"})
jun=pd.read_csv("/tmp/gg_panel/2026-06-13.csv",usecols=["channel_id","subscriber_count"]).rename(columns={"subscriber_count":"subs_2026"})
df=pred.merge(clean,on="channel_id",how="inner").merge(jun,on="channel_id",how="inner")
df["growth_15mo_log"]=np.log1p(df.subs_2026)-np.log1p(df.subs_2025)
df["growth_15mo_pct"]=np.where(df.subs_2025>0,(df.subs_2026-df.subs_2025)/df.subs_2025,np.nan)
df["log_subs0"]=np.log1p(df.subs_2025); df["log_prenvid"]=np.log1p(df.pre_nvid)
print("final analytic N:",len(df))

NUM={"N":int(len(df)),"baseline":"~2025-03 (Infludata)","endpoint":"2026-06-13","horizon_months":15}
# FAILURE RATES at multiple thresholds (production cessation as of latest scrape)
for thr in [90,180,270,365]:
    rate=(df.days_since_last>thr).mean()
    NUM[f"fail_rate_{thr}d"]=round(float(rate),3)
print("\n===== FAILURE (production cessation) at thresholds =====")
for thr in [90,180,270,365]:
    print(f"  no upload in {thr}d: {100*NUM[f'fail_rate_{thr}d']:.1f}% failed")

# winner-take-all over 15 months
tot=df.eval("subs_2026-subs_2025").clip(lower=0).sum()
df["szdec"]=pd.qcut(df.subs_2025.rank(method="first"),10,labels=False)
topshare=df.groupby("szdec").apply(lambda x:(x.subs_2026-x.subs_2025).clip(lower=0).sum()).iloc[-1]/tot
NUM["wta_top_decile_share_15mo"]=round(float(topshare),3)
print(f"\nWINNER-TAKE-ALL (15mo): top size-decile captured {100*topshare:.0f}% of all net new subscribers")

def wins(s,p=0.01): return s.clip(s.quantile(p),s.quantile(1-p))
for c in ["growth_15mo_log","pre_consistency","pre_active_share","log_prenvid","pre_age_years","log_subs0"]:
    df[c+"_w"]=wins(df[c])

# ===== H1 (15mo): pre-2025 reliability -> SURVIVAL (fail at 180d) =====
print("\n===== H1: pre-2025 reliability -> failure (no upload 180d), 15-mo horizon =====")
df["failed180"]=(df.days_since_last>180).astype(int)
ds=df.dropna(subset=["failed180","pre_consistency","log_prenvid","pre_age_years","log_subs0"])
ms=smf.logit("failed180 ~ pre_consistency + log_prenvid + pre_age_years + log_subs0",data=ds).fit(disp=0)
iqr=ds.pre_consistency.quantile(.75)-ds.pre_consistency.quantile(.25)
NUM["surv15_consistency_b"]=round(float(ms.params["pre_consistency"]),3)
NUM["surv15_OR_iqr"]=round(float(np.exp(ms.params["pre_consistency"]*iqr)),3)
print("pre_consistency b=%.3f se=%.3f  IQR->failure OR x%.3f"%(ms.params["pre_consistency"],ms.bse["pre_consistency"],NUM["surv15_OR_iqr"]))

# ===== H2 (15mo): pre-2025 reliability -> GROWTH over 15 months =====
print("\n===== H2: pre-2025 reliability -> 15-month subscriber growth (net of baseline size) =====")
dg=df.dropna(subset=["growth_15mo_log_w","pre_consistency_w","log_prenvid_w","pre_age_years_w","log_subs0_w"])
mg=smf.ols("growth_15mo_log_w ~ pre_consistency_w + pre_active_share_w + log_prenvid_w + pre_age_years_w + log_subs0_w",data=dg).fit(cov_type="HC1")
print("R2=%.3f N=%d"%(mg.rsquared,int(mg.nobs)))
print(pd.concat([mg.params.round(3),mg.conf_int().round(3)],axis=1).to_string())
NUM["growth15_consistency_b"]=round(float(mg.params["pre_consistency_w"]),3)
NUM["growth15_consistency_ci"]=[round(float(mg.conf_int().loc["pre_consistency_w",0]),3),round(float(mg.conf_int().loc["pre_consistency_w",1]),3)]
# horse race: volume vs consistency on 15mo growth
mvol=smf.ols("growth_15mo_log_w ~ log_prenvid_w + pre_age_years_w + log_subs0_w",data=dg).fit(cov_type="HC1")
mboth=smf.ols("growth_15mo_log_w ~ log_prenvid_w + pre_consistency_w + pre_age_years_w + log_subs0_w",data=dg).fit(cov_type="HC1")
NUM["growth15_vol_alone"]=round(float(mvol.params["log_prenvid_w"]),3)
NUM["growth15_vol_withcons"]=round(float(mboth.params["log_prenvid_w"]),3)
NUM["growth15_cons_inboth"]=round(float(mboth.params["pre_consistency_w"]),3)
print(f"\n15mo growth horse race: volume alone={NUM['growth15_vol_alone']} -> with consistency={NUM['growth15_vol_withcons']}; consistency b={NUM['growth15_cons_inboth']}")
# effect size
p25,p75=dg.pre_consistency.quantile(.25),dg.pre_consistency.quantile(.75)
NUM["growth15_iqr_pct"]=round(100*(np.exp((p75-p25)*mg.params["pre_consistency_w"])-1),1)
print(f"IQR consistency -> {NUM['growth15_iqr_pct']}% extra subscriber growth over 15 months")

df.to_csv(f"{PROJ}/processed/long_horizon.csv",index=False)
json.dump(NUM,open(f"{PROJ}/output/long_horizon_numbers.json","w"),indent=2)
print("\nSAVED long_horizon.csv + long_horizon_numbers.json")
print(json.dumps(NUM,indent=2))
