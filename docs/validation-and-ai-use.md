# Validation and AI Use — Project 1, NVIDIA (NVDA)

**Student:** Drew Scheiderer · **Course:** FIN 43900, AI in Finance, Purdue, Fall 2026
**Status:** working source for `Validation-and-AI-Use.pdf`. Sections marked **[DREW]** are
mine to complete. The Locked Changed-Input Record is filled by hand with AI closed.

> Coursework for a learning exercise. Not investment research and not financial advice.

---

## Decision, version, and as-of boundary

| Item | Value |
|---|---|
| Decision / user | Initiate, watch/defer, or do not initiate NVDA, for a buy-side investment committee holding no position |
| Horizon | 3–5 year holding period; five-year explicit forecast FY2027E–FY2031E plus terminal value |
| Repository | https://github.com/dscheid7717/SPCX-research |
| Analysis commit | `9222448` (engine, app, frozen output). Final frozen commit: **[DREW: fill after last commit]** |
| Run timestamp | Frozen output generated 2026-10-15; cold-run log in `docs/cold-run-log.txt` |
| Source cutoffs | NVIDIA 10-K FY2026 (filed 2026-02-25) and 10-Q Q2 FY2027 (filed 2026-08-26); peer 10-Ks filed 2025-12-18 (AVGO) and 2026-02-04 (AMD); market data close 2026-10-14 |
| Environment | Python 3.12.10; `requirements.txt` (numpy, pandas, matplotlib, scipy, yfinance, streamlit pinned ranges); finance engine is standard library only |

## Data and convention ledger

| Material input | Source | As-of / availability | Definition / units | Transformation / exclusion | Risk |
|---|---|---|---|---|---|
| FY2026 revenue 215,938 | 10-K acc. 0001045810-26-000021, income statement | period 2026-01-25, filed 2026-02-25 | USD M, GAAP | base year; hand-confirmed against Item 8 (Lab 10) | low |
| Opening balance sheet (assets 206,803, liabilities 49,510, equity 157,293) | 10-K balance sheet | 2026-01-25 | USD M | mapped into 4 asset / 4 liability buckets; `check_opening_balance()` proves totals | low (checked) |
| H1 FY2027 revenue 177,837; Q2 96,221 | 10-Q acc. 0001045810-26-000075 (SEC XBRL `Revenues`) | period 2026-07-26, filed 2026-08-26 | USD M | anchors FY2027E = H1 + 2 × Q2 = 370,279 (+71.47%) | medium: H2 is a judgment |
| H1 FY2027 gross margin 74.96% | 10-Q (`GrossProfit` 133,299 / `Revenues`) | 2026-07-26 | ratio | forecast GM path starts at 75.0% | medium |
| FY2026 inventory write-down 4,000 | 10-K (XBRL `InventoryWriteDown`) | 2026-01-25 | USD M, in cost of revenue | normalisation: reported GM 71.07% → 72.92% | low |
| FY2026 equity-investment gains 8,918 | 10-K cash flow statement | 2026-01-25 | USD M, other income | excluded from forecast; stakes carried in bridge | medium |
| Cash + marketable securities 62,556 | 10-K balance sheet rows 16–17 (10,605 + 51,951) | 2026-01-25 | USD M | added in bridge; pro-forma holds treasury flat here | low (definition checked — see register) |
| Non-marketable equity securities 22,251 | 10-K balance sheet row 27 | 2026-01-25 | USD M, carrying value | added in bridge (new in Edition B) | medium: carrying ≠ fair value |
| Debt 8,468 | 10-K Note 11 (999 + 7,469) | 2026-01-25 | USD M, carrying | subtracted in bridge; Jul-2026 debt of 33,366 disclosed, not used | medium: post-period issuance |
| Diluted shares 24,514 | 10-K EPS note | FY2026 weighted average | millions | per-share basis throughout | low (0.9% vs basic) |
| NVDA price $221.30 | Yahoo Finance via yfinance | close 2026-10-14 | USD | WACC equity weight, comps, decision | low |
| Risk-free 5.190% | ^TNX via yfinance | close 2026-10-14 | 10-year UST yield | CAPM | low |
| Beta 2.216 (Blume 1.815) | own OLS, `nvidia/beta.py`, 5y monthly vs S&P 500 | prices cached 2026-09-22 | slope | CAPM; Blume in high case | **high: carries the answer** |
| ERP 5.0% | course convention | — | — | CAPM | high |
| Pre-tax cost of debt 2.92% | 10-K Note 11, principal-weighted (Lab 06) | 2026-01-25 | rate | WACC (debt weight 0.16%) | negligible |
| Peer financials (AMD, AVGO) | 10-K XBRL: AMD acc. 0000002488-26-000018; AVGO acc. 0001730168-25-000121 | FY ends 2025-12-27, 2025-11-02 | USD M | EV = price × diluted shares + debt − cash & ST investments; EBITDA = GAAP operating income + CF-statement D&A incl. acquisition amortisation | medium: AMD/AVGO D&A taken at tag level — **[DREW: hand-confirm against each cash flow statement]** |
| Peer prices AMD $570.82, AVGO $346.25 | Yahoo Finance via yfinance | close 2026-10-14 | USD | comps | low |

