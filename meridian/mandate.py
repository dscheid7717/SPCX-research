"""Lab 13 — Meridian Foundation Reserve mandate checker.

Checks candidate portfolios against the CIO's checkable rules (S3, S5, S6, S8).
S9 (calendar-year loss) has no measure and no breach rule, so it is never tested.
Standard library only. Run: python mandate.py
"""

# ---------------------------------------------------------------- inputs (edit here)

# holding: (issuer, business days to redeem, reserve-eligible)
HOLDINGS = {
    "Cash":                       ("none",             0,  True),
    "Treasury bills":             ("U.S. Treasury",    1,  True),
    "Treasury 10-year note":      ("U.S. Treasury",    1,  True),
    "Global equity index fund":   ("diversified fund", 2,  False),
    "Investment-grade bond fund": ("diversified fund", 3,  False),
    "Private real estate fund":   ("diversified fund", 90, False),
    "Acme Corp bonds":            ("Acme Corp",        4,  False),
    "Acme Corp stock":            ("Acme Corp",        1,  False),
}

# Issuers exempt from the single-issuer limit (cash, the Treasury, diversified funds).
EXEMPT_ISSUERS = {"none", "U.S. Treasury", "diversified fund"}

# Candidate portfolios, percent weights.
CANDIDATES = {
    "A": {"Cash": 2, "Treasury bills": 2, "Treasury 10-year note": 10,
          "Global equity index fund": 60, "Investment-grade bond fund": 26,
          "Private real estate fund": 0, "Acme Corp bonds": 0, "Acme Corp stock": 0},
    "B": {"Cash": 1, "Treasury bills": 0, "Treasury 10-year note": 0,
          "Global equity index fund": 55, "Investment-grade bond fund": 20,
          "Private real estate fund": 15, "Acme Corp bonds": 5, "Acme Corp stock": 4},
    "C": {"Cash": 1, "Treasury bills": 1, "Treasury 10-year note": 0,
          "Global equity index fund": 70, "Investment-grade bond fund": 20,
          "Private real estate fund": 0, "Acme Corp bonds": 0, "Acme Corp stock": 8},
    # D: proposed by AI in the Lab 13 "attack" step — passes every checkable rule.
    "D": {"Cash": 1, "Treasury bills": 1, "Treasury 10-year note": 1,
          "Global equity index fund": 97, "Investment-grade bond fund": 0,
          "Private real estate fund": 0, "Acme Corp bonds": 0, "Acme Corp stock": 0},
}

RESERVE_SIZE = 100.0          # USD millions
QUARTERLY_DISTRIBUTION = 0.75  # USD millions per quarter
QUARTERS_TO_COVER = 4
LIQUIDITY_WINDOW_DAYS = 5     # business days
MIN_LIQUID_SHARE = 90.0       # percent
ISSUER_LIMIT = 8.0            # percent
TOLERANCE = 1e-9              # guards float comparisons such as a sum of 100.0000001


# ---------------------------------------------------------------- calculations

def reserve_minimum_pct():
    """Twelve months of payouts as a percent of the reserve (S3)."""
    return QUARTERS_TO_COVER * QUARTERLY_DISTRIBUTION / RESERVE_SIZE * 100


def largest_company_weight(weights):
    """Largest combined weight of one non-exempt issuer; a company's bonds and stock count together."""
    by_issuer = {}
    for holding, weight in weights.items():
        issuer = HOLDINGS[holding][0]
        if issuer not in EXEMPT_ISSUERS:
            by_issuer[issuer] = by_issuer.get(issuer, 0) + weight
    return max(by_issuer.values(), default=0.0)


def check_candidate(weights):
    """Return a list of (rule, measured value, passed) for one candidate."""
    total = sum(weights.values())
    lowest = min(weights.values())
    reserve = sum(w for h, w in weights.items() if HOLDINGS[h][2])
    liquid = sum(w for h, w in weights.items() if HOLDINGS[h][1] <= LIQUIDITY_WINDOW_DAYS)
    largest = largest_company_weight(weights)
    reserve_min = reserve_minimum_pct()

    return [
        ("Weights sum to 100", total, abs(total - 100) <= TOLERANCE),
        ("Long-only (lowest weight not negative)", lowest, lowest >= 0),
        (f"Reserve-eligible >= {reserve_min:.1f}%", reserve, reserve >= reserve_min - TOLERANCE),
        (f"Redeemable in {LIQUIDITY_WINDOW_DAYS} days >= {MIN_LIQUID_SHARE:.0f}%",
         liquid, liquid >= MIN_LIQUID_SHARE - TOLERANCE),
        (f"Largest single company <= {ISSUER_LIMIT:.0f}%", largest, largest <= ISSUER_LIMIT + TOLERANCE),
    ]


# ---------------------------------------------------------------- report

def main():
    print(f"Reserve minimum: {reserve_minimum_pct():.1f}% of the portfolio "
          f"({QUARTERS_TO_COVER} quarters x ${QUARTERLY_DISTRIBUTION}M / ${RESERVE_SIZE:.0f}M)")
    for name, weights in CANDIDATES.items():
        print(f"\nCandidate {name}")
        results = check_candidate(weights)
        for rule, value, passed in results:
            print(f"  {rule:<42} {value:6.1f}  {'pass' if passed else 'FAIL'}")
        print(f"  {'Calendar-year loss <= 10% (S9)':<42} requires CIO clarification")
        failures = sum(1 for _, _, passed in results if not passed)
        print("  Verdict: " + ("passes every checkable rule" if failures == 0
                                else f"fails {failures} rule(s)"))


if __name__ == "__main__":
    main()
