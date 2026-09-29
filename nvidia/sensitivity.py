"""One-at-a-time sensitivity on the NVIDIA pro-forma -- which inputs move the answer.

FIN 43900 (AI in Finance, Purdue), Lab 11 -- Session 11.
Author: Drew Scheiderer.

The question this answers: which assumptions drive NVIDIA's forecast and value, and
what explains their effects?

METHOD. One-at-a-time sensitivity. Each run restores EVERY independent input to base
from a snapshot, changes exactly one of them, rebuilds all five years, and reruns the
accounting checks. One-at-a-time means interactions are not captured -- moving growth
and margin together is not the sum of moving each alone. It ranks drivers; it does not
build scenarios, and it contains no probabilities. A wide span can mean a wide input
range rather than an important input, which is why every conclusion here is stated
"over these ranges".

WHY A SNAPSHOT RATHER THAN SAVE-AND-RESTORE. The Lab 09 sensitivity on Asbury saved the
one constant it was about to change and put it back in a `finally` block. That is enough
when every input is a float. Here four of them are LISTS -- the revenue growth, gross
margin, R&D and SG&A paths -- and a list handed to the engine can be mutated in place by
a careless edit, which would leak into every later run and never announce itself. So
this file snapshots all twenty-four independent inputs up front with a deep copy, and
restores all twenty-four before every single run. A run cannot inherit anything from the
run before it, whether or not the previous run raised.

The engine is imported from proforma.py, not copied. That engine reproduces the filed
FY2026 opening balance sheet and balances to zero in all five years, so every figure
below comes from arithmetic already checked.

Standard library only.

Run with:        cd nvidia && python sensitivity.py
Trace one run:   cd nvidia && python sensitivity.py --trace "<run label>"
Check the rig:   cd nvidia && python sensitivity.py --selftest
"""

import copy
import sys

import proforma


# ---------------------------------------------------------------------------
# THE BASE INPUT SET -- snapshotted once, restored before every run
# ---------------------------------------------------------------------------
# Every INDEPENDENT input the engine reads. Calculated statement totals are not
# listed here and are never overridden: they have to recalculate, or the test is
# not testing a linked model.
INDEPENDENT_INPUTS = [
    "OPENING",
    "REVENUE_GROWTH", "GROSS_MARGIN", "RD_TO_REVENUE", "SGA_TO_GROSS_PROFIT",
    "SBC_TO_REVENUE", "DEPRECIATION_TO_OPENING_PPE", "CAPEX_TO_REVENUE", "TAX_RATE",
    "INVENTORY_DAYS", "SUPPLY_OBLIGATIONS_TO_INVENTORY", "OTHER_WC_TO_REVENUE_CHANGE",
    "MINIMUM_CASH", "REVOLVER_LIMIT", "REVOLVER_RATE", "CASH_YIELD", "DEBT_RATE",
    "DEBT_REPAYMENT", "SHARE_BUYBACK", "DIVIDENDS", "TARGET_CASH",
    "COST_OF_EQUITY", "TERMINAL_GROWTH", "SHARES_OUTSTANDING",
]

# Deep copy, so the lists in the snapshot are not the same objects the engine holds.
BASE_INPUTS = {name: copy.deepcopy(getattr(proforma, name))
               for name in INDEPENDENT_INPUTS}


def restore_base():
    """Put every independent input back to its snapshot value. Deep copy each time."""
    for name, value in BASE_INPUTS.items():
        setattr(proforma, name, copy.deepcopy(value))


