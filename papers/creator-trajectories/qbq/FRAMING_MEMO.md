# FRAMING MEMO — EXPLORATORY, NOT LOCKED

> Status (updated 2026-06-17, per Katie): this is a CANDIDATE direction from an open exploration of
> what to do with the longitudinal data, NOT a committed framing. The reach-scaling framing below was
> superseded mid-exploration by a survival-centered reading (see the exploration note in
> `RESEARCH/YT LONGITUDINAL/PROGRESS_LOG.md`, 2026-06-17). Nothing here is locked. Revisit and
> re-decide the framing when picking the project back up.

## §1 Phenomenon (canonical numbers + N)
Solo creator-entrepreneurs are a large and growing organizational form (Goldman Sachs projects the creator economy near $480B by 2027). I study the full reconstructed production histories of **9,591 U.S. solo (individual-run) YouTube creators**, built from **11,576,217 dated video uploads** in a longitudinal inventory. The median creator is ~7.4 years old with 652 lifetime uploads and 16,400 subscribers. Analytic N = 9,583.

## §2 Mechanism (named, conditioned, distinct from the finding)
**The reliability premium.** A platform's selection environment (the recommender algorithm plus the audience's attention routines) rewards *reliable* production over *voluminous* production. Steady cadence is a credible, observable signal of organizational reliability and accountability (Hannan & Freeman 1984) that lowers audience uncertainty and entrains attention; raw volume without rhythm is unreliable output that the evaluation system discounts. The mechanism (reliability-as-signal, entrainment-of-attention) is distinct from the finding (consistency predicts scale): the finding is the association; the mechanism is why selection favors it.

## §3 Alternatives + discriminating tests
1. *Volume-is-everything (folk theory)*: predicts log-volume dominates. TEST: nested models — volume coef collapses 0.33→0.10 once rhythm enters (Table 3).
2. *Still-active artifact* (consistency just proxies "posted recently"): TEST: control log days-since-last-upload; consistency b=2.38 stable, recency ≈ 0 (Table 3, m3).
3. *Niche sorting* (steady creators are in high-reach categories): TEST: category FE; consistency b=2.49 within-category; category alone explains R²=0.02 (Table 3, m4).
4. *Reverse causality* (success enables steady posting): NOT ruled out cross-sectionally; declared a boundary, framed as association not effect.
5. *Survivorship*: addressed via abandonment model (Table 4B) and full-tenure (zeros-included) cadence measure.

## §4 Theory contradicted/extended
EXTENDS organizational reliability theory (Hannan & Freeman 1984) into platform/creator ventures; CONTRADICTS the platform-labor "always-on / maximize output" visibility-labor narrative (Duffy 2017; Bishop 2019; Cotter 2018) by showing the temporal *structure* of production, not its *quantity*, is what scales. Connects to audience-evaluation (Zuckerman 1999; Hsu 2006; Hsu, Hannan & Koçak 2009; Pontikes 2012) and entrepreneurship-as-scaling (Shane & Venkataraman 2000; Fisher, Josefy & Neubert 2024).

## §5 Falsifiable expectations
- E1: net of volume and age, consistency is positively associated with subscribers. [SUPPORTED b=2.38***]
- E2: volume's association with subscribers attenuates sharply once consistency is modeled. [SUPPORTED 0.33→0.10]
- E3: volume is *negatively* associated with per-video attention (dilution); consistency positively. [SUPPORTED vpv: vol −0.51, consistency +2.83]
- E4: low consistency predicts venture abandonment. [SUPPORTED logit −7.28; stall 18.6% Q1 vs 1.0% Q5]

## §6 Contribution (challenged assumption)
Challenges the assumption (shared by platform-labor and lay creator advice) that creator success is an output-maximization problem. Reframes it as an organizational-reliability problem: the venture scales when its production becomes a dependable routine, not when its output volume rises.

## §7 ONE-SENTENCE MESSAGE (tweet test)
Among solo creator-entrepreneurs, steadiness beats volume: a steady production rhythm predicts ~57% more subscribers across its interquartile range, while doubling output buys only ~6%, because platforms select for reliable producers, not prolific ones.
