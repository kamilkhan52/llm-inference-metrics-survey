#!/usr/bin/env python3
"""Headline metrics used without a definition (full-text records).
A definition entry counts as 'undefined' when the extractor's quote/notes flag it as not defined.
Usage: python3 -I def_undefined.py <project_dir>"""
import json, glob, os, sys, re, collections
P = sys.argv[1]
UNDEF = re.compile(r"not (formally |explicitly |further )?defined|never (formally |explicitly )?defined|without (a )?(formal |explicit )?definition|undefined|used \(not defined\)|\(not defined|no (formal|explicit) definition|never given a formal|units? (not stated|never|unstated)|not stated|unstated|never formally|only acronym|named but not defined", re.I)
recs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(P, "records", "*.json")))]
full = [r for r in recs if r.get("read_level") == "full"]
LAT_THR = {"TTFT","TPOT","TBT","E2E","NORM_LAT","TOKEN_LAT","THR_TOK","THR_REQ","GOODPUT","SLO_ATT","PROGRAM_JCT","TPS_USER","QOE","COST","ENERGY"}
out = collections.defaultdict(list); n_head = collections.Counter()
for r in full:
    k = r["key"]; hm = set((r.get("headline_claim") or {}).get("metrics", []) or [])
    defs = collections.defaultdict(list)
    for d in r.get("metric_definitions", []) or []:
        txt = (d.get("definition_quote","") + " || " + (d.get("notes") or ""))
        defs[d["canonical"]].append(bool(UNDEF.search(txt)))
    for c in hm & LAT_THR:
        n_head[c] += 1
        if c not in defs: out[c].append((k, "no definition entry"))
        elif all(defs[c]): out[c].append((k, "entry flagged undefined"))
        elif any(defs[c]): out[c].append((k, "partial: some entries flagged (units/scope unstated)"))
tot = set()
for c in sorted(out, key=lambda c: -len(out[c])):
    strict = [k for k, why in out[c] if not why.startswith("partial")]
    tot |= set(strict)
    print(f"## {c}: headline in {n_head[c]} papers; undefined {len(strict)}; partial {len(out[c])-len(strict)}")
    for k, why in out[c]: print("   ", k, "-", why)
print("papers with >=1 undefined headline metric (strict):", len(tot), "of", len(full))