# ---------------------------------------------------------------------------
# THE DRIVERS -- my choice, not the AI's. See the Lab 11 write-up.
# ---------------------------------------------------------------------------
# The lab is explicit that the choice of drivers and the width of their ranges are
# mine: "Do not generate company data, choose new ranges, or write my interpretation
# for me." So this block shipped UNSET, and the script refused to run until I filled
# it -- run it with the drivers blanked and it still prints the available inputs and
# exits 2 rather than guessing. The values below are the ones I chose, and both
# ranges are derived from NVIDIA's own history in the write-up.
#
# Both drivers move a uniform +/-2 percentage points on all five forecast years.
# Equal shifts are deliberate: they make the two spans comparable, so the ranking
# is a fact about the model rather than about which range I made wider.
#
# Rules the validator below enforces, because they are the ones a partner is asked
# to check:
#   - `attribute` must name an INDEPENDENT input from the list above, not a
#     calculated total.
#   - `base` must equal what the model actually carries today. If it does not, the
#     range is written against a model that no longer exists.
#   - exactly one attribute moves per run.
#
# UNITS MATTER AND THE VALIDATOR CANNOT CHECK THEM. A move from 71.0% to 72.0% is
# one PERCENTAGE POINT (+0.01 in decimal). A 1 PERCENT increase would be
# 71.0% x 1.01 = 71.71%. Those are different inputs. For a path input (a five-year
# list) state whether the shift applies to every year or only some, and write the
# list out year by year.

PENDING = None      # sentinel: an unfilled field

DRIVERS = [
    {
        "name": "Revenue growth",
        "attribute": "REVENUE_GROWTH",
        "units": "percentage points of annual growth, decimal form (+/-0.02 each year)",
        "years": "all five, FY2027E-FY2031E",
        "reason": ("uniform shift, the same mechanism my Lab 06 reverse DCF applies to this "
                   "same path; +/-2pp matched to the gross margin range so the spans compare"),
        "lower": [0.28, 0.20, 0.14, 0.09, 0.05],
        "base":  [0.30, 0.22, 0.16, 0.11, 0.07],
        "higher": [0.32, 0.24, 0.18, 0.13, 0.09],
    },
    {
        "name": "Gross margin",
        "attribute": "GROSS_MARGIN",
        "units": "percentage points of revenue, decimal form (+/-0.02 each year)",
        "years": "all five, FY2027E-FY2031E",
        "reason": ("observed three-year swing was 3.9pp peak to trough (74.99% FY2025 vs "
                   "71.07% FY2026), so +/-2pp brackets the width the company actually delivered"),
        "lower": [0.690, 0.685, 0.680, 0.675, 0.670],
        "base":  [0.710, 0.705, 0.700, 0.695, 0.690],
        "higher": [0.730, 0.725, 0.720, 0.715, 0.710],
    },
]

# Which output to use when naming the larger driver. All three are reported either
# way; this only picks the headline.
HEADLINE_OUTPUT = "value_per_share"

TOLERANCE = 0.005     # USD millions / dollars per share, for the restored-base check


# ---------------------------------------------------------------------------
# ANALYSIS -- one run, and the outputs it reports
# ---------------------------------------------------------------------------
def run_case(attribute=None, value=None):
    """Restore every input to base, optionally change ONE, and rebuild the model.

    Returns the three comparison outputs plus the accounting checks, or a record
    marked invalid if the engine refused. A refusal is a result, not a crash: the
    lab asks for invalid runs to be flagged rather than ranked.
    """
    restore_base()
    if attribute is not None:
        if attribute not in BASE_INPUTS:
            raise KeyError(
                f"{attribute!r} is not an independent input. Overriding a calculated "
                f"total would break the linkage this test exists to measure."
            )
        setattr(proforma, attribute, copy.deepcopy(value))

    try:
        projection = proforma.build_projection()
        final = projection[-1]

        # The checks stay visible whether or not they pass.
        worst_gap = max(abs(year["balance_gap"]) for year in projection)
        lowest_cash = min(year["cash"] for year in projection)

        proforma.assert_balanced(projection)
        valuation = proforma.value_equity(projection)

        return {
            "valid": True,
            "reason_invalid": None,
            "operating_profit": final["operating_income"],
            "fcfe": final["fcfe"],
            "value_per_share": valuation["value_per_share"],
            "worst_gap": worst_gap,
            "lowest_cash": lowest_cash,
            "projection": projection,
        }
    except ValueError as error:
        # Either the sheet did not balance or the Gordon formula was undefined.
        return {
            "valid": False,
            "reason_invalid": str(error).splitlines()[0],
            "operating_profit": None,
            "fcfe": None,
            "value_per_share": None,
            "worst_gap": None,
            "lowest_cash": None,
            "projection": None,
        }
    finally:
        restore_base()


