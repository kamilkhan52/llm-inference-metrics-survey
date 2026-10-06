#!/usr/bin/env python3
"""Overview of metric definitions per record. Usage: python3 -I def_overview.py <project_dir>"""
import json, glob, os, sys, csv, collections
P = sys.argv[1]
sel = {row["key"]: row for row in csv.DictReader(open(os.path.join(P, "SELECTION.tsv")), delimiter="\t")}
recs = [json.load(open(f)) for f in sorted(glob.glob(os.path.join(P, "records", "*.json")))]
cnt = collections.Counter(); papers = collections.defaultdict(set)
tracks = collections.Counter()
for r in recs:
    tr = sel.get(r["key"], {}).get("track", "?"); tracks[(tr, r.get("read_level"))] += 1
    for d in r.get("metric_definitions", []) or []:
        c = d.get("canonical"); cnt[c] += 1; papers[c].add(r["key"])
print(tracks)
for c, n in cnt.most_common(40):
    print(f"{c:30s} defs={n:3d} papers={len(papers[c])}")
# abstract-only records with definitions
ab = [r["key"] for r in recs if r.get("read_level") == "abstract" and r.get("metric_definitions")]
print("abstract records with defs:", len(ab), ab[:10])
