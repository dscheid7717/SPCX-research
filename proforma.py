"""Five-year three-statement pro-forma engine with an equity (FCFE) valuation.

FIN 43900 (AI in Finance, Purdue), Lab 09 — Session 9.
Author: Drew Scheiderer.

The question this answers: what are five years of a company's statements worth,
built from assumptions you can defend, and how do you know the statements are right?

Two ideas carry this file.

1. CASH IS COMPUTED LAST. Every other line is projected from an assumption. Cash is
   whatever is left over once the business has earned, invested, borrowed and paid.
   That ordering is what makes the balance-sheet check meaningful: if cash were
   plugged to force a balance, the check could never fail and would prove nothing.

2. A BALANCE SHEET THAT DOES NOT BALANCE IS A BUG, NOT A FORECAST. assert_balanced()
   raises before any valuation runs. A model that will happily value broken statements
   has not been checked.

Currently carrying the Asbury Automotive Group (ABG) training case, whose known answer
is $291.75 per share.

Standard library only. Run with: python proforma.py
"""

import sys

# ---------------------------------------------------------------------------
# INPUTS -- the only block intended to be edited
# ---------------------------------------------------------------------------
# Each assumption carries a LABEL, and every judgment carries a reason:
#   history   -- computed from the filings, shown as the arithmetic that makes it
#   guidance  -- the company said so
#   judgment  -- the analyst chose it, and owns it
#   fact      -- a reported figure
#
# All money is USD millions.

COMPANY = "Asbury Automotive Group (ABG)"
FIRST_YEAR = 2026
YEARS = 5

# --- Opening balance sheet, FY2025 (fact: the filed statements) -------------
OPENING = {
    "revenue": 17_999.0,      # FY2025 revenue, the base the projection grows from
    "inventory": 2_135.8,
    "ppe": 3_070.4,
    "other_assets": 6_371.6,
    "cash": 40.4,
    "floor_plan": 2_027.0,    # inventory loans -- see FLOOR PLAN note below
    "debt": 3_572.0,
    "other_liabilities": 2_127.5,
    "equity": 3_891.7,
    "revolver": 0.0,          # undrawn at the opening date
}

# --- Income statement assumptions -------------------------------------------
REVENUE_GROWTH = 0.018        # judgment: organic (same-store) growth, not reported
                              # growth. Reported growth can be bought through
                              # acquisitions; the stores already owned grow at 1.8%.
GROSS_MARGIN = 0.1705         # judgment
SGA_TO_GROSS_PROFIT = [0.665, 0.655, 0.645, 0.645, 0.645]   # judgment: 2026 -> 2030
                              # Note this schedule assumes margin expansion. It is the
                              # least-earned line in the table and the first one a
                              # reviewer should attack.

# history: FY2025 depreciation / FY2025 year-end PP&E. Written as the arithmetic
# that makes it so the exact figure is used, not a rounded one.
DEPRECIATION_TO_OPENING_PPE = 82.4 / 3_070.4

IMPAIRMENT = 120.0            # judgment: non-cash, so it lands in operating income
                              # and is added straight back in FCFE. Its only effect
                              # on cash is the tax it shields.
CAPEX = 250.0                 # guidance
TAX_RATE = 0.255              # judgment

# --- Balance sheet assumptions ----------------------------------------------
# history: FY2025 inventory / FY2025 cost of sales, expressed in days.
INVENTORY_DAYS = 2_135.8 / (17_999.0 - 3_071.7) * 365
# history: FY2025 floor plan / FY2025 inventory. Inventory loans track inventory.
FLOOR_PLAN_TO_INVENTORY = 2_027.0 / 2_135.8
OTHER_WC_TO_REVENUE_CHANGE = 0.008   # judgment: working capital other than inventory
                                     # moves with the CHANGE in revenue, not its level

# --- Financing assumptions ---------------------------------------------------
MINIMUM_CASH = 25.0           # history
REVOLVER_LIMIT = 850.0        # judgment
REVOLVER_RATE = 0.06          # judgment
FLOOR_PLAN_RATE = 0.0467      # history
DEBT_RATE = 0.0544            # history
DEBT_REPAYMENT = 150.0        # judgment
SHARE_BUYBACK = 150.0         # judgment. NOTE: this reduces cash and equity but does
                              # NOT enter FCFE and does NOT retire shares in this
                              # model, so it has no effect on value per share.

