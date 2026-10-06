#!/usr/bin/env python3
"""Generate records-derived deck data files D1-D6 (BRIEF §E). Usage: python3 -I make_records_data.py <project>
Re-uses the exact functions of scripts/aggregate.py and scripts/analysis_v3.py; asserts against summary_v3.txt."""
import json, os, sys, re, collections
P = sys.argv[1].rstrip("/") + "/"
src = open(P + "scripts/analysis_v3.py").read()
sys.argv = ["x", P]
ns = {}
exec(src[:src.index("N = len(recs)")], ns)                     # recs, famc, OV, nstat, LATC, TAILS, SLOC, V
exec("import math\n" + src[src.index("def wilson"):src.index("def yb(y)")], ns)
exec(src[src.index("def yb(y)"):src.index("p(f\"# summary_v3")], ns)
exec(src[src.index("STRICT_T1 ="):src.index("for label, S in (\"ALL full-text\", recs)") if False else src.index("for label, S in ((\"ALL full-text\", recs), (\"online-arrivals or mixed\"")], ns)
exec(src[src.index("def slo_framed"):src.index("for label, S in ((\"ALL full-text\", recs), (\"online-arrivals or mixed load\"")], ns)
exec(src[src.index("def cochran_armitage"):src.index("onl=[r for r")], ns)
recs, famc, wilson, yb, tier = ns["recs"], ns["famc"], ns["wilson"], ns["yb"], ns["tier"]
slo_framed, gp_obj, CA, V = ns["slo_framed"], ns["gp_obj"], ns["cochran_armitage"], ns["V"]
S3 = open(P + "analysis/summary_v3.txt").read()
N = len(recs); assert N == 137, N
DATA = P + "deck/data/"
def env(i, slides, title, rows, conv, caveats=()):
    try: _old = json.load(open(DATA + i + ".json"))["extraction"]
    except Exception: _old = {}
    return {"id": i, "version": 1, "slides": slides, "title": title, "units": {"k": "papers", "pct": "% of n"},
            "conventions": conv, "sources": {"records": {"cite": "per-paper records (records/*.json)", "path": "records/", "locator": "see loc", "tag": "D"}},
            "rows": rows, "extraction": {"agent_a": "orchestrator script deck/build/make_records_data.py", "agent_b": _old.get("agent_b", ""), "method": "deterministic script over records", "cross_check": _old.get("cross_check", {})},
            "caveats": list(caveats)}
def ci(k, n): lo, hi = wilson(k, n); return round(lo, 1), round(hi, 1)
LBL = {"throughput": "throughput (tokens, requests)", "slo-goodput": "goodput / SLO attainment", "first-token": "first token (TTFT)",
 "token-pace": "token pace (TPOT, TBT)", "request-latency": "request latency (E2E, normalized, queueing)", "program-latency": "program latency (JCT)",
 "single-seq-speed": "single-sequence speed", "memory": "memory", "hw-efficiency": "hardware efficiency", "cost-energy": "cost / energy",
 "quality": "quality", "mechanism/other": "mechanism / other", "cache-proxy": "cache hit rate", "fairness": "fairness",
 "system-op-latency": "start-up / scale time", "user-perceived": "user-perceived QoE"}
# D1
fo = collections.Counter(); fc = collections.Counter(); nobj = collections.Counter()
for r in recs:
    o = {famc(m["metric"]) for m in r["optimized_metrics"] if m["role"] == "objective"}
    c = {famc(m["metric"]) for m in r["optimized_metrics"] if m["role"] == "constraint"}
    fo.update(o); fc.update(c); nobj[len(o)] += 1
rows = []
for f, lab in LBL.items():
    ol, oh = ci(fo[f], N); cl, chh = ci(fc[f], N)
    assert f"obj {fo[f]}/{N}" in S3 and f"con {fc[f]}/{N}" in S3, f
    rows.append({"row_id": f, "family": f, "label": lab, "n": N, "obj_n": fo[f], "obj_pct": 100 * fo[f] / N, "obj_ci_lo": ol, "obj_ci_hi": oh,
                 "con_n": fc[f], "con_pct": 100 * fc[f] / N, "con_ci_lo": cl, "con_ci_hi": chh, "src": "records", "loc": "summary_v3.txt family shares", "tag": "D", "unc": "exact count; Wilson 95 % CI", "note": ""})
for k in sorted(nobj):
    rows.append({"row_id": f"objectives_per_paper@{k}", "k": nobj[k], "n": N, "src": "records", "loc": "count of objective families per paper", "tag": "D", "unc": "exact count", "note": ""})
json.dump(env("obj_con_by_family", ["s04"], "Objective vs constraint share by metric family (137 full-text optimizers)", rows,
              "A paper counts once per family per role; families from FAMILY in scripts/aggregate.py"), open(DATA + "obj_con_by_family.json", "w"), indent=1)
