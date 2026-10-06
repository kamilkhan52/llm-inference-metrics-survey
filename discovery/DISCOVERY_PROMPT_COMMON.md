# Common instructions for discovery agents (D1..D6)

Project: ./  (read SCHEMA.md there first: clusters + metric codes)
Overall study (context): a survey of ~100 LLM inference-optimization papers (2021-10 .. 2026-10, most from
2024-2026) recording, from full-text reads, WHICH METRIC(S) each paper optimizes (TTFT, TPOT/TBT, E2E,
throughput, goodput, SLO attainment, cost, energy, ...) and how it defines them. Your job is ONLY discovery
(abstract level): build a candidate list for your cluster. A later agent reads each full text.

Inclusion: the paper proposes a method/system/algorithm that makes generative LLM (decoder transformer)
inference faster/cheaper/more efficient/better-served and evaluates it. Peer-reviewed (OSDI, SOSP, NSDI,
EuroSys, ASPLOS, ISCA, MICRO, HPCA, SC, ATC, MLSys, ICML, NeurIPS, ICLR, ACL/EMNLP, SIGCOMM, FAST, VLDB ...)
or an arXiv preprint with real uptake (citations, a known group, or a widely used system). A full text must be
openly available (arXiv or author/USENIX/ACM open access) for it to be useful. Exclude training-only work,
pure surveys, and non-LLM models. Metric/benchmark/simulator papers that DEFINE or CRITIQUE serving metrics
are allowed only in D6.

Recency target for your list: >= 60 % from 2024-2026 and >= 30 % from 2025-2026. Include the canonical
older papers in your cluster too (they anchor the history).

Tools: use the Semantic Scholar Graph API
  https://api.semanticscholar.org/graph/v1/paper/search?query=<q>&fields=title,year,venue,citationCount,externalIds,abstract&limit=50
  (unauthenticated: ~1 request/s, back off on HTTP 429 with sleep 3-10 s; do not hammer),
OpenAlex https://api.openalex.org/works?search=<q>&per-page=50 , and the arXiv API http://export.arxiv.org/api/query?search_query=...
via curl from Bash, plus WebSearch/WebFetch. Verify every arXiv ID against the arXiv abstract page or API
(title must match). Never invent an ID; if you cannot verify it, put "unverified" in the note column.

Output 1: ./candidates/<CLUSTER>.tsv, tab-separated,
header exactly:
key	arxiv_id	title	first_author	year	venue	cluster	layer	citations	abstract_metric_guess	abstract_clear	note
- key = arxiv_<id> (e.g. arxiv_2309.06180) or <venue><year>_<name> if no arXiv version
- year = first public version year; venue = published venue+year if any, else "arXiv"
- layer = one value from SCHEMA.md "layer" list
- citations = Semantic Scholar or OpenAlex count (say which in note if OpenAlex), "" if unknown
- abstract_metric_guess = semicolon-separated canonical codes for what the abstract says is OPTIMIZED
  (e.g. "THR_TOK;TTFT"), using SCHEMA.md codes or OTHER:<name>
- abstract_clear = yes if the abstract alone states the optimized metric unambiguously with a number
  (e.g. "reduces P99 TTFT by 2.3x"), else no
Output 2: ./discovery/<CLUSTER>_abstracts.jsonl, one JSON
object per candidate: {"key":..., "title":..., "abstract": "<full abstract text verbatim>", "source": "s2|openalex|arxiv"}.
Save both files incrementally (after every ~10 candidates).

Target: 28-35 candidates for your cluster, best-known and most representative first, covering the sub-areas
of the cluster in balance. Do not include a paper clearly belonging to another cluster unless it is central to
yours (note "also Dn").
Return (<= 300 words): counts by year, sub-area coverage, any seeds you could not verify, and notable
2025-2026 additions. Keep it compact; I manage context.
