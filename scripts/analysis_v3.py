#!/usr/bin/env python3
"""Revision analyses after review R1 (run after scripts/aggregate.py). Usage: python3 -I analysis_v3.py <project>
Writes analysis/summary_v3.txt. Uses record fields added by the re-pass (evidence_kind, stat_basis, load_class)."""
import json, glob, os, sys, collections, csv, math
P = sys.argv[1]
src = open(os.path.join(P, "scripts", "aggregate.py")).read()
ns = {}; exec(src[src.index("OVERRIDE ="):src.index("FAM = {  # legacy")], ns)
famc, OV, nstat = ns["famc"], ns["OVERRIDE"], ns["nstat"]
dv = open(os.path.join(P, "analysis", "def_variants.py")).read()
vns = {}; exec(dv[dv.index("def k("):dv.index("\nV = {")] + "\n" + dv[dv.index("V = {"):].split("\n}\n")[0] + "\n}\n", vns)
V = vns["V"]
sel = {r["key"]: r for r in csv.DictReader(open(os.path.join(P, "SELECTION.tsv")), delimiter="\t")}
LATC = {"TTFT","TPOT","TBT","E2E","NORM_LAT","QUEUE","PROGRAM_JCT","TPS_USER"}   # serving latencies (TOKEN_LAT excluded)
TAILS = {"P90","P95","P97","P99","max"}
SLOC = {"GOODPUT","SLO_ATT","OTHER:smooth_goodput"}
recs = []
for f in sorted(glob.glob(os.path.join(P, "records", "*.json"))):
    r = json.load(open(f))
    mp = str(r.get("technique","")).startswith("METRIC-PAPER") or sel.get(r["key"],{}).get("track") == "mp-full"
    if mp or r.get("read_level") != "full": continue
    for m in r["optimized_metrics"]:
        m["metric"] = OV.get((r["key"], m["metric"]), m["metric"]); m["stat"] = nstat(m.get("stat"))
    r["_year"] = 2000 + int(r["key"][6:8]) if r["key"].startswith("arxiv_") else int(r.get("year") or 0)
    recs.append(r)
N = len(recs); out = []
def p(*a): out.append(" ".join(str(x) for x in a))
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    ph = k/n; d = 1 + z*z/n; c = (ph + z*z/(2*n))/d; h = z*math.sqrt(ph*(1-ph)/n + z*z/(4*n*n))/d
    return (100*(c-h), 100*(c+h))
def share(k, n): lo, hi = wilson(k, n); return f"{k}/{n} = {100*k/n:.0f}% [95% CI {lo:.0f}–{hi:.0f}]" if n else "0/0"
def yb(y): return "2022-23" if y <= 2023 else ("2024" if y == 2024 else "2025-26")
p(f"# summary_v3 — {N} full-text optimizer records")
# evidence kind
ek = collections.Counter(m.get("evidence_kind","(missing)") for r in recs for m in r["optimized_metrics"])
p("\n## evidence_kind of optimized_metrics entries"); p(ek.most_common())
p("papers with >=1 design-evidenced objective:", sum(1 for r in recs if any(m.get('evidence_kind')=='design' and m['role']=='objective' for m in r['optimized_metrics'])))
# load class
lc = collections.Counter(r.get("load_class","(missing)") for r in recs)
p("\n## load_class"); p(lc.most_common())
# family shares (design or result-only objectives)
p("\n## family shares (objective / constraint), all full-text optimizers")
fo = collections.Counter(); fc = collections.Counter()
for r in recs:
    fo.update({famc(m["metric"]) for m in r["optimized_metrics"] if m["role"]=="objective"})
    fc.update({famc(m["metric"]) for m in r["optimized_metrics"] if m["role"]=="constraint"})
for f in sorted(set(fo)|set(fc), key=lambda f: -(fo[f]+fc[f])):
    p(f"  {f:20s} obj {share(fo[f],N):30s} con {share(fc[f],N)}")
