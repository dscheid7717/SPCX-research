# CLAUDE.md

Working instructions for Claude Code in this repository. Ported from my Codex `AGENTS.md`
(2026-09-08) so both tools behave the same way.

## Course context

This repository is my individual work for **FIN 43900 — AI in Finance (Fall 2026)**, Purdue.
Course materials: https://github.com/CinderZhang/FIN43900-Fall2026

- **Brightspace is authoritative** for all dates, points, and submissions. The course repo is
  content only. If the two disagree, Brightspace governs.
- **Project 1** — I am the equity research analyst; the decision is initiate / watch-defer /
  do not initiate **SPCX (Space Exploration Technologies Corp.)** for an investment committee
  with no current position.
- Weekly lab checkouts are usually submitted as GitHub links to files in this repo.

## Academic-integrity rules that constrain you

These come from `PROJECT-SUBMISSION-ARCHITECTURE.md` and the AI Boundary Card. They are not
negotiable.

- **Never modify `docs/Project_1_Edition_A.md`.** It is the timestamped pre-AI baseline of
  record. Corrections are filed as a dated addendum *after* the unchanged Edition A, inside the
  research-evolution document — never as an edit to Edition A itself.
- **Disclose your role.** Anything drafted with AI assistance carries the course report footer
  (learning-exercise disclaimer, named AI tools, "errors are my own").
- **I must be able to explain every line on camera.** Video 2 is a 5-minute codebase
  walkthrough. Prefer code I can defend over code that is merely clever, and explain the
  financial logic as you go rather than only the syntax.
- **Never commit secrets** — no passwords, API keys, tokens, account numbers, or private data.
  Credentials are named-but-empty in `.env.example`.
- Before any Locked Changed-Input Record run, I write the human-authored prediction *first*.
  Do not write predictions for me.
- Compute material finance results in the analysis layer, not in the interface. The required
  direction is evidence → analysis → tests → frozen visible output → app.

## How to work with me

I am Drew Scheiderer, a senior at Purdue studying Finance and Business Analytics. I am
comfortable with financial concepts, data analysis, spreadsheets, and business strategy. I value
work that connects technical analysis to clear business decisions.

- Follow KISS: prefer the simplest solution that clearly satisfies the requirements.
- Lead with the answer, recommendation, or key takeaway.
- Explain reasoning concisely; avoid unnecessary jargon. When using technical terms, connect
  them to their financial or business meaning.
- Make reasonable assumptions when details are missing, but state assumptions that could
  materially affect the result.
- Ask a clarifying question only when different interpretations would substantially change the
  work.
- Flag errors, weak assumptions, data limitations, and risks directly.
- Prefer practical outputs I can use in coursework, presentations, interviews, or professional
  settings.

## Finance work

- Show formulas and assumptions for financial calculations.
- Distinguish clearly between historical results, forecasts, and scenarios.
- Use appropriate metrics: NPV, IRR, WACC, free cash flow, margins, growth rates, valuation
  multiples, risk-adjusted returns.
- Check units, signs, dates, compounding periods, and rounding.
- For valuation or forecasting, include a concise sensitivity analysis when it would affect the
  conclusion. Report a range, not false point precision.
- Every load-bearing number carries value, unit, as-of date, and an exact source locator. A row
  I cannot source is labeled `unresolved`, `estimate`, or `placeholder` — never invented.
- Do not present estimates as facts or imply certainty the evidence does not support.

## Business analytics work

- Start with the business question before selecting a method.
- Explain what results mean for a decision, not only whether they are statistically significant.
- Check data quality, missing values, outliers, leakage, and possible bias.
- Use reproducible workflows and preserve source data.
- Prefer clear tables and charts over complex visuals. Label axes, units, time periods, sources,
  and assumptions.
- When building a model, report relevant validation metrics and explain limitations in plain
  language.

## Coding and files

- Prefer readable, well-structured solutions over clever ones.
- Use descriptive names; comment only where the reasoning is not obvious.
- Follow the existing project structure and style.
- Do not overwrite source files or unrelated work without explicit permission.
- Verify important changes with a test, calculation check, or rendered output. When the course
  supplies known answers, match them to the stated precision before moving on.
- For spreadsheets, keep inputs, calculations, and outputs clearly separated.
- For notebooks, organize the work to run top to bottom without hidden state.

## File naming

- One company, one folder. Dated, descriptive names — `SpaceX_2026-09-03_report.md`.
- No `final_v2_REAL.md`, no `Untitled(3).md`, no duplicate copies of the same document.

## Deliverables

- Polished enough for an upper-level Purdue business course or an entry-level finance and
  analytics role.
- Summarize the conclusion, supporting evidence, and recommended next action.
- Cite external data and identify its as-of date.
- Proofread final deliverables.
- When handing off files, briefly explain what was created or changed and how to use it.

## Default tools and conventions

- Excel-compatible workbooks for spreadsheet deliverables unless another format is requested.
- Python plus common analytics libraries for reproducible analysis; pin versions to
  `requirements.txt`.
- SQL for relational data work.
- Markdown for short reports and documentation.
- Standard U.S. financial conventions: USD, commas for thousands, parentheses for negatives,
  clearly labeled percentages.
