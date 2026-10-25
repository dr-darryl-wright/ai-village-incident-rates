"""Share of computer-use turns with readable reasoning text (>= 50 characters), per agent per month.
Reasoning text = Anthropic `thinking` blocks, OpenAI `reasoning` item summaries/content, Gemini parts with
`thought: true`, and `reasoning_content`/`reasoning` strings (e.g. DeepSeek). Encrypted or redacted reasoning
does not count. Writes outputs/reasoning_visibility_by_agent_month.csv."""
import gzip, orjson, csv, collections, os, time
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = f"{B}/data"; O = f"{B}/outputs"
name = {a["id"]: a["name"] for a in map(orjson.loads, gzip.open(f"{D}/agents.jsonl.gz", "rb"))}
sa = {s["id"]: name.get(s["agent_id"]) for s in map(orjson.loads, gzip.open(f"{D}/computer_use_sessions.jsonl.gz", "rb"))}
def rtext(o, out):
    if isinstance(o, dict):
        t = o.get("type")
        if t == "thinking" and isinstance(o.get("thinking"), str): out.append(o["thinking"])
        elif t == "reasoning":
            for k in ("summary", "content"):
                for s in o.get(k) or []:
                    if isinstance(s, dict) and isinstance(s.get("text"), str): out.append(s["text"])
        if o.get("thought") is True and isinstance(o.get("text"), str): out.append(o["text"])
        for k in ("reasoning_content", "reasoning"):
            if isinstance(o.get(k), str): out.append(o[k])
        for v in o.values():
            if isinstance(v, (dict, list)): rtext(v, out)
    elif isinstance(o, list):
        for v in o: rtext(v, out)
c = collections.defaultdict(lambda: [0, 0]); t0 = time.time()
for i, line in enumerate(gzip.open(f"{D}/computer_use_turns.jsonl.gz", "rb")):
    if b"thinking" not in line and b"reasoning" not in line and b'"thought"' not in line:
        r = orjson.loads(line); k = (sa.get(r["session_id"]), r["created_at"][:7]); c[k][0] += 1; continue
    r = orjson.loads(line); out = []; rtext(r.get("agent_messages"), out)
    k = (sa.get(r["session_id"]), r["created_at"][:7]); c[k][0] += 1; c[k][1] += sum(len(x) for x in out) >= 50
with open(f"{O}/reasoning_visibility_by_agent_month.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["agent", "month", "turns", "turns_with_reasoning", "share"])
    for (a, m), (n, k) in sorted(c.items(), key=lambda x: (x[0][0] or "", x[0][1])): w.writerow([a, m, n, k, round(k / n, 3)])
print("done", i + 1, round(time.time() - t0), "s")
