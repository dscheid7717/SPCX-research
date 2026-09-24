"""Equity beta estimated from market data -- NVIDIA Corporation.

FIN 43900 (AI in Finance, Purdue), Lab 09 -- Session 9.
Author: Drew Scheiderer.

The question this answers: NVIDIA's cost of equity -- and therefore the 16.01%
WACC that drives the Lab 06 DCF -- rests almost entirely on one number, beta.
Lab 06 used a beta of 2.217 taken from a data provider. This script estimates
beta from the price history directly, so that figure stops being borrowed and
starts being something I produced and can defend.

Beta is not a fact to look up. It is the slope of a regression, and the slope
moves with three choices the analyst makes: how far back to look, how often to
sample, and which index to call "the market". So the script does not report a
number. It reports the same regression run under five defensible
specifications, with a standard error on each, and leaves the spread visible.

Prices are pulled once with yfinance and cached to CSV, so every later run is
reproducible from the saved data and the answer cannot drift underneath me.
The analysis layer below is standard library only -- no statistics package
computes the slope -- because I have to explain every line of it on camera.

Run with: cd nvidia && python beta.py
Force a fresh pull with: python beta.py --refresh
"""

import csv
import datetime as dt
import math
import pathlib
import sys

# ---------------------------------------------------------------------------
# INPUTS -- the only block intended to be edited
# ---------------------------------------------------------------------------

COMPANY = "NVIDIA Corporation (NVDA)"
TICKER = "NVDA"
MARKET_TICKER = "^GSPC"      # S&P 500 index. The stand-in for "the market".
MARKET_LABEL = "S&P 500"

# As-of date for the whole estimate. Every window is measured back from here.
AS_OF = dt.date(2026, 9, 22)

# Longest window needed, plus a buffer so the first return of the 5-year
# monthly window has a prior observation to be computed from.
HISTORY_START = dt.date(2021, 6, 1)

DATA_DIR = pathlib.Path(__file__).resolve().parent / "data"
PRICE_CACHE = DATA_DIR / "NVIDIA_2026-09-22_beta_prices.csv"

# Specifications to run. (label, years of history, sampling frequency).
# These are the conventions actually used in practice, not an arbitrary sweep:
# 5-year monthly is the classic textbook and Value Line convention, 2-year
# weekly is Bloomberg's default, and the daily windows are what a quant desk
# would reach for. Disagreement among them IS the finding.
SPECIFICATIONS = [
    ("5-year monthly", 5, "monthly"),
    ("2-year weekly", 2, "weekly"),
    ("5-year weekly", 5, "weekly"),
    ("1-year daily", 1, "daily"),
    ("2-year daily", 2, "daily"),
]

# The specification carried forward into the cost of equity. Chosen before
# seeing the results: 5-year monthly is the convention the DCF's terminal
# value implicitly assumes, because a perpetuity is a long-horizon claim.
BASE_SPECIFICATION = "5-year monthly"

# CAPM inputs. Both carried over unchanged from the Lab 06 WACC build so the
# only thing that moves in the comparison below is beta itself.
RISK_FREE = 0.04944          # 10-year US Treasury, 2026-09-10 (Lab 06 input)
EQUITY_RISK_PREMIUM = 0.05   # assumption: long-run US ERP (Lab 06 input)
LAB06_BETA = 2.217           # provider beta used in nvidia/dcf.py WACC

# Beta is estimated on returns in excess of the risk-free rate, which is what
# CAPM is written in. The annual rate is de-annualized to the sampling
# frequency using these period counts.
PERIODS_PER_YEAR = {"daily": 252, "weekly": 52, "monthly": 12}

# 95% interval from the normal approximation. Every window here has enough
# observations that the t-distribution correction is immaterial; with 24
# monthly observations it would not be, which is why the observation count is
# printed beside every estimate.
CONFIDENCE_Z = 1.96


