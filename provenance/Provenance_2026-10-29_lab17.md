# Lab 17 — Point-in-Time Audit

**Author:** Drew Scheiderer · **Date:** 2026-10-29 · **Project 2 universe:** BIL / IEF / LQD / VT
(objective: CPI + 4%)

**Question (D):** Was each number in my series knowable on the day I would have traded on it,
and may Project 2 use it?

**Files:** [`asof_app.py`](asof_app.py)

**Run** (from this folder, with the project `.venv` active): `streamlit run asof_app.py`

---

## Explain to my partner first (no screen)

Inflation (CPI) pushes yields up, so IEF and LQD lose value.

## I — the app: `asof_app.py`

Built from the Lab 17 instruction with Claude Code.
- **Data:** FRED's and ALFRED's public CSV downloads, with no API key and one request per series.
  `fetch_today` gets the series as it reads today; `fetch_as_known` gets it as it read on the
  "as known on" date. Both are cached, and a "." in the data is treated as a missing day.
- **Sidebar:** the four rate series (all selected at the start), a box for any other FRED IDs,
  the start date (2020-01-01) and the "as known on" date (today).
- **Page:** a line chart per series with the last date known then; one table with each ID linked
  to its FRED page, the last date and value then vs. today, how many values were published later,
  and how many have been revised since.
- **Errors:** an unknown ID shows an error for that series only, and the rest of the page keeps
  working.

**Build note:** FRED stalled requests that sent a browser-style User-Agent (60-second timeout) but
answered the default Python one in 0.1 seconds, so the app uses the default.

## V — proof on the known answer

As known on **2026-10-05**:

| Series | Last date known | Value | Course answer |
|---|---|---:|---|
| BAA | 2026-09 | 6.47 | ✓ |
| FEDFUNDS | 2026-09 | 3.75 | ✓ |
| DGS10 | 2026-10-02 | 5.28 | ✓ |
| MORTGAGE30US | 2026-10-01 | 7.28 | ✓ |

On today's data (downloaded 2026-10-29), DGS10 has 16 values after 2 October and
MORTGAGE30US has 4. Neither has any revisions: market rates are known the same day and never
change.

**PAYEMS probe** (as known on **2025-01-15**):
- December 2024 read **159,536** then and reads **158,316** today, 1,220 thousand jobs lower.
- **381** values on the same dates have been revised since, so the app is not reading today's
  data twice.

**Unknown ID test:** `NOTASERIES` shows "could not load (HTTP Error 404)" and every other series
still loads.

## E — my series: CPIAUCSL

| As known on | Last month known | Value | Published later | Revised since |
|---|---|---:|---:|---:|
| 2026-09-30 (last day of last month) | 2026-08 | 334.131 | 1 | 0 |
| 2026-10-29 (today) | 2026-09 | 336.298 | 0 | 0 |

September 2026 vanishes when the date moves back to 30 September: it had not been published yet.
Going back further shows the revisions. As known on 2025-01-15, **60** values had been revised
since, and December 2024 read 317.685 then against 317.604 today.

### Data card

| Field | CPIAUCSL |
|---|---|
| **Source** | U.S. Bureau of Labor Statistics, via FRED/ALFRED (Federal Reserve Bank of St. Louis): [fred.stlouisfed.org/series/CPIAUCSL](https://fred.stlouisfed.org/series/CPIAUCSL) |
| **What it measures** | Consumer Price Index for All Urban Consumers: All Items in U.S. City Average. The price level of a typical consumer basket. |
| **Units** | Index, 1982–1984 = 100, seasonally adjusted, monthly |
| **Publication lag** | About two weeks after the month ends. August 2026 first appears in the ALFRED vintage of 2026-09-11; September 2026 in the vintage of 2026-10-14. |
| **Revisions** | Yes. The seasonally adjusted values are revised each year for the past five years: everything from 2021-01 to 2025-12 changed between the 2026-01-31 vintage and today. The latest few months are not revised month to month (0 revisions since 2026-09-30). |
| **Gaps** | **October 2025 is missing** (blank on FRED). It was never published because of the 2025 federal government shutdown. |
| **Download date** | 2026-10-29 |
| **Why it matters for Project 2** | My objective is CPI + 4%, and inflation moves bond yields, which drive IEF and LQD. |

**Three values checked by hand against the FRED page:**

| Month | App value | FRED page |
|---|---:|---|
| 2026-09 | 336.298 | checked ✓ |
| 2026-08 | 334.131 | checked ✓ |
| 2024-12 | 317.604 | checked ✓ |

All three values were checked on the FRED page and are correct.

**Partner attack on the card:**

**Field trusted least: publication date.** My partner trusted CPIAUCSL the least because its
last "as known" date is the latest of the series.

> **TODO (Drew):** your two-sentence answer, with evidence from the app or the FRED page.

## Explain the code (no AI)

`fetch_as_known` builds the ALFRED web address with the series and date. `_read_csv` downloads
the data and returns the dates and values. The data is downloaded once per hour
(`@st.cache_data(ttl=3600)`). When there is a bad ID, FRED returns a 404 error.

**Partner's question:** How did I get the data?

**My answer:** From FRED's and ALFRED's public CSV downloads. `fetch_as_known` builds the ALFRED
web address with the series and date, and `_read_csv` downloads it and returns the dates and
values.

## Your call

**Admit, with an as-of rule:** use CPI only as known on the given decision date, and assume a
two-week lag. This ensures the data used was actually available at the time. This would change
if the series stopped being published or if the revisions became large.

## Data card — learn on my own

1. **What it is:** a record of where the data comes from (here, FRED and its CSV files) and how it
   behaves.
2. **How it works:** leaks are stopped by the publication lag, revisions and download date fields.
3. **Why "cleaned the data" is not a data card:** cleaning the data just hides which rows were
   changed and why.

## Reflect

1. CPI is published about two weeks after the month ends. On September 30th, the app still shows
   August as the latest month.
2. A backtest on today's values would assume we knew each month's CPI right away, which makes
   indicators look sharper than they actually could have been.

---

*This is a learning exercise. It is not investment advice. Data: FRED and ALFRED, Federal Reserve
Bank of St. Louis, downloaded 2026-10-29. AI assistance: `asof_app.py`, the known-answer and probe
runs, and the factual parts of the data card were produced with Claude Code (Claude Opus 5.5). The
partner, no-AI, call, learn-on-my-own and reflection sections are my own. Any remaining errors are
my own.*
