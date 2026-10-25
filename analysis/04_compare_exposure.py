"""Compare exposure measures per agent and per month: span (first-last event), span minus pauses,
turn-based active time (gaps capped at 2/5/10 min), and turn counts. Writes outputs/exposure_compare_by_agent.csv."""
import csv, collections, os
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); O = f"{B}/outputs"
ex = {r["agent"]: r for r in csv.DictReader(open(f"{O}/exposure_by_agent.csv"))}
span_m = collections.Counter()
for r in csv.DictReader(open(f"{O}/agent_day_activity.csv")): span_m[r["pt_date"][:7]] += float(r["span_hours"])
t = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0]); tm = collections.defaultdict(lambda: [0, 0.0, 0.0, 0.0])
for r in csv.DictReader(open(f"{O}/turn_activity_by_agent_day.csv")):
    v = [int(r["turns"]), float(r["active_h_cap2m"]), float(r["active_h_cap5m"]), float(r["active_h_cap10m"])]
    for acc in (t[r["agent"]], tm[r["pt_date"][:7]]):
        for i in range(4): acc[i] += v[i]
print("month    span_h  turn_h_cap5m  ratio  turns")
for m in sorted(span_m): print(m, f"{span_m[m]:7.0f} {tm[m][2]:10.0f} {tm[m][2]/span_m[m]:7.2f} {tm[m][0]:8}")
with open(f"{O}/exposure_compare_by_agent.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["agent", "joined", "span_h", "net_h_minus_pause", "turn_h_cap2m", "turn_h_cap5m", "turn_h_cap10m", "turns", "turns_per_net_h"])
    for a, r in ex.items():
        v = t.get(a, [0, 0, 0, 0]); net = float(r["net_hours"])
        w.writerow([a, r["joined"], r["span_hours"], r["net_hours"], *(round(x, 1) for x in v[1:]), v[0], round(v[0] / net, 1) if net else ""])
