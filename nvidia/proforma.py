"""Five-year three-statement pro-forma with an equity (FCFE) valuation -- NVIDIA Corporation.

FIN 43900 (AI in Finance, Purdue), Lab 10 -- Session 10.
Author: Drew Scheiderer.

The question this answers: what are five years of NVIDIA's statements worth, built
from assumptions I can defend?

This is a sibling of the root `proforma.py`, not an import of it. The root file carries
the Asbury Automotive Group training case and reproduces its published $291.75, and
Lab 10 begins by rerunning it unchanged. It is not edited here. A sibling was the right
call rather than an import because NVIDIA's income statement has a different SHAPE, not
just different numbers:

  - research and development is NVIDIA's largest operating expense (18,497 against SG&A
    of 4,579 in FY2026). ABG's engine has no R&D line at all, and folding R&D into SG&A
    would hide the single biggest cost decision in the model.
  - ABG's floor plan does not exist here. Its replacement is named below.
  - NVIDIA earns more interest than it pays. ABG's engine has no interest income line.
  - stock-based compensation is a material non-cash expense (6,386) that ABG does not
    separately model.

Three ideas carry this file. The first two are inherited from Lab 09; the third is new
and is where NVIDIA breaks the ABG template.

1. CASH IS COMPUTED LAST. Every other line is projected from an assumption. Cash is
   whatever is left once the business has earned, invested, borrowed and paid. That
   ordering is what makes the balance check meaningful: a plugged cash line could never
   fail and would prove nothing.

2. A BALANCE SHEET THAT DOES NOT BALANCE IS A BUG, NOT A FORECAST. assert_balanced()
   raises before any valuation runs.

3. STOCK-BASED COMPENSATION HAS TO BE BOOKED TWICE OR THE SHEET WILL NOT BALANCE. SBC is
   added back in the cash flow because it moved no cash, AND credited to equity because
   it is paid in shares. Do only the first and the balance check fails by exactly the
   SBC amount every year. This is the error the check block is best at catching, and it
   is the reason the check earns its place.

Standard library only. Every figure below is traced to a filing in the write-up,
NVIDIA_2026-09-24_lab10.md.

Run with:            python proforma.py
Prove it refuses:    python proforma.py --prove-refusal
"""

import sys

# ---------------------------------------------------------------------------
# INPUTS -- the only block intended to be edited
# ---------------------------------------------------------------------------
# Each assumption carries a LABEL, and every judgment carries a reason:
#   history   -- computed from the filings, written as the arithmetic that makes it
#   guidance  -- the company said so
#   judgment  -- I chose it, and I own it
#   fact      -- a reported figure
#
# All money is USD millions. Fiscal years end in late January; FY2026 ended
# January 25, 2026, so the projection runs FY2027E through FY2031E.

COMPANY = "NVIDIA Corporation (NVDA)"
FIRST_YEAR = 2027
YEARS = 5

# --- Opening balance sheet, FY2026 actual (fact: 10-K, period end Jan 25, 2026) ----
# Two mappings from the filed sheet into the engine's buckets, both deliberate:
#
#   cash  = cash and equivalents 10,605 + marketable securities 51,951 = 62,556.
#           NVIDIA runs its treasury as one liquid portfolio and reports interest
#           income on the whole of it, so splitting them would put the earning
#           asset in one bucket and the earnings in another. This is the same
#           62,556 carried as non-operating cash in the Lab 06 DCF.
#
#   other_assets = everything else: receivables, goodwill, intangibles, deferred
#           tax assets, non-marketable equity securities, operating lease assets,
#           prepaids. It is a plug by construction, and the opening check below
#           proves it reconciles to the filed total of 206,803.
OPENING = {
    "revenue": 215_938.0,        # FY2026 revenue, the base the projection grows from
    "inventory": 21_403.0,
    "ppe": 10_383.0,             # property and equipment, net
    "other_assets": 112_461.0,   # 206,803 total assets - 62,556 - 21,403 - 10,383
    "cash": 62_556.0,            # 10,605 equivalents + 51,951 marketable securities
    "supply_obligations": 2_739.0,   # THE NAMED LINE -- see below
    "debt": 8_468.0,             # short-term 999 + long-term 7,469
    "other_liabilities": 38_303.0,   # 49,510 total liabilities - 8,468 - 2,739
    "equity": 157_293.0,
    "revolver": 0.0,
}

