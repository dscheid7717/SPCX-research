"""Project 1 analysis engine -- NVIDIA Corporation (NVDA).

FIN 43900 (AI in Finance, Purdue), Project 1 -- Corporate Finance Application.
Author: Drew Scheiderer.

The decision this supports: should a buy-side fund with no position INITIATE, WATCH/DEFER,
or NOT INITIATE a position in NVDA? Answered as a valuation range with conditions, never a
single confident number.

What this file adds on top of the lab engines, and what it reuses:

  - The five-year three-statement pro-forma is nvidia/proforma.py (Lab 10), imported and
    driven -- not copied. Its accounting checks (opening sheet reconciles to the 10-K, sheet
    balances every year, cash computed last) still stop the model.
  - The FCFF discounting is nvidia/dcf.py (Lab 06): present_value_explicit,
    gordon_terminal_value and discount_factor are the functions that already reproduced the
    course's twelve training answers. Here they are fed FCFF built from the PRO-FORMA'S
    operating forecast instead of a hand-grown starting cash flow.
  - New here: the Edition B driver set re-anchored to the Q2 FY2027 10-Q, a cash flow
    statement that must tie to balance-sheet cash, an FCFF-to-FCFE reconciliation, a WACC
    built from components, low/base/high cases, named what-ifs, a WACC x growth grid with
    monotonicity checks, two reverse solves, EV/EBITDA and P/E comparables under one written
    policy, and the decision rule.

Lab 10's inputs inside proforma.py are left exactly as they were -- they are the lab record.
The Project 1 inputs below are applied on top for each run and restored afterwards.

Standard library only.

Run:             python analysis.py              (prints the report)
Freeze output:   python analysis.py --freeze     (writes visible_output.json + output report)
Tests:           python -m unittest test_project -v
"""

import contextlib
import copy
import json
import pathlib
import sys

import dcf as dcf_engine
import proforma

HERE = pathlib.Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# DECISION FRAME
# ---------------------------------------------------------------------------
DECISION = (
    "Initiate, watch/defer, or do not initiate a long position in NVIDIA (NVDA) common "
    "stock, for a buy-side investment committee that holds no current position."
)
USER = "Buy-side investment committee; no current NVDA position"
HORIZON = "3-5 year holding period; five-year explicit forecast FY2027E-FY2031E plus terminal value"
AS_OF = "2026-10-14"
CURRENCY = "USD; money in USD millions, per-share values in USD"
SHARE_BASIS = "diluted: 24,514M FY2026 diluted weighted-average shares (10-K EPS note)"
EXCLUSIONS = [
    "No intra-quarter information after the Q2 FY2027 10-Q (filed 2026-08-26) enters the "
    "forecast; market prices are the 2026-10-14 close.",
    "Gains and losses on equity investments are excluded from the operating forecast; the "
    "investments themselves are carried in the bridge instead.",
    "Operating leases are treated as operating costs (lease expense sits inside operating "
    "expense), so lease liabilities are NOT deducted in the bridge.",
    "Transaction (M&A) multiples are not used: no control transaction for a company of "
    "NVIDIA's size and business exists whose control premium, synergies and date could be "
    "defended as comparable.",
]

# ---------------------------------------------------------------------------
# SOURCED FACTS -- every load-bearing number carries a source and as-of date
# ---------------------------------------------------------------------------
# NVIDIA Form 10-K, FY ended 2026-01-25, filed 2026-02-25, accession 0001045810-26-000021.
# NVIDIA Form 10-Q, quarter ended 2026-07-26, filed 2026-08-26, accession 0001045810-26-000075.
# Market data: Yahoo Finance via yfinance, daily close 2026-10-14.
TEN_K = "NVIDIA 10-K FY2026 (period 2026-01-25, filed 2026-02-25, acc. 0001045810-26-000021)"
TEN_Q = "NVIDIA 10-Q Q2 FY2027 (period 2026-07-26, filed 2026-08-26, acc. 0001045810-26-000075)"

FY2026_REVENUE = 215_938.0          # fact: 10-K income statement
FY2026_GROSS_PROFIT = 153_463.0     # fact: 10-K income statement
FY2026_INVENTORY_WRITEDOWN = 4_000.0    # fact: 10-K, XBRL InventoryWriteDown (H20-related charges)
FY2026_INVESTMENT_GAINS = 8_918.0   # fact: 10-K cash flow statement, gains on equity securities
H1_FY2027_REVENUE = 177_837.0       # fact: 10-Q, six months ended 2026-07-26
Q2_FY2027_REVENUE = 96_221.0        # fact: 10-Q, quarter ended 2026-07-26
H1_FY2027_GROSS_PROFIT = 133_299.0  # fact: 10-Q
H1_FY2027_RD = 13_375.0             # fact: 10-Q
H1_FY2027_SGA = 2_654.0             # fact: 10-Q
H1_FY2027_DIVIDENDS = 6_290.0       # fact: 10-Q cash flow statement
H1_FY2027_BUYBACKS = 39_044.0       # fact: 10-Q cash flow statement
H1_FY2027_INVESTMENT_GAINS = 23_707.0   # fact: 10-Q, gains on investments (excluded, see EXCLUSIONS)
JUL2026_DEBT = 33_366.0             # fact: 10-Q balance sheet -- debt rose after the base year

MARKET = {
    "price": 221.30,                # fact: NVDA close 2026-10-14
    "price_date": "2026-10-14",
    "price_source": "Yahoo Finance via yfinance, daily close",
    "risk_free": 0.05190,           # fact: 10-year US Treasury yield (^TNX) close 2026-10-14
}

# Bridge items, all from the same FY2026 10-K balance sheet the pro-forma opens on.
BRIDGE = {
    "cash_and_marketable_securities": 62_556.0,  # 10,605 cash + 51,951 marketable securities
    "non_marketable_equity_securities": 22_251.0,  # balance sheet row 27, carrying value
    "debt": 8_468.0,                # 999 short-term + 7,469 long-term, carrying amount
    "diluted_shares": 24_514.0,     # millions, diluted weighted average, EPS note
}

# ---------------------------------------------------------------------------
# PROJECT 1 BASE INPUTS (Edition B) -- the only block intended to be edited
# ---------------------------------------------------------------------------
# FY2027E revenue = six months already reported + the second half at the Q2 run rate, with no
# further sequential growth assumed. That is a judgment, and it is deliberately the cautious
# reading of the 10-Q: Q2 was up 18% on Q1.
FY2027E_REVENUE = H1_FY2027_REVENUE + 2 * Q2_FY2027_REVENUE
FY2027E_GROWTH = FY2027E_REVENUE / FY2026_REVENUE - 1          # = 71.47%