OUTPUTS = [
    ("operating_profit", "FY2031E operating profit", "USD m"),
    ("fcfe", "FY2031E free cash flow to equity (FCFE)", "USD m"),
    ("value_per_share", "Value per share", "USD"),
]


def validate_drivers():
    """Fail loudly on an unfilled or mis-specified driver, naming what is wrong."""
    problems = []
    for index, driver in enumerate(DRIVERS, start=1):
        unfilled = [key for key, value in driver.items() if value is PENDING]
        if unfilled:
            problems.append(
                f"driver {index}: not filled in -- {', '.join(sorted(unfilled))}"
            )
            continue

        if driver["attribute"] not in BASE_INPUTS:
            problems.append(
                f"driver {index} ({driver['name']}): {driver['attribute']!r} is not an "
                f"independent input"
            )
            continue

        actual = BASE_INPUTS[driver["attribute"]]
        if driver["base"] != actual:
            problems.append(
                f"driver {index} ({driver['name']}): stated base {driver['base']!r} does "
                f"not match the model's current value {actual!r}"
            )
        if driver["lower"] == driver["higher"]:
            problems.append(
                f"driver {index} ({driver['name']}): lower and higher are identical"
            )
    return problems


def run_sensitivity():
    """Base, then lower/base/higher for each driver, then base restored and rerun."""
    opening_base = run_case()
    results = []

    for driver in DRIVERS:
        runs = []
        for level in ("lower", "base", "higher"):
            label = f"{driver['name']} {level}"
            run = run_case(driver["attribute"], driver[level])
            run["label"] = label
            run["level"] = level
            run["input_value"] = driver[level]
            runs.append(run)
        results.append({"driver": driver, "runs": runs})

    closing_base = run_case()
    return opening_base, results, closing_base


def span(runs, key):
    """Maximum minus minimum across the VALID runs. Nonnegative by construction."""
    values = [run[key] for run in runs if run["valid"]]
    if len(values) < 2:
        return None
    return max(values) - min(values)


# ---------------------------------------------------------------------------
# INTERFACE -- display only, no finance computed below this line
# ---------------------------------------------------------------------------
def format_input(value):
    """Render a scalar or a five-year path compactly, without hiding the values."""
    if isinstance(value, list):
        return "[" + ", ".join(f"{item:g}" for item in value) + "]"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def print_driver(entry, base_run):
    driver, runs = entry["driver"], entry["runs"]
    print(f"\nDRIVER: {driver['name']}")
    print("-" * 96)
    print(f"  Input          {driver['attribute']}")
    print(f"  Units          {driver['units']}")
    print(f"  Years affected {driver['years']}")
    print(f"  Reason         {driver['reason']}")
    print()
    header = f"{'Run':10}{'Input value':>34}"
    for _, caption, unit in OUTPUTS:
        header += f"{caption.split('(')[0].strip()[:22] + ' (' + unit + ')':>28}"
    print(header)
    print("-" * 96)

    for run in runs:
        line = f"{run['level']:10}{format_input(run['input_value']):>34}"
        if not run["valid"]:
            line += f"{'INVALID -- ' + run['reason_invalid'][:60]:>84}"
            print(line)
            continue
        for key, _, _ in OUTPUTS:
            line += f"{run[key]:>28,.2f}"
        print(line)

    # Signed changes from base, in output units.
    print(f"\n  {'Change from base':<26}" + "".join(
        f"{caption.split('(')[0].strip()[:22]:>28}" for _, caption, _ in OUTPUTS))
    for run in runs:
        if run["level"] == "base" or not run["valid"]:
            continue
        line = f"  {run['level']:<26}"
        for key, _, _ in OUTPUTS:
            line += f"{run[key] - base_run[key]:>+28,.2f}"
        print(line)

    print(f"\n  {'Output span (max - min)':<26}" + "".join(
        f"{(span(runs, key) if span(runs, key) is not None else float('nan')):>28,.2f}"
        for key, _, _ in OUTPUTS))

    invalid = [run for run in runs if not run["valid"]]
    if invalid:
        print(f"\n  {len(invalid)} run(s) invalid and excluded from the span above, not ranked.")