# Filed totals, carried so the opening sheet can be checked rather than trusted.
FILED_TOTAL_ASSETS = 206_803.0
FILED_TOTAL_LIABILITIES = 49_510.0

# --- THE LINE THAT MAKES NVIDIA DIFFERENT -----------------------------------------
# ABG's floor plan is a lender financing the inventory on the lot: inventory rises,
# the loan rises with it, and cash is unharmed. NVIDIA has no floor plan. Its
# structural analogue is EXCESS INVENTORY PURCHASE OBLIGATIONS -- 2,739 at FY2026
# against 2,095 at FY2025, inside accrued and other current liabilities.
#
# It is the mirror image of floor plan, and that is the whole point. NVIDIA owns no
# fabs, so it must commit to foundry and memory capacity years before it knows what
# it can sell. When it commits to more than it can sell, the loss is accrued here.
#
#   floor plan  -- a liability that makes inventory CHEAPER to hold
#   this line   -- a liability that measures inventory NVIDIA WISHES IT HAD NOT ORDERED
#
# Mechanically the two behave alike: both scale with inventory, and an increase in
# either adds back to cash because the expense was accrued and not paid. So it is
# modelled exactly the way floor plan was -- as a ratio to inventory, with the change
# routed through FCFE. Economically they point in opposite directions, which is the
# sentence I would defend: for a dealer, financed inventory is a sign the model is
# working; for a fabless designer, a growing over-commitment accrual is a warning.
SUPPLY_OBLIGATIONS_TO_INVENTORY = 2_739.0 / 21_403.0        # history: FY2026

# --- Income statement assumptions --------------------------------------------------
# judgment: the same five-year path as my Lab 06 DCF, deliberately unchanged. The two
# models should differ in what they MODEL -- free cash flow to the firm against a full
# set of statements -- not in what I believe about the business. If I moved growth here
# I could not tell whether a difference in value came from the method or from me.
# The path decays toward the 3% terminal rate rather than stepping down to it.
REVENUE_GROWTH = [0.30, 0.22, 0.16, 0.11, 0.07]              # FY2027E -> FY2031E

# judgment: FY2026 came in at 71.07% (153,463 / 215,938), against 74.99% in FY2025.
# It is already falling. Two reasons to keep it falling, gently: revenue is shifting
# from discrete GPUs toward full rack-scale systems, which carry more bought-in
# content per dollar of revenue; and AMD plus hyperscaler custom silicon give buyers
# a credible second source for the first time. A four-point fade over five years is
# slower than the last twelve months delivered, so this is not a bearish line.
GROSS_MARGIN = [0.710, 0.705, 0.700, 0.695, 0.690]

# judgment, and the least obvious line in the table. R&D was 8.57% of revenue in FY2026
# (18,497 / 215,938), down from 14.24% in FY2024 -- it did not fall because NVIDIA spent
# less, it fell because revenue tripled underneath it. Run that backwards: as growth
# decelerates from 30% to 7%, a research budget committed years ahead cannot decelerate
# with it, so the RATIO climbs even while the dollars keep rising. Holding 8.57% flat
# would quietly assume NVIDIA can throttle its roadmap to match its revenue. It cannot.
RD_TO_REVENUE = [0.085, 0.090, 0.095, 0.100, 0.105]

# judgment: 2.98% in FY2026 (4,579 / 153,463), down from 5.99% in FY2024. The operating
# leverage in this line has already been harvested; assuming more of it is the cheapest
# way to manufacture earnings, so it is held flat at 3.0%.
SGA_TO_GROSS_PROFIT = [0.030, 0.030, 0.030, 0.030, 0.030]

# history: FY2026 stock-based compensation / FY2026 revenue. Non-cash, so it is added
# back in FCFE -- and credited to equity, per idea 3 in the docstring.
SBC_TO_REVENUE = 6_386.0 / 215_938.0

