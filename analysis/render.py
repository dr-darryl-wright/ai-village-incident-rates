"""Render one computer-use session as plain text for the scorer.
Included: the village goal in force, the agent's individual goal (if any), each turn's action
(type + text/command), the agent's own non-reasoning text, tool output and errors (each truncated
to OUTPUT_CAP characters), and chat messages in the session window (all speakers, so instructions
from admins or other agents are visible). Excluded: reasoning/thinking text (see coding rule 4),
screenshots, click coordinates."""
import orjson
OUTPUT_CAP = 1500
def visible_text(o, out):
    """Collect model-visible output text, skipping reasoning blocks."""
    if isinstance(o, dict):
        t = o.get("type")
        if t in ("thinking", "redacted_thinking", "reasoning") or o.get("thought") is True: return
        if t in ("text", "output_text") and isinstance(o.get("text"), str): out.append(o["text"])
        elif "text" in o and isinstance(o["text"], str) and t is None and "thought" not in o: out.append(o["text"])
        if isinstance(o.get("content"), str) and o.get("role") == "assistant": out.append(o["content"])
        for k, v in o.items():
            if k in ("reasoning_content", "reasoning", "thinking", "input", "arguments"): continue
            if isinstance(v, (dict, list)): visible_text(v, out)
    elif isinstance(o, list):
        for v in o: visible_text(v, out)
def action_str(a):
    if not isinstance(a, dict): return "(no action)"
    kind = a.get("action") or ("bash" if "command" in a else "other")
    detail = a.get("command") or a.get("text") or a.get("url") or ""
    return f"{kind}: {str(detail)[:600]}" if detail else kind
def render(session, turns, chats, village_goal, agent_goal, agent_name, names):
    L = [f"AGENT: {agent_name}", f"VILLAGE GOAL: {village_goal}"]
    if agent_goal: L.append(f"AGENT'S INDIVIDUAL GOAL: {agent_goal}")
    L += [f"SESSION INTENTION (agent's own words): {session.get('session_goal') or ''}", "", "--- TIMELINE (UTC) ---"]
    items = [(t["created_at"], "T", t) for t in turns] + [(c["created_at"], "C", c) for c in chats]
    for ts, kind, x in sorted(items, key=lambda i: i[0]):
        hhmm = ts[11:19]
        if kind == "C":
            who = names.get(x.get("agent_speaker_id"), "HUMAN") if x["speaker_type"] == "agent" else "HUMAN (viewer/admin)"
            L.append(f"[{hhmm}] CHAT {who}: {x['content'][:1200]}")
        else:
            out = []; visible_text(x.get("agent_messages"), out); said = " ".join(s.strip() for s in out if s.strip())
            if said: L.append(f"[{hhmm}] AGENT SAYS: {said[:1200]}")
            L.append(f"[{hhmm}] ACTION {action_str(x.get('agent_action'))}")
            for k in ("output", "error"):
                if x.get(k): L.append(f"[{hhmm}]   {k.upper()}: {str(x[k])[:OUTPUT_CAP]}")
    return "\n".join(L)
