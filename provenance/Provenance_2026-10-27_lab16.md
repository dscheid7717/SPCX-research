# Lab 16 — Provenance Gate

**Author:** Drew Scheiderer · **Date:** 2026-10-27 · **Case:** fictional card-spend index for
three retailers (course training table)

**Question (D):** On the day you would have traded, what did this data actually say, and how
much of what you see now came later?

**Files:** [`asof.py`](asof.py) · executed output
[`output/Provenance_2026-10-27_lab16_asof.txt`](output/Provenance_2026-10-27_lab16_asof.txt)

**Run** (from this folder): `python asof.py`

---

## Explain to my partner first (no screen)

The month measured is the period the data describes. The publication date is when the data is
released.

## R — the training table and the rules

Decision date **2026-03-31**. A row is knowable only if it was published on or before that day.
Twelve rows (AAA, BBB, CCC, plus one row with no ticker), as in the lab table and the inputs at
the top of `asof.py`.

Rules, in order:
1. Quarantine a row with no ticker.
2. Remove an exact duplicate.
3. Remove a row published after the decision date.
4. For one ticker and month with two publications, keep the latest one published by the decision
   date (a revision).

**Signal** = latest knowable month ÷ previous month − 1.

## I — the filter: `asof.py`

Built from the Lab 16 instruction with Claude Code. Standard library only.
- Each rule is its own function (`rule1_…` to `rule4_…`), and `as_of_panel` applies them in
  order while recording the row numbers each rule removes.
- `naive_panel` uses every row's latest publication and ignores the decision date.
- `signals` computes the percent change for each ticker.
- Every row keeps its original row number from start to end.

## V — proof on the known answer

### Row funnel

| Funnel step | Rows removed | Course answer |
|---|---|---|
| Quarantined: no ticker | 11 | ✓ |
| Exact duplicate | 7 | ✓ |
| Published after 31 March | 3, 8, 10 | ✓ |
| Older vintage replaced by a revision | 2 | ✓ |
| As-of panel | 1, 4, 5, 6, 9, 12 | ✓ |

### Signals

| Ticker | As-of signal | Naive signal | Course answer |
|---|---|---|---|
| AAA | +1.98% (February) | +5.83% (March) | ✓ |
| BBB | (1.02%) (February) | (5.15%) (March) | ✓ |
| CCC | +0.91% (February) | +1.82% (February, revised) | ✓ |

**By hand, AAA:**
- As-of: 103.0 ÷ 101.0 − 1 = **+1.98%**. February uses the 25 March revision (row 4), not row 2.
- Naive: 109.0 ÷ 103.0 − 1 = **+5.83%**, using March, which was published 10 April.
- The leak is 3.85 points that nobody had on 31 March.
- Classic error check: keeping row 2 instead of row 4 would give 104.0 ÷ 101.0 − 1 = +2.97%. The
  filter gives +1.98%, so rule 4 works.

**Where each gap comes from:**
- AAA and BBB: the naive column uses March, which was not published until 10 April (rows 3 and 8).
- CCC: both columns use February, but the naive one uses the 5 April revision, 112.0 (row 10),
  where the as-of one uses the 10 March value, 111.0 (row 12). The month is the same; the
  vintage is different.

**Swap and break: later decision date.** I set the decision date to `2026-04-15` and ran it:

```
  Ticker           As-of signal           Naive signal
  AAA          +5.83% (2026-03)       +5.83% (2026-03)
  BBB          -5.15% (2026-03)       -5.15% (2026-03)
  CCC          +1.82% (2026-02)       +1.82% (2026-02)
```

The as-of signal becomes the naive signal for every ticker. The gap at 31 March is exactly what
had not been published yet. Undone (back to 2026-03-31).

**Partner swap:** not done. I had no partner (see the note at the end). I ran the later-date test
above on my own file.

## Explain the code (no AI)

**Question I worked through (no partner):** Why include rule 4 if rule 3 already removes everything after the
decision date?

**My answer:** Rule 3 only removes late rows. Two publications of the same month can both come
out before the decision date (AAA February: rows 2 and 4), and rule 4 keeps the latest one, so we
use the most up-to-date information that was available.

## Floor check

- [x] Filter matches the known answer (funnel and all six signals)
- [x] A later decision date (2026-04-15) turns the as-of signal into the naive signal
- [ ] Partner's file run and broken in class (not done; no partner, see the note at the end)

## Point-in-time — learn on my own

1. **Look-ahead bias** is the error of using information in a prediction or backtest that wasn't
   available yet at the time of the decision.
2. **How it works:** event time is the month measured, publication time is when it is released,
   and a revision replaces a number only from the date it was released.
3. **AAA:** the +5.83% uses March data published 10 April, after the decision date. On 31 March
   you could only know +1.98%.

## Reflect

1. **Rule 3 mattered most.** The rows it removed (3 and 8, March data published 10 April) caused
   the biggest gaps between the as-of and naive signals.
2. **A naive backtest would claim** signals that are stronger and better timed than anything
   tradable, so the strategy looks more profitable than it ever could be in practice.

**Note on partner work:** I attended a different session than my usual one and had no partner,
so I completed this lab individually in class. The partner steps (explain first, swap and break,
the code question) were done on my own.

---

*This is a learning exercise on a fictional, course-authored table. It is not investment advice.
AI assistance: `asof.py` and the factual sections of this write-up were produced with Claude Code
(Claude Opus 5.5), then run and checked against the course's known answer. The partner, no-AI,
learn-on-my-own and reflection sections are my own. Any remaining errors are my own.*