BASE_INPUTS = {
    # --- operating drivers (fed to the pro-forma) ---
    "revenue_growth": [FY2027E_GROWTH, 0.22, 0.16, 0.11, 0.07],
    "gross_margin": [0.750, 0.735, 0.720, 0.705, 0.690],
    "rd_to_revenue": [0.075, 0.085, 0.095, 0.100, 0.105],
    "sga_to_gross_profit": [0.020, 0.025, 0.030, 0.030, 0.030],
    "tax_rate": 0.16,
    "capex_to_revenue": proforma.CAPEX_TO_REVENUE,
    "buyback": 78_000.0,            # H1 FY2027 39,044 annualised
    "dividends": 12_600.0,          # H1 FY2027 6,290 annualised
    # --- discount rate ---
    "risk_free": MARKET["risk_free"],
    "beta": 2.216,                  # own estimate, 5y monthly vs S&P 500, nvidia/beta.py
    "equity_risk_premium": 0.05,    # course convention
    "pre_tax_cost_of_debt": 0.0292, # principal-weighted note rates, 10-K Note 11 (Lab 06)
    "terminal_growth": 0.03,        # long-run nominal US growth; must stay below WACC
    # --- market ---
    "price": MARKET["price"],
    # --- treatment switches ---
    "sbc_as_cash_cost": False,      # True: do not add stock compensation back in FCFF
    "inject_fault": None,           # None | "drop_sbc_equity_credit" | "opening_mapping_error"
}

BLUME_BETA = 1.815                  # nvidia/beta.py: raw 2.216 shrunk one third toward 1.0

# Load-bearing driver record: value . basis . challenge . evidence that would change it.
# This is the assumption-challenge record; docs/validation-and-ai-use.md renders it.
DRIVER_RECORD = [
    {
        "driver": "FY2027E revenue growth",
        "value": "71.5% (FY2027E revenue 370,279)",
        "label": "judgment anchored on fact",
        "basis": "H1 FY2027 reported 177,837 (10-Q) + H2 at the Q2 run rate 96,221 x 2; no "
                 "further sequential growth assumed.",
        "challenge": "Lab 10 used 30%. The 10-Q filed 2026-08-26 already showed H1 up 95.8% "
                     "year over year, so 30% would require H2 revenue to FALL to 102,882 -- "
                     "below the Q2 quarter alone doubled.",
        "would_change_it": "Q3 FY2027 10-Q revenue below 90,000 (sequential decline) lowers "
                           "it; above 105,000 means the flat run rate is too cautious.",
        "challenger": "own analysis (10-Q review, Project 1)",
    },
    {
        "driver": "Revenue growth FY2028E-FY2031E",
        "value": "22% / 16% / 11% / 7%",
        "label": "judgment",
        "basis": "Lab 06/10 decay path kept unchanged so only the year the evidence "
                 "contradicted moves; fades toward the 3% terminal rate.",
        "challenge": "Colin (Lab 11): could the driver ranking just reflect the ranges "
                     "chosen? Conceded in part -- growth's lead over margin is range-"
                     "dependent; equal +/-2pp is not equal economic uncertainty.",
        "would_change_it": "Hyperscaler capex guidance for calendar 2027 flat or down; "
                           "Compute & Networking growth below 20% in any two consecutive "
                           "quarters year over year.",
        "challenger": "Colin (Lab 11 partner exchange, 2026-09-29)",
    },
    {
        "driver": "Gross margin path",
        "value": "75.0% -> 69.0% (fading 1.5pp a year)",
        "label": "judgment re-anchored on fact",
        "basis": "Start at H1 FY2027 reported 74.96%. End point 69% unchanged from Lab 10: "
                 "rack-scale systems carry more bought-in content and custom silicon gives "
                 "buyers a second source.",
        "challenge": "FY2026 reported 71.07% was depressed by a 4,000 inventory write-down; "
                     "normalised it is 72.92%. Starting from the reported figure would have "
                     "carried a one-time charge into every forecast year.",
        "would_change_it": "Two consecutive quarters below 70% (competitive entry faster "
                           "than assumed) or above 75% (pricing power holding).",
        "challenger": "own analysis (contamination catalog)",
    },
    {
        "driver": "R&D / revenue",
        "value": "7.5% -> 10.5%",
        "label": "judgment",
        "basis": "H1 FY2027 7.52%. The ratio rises as growth slows because a roadmap "
                 "committed years ahead cannot decelerate with revenue (Lab 10 reasoning).",
        "challenge": "Holding the ratio flat would assume NVIDIA can throttle its roadmap.",
        "would_change_it": "R&D dollars falling year over year, or guidance of a "
                           "materially larger roadmap (e.g. annual architecture cadence "
                           "broadened).",
        "challenger": "own analysis",
    },
    {
        "driver": "Cost of equity / WACC",
        "value": "beta 2.216 -> Ke 16.27%, WACC ~16.25%",
        "label": "estimate",
        "basis": "CAPM: risk-free 5.19% (10y UST 2026-10-14) + 2.216 x 5% ERP. Beta is my "
                 "own OLS estimate, 5y monthly vs S&P 500. Debt is 0.16% of capital.",
        "challenge": "Colin (Lab 12): 'How did you choose your beta?' -- I misdescribed the "
                     "method in the room; corrected in the Lab 12 record. The Blume-"
                     "adjusted 1.815 gives Ke 14.27%, a 200bp swing that is run as the high "
                     "case.",
        "would_change_it": "A 2-year beta re-estimate below 1.8, or a defensible "
                           "forward-looking ERP below 5%.",
        "challenger": "Colin (Lab 12 review, 2026-10-01)",
    },
    {
        "driver": "Terminal growth",
        "value": "3.0%",
        "label": "assumption",
        "basis": "Long-run nominal US growth; course rule: perpetual growth may not exceed "
                 "long-run nominal economic growth.",
        "challenge": "Terminal value is roughly 60% of enterprise value, so this and WACC "
                     "carry most of the answer.",
        "would_change_it": "Nothing company-specific; only a change in long-run nominal "
                           "growth expectations.",
        "challenger": "own analysis",
    },
    {
        "driver": "Excess inventory purchase obligations / inventory",
        "value": "12.80%",
        "label": "history",
        "basis": "FY2026 2,739 / 21,403. The company-specific line: fabless, so NVIDIA "
                 "commits to foundry capacity before it knows demand.",
        "challenge": "Small in value terms; it is a monitoring signal more than a value "
                     "driver.",
        "would_change_it": "The ratio rising above 15% in a 10-Q -- the first sign of "
                           "over-ordering.",
        "challenger": "own analysis (Lab 10)",
    },
    {
        "driver": "DCF vs pro-forma agreement",
        "value": "FCFF/WACC and FCFE/Ke reconcile",
        "label": "model output",
        "basis": "Both run off the same projection; FCFE = FCFF + after-tax net interest - "
                 "debt repaid, checked every year.",
        "challenge": "Colin (Lab 12): 'Which valuation do you trust more?' The agreement "
                     "validates the plumbing, not the inputs.",
        "would_change_it": "n/a -- a reconciliation failure is a bug, not a view.",
        "challenger": "Colin (Lab 12 review, 2026-10-01)",
    },
]

