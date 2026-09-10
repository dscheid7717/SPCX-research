"""Five-year FCFF DCF with sensitivity grid and reverse DCF -- NVIDIA Corporation.

FIN 43900 (AI in Finance, Purdue), Lab 06 -- Session 6.
Author: Drew Scheiderer.

Three questions, one command:
  1. What is one NVDA share worth on a five-year FCFF DCF?
  2. How much does that answer move when the discount rate and terminal
     growth rate move? (the sensitivity grid)
  3. What growth path does today's market price already assume?
     (the reverse DCF)

Inputs and their sources are documented in NVIDIA_2026-09-10_dcf_inputs.md.
Standard library only. Run with: python dcf.py
"""

# ---------------------------------------------------------------------------
# INPUTS -- the only block intended to be edited
# ---------------------------------------------------------------------------
# NVIDIA Corporation, Form 10-K for fiscal year ended January 25, 2026.
# Every row below is traced to a locator in NVIDIA_2026-09-10_dcf_inputs.md.

COMPANY = "NVIDIA Corporation (NVDA)"

STARTING_FCFF = 96895.8      # USD millions. OCF 102,718 + after-tax interest 219.8 - capex 6,042
# Years 1-5 FCFF growth. ANALYST FORECAST, not a sourced figure. Continues the
# observed deceleration (FY2025 +124.1%, FY2026 +58.7%) without assuming a
# cliff, and lands Year 5 near enough to the 3% terminal rate that the Gordon
# fade is not a discontinuity.
GROWTH_RATES = [0.30, 0.22, 0.16, 0.11, 0.07]
WACC = 0.1601                # estimate: 4.944% risk-free + 2.217 beta x 5% ERP, debt-weighted
TERMINAL_GROWTH = 0.03       # assumption: long-run nominal US economy
NON_OPERATING_CASH = 62556.0  # cash and equivalents 10,605 + marketable securities 51,951
DEBT = 8468.0                # Note 11 net carrying amount
DILUTED_SHARES = 24514.0     # millions, diluted weighted-average shares from the EPS note

# --- Sensitivity grid axes -------------------------------------------------
GRID_WACC = [0.14, 0.1601, 0.18]
GRID_TERMINAL_GROWTH = [0.02, 0.03, 0.04]

# --- Reverse DCF -----------------------------------------------------------
TARGET_PRICE = 218.36        # NVDA close, 2026-09-10
# Bisection bounds for the uniform shift added to all five growth rates, in
# decimal form. The lab's training defaults are -0.05 and +0.10; NVDA needs a
# far wider upper bound because the market price implies growth well above any
# forecast path, and a bracket that cannot reach the target is a failed search,
# not an answer.
SHIFT_LOWER_BOUND = -0.20
SHIFT_UPPER_BOUND = 1.50

# Show the training-case self-check beneath the company results.
RUN_TRAINING_SELF_CHECK = True


# ---------------------------------------------------------------------------
# ANALYSIS LAYER -- every financial calculation lives here
# ---------------------------------------------------------------------------


def project_fcff(starting_fcff, growth_rates):
    """Grow Year 0 FCFF forward one year at a time.

    Each year compounds off the prior projected year, not off Year 0, so the
    growth schedule fades the way an analyst forecast fades.
    """
    projected = []
    current = starting_fcff
    for rate in growth_rates:
        current = current * (1.0 + rate)
        projected.append(current)
    return projected


def discount_factor(wacc, year):
    """Present value factor for a cash flow arriving at the END of `year`."""
    return 1.0 / (1.0 + wacc) ** year


def present_value_explicit(projected_fcff, wacc):
    """PV of the explicit five-year forecast, discounted at t = 1..5."""
    return sum(
        fcff * discount_factor(wacc, year)
        for year, fcff in enumerate(projected_fcff, start=1)
    )


def gordon_terminal_value(final_fcff, wacc, terminal_growth):
    """Value at Year 5 of every cash flow from Year 6 onward.

    Gordon Growth: the Year 6 cash flow, final_fcff * (1 + g), capitalized at
    (WACC - g). The result is stated in Year 5 dollars and still has to be
    discounted back to today.
    """
    return final_fcff * (1.0 + terminal_growth) / (wacc - terminal_growth)


