"""Pre-freeze checks (pilot/PILOT_PROTOCOL.md sections 2, 3 and 5). Counts only; no session content is printed or written.
1. Term check: for each keyword term, frame sessions it flags and sessions it alone flags. Threshold: 2% of frame sessions.
2. Call-out window check: stratum sizes with 30 min, 2 h (used), 8 h and end-of-UTC-day windows.
3. Truncation check: share of items longer than each rendering limit, overall and in flagged frame sessions.
4. Share of items cut at alternative limits (frame sessions; chats from 13 October 2025).
5. Size and cost: rendered length of (a) 300 random sessions with a turn in 2026 and (b) a pilot-like mix
   (60 early flagged, 150 late flagged, 100 rest), both drawn with seed 7 (not the pilot seed), under the
   earlier code limits (actions 600, output 1,500, text 1,200) and the current limits.
SIGNALS_VARIANT=original reads outputs/session_signals_original_patterns.csv.gz and writes
outputs/prefreeze_checks_original_patterns.txt (sections 1-3 only, with the limits proposed before the checks:
actions 3,000, output 1,500, text and chat 1,200). Default: outputs/session_signals.csv.gz -> outputs/prefreeze_checks.txt."""
import gzip, orjson, csv, random, collections, bisect, os, sys, statistics as st
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import render as R
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); D = f"{B}/data"; O = f"{B}/outputs"
VARIANT = os.environ.get("SIGNALS_VARIANT", "final")
SIG = f"{O}/session_signals.csv.gz" if VARIANT == "final" else f"{O}/session_signals_original_patterns.csv.gz"
OUT = f"{O}/prefreeze_checks.txt" if VARIANT == "final" else f"{O}/prefreeze_checks_original_patterns.txt"
CAPS = (R.ACTION_CAP, R.OUTPUT_CAP, R.TEXT_CAP) if VARIANT == "final" else (3000, 1500, 1200)
lines = []
def say(*a):
    s = " ".join(str(x) for x in a); print(s); lines.append(s)
say(f"Variant: {VARIANT} | signals file: {os.path.basename(SIG)} | limits for section 3: actions {CAPS[0]}, output {CAPS[1]}, agent text and chat {CAPS[2]}")
sig = list(csv.DictReader(gzip.open(SIG, "rt")))
CC = "Opus 4.5 (Claude Code)"
frame = [r for r in sig if "2025-10-13" <= r["first_utc"] and r["agent"] != CC]
pre = [r for r in sig if r["first_utc"] < "2025-10-13" and r["agent"] != CC]
def flagged(r, w="callout_hits"): return int(r["self_hits"]) > 0 or int(r[w]) > 0
def terms(r): return [t for t in r["self_terms"].split(";") if t] + [t for t in r["call_terms"].split(";") if t]
N = len(frame); thr = 0.02 * N
say(f"Frame sessions: {N} | 2% threshold: {thr:.0f} sessions | latest first turn in frame: {max(r['first_utc'] for r in frame)[:10]}")
say(f"All sessions: {len(sig)}, flagged {sum(1 for r in sig if flagged(r))}")
y26 = [r for r in sig if r["first_utc"] >= "2026-01-01" and r["agent"] != CC]
so = sum(1 for r in y26 if int(r["self_hits"]) > 0 and int(r["callout_hits"]) == 0); co = sum(1 for r in y26 if int(r["self_hits"]) == 0 and int(r["callout_hits"]) > 0)
bo = sum(1 for r in y26 if int(r["self_hits"]) > 0 and int(r["callout_hits"]) > 0)
say(f"2026 frame (first turn from 1 January 2026): {len(y26)} sessions, flagged {so+co+bo} ({so} own-words only, {co} call-out only, {bo} both)")
say("\n1. TERM CHECK (frame sessions; 'alone' = no other term matched in that session)")
tot = collections.Counter(); alone = collections.Counter()
for r in frame:
    ts = set(terms(r))
    for t in ts: tot[t] += 1
    if len(ts) == 1: alone[next(iter(ts))] += 1
