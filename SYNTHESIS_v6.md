# What do LLM inference-optimization papers optimize? A full-text survey of 137 optimizers and 10 metric papers
Public version of synthesis v6.1 (2026-10-06). It was revised through five adversarial review rounds; the section on
implications for the authors' own unpublished work is omitted from this public copy.
Repository root = project directory. Full texts of papers are not redistributed (see README).

Tags: [P] primary, full text read (per-paper record in `records/`); [abstract only]; [D] our count from the records
(script named); [Syn] our synthesis. Percentages carry Wilson 95 % confidence intervals where they support a claim.

Coding terms:
- **Objective:** what a method is designed to improve. It must be backed by a verbatim *design* statement: problem
  formulation, objective function, reward, policy goal or stated design goal. After a re-pass of every record, the re-pass
  agents labelled 402 of 403 optimized entries "design". The R2 reviewer judged about 7 of 45 checked quotes
  (≈ 15 %) to be motivation or evaluation sentences, so a minority of objectives rest on weak design evidence.
- **Constraint:** what the method must respect, such as an SLO, a quality floor or a memory budget.
- **Reported:** evaluated, or claimed in a headline, but not targeted.

Population: 137 full-text optimizer papers unless stated. The 55 abstract-only and 10 metric/benchmark papers are kept
separate.

---

## 0. Short answer

1. **The commonest objective is throughput; token pace and quality enter mostly as constraints** [D].
   - Throughput (token or request) is an objective in 42 % of papers [34–50]. Only 20 of these 57 also state a latency
     constraint.
   - Token pace (TPOT/TBT) is a constraint in 19 % and an objective in 6 %. Quality is a constraint in 26 % [20–34] and an
     objective in 2 %.
   - Other latencies are not mainly constraints. TTFT is an objective in 14 % and a constraint in 15 %; request latency is
     an objective in 14 % and a constraint in 7 %. Across the corpus, a latency family is an objective in 45 papers and a
     constraint in 38.
   - Goodput or SLO attainment is an objective in 18 % [12–25].
   - "Maximize throughput, goodput or cost subject to latency targets (TTFT, TPOT/TBT or E2E)" describes about half of the 82 papers with such
     an objective (42, counting goodput objectives). It is the typical form for schedulers and P/D systems, not for the
     corpus as a whole [D/Syn].
2. **Two things set what a paper optimizes: its technique layer and the load it is evaluated under** [D, §4].
   - **No online serving load.** 60 of 137 papers (44 %) never evaluate under online request arrivals: offline batch 32,
     single sequence 25, analytical 3. This covers most speculative-decoding, quantization, KV-compression, kernel and
     offloading work. These optimize single-sequence decode speed, memory or kernel efficiency, with quality as a
     constraint.
   - **Schedulers and P/D-disaggregation systems** mostly optimize throughput or goodput (21 of 23 schedulers). About
     half add latency constraints: 12 of 23 schedulers state one (13 of 23 counting goodput objectives), as do 5 of 8
     P/D systems.
   - **Routers and placement systems** are mixed. Across the 13 such papers, TTFT, E2E, throughput and cost appear about
     equally often as objectives, and only 3 state a TTFT constraint.
   - **Prefix caching** optimizes TTFT or throughput.
   - **Agent and compound serving** optimizes program-level completion time (10 of 16 papers).
3. **The tail is rarely the quantity minimized. It enters as a distributional target over requests** [D, §6].
   - **Directly minimized:** only 2 papers (strict reading). GORGO tunes its router against −p95 TTFT; Autellix targets
     P95/P99 program latency to curb starvation.
   - **Tail named as a design aim, no percentile objective:** 3 more. Preble aims at "average and tail latency" (P99 is its evaluation statistic). Kairos prioritizes by
     accumulated latency to reduce tail workflow latency. PolyServe uses wait-time-aware scheduling to manage tail
     latency.
   - **Distributional target:** 32 of the 77 papers evaluated under online or mixed load (42 % [31–53]) set a percentile
     SLO, goodput/attainment at X %, or per-token deadlines.
   - **Mean or unspecified:** 25 of those 77 (32 %) target latency at the mean or leave the statistic unspecified. Corpus-wide,
     only about 4–5 of the 32 tier-3 papers name the mean in a design statement (about 9 papers across all tiers do).
   - **Many "TPOT SLOs" are attainment of a per-request *mean*.** About 6–8 papers constrain per-request mean TPOT (AdaSpec and AdaServe mixed: per-step bounds in design, per-request
     means in evaluation); about 13 constrain token-level timing by percentile, per-iteration budget, every-token bound or
     per-token deadline.
   - **Routers that target tails exist; the one RL router in the corpus does not.** GORGO uses an evolution strategy. The online-LP
     router (Chen et al., ICML 2026) folds tail-latency thresholds into per-request indicator rewards. The learned routers
     in the corpus target the mean or leave the statistic unspecified: Lodestar (an online-learned predictor with greedy
     routing; reward −TTFT) and the Intelligent Router (heuristic-guided RL; "minimize end-to-end latency").
   - **GORGO shows how a tail objective can be gamed** [P, arxiv_2602.11688, Table 8]. With the queue weight unbounded
     (W_queue = 0, labelled "reward hacking"), one setting wins every TTFT percentile by sending about 100 % of traffic
     to one replica, with the worst E2E tails and worst median ITL. GORGO's main design bounds the queue weight to
     [0.05, 0.5] and improves held-out p95 E2E by 14.3–30.9 %; the authors say the bound "mitigates but does not
     eliminate" the trade-off.
