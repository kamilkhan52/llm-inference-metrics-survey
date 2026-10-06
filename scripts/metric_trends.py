#!/usr/bin/env python3
"""Per-metric-family trends by first-arXiv year bucket: objective / constraint / either shares with Wilson CIs and
Cochran-Armitage trend tests (Holm-adjusted), for all full-text optimizers and the online/mixed-load subset.
Usage: python3 -I metric_trends.py <project>  -> analysis/metric_trends.txt and analysis/metric_trends.json"""
import json, os, sys, math, collections
P = sys.argv[1].rstrip("/") + "/"
src = open(P + "scripts/analysis_v3.py").read()
sys.argv = ["x", P]; ns = {}
exec(src[:src.index("N = len(recs)")], ns)
exec("import math\n" + src[src.index("def wilson"):src.index("def yb(y)")], ns)
exec(src[src.index("def yb(y)"):src.index('p(f"# summary_v3')], ns)
exec(src[src.index("def cochran_armitage"):src.index("onl=[r for r")], ns)
recs, famc, wilson, yb, CA = ns["recs"], ns["famc"], ns["wilson"], ns["yb"], ns["cochran_armitage"]
FAMS = ["first-token", "token-pace", "request-latency", "program-latency", "single-seq-speed", "throughput",
        "slo-goodput", "cost-energy", "memory", "hw-efficiency", "quality"]
LABEL = {"first-token": "TTFT", "token-pace": "TPOT / TBT / TPS-per-user", "request-latency": "E2E (TTLT), normalized, queueing",
         "program-latency": "program / workflow JCT", "single-seq-speed": "single-sequence decode speed",
         "throughput": "throughput (tokens/s, req/s)", "slo-goodput": "goodput / SLO attainment", "cost-energy": "cost / energy",
         "memory": "memory", "hw-efficiency": "hardware efficiency", "quality": "quality"}
B = ("2022-23", "2024", "2025-26")
def roles(r, f):
    o = any(famc(m["metric"]) == f and m["role"] == "objective" for m in r["optimized_metrics"])
    c = any(famc(m["metric"]) == f and m["role"] == "constraint" for m in r["optimized_metrics"])
    return o, c
MODEL = {"KV-compression", "quantization/sparsity/model-compression", "speculative/decoding-algorithm", "kernels/attention", "parallelism/offloading/hardware-mapping"}
subsets = {"all": recs, "online_mixed": [r for r in recs if r.get("load_class") in ("online-arrivals", "mixed")],
           "system_layers": [r for r in recs if r.get("layer") not in MODEL]}
rows = []; tests = []
for sname, S in subsets.items():
    for f in FAMS:
        for role in ("objective", "constraint", "either"):
            cs = []
            for b in B:
                g = [r for r in S if yb(r["_year"]) == b]; n = len(g)
                k = sum(1 for r in g if (lambda o, c: {"objective": o, "constraint": c, "either": o or c}[role])(*roles(r, f)))
                lo, hi = wilson(k, n); cs.append((k, n))
                rows.append(dict(row_id=f"{sname}|{f}|{role}|{b}", subset=sname, family=f, label=LABEL[f], role=role, period=b,
                                 k=k, n=n, pct=100 * k / n, ci_lo=round(lo, 1), ci_hi=round(hi, 1)))
            z, p = CA(cs); tests.append(dict(row_id=f"{sname}|{f}|{role}|trend", subset=sname, family=f, role=role, z=round(z, 2), p=p,
                                              first=cs[0], last=cs[-1]))
# Holm correction within each subset x role (11 families)
for sname in subsets:
    for role in ("objective", "constraint", "either"):
        T = sorted([t for t in tests if t["subset"] == sname and t["role"] == role], key=lambda t: t["p"]); m = len(T); prev = 0
        for i, t in enumerate(T):
            adj = min(1.0, max(prev, (m - i) * t["p"])); t["p_holm"] = adj; prev = adj
out = []
for sname in subsets:
    out.append(f"\n## {sname} (n per period: " + ", ".join(str(len([r for r in subsets[sname] if yb(r['_year']) == b])) for b in B) + ")")
    for role in ("objective", "either"):
        out.append(f"  role={role}")
        for f in FAMS:
            rr = [r for r in rows if r["subset"] == sname and r["family"] == f and r["role"] == role]
            t = [t for t in tests if t["subset"] == sname and t["family"] == f and t["role"] == role][0]
            out.append(f"   {f:18s} " + "  ".join(f"{r['k']:2d}/{r['n']:2d}={r['pct']:4.0f}%" for r in rr) + f"   z={t['z']:+.2f} p={t['p']:.3f} holm={t['p_holm']:.3f}")
open(P + "analysis/metric_trends.txt", "w").write("\n".join(out) + "\n")
json.dump({"rows": rows, "tests": tests}, open(P + "analysis/metric_trends.json", "w"), indent=1)
print("\n".join(out))