def run_dcf(
    starting_fcff,
    growth_rates,
    wacc,
    terminal_growth,
    non_operating_cash,
    debt,
    diluted_shares,
):
    """Run the full model and return every reported figure in one dict."""
    # A perpetuity only converges when the discount rate exceeds the growth
    # rate. At or above WACC the formula returns a negative or infinite value
    # that looks like a number but means nothing, so refuse to run.
    if terminal_growth >= wacc:
        raise ValueError(
            "Terminal growth ({:.4f}) must be below WACC ({:.4f}); the Gordon "
            "Growth Method does not converge otherwise.".format(
                terminal_growth, wacc
            )
        )

    projected_fcff = project_fcff(starting_fcff, growth_rates)
    horizon = len(projected_fcff)

    pv_explicit = present_value_explicit(projected_fcff, wacc)
    terminal_value = gordon_terminal_value(
        projected_fcff[-1], wacc, terminal_growth
    )
    pv_terminal = terminal_value * discount_factor(wacc, horizon)

    enterprise_value = pv_explicit + pv_terminal
    # Cash is a non-operating asset the DCF never valued, so it is added back.
    # Debt is a claim ahead of shareholders, so it is subtracted.
    equity_value = enterprise_value + non_operating_cash - debt
    value_per_share = equity_value / diluted_shares

    # How much of the answer rests on the terminal assumption rather than on
    # the five years actually forecast. A high share is a warning, not an error.
    terminal_share = pv_terminal / enterprise_value * 100.0

    return {
        "projected_fcff": projected_fcff,
        "pv_explicit": pv_explicit,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "value_per_share": value_per_share,
        "terminal_pct_of_ev": terminal_share,
    }


def value_per_share_only(starting_fcff, growth_rates, wacc, terminal_growth,
                         non_operating_cash, debt, diluted_shares):
    """Value per share alone, or None where the model does not converge.

    The grid needs to ask "what is this cell worth?" without a failed cell
    stopping the whole run.
    """
    if terminal_growth >= wacc:
        return None
    return run_dcf(
        starting_fcff, growth_rates, wacc, terminal_growth,
        non_operating_cash, debt, diluted_shares,
    )["value_per_share"]


def sensitivity_grid(starting_fcff, growth_rates, wacc_values,
                     terminal_growth_values, non_operating_cash, debt,
                     diluted_shares):
    """Value per diluted share for every WACC x terminal-growth combination.

    Everything except those two inputs is held fixed. Cells where terminal
    growth is at or above WACC are returned as None -- invalid, not valued.
    """
    return [
        [
            value_per_share_only(
                starting_fcff, growth_rates, wacc, terminal_growth,
                non_operating_cash, debt, diluted_shares,
            )
            for terminal_growth in terminal_growth_values
        ]
        for wacc in wacc_values
    ]


def reverse_dcf_growth_shift(
    target_price,
    starting_fcff,
    growth_rates,
    wacc,
    terminal_growth,
    non_operating_cash,
    debt,
    diluted_shares,
    lower_bound,
    upper_bound,
    tolerance=1e-8,
    max_iterations=200,
):
    """Solve for the uniform shift on all five growth rates that hits a price.

    Answers "what growth does the market price already assume?" -- holding
    WACC, terminal growth, starting FCFF and the cash/debt/share bridge fixed.

    Value per share rises monotonically with the shift, so bisection is safe:
    each step halves a bracket known to contain the answer.

    Returns the solved shift, or None if the target lies outside the bracket.
    Raises ValueError on a bracket that is economically meaningless.
    """
    if lower_bound >= upper_bound:
        raise ValueError(
            "Lower bound ({:.4f}) must be below upper bound ({:.4f}).".format(
                lower_bound, upper_bound
            )
        )

    # A shift that drives any annual growth rate to -100% or below wipes out
    # the cash flow entirely and makes the search meaningless. Refuse it.
    worst_rate = min(growth_rates) + lower_bound
    if worst_rate <= -1.0:
        raise ValueError(
            "Lower bound {:+.4f} pushes an annual growth rate to {:.4f}, at or "
            "below -100%. Raise SHIFT_LOWER_BOUND.".format(
                lower_bound, worst_rate
            )
        )

    def value_at(shift):
        return value_per_share_only(
            starting_fcff, [g + shift for g in growth_rates], wacc,
            terminal_growth, non_operating_cash, debt, diluted_shares,
        )

    value_low = value_at(lower_bound)
    value_high = value_at(upper_bound)

    # If the target is not bracketed, say so. Returning a bound would be
    # reporting the edge of the search as if it were the answer.
    if value_low is None or value_high is None:
        return None
    if not (value_low <= target_price <= value_high):
        return None

    low, high = lower_bound, upper_bound
    for _ in range(max_iterations):
        middle = (low + high) / 2.0
        if high - low < tolerance:
            break
        if value_at(middle) < target_price:
            low = middle
        else:
            high = middle
    return (low + high) / 2.0


# ---------------------------------------------------------------------------
# INTERFACE LAYER -- printing only, no financial computation
# ---------------------------------------------------------------------------


