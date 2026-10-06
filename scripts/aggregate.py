#!/usr/bin/env python3
"""Aggregate records/*.json into analysis tables. Usage: python3 -I aggregate.py <project_dir>"""
import json, glob, os, sys, collections, csv
P = sys.argv[1]
recs = []
for f in sorted(glob.glob(os.path.join(P, "records", "*.json"))):
    r = json.load(open(f)); r["_file"] = os.path.basename(f); recs.append(r)
sel = {row["key"]: row for row in csv.DictReader(open(os.path.join(P, "SELECTION.tsv")), delimiter="\t")}
def is_mp(r): return str(r.get("technique","")).startswith("METRIC-PAPER") or sel.get(r["key"],{}).get("track")=="mp-full"
def oos(r): return "OUT OF SCOPE" in str(r.get("extractor_notes",""))
# Normalization rules N1-N6 (decided 2026-10-06 after blind QA; see RESEARCH_LOG "Normalization rules")
OVERRIDE = {("arxiv_2404.14527","TPOT"):"NORM_LAT",   # Melange "TPOT" = request latency / output tokens (N2)
            ("arxiv_2502.04563","TPS_USER"):"TOKEN_LAT"}  # WaferLLM TPR at batch 1 = single-sequence speed (N3)
FAMILY = {
 "first-token": ["TTFT","OTHER:prefill_latency","OTHER:QTTFT","OTHER:TTFVT"],
 "token-pace": ["TPOT","TBT","TPS_USER","OTHER:reading_speed_token_deadline_SLO"],
 "request-latency": ["E2E","NORM_LAT","QUEUE"],
 "program-latency": ["PROGRAM_JCT"],
 "single-seq-speed": ["TOKEN_LAT","OTHER:iteration_latency"],
 "throughput": ["THR_TOK","THR_REQ","OTHER:spec_goodput","OTHER:batch_scalability","OTHER:num_served_adapters"],
 "slo-goodput": ["GOODPUT","SLO_ATT","OTHER:smooth_goodput"],
 "user-perceived": ["QOE","OTHER:fluidity_index","OTHER:fluid_token_generation_rate","OTHER:user_idle_latency"],
 "cost-energy": ["COST","ENERGY","OTHER:servers_per_power_budget"],
 "memory": ["MEMORY","OTHER:kv_size","OTHER:flash_io_volume"],
 "quality": ["QUALITY"],
 "fairness": ["FAIRNESS"],
 "hw-efficiency": ["UTIL","OTHER:kernel_speedup","OTHER:attn_kernel_runtime","OTHER:attn_kernel_speed","OTHER:GEMM_kernel_speedup",
                   "OTHER:pipeline_bubbles","OTHER:pipeline_bubble_time","OTHER:HBM_accesses"],
 "cache-proxy": ["OTHER:cache_hit_rate","OTHER:token_hit_rate","OTHER:prefix_cache_hit_rate","OTHER:kv_cache_hit_ratio","OTHER:expert_hit_rate"],
 "system-op-latency": ["OTHER:model_startup_latency","OTHER:scale_time"],
}
C2F = {c:f for f,cs in FAMILY.items() for c in cs}
def famc(c): return C2F.get(c, "mechanism/other")   # ACCEPT, PREEMPT, kendall_tau, preprocessing times, ...
def nstat(s):
    s=str(s or "n/a").strip()
    return {"P50":"median","median":"median"}.get(s, s if s in ("mean","P90","P95","P97","P99","max","attainment") else "n/a")
LATFAM = {"first-token","token-pace","request-latency","program-latency","single-seq-speed"}
TAILS = {"P90","P95","P97","P99","max"}
FAM = {  # legacy (unused)
 "TTFT":"latency-request","TPOT":"latency-token","TBT":"latency-token","TPS_USER":"latency-token","E2E":"latency-request",
 "NORM_LAT":"latency-request","TOKEN_LAT":"latency-single-seq","QUEUE":"latency-request","PROGRAM_JCT":"latency-program",
 "THR_TOK":"throughput","THR_REQ":"throughput","GOODPUT":"slo","SLO_ATT":"slo","COST":"cost/energy","ENERGY":"cost/energy",
 "MEMORY":"memory","QUALITY":"quality","FAIRNESS":"fairness","QOE":"qoe","ACCEPT":"other","UTIL":"utilization","PREEMPT":"other"}