# history: FY2026 depreciation and amortization / FY2026 OPENING PP&E. Charged on the
# opening balance because assets bought during the year were not in service all year.
DEPRECIATION_TO_OPENING_PPE = 2_843.0 / 6_283.0

# history: FY2026 purchases of property, equipment and intangibles / FY2026 revenue.
# ABG's capital spending is a constant because a dealer's store count barely moves.
# NVIDIA's tripled in two years alongside revenue, so a constant would be wrong by
# more than the line is worth. It is scaled to revenue instead.
CAPEX_TO_REVENUE = 6_042.0 / 215_938.0

# judgment: the effective rate ran 12.00%, 13.27%, 15.12% across FY2024-FY2026 -- a
# steady climb as the global minimum tax phases in and foreign income loses its
# advantage. 16% continues that drift by about one point and then holds.
TAX_RATE = 0.16

# --- Balance sheet assumptions ------------------------------------------------------
# history: FY2026 inventory / FY2026 cost of revenue, expressed in days. 125 days is
# long for a technology company and is a direct consequence of the same fabless
# structure that produces the supply-obligation line above.
INVENTORY_DAYS = 21_403.0 / 62_475.0 * 365

# history: the change in non-inventory working capital over the change in revenue,
# FY2025 -> FY2026. Receivables plus prepaids, less payables and less accrued
# liabilities EXCLUDING the supply obligations, which are modelled separately just
# above and must not be counted twice:
#   FY2026  38,466 + 3,180 - 9,812 - (21,352 - 2,739) = 13,221
#   FY2025  23,065 + 3,771 - 6,310 - (11,737 - 2,095) = 10,884
#   change 2,337 over revenue change of 85,441
OTHER_WC_TO_REVENUE_CHANGE = (
    (38_466.0 + 3_180.0 - 9_812.0 - (21_352.0 - 2_739.0))
    - (23_065.0 + 3_771.0 - 6_310.0 - (11_737.0 - 2_095.0))
) / (215_938.0 - 130_497.0)

# --- Financing assumptions -----------------------------------------------------------
# judgment: roughly the cash and equivalents NVIDIA actually operated on at FY2026 year
# end (10,605), excluding the securities portfolio. The floor is never expected to bind
# here; it is kept so the check has something it CAN fail.
MINIMUM_CASH = 10_000.0
REVOLVER_LIMIT = 10_000.0     # judgment: a modelling device, not a disclosed facility
REVOLVER_RATE = 0.06          # judgment

# history: FY2026 interest income / average of opening and closing cash-plus-securities.
#   2,300 / ((8,589 + 34,621 + 10,605 + 51,951) / 2)
# The average balance is used rather than the opening balance because the portfolio grew
# by nearly half during the year; dividing by the opening balance alone would report a
# yield of 5.32% that the portfolio never actually earned.
CASH_YIELD = 2_300.0 / ((8_589.0 + 34_621.0 + 10_605.0 + 51_951.0) / 2.0)

# history: FY2026 interest expense / FY2026 opening total debt (8,463, all long-term).
DEBT_RATE = 259.0 / 8_463.0

# judgment: NVIDIA repaid 1,250 in each of FY2024 and FY2025 and nothing in FY2026, and
# holds 999 of short-term debt due inside a year. 1,000 a year lets the stack run off
# without refinancing, which is what a company with 62,556 of liquidity would do.
DEBT_REPAYMENT = 1_000.0

# judgment: FY2026 repurchases were 40,086 and FY2025 were 33,706, under a standing board
# authorization. Held flat at 40,000.
#
# NOTE, and it matters more here than it did for ABG: this reduces cash and equity but
# does NOT retire shares in this model. That is not laziness, it is what the filings
# show. NVIDIA repurchased 40,086 of stock in FY2026 and its shares outstanding fell
# from 24,477 to 24,304 -- seven tenths of one percent -- because stock-based
# compensation issued shares back almost as fast as the buyback retired them. Modelling
# the buyback as shrinking the share count would credit NVIDIA with a per-share tailwind
# the evidence says it did not get.
SHARE_BUYBACK = 40_000.0
DIVIDENDS = 1_000.0           # judgment: FY2026 paid 974, held flat

