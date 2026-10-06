# DEFINITIONS — metric taxonomy derived from the survey (agent DEF, 2026-10-06)

**What this is.** The list of metrics that LLM inference-optimization papers use, and how each is defined, derived
from the per-paper records rather than assumed. Built from `analysis/definitions_by_metric.md` (every verbatim
definition the extractors copied), `records/*.json` (`metric_definitions`, `optimized_metrics`, `slo_spec`,
`extractor_notes`), `notes/E01.md`..`E15.md`, and spot checks in `fulltext/`.

**Population.** 143 full-text records (133 optimizers + 10 metric/benchmark papers). The 55 abstract-only records contain
no metric definitions, so every definition below is **[P]** (full text read). Where an abstract-only claim is used it is
tagged **[abstract only]**. **[Syn]** marks my own synthesis.

**Counts.** "n papers" = distinct full-text records assigned to a variant by me after reading the copied definition,
its extractor note and (for the quotes used here) the full text. Assignments are listed key-by-key in
`analysis/def_variants.py` (run `python3 -I analysis/def_variants.py .`); usage counts come from `analysis/def_usage.py`;
the regex screen for undefined metrics is `analysis/def_undefined.py`. A paper can fall into several variants of one
metric (often because it defines a term one way in §2 and measures it another way in §6). Records were being edited by
the tail-audit agent while this ran, so usage counts can drift by ±1 on a re-run.

**Quotes.** 181 quotes relied on here were checked against `fulltext/<key>.txt` by
`analysis/def_verify_quotes.py` (whitespace/hyphen-normalised, column-aware). 161 matched automatically. The other 20 were
found by manual `grep -a`: they were split across two-column lines or hyphen breaks, or had lost subscripts, e.g.
`EGPU + ECPU + EDRAM` in arxiv_2512.03024. Quotes not in that list are the extractors' verbatim copies from
`definitions_by_metric.md`. Section locators are the extractors' unless I re-checked them (Etalon §3.1/§5.2, Andes §3.1).

**Usage at a glance** (papers mentioning the code in any record field, from `def_usage.py`): TTFT 66, throughput (tokens
or requests) 97 (tokens 64, requests 47), E2E 53, TPOT or TBT 53 (TPOT 29, TBT 29, both 5), quality 47, memory 43, UTIL 38,
SLO attainment or goodput 42 (SLO_ATT 36, GOODPUT 22), single-sequence speed 33, cost 31, normalized latency 15,
program JCT 14, queueing 13, acceptance 12, energy 11, fairness 6, per-user rate 4, QoE 2 (+5 papers with QoE-like
OTHER codes).

---

## 0. Final metric list (one line each)

Notation [Syn]: for a request arriving at time *a* and emitting output tokens at times t_1..t_n (prompt length p):
TTFT = t_1 − a; gaps g_i = t_i − t_{i−1} (i = 2..n); TPOT = (t_n − t_1)/(n − 1) = mean g_i; E2E = t_n − a =
TTFT + (n − 1)·TPOT; normalized latency = E2E / n.

