#!/usr/bin/env python3
"""Per-code usage vs definition counts over full-text records (incl. metric papers).
Usage: python3 -I def_usage.py <project_dir>"""
import json, glob, os, sys, collections
P = sys.argv[1]
recs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(P, "records", "*.json")))]
full = [r for r in recs if r.get("read_level") == "full"]
use = collections.defaultdict(set); dfn = collections.defaultdict(set); head = collections.defaultdict(set); anym = collections.defaultdict(set); opt = collections.defaultdict(set)
for r in full:
    k = r["key"]
    for m in r.get("optimized_metrics", []) or []: use[m["metric"]].add(k); opt[m["metric"]].add(k)
    for m in r.get("reported_metrics", []) or []: use[m["metric"]].add(k)
    for m in (r.get("headline_claim") or {}).get("metrics", []) or []: use[m].add(k); head[m].add(k)
    for d in r.get("metric_definitions", []) or []: dfn[d["canonical"]].add(k); anym[d["canonical"]].add(k)
    for c in list(use):
        if k in use[c]: anym[c].add(k)
print(f"full-text records: {len(full)}")
print(f"{'code':22s} used optimized headline defined headline&no-def-entry any-field")
for c in sorted(use, key=lambda c: -len(use[c])):
    if len(use[c]) < 3 and not c in ("QOE","QUEUE","TPS_USER"): continue
    hu = head[c] - dfn[c]
    print(f"{c:22s} {len(use[c]):4d} {len(opt[c]):9d} {len(head[c]):8d} {len(dfn[c]):7d} {len(hu):5d} {len(anym[c]):5d}")
U = lambda *cs: len(set().union(*[anym[c] for c in cs]))
print("any-field unions: TPOT|TBT", U("TPOT","TBT"), " THR_TOK|THR_REQ", U("THR_TOK","THR_REQ"), " GOODPUT|SLO_ATT", U("GOODPUT","SLO_ATT"),
      " TPOT&TBT", len(anym["TPOT"] & anym["TBT"]))
