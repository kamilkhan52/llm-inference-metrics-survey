# Per-paper record schema and preliminary metric vocabulary

Every surveyed paper gets one JSON file: `records/<key>.json`, where `<key>` is `arxiv_<id>` (e.g.
`arxiv_2309.06180`) or `<venue><year>_<shortname>` when there is no arXiv version.

## JSON fields

```json
{
  "key": "arxiv_2309.06180",
  "title": "...",
  "first_author": "...",
  "year": 2023,
  "venue": "SOSP'23 (or arXiv preprint)",
  "url": "https://arxiv.org/abs/2309.06180",
  "cluster": "D1..D6 (see discovery clusters)",
  "technique": "one line: what the method changes (e.g. 'paged KV memory + continuous batching')",
  "layer": "one of: request-scheduling | cluster-routing/placement | PD-disaggregation | KV-memory | KV-compression | prefix/context-caching | speculative/decoding-algorithm | quantization/sparsity/model-compression | kernels/attention | parallelism/offloading/hardware-mapping | agent/compound-serving | energy/cost | MoE-serving | LoRA/multi-model | long-context | other",
  "read_level": "full | abstract",
  "fulltext_path": "fulltext/arxiv_2309.06180.txt  (null if abstract only)",

  "optimized_metrics": [
    {"metric": "<canonical code>", "stat": "mean|P50|P90|P95|P99|max|attainment|n/a",
     "role": "objective | constraint",
     "evidence": "verbatim quote that shows this is what the method targets (problem statement, objective, design goal, abstract claim)",
     "locator": "§3.1 / p.4 / abstract / txt line N"}
  ],
  "headline_claim": {"text": "verbatim headline result, usually from abstract", "metrics": ["<codes>"], "locator": "..."},
  "reported_metrics": [
    {"metric": "<canonical code>", "stat": "...", "where": "Fig 7 / Table 3"}
  ],
  "metric_definitions": [
    {"term_as_written": "TBT", "canonical": "TBT", "definition_quote": "verbatim definition from the paper",
     "locator": "...", "notes": "e.g. TTFT includes queueing delay; throughput counts output tokens only"}
  ],
  "slo_spec": "how SLOs are set, if any (thresholds, scaling factors, attainment target), else null",
  "load_regime": "how load is varied: fixed batch size | request-rate sweep | trace replay | offline batch | batch=1",
  "tradeoff_acknowledged": "what metric the paper says gets worse, or null",
  "eval_type": "real-system | simulation | both | analytical",
  "hardware": "...", "models": "...", "workloads": "...",
  "confidence": "high | medium | low",
  "extractor_notes": "anything ambiguous, e.g. 'abstract says latency but eval only reports normalized latency'"
}
```

Rules:
- `optimized_metrics` = what the METHOD is designed to improve (objective) or must respect (constraint).
  Read it from the problem formulation, design goals, objective function and abstract, not from the
  set of plotted metrics. `reported_metrics` = everything evaluated.
- Every `optimized_metrics` entry needs a verbatim quote + locator. No quote, no entry.
- Use the paper's own term in `term_as_written`, map it to a canonical code. If a paper defines a
  metric, copy the definition verbatim; these quotes build the survey's definitions table.
- If no code fits, use `OTHER:<short_name>` and define it in `metric_definitions`.
- `read_level: abstract` only when the full text cannot be obtained; then confidence is at most medium.

## Preliminary canonical metric codes (extend with OTHER:<name> when needed)

| Code | Meaning (preliminary — the survey refines these) |
|---|---|
| TTFT | time to first token (note whether it includes queueing) |
| TPOT | time per output token, averaged over a request's decode tokens (excl. first) |
| TBT | time between consecutive tokens / inter-token latency (ITL), token-level distribution |
| E2E | end-to-end request latency (= TTLT, JCT for a single request, completion time) |
| NORM_LAT | normalized latency: request latency / output (or total) length, s/token |
| TOKEN_LAT | per-token latency of a single sequence (batch=1 decoding speed), incl. wall-clock speedup |
| THR_TOK | system throughput in tokens/s (state input+output vs output-only, per GPU or total) |
| THR_REQ | throughput in requests/s, or max sustainable request rate / capacity |
| TPS_USER | per-user (per-stream) token rate, tokens/s/user (~ 1/TPOT) |
| GOODPUT | throughput counting only SLO-meeting work (rate at X% attainment, or SLO-meeting tokens/s) |
| SLO_ATT | fraction of requests meeting SLO(s) |
| QUEUE | queueing / scheduling delay |
| COST | $ per token / per request, $/hr, number of GPUs, resource usage |
| ENERGY | energy per token/request, power, carbon |
| MEMORY | memory footprint, KV capacity, achievable batch size, fragmentation |
| QUALITY | accuracy / perplexity / task score (usually a constraint for lossy methods) |
| FAIRNESS | fairness across users/tenants (e.g. service counters) |
| QOE | user-perceived quality of experience defined over the token-delivery timeline |
| PROGRAM_JCT | completion time of a multi-call program / agent / workflow |
| ACCEPT | speculative-decoding acceptance rate / mean accepted length |
| UTIL | hardware utilization (MFU, bandwidth utilization, GPU busy %) |
| PREEMPT | preemption / recomputation / swap counts or overheads |
| OTHER:<name> | anything else |

## Discovery clusters

| Cluster | Scope |
|---|---|
| D1 | Within-replica request scheduling, batching, preemption, fairness, SLO-aware and length-aware scheduling |
| D2 | Cluster level: prefill/decode disaggregation, routing/load balancing, autoscaling, placement, heterogeneous/spot/cost-efficient serving, multi-model & LoRA serving, energy/power |
| D3 | KV cache: paged/virtual memory, prefix/context caching, KV offload/tiering/transfer, KV compression/eviction/quantization, long-context serving |
| D4 | Decoding algorithms: speculative decoding (incl. serving-aware), parallel/lookahead decoding, early exit; model compression for inference (weight/activation/KV quantization, sparsity), MoE inference |
| D5 | Kernels, runtimes, parallelism and hardware mapping: attention kernels, fused/overlapped execution, tensor/pipeline/sequence parallel inference, offloading (CPU/SSD), on-device/edge, heterogeneous hardware, compilers |
| D6 | Agentic / compound / multi-call / reasoning-model serving, structured generation, and serving benchmarks/metric papers (papers that propose or critique serving metrics) |