# --- Valuation assumptions ---------------------------------------------------
COST_OF_EQUITY = 0.10         # judgment
TERMINAL_GROWTH = 0.025       # judgment
SHARES_OUTSTANDING = 17.951349   # fact: 10-Q, 30 June 2026 (millions)

BALANCE_TOLERANCE = 0.05      # USD millions. Tight enough to catch a real error,
                              # loose enough to ignore float representation noise.


# ---------------------------------------------------------------------------
# ANALYSIS -- the projection engine
# ---------------------------------------------------------------------------
def project_year(opening, sga_ratio):
    """Project one year forward from an opening balance sheet.

    Returns a dict holding that year's income statement, balance sheet, cash flow
    and closing position. The ORDER of the calculations below is the whole point:
    everything is earned from an assumption, and cash falls out last.
    """
    year = {}

    # --- Income statement ---------------------------------------------------
    revenue = opening["revenue"] * (1 + REVENUE_GROWTH)
    gross_profit = revenue * GROSS_MARGIN
    sga = gross_profit * sga_ratio

    # Depreciation is charged on the PP&E the company OPENED the year with, because
    # assets bought during the year have not been in service a full year.
    depreciation = opening["ppe"] * DEPRECIATION_TO_OPENING_PPE
    impairment = IMPAIRMENT

    operating_income = gross_profit - sga - depreciation - impairment

    # Interest is charged on OPENING debt balances for the same reason: the money
    # borrowed during the year was not outstanding for the whole year.
    interest = (
        opening["floor_plan"] * FLOOR_PLAN_RATE
        + opening["debt"] * DEBT_RATE
        + opening["revolver"] * REVOLVER_RATE
    )

    pretax_income = operating_income - interest
    # max(0, ...) because a loss does not generate a cash tax refund here. This is
    # conservative: it never books a benefit the company may not be able to use.
    tax = max(0.0, pretax_income) * TAX_RATE
    net_income = pretax_income - tax

    # --- Balance sheet, every line EXCEPT cash ------------------------------
    cost_of_sales = revenue - gross_profit
    inventory = cost_of_sales * INVENTORY_DAYS / 365

    # Floor plan is inventory financing, so it rises and falls with inventory.
    floor_plan = inventory * FLOOR_PLAN_TO_INVENTORY

    ppe = opening["ppe"] + CAPEX - depreciation

    # Other assets absorb the non-inventory working capital build and the impairment
    # write-down, since the impairment reduces the carrying value of assets.
    revenue_change = revenue - opening["revenue"]
    other_working_capital_change = OTHER_WC_TO_REVENUE_CHANGE * revenue_change
    other_assets = opening["other_assets"] + other_working_capital_change - impairment

    debt = opening["debt"] - DEBT_REPAYMENT
    other_liabilities = opening["other_liabilities"]
    equity = opening["equity"] + net_income - SHARE_BUYBACK

    # --- Free cash flow to equity -------------------------------------------
    # FCFE is cash available to shareholders AFTER lenders are served, so it is
    # discounted at the cost of equity and values the equity directly -- no
    # enterprise-to-equity bridge needed.
    #
    # Depreciation and impairment are added back because they reduced income without
    # moving cash. Floor plan is treated as OPERATING, not financing: it funds
    # inventory, so an inventory build that the manufacturer finances should not look
    # like a cash drain. Removing that term is what sends ABG's cash to about
    # -1.1 billion.
    inventory_change = inventory - opening["inventory"]
    floor_plan_change = floor_plan - opening["floor_plan"]

    fcfe = (
        net_income
        + depreciation
        + impairment
        - CAPEX
        - inventory_change
        - other_working_capital_change
        + floor_plan_change
        - DEBT_REPAYMENT
    )

    # --- Cash, computed LAST, and the revolver ------------------------------
    cash_before_revolver = opening["cash"] + fcfe - SHARE_BUYBACK
    revolver = opening["revolver"]

    if cash_before_revolver < MINIMUM_CASH:
        # Draw only what is needed to reach the minimum, and only what is available.
        shortfall = MINIMUM_CASH - cash_before_revolver
        draw = min(shortfall, REVOLVER_LIMIT - revolver)
        revolver += draw
        cash = cash_before_revolver + draw
    elif revolver > 0 and cash_before_revolver > MINIMUM_CASH:
        # Surplus cash repays the revolver first, down to the minimum cash balance.
        repayment = min(revolver, cash_before_revolver - MINIMUM_CASH)
        revolver -= repayment
        cash = cash_before_revolver - repayment
    else:
        cash = cash_before_revolver

    year.update(
        revenue=revenue,
        gross_profit=gross_profit,
        sga=sga,
        depreciation=depreciation,
        impairment=impairment,
        operating_income=operating_income,
        interest=interest,
        pretax_income=pretax_income,
        tax=tax,
        net_income=net_income,
        inventory=inventory,
        ppe=ppe,
        other_assets=other_assets,
        cash=cash,
        floor_plan=floor_plan,
        debt=debt,
        other_liabilities=other_liabilities,
        equity=equity,
        revolver=revolver,
        inventory_change=inventory_change,
        other_working_capital_change=other_working_capital_change,
        floor_plan_change=floor_plan_change,
        fcfe=fcfe,
        repayment=DEBT_REPAYMENT,
        buyback=SHARE_BUYBACK,
    )

    year["total_assets"] = year["cash"] + year["inventory"] + year["ppe"] + year["other_assets"]
    year["total_liabilities"] = (
        year["floor_plan"] + year["debt"] + year["other_liabilities"] + year["revolver"]
    )
    year["balance_gap"] = year["total_assets"] - year["total_liabilities"] - year["equity"]

    return year


