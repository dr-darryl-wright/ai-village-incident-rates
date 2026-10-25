"""Pass over computer_use_turns.jsonl.gz (2.8 GB). Writes:
  outputs/turn_index.csv.gz  - one row per turn: turn_id, session_id, agent, created_utc, action_type
  outputs/turn_activity_by_agent_day.csv - turns and active hours per agent per PT day, where active time is
      the sum of gaps between an agent's consecutive turns, each gap capped at 2, 5 or 10 minutes.
Progress is printed every 100k rows to outputs/03_progress.log."""
import gzip, orjson, csv, collections, datetime as dt, zoneinfo, os, time
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = f"{B}/data"; O = f"{B}/outputs"
PT = zoneinfo.ZoneInfo("America/Los_Angeles")
def parse(x):
    base, _, frac = x.partition(".")
    return dt.datetime.fromisoformat(base + ("." + frac.ljust(6, "0") if frac else "")).replace(tzinfo=dt.timezone.utc)
name = {a["id"]: a["name"] for a in map(orjson.loads, gzip.open(f"{D}/agents.jsonl.gz", "rb"))}
sess_agent = {s["id"]: name.get(s["agent_id"], s["agent_id"]) for s in map(orjson.loads, gzip.open(f"{D}/computer_use_sessions.jsonl.gz", "rb"))}
ts_by_agent = collections.defaultdict(list); missing = 0; t0 = time.time(); log = open(f"{O}/03_progress.log", "w")
with gzip.open(f"{O}/turn_index.csv.gz", "wt", newline="") as fi:
    w = csv.writer(fi); w.writerow(["turn_id", "session_id", "agent", "created_utc", "action_type"])
    for i, line in enumerate(gzip.open(f"{D}/computer_use_turns.jsonl.gz", "rb")):
        r = orjson.loads(line); a = sess_agent.get(r["session_id"])
        if a is None: missing += 1; a = "UNKNOWN"
        act = r.get("agent_action"); typ = (act.get("action") or ("bash" if "command" in act else "other")) if isinstance(act, dict) else "none"
        w.writerow([r["id"], r["session_id"], a, r["created_at"], typ])
        ts_by_agent[a].append(parse(r["created_at"]).timestamp())
        if i % 100000 == 0: print(i, round(time.time() - t0), "s", file=log, flush=True)
caps = (120, 300, 600); rows = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0])
for a, ts in ts_by_agent.items():
    ts.sort()
    for j, t in enumerate(ts):
        day = dt.datetime.fromtimestamp(t, PT).date().isoformat(); r = rows[(a, day)]; r[0] += 1
        if j:
            g = t - ts[j - 1]
            for k, c in enumerate(caps): r[1 + k] += min(g, c)
with open(f"{O}/turn_activity_by_agent_day.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["agent", "pt_date", "turns", "active_h_cap2m", "active_h_cap5m", "active_h_cap10m"])
    for (a, d), r in sorted(rows.items(), key=lambda x: (x[0][1], x[0][0])): w.writerow([a, d, r[0], *(round(x / 3600, 3) for x in r[1:])])
print("DONE rows", i + 1, "sessions missing", missing, round(time.time() - t0), "s", file=log, flush=True)