# Base-year normalisation catalog (Week 2 contamination catalog applied to FY2026).
NORMALIZATIONS = [
    {
        "item": "Inventory write-down (incl. H20 export-restriction charges)",
        "type": "one-time expense",
        "amount": FY2026_INVENTORY_WRITEDOWN,
        "source": TEN_K + ", XBRL InventoryWriteDown",
        "direction": "punished FY2026 gross margin",
        "treatment": "Reported GM 71.07% -> normalised 72.92%. Forecast GM starts from the "
                     "H1 FY2027 run rate instead of FY2026 reported.",
    },
    {
        "item": "Gains on non-marketable and publicly-held equity securities",
        "type": "one-time income (mark-to-market)",
        "amount": FY2026_INVESTMENT_GAINS,
        "source": TEN_K + ", cash flow statement",
        "direction": "flattered FY2026 net income (8,918 of 120,067)",
        "treatment": "Excluded from the forecast; the stakes are added in the bridge at "
                     "carrying value instead. H1 FY2027 gains of 23,707 treated the same way.",
    },
    {
        "item": "Effective tax rate drift (global minimum tax)",
        "type": "basis change",
        "amount": None,
        "source": TEN_K + " (12.0% / 13.3% / 15.1% FY2024-26); " + TEN_Q + " (16.5% H1)",
        "direction": "rising",
        "treatment": "16% forecast rate rather than any single historical year.",
    },
    {
        "item": "Debt issued after the base year",
        "type": "basis change (post-period)",
        "amount": JUL2026_DEBT - BRIDGE["debt"],
        "source": TEN_Q + " balance sheet",
        "direction": "debt 8,468 -> 33,366",
        "treatment": "Bridge stays on the FY2026 balance sheet the forecast opens from, so "
                     "cash flows and claims are dated together. Disclosed as a limitation.",
    },
    {
        "item": "Share basis",
        "type": "mechanical",
        "amount": None,
        "source": TEN_K + " EPS note and cover; " + TEN_Q,
        "direction": "24,514 diluted WA vs 24,304 outstanding vs 24,285 Q2 diluted",
        "treatment": "Diluted 24,514 throughout; using 24,304 would raise value ~0.9%.",
    },
]

# ---------------------------------------------------------------------------
# SCENARIOS -- causal, not +/- percentages
# ---------------------------------------------------------------------------
# Low and high change several CAUSALLY LINKED inputs together, each with its story. FY2027E is
# half reported already, so even the low case keeps the reported first half.
CASES = {
    "low": {
        "name": "AI capex digestion",
        "story": "Hyperscalers pause after FY2027: H2 FY2027 only matches H1, FY2028 revenue "
                 "falls 10%, and custom silicon takes share so gross margin fades to 65%.",
        "overrides": {
            "revenue_growth": [2 * H1_FY2027_REVENUE / FY2026_REVENUE - 1,
                               -0.10, 0.05, 0.05, 0.04],
            "gross_margin": [0.745, 0.700, 0.670, 0.660, 0.650],
        },
    },
    "base": {
        "name": "Re-anchored base",
        "story": "Reported H1 FY2027 plus a flat H2 run rate, then the Lab 10 decay path; "
                 "gross margin fades from 75% to 69%.",
        "overrides": {},
    },
    "high": {
        "name": "Sustained build-out",
        "story": "Demand broadens beyond hyperscalers: FY2027 +80%, then 30/20/12/7%; "
                 "pricing power holds gross margin at 74%; as revenue diversifies the "
                 "Blume-adjusted beta (1.815) is the better risk estimate.",
        "overrides": {
            "revenue_growth": [0.80, 0.30, 0.20, 0.12, 0.07],
            "gross_margin": [0.750, 0.745, 0.740, 0.740, 0.740],
            "beta": BLUME_BETA,
        },
    },
}

WHAT_IFS = {
    "hyperscaler_pause": {
        "name": "Hyperscaler capex pause (downside)",
        "story": "Base, except FY2028E revenue is flat (0% growth) before the decay resumes.",
        "overrides": {"revenue_growth": [FY2027E_GROWTH, 0.0, 0.16, 0.11, 0.07]},
    },
    "margin_compression": {
        "name": "Custom-silicon margin compression (downside)",
        "story": "Base, except gross margin falls to 65% by FY2029E and stays there.",
        "overrides": {"gross_margin": [0.750, 0.700, 0.650, 0.650, 0.650]},
    },
    "sbc_cost": {
        "name": "Stock compensation treated as a cash cost",
        "story": "Base, except SBC is not added back in FCFF -- it is a real cost paid in shares.",
        "overrides": {"sbc_as_cash_cost": True},
    },
    "blume_beta": {
        "name": "Blume-adjusted beta",
        "story": "Base, except beta 1.815 instead of the raw 2.216.",
        "overrides": {"beta": BLUME_BETA},
    },
}

# ---------------------------------------------------------------------------
# COMPARABLES -- policy written before the multiples were computed
# ---------------------------------------------------------------------------
PEER_POLICY = [
    "Fabless or design-led semiconductor companies whose largest revenue source is "
    "data-centre / AI compute or networking silicon.",
    "Positive GAAP operating income and diluted EPS in the latest fiscal year (a negative "
    "multiple carries no information).",
    "Latest fiscal-year 10-K, fiscal year ending within 120 days of NVIDIA's 2026-01-25.",
    "One price date for all companies: 2026-10-14 close.",
    "One definition for all: EV = price x diluted WA shares + total debt (carrying) - cash, "
    "equivalents and short-term investments. EBITDA = GAAP operating income + depreciation "
    "and amortisation from the cash flow statement, INCLUDING acquisition-intangible "
    "amortisation. P/E = price / GAAP diluted EPS.",
    "Intel excluded (Lab 08): integrated manufacturer with its own fabs, negative FY2025 EPS.",
]

COMPANIES = {
    "NVDA": {
        "price": 221.30, "fiscal_end": "2026-01-25",
        "source": "10-K acc. 0001045810-26-000021",
        "revenue": 215_938.0, "operating_income": 130_387.0, "d_and_a": 2_843.0,
        "eps": 4.90, "diluted_shares": 24_514.0,
        "cash_and_st_investments": 62_556.0, "debt": 8_468.0,
    },
    "AMD": {
        "price": 570.82, "fiscal_end": "2025-12-27",
        "source": "10-K acc. 0000002488-26-000018 (XBRL)",
        "revenue": 34_639.0, "operating_income": 3_694.0,
        "d_and_a": 750.0 + 2_254.0,   # D&A 750 + amortisation of acquisition intangibles 2,254
        "eps": 2.65, "diluted_shares": 1_636.0,
        "cash_and_st_investments": 5_539.0 + 5_013.0,
        "debt": 2_348.0 + 874.0,
    },
    "AVGO": {
        "price": 346.25, "fiscal_end": "2025-11-02",
        "source": "10-K acc. 0001730168-25-000121 (XBRL)",
        "revenue": 63_887.0, "operating_income": 25_484.0,
        "d_and_a": 574.0 + 8_062.0,   # depreciation 574 + amortisation of intangibles 8,062
        "eps": 4.77, "diluted_shares": 4_853.0,
        "cash_and_st_investments": 16_178.0,
        "debt": 61_984.0 + 3_152.0,
    },
}
TARGET_TICKER = "NVDA"
PEER_TICKERS = ["AMD", "AVGO"]
PEER_FISCAL_WINDOW_DAYS = 120

