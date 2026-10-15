# Validation and AI Use — Project 1, NVIDIA (NVDA)

**Student:** Drew Scheiderer · **Course:** FIN 43900, AI in Finance, Purdue, Fall 2026
**Status:** working source for `Validation-and-AI-Use.pdf`. The Locked Changed-Input Record is
my Lab 11 locked prediction, human-authored with AI closed and committed before the run.

> Coursework for a learning exercise. Not investment research and not financial advice.

---

## Decision, version, and as-of boundary

| Item | Value |
|---|---|
| Decision / user | Initiate, watch/defer, or do not initiate NVDA, for a buy-side investment committee holding no position |
| Horizon | 3–5 year holding period; five-year explicit forecast FY2027E–FY2031E plus terminal value |
| Repository | https://github.com/dscheid7717/SPCX-research |
| Analysis commit | `9222448` (engine, app, frozen output). Final frozen commit: recorded in `project-submission-manifest.csv`, column frozen_or_commit_id |
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
| Peer financials (AMD, AVGO) | 10-K XBRL: AMD acc. 0000002488-26-000018; AVGO acc. 0001730168-25-000121 | FY ends 2025-12-27, 2025-11-02 | USD M | EV = price × diluted shares + debt − cash & ST investments; EBITDA = GAAP operating income + CF-statement D&A incl. acquisition amortisation | medium: AMD/AVGO D&A taken at XBRL tag level, not hand-read (disclosed under Limitations) |
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
| Decision rule can be moved by evidence | rule that no downside can alter | first-run review: does any downside case change the action? | **failed** under the median-only rule (`93a7ac9`); after adding the earnings-persistence leg and my Lab 12 67% margin floor, the low case, hyperscaler-pause and margin-compression what-ifs give DO NOT INITIATE | revised, disclosed | `9222448` commit message; `analysis.py` decision-rule block |
| Frozen output is reproducible | hand-edited or stale visible output | fresh `run_analysis()` equals `visible_output.json` | equal | pass | `ReproducibilityTests` |
| Clean environment reproduces | hidden local state | **cold run:** fresh clone, fresh venv, `pip install -r requirements.txt`, tests, analysis, diff against frozen report, app smoke test | run 1 **failed** at the app step (`streamlit.proto` missing: Windows long paths disabled, 176-character folder prefix); run 2 from a short path clean — 27/27 tests, report identical to frozen, app WATCH/DEFER $78.83, 291 s | failure diagnosed as environment, not code; README now tells Windows users to clone to a short path | `docs/cold-run-log.txt` |

## Locked Changed-Input Record — human prediction first; AI closed during execution

This record is my **Lab 11 locked prediction, taken as is**. It was human-authored with AI
closed and committed before any sensitivity run, as Lab 11 required. Full text:
`nvidia/NVIDIA_2026-09-29_lab11_locked_prediction.md`. It was run on the Lab 10 pro-forma, the
same engine `nvidia/analysis.py` now drives.

### Precommit before the run and before AI assistance on the prediction

| Precommit timestamp | Repository commit | Material input | Old → new value/units | Expected output direction | Expected decision effect |
|---|---|---|---|---|---|
| 2026-09-29 15:34:46 −04:00 | `dbf76fd` ("Lock the Lab 11 sensitivity prediction before any run") | (1) `REVENUE_GROWTH`; (2) `GROSS_MARGIN` — in `nvidia/proforma.py` | (1) 0.30/0.22/0.16/0.11/0.07 → uniform ±0.02 (±2pp, decimal) every year; (2) 0.710→0.690 path → uniform ±0.02 (±2pp, not ±2%) | Both move value per share, FY2031E operating profit and FCFE in the **same direction as the input**. Growth: **1–4% of value per pp**. Margin: **≤1% per pp**. Growth's span > margin's; span ratio ~1×–4× | Not a separate field in the Lab 11 template, so not recorded before the run. The precommitted words were directional only: lower growth → value "would drop significantly"; lower margin → value drops, "not to as large of a magnitude" |

### Preserved execution result

| Before/after output | Actual decision effect | Prediction reconciliation | Failure diagnosis or why action did not change | Evidence path |
|---|---|---|---|---|
| Base $58.23. Growth −2/+2pp: $54.51 / $62.17 (span 7.66; 3.29% of base per pp). Margin −2/+2pp: $56.12 / $60.33 (span 4.21; 1.81% per pp) | **None — WATCH–DEFER unchanged** | 4 of 5 claims correct: ranking, sign, growth size, span ratio (1.8×). **Wrong:** margin size, 1.81% per pp vs ≤1% predicted (~1.8× my ceiling) | *Failure:* (a) a point of margin is a point of **revenue** (471,842 in FY2031E), so 2pp = 9,437 of gross profit vs 255,618 operating profit; (b) terminal value is 59% of value and capitalises the final year, amplifying both drivers. One stated reason (strategic capital) is not a mechanism the model contains. *No change because:* both drivers together span $54.51–$62.17 against a $224.58 price; no operating assumption defensible from NVIDIA's history closes a $166 gap — the disagreement is the discount rate | `nvidia/NVIDIA_2026-09-29_lab11_locked_prediction.md`; `nvidia/output/NVIDIA_2026-09-29_lab11_sensitivity.txt`; `git show dbf76fd` |