| # | Metric (canonical code) | Consensus operational definition (mine) [Syn] | Main unit |
|---|---|---|---|
| 1 | Time to first token (TTFT) | t_1 − a, measured at the client or server boundary from **arrival**, so it includes queueing, scheduling, any KV loading, and prefill | s |
| 2 | Time per output token (TPOT) | per-request mean decode gap (t_n − t_1)/(n − 1), excluding the first token; a distribution over **requests** | ms/token |
| 3 | Time between tokens (TBT; = ITL, inter-token latency) | each gap g_i is one sample; a distribution over **tokens** (or over each request's own gaps) | ms |
| 4 | End-to-end latency (E2E; also TTLT, request JCT, completion time) | t_n − a per request, including queueing | s |
| 5 | Normalized latency | E2E / n (output tokens), aggregated over requests (mean or median) | s/token |
| 6 | Single-sequence decode speed (TOKEN_LAT) | per-token time (or tokens/s, or speedup) of one sequence at batch 1 or a fixed small batch, with no arrival process | ms/token, tok/s, × |
| 7 | Per-user token rate (TPS/user, interactivity) | 1/TPOT, or 1/TBT per stream | tok/s/user |
| 8 | Token throughput (THR_TOK) | tokens completed per unit wall time by the system; must state input+output vs output, phase, and per-GPU vs total | tok/s (/GPU) |
| 9 | Request throughput / capacity (THR_REQ) | completed requests per unit time; "capacity" = the highest offered rate the system sustains under a stated latency condition | req/s |
| 10 | Goodput | throughput that counts only SLO-satisfying work; usual form: max request rate at which ≥ X % of requests meet all SLOs | req/s (/GPU) or tok/s |
| 11 | SLO attainment | fraction of requests (or tokens) that meet their latency SLO(s) | % |
| 12 | Queueing / scheduling delay | arrival → first scheduled (or summed waiting across calls) | s |
| 13 | Program / workflow JCT | submission → final output of a multi-call program (agent, DAG, RAG pipeline) | s |
| 14 | Token-timeline QoE family (QoE, fluidity, smooth goodput, deadline attainment) | how well the token-delivery timeline tracks a per-token deadline schedule, e.g. TTFT target + i/reading speed | [0,1], tok/s |
| 15 | Cost | resources or money per unit of served work: GPU count, $/h, GPU-seconds, $/token, throughput per $ | $, GPUs |
| 16 | Energy / power | J per token or per response, Wh per experiment, W; must state measurement scope (GPU vs node) | J, Wh, W |
| 17 | Memory | KV / weight / peak footprint, fragmentation or waste, or the batch size / context length it allows | GB, %, tokens |
| 18 | Quality | task accuracy, perplexity, F1/ROUGE; usually a constraint ("lossless", "≤ x drop") | task units |
| 19 | Fairness | spread of service (weighted tokens) or latency across clients: service difference, Jain's index, max wait | tokens, ratio, s |
| 20 | Utilization | MFU, achieved FLOP/s or bandwidth as a fraction of peak, KV-block occupancy, offered/max load | % |
| 21 | Speculative acceptance (ACCEPT) | acceptance rate α, or mean accepted tokens per verification step τ | ratio, tokens/step |
| 22 | Mechanism proxies (OTHER) | cache/token hit rate, preemption or stall counts, model-startup latency, pipeline bubbles, Kendall's τ of the schedule | various |

The data adds four items to the expected list (TTFT, TPS, TBT, TTLT, TPS/user, goodput): **single-sequence decode speed**
as its own family (33 papers; speculative, quantization and offloading papers almost never report a serving-load
latency); **program/workflow JCT** (14); the **token-timeline QoE family** (7 papers, all 2023–25); and **mechanism
proxies** that some papers optimize directly, such as Marconi's token hit rate and FLOP efficiency (arxiv_2411.19379) and
ServerlessLLM's model startup latency (arxiv_2401.14351).

---

## 1. Per-metric definitions and variants

### 1.1 TTFT — time to first token
Used by 66 papers. 55 have a definition entry, of which 36 say something about where TTFT starts or what it includes.

**(a) Consensus [Syn].** TTFT = time from request arrival at the serving system (or the gateway, for routers) to the
emission of the first output token. Under load it includes queueing and scheduling delay, any KV-cache fetch, and
prefill. Etalon's definition [P] states this: "Time To First Token (TTFT) [32, 7] is the latency between the request
arrival and the first output token generated by the system for the request. It includes the scheduling delay (time
elapsed from request arrival to start of prompt processing) and the prompt processing time." (arxiv_2407.07000, §2.2)

**(b, c) Variants.**

| Variant | n | Papers (keys) | Verbatim example [P] |
|---|---|---|---|
| T1 Starts at arrival or submission; queueing stated as included | 16 | 2402.01869 InferCept, 2403.02310 Sarathi-Serve, 2407.00079 Mooncake, 2407.07000 Etalon, 2504.19867 semi-PD, 2507.17769 PolyServe, 2508.01989 TaiChi, 2512.04013 AugServe, mlsys2025_sola, 2502.05370 FineMoE, 2503.14649 RAGO, 2510.18672 RLLM-serving, 2406.03243 Llumnix, 2602.16603 FlowPrefill, 2310.07240 CacheGen, 2412.17246 BlitzScale | "For a given request, TTFT measures the latency of generating the first output token from the moment a request arrives in the system." (2403.02310, §2.4); "TTFT reflects the queuing delay before the first token is generated." (2512.04013, §6.1) |
| T2 TTFT *defined as* the prefill phase's duration | 15 | 2310.07240, 2311.01282, 2401.09670 DistServe, 2403.19708, 2405.16444 CacheBlend, 2410.01228 ConServe, 2411.01783, 2504.07494 Apt-Serve, 2506.02634, 2510.09665 LMCache, 2512.18194 TraCT, 2510.18672, 2406.01566 Helix, 2405.06856 Aladdin, 2410.18038 POD | "the time to first token (TTFT), which is the duration of the prefill phase" (2401.09670, §1); "time-to-first-token (TTFT), which is the prefill delay" (2510.09665, §8) |
| T2a …but measured under load, so queueing is in fact included (extractor-flagged) | 5 | 2401.09670, 2504.07494, 2510.09665, 2512.18194, 2410.18038 | DistServe's latency model includes queueing (§2.2, extractor note), and TraCT's Fig 10 breakdown has a scheduler-queue component |
| T3 Measured offline or for one request, so queueing is zero by construction | 7 | 2311.04934 Prompt Cache, 2411.00136 LLM-Inference-Bench, 2411.01783, 2502.14866 LServe, 2311.01282, 2310.07240, 2411.15100 XGrammar | "We measure TTFT by setting the maximum output to one token and recording the time to generate this output." (2411.00136, §III.5(b)) |
| T5 Includes loading or transferring KV from another tier or node | 4 | 2310.07240, 2405.16444, 2407.00079, 2508.18572 Strata | "This includes the loading delay of the KV cache and the prefill delay of the new questions." (2310.07240, §7.1); Mooncake Alg. 1: TTFT = T_transfer + T_queue + T_prefill (extractor) |
| T6 Covers a whole pre-generation pipeline (RAG, reasoning, tools) | 3 | 2503.14649 RAGO, 2504.08784 SLOs-Serve, 2510.18672 | "[TTFT] Time-to-First-Token ↦ average latency from request reception to the generation of the first output token." (2503.14649, §4), where reception precedes query rewrite, retrieval and rerank |
| T6' Time to first *visible* token (hidden reasoning included) | 1 | 2510.18672 | "Time to First Visible Token (TTFVT): The time from receiving a request until the first token is actually displayed to the user." (§E.2) |
| T7 Includes the wait for model scale-up or model switching | 2 | 2412.17246, sosp2025_aegaeon | "the latency includes the queueing delays waiting for the scaled instance to be ready for inference" (2412.17246, §3.1) |
| T8 Queueing kept as a separate metric | 1 | 2506.02634 | "queued TTFT (QTTFT) …, i.e., the TTFT plus the time when waiting for GPU to process the request." (§4.2) |
| T9 Normalized by prompt length | 1 | 2404.09526 LoongServe | "normalized input latency, i.e., the mean of prefill phase time divided by the input lengths" (§7.1) |
| — No statement of start point or scope | 19 | e.g. 2311.18677 Splitwise ("How quickly user sees initial response"), 2405.05465 Vidur, 2501.01005 FlashInfer, 2606.00946 Lodestar, sosp2025_aegaeon | Lodestar's TTFT "is never given a formal definition" (extractor), yet it is the router's reward |

Statistic of TTFT where it is optimized (pre-tail-audit, `def_usage`/`summary_v2`): 16 papers use the mean as the
objective. As a constraint, 9 use an attainment fraction, 5 P99 and 2 P90. Vidur explains a looser TTFT percentile:
"We use a more relaxed constraint of P90 for TTFT since it is a one time delay experienced by the user, as opposed to TBT
which is recurrent for each output token." (arxiv_2405.05465, §7.3)

**(d) Pitfalls.**
- **"TTFT = prefill time" vs arrival-based TTFT.** 15 papers define TTFT as the prefill duration and 16 as arrival-based.
  5 of the prefill-defined papers then report it under queueing load. A TTFT gain from a prefill kernel (T3) and one from
  scheduling (T1) are different quantities; only T1 contains the queueing a router or scheduler controls. [Syn]
- **What sits before prefill varies.** KV fetch (4 papers), RAG retrieval, reasoning or tool stages (3), and model
  scale-up (2) are inside TTFT in some papers and absent in others. RAGO's TTFT is a pipeline latency, not an LLM-engine
  latency.
- **TTFT ≈ E2E for short outputs.** Preble drops TTFT/TPOT as key metrics because "our target LLM use has short output
  lengths, rendering TPOT not as meaningful and TTFT close to the request latency." (arxiv_2407.00023, §4.1). TraCT fixes
  output length at 3 tokens (extractor), so its "P99 latency" in the abstract is P99 TTFT.
- **Prompt-length dependence.** TTFT grows with prompt length, so 8 papers make the TTFT SLO a function of prompt length
  (§1.11). Etalon warns that dividing TTFT by prompt length "normalizes the scheduling delay as well and would penalize
  shorter input requests disproportionately" (arxiv_2407.07000, §3.1).
- **Undefined in many headline uses.** TTFT is a headline or primary metric without any definition in 15 papers, and with
  queueing scope unstated in 6 more (§3).

### 1.2–1.3 TPOT and TBT/ITL — token pace (treated together because the papers mix them)
TPOT is used by 29 papers and TBT by 29, 53 distinct. Only 5 use both codes. 43 papers say how they compute token pace.

**(a) Consensus [Syn].**
- **TPOT** is a per-request scalar: (t_n − t_1)/(n − 1). It excludes the first token, has one value per request, and its
  percentiles are taken over requests. DistServe: "the time per output token (TPOT), which represents the average time
  taken to generate a token for each request (except for the first token)" (arxiv_2401.09670, §1).
- **TBT (= ITL)** is per token: every gap g_i is a sample, and percentiles are taken over all tokens or over each
  request's own gaps. Sarathi-Serve: "TBT on the other hand measures the interval between the generation of consecutive
  output tokens of a request, and affects the overall perceived fluidity of the response." (arxiv_2403.02310, §2.4).
- ConServe states the relation: "Note that TBT is measured per token and is stricter than time per output token (TPOT),
  which averages the TBT across all tokens per request." (arxiv_2410.01228, §2 fn 1)

**(b, c) Variants.**

| Variant | n | Papers (keys) | Verbatim example [P] |
|---|---|---|---|
| P1 TPOT = per-request mean over decode tokens | 13 | 2401.09670 DistServe, 2405.06856 Aladdin (as "ATGT"), 2407.07000 Etalon, 2410.14257, 2504.19867 semi-PD, mlsys2025_sola, 2406.03243 Llumnix ("decode latency"), 2508.01989 TaiChi, 2404.09526 LoongServe ("normalized output latency"), 2501.12162 AdaServe, 2401.14351, 2411.15100, 2505.06371 | "ATGT = t_decode / (l_out − 1)" (2405.06856, §3); "It is calculated as the total decode time of a request normalized by the number of decode tokens generated." (2407.07000, §2.2) |
| P2 Called TBT or ITL ("inter-token") but defined as an **average** | 5 | 2311.18677 Splitwise, 2408.13510 Intelligent Router, 2510.09665 LMCache, 2510.18672, 2411.00136 | Splitwise Table II: "Time between tokens (TBT): Average token streaming latency", yet its SLOs are on P50/P90/P99 TBT; "inter-token-latency (ITL), which is the average delay between the generation of two consecutive output tokens" (2510.09665, §8) |
| P2' ITL as a batch aggregate | 1 | 2411.00136 | "ITL = (End-to-End Latency − TTFT) / (Batch Size × (Output Tokens − 1))" (§III.5(c)): this divides by batch size, so it is not a per-stream interval |
| P3 TBT as a token-level distribution | 16 | 2403.02310, 2410.01228, 2407.00079, 2407.07000, 2410.18038, 2401.08671, 2312.12456, 2408.00741, 2501.14808, 2508.16449, 2405.05465, 2505.09999, 2504.02263, 2507.17769, sosp2025_aegaeon, 2501.01005 | 2403.02310 quote above |
| P3b Percentile of a request's **own** gaps, then pass/fail per request | 1 | 2504.07494 Apt-Serve | "P99 TBT refers to the 99th percentile of TBT latency for each individual request" (§3.1 fn 1) |
| P4 Per-step (iteration) execution time used as TBT/TPOT | 5 | 2410.01228, 2504.02263 MegaScale-Infer, 2506.12708 CloudMatrix384 (fixed-batch decode TPOT, with MTP), 2507.19427 Step-3, 2409.17264 Medha | "time between tokens (TBT), which is the execution time of each step in the decode phase" (2410.01228, §2); "Performance target: 50ms time per output token (TPOT, ≥ 20 tokens/sec)" (2507.19427, §3.1) |
| P5 Cumulative **deadline** form | 6 | 2507.17769 PolyServe, 2407.07000 Etalon, 2410.14257, 2504.20068 JITServe, sosp2025_aegaeon, 2501.12162 AdaServe | "the i-th token must be produced before TTFT + i · TPOT" (2507.17769, §2); "token i counts toward goodput if it finishes by TTFT_SLO + i x TBT_SLO" (2504.20068, §3) |
| P6 Maximum or worst case over tokens or windows | 2 | 2504.08784 SLOs-Serve, 2503.14649 RAGO | "we measure the TPOT every 10 tokens" and take the max (2504.08784, §6); "we report the worst-case TPOT latency" (2503.14649, §4) |
| P7 "TPOT" = whole request latency ÷ output tokens | 1 | 2404.14527 Melange | "TPOT is determined by dividing request latency by the number of generated tokens." (§4.1): this is normalized latency (§1.5) and includes prefill and queueing |
| P8 TPOT and TBT used as synonyms | 3 | 2409.17264 Medha, 2503.24000 ("TBOT"), 2507.17769 | "Time-Per-Output-Token (TPOT) or Time-Between-Tokens (TBT) [4]" (2409.17264, §2.1) |
| P9 Distinction made explicit | 3 | 2410.01228, 2504.19867, 2407.07000 | "Some works [19] use Time-between-Tokens (TBT) to measure the latency between successive tokens. In this work, we use the TPOT metric." (2504.19867, §2.2) |

**Opposite normative stances.**
- Aladdin rejects TBT: "the TBT metric is an over-strict metric with less flexibility, and it does not directly affect the
  user's quality of experience" (arxiv_2405.06856, §3).
- Andes rejects mean and tail TPOT: "average/P90/P99 time-per-output-token (TPOT) can miss outlier TPOT inflations that
  lead to user-perceived pauses in text streaming" (arxiv_2404.16283, §3.1).
- PolyServe takes the middle: "While some works target average TPOT, … adhering to maximum TPOT can be too restrictive"
  (arxiv_2507.17769, §2), and adopts the deadline form P5.
- Etalon shows the choice changes conclusions: "the tail TBT-based throughput for vLLM is 3× worse than Sarathi due to huge
  generation stalls, while the TPOT based throughput shows these systems at par." (arxiv_2407.07000, §5.2)
- The smooth-goodput paper shows that a chained per-token TBT SLO can be gamed: "manually delaying the delivery of some
  tokens can improve SLOs" (arxiv_2410.14257, abstract). It also notes that a TPOT deadline constrains only "the first and
  last tokens" (§3.1).

**Other names for token pace:** ITL (5 papers; FlashInfer expands it both as "Inter-Token-Latency" and "Inference Time
Latency", arxiv_2501.01005), TBOT (arxiv_2503.24000), TTIT "time-to-incremental-token" (arxiv_2411.01783), TTL
"token-to-token latency" (arxiv_2507.07120), ATGT (arxiv_2405.06856), "decode latency" (arxiv_2406.03243,
arxiv_2406.01566), "normalized output latency" (arxiv_2404.09526), "tail time per token (TPT)" (arxiv_2411.19379,
motivation only).

**(d) Pitfalls.**
- **Mean over tokens hides stalls.** P99 TPOT across requests and P99 TBT across tokens are different numbers. A single
  10 s stall shifts one request's TPOT a little but is one extreme TBT sample. Etalon: "Both these metrics normalise the
  latency by the number of decode tokens in the request. This normalization can mask the jitters that occur as
  intermittent stalls" (arxiv_2407.07000, §3.1). A paper's label does not tell you which it computed: 5 papers call an
  average "TBT"/"ITL". [Syn]
- **System view vs client view.** Per-step execution time (P4) equals the observed gap only when the request is in every
  iteration. It misses gaps caused by preemption or by queueing between decode steps. semi-PD's TPOT model explicitly
  excludes decode-side waiting (extractor note on arxiv_2504.19867).
- **Speculative decoding breaks per-token gaps.** Several tokens arrive at once, so SLOs-Serve measures TPOT "every 10
  tokens" and AdaServe writes the SLO as a cumulative constraint (arxiv_2501.12162, Eq. 2).
- **Batch-1 "TBT" is a different metric.** Sequoia's "TBT refers to time between tokens" (arxiv_2402.12374, Table 1) is the
  mean ms/token of a single sequence at batch 1, not a serving-load gap distribution (§2).
- **Off-by-one and first-token inclusion** differ: P1 excludes the first token, Melange's "TPOT" includes prefill and
  queueing, and DistServe's footnote composes E2E as "TTFT plus TPOT times the number of generated tokens in the decoding phase" (§1 fn 1), i.e. the same identity.

### 1.4 E2E — end-to-end request latency (TTLT, request JCT, completion time)
Used by 53 papers; 32 have a definition entry and are assigned below.

**(a) Consensus [Syn].** Per request, arrival → last output token (time to last token), including queueing. Preble lists
the parts: "average end-to-end request latency (including scheduling time, queueing time, prefill, and decoding time)"
(arxiv_2407.00023, §4.1). JITServe says "E2EL like time-to-last-token" (arxiv_2504.20068, abstract).

**(b, c) Variants.**

| Variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| E1 Per request from arrival or submission, queueing stated | 8 | 2302.11665 AlpaServe, 2311.15566 SpotServe, 2407.00023 Preble, 2505.13326 SART, 2510.18672, 2412.17246, 2410.14257, 2404.08509 SSJF | "request latency (which includes the GPU execution time and queuing delay)" (2302.11665, §3.1); "the end-to-end latency of a request includes queuing latency … and inference latency" (2505.13326, §2) |
| E2 Per request, start point not stated | 7 | 2502.07903, 2504.07347, 2311.18677, 2504.20068, 2503.18292, 2401.11181, 2406.14066 | "Inference latency is the time required to complete each inference request from start to finish." (2502.07903, §2) |
| E3 Queueing excluded | 3 | 2512.15705 DREX, 2505.13326 (as a second metric), 2405.05465 (static workloads) | "RCT: Time between when a request is scheduled to when it is complete." (2512.15705, Table 4) |
| E4 Wall-clock of a fixed offline batch (no arrivals) | 8 | 2207.00032 DeepSpeed-Inference, 2211.05102, 2306.14048 H2O, 2303.06865 FlexGen, 2406.19707 InfiniGen, 2402.05099 Hydragen, 2505.11329 TokenWeave, 2603.16104 Helium | "the latency t is defined as the total number of seconds spent to process the prompts and generate all the bn tokens" (2303.06865, §3) |
| E5 Single request at batch 1 | 2 | 2503.24000, 2406.00059 Conveyor | "with a fixed batch size of one" (2503.24000, §4.3) |
| E6 "End-to-end latency" used for something that is not a request's latency | 4 | 2211.10438 SmoothQuant, 2310.19102 Atom, 2305.09781 SpecInfer, 2406.10774 Quest | "We measure the end-to-end latency of generating all hidden states for a batch of 4 sentences in one pass, i.e., the context stage latency." (2211.10438, §5.3); "We measure the latency as the average decoding time of each token, without considering the queuing time." (2310.19102, §5.3) |
| E7 Reported only as a speedup ratio | 3 | 2503.05096 AdaSpec, 2406.14066 TurboSpec, 2406.00059 | Conveyor's improvement is old/new − 1, so a "376.4%" improvement is a 4.76× ratio (extractor note) |

**(d) Pitfalls.**
- Of the 32 papers, 8 (E4) measure the time a whole offline batch takes and 4 (E6) attach the E2E label to a single
  prefill pass or to per-token time. Nothing in the term distinguishes these from per-request serving latency. [Syn]
- With queueing included, E2E is driven mostly by load and output length. Lodestar rejects E2E and TPOT as router rewards
  because they are "observed … much further in the future than the routing decision time" and "affected by one more
  unknown factor, the number of decode tokens" (arxiv_2606.00946, §4.1).
- Speedup-only reporting (E7, and most of §1.6) cannot be put on an absolute latency axis.

### 1.5 Normalized latency (s/token)
15 papers, all with a definition entry. 19 distinct papers including the program-level forms.

**(a) Consensus [Syn].** Per request, E2E divided by the number of output tokens, then averaged over requests (mean, or
median for Orca). It is used as the latency axis of a throughput–latency curve. vLLM: "the mean of every request's
end-to-end latency divided by its output length, as in Orca [60]" (arxiv_2309.06180, §6.1).

**(b, c) Variants.**

| Variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| N1 Mean over requests of E2E / output tokens | 9 | 2309.06180 vLLM, 2305.05920 FastServe, 2312.05516 Pensieve (§6.2), 2408.12757 NanoFlow, 2411.01142 NEO, 2408.15792 LTR, 2512.04013 AugServe, 2405.19888 Parrot, 2404.14527 Melange (as "TPOT") | "average per-token latency is calculated as the mean of every job's end-to-end latency divided by its output length" (2305.05920, §6.1) |
| N2 Median over requests | 5 | osdi2022_orca, 2402.01869 InferCept, 2403.01876 DejaVu, 2405.05465 Vidur, 2407.07000 Etalon | "we report median latency normalized by the number of generated tokens of each request" (osdi2022_orca, §6.2) |
| N3 P90 over requests | 2 | 2312.05516 (§6.1), 2408.15792 | Pensieve contradicts itself: "90-percentile normalized latency" (§6.1) vs "the mean of each request's end-to-end latency divided by its output length" (§6.2) |
| N4 Token-weighted ratio of sums | 1 | osdi2024_dlora | "the average latency is calculated by dividing the sum of each request's end-to-end latency by the total number of output tokens" (§7.1) |
| N5 Denominator = input + output length | 1 | 2404.09526 LoongServe | "the mean of requests' end-to-end latency divided by their sequence lengths" (§7.1) |
| N6 Denominator = decode tokens | 1 | 2407.07000 | "total execution time of a request normalized by the number of decode tokens" (§2.2) |
| N7 Tool/interception time removed | 1 | 2402.01869 | "We also remove a request's intercepted time from its end-to-end latency" (§6.1) |
| N8 Program-level token latency | 3 | 2502.13965 Autellix, 2508.06948 Kairos, 2412.20993 Certaindex (as a fairness proxy) | "program-level token latency, defined as the total program response time divided by the number of tokens generated" (2502.13965, §6) |

The same quantity has at least seven names: "normalized latency", "average per-token latency" (FastServe), "per-token
latency" (LTR, NEO), "average latency" (dLoRA), "normalized end-to-end latency" (Vidur), "normalized per-token latency"
(LoongServe), and "TPOT" (Melange).

**(d) Pitfalls.**
- Normalized latency mixes TTFT and TPOT in proportions set by output length: E2E/n = TTFT/n + TPOT·(n−1)/n [Syn]. Etalon
  shows what this hides: vLLM scheduling delay "is above 25s for almost 60% of the requests … However, the normalized
  latency for these systems differs only be a few hundred milliseconds!" (arxiv_2407.07000, §3.1).
- Mean vs median vs P90 vs token-weighted ratio (N1–N4) give different numbers for the same run. The token-weighted form
  is dominated by long requests. [Syn]
- Called "per-token latency", it collides with single-sequence decode latency (§1.6) and with TPOT (§2).

### 1.6 Single-sequence decode speed (TOKEN_LAT)
33 papers, mostly speculative decoding, quantization, sparsity and offloading. 28 are assigned to variants.

**(a) Consensus [Syn].** Per-token latency (or tokens/s, or speedup over autoregressive decoding) of one sequence, or of
a fixed small batch, with no arrival process. It is a kernel or algorithm speed, not a serving latency.

| Variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| S1 ms/token at batch 1 | 8 | 2210.17323 GPTQ, 2310.17157 Deja Vu, 2312.11514, 2309.17453 StreamingLLM, 2406.10774 Quest, 2402.12374 Sequoia, 2411.01783, 2507.07120 Helix | "Average per-token latency (batch size 1) when generating sequences of length 128." (2210.17323, Table 6) |
| S2 tokens/s of one sequence, often called "throughput" | 7 | 2306.00978 AWQ, 2312.12456 PowerInfer, 2312.17238, 2402.02057 Lookahead, 2404.16710 LayerSkip, 2311.01282, 2502.04563 WaferLLM | "We measure the throughput of single batch inference" (2402.02057, §5) |
| S3 Wall-clock speedup vs autoregressive | 8 | 2211.17192, 2401.10774 Medusa, 2401.15077 EAGLE, 2503.01840 EAGLE-3, 2404.16710, 2402.12374, 2406.14066, 2503.05096 | "Speedup = Acceleration rate / Overhead" (2401.10774, App. B.1) |
| S4 Per-step latency at a fixed batch > 1 | 7 | 2408.11049 MagicDec, 2404.14469 SnapKV, 2502.14866, 2207.00032, 2305.09781 SpecInfer, 2310.19102, 2211.10438 | "Decoding latency comparison … on various batch sizes … decoding latency (ms/token)" (2404.14469, Fig 7) |

**(d) Pitfalls.**
- Gains shrink with batch size. EAGLE-3's headline 6.5× is at batch 1, and its throughput gain is 1.38× at batch 64 (E10
  note, arxiv_2503.01840). EAGLE says "EAGLE primarily focuses on latency rather than throughput" (arxiv_2401.15077,
  §4.4) while its abstract claims "doubled throughput".
- At a fixed batch, a per-token speedup is also a throughput speedup. MagicDec relies on this (extractor note on
  arxiv_2408.11049). Under a serving load the two separate.
- Baselines differ: Hugging Face FP16 (AWQ, Medusa), a recompute baseline (StreamingLLM's 22.2×), or more GPUs (GPTQ's
  speedup folds in a 5→1 GPU reduction; E08 note).
- About 20 abstract-only records say only "latency" or "speedup" [abstract only] (RESEARCH_LOG, A01).

### 1.7 Per-user token rate (TPS/user, interactivity)
4 papers carry the code; 6 define or use a per-stream rate (U1 5 + U3 1), and 2 more use "TPS" for system tokens/s (U2). (Corrected after report review r2.)

**(a) Consensus [Syn].** Tokens/s delivered to one stream = 1/TPOT, or 1/TBT. It is the interactivity axis of the
throughput–interactivity frontier.

| Variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| U1 Per-request rate defined as the reciprocal of TPOT or TTL | 5 | 2401.08671 FastGen (EMA rate SLA), 2502.04563 WaferLLM, 2507.07120 Helix, 2507.19427 Step-3, 2404.16283 Andes (token delivery speed) | "TPR is derived from the more widely used Time per Output Token (TPOT), with TPR = 1/TPOT." (2502.04563, §7); "user interactivity is measured as reciprocal of decoding TTL" (2507.07120, §3) |
| U2 "TPS" meaning **system** tokens/s | 2 | 2510.18672, 2501.14808 | "Tokens per second (TPS) of system represents the mean of total output tokens number per second" (2510.18672, §2) |
| U3 "TPS" meaning the per-request rate | 1 | 2502.05370 FineMoE | "Tokens-Per-Second (TPS) or Time-Per-Output-Token (TPOT) is used to measure the generation rate" (§2.1) |

**(d) Pitfalls.** "TPS" means system throughput in some papers and a per-user rate in others. Step-3 uses "50 ms TPOT"
and a "20 tokens/s decoding SLA" as the same constraint (arxiv_2507.19427, §3.1, §7.3). FastGen's rate is an exponential
moving average, not the reciprocal of a percentile (E02 note).

### 1.8 Token throughput (THR_TOK)
64 papers; 40 are assigned to variants.

**(a) Consensus [Syn].** Tokens processed per second of wall time over a stated interval. A usable statement fixes four
things: (i) which tokens count (input+output, output only, one phase only); (ii) the time base (whole run including
prefill, or decode iterations only); (iii) the normaliser (total system, per GPU, per $); (iv) the regime (offline batch
at max size, open-loop rate sweep, or a latency-constrained operating point). No single convention dominates, so there
is no consensus on (i)–(iv). The most explicit definition, NanoFlow's, counts "the number of tokens processed per second
by both prefill and decode phases" and reports it per GPU (arxiv_2408.12757, §3.1, §3.5).

| Variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| K1 Input + output tokens | 7 | 2401.00588 VTC, 2408.12757 NanoFlow, 2410.01228 ConServe, 2411.00136, 2411.01142 NEO, 2404.09526 LoongServe, 2404.14527 Melange (tokens per $) | "Throughput is the total number of tokens (including input and output tokens) processed divided by the total execution time." (2401.00588, App.) |
| K2 Output tokens over prefill + decode time | 13 | 2303.06865 FlexGen, 2306.14048 H2O, 2411.11217 MoE-Lightning, 2502.04563, 2310.19102 Atom, 2502.07903 HexGen-2, 2406.01566 Helix, 2508.18572 Strata, 2510.18672, 2512.15705, 2507.07120, 2402.05099 Hydragen, 2405.04532 QServe | "The generation throughput is defined as bn/t." (2303.06865, §3); "the number of tokens generated divided by total generation time (i.e., prefill time + decode time)" (2411.11217, §5) |
| K3 Decode phase only (prefill time excluded) | 8 | 2303.06865 (2nd metric), 2410.21465 ShadowKV, 2504.02263 MegaScale-Infer, 2506.12708 CloudMatrix384 (fixed-batch decode TPOT, with MTP), 2507.19427 Step-3, 2405.04437 vAttention, 2308.16369 Sarathi, 2211.05102 | "tokens generated per second, excluding the first output token, divided by the number of GPUs" (2504.02263, §7.1); Sarathi computes it "by dividing the time to process one decode iteration by the batch size" (2308.16369, §5.1.1) |
| K4 Prefill or input tokens only | 8 | 2403.19708 CachedAttention, 2311.18677, 2405.04437, 2407.05858 llm.npu, 2506.12708, 2503.24000, 2404.09526, 2211.05102 | "Prefilling throughput is the metric to evaluate the speed of processing the prompt." (2403.19708, §5.2), and its 7.8× headline is this metric |
| K5 Token accounting not stated | 8 | 2402.02750 KIVI, 2403.00579 NeuPIMs, 2503.01840 EAGLE-3, 2505.11329 TokenWeave, 2401.15077 EAGLE, 2308.16369, 2501.14808 HyGen, 2207.00032 | KIVI: throughput "never formally defined; units not stated" (extractor) |
| G1 Normalised per GPU or accelerator | 5 | 2408.12757, 2504.02263, 2506.12708 (also per TFLOPS), 2507.19427 ("TGS: Tokens/GPU/s"), 2507.07120 | "Throughput per GPU is quantified as the total number of tokens generated per second per GPU" (2507.07120, §3) |
| G2 Whole system, cluster or node, stated | 6 | 2406.01566, 2502.07903, 2402.05099 (8-GPU TP group), 2411.00136, 2512.15705, 2401.00588 | — |
| R1 Offline, batch raised to the memory limit | 5 | 2402.02750, 2405.04532, 2401.15077, 2410.21465, 2306.06000 S3 | "We increase the batch size until out of memory and report the peak memory usage and throughput" (2402.02750, §4.3) |
| R3 Fixed batch tuned to a per-token latency target | 5 | 2506.12708, 2507.19427, 2310.19102, 2504.02263, 2404.14527 | "We assess absolute decode throughput (tokens/s) targeting a time-per-output-token (TPOT) SLO of below 50 ms" (2506.12708, §5.2) |
| R4 Analytical bound or stability region, not measured | 3 | 2408.12757 ("optimal throughput"), 2410.21465 ("infinite batch size"), 2504.07347 | "A scheduling algorithm is said to achieve throughput λ if the associated DTMC … is irreducible and positive recurrent when the arrival rate is λ" (2504.07347, §3.2) |

**(d) Pitfalls.**
- Input+output vs output-only differs by the factor (p+d)/d (prompt and decode lengths). NanoFlow gives the conversions:
  "decoding throughput … is d/(p+d) × Throughput_total, and request per second is 1/(p+d) × Throughput_total"
  (arxiv_2408.12757, §3.1). For prompt-heavy workloads the gap is large. [Syn: same identity]
- Prefill throughput reported as "throughput": CachedAttention's 7.8× is prefill-only.
- Per-GPU vs total, and per GPU vs per NPU die. Step-3 divides by all attention and FFN GPUs, and its 4,039 is a peak
  minute against a 3,910 long-term average (E13 note).
- Offline max-batch throughput (R1) is a memory-capacity result. It says nothing about the throughput reachable under a
  latency target. CloudMatrix384 shows how much that matters: 1,943 / 974 / 538 tokens/s per NPU at 50 / 30 / 15 ms TPOT
  (arxiv_2506.12708, Table 4).
- Fixed-length synthetic inputs hide output-length changes. arxiv_2503.24000 shows KV compression can lengthen responses
  and introduces "response length difference" D = (L_un − L_cs)/L_un (§4.3).

### 1.9 Request throughput and capacity (THR_REQ)
47 papers; 34 assigned.

**(a) Consensus [Syn].** Completed requests (or programs) per second. Most papers report **capacity**: the highest
offered request rate the system sustains under a stated condition. That condition is what defines the metric, and it
varies (Q4, Q5, and goodput in §1.10).

| Variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| Q1 Completed requests per s or per min, measured | 11 | 2311.03285 S-LoRA, 2402.01869, 2407.00047 QLM, 2401.08671 FastGen, 2503.18292 Jenga, 2512.18194, 2510.18672, 2408.15792, 2405.04437 (req/min), 2410.18038 (req/min), osdi2022_orca | "we also report the number of finished requests per second (i.e., throughput)" (2402.01869, §6.1) |
| Q2 Offline samples or sequences per s | 2 | 2306.06000 S3, 2305.13144 | "maximum throughput in sequences per second" (2306.06000, §4.1) |
| Q3 Programs or jobs per s | 4 | 2312.07104 SGLang, 2502.13965, 2412.20993, 2511.02230 | "comparing the number of program instances executed per second (programs per second, p/s)" (2312.07104, §6.1) |
| Q4 Max rate before the latency or queueing knee (no numeric SLO) | 5 | 2309.06180 vLLM, osdi2022_orca, 2405.04437, 2405.05465 Vidur, 2402.01869 | "Capacity of the system is defined as the maximum queries per second that it can support without the queuing delay blowing up. Specifically we constrain the P99 scheduling delay to be under 5 seconds." (2405.05465, §6) |
| Q5 Max rate under an explicit latency target, no attainment fraction | 14 | 2311.18677 Splitwise, 2407.07000, 2305.05920, 2404.09526, osdi2024_dlora, 2312.05516, 2405.16444 CacheBlend, 2510.09665 LMCache, 2407.00079, 2411.01142, 2409.17264, 2505.09999, 2403.02310 Sarathi-Serve, 2508.18572 | "Capacity … defined as the maximum request load (queries-per-second) a system can sustain while meeting certain latency targets." (2403.02310, §2.4); "2.3-14x higher query processing rate (i.e., throughput), at the same TTFT" (2510.09665, §8.1) |
| Q6 Queueing-stability throughput | 1 | 2504.07347 | see R4 above |

**(d) Pitfalls.**
- vLLM's and Orca's headline "throughput" is the rate at the knee of a mean or median normalized-latency curve (E01, E06
  notes). It is not a measured req/s, and the knee is read by eye.
- "Throughput at the same TTFT" (CacheBlend, LMCache, Strata) is a capacity at a latency target chosen per figure.
- Capacity condition: "P99 scheduling delay < 5 s" (Vidur), "median scheduling delay ≤ 2 s" plus P99 TBT (Sarathi-Serve),
  all 9 percentile SLOs (Splitwise), or "without incurring high queuing delays" (vAttention, §7.4). Capacities from
  different papers are not comparable.

### 1.10 Goodput
The term (or "effective throughput") is defined in 22 papers. 23 papers are assigned to variants, including FastServe's
"P95 goodput" and the deadline forms.

**(a) Consensus [Syn].** Throughput that counts only SLO-satisfying work. The modal form, and the one from DistServe, is
the **maximum request rate at which at least X % of requests meet all their latency SLOs**, with X = 90 in most papers,
optionally per GPU: "per-GPU goodput, defined as the maximum request rate that can be served adhering to the SLO
attainment goal (say, 90%) for each GPU provisioned" (arxiv_2401.09670, §1).

| Variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| GP1 Max request rate at X % attainment | 13 | 2401.09670 DistServe, mlsys2025_sola, 2508.01989 TaiChi, 2507.17769 PolyServe, sosp2025_aegaeon, 2602.16603 FlowPrefill, 2504.07494 Apt-Serve, 2504.08784 SLOs-Serve, 2504.19867 semi-PD, 2404.09526 LoongServe, 2305.05920 FastServe, 2302.11665 AlpaServe, 2412.20993 Certaindex | "goodput, defined as the maximum sustainable request rate under an SLO attainment goal (e.g., 90%)" (2602.16603, §1); "the throughput when 95% of jobs can be completed within the SLO" (2305.05920, §6.2) |
| …X used | — | 90 %: 11 of 13; 95 %: FastServe; 99 %: AlpaServe (also SOLA and DistServe as a second level); 70 %: Apt-Serve intro example | "goodput (i.e., the maximum input request rate) under 90% and 99% SLO attainment" (mlsys2025_sola, §6.1) |
| GP1a …per GPU | 2 | 2401.09670, 2504.08784 | "maximum request load per GPU while maintaining 90% SLO attainment" (2504.08784, §1) |
| GP1b …single SLO, not joint | 4 | 2602.16603 (TTFT only), sosp2025_aegaeon (per-token attainment), 2302.11665 (request latency), 2412.20993 (program deadline) | — |
| GP2 Measured rate or count of SLO-meeting requests | 5 | 2401.08671 FastGen, 2512.04013 AugServe, 2504.20068 JITServe (request-level), 2412.17246, 2410.14257 (text) | "Requests that adhere to these SLAs are deemed successful, and the throughput of these successful requests is referred to as effective throughput." (2401.08671, §4.1.2) |
| GP3 SLO-meeting **tokens** per s | 3 | 2501.12162 AdaServe, 2410.14257 (Eq. 7), 2504.20068 (token-level; deadline variant counts input+output) | "Goodput is measured as the number of tokens generated per second for requests that successfully attain their SLO." (2501.12162, §6.1) |
| GP4 **Fraction** of requests meeting deadlines (not a rate) | 1 | 2409.17264 Medha | "maximize goodput – the fraction of requests meeting their deadlines" (§4.1) |
| GP5 **No SLO**: accepted tokens per s | 1 | 2406.14066 TurboSpec | "Goodput = Number of Generated Tokens / Execution Time" with only validated and bonus tokens counted; "in the absence of speculative decoding, the goodput and throughput are the same" (§4.1.1, §1) |
| GP6 Only fully completed in-SLO requests count | 1 | 2407.00079 Mooncake | "only requests that fully complete their execution are counted in the measure of goodput. Otherwise, all previously consumed/generated tokens are not counted" (§2) |
| GP7 Applications completed before their deadline | 1 | 2506.14851 | "maximize the goodput (number of applications that complete before the deadline)" (§2) |
| GP8 Smooth goodput (benefit minus an idle-latency penalty) | 1 | 2410.14257 | "The smooth goodput is defined as the service benefit per unit of time … benefit(r) = n_r − α · f(l_r)" (§4.3) |

**(d) Pitfalls.**
- **Unit.** req/s (GP1, GP2), tokens/s (GP3, GP5), a fraction (GP4), or applications (GP7). In one paper the text says
  requests/s while the formula weights by tokens: "Goodput is defined as the number of completed requests that meet the SLOs
  per second" vs Goodput = Σ 1(∀i, t_i ≤ d_i)·n_r / T (arxiv_2410.14257, §4.1, Eq. 7).
- **Which SLOs, and joint or not.** DistServe requires TTFT and TPOT jointly. FlowPrefill uses TTFT only and leaves decode
  unconstrained (E03 note). AugServe uses TTFT plus normalized latency (arxiv_2512.04013, §6). Aegaeon counts per-token
  deadlines. A joint goodput is never larger than a single-SLO goodput at the same thresholds. [Syn]
- **Threshold scale.** Goodput depends steeply on the SLO thresholds, which are set per paper (§1.11), so goodput ratios
  between papers mean little. Aegaeon's advantage over MuxServe disappears at its strictest SLO scale, 0.2× (E05 note).
- **Gaming.** Abandoning requests that already missed their SLO raises request-level goodput (arxiv_2410.14257,
  abstract). Mooncake turns this into a design choice through early rejection.
- **The same word means unrelated things.** TurboSpec's goodput has no SLO, and Medha's is a fraction (§2).

### 1.11 SLO attainment, and how SLOs are set
SLO attainment appears in 36 papers; 34 are assigned to attainment variants. 61 full-text records have a non-null
`slo_spec`, and 49 are assigned to SLO-form variants.

**(a) Consensus [Syn].** The fraction of requests whose per-request latency metrics all meet their thresholds, e.g.
"SLO attainment (the proportion of requests that meet the SLOs)" (arxiv_2401.09670, §1).

| Attainment variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| A1 Per request, all SLOs jointly | 8 | 2401.09670, mlsys2025_sola, 2405.06856 Aladdin, 2504.07494, 2504.08784, 2512.03416 TokenScale, 2512.04013, 2401.08671 | "The SLO attainment rate is calculated by the number of served user requests that satisfy both TTFT and P99 TBT SLOs divided by the total number of requests" (2504.07494, §6.2) |
| A2 Per request, one metric | 8 | 2311.03285, 2602.16603, 2310.07240, 2501.12162, 2503.05096, 2407.00047, 2502.07903, 2302.11665 | "SLO attainment is defined as the percentage of requests that return the first token in 6 seconds." (2311.03285, §7.1) |
| A3 Separate pass rate per metric | 2 | 2508.16449 GreenLLM, 2412.17246 | "We collect the pass rates (TTFT%, TBT%)" (2508.16449, §4.3) |
| A4 Per **token** | 2 | sosp2025_aegaeon, 2407.07000 (fluidity-index) | "we define SLO attainment as the percentage of token generation times that meet their deadlines" (sosp2025_aegaeon, §2.1) |
| A5 Percentile-threshold SLO (PXX ≤ bound) with no per-request fraction | 8 | 2311.18677, 2407.00079, 2408.00741, 2405.05465, 2505.09999, 2410.01228, 2403.02310, 2501.01005 | "TTFTP90 = 4× indicates that 90% of inference requests will have a TTFT no greater than four times that of a single request running under the same conditions without interference" (2407.00079, §2) |
| A6 Program or application deadline | 2 | 2412.20993, 2506.14851 | "P90 deadline attainment, the percentage of queries completed within their deadlines" (2412.20993, App.) |
| A7 Threshold on a **mean** latency | 4 | osdi2024_dlora, 2408.12757, 2404.14527, 2505.06371 | Melange checks attainment post hoc: 99.5% / 99.95% of requests met an average-TPOT SLO (E04 note) |

| SLO-threshold form | n | Papers (examples) | Verbatim example [P] |
|---|---|---|---|
| F1 Absolute values | 30 | 2401.09670 (Table 1), sosp2025_aegaeon (10 s / 100 ms), 2505.09999 (8 s / 60 ms), 2512.03416, 2507.17769, 2504.02263 (150 ms TBT), 2506.12708 (50/30/15 ms TPOT), … | DistServe sets them empirically because "there exists no available SLO settings" (slo_spec); JITServe takes them from "P95 latencies measured on 1K DeepSeek API calls" (slo_spec) |
| F2 Multiple of uncontended, single-request or one-iteration latency | 22 | 2302.11665 (5×), 2311.18677 (2–6×), 2403.02310 (5×/25× a decode iteration), 2408.00741 (5×), 2407.00079 (10×/5×), mlsys2025_sola (5–15×), osdi2024_dlora (10× an iteration), 2504.19867 (7.5×/10×), 2405.06856 (1.3×), 2412.17246 (5× the **average** latency), 2501.14808 (5–50 % over the online-only baseline), … | "We set the SLOs to 5× the latency of a single request running isolated on a system [30]." (2408.00741, §III-A) |
| F3 TTFT bound grows with prompt length | 8 | 2401.08671 (prompt tokens/512 s), 2408.00741, 2512.03416 (250/400/2000 ms), 2407.07000, 2404.16283, 2508.16449, 2504.08784, 2504.07494 | "The target TTFT should depend on the service, be it constant or proportional to the prompt length." (2404.16283, §2.1) |
| F4 Justified by human reading speed | 9 | 2306.06000 (0.1875 s/token), 2310.19102 (100 ms), 2401.08671 (2/4/6 tok/s), 2404.16283, 2410.14257 (5 tok/s), 2408.12757 (200 ms), 2404.14527, 2505.06371, 2504.08784 | "the average reading speed of English readers, 4 words per second [12] and 0.1875 second per token [13]" (2306.06000, §1) |
| F5 Per-token deadline schedule | 6 | 2407.07000, 2410.14257, 2507.17769, 2504.20068, sosp2025_aegaeon, 2501.12162 | "We then define the deadline for the generation of the ith token as Di = Dp + i × Dd." (2407.07000, §4.1) |

**(d) Pitfalls.**
- "SLO = 5×" can mean 5× the latency of an isolated request (DynamoLLM), of one decode iteration (Sarathi-Serve, dLoRA),
  of the **average** latency under load (BlitzScale evaluation), or of single-device latency (AlpaServe, HexGen-2). These
  thresholds are not comparable. [Syn from the quotes above]
- A5 (P99 of each metric ≤ bound) and A1 (fraction of requests meeting all bounds jointly) differ when the violations
  fall on different requests. A1 at 99 % is stricter than two separate P99 bounds. [Syn]
- A7 SLOs bound a mean, so a heavy tail can still "meet" them (dLoRA, NanoFlow, Melange).
- The same reading-speed rationale (F4) is attached to per-token targets from 40 ms (Melange) to 0.5 s (FastGen at
  2 tokens/s), a 12× range. [Syn from slo_spec values]

### 1.12 Queueing / scheduling delay (QUEUE)
13 papers use it; 3 define it. It is mostly an internal objective or a diagnostic, rarely a headline.
- **Consensus [Syn]:** arrival → start of prefill (scheduling delay). For programs, the sum of the waits of all calls.
- **Variants:**
  - Scheduling delay as a capacity condition: P99 < 5 s in Vidur (arxiv_2405.05465, §6); median ≤ 2 s in Sarathi-Serve
    (E01 note).
  - Program-level cumulative waiting: "waiting time, the total queuing time of a program's LLM calls on the engine"
    (arxiv_2502.13965, §3).
  - Queueing-time ratio used to set the load (arxiv_2508.06948).
  - Per-turn queueing in agent loops (arxiv_2511.02230).
  - Pending-time reduction as the scheduler objective (arxiv_2504.07494).
  - Queue length as an RL router's penalty (arxiv_2408.13510).
- **Pitfall:** queueing is folded into TTFT or E2E in 16 + 8 papers (§1.1 T1, §1.4 E1), so a gain in either can be a pure
  queueing effect. Etalon's TTFT critique: "Naively comparing two systems on their TTFT does not reveal the individual
  contribution of these components" (arxiv_2407.07000, §3.1).

### 1.13 Program / workflow JCT (PROGRAM_JCT)
14 papers (13 assigned), almost all 2024–26 agent, compound and RAG systems.
- **Consensus [Syn]:** submission of a multi-call program → its final output, including LLM queueing and execution, and
  (by default) tool or external time. Parrot: "the system should minimize the end-to-end time it takes to receive the
  final summary, rather than the latency of individual requests." (arxiv_2405.19888, §3).

| Variant | n | Papers | Verbatim example [P] |
|---|---|---|---|
| J1 App submission → final output, under load | 6 | 2405.19888 Parrot, 2407.00326 Teola, 2506.14851, 2510.18586 TokenCake, 2511.02230 Continuum, 2502.13965 Autellix | "a single-threaded program's end-to-end latency comprises three components: (1) waiting time … (2) execution time … and (3) interceptions" (2502.13965, §3) |
| J2 One program at a time (batch 1) | 4 | 2312.07104 SGLang, 2507.07400 KVFlow, 2312.04511 LLMCompiler, 2406.00059 | "we execute a single program at a time without batching and report the average latency" (2312.07104, §6.1) |
| J3 Normalised per generated token | 2 | 2502.13965, 2508.06948 | see §1.5 N8 |
| J4 Batch makespan of many workflows | 1 | 2603.16104 Helium | "total wall-clock time for query batch preparation and execution" (§7.1) |
| J5 / J6 Tool time included / excluded | 4 / 2 | included: 2510.18586, 2511.02230, 2406.00059, 2506.14851; excluded or subtracted: 2402.01869, 2502.13965 | — |

- **Pitfalls:** tool time in or out (J5 vs J6). Critical-path vs summed time for parallel programs (Autellix divides
  "critical path response time" by tokens of all threads, fn 2). The same paper may treat a batch makespan (Helium) or a
  per-token normalisation (Kairos) as "latency".

### 1.14 Token-timeline QoE family (QOE, fluidity, smooth goodput, per-token deadline attainment)
7 papers, 2023–2025. All score the token-delivery timeline against a schedule the user would accept.

| Variant | Paper | Definition [P] |
|---|---|---|
| QoE as normalised area of delay (average slowdown) | 2404.16283 Andes | "QoE = 1 − S_delay / S_whole", with S_delay = Σ_i (T_i^Actual − T_i^Ideal) against an ideal TTFT + reading-speed timeline (§3.1) |
| Fluidity-index: fraction of token deadlines met, slack carried forward | 2407.07000 Etalon | "return (total_deadlines − missed_deadlines) / total_deadlines" (Alg. 1); fluid token generation rate = inverse of the minimum Dd such that 99 % of requests have fluidity ≥ 0.9 (§5.1) |
| Smooth goodput with **max** idle latency | 2410.14257 | "l_r = max_{i=1..n} (t_i − d_i)" with d_i = V × i (§4.3, Eq. 9), explicitly contrasted with Andes' average |
| Per-token deadline attainment | sosp2025_aegaeon, 2504.20068 | see §1.10, §1.11 |
| Soft first-token satisfaction | 2311.03285 S-LoRA | "The satisfaction becomes 0 if the first token latency exceeds the SLO." (§7.1) |
| Time to first *visible* token | 2510.18672 | see §1.1 T6' |

- **Pitfalls:** average (Andes) vs max (smooth goodput) aggregation over tokens. With or without slack carry-forward:
  Etalon resets deadlines after a miss, because otherwise "a single stall can amount to 10s of deadline-misses" (§4.1).
  The reading-speed parameter V is a free choice of 4.5 to 30 tokens/s in arxiv_2410.14257 (slo_spec).

### 1.15 Cost
31 papers; 26 assigned.

| Variant | n | Papers | Example [P] |
|---|---|---|---|
| C1 GPU or instance count to meet a target | 9 | 2405.06856, sosp2025_aegaeon (1,192 → 213 GPUs), 2512.03416, 2302.11665, 2306.06000, 2210.17323, 2407.00047, 2404.16283, 2406.03243 | "we use the number of GPUs required to achieve a certain SLO attainment rate as the main metric" (2405.06856, §6.1) |
| C2 $/h rental or $ for the workload | 6 | 2404.14527, 2311.15566, 2408.00741, 2405.05465 (QPS per $), 2403.19708, 2311.18677 | "The service cost is computed by summing the hourly on-demand cloud renatl rates for each of the selected GPUs." (2404.14527, §5.1) |
| C3 Instance-time (GPU-seconds) | 4 | 2507.17769, 2401.11181, 2412.17246, 2211.05102 (chip-seconds per token) | "We define the cost as instance · second" (2507.17769, §3) |
| C4 Analytic $ per 1M tokens (roofline) | 1 | 2507.19427 Step-3 | "accelerators constantly at their peak FLOPs and maximum memory bandwidth" (§4.2) |
| C5 Throughput per purchase price, per chip, or tokens per $ | 4 | 2504.02263, 2503.14649 (QPS/chip), 2404.14527 (T/$), 2405.04532 | — |
| C6 API $ or tokens generated as a compute proxy | 2 | 2312.04511, 2412.20993 | — |
| C7 Cost as a budget constraint | 1 | 2502.07903 HexGen-2 | — |

- **Pitfalls:** a measured $ (C2) is not comparable to analytic $ (C4) or to GPU counts at a given attainment (C1).
  DistServe uses per-GPU goodput as its cost proxy (§1.10). TetriInfer's "perf/$" is never defined (E03 note).

### 1.16 Energy / power
11 papers.

| Variant | n | Papers | Example [P] |
|---|---|---|---|
| W1 GPU/accelerator-only scope | 3 | 2505.06371 ML.ENERGY (Zeus), 2411.00136, 2508.16449 | "We report the power consumed only by the accelerators, not host and other peripherals." (2411.00136, §III.5(e)) |
| W2 Node-level scope | 1 | 2512.03024 TokenPowerBench | E_total = E_GPU + E_CPU + E_DRAM + E_Others (Eq. 2) |
| W3 Total Wh of an experiment under SLO | 1 | 2408.00741 DynamoLLM | "we measure the energy consumption in Watt-hours (Wh) while meeting certain latency SLOs" (§II) |
| W4 Energy per token | 2 | 2508.16449 ("energy per token (i.e., power/TPS)"), 2512.03024 | — |
| W5 Energy per response | 2 | 2505.06371, 2512.03024 | "any work less than the full response (e.g., per token) is not considered a complete request" (2505.06371, §2.3) |
| W6 Throughput per watt / iso-power | 4 | 2411.00136, 2504.02263, 2311.18677, 2505.06371 | — |

- **Pitfalls:** scope (GPU vs node) can differ by the CPU, DRAM and idle share. J/token vs J/response differ by output
  length, and ML.ENERGY argues per-token energy hides verbosity. ML.ENERGY measures only a "steady state" window
  (saturated batch), which excludes ramp-up (§3.2).

### 1.17 Memory
43 papers. Mostly an objective for KV/quantization papers and a constraint elsewhere. Only 4 papers define a memory
metric.
- **Variants [P, from records]:**
  - Peak GPU memory (KIVI 2402.02750, SmoothQuant 2211.10438).
  - Weight footprint or GPUs needed (LLM.int8 2208.07339, GPTQ 2210.17323, AWQ 2306.00978).
  - KV waste or fragmentation (vLLM 2309.06180, vAttention 2405.04437, Jenga 2503.18292, S-LoRA 2311.03285, LoongServe
    2404.09526).
  - KV budget % (H2O 2306.14048).
  - Max batch size (ShadowKV 2410.21465).
  - Max context before OOM (SnapKV 2404.14469: "memory efficiency" = 16K → 131K tokens).
  - KV involved in attention (InfiniGen 2406.19707, "relative KV cache size").
  - KV bytes to transmit (CacheGen 2310.07240: "this measures the bandwidth needed to load KV caches").
  - KV occupancy over time (2510.18672, 2510.18586).
  - Cache size needed for a hit ratio (2506.02634).
- **Pitfalls:** "memory efficiency" and "memory utilization" name at least four different quantities. Jenga's "+79.6 %
  memory utilization" equals the analytic waste figure for one model (E07 note).

### 1.18 Quality
47 papers, almost always as a constraint (37 constraint entries vs 3 objectives in `summary_v2`).
- **Variants:**
  - Lossless by construction: exact speculative sampling, exact attention, lossless expert loading. Examples:
    2211.17192 "with identical outputs", 2503.01840, 2402.12374, 2502.05370, 2205.14135.
  - Perplexity (GPTQ, AWQ, StreamingLLM, Atom, …).
  - Task accuracy, F1 or ROUGE with a tolerance. CacheBlend: "reduction in F1 and Rouge-L score is within 0.02"
    (arxiv_2405.16444, §7.1, extractor).
  - Accuracy inside the objective: LLMCompiler 2312.04511, SART 2505.13326 (efficiency "when achieving the same level of
    accuracy"), Certaindex 2412.20993.
  - Proxy quality: DREX softmax confidence at P95 (2512.15705); FA3 RMSE (2407.08608).
  - Output-length change: 2503.24000.
- **Pitfall:** lossy methods report quality on different benchmarks, so their efficiency gains are paired with
  incomparable quality budgets. [Syn]

### 1.19 Fairness
6 papers.
- **Variants:**
  - Max-min bound on weighted service, "W(t1,t2) = w_p * n_p(t1,t2) + w_q * n_q(t1,t2)" with w_p = 1, w_q = 2 (VTC,
    arxiv_2401.00588, §3.1).
  - The same with prefix-cached tokens excluded, plus Jain's index, "J(x1,...,xn) = (sum x_i)^2 / (n sum x_i^2)"
    (arxiv_2501.14312, §6.1).
  - max_waiting_time (arxiv_2408.15792).
  - Finish-time fairness via latency per token (arxiv_2412.20993).
  - Starvation prevention as a constraint (osdi2024_dlora, 2407.00023).
- **Pitfall:** service-based fairness (tokens) and latency-based fairness (waiting time) can rank schedulers
  differently. [Syn]

### 1.20 Utilization
38 papers.
- **Variants:**
  - MFU vs peak (Pope et al. 2211.05102: "the ratio of the observed throughput to the theoretical maximum throughput if
    the benchmarked hardware setup were operating at peak FLOPS"; Vidur, Medha, Step-3).
  - Achieved attention TFLOPs/s as a fraction of peak (FA2 2307.08691, FA3 2407.08608, DeepSpeed 2207.00032).
  - Bandwidth utilization (FlashInfer 2501.01005, Strata PCIe).
  - Offered-load utilization: "the offered load relative to the GPU's maximum achievable load" (2410.01228, Fig 2).
  - KV-block occupancy (2510.18586).
  - Tokens/s per TFLOPS (2506.12708).
- **Pitfall:** FA2's MFU formula is the training one, with the attention term not halved for causal masking (§4.2). It
  is not an inference metric (E11 note).

### 1.21 Speculative acceptance (ACCEPT)
12 papers.
- **Variants:**
  - Acceptance rate α = E[min(p, q)] (2211.17192, Def 3.1).
  - Mean accepted length τ per verification (EAGLE 2401.15077, EAGLE-3 2503.01840).
  - "Acceleration rate", which counts the bonus token (Medusa 2401.10774).
  - Step compression ratio (Lookahead 2402.02057).
  - Tokens per decoding step (Sequoia 2402.12374, SpecInfer 2305.09781).
  - Per-draft-token acceptance (LayerSkip 2404.16710, EAGLE-3 "n-α").
- **Pitfall:** τ with or without the bonus token differs by 1. Speedup = acceleration rate / per-step overhead (Medusa),
  so equal τ does not mean equal speedup.

### 1.22 Mechanism proxies optimized directly (OTHER)
- Token hit rate and FLOP efficiency (2411.19379). Marconi accepts a 6.3 % worse P5 TTFT for P50/P95 gains (E07 note).
- Cache hit rate (2312.07104: "number of cached prompt tokens / number of prompt tokens").
- Expert hit rate (2502.05370).
- Model startup latency (2401.14351).
- Kendall's τ of the predicted schedule (2408.15792).
- Token velocity, a capacity per stage (2512.03416).
- Generation stalls (2403.02310, 2410.18038: "% requests with stalls" above 200/500 ms TBT).
- Preemption blocking time (2602.16603).

---

## 2. Terms that mean different things (same word, different quantity)

| Term as written | Quantity A (common use) | Other quantities under the same word (paper, locator, verbatim) [P] |
|---|---|---|
| **TBT** | Each inter-token gap under serving load (2403.02310, §2.4) | **Sequoia**: mean ms/token of one sequence at batch 1, "TBT refers to time between tokens." (2402.12374, Table 1). **Splitwise**: "Average token streaming latency" (2311.18677, Table II). **Intelligent Router**: "the average token streaming latency" (2408.13510, §6). **ConServe**: per-step execution time (2410.01228, §2) |
| **ITL** | Inter-token latency, = TBT | **FlashInfer** also expands it as "Inference Time Latency" (2501.01005, App. G). **LLM-Inference-Bench**: (E2E − TTFT)/(Batch × (Out − 1)), a batch aggregate (2411.00136, Eq. 1). **LMCache**: "the average delay" (2510.09665, §8). **RLLM**: "the average time between" (2510.18672, §2) |
| **TPOT** | Per-request mean decode gap excluding the first token (2401.09670, §1) | **Melange**: "dividing request latency by the number of generated tokens" (2404.14527, §4.1), i.e. normalized latency. **PolyServe**: inter-token time enforced as a deadline (2507.17769, §2). **RAGO**: worst case (2503.14649, §4). **Step-3/CloudMatrix384**: per-step time at a fixed batch (2507.19427, 2506.12708) |
| **End-to-end latency** | Request arrival → last token (2407.00023, §4.1) | **SmoothQuant**: one prefill pass over a batch of 4 (2211.10438, §5.3). **Atom**: "average decoding time of each token, without considering the queuing time" (2310.19102, §5.3). **SpecInfer**: Fig 7 "end-to-end inference latency" plots average per-token latency (2305.09781, §6.2). **Quest**: "End-to-end latency of Quest", i.e. one-token decode at batch 1 (2406.10774, Fig 10). **Helium**: makespan of a batch of workflows (2603.16104, §7.1). **RLLM**: "from submitting the first token of a request" (2510.18672, §2) |
| **Goodput** | Max request rate at X % SLO attainment (2401.09670, §1) | **TurboSpec**: accepted tokens / execution time, no SLO (2406.14066, §4.1.1). **Medha**: "the fraction of requests meeting their deadlines" (2409.17264, §4.1). **AdaServe**: SLO-meeting tokens/s (2501.12162, §6.1). **Mooncake**: only fully completed requests count (2407.00079, §2). **Hermes/PDGraph**: applications completing before their deadline (2506.14851, §2) |
| **Throughput** | Tokens/s or req/s of the system | **Lookahead**: "throughput of single batch inference" = one sequence's tokens/s (2402.02057, §5). **FlashDecoding++**: "throughput of generating tokens (i.e., reducing latency of each token)" (2311.01282, §1). **vLLM**: max request rate before normalized latency explodes (2309.06180, §6.2). **Dai et al.**: queueing-stability region (2504.07347, §3.2). **CachedAttention**: prefill throughput (2403.19708, §5.2). **Continuum**: offered job arrival rate on the x-axis (2511.02230, E14 note). **AdaSpec**: accepted tokens per speculation step (2503.05096, §4) |
| **Per-token latency** | — | **NORM_LAT** (E2E/output length): FastServe 2305.05920, LTR 2408.15792, NEO 2411.01142 ("dividing its full latency by its output token number"). **Single-sequence decode**: GPTQ 2210.17323, SpecInfer 2305.09781. **TPOT**: ServerlessLLM 2401.14351 ("the average time to generate a token") |
| **Latency** (unqualified) | E2E | **ServerlessLLM**: model startup latency (2401.14351, §7). **FlexGen**: whole-block time for b·n tokens, thousands of seconds (2303.06865, §3). **TokenWeave**: a forward pass of a batch (2505.11329, App.). **Kairos**: program-level token latency (2508.06948, §7.1) |
| **Capacity** | Max sustainable QPS under latency targets (2403.02310, §2.4) | **Vidur**: P99 scheduling delay < 5 s (2405.05465, §6). **vAttention**: "without incurring high queuing delays" (2405.04437, §7.4). **SLOs-Serve**: per-GPU load at 90 % attainment (2504.08784, §1). **TokenScale**: "Token Velocity", the maximum per-stage release rate (2512.03416, §III-B). **dLoRA**: "peak capacity of a LoRA adapter" in requests that fit in memory (osdi2024_dlora, §5.1) |
| **TPS** | System tokens/s (2510.18672, §2) | **Per-request** generation rate (2502.05370, §2.1). **TPR = 1/TPOT** (2502.04563, §7) |
| **Effective throughput** | Goodput in req/s at an attainment level (2504.07494, §1) | **FastGen**: measured req/s of SLA-meeting requests (2401.08671, §4.1.2). **AugServe**: SLO-satisfying requests per unit time (2512.04013, §1) |
| **Normalized latency** | E2E / output tokens, mean (2309.06180, §6.1) | **Median** (osdi2022_orca, 2402.01869, 2403.01876). **P90** (2312.05516 §6.1, contradicted by §6.2). **Divided by input+output** (2404.09526, §7.1). **Ratio of sums** (osdi2024_dlora, §7.1). **Program-level** (2502.13965, §6) |
| **SLO 5×** | 5 × an isolated request's latency (2408.00741, §III-A) | 5 × one decode iteration (2403.02310 strict SLO); 5 × the **average** latency (2412.17246, §6.2); 5 × single-device latency (2302.11665, §6.1) |
| **P99 latency** | P99 of E2E | **TraCT**: P99 TTFT (2512.18194, §5.3). **Apt-Serve**: P99 of a request's own TBTs (2504.07494, §3.1) |
| **Speedup / "N× faster"** | Wall-clock ratio vs a baseline | Fixed-batch per-token ratio, which equals the throughput ratio (2408.11049); old/new − 1 reported as a percentage (2406.00059); vs a recompute baseline (2309.17453, 22.2×); with a GPU-count change folded in (2210.17323) |

---

## 3. Undefined metrics — headline or primary metrics used without a definition

Curated from extractor flags ("never/not formally defined", "units not stated", "only acronym expansions") and listed in
`analysis/def_variants.py` (UNDEF). "Undefined" = no definition anywhere in the paper. "Scope unstated" = a loose
definition that leaves queueing, token type or unit open.

| Metric | Undefined (n) | Scope unstated (n) | Examples (key: what is missing) |
|---|---|---|---|
| Throughput (tokens or requests) | 14 | 5 | 2402.02750 KIVI: "Throughput never formally defined; units not stated (token/s vs req/s; input+output vs output only)". osdi2022_orca: req/s "never defined in text". 2309.06180 vLLM: only operationalised as the knee of the normalized-latency curve. 2401.15077 EAGLE: "units not stated". 2503.01840 EAGLE-3: "input/output token accounting unstated". 2405.16444 CacheBlend: "Never defined formally" |
| TTFT / first-token latency | 15 | 6 | 2405.05465 Vidur: "TTFT and TBT never formally defined; listed as simulator outputs". 2606.00946 Lodestar: "never given a formal definition" yet it is the RL reward. 2501.01005 FlashInfer: "Neither TTFT nor ITL is formally defined". 2411.19379: queueing "not stated" |
| TBT / ITL / TBOT | 5 | 0 | 2508.16449: "not formally defined; used as sliding-window P95". 2503.24000: "TBOT … named but not defined" |
| E2E / JCT / "latency" | 8 | 1 | 2401.11181 TetriInfer: JCT "used without formal definition". 2407.00326 Teola: "never formally defines 'latency'". 2503.18292 Jenga: "Only acronym expansions" |
| Single-sequence speed | 5 | 0 | 2309.17453 StreamingLLM: "Not defined formally". 2507.07120: TTL "never formally defined beyond reciprocal of interactivity" |
| SLO / attainment | 2 | 0 | 2404.09526: SLO = 25× an "inference latency" that is never defined. 2512.03416: "TTFT/TPOT/SLO attainment themselves not formally defined" |
| Cost / energy | 2 | 0 | 2401.11181: "perf/$ never formally defined". 2512.03024: "power imbalance and energy-delay product are named but never formally defined" |
| **Distinct papers** | **40 of 143 (28 %)** | **+10 with scope-unstated only (35 % in total)** | |

The automated screen (`def_undefined.py`) flags 54 of 143 papers. It is looser: it also counts headline metrics for which
the extractor copied no definition entry. Beyond the full-text set, about 20 abstract-only records claim only
"latency" or "speedup" with no metric named [abstract only] (RESEARCH_LOG, A01).

---

## 4. Relationships between metrics (only those the papers support)

| # | Relationship | Support |
|---|---|---|
| R1 | **E2E = TTFT + (n − 1)·TPOT** per request (exact identity from the §0 definitions) [Syn] | DistServe states the same identity: "The overall request latency equals TTFT plus TPOT times the number of generated tokens in the decoding phase." (arxiv_2401.09670 §1 fn 1; corrected after report review r4) |
| R2 | **Per-user rate = 1/TPOT** (or 1/TBT per gap) | "TPR = 1/TPOT" (arxiv_2502.04563, §7); interactivity = "reciprocal of decoding TTL" (arxiv_2507.07120, §3); "50ms time per output token (TPOT, ≥ 20 tokens/sec)" (arxiv_2507.19427, §3.1) [P]. Etalon turns both into stream-rate "throughputs" ("we plot the inverse of the observed mean TPOT … and the inverse of the 99th percentile TBT", arxiv_2407.07000, §5.1), and they disagree by 3× on the same run (§5.2) [P] |
| R3 | **Normalized latency = TTFT/n + TPOT·(n−1)/n**: a length-weighted mix of first-token and decode latency, so it moves with the output-length distribution [Syn from R1] | Etalon: normalization "ends up hiding specifics about metrics such as scheduling delay" (arxiv_2407.07000, §3.1) [P]. Lodestar rejects decode-dependent metrics as rewards because of the "unknown factor, the number of decode tokens" (arxiv_2606.00946, §4.1) [P] |
| R4 | **Goodput = throughput restricted to SLO-meeting work.** At a given load, goodput ≤ throughput, and joint-SLO goodput ≤ single-SLO goodput [Syn] | DistServe GP1 (§1.10); Mooncake: "maximize overall throughput while adhering to SLOs, a concept referred to as goodput" (arxiv_2407.00079, §2) [P]; smooth goodput equals goodput minus an idle-latency penalty (arxiv_2410.14257, Eq. 10–11) [P] |
| R5 | **Throughput–interactivity (latency) frontier**: raising the batch raises tokens/s/GPU and lowers tokens/s/user, so a method is a frontier shift, not a point | Helix: "we characterize the full Pareto frontier between throughput per gpu (tokens/sec/gpu) vs. interactivity (tokens/sec/user)" (arxiv_2507.07120, §3) [P]. CloudMatrix384: 1,943 / 974 / 538 tokens/s/NPU at TPOT ≤ 50 / 30 / 15 ms via batch 96 / 24 / 8 (arxiv_2506.12708, Table 4) [P]. Pope et al.: "a new Pareto frontier on the latency and model FLOPS utilization (MFU) tradeoffs" (arxiv_2211.05102, abstract) [P]. RAGO outputs a TTFT vs QPS/chip frontier (E14 note) [P]. ML.ENERGY: a time–energy Pareto frontier (arxiv_2505.06371, §3.3) [P] |
| R6 | **At a fixed batch, throughput ∝ 1/per-token latency**, so the two report the same gain; under an arrival process they separate | Helium: "Since throughput is inversely proportional to latency for a fixed batch size, we report only latency" (arxiv_2603.16104, §7.1) [P]. FlashDecoding++: "throughput of generating tokens (i.e., reducing latency of each token)" (arxiv_2311.01282, §1) [P]. MagicDec equates fixed-batch latency speedup with throughput speedup (extractor note, arxiv_2408.11049). EAGLE-3: 6.5× at batch 1 but 1.38× throughput at batch 64 (E10 note) [P] |
| R7 | **Unit conversions between throughputs**: output-only = d/(p+d) × total tokens/s; req/s = 1/(p+d) × total tokens/s | NanoFlow (arxiv_2408.12757, §3.1) [P] |
| R8 | **TTFT ↔ TBT trade-off** through prefill/decode interference: chunk size or token budget moves latency from one to the other | DistServe: chunked prefill "trades TTFT for TPOT" (arxiv_2401.09670, §2, record `tradeoff_acknowledged`) [P]; Sarathi-Serve's token budget is derived from the TBT SLO (E01) [P]; POD-Attention reports 95+% of vLLM requests stalling vs Sarathi's long median TTFT (E12) [P]; Dai et al. Table 3: Sarathi-Serve best E2E/TTFT, FasterTransformer best TBT (E03) [P] |
| R9 | **Mean and tail of the same metric can move in opposite directions** | DynamoLLM: P50 TTFT/TBT +11.4 % / +7.6 % while P99 −5.3 % / −11.1 % (E04). Marconi: P5 TTFT worse, P50/P95 better (E07). Preble's local fairness improves P99, not the average (E04). Autellix's MLFQ improves the mean and hurts tails (E13). TokenCake's priority_first has the lowest mean and an inflated tail (E14). SART: N = 4, 8 raise P50/P90 but lower P97/P99 (E14). All [P] |
| R10 | **TTFT is the earliest observable latency signal** for an online decision; E2E and TPOT arrive later and carry decode-length noise | Lodestar (arxiv_2606.00946, §4.1) [P]. The Intelligent Router instead uses mean E2E with a queue-length penalty in its reward (E04; arxiv_2408.13510) [P] |
| R11 | **Metric choice can reverse rankings** | Etalon (vLLM vs Sarathi-Serve: TPOT parity, P99 TBT 3×, fluidity capacity equal at 0.6 QPS; arxiv_2407.07000, §5.2) [P]. ServeGen: naive Poisson workloads flip the best PD configuration (E15) [P]. arxiv_2503.24000: fixed-length throughput benchmarks hide response-length inflation (§4.3) [P] |

---

## 5. What should change in the survey's framing [Syn]

1. **Report the metric vocabulary at the variant level, not the name level.** Five names hide incompatible quantities:
   TTFT (prefill-only vs arrival-based), TBT/ITL (token distribution vs average vs batch-1 per-token), goodput (rate at X %,
   tokens/s, fraction, no SLO), throughput (input+output vs output vs decode vs prefill; offline-max vs latency-bound),
   and "end-to-end latency" (request vs batch vs prefill pass). Any per-paper count of "optimizes TTFT" should be split
   at least into T1 (arrival-based) and T2/T3 (prefill-only).
2. **Treat single-sequence decode speed as its own family,** separate from serving latency. 33 papers (most of D4 and
   part of D5) never measure latency under an arrival process, so they cannot support claims about TTFT, TBT or tails.
3. **Capacity under a latency condition is the dominant "throughput" in serving papers.** Q4 + Q5 + GP1 = 32 assigned
   papers. The condition (mean vs median normalized latency, a P99 threshold, an attainment fraction, scheduling delay)
   is part of the metric's definition, and the H1 "throughput → SLO" shift partly reflects a change in how this
   condition is written.
4. **SLO thresholds are not standardised.** 30 papers use absolute values and 22 multiples of an unloaded latency, and
   "5×" alone has four bases. Cross-paper goodput or attainment ratios should not be compared. DistServe says so:
   "there exists no available SLO settings" (slo_spec, arxiv_2401.09670).
5. **For anyone reporting serving latency.**
   - State TTFT as arrival-based (T1) and TBT as the token-level distribution (P3), and keep P99 TPOT (over requests)
     separate from P99 TBT (over tokens).
   - Normalized latency and mean TPOT are poor proxies for tail experience (R3, Etalon §3.1).
6. **Undefined headline metrics are common.** 40 of 143 full-text papers (28 %), 50 (35 %) counting scope-unstated
   cases, so any table of "what papers optimize" carries definitional uncertainty that should be stated alongside it.