# ---------------------------------------------------------------------------
# DATA LAYER -- fetch and cache only, no financial calculation
# ---------------------------------------------------------------------------


def fetch_prices():
    """Download adjusted closes for the stock and the index, and cache them.

    auto_adjust=True returns prices already adjusted for splits and dividends.
    That matters twice over here: NVIDIA's 10-for-1 split in June 2024 would
    otherwise show up as a -90% return, and an unadjusted series would drop
    the dividend component of the market's return.
    """
    import pandas as pd
    import yfinance as yf

    raw = yf.download(
        [TICKER, MARKET_TICKER],
        start=HISTORY_START.isoformat(),
        end=(AS_OF + dt.timedelta(days=1)).isoformat(),  # yfinance end is exclusive
        auto_adjust=True,
        progress=False,
    )
    closes = raw["Close"][[TICKER, MARKET_TICKER]].dropna()
    if closes.empty:
        raise RuntimeError("yfinance returned no overlapping price history.")

    DATA_DIR.mkdir(exist_ok=True)
    frame = pd.DataFrame({
        "date": closes.index.strftime("%Y-%m-%d"),
        "stock": closes[TICKER].to_numpy(),
        "market": closes[MARKET_TICKER].to_numpy(),
    })
    frame.to_csv(PRICE_CACHE, index=False)
    return load_cached_prices()


def load_cached_prices():
    """Read the cached CSV into a list of (date, stock price, market price)."""
    rows = []
    with open(PRICE_CACHE, newline="") as handle:
        for record in csv.DictReader(handle):
            rows.append((
                dt.date.fromisoformat(record["date"]),
                float(record["stock"]),
                float(record["market"]),
            ))
    rows.sort(key=lambda row: row[0])
    return rows


def get_prices(refresh=False):
    """Use the cache when it exists; fetch only when it does not."""
    if refresh or not PRICE_CACHE.exists():
        return fetch_prices()
    return load_cached_prices()


# ---------------------------------------------------------------------------
# ANALYSIS LAYER -- every financial and statistical calculation lives here
# ---------------------------------------------------------------------------


def resample(prices, frequency):
    """Keep the last observation of each day, ISO week, or calendar month.

    Sampling frequency is a real choice, not housekeeping. Daily returns give
    the most observations but pick up microstructure noise and the fact that
    NVIDIA and the index do not stop trading at exactly the same instant, both
    of which bias the slope downward. Monthly returns are cleaner per
    observation but leave only 60 of them in five years.
    """
    if frequency == "daily":
        return list(prices)
    if frequency == "weekly":
        def key(date):
            return date.isocalendar()[:2]        # (ISO year, ISO week)
    elif frequency == "monthly":
        def key(date):
            return (date.year, date.month)
    else:
        raise ValueError("Unknown frequency: {}".format(frequency))

    last_of_period = {}
    for row in prices:
        last_of_period[key(row[0])] = row        # later rows overwrite earlier
    return [last_of_period[period] for period in sorted(last_of_period)]


def simple_returns(prices):
    """Period-over-period percentage change, as (date, r_stock, r_market).

    Simple returns, not log returns. CAPM is written in simple returns and
    portfolio returns aggregate linearly in them; the difference is negligible
    at these magnitudes but the convention should be stated, not assumed.
    """
    returns = []
    for previous, current in zip(prices, prices[1:]):
        returns.append((
            current[0],
            current[1] / previous[1] - 1.0,
            current[2] / previous[2] - 1.0,
        ))
    return returns


