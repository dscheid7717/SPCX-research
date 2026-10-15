# Decision Memo — NVIDIA (NVDA)

**To:** Investment Committee (no current position) · **From:** Drew Scheiderer, AI task force
**As of:** October 14, 2026 · **Price:** $221.30 · USD; per-share values on 24,514M diluted shares

> Coursework for a learning exercise. Not investment research and not financial advice.

## Decision and committee ask

**WATCH/DEFER. Do not initiate at $221.30.** My FCFF valuation range is **$49–$115 per share,
base $79**. No case I can support from NVIDIA's own filings reaches the price. I am not
recommending *do not initiate* because NVIDIA is the cheapest of its admitted peers on
EV/EBITDA while earning the best margins, and in my base case those earnings keep growing.

**Ask:** keep NVDA on the watch list. Re-review at the Q3 FY2027 10-Q (quarter ending late
October 2026) against the triggers below.

## Evidence and as-of date

| | Value | Type | Source |
|---|---|---|---|
| H1 FY2027 revenue | 177,837 (+95.8% YoY) | fact | 10-Q, period 2026-07-26, filed 2026-08-26 |
| H1 FY2027 gross margin | 74.96% | fact | same 10-Q |
| FY2026 revenue / normalised GM | 215,938 / 72.92% (reported 71.07% less a 4,000 write-down) | fact / normalisation | 10-K, filed 2026-02-25 |
| Cost of equity / WACC | 16.27% / 16.25% | estimate | 5.19% UST (2026-10-14) + own beta 2.216 × 5% ERP |
| Base value per share | $79 (EV 1,856,186; terminal value 57% of EV) | model output | `nvidia/analysis.py` |
| EV/EBITDA, trailing | NVDA 40.3×, AVGO 50.7×, AMD 138.3× | model output | 10-K XBRL; 2026-10-14 prices |

**Bridge:** EV 1,856,186 + cash and securities 62,556 + non-marketable equity stakes 22,251
− debt 8,468 = equity 1,932,525 ÷ 24,514M diluted shares = **$78.83**. The FCFE build on the
same statements gives $76.06. The two agree because they use the same forecast, so the
agreement shows the model's arithmetic is consistent. It doesn't show the inputs are right.

## Why the methods disagree, and why I do not average them

The DCF gives $79. AVGO's EV/EBITDA applied to NVIDIA gives about $278. The 3.5× gap is
information, not noise:

- **The DCF depends on beta.** NVIDIA is 99.8% equity-funded, so WACC is simply its cost of
  equity. The reverse DCF shows the price needs a beta of **0.51** (cost of equity 7.74%) on my
  operating forecast. On my 16.25% discount rate, it needs FY2028–31 growth **45 points
  above** my path every year.

- **The comps depend on the peers' earnings.** AMD's multiple is inflated by thin margins and
  acquisition amortisation. With two peers, the multiples show where NVIDIA ranks, not what it
  is worth.

The DCF sets the range. The comps only decide whether the name stays on watch.

## Material assumptions and sensitivities

| Case / what-if | Value per share | Action under the rule |
|---|---:|---|
| **Low: AI capex digestion** (H2 FY2027 = H1; FY2028 revenue −10%; GM to 65%) | $49 | **DO NOT INITIATE** |
| **Base** (H1 + flat H2; then 22/16/11/7%; GM 75% → 69%) | $79 | WATCH/DEFER |
| **High: sustained build-out** (+80%, then 30/20/12/7%; GM 74%; Blume beta 1.815) | $115 | WATCH/DEFER |
| Hyperscaler pause (FY2028 growth 0%) | $67 | **DO NOT INITIATE** |
| Custom-silicon margin compression (GM 65% from FY2029) | $74 | WATCH/DEFER |
| Stock compensation treated as a cash cost | $74 | WATCH/DEFER |
| Blume-adjusted beta 1.815 | $93 | WATCH/DEFER |
| WACC ±2pp × terminal growth 2–4% grid | $66–$99 | — |

These are scenarios, not probabilities. The decision is most sensitive to the discount rate,
then to FY2028 growth.

## Principal risks, failure conditions, and monitoring triggers

| Trigger | Threshold | Window | Moves to |
|---|---|---|---|
| Price | NVDA closes at or below base-case value (~$79) | daily | **INITIATE** review |
| Demand turn | any 10-Q with year-over-year revenue decline | each 10-Q | **DO NOT INITIATE** |
| Competitive entry | gross margin below 70% for a reported quarter | each 10-Q | rerun; low-case path |
| Relative value lost | NVDA EV/EBITDA at or above the lowest admitted peer | each review | **DO NOT INITIATE** |
| Over-ordering | excess purchase obligations above 15% of inventory | each 10-Q | escalate |
| Model integrity | any accounting or bridge check fails | every run | no value reported |

**Known limitations:**

- The forecast is dated from the January 2026 balance sheet. Debt has since risen to 33,366.
  Rolling the base value forward to today adds about 11%, far short of the price.

- Beta carries the answer.
- Only two peers are admitted.

## Action requested and next review point

1. Approve **WATCH/DEFER** with the triggers above.
2. Re-review when the Q3 FY2027 10-Q is filed.
3. My next research priority is the discount rate: a re-estimate of beta on 2-year data and a
   forward-looking equity risk premium.

Validation, sources and AI use: `docs/validation-and-ai-use.md`. Model and tests:
`nvidia/analysis.py`, `nvidia/test_project.py`. Frozen output: `nvidia/visible_output.json`.

*AI assistance: analysis and drafting assisted by Claude Code (Claude Opus 5.5) and, in the labs,
ChatGPT/Codex; sources gathered and verified by me; the judgments are mine. Any remaining errors
are my own.*
