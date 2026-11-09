"""Make pilot/scoring_prompt.md (what the scorer receives) from pilot/scoring_prompt_annotated.md (for readers).
Removes the paragraph citing CLTR's prompt and every [ADAPTED] marker, then checks that the result contains
no "[ADAPTED]" and no "CLTR". Usage: python3 tools/make_scorer_prompt.py [--check]  (--check: fail if the file differs)"""
import re, sys, os
B = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
src = open(f"{B}/pilot/scoring_prompt_annotated.md").read()
out = re.sub(r"\n\nThis prompt adapts the scoring prompt in Shaffer Shane[^\n]*\n", "\n", src, count=1)
out = re.sub(r" ?\[ADAPTED(: [^\]]*)?\]", "", out)
assert "[ADAPTED" not in out and "CLTR" not in out and "Shaffer" not in out, "scorer prompt still has a marker or a CLTR reference"
dst = f"{B}/pilot/scoring_prompt.md"
if "--check" in sys.argv:
    ok = os.path.exists(dst) and open(dst).read() == out
    print("scorer prompt matches annotated copy" if ok else "MISMATCH: run tools/make_scorer_prompt.py"); sys.exit(0 if ok else 1)
open(dst, "w").write(out); print("wrote", dst, len(out), "characters")