def excess_returns(returns, frequency, risk_free_annual):
    """Subtract the per-period risk-free rate from both return series.

    CAPM prices excess returns, so this is the specification the model calls
    for. With a CONSTANT risk-free rate it cannot change the slope at all:
    subtracting the same number from every observation shifts each series'
    mean by that same number, so every deviation from the mean -- and
    therefore the covariance, the variance, and their ratio -- is untouched.
    The step earns its place only when the risk-free rate varies period to
    period, which is the more defensible build. It is kept here so the
    specification is explicit, and the report prints both to prove the point
    rather than assert it.
    """
    periods = PERIODS_PER_YEAR[frequency]
    # Geometric de-annualization: compounding the per-period rate `periods`
    # times must return the annual rate. Dividing by 252 would not.
    per_period = (1.0 + risk_free_annual) ** (1.0 / periods) - 1.0
    return [(date, r_i - per_period, r_m - per_period)
            for date, r_i, r_m in returns]


def window(returns, as_of, years):
    """Keep only returns dated within `years` before the as-of date."""
    try:
        start = as_of.replace(year=as_of.year - years)
    except ValueError:                           # 29 February
        start = as_of.replace(year=as_of.year - years, day=28)
    return [row for row in returns if start <= row[0] <= as_of]


def mean(values):
    return sum(values) / len(values)


def regress_beta(returns):
    """Ordinary least squares slope of stock returns on market returns.

    This is the definition of beta. Everything else is interpretation.

        beta = sum((r_m - mean_m) * (r_i - mean_i)) / sum((r_m - mean_m)^2)

    which is the sample covariance over the sample variance of the market --
    the (n-1) denominators cancel, so they are never computed here.

    Returns the slope, the intercept (Jensen's alpha, per period), R-squared,
    the standard error of the slope, and the observation count.
    """
    if len(returns) < 3:
        raise ValueError("Need at least 3 observations to estimate a slope.")

    market = [row[2] for row in returns]
    stock = [row[1] for row in returns]
    mean_market, mean_stock = mean(market), mean(stock)

    deviations_market = [value - mean_market for value in market]
    deviations_stock = [value - mean_stock for value in stock]

    cross_product = sum(m * s for m, s in zip(deviations_market, deviations_stock))
    market_squares = sum(m * m for m in deviations_market)
    if market_squares == 0.0:
        raise ValueError("Market returns have zero variance; beta undefined.")

    beta = cross_product / market_squares
    alpha = mean_stock - beta * mean_market

    # Residual = the part of NVIDIA's return the market does not explain. This
    # is the diversifiable risk CAPM says investors are not paid to hold.
    residuals = [s - alpha - beta * m for m, s in zip(market, stock)]
    sum_squared_residuals = sum(e * e for e in residuals)
    total_sum_squares = sum(s * s for s in deviations_stock)

    r_squared = (1.0 - sum_squared_residuals / total_sum_squares
                 if total_sum_squares > 0 else float("nan"))

    # Two degrees of freedom are spent estimating the slope and the intercept.
    residual_variance = sum_squared_residuals / (len(returns) - 2)
    standard_error = math.sqrt(residual_variance / market_squares)

    return {
        "beta": beta,
        "alpha": alpha,
        "r_squared": r_squared,
        "standard_error": standard_error,
        "observations": len(returns),
    }


def decompose_beta(returns):
    """Beta as correlation times the ratio of standard deviations.

        beta = corr(r_i, r_m) * (sigma_i / sigma_m)

    Algebraically identical to the regression slope, but it separates the two
    economic drivers. A stock can be twice as volatile as the market and still
    carry a beta near 1 if only half that volatility moves with the market.
    Volatility is not beta, and this is where that becomes visible.
    """
    market = [row[2] for row in returns]
    stock = [row[1] for row in returns]
    mean_market, mean_stock = mean(market), mean(stock)

    deviations_market = [value - mean_market for value in market]
    deviations_stock = [value - mean_stock for value in stock]
    degrees_of_freedom = len(returns) - 1

    variance_market = sum(m * m for m in deviations_market) / degrees_of_freedom
    variance_stock = sum(s * s for s in deviations_stock) / degrees_of_freedom
    covariance = sum(m * s for m, s in zip(deviations_market,
                                           deviations_stock)) / degrees_of_freedom

    sigma_market = math.sqrt(variance_market)
    sigma_stock = math.sqrt(variance_stock)
    correlation = covariance / (sigma_stock * sigma_market)

    return {
        "sigma_stock": sigma_stock,
        "sigma_market": sigma_market,
        "volatility_ratio": sigma_stock / sigma_market,
        "correlation": correlation,
        "beta": correlation * sigma_stock / sigma_market,
    }