# ---------------------------------------------------------------------------
# DECISION RULE -- applied to every case and what-if, not only the base
# ---------------------------------------------------------------------------
# Absolute value (the DCF) decides; relative value (the comps) can only hold a name on watch,
# never initiate it. That is the Lab 08 reasoning written down as a rule:
#   INITIATE         price <= the scenario's DCF value per share
#   WATCH/DEFER      price above it, BUT relative value supports waiting: NVDA's trailing
#                    EV/EBITDA is below EVERY admitted peer's AND the scenario's EBITDA never
#                    falls year over year
#   DO NOT INITIATE  otherwise
# Why the earnings-persistence leg: a low trailing multiple only means "cheap" if the earnings
# it is measured on persist. In a scenario where EBITDA falls, the trailing multiple overstates
# the discount and stops being evidence for waiting.
# Revision record: the first-run rule (commit 93a7ac9) held the name on watch whenever NVDA was
# below the peer MEDIAN, with no persistence leg. Its first run showed no downside case could
# ever alter the action, which fails the project's requirement that one could -- so the rule
# was revised after that run, and the revision is disclosed in docs/validation-and-ai-use.md.
GRID_WACC_STEPS = [-0.02, -0.01, 0.0, 0.01, 0.02]
GRID_TERMINAL_GROWTH = [0.020, 0.025, 0.030, 0.035, 0.040]
TOLERANCE = 0.05      # USD millions, for every accounting check


# ---------------------------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------------------------
# Mapping from Project 1 input names to the pro-forma's module-level constants.
_PROFORMA_MAP = {
    "revenue_growth": "REVENUE_GROWTH",
    "gross_margin": "GROSS_MARGIN",
    "rd_to_revenue": "RD_TO_REVENUE",
    "sga_to_gross_profit": "SGA_TO_GROSS_PROFIT",
    "tax_rate": "TAX_RATE",
    "capex_to_revenue": "CAPEX_TO_REVENUE",
    "buyback": "SHARE_BUYBACK",
    "dividends": "DIVIDENDS",
    "terminal_growth": "TERMINAL_GROWTH",
}
_PROFORMA_SNAPSHOT_NAMES = list(_PROFORMA_MAP.values()) + [
    "OPENING", "COST_OF_EQUITY", "SHARES_OUTSTANDING",
]


def base_inputs():
    """A fresh deep copy of the Project 1 base inputs."""
    return copy.deepcopy(BASE_INPUTS)


def apply_overrides(inputs, overrides):
    """Return a copy of inputs with overrides applied. Unknown names are refused."""
    result = copy.deepcopy(inputs)
    for name, value in overrides.items():
        if name not in result:
            raise KeyError(f"unknown input '{name}'")
        result[name] = copy.deepcopy(value)
    return result


@contextlib.contextmanager
def _proforma_set_to(inputs, cost_of_equity):
    """Point the Lab 10 engine at these inputs for one run, then restore it exactly."""
    snapshot = {name: copy.deepcopy(getattr(proforma, name))
                for name in _PROFORMA_SNAPSHOT_NAMES}
    try:
        for key, constant in _PROFORMA_MAP.items():
            setattr(proforma, constant, copy.deepcopy(inputs[key]))
        proforma.COST_OF_EQUITY = cost_of_equity
        proforma.SHARES_OUTSTANDING = BRIDGE["diluted_shares"]
        if inputs["inject_fault"] == "opening_mapping_error":
            # A realistic mistype: 1,000 dropped from one opening asset line.
            opening = copy.deepcopy(proforma.OPENING)
            opening["other_assets"] -= 1_000.0
            proforma.OPENING = opening
        yield
    finally:
        for name, value in snapshot.items():
            setattr(proforma, name, value)


def cost_of_equity(inputs):
    """CAPM: risk-free + beta x equity risk premium."""
    return inputs["risk_free"] + inputs["beta"] * inputs["equity_risk_premium"]


def wacc(inputs):
    """Market-value weighted: equity at price x diluted shares, debt at carrying value."""
    equity_value = inputs["price"] * BRIDGE["diluted_shares"]
    debt_value = BRIDGE["debt"]
    after_tax_debt = inputs["pre_tax_cost_of_debt"] * (1 - inputs["tax_rate"])
    return ((equity_value * cost_of_equity(inputs) + debt_value * after_tax_debt)
            / (equity_value + debt_value))


def _check(name, passed, detail):
    return {"check": name, "passed": bool(passed), "detail": detail}


def _cash_flow_statement(projection, opening_cash, opening_revolver):
    """Indirect cash flow statement from the projection; ending cash must tie to the sheet."""
    rows = []
    cash, revolver = opening_cash, opening_revolver
    for year in projection:
        cfo = (year["net_income"] + year["depreciation"] + year["stock_compensation"]
               - year["inventory_change"] - year["other_working_capital_change"]
               + year["supply_obligations_change"])
        cfi = -year["capex"]
        cff = (-year["repayment"] - year["buyback"] - year["dividends"]
               - year["surplus_distribution"] + (year["revolver"] - revolver))
        ending = cash + cfo + cfi + cff
        rows.append({
            "label": year["label"], "cfo": cfo, "cfi": cfi, "cff": cff,
            "ending_cash_from_cfs": ending, "balance_sheet_cash": year["cash"],
            "tie_gap": ending - year["cash"],
        })
        cash, revolver = year["cash"], year["revolver"]
    return rows


def _fcff(year, tax_rate, sbc_as_cash_cost):
    """FCFF = EBIT(1 - t) + D&A + SBC - capex - change in working capital + supply accrual."""
    sbc_addback = 0.0 if sbc_as_cash_cost else year["stock_compensation"]
    return (year["operating_income"] * (1 - tax_rate) + year["depreciation"] + sbc_addback
            - year["capex"] - year["inventory_change"]
            - year["other_working_capital_change"] + year["supply_obligations_change"])


