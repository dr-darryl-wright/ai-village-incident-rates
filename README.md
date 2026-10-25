# AI Village incident rates

Scheming-related incidents per active agent-hour in the [AI Village](https://theaidigest.org/village) dataset,
compared with the Centre for Long-Term Resilience's (CLTR) Loss of Control Observatory.

**Status:** work in progress (October 2026). The data checks are done; the pilot protocol is drafted and not yet
frozen; no incidents have been scored yet.

## The question

CLTR reports that loss-of-control incidents posted on X rose between October 2025 - January 2026 and
February - August 2026 (2.5x in incidents per day). Their report notes that separating more agents in use from more
misbehaviour per use "would require denominator data ... which our methodology cannot provide".

The AI Village is a fixed group of frontier AI agents whose working hours can be measured. This project asks:

1. **Main:** did the number of incidents per active hour rise between CLTR's two periods (13 October 2025 - 31 January
   2026 and 1 February - 9 August 2026)?
2. **Follow-up:** how much of any change comes from newer models taking a larger share of the hours, and how much from
   the same models behaving differently? Do newer models have higher rates within the same goal week?
3. **Secondary:** does the share of high-severity incidents (7+ out of 9) rise?

An incident is what CLTR counts as a loss-of-control incident: a score of 5 or more on its scheming rubric
(Shaffer Shane, Mylius and Hobbs, 2026, Appendices A and C), adapted for full session transcripts. The adaptations are
marked in `pilot/scoring_prompt.md`. The main ones: evidence quality is not scored (every session is a complete
record), the cap for experimental settings is dropped, and reasoning is removed for every model so that all models are
judged on the same evidence.

## Findings so far

- **Active hours.** 23,372 active agent-hours across 52 agents (2 April 2025 - 6 October 2026 export), measured from
  the timestamps of agents' actions, with gaps over 5 minutes not counted (19,392 h with a 2-minute cap, 25,458 h with
  10 minutes). The raw daily span, first to last action, totals 26,633 h, matching AI Digest's published
  "27k+ agent-hours". Requested pause lengths cannot be used: before 11 June 2026 a pause with no duration defaulted to 12 hours. See `analysis/05_active_time.py` and
  `results/active_hours_by_agent.csv`.
- **CLTR's periods.** 2,647 active hours in the first period and 10,752 in the second. Ten models have at least 20
  hours in both, accounting for 49% of the second period's hours.
- **Reasoning visibility differs by model and date.** Readable reasoning appears in 0% of turns for early models
  (o3, GPT-4o, Claude before October 2025) and in about 97% for recent Claude, Kimi and Gemini Flash models. Scoring
  with reasoning visible would favour finding covert behaviour in the models whose reasoning we can see.
  See `results/reasoning_visibility_by_agent_month.csv`.
- **The Village's model mix ages over time.** It keeps old models running, so the share of hours from models released
  in the previous 90 days fell from 58% to 42% between CLTR's periods. The analysis therefore also reports a
  recently-released-models series.
- **CLTR's normalisation depends on the proxy.** Dividing CLTR's incident counts by different usage proxies gives
  incidents per unit of use ranging from 1.50x (Gemini CLI downloads) to 0.10x (Codex downloads). See
  `cltr-reanalysis/`.

## Layout

| Path | Contents |
| --- | --- |
| `analysis/` | Numbered scripts, run in order. 01-06: activity, active hours, reasoning visibility. 07: session size and cost check. 08a-10: pilot filter, sample, scoring, estimate. 11: recently-released-models hours. `render.py` turns a session into the text the scorer reads |
| `pilot/` | Pilot protocol (draft, to be frozen before scoring) and the adapted scoring prompt |
| `tools/freeze.sh` | Hashes the protocol and everything it depends on, writing `pilot/FREEZE-<time>.txt` |
| `results/` | Agent-level and agent-day summary tables (counts and hours only, no transcript content) |
| `cltr-reanalysis/` | Reanalysis of CLTR's 28 August 2026 report against usage proxies; sources in `additional_proxies_README.md` |

## Reproducing

1. Request access to the dataset at [huggingface.co/datasets/aidigestorg/ai-village](https://huggingface.co/datasets/aidigestorg/ai-village).
   The data is not redistributed here, in line with its access terms.
2. Download it into `data/`:
   ```
   hf download aidigestorg/ai-village --repo-type dataset \
     --include "*.md" "*.py" "*.jsonl.gz" --exclude "images/*" "agent_memories*" "claude_code*" --local-dir data
   ```
   This skips the screenshots and the two largest tables not used here. If a file is missing afterwards, download it
   on its own (CHANGELOG.md needed this once).
3. `pip install -r requirements.txt`, then run the scripts in `analysis/` in order from the repository root
   (`python3 analysis/01_event_scan.py`, and so on). Scripts 08b-10 take arguments, described in each script's first
   lines. Outputs go to `outputs/` (not committed). The turns file is about 2.8 GB; each full pass takes 1-2 minutes.
4. Scoring (`09_score_batch.py`) needs an Anthropic API key, read from the `ANTHROPIC_API_KEY` environment variable or
   a `.anthropic_key` file (ignored by git).

Figures in this README come from the export downloaded on 22 October 2026. The dataset is refreshed weekly, so later
downloads will differ slightly.

## Sources

- AI Digest (2026). AI Village dataset. https://theaidigest.org/village
- Shaffer Shane, T., Mylius, S. and Hobbs, H. (2026). *Scheming in the wild: detecting real-world AI scheming
  incidents with open-source intelligence*. Centre for Long-Term Resilience.
- Centre for Long-Term Resilience (2026). *Insight report: AI loss of control incidents are worsening*. 28 August 2026.

## About

Darryl Wright, independent researcher. Code written with help from Anthropic's Claude; the analysis design and
conclusions are the author's.