def fam(c): return FAM.get(c, "other")
TAIL = {"P90","P95","P99","P99.9","max","tail"}
rows = []
for r in recs:
    for m in r.get("optimized_metrics",[]):
        m["metric"] = OVERRIDE.get((r["key"], m["metric"]), m["metric"]); m["stat"] = nstat(m.get("stat"))
    obj = [m for m in r.get("optimized_metrics",[]) if m.get("role")=="objective"]
    con = [m for m in r.get("optimized_metrics",[]) if m.get("role")=="constraint"]
    yr = r.get("year")
    if r["key"].startswith("arxiv_"): yr = 2000 + int(r["key"][6:8])   # first arXiv version year from the ID (N7)
    rows.append(dict(key=r["key"], title=r.get("title","")[:70], year=yr, layer=r.get("layer"),
        read=r.get("read_level"), mp=is_mp(r), oos=oos(r), conf=r.get("confidence"),
        obj=sorted({m["metric"] for m in obj}), con=sorted({m["metric"] for m in con}),
        objf=sorted({famc(m["metric"]) for m in obj}), conf_=sorted({famc(m["metric"]) for m in con}),
        flag=("FA-training" if r["key"] in ("arxiv_2205.14135","arxiv_2307.08691") else ("non-generative" if r["key"]=="arxiv_2302.11665" else "")),
        tail_obj=sorted({f'{m["metric"]}@{m["stat"]}' for m in obj if famc(m["metric"]) in LATFAM and m["stat"] in TAILS}),
        tail_con=sorted({f'{m["metric"]}@{m["stat"]}' for m in con if famc(m["metric"]) in LATFAM and m["stat"] in TAILS}),
        lat_obj_stats=sorted({m["stat"] for m in obj if famc(m["metric"]) in LATFAM}),
        obj_stats=sorted({f'{m["metric"]}@{m.get("stat","n/a")}' for m in obj}),
        con_stats=sorted({f'{m["metric"]}@{m.get("stat","n/a")}' for m in con}),
        reported=sorted({m.get("metric") for m in r.get("reported_metrics",[]) if m.get("metric")}),
        tail_role=r.get("tail_role","unaudited"), eval_type=r.get("eval_type"), load=r.get("load_regime"), tradeoff=r.get("tradeoff_acknowledged")))
json.dump(rows, open(os.path.join(P,"analysis","paper_table.json"),"w"), indent=1)
core = [x for x in rows if not x["mp"] and not x["oos"]]
full = [x for x in core if x["read"]=="full"]; ab = [x for x in core if x["read"]=="abstract"]
out = []
def pr(*a): out.append(" ".join(str(x) for x in a))
pr(f"records={len(rows)} core_optimizers={len(core)} full={len(full)} abstract={len(ab)} metric_papers={sum(x['mp'] for x in rows)} out_of_scope={sum(x['oos'] for x in rows)}")
pr("\n## Full-read optimizers by year"); pr(dict(sorted(collections.Counter(x["year"] for x in full).items())))
pr("\n## Full-read optimizers by layer"); pr(collections.Counter(x["layer"] for x in full).most_common())
for label, S in (("FULL", full), ("ABSTRACT", ab)):
    n = len(S)
    pr(f"\n## {label}: share of papers with metric as OBJECTIVE / as CONSTRAINT (n={n})")
    co = collections.Counter(c for x in S for c in x["obj"]); cc = collections.Counter(c for x in S for c in x["con"])
    for c in sorted(set(co)|set(cc), key=lambda c: -(co[c]+cc[c])):
        pr(f"  {c:22s} obj {co[c]:3d} ({100*co[c]/n:4.0f}%)  con {cc[c]:3d} ({100*cc[c]/n:4.0f}%)")
pr("\n## FULL: layer x objective-family (count of papers)")
fams = ["throughput","latency-request","latency-token","latency-single-seq","latency-program","slo","cost/energy","memory","quality","fairness","qoe","utilization","other"]
pr("  layer".ljust(40) + " ".join(f[:8].rjust(8) for f in fams) + "   n")
for L, grp in sorted(collections.defaultdict(list, {k:[x for x in full if x["layer"]==k] for k in {x["layer"] for x in full}}).items(), key=lambda kv:-len(kv[1])):
    cnt = collections.Counter(f for x in grp for f in {fam(c) for c in x["obj"]})
    pr(f"  {str(L)[:38]:38s}" + " ".join(str(cnt[f]).rjust(8) for f in fams) + f"   {len(grp)}")
