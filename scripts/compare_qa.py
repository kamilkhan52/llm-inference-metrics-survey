#!/usr/bin/env python3
"""Compare records/ vs qa/records/ objective+constraint code sets. Usage: python3 -I compare_qa.py <project>"""
import json, glob, os, sys
P = sys.argv[1]
def sets(r):
    o = {m["metric"] for m in r["optimized_metrics"] if m.get("role")=="objective"}
    c = {m["metric"] for m in r["optimized_metrics"] if m.get("role")=="constraint"}
    return o, c
def norm(s): return {("OTHER" if x.startswith("OTHER:") else x) for x in s}
tot = dict(n=0, jo=0.0, ju=0.0, prim=0, cexact=0)
for f in sorted(glob.glob(os.path.join(P,"qa","records","*.json"))):
    k = os.path.basename(f); a = json.load(open(os.path.join(P,"records",k))); b = json.load(open(f))
    oa, ca = map(norm, sets(a)); ob, cb = map(norm, sets(b))
    ua, ub = oa|ca, ob|cb
    jo = len(oa&ob)/len(oa|ob) if oa|ob else 1; ju = len(ua&ub)/len(ua|ub) if ua|ub else 1
    # "primary agreement": first-listed objective of A appears among B's objectives or vice versa
    pa = a["optimized_metrics"][0]["metric"]; pb = b["optimized_metrics"][0]["metric"]
    prim = (norm({pa}) <= ob) or (norm({pb}) <= oa)
    tot["n"]+=1; tot["jo"]+=jo; tot["ju"]+=ju; tot["prim"]+=prim; tot["cexact"]+= (ca==cb)
    print(f"{k:28s} Jobj={jo:.2f} Jall={ju:.2f} prim={'Y' if prim else 'N'}  A:{sorted(oa)};{sorted(ca)}  B:{sorted(ob)};{sorted(cb)}")
n=tot["n"]
if n: print(f"\nn={n} mean Jaccard(objectives)={tot['jo']/n:.2f} mean Jaccard(obj+con)={tot['ju']/n:.2f} primary-objective agreement={tot['prim']}/{n} constraint-set exact={tot['cexact']}/{n}")
