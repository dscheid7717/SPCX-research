# Meridian Foundation Reserve — Lab 14: Portfolio Baselines

**Author:** Drew Scheiderer · **Date:** 2026-10-20 (completed 2026-10-22) · **Case:** Meridian
Foundation Reserve (fictional, course-assigned common case; not Project 2 work)

**Question (D):** What does each simple portfolio earn and risk — and does any of them meet the
Meridian mandate?

**Files:** [`portfolio.py`](portfolio.py) · [`mandate.py`](mandate.py) (candidate E added) ·
executed output [`output/Meridian_2026-10-20_lab14_portfolio.txt`](output/Meridian_2026-10-20_lab14_portfolio.txt)
and [`output/Meridian_2026-10-20_lab14_mandate.txt`](output/Meridian_2026-10-20_lab14_mandate.txt) ·
Project 2 universe [`prices.csv`](prices.csv)

> **Record note:** I missed the Tuesday session. Every section, including the partner and
> no-AI steps, was completed with Claude Code as a catch-up record so that I can do Lab 15. It is
> not submitted as my own no-AI work.

---

## Answer

**No baseline both meets the 6.5% objective and passes the mandate.** The benchmark is the only
one that earns 6.5% or more (6.80%), but it holds 0% in reserve-eligible assets and fails S3 (3.0%
minimum). Equal weight and inverse volatility hold plenty of reserve but earn only 5.20% and
3.77%. The best mix has to sit between the benchmark and equal weight, which is Lab 15's search.

## 0. Rerun Lab 13

`python mandate.py` reproduces the Lab 13 verdicts: A passes every checkable rule, B fails 3 and
C fails 1, and D passes. Unchanged.

## 1. Explain to a partner: why two risky assets can be less risky than either alone

Portfolio volatility is not the weighted average of the two volatilities. Portfolio variance
includes a cross term, 2·w₁·w₂·ρ·σ₁·σ₂, and when the correlation ρ is below +1 that term is
smaller than it would be if the assets moved in lockstep. When bonds fall, equities don't
reliably fall with them, so part of the movement cancels out.

The benchmark: 40% IG bonds (σ 6%) and 60% equity (σ 16%). The weighted average volatility is
0.4×6 + 0.6×16 = **12.0%**. With ρ = 0.25 the true figure is **10.46%**: 1.54 points of risk
removed without giving up any return (still 6.80%). If ρ were +1 the portfolio would carry the
full 12.0%. At ρ = −1 it would drop to 7.2%. The lower the correlation, the more risk cancels.

## 2. R — inputs (course-authored training values, not market estimates)

| Sleeve | Expected return | Volatility | Reserve-eligible |
|---|---:|---:|---|
| Treasury bills | 3.5% | 0.5% | yes |
| Treasury 10-year note | 4.3% | 7.0% | yes |
| Investment-grade bond fund | 5.0% | 6.0% | no |
| Global equity index fund | 8.0% | 16.0% | no |

Correlations as in the lab table (IG–equity 0.25; 10-year–IG 0.80; 10-year–equity −0.10).
**Objective** = CPI 2.5% (*labelled estimate*) + 4% = **6.5%**. **Reserve minimum** = 3.0% (Lab 13, S3).

## 3. I — the engine: `portfolio.py`

Built from the Lab 14 instruction with Claude Code. Standard library only. The inputs sit at the
top and each calculation has its own function (`covariance_matrix`, `portfolio_return`,
`portfolio_volatility`, `reserve_weight`, three weighting functions, `summarize`) so Lab 15's app
can import them. Run from this folder: `python portfolio.py`.

```
Portfolio           Weights (%)                   Return     Vol  Reserve  Meets 6.5%?
--------------------------------------------------------------------------------------
Benchmark           0.0 / 0.0 / 40.0 / 60.0         6.80   10.46      0.0  yes
Equal weight        25.0 / 25.0 / 25.0 / 25.0       5.20    5.21     50.0  no
Inverse volatility  84.3 / 6.0 / 7.0 / 2.6          3.77    1.05     90.3  no
```