def blume_adjusted(raw_beta):
    """Shrink a raw beta one third of the way toward 1.0.

        adjusted = 0.33 + 0.67 * raw

    Blume's finding is empirical, not theoretical: betas estimated in one
    period tend to sit closer to 1.0 in the next, because businesses diversify
    and mean-revert. A DCF discounts twenty-plus years of cash flow, so the
    input wanted is the beta that will hold over that horizon, not the one
    that held over the sample. For a high-beta name this cuts the estimate
    materially, which is exactly why it has to be disclosed rather than
    silently applied.
    """
    return 0.33 + 0.67 * raw_beta


def annualize_volatility(period_sigma, frequency):
    """Scale a per-period standard deviation to annual, by the square root of time."""
    return period_sigma * math.sqrt(PERIODS_PER_YEAR[frequency])


def cost_of_equity(beta, risk_free=RISK_FREE, premium=EQUITY_RISK_PREMIUM):
    """CAPM required return on equity: r_f + beta * (equity risk premium)."""
    return risk_free + beta * premium


def estimate(prices, years, frequency, as_of=AS_OF, use_excess=True):
    """Run one full specification end to end: resample, return, window, regress."""
    sampled = resample(prices, frequency)
    returns = simple_returns(sampled)
    if use_excess:
        returns = excess_returns(returns, frequency, RISK_FREE)
    windowed = window(returns, as_of, years)
    result = regress_beta(windowed)
    result["decomposition"] = decompose_beta(windowed)
    result["frequency"] = frequency
    result["years"] = years
    result["first_date"] = windowed[0][0]
    result["last_date"] = windowed[-1][0]
    return result


# ---------------------------------------------------------------------------
# INTERFACE LAYER -- printing only, no financial computation
# ---------------------------------------------------------------------------


def report_header(prices):
    print("Equity Beta -- {}".format(COMPANY))
    print("=" * 74)
    print("Market proxy: {} ({})".format(MARKET_LABEL, MARKET_TICKER))
    print("Price history: {} to {}  ({:,} trading days, adjusted closes)".format(
        prices[0][0], prices[-1][0], len(prices)))
    print("Returns measured in excess of a {:.3%} annual risk-free rate.".format(
        RISK_FREE))
    print("Source: yfinance, cached at data/{}".format(PRICE_CACHE.name))


def report_specifications(results):
    print()
    print("Beta under five defensible specifications")
    print("-" * 74)
    print("{:<16}{:>5}{:>9}{:>9}{:>18}{:>8}".format(
        "Specification", "Obs", "Beta", "Std err", "95% interval", "R-sq"))
    for label, result in results:
        low = result["beta"] - CONFIDENCE_Z * result["standard_error"]
        high = result["beta"] + CONFIDENCE_Z * result["standard_error"]
        print("{:<16}{:>5d}{:>9.3f}{:>9.3f}{:>18}{:>8.3f}".format(
            label, result["observations"], result["beta"],
            result["standard_error"],
            "{:.2f} to {:.2f}".format(low, high), result["r_squared"]))

    betas = [result["beta"] for _, result in results]
    print("-" * 74)
    print("Spread across specifications: {:.3f} to {:.3f}  (range {:.3f})".format(
        min(betas), max(betas), max(betas) - min(betas)))
    print("Same stock, same index, same day. The spread is the method, not the")
    print("market -- which is why a single point estimate would overstate what")
    print("this evidence supports.")


