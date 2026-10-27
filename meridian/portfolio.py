"""Lab 14 — Meridian Foundation Reserve: portfolio risk engine.

Prices three baseline portfolios (benchmark, equal weight, inverse volatility) from
course-authored training values: expected return, volatility and correlation per sleeve.
Standard library only. Run: python portfolio.py
"""

import csv
import io
import math
import statistics

# ---------------------------------------------------------------- inputs (edit here)
# Course-authored training values, not market estimates. Percent per year.

SLEEVES = ["Treasury bills", "Treasury 10-year note", "Investment-grade bond fund",
           "Global equity index fund"]

EXPECTED_RETURN = {   # percent per year
    "Treasury bills":             3.5,
    "Treasury 10-year note":      4.3,
    "Investment-grade bond fund": 5.0,
    "Global equity index fund":   8.0,
}

VOLATILITY = {        # percent per year
    "Treasury bills":             0.5,
    "Treasury 10-year note":      7.0,
    "Investment-grade bond fund": 6.0,
    "Global equity index fund":  16.0,
}

# Rows and columns in SLEEVES order: bills, 10-year, IG bonds, equity.
CORRELATION = [
    [1.00,  0.10, 0.05,  0.00],
    [0.10,  1.00, 0.80, -0.10],
    [0.05,  0.80, 1.00,  0.25],
    [0.00, -0.10, 0.25,  1.00],
]

# CPI + 4%, with CPI taken as 2.5% (a labelled estimate, not a forecast).
CPI_ESTIMATE = 2.5
OBJECTIVE_RETURN = CPI_ESTIMATE + 4.0   # 6.5% per year

RESERVE_ELIGIBLE = {"Treasury bills", "Treasury 10-year note"}   # Lab 13, S3

TOLERANCE = 1e-9


# ---------------------------------------------------------------- checks

def validate_correlation(corr):
    """Stop with a clear message if the correlation table is not square, symmetric and within [-1, 1]."""
    n = len(corr)
    for i, row in enumerate(corr):
        if len(row) != n:
            raise SystemExit(f"Refusing to run: correlation row {i + 1} has {len(row)} values, expected {n}.")
        for j, value in enumerate(row):
            if not -1.0 <= value <= 1.0:
                raise SystemExit(f"Refusing to run: correlation ({i + 1},{j + 1}) = {value} is outside -1 to 1.")
            if abs(value - corr[j][i]) > TOLERANCE:
                raise SystemExit(f"Refusing to run: correlation table is not symmetric at "
                                 f"({i + 1},{j + 1}) = {value} vs ({j + 1},{i + 1}) = {corr[j][i]}.")
        if abs(row[i] - 1.0) > TOLERANCE:
            raise SystemExit(f"Refusing to run: diagonal correlation ({i + 1},{i + 1}) = {row[i]}, must be 1.")


# ---------------------------------------------------------------- calculations

def covariance_matrix(vols, corr):
    """Covariance(i, j) = correlation(i, j) x vol(i) x vol(j), with vols as decimals."""
    n = len(vols)
    return [[corr[i][j] * vols[i] * vols[j] for j in range(n)] for i in range(n)]


def portfolio_return(weights, returns):
    """Expected return = sum of weight x return (same units as returns)."""
    return sum(w * r for w, r in zip(weights, returns))


def portfolio_volatility(weights, cov):
    """Volatility = sqrt(sum over i, j of w_i x w_j x cov(i, j)); includes every correlation term."""
    n = len(weights)
    variance = sum(weights[i] * weights[j] * cov[i][j] for i in range(n) for j in range(n))
    return math.sqrt(variance)


def reserve_weight(weights, sleeves, eligible):
    """Total weight in reserve-eligible sleeves."""
    return sum(w for w, s in zip(weights, sleeves) if s in eligible)


def benchmark_weights(sleeves):
    """S4 benchmark: 40% investment-grade bond fund, 60% global equity index fund."""
    target = {"Investment-grade bond fund": 0.40, "Global equity index fund": 0.60}
    return [target.get(s, 0.0) for s in sleeves]


def equal_weights(sleeves):
    """Same weight in every sleeve."""
    return [1.0 / len(sleeves)] * len(sleeves)


def inverse_volatility_weights(vols):
    """Each weight = (1 / vol) / sum of (1 / vol), so weights sum to 100%."""
    inverse = [1.0 / v for v in vols]
    total = sum(inverse)
    return [x / total for x in inverse]


def summarize(weights, sleeves, returns, vols, corr, eligible, objective):
    """Return a dict of the portfolio's weights, return, volatility, reserve weight and objective test.

    Inputs in percent; results in percent.
    """
    cov = covariance_matrix([v / 100 for v in vols], corr)
    exp_return = portfolio_return(weights, returns)
    vol = portfolio_volatility(weights, cov) * 100
    return {
        "weights_pct": [w * 100 for w in weights],
        "return_pct": exp_return,
        "volatility_pct": vol,
        "reserve_pct": reserve_weight(weights, sleeves, eligible) * 100,
        "meets_objective": exp_return >= objective - TOLERANCE,
    }