**Post-run edits, declared in the record itself:** after the run I filled two per-driver tables
that were empty scaffolding in `dbf76fd`; the quantified forecast was already in the committed
text and `git diff dbf76fd HEAD` on that file shows it unchanged.

**Carried to the Project 1 model (AI-run, 2026-10-15; not part of the locked record):** the same
±2pp shifts on the Edition B base give growth $74.27 / $78.83 / $83.66 (2.98% per pp) and margin
$76.10 / $78.83 / $81.57 (1.73% per pp). The Lab 11 ranking holds; the margin under-prediction
persists at the same size; the action is WATCH/DEFER throughout.

## Judgment carry-forward — Labs 06–12 into Project 1

My lab judgments are the default. Where Project 1 changes one, the reason is stated.

| Judgment | Lab source | Lab value | Project 1 value | Kept / changed | Why |
|---|---|---|---|---|---|
| FY2027E revenue growth | Lab 06, 10 | 30% | **71.5%** (H1 reported + H2 at Q2 run rate) | **changed** | The Q2 FY2027 10-Q (filed 2026-08-26) shows H1 +95.8%; 30% would require H2 revenue to *fall* to 102,882 |
| FY2028E–31E growth | Lab 06, 10 | 22 / 16 / 11 / 7% | 22 / 16 / 11 / 7% | kept | No evidence against the decay path |
| Gross margin path | Lab 10 | 71.0% → 69.0% | **75.0%** → 69.0% | start changed, endpoint kept | H1 FY2027 74.96%; FY2026's 71.07% was depressed by a 4,000 write-down (normalised 72.92%). The competitive-fade reasoning and 69% endpoint stand |
| Gross margin floor | Lab 11 range, Lab 12 trigger | 67% → do not initiate | 67% → do not initiate, **now enforced by the decision rule** | kept, strengthened | The custom-silicon what-if (65%) now flips to DO NOT INITIATE, as my Lab 12 trigger says it should |
| R&D / revenue | Lab 10 | 8.5% → 10.5%, rising | **7.5%** → 10.5% | start changed, logic kept | H1 FY2027 7.52%; the ratio still rises as growth slows |
| SG&A / gross profit | Lab 10 | 3.0% flat | **2.0%** → 3.0% by FY2029E | start changed | H1 FY2027 1.99%; returns to my 3.0% |
| Tax rate | Lab 10 | 16% | 16% | kept | H1 FY2027 effective 16.5% supports it |
| Capex, inventory days, SBC, D&A, supply-obligation ratios | Lab 10 | FY2026 history | same | kept | — |
| Treasury held flat; surplus distributed | Lab 10 correction | 62,556 | same | kept | Prevents double-counting interest on distributed cash |
| Buybacks / dividends | Lab 10 | 40,000 / 1,000 | **78,000 / 12,600** | changed | H1 FY2027 annualised (39,044 / 6,290). No value effect: the surplus distribution is a residual |
| Beta | Lab 09, 10 | 2.216 base; Blume 1.815 "as a sensitivity, not buried" | same; Blume in the high case and a what-if | kept | — |
| Risk-free rate / price | Lab 06, 10 | 4.944%, $218.36 (09-10); $224.58 (09-24) | **5.190%, $221.30 (10-14)** | changed | One date for every market fact, including peers |
| ERP, terminal growth, diluted shares | Lab 06 | 5%, 3%, 24,514M | same | kept | — |
| Bridge | Lab 06 | EV + 62,556 − 8,468 | **+ 22,251 non-marketable equity** | changed | My Lab 11 note: those stakes are excluded from the forecast "by construction". Left out of the bridge too, their value would vanish |
| Peer set and policy | Lab 08 | AMD, AVGO; INTC excluded; one price date; GAAP | same; **EV/EBITDA added** | kept + extended | Project requires an EV multiple; EBITDA neutralises the acquisition amortisation Lab 08 found distorting AMD's P/E |
| Never average the methods | Lab 08, 12 | — | same | kept | — |
| Call | Labs 08–12 | WATCH–DEFER | WATCH/DEFER | kept | — |
| Initiate trigger | Lab 06, 08, 12 | price below ~$114 (0.5× edge of the reasonableness band) | **price ≤ base-case value ($79)** | **changed** | The 0.5×–2.0× band tests whether a model is sane against the market; it is not a margin of safety. $114 meant paying twice my own value. (It sits close to the new high case, $115.) |
| Do-not-initiate: segment growth | Lab 12 | Compute & Networking slower than my 30% FY2027 path | YoY revenue decline → DO NOT INITIATE; C&N growth below path → escalate and rerun | changed | The 30% path was contradicted by the 10-Q |
| Do-not-initiate: supply obligations | Lab 12 | ratio above 12.8% of inventory | above 12.8% → **escalate and rerun** | threshold kept, action changed | 12.8% is today's level, so any uptick would flip the call; one quarter's accrual timing is a reason to rerun, not to decide |
| Re-underwrite conditions | Lab 12 | defensible Ke materially below 16%; peers at 20–30× trailing GAAP P/E | same | kept | — |
| Research priority | Lab 11, 12 | beta first, C&N growth second | same | kept | Reverse DCF: the price needs beta 0.51 |

