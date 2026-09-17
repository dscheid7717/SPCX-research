"""Comparable-company P/E valuation -- NVIDIA Corporation.

FIN 43900 (AI in Finance, Purdue), Lab 08 -- Session 8.
Author: Drew Scheiderer.

The question this answers: what would one NVIDIA share be worth if investors
priced its earnings the way they price comparable companies' earnings, and how
does that sit beside the Lab 06 discounted cash flow?

The analysis layer is imported from the Lab 07 calculator rather than copied.
That calculator was checked against the course's published Asbury answers, so
the NVIDIA figures below come from arithmetic that has already been validated.
Only the inputs and two NVIDIA-specific tests are new.

Standard library only. Run with: cd nvidia && python comps.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "asbury"))

from comps import (  # noqa: E402  -- import follows the path insert above
    format_price,
    leave_one_out,
    prepare_peers,
    report_inputs,
    report_leave_one_out,
    report_method_note,
    report_range,
    summarize,
)

# ---------------------------------------------------------------------------
# INPUTS -- the only block intended to be edited
# ---------------------------------------------------------------------------
# Comparison basis: September 10, 2026 closing prices -- the same trading date
# and the same price source as the Lab 06 DCF -- paired with each company's
# latest TOTAL GAAP DILUTED EPS from an annual report published before that
# date. Reported GAAP throughout; no company's non-GAAP figure is used.

PRICE_DATE = "2026-09-10"

TARGET = {
    "ticker": "NVDA",
    "name": "NVIDIA",
    "price": 218.36,   # Nasdaq close 2026-09-10 (yfinance), matches Lab 06
    "eps": 4.90,       # FY2026 (ended 2026-01-25), INCOME_STATEMENT row 34
    "net_income": 120067.0,  # INCOME_STATEMENT row 30, USD millions
    "fiscal_end": "2026-01-25",
}

# Peers admitted under the written policy: use or qualify only.
PEERS = [
    {
        "ticker": "AMD",
        "name": "Advanced Micro",
        "price": 503.60,  # Nasdaq close 2026-09-10
        "eps": 2.65,      # FY2025 ended 2025-12-27, 10-K filed 2026-02-04
        "net_income": 4335.0,   # FY2025 net income, USD millions (10-K)
        "fiscal_end": "2025-12-27",
    },
    {
        "ticker": "AVGO",
        "name": "Broadcom",
        "price": 360.83,  # Nasdaq close 2026-09-10
        "eps": 4.77,      # FY2025 ended 2025-11-02, 10-K filed 2025-12-18
        "net_income": 23126.0,  # FY2025 net income, USD millions (10-K)
        "fiscal_end": "2025-11-02",
    },
]

# Candidates screened out under the policy, kept visible rather than deleted.
# These are excluded on a business-model or earnings judgment made before the
# arithmetic, which is why they are not simply handed to the calculator.
EXCLUDED = [
    {
        "ticker": "INTC",
        "name": "Intel",
        "price": 100.32,
        "eps": -0.06,     # FY2025 ended 2025-12-27, 10-K filed 2026-01-23
        "reason": ("integrated device manufacturer with its own fabs and a "
                   "foundry business, not a fabless designer; and FY2025 "
                   "diluted EPS is negative, so no positive multiple exists"),
    },
]

# Components used to test the target's earnings basis. All from the same
# FY2026 Form 10-K as the EPS above, so the adjustment is sourced, not assumed.
NVDA_NET_INCOME = 120067.0        # INCOME_STATEMENT row 30, USD millions
NVDA_PRETAX_INCOME = 141450.0     # INCOME_STATEMENT row 28
NVDA_TAX_EXPENSE = 21383.0        # INCOME_STATEMENT row 29
NVDA_DILUTED_SHARES = 24514.0     # INCOME_STATEMENT row 39, millions
NVDA_INVESTMENT_GAINS = 8918.0    # CASH_FLOW rows 21-22: gains on non-marketable
                                  # and publicly-held equity securities, net


# ---------------------------------------------------------------------------
# ANALYSIS LAYER -- NVIDIA-specific calculations only
# ---------------------------------------------------------------------------


def effective_tax_rate():
    """Income tax expense / income before income tax, from the filing."""
    return NVDA_TAX_EXPENSE / NVDA_PRETAX_INCOME


def eps_excluding_investment_gains():
    """Diluted EPS with the year's equity-securities gains taken back out.

    NVIDIA's FY2026 net income includes $8,918M of gains on non-marketable and
    publicly-held equity securities. The cash flow statement removes that same
    amount as a non-cash item, so it is a mark-to-market gain on investments
    rather than profit earned by selling chips.

    P/E multiplies the target's EPS, so anything unusual in that EPS is carried
    straight into every implied price. Removing it at the company's own
    effective rate shows how much of the answer rests on investment gains.

    The blended effective rate is an approximation -- investment gains may not
    be taxed at the company's average rate -- so this is a sensitivity, not a
    restatement of reported earnings.
    """
    after_tax_gains = NVDA_INVESTMENT_GAINS * (1.0 - effective_tax_rate())
    return (NVDA_NET_INCOME - after_tax_gains) / NVDA_DILUTED_SHARES


def eps_as_computed():
    """Net income / diluted shares, for a like-for-like comparison.

    The filing's rounded $4.90 and this computed figure differ only by the
    filing's rounding. Comparing the adjusted EPS against this one keeps both
    sides of the sensitivity on the same basis.
    """
    return NVDA_NET_INCOME / NVDA_DILUTED_SHARES


def share_basis_check(companies):
    """Derive each company's diluted share count back out of its own filing.

    A P/E is meaningless if the price and the EPS sit on different stock-split
    bases -- a 10-for-1 split restates EPS but an unadjusted price would not
    follow, and the multiple would be wrong by a factor of ten. This is the
    control for that.

    Net income / diluted EPS recovers the share count the company itself used.
    Multiplying that by the quoted price gives a market capitalisation. If the
    price and the EPS were on different split bases, the implied market cap
    would be off by the split factor and would look obviously wrong.
    """
    rows = []
    for company in companies:
        eps = company.get("eps")
        net_income = company.get("net_income")
        if not eps or net_income is None or eps <= 0:
            rows.append({"company": company, "shares": None, "market_cap": None})
            continue
        shares = net_income / eps
        rows.append({
            "company": company,
            "shares": shares,
            "market_cap": shares * company["price"],
        })
    return rows


def earnings_basis_test(usable_peers):
    """Implied prices on reported EPS versus EPS excluding investment gains."""
    bases = [
        ("Reported diluted EPS", TARGET["eps"]),
        ("Computed net income / diluted shares", eps_as_computed()),
        ("Excluding equity-securities gains", eps_excluding_investment_gains()),
    ]
    results = []
    for label, eps in bases:
        summary = summarize(usable_peers, eps)
        results.append({
            "label": label,
            "eps": eps,
            "min_price": summary["min_price"] if summary else None,
            "median_price": summary["median_price"] if summary else None,
            "max_price": summary["max_price"] if summary else None,
        })
    return results


# ---------------------------------------------------------------------------
# INTERFACE LAYER -- formatting only, no calculation
# ---------------------------------------------------------------------------


def report_excluded(excluded):
    if not excluded:
        return
    print("-" * 66)
    print("Screened out under the policy, before any arithmetic")
    for candidate in excluded:
        print("  {} ({})  price {}  diluted EPS {}".format(
            candidate["name"], candidate["ticker"],
            format_price(candidate["price"]), format_price(candidate["eps"])))
        print("      reason: {}".format(candidate["reason"]))


def report_share_basis(rows):
    print("-" * 66)
    print("Share-basis check: price and EPS on the same split basis?")
    print("  {:<8} {:>10} {:>14} {:>16}".format(
        "Ticker", "FY end", "Implied shares", "Implied mkt cap"))
    for row in rows:
        company = row["company"]
        if row["shares"] is None:
            print("  {:<8} {:>10} {:>14}".format(
                company["ticker"], company.get("fiscal_end", "--"), "not meaningful"))
            continue
        print("  {:<8} {:>10} {:>13,.0f}M {:>15,.0f}M".format(
            company["ticker"], company.get("fiscal_end", "--"),
            row["shares"], row["market_cap"]))
    print()
    print("  Implied shares = net income / diluted EPS, both from the same")
    print("  filing. Each implied market cap is the size the company actually")
    print("  is, so no price/EPS pair is off by a stock-split factor.")


def report_earnings_basis(results):
    print("-" * 66)
    print("Earnings-basis test: what the target's own EPS carries")
    print("  NVIDIA effective tax rate: {:.4%}".format(effective_tax_rate()))
    print()
    print("  {:<38} {:>7}  {:>12}".format("Target EPS basis", "EPS", "At median"))
    for row in results:
        print("  {:<38} {:>7}  {:>12}".format(
            row["label"], format_price(row["eps"]), format_price(row["median_price"])))
    print()
    print("  The peer multiples are identical in every row. Only the target's")
    print("  own EPS changes, so the whole difference is the earnings basis.")


def main():
    usable, unusable = prepare_peers(PEERS, TARGET)
    summary = summarize(usable, TARGET["eps"])

    print("NVIDIA Corporation (NVDA) -- Lab 08")
    print("Prices: {} closes.  Earnings: latest annual GAAP diluted EPS".format(PRICE_DATE))
    print("published before that date.")
    print()

    report_inputs(TARGET, usable, unusable)
    report_excluded(EXCLUDED)
    report_share_basis(share_basis_check([TARGET] + usable))
    report_range(summary, TARGET)
    report_leave_one_out(leave_one_out(usable, TARGET["eps"]), summary)
    report_earnings_basis(earnings_basis_test(usable))
    report_method_note()


if __name__ == "__main__":
    main()
