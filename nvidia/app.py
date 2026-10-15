"""Project 1 committee app -- NVIDIA (NVDA).

Run from the nvidia folder:   streamlit run app.py

Two halves, deliberately separate:
  1. COMMITTEE VIEW renders the frozen visible_output.json -- the validated, reviewable result.
     Nothing in it is computed here.
  2. WHAT-IF PANEL moves a few bounded drivers and calls analysis.run_model(), the same engine
     that produced the frozen file. The app computes no finance itself; it formats what the
     engine returns. "Reset to base" restores the frozen base inputs.
"""

import json
import pathlib

import pandas as pd
import streamlit as st

import analysis

HERE = pathlib.Path(__file__).resolve().parent
FROZEN = HERE / "visible_output.json"

st.set_page_config(page_title="NVDA Project 1 -- Committee", layout="wide")
st.title("NVIDIA (NVDA) -- initiate, watch/defer, or do not initiate?")
st.caption("FIN 43900 Project 1 · Drew Scheiderer · coursework, not investment advice. "
           "USD millions unless noted; per-share values in USD.")

# ---------------------------------------------------------------------------
# 1. COMMITTEE VIEW -- frozen output only
# ---------------------------------------------------------------------------
if not FROZEN.exists():
    st.error("visible_output.json is missing. Run `python analysis.py --freeze` first.")
    st.stop()
frozen = json.loads(FROZEN.read_text(encoding="utf-8"))
rec = frozen["recommendation"]
val = frozen["valuation"]

st.header("Committee view (frozen)")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Action", rec["action"])
c2.metric("DCF range (low-base-high)",
          " / ".join(f"${v:,.0f}" for v in val["dcf_low_base_high_per_share"]))
c3.metric("Price", f"${frozen['material_inputs']['price']:,.2f}", help=f"close {frozen['as_of']}")
c4.metric("Terminal value share of EV", f"{val['terminal_share_of_ev']:.1%}")
st.write(f"**Why:** {rec['reason']}")
st.write(f"**Reversal trigger:** {frozen['reversal_trigger']}")
with st.expander("Conditions, cases, comparables, reverse DCF, limitations"):
    st.write("**Conditions**")
    for item in rec["conditions"]:
        st.write(f"- {item}")
    st.write("**Cases and the action the rule gives under each**")
    st.table(pd.DataFrame({
        "case": val["case_names"],
        "value per share": [f"${v:,.2f}" for v in val["dcf_low_base_high_per_share"]],
        "action": val["case_actions"],
    }))
    st.write("**Named what-ifs**")
    st.table(pd.DataFrame([
        {"what-if": name, "value per share": f"${d['value_per_share']:,.2f}", "action": d["action"]}
        for name, d in val["what_ifs"].items()]))
    st.write("**Comparables** (one definition, 2026-10-14 prices)")
    st.table(pd.DataFrame(val["comparables"]).T.rename(
        columns={"ev_ebitda": "EV/EBITDA (x)", "pe": "P/E (x)"}))
    r = val["reverse_dcf"]
    st.write(f"**Reverse DCF:** the price implies FY2028-31 growth "
             f"{r['uniform_growth_shift_pp']:+.1f}pp above base every year, or a beta of "
             f"{r['implied_beta']:.2f} (cost of equity {r['implied_cost_of_equity']:.2%}). "
             "One consistent assumption set, not proof of mispricing.")
    st.write("**Limitations**")
    for item in frozen["limitations"]:
        st.write(f"- {item}")

# ---------------------------------------------------------------------------
# 2. WHAT-IF PANEL -- bounded drivers, same engine
# ---------------------------------------------------------------------------
BASE = analysis.base_inputs()
DEFAULTS = {
    "fy2027_growth": round(BASE["revenue_growth"][0] * 100, 1),
    "later_growth_shift": 0.0,
    "margin_shift": 0.0,
    "beta": BASE["beta"],
    "terminal_growth": BASE["terminal_growth"] * 100,
    "sbc_cost": False,
    "fault": "none",
}
for key, value in DEFAULTS.items():
    st.session_state.setdefault(key, value)