def run_model(inputs=None):
    """Build the pro-forma, check it, and value it. Refuses to value a model that fails.

    Returns a dict with 'valid', 'checks', the statements, and (only if valid) 'valuation'.
    """
    inputs = base_inputs() if inputs is None else inputs
    ke = cost_of_equity(inputs)
    discount_rate = wacc(inputs)
    checks = []
    result = {"inputs": copy.deepcopy(inputs), "cost_of_equity": ke, "wacc": discount_rate,
              "checks": checks, "valid": False, "valuation": None}

    with _proforma_set_to(inputs, ke):
        # 1. Base year reconciles to the filing.
        try:
            assets, liabilities, gap = proforma.check_opening_balance()
            checks.append(_check(
                "Base year reconciles to the 10-K", True,
                f"assets {assets:,.0f} = filed {proforma.FILED_TOTAL_ASSETS:,.0f}; "
                f"liabilities {liabilities:,.0f} = filed {proforma.FILED_TOTAL_LIABILITIES:,.0f}"))
        except ValueError as error:
            checks.append(_check("Base year reconciles to the 10-K", False, str(error)))
            return result
        base_revenue_ok = abs(proforma.OPENING["revenue"] - FY2026_REVENUE) < TOLERANCE
        checks.append(_check("Base revenue equals filed FY2026 revenue", base_revenue_ok,
                             f"{proforma.OPENING['revenue']:,.0f} vs {FY2026_REVENUE:,.0f}"))

        projection = proforma.build_projection()
        opening = dict(proforma.OPENING)

        if inputs["inject_fault"] == "drop_sbc_equity_credit":
            # The Lab 10 refusal demonstration: SBC added back in cash but never credited
            # to equity. The gap must equal SBC exactly.
            for year in projection:
                year["equity"] -= year["stock_compensation"]
                year["balance_gap"] = (year["total_assets"] - year["total_liabilities"]
                                       - year["equity"])

        # 2. Balance sheet balances every year.
        worst_gap = max(abs(year["balance_gap"]) for year in projection)
        checks.append(_check("Balance sheet balances every year", worst_gap <= TOLERANCE,
                             f"largest |assets - liabilities - equity| = {worst_gap:,.2f}"))

        # 3. Cash flow statement ties to balance-sheet cash.
        cash_flows = _cash_flow_statement(projection, opening["cash"], opening["revolver"])
        worst_tie = max(abs(row["tie_gap"]) for row in cash_flows)
        checks.append(_check("Cash flow ties to balance-sheet cash", worst_tie <= TOLERANCE,
                             f"largest |CFS ending cash - BS cash| = {worst_tie:,.2f}"))

        # 4. Minimum cash respected (the revolver logic did its job).
        low_cash = min(year["cash"] for year in projection)
        checks.append(_check("Cash never below the minimum", low_cash >= proforma.MINIMUM_CASH - TOLERANCE,
                             f"lowest cash {low_cash:,.0f} vs minimum {proforma.MINIMUM_CASH:,.0f}"))

        # 5. FCFF and FCFE reconcile: FCFE = FCFF + after-tax net interest - debt repaid
        #    (+ SBC when FCFF treats it as a cash cost, because FCFE always adds it back).
        tax_rate = inputs["tax_rate"]
        fcff = [_fcff(year, tax_rate, inputs["sbc_as_cash_cost"]) for year in projection]
        worst_recon = 0.0
        for year, firm_flow in zip(projection, fcff):
            expected_fcfe = (firm_flow + year["net_interest"] * (1 - tax_rate)
                             - year["repayment"]
                             + (year["stock_compensation"] if inputs["sbc_as_cash_cost"] else 0.0))
            worst_recon = max(worst_recon, abs(expected_fcfe - year["fcfe"]))
        checks.append(_check("FCFF reconciles to the pro-forma's FCFE", worst_recon <= TOLERANCE,
                             f"largest gap {worst_recon:,.4f}"))

        # 6. Terminal growth below the discount rate, or the Gordon formula is undefined.
        g = inputs["terminal_growth"]
        checks.append(_check("Terminal growth below WACC", g < discount_rate,
                             f"g {g:.2%} vs WACC {discount_rate:.2%}"))

        fcfe_value = None
        if all(item["passed"] for item in checks):
            fcfe_value = proforma.value_equity(projection, ke)["value_per_share"]

    result["projection"] = [
        {key: year[key] for key in (
            "label", "revenue", "gross_profit", "research_development", "sga",
            "depreciation", "operating_income", "net_interest", "tax", "net_income",
            "stock_compensation", "cash", "inventory", "ppe", "other_assets",
            "supply_obligations", "debt", "other_liabilities", "revolver", "equity",
            "total_assets", "total_liabilities", "balance_gap", "capex", "fcfe")}
        for year in projection
    ]
    result["cash_flows"] = cash_flows
    result["fcff"] = fcff

    if not all(item["passed"] for item in checks):
        return result        # loud refusal: no value is produced for a broken model

    # --- Valuation: the Lab 06 engine, fed pro-forma FCFF ---
    pv_explicit = dcf_engine.present_value_explicit(fcff, discount_rate)
    terminal_value = dcf_engine.gordon_terminal_value(fcff[-1], discount_rate, g)
    pv_terminal = terminal_value * dcf_engine.discount_factor(discount_rate, len(fcff))
    enterprise_value = pv_explicit + pv_terminal
    equity_value = (enterprise_value + BRIDGE["cash_and_marketable_securities"]
                    + BRIDGE["non_marketable_equity_securities"] - BRIDGE["debt"])
    per_share = equity_value / BRIDGE["diluted_shares"]

    # 7. Bridge arithmetic holds both ways.
    bridge_gap = (per_share * BRIDGE["diluted_shares"]
                  - (pv_explicit + pv_terminal + BRIDGE["cash_and_marketable_securities"]
                     + BRIDGE["non_marketable_equity_securities"] - BRIDGE["debt"]))
    checks.append(_check("Enterprise-to-equity bridge reconciles", abs(bridge_gap) <= TOLERANCE,
                         f"EV {enterprise_value:,.0f} + cash/securities "
                         f"{BRIDGE['cash_and_marketable_securities']:,.0f} + equity stakes "
                         f"{BRIDGE['non_marketable_equity_securities']:,.0f} - debt "
                         f"{BRIDGE['debt']:,.0f} = {equity_value:,.0f}"))

    result["valid"] = all(item["passed"] for item in checks)
    result["valuation"] = {
        "pv_explicit": pv_explicit,
        "terminal_value": terminal_value,
        "pv_terminal": pv_terminal,
        "enterprise_value": enterprise_value,
        "equity_value": equity_value,
        "value_per_share": per_share,
        "terminal_share_of_ev": pv_terminal / enterprise_value,
        "fcfe_value_per_share": fcfe_value,
    }
    return result


def value_per_share(inputs):
    """Value per share, or None if the model refuses."""
    run = run_model(inputs)
    return run["valuation"]["value_per_share"] if run["valid"] else None


def sensitivity_grid(inputs=None):
    """Value per share over WACC x terminal growth, all else held at the given inputs.

    WACC is moved directly here (not through beta), so the grid isolates the discount rate.
    """
    inputs = base_inputs() if inputs is None else inputs
    base = run_model(inputs)
    base_wacc = base["wacc"]
    fcff = base["fcff"]
    waccs = [base_wacc + step for step in GRID_WACC_STEPS]
    rows = []
    for rate in waccs:
        row = []
        for g in GRID_TERMINAL_GROWTH:
            if g >= rate:
                row.append(None)
                continue
            ev = (dcf_engine.present_value_explicit(fcff, rate)
                  + dcf_engine.gordon_terminal_value(fcff[-1], rate, g)
                  * dcf_engine.discount_factor(rate, len(fcff)))
            equity = (ev + BRIDGE["cash_and_marketable_securities"]
                      + BRIDGE["non_marketable_equity_securities"] - BRIDGE["debt"])
            row.append(equity / BRIDGE["diluted_shares"])
        rows.append(row)
    return {"wacc": waccs, "terminal_growth": list(GRID_TERMINAL_GROWTH), "values": rows}


