"""Lab 16 — Provenance gate: point-in-time (as-of) filter.

Applies four rules, in order, to a fictional card-spend index for three retailers, and shows what
was knowable on the decision date beside a naive signal that ignores publication dates.
Standard library only. Run: python asof.py
"""

from datetime import date

# ---------------------------------------------------------------- inputs (edit here)
# Course-authored training table (fictional). (row, ticker, month measured, published on, index)

TABLE = [
    (1,  "AAA", "2026-01", "2026-02-10", 101.0),
    (2,  "AAA", "2026-02", "2026-03-10", 104.0),
    (3,  "AAA", "2026-03", "2026-04-10", 109.0),
    (4,  "AAA", "2026-02", "2026-03-25", 103.0),
    (5,  "BBB", "2026-01", "2026-02-10",  98.0),
    (6,  "BBB", "2026-02", "2026-03-10",  97.0),
    (7,  "BBB", "2026-02", "2026-03-10",  97.0),
    (8,  "BBB", "2026-03", "2026-04-10",  92.0),
    (9,  "CCC", "2026-01", "2026-02-10", 110.0),
    (10, "CCC", "2026-02", "2026-04-05", 112.0),
    (11, "",    "2026-02", "2026-03-10",  99.0),
    (12, "CCC", "2026-02", "2026-03-10", 111.0),
]

DECISION_DATE = "2026-03-31"


# ---------------------------------------------------------------- rules (applied in this order)

def rule1_quarantine_no_ticker(rows):
    """Rule 1: quarantine any row with no ticker."""
    kept = [r for r in rows if r[1].strip()]
    removed = [r for r in rows if not r[1].strip()]
    return kept, removed


def rule2_remove_exact_duplicates(rows):
    """Rule 2: remove a row identical (apart from its row number) to an earlier row; keep the first."""
    seen, kept, removed = set(), [], []
    for r in rows:
        content = r[1:]
        if content in seen:
            removed.append(r)
        else:
            seen.add(content)
            kept.append(r)
    return kept, removed


def rule3_remove_late(rows, decision_date):
    """Rule 3: remove any row published after the decision date."""
    cutoff = date.fromisoformat(decision_date)
    kept = [r for r in rows if date.fromisoformat(r[3]) <= cutoff]
    removed = [r for r in rows if date.fromisoformat(r[3]) > cutoff]
    return kept, removed


def rule4_keep_latest_revision(rows):
    """Rule 4: for each ticker and month, keep only the latest publication (a revision).

    Runs after rule 3, so every row here was already published by the decision date.
    """
    latest = {}
    for r in rows:
        key = (r[1], r[2])                                   # ticker, month measured
        if key not in latest or r[3] > latest[key][3]:      # ISO dates compare correctly as text
            latest[key] = r
    kept = [r for r in rows if latest[(r[1], r[2])] is r]
    removed = [r for r in rows if latest[(r[1], r[2])] is not r]
    return kept, removed


def as_of_panel(rows, decision_date):
    """Apply rules 1-4 in order. Return the panel and a funnel of (step, removed rows)."""
    funnel = []
    rows, removed = rule1_quarantine_no_ticker(rows)
    funnel.append(("Quarantined: no ticker", removed))
    rows, removed = rule2_remove_exact_duplicates(rows)
    funnel.append(("Exact duplicate", removed))
    rows, removed = rule3_remove_late(rows, decision_date)
    funnel.append((f"Published after {decision_date}", removed))
    rows, removed = rule4_keep_latest_revision(rows)
    funnel.append(("Older vintage replaced by a revision", removed))
    return rows, funnel


def naive_panel(rows):
    """Every row's latest publication, ignoring the decision date (what today's file shows)."""
    rows, _ = rule1_quarantine_no_ticker(rows)
    rows, _ = rule2_remove_exact_duplicates(rows)
    rows, _ = rule4_keep_latest_revision(rows)
    return rows


# ---------------------------------------------------------------- signal

def signals(panel):
    """Per ticker: percent change from the previous month to the latest month in the panel.

    Returns {ticker: (percent change, latest month)}; None if the ticker has fewer than two months.
    """
    by_ticker = {}
    for _, ticker, month, _, value in panel:
        by_ticker.setdefault(ticker, {})[month] = value
    result = {}
    for ticker in sorted(by_ticker):
        months = sorted(by_ticker[ticker])
        if len(months) < 2:
            result[ticker] = None
            continue
        latest, previous = months[-1], months[-2]
        change = (by_ticker[ticker][latest] / by_ticker[ticker][previous] - 1) * 100
        result[ticker] = (change, latest)
    return result


# ---------------------------------------------------------------- report

def main():
    panel, funnel = as_of_panel(TABLE, DECISION_DATE)

    print(f"Decision date: {DECISION_DATE}   Rows in: {len(TABLE)}\n")
    print("Row funnel")
    for step, removed in funnel:
        numbers = ", ".join(str(r[0]) for r in removed) or "none"
        print(f"  {step:<40} removed {len(removed)}: {numbers}")
    print(f"  {'As-of panel':<40} kept {len(panel)}: {', '.join(str(r[0]) for r in panel)}\n")

    print("As-of panel")
    print(f"  {'Row':>3}  {'Ticker':<6} {'Month':<8} {'Published':<11} {'Index':>6}")
    for r in sorted(panel, key=lambda r: (r[1], r[2])):
        print(f"  {r[0]:>3}  {r[1]:<6} {r[2]:<8} {r[3]:<11} {r[4]:>6.1f}")

    as_of = signals(panel)
    naive = signals(naive_panel(TABLE))
    print("\nSignal: % change, previous month to latest month")
    print(f"  {'Ticker':<6} {'As-of signal':>22} {'Naive signal':>22}")
    for ticker in sorted(set(as_of) | set(naive)):
        cells = []
        for s in (as_of.get(ticker), naive.get(ticker)):
            cells.append("n/a" if s is None else f"{s[0]:+.2f}% ({s[1]})")
        print(f"  {ticker:<6} {cells[0]:>22} {cells[1]:>22}")


if __name__ == "__main__":
    main()
