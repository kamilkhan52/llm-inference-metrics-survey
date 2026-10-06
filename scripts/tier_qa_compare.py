#!/usr/bin/env python3
"""Compare scripted tail tiers with blind coder TQ (qa/tier_qa.json). Usage: python3 -I tier_qa_compare.py <project>"""
import json, collections, sys
P = sys.argv[1].rstrip('/') + '/'
src = open(P + 'scripts/analysis_v3.py').read()
ns = {"__name__": "x"}; sys_argv = sys.argv
exec(src[:src.index('N = len(recs)')], ns)
exec(src[src.index('STRICT_T1 ='):src.index('for label, S in (("ALL full-text", recs), ("online-arrivals or mixed"')], ns)
tier = ns['tier']; recs = {r['key']: r for r in ns['recs']}
qa = json.load(open(P + 'qa/tier_qa.json'))
def blind(t):
    t = t.upper().replace(' ', '')
    return {'T1A': '1', 'T1B': '1', 'T2A': '2a', 'T2B': '2b', 'T3': '3', 'T5': '5'}[t]
def ours(t): return {'1a': '1', '1b': '1', '2a': '2a', '2b': '2b', '3 ': '3', '5 ': '5'}[t[:2]]
pairs = [(q['key'], ours(tier(recs[q['key']])), blind(q['tier']), q.get('note', '')) for q in qa]
n = len(pairs); agree = sum(a == b for _, a, b, _ in pairs)
pa = collections.Counter(a for _, a, _, _ in pairs); pb = collections.Counter(b for _, _, b, _ in pairs)
pe = sum(pa[c] * pb[c] for c in set(pa) | set(pb)) / n / n
print(f"tier agreement {agree}/{n}, Cohen kappa {((agree/n)-pe)/(1-pe):.2f}; ours {dict(pa)} blind {dict(pb)}")
col = lambda x: 'tier1+2a' if x in ('1', '2a') else 'other'
print("collapsed tier1+2a vs rest:", sum(col(a) == col(b) for _, a, b, _ in pairs), "/", n)
for k, a, b, note in pairs:
    if a != b: print("  DIS", k, "ours", a, "blind", b, "|", note[:140])