# judgment, and the correction that matters most in this file. NVIDIA opens with 62,556
# of cash and securities and the treasury is held flat there; everything earned above it
# is returned to shareholders as a surplus distribution, computed as a residual.
#
# Why this is not optional. Discounting FCFE ASSUMES every dollar of it reaches
# shareholders in the year it is earned. My first version left the surplus on the
# balance sheet, where it compounded to 831,139 by FY2031 and threw off 27,337 of
# interest income -- income the valuation then discounted, on cash it had already
# treated as paid out. That is counting the same dollars twice, and it lifted value per
# share by about a tenth. Holding the treasury flat forces the two halves of the model
# to tell the same story.
#
# The surplus is large and NVIDIA is not in fact distributing it -- it is accumulating.
# That is a real disagreement between my model and the company's behaviour, not an
# error, and it is stated in the write-up rather than smoothed away.
TARGET_CASH = 62_556.0

# --- Valuation assumptions ------------------------------------------------------------
# judgment, carried from my own beta work in nvidia/beta.py rather than from a provider:
# CAPM at a 4.944% risk-free rate plus a 5% equity risk premium on a beta of 2.216,
# estimated over five years of monthly returns against the S&P 500. FCFE is cash to
# shareholders after lenders are served, so it discounts at the cost of EQUITY, not WACC.
COST_OF_EQUITY = 0.1603
# The Blume-adjusted beta of 1.815 from the same file implies 14.02%. That alternative is
# run as a sensitivity in the write-up rather than buried as a point estimate here.
COST_OF_EQUITY_ALTERNATIVE = 0.1402

TERMINAL_GROWTH = 0.03        # judgment: long-run nominal US economy, same as Lab 06
SHARES_OUTSTANDING = 24_514.0 # fact: diluted weighted-average shares, FY2026 EPS note.
                              # Diluted rather than the 24,304 issued and outstanding,
                              # for consistency with Labs 06 and 08 and because the SBC
                              # above will keep converting into shares.

# Market reference for the closing comparison. No recommendation is drawn from it.
MARKET_PRICE = 224.58         # fact: NVDA close, September 24, 2026
MARKET_PRICE_DATE = "September 24, 2026"

BALANCE_TOLERANCE = 0.05      # USD millions