4. **Metric names do not pin down quantities** [P, notes/DEFINITIONS.md; counts over the 143 full-text records available
   when it was built].
   - **TTFT:** counted from arrival in 16 papers, as prefill time in 15 (5 of which measure under load anyway),
     unstated in 19–20 (20 by script after the re-pass).
   - **Goodput:** at least 8 definitions. The most common is "max rate at X % attainment" (13 papers, X = 90 in 11).
     Others include SLO-meeting tokens/s, a *fraction* (Medha), and a no-SLO version (TurboSpec).
   - **Throughput:** tokens counted four different ways, plus "unstated".
   - **TPOT vs TBT:** TPOT is a per-request mean, TBT a per-token distribution, and 5 papers call a mean "TBT".
   - **Undefined headline metric:** 28 % of papers.
   - **Benchmark harnesses** (MLPerf, vLLM, GenAI-Perf) agree that TTFT includes server-side queueing (MLPerf from the
     scheduled arrival, the others from request send) and on TPOT. They diverge on ITL, throughput accounting and
     goodput [P, notes/INDUSTRY_DEFS.md]. MLPerf gates TTFT and TPOT each at P99 (separately, not a joint 99 %), where
     11 of the 13 papers that define goodput as max rate at X % attainment use X = 90 (joint in most). vLLM's "goodput" is a measured good-request rate at a single
     load.
5. **Headline wording often names a narrower quantity than it implies** [P]. Examples:
   - SmoothQuant's "end-to-end latency" is one forward pass of a batch of 4.
   - SpecInfer's "end-to-end latency" is average per-token latency.
   - Sequoia's "TBT" is ms/token for one sequence.
   - ServerlessLLM's "latency" is model start-up time.
   - vLLM's "throughput" is the request rate at the knee of a mean normalized-latency curve.
   - EAGLE-3's "up to 6.5×" is single-sequence speedup; its SGLang throughput gain is 1.81× at batch 2 and 1.38× at
     batch 64.

   Abstracts are not enough to code objectives. On the same 133 papers, abstract-level codes matched the full-text
   objective set exactly in 16 cases (mean Jaccard 0.43) [D].