# request latency split by load class
rl = [r for r in recs if any(famc(m["metric"])=="request-latency" and m["role"]=="objective" for m in r["optimized_metrics"])]
p("\n## request-latency objective papers by load_class:", collections.Counter(r.get("load_class") for r in rl).most_common())
p("   batch_time recodes:", [r["key"] for r in recs if any(m["metric"]=="OTHER:batch_time" for m in r["optimized_metrics"])])
# tail tiers (serving latencies only)
STRICT_T1 = {"arxiv_2602.11688", "arxiv_2502.13965"}          # GORGO (-p95 TTFT fitness), Autellix (P95/P99 program latency goal)
LENIENT_T1 = {"arxiv_2407.00023", "arxiv_2508.06948", "arxiv_2507.17769"}  # tail named as design aim, no percentile objective: Preble, Kairos, PolyServe
DETERMINISTIC = {"arxiv_2504.02263", "arxiv_2404.07947", "arxiv_2306.06000", "arxiv_2512.15705", "arxiv_2310.07240"}  # fixed per-request bounds, not distributional
def tier(r):
    om = r["optimized_metrics"]; k = r["key"]
    if k in STRICT_T1: return "1a percentile minimized (strict)"
    if k in LENIENT_T1: return "1b tail named as design aim, no percentile objective (lenient)"
    if r.get("load_class") == "single-sequence": return "5 no serving-latency target"   # batch-1 latency is not serving latency (matches blind QA prompt)
    if k in DETERMINISTIC: return "2b deterministic latency bound"
    if any(m["role"]=="constraint" and m["metric"] in LATC and m["stat"] in TAILS for m in om) or \
       any(m["metric"] in SLOC for m in om) or any(m["metric"] in LATC and m["stat"]=="attainment" for m in om) or \
       any(m["metric"] in ("QOE","OTHER:fluidity_index","OTHER:user_idle_latency") for m in om):
        return "2a distributional over requests/tokens (percentile SLO, attainment, goodput, per-token deadlines)"
    if any(m["metric"] in LATC for m in om): return "3 mean or unspecified"
    return "5 no serving-latency target"
for label, S in (("ALL full-text", recs), ("online-arrivals or mixed", [r for r in recs if r.get("load_class") in ("online-arrivals","mixed")])):
    T = collections.Counter(tier(r) for r in S); n = len(S)
    p(f"\n## tail tiers v2 — {label} (n={n})")
    for t in sorted(T): p(f"  {t:95s} {share(T[t],n)}")
p("   tier3 papers with 'mean'/'average' (word match) in the design quote of a serving-latency entry:",
  sum(1 for r in recs if tier(r)=="3 mean or unspecified" and any(m["metric"] in LATC and __import__("re").search(r"\b(mean|average|avg)\b", m.get("evidence","").lower()) for m in r["optimized_metrics"])))
p("   tail_role (audit) counts:", collections.Counter(r.get("tail_role","unaudited") for r in recs).most_common())
# stat basis among serving-latency objectives
sb = collections.Counter((m["stat"], m.get("stat_basis","(missing)")) for r in recs for m in r["optimized_metrics"] if m["role"]=="objective" and m["metric"] in LATC)
p("\n## serving-latency OBJECTIVE entries: (stat, stat_basis)"); p(sb.most_common())
# trends with CIs: all, online-arrivals subset
def slo_framed(r):
    om = r["optimized_metrics"]
    return any(m["metric"] in SLOC and m["role"]=="objective" for m in om) or any(m["role"]=="constraint" and famc(m["metric"]) in ("first-token","token-pace","request-latency") for m in om)
def gp_obj(r): return any(m["metric"] in SLOC and m["role"]=="objective" for m in r["optimized_metrics"])
for label, S in (("ALL full-text", recs), ("online-arrivals or mixed load", [r for r in recs if r.get("load_class") in ("online-arrivals","mixed")])):
    p(f"\n## trend — {label}")
    for b in ("2022-23","2024","2025-26"):
        g = [r for r in S if yb(r["_year"])==b]; n = len(g)
        p(f"  {b}: n={n:3d}  SLO-framed {share(sum(map(slo_framed,g)),n):28s} goodput/attainment objective {share(sum(map(gp_obj,g)),n)}")
# capacity variants by year from DEFINITIONS assignments
def cochran_armitage(counts):  # counts: list of (k, n) per ordered group, scores 0..g-1
    ks=[c[0] for c in counts]; ns=[c[1] for c in counts]; N=sum(ns); K=sum(ks); pbar=K/N; sc=list(range(len(counts)))
    T=sum(s*(k-n*pbar) for s,k,n in zip(sc,ks,ns)); sb=sum(s*n for s,n in zip(sc,ns))/N
    V=pbar*(1-pbar)*sum(n*(s-sb)**2 for s,n in zip(sc,ns))
    z=T/math.sqrt(V) if V>0 else 0; pv=math.erfc(abs(z)/math.sqrt(2)); return z,pv
onl=[r for r in recs if r.get("load_class") in ("online-arrivals","mixed")]
p("\n## within online/mixed: trend tests (Cochran-Armitage, two-sided)")
for name,fn in (("SLO-framed",slo_framed),("goodput/attainment objective",gp_obj)):
    c=[(sum(map(fn,[r for r in onl if yb(r["_year"])==b])),len([r for r in onl if yb(r["_year"])==b])) for b in ("2022-23","2024","2025-26")]
    z,pv=cochran_armitage(c); p(f"  {name}: {c}  z={z:.2f} p={pv:.3f}")