# ---------------------------------------------------------------------------
# ANALYSIS -- the projection engine
# ---------------------------------------------------------------------------
def project_year(opening, growth, gross_margin, rd_ratio, sga_ratio):
    """Project one year forward from an opening balance sheet.

    The ORDER below is the whole design: income statement, then every balance sheet
    line EXCEPT cash, then free cash flow to equity, and only then cash.
    """
    year = {}

    # --- Income statement ---------------------------------------------------
    revenue = opening["revenue"] * (1 + growth)
    gross_profit = revenue * gross_margin
    research_development = revenue * rd_ratio
    sga = gross_profit * sga_ratio

    # Charged on the PP&E the company OPENED the year with.
    depreciation = opening["ppe"] * DEPRECIATION_TO_OPENING_PPE

    operating_income = gross_profit - research_development - sga - depreciation

    # Interest on OPENING balances, both directions. NVIDIA earns far more than it
    # pays; leaving interest income out would understate pretax income by about 2,700
    # in the first year alone.
    interest_expense = (
        opening["debt"] * DEBT_RATE + opening["revolver"] * REVOLVER_RATE
    )
    interest_income = opening["cash"] * CASH_YIELD
    net_interest = interest_income - interest_expense

    # Deliberately excluded: "other income, net" of 9,022 in FY2026, of which 8,918 was
    # gains on non-marketable and publicly-held equity securities. Those are unrealized
    # marks on strategic stakes, they are backed out of operating cash flow in the
    # filing itself, and forecasting them would be forecasting the stock market.
    pretax_income = operating_income + net_interest
    tax = max(0.0, pretax_income) * TAX_RATE     # a loss books no refund here
    net_income = pretax_income - tax

    # Non-cash, and it has to appear in two places. See idea 3 in the docstring.
    stock_compensation = revenue * SBC_TO_REVENUE

    # --- Balance sheet, every line EXCEPT cash ------------------------------
    cost_of_revenue = revenue - gross_profit
    inventory = cost_of_revenue * INVENTORY_DAYS / 365

    # The named line, modelled exactly as ABG's floor plan was: it tracks inventory.
    supply_obligations = inventory * SUPPLY_OBLIGATIONS_TO_INVENTORY

    capex = revenue * CAPEX_TO_REVENUE
    ppe = opening["ppe"] + capex - depreciation

    revenue_change = revenue - opening["revenue"]
    other_working_capital_change = OTHER_WC_TO_REVENUE_CHANGE * revenue_change
    other_assets = opening["other_assets"] + other_working_capital_change

    debt = opening["debt"] - DEBT_REPAYMENT
    other_liabilities = opening["other_liabilities"]

    # --- Free cash flow to equity -------------------------------------------
    # Cash to shareholders after lenders are served, so it is discounted at the cost
    # of equity and values the equity directly -- no enterprise-to-equity bridge.
    inventory_change = inventory - opening["inventory"]
    supply_obligations_change = supply_obligations - opening["supply_obligations"]

    fcfe = (
        net_income
        + depreciation
        + stock_compensation
        - capex
        - inventory_change
        - other_working_capital_change
        + supply_obligations_change
        - DEBT_REPAYMENT
    )

    # --- Cash, computed LAST, and the revolver ------------------------------
    # Anything left above the target treasury is returned to shareholders, so the
    # valuation's assumption and the balance sheet agree. If FCFE falls short of the
    # declared buyback and dividend, the surplus is zero and cash is drawn down
    # instead -- which is when the minimum-cash floor and the revolver below matter.
    cash_available = opening["cash"] + fcfe - SHARE_BUYBACK - DIVIDENDS
    surplus_distribution = max(0.0, cash_available - TARGET_CASH)

    # Stock compensation is ADDED to equity because it is paid in shares. Drop this
    # term and the balance check fails by exactly `stock_compensation` every year.
    equity = (
        opening["equity"] + net_income + stock_compensation
        - SHARE_BUYBACK - DIVIDENDS - surplus_distribution
    )

    cash_before_revolver = cash_available - surplus_distribution
    revolver = opening["revolver"]

    if cash_before_revolver < MINIMUM_CASH:
        shortfall = MINIMUM_CASH - cash_before_revolver
        draw = min(shortfall, REVOLVER_LIMIT - revolver)
        revolver += draw
        cash = cash_before_revolver + draw
    elif revolver > 0 and cash_before_revolver > MINIMUM_CASH:
        repayment = min(revolver, cash_before_revolver - MINIMUM_CASH)
        revolver -= repayment
        cash = cash_before_revolver - repayment
    else:
        cash = cash_before_revolver

    year.update(
        revenue=revenue,
        gross_profit=gross_profit,
        research_development=research_development,
        sga=sga,
        depreciation=depreciation,
        operating_income=operating_income,
        interest_income=interest_income,
        interest_expense=interest_expense,
        net_interest=net_interest,
        pretax_income=pretax_income,
        tax=tax,
        net_income=net_income,
        stock_compensation=stock_compensation,
        inventory=inventory,
        ppe=ppe,
        other_assets=other_assets,
        cash=cash,
        supply_obligations=supply_obligations,
        debt=debt,
        other_liabilities=other_liabilities,
        equity=equity,
        revolver=revolver,
        capex=capex,
        inventory_change=inventory_change,
        other_working_capital_change=other_working_capital_change,
        supply_obligations_change=supply_obligations_change,
        fcfe=fcfe,
        repayment=DEBT_REPAYMENT,
        buyback=SHARE_BUYBACK,
        dividends=DIVIDENDS,
        surplus_distribution=surplus_distribution,
        total_distribution=SHARE_BUYBACK + DIVIDENDS + surplus_distribution,
    )

    year["total_assets"] = (
        year["cash"] + year["inventory"] + year["ppe"] + year["other_assets"]
    )
    year["total_liabilities"] = (
        year["supply_obligations"] + year["debt"]
        + year["other_liabilities"] + year["revolver"]
    )
    year["balance_gap"] = (
        year["total_assets"] - year["total_liabilities"] - year["equity"]
    )

    return year


