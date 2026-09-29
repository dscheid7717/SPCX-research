# Locked Changed-Input Record — Lab 11 Sensitivity

**Model:** [`nvidia/proforma.py`](proforma.py) · **Company:** NVIDIA Corporation (NVDA)
**Base outputs, before any change** — from [`output/NVIDIA_2026-09-29_lab11_base.txt`](output/NVIDIA_2026-09-29_lab11_base.txt):

| Output | Base value |
|---|---:|
| FY2031E operating profit | 255,618 USD m |
| FY2031E free cash flow to equity (FCFE) | 222,922 USD m |
| Value per share | $58.23 |

> **Status: locked, then reconciled.** Lab 11 requires that *"before running a change, close AI
> and save one prediction with a timestamp or Git commit: input old → new with units, expected
> output direction and rough size, and why."*
>
> **Audit trail, verifiable in `git log`:**
>
> | Commit | What it contains |
> |---|---|
> | `dbf76fd` | the prediction, committed **before** any sensitivity run had been executed |
> | `86a8a9f` | the results, the reconciliation below, and the Lab 11 write-up |
>
> **Post-run edits to this file, declared.** After the run I filled the two per-driver
> "predicted direction and rough size" tables, which were left as empty template scaffolding in
> `dbf76fd`, and replaced this status block, which still read as a to-do. **Neither edit changed
> the prediction.** The quantified forecast — 1–4% of value per percentage point of revenue
> growth against 1% or less per percentage point of gross margin, and revenue growth ranked
> larger — was already written in the "Which driver I expect to be larger" section of `dbf76fd`,
> and `git diff dbf76fd HEAD -- nvidia/NVIDIA_2026-09-29_lab11_locked_prediction.md` shows it
> unchanged. The tables now restate that forecast and mark plainly that operating profit and
> FCFE were **not** sized in advance — only value per share was.

---

## Driver 1 — Revenue growth

**Input (name in `proforma.py`):** `REVENUE_GROWTH`

**Old → new, with units:** a uniform **−2 / +2 percentage point** shift applied to every
forecast year's growth rate, in decimal form.

| | FY2027E | FY2028E | FY2029E | FY2030E | FY2031E |
|---|---:|---:|---:|---:|---:|
| lower | 0.28 | 0.20 | 0.14 | 0.09 | 0.05 |
| **base** | **0.30** | **0.22** | **0.16** | **0.11** | **0.07** |
| higher | 0.32 | 0.24 | 0.18 | 0.13 | 0.09 |

**Years affected:** all five, FY2027E–FY2031E.

**Why this range:** the same uniform-shift mechanism my Lab 06 reverse DCF already uses on this
same growth path. ±2pp is matched to the gross-margin range below so the two spans are
comparable. Every shifted path stays coherent: the higher path tops out at 32%, less than half
FY2026's actual 65.5%, and the lower path ends at 5%, still above the 3% terminal rate so the
Gordon fade is not a discontinuity.

**Predicted direction and rough size:**

| Output | Direction | Rough size | Why |
|---|---|---|---|
| FY2031E operating profit | same direction as the input | *not predicted* | I sized only value per share |
| FY2031E FCFE | same direction as the input | *not predicted* | I sized only value per share |
| Value per share | same direction as the input | **1–4% of value per percentage point of growth** | revenue growth drives the company in the normal way revenue growth does, and it compounds across all five years |

---

## Driver 2 — Gross margin

**Input (name in `proforma.py`):** `GROSS_MARGIN`

**Old → new, with units:** a uniform **−2 / +2 percentage point** shift applied to every
forecast year's margin, in decimal form. (Percentage points, not percent: 0.710 → 0.730, not
0.710 × 1.02 = 0.7242.)

| | FY2027E | FY2028E | FY2029E | FY2030E | FY2031E |
|---|---:|---:|---:|---:|---:|
| lower | 0.690 | 0.685 | 0.680 | 0.675 | 0.670 |
| **base** | **0.710** | **0.705** | **0.700** | **0.695** | **0.690** |
| higher | 0.730 | 0.725 | 0.720 | 0.715 | 0.710 |

