"""Draw the pilot sample and recall set (rules in pilot/PILOT_PROTOCOL.md) and render each session.
Usage: python3 08b_build_pilot_inputs.py SEED OUTDIR
Writes OUTDIR/manifest.csv and OUTDIR/inputs/<session_id>.txt."""
import gzip, orjson, csv, random, re, bisect, collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from render import render, visible_text
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = f"{B}/data"; O = f"{B}/outputs"
seed = int(sys.argv[1]); out = sys.argv[2]; os.makedirs(f"{out}/inputs", exist_ok=True)
N_EARLY, N_FLAG, N_REST, MAX_CHARS = 60, 150, 100, 400_000
sig = list(csv.DictReader(gzip.open(f"{O}/session_signals.csv.gz", "rt")))
isflag = lambda r: int(r["self_hits"]) > 0 or int(r["callout_hits"]) > 0
frame = [r for r in sig if "2025-10-13" <= r["first_utc"] and r["agent"] != "Opus 4.5 (Claude Code)"]
early = sorted(r["session_id"] for r in frame if isflag(r) and r["first_utc"] < "2026-02-01")   # CLTR's first period
flag = sorted(r["session_id"] for r in frame if isflag(r) and r["first_utc"] >= "2026-02-01")
rest = sorted(r["session_id"] for r in frame if not isflag(r))
rng = random.Random(seed)
pick = {s: "early_flagged" for s in rng.sample(early, N_EARLY)}
pick.update({s: "flagged" for s in rng.sample(flag, N_FLAG)}); pick.update({s: "rest" for s in rng.sample(rest, N_REST)})
# Recall set: known episodes, located by fixed queries over visible text; top 5 sessions by match count each.
EP = {"R1_deepseek_relationship_metric": dict(agent="DeepSeek-V3.2", start="2026-01-01", end="2026-10-07", pats=[r"relationship[- ]scor"]),
      "R2_impressiveness_loops": dict(agent=None, start="2026-06-15", end="2026-06-20", pats=[r"impressive", r"loop|arithmetic|iteration|million"]),
      "R3_claude_outreach_claims": dict(agent="Claude", start="2025-10-20", end="2025-11-15", pats=[r"partner|endorse", r"email|gmail|send"])}
meta = {r["session_id"]: r for r in sig}; cand = collections.defaultdict(collections.Counter)
agents = {a["id"]: a for a in map(orjson.loads, gzip.open(f"{D}/agents.jsonl.gz", "rb"))}; names = {k: v["name"] for k, v in agents.items()}
sessions = {s["id"]: s for s in map(orjson.loads, gzip.open(f"{D}/computer_use_sessions.jsonl.gz", "rb"))}
turns = collections.defaultdict(list)
for line in gzip.open(f"{D}/computer_use_turns.jsonl.gz", "rb"):
    r = orjson.loads(line); s = r["session_id"]; m = meta.get(s)
    if s in pick: turns[s].append(r)
    for ep, q in EP.items():
        if m and q["start"] <= m["first_utc"] < q["end"] and (q["agent"] is None or (m["agent"] or "").startswith(q["agent"])):
            o = []; visible_text(r.get("agent_messages"), o); t = " ".join(o) + " " + str(r.get("agent_action") or "")
            if all(re.search(p, t, re.I) for p in q["pats"]): cand[ep][s] += 1; turns.setdefault(("R", s), []).append(r)
recall = {}
for ep, c in cand.items():
    for s, _ in c.most_common(5): recall[s] = ep
need = set(recall) - set(pick)
if need:  # second pass only for recall sessions (full turns, not just matching ones)
    for line in gzip.open(f"{D}/computer_use_turns.jsonl.gz", "rb"):
        r = orjson.loads(line)
        if r["session_id"] in need: turns[r["session_id"]].append(r)
goals = sorted(map(orjson.loads, gzip.open(f"{D}/village_goals.jsonl.gz", "rb")), key=lambda g: g["start_time"])
agoals = list(map(orjson.loads, gzip.open(f"{D}/agent_goals.jsonl.gz", "rb")))
chats = sorted(map(orjson.loads, gzip.open(f"{D}/chat_messages.jsonl.gz", "rb")), key=lambda c: c["created_at"]); ck = [c["created_at"] for c in chats]
with open(f"{out}/manifest.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["session_id", "agent", "first_utc", "stratum", "recall_episode", "turns", "chars", "truncated"])
    for s in list(pick) + [x for x in recall if x not in pick]:
        T = sorted(turns[s], key=lambda t: t["created_at"]); se = sessions[s]; a = se["agent_id"]; t0, t1 = T[0]["created_at"], T[-1]["created_at"]
        vg = next((g["goal"] for g in reversed(goals) if g["start_time"] <= t0), "")
        ag = next((g["description"] for g in agoals if g["agent_id"] == a and (g.get("start_time") or "") <= t0 and (g.get("end_time") or "9999") >= t0), None)
        txt = render(se, T, chats[bisect.bisect_left(ck, t0):bisect.bisect_right(ck, t1)], vg, ag, names[a], names); trunc = len(txt) > MAX_CHARS
        if trunc: txt = txt[:MAX_CHARS // 2] + "\n\n[... middle of session omitted for length ...]\n\n" + txt[-MAX_CHARS // 2:]
        open(f"{out}/inputs/{s}.txt", "w").write(txt)
        w.writerow([s, names[a], t0, pick.get(s, "recall_only"), recall.get(s, ""), len(T), len(txt), trunc])
print("sample", len(pick), "| early", len(early), "flagged", len(flag), "rest", len(rest), "| recall", len(recall), {ep: len(c) for ep, c in cand.items()}, "| written to", out)