**Formulas.** Covariance(i, j) = ρᵢⱼ·σᵢ·σⱼ. Return = Σ wᵢ·rᵢ. Volatility = √(Σᵢ Σⱼ wᵢ·wⱼ·Covᵢⱼ).
The double sum covers every pair, so the correlation terms can't be dropped by accident.
Inverse-volatility weight = (1/σᵢ) ÷ Σ(1/σⱼ).

## 4. V — proof on the known answer

| Portfolio | Weights: bills / 10-year / IG / equity | Return | Volatility | Reserve | Meets 6.5%? | Match |
|---|---|---:|---:|---:|---|---|
| Benchmark | 0.0 / 0.0 / 40.0 / 60.0 | 6.80 | 10.46 | 0.0 | yes | ✓ |
| Equal weight | 25.0 / 25.0 / 25.0 / 25.0 | 5.20 | 5.21 | 50.0 | no | ✓ |
| Inverse volatility | 84.3 / 6.0 / 7.0 / 2.6 | 3.77 | 1.05 | 90.3 | no | ✓ |

Every value matches the course table to the stated precision. The benchmark's 10.46 (not 9.90)
confirms that the correlation term is included.

**Prove it computes.** IG–equity correlation set to 0.50 in both cells, then rerun. The
benchmark's volatility rose to **11.00** as expected (equal weight 5.49, inverse volatility 1.09).
Set back to 0.25.

**Refuses a bad correlation (swap and break).** IG–equity correlation set to 1.3. Output:
`Refusing to run: correlation (3,4) = 1.3 is outside -1 to 1.`, exit code 1. I also tried an
asymmetric table (0.25 vs 0.30), which was refused with `correlation table is not symmetric at
(3,4)`. Both undone.

**Explain the code: the volatility block.**

```python
def portfolio_volatility(weights, cov):
    n = len(weights)
    variance = sum(weights[i] * weights[j] * cov[i][j] for i in range(n) for j in range(n))
    return math.sqrt(variance)
```

- `n` is the number of sleeves (4).
- The double loop visits all 16 (i, j) pairs. Diagonal pairs (i = j) give wᵢ²σᵢ², the standalone
  risk. Off-diagonal pairs appear twice, (i, j) and (j, i), which supplies the "2·w₁·w₂·cov" in
  the hand formula.
- `cov[i][j]` was built in `covariance_matrix` as ρ·σᵢ·σⱼ with volatilities in decimals, so the
  variance comes out in decimal² and `sqrt` returns a decimal. `summarize` multiplies by 100 to
  print percent.
- *Partner question:* "Why convert volatility to decimals but leave returns in percent?" *Answer:*
  return is linear in the weights, so percent in gives percent out. Variance multiplies two
  volatilities, so percent in would give percent² and a √ off by a factor of 10.

**Read it: the benchmark through the mandate checker.** Added to `mandate.py` as **candidate E**
(40 IG fund, 60 equity fund):

```
Candidate E
  Weights sum to 100                          100.0  pass
  Long-only (lowest weight not negative)        0.0  pass
  Reserve-eligible >= 3.0%                      0.0  FAIL
  Redeemable in 5 days >= 90%                 100.0  pass
  Largest single company <= 8%                  0.0  pass
  Calendar-year loss <= 10% (S9)             requires CIO clarification
  Verdict: fails 1 rule(s)
```

**The client's own benchmark breaks the client's own mandate.** It fails S3 at 0.0% reserve.

## Floor check

- [x] Engine matches the known answer (all 15 values)
- [x] Refuses a bad correlation (1.3, and an asymmetric table)
- [x] Benchmark run through the mandate checker (E fails reserve at 0.0%)

## 5. Diversification — learn on my own

1. **What it is:** combining assets whose returns don't move perfectly together, so that the
   portfolio's risk is lower than the weighted average of the individual risks.
2. **How it works:** variance = Σ wᵢ²σᵢ² + Σᵢ≠ⱼ wᵢwⱼρᵢⱼσᵢσⱼ. With ρ = +1, volatility is exactly the
   weighted average. Any ρ below +1 shrinks the cross term, so some of each asset's movement
   offsets the others. Diversification removes issuer-specific risk but not the systematic risk
   that all the assets share. A low historical correlation is evidence, not a promise: it can rise
   in a crisis.