say(f"{'term':<16}{'flags':>8}{'alone':>8}{'alone % of frame':>18}  over threshold?")
for t, n in sorted(tot.items(), key=lambda x: (-alone[x[0]], x[0])):
    say(f"{t:<16}{n:>8}{alone[t]:>8}{100*alone[t]/N:>17.2f}%  {'YES' if alone[t] > thr else ''}")
say("\n2. CALL-OUT WINDOW CHECK (flagged = own words, or a call-out linked within the window)")
base = {r["session_id"]: flagged(r) for r in frame}
say(f"{'window':<10}{'early flagged':>15}{'late flagged':>14}{'rest':>9}{'flagged by call-out only':>26}{'moved vs 2 h':>14}")
for w, col in (("30 min", "callout_hits_30m"), ("2 h", "callout_hits"), ("8 h", "callout_hits_8h"), ("UTC day", "callout_hits_day")):
    f = {r["session_id"]: flagged(r, col) for r in frame}
    e = sum(1 for r in frame if f[r["session_id"]] and r["first_utc"] < "2026-02-01"); l = sum(1 for r in frame if f[r["session_id"]] and r["first_utc"] >= "2026-02-01")
    c = sum(1 for r in frame if int(r["self_hits"]) == 0 and int(r[col]) > 0); mv = sum(1 for s in f if f[s] != base[s])
    say(f"{w:<10}{e:>15}{l:>14}{N-e-l:>9}{c:>26}{mv:>14}")
say(f"Flagged sessions before 13 October 2025 (2 h window, excluding {CC}): {sum(1 for r in pre if flagged(r))}")
say(f"\n3. TRUNCATION CHECK (share of items longer than the limit; threshold 5%)")
for label, rows in (("all frame sessions", frame), ("flagged frame sessions", [r for r in frame if flagged(r)])):
    a, ac, o, oc, t, tc = [sum(int(r[k]) for r in rows) for k in ("n_actions", "n_actions_cut", "n_outputs", "n_outputs_cut", "n_texts", "n_texts_cut")]
    say(f"{label}: actions > {CAPS[0]}: {ac}/{a} ({100*ac/max(a,1):.2f}%) | tool outputs/errors > {CAPS[1]}: {oc}/{o} ({100*oc/max(o,1):.2f}%) | agent text > {CAPS[2]}: {tc}/{t} ({100*tc/max(t,1):.2f}%)")
