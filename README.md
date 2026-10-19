# FIN 43900 Project 1 — NVIDIA (NVDA) Corporate Finance Application

Equity valuation and committee decision on **NVIDIA Corporation (NVDA)** for FIN 43900, AI in
Finance, Purdue University, Fall 2026. Author: Drew Scheiderer.

> This repository is coursework for a learning exercise. It is not investment research and it
> is not financial advice.

> **Company switch, 2026-09-22.** This repository began as SPCX (Space Exploration
> Technologies Corp.) research and is still named `SPCX-research` so that lab links already
> submitted on Brightspace keep resolving. Edition A was written on SPCX and is preserved
> unchanged in `spacex/`; the switch is explained in the dated addendum in
> `docs/research-evolution.md`.

## Finance decision and intended user

**Decision:** initiate, watch/defer, or do not initiate a long position in NVDA.
**Intended user:** a buy-side investment committee with no current position.
**Horizon:** 3–5 year holding period; five-year explicit forecast FY2027E–FY2031E plus a
terminal value. **As-of date:** October 14, 2026 (price $221.30).
**Currency and share basis:** USD millions; per-share values in USD on **24,514M diluted**
weighted-average shares (FY2026 10-K EPS note).
**Exclusions:** equity-investment gains are excluded from the operating forecast and the
stakes are carried in the bridge instead; operating leases are treated as operating costs;
transaction multiples are not used because no defensible control comparable exists.

## Visible result

**Committee action: WATCH/DEFER.** FCFF DCF range **$49–$115 per share, base $79**, against a
$221.30 price. The name stays on watch, not rejected, because NVIDIA trades below both admitted
peers on trailing EV/EBITDA (40.3× vs 50.7× and 138.3×) while its earnings keep growing in the
base case. In the AI-capex-digestion case, and whenever gross margin breaks 67%, the same rule
gives **DO NOT INITIATE**.

Readable without running anything:

- [`nvidia/output/NVIDIA_2026-10-14_project1_report.txt`](nvidia/output/NVIDIA_2026-10-14_project1_report.txt)
  — every check, the five-year statements, the DCF and bridge, cases, what-ifs, the WACC ×
  growth grid, the reverse DCF, comparables and the action.
- [`nvidia/visible_output.json`](nvidia/visible_output.json) — the frozen contract the app
  renders: material inputs, as-of date, range, action, conditions, reversal trigger, units,
  limitations.
- [`docs/decision-memo.md`](docs/decision-memo.md) — the two-page committee memo.
- **Application capture** — the semi-adjustable app (`streamlit run app.py`), captured 2026-10-19:
  - [`docs/app-screenshots/app-1-base.png`](docs/app-screenshots/app-1-base.png) — base case:
    committee view, cases, what-ifs, comparables and every check passing.
  - [`docs/app-screenshots/app-2-margin-minus-3pp.png`](docs/app-screenshots/app-2-margin-minus-3pp.png)
    — gross margin −3pp: $74.73 (−5.2%), action flips to DO NOT INITIATE (67% floor).
  - [`docs/app-screenshots/app-3-fault-refused.png`](docs/app-screenshots/app-3-fault-refused.png)
    — injected fault (stock compensation not credited to equity): the balance check fails red
    and the model refuses to value.

## Setup and run

On Windows, clone to a short path (for example `C:\p1`) or enable long paths: the cold run
showed pip silently skips streamlit's nested files under a long folder path
(`docs/cold-run-log.txt`).

1. Create an isolated environment: `python -m venv .venv`
2. Activate it — Windows: `.venv\Scripts\activate` · macOS/Linux: `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` only if a data provider key is needed. Never commit `.env`.
   No key is needed to reproduce the result — all inputs are frozen in the code.
5. From the `nvidia` folder:
   - tests: `python -m unittest test_project -v`
   - analysis: `python analysis.py` (add `--freeze` to rewrite the frozen output)
   - app: `streamlit run app.py`

The finance engine is standard library only; pandas and streamlit are used by the app.

## Repository map

### Required analysis-to-interface flow

**evidence → analysis → tests → frozen visible output → app.**
1. Sourced inputs carry source and as-of date in `nvidia/analysis.py` (facts block,
   `DRIVER_RECORD`, `NORMALIZATIONS`, `COMPANIES`) and in the data ledger in
   `docs/validation-and-ai-use.md`.
2. `nvidia/analysis.py` computes every material result. It drives the Lab 10 pro-forma
   (`nvidia/proforma.py`) and the Lab 06 DCF functions (`nvidia/dcf.py`) without editing them.
3. `nvidia/test_project.py` runs 27 tests: known answers, articulation, bridge, directional
   changed-input tests, DCF boundaries, highest-risk failures, peer policy, reproducibility.
4. `python analysis.py --freeze` refuses to write unless every check passes, then writes
   `nvidia/visible_output.json` and the frozen report.
5. `nvidia/app.py` renders the frozen contract, and its what-if panel calls the same engine.

### Project 1 files