def report_dcf(results, company):
    """Print the twelve required results, each to four decimals."""
    print("Five-Year FCFF DCF -- {}".format(company))
    print("=" * 62)
    for year, fcff in enumerate(results["projected_fcff"], start=1):
        print("FCFF Year {:d}{:>42.4f}".format(year, fcff))
    print("-" * 62)
    print("PV of explicit FCFF{:>43.4f}".format(results["pv_explicit"]))
    print("Terminal value at Year 5{:>38.4f}".format(results["terminal_value"]))
    print("PV of terminal value{:>42.4f}".format(results["pv_terminal"]))
    print("Enterprise value{:>46.4f}".format(results["enterprise_value"]))
    print("Equity value{:>50.4f}".format(results["equity_value"]))
    print("Value per share{:>47.4f}".format(results["value_per_share"]))
    print("Terminal value % of EV{:>40.4f}".format(results["terminal_pct_of_ev"]))


def report_grid(grid, wacc_values, terminal_growth_values, base_wacc,
                base_terminal_growth):
    """Print the sensitivity grid as a terminal-readable table."""
    print()
    print("Sensitivity: value per diluted share ($)")
    print("=" * 62)
    header = "{:<14}".format("WACC \\ g")
    for terminal_growth in terminal_growth_values:
        header += "{:>14}".format("{:.2%}".format(terminal_growth))
    print(header)
    print("-" * 62)

    for row_index, wacc in enumerate(wacc_values):
        line = "{:<14}".format("{:.2%}".format(wacc))
        for column_index, terminal_growth in enumerate(terminal_growth_values):
            value = grid[row_index][column_index]
            if value is None:
                cell = "invalid"
            else:
                cell = "{:,.2f}".format(value)
                # Mark the base case so the centre of the grid is unmistakable.
                if (abs(wacc - base_wacc) < 1e-9
                        and abs(terminal_growth - base_terminal_growth) < 1e-9):
                    cell = "*" + cell + "*"
            line += "{:>14}".format(cell)
        print(line)

    print("-" * 62)
    print("* base case *  |  'invalid': terminal growth >= WACC, no convergence")

    valid = [v for row in grid for v in row if v is not None]
    if valid:
        print("Range across the corners: ${:,.2f} to ${:,.2f}".format(
            min(valid), max(valid)))


def report_reverse_dcf(shift, target_price, growth_rates, wacc,
                       terminal_growth, lower_bound, upper_bound):
    """Print the reverse DCF result and everything held fixed."""
    print()
    print("Reverse DCF: the growth the price already assumes")
    print("=" * 62)
    print("Target price{:>50.4f}".format(target_price))

    if shift is None:
        print()
        print("NO SOLUTION in the bracket [{:+.2%}, {:+.2%}].".format(
            lower_bound, upper_bound))
        print("The target price cannot be reached by shifting growth alone")
        print("inside these bounds. Widen them or reconsider another input --")
        print("a bound is not an answer.")
        return

    print("Solved uniform growth shift{:>35}".format(
        "{:+.4f}  ({:+.2f} points)".format(shift, shift * 100.0)))
    print()
    print("Implied growth path, Years 1-5:")
    for year, rate in enumerate(growth_rates, start=1):
        print("  Year {:d}:  {:>7.2%}  ->  {:>7.2%}".format(
            year, rate, rate + shift))
    print()
    print("Held fixed while solving:")
    print("  - Starting FCFF")
    print("  - WACC ({:.2%})".format(wacc))
    print("  - Terminal growth ({:.2%})".format(terminal_growth))
    print("  - Non-operating cash, debt, and diluted shares (the bridge)")
    print()
    print("This is one set of assumptions consistent with the price.")
    print("It is not proof of mispricing.")


# ---------------------------------------------------------------------------
# TRAINING-CASE SELF-CHECK
# ---------------------------------------------------------------------------
# The lab requires reproducing the training case before trusting the company
# run. Rather than editing the inputs block back and forth, the same analysis
# functions are re-run here against the training inputs and compared to the
# published known answers.

TRAINING_INPUTS = {
    "starting_fcff": 100.0,
    "growth_rates": [0.08, 0.06, 0.05, 0.04, 0.03],
    "wacc": 0.10,
    "terminal_growth": 0.03,
    "non_operating_cash": 50.0,
    "debt": 300.0,
    "diluted_shares": 50.0,
}

# Published answers from the Lab 06 handout.
TRAINING_KNOWN_VALUE_PER_SHARE = 27.50
TRAINING_KNOWN_GRID = {
    (0.09, 0.02): 28.60, (0.09, 0.03): 32.94, (0.09, 0.04): 39.02,
    (0.10, 0.02): 24.36, (0.10, 0.03): 27.50, (0.10, 0.04): 31.69,
    (0.11, 0.02): 21.06, (0.11, 0.03): 23.41, (0.11, 0.04): 26.44,
}
TRAINING_TARGET_PRICE = 30.00
TRAINING_KNOWN_SHIFT_POINTS = 1.78


