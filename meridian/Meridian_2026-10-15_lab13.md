# Meridian Foundation Reserve — Lab 13: Portfolio Mandate Defense

**Author:** Drew Scheiderer · **Date:** 2026-10-15 · **Case:** Meridian Foundation Reserve
(fictional, course-assigned common case; not Project 2 work)

**Question (D):** Which of these portfolios does the Meridian Foundation's mandate permit — and
what must the CIO answer before anyone optimizes?

**Files:** [`mandate.py`](mandate.py) · executed output
[`output/Meridian_2026-10-15_lab13_checker.txt`](output/Meridian_2026-10-15_lab13_checker.txt)

---

## 1. Sort before you build (no AI)

Types and reasons are mine, written without AI review. Timing note: I did the sort after the
checker had been built, not before as the lab asks.

| # | What the CIO said | Type | One-line reason |
|---|---|---|---|
| S1 | Horizon seven years; annual rebalancing. | Hard constraint | Establishes the required timeframe and rebalancing schedule |
| S2 | Objective: CPI + 4% a year, net of costs, over rolling five-year periods. | Objective | Defines a target for the portfolio |
| S3 | Pays out $0.75M every quarter; twelve months of payouts held in cash or daily-liquid government securities. | Hard constraint | Establishes the mandatory cash requirements |
| S4 | Benchmark: 60% global equities, 40% U.S. investment-grade bonds. | Preference | Provides a comparison, but doesn't require the portfolio to meet them |
| S5 | Long-only: no borrowing, short sales or derivatives. | Hard constraint | Prohibits certain investments |
| S6 | No single issuer above 8%. | Hard constraint | Sets up a mandatory qualifier for the portfolio |
| S7 | Annual turnover at most 25% without committee approval. | Hard constraint | Sets up a requirement for committee approval |
| S8 | At least 90% redeemable within five business days. | Hard constraint | Sets up a hard limit in a given time frame |
| S9 | "The reserve cannot have a calendar-year loss greater than 10%." No measure, no breach rule. | Unverifiable promise | Cannot guarantee a specific loss amount in the future |
| S10 | No sector, ESG, tax or home-bias preference; nobody has said what the pilot should optimize. | Missing | CIO has not specified what the pilot should optimize |

## 2. The checker — `mandate.py`

Built from the Lab 13 instruction with Claude Code. Standard library only; every threshold is
computed from the inputs at the top of the file. Run from this folder: `python mandate.py`.

**Reserve minimum** = quarters × distribution ÷ reserve size = 4 × $0.75M ÷ $100M = **3.0%**.

| Rule | A | B | C |
|---|---|---|---|
| Weights sum to 100 | 100.0 pass | 100.0 pass | 100.0 pass |
| Long-only (lowest weight) | 0.0 pass | 0.0 pass | 0.0 pass |
| Reserve-eligible ≥ 3.0% (S3) | 14.0 pass | 1.0 FAIL | 2.0 FAIL |
| Redeemable in 5 days ≥ 90% (S8) | 100.0 pass | 85.0 FAIL | 100.0 pass |
| Largest single company ≤ 8% (S6) | 0.0 pass | 9.0 FAIL | 8.0 pass |
| Calendar-year loss (S9) | requires CIO clarification | same | same |
| Verdict | passes every checkable rule | fails 3 rule(s) | fails 1 rule(s) |

**Validation against the known answer:** every value matches the Lab 13 V-table to one decimal.
B's 9.0% is Acme bonds (5%) + Acme stock (4%) combined under one issuer. C's 8.0% Acme stock sits
exactly at the limit and passes ("at most 8%").

**Long-only probe:** in A, Cash set to −2 and global equity to 64, then rerun. Result: A's lowest
weight reads **−2.0 FAIL**, reserve-eligible still passes at **10.0**, all other rules pass —
"fails 1 rule(s)". Weights restored afterwards.

**Answer to the mandate question (checkable rules only):** only **A** passes every checkable rule.
No candidate can be cleared on S9, because the CIO has not defined it.

## 3. The attack — candidate D

**AI proposal (Claude Code, prompted with the Lab 13 E message):** 1% cash, 1% Treasury bills,
1% Treasury 10-year note, **97% global equity index fund**.