| Path | Contents |
|---|---|
| `nvidia/analysis.py` | Project 1 engine: Edition B drivers, FCFF DCF from the pro-forma, WACC, bridge, cases, what-ifs, grid, reverse DCF, comparables, decision rule |
| `nvidia/test_project.py` | Validation suite (27 tests) |
| `nvidia/app.py` | Streamlit committee app: frozen view + bounded what-if panel, reset to base, fault switch |
| `nvidia/visible_output.json` | Frozen visible output |
| `nvidia/output/NVIDIA_2026-10-14_project1_report.txt` | Frozen executed report |
| `docs/research-evolution.md` | Edition A (unchanged), dated addendum, Edition B and the A-to-B table |
| `docs/decision-memo.md` | Two-page decision memo |
| `docs/validation-and-ai-use.md` | Data ledger, validation register, Locked Changed-Input Record, AI-use register |
| `docs/cold-run-log.txt` | Clean end-to-end run in a fresh clone and environment |
| `docs/transcript-video-{1,2,3}.txt` | Corrected video transcripts |
| `project-submission-manifest.csv` | The 12-row submission manifest |

### Lab record (unchanged)

| Path | Contents |
|---|---|
| `dcf.py`, `proforma.py` | Lab 05 / Lab 09 training-case engines (match the course's known answers) |
| `asbury/` | Lab 07 comps and Lab 09 sensitivity on the Asbury training case |
| `nvidia/dcf.py`, `nvidia/comps.py`, `nvidia/proforma.py`, `nvidia/sensitivity.py`, `nvidia/beta.py` | Lab 06, 08, 10, 11 and 09 NVIDIA models |
| `nvidia/NVIDIA_2026-*_lab*.md` | Lab 06–12 write-ups, including the Lab 11 locked prediction |
| `nvidia/data/` | FY2026 10-K workbook; cached beta price history |
| `spacex/` | Superseded SPCX work and **Edition A — never edited** |

## Data sources and point-in-time boundary

Nothing published after **October 14, 2026** is used.

- **NVIDIA Form 10-K**, FY ended January 25, 2026, filed February 25, 2026, accession
  `0001045810-26-000021` — base year, opening balance sheet, bridge.
- **NVIDIA Form 10-Q**, quarter ended July 26, 2026, filed August 26, 2026, accession
  `0001045810-26-000075` — H1 FY2027 actuals that anchor the FY2027E drivers.
- **AMD Form 10-K** FY2025 (accession `0000002488-26-000018`) and **Broadcom Form 10-K**
  FY2025 (accession `0001730168-25-000121`), via SEC XBRL company facts.
- **Market data:** NVDA, AMD and AVGO closes and the 10-year Treasury yield (^TNX), Yahoo
  Finance via `yfinance`, **close October 14, 2026**. Beta uses five years of monthly prices
  cached September 22, 2026.

## Financial conventions and assumptions

USD millions unless stated; negatives in parentheses in write-ups; percentages labelled.
Fiscal years end in late January (FY2026 is mostly calendar 2025). Each input is labelled
`fact`, `history`, `normalization`, `judgment`, `estimate` or `model output`. Every
load-bearing driver carries value · basis · challenge · evidence that would change it, in
`DRIVER_RECORD` in `nvidia/analysis.py`. FCFF = EBIT(1 − t) + D&A + SBC − capex − Δworking
capital + Δpurchase-obligation accrual. The discount rate is the WACC: CAPM cost of equity
(5.19% + 2.216 × 5%) at a 99.84% equity weight. Terminal growth is 3%.

## Validation and changed-input tests

See `docs/validation-and-ai-use.md` for the full register. In brief:
- **Known answers:** the 12 Lab 06 training answers and the Asbury $291.75 are reproduced.
- **Independent definition check:** the XBRL figure of 39,520 was rejected in favour of the
  10-K "marketable securities" line of 51,951.
- **Directional tests:** written and committed before first execution (`93a7ac9`).
- **Articulation:**
  - the balance sheet balances every year;
  - the cash flow statement ties to balance-sheet cash;
  - the base year reconciles to the filing;
  - FCFF reconciles to FCFE.
- **DCF boundary and bridge:** the WACC × growth grid moves in the expected directions, and
  the model refuses to value when terminal growth is at or above WACC.
- **Highest-risk failures:** the model refuses to value if stock compensation isn't credited
  to equity, or if an opening balance is mis-mapped.
- **Peer-policy checks.**
- **Cold run:** `docs/cold-run-log.txt`.

## Known limitations, monitoring, and reversal triggers

- The forecast is dated from the January 2026 balance sheet, but the price is from October
  2026. Debt has since risen to 33,366.
- WACC rests on beta: switching from the raw beta to the Blume-adjusted beta moves value from
  $79 to $93.
- The price implies a beta of 0.51 on my operating forecast.
- Only two peers are admitted, and their multiples are trailing.

**Reversal triggers:**
- **INITIATE** if the price is at or below the base-case value.
- **DO NOT INITIATE** if a 10-Q shows a year-over-year revenue decline, gross margin below
  67%, or NVIDIA's EV/EBITDA at or above the lowest admitted peer's.
- **Escalate and rerun** if excess purchase obligations exceed 12.8% of inventory.
- Review at each 10-Q.

---

*AI assistance: research, code and drafting assisted by Claude Code (Claude Opus 5.5) and
ChatGPT/Codex, as recorded in `docs/validation-and-ai-use.md`; sources gathered and verified by
me; the judgments are mine.*

*Any remaining errors are my own.*