def grid_is_monotonic(grid):
    """Value must fall as WACC rises (down a column) and rise with growth (along a row)."""
    values = grid["values"]
    for row in values:
        cells = [v for v in row if v is not None]
        if any(b <= a for a, b in zip(cells, cells[1:])):
            return False
    for col in range(len(grid["terminal_growth"])):
        cells = [row[col] for row in values if row[col] is not None]
        if any(b >= a for a, b in zip(cells, cells[1:])):
            return False
    return True


def _bisect(function, low, high, target, tolerance=1e-7, iterations=200):
    """Solve function(x) = target on [low, high]; None if the target is not bracketed."""
    f_low, f_high = function(low), function(high)
    if f_low is None or f_high is None:
        return None
    if (f_low - target) * (f_high - target) > 0:
        return None
    for _ in range(iterations):
        middle = (low + high) / 2
        f_mid = function(middle)
        if f_mid is None:
            return None
        if (f_low - target) * (f_mid - target) <= 0:
            high = middle
        else:
            low, f_low = middle, f_mid
        if high - low < tolerance:
            break
    return (low + high) / 2


def reverse_dcf(inputs=None):
    """What does the market price already assume? Two separate solves, others held fixed."""
    inputs = base_inputs() if inputs is None else inputs
    price = inputs["price"]

    # FY2027E is held fixed: half of it is already reported, so the market's expectation can
    # only sit in FY2028E-FY2031E.
    def shifted_path(shift):
        path = list(inputs["revenue_growth"])
        return path[:1] + [rate + shift for rate in path[1:]]

    def value_at_shift(shift):
        return value_per_share(apply_overrides(inputs, {"revenue_growth": shifted_path(shift)}))

    shift = _bisect(value_at_shift, -0.30, 1.50, price)

    def value_at_beta(beta):
        return value_per_share(apply_overrides(inputs, {"beta": beta}))

    implied_beta = _bisect(value_at_beta, 0.05, 4.0, price)
    implied_ke = (None if implied_beta is None else
                  cost_of_equity(apply_overrides(inputs, {"beta": implied_beta})))
    implied_path = None if shift is None else shifted_path(shift)
    implied_fy2031_revenue = None
    if implied_path:
        revenue = FY2026_REVENUE
        for rate in implied_path:
            revenue *= 1 + rate
        implied_fy2031_revenue = revenue
    return {
        "price": price,
        "growth_shift": shift,
        "implied_growth_path": implied_path,
        "implied_fy2031_revenue": implied_fy2031_revenue,
        "implied_beta": implied_beta,
        "implied_cost_of_equity": implied_ke,
        "held_fixed": "FY2027E growth (half reported), margins, cost ratios, capex intensity, "
                      "terminal growth 3%, the bridge; beta for the growth solve and growth "
                      "for the beta solve",
    }


def _days_between(first, second):
    import datetime
    a = datetime.date.fromisoformat(first)
    b = datetime.date.fromisoformat(second)
    return abs((a - b).days)