def print_checks(label, run):
    if not run["valid"]:
        print(f"{label:36}INVALID -- {run['reason_invalid']}")
        return
    print(f"{label:36}worst |assets-liab-equity| {run['worst_gap']:>10,.2f}"
          f"     lowest cash {run['lowest_cash']:>12,.1f}")


def print_ranking(results):
    print("\n\nWHICH DRIVER IS LARGER, OVER THESE RANGES")
    print("=" * 96)
    print(f"{'Output':44}" + "".join(f"{entry['driver']['name'][:22]:>26}"
                                     for entry in results))
    print("-" * 96)
    for key, caption, unit in OUTPUTS:
        line = f"{caption + ' span (' + unit + ')':44}"
        spans = []
        for entry in results:
            value = span(entry["runs"], key)
            spans.append(value)
            line += f"{value:>26,.2f}" if value is not None else f"{'n/a':>26}"
        print(line)

    usable = [(entry["driver"]["name"], span(entry["runs"], HEADLINE_OUTPUT))
              for entry in results]
    usable = [(name, value) for name, value in usable if value is not None]
    if len(usable) == 2:
        (name_a, span_a), (name_b, span_b) = usable
        larger = name_a if span_a >= span_b else name_b
        ratio = max(span_a, span_b) / min(span_a, span_b) if min(span_a, span_b) else None
        print(f"\nLarger driver for value per share, OVER THESE RANGES: {larger}")
        if ratio:
            print(f"Its span is {ratio:,.1f}x the other's.")
    print("\n'Over these ranges' is not a throwaway. A bigger span can reflect a wider")
    print("input range rather than a more important input. Narrow one range and the")
    print("ranking can flip without anything about NVIDIA changing.")


def print_trace(label):
    """Print full statements for one named run, so a result can be traced."""
    for driver in DRIVERS:
        for level in ("lower", "base", "higher"):
            if f"{driver['name']} {level}".lower() != label.lower():
                continue
            run = run_case(driver["attribute"], driver[level])
            print("=" * 96)
            print(f"TRACE: {driver['name']} {level} "
                  f"({driver['attribute']} = {format_input(driver[level])})")
            print("=" * 96)
            if not run["valid"]:
                print(f"INVALID -- {run['reason_invalid']}")
                return 1
            proforma.print_statements(run["projection"])
            proforma.print_checks(run["projection"])
            return 0
    print(f"No run named {label!r}. Labels are '<driver name> lower|base|higher'.",
          file=sys.stderr)
    return 1


def selftest():
    """Prove the rig before trusting it. No driver results are produced here.

    These four checks exercise the machinery only, so this can be run before the
    drivers are chosen and it cannot reveal a sensitivity result.
    """
    print("=" * 96)
    print("SELF-CHECK -- the rig, not the company")
    print("=" * 96)
    passed = True

    # 1. Three consecutive base runs must be identical. Catches state leaking
    #    between runs, which is the failure mode this whole file is built against.
    runs = [run_case() for _ in range(3)]
    ok = all(abs(run["value_per_share"] - runs[0]["value_per_share"]) < 1e-12
             and abs(run["fcfe"] - runs[0]["fcfe"]) < 1e-9 for run in runs)
    passed &= ok
    print(f"Three base runs identical           {runs[0]['value_per_share']:>14,.6f}"
          f"   {'OK' if ok else 'MISMATCH'}")

    # 2. Overriding an input WITH ITS OWN BASE VALUE must reproduce base exactly.
    #    If it does not, the override path differs from the no-override path.
    same = run_case("TAX_RATE", BASE_INPUTS["TAX_RATE"])
    ok = abs(same["value_per_share"] - runs[0]["value_per_share"]) < 1e-12
    passed &= ok
    print(f"Override with base value is a no-op {same['value_per_share']:>14,.6f}"
          f"   {'OK' if ok else 'MISMATCH'}")

    # 3. A run that RAISES must not leave the model contaminated. Terminal growth
    #    above the cost of equity makes the Gordon formula undefined, so the engine
    #    refuses -- and base must still reproduce afterwards.
    broken = run_case("TERMINAL_GROWTH", 0.99)
    after = run_case()
    ok = (not broken["valid"]
          and abs(after["value_per_share"] - runs[0]["value_per_share"]) < 1e-12)
    passed &= ok
    print(f"Base survives a refused run         {after['value_per_share']:>14,.6f}"
          f"   {'OK' if ok else 'MISMATCH'}")

    # 4. A list input must not be mutated in place by a run. This is the reason the
    #    snapshot is a deep copy rather than a reference.
    shifted = [rate + 0.05 for rate in BASE_INPUTS["REVENUE_GROWTH"]]
    run_case("REVENUE_GROWTH", shifted)
    ok = proforma.REVENUE_GROWTH == BASE_INPUTS["REVENUE_GROWTH"]
    passed &= ok
    print(f"List input restored after override  {format_input(proforma.REVENUE_GROWTH):>14}"
          f"   {'OK' if ok else 'MISMATCH'}")

    print("=" * 96)
    print(f"SELF-CHECK {'PASSED' if passed else 'FAILED'}")
    return 0 if passed else 1