def baselines(sleeves=SLEEVES, returns_by=EXPECTED_RETURN, vols_by=VOLATILITY):
    """The three Lab 14 baseline portfolios as {name: weights (decimals)}."""
    vols = [vols_by[s] for s in sleeves]
    return {
        "Benchmark": benchmark_weights(sleeves),
        "Equal weight": equal_weights(sleeves),
        "Inverse volatility": inverse_volatility_weights(vols),
    }


# ---------------------------------------------------------------- Lab 15: search and estimation

def all_mixes(n_assets, step=5):
    """Every long-only mix of n_assets in `step`-point increments, as decimal weights summing to 1."""
    units = 100 // step

    def split(remaining, slots):
        if slots == 1:
            yield [remaining]
            return
        for first in range(remaining + 1):
            for rest in split(remaining - first, slots - 1):
                yield [first] + rest

    for mix in split(units, n_assets):
        yield [u * step / 100 for u in mix]


def lowest_risk_mix(sleeves, returns, vols, corr, eligible, objective, reserve_min, step=5):
    """Lowest-volatility long-only mix with return >= objective and reserve weight >= reserve_min.

    returns, vols, objective, reserve_min in percent. Returns the summarize() dict, or None if no
    mix meets both rules.
    """
    validate_correlation(corr)
    cov = covariance_matrix([v / 100 for v in vols], corr)
    best_weights, best_vol = None, None
    for weights in all_mixes(len(sleeves), step):
        if portfolio_return(weights, returns) < objective - TOLERANCE:
            continue
        if reserve_weight(weights, sleeves, eligible) * 100 < reserve_min - TOLERANCE:
            continue
        vol = portfolio_volatility(weights, cov)
        if best_vol is None or vol < best_vol - TOLERANCE:
            best_weights, best_vol = weights, vol
    if best_weights is None:
        return None
    return summarize(best_weights, sleeves, returns, vols, corr, eligible, objective)


def estimate_from_prices(csv_text, last_months=None):
    """Estimate inputs from monthly prices (date first, oldest first, one column per ticker).

    Monthly simple returns; annual return = mean x 12, annual volatility = SD x sqrt(12), both in
    percent; correlations of monthly returns. last_months=36 keeps only the last 36 monthly returns.
    History, not a forecast: label the results `estimate`.
    """
    rows = [r for r in csv.reader(io.StringIO(csv_text)) if r]
    tickers = [t.strip() for t in rows[0][1:]]
    prices = [[float(x) for x in r[1:]] for r in rows[1:]]
    monthly = [[prices[t][k] / prices[t - 1][k] - 1 for k in range(len(tickers))]
               for t in range(1, len(prices))]
    if last_months:
        monthly = monthly[-last_months:]
    if len(monthly) < 3:
        raise ValueError("Need at least three monthly returns to estimate.")
    columns = list(zip(*monthly))
    returns = [statistics.mean(c) * 12 * 100 for c in columns]
    vols = [statistics.stdev(c) * math.sqrt(12) * 100 for c in columns]
    corr = [[1.0 if i == j else statistics.correlation(columns[i], columns[j])
             for j in range(len(tickers))] for i in range(len(tickers))]
    first_date, last_date = rows[1][0], rows[-1][0]
    return {"tickers": tickers, "returns": returns, "vols": vols, "corr": corr,
            "months": len(monthly), "first_price_date": first_date, "last_price_date": last_date}


# ---------------------------------------------------------------- report

def main():
    validate_correlation(CORRELATION)
    returns = [EXPECTED_RETURN[s] for s in SLEEVES]
    vols = [VOLATILITY[s] for s in SLEEVES]

    print(f"Objective: CPI {CPI_ESTIMATE:.1f}% (estimate) + 4.0% = {OBJECTIVE_RETURN:.1f}% a year")
    print("Weights order: bills / 10-year / IG bonds / equity\n")
    header = f"{'Portfolio':<20}{'Weights (%)':<28}{'Return':>8}{'Vol':>8}{'Reserve':>9}  Meets {OBJECTIVE_RETURN:.1f}%?"
    print(header)
    print("-" * len(header))
    for name, weights in baselines().items():
        r = summarize(weights, SLEEVES, returns, vols, CORRELATION, RESERVE_ELIGIBLE, OBJECTIVE_RETURN)
        w_text = " / ".join(f"{w:.1f}" for w in r["weights_pct"])
        print(f"{name:<20}{w_text:<28}{r['return_pct']:>8.2f}{r['volatility_pct']:>8.2f}"
              f"{r['reserve_pct']:>9.1f}  {'yes' if r['meets_objective'] else 'no'}")


if __name__ == "__main__":
    main()