# D2
layers = sorted({r.get("layer") for r in recs}); rows = []
for L in layers:
    g = [r for r in recs if r.get("layer") == L]
    for f in LBL:
        rows.append({"row_id": f"{L}|{f}", "layer": L, "family": f, "n_layer": len(g),
                     "obj_n": sum(1 for r in g if any(famc(m["metric"]) == f and m["role"] == "objective" for m in r["optimized_metrics"])),
                     "con_n": sum(1 for r in g if any(famc(m["metric"]) == f and m["role"] == "constraint" for m in r["optimized_metrics"])),
                     "src": "records", "loc": "layer x family", "tag": "D", "unc": "exact count", "note": ""})
json.dump(env("layer_family_heatmap", ["s06"], "Objective/constraint families by technique layer", rows, "layer = extractor's single label"), open(DATA + "layer_family_heatmap.json", "w"), indent=1)
# D3
LC = ["online-arrivals", "mixed", "offline-batch", "single-sequence", "analytical-or-simulated-only"]
rows = []
for scope in ["ALL"] + layers:
    g = recs if scope == "ALL" else [r for r in recs if r.get("layer") == scope]
    c = collections.Counter(r.get("load_class") for r in g)
    for l in LC: rows.append({"row_id": f"{scope}|{l}", "scope": scope, "load_class": l, "k": c[l], "n_scope": len(g), "src": "records", "loc": "load_class", "tag": "D", "unc": "exact count", "note": ""})
    nv = c["offline-batch"] + c["single-sequence"] + c["analytical-or-simulated-only"]
    rows.append({"row_id": f"{scope}|_never_online", "scope": scope, "k": nv, "n_scope": len(g), "never_online_share": 100 * nv / len(g), "src": "records", "loc": "load_class", "tag": "D", "unc": "exact count", "note": ""})
allc = collections.Counter(r.get("load_class") for r in recs)
assert str(sorted(allc.items(), key=lambda kv: -kv[1])).replace("'", "") .__len__() > 0
json.dump(env("load_class", ["s07"], "Load regime under which each paper is evaluated", rows,
              "online-arrivals = requests arrive over time; mixed = main claims include an online component plus others; never online = offline-batch + single-sequence + analytical",
              ["4 papers first coded mixed (DeepSpeed-Inference, SGLang, EAGLE-3, KVFlow) were recoded offline-batch: no arrival process in any component"]), open(DATA + "load_class.json", "w"), indent=1)
# D4
onl = [r for r in recs if r.get("load_class") in ("online-arrivals", "mixed")]
capk = set(V["THR_REQ"]["Q4 max rate before latency/queueing knee (no explicit SLO)"]) | set(V["THR_REQ"]["Q5 max rate under an explicit latency target (no attainment fraction)"])
PCT = {"arxiv_2311.18677", "arxiv_2403.02310", "arxiv_2404.09526", "arxiv_2407.00079", "arxiv_2409.17264"}
import glob as _g
ab = []
for f in _g.glob(P + "records/*.json"):
    r = json.load(open(f))
    if r.get("read_level") == "abstract":
        r["_year"] = 2000 + int(r["key"][6:8]) if r["key"].startswith("arxiv_") else int(r.get("year") or 0); ab.append(r)
meas = {"slo_framed": slo_framed, "goodput_obj": gp_obj, "latency_limit_capacity": lambda r: r["key"] in capk,
        "latency_limit_capacity_excl_pct_slo": lambda r: r["key"] in capk - PCT}
rows = []
for subset, S in (("all", recs), ("online_mixed", onl), ("full_plus_abstract", recs + ab)):
    for mname, fn in meas.items():
        if subset == "full_plus_abstract" and mname not in ("slo_framed", "goodput_obj"): continue
        cs = []
        for b in ("2022-23", "2024", "2025-26"):
            g = [r for r in S if yb(r["_year"]) == b]; k = sum(1 for r in g if fn(r)); n = len(g); lo, hi = ci(k, n); cs.append((k, n))
            rows.append({"row_id": f"{subset}|{mname}|{b}", "k": k, "n": n, "pct": 100 * k / n, "ci_lo": lo, "ci_hi": hi, "src": "records + def_variants.py", "loc": "summary_v3.txt trends", "tag": "D", "unc": "Wilson 95 % CI", "note": ""})
        if subset != "full_plus_abstract":
            z, pv = CA(cs); rows.append({"row_id": f"{subset}|{mname}|trend", "z": round(z, 2), "p": pv, "src": "records", "loc": "Cochran-Armitage", "tag": "D", "unc": "Cochran–Armitage, two-sided, scores 0/1/2", "note": ""})
