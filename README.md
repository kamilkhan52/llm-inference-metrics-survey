# What do LLM inference-optimization papers optimize?

A full-text survey of **137 LLM inference-optimization papers** (2022–2026) plus **10 metric/benchmark papers**. For each
paper it records which metric(s) the method is *designed to optimize*, which it only *constrains* or *reports*, and how it
*defines* them. It also derives a metric taxonomy (TTFT, TPOT, TBT/ITL, E2E, throughput, goodput, SLO attainment, and
more) from the papers' own definitions. A bonus track codes 55 more papers from their abstracts only.

- **Slides (14):** `deck/deck.html`. Open it in a browser; arrow keys move between slides, P starts presenter mode.
- **Report:** `report/report.html`, the long-form companion with every figure, table and reference.
- **Synthesis (Markdown):** `SYNTHESIS_v6.md`.

## Headline findings

All counts are over the 137 full-text optimizer papers unless stated. See the synthesis for confidence intervals and
scope.

- **Throughput is the most common objective** (42 %). Only 20 of those 57 papers also state a latency constraint.
- **Token pace and quality are mostly constraints.** TPOT/TBT is a constraint in 19 % of papers and an objective in 6 %.
  Quality is a constraint in 26 % and an objective in 2 %.
- **44 % of papers never evaluate under online request arrivals.** Their speed-ups are batch-1 or fixed-batch numbers.
  For example, EAGLE-3's "up to 6.5×" is a single-sequence speed-up, while its SGLang throughput gain falls from 1.81× at
  batch 2 to 1.38× at batch 64.
- **Tails are rarely the quantity minimized.**
  - Only 2 papers minimize a latency percentile: GORGO (−p95 TTFT) and Autellix. Three more name a tail as a design aim.
  - Among papers evaluated under online load, 42 % instead set distributional SLOs: percentile SLOs, goodput or
    attainment at X %, or per-token deadlines. Many of these are attainment targets on per-request *mean* TPOT.
- **The same metric name means different quantities.**
  - TTFT is timed from arrival in 16 papers and as prefill time only in 15; about 20 don't say.
  - Goodput has at least 8 definitions.
  - Throughput counts input+output, output-only, decode-only or prefill-only tokens, or doesn't say.
  - 28 % of papers never define their headline metric.
  - Benchmark harnesses (MLPerf, vLLM, GenAI-Perf) agree that TTFT includes queueing, but disagree on ITL, which
    tokens throughput counts, and goodput.
- **Change over time.** Within papers evaluated under online load, SLO framing is flat. What declined significantly
  (p < 0.001) is defining capacity as "the max rate before latency blows up". Goodput as an objective rose, but not
  significantly.
- **Mean metrics hide stalls.** In Etalon's Llama-3-8B/H100 setup, the capacity ranking of vLLM and Sarathi-Serve flips
  depending on whether you use TPOT, P99 TBT or fluidity.

## Method

1. **Discovery.** Six agents searched Semantic Scholar, OpenAlex, the arXiv API and the web by technique area, and
   checked every arXiv ID against its title. This gave 210 unique candidates (`candidates/`, `discovery/`).
2. **Selection.** The sample is purposive, not random (`SELECTION.tsv`):
   - 133 optimizers read in full, plus 4 routing and scheduling papers added during review;
   - 10 metric/benchmark papers read in full;
   - 60 papers on an abstract-only track (55 usable);
   - 7 non-optimizers excluded.
3. **Extraction.** One JSON record per paper (`records/`, schema in `SCHEMA.md`). Every objective or constraint carries
   a verbatim *design* quote with a locator, and every metric definition is copied verbatim. A validator is at
   `scripts/validate_record.py`.
4. **Quality control** (`qa/`):
   - **Blind second extraction** of 30 papers: the primary objective matched in 28 of 30.
   - **Blind second coding of tail tiers** for 30 papers: 25 of 30 matched (κ = 0.76).
   - **Audit of every paper with a tail statistic** (40 papers).
   - **Re-pass of all records** to separate design quotes from headline results.
   - **Script check of quotes** against the full texts.
5. **Analysis.** Counts are made at the level of metric *families*.
   - Scripts: `scripts/aggregate.py`, `scripts/analysis_v3.py`, `deck/build/make_records_data.py`.
   - Outputs: `analysis/` (`PAPER_TABLE.md`, `paper_table.csv`, `summary_v2.txt`, `summary_v3.txt`).
   - The definition taxonomy is in `notes/DEFINITIONS.md` and benchmark-harness definitions are in
     `notes/INDUSTRY_DEFS.md`.
6. **Review.** The synthesis went through five adversarial review rounds, the deck four, and the report five.

The work was done with LLM agents (Claude) orchestrated over the full texts. The prompts are included
(`EXTRACTION_PROMPT_COMMON.md`, `discovery/DISCOVERY_PROMPT_COMMON.md`, `qa/*_PROMPT.md`).

## Reproducing the numbers

```bash
python3 -I scripts/aggregate.py .        # -> analysis/summary.txt, summary_v2.txt, paper_table.json, definitions_by_metric.md
python3 -I scripts/analysis_v3.py .      # -> analysis/summary_v3.txt (tiers, trends with Wilson CIs, trend tests)
python3 -I scripts/paper_table_md.py .   # -> analysis/PAPER_TABLE.md, paper_table.csv
python3 -I deck/build/make_records_data.py .   # -> deck/data/*.json (records-derived figure data)
```

## What is not included

- **Paper full texts** (PDFs and text extractions) are not redistributed. Each record links to its arXiv page or
  venue, and the scripts expect them under `fulltext/arxiv_<id>.pdf|.txt` if you fetch them yourself.
- **Internal working files** are left out: agent logs, review drafts, and a section on the authors' own unpublished
  work. Some figure footers cite these internal files as locators.

## Caveats

- The sample is purposive, so shares describe this corpus, not the whole field.
- Coding was done by LLM agents with blind spot-checks. Constraint coding is noisier than objective coding.
- Paper venue strings come from discovery metadata and are not used in any count.
