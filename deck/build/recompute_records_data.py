#!/usr/bin/env python3
"""Independent recompute (agent B) of the six records-derived deck data files -> deck/data/<id>.b.json.
Usage: python3 -I recompute_records_data.py <project>"""
import json, glob, os, sys, csv, math, re, collections
P = sys.argv[1]; D = os.path.join(P, "deck", "data")
# ---- definitions pulled from scripts (exec only the dicts) ----
src = open(os.path.join(P, "scripts/aggregate.py")).read()
ns = {}; exec(src[src.index("OVERRIDE ="):src.index("LATFAM")], ns)
FAMILY, OV = ns["FAMILY"], ns["OVERRIDE"]
C2F = {c: f for f, cs in FAMILY.items() for c in cs}
famc = lambda c: C2F.get(c, "mechanism/other")
def nstat(s):
    s = str(s or "n/a").strip()
    return {"P50": "median", "median": "median"}.get(s, s if s in ("mean","P90","P95","P97","P99","max","attainment") else "n/a")
dv = open(os.path.join(P, "analysis/def_variants.py")).read()
vns = {}; exec(dv[dv.index("def k("):dv.index("\nV = {")] + "\n" + dv[dv.index("V = {"):].split("\n}\n")[0] + "\n}\n", vns)
V = vns["V"]
sel = {r["key"]: r for r in csv.DictReader(open(os.path.join(P, "SELECTION.tsv")), delimiter="\t")}
def is_mp(r): return str(r.get("technique", "")).startswith("METRIC-PAPER") or sel.get(r["key"], {}).get("track") == "mp-full"
def year(r): return 2000 + int(r["key"][6:8]) if r["key"].startswith("arxiv_") else int(r.get("year") or 0)
allrecs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(P, "records/*.json")))]
for r in allrecs:
    for m in r.get("optimized_metrics", []) or []:
        m["metric"] = OV.get((r["key"], m["metric"]), m["metric"]); m["stat"] = nstat(m.get("stat"))
    r["_y"] = year(r)