**Years affected:** all five, FY2027E–FY2031E.

**Why this range:** NVIDIA's observed three-year gross margin swing was **3.9 percentage
points** peak to trough — 74.99% in FY2025 against 71.07% in FY2026 — so a ±2pp band puts
roughly the same total width around my path as the company actually delivered in three years.
The upper bound of 73.0% in FY2027 stays inside observed history; only the lower bound needs
judgment, and it is the same competitive-erosion argument already in my Lab 10 assumption table.

Gross margin was chosen over R&D ÷ revenue because R&D's history cannot legitimately source a
range. My own Lab 10 argument is that R&D fell from 14.24% to 8.57% *because revenue tripled
underneath it* — so the 14.24% belongs to a company earning $61B, and importing it as an upper
bound would smuggle back the denominator effect I disqualified. A margin is a margin at any
scale.

**Predicted direction and rough size:**

| Output | Direction | Rough size | Why |
|---|---|---|---|
| FY2031E operating profit | same direction as the input | *not predicted* | I sized only value per share |
| FY2031E FCFE | same direction as the input | *not predicted* | I sized only value per share |
| Value per share | same direction as the input | **around 1% or less of value per percentage point of margin** | margin moves value, but to a smaller magnitude than revenue growth |

---

## Which driver I expect to be larger, and why

**Prediction: revenue growth moves value more than gross margin, over these ranges.**

In my words, before any run:

> My prediction is that the change in revenue growth would affect value more. My reasoning is
> that revenue growth is driving the company in the normal way that revenue growth does.
> Additionally, much of Nvidia's valuation comes from capital committed to other companies and
> capital committed to Nvidia. A drop in revenue growth would affect the company directly and
> affect their valuation to their partners and the market as a whole.

**Direction and rough size, in my words:**

> If revenue growth drops from around 30% to around 7%, the value of Nvidia would drop
> significantly. If gross margin drops, Nvidia's value would drop, but not to as large of a
> magnitude as revenue growth.

So: both drivers move all three outputs in the same direction as the input — lower growth or
lower margin means lower operating profit, lower FCFE and lower value per share — and **revenue
growth's span is larger than gross margin's** on all three.

**Quantified, per unit of input:**

> I believe Nvidia's value would change multiple percentage points (1-4%) for each percentage
> point drop in revenue growth. I believe Nvidia's value would change around 1% to less than 1%
> for each percentage point change in gross margin.

**What that commits me to.** The test moves each driver ±2pp, so at a base of $58.23 per share:

| Driver | Predicted sensitivity | Per ±2pp side | Implied span (higher − lower) |
|---|---|---:|---:|
| Revenue growth | 1–4% of value per pp | 2–8%, i.e. $1.16–$4.66 | **4–16%, i.e. $2.33–$9.32** |
| Gross margin | ≤1% of value per pp | ≤2%, i.e. ≤$1.16 | **≤4%, i.e. ≤$2.33** |

So three claims the run can confirm or refute:

1. **Ranking** — revenue growth's value span exceeds gross margin's.
2. **Sign** — both drivers move all three outputs in the same direction as the input.
3. **Magnitude** — revenue growth's span lands in $2.33–$9.32 and gross margin's at or below
   $2.33. Since the ranges are equal ±2pp shifts, the ratio of the two spans should come out
   somewhere between roughly 1x and 4x.

**The mechanism, traced input → statement → output.** Read off the wiring in
[`proforma.py`](proforma.py) — the two drivers do not take the same route, which is part of why
they are a useful pair.

**Revenue growth** touches almost everything, because revenue is the base every other line
scales off:

1. `revenue = prior revenue x (1 + growth)` — and it compounds, so year 5 carries all five shifts
2. → gross profit (revenue x margin) → operating income → pretax → net income
3. → R&D and SG&A both scale off revenue and gross profit, so they partly offset the move
4. → cost of revenue → inventory (125 days) → change in inventory, a cash use
5. → supply obligations (12.8% of inventory) → a partial offset to that cash use
6. → other working capital, which moves with the *change* in revenue
7. → stock compensation (2.96% of revenue), added back in cash and credited to equity
8. → FCFE → value per share