def build_projection(opening=None):
    """Project YEARS years forward. Returns a list of year dicts, 2026 first."""
    state = dict(opening or OPENING)
    projection = []

    for index in range(YEARS):
        year = project_year(state, SGA_TO_GROSS_PROFIT[index])
        year["label"] = f"FY{FIRST_YEAR + index}E"
        projection.append(year)

        # This year's closing position becomes next year's opening position.
        state = {
            "revenue": year["revenue"],
            "inventory": year["inventory"],
            "ppe": year["ppe"],
            "other_assets": year["other_assets"],
            "cash": year["cash"],
            "floor_plan": year["floor_plan"],
            "debt": year["debt"],
            "other_liabilities": year["other_liabilities"],
            "equity": year["equity"],
            "revolver": year["revolver"],
        }

    return projection


# ---------------------------------------------------------------------------
# THE CHECKS -- these stop the model
# ---------------------------------------------------------------------------
def assert_balanced(projection):
    """Raise if any year fails a check. Called BEFORE any valuation runs.

    Two checks:
      1. assets - liabilities - equity == 0, within tolerance
      2. cash is at or above the minimum

    The first is the one that matters. Because cash is computed last rather than
    plugged, a non-zero gap means a real modelling error -- a line that was projected
    on the balance sheet but never routed through cash flow, or the reverse.
    """
    failures = []

    for year in projection:
        if abs(year["balance_gap"]) > BALANCE_TOLERANCE:
            failures.append(
                f"{year['label']}: balance sheet does not balance. "
                f"Assets - liabilities - equity = {year['balance_gap']:,.1f}"
            )
        if year["cash"] < MINIMUM_CASH - BALANCE_TOLERANCE:
            failures.append(
                f"{year['label']}: cash of {year['cash']:,.1f} is below the "
                f"minimum of {MINIMUM_CASH:,.1f}"
            )

    if failures:
        raise ValueError(
            "Pro-forma checks failed -- refusing to value these statements.\n  "
            + "\n  ".join(failures)
        )


# ---------------------------------------------------------------------------
# VALUATION
# ---------------------------------------------------------------------------
def value_equity(projection):
    """Discount the five FCFE plus a terminal value at the cost of equity."""
    pv_explicit = 0.0
    for index, year in enumerate(projection, start=1):
        pv_explicit += year["fcfe"] / (1 + COST_OF_EQUITY) ** index

    # The final year's debt repayment is added back before capitalising, because a
    # scheduled paydown is not a perpetual claim on cash -- the debt eventually runs
    # out. Capitalising FCFE net of repayment would assume the company pays down debt
    # forever, which would understate the terminal value.
    final = projection[-1]
    terminal_base = final["fcfe"] + final["repayment"]
    terminal_value = (
        terminal_base * (1 + TERMINAL_GROWTH) / (COST_OF_EQUITY - TERMINAL_GROWTH)
    )
    pv_terminal = terminal_value / (1 + COST_OF_EQUITY) ** YEARS

    equity_value = pv_explicit + pv_terminal

    return {
        "pv_explicit": pv_explicit,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "equity_value": equity_value,
        "terminal_share": pv_terminal / equity_value,
        "value_per_share": equity_value / SHARES_OUTSTANDING,
    }


