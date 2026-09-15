"""Comparable-company P/E valuation -- Asbury Automotive training case.

FIN 43900 (AI in Finance, Purdue), Lab 07 -- Session 7.
Author: Drew Scheiderer.

The question this answers: what would one share of the target be worth if
investors priced its earnings the way they price comparable companies'
earnings?

Price-to-earnings (P/E) divides price per share by annual earnings per share.
Dividing by EPS puts companies of very different size on a common basis --
dollars of share price per dollar of annual earnings -- so a $421 stock and a
$169 stock become directly comparable. Applying a peer's multiple to the
target's own EPS converts that comparison into a price for the target.

IMPORTANT -- P/E is an EQUITY multiple. Price per share is already what is left
for shareholders after lenders are paid, so a P/E-derived value must NEVER have
cash added or debt subtracted. That bridge belongs to enterprise-value methods
such as the FCFF discounted cash flow, where the cash flow being discounted is
pre-financing and therefore belongs to lenders and shareholders together.

Standard library only. Run with: python comps.py
"""

import statistics

# ---------------------------------------------------------------------------
# INPUTS -- the only block intended to be edited
# ---------------------------------------------------------------------------
# Frozen Lab 07 case inputs: December 31, 2024 closing prices paired with
# FY2024 total GAAP diluted EPS (not management's adjusted EPS). Price and EPS
# must sit on the same stock-split basis or the multiple is meaningless.

TARGET = {
    "ticker": "ABG",
    "name": "Asbury Automotive",
    "price": 243.03,
    "eps": 21.50,
}

# Peers are dictionaries in the same shape. A peer with a missing or
# nonpositive price or EPS is reported as not meaningful rather than silently
# dropped, so the exclusion is always visible.
PEERS = [
    {"ticker": "AN", "name": "AutoNation", "price": 169.84, "eps": 16.92},
    {"ticker": "GPI", "name": "Group 1 Automotive", "price": 421.48, "eps": 36.81},
]

NOT_MEANINGFUL = "not meaningful"


# ---------------------------------------------------------------------------
# ANALYSIS LAYER -- every calculation lives here
# ---------------------------------------------------------------------------


def is_usable(company):
    """True when the company can support a positive P/E multiple.

    A negative or zero EPS does not produce a meaningful positive multiple: a
    loss-making company divided into a positive price gives a negative number
    that looks like a multiple but means nothing. A missing input cannot be
    valued either.
    """
    price = company.get("price")
    eps = company.get("eps")
    if price is None or eps is None:
        return False
    return price > 0 and eps > 0


def price_earnings(company):
    """P/E = price per share / annual diluted EPS. Returns None if unusable."""
    if not is_usable(company):
        return None
    return company["price"] / company["eps"]


def prepare_peers(peers, target):
    """Deduplicate peers, drop the target, and split usable from unusable.

    The target is excluded from its own peer set: a company cannot be evidence
    for how the market prices itself. Duplicates are removed because repeating
    one company would silently double its weight in the median.
    """
    seen = set()
    deduplicated = []
    for peer in peers:
        key = peer["ticker"].strip().upper()
        if key == target["ticker"].strip().upper():
            continue
        if key in seen:
            continue
        seen.add(key)
        deduplicated.append(peer)

    usable = [p for p in deduplicated if is_usable(p)]
    unusable = [p for p in deduplicated if not is_usable(p)]
    return usable, unusable


def implied_price(multiple, target_eps):
    """Apply a peer multiple to the target's own EPS.

    This is the step that turns a comparison into a valuation: the peer supplies
    the multiple, the target supplies the earnings.
    """
    if multiple is None or target_eps is None or target_eps <= 0:
        return None
    return multiple * target_eps


def summarize(usable_peers, target_eps):
    """Minimum, median and maximum peer multiples with their implied prices.

    Full precision is retained here; rounding happens only at the point of
    display, so no downstream figure inherits a rounding error.
    """
    multiples = sorted(price_earnings(p) for p in usable_peers)
    if not multiples:
        return None

    median_multiple = statistics.median(multiples)
    return {
        "count": len(multiples),
        "min_multiple": multiples[0],
        "median_multiple": median_multiple,
        "max_multiple": multiples[-1],
        "min_price": implied_price(multiples[0], target_eps),
        "median_price": implied_price(median_multiple, target_eps),
        "max_price": implied_price(multiples[-1], target_eps),
    }


def leave_one_out(usable_peers, target_eps):
    """Remove each peer in turn and report the effect on the median estimate.

    This is how a 'qualify' decision is tested rather than merely asserted: it
    shows how much of the estimate depends on any single peer. The dollar
    change is computed from unrounded values.
    """
    baseline = summarize(usable_peers, target_eps)
    baseline_price = baseline["median_price"] if baseline else None

    results = []
    for removed in usable_peers:
        remaining = [p for p in usable_peers if p is not removed]
        remaining_summary = summarize(remaining, target_eps)
        if remaining_summary is None:
            results.append({"removed": removed, "summary": None, "change": None})
            continue
        change = None
        if remaining_summary["median_price"] is not None and baseline_price is not None:
            change = remaining_summary["median_price"] - baseline_price
        results.append({
            "removed": removed,
            "summary": remaining_summary,
            "change": change,
        })
    return results


