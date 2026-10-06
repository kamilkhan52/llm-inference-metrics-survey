# Blind QA re-extraction (Q1..Q3)

You are a BLIND second extractor in a literature survey. Project: ./.
Read SCHEMA.md and EXTRACTION_PROMPT_COMMON.md there and follow them, with these differences:
- DO NOT open, list or grep anything under records/ or notes/ (another agent already extracted these papers; your
  job is an independent second reading so we can measure agreement). Do not read qa/records/ files other than
  your own.
- Write your records to qa/records/<key>.json (not records/). Validate with
  python3 -I scripts/validate_record.py qa/records/<key>.json
- Full texts are in fulltext/arxiv_<id>.txt (already downloaded).
- Focus effort on the fields that matter for agreement: optimized_metrics (code, stat, role, quote, locator),
  headline_claim, metric_definitions, load_regime, eval_type. reported_metrics can be brief.
Return (<= 200 words): one line per paper "key | objective codes@stat ; constraint codes@stat", plus any paper
where you found it genuinely ambiguous which metric is the objective (say why).