## Validation register

| Claim / output | Failure mode | Test and expected result | Actual result | Disposition | Evidence |
|---|---|---|---|---|---|
| DCF engine is correct | arithmetic error in discounting / Gordon / bridge | **Known answer:** reproduce the course's 12 Lab 06 training answers ($27.50, nine grid cells, +1.78pp reverse DCF) | all 12 match to $0.005 / 0.01pp | pass | `test_project.KnownAnswerTests` |
| Pro-forma engine is correct | statement linkage error | **Known answer:** root Asbury training case prints published $291.75 | matches | pass | `test_asbury_proforma_training_case` |
| Bridge cash is the right object | provider label ≠ filing line | **Independent definition check:** SEC XBRL `AvailableForSaleSecuritiesDebtSecurities` gives 39,520 for 2026-01-25; the 10-K balance sheet line "Marketable securities" gives 51,951 | they differ by 12,431: the XBRL tag is the debt-securities note total, not the balance-sheet line | XBRL value **rejected**; filing line governs | 10-K workbook `BALANCE_SHEET` row 17; this record |
| Value responds in the right direction | sign error in a driver | **Directional changed-input tests, written and committed before first execution (`93a7ac9`, 2026-10-15 12:39 ET):** beta ↑ → value ↓; FY2027E growth ↑ → value ↑; GM ↓ → value ↓; SBC as cash cost → value ↓; reset recovers base | all as predicted | pass | `DirectionalChangedInputTests`; `git show 93a7ac9` |
| Statements articulate | plugged or unrouted line | balance sheet balances every year; CFS ending cash = BS cash; base year = filed totals and revenue | max gap 0.00 on all three | pass | `ArticulationTests`; report "CHECKS" |
| DCF uses the pro-forma consistently | FCFF and FCFE built from different stories | FCFE = FCFF + after-tax net interest − debt repaid, every year | max gap 0.0000 | pass | check "FCFF reconciles to the pro-forma's FCFE" |
| DCF boundaries | value moves the wrong way, or Gordon used where undefined | grid strictly ↓ in WACC and ↑ in g over 5 × 5; g ≥ WACC refuses | monotonic; refusal returns no value | pass | `DcfBoundaryTests` |
| Bridge reconciles | EV-to-equity arithmetic | EV + 62,556 + 22,251 − 8,468 = equity; × shares both ways | exact | pass | `BridgeTests` |
| Peer policy applied consistently | definition drift between companies | every company carries every field; fiscal ends within 120 days; positive EBITDA/EPS; EV/EBITDA recomputes; NVDA recomputed by hand | all pass; NVDA 40.3× by hand | pass | `PeerPolicyTests` |
| **Highest-risk failure (model)** | a broken sheet is valued silently | inject SBC-without-equity-credit and an opening mis-map; model must refuse, gap must equal SBC exactly; next run must be clean | refuses; gap = SBC; no leak | pass | `HighestRiskFailureTests`; app fault switch |
| **Highest-risk failure (evidence)** | a stale driver carried forward | compare Lab 10 FY2027E growth (30%) to the 10-Q filed 2026-08-26 | H1 already +95.8% YoY; 30% would need H2 revenue to fall to 102,882 | **Lab 10 driver failed**; replaced (Edition B) | `analysis.py` DRIVER_RECORD |
| Decision rule can be moved by evidence | rule that no downside can alter | first-run review: does any downside case change the action? | **failed** under the median-only rule (`93a7ac9`); after adding the earnings-persistence leg the low case and hyperscaler-pause what-if give DO NOT INITIATE | revised, disclosed | `9222448` commit message; `analysis.py` decision-rule block |
| Frozen output is reproducible | hand-edited or stale visible output | fresh `run_analysis()` equals `visible_output.json` | equal | pass | `ReproducibilityTests` |
| Clean environment reproduces | hidden local state | **cold run:** fresh clone, fresh venv, `pip install -r requirements.txt`, tests, analysis, diff against frozen report, app smoke test | run 1 **failed** at the app step (`streamlit.proto` missing: Windows long paths disabled, 176-character folder prefix); run 2 from a short path clean — 27/27 tests, report identical to frozen, app WATCH/DEFER $78.83, 291 s | failure diagnosed as environment, not code; README now tells Windows users to clone to a short path | `docs/cold-run-log.txt` |