It passes every rule `mandate.py` checks: sum 100.0, lowest weight 0.0, reserve-eligible 3.0%
(exactly at the minimum), 100.0% redeemable in 5 days, no single company. The checker confirms
"passes every checkable rule" (see output file).

Statements it offends or exposes, as the AI argued them: **S9**, because a nearly all-equity
portfolio can plausibly lose well over 10% in a calendar year; **S4**, because it is far from
the 60/40 benchmark; and **S2/S3**, because the payout reserve has no buffer above the minimum.

**My judgment (AI closed, two sentences):**

The CIO would reject the portfolio because of the constraint in S3. It says that 12 months of
payouts must be maintained in cash or daily-liquid investments. The 3% in D would only satisfy
that if the portfolio is large enough.

**Partner swap (playing both roles):**

Skipped: I did not do the partner exercise because we did not do the lab in class.

## 4. My question for the CIO (AI closed)

**Question:** Should the portfolio optimize for maximizing returns or minimizing downside risk?

**The answer that changes the design:** If the answer is minimizing downside risk, then the
portfolio should be far more heavily allocated to treasuries and cash.

## 5. Investment policy statement — mapping S1–S10

**What it is and how it works:** An IPS is a document that establishes the guidelines for a
portfolio. It provides the framework for making consistent investment decisions. An IPS defines
what the portfolio should achieve and what constraints it must follow. Together, they create a
guide to ensure investments align with the client's needs.

**Mapping S1–S10 onto the policy statement** (drafted with Claude Code; IPS elements follow
CFA Institute, *Elements of an Investment Policy Statement for Institutional Investors*). The
type column is my sort from section 1, unchanged.

| # | My type | IPS element | What it covers in Meridian's IPS |
|---|---|---|---|
| S1 | Hard constraint | Constraints: time horizon · Risk management: rebalancing | Seven-year horizon; rebalance annually |
| S2 | Objective | Return objective | CPI + 4% net of costs, judged over rolling five-year periods |
| S3 | Hard constraint | Constraints: liquidity (cash-flow needs) | $3.0M a year of payouts → at least 3.0% held reserve-eligible |
| S4 | Preference | Risk management: performance measurement / benchmark | 60/40 global equity / U.S. IG bonds as the yardstick |
| S5 | Hard constraint | Constraints: permitted investments (legal / unique circumstances) | No leverage, shorts or derivatives |
| S6 | Hard constraint | Risk management: concentration / diversification limits | No company above 8%; cash, Treasury and diversified funds exempt |
| S7 | Hard constraint | Governance · Risk management: rebalancing and implementation | Turnover above 25% a year needs committee approval |
| S8 | Hard constraint | Constraints: liquidity | At least 90% redeemable within five business days |
| S9 | Unverifiable promise | Risk objective (risk tolerance) | Stated as a loss ceiling with no measure, confidence level or breach rule |
| S10 | Missing | Constraints: tax and unique circumstances · gap in return/risk objectives | No preferences stated; no objective defined for the optimizer |

**What the mapping shows:** the constraint side of the IPS is well specified (S1, S3, S5–S8 are
measurable), but the risk objective is undefined (S9) and nothing says what an optimizer should
maximize or minimize (S10). The IPS cannot yet support optimization.

## 6. Reflect

**1. Why a portfolio can pass every checkable rule and still be wrong for this client:**
A portfolio can pass all the rules, but still be wrong for the client because 97% in equities
can still expose them to major downside risk. This is why an optimization strategy is necessary,
because a portfolio that meets all of the hard constraints can still be optimized for the wrong
objective.

**2. The S1–S10 type I was least sure of:** S10, because the CIO has not defined what the
portfolio should optimize.

---

*This is a learning exercise on a fictional, course-authored case. It is not investment advice.
AI assistance: `mandate.py` and the candidate-D proposal were produced with Claude Code (Claude
Opus 5.5), then run and checked by me against the course's known answer. The S1–S10 mapping onto
the policy statement was drafted with Claude Code from my own statement sort. The statement sort,
the D judgment, the CIO question and the reflection are my own, written with AI closed. Any remaining errors are my own.*
