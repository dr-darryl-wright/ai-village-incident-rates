"""Primary exposure measure: active hours per agent per PT day from the union of
(a) computer-use turn timestamps and (b) the agent's own events (talk, session start/stop,
consolidate, search, outreach requests; NOT wait/pause, which are idling).
Active time = sum of gaps between consecutive activity timestamps, each gap capped (2, 5, 10 min).
Writes outputs/active_hours_by_agent_day.csv and outputs/active_hours_by_agent.csv."""
import gzip, orjson, csv, collections, datetime as dt, zoneinfo, os
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = f"{B}/data"; O = f"{B}/outputs"
PT = zoneinfo.ZoneInfo("America/Los_Angeles")
def parse(x):
    base, _, frac = x.partition(".")
    return dt.datetime.fromisoformat(base + ("." + frac.ljust(6, "0") if frac else "")).replace(tzinfo=dt.timezone.utc).timestamp()
name = {a["id"]: a["name"] for a in map(orjson.loads, gzip.open(f"{D}/agents.jsonl.gz", "rb"))}
ts = collections.defaultdict(list); idle = {"WAIT", "PAUSE"}
for line in gzip.open(f"{D}/events.jsonl.gz", "rb"):
    e = orjson.loads(line); d = e["data"]; a = d.get("agentId") or d.get("speakerId")
    if a in name and d.get("actionType") not in idle: ts[name[a]].append(parse(e["created_at"]))
for r in csv.DictReader(gzip.open(f"{O}/turn_index.csv.gz", "rt")): ts[r["agent"]].append(parse(r["created_utc"]))
caps = (120, 300, 600); day = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0])
for a, v in ts.items():
    v.sort()
    for j, t in enumerate(v):
        r = day[(a, dt.datetime.fromtimestamp(t, PT).date().isoformat())]; r[0] += 1
        if j:
            g = t - v[j - 1]
            for k, c in enumerate(caps): r[1 + k] += min(g, c)
tot = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0, 0])
with open(f"{O}/active_hours_by_agent_day.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["agent", "pt_date", "activity_points", "active_h_cap2m", "active_h_cap5m", "active_h_cap10m"])
    for (a, d), r in sorted(day.items(), key=lambda x: (x[0][1], x[0][0])):
        w.writerow([a, d, r[0], *(round(x / 3600, 3) for x in r[1:])]); T = tot[a]
        for i in range(4): T[i] += r[i]
        T[4] += 1
with open(f"{O}/active_hours_by_agent.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["agent", "active_days", "activity_points", "active_h_cap2m", "active_h_cap5m", "active_h_cap10m"])
    for a, T in sorted(tot.items(), key=lambda x: -x[1][2]): w.writerow([a, T[4], T[0], *(round(x / 3600, 1) for x in T[1:4])])
s = [sum(T[i] for T in tot.values()) for i in range(4)]
print("activity points", s[0], "| active hours cap2/5/10:", *(round(x / 3600) for x in s[1:]))