def main():
    if "--selftest" in sys.argv:
        return selftest()

    if "--trace" in sys.argv:
        index = sys.argv.index("--trace")
        if index + 1 >= len(sys.argv):
            print("--trace needs a run label, e.g. --trace \"Gross margin higher\"",
                  file=sys.stderr)
            return 1
        if validate_drivers():
            print("Drivers are not filled in yet; nothing to trace.", file=sys.stderr)
            return 2
        return print_trace(sys.argv[index + 1])

    problems = validate_drivers()
    if problems:
        print("=" * 96)
        print("SENSITIVITY NOT RUN -- the two drivers and their ranges are not set")
        print("=" * 96)
        for problem in problems:
            print(f"  - {problem}")
        print()
        print("Lab 11 requires me to choose the drivers and the ranges myself, and to")
        print("lock a written prediction before the first run. Fill in DRIVERS above,")
        print("then commit the Locked Changed-Input Record, then run this file.")
        print()
        print("Independent inputs available:")
        for name in INDEPENDENT_INPUTS:
            if name == "OPENING":
                continue
            print(f"    {name:34}{format_input(BASE_INPUTS[name])}")
        return 2

    opening_base, results, closing_base = run_sensitivity()

    print("=" * 96)
    print("ONE-AT-A-TIME SENSITIVITY -- NVIDIA Corporation (NVDA)")
    print("=" * 96)
    print("Every run restores all 24 independent inputs from a snapshot, then changes")
    print("exactly one. Linked statement quantities recalculate; none are overridden.")
    print()
    print(f"{'Base':10}{'':34}" + "".join(
        f"{caption.split('(')[0].strip()[:22] + ' (' + unit + ')':>28}"
        for _, caption, unit in OUTPUTS))
    print("-" * 96)
    line = f"{'base':10}{'(model as filed)':>34}"
    for key, _, _ in OUTPUTS:
        line += f"{opening_base[key]:>28,.2f}"
    print(line)

    for entry in results:
        print_driver(entry, opening_base)

    print("\n\nACCOUNTING CHECKS")
    print("=" * 96)
    print_checks("Base, before the analysis", opening_base)
    for entry in results:
        for run in entry["runs"]:
            print_checks(f"  {run['label']}", run)
    print_checks("Base, restored and rerun", closing_base)

    print("\nRESTORED-BASE CHECK")
    print("-" * 96)
    drift_failures = []
    for key, caption, unit in OUTPUTS:
        drift = closing_base[key] - opening_base[key]
        status = "OK" if abs(drift) <= TOLERANCE else "DRIFTED"
        if status == "DRIFTED":
            drift_failures.append(caption)
        print(f"{caption + ' (' + unit + ')':56}{drift:>+16,.6f}   {status}")
    if drift_failures:
        print("\nBase did not restore. Every span above is suspect.", file=sys.stderr)
        return 1
    print("\nBase restored exactly. The spans above are comparable to one another.")

    print_ranking(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