def reset_to_base():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value


st.header("What-if panel (live engine)")
st.sidebar.header("Bounded drivers")
st.sidebar.button("Reset to base", on_click=reset_to_base, type="primary")
st.sidebar.slider("FY2027E revenue growth (%)", 55.0, 95.0, key="fy2027_growth", step=0.5,
                  help="Base 71.5%: H1 reported + H2 at the Q2 run rate.")
st.sidebar.slider("FY2028E-FY2031E growth shift (pp)", -15.0, 15.0, key="later_growth_shift",
                  step=0.5)
st.sidebar.slider("Gross margin shift, every year (pp)", -6.0, 3.0, key="margin_shift", step=0.5)
st.sidebar.slider("Beta", 1.0, 3.0, key="beta", step=0.05,
                  help="Raw 2.216; Blume-adjusted 1.815.")
st.sidebar.slider("Terminal growth (%)", 1.0, 4.0, key="terminal_growth", step=0.25)
st.sidebar.checkbox("Treat stock compensation as a cash cost", key="sbc_cost")
st.sidebar.selectbox(
    "Inject a fault (shows the checks failing loudly)",
    ["none", "drop_sbc_equity_credit", "opening_mapping_error"], key="fault")

s = st.session_state
inputs = analysis.apply_overrides(BASE, {
    # At the slider's default the exact base growth (71.47%) is used, not the rounded slider
    # value, so "Reset to base" reproduces the frozen base value to the cent.
    "revenue_growth": [BASE["revenue_growth"][0] if s.fy2027_growth == DEFAULTS["fy2027_growth"]
                       else s.fy2027_growth / 100]
                      + [g + s.later_growth_shift / 100 for g in BASE["revenue_growth"][1:]],
    "gross_margin": [m + s.margin_shift / 100 for m in BASE["gross_margin"]],
    "beta": s.beta,
    "terminal_growth": s.terminal_growth / 100,
    "sbc_as_cash_cost": s.sbc_cost,
    "inject_fault": None if s.fault == "none" else s.fault,
})

base_run = analysis.run_model(BASE)
run = analysis.run_model(inputs)
base_value = base_run["valuation"]["value_per_share"]

checks = pd.DataFrame(run["checks"])
failed = checks[~checks["passed"]]

if run["valid"]:
    value = run["valuation"]["value_per_share"]
    comps = analysis.comparables()
    action, reason = analysis.decide(inputs["price"], value, comps["nvda_below_every_peer"],
                                     analysis.ebitda_persists(run))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Value per share", f"${value:,.2f}", f"{value - base_value:+,.2f} vs base")
    m2.metric("Change vs base", f"{value / base_value - 1:+.1%}")
    m3.metric("WACC", f"{run['wacc']:.2%}")
    m4.metric("Action under these inputs", action)
    st.caption(reason)
else:
    st.error("MODEL REFUSED TO VALUE -- at least one check failed. No number is shown for a "
             "broken model.")

st.subheader("Checks")
st.dataframe(
    checks.style.apply(
        lambda row: ["background-color: #f8d7da; color: #721c24" if not row["passed"]
                     else "background-color: #d4edda; color: #155724"] * len(row), axis=1),
    hide_index=True, width="stretch")
if len(failed):
    st.error(f"{len(failed)} check(s) FAILED: " + "; ".join(failed["check"]))
else:
    st.success("All checks pass.")

if run.get("projection"):
    st.subheader("Pro-forma under these inputs (USD millions)")
    table = pd.DataFrame(run["projection"]).set_index("label")[
        ["revenue", "gross_profit", "operating_income", "net_income", "cash",
         "total_assets", "equity", "balance_gap", "fcfe"]]
    table["fcff"] = run["fcff"]
    st.dataframe(table.T.style.format("{:,.1f}"), width="stretch")

st.info("The interface does not establish finance quality: sources, conventions, tests and "
        "the frozen validation record are in docs/ and nvidia/test_project.py.")