def report_decomposition(label, result):
    parts = result["decomposition"]
    frequency = result["frequency"]
    print()
    print("Where the base-case beta comes from  [{}]".format(label))
    print("-" * 74)
    print("  Annualized volatility, NVDA{:>45.2%}".format(
        annualize_volatility(parts["sigma_stock"], frequency)))
    print("  Annualized volatility, {}{:>41.2%}".format(
        MARKET_LABEL, annualize_volatility(parts["sigma_market"], frequency)))
    print("  Volatility ratio  (sigma_i / sigma_m){:>35.3f}".format(
        parts["volatility_ratio"]))
    print("  Correlation with the market{:>45.3f}".format(parts["correlation"]))
    print("  Beta = correlation x volatility ratio{:>35.3f}".format(parts["beta"]))
    print()
    print("  NVDA is about {:.1f}x as volatile as the index, but only {:.0%} of".format(
        parts["volatility_ratio"], parts["correlation"]))
    print("  that volatility moves with it. Beta prices the second part only;")
    print("  the rest is diversifiable and, under CAPM, unpaid.")
    print("  R-squared of {:.3f} says {:.0f}% of NVDA's variance is market-driven.".format(
        result["r_squared"], result["r_squared"] * 100.0))


def report_raw_versus_excess(prices, label, years, frequency):
    excess = estimate(prices, years, frequency, use_excess=True)["beta"]
    raw = estimate(prices, years, frequency, use_excess=False)["beta"]
    print()
    print("Specification check: excess returns versus raw returns  [{}]".format(label))
    print("-" * 74)
    print("  Beta on excess returns (CAPM form){:>38.4f}".format(excess))
    print("  Beta on raw returns{:>53.4f}".format(raw))
    print("  Difference{:>62.4f}".format(excess - raw))
    print("  Exactly zero, and it has to be: a constant subtracted from both")
    print("  series leaves every deviation from the mean unchanged, so the")
    print("  slope cannot move. A time-varying risk-free rate would change")
    print("  this -- a constant one never can.")


def report_cost_of_equity(label, base_beta):
    adjusted = blume_adjusted(base_beta)
    print()
    print("What beta does to the Lab 06 valuation")
    print("-" * 74)
    print("  CAPM: cost of equity = {:.3%} + beta x {:.2%}".format(
        RISK_FREE, EQUITY_RISK_PREMIUM))
    print()
    print("  {:<42}{:>9}{:>16}".format("Beta source", "Beta", "Cost of equity"))
    rows = [
        ("Lab 06 provider beta (used in dcf.py)", LAB06_BETA),
        ("This estimate, {}".format(label), base_beta),
        ("This estimate, Blume-adjusted", adjusted),
    ]
    for source, beta in rows:
        print("  {:<42}{:>9.3f}{:>16.2%}".format(
            source, beta, cost_of_equity(beta)))

    betas = [beta for _, beta in rows]
    spread = cost_of_equity(max(betas)) - cost_of_equity(min(betas))
    print()
    print("  That is a {:.0f} basis point swing in the discount rate from the".format(
        spread * 10000))
    print("  beta choice alone. NVIDIA carries almost no debt, so WACC sits")
    print("  within a few basis points of cost of equity and inherits all of it.")
    print()
    print("  Conclusion to carry forward: report the DCF across this beta range,")
    print("  not at one rate. A point estimate here is false precision.")


# ---------------------------------------------------------------------------
# SELF-CHECK -- the arithmetic before the data
# ---------------------------------------------------------------------------
# Same discipline as the Lab 06 DCF: prove the estimator is right on inputs
# whose answer is known independently, before trusting it on NVIDIA.

