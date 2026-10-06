# INDUSTRY_DEFS — metric definitions in industrial benchmark harnesses (agent IND, 2026-10-06)

All sources fetched 2026-10-06 from the default branch (master/main), so line numbers can drift. Local copies are in
`fulltext/industry_*`; line numbers below refer to those copies. [P] = read in full text; [unverified] = not read.

## 1. MLPerf Inference (MLCommons) — LLM tasks, Server / Interactive scenarios

Sources: `industry_mlperf_inference_rules.adoc` (github.com/mlcommons/inference_policies, inference_rules.adoc),
`industry_mlperf_loadgen_{logging,loadgen,results}.cc` and `industry_mlperf_mlperf.conf`
(github.com/mlcommons/inference, loadgen/), `industry_mlperf_llama2_readme.md`.

| Item | Definition / value | Locator |
|---|---|---|
| TTFT, TPOT (rules text) | "For LLM benchmarks, 2 latency metrics are collected - time to first token (TTFT) which measures the latency of the first token, and time per output token (TPOT) which measures the average interval between all the tokens generated." [P] | rules.adoc l.270 (footnote on DeepSeek-r1 row) |
| Latency origin | "Latency is defined as the time from when the LoadGen was scheduled to pass a query to the SUT, to the time it receives a reply." In code: `latency = sched.delta(complete_begin_time)` with `sched{query->scheduled_time}`; the first-token path uses the same `scheduled_time` origin. So TTFT = first-token time minus scheduled arrival time, which **includes issue delay and all queueing in the SUT**. [P] | rules.adoc l.~400; loadgen.cc l.103, 130, 156 |
| TPOT computation | Per sample: `time_per_output_token_[i] = (latency - token_latencies_[i]) / (n_tokens - 1)` = (end-to-end latency minus TTFT)/(n-1). Per-request scalar, excludes first token; same as DistServe/vLLM TPOT. n_tokens must be > 1. [P] | logging.cc l.475-476, 450-454 |
| Percentile | Server/Interactive tail latency 99% (`*.Server.target_latency_percentile = 99`); the token-latency percentile objects take `settings.target_latency_percentile`, so TTFT and TPOT are both checked at P99 over requests. Constraint check: P99 TTFT <= ttft_latency AND P99 TPOT <= tpot_latency, otherwise "TTFT/TPOT constrain not met: Reduce target QPS". Loadgen also prints P50/90/95/97/99/99.9. [P] | rules.adoc l.141; mlperf.conf l.83; results.cc l.356-370; results.h |
| Performance metric | Server: "Maximum Poisson throughput parameter supported" (max QPS for which the P99 constraints hold; binary search over QPS). Offline: "Measured throughput". [P] | rules.adoc l.141-142, 409-415 |
| Tokens/s counting | Loadgen sums `n_tokens` reported by the SUT per sample. Offline "Tokens per second" = token_count / max_latency; Server "Completed tokens per second" = token_count / final_query_all_samples_done_time. These are **output tokens only** (n_tokens is the generated-token count); prompt tokens not counted. [P; "output only" is my reading of n_tokens, the rules do not say so in one sentence] | results.cc l.446-452 |
| Token-count guard | Output length must be within 90% (some tasks 90-110%) of the reference tokens_per_sample, so tokens/s cannot be raised by truncating outputs. [P] | rules.adoc l.266-269; l.889 |
| Goodput | No goodput metric: the SLO is a hard validity gate (P99), and the score is the max QPS passing it. | - |

SLO thresholds (TTFT/TPOT, both P99) [P, rules.adoc l.266-271, mlperf.conf l.117-164]:

| Task | Server (Conversational) | Interactive |
|---|---|---|
| Llama3.1-8B | 2000 ms / 100 ms | 500 ms / 30 ms |
| Llama2-70B | 2000 ms / 200 ms | 450 ms / 40 ms |
| Llama3.1-405B | 6000 ms / 175 ms | 4500 ms / 80 ms |
| Mixtral-8x7B | 2000 ms / 200 ms | none |
| DeepSeek-R1 | 2000 ms / 80 ms | 1500 ms / 15 ms |
| GPT-OSS-120B | 3000 ms / 80 ms | 2000 ms / 15 ms |
| Qwen3-VL-235B | 12 s (end-to-end) | 1.5 s |