pr("\n## FULL: objective-family share by year bucket (papers)")
def yb(y): return "<=2023" if y and int(y)<=2023 else ("2024" if y and int(y)==2024 else "2025-26")
for b in ("<=2023","2024","2025-26"):
    grp=[x for x in full if yb(x["year"])==b]; n=len(grp)
    cnt = collections.Counter(f for x in grp for f in {fam(c) for c in x["obj"]})
    slo_any = sum(1 for x in grp if {"GOODPUT","SLO_ATT"} & (set(x["obj"])|set(x["con"])) or any(c in x["con"] for c in ("TTFT","TPOT","TBT","E2E")))
    pr(f"  {b:8s} n={n:3d} " + ", ".join(f"{f}={100*cnt[f]/n:.0f}%" for f in fams if cnt[f]) + f" | any SLO/latency-constraint={100*slo_any/n:.0f}%")
pr("\n## FULL: statistic of LATENCY objectives/constraints (metric@stat counts)")
lat = {"TTFT","TPOT","TBT","E2E","NORM_LAT","TOKEN_LAT","QUEUE","PROGRAM_JCT","TPS_USER"}
sc = collections.Counter()
for x in full:
    for s in x["obj_stats"]+x["con_stats"]:
        m, st = s.split("@",1)
        if m in lat: sc[st]+=1
pr(sc.most_common())
tailpapers = [x for x in full if any(s.split("@",1)[0] in lat and s.split("@",1)[1] in TAIL for s in x["obj_stats"])]
tailcon = [x for x in full if any(s.split("@",1)[0] in lat and s.split("@",1)[1] in TAIL for s in x["con_stats"])]
pr(f"papers with a TAIL latency OBJECTIVE: {len(tailpapers)}/{len(full)}; with a TAIL latency CONSTRAINT: {len(tailcon)}/{len(full)}")
pr("  tail-objective papers:", ", ".join(x["key"] for x in tailpapers))
pr("\n## FULL: eval_type"); pr(collections.Counter(x["eval_type"] for x in full).most_common())
pr("\n## FULL: number of objective metrics per paper"); pr(sorted(collections.Counter(len(x["obj"]) for x in full).items()))
pr("\n## FULL: tradeoff acknowledged (non-null)"); pr(sum(1 for x in full if x["tradeoff"]), "/", len(full))
pr("\n## OTHER: codes used"); pr(collections.Counter(c for x in rows for c in x["obj"]+x["con"]+x["reported"] if c.startswith("OTHER")).most_common())
open(os.path.join(P,"analysis","summary.txt"),"w").write("\n".join(out)+"\n")
# definitions dump grouped by canonical code
defs = collections.defaultdict(list)
for r in recs:
    for d in r.get("metric_definitions",[]) or []:
        defs[d.get("canonical")].append(dict(key=r["key"], year=r.get("year"), term=d.get("term_as_written"),
            q=d.get("definition_quote"), loc=d.get("locator"), notes=d.get("notes")))
with open(os.path.join(P,"analysis","definitions_by_metric.md"),"w") as fh:
    for c in sorted(defs, key=lambda c:-len(defs[c])):
        fh.write(f"\n## {c} ({len(defs[c])} definitions)\n")
        for d in defs[c]:
            fh.write(f"- [{d['key']} {d['year']}] term={d['term']!r}: \"{d['q']}\" ({d['loc']})" + (f" — {d['notes']}" if d['notes'] else "") + "\n")
print("\n".join(out))

# ---------- v2 family-level analysis ----------
out2=[]
def p2(*a): out2.append(" ".join(str(x) for x in a))
FAMS=list(FAMILY)+["mechanism/other"]
for label,S in (("FULL core optimizers",full),("FULL excl flagged",[x for x in full if not x["flag"]]),("ABSTRACT",ab)):
    n=len(S); p2(f"\n## {label} (n={n}): family as OBJECTIVE / CONSTRAINT")
    co=collections.Counter(f for x in S for f in x["objf"]); cc=collections.Counter(f for x in S for f in x["conf_"])
    for f in sorted(FAMS,key=lambda f:-(co[f]+cc[f])):
        if co[f] or cc[f]: p2(f"  {f:20s} obj {co[f]:3d} ({100*co[f]/n:3.0f}%)  con {cc[f]:3d} ({100*cc[f]/n:3.0f}%)  either {sum(1 for x in S if f in x['objf'] or f in x['conf_']):3d}")