recs = [r for r in allrecs if r.get("read_level") == "full" and not is_mp(r)]
absr = [r for r in allrecs if r.get("read_level") == "abstract"]
N = len(recs); assert N == 137, N
OM = lambda r: r.get("optimized_metrics") or []
def wil(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    ph = k/n; d = 1+z*z/n; c = (ph+z*z/(2*n))/d; h = z*math.sqrt(ph*(1-ph)/n+z*z/(4*n*n))/d
    return (round(100*(c-h), 1), round(100*(c+h), 1))
def ca(counts):
    ks=[c[0] for c in counts]; ns_=[c[1] for c in counts]; n=sum(ns_); pb=sum(ks)/n; sc=range(len(counts))
    T=sum(s*(k-m*pb) for s,k,m in zip(sc,ks,ns_)); sb=sum(s*m for s,m in zip(sc,ns_))/n
    v=pb*(1-pb)*sum(m*(s-sb)**2 for s,m in zip(sc,ns_)); z=T/math.sqrt(v) if v>0 else 0.0
    return z, math.erfc(abs(z)/math.sqrt(2))
FAMS = ["throughput","slo-goodput","first-token","token-pace","request-latency","program-latency","single-seq-speed","memory",
        "hw-efficiency","cost-energy","quality","mechanism/other","cache-proxy","fairness","system-op-latency","user-perceived"]
LAB = {"throughput":"throughput (tokens, requests)","slo-goodput":"goodput / SLO attainment","first-token":"first token (TTFT)",
 "token-pace":"token pace (TPOT, TBT)","request-latency":"request latency (E2E, normalized, queueing)","program-latency":"program latency (JCT)",
 "single-seq-speed":"single-sequence speed","memory":"memory","hw-efficiency":"hardware efficiency","cost-energy":"cost / energy",
 "quality":"quality","mechanism/other":"mechanism / other","cache-proxy":"cache hit rate","fairness":"fairness",
 "system-op-latency":"start-up / scale time","user-perceived":"user-perceived QoE"}
def fams(r, role): return {famc(m["metric"]) for m in OM(r) if m.get("role") == role}
out = {}
# ---- D1
rows = []
for f in FAMS:
    o = sum(f in fams(r, "objective") for r in recs); c = sum(f in fams(r, "constraint") for r in recs)
    ol, oh = wil(o, N); cl, ch = wil(c, N)
    rows.append(dict(row_id=f, family=f, label=LAB[f], n=N, obj_n=o, obj_pct=100*o/N, obj_ci_lo=ol, obj_ci_hi=oh,
                     con_n=c, con_pct=100*c/N, con_ci_lo=cl, con_ci_hi=ch))
cnt = collections.Counter(len(fams(r, "objective")) for r in recs)
for k in (1,2,3,4): rows.append(dict(row_id=f"objectives_per_paper@{k}", k=cnt[k]))
out["obj_con_by_family"] = rows
# ---- D2
layers = sorted({r["layer"] for r in recs}); assert len(layers) == 15, layers
rows = []
for L in layers:
    g = [r for r in recs if r["layer"] == L]
    for f in FAMS:
        rows.append({"row_id": f"{L}|{f}", "layer": L, "family": f, "n_layer": len(g),
            "obj_n": sum(f in fams(r, "objective") for r in g), "con_n": sum(f in fams(r, "constraint") for r in g)})
out["layer_family_heatmap"] = rows
# ---- D3
LC = ["online-arrivals","mixed","offline-batch","single-sequence","analytical-or-simulated-only"]
rows = []
for scope in ["ALL"] + layers:
    g = recs if scope == "ALL" else [r for r in recs if r["layer"] == scope]
    c = collections.Counter(r.get("load_class") for r in g)
    for l in LC: rows.append({"row_id": f"{scope}|{l}", "scope": scope, "load_class": l, "k": c[l], "n_scope": len(g)})
    nv = c["offline-batch"] + c["single-sequence"] + c["analytical-or-simulated-only"]
    rows.append({"row_id": f"{scope}|_never_online", "scope": scope, "load_class": "_never_online", "k": nv, "n_scope": len(g),
                 "never_online_share": 100*nv/len(g)})
# reviewer judgement (reads of the 14 mixed quotes): only arxiv_2405.16444 lacks a clear online-arrival statement
JUDG = {"arxiv_2405.16444": "unclear"}
for r in recs:
    if r.get("load_class") == "mixed" and r["key"] in JUDG:
        rows.append({"row_id": f"mixed_no_online|{r['key']}", "quote": (r.get("load_class_quote") or "")[:300], "judgement": JUDG[r["key"]]})
out["load_class"] = rows
# ---- D4
SLOC = {"GOODPUT","SLO_ATT","OTHER:smooth_goodput"}
def gp_obj(r): return any(m["metric"] in SLOC and m.get("role") == "objective" for m in OM(r))
def slo_f(r): return gp_obj(r) or any(m.get("role") == "constraint" and famc(m["metric"]) in ("first-token","token-pace","request-latency") for m in OM(r))
Q4 = [n for n in V["THR_REQ"] if n.startswith("Q4 ")][0]; Q5 = [n for n in V["THR_REQ"] if n.startswith("Q5 ")][0]
cap = set(V["THR_REQ"][Q4]) | set(V["THR_REQ"][Q5])
EXC = {"arxiv_2311.18677","arxiv_2403.02310","arxiv_2404.09526","arxiv_2407.00079","arxiv_2409.17264"}
bk = lambda y: "2022-23" if y <= 2023 else ("2024" if y == 2024 else "2025-26")
PER = ["2022-23","2024","2025-26"]
subsets = {"all": recs, "online_mixed": [r for r in recs if r.get("load_class") in ("online-arrivals","mixed")], "full_plus_abstract": recs + absr}
meas = {"slo_framed": slo_f, "goodput_obj": gp_obj, "latency_limit_capacity": lambda r: r["key"] in cap,
        "latency_limit_capacity_excl_pct_slo": lambda r: r["key"] in cap - EXC}
rows = []
for sn, S in subsets.items():
    for mn, fn in meas.items():
        if sn == "full_plus_abstract" and mn not in ("slo_framed", "goodput_obj"): continue
        if mn.endswith("excl_pct_slo") and sn != "online_mixed": continue
        cs = []
        for p in PER:
            g = [r for r in S if bk(r["_y"]) == p]; k = sum(map(fn, g)); n = len(g); cs.append((k, n)); lo, hi = wil(k, n)
            rows.append({"row_id": f"{sn}|{mn}|{p}", "k": k, "n": n, "pct": 100*k/n, "ci_lo": lo, "ci_hi": hi})
        if sn != "full_plus_abstract":
            z, pv = ca(cs); rows.append({"row_id": f"{sn}|{mn}|trend", "z": z, "p": pv})
out["trend_online"] = rows
# ---- D5
STRICT = {"arxiv_2602.11688","arxiv_2502.13965"}; LEN = {"arxiv_2407.00023","arxiv_2508.06948","arxiv_2507.17769"}
DET = {"arxiv_2504.02263","arxiv_2404.07947","arxiv_2306.06000","arxiv_2512.15705","arxiv_2310.07240"}
LATC = {"TTFT","TPOT","TBT","E2E","NORM_LAT","QUEUE","PROGRAM_JCT","TPS_USER"}; TAILS = {"P90","P95","P97","P99","max"}
def tier(r):
    om = OM(r); k = r["key"]
    if k in STRICT: return "1a"
    if k in LEN: return "1b"
    if r.get("load_class") == "single-sequence": return "5"
    if k in DET: return "2b"
    if any(m.get("role") == "constraint" and m["metric"] in LATC and m["stat"] in TAILS for m in om) or any(m["metric"] in SLOC for m in om) \
       or any(m["metric"] in LATC and m["stat"] == "attainment" for m in om) or any(m["metric"] in ("QOE","OTHER:fluidity_index","OTHER:user_idle_latency") for m in om): return "2a"
    if any(m["metric"] in LATC for m in om): return "3"
    return "5"
TL = {"1a":"percentile minimized","1b":"tail stated as aim","2a":"distributional target: percentile SLO, attainment, goodput, per-token deadline",
      "2b":"deterministic bound","3":"mean or unspecified","5":"no serving-latency target"}
rows = []
for pn, S in (("all", recs), ("online_mixed", subsets["online_mixed"])):
    for t in ["1a","1b","2a","2b","3","5"]:
        ks = [r["key"] for r in S if tier(r) == t]; lo, hi = wil(len(ks), len(S))
        rows.append({"row_id": f"{pn}|{t}", "tier": t, "label": TL[t], "k": len(ks), "n": len(S), "pct": 100*len(ks)/len(S), "ci_lo": lo, "ci_hi": hi, "keys": ks})
mn = [r["key"] for r in recs if tier(r) == "3" and any(m["metric"] in LATC and re.search(r"\b(mean|average|avg)\b", (m.get("evidence") or "").lower()) for m in OM(r))]
rows.append({"row_id": "all|3_mean_named", "k": len(mn), "keys": mn})
tr = collections.Counter(r.get("tail_role", "unaudited") for r in recs)
for t in ("T-OBJ","T-SLO","T-REP","NONE"): rows.append({"row_id": f"audit|{t}", "k": tr[t], "n": 40})
assert sum(tr[t] for t in ("T-OBJ","T-SLO","T-REP","NONE")) == 40
out["tail_tiers"] = rows
# ---- D6
FULLALL = [r for r in allrecs if r.get("read_level") == "full"]
LBL = {"T1":"from arrival, queueing included","T2":"= prefill duration","T2a":"…then measured under load","T3":"offline / one request",
 "T5":"includes KV loading","T6":"whole pre-generation pipeline","T7":"includes scale-up wait","T8":"queueing kept separate","unstated":"no start point stated",
 "GP1":"max rate at X % attainment","GP1a":"…per GPU","GP1b":"…single SLO only","GP2":"measured rate of SLO-meeting requests","GP3":"SLO-meeting tokens/s",
 "GP4":"a fraction, not a rate","GP5":"no SLO (accepted tokens/s)","GP6":"completed requests only","GP7":"applications by deadline","GP8":"smooth goodput",
 "K1":"input + output","K2":"output, over prefill + decode time","K3":"decode phase only","K4":"prefill / input only","K5":"not stated"}
rows = []
def addv(metric, mkey, codes):
    for name, ks in V[mkey].items():
        c = name.split()[0]
        if c in codes: rows.append({"row_id": f"{metric}|{c}", "metric": metric, "variant_code": c, "label": LBL[c], "n": len(set(ks)), "keys": sorted(set(ks))})
addv("TTFT", "TTFT", {"T1","T2","T2a","T3","T5","T6","T7","T8"})
intt = set(k for ks in V["TTFT"].values() for k in ks)
un = sorted(r["key"] for r in FULLALL if any(d.get("canonical") == "TTFT" for d in (r.get("metric_definitions") or [])) and r["key"] not in intt)
rows.append({"row_id": "TTFT|unstated", "metric": "TTFT", "variant_code": "unstated", "label": LBL["unstated"], "n": len(un), "keys": un})
addv("GOODPUT", "GOODPUT", {f"GP{i}" for i in range(1,9)} | {"GP1a","GP1b"})
addv("THR_TOK", "THR_TOK", {"K1","K2","K3","K4","K5"})
for x in rows: x["population"] = f"{len(FULLALL)} full-text records"
out["def_variants"] = rows
for k, v in out.items():
    json.dump({"id": k, "rows": v}, open(os.path.join(D, k + ".b.json"), "w"), indent=1)
print({k: len(v) for k, v in out.items()}, "FULLALL", len(FULLALL), "TTFT unstated", len(un))