## Named AI-use register

| Tool / model and version | Date | Material task | Output / claim used or considered | Independent check | Disposition | Effect on decision |
|---|---|---|---|---|---|---|
| ChatGPT / Codex; Claude Code | 2026-09-08 → 2026-10-01 | Lab 06–12 drafting and code, as disclosed in each lab write-up | Lab models and write-ups | known-answer reproduction each lab; hand checks recorded in the labs | accepted with the checks recorded there | built the Lab 06–11 evidence base |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Pull NVDA and peer filing facts from SEC XBRL company-facts | candidate value 39,520 for "marketable securities" (`AvailableForSaleSecuritiesDebtSecurities`) | 10-K balance sheet, workbook `BALANCE_SHEET` row 17: 51,951 | **rejected** — wrong object (note total, not the balance-sheet line) | none: bridge kept at 62,556 |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Review of Lab 10 drivers against the Q2 FY2027 10-Q | claim that FY2027E growth of 30% is contradicted by H1 +95.8% | quarterly facts sum to the half-years: 81,615 + 96,221 = 177,836 (vs 177,837, $1M rounding); 44,062 + 46,743 = 90,805 | **accepted**; Lab 10 driver **modified** (see carry-forward) | base value $58 → $79; action unchanged |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Proposed Edition B driver values, low/high cases, what-ifs | values in `analysis.py` BASE_INPUTS, CASES, WHAT_IFS | each anchored to a cited 10-Q / 10-K figure; lab judgments kept unless the carry-forward table states a reason | **modified**: lab judgments kept as default; changes limited to those in the carry-forward table | sets the $49–$115 range |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Decision rule | first version could not be moved by any downside case | first run of the engine | **modified**: earnings-persistence leg (`9222448`), then my Lab 12 67% margin floor | low case, hyperscaler pause and margin compression flip to DO NOT INITIATE |
| Claude Code (Claude Opus 5.5) | 2026-10-15 | Wrote `analysis.py`, `app.py`, `test_project.py` | engine, app and 27 tests | 12 course known answers + Asbury $291.75 reproduced; articulation checks; two cold runs | **accepted** after tests and cold run | delivery |
| Claude Code subagent | 2026-10-15 | Read the public course repo for Project 1 requirements | "the analytic rubric file is not in the public repo" | repository tree listing | **qualified**: true of the public repo only; Brightspace governs | none |

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
- AMD and Broadcom D&A are taken from SEC XBRL tags, not hand-read from each cash flow statement.
- Scenario endpoints are judgments, not probabilities.

**Monitoring and kill/escalation rules**

| Trigger | Metric and threshold | Window | Action |
|---|---|---|---|
| Initiate | NVDA close ≤ base-case value (~$79) | daily | escalate to committee for initiation |
| Demand turn | any 10-Q with YoY revenue decline | each 10-Q (next: Q3 FY2027) | DO NOT INITIATE (low-case path) |
| Competitive entry | gross margin below 67% (Lab 11/12 floor) | each 10-Q | DO NOT INITIATE |
| Relative value lost | NVDA trailing EV/EBITDA ≥ lowest admitted peer | each 10-K / price review | DO NOT INITIATE |
| Over-ordering | excess purchase obligations > 12.8% of inventory (Lab 12) | each 10-Q | escalate and rerun |
| Segment deceleration | Compute & Networking growth below the forecast path | each 10-Q | escalate and rerun |
| Re-underwrite | defensible Ke materially below 16%; or peers at 20–30× trailing GAAP P/E (Lab 12) | as evidence arrives | rerun valuation |
| Model integrity | any check fails | every run | kill: no value is reported until fixed |