p2("\n## FULL: layer x objective family")
short=["first-token","token-pace","request-latency","program-latency","single-seq-speed","throughput","slo-goodput","user-perceived","cost-energy","memory","quality","hw-efficiency"]
p2("layer".ljust(36)+" ".join(f[:7].rjust(7) for f in short)+"    n")
layers=collections.defaultdict(list)
for x in full: layers[x["layer"]].append(x)
for L,g in sorted(layers.items(),key=lambda kv:-len(kv[1])):
    cnt=collections.Counter(f for x in g for f in x["objf"])
    p2(f"{str(L)[:35]:36s}"+" ".join(str(cnt[f]).rjust(7) for f in short)+f"   {len(g)}")
p2("\n## FULL: objective family share by year bucket")
for b in ("<=2023","2024","2025-26"):
    g=[x for x in full if yb(x["year"])==b]; n=len(g); cnt=collections.Counter(f for x in g for f in x["objf"])
    slo=sum(1 for x in g if "slo-goodput" in x["objf"] or ({"first-token","token-pace","request-latency"} & set(x["conf_"])))
    p2(f"  {b:8s} n={n:3d} "+", ".join(f"{f}={100*cnt[f]/n:.0f}%" for f in FAMS if cnt[f])+f" | SLO-framed (goodput/attainment objective or latency constraint)={slo} ({100*slo/n:.0f}%)")
p2("\n## FULL: latency statistic — papers whose latency OBJECTIVE uses each stat")
st=collections.Counter(s for x in full for s in x["lat_obj_stats"]); p2(st.most_common())
nl=sum(1 for x in full if x["lat_obj_stats"]); p2(f"papers with any latency objective: {nl}/{len(full)}")
p2(f"papers with TAIL latency objective: {sum(1 for x in full if x['tail_obj'])}; tail latency constraint: {sum(1 for x in full if x['tail_con'])}; either: {sum(1 for x in full if x['tail_obj'] or x['tail_con'])}")
for x in full:
    if x["tail_obj"] or x["tail_con"]: p2(f"   {x['key']} ({x['year']}, {x['layer']}): obj {x['tail_obj']} con {x['tail_con']}")
p2("\n## FULL: eval_type"); p2(collections.Counter(x["eval_type"] for x in full).most_common())
p2("\n## FULL: # objective families per paper"); p2(sorted(collections.Counter(len(x["objf"]) for x in full).items()))
p2("\n## FULL: audited tail role (qa/TAIL_AUDIT.md; unaudited = no tail entry and <8 percentile mentions in text)")
p2(collections.Counter(x["tail_role"] for x in full).most_common())
for c in ("T-OBJ","T-SLO"):
    p2(f"  {c}: " + "; ".join(f"{x['key']} ({x['year']}, {x['layer']})" for x in full if x["tail_role"]==c))
# abstract-guess (discovery) vs full-text objective families
cand={}
for f in glob.glob(os.path.join(P,"candidates","D*.tsv")):
    for r in csv.DictReader(open(f),delimiter="\t"): cand.setdefault(r["key"].strip(), r)
agree=0; tot=0; disagree=[]
for x in full:
    c=cand.get(x["key"])
    if not c: continue
    g={famc(t.strip()) for t in c["abstract_metric_guess"].split(";") if t.strip()}
    tot+=1
    if g & set(x["objf"]): agree+=1
    else: disagree.append((x["key"],sorted(g),x["objf"]))
p2(f"\n## Abstract-guess (discovery) vs full-text objective family overlap: {agree}/{tot}")
for d in disagree: p2("   ", d)
open(os.path.join(P,"analysis","summary_v2.txt"),"w").write("\n".join(out2)+"\n")
json.dump(rows, open(os.path.join(P,"analysis","paper_table.json"),"w"), indent=1)
print("\n".join(out2))