# ---------------------------------------------------------------------------
# INTERFACE -- display only, no finance computed below this line
# ---------------------------------------------------------------------------
def _table(title, rows, projection):
    """Print one statement, years across, one decimal."""
    labels = [year["label"] for year in projection]
    width = 14

    print(f"\n{title}")
    print("-" * (26 + width * len(labels)))
    print(f"{'':26}" + "".join(f"{label:>{width}}" for label in labels))

    for caption, key in rows:
        if caption.startswith("--"):
            print()
            continue
        cells = "".join(f"{year[key]:>{width},.1f}" for year in projection)
        print(f"{caption:26}" + cells)


def print_statements(projection):
    _table(
        "INCOME STATEMENT (USD millions)",
        [
            ("Revenue", "revenue"),
            ("Gross profit", "gross_profit"),
            ("SG&A", "sga"),
            ("Depreciation", "depreciation"),
            ("Impairment", "impairment"),
            ("Operating income", "operating_income"),
            ("Interest", "interest"),
            ("Pretax income", "pretax_income"),
            ("Tax", "tax"),
            ("Net income", "net_income"),
        ],
        projection,
    )

    _table(
        "BALANCE SHEET (USD millions)",
        [
            ("Cash", "cash"),
            ("Inventory", "inventory"),
            ("PP&E", "ppe"),
            ("Other assets", "other_assets"),
            ("Total assets", "total_assets"),
            ("--", None),
            ("Floor plan", "floor_plan"),
            ("Revolver", "revolver"),
            ("Term debt", "debt"),
            ("Other liabilities", "other_liabilities"),
            ("Total liabilities", "total_liabilities"),
            ("Equity", "equity"),
        ],
        projection,
    )

    _table(
        "CASH FLOW TO EQUITY (USD millions)",
        [
            ("Net income", "net_income"),
            ("Depreciation", "depreciation"),
            ("Impairment", "impairment"),
            ("Capital spending", "capex_display"),
            ("Change in inventory", "inventory_change"),
            ("Change in other WC", "other_working_capital_change"),
            ("Change in floor plan", "floor_plan_change"),
            ("Debt repayment", "repayment"),
            ("Free cash flow to equity", "fcfe"),
            ("--", None),
            ("Share buyback", "buyback"),
            ("Cash, year end", "cash"),
        ],
        projection,
    )


def print_checks(projection):
    print("\nCHECKS")
    print("-" * 66)
    print(f"{'Year':10}{'Assets - liab - equity':>26}{'Cash':>14}{'Above min':>14}")
    for year in projection:
        above = "yes" if year["cash"] >= MINIMUM_CASH else "NO"
        print(
            f"{year['label']:10}{year['balance_gap']:>26,.1f}"
            f"{year['cash']:>14,.1f}{above:>14}"
        )


def print_valuation(valuation):
    print("\nEQUITY VALUATION (FCFE discounted at the cost of equity)")
    print("-" * 66)
    print(f"{'PV of five years of FCFE':40}{valuation['pv_explicit']:>16,.1f}")
    print(f"{'Terminal value at 2030':40}{valuation['terminal_value']:>16,.1f}")
    print(f"{'PV of terminal value':40}{valuation['pv_terminal']:>16,.1f}")
    print(f"{'Equity value':40}{valuation['equity_value']:>16,.1f}")
    print(f"{'Share of value after 2030':40}{valuation['terminal_share']:>15.1%}")
    print(f"{'Shares outstanding (millions)':40}{SHARES_OUTSTANDING:>16,.6f}")
    print(f"{'Value per share':40}{valuation['value_per_share']:>16,.2f}")


def main():
    print("=" * 66)
    print(f"FIVE-YEAR PRO-FORMA -- {COMPANY}")
    print("=" * 66)

    projection = build_projection()

    # Capital spending is a constant, so it is not stored per year by the engine.
    # Attach it here purely so the cash-flow table can display it.
    for year in projection:
        year["capex_display"] = CAPEX

    print_statements(projection)
    print_checks(projection)

    # The refusal. Nothing below this line runs if a year fails.
    try:
        assert_balanced(projection)
    except ValueError as error:
        print(f"\n{error}", file=sys.stderr)
        raise SystemExit(1)

    print("\nAll checks passed -- statements are internally consistent.")

    print_valuation(value_equity(projection))


if __name__ == "__main__":
    main()
