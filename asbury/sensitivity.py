"""Which assumptions actually carry the ABG valuation? A one-at-a-time test.

FIN 43900 (AI in Finance, Purdue), Lab 09 -- Session 9.
Author: Drew Scheiderer.

The question this answers: of the nine judgment rows in the Lab 09 assumption
set -- twelve individual parameters -- which three move the valuation most,
measured rather than guessed?

Lab 09 asks which three judgments carry the ABG value. Reading the assumption
table, my first answer was organic growth, the SG&A schedule, and the debt
repayment / buyback pair. This script tested that answer and disagreed with two
thirds of it, so the answer changed. The record of that is the point of the file.

METHOD. One-at-a-time sensitivity. Each run changes exactly one assumption,
holds every other assumption at its base value, rebuilds all five years, and
reports the change in value per share. One-at-a-time means interactions between
assumptions are not captured -- moving growth and margin together is not the sum
of moving each alone. It is the right tool for ranking, not for scenario work.

The engine is imported from proforma.py rather than copied. That engine
reproduces the course's published ABG answer of $291.75 per share, so every
figure below comes from arithmetic that has already been validated.

Standard library only. Run with: cd asbury && python sensitivity.py
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import proforma  # noqa: E402  -- import follows the path insert above


# ---------------------------------------------------------------------------
# INPUTS -- the assumptions to test, and how far to move each
# ---------------------------------------------------------------------------
# Where an assumption is a rate, it moves one percentage point, so the results
# are comparable across rows. Where a one-point move is meaningless -- an
# absolute dollar figure, or a policy the company either has or does not -- the
# test removes or resizes the assumption instead, and the label says so. Those
# rows are NOT comparable with the one-point rows and are not ranked against
# them; read them on their own terms.
#
# Capital spending is included even though it is guidance rather than judgment,
# because leaving it out would hide how much of the value it moves. It is not a
# candidate for the three, since the company told us the figure -- it is not
# mine to choose.
#
# The base SG&A schedule declines from 66.5% to 64.5%. That decline is an
# assumption of margin expansion that the filings do not promise, so it gets a
# second, structural test: hold the ratio flat and see what the expansion was
# worth.

BASE_SGA = [0.665, 0.655, 0.645, 0.645, 0.645]

CASES = [
    ("Terminal growth", "judgment", "2.5% -> 3.5%", {"TERMINAL_GROWTH": 0.035}),
    ("Cost of equity", "judgment", "10% -> 11%", {"COST_OF_EQUITY": 0.11}),
    ("Gross margin", "judgment", "17.05% -> 18.05%", {"GROSS_MARGIN": 0.1805}),
    ("SG&A expansion", "judgment", "removed: flat at 66.5%", {"SGA_TO_GROSS_PROFIT": [0.665] * 5}),
    ("Organic growth", "judgment", "1.8% -> 2.8%", {"REVENUE_GROWTH": 0.028}),
    ("Impairment", "judgment", "removed: 120 -> 0", {"IMPAIRMENT": 0.0}),
    ("Debt repayment", "judgment", "removed: 150 -> 0", {"DEBT_REPAYMENT": 0.0}),
    ("SG&A ratios", "judgment", "all +1pp (worse)", {"SGA_TO_GROSS_PROFIT": [r + 0.01 for r in BASE_SGA]}),
    ("Share buyback", "judgment", "raised: 150 -> 400", {"SHARE_BUYBACK": 400.0}),
    ("Tax rate", "judgment", "25.5% -> 26.5%", {"TAX_RATE": 0.265}),
    ("Capital spending", "guidance", "+20%: 250 -> 300", {"CAPEX": 300.0}),
    ("Other working capital", "judgment", "0.8% -> 1.8%", {"OTHER_WC_TO_REVENUE_CHANGE": 0.018}),
    ("Share buyback", "judgment", "removed: 150 -> 0", {"SHARE_BUYBACK": 0.0}),
    ("Revolver rate", "judgment", "6% -> 7%", {"REVOLVER_RATE": 0.07}),
    ("Revolver limit", "judgment", "850 -> 100", {"REVOLVER_LIMIT": 100.0}),
]

# The three judgments I carried into the checkout, chosen on the evidence below.
CHOSEN = {"Terminal growth", "Gross margin", "SG&A expansion"}


# ---------------------------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------------------------
def value_with(**overrides):
    """Value the company with one or more assumptions temporarily replaced.

    The engine keeps its assumptions as module-level constants, so a test swaps
    the constant, reruns, and puts the original back. The restore sits in a
    finally block so that a run which raises -- an assumption that breaks the
    balance sheet, say -- cannot leave a changed assumption behind and
    contaminate every later case.
    """
    original = {name: getattr(proforma, name) for name in overrides}
    try:
        for name, value in overrides.items():
            setattr(proforma, name, value)

        projection = proforma.build_projection()
        # Same refusal the engine applies: an unbalanced sheet is never valued,
        # including inside a sensitivity run.
        proforma.assert_balanced(projection)
        return proforma.value_equity(projection)["value_per_share"]
    finally:
        for name, value in original.items():
            setattr(proforma, name, value)


def run_sensitivity():
    """Return the base value and every case, ranked by absolute impact."""
    base = value_with()
    results = []

    for assumption, label, change, overrides in CASES:
        try:
            value = value_with(**overrides)
            results.append(
                {
                    "assumption": assumption,
                    "label": label,
                    "change": change,
                    "value": value,
                    "delta": value - base,
                    "percent": (value - base) / base * 100,
                    "refused": False,
                }
            )
        except ValueError:
            # The engine refused to value this case. That is a result, not a bug.
            results.append(
                {
                    "assumption": assumption,
                    "label": label,
                    "change": change,
                    "value": None,
                    "delta": None,
                    "percent": None,
                    "refused": True,
                }
            )

    results.sort(key=lambda row: abs(row["percent"]) if not row["refused"] else -1, reverse=True)
    return base, results


# ---------------------------------------------------------------------------
# INTERFACE -- display only, no finance computed below this line
# ---------------------------------------------------------------------------
def main():
    base, results = run_sensitivity()

    print("=" * 78)
    print("WHICH JUDGMENTS CARRY THE VALUE? -- Asbury Automotive Group (ABG)")
    print("=" * 78)
    print(f"\nBase value per share: ${base:,.2f}")
    print("One assumption changed per run; all others held at base.")
    print("A marked row is one of the three judgments I carried into the checkout.\n")

    print(f"{'':2}{'Assumption':22}{'Label':11}{'Change':24}{'$/share':>9}{'Impact':>9}")
    print("-" * 78)

    for row in results:
        mark = "*" if row["assumption"] in CHOSEN else " "
        if row["refused"]:
            print(
                f"{mark:2}{row['assumption']:22}{row['label']:11}"
                f"{row['change']:24}{'REFUSED':>9}{'':>9}"
            )
            continue
        print(
            f"{mark:2}{row['assumption']:22}{row['label']:11}{row['change']:24}"
            f"{row['value']:>9,.2f}{row['percent']:>8.1f}%"
        )

    print("\n" + "-" * 78)
    print("READING IT")
    print("-" * 78)
    print(
        "The valuation is carried by the terminal value, which is about 80% of the\n"
        "total and runs through a denominator of cost of equity minus terminal\n"
        "growth -- 7.5 points. A thin denominator is a sensitive one, which is why\n"
        "terminal growth tops the table on a one-point move.\n"
        "\n"
        "Gross margin is second because it sits at the top of the funnel: every\n"
        "dollar of it flows down through the SG&A ratio and the tax rate into both\n"
        "the explicit years and the terminal base.\n"
        "\n"
        "The SG&A schedule earns its place on the structural test rather than the\n"
        "one-point one. Declining the ratio from 66.5% to 64.5% assumes a margin\n"
        "expansion the filings do not promise, and that assumption alone is worth\n"
        "roughly a tenth of the value.\n"
        "\n"
        "Two rows look decisive and are not. Impairment is non-cash and is added\n"
        "straight back in FCFE, so the only thing it does to cash is shield tax --\n"
        "removing it makes the income statement look better and the company worth\n"
        "less. The revolver is never drawn in the base case, so its rate and limit\n"
        "do nothing at all.\n"
        "\n"
        "One row is not a judgment at all. Capital spending is guidance, and a 20%\n"
        "increase in it costs more value than any judgment except the discount-rate\n"
        "pair and gross margin. That is worth knowing -- it says the valuation is\n"
        "highly geared to reinvestment -- but it is not a candidate for the three,\n"
        "because the company supplied the number rather than me. Note also that a\n"
        "20% move is a larger shock than the one-point moves above it, so its rank\n"
        "in the table overstates the comparison.\n"
        "\n"
        "The buyback is the subtlest row. At 150 it does not touch value: it sits\n"
        "downstream of FCFE and the model does not retire shares. Raise it to 400\n"
        "and it starts to matter -- not because buybacks became valuable, but\n"
        "because cash then falls through the minimum, the revolver draws, and the\n"
        "interest feeds back into net income. The assumption is inert only while\n"
        "cash stays above the floor. That the model does not retire shares is a\n"
        "real limitation: 150 a year at about $292 would retire close to 3% of the\n"
        "share count annually, and the accretion is not captured here."
    )


if __name__ == "__main__":
    main()
