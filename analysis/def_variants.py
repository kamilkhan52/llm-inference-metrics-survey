#!/usr/bin/env python3
"""Definition-variant assignments for notes/DEFINITIONS.md (agent DEF, 2026-10-06).
Each variant lists the paper keys assigned by reading analysis/definitions_by_metric.md, the records'
metric_definitions/slo_spec/extractor_notes and notes/E01-E15.md (spot-checked against fulltext/ with
def_verify_quotes.py). A paper may sit in several variants of one metric (e.g. it defines TTFT as prefill
duration in one section and from arrival in another). Prints counts and checks every key is a full-text record.
Usage: python3 -I def_variants.py <project_dir>"""
import json, glob, os, sys
P = sys.argv[1]
FULL = {}
for f in glob.glob(os.path.join(P, "records", "*.json")):
    r = json.load(open(f))
    if r.get("read_level") == "full":
        FULL[r["key"]] = r

def k(*ids):  # short arXiv ids -> keys
    return [i if (i.startswith(("osdi", "mlsys", "sosp"))) else "arxiv_" + i for i in ids]

V = {
 # ---------------- TTFT ----------------
 "TTFT": {
  "T1 start = request arrival/submission, queueing stated as included": k(
    "2402.01869", "2403.02310", "2407.00079", "2407.07000", "2504.19867", "2507.17769", "2508.01989", "2512.04013",
    "mlsys2025_sola", "2502.05370", "2503.14649", "2510.18672", "2406.03243", "2602.16603", "2310.07240", "2412.17246"),
  "T2 TTFT defined as = prefill (phase) duration/delay": k(
    "2310.07240", "2311.01282", "2401.09670", "2403.19708", "2405.16444", "2410.01228", "2411.01783", "2504.07494",
    "2506.02634", "2510.09665", "2512.18194", "2510.18672", "2406.01566", "2405.06856", "2410.18038"),
  "T2a ... yet measured under load with queueing (inconsistency flagged by extractor)": k(
    "2401.09670", "2504.07494", "2510.09665", "2512.18194", "2410.18038"),
  "T3 measured offline / single request (no queueing by construction)": k(
    "2311.04934", "2411.00136", "2411.01783", "2502.14866", "2311.01282", "2310.07240", "2411.15100"),
  "T5 includes KV loading/transfer from another tier": k("2310.07240", "2405.16444", "2407.00079", "2508.18572"),
  "T6 covers a whole pre-generation pipeline (RAG / reasoning / tools)": k("2503.14649", "2504.08784", "2510.18672"),
  "T7 includes model scale-up / model switching wait": k("2412.17246", "sosp2025_aegaeon"),
  "T8 queueing explicitly separated (TTFT excl. queue, QTTFT incl.)": k("2506.02634"),
 },
 # ---------------- token pace: TPOT / TBT / ITL ----------------
 "PACE": {
  "P1 TPOT = per-request mean over decode tokens (excl. first token / decode phase only)": k(
    "2401.09670", "2405.06856", "2407.07000", "2410.14257", "2504.19867", "mlsys2025_sola", "2406.03243",
    "2508.01989", "2404.09526", "2501.12162", "2401.14351", "2411.15100", "2505.06371"),
  "P2 named TBT/ITL (inter-token) but defined as an average": k(
    "2311.18677", "2408.13510", "2510.09665", "2510.18672", "2411.00136"),
  "P3 TBT = each inter-token gap is a sample (token-level distribution, percentiles over all tokens)": k(
    "2403.02310", "2410.01228", "2407.00079", "2407.07000", "2410.18038", "2401.08671", "2312.12456", "2408.00741",
    "2501.14808", "2508.16449", "2405.05465", "2505.09999", "2504.02263", "2507.17769", "sosp2025_aegaeon", "2501.01005"),
  "P3b percentile of a request's own gaps, then per-request pass/fail": k("2504.07494"),
  "P4 per-step (iteration) execution time used as TBT/TPOT": k("2410.01228", "2504.02263", "2506.12708", "2507.19427", "2409.17264"),
  "P5 cumulative deadline form (token i due by TTFT + i*x, or reading-speed V*i)": k(
    "2507.17769", "2407.07000", "2410.14257", "2504.20068", "sosp2025_aegaeon", "2501.12162"),
  "P6 maximum / worst case over tokens or windows": k("2504.08784", "2503.14649"),
  "P7 TPOT = whole request latency / output tokens (incl. prefill, queueing)": k("2404.14527"),
  "P8 TPOT and TBT used as synonyms": k("2409.17264", "2503.24000", "2507.17769"),
  "P9 TBT/TPOT distinction made explicit": k("2410.01228", "2504.19867", "2407.07000"),
  "P10 'ITL' term used": k("2501.01005", "2411.00136", "2510.09665", "2510.18672", "2407.00047"),
 },
 # ---------------- E2E ----------------
 "E2E": {
  "E1 per request, arrival/submission -> last token, queueing included (stated)": k(
    "2302.11665", "2311.15566", "2407.00023", "2505.13326", "2510.18672", "2412.17246", "2410.14257", "2404.08509"),
  "E2 per request, start point not stated ('start to finish', 'total query time')": k(
    "2502.07903", "2504.07347", "2311.18677", "2504.20068", "2503.18292", "2401.11181", "2406.14066"),
  "E3 queueing excluded (from scheduling / execution only)": k("2512.15705", "2505.13326", "2405.05465"),
  "E4 wall-clock of a fixed offline batch (no arrivals)": k(
    "2207.00032", "2211.05102", "2306.14048", "2303.06865", "2406.19707", "2402.05099", "2505.11329", "2603.16104"),
  "E5 single request at batch 1": k("2503.24000", "2406.00059"),
  "E6 'end-to-end latency' label on a non-request quantity (prefill pass / per-token time)": k(
    "2211.10438", "2310.19102", "2305.09781", "2406.10774"),
  "E7 reported only as speedup ratio": k("2503.05096", "2406.14066", "2406.00059"),
 },
 # ---------------- normalized latency ----------------
 "NORM_LAT": {
  "N1 mean over requests of E2E / output tokens": k(
    "2309.06180", "2305.05920", "2312.05516", "2408.12757", "2411.01142", "2408.15792", "2512.04013", "2405.19888", "2404.14527"),
  "N2 median over requests": k("osdi2022_orca", "2402.01869", "2403.01876", "2405.05465", "2407.07000"),
  "N3 P90 over requests": k("2312.05516", "2408.15792"),
  "N4 token-weighted: sum(E2E) / sum(output tokens)": k("osdi2024_dlora"),
  "N5 denominator = input + output length": k("2404.09526"),
  "N6 denominator = decode tokens": k("2407.07000"),
  "N7 tool/interception time subtracted": k("2402.01869"),
  "N8 program-level: program time / tokens of all calls": k("2502.13965", "2508.06948", "2412.20993"),
 },
 # ---------------- single-sequence speed ----------------
 "TOKEN_LAT": {
  "S1 ms/token of one sequence at batch 1": k(
    "2210.17323", "2310.17157", "2312.11514", "2309.17453", "2406.10774", "2402.12374", "2411.01783", "2507.07120"),
  "S2 tokens/s of one sequence (often called 'throughput')": k(
    "2306.00978", "2312.12456", "2312.17238", "2402.02057", "2404.16710", "2311.01282", "2502.04563"),
  "S3 wall-clock speedup vs autoregressive decoding": k(
    "2211.17192", "2401.10774", "2401.15077", "2503.01840", "2404.16710", "2402.12374", "2406.14066", "2503.05096"),
  "S4 per-step latency at a fixed batch > 1": k(
    "2408.11049", "2404.14469", "2502.14866", "2207.00032", "2305.09781", "2310.19102", "2211.10438"),
 },
 # ---------------- token throughput ----------------
 "THR_TOK": {
  "K1 input + output tokens": k("2401.00588", "2408.12757", "2410.01228", "2411.00136", "2411.01142", "2404.09526", "2404.14527"),
  "K2 output tokens over prefill+decode time": k(
    "2303.06865", "2306.14048", "2411.11217", "2502.04563", "2310.19102", "2502.07903", "2406.01566", "2508.18572",
    "2510.18672", "2512.15705", "2507.07120", "2402.05099", "2405.04532"),
  "K3 decode phase only (prefill time excluded)": k(
    "2303.06865", "2410.21465", "2504.02263", "2506.12708", "2507.19427", "2405.04437", "2308.16369", "2211.05102"),
  "K4 prefill / input tokens only": k(
    "2403.19708", "2311.18677", "2405.04437", "2407.05858", "2506.12708", "2503.24000", "2404.09526", "2211.05102"),
  "K5 token accounting not stated": k(
    "2402.02750", "2403.00579", "2503.01840", "2505.11329", "2401.15077", "2308.16369", "2501.14808", "2207.00032"),
  "G1 normalised per GPU / accelerator": k("2408.12757", "2504.02263", "2506.12708", "2507.19427", "2507.07120"),
  "G2 explicitly whole system / cluster / node": k("2406.01566", "2502.07903", "2402.05099", "2411.00136", "2512.15705", "2401.00588"),
  "R1 offline, batch pushed to the memory limit": k("2402.02750", "2405.04532", "2401.15077", "2410.21465", "2306.06000"),
  "R3 at fixed batch tuned to a per-token latency target": k("2506.12708", "2507.19427", "2310.19102", "2504.02263", "2404.14527"),
  "R4 analytical upper bound / stability region": k("2408.12757", "2410.21465", "2504.07347"),
 },
 # ---------------- request throughput / capacity ----------------
 "THR_REQ": {
  "Q1 completed requests per s/min, measured": k(
    "2311.03285", "2402.01869", "2407.00047", "2401.08671", "2503.18292", "2512.18194", "2510.18672", "2408.15792",
    "2405.04437", "2410.18038", "osdi2022_orca"),
  "Q2 offline samples / sequences per s": k("2306.06000", "2305.13144"),
  "Q3 programs / jobs per s": k("2312.07104", "2502.13965", "2412.20993", "2511.02230"),
  "Q4 max rate before latency/queueing knee (no explicit SLO)": k("2309.06180", "osdi2022_orca", "2405.04437", "2405.05465", "2402.01869"),
  "Q5 max rate under an explicit latency target (no attainment fraction)": k(
    "2311.18677", "2407.07000", "2305.05920", "2404.09526", "osdi2024_dlora", "2312.05516", "2405.16444", "2510.09665",
    "2407.00079", "2411.01142", "2409.17264", "2505.09999", "2403.02310", "2508.18572"),
  "Q6 queueing-stability (positive recurrence) throughput": k("2504.07347"),
 },
 # ---------------- goodput ----------------
 "GOODPUT": {
  "GP1 max request rate at X% SLO attainment": k(
    "2401.09670", "mlsys2025_sola", "2508.01989", "2507.17769", "sosp2025_aegaeon", "2602.16603", "2504.07494",
    "2504.08784", "2504.19867", "2404.09526", "2305.05920", "2302.11665", "2412.20993"),
  "GP1a ... normalised per GPU": k("2401.09670", "2504.08784"),
  "GP1b ... single SLO only (TTFT only / per-token only / deadline only)": k("2602.16603", "sosp2025_aegaeon", "2302.11665", "2412.20993"),
  "GP2 measured rate (or count) of SLO-meeting requests": k("2401.08671", "2512.04013", "2504.20068", "2412.17246", "2410.14257"),
  "GP3 SLO-meeting tokens per s": k("2501.12162", "2410.14257", "2504.20068"),
  "GP4 fraction of requests meeting deadlines": k("2409.17264"),
  "GP5 no SLO: accepted (correct) tokens per s": k("2406.14066"),
  "GP6 only fully completed in-SLO requests count (aborted work = 0)": k("2407.00079"),
  "GP7 applications completed before deadline": k("2506.14851"),
  "GP8 smooth goodput (benefit minus idle-latency penalty)": k("2410.14257"),
 },
 # ---------------- SLO attainment ----------------
 "SLO_ATT": {
  "A1 per request, all SLOs jointly": k("2401.09670", "mlsys2025_sola", "2405.06856", "2504.07494", "2504.08784", "2512.03416", "2512.04013", "2401.08671"),
  "A2 per request, one metric only": k("2311.03285", "2602.16603", "2310.07240", "2501.12162", "2503.05096", "2407.00047", "2502.07903", "2302.11665"),
  "A3 separate pass rate per metric": k("2508.16449", "2412.17246"),
  "A4 per token (fraction of token deadlines met)": k("sosp2025_aegaeon", "2407.07000"),
  "A5 percentile-threshold SLO (PXX of metric <= bound), no per-request fraction": k(
    "2311.18677", "2407.00079", "2408.00741", "2405.05465", "2505.09999", "2410.01228", "2403.02310", "2501.01005"),
  "A6 program / application deadline attainment": k("2412.20993", "2506.14851"),
  "A7 threshold on a MEAN latency": k("osdi2024_dlora", "2408.12757", "2404.14527", "2505.06371"),
 },
 # ---------------- SLO threshold forms (from slo_spec) ----------------
 "SLO_FORM": {
  "F1 absolute ms/s values": k(
    "2401.09670", "sosp2025_aegaeon", "2505.09999", "2512.03416", "2501.12162", "2512.04013", "2311.03285", "2407.00047",
    "2504.07494", "2504.02263", "2506.12708", "2507.19427", "2404.14527", "2405.05465", "2504.20068", "2501.01005",
    "2408.12757", "2507.17769", "2602.16603", "2508.16449", "2508.01989", "2310.07240", "2407.07000", "2504.19867",
    "2412.17246", "2410.01228", "2306.06000", "2310.19102", "2505.06371", "2409.17264"),
  "F2 multiple of uncontended / single-request / one-iteration latency": k(
    "2302.11665", "2305.05920", "2311.18677", "2403.02310", "2404.09526", "2405.06856", "2407.00079", "2408.00741",
    "2410.01228", "2412.17246", "2501.12162", "2502.07903", "2504.08784", "2504.19867", "2503.05096", "2506.14851",
    "2412.20993", "2512.04013", "mlsys2025_sola", "osdi2024_dlora", "2401.09670", "2501.14808"),
  "F3 TTFT bound depends on prompt length": k("2401.08671", "2408.00741", "2512.03416", "2407.07000", "2404.16283", "2508.16449", "2504.08784", "2504.07494"),
  "F4 justified by human reading speed": k("2306.06000", "2310.19102", "2401.08671", "2404.16283", "2410.14257", "2408.12757", "2404.14527", "2505.06371", "2504.08784"),
  "F5 per-token deadline schedule": k("2407.07000", "2410.14257", "2507.17769", "2504.20068", "sosp2025_aegaeon", "2501.12162"),
 },
 # ---------------- per-user rate ----------------
 "TPS_USER": {
  "U1 per-request token rate defined (tokens/s/user = 1/TPOT or 1/TTL)": k("2401.08671", "2502.04563", "2507.07120", "2507.19427", "2404.16283"),
  "U2 'TPS' used for SYSTEM tokens/s": k("2510.18672", "2501.14808"),
  "U3 'TPS' used for per-request rate": k("2502.05370"),
 },
 # ---------------- program / workflow latency ----------------
 "PROGRAM_JCT": {
  "J1 submission -> final output of the app, under load (incl. queueing)": k("2405.19888", "2407.00326", "2506.14851", "2510.18586", "2511.02230", "2502.13965"),
  "J2 one program at a time (batch 1, no queueing)": k("2312.07104", "2507.07400", "2312.04511", "2406.00059"),
  "J3 normalised per generated token": k("2502.13965", "2508.06948"),
  "J4 batch makespan of many workflows": k("2603.16104"),
  "J5 tool/external time included": k("2510.18586", "2511.02230", "2406.00059", "2506.14851"),
  "J6 tool/external time excluded or subtracted": k("2402.01869", "2502.13965"),
 },
 # ---------------- user-perceived ----------------
 "QOE": {
  "Q-a QoE over token-delivery timeline (Andes)": k("2404.16283"),
  "Q-b soft first-token satisfaction reward": k("2311.03285"),
  "Q-c fluidity-index / fluid token rate": k("2407.07000"),
  "Q-d smooth goodput / user idle latency": k("2410.14257"),
  "Q-e per-token deadline attainment": k("sosp2025_aegaeon", "2504.20068"),
  "Q-f time to first VISIBLE token": k("2510.18672"),
 },
 # ---------------- cost ----------------
 "COST": {
  "C1 GPU/instance count": k("2405.06856", "sosp2025_aegaeon", "2512.03416", "2302.11665", "2306.06000", "2210.17323", "2407.00047", "2404.16283", "2406.03243"),
  "C2 $ per hour (rental) or $ for the workload": k("2404.14527", "2311.15566", "2408.00741", "2405.05465", "2403.19708", "2311.18677"),
  "C3 instance-time (GPU-seconds, resource usage time)": k("2507.17769", "2401.11181", "2412.17246", "2211.05102"),
  "C4 analytic $ per 1M tokens (roofline)": k("2507.19427"),
  "C5 throughput per purchase price / per chip / tokens per $": k("2504.02263", "2503.14649", "2404.14527", "2405.04532"),
  "C6 API token $ / tokens generated as compute proxy": k("2312.04511", "2412.20993"),
  "C7 cost as budget constraint": k("2502.07903"),
 },
 # ---------------- energy ----------------
 "ENERGY": {
  "W1 GPU/accelerator-only scope": k("2505.06371", "2411.00136", "2508.16449"),
  "W2 node-level scope (GPU+CPU+DRAM+other)": k("2512.03024"),
  "W3 total energy (Wh) of an experiment under SLO": k("2408.00741"),
  "W4 energy per token": k("2508.16449", "2512.03024"),
  "W5 energy per response/request": k("2505.06371", "2512.03024"),
  "W6 throughput per watt / iso-power": k("2411.00136", "2504.02263", "2311.18677", "2505.06371"),
 },
}