## Locked Changed-Input Record — human prediction first; AI closed during execution

**[DREW — to be completed by hand, AI closed, BEFORE the run.]** Commit this file with only
the precommit table filled, note the commit hash, then run the change and fill the second
table. Suggested command (any one input):

```
cd nvidia
python -c "import analysis as a; i=a.base_inputs(); i['beta']=1.815; r=a.run_analysis(i); print(round(r['base']['valuation']['value_per_share'],2), r['decision'])"
```

### Precommit before the run and before AI assistance on the prediction

| Precommit timestamp | Repository commit | Material input | Old → new value/units | Expected output direction | Expected decision effect |
|---|---|---|---|---|---|
|  |  |  |  |  |  |

### Preserved execution result

| Before/after output | Actual decision effect | Prediction reconciliation | Failure diagnosis or why action did not change | Evidence path |
|---|---|---|---|---|
| base $78.83 → |  |  |  |  |

*Supporting history:* the Lab 11 locked prediction (`dbf76fd`, 2026-09-29 15:34 ET) is a prior
human-authored record on the Lab 10 model; it lacks the decision-effect fields this template
requires, which is why a Project 1 record is made above.

## Named AI-use register

| Tool / model and version | Date | Material task | Output / claim used or considered | Independent check | Disposition | Effect on decision |
|---|---|---|---|---|---|---|
| ChatGPT / Codex; Claude Code | 2026-09-08 → 2026-10-01 | Lab 06–12 drafting and code, as disclosed in each lab write-up | Lab models and write-ups | known-answer reproduction each lab; hand checks recorded in the labs | accepted with the checks recorded there | built the Lab 06–11 evidence base |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Pull NVDA and peer filing facts from SEC XBRL company-facts | candidate value 39,520 for "marketable securities" (`AvailableForSaleSecuritiesDebtSecurities`) | 10-K balance sheet, workbook `BALANCE_SHEET` row 17: 51,951 | **rejected** — wrong object (note total, not the balance-sheet line) | none: bridge kept at 62,556 |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Review of Lab 10 drivers against the Q2 FY2027 10-Q | claim that FY2027E growth of 30% is contradicted by H1 +95.8% | **[DREW: open the 10-Q income statement and confirm 177,837 / 90,805]** | **[DREW: accept / modify]** | base value $58 → $79 |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Proposed Edition B driver values, low/high cases, what-ifs | values in `analysis.py` BASE_INPUTS, CASES, WHAT_IFS | each anchored to a cited 10-Q / 10-K figure in DRIVER_RECORD | **[DREW: accept / modify each — these are judgments I must own]** | sets the $49–$115 range |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Decision rule | first version could not be moved by any downside case | first run of the engine | **modified**: earnings-persistence leg added, disclosed in commit `9222448` | low case now flips to DO NOT INITIATE |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Wrote `analysis.py`, `app.py`, `test_project.py` | engine, app and 27 tests | known answers, articulation checks, cold run; **[DREW: read every function before Video 2]** | **[DREW]** | delivery |
| Claude Code subagent | 2026-10-15 | Read the public course repo for Project 1 requirements | "the analytic rubric file is not in the public repo" | **[DREW: check Brightspace]** | qualified: true of the public repo only | none |

## Limitations, monitoring, and kill/escalation rules

**Limitations**

- The forecast opens on the FY2026 balance sheet (2026-01-25) and discounts from that date; the
  price is 2026-10-14. Rolling the base value forward roughly 0.7 year at WACC would raise it
  about 11% before deducting H1 distributions — far from closing the gap to price.

- WACC rests almost entirely on beta. Raw 2.216 vs Blume 1.815 is a ~200bp swing ($79 → $93).
- The reverse DCF puts the disagreement in the discount rate: the price needs a beta of 0.51
  (cost of equity 7.74%) on my operating forecast, or FY2028–31 growth 45pp above my path.

- Two peers only; trailing multiples lag NVIDIA's growth; AMD's multiple is inflated by thin
  margins and acquisition amortisation.

- Scenario endpoints are judgments, not probabilities.

**Monitoring and kill/escalation rules**
| Trigger | Metric and threshold | Window | Action |
|---|---|---|---|
| Initiate | NVDA close ≤ base-case value | daily | escalate to committee for initiation |
| Downside evidence | any 10-Q with YoY revenue decline, or GM < 70% | each 10-Q (next: Q3 FY2027) | rerun; rule gives DO NOT INITIATE in the low-case path |
| Relative value lost | NVDA trailing EV/EBITDA ≥ lowest admitted peer | each 10-K / price review | DO NOT INITIATE |
| Model integrity | any check fails | every run | kill: no value is reported until fixed |
