#!/usr/bin/env python3
"""Deck data file D7 metric_trends.json from scripts/metric_trends.py output + composition and robustness rows.
Usage: python3 -I make_metric_trends_data.py <project>"""
import json, sys, os, glob, collections
P = sys.argv[1].rstrip("/") + "/"
mt = json.load(open(P + "analysis/metric_trends.json"))
src = open(P + "scripts/analysis_v3.py").read(); sys.argv = ["x", P]; ns = {}
exec(src[:src.index("N = len(recs)")], ns)
exec("import math\n" + src[src.index("def wilson"):src.index('p(f"# summary_v3')], ns)
exec(src[src.index("def cochran_armitage"):src.index("onl=[r for r")], ns)
recs, famc, yb, CA, OV, wilson = ns["recs"], ns["famc"], ns["yb"], ns["cochran_armitage"], ns["OV"], ns["wilson"]
B = ("2022-23", "2024", "2025-26")
rows = [dict(r, src="records", loc="analysis/metric_trends.txt", tag="D", unc="exact count; Wilson 95 % CI", note="") for r in mt["rows"]]
for t in mt["tests"]:
    rows.append(dict(row_id=t["row_id"], subset=t["subset"], family=t["family"], role=t["role"], z=t["z"], p=t["p"], p_holm=t["p_holm"],
                     src="records", loc="analysis/metric_trends.txt", tag="D", unc="Cochran–Armitage two-sided, scores 0/1/2; Holm over 11 families", note=""))
MODEL = {"KV-compression", "quantization/sparsity/model-compression", "speculative/decoding-algorithm", "kernels/attention", "parallelism/offloading/hardware-mapping"}
for b in B:
    g = [r for r in recs if yb(r["_year"]) == b]; k = sum(1 for r in g if r.get("layer") in MODEL); lo, hi = wilson(k, len(g))
    rows.append(dict(row_id=f"composition|model_side_layers|{b}", period=b, k=k, n=len(g), pct=100 * k / len(g), ci_lo=round(lo, 1), ci_hi=round(hi, 1),
                     src="records", loc="layer field", tag="D", unc="exact count", note="layers: " + ", ".join(sorted(MODEL))))
    g2 = [r for r in recs if yb(r["_year"]) == b and r.get("load_class") in ("online-arrivals", "mixed")]
    rows.append(dict(row_id=f"composition|online_mixed|{b}", period=b, k=len(g2), n=len(g), pct=100 * len(g2) / len(g), src="records", loc="load_class", tag="D", unc="exact count", note=""))
ab = []
for f in glob.glob(P + "records/*.json"):
    r = json.load(open(f))
    if r.get("read_level") == "abstract":
        r["_year"] = 2000 + int(r["key"][6:8]) if r["key"].startswith("arxiv_") else int(r.get("year") or 0); ab.append(r)
S = recs + ab
for fam in ("first-token", "token-pace", "request-latency", "throughput", "slo-goodput", "program-latency", "single-seq-speed", "memory", "quality", "cost-energy", "hw-efficiency"):
    cs = []
    for b in B:
        g = [r for r in S if yb(r["_year"]) == b]
        k = sum(1 for r in g if any(famc(OV.get((r["key"], m["metric"]), m["metric"])) == fam for m in r["optimized_metrics"])); cs.append((k, len(g)))
        rows.append(dict(row_id=f"full_plus_abstract|{fam}|either|{b}", family=fam, period=b, k=k, n=len(g), pct=100 * k / len(g), src="records",
                         loc="full + abstract records", tag="D", unc="exact count (abstract coding lower confidence)", note=""))
    z, p = CA(cs); rows.append(dict(row_id=f"full_plus_abstract|{fam}|either|trend", z=round(z, 2), p=p, src="records", loc="", tag="D", unc="Cochran–Armitage, unadjusted", note=""))
env = {"id": "metric_trends", "version": 1, "slides": ["s10"], "title": "Share of papers targeting each metric family, by first-arXiv period",
       "units": {"k": "papers", "pct": "% of papers in the period"},
       "conventions": "role 'either' = metric family is an objective or a constraint of the method; 'objective' only = designed to improve; periods by first arXiv version (2022-23, 2024, 2025-26); subsets: all 137 full-text optimizers; online_mixed = evaluated under online request arrivals (77); full_plus_abstract adds 55 abstract-coded papers",
       "sources": {"records": {"cite": "per-paper records", "path": "records/", "locator": "scripts/metric_trends.py", "tag": "D"}},
       "rows": rows, "extraction": {"agent_a": "orchestrator scripts (scripts/metric_trends.py, deck/build/make_metric_trends_data.py)", "agent_b": "", "method": "deterministic script", "cross_check": {}},
       "caveats": ["purposive sample", "2022-23 online subset n = 8", "no 2025-26 compression paper read in full: model-side layers fall 56 % -> 37 % -> 17 % of full-text papers", "abstracts rarely state constraints"]}
json.dump(env, open(P + "deck/data/metric_trends.json", "w"), indent=1)
print("rows", len(rows))
