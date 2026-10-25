"""Pass 1 over events.jsonl.gz: per-agent, per-day activity spans and event counts.
Writes outputs/agent_day_activity.csv and prints event-type counts by month."""
import gzip, json, csv, collections, datetime as dt, zoneinfo, sys, os
D = os.path.join(os.path.dirname(__file__), "..", "data")
O = os.path.join(os.path.dirname(__file__), "..", "outputs")
PT = zoneinfo.ZoneInfo("America/Los_Angeles")
def parse(x):
    """UTC timestamp 'YYYY-MM-DD HH:MM:SS[.f]' with 1-6 fraction digits (Python 3.10 needs 0, 3 or 6)."""
    base, _, frac = x.partition(".")
    return dt.datetime.fromisoformat(base + ("." + frac.ljust(6, "0") if frac else "")).replace(tzinfo=dt.timezone.utc)
agents = {a["id"]: a["name"] for a in map(json.loads, gzip.open(f"{D}/agents.jsonl.gz", "rt"))}
span = {}                       # (agent, ptdate) -> [first, last, n_events, n_talk, n_consol, n_start, n_wait]
bytype = collections.Counter()  # (month, type)
for line in gzip.open(f"{D}/events.jsonl.gz", "rt"):
    e = json.loads(line); d = e["data"]; t = d.get("actionType")
    ts = parse(e["created_at"])
    bytype[(ts.strftime("%Y-%m"), t)] += 1
    a = d.get("agentId") or d.get("speakerId")
    if a not in agents: continue
    k = (a, ts.astimezone(PT).date().isoformat())
    s = span.setdefault(k, [ts, ts, 0, 0, 0, 0, 0])
    s[0] = min(s[0], ts); s[1] = max(s[1], ts); s[2] += 1
    s[3] += t == "AGENT_TALK"; s[4] += t == "CONSOLIDATE"; s[5] += t == "START_USING_COMPUTER"; s[6] += t in ("WAIT", "PAUSE")
with open(f"{O}/agent_day_activity.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["agent", "pt_date", "first_utc", "last_utc", "span_hours", "n_events", "n_talk", "n_consolidate", "n_start_session", "n_wait_pause"])
    for (a, day), s in sorted(span.items(), key=lambda x: (x[0][1], agents[x[0][0]])):
        w.writerow([agents[a], day, s[0].isoformat(), s[1].isoformat(), round((s[1] - s[0]).total_seconds() / 3600, 3), *s[2:]])
months = sorted({m for m, _ in bytype}); types = sorted({t for _, t in bytype}, key=lambda t: -sum(bytype[(m, t)] for m in months))
print("month  " + " ".join(f"{t[:10]:>10}" for t in types[:9]))
for m in months: print(m, " ".join(f"{bytype[(m, t)]:>10}" for t in types[:9]))
print("agent-days:", len(span))