def build_projection(opening=None):
    """Project YEARS years forward. Returns a list of year dicts, FY2027E first."""
    state = dict(opening or OPENING)
    projection = []

    for index in range(YEARS):
        year = project_year(
            state,
            REVENUE_GROWTH[index],
            GROSS_MARGIN[index],
            RD_TO_REVENUE[index],
            SGA_TO_GROSS_PROFIT[index],
        )
        year["label"] = f"FY{FIRST_YEAR + index}E"
        projection.append(year)

        # This year's closing position becomes next year's opening position.
        state = {
            key: year[key]
            for key in (
                "revenue", "inventory", "ppe", "other_assets", "cash",
                "supply_obligations", "debt", "other_liabilities",
                "equity", "revolver",
            )
        }

    return projection


# ---------------------------------------------------------------------------
# THE CHECKS -- these stop the model
# ---------------------------------------------------------------------------
def check_opening_balance():
    """Prove the opening sheet reconciles to the FILED totals before projecting.

    Two of the opening lines -- other_assets and other_liabilities -- were derived by
    subtraction, so they cannot disagree with the engine. They CAN disagree with the
    10-K, and that is the error this catches: a mistyped figure anywhere in the
    mapping shows up here rather than silently propagating through five years.
    """
    assets = (
        OPENING["cash"] + OPENING["inventory"]
        + OPENING["ppe"] + OPENING["other_assets"]
    )
    liabilities = (
        OPENING["supply_obligations"] + OPENING["debt"]
        + OPENING["other_liabilities"] + OPENING["revolver"]
    )
    failures = []
    if abs(assets - FILED_TOTAL_ASSETS) > BALANCE_TOLERANCE:
        failures.append(
            f"opening assets of {assets:,.1f} do not match the filed "
            f"{FILED_TOTAL_ASSETS:,.1f}"
        )
    if abs(liabilities - FILED_TOTAL_LIABILITIES) > BALANCE_TOLERANCE:
        failures.append(
            f"opening liabilities of {liabilities:,.1f} do not match the filed "
            f"{FILED_TOTAL_LIABILITIES:,.1f}"
        )
    gap = assets - liabilities - OPENING["equity"]
    if abs(gap) > BALANCE_TOLERANCE:
        failures.append(f"opening sheet does not balance: gap of {gap:,.1f}")

    if failures:
        raise ValueError(
            "Opening balance sheet failed its checks -- refusing to project.\n  "
            + "\n  ".join(failures)
        )
    return assets, liabilities, gap