## 2. vLLM `vllm bench serve` (vllm/benchmarks/serve.py, lib/endpoint_request_func.py)

Sources: `industry_vllm_serve.py`, `industry_vllm_endpoint_request_func.py`.

| Metric | Definition (code) | Locator |
|---|---|---|
| TTFT | `st = time.perf_counter()` taken just before the HTTP request is sent; `output.ttft = timestamp - st` at the first streamed chunk with content. Client-side, from request send; excludes any client-side wait before send. With `--max-concurrency`, a separate `client_queue_time = start_time - request_arrival_time` is reported (`client_queue_time`, `e2el_including_client_queue`), so the harness distinguishes in-server from client-side queueing. | endpoint_request_func.py l.228, 266; serve.py l.984, 1318-1325, 1398-1410 |
| ITL | Every gap between consecutive streamed chunks, `output.itl.append(timestamp - most_recent_timestamp)`; pooled across all requests (per-token samples). Note chunks may bundle several tokens. | endpoint_request_func.py l.270; serve.py l.632 |
| TPOT | `(latency - ttft) / (output_len - 1)` if output_len > 1; label "Time per Output Token (excl. 1st token)". Per-request scalar. | serve.py l.625-629, 1395 |
| E2EL | `output.latency = most_recent_timestamp - st` (send to last chunk). | endpoint_request_func.py l.287 |
| Request throughput | `completed / dur_s` | serve.py l.749 |
| Output token throughput | `sum(actual_output_lens) / dur_s` (output tokens only; tokenizer re-count when server did not report) | serve.py l.751 |
| Total token throughput | `(total_input + sum(actual_output_lens)) / dur_s` (prompt + output) | serve.py l.752 |
| Goodput | `request_goodput = good_completed / dur_s`: completions per second for which every given SLO holds (`slo >= value` for ttft, tpot, e2el). Allowed SLO keys: ttft, tpot, e2el (ms). Note: a request with output_len <= 1 gets TPOT = 0 for goodput (always passes). Help text cites DistServe. This is a **rate of good requests over the run**, not DistServe's "max rate at which >= X% attain SLO". | serve.py l.640-660, 750, 1473-1479, 1820-1830 |
| Default percentiles | `--metric-percentiles` default "99"; `--percentile-metrics` default "ttft,tpot,itl" (generation) or "e2el" (pooling); mean, median, std always reported. | serve.py l.1800-1818 |
| SLO thresholds | None by default; user supplied via `--goodput`. | - |

## 3. NVIDIA GenAI-Perf and NIM benchmarking guide

Sources: `industry_genaiperf_README.md` (github.com/triton-inference-server/perf_analyzer, genai-perf/README.md, Metrics section l.482-496),
`industry_genaiperf_goodput.md` (genai-perf/docs/goodput.md), `industry_nim_metrics.txt` (docs.nvidia.com/nim/benchmarking/llm/latest/metrics.html; this page now documents the successor tool **AIPerf**).

| Metric | Definition (verbatim) | Locator |
|---|---|---|
| TTFT | "Time between when a request is sent and when its first response is received, one value per request in benchmark" (GenAI-Perf). NIM guide: "Time to first token generally includes request queuing time, prefill time, and network latency." So server-side queueing is included; the clock starts at send. [P] | README l.489; nim.txt l.44 |
| Time to second token | Time between first and second streaming response. | README l.490 |
| ITL | "Time between intermediate responses for a single request divided by the number of generated tokens of the latter response, one value per response per request". NIM/AIPerf: "ITL is defined as the average time between consecutive tokens and is also known as time per output token (TPOT)", = (e2e_latency - TTFT)/(output_tokens - 1); the guide itself notes "tools differ on whether TTFT is included in the average". So NVIDIA's ITL is TPOT-like in AIPerf and per-response in GenAI-Perf. [P] | README l.491; nim.txt l.65-73 |
| Output token throughput per user | "Total number of output tokens (excluding the first token) divided by the total duration of the generation phase of each request" (GenAI-Perf). NIM: "TPS per user ... output sequence length divided by e2e_latency for each request, which asymptotically approaches 1/ITL" (includes the first token and prefill, unlike GenAI-Perf). | README l.492; nim.txt l.97-100 |
| System throughput | GenAI-Perf: "Total number of output tokens from benchmark divided by benchmark duration"; request throughput = final responses / duration. AIPerf/NIM: total output tokens / (Ty - Tx), first request to last response. Output tokens only. | README l.496-497; nim.txt l.90-93 |
| Goodput | "the number of completed requests per second that meet specified metric constraints, also called service level objectives." Flag `--goodput time_to_first_token:75 inter_token_latency:19.75` (ms) and `request_latency:22.5`. Example output prints "Request goodput (per sec)" next to request throughput. (Exactly how ITL SLO is applied to a request, per-response vs mean, was not read in source [unverified].) | goodput.md l.~26-31, 54-70 |
| Percentiles | avg, min, max, p99, p90, p75 for per-request metrics. | README l.489-495 |
| SLO thresholds | None by default; user-supplied. | - |

