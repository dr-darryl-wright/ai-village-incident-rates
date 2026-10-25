"""'Recently released models' series: on each PT date, keep hours only from agents that joined the Village within the
previous W days (W = 90 main; 60 and 180 as checks). Village join dates track public release closely for most models.
Excluded: fine-tuned leaders, the Claude Code agent, and Claude 3 Opus (an older model re-added in September 2026, so
its join date does not reflect its release). Writes outputs/recent_models_by_day.csv."""
import csv, gzip, json, os, datetime as dt
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
EXCL = {"Opus 4.5 (Claude Code)", "Claude 3 Opus", "Fine-Tuned Leader", "[Temporary] Fine-tuned Leader"}
join = {a["name"]: dt.date.fromisoformat(a["created_at"][:10]) for a in map(json.loads, gzip.open(f"{B}/data/agents.jsonl.gz", "rt"))}
rows = []
for r in csv.DictReader(open(f"{B}/outputs/active_hours_by_agent_day.csv")):
    if r["agent"] in EXCL: continue
    age = (dt.date.fromisoformat(r["pt_date"]) - join[r["agent"]]).days
    rows.append((r["pt_date"], r["agent"], age, float(r["active_h_cap5m"])))
with open(f"{B}/outputs/recent_models_by_day.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["pt_date", "agent", "days_since_join", "active_h_cap5m"]); w.writerows(rows)
for n, a, b in (("P1 13 Oct 2025-31 Jan 2026", "2025-10-13", "2026-01-31"), ("P2 1 Feb-9 Aug 2026", "2026-02-01", "2026-08-09")):
    out = []
    for W in (60, 90, 180):
        sel = [x for x in rows if a <= x[0] <= b and x[2] <= W]
        out.append(f"{W}d: {sum(x[3] for x in sel):.0f} h, {len({x[1] for x in sel})} models")
    print(n, "|", " | ".join(out))
