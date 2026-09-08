# SPCX Research — FIN 43900 Project 1

Equity research on **Space Exploration Technologies Corp. (SPCX)** for FIN 43900, AI in
Finance, Purdue University, Fall 2026. Author: Drew Scheiderer.

> This repository is coursework for a learning exercise. It is not investment research and it
> is not financial advice.

## Finance decision and intended user

**Decision:** initiate, watch-defer, or do not initiate a position in SPCX.

**Intended user:** a buy-side investment committee with no current position, which needs a
risk-aware recommendation and a focused diligence plan before committing capital.

**As-of date:** September 3, 2026. **Current call: WATCH–DEFER** — do not initiate until
valuation and the durability of consolidated free cash flow can be tested.

The evidence base is SpaceX's Form 10-Q for the quarter ended June 30, 2026 (filed August 4,
2026), supplemented by the June 2026 IPO prospectus, subsequent 8-Ks, the Q2 2026 earnings
call, and external reporting. See [docs/sources.md](docs/sources.md).

## Visible result

**Not yet produced.** The DCF model and its executed output land in Week 3 (Labs 05–06); a
frozen `visible_output.json` and application view are Project 1 deliverables. This section
will point to that frozen output — material inputs, as-of date, valuation range, and
conditions — readable without executing anything.

## Repository map

| Path | Contents |
|---|---|
| `docs/Project_1_Edition_A.md` | Edition A — the timestamped pre-AI baseline. **Never edited after the fact**; corrections are filed as dated addenda in the research-evolution document. |
| `docs/SpaceX_2026-09-03_report.md` | Company research report: sourced financial analysis, the current call, and what would change it. |
| `docs/sources.md` | Citation-to-use map — every source in the report traced to its original location and to where it is used. |
| `data/SpaceX_Q2_2026_10-Q.xls` | Local copy of the Q2 2026 Form 10-Q financial workbook (EDGAR Online export). |
| `requirements.txt` | Pinned dependency ranges, mirroring the course project environment. |
| `.env.example` | Named-but-empty credential variables. No secrets are committed anywhere. |

Analysis code (`dcf.py` and later modules) is added at the repository root as each lab
produces it.

## Setup and run

1. Create an isolated environment: `python -m venv .venv`
2. Activate it — Windows: `.venv\Scripts\activate` · macOS/Linux: `source .venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` only if a data provider key is needed. Never commit `.env`.

The Week 3 DCF model uses only the Python standard library and runs with `python dcf.py`.

## Data sources and point-in-time boundary

Primary source is SpaceX's Form 10-Q for the quarter and six months ended June 30, 2026, SEC
accession 0001628280-26-052535, filed August 4, 2026. All figures are as reported for those
periods; nothing in this repository incorporates information published after the stated
as-of date of each document.

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