## 4. SGLang `bench_serving` (now sglang/benchmark/serving.py), llm-d, NVIDIA Dynamo

- SGLang [P]: `industry_sglang_serving.py`. `ttft = timestamp - st` at first streamed chunk (l.217); TPOT = `(latency - ttft)/(output_len-1)` (l.1156-1157); ITL = chunk gaps pooled (l.222; chunk gap divided by new tokens in one path, l.790); output_throughput = sum(output_lens)/duration (l.1268), total_throughput adds input (l.1270); request_throughput = completed/duration. Reports mean, median, std, P90, P95, P99 for TTFT/TPOT/ITL/E2E (l.1047-1078). **No goodput or SLO flag** (grep for goodput/slo: none). Header comment says TPOT excludes the first token (l.1055).
- llm-d, NVIDIA Dynamo goodput/SLO definitions: [unverified], not fetched (time-box).

## 5. Comparison with the modal academic definitions (DEFINITIONS.md 1.1, 1.2-1.3, 1.8, 1.10)

| Dimension | Modal academic | MLPerf | vLLM | GenAI-Perf / NIM | SGLang |
|---|---|---|---|---|---|
| TTFT includes queueing? | Yes: arrival to first token incl. scheduling delay | Yes: clock starts at scheduled arrival (includes issue delay) | Partly: from request send; server queueing yes, client-side wait reported separately | Yes: from send (NIM text says includes queuing) | From send; same as vLLM |
| TPOT | (t_n - t_1)/(n-1), per request | Same, (latency - TTFT)/(n-1) | Same | AIPerf: same, but calls it ITL; GenAI-Perf ITL is per response | Same |
| ITL/TBT (per-gap) | Every gap is a sample | Not used | Pooled gaps (chunks may bundle tokens) | Per response, divided by tokens in response | Pooled gaps |
| Percentile | Mixed; P99 common for TBT, P90/P99 for TTFT | P99 over requests for both TTFT and TPOT (gate) | P99 default | p99/p90/p75 | P90/P95/P99 |
| Throughput tokens | No consensus (input+output vs output) | Output tokens / wall time | Output and total (in+out) both reported | Output tokens only | Output and total both reported |
| Goodput | Max request rate with >= X% (usually 90%) meeting all SLOs (DistServe) | None; P99 SLO is a pass/fail gate and score is max QPS (equivalent in spirit to goodput at X = 99%) | good requests per second at the offered load, all SLOs ("all"), no attainment target | Same kind: good completions per second | None |

Key points. (1) MLPerf's Server scenario is the closest industrial analogue of DistServe-style goodput: it searches for the maximum QPS at which P99 TTFT and P99 TPOT meet fixed per-model bounds. Its attainment target is 99%, versus the 90% modal academic value. (2) vLLM and GenAI-Perf "goodput" is a different quantity from the academic modal one: it is the measured good-request rate at one offered load, not a maximum rate subject to an attainment threshold. The vLLM help text nevertheless cites DistServe. (3) TPOT is aligned everywhere; ITL is the term that diverges (per-gap in vLLM/SGLang, per-response in GenAI-Perf, equal to TPOT in NIM/AIPerf). (4) Throughput token counting differs: MLPerf and GenAI-Perf count output tokens; vLLM/SGLang report both output-only and total.