def comparables():
    """EV/EBITDA and P/E under the written policy, plus the policy-consistency checks."""
    rows = {}
    for ticker, data in COMPANIES.items():
        market_cap = data["price"] * data["diluted_shares"]
        ev = market_cap + data["debt"] - data["cash_and_st_investments"]
        ebitda = data["operating_income"] + data["d_and_a"]
        rows[ticker] = {
            "market_cap": market_cap, "enterprise_value": ev, "ebitda": ebitda,
            "ev_ebitda": ev / ebitda if ebitda > 0 else None,
            "pe": data["price"] / data["eps"] if data["eps"] > 0 else None,
            "ebitda_margin": ebitda / data["revenue"],
            "fiscal_end": data["fiscal_end"],
        }

    target = COMPANIES[TARGET_TICKER]
    target_ebitda = rows[TARGET_TICKER]["ebitda"]
    implied = {}
    for ticker in PEER_TICKERS:
        ev_multiple = rows[ticker]["ev_ebitda"]
        implied_ev = ev_multiple * target_ebitda
        implied_equity = (implied_ev - target["debt"] + target["cash_and_st_investments"])
        implied[ticker] = {
            "from_ev_ebitda": implied_equity / target["diluted_shares"],
            "from_pe": rows[ticker]["pe"] * target["eps"],
        }

    peer_ev = sorted(rows[t]["ev_ebitda"] for t in PEER_TICKERS)
    peer_median_ev_ebitda = (peer_ev[len(peer_ev) // 2] if len(peer_ev) % 2 else
                             (peer_ev[len(peer_ev) // 2 - 1] + peer_ev[len(peer_ev) // 2]) / 2)
    lowest_peer_ev_ebitda = peer_ev[0]

    required = ("price", "fiscal_end", "revenue", "operating_income", "d_and_a", "eps",
                "diluted_shares", "cash_and_st_investments", "debt", "source")
    policy_checks = [
        _check("Every company carries every field of the one definition",
               all(all(key in COMPANIES[t] for key in required) for t in COMPANIES),
               "fields: " + ", ".join(required)),
        _check("Peer fiscal years end within 120 days of NVIDIA's",
               all(_days_between(COMPANIES[t]["fiscal_end"], target["fiscal_end"])
                   <= PEER_FISCAL_WINDOW_DAYS for t in PEER_TICKERS),
               ", ".join(f"{t} {COMPANIES[t]['fiscal_end']}" for t in PEER_TICKERS)),
        _check("Positive EBITDA and EPS for every admitted company",
               all(rows[t]["ebitda"] > 0 and COMPANIES[t]["eps"] > 0 for t in COMPANIES),
               "a negative multiple is excluded, not averaged"),
        _check("EV/EBITDA recomputes from its parts for every company",
               all(abs(rows[t]["ev_ebitda"] * rows[t]["ebitda"] - rows[t]["enterprise_value"])
                   < TOLERANCE for t in COMPANIES),
               "EV = price x diluted shares + debt - cash and short-term investments"),
    ]
    return {
        "policy": PEER_POLICY, "rows": rows, "implied_nvda_value": implied,
        "peer_median_ev_ebitda": peer_median_ev_ebitda,
        "lowest_peer_ev_ebitda": lowest_peer_ev_ebitda,
        "nvda_below_every_peer": rows[TARGET_TICKER]["ev_ebitda"] < lowest_peer_ev_ebitda,
        "checks": policy_checks,
    }


def ebitda_persists(run):
    """True if the scenario's EBITDA never falls -- FY2026 actual through FY2031E."""
    actual = COMPANIES[TARGET_TICKER]["operating_income"] + COMPANIES[TARGET_TICKER]["d_and_a"]
    path = [actual] + [y["operating_income"] + y["depreciation"] for y in run["projection"]]
    return all(b >= a for a, b in zip(path, path[1:]))


def decide(price, value, nvda_below_every_peer, earnings_persist):
    """Apply the written decision rule to one scenario. Returns (action, reason)."""
    if price <= value:
        return "INITIATE", f"price ${price:,.2f} at or below DCF value ${value:,.2f}"
    if nvda_below_every_peer and earnings_persist:
        return ("WATCH/DEFER", f"price ${price:,.2f} above DCF value ${value:,.2f}, but NVDA "
                               "trades below every admitted peer on EV/EBITDA and the "
                               "earnings behind that multiple persist in this scenario")
    if not earnings_persist:
        return ("DO NOT INITIATE", f"price ${price:,.2f} above DCF value ${value:,.2f}, and "
                                   "EBITDA falls in this scenario, so the low trailing multiple "
                                   "overstates the discount")
    return ("DO NOT INITIATE", f"price ${price:,.2f} above DCF value ${value:,.2f} and NVDA is "
                               "not cheap against peers")


def run_analysis(inputs=None):
    """Every material Project 1 result, from one call. The app and the freeze both use this."""
    inputs = base_inputs() if inputs is None else inputs
    base_run = run_model(inputs)
    comps = comparables()

    def scenario(definition):
        run = run_model(apply_overrides(inputs, definition["overrides"]))
        entry = {"name": definition["name"], "story": definition["story"],
                 "valid": run["valid"], "wacc": run["wacc"], "value_per_share": None,
                 "action": "REFUSED -- a check failed", "reason": None,
                 "earnings_persist": None}
        if run["valid"]:
            value = run["valuation"]["value_per_share"]
            persist = ebitda_persists(run)
            action, reason = decide(inputs["price"], value, comps["nvda_below_every_peer"],
                                    persist)
            entry.update(value_per_share=value, action=action, reason=reason,
                         earnings_persist=persist,
                         fy2031_revenue=run["projection"][-1]["revenue"])
        return entry

    cases = {key: scenario(case) for key, case in CASES.items()}
    what_ifs = {key: scenario(case) for key, case in WHAT_IFS.items()}
    grid = sensitivity_grid(inputs) if base_run["valid"] else None
    reverse = reverse_dcf(inputs) if base_run["valid"] else None

    decision = None
    if cases["base"]["valid"]:
        decision = {"action": cases["base"]["action"], "reason": cases["base"]["reason"]}

    checks = list(base_run["checks"]) + comps["checks"]
    if grid:
        checks.append(_check("DCF grid monotonic (value falls with WACC, rises with g)",
                             grid_is_monotonic(grid), "checked over the 5 x 5 grid"))
    return {
        "base": base_run, "cases": cases, "what_ifs": what_ifs, "comparables": comps,
        "grid": grid, "reverse_dcf": reverse, "decision": decision, "checks": checks,
        "all_checks_passed": all(item["passed"] for item in checks),
    }


# ---------------------------------------------------------------------------
# FROZEN OUTPUT -- the validated subset, exported deliberately
# ---------------------------------------------------------------------------
def visible_output(results):
    """The frozen interface contract the app and the grader read without running code."""
    base = results["base"]
    cases = results["cases"]
    comps = results["comparables"]
    reverse = results["reverse_dcf"]
    low, mid, high = (cases[k]["value_per_share"] for k in ("low", "base", "high"))
    return {
        "decision": DECISION,
        "intended_user": USER,
        "horizon": HORIZON,
        "as_of": AS_OF,
        "currency_and_units": CURRENCY,
        "share_basis": SHARE_BASIS,
        "sources": [TEN_K, TEN_Q,
                    "Market data: NVDA $221.30, AMD $570.82, AVGO $346.25, 10y UST 5.190%, "
                    "Yahoo Finance via yfinance, close 2026-10-14",
                    "Peers: AMD 10-K acc. 0000002488-26-000018; Broadcom 10-K acc. "
                    "0001730168-25-000121 (SEC XBRL company facts)"],
        "material_inputs": {
            "price": base["inputs"]["price"],
            "revenue_growth": [round(r, 4) for r in base["inputs"]["revenue_growth"]],
            "gross_margin": base["inputs"]["gross_margin"],
            "beta": base["inputs"]["beta"],
            "risk_free": base["inputs"]["risk_free"],
            "equity_risk_premium": base["inputs"]["equity_risk_premium"],
            "cost_of_equity": round(base["cost_of_equity"], 4),
            "wacc": round(base["wacc"], 4),
            "terminal_growth": base["inputs"]["terminal_growth"],
            "bridge": BRIDGE,
        },
        "valuation": {
            "dcf_low_base_high_per_share": [round(low, 2), round(mid, 2), round(high, 2)],
            "case_names": [cases[k]["name"] for k in ("low", "base", "high")],
            "enterprise_value": round(base["valuation"]["enterprise_value"], 0),
            "terminal_share_of_ev": round(base["valuation"]["terminal_share_of_ev"], 4),
            "fcfe_cross_check_per_share": round(base["valuation"]["fcfe_value_per_share"], 2),
            "case_actions": [cases[k]["action"] for k in ("low", "base", "high")],
            "what_ifs": {v["name"]: {"value_per_share": round(v["value_per_share"], 2),
                                     "action": v["action"]}
                         for v in results["what_ifs"].values()},
            "wacc_growth_grid_range": [
                round(min(v for row in results["grid"]["values"] for v in row if v), 2),
                round(max(v for row in results["grid"]["values"] for v in row if v), 2)],
            "reverse_dcf": {
                "uniform_growth_shift_pp": round(reverse["growth_shift"] * 100, 2)
                if reverse["growth_shift"] is not None else None,
                "implied_beta": round(reverse["implied_beta"], 3)
                if reverse["implied_beta"] is not None else None,
                "implied_cost_of_equity": round(reverse["implied_cost_of_equity"], 4)
                if reverse["implied_cost_of_equity"] is not None else None,
            },
            "comparables": {
                t: {"ev_ebitda": round(r["ev_ebitda"], 1), "pe": round(r["pe"], 1)}
                for t, r in comps["rows"].items()},
            "nvda_implied_from_peers_per_share": {
                t: {k: round(v, 2) for k, v in d.items()}
                for t, d in comps["implied_nvda_value"].items()},
        },
        "recommendation": {
            "action": results["decision"]["action"],
            "reason": results["decision"]["reason"],
            "range_per_share": f"${low:,.0f}-${high:,.0f} (DCF low-high); base ${mid:,.0f}",
            "conditions": [
                "Watch holds only while NVDA's trailing EV/EBITDA stays below every admitted "
                "peer's and the evidence keeps EBITDA growing.",
                "Initiate condition: price at or below the base-case DCF value.",
                "Downside evidence that flips the action: a reported quarter showing "
                "year-over-year revenue decline or gross margin below 70% moves the evidence "
                "toward the AI-capex-digestion case, where the rule gives DO NOT INITIATE.",
            ],
        },
        "reversal_trigger": (
            "INITIATE if NVDA closes at or below the base-case value per share. DO NOT "
            "INITIATE if a 10-Q shows year-over-year revenue decline (the low-case path), or "
            "if NVDA's trailing EV/EBITDA rises to or above the lowest admitted peer's. "
            "Review at each 10-Q; next due for Q3 FY2027 (quarter ending late October 2026)."),
        "checks": [{"check": c["check"], "passed": c["passed"]} for c in results["checks"]],
        "all_checks_passed": results["all_checks_passed"],
        "limitations": [
            "The forecast opens on the FY2026 (Jan 2026) balance sheet and discounts from that "
            "date; the price is October 2026. Debt rose to 33,366 and distributions continued "
            "in between.",
            "WACC rests almost entirely on beta; the raw-to-Blume swing is about 200bp.",
            "Two peers only; trailing multiples lag NVIDIA's growth.",
            "Scenario endpoints are judgments, not probabilities.",
        ],
    }


def _fmt(value):
    return "n/a" if value is None else f"{value:,.2f}"


def report(results):
    """Plain-text report -- display only, every number comes from run_analysis."""
    lines = []
    add = lines.append
    base = results["base"]
    add("=" * 78)
    add("PROJECT 1 -- NVIDIA (NVDA) -- valuation range and committee action")
    add("=" * 78)
    add(f"Decision: {DECISION}")
    add(f"As of {AS_OF}. {CURRENCY}. Share basis: {SHARE_BASIS}.")
    add(f"Price ${base['inputs']['price']:,.2f} ({MARKET['price_date']}, {MARKET['price_source']})")
    add("")
    add("CHECKS (a failure stops the valuation)")
    for item in results["checks"]:
        add(f"  [{'PASS' if item['passed'] else 'FAIL'}] {item['check']}: {item['detail']}")
    add("")
    add("PRO-FORMA (USD millions)")
    labels = [y["label"] for y in base["projection"]]
    add("  " + " " * 26 + "".join(f"{l:>13}" for l in labels))
    for key, name in [("revenue", "Revenue"), ("gross_profit", "Gross profit"),
                      ("operating_income", "Operating income"), ("net_income", "Net income"),
                      ("cash", "Cash (BS)"), ("total_assets", "Total assets"),
                      ("equity", "Equity"), ("balance_gap", "Balance gap"),
                      ("fcfe", "FCFE")]:
        add(f"  {name:<26}" + "".join(f"{y[key]:>13,.1f}" for y in base["projection"]))
    add(f"  {'FCFF':<26}" + "".join(f"{v:>13,.1f}" for v in base["fcff"]))
    add(f"  {'CFS ending cash':<26}" + "".join(
        f"{r['ending_cash_from_cfs']:>13,.1f}" for r in base["cash_flows"]))
    add("")
    v = base["valuation"]
    add("FCFF DCF (base)")
    add(f"  Cost of equity {base['cost_of_equity']:.2%}   WACC {base['wacc']:.2%}   "
        f"terminal growth {base['inputs']['terminal_growth']:.2%}")
    add(f"  PV explicit {v['pv_explicit']:,.0f} + PV terminal {v['pv_terminal']:,.0f} "
        f"= EV {v['enterprise_value']:,.0f}  (terminal share {v['terminal_share_of_ev']:.1%})")
    add(f"  EV + cash/securities {BRIDGE['cash_and_marketable_securities']:,.0f} + equity "
        f"stakes {BRIDGE['non_marketable_equity_securities']:,.0f} - debt "
        f"{BRIDGE['debt']:,.0f} = equity {v['equity_value']:,.0f}")
    add(f"  / {BRIDGE['diluted_shares']:,.0f}M diluted shares = ${v['value_per_share']:,.2f}"
        f"   (FCFE cross-check ${v['fcfe_value_per_share']:,.2f})")
    add("")
    add("CASES (causal)")
    for key in ("low", "base", "high"):
        c = results["cases"][key]
        add(f"  {key:<5} {c['name']:<26} ${_fmt(c['value_per_share']):>9}  WACC {c['wacc']:.2%}"
            f"  -> {c['action']}")
        add(f"        {c['story']}")
    add("")
    add("WHAT-IFS (each off base) and the action the rule gives under each")
    for c in results["what_ifs"].values():
        add(f"  {c['name']:<46} ${_fmt(c['value_per_share']):>9}  -> {c['action']}")
    add("")
    grid = results["grid"]
    add("WACC x TERMINAL GROWTH (value per share, $)")
    add("  WACC \\ g " + "".join(f"{g:>10.1%}" for g in grid["terminal_growth"]))
    for rate, row in zip(grid["wacc"], grid["values"]):
        add(f"  {rate:>8.2%} " + "".join(f"{_fmt(x):>10}" for x in row))
    add("")
    r = results["reverse_dcf"]
    add("REVERSE DCF -- what the price assumes")
    if r["growth_shift"] is not None:
        add(f"  Uniform growth shift {r['growth_shift'] * 100:+.2f}pp: path "
            + " / ".join(f"{x:.1%}" for x in r["implied_growth_path"])
            + f"; FY2031E revenue {r['implied_fy2031_revenue']:,.0f}")
    if r["implied_beta"] is not None:
        add(f"  Or beta {r['implied_beta']:.3f} (cost of equity {r['implied_cost_of_equity']:.2%}) "
            "with the base operating forecast")
    add(f"  Held fixed: {r['held_fixed']}. One consistent assumption set, not proof of mispricing.")
    add("")
    comps = results["comparables"]
    add("COMPARABLES (policy fixed before computing; one definition, one price date)")
    for t, row in comps["rows"].items():
        add(f"  {t:<5} EV {row['enterprise_value']:>12,.0f}  EBITDA {row['ebitda']:>10,.0f}  "
            f"EV/EBITDA {row['ev_ebitda']:>6.1f}x  P/E {row['pe']:>6.1f}x  "
            f"EBITDA margin {row['ebitda_margin']:.1%}")
    add(f"  Peer median EV/EBITDA {comps['peer_median_ev_ebitda']:.1f}x; lowest peer "
        f"{comps['lowest_peer_ev_ebitda']:.1f}x; NVDA below every peer: "
        f"{comps['nvda_below_every_peer']}")
    for t, d in comps["implied_nvda_value"].items():
        add(f"  NVDA at {t}'s multiples: EV/EBITDA ${d['from_ev_ebitda']:,.2f}   "
            f"P/E ${d['from_pe']:,.2f}")
    add("")
    d = results["decision"]
    add(f"COMMITTEE ACTION: {d['action']} -- {d['reason']}")
    return "\n".join(lines)


def freeze(results):
    """Write the frozen contract and the human-readable report. Refuses if any check fails."""
    if not results["all_checks_passed"]:
        raise ValueError("Refusing to freeze: at least one check failed.")
    (HERE / "visible_output.json").write_text(
        json.dumps(visible_output(results), indent=2) + "\n", encoding="utf-8")
    output_dir = HERE / "output"
    output_dir.mkdir(exist_ok=True)
    (output_dir / "NVIDIA_2026-10-14_project1_report.txt").write_text(
        report(results) + "\n", encoding="utf-8")


def main():
    results = run_analysis()
    print(report(results))
    if not results["all_checks_passed"]:
        print("\nAt least one check FAILED -- valuation not trusted.", file=sys.stderr)
        return 1
    if "--freeze" in sys.argv:
        freeze(results)
        print("\nFrozen: visible_output.json and output/NVIDIA_2026-10-14_project1_report.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())
