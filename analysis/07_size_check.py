"""Size check for cost: render 300 random 2026 sessions (seed 7, NOT the pilot seed) and report token estimates."""
import gzip, orjson, csv, random, collections, bisect, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from render import render
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = f"{B}/data"; O = f"{B}/outputs"
agents = {a["id"]: a for a in map(orjson.loads, gzip.open(f"{D}/agents.jsonl.gz", "rb"))}; names = {k: v["name"] for k, v in agents.items()}
sessions = {s["id"]: s for s in map(orjson.loads, gzip.open(f"{D}/computer_use_sessions.jsonl.gz", "rb"))}
frame = sorted({r["session_id"] for r in csv.DictReader(gzip.open(f"{O}/turn_index.csv.gz", "rt")) if r["created_utc"] >= "2026-01-01"})
pick = set(random.Random(7).sample(frame, 300)); turns = collections.defaultdict(list)
for line in gzip.open(f"{D}/computer_use_turns.jsonl.gz", "rb"):
    r = orjson.loads(line)
    if r["session_id"] in pick: turns[r["session_id"]].append(r)
goals = sorted(map(orjson.loads, gzip.open(f"{D}/village_goals.jsonl.gz", "rb")), key=lambda g: g["start_time"])
agoals = list(map(orjson.loads, gzip.open(f"{D}/agent_goals.jsonl.gz", "rb")))
chats = sorted(map(orjson.loads, gzip.open(f"{D}/chat_messages.jsonl.gz", "rb")), key=lambda c: c["created_at"]); ckeys = [c["created_at"] for c in chats]
toks = []; nturns = []
for sid in pick:
    T = sorted(turns[sid], key=lambda t: t["created_at"]); s = sessions[sid]; a = s["agent_id"]; t0, t1 = T[0]["created_at"], T[-1]["created_at"]
    vg = next((g["goal"] for g in reversed(goals) if g["start_time"] <= t0), "")
    ag = next((g["description"] for g in agoals if g["agent_id"] == a and (g.get("start_time") or "") <= t0 and (g.get("end_time") or "9999") >= t0), None)
    C = chats[bisect.bisect_left(ckeys, t0):bisect.bisect_right(ckeys, t1)]
    txt = render(s, T, C, vg, ag, names[a], names); toks.append(len(txt) / 4); nturns.append(len(T))
toks.sort(); q = lambda p: toks[int(p * (len(toks) - 1))]
print(f"sessions {len(toks)} | turns/session median {st.median(nturns)} | est tokens/session median {q(.5):.0f}, mean {st.mean(toks):.0f}, p90 {q(.9):.0f}, max {toks[-1]:.0f}")