6. **The expected metric list needs four additions** [Syn]:
   - single-sequence decode speed, which is not a serving latency;
   - program/workflow completion time;
   - token-timeline QoE metrics (Andes QoE, Etalon fluidity, smooth goodput), which penalize stalls that mean TPOT
     hides;
   - mechanism proxies optimized directly (cache hit rate, model start-up time).

   TPS/user is coded in only 4 records (DeepSpeed-FastGen's per-client rate SLA, Helix Parallelism, WaferLLM,
   Step-3's 20 tok/s SLA); 6 records define or use a per-stream token rate, and 2 more use "TPS" for system tokens/s (DEFINITIONS §1.7). It is the interactivity axis of the throughput–interactivity trade-off, which CloudMatrix384
   shows under a TPOT bound: decode throughput of 1,943 tok/s per NPU at 50 ms (batch 96) versus 538 at 15 ms
   (batch 8) [P].

---

## 1. Corpus and method

**Discovery** [D, `candidates/`, `SELECTION.tsv`]. Six Sonnet agents covered six layers: scheduling, cluster level, KV
cache, decoding and compression, kernels/runtime/hardware, and agentic serving plus metric papers. They used Semantic
Scholar, OpenAlex, the arXiv API and web search. Every arXiv ID was checked against its title. The result was 210 unique
papers.

**Selection** was purposive, not random:
- canonical, high-uptake or venue-published work;
- at least 60 % from 2024–26 and at least 30 % from 2025–26 in each cluster;
- 133 optimizers read in full, plus 4 routing and scheduling papers added after review R1 (GORGO, the online-LP router,
  PPD, ExeGPT), for 137 in total;
- 10 metric/benchmark papers read in full;
- 60 papers on an abstract-only track, of which 55 had a usable abstract;
- 7 non-optimizers excluded.

**Composition** [D]:
- Year (first arXiv version): 2022: 8, 2023: 26, 2024: 57, 2025: 40, 2026: 6.
- Layer:

| Layer | Papers |
|---|---|
| request scheduling | 23 |
| agent/compound | 16 |
| cluster routing | 13 |
| parallelism/offload/hardware | 13 |
| speculative/decoding | 13 |
| kernels | 8 |
| prefix caching | 8 |
| P/D disaggregation | 8 |
| quantization | 7 |
| KV compression | 7 |
| KV memory | 5 |
| long context | 5 |
| energy/cost | 4 |
| MoE | 4 |
| LoRA/multi-model | 3 |

**Selection skew.** No 2025–26 quantization or KV-compression paper was read in full; those went to the abstract
track. Time trends therefore have to be read within comparable subsets (§5).

**Full texts.** All 147 full texts were obtained: arXiv, plus USENIX/ACM/author PDFs for Orca, SOLA, dLoRA and Aegaeon.
Nothing is outstanding.

**Extraction and checks.**
- 16 Sonnet extraction agents each produced one JSON record per paper (`SCHEMA.md`, `scripts/validate_record.py`).
- **Re-pass after R1.** Every optimized entry needed a design-statement quote, or it was moved to "reported". About 48
  headline-only entries were demoted. Statistics were set to "unspecified" unless the paper states them, and a load
  class was recorded for each paper. Backups are in `archive/records_pre_tailaudit/` and `archive/records_pre_repass/`.
- **Blind second extraction** of 30 records, 2 per batch for E01–E12 plus 6 from the agent and industrial batches.
  Primary-objective agreement was 28/30. Mean Jaccard was 0.74 on objective codes and 0.74 on objective plus
  constraint, and the objective sets and constraint sets each matched exactly in 14/30 [D, `qa/QA_COMPARISON_v2.txt`].
  Primary objectives are therefore reliable, but exact sets, especially constraints, are noisy. The 2 primary misses
  are coding conventions, now fixed as normalization rules N1–N7.
- **Blind tail-tier coding** of 30 papers (23 online/mixed, 7 other, after the load-class recode) by a coder who saw only the full texts: tier
  agreement 25/30, Cohen κ = 0.76. On "tier 1 + 2a vs the rest" it agreed on 29/30 [D, `qa/TIER_QA_COMPARISON.txt`].
  The disagreements were borderline calls: tier 3 vs 5 for HexGen-2, LMCache and vLLM; 5 vs 2b for VTC; 2a vs 3 for
  LoongServe.
- **Tail-role audit** of 40 papers [qa/TAIL_AUDIT.md].
- **Quote verification:** 181 definition quotes were checked against the full texts.

**Analysis** was done at the level of metric *families*: 16 families, 15 named plus mechanism/other (`FAMILY` in `scripts/aggregate.py`;
`scripts/analysis_v3.py`). The families group codes, so different groupings move individual shares but not the
ordering. Merging goodput into throughput makes throughput's lead larger.

---

## 2. The metric list, derived from the papers

Notation [Syn, DEFINITIONS.md §0]. A request arrives at *a* and emits tokens at t_1..t_n. Then:
- TTFT = t_1 − a
- TPOT = (t_n − t_1)/(n−1)
- TBT samples are the gaps t_i − t_{i−1}
- E2E = t_n − a = TTFT + (n−1)·TPOT
- normalized latency = E2E/n

| # | Metric | Operational definition (consensus) | Variants found (papers) [P; counts D: analysis/def_variants.py, over the 143 records available then] |
|---|---|---|---|
| 1 | TTFT | arrival → first token (queueing + any KV load + prefill) | from arrival (16); = prefill time (15, 5 of which measure under load); offline (7); unstated (19–20); incl. RAG pipeline (RAGO); incl. KV loading (CacheGen); measured after prefill at a decode-side router (OLP router) |
| 2 | TPOT | per-request mean decode gap; a distribution over requests | per-request mean (13); "latency/output tokens" incl. prefill (Mélange); per-iteration time (5); deadline form TTFT + i·TPOT (6) |
| 3 | TBT / ITL | each gap is a sample; a distribution over tokens | token-level distribution (16); an average called TBT/ITL (5); batch-1 ms/token (Sequoia); per-request P99 of own gaps (Apt-Serve) |
| 4 | E2E (TTLT, JCT) | arrival → last token | per request under load; offline batch wall time recoded as OTHER:batch_time in 6 records (SmoothQuant, FlexGen, H2O, InfiniGen, Helium, dLoRA's migration objective) |
| 5 | Normalized latency | E2E / output tokens, averaged | mean (9), median (5), P90 (2), ratio of sums (dLoRA), ÷ input+output (LoongServe); at least 7 names |
| 6 | Single-sequence decode speed | per-token time, tok/s or speedup at batch 1 or a fixed batch, no arrivals | ms/token; tokens/s of one sample called "throughput"; wall-clock speedup |
| 7 | TPS/user (interactivity) | 1/TPOT per stream | 1/TTL (Helix); TPR = 1/TPOT at batch 1 (WaferLLM); 20 tok/s SLA (Step-3); per-client rate SLA (FastGen) |
| 8 | Token throughput | tokens/s completed; must state which tokens, phase, per GPU | input+output (7), output-only (13), decode-only (8), prefill-only (8), unstated (8) |
| 9 | Request throughput / capacity | completed req/s, or max rate sustained under a stated condition | measured req/s (11); knee of a latency curve, no numeric SLO (5: vLLM, Orca, …); max rate under an explicit latency target (14); programs/s (4); queueing-stability limit (1) |
| 10 | Goodput | throughput counting only SLO-satisfying work | max rate at X % attainment (13; X = 90 in 11); measured SLO-meeting req/s (5); SLO-meeting tokens/s (3); a fraction (Medha); no SLO (TurboSpec); completed-only (Mooncake); apps by deadline; smooth goodput |
| 11 | SLO attainment | fraction of requests (or tokens) meeting SLOs | per request, joint TTFT+TPOT; per token (Aegaeon); per-request mean TPOT ≤ SLO (AdaServe) |
| 12 | Queueing delay | arrival → first scheduled | P99 scheduling delay as a capacity condition (Vidur) |
| 13 | Program/workflow JCT | submission → final output of a multi-call program | mean JCT; batch makespan (Helium); program-level token latency = program time / tokens (Autellix, Kairos) |
| 14 | Token-timeline QoE | how the delivery timeline tracks per-token deadlines | Andes QoE = 1 − S_delay/S_whole; Etalon fluidity index; smooth goodput (idle latency = max_i(t_i − d_i)) |
| 15–22 | Cost, energy, memory, quality, fairness, utilization, acceptance, mechanism proxies | see DEFINITIONS.md §1.15–1.22 | energy scope: GPU-only (ML.ENERGY) vs node (TokenPowerBench); fairness as weighted service (input 1, output 2; VTC, DLPM) |

**Industry harnesses** [P, notes/INDUSTRY_DEFS.md]:
- **MLPerf Inference** times latency from the LoadGen scheduled time, so TTFT includes queueing, and uses
  TPOT = (latency − TTFT)/(n − 1). It gates on P99 TTFT and P99 TPOT, for example 2,000 ms / 200 ms for Llama-2-70B in
  the server scenario and 450 / 40 ms interactive. The score is the maximum Poisson QPS that passes.
- **vLLM `bench serve`** reports TTFT from request send, TPOT excluding the first token, ITL as pooled gaps, and
  output-only and total token throughput. Its goodput is the measured rate of requests meeting all given SLOs, at one
  offered load. It cites DistServe but is a different quantity.
- **GenAI-Perf/AIPerf.** AIPerf defines ITL equal to TPOT; GenAI-Perf's ITL is per response. They give TPS/user
  variants with or without the first token.
- **Summary:** the harnesses agree with the modal academic TTFT and TPOT. They disagree with each other on ITL,
  throughput tokens and goodput.

**SLO thresholds have no standard** [P, DEFINITIONS.md §1.11].
- 30 papers use absolute thresholds and 22 use a multiple of a baseline. "5×" alone has four different baselines.
- 8 papers scale the TTFT bound with prompt length.
- "Human reading speed" is used to justify per-token targets from 40 ms to 0.5 s.
- DistServe sets SLOs empirically "because there exists no available SLO settings for these applications as far as we
  know" [P, arxiv_2401.09670 §6].
- MLPerf's fixed P99 gates are the nearest thing to a public standard.

---

## 3. What papers optimize: objective vs constraint

Table: share of 137 full-text optimizers with each metric family as objective or constraint, with Wilson 95 % CIs [D,
`analysis/summary_v3.txt`]. Abbreviations: con = constraint; Ftok = first-token (TTFT); TBT/TPOT = token pace;
single-seq = single-sequence decode speed.

| Family | Objective | Constraint | Reading |
|---|---|---|---|
| throughput | 42 % [34–50] | 1 % | the default quantity to maximize |
| single-sequence speed | 18 % [13–26] | 1 % | papers evaluated without arrivals |
| memory | 18 % [12–25] | 8 % | KV and weight footprint, enabling batch size |
| slo-goodput | 18 % [12–25] | 2 % | goodput or attainment as the objective |
| hardware efficiency | 18 % [12–25] | 1 % | kernels, MFU |
| first-token (TTFT) | 14 % [9–21] | 15 % [10–21] | objective for caching and some routers; constraint for schedulers and P/D |
| request latency (E2E, normalized, queueing) | 14 % [9–21] | 7 % | 17 of 19 such papers are evaluated under online arrivals; batch wall-times were recoded |
| cost / energy | 14 % [9–21] | 1 % | GPUs, $, J, under latency SLOs |
| program latency | 7 % [4–13] | 1 % | agent and compound serving |
| token pace (TPOT/TBT/TPS-user) | 6 % [3–11] | 19 % [13–26] | **mostly a constraint** |
| quality | 2 % [1–6] | 26 % [20–34] | **almost always a constraint** ("lossless", "≤ x drop") |
| mechanism proxies, fairness, QoE, start-up latency | ≤ 11 % | | small, but each defines its own metric |

Papers have 1 objective family in 49 cases, 2 in 62, and 3–4 in 26 [D].

## 4. Metric choice follows the technique layer and the load regime

Table: objective-family counts by layer, with the constraint families computed from the records [D]. Abbreviations:
Ftok = first-token; single-seq = single-sequence decode speed.

| Layer (n) | Objectives (count) | Constraints (count) |
|---|---|---|
| request scheduling (23) | throughput 14, slo-goodput 9, request latency 6, hw-eff 6 | token pace 8, Ftok 7, request latency 3 |
| agent/compound (16) | program latency 10, request latency 4, throughput 4 | token pace 2 |
| cluster routing/placement (13) | Ftok 4, request latency 4, throughput 4, cost 4, slo-goodput 3 | Ftok 3, token pace 2 |
| parallelism/offload/hardware (13) | throughput 7, hw-eff 7, single-seq 6, memory 4 | memory 3, quality 3 |
| speculative/decoding (13) | single-seq 9, throughput 5 | quality 10 |
| P/D disaggregation (8) | throughput 4, slo-goodput 4 | Ftok 5, token pace 5 |
| prefix/context caching (8) | Ftok 4, throughput 3 | quality 2 |
| kernels (8) | hw-eff 6 | quality 2 |
| KV compression (7) / quantization (7) | memory 5 / 4, single-seq 4 / 3 | quality 6 / 7 |
| long context (5) | Ftok 3, throughput 4 | slo-goodput 1, token pace 1, quality 1 |
| energy/cost (4) | cost/energy 4 | Ftok 2, token pace 2 |

Readings [Syn]:
- **H2 is supported.** The layer label was assigned by the same extractor that coded the metrics, and two layers
  (energy/cost, agent/compound) are partly defined by their metric. For those two layers the mapping is close to
  definitional.
- **The load regime is the sharper divide.** It explains why speed claims from different layers do not compare.
  - Speculative decoding, compression and kernel papers are mostly evaluated at batch 1 or a fixed batch.
  - Serving-aware speculative decoding moves to goodput or attainment under load: AdaServe, AdaSpec, and TurboSpec
    (whose "goodput" has no SLO).
  - EAGLE-3's "up to 6.5×" is single-sequence speedup over vanilla autoregressive decoding. In SGLang on H100 its
    throughput gain is 1.81× at batch 2 and 1.38× at batch 64 (Table 3, run by the SGLang team) [P].
  - SpecInfer's gain shrinks with batch size. MagicDec reports the reverse beyond a "critical sequence length": for long
    contexts, speculative decoding "can achieve higher speedups for larger batches" (up to 2.51× for LLaMA-3.1-8B)
    [P, arxiv_2408.11049 §1]. The regime, not the method, sets the sign.
- **Routing papers rarely target TTFT alone.** Of the 13 cluster-routing/placement papers, 4 have a first-token
  objective. Only Lodestar and GORGO make TTFT the routing objective outright.
  - Lodestar argues that "The time that TPOT and end-to-end latency are observed is much further in the future than the
    routing decision time", and that they are
    noisy because "they are affected by one more unknown factor, the number of decode tokens" [P,
    arxiv_2606.00946].
  - GORGO uses p95 TTFT as its tuning fitness [P, arxiv_2602.11688].

## 5. Change over time

Shares by year with Wilson 95 % CIs. "SLO-framed" = a goodput/attainment objective or a latency constraint [D,
`scripts/analysis_v3.py`].

| Subset | 2022–23 | 2024 | 2025–26 |
|---|---|---|---|
| All full-text (n = 34 / 57 / 46): SLO-framed | 18 % [8–34] | 28 % [18–41] | 46 % [32–60] |
| All full-text: goodput/attainment objective | 6 % [2–19] | 14 % [7–25] | 30 % [19–45] |
| Online or mixed load (n = 8 / 35 / 34): SLO-framed | 50 % [22–78] | 43 % [28–59] | 47 % [31–63] |
| Online or mixed load: goodput/attainment objective | 25 % [7–59] | 23 % [12–39] | 41 % [26–58] |
| Online or mixed load: capacity at a latency knee or target (DEFINITIONS Q4+Q5; the 4 E16 papers are not in the variant lists) | 5/8 | 9/35 | 2/34 |
| Full + abstract records (n = 39 / 73 / 80): SLO-framed | 18 % | 23 % | 36 % |

Trend tests within online/mixed papers (Cochran–Armitage, two-sided):
- SLO-framed: p = 0.95 (flat).
- Goodput/attainment as the objective: p = 0.14 (not significant).
- Knee/latency-target capacity: p < 0.001 (significant decline). Five of the 16 papers (Splitwise, Sarathi-Serve,
  LoongServe, Mooncake, Medha) define capacity under percentile or attainment SLOs, which is goodput in all but name.
  Excluding them, 4/8 → 5/35 → 2/34, and the decline is still significant (p = 0.005).

Readings [Syn]:
- **H1 is partly supported.** The corpus-wide SLO-framed share rises from 18 % to 46 %, and much of that is
  **composition**. Measured from the pooled 2022–24 rate (24 %), about half of the rise is composition; measured from
  2022–23 alone (8 online papers), about three-quarters is. Recent papers in our sample are more often serving systems evaluated under load: holding the
  2022–24 rates within each load class fixed, the 2025–26 mix predicts 34 % against the 46 % observed and
  the pooled 2022–24 rate of 24 %. The rest comes mostly from non-online 2025–26 papers that design to latency bounds (RAGO,
  MegaScale-Infer, CloudMatrix384, Step-3, DREX): 5 of 12, against 3 of 48 before 2025. Within online-load
  papers, about 43–50 % are SLO-framed in every period.
- **What changed significantly is how capacity is defined.** Within online-load papers, "max rate before latency/queueing
  blows up", or under a latency target, falls from 14/43 (33 %) before 2025 to 2/34 (6 %) in 2025–26.
- **Goodput at an attainment level looks like the replacement, but the evidence is weak.** Its rise as an objective
  (25 % → 23 % → 41 %) is not statistically significant at these sample sizes.
- **No level claims for 2022–23.** That cell has only 8 online-load papers.
- **Version 1's claimed declines in single-sequence-speed and memory objectives are withdrawn.** They were artefacts of
  track allocation: no 2025–26 compression paper was read in full.
- **The sample is purposive.** Discovery asked for at least 30 % 2025–26 papers per cluster, so these are shares of our
  corpus, not of the field.

## 6. Mean vs tail

Tiers describe how a method's *design* treats the statistic of serving latency [D, `scripts/analysis_v3.py`].
- Papers evaluated only on single sequences fall in tier 5, because batch-1 latency is not serving latency.
- Tier 1 membership is set by hand from qa/TAIL_AUDIT.md and the R2/R3 reviews. The blind second coding (§1) covered
  only one tier-1 paper (GORGO).

| Tier | All (n = 137) | Online/mixed load (n = 77) | Who / notes |
|---|---|---|---|
| 1a. A percentile is the quantity minimized (strict) | 2 (1 %) | 2 (3 %) | GORGO (fitness −p95 TTFT); Autellix (P95/P99 program latency, to curb starvation) |
| 1b. Tail named as a design aim, no percentile objective | 3 (2 %) | 3 (4 %) | Preble ("average and tail latency"; P99 is its evaluation statistic); Kairos (prioritizes by accumulated latency to "reduce tail"); PolyServe (wait-time-aware scheduling to "manage tail latency") |
| 2a. Distributional target over requests or tokens | 32 (23 % [17–31]) | 32 (42 % [31–53]) | percentile SLOs (Splitwise's nine P50/P90/P99 SLOs; Sarathi-Serve P99 TBT; Mooncake P90 TTFT/TBT; DynamoLLM, ConServe P99; GreenLLM P95 TBT); goodput/attainment at X % (DistServe and successors); per-token deadlines or QoE (Andes, Aegaeon, JITServe); tail-threshold indicator rewards (OLP router) |
| 2b. Deterministic per-request or per-batch bound | 4 (3 %) | 0 | MegaScale-Infer (150 ms TBT), ExeGPT (bound on the P99-*length* sequence), S3, DREX |
| 3. Mean, or statistic unspecified | 32 (23 % [17–31]) | 25 (32 % [23–44]) | about 4–5 of 32 name the mean in a design quote; the rest take the statistic from evaluation or leave it unstated. Corpus-wide, about 9 papers name a mean in a latency design quote (R3 manual check). |
| 5. No serving-latency target | 64 (47 %) | 15 (19 %) | throughput-, memory-, speed- or cost-only, or single-sequence only |

Readings [Syn]:
- **Tails mostly enter design as SLOs over the request distribution.** Tier 2a is about 6–16 times tier 1 (32 vs 5
  lenient, 2 strict).
- **"Distributional" does not always mean "tail".** Many attainment targets are fractions of requests whose *mean* TPOT
  meets a threshold (e.g. AdaServe), so they constrain how per-request means are spread across requests, not
  token-level stalls. About 6–8 papers constrain per-request mean TPOT (DistServe, semi-PD, TaiChi, TokenScale, SOLA, Aladdin; AdaSpec and
  AdaServe are mixed: they bound each step in design but score SLOs on per-request means). About 13 constrain
  token-level timing directly:
  by percentile in Splitwise, Sarathi-Serve, Mooncake (P90), DynamoLLM, ConServe, HyGen, Apt-Serve and GreenLLM (P95),
  by a per-iteration budget in Medha, for every token in SLOs-Serve, and by per-token deadlines (token i by
  TTFT + i·TPOT) in Aegaeon, JITServe and PolyServe.
- **Directly minimizing a percentile is rare, and tier 1 is mostly recent.**
  - Strict: GORGO (2026) and Autellix (2025).
  - Lenient: Preble (2024), Kairos (2025) and PolyServe (2025).
  - Agent-serving papers reach tails through starvation and fairness mechanisms rather than percentile objectives.
- **Tail numbers in headlines are mostly reported results** [qa/TAIL_AUDIT.md]. 26 of 40 audited papers report tails
  without targeting them, e.g. Llumnix, Medha (174× tail-latency headline: P99 in the abstract, P90 TTFT vs LoongServe in Fig. 1a), SpotServe, TraCT, POD-Attention.
- **Mean metrics hide stalls, and the choice of metric can reverse a ranking.** Three metric papers argue this [P]:
  - **Etalon.** On Llama-3-8B/H100 with a 25 ms target, capacity in QPS (chart reads, ±0.02) is:
    - by TPOT: vLLM 0.66, Sarathi-Serve 1.16;
    - by P99 TBT: vLLM 0.65, Sarathi-Serve 0.34;
    - by fluidity: both 0.6 (Fig. 6a).

    Its Fig. 3 shows two systems with similar TPOT-based throughput but about 3× different tail-TBT-based throughput
    (arxiv_2407.07000).
  - **Andes.** A case where "TTFT or average TPOT does not degrade" while the user sees a mid-stream pause
    (arxiv_2404.16283).
  - **Smooth goodput.** Existing metrics can be gamed by delaying output or abandoning late requests (arxiv_2410.14257).
- **Tail objectives can be gamed too.** GORGO's −p95 TTFT fitness with an unbounded queue weight (W_queue = 0)
  concentrates about 100 % of traffic on one replica [P, Table 8]; its bounded main design mitigates but does not
  eliminate this, and improves held-out p95 E2E by 14.3–30.9 %.
- **Etalon also warns against P99 TBT alone**: "Solely examining tail latency disproportionately penalizes vLLM … while
  TPOT downplays the discrepancies…, tail-TBT overstates them" [P, arxiv_2407.07000 §3.1]; it proposes per-token
  deadline measures (fluidity index) instead.
- **H4 is supported, in qualified form.** The tail is rarely the quantity minimized (2 strict, 5 lenient, of 137), but a distributional
  SLO or attainment target appears in 42 % (32 of 77) of papers evaluated under online load.

## 7. What makes cross-paper numbers incomparable

These are ranked by how often they would change a comparison [Syn, DEFINITIONS.md counts]:

1. **TTFT start point.** Some papers time from arrival and others time prefill only (16 vs 15, with 19–20 unstated). A
   prefill-only TTFT omits the queueing that dominates under load. Benchmark harnesses time from arrival or send.
2. **How token pace is aggregated.** A per-request mean TPOT, a token-level TBT distribution and a per-request P99 of a
   request's own gaps are different random variables. "P99 TPOT" across requests is not P99 TBT across tokens.
3. **Goodput definition and SLO thresholds.**
   - Attainment level: X = 90 dominates the papers; MLPerf uses 99 %.
   - Joint vs single SLO.
   - Max rate vs measured rate at one load (vLLM).
   - SLO-based results fall steeply with the threshold. Aegaeon's advantage over MuxServe, in the number of models
     served at SLO, vanishes at an SLO scale of 0.2× [P].
4. **Throughput accounting.** Which tokens and phase are counted, and whether it is per GPU. Whether it was measured
   offline or read off a latency curve. "Throughput at the same TTFT" in CacheBlend, LMCache and Strata is a capacity
   at a target chosen per figure.
5. **Load regime.** 44 % of papers never evaluate under online arrivals. For speculative decoding and quantization the
   regime can reverse the sign of a result.
6. **Normalization.** Normalized latency divides by output length in vLLM and Orca, and by input + output in
   LoongServe. It mixes TTFT and TPOT.
7. **Energy scope.** GPU-only over a steady-state window (ML.ENERGY) vs node-level with a prefill/decode split
   (TokenPowerBench).
8. **Undefined metrics.** 40 of 143 full-text papers (28 %) use a headline metric they never define, or 50 (35 %) if
   loosely defined ones are included [P, DEFINITIONS.md §3].

## 8. Abstracts vs full texts (same papers)

[D, `scripts/analysis_v3.py`]
- **The test.** Discovery agents coded what the abstract says is optimized for every candidate, before any full-text
  read. We compared those codes with the final full-text objective codes on the same 133 papers.
  - Exact match of the objective code set: 16 of 133 (mean Jaccard 0.43).
  - At least one objective family in common: 124 of 133. Identical family set: 30 of 133.
  - So abstracts usually name one of the right *families*, but not the variant or the statistic.
- **Not tested.** The screening field asked only what is optimized, so it cannot show whether abstracts reveal
  constraints.
- **The abstract track shows the same vagueness.** About 20 of 55 abstract-only records say only "latency" or "speedup"
  without saying which.
- **Headlines name narrower quantities than their words suggest** (§0.5). SmoothQuant, SpecInfer, Sequoia,
  ServerlessLLM, vLLM, EAGLE-3, Strata ("3.75×" is throughput at equal TTFT) and Apt-Serve (formal objective = summed
  pending time).
- **Conclusion.** Coding from abstracts is good enough for "which family" but not for "which metric, which statistic,
  under which constraint". The full-text requirement was necessary.

## 9. Hypotheses: verdicts

| H | Verdict | Evidence |
|---|---|---|
| H1 shift to SLO-bound metrics | **Partly supported** | Corpus-wide SLO-framed share 18 → 28 → 46 %, about half composition from the pooled 2022–24 baseline (more from 2022–23). Within online-load papers it is flat (50 → 43 → 47 %, p = 0.95). Knee/latency-target capacity definitions fell significantly: 14/43 (33 %) before 2025 → 2/34 (6 %), p < 0.001; p = 0.005 excluding the 5 percentile-SLO capacity papers. The goodput-objective rise (25 → 23 → 41 %) is not significant (p = 0.14). Purposive sample. |
| H2 technique layer determines the metric | **Supported**, with load regime as the sharper divide | §4. 44 % of papers are never evaluated under online arrivals. Two layers are partly defined by their metric. |
| H3 definitions are inconsistent | **Strongly supported** | TTFT 16/15/19–20. At least 8 goodput definitions. Throughput tokens counted four ways plus "unstated". 28–35 % undefined headline metrics. Harnesses disagree on ITL and goodput. |
| H4 tails a minority | **Supported, qualified** | A percentile is minimized in 2 papers of 137 (5 counting a tail named as a design aim). A distributional SLO or attainment target appears in 42 % (32/77) of online-load papers, often attainment of per-request means. |
| H5 per-user and program metrics recent and a minority | **Partly** | Program latency is an objective in 10 papers, all agent/compound, 2023–26. Token-timeline QoE in 7 papers, including metric papers. TPS/user in 4 records. |

## 10. Threats to validity and what would change our mind

- **Purposive sample.** The §5 readings would be overturned by a random sample of 2022–26 OSDI/SOSP/NSDI/MLSys/EuroSys
  serving papers that showed no decline in knee-style capacity definitions within online-load papers.
- **LLM extraction.** On 30 blind re-extractions, the primary objective matched in 28 and the mean Jaccard was 0.74.
  Constraint sets matched exactly in only 14/30, so constraint shares are noisier. The R1 reviewer's spot check of 13
  records found the primary objective right in all 13, with about 11 % of individual entries wrong before the re-pass.
- **Objective vs reported is a judgment call.** Some papers have no single objective (Pope et al.'s Pareto frontier,
  RAGO's Pareto axes); these were coded as multiple objectives. Weak design quotes are flagged in each record's
  `repass_log`.
- **Statistic coding.** "Unspecified" is common: 30 of 62 serving-latency objective entries. So tier 3 merges "mean"
  with "unspecified". Tier coding is checked by one blind second coder (κ = 0.76), not more.
- **Venue and year.** Years come from the first arXiv version. Several venue strings came from discovery agents'
  memory and are not used in any count.
- **Coverage gaps.** The corpus lacks:
  - industrial blog-only systems (TensorRT-LLM, Dynamo, llm-d), which are only partly covered by INDUSTRY_DEFS;
  - 2025–26 compression papers read in full;
  - reasoning-era serving metrics (time to first answer token; whether reasoning tokens count in TPOT and throughput),
    beyond the two reasoning-serving papers read;
  - rejection/drop rate under admission control, which matters for goodput comparisons (Mooncake counts only completed
    requests; OLP admits by bid price).
- **No weighting.** Papers are counted equally, regardless of venue or citations.
- **"SLO-framed" definition.** It counts goodput/attainment objectives and latency constraints, not slo-goodput
  constraints (3 papers).

## Appendix pointers

- Per-paper table: `analysis/PAPER_TABLE.md` / `analysis/paper_table.csv` (202 rows); per-paper records: `records/`.
- Metric taxonomy: `notes/DEFINITIONS.md`. Industry definitions: `notes/INDUSTRY_DEFS.md`.
- Aggregates: `analysis/summary_v2.txt`, `analysis/summary_v3.txt` (reproduce with `scripts/aggregate.py`,
  `scripts/analysis_v3.py`).
- QA: `qa/QA_COMPARISON_v2.txt`, `qa/TAIL_AUDIT.md`, `qa/TIER_QA_COMPARISON.txt`.
