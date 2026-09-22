# FIN 43900 Project 1 — Equity Research

Equity research on **NVIDIA Corporation (NVDA)** for FIN 43900, AI in Finance, Purdue
University, Fall 2026. Author: Drew Scheiderer.

> **Company switch, 2026-09-22.** This repository began as SPCX (Space Exploration
> Technologies Corp.) research and is still named `SPCX-research` so that lab links already
> submitted on Brightspace keep resolving. The company for all work from 2026-09-22 forward is
> NVIDIA. The SPCX material in `spacex/` is left exactly as it stood and is not extended.

> This repository is coursework for a learning exercise. It is not investment research and it
> is not financial advice.

## Finance decision and intended user

**Decision:** initiate, watch-defer, or do not initiate a position in NVDA.

**Intended user:** a buy-side investment committee with no current position, which needs a
risk-aware recommendation and a focused diligence plan before committing capital.

**As-of date:** September 17, 2026. **Current call: WATCH–DEFER**, carried from the Lab 08
triangulation — revised up from Lab 06's *do not initiate* on a valuation-conviction change, not
a business-quality one. The reasoning and the conditions that would flip it are in
[nvidia/NVIDIA_2026-09-17_lab08.md](nvidia/NVIDIA_2026-09-17_lab08.md).

The evidence base is NVIDIA's Form 10-K for the fiscal year ended January 25, 2026, with market
data as of September 10, 2026 and peer earnings traced to SEC XBRL filing tags. Sources and
as-of dates are carried in the Lab 06 and Lab 08 write-ups.

The superseded SPCX call — WATCH–DEFER as of September 3, 2026, on the Q2 2026 Form 10-Q — is
preserved in [spacex/SpaceX_2026-09-03_report.md](spacex/SpaceX_2026-09-03_report.md) and
[spacex/sources.md](spacex/sources.md). It is history, not the current position.

## Visible result

**Not yet produced.** The DCF model and its executed output land in Week 3 (Labs 05–06); a
frozen `visible_output.json` and application view are Project 1 deliverables. This section
will point to that frozen output — material inputs, as-of date, valuation range, and
conditions — readable without executing anything.

## Repository map

Work is organised one company per folder.

| Path | Contents |
|---|---|
| `dcf.py` | Lab 05 five-year FCFF DCF, carrying the training-case inputs and matching the twelve known answers. |
| `spacex/Project_1_Edition_A.md` | Edition A — the timestamped pre-AI baseline. **Never edited after the fact**; corrections are filed as dated addenda in the research-evolution document. |
| `spacex/SpaceX_2026-09-03_report.md` | Company research report: sourced financial analysis, the current call, and what would change it. |
| `spacex/sources.md` | Citation-to-use map — every source in the report traced to its original location and to where it is used. |
| `spacex/data/SpaceX_Q2_2026_10-Q.xls` | Local copy of the Q2 2026 Form 10-Q financial workbook (EDGAR Online export). |
| `nvidia/NVIDIA_2026-09-10_lab06.md` | Lab 06 write-up: sourced inputs, sensitivity grid, reverse DCF, reasonableness, and the conditional call. |
| `nvidia/dcf.py` | Lab 06 model — twelve lines, sensitivity grid, reverse DCF, and the training-case self-check, from one command. |
| `nvidia/data/NVIDIA_2026-01-25_10-K.xls` | Local copy of the FY2026 Form 10-K financial workbook (EDGAR Online export). |
| `nvidia/NVIDIA_2026-09-17_lab08.md` | Lab 08 write-up: peer policy, two sourced candidate decisions, checked comparison, DCF triangulation, and the revised conditional call. |
| `nvidia/comps.py` | Lab 08 NVIDIA comparables calculator. Imports its analysis layer from `asbury/comps.py`, adding a share-basis check and an earnings-basis sensitivity. |
| `asbury/Asbury_2026-09-15_lab07.md` | Lab 07 write-up: peer policy, use/qualify decisions, implied range, and the leave-one-peer-out interpretation. |
| `asbury/comps.py` | Lab 07 comparable-company P/E calculator for the Asbury training case. |
| `requirements.txt` | Pinned dependency ranges, mirroring the course project environment. |
| `.env.example` | Named-but-empty credential variables. No secrets are committed anywhere. |

**A note on the company history.** Labs 06 and 08 were run on NVIDIA after the instructor
directed the class to use a company with an established published beta — SpaceX listed in June
2026 and has too little trading history for one to exist. As of 2026-09-22 NVIDIA is the company
for all work, Project 1 included, so the two-company split is closed. The SPCX files in
`spacex/` are unchanged and remain the record of that earlier work; `spacex/Project_1_Edition_A.md`
in particular is a timestamped pre-AI baseline and is never edited.

Lab 07 uses the Asbury Automotive training case supplied by the course, kept in `asbury/`
so it stays separate from the Project 1 company work.

## Setup and run

1. Create an isolated environment: `python -m venv .venv`
2. Activate it — Windows: `.venv\Scripts\activate` · macOS/Linux: `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` only if a data provider key is needed. Never commit `.env`.

The Week 3 DCF models use only the Python standard library. Run the Lab 05 training-case model
with `python dcf.py`, and the Lab 06 NVIDIA model with `cd nvidia && python dcf.py`. The Lab 07
comparables calculators are also standard library only: `cd asbury && python comps.py` for
the Lab 07 training case, and `cd nvidia && python comps.py` for the Lab 08 NVIDIA comparison.
The NVIDIA calculator imports the Lab 07 analysis functions, so the arithmetic it runs is the
version already checked against the course's published answers.

## Data sources and point-in-time boundary

Nothing in this repository incorporates information published after the stated as-of date of
each document.

The superseded SPCX work draws on SpaceX's Form 10-Q for the quarter and six months ended
June 30, 2026, SEC accession 0001628280-26-052535, filed August 4, 2026, as reported for those
periods.

For the NVIDIA valuation, the primary source is NVIDIA's Form 10-K for the fiscal year ended
January 25, 2026, filed February 25, 2026. Market data — share price, beta, and the 10-year
Treasury yield — is as of September 10, 2026 and is labeled with its retrieval date in the
Lab 06 write-up.

Lab 07 uses the course's frozen Asbury case inputs: December 31, 2024 closing prices paired
with FY2024 total GAAP diluted EPS. No data is fetched at run time.

Lab 08 compares NVIDIA against AMD and Broadcom at September 10, 2026 closing prices — the same
trading date and price source as the Lab 06 DCF — paired with each company's latest total GAAP
diluted EPS from an annual report published before that date. Peer earnings are traced to the
SEC XBRL `EarningsPerShareDiluted` filing tag with period, form type and accession number. Inputs
are frozen in the file; nothing is fetched at run time.

## Financial conventions

Dollar amounts are in USD millions unless stated otherwise. Negative values appear in
parentheses. Historical results, forecasts, and scenarios are labeled distinctly. Any figure
that could not be sourced is labeled `unresolved`, `estimate`, or `placeholder` rather than
carried as fact.

## Known limitations

Edition A records the open questions in full. The material ones: no verified share price,
fully diluted share count, or enterprise value; no segment-level free cash flow; no
established normalized capital-expenditure run rate for the AI segment; and no peer set or
multiple range for segment valuation. Adjusted EBITDA is reported by the company but is not
treated as a substitute for free cash flow.

---

*AI assistance: research and drafting assisted by ChatGPT/Codex and Claude Code; sources
gathered and verified by me; the judgments are mine.*

*Any remaining errors are my own.*
