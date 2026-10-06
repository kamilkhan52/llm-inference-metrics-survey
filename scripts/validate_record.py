#!/usr/bin/env python3
"""Validate records/<key>.json files against SCHEMA.md. Usage: python3 -I validate_record.py <file>..."""
import json, sys, re
CODES = {"TTFT","TPOT","TBT","E2E","NORM_LAT","TOKEN_LAT","THR_TOK","THR_REQ","TPS_USER","GOODPUT","SLO_ATT",
         "QUEUE","COST","ENERGY","MEMORY","QUALITY","FAIRNESS","QOE","PROGRAM_JCT","ACCEPT","UTIL","PREEMPT"}
REQ = ["key","title","first_author","year","venue","url","cluster","technique","layer","read_level",
       "optimized_metrics","headline_claim","reported_metrics","metric_definitions","eval_type","confidence"]
def ok_code(c): return c in CODES or re.fullmatch(r"OTHER:[A-Za-z0-9_\-/]+", c or "") is not None
bad = 0
for f in sys.argv[1:]:
    errs = []
    try:
        r = json.load(open(f))
    except Exception as e:
        print(f"FAIL {f}: not JSON ({e})"); bad += 1; continue
    for k in REQ:
        if k not in r: errs.append(f"missing {k}")
    if r.get("read_level") not in ("full","abstract"): errs.append("read_level must be full|abstract")
    if r.get("read_level") == "full" and not r.get("fulltext_path"): errs.append("full read needs fulltext_path")
    om = r.get("optimized_metrics") or []
    if not om: errs.append("optimized_metrics empty")
    for m in om:
        if not ok_code(m.get("metric")): errs.append(f"bad code {m.get('metric')}")
        if not m.get("evidence") or not m.get("locator"): errs.append(f"{m.get('metric')}: needs evidence+locator")
        if m.get("role") not in ("objective","constraint"): errs.append(f"{m.get('metric')}: role objective|constraint")
    for m in r.get("reported_metrics") or []:
        if not ok_code(m.get("metric")): errs.append(f"bad reported code {m.get('metric')}")
    for d in r.get("metric_definitions") or []:
        if not ok_code(d.get("canonical")): errs.append(f"bad def code {d.get('canonical')}")
    print(("FAIL " if errs else "OK   ") + f + ("" if not errs else ": " + "; ".join(errs)))
    bad += bool(errs)
sys.exit(1 if bad else 0)
