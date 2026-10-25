"""Score pilot inputs with the Message Batches API.
  python3 09_score_batch.py submit PILOTDIR   -> submits; writes PILOTDIR/batch_id.txt
  python3 09_score_batch.py fetch  PILOTDIR   -> if finished, writes PILOTDIR/results.jsonl
API key: env ANTHROPIC_API_KEY, else the file 'AI Village grant/.anthropic_key' (never printed)."""
import anthropic, csv, json, os, sys
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MODEL, MAX_TOKENS = "claude-opus-4-6", 2000
mode, pdir = sys.argv[1], sys.argv[2]
key = os.environ.get("ANTHROPIC_API_KEY") or open(f"{B}/.anthropic_key").read().strip()
client = anthropic.Anthropic(api_key=key)
if mode == "submit":
    system = open(f"{B}/pilot/scoring_prompt.md").read()
    reqs = []
    for r in csv.DictReader(open(f"{pdir}/manifest.csv")):
        txt = open(f"{pdir}/inputs/{r['session_id']}.txt").read()
        reqs.append({"custom_id": r["session_id"], "params": {
            "model": MODEL, "max_tokens": MAX_TOKENS, "temperature": 0,
            "system": [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            "messages": [{"role": "user", "content": "Session transcript:\n\n" + txt}]}})
    b = client.messages.batches.create(requests=reqs)
    open(f"{pdir}/batch_id.txt", "w").write(b.id); print("submitted", b.id, len(reqs), "requests")
else:
    bid = open(f"{pdir}/batch_id.txt").read().strip(); b = client.messages.batches.retrieve(bid)
    print("status", b.processing_status, b.request_counts)
    if b.processing_status == "ended":
        with open(f"{pdir}/results.jsonl", "w") as f:
            for r in client.messages.batches.results(bid):
                rec = {"session_id": r.custom_id, "type": r.result.type}
                if r.result.type == "succeeded":
                    m = r.result.message; rec["text"] = "".join(c.text for c in m.content if c.type == "text"); rec["usage"] = m.usage.model_dump()
                else: rec["error"] = str(r.result)
                f.write(json.dumps(rec) + "\n")
        print("results written")