3. **By hand, the benchmark:**

| Step | Calculation | Result |
|---|---|---:|
| Return | 0.40 × 5.0 + 0.60 × 8.0 | 6.80% |
| Covariance | 0.25 × 0.06 × 0.16 | 0.0024 |
| Variance | 0.40²×0.06² + 0.60²×0.16² + 2×0.40×0.60×0.0024 = 0.000576 + 0.009216 + 0.001152 | 0.010944 |
| Volatility | √0.010944 | **10.46%** |
| Classic error (no cross term) | √(0.000576 + 0.009216) | 9.90% |

## 6. Reflect

1. **Why inverse volatility piles into bills:** bills have a volatility of 0.5% against 6–16% for
   the others, so 1/σ for bills is 200 against 6–14 for the rest, and they take 84.3% of the
   weight. The method looks only at each asset's own risk. It ignores expected return (so it lands
   at 3.77%, far below 6.5%) and ignores correlations. It is "low risk" only because it holds
   almost nothing risky.
2. **Which baseline to show the CIO first:** the **benchmark**. It is the CIO's own yardstick
   (S4), it is the only baseline that clears the 6.5% objective, and it fails the CIO's own
   reserve rule. That sets up the real question: how little has to move from the benchmark into
   bills or the 10-year note to fix the reserve without losing the objective?

---

## Before Thursday — my Project 2 universe, in funds

**Objective:** expected return ≥ **6.5%** a year (CPI 2.5% *estimate* + 4%).
**Hard constraint:** at least **3%** in the reserve-eligible fund (BIL) as a payout reserve.

| Role | Ticker | Fund name | Reserve-eligible |
|---|---|---|---|
| Cash and reserve | BIL | SPDR Bloomberg 1-3 Month T-Bill ETF | yes |
| Government bonds | IEF | iShares 7-10 Year Treasury Bond ETF | no* |
| Fixed income | LQD | iShares iBoxx $ Investment Grade Corporate Bond ETF | no |
| Equity | VT | Vanguard Total World Stock Index Fund ETF Shares | no |

*Meridian counted the 10-year note as reserve-eligible. I count only BIL, because a 7–10 year
Treasury fund can lose several percent in a month (its worst month in this sample was −4.7%), so
it is not "cash or daily-liquid" in any sense a payout reserve needs.

These are the course's practice examples, used as a training universe, not as recommendations.

**[`prices.csv`](prices.csv):** monthly **Adj Close** (adjusted for distributions), date first,
oldest month first, one column per ticker. **60 month-start prices, 2021-10-01 to 2026-09-01**
(59 monthly returns). No missing values.

| Ticker | Source | Download date |
|---|---|---|
| BIL, IEF, LQD, VT | Yahoo Finance via `yfinance` 1.7.0, `interval="1mo"`, `auto_adjust=True` (the Close column equals Adj Close) | 2026-10-22 |

**Sanity check (history, not forecast; labelled `estimate` for Lab 15):** annualized as mean × 12
and SD × √12.

| Ticker | Return | Volatility |
|---|---:|---:|
| BIL | 3.66% | 0.49% |
| IEF | (1.73%) | 7.72% |
| LQD | (0.93%) | 9.87% |
| VT | 11.05% | 14.92% |

**Data limitation to flag for Lab 15:** the window starts in October 2021, right before the 2022
rate shock, so both bond funds show *negative* five-year average returns. These are history, not
expected returns. An optimizer fed these numbers will treat bonds as pure drag and VT as the only
route to 6.5%. In-sample bond–equity correlations are also high (LQD–VT 0.80), which leaves less
diversification than the Meridian training values imply.

---

*This is a learning exercise on a fictional, course-authored case plus a practice fund universe.
It is not investment advice. AI assistance: `portfolio.py`, the candidate-E addition to
`mandate.py`, the price download and this write-up, including the partner and no-AI sections,
were produced with Claude Code (Claude Opus 5.5) as a catch-up record for a missed session. Values
were checked against the course's known answers. I chose the Project 2 universe, objective and
constraint. Any remaining errors are my own.*