# Headline / primary metrics used without a definition (curated from extractor flags "never/not formally defined",
# "units not stated", "only acronym"; def_undefined.py gives the raw regex screen). U = no definition at all;
# S = defined loosely but scope (queueing / token type / unit) unstated.
UNDEF = {
 "throughput (tokens or requests)": {
   "U": k("2308.16369", "2401.15077", "2402.02750", "2403.00579", "2503.01840", "2505.11329", "2503.24000", "2311.03285",
          "2404.08509", "2405.16444", "2511.02230", "osdi2022_orca", "mlsys2025_sola", "2309.06180"),
   "S": k("2305.05920", "2411.01142", "2405.04532", "2501.14808", "2207.00032")},
 "TTFT / first-token latency": {
   "U": k("2401.11181", "2312.07104", "2405.05465", "2405.06856", "2501.01005", "2501.14808", "2502.14866", "2503.24000",
          "2508.16449", "2508.18572", "2512.18194", "2606.00946", "2411.15100", "2311.03285", "2404.16283"),
   "S": k("2403.19708", "2410.18038", "2411.19379", "2510.09665", "2408.00741", "2406.01566")},
 "TBT / ITL / TBOT": {"U": k("2405.05465", "2501.01005", "2501.14808", "2508.16449", "2503.24000"), "S": []},
 "E2E / JCT / 'latency'": {
   "U": k("2401.11181", "2404.08509", "2406.14066", "2503.18292", "2407.00326", "2507.07400", "2511.02230", "2505.13326"),
   "S": k("2305.05920")},
 "single-sequence speed": {"U": k("2211.10438", "2309.17453", "2312.12456", "2312.17238", "2507.07120"), "S": []},
 "SLO / attainment": {"U": k("2512.03416", "2404.09526"), "S": []},
 "cost / energy": {"U": k("2401.11181", "2512.03024"), "S": []},
}

def main():
    bad = []
    print("## UNDEFINED headline/primary metrics")
    allu, alls = set(), set()
    for term, d in UNDEF.items():
        print(f"  {term}: undefined {len(d['U'])}, scope-unstated {len(d['S'])}")
        allu |= set(d["U"]); alls |= set(d["S"])
        for x in d["U"] + d["S"]:
            if x not in FULL: bad.append(("UNDEF", term, x))
    print(f"  distinct papers with >=1 undefined headline metric: {len(allu)}; plus scope-unstated only: {len(alls - allu)}; of {len(FULL)}")
    for metric, vs in V.items():
        print(f"## {metric}")
        allk = set()
        for name, keys in vs.items():
            for x in keys:
                if x not in FULL: bad.append((metric, name, x))
            allk |= set(keys)
            print(f"  {len(set(keys)):3d}  {name}")
        print(f"  {len(allk):3d}  (distinct papers in any variant)")
    print("NOT FULL-TEXT RECORDS:", bad if bad else "none")

if __name__ == "__main__":
    main()