def assert_balanced(projection):
    """Raise if any year fails a check. Called BEFORE any valuation runs.

    Because cash is computed last rather than plugged, a non-zero gap means a real
    modelling error -- a line projected on the balance sheet but never routed through
    cash flow, or the reverse.
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
def value_equity(projection, cost_of_equity=COST_OF_EQUITY):
    """Discount the five FCFE plus a terminal value at the cost of equity."""
    if TERMINAL_GROWTH >= cost_of_equity:
        raise ValueError(
            f"Terminal growth ({TERMINAL_GROWTH:.4f}) must be below the cost of "
            f"equity ({cost_of_equity:.4f}); the Gordon formula is undefined otherwise."
        )

    pv_explicit = 0.0
    for index, year in enumerate(projection, start=1):
        pv_explicit += year["fcfe"] / (1 + cost_of_equity) ** index

    # The final year's debt repayment is added back before capitalising: a scheduled
    # paydown is not a perpetual claim on cash, because the debt eventually runs out.
    final = projection[-1]
    terminal_base = final["fcfe"] + final["repayment"]
    terminal_value = (
        terminal_base * (1 + TERMINAL_GROWTH) / (cost_of_equity - TERMINAL_GROWTH)
    )
    pv_terminal = terminal_value / (1 + cost_of_equity) ** YEARS
    equity_value = pv_explicit + pv_terminal

    return {
        "cost_of_equity": cost_of_equity,
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
    labels = [year["label"] for year in projection]
    width = 14

    print(f"\n{title}")
    print("-" * (30 + width * len(labels)))
    print(f"{'':30}" + "".join(f"{label:>{width}}" for label in labels))

    for caption, key in rows:
        if caption.startswith("--"):
            print()
            continue
        cells = "".join(f"{year[key]:>{width},.0f}" for year in projection)
        print(f"{caption:30}" + cells)


def print_statements(projection):
    _table(
        "INCOME STATEMENT (USD millions)",
        [
            ("Revenue", "revenue"),
            ("Gross profit", "gross_profit"),
            ("Research and development", "research_development"),
            ("SG&A", "sga"),
            ("Depreciation and amortization", "depreciation"),
            ("Operating income", "operating_income"),
            ("Interest income", "interest_income"),
            ("Interest expense", "interest_expense"),
            ("Pretax income", "pretax_income"),
            ("Tax", "tax"),
            ("Net income", "net_income"),
        ],
        projection,
    )

    _table(
        "BALANCE SHEET (USD millions)",
        [
            ("Cash and securities", "cash"),
            ("Inventory", "inventory"),
            ("PP&E, net", "ppe"),
            ("Other assets", "other_assets"),
            ("Total assets", "total_assets"),
            ("--", None),
            ("Supply obligations", "supply_obligations"),
            ("Revolver", "revolver"),
            ("Debt", "debt"),
            ("Other liabilities", "other_liabilities"),
            ("Total liabilities", "total_liabilities"),
            ("Shareholders' equity", "equity"),
        ],
        projection,
    )

    _table(
        "CASH FLOW TO EQUITY (USD millions)",
        [
            ("Net income", "net_income"),
            ("Depreciation and amortization", "depreciation"),
            ("Stock-based compensation", "stock_compensation"),
            ("Capital spending", "capex"),
            ("Change in inventory", "inventory_change"),
            ("Change in other WC", "other_working_capital_change"),
            ("Change in supply obligations", "supply_obligations_change"),
            ("Debt repayment", "repayment"),
            ("Free cash flow to equity", "fcfe"),
            ("--", None),
            ("Share buyback", "buyback"),
            ("Dividends", "dividends"),
            ("Surplus distribution", "surplus_distribution"),
            ("Total returned to holders", "total_distribution"),
            ("Cash, year end", "cash"),
        ],
        projection,
    )


def print_opening_check(assets, liabilities, gap):
    print("\nOPENING BALANCE SHEET (FY2026 actual, 10-K period end Jan 25, 2026)")
    print("-" * 74)
    print(f"{'Assets, mapped into the engine':46}{assets:>14,.1f}")
    print(f"{'Assets, as filed':46}{FILED_TOTAL_ASSETS:>14,.1f}")
    print(f"{'Liabilities, mapped into the engine':46}{liabilities:>14,.1f}")
    print(f"{'Liabilities, as filed':46}{FILED_TOTAL_LIABILITIES:>14,.1f}")
    print(f"{'Assets - liabilities - equity':46}{gap:>14,.1f}")


def print_checks(projection):
    print("\nCHECKS")
    print("-" * 74)
    print(f"{'Year':12}{'Assets - liab - equity':>26}{'Cash':>18}{'Above min':>14}")
    for year in projection:
        above = "yes" if year["cash"] >= MINIMUM_CASH else "NO"
        print(
            f"{year['label']:12}{year['balance_gap']:>26,.1f}"
            f"{year['cash']:>18,.1f}{above:>14}"
        )


def print_valuation(valuation):
    print("\nEQUITY VALUATION (FCFE discounted at the cost of equity)")
    print("-" * 74)
    print(f"{'Cost of equity':46}{valuation['cost_of_equity']:>13.2%}")
    print(f"{'Terminal growth':46}{TERMINAL_GROWTH:>13.2%}")
    print(f"{'PV of five years of FCFE':46}{valuation['pv_explicit']:>14,.0f}")
    print(f"{'Terminal value at FY2031':46}{valuation['terminal_value']:>14,.0f}")
    print(f"{'PV of terminal value':46}{valuation['pv_terminal']:>14,.0f}")
    print(f"{'Equity value':46}{valuation['equity_value']:>14,.0f}")
    print(f"{'Share of value after FY2031':46}{valuation['terminal_share']:>13.1%}")
    print(f"{'Diluted shares (millions)':46}{SHARES_OUTSTANDING:>14,.0f}")
    print(f"{'Value per share':46}{valuation['value_per_share']:>14,.2f}")


def print_market_comparison(projection):
    """The model against the market, on the same share count. A question, not a call."""
    base = value_equity(projection, COST_OF_EQUITY)
    alternative = value_equity(projection, COST_OF_EQUITY_ALTERNATIVE)
    low, high = sorted(
        [base["value_per_share"], alternative["value_per_share"]]
    )

    print("\nTHE MODEL AGAINST THE MARKET")
    print("-" * 74)
    print(
        f"  At a {COST_OF_EQUITY:.2%} cost of equity (beta 2.216, my own estimate), "
        f"this model says {base['value_per_share']:,.2f}."
    )
    print(
        f"  At {COST_OF_EQUITY_ALTERNATIVE:.2%} (Blume-adjusted beta 1.815), it says "
        f"{alternative['value_per_share']:,.2f}."
    )
    print(
        f"  The market says {MARKET_PRICE:,.2f} on {MARKET_PRICE_DATE}, on the same "
        f"{SHARES_OUTSTANDING:,.0f} million diluted shares."
    )
    print()
    print(f"  The range {low:,.2f} to {high:,.2f} comes from one input -- beta -- and")
    print("  nothing else. The question that leaves me is not whether NVIDIA is cheap.")
    print("  It is which of us is wrong about the discount rate: the market is pricing")
    print("  NVIDIA as though its cost of equity were far below what its own five-year")
    print("  return history implies. No recommendation is drawn here.")


def prove_refusal():
    """Demonstrate that the model STOPS on a broken sheet, rather than valuing it.

    The break chosen is the realistic one: stock-based compensation added back in the
    cash flow but never credited to equity. That is idea 3 in the docstring, and the
    gap it opens is exactly the SBC amount -- which is how I know the check is reading
    the error and not merely reporting float noise.
    """
    print("=" * 74)
    print("REFUSAL DEMONSTRATION -- stock compensation dropped from equity")
    print("=" * 74)
    print("Injecting the error: equity no longer receives the SBC credit.\n")

    projection = build_projection()
    for year in projection:
        year["equity"] -= year["stock_compensation"]
        year["balance_gap"] = (
            year["total_assets"] - year["total_liabilities"] - year["equity"]
        )

    print_checks(projection)
    print()
    try:
        assert_balanced(projection)
    except ValueError as error:
        print(error, file=sys.stderr)
        first = projection[0]
        print(
            f"\nThe FY2027E gap of {first['balance_gap']:,.1f} is exactly that year's "
            f"stock-based\ncompensation of {first['stock_compensation']:,.1f}. "
            "The check found the real error.",
            file=sys.stderr,
        )
        print("\nModel refused to value these statements, as it should.", file=sys.stderr)
        return 1

    print("ERROR: the model did NOT refuse. The check is not working.", file=sys.stderr)
    return 1


def main():
    if "--prove-refusal" in sys.argv:
        return prove_refusal()

    print("=" * 74)
    print(f"FIVE-YEAR PRO-FORMA -- {COMPANY}")
    print("=" * 74)

    try:
        opening_check = check_opening_balance()
    except ValueError as error:
        print(f"\n{error}", file=sys.stderr)
        return 1
    print_opening_check(*opening_check)

    projection = build_projection()

    print_statements(projection)
    print_checks(projection)

    # The refusal. Nothing below this line runs if a year fails.
    try:
        assert_balanced(projection)
    except ValueError as error:
        print(f"\n{error}", file=sys.stderr)
        return 1

    print("\nAll checks passed -- statements are internally consistent.")

    print_valuation(value_equity(projection))
    print_market_comparison(projection)
    return 0


if __name__ == "__main__":
    sys.exit(main())