def run_training_self_check():
    """Reproduce the published training answers; report every comparison."""
    print()
    print("Training-case self-check (published answers vs this model)")
    print("=" * 62)

    passed = True

    value = run_dcf(**TRAINING_INPUTS)["value_per_share"]
    ok = abs(value - TRAINING_KNOWN_VALUE_PER_SHARE) < 0.005
    passed &= ok
    print("Value per share       expected {:>8.2f}   got {:>8.4f}   {}".format(
        TRAINING_KNOWN_VALUE_PER_SHARE, value, "OK" if ok else "MISMATCH"))

    print("-" * 62)
    print("Grid, cell by cell:")
    for (wacc, terminal_growth), expected in sorted(TRAINING_KNOWN_GRID.items()):
        got = value_per_share_only(
            TRAINING_INPUTS["starting_fcff"], TRAINING_INPUTS["growth_rates"],
            wacc, terminal_growth, TRAINING_INPUTS["non_operating_cash"],
            TRAINING_INPUTS["debt"], TRAINING_INPUTS["diluted_shares"],
        )
        ok = got is not None and abs(got - expected) < 0.005
        passed &= ok
        print("  WACC {:.0%} / g {:.0%}    expected {:>8.2f}   got {:>8.4f}   {}"
              .format(wacc, terminal_growth, expected, got,
                      "OK" if ok else "MISMATCH"))

    print("-" * 62)
    shift = reverse_dcf_growth_shift(
        TRAINING_TARGET_PRICE,
        TRAINING_INPUTS["starting_fcff"], TRAINING_INPUTS["growth_rates"],
        TRAINING_INPUTS["wacc"], TRAINING_INPUTS["terminal_growth"],
        TRAINING_INPUTS["non_operating_cash"], TRAINING_INPUTS["debt"],
        TRAINING_INPUTS["diluted_shares"],
        lower_bound=-0.05, upper_bound=0.10,
    )
    shift_points = None if shift is None else shift * 100.0
    ok = shift_points is not None and abs(
        shift_points - TRAINING_KNOWN_SHIFT_POINTS) < 0.01
    passed &= ok
    print("Reverse DCF at $30.00 expected {:>+8.2f} pts   got {:>+8.4f} pts   {}"
          .format(TRAINING_KNOWN_SHIFT_POINTS,
                  float("nan") if shift_points is None else shift_points,
                  "OK" if ok else "MISMATCH"))

    print("=" * 62)
    print("SELF-CHECK {}".format("PASSED" if passed else "FAILED"))
    return passed


# ---------------------------------------------------------------------------


def main():
    results = run_dcf(
        STARTING_FCFF,
        GROWTH_RATES,
        WACC,
        TERMINAL_GROWTH,
        NON_OPERATING_CASH,
        DEBT,
        DILUTED_SHARES,
    )
    report_dcf(results, COMPANY)

    grid = sensitivity_grid(
        STARTING_FCFF, GROWTH_RATES, GRID_WACC, GRID_TERMINAL_GROWTH,
        NON_OPERATING_CASH, DEBT, DILUTED_SHARES,
    )
    report_grid(grid, GRID_WACC, GRID_TERMINAL_GROWTH, WACC, TERMINAL_GROWTH)

    shift = reverse_dcf_growth_shift(
        TARGET_PRICE, STARTING_FCFF, GROWTH_RATES, WACC, TERMINAL_GROWTH,
        NON_OPERATING_CASH, DEBT, DILUTED_SHARES,
        SHIFT_LOWER_BOUND, SHIFT_UPPER_BOUND,
    )
    report_reverse_dcf(shift, TARGET_PRICE, GROWTH_RATES, WACC,
                       TERMINAL_GROWTH, SHIFT_LOWER_BOUND, SHIFT_UPPER_BOUND)

    # Reasonableness, printed rather than left to the reader.
    value = results["value_per_share"]
    print()
    print("Reasonableness")
    print("=" * 62)
    print("Value per share {:>10.2f}   |   Market price {:>10.2f}   |   {:.2f}x"
          .format(value, TARGET_PRICE, value / TARGET_PRICE))
    inside = 0.5 <= value / TARGET_PRICE <= 2.0
    print("Inside the 0.5x to 2.0x band: {}".format("YES" if inside else "NO"))

    if RUN_TRAINING_SELF_CHECK:
        run_training_self_check()


if __name__ == "__main__":
    main()