# ---------------------------------------------------------------------------
# INTERFACE LAYER -- formatting only, no calculation
# ---------------------------------------------------------------------------


def format_multiple(value):
    """Multiples to six decimals, per the lab's display convention."""
    return NOT_MEANINGFUL if value is None else "{:.6f}x".format(value)


def format_price(value):
    """Prices to cents."""
    return NOT_MEANINGFUL if value is None else "${:,.2f}".format(value)


def format_change(value):
    """Signed dollar change to cents."""
    return NOT_MEANINGFUL if value is None else "{}${:,.2f}".format(
        "-" if value < 0 else "+", abs(value))


def report_inputs(target, usable, unusable):
    print("Comparable-Company P/E Valuation")
    print("=" * 66)
    print("Target: {} ({})   price {}   diluted EPS {}".format(
        target["name"], target["ticker"],
        format_price(target["price"]), format_price(target["eps"])))

    target_multiple = price_earnings(target)
    print("Target's own observed P/E: {}  (context only -- never in the peer set)"
          .format(format_multiple(target_multiple)))
    print("-" * 66)

    print("Peer multiples")
    for peer in usable:
        print("  {:<22} {:>12} / {:>8}  =  {}".format(
            "{} ({})".format(peer["name"], peer["ticker"]),
            format_price(peer["price"]), format_price(peer["eps"]),
            format_multiple(price_earnings(peer))))
    for peer in unusable:
        print("  {:<22} {}: missing or nonpositive price or EPS".format(
            "{} ({})".format(peer["name"], peer["ticker"]), NOT_MEANINGFUL))


def report_range(summary, target):
    print("-" * 66)
    if summary is None:
        print("No usable peers. No implied valuation can be produced.")
        return

    if target["eps"] is None or target["eps"] <= 0:
        print("Target EPS is missing or nonpositive, so every implied price is")
        print("{}. A P/E comparison cannot value negative earnings.".format(NOT_MEANINGFUL))
        return

    if summary["count"] == 1:
        print("One usable peer: reference estimate only, not a range.")
        print("  Peer multiple          {}".format(format_multiple(summary["median_multiple"])))
        print("  Implied price          {}".format(format_price(summary["median_price"])))
        print()
        print("A single observation cannot bracket a value. Treat this as one")
        print("reference point, not a valuation range.")
        return

    print("Implied value for {} at peer multiples".format(target["ticker"]))
    print("  Minimum peer P/E       {:>14}   implies {}".format(
        format_multiple(summary["min_multiple"]), format_price(summary["min_price"])))
    print("  Median peer P/E        {:>14}   implies {}".format(
        format_multiple(summary["median_multiple"]), format_price(summary["median_price"])))
    print("  Maximum peer P/E       {:>14}   implies {}".format(
        format_multiple(summary["max_multiple"]), format_price(summary["max_price"])))
    print()
    print("  Peer-implied range     {} to {}".format(
        format_price(summary["min_price"]), format_price(summary["max_price"])))
    print("  At the peer median     {}".format(format_price(summary["median_price"])))

    if summary["count"] == 2:
        print()
        print("  Note: with two peers the median is the midpoint of the two")
        print("  multiples and is sensitive to both. This is a small comparison,")
        print("  not a confidence interval.")


def report_leave_one_out(results, summary):
    print("-" * 66)
    print("Leave-one-peer-out: how much rests on any single peer")
    if summary is None or not results:
        print("  No usable peers to remove.")
        return

    baseline = summary["median_price"]
    print("  Full-peer median estimate: {}".format(format_price(baseline)))
    print()
    for result in results:
        removed = result["removed"]
        label = "Remove {} ({})".format(removed["name"], removed["ticker"])
        if result["summary"] is None:
            print("  {:<34} no peers remain, no estimate".format(label))
            continue
        remaining = result["summary"]
        kind = "reference estimate" if remaining["count"] == 1 else "median estimate"
        print("  {:<34} {} {}   change {}".format(
            label, kind, format_price(remaining["median_price"]),
            format_change(result["change"])))


def report_method_note():
    print("-" * 66)
    print("Method note: P/E is an equity multiple. These implied prices are")
    print("already values per share to shareholders -- no cash is added and no")
    print("debt is subtracted. That bridge belongs to enterprise-value methods")
    print("such as an FCFF DCF, not here.")


def main():
    usable, unusable = prepare_peers(PEERS, TARGET)
    summary = summarize(usable, TARGET["eps"])

    report_inputs(TARGET, usable, unusable)
    report_range(summary, TARGET)
    report_leave_one_out(leave_one_out(usable, TARGET["eps"]), summary)
    report_method_note()


if __name__ == "__main__":
    main()