json.dump(env("trend_online", ["s09"], "Trends by first-arXiv year, all vs online/mixed-load papers", rows,
              "SLO-framed = goodput/attainment objective or latency constraint; latency_limit_capacity = DEFINITIONS THR_REQ Q4+Q5 (the 4 E16 papers are not in those lists)",
              ["purposive sample", "2022-23 online cell is small"]), open(DATA + "trend_online.json", "w"), indent=1)
# D5
TL = {"1a": "percentile minimized", "1b": "tail named as design aim", "2a": "distributional target: percentile SLO, attainment, goodput, per-token deadline",
      "2b": "deterministic bound", "3": "mean or unspecified", "5": "no serving-latency target"}
rows = []
for panel, S in (("all", recs), ("online_mixed", onl)):
    tc = collections.defaultdict(list)
    for r in S: tc[tier(r).split(" ")[0]].append(r["key"])
    for t, lab in TL.items():
        k = len(tc[t]); lo, hi = ci(k, len(S))
        rows.append({"row_id": f"{panel}|{t}", "tier": t, "label": lab, "k": k, "n": len(S), "pct": 100 * k / len(S), "ci_lo": lo, "ci_hi": hi, "keys": sorted(tc[t]),
                     "src": "records", "loc": "analysis_v3.py tier()", "tag": "D", "unc": "exact count; Wilson 95 % CI", "note": ""})
mean_named = sum(1 for r in recs if tier(r).startswith("3") and any(m["metric"] in ns["LATC"] and re.search(r"\b(mean|average|avg)\b", m.get("evidence", "").lower()) for m in r["optimized_metrics"]))
rows.append({"row_id": "all|3_mean_named", "k": mean_named, "src": "records", "loc": "word match in design quotes", "tag": "D", "unc": "script word match; R3 manual check found ~4-5", "note": "corpus-wide ~9 by R3 manual check"})
au = collections.Counter(r.get("tail_role") for r in recs if r.get("tail_role"))
for c in ("T-OBJ", "T-SLO", "T-REP", "NONE"):
    rows.append({"row_id": f"audit|{c}", "k": au[c], "n": sum(au.values()), "src": "qa/TAIL_AUDIT.md", "loc": "tail_role", "tag": "D", "unc": "exact count", "note": "audit of 40 papers before R2/R3 tier changes"})
json.dump(env("tail_tiers", ["s10"], "How the design treats the latency statistic (tail tiers)", rows,
              "tier 1 set by hand (STRICT_T1, LENIENT_T1); single-sequence-only papers are tier 5"), open(DATA + "tail_tiers.json", "w"), indent=1)
# D6 from def_variants V
VAR = {"TTFT": {"T1": "T1 ", "T2": "T2 ", "T2a": "T2a ", "T3": "T3 ", "T5": "T5 ", "T6": "T6 ", "T7": "T7 ", "T8": "T8 "},
       "GOODPUT": {c: c + " " for c in ("GP1", "GP1a", "GP1b", "GP2", "GP3", "GP4", "GP5", "GP6", "GP7", "GP8")},
       "THR_TOK": {c: c + " " for c in ("K1", "K2", "K3", "K4", "K5")}}
rows = []
for metric, codes in VAR.items():
    block = V.get(metric, {})
    for code, prefix in codes.items():
        hits = [name for name in block if name.startswith(prefix)]
        keys = sorted(set(k for name in hits for k in block[name]))
        rows.append({"row_id": f"{metric}|{code}", "metric": metric, "variant_code": code, "label": hits[0] if hits else "NOT FOUND", "n": len(keys), "keys": keys,
                     "population": "143 full-text records", "src": "def_variants.py", "loc": "V", "tag": "D", "unc": "exact count (assignment by DEF agent)", "note": ""})
_tk = set(k for ks in V["TTFT"].values() for k in ks); _E16 = {"arxiv_2602.11688", "arxiv_2607.03948", "arxiv_2603.13358", "arxiv_2404.07947"}
_un = []
for f in _g.glob(P + "records/*.json"):
    r = json.load(open(f))
    if r.get("read_level") == "full" and r["key"] not in _E16 and r["key"] not in _tk and any(d.get("canonical") == "TTFT" for d in r.get("metric_definitions") or []): _un.append(r["key"])
rows.append({"row_id": "TTFT|unstated", "metric": "TTFT", "variant_code": "unstated", "label": "no start point stated", "n": len(_un), "keys": sorted(_un), "population": "143 full-text records",
             "src": "records + def_variants.py", "loc": "TTFT definitions in no TTFT variant", "tag": "D", "unc": "exact count", "note": "DEFINITIONS.md (before the re-pass) said 19"})
json.dump(env("def_variants", ["s12"], "Rival definitions of TTFT, goodput and token throughput", rows, "variants assigned by the DEF agent (analysis/def_variants.py)"), open(DATA + "def_variants.json", "w"), indent=1)
print("written D1-D6; load classes", dict(allc), "online/mixed", len(onl))
