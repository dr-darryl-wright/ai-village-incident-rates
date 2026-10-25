# Additional usage proxies (collected 24 October 2026)

`additional_proxies.csv` adds two proxies that are not Claude-specific, for the same months as `monthly_series.csv`.

**Gemini CLI npm downloads** (`@google/gemini-cli`), monthly totals from
`https://api.npmjs.org/downloads/point/<first day>:<last day>/@google/gemini-cli`. Same source and method as the
Claude Code and Codex series: the same query for `@anthropic-ai/claude-code` returned exactly the values already in
`monthly_series.csv` for October 2025 (23,989,032) and July 2026 (49,100,543).

**OpenRouter total tokens per day** (billions), from the weekly series behind the "Top Models" chart on
openrouter.ai/rankings (endpoint `/api/frontend/v1/rankings/model-rankings-chart`, read in a browser on 24 October 2026).
Weekly total = the nine top models plus "Others". Each week is assigned to the month of its midpoint (start + 3 days),
as for the Google Trends series; the monthly value is the mean tokens per day over those weeks.
- The first week in the series (starting 20 October 2025) is partial (1.22 trillion tokens against 5.51 trillion the
  next week), so October uses only the week starting 27 October.
- Only totals are usable. The per-family split covers just the nine top models each week, so a family drops to zero
  whenever it leaves the top nine.
- OpenRouter's growth over this period is driven largely by low-cost open-weight models (DeepSeek, MiniMax, Tencent,
  Xiaomi, Z.ai), so it is cross-family but not representative of agent use in general.

Growth, Feb-Aug 2026 over Oct 2025-Jan 2026 (mean of monthly per-day values): Gemini CLI 1.68x (CLTR incidents per
unit 1.50x); OpenRouter 6.21x (CLTR incidents per unit 0.40x).
