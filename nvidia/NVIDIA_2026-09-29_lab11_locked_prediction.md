# Locked Changed-Input Record — Lab 11 Sensitivity

**Model:** [`nvidia/proforma.py`](proforma.py) · **Company:** NVIDIA Corporation (NVDA)
**Base outputs, before any change** — from [`output/NVIDIA_2026-09-29_lab11_base.txt`](output/NVIDIA_2026-09-29_lab11_base.txt):

| Output | Base value |
|---|---:|
| FY2031E operating profit | 255,618 USD m |
| FY2031E free cash flow to equity (FCFE) | 222,922 USD m |
| Value per share | $58.23 |

> **Status: NOT YET WRITTEN — human-authored, pre-run.**
>
> Lab 11: *"Before running a change, close AI and save one prediction with a timestamp or
> Git commit: input old → new with units, expected output direction and rough size, and
> why."*
>
> Claude built the sensitivity rig and verified it against itself, but has **not** run either
> driver and has not chosen the drivers or the ranges. The lab's own instruction to the AI is
> *"Do not generate company data, choose new ranges, or write my interpretation for me."*
>
> **Commit this file before the first sensitivity run.** The commit timestamp is the evidence
> that the prediction preceded the result.

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
| FY2031E operating profit | | _to fill_ | |
| FY2031E FCFE | | _to fill_ | |
| Value per share | | _to fill_ | |

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
| FY2031E operating profit | | _to fill_ | |
| FY2031E FCFE | | _to fill_ | |
| Value per share | | _to fill_ | |

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

**Actual results:**

**Where the prediction was wrong, and what explains the error:**

**Does this change my valuation conclusion or research priority?** (A reasoned "no change"
is a valid answer and is explicitly allowed.)

---

*Prediction written by Drew Scheiderer with no AI assistance, before any sensitivity run.*