**Gross margin** enters in one place but splits in two directions:

1. `gross profit = revenue x margin` → operating income → net income → FCFE *(income statement)*
2. `cost of revenue = revenue − gross profit`, so a higher margin means a **lower** cost of
   revenue → lower inventory → smaller cash use → higher FCFE *(balance sheet)*
3. SG&A is 3% of gross profit, so it moves with margin and slightly damps the effect
4. supply obligations follow inventory, so they move against the inventory effect

The structural difference: revenue growth **compounds across five years and rescales the whole
model**, while gross margin is a level shift applied to a revenue base that growth already
fixed. Revenue is the only input here that feeds itself year to year.

> **Note to self, written before the run.** The second half of my reasoning above — strategic
> capital committed to and by NVIDIA — is an argument about the real company, not about this
> model. My model holds the 22,251 of non-marketable equity securities flat inside other
> assets, and Lab 10 explicitly excluded the 9,022 of "other income, net" (8,918 of it
> investment gains) from the forecast. So that channel **cannot** move any output here. It is
> a real-world reason the market might react more than my model does, and it belongs in the
> interpretation, but it is not a mechanism I can trace through the statements. The traceable
> mechanism has to run through revenue → gross profit → operating income → net income → FCFE,
> and through revenue → cost of revenue → inventory → working capital.

---

## Reconciliation — filled in AFTER the run, not before

Run at commit `dbf76fd`+1; full output in
[`output/NVIDIA_2026-09-29_lab11_sensitivity.txt`](output/NVIDIA_2026-09-29_lab11_sensitivity.txt).

**Actual results.** Base value per share $58.23.

| Driver | Value: lower / base / higher | Span | Per pp of input |
|---|---|---:|---:|
| Revenue growth | 54.51 / 58.23 / 62.17 | **7.66** | 3.29% of base |
| Gross margin | 56.12 / 58.23 / 60.33 | **4.21** | 1.81% of base |

| Claim | Predicted | Actual | Verdict |
|---|---|---|---|
| Ranking | growth span > margin span | 7.66 vs 4.21 | correct |
| Sign | both move with the input | both, all three outputs | correct |
| Revenue growth size | 1-4% of value per pp | 3.29% per pp | correct |
| Gross margin size | 1% or less per pp | 1.81% per pp | **wrong, ~1.8x my ceiling** |
| Span ratio | roughly 1x to 4x | 1.8x | correct |

**Where the prediction was wrong, and what explains the error.** Four of five right. I
understated gross margin by about 80%, for two reasons I had not traced before running.

1. A percentage point of margin is a percentage point of REVENUE, and FY2031 revenue is
   471,842. So 2pp is 9,437 of gross profit before any offset, against base operating profit of
   255,618. I was sizing margin against margin, when the base that matters is revenue.
2. The terminal value is 59.0% of this valuation and capitalises final-year FCFE, so anything
   that moves the final year moves most of the answer. That amplifies both drivers and I had
   carried it into neither estimate.

I also gave a reason that could not have worked. Strategic capital committed to and by NVIDIA
is excluded from this model by construction, as the pre-run note above says. The ranking was
right; one of my two stated reasons for it was not a mechanism the model contains.

**Does this change my valuation conclusion or research priority?**

**Conclusion: no change, and the no-change reason is the finding.** Both operating drivers
together move value across $54.51-$62.17. The market is at $224.58 and Lab 10's beta grid ran
$48-$74. No operating assumption I can defend from NVIDIA's own history closes a $166 gap, so
the disagreement with the market is not about operations. The call stays WATCH-DEFER.

**Research priority: changed.** Between the two, revenue growth earns the diligence at 1.8x the
leverage. But both are second-order next to the discount rate, which this lab did not test
because it is a valuation input rather than an operating driver.

---

*Prediction written by Drew Scheiderer with no AI assistance, before any sensitivity run.
Reconciliation added after the run, against the committed prediction.*
