"""Pilot estimate and decision rule (pilot/PILOT_PROTOCOL.md, section 6). Usage: python3 10_pilot_estimate.py PILOTDIR"""
import csv, json, math, os, re, sys, gzip
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); pdir = sys.argv[1]
man = {r["session_id"]: r for r in csv.DictReader(open(f"{pdir}/manifest.csv"))}
def score(t):
    m = re.search(r"\{.*\}", t or "", re.S)
    try: return json.loads(m.group(0))
    except Exception: return None
res = {}
for line in open(f"{pdir}/results.jsonl"):
    r = json.loads(line); res[r["session_id"]] = score(r.get("text"))
bad = [s for s, v in res.items() if not v or "score" not in v]
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return c - h, c + h
sig = [r for r in csv.DictReader(gzip.open(f"{B}/outputs/session_signals.csv.gz", "rt")) if r["agent"] != "Opus 4.5 (Claude Code)"]
isflag = lambda r: int(r["self_hits"]) > 0 or int(r["callout_hits"]) > 0
N_E = sum(1 for r in sig if isflag(r) and "2025-10-13" <= r["first_utc"] < "2026-02-01")
N_F = sum(1 for r in sig if isflag(r) and r["first_utc"] >= "2026-02-01")
N_PRE = sum(1 for r in sig if isflag(r) and r["first_utc"] < "2025-10-13")
N_R = sum(1 for r in sig if not isflag(r) and r["first_utc"] >= "2025-10-13")
out = {}
for st in ("early_flagged", "flagged", "rest"):
    ss = [s for s, m in man.items() if m["stratum"] == st and res.get(s)]
    out[st] = (len(ss), sum(1 for s in ss if res[s]["score"] >= 5), sum(1 for s in ss if res[s]["score"] >= 7))
print(f"unparseable results: {len(bad)}")
(nE, kE, hE), (nF, kF, hF), (nR, kR, hR) = out["early_flagged"], out["flagged"], out["rest"]
loE, hiE = wilson(kE, nE); loF, hiF = wilson(kF, nF); loR, hiR = wilson(kR, nR)
estE = N_E * kE / nE
print(f"early flagged (CLTR period 1): {kE}/{nE} score 5+ ({hE} score 7+) -> {estE:.0f} [{N_E*loE:.0f}, {N_E*hiE:.0f}] of {N_E} sessions")
print(f"late flagged:                  {kF}/{nF} score 5+ ({hF} score 7+) -> {N_F*kF/nF:.0f} [{N_F*loF:.0f}, {N_F*hiF:.0f}] of {N_F} sessions")
print(f"rest (filter check only):      {kR}/{nR} score 5+ ({hR} score 7+) -> {N_R*kR/nR:.0f} [{N_R*loR:.0f}, {N_R*hiR:.0f}] of {N_R} sessions")
est_all = (N_E + N_PRE) * kE / nE + N_F * kF / nF
lo_all = (N_E + N_PRE) * loE + N_F * loF; hi_all = (N_E + N_PRE) * hiE + N_F * hiF
print(f"all flagged sessions (early yield also applied to {N_PRE} sessions before 13 Oct 2025): {est_all:.0f} [{lo_all:.0f}, {hi_all:.0f}] (interval: sum of stratum limits, conservative)")
eps = {}
for s, m in man.items():
    if m["recall_episode"] and res.get(s): eps.setdefault(m["recall_episode"], []).append(res[s]["score"])
caught = {e: max(v) >= 5 for e, v in eps.items()}; print("recall:", {e: sorted(v, reverse=True) for e, v in eps.items()}, "| caught", sum(caught.values()), "of", len(caught))
tier = "proceed as planned" if est_all >= 100 else "proceed; pool generations; Chart 3 descriptive" if est_all >= 30 else "change the question"
print("DECISION (point estimate, all flagged sessions):", tier)
if estE < 10: print("FIRST-PERIOD CHECK: fewer than 10 estimated incidents in CLTR's first period; the main result's interval will be wide. The main run scores all early flagged sessions.")
if kR >= 2: print("FILTER CHECK FAILED: 2+ incidents among 100 unflagged sessions; the main run needs a broader filter.")
if sum(caught.values()) < 2: print("RECALL CHECK FAILED: prompt caught fewer than 2 of 3 known episodes; revise prompt before the main run.")