chats = sorted(map(orjson.loads, gzip.open(f"{D}/chat_messages.jsonl.gz", "rb")), key=lambda c: c["created_at"]); ck = [c["created_at"] for c in chats]
cf = [len(c["content"] or "") for c in chats if c["created_at"] >= "2025-10-13"]
say(f"all chat messages from 13 October 2025 > {CAPS[2]}: {sum(x > CAPS[2] for x in cf)}/{len(cf)} ({100*sum(x > CAPS[2] for x in cf)/len(cf):.2f}%)")
if VARIANT == "final":
    say("\n4. SHARE CUT AT ALTERNATIVE LIMITS (frame sessions; chats from 13 October 2025)")
    fr = {r["session_id"] for r in frame}; A = (600, 3000, 4000, 6000, 8000); OC = (1500, 3000, 5000, 8000); na = no = 0
    ca = collections.Counter(); co_ = collections.Counter()
    for line in gzip.open(f"{D}/computer_use_turns.jsonl.gz", "rb"):
        r = orjson.loads(line)
        if r["session_id"] not in fr: continue
        a = r.get("agent_action")
        if isinstance(a, dict):
            det = a.get("command") or a.get("text") or a.get("url") or ""
            if det:
                L = len(str(det)); na += 1
                for c in A: ca[c] += L > c
        for k in ("output", "error"):
            if r.get(k):
                L = len(str(r[k])); no += 1
                for c in OC: co_[c] += L > c
    say("actions: " + ", ".join(f"> {c}: {100*ca[c]/na:.2f}%" for c in A))
    say("tool outputs/errors: " + ", ".join(f"> {c}: {100*co_[c]/no:.2f}%" for c in OC))
    say("chat messages: " + ", ".join(f"> {c}: {100*sum(x > c for x in cf)/len(cf):.2f}%" for c in (1200, 2000, 3000, 5000)))
    say("\n5. SIZE AND COST (tokens = characters / 4; seed 7, not the pilot seed)")
    agents = {a["id"]: a for a in map(orjson.loads, gzip.open(f"{D}/agents.jsonl.gz", "rb"))}; names = {k: v["name"] for k, v in agents.items()}
    sessions = {s["id"]: s for s in map(orjson.loads, gzip.open(f"{D}/computer_use_sessions.jsonl.gz", "rb"))}
    rand = set(random.Random(7).sample(sorted(r["session_id"] for r in sig if r["last_utc"] >= "2026-01-01"), 300))
    e = sorted(r["session_id"] for r in frame if flagged(r) and r["first_utc"] < "2026-02-01"); l = sorted(r["session_id"] for r in frame if flagged(r) and r["first_utc"] >= "2026-02-01")
    rest = sorted(r["session_id"] for r in frame if not flagged(r)); g = random.Random(7)
    mix = set(g.sample(e, 60)) | set(g.sample(l, 150)) | set(g.sample(rest, 100))
    want = rand | mix; turns = collections.defaultdict(list)
    for line in gzip.open(f"{D}/computer_use_turns.jsonl.gz", "rb"):
        r = orjson.loads(line)
        if r["session_id"] in want: turns[r["session_id"]].append(r)
    goals = sorted(map(orjson.loads, gzip.open(f"{D}/village_goals.jsonl.gz", "rb")), key=lambda g: g["start_time"])
    agoals = list(map(orjson.loads, gzip.open(f"{D}/agent_goals.jsonl.gz", "rb")))
    def sizes(ids):
        out = []
        for sid in sorted(ids):
            T = sorted(turns[sid], key=lambda t: t["created_at"]); s = sessions[sid]; a = s["agent_id"]; t0, t1 = T[0]["created_at"], T[-1]["created_at"]
            vg = next((g["goal"] for g in reversed(goals) if g["start_time"] <= t0), "")
            ag = next((g["description"] for g in agoals if g["agent_id"] == a and (g.get("start_time") or "") <= t0 and (g.get("end_time") or "9999") >= t0), None)
            txt = R.render(s, T, chats[bisect.bisect_left(ck, t0):bisect.bisect_right(ck, t1)], vg, ag, names[a], names)
            if len(txt) > 400_000: txt = txt[:200_000] + txt[-200_000:]
            out.append(len(txt) / 4)
        return out
    def old_limits():
        keep = (R.action_str.__defaults__, R.cut_output, R.TEXT_CAP)
        R.action_str.__defaults__ = (600,); R.cut_output = lambda x: str(x)[:1500]; R.TEXT_CAP = 1200
        return keep
    def restore(keep): R.action_str.__defaults__, R.cut_output, R.TEXT_CAP = keep
    ptok = len(open(f"{B}/pilot/scoring_prompt.md").read()) / 4
    say(f"scoring prompt (pilot/scoring_prompt.md): {ptok:.0f} tokens")
    for label, ids in (("300 random sessions with a turn in 2026", rand), ("pilot-like mix (60 early flagged, 150 late flagged, 100 rest)", mix)):
        k = old_limits(); old = sorted(sizes(ids)); restore(k); new = sorted(sizes(ids))
        for lab, v in (("earlier code limits", old), ("current limits", new)):
            m = st.mean(v); cin = 325 * (m + ptok + 10) * 2.5 / 1e6; cout = 325 * 600 * 12.5 / 1e6; cmax = 325 * 2000 * 12.5 / 1e6
            say(f"{label}, {lab}: mean {m:.0f} tokens, median {v[len(v)//2]:.0f}, p90 {v[int(.9*(len(v)-1))]:.0f}, max {v[-1]:.0f}"
                + (f" | pilot cost at batch prices ($2.50/$12.50 per million): input ${cin:.2f} + output ${cout:.2f} = ${cin+cout:.2f}; if every output hit 2,000 tokens: ${cin+cmax:.2f}" if lab == "current limits" else ""))
open(OUT, "w").write("\n".join(lines) + "\n")