_capk=set(V["THR_REQ"]["Q4 max rate before latency/queueing knee (no explicit SLO)"])|set(V["THR_REQ"]["Q5 max rate under an explicit latency target (no attainment fraction)"])
c=[(sum(1 for r in onl if yb(r["_year"])==b and r["key"] in _capk),len([r for r in onl if yb(r["_year"])==b])) for b in ("2022-23","2024","2025-26")]
PCTCAP = {"arxiv_2311.18677","arxiv_2403.02310","arxiv_2404.09526","arxiv_2407.00079","arxiv_2409.17264"}  # capacity under percentile/attainment SLOs
c2=[(sum(1 for r in onl if yb(r["_year"])==b and r["key"] in _capk-PCTCAP),len([r for r in onl if yb(r["_year"])==b])) for b in ("2022-23","2024","2025-26")]
z2,pv2=cochran_armitage(c2); p(f"  knee/latency-target capacity EXCLUDING percentile-SLO capacity papers: {c2}  z={z2:.2f} p={pv2:.3f}")
pre=(c[0][0]+c[1][0], c[0][1]+c[1][1]); p(f"  knee/target capacity before 2025: {pre[0]}/{pre[1]}; 2025-26: {c[2][0]}/{c[2][1]}")
z,pv=cochran_armitage(c); p(f"  knee/latency-target capacity: {c} -> "+", ".join(f"{100*k/n:.0f}%" for k,n in c)+f"  z={z:.2f} p={pv:.3f}")

cap = set(V["THR_REQ"]["Q4 max rate before latency/queueing knee (no explicit SLO)"]) | set(V["THR_REQ"]["Q5 max rate under an explicit latency target (no attainment fraction)"])
gpk = set(k for name, ks in V["GOODPUT"].items() for k in ks)
keys = {r["key"]: r for r in recs}
p("\n## capacity definitions by year (DEFINITIONS.md variant assignments; full-text optimizers only)")
for b in ("2022-23","2024","2025-26"):
    g = [r for r in recs if yb(r["_year"])==b]; n = len(g)
    c1 = sum(1 for r in g if r["key"] in cap); c2 = sum(1 for r in g if r["key"] in gpk); c3 = sum(1 for r in g if r["key"] in cap|gpk)
    p(f"  {b}: n={n}  knee-or-latency-target capacity (THR_REQ Q4+Q5) {share(c1,n)} | any goodput variant (GOODPUT GP*) {share(c2,n)} | either {share(c3,n)}")
# robustness: full + abstract
ab = []
for f in glob.glob(os.path.join(P, "records", "*.json")):
    r = json.load(open(f))
    if r.get("read_level") == "abstract":
        r["_year"] = 2000 + int(r["key"][6:8]) if r["key"].startswith("arxiv_") else int(r.get("year") or 0); ab.append(r)
p("\n## robustness: full + abstract records combined (abstract coding is lower confidence)")
for b in ("2022-23","2024","2025-26"):
    g = [r for r in recs+ab if yb(r["_year"])==b]; n = len(g)
    p(f"  {b}: n={n}  SLO-framed {share(sum(map(slo_framed,g)),n)}  goodput/attainment objective {share(sum(map(gp_obj,g)),n)}")
# layer constraint column
p("\n## constraints by layer (families, count of papers)")
lay = collections.defaultdict(list)
for r in recs: lay[r.get("layer")].append(r)
for L, g in sorted(lay.items(), key=lambda kv: -len(kv[1])):
    c = collections.Counter(f for r in g for f in {famc(m["metric"]) for m in r["optimized_metrics"] if m["role"]=="constraint"})
    p(f"  {str(L)[:36]:36s} n={len(g):2d} " + ", ".join(f"{f} {v}" for f, v in c.most_common()))
# TPS_USER
p("\n## TPS_USER anywhere in record (optimized/reported/definitions):")
for r in recs:
    s = json.dumps(r)
    if '"TPS_USER"' in s: p("  ", r["key"], r.get("layer"), r["title"][:60])
# abstract guess vs full text on the same papers (code level)
cand = {}
for f in glob.glob(os.path.join(P, "candidates", "D*.tsv")):
    for row in csv.DictReader(open(f), delimiter="\t"): cand.setdefault(row["key"].strip(), row)
ex = 0; jac = []; con_in_abs = 0; ncon = 0; n = 0
for r in recs:
    c = cand.get(r["key"])
    if not c: continue
    g = {t.strip() for t in c["abstract_metric_guess"].split(";") if t.strip()}
    g = {OV.get((r["key"], t), t) for t in g}
    o = {m["metric"] for m in r["optimized_metrics"] if m["role"]=="objective"}
    co = {m["metric"] for m in r["optimized_metrics"] if m["role"]=="constraint" and famc(m["metric"]) in ("first-token","token-pace","request-latency")}
    n += 1; ex += (g == o); jac.append(len(g & o)/len(g | o) if g | o else 1)
    if co: ncon += 1; con_in_abs += bool(co & g)
p(f"\n## abstract guess (discovery, same papers) vs full-text objectives: n={n}; exact code-set match {ex}; mean Jaccard {sum(jac)/len(jac):.2f}; papers with a latency constraint {ncon}, of which the abstract guess names the constrained metric {con_in_abs}")
open(os.path.join(P, "analysis", "summary_v3.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
