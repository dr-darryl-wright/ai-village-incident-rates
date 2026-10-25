"""Exposure per agent: span hours (first-to-last event per PT day), minus self-pause time
(PAUSE events' `seconds`, capped at the remaining span of that day). Also counts sessions.
Writes outputs/exposure_by_agent.csv."""
import gzip, json, csv, collections, datetime as dt, zoneinfo, os
B = os.path.join(os.path.dirname(__file__), ".."); D = f"{B}/data"; O = f"{B}/outputs"
PT = zoneinfo.ZoneInfo("America/Los_Angeles")
def parse(x):
    base, _, frac = x.partition(".")
    return dt.datetime.fromisoformat(base + ("." + frac.ljust(6, "0") if frac else "")).replace(tzinfo=dt.timezone.utc)
agents = {a["id"]: a for a in map(json.loads, gzip.open(f"{D}/agents.jsonl.gz", "rt"))}
span = {}; pause = collections.Counter(); pause_n = collections.Counter(); seconds_missing = 0
for r in csv.DictReader(open(f"{O}/agent_day_activity.csv")):
    span[(r["agent"], r["pt_date"])] = (parse(r["first_utc"].replace("T", " ")[:26]), parse(r["last_utc"].replace("T", " ")[:26]))
name = {k: v["name"] for k, v in agents.items()}
for line in gzip.open(f"{D}/events.jsonl.gz", "rt"):
    if '"PAUSE"' not in line: continue
    e = json.loads(line); d = e["data"]
    if d.get("actionType") != "PAUSE" or d.get("agentId") not in name: continue
    ts = parse(e["created_at"]); k = (name[d["agentId"]], ts.astimezone(PT).date().isoformat())
    s = d.get("seconds")
    if s is None: seconds_missing += 1; continue
    end = span.get(k, (ts, ts))[1]
    pause[k] += max(0, min(float(s), (end - ts).total_seconds())); pause_n[k] += 1
sess = collections.Counter(name.get(r["agent_id"]) for r in map(json.loads, gzip.open(f"{D}/computer_use_sessions.jsonl.gz", "rt")))
per = collections.defaultdict(lambda: dict(days=0, span=0.0, pause=0.0, first=None, last=None))
for (a, day), (f, l) in span.items():
    p = per[a]; p["days"] += 1; p["span"] += (l - f).total_seconds() / 3600; p["pause"] += pause[(a, day)] / 3600
    p["first"] = min(p["first"] or day, day); p["last"] = max(p["last"] or day, day)
byname = {v["name"]: v for v in agents.values()}
with open(f"{O}/exposure_by_agent.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["agent", "model_string", "joined", "first_active", "last_active", "agent_days", "span_hours", "pause_hours", "net_hours", "sessions"])
    for a, p in sorted(per.items(), key=lambda x: byname[x[0]]["created_at"]):
        w.writerow([a, byname[a]["model_string"], byname[a]["created_at"][:10], p["first"], p["last"], p["days"], round(p["span"], 1), round(p["pause"], 1), round(p["span"] - p["pause"], 1), sess[a]])
print("PAUSE events without seconds:", seconds_missing)