# Hand-worked five-observation case. Market returns x, stock returns y:
#   x = [ 0.01, -0.02,  0.03,  0.00, -0.01]   mean =  0.002
#   y = [ 0.02, -0.03,  0.05,  0.01, -0.02]   mean =  0.006
#   sum of cross-products            = 0.00244
#   sum of squared market deviations = 0.00148
#   beta = 0.00244 / 0.00148 = 1.648649
HAND_CHECK_RETURNS = [
    (dt.date(2026, 1, 1), 0.02, 0.01),
    (dt.date(2026, 1, 2), -0.03, -0.02),
    (dt.date(2026, 1, 3), 0.05, 0.03),
    (dt.date(2026, 1, 4), 0.01, 0.00),
    (dt.date(2026, 1, 5), -0.02, -0.01),
]
HAND_CHECK_BETA = 0.00244 / 0.00148


def run_self_check(prices):
    """Four checks the estimator must pass before any NVIDIA number is believed."""
    print()
    print("Self-check")
    print("=" * 74)
    passed = True

    # 1. Hand-worked slope. Catches an error anywhere in the regression.
    got = regress_beta(HAND_CHECK_RETURNS)["beta"]
    ok = abs(got - HAND_CHECK_BETA) < 1e-9
    passed &= ok
    print("Hand-worked 5-point slope    expected {:>9.6f}  got {:>9.6f}   {}".format(
        HAND_CHECK_BETA, got, "OK" if ok else "MISMATCH"))

    # 2. The market against itself must have beta exactly 1 and R-squared 1.
    self_returns = [(date, r_m, r_m) for date, _, r_m in HAND_CHECK_RETURNS]
    identity = regress_beta(self_returns)
    ok = (abs(identity["beta"] - 1.0) < 1e-12
          and abs(identity["r_squared"] - 1.0) < 1e-12)
    passed &= ok
    print("Market regressed on itself   expected {:>9.6f}  got {:>9.6f}   {}".format(
        1.0, identity["beta"], "OK" if ok else "MISMATCH"))

    # 3. Doubling every stock return must double beta exactly -- the estimator
    #    has to be linear in the dependent variable, or it is not a slope.
    doubled = [(date, 2.0 * r_i, r_m) for date, r_i, r_m in HAND_CHECK_RETURNS]
    got = regress_beta(doubled)["beta"]
    ok = abs(got - 2.0 * HAND_CHECK_BETA) < 1e-9
    passed &= ok
    print("Doubled stock returns        expected {:>9.6f}  got {:>9.6f}   {}".format(
        2.0 * HAND_CHECK_BETA, got, "OK" if ok else "MISMATCH"))

    # 4. On the real data, the two independent formulas must agree. The
    #    regression path and the correlation x volatility-ratio path share no
    #    code, so agreement to twelve decimals is evidence both are right.
    live = estimate(prices, 5, "monthly")
    difference = abs(live["beta"] - live["decomposition"]["beta"])
    ok = difference < 1e-12
    passed &= ok
    print("Regression vs decomposition  agree to  {:>9.2e}  on live data  {}".format(
        difference, "OK" if ok else "MISMATCH"))

    print("=" * 74)
    print("SELF-CHECK {}".format("PASSED" if passed else "FAILED"))
    return passed


# ---------------------------------------------------------------------------


def main():
    refresh = "--refresh" in sys.argv
    try:
        prices = get_prices(refresh=refresh)
    except Exception as error:               # noqa: BLE001 -- reported, not hidden
        print("Could not load prices: {}".format(error))
        print("Run once with a network connection to build the cache:")
        print("    python beta.py --refresh")
        return 1

    report_header(prices)

    results = [(label, estimate(prices, years, frequency))
               for label, years, frequency in SPECIFICATIONS]
    report_specifications(results)

    base = dict(results)[BASE_SPECIFICATION]
    report_decomposition(BASE_SPECIFICATION, base)

    base_spec = next(spec for spec in SPECIFICATIONS
                     if spec[0] == BASE_SPECIFICATION)
    report_raw_versus_excess(prices, *base_spec)

    report_cost_of_equity(BASE_SPECIFICATION, base["beta"])

    return 0 if run_self_check(prices) else 1


if __name__ == "__main__":
    sys.exit(main())
