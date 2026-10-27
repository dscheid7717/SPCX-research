"""Lab 15 — Portfolio stability app (Streamlit).

Finds the lowest-risk long-only mix that meets the objective and the reserve rule, beside the
answer for the inputs as loaded. All math is imported from portfolio.py; none is copied here.
Run from this folder: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import portfolio as engine

st.set_page_config(page_title="Portfolio Stability", layout="wide")
st.title("Lowest-risk mix that meets the mandate")
st.caption("Built with AI help (Claude Code). A learning demonstration, not investment advice.")

# ---------------------------------------------------------------- sidebar
with st.sidebar:
    objective = st.number_input("Objective: expected return at least (%)", value=6.5, step=0.1, format="%.2f")
    reserve_min = st.number_input("Reserve minimum (%)", value=3.0, min_value=0.0, max_value=100.0, step=1.0)
    upload = st.file_uploader("Upload prices.csv (date first, oldest first, one column per ticker)", type="csv")
    last_36 = st.toggle("Last 36 months only", value=False, disabled=upload is None)

# ---------------------------------------------------------------- inputs
if upload is None:
    source = "Meridian (course training values)"
    sleeves = list(engine.SLEEVES)
    loaded_returns = [engine.EXPECTED_RETURN[s] for s in sleeves]
    loaded_vols = [engine.VOLATILITY[s] for s in sleeves]
    loaded_corr = engine.CORRELATION
    start_returns, vols, corr = loaded_returns, loaded_vols, loaded_corr
    default_eligible = engine.RESERVE_ELIGIBLE
    note = "Training values, not market estimates."
else:
    text = upload.getvalue().decode("utf-8-sig")
    full = engine.estimate_from_prices(text)
    used = engine.estimate_from_prices(text, last_months=36) if last_36 else full
    source = f"{upload.name}"
    sleeves = full["tickers"]
    loaded_returns, loaded_vols, loaded_corr = full["returns"], full["vols"], full["corr"]
    start_returns, vols, corr = used["returns"], used["vols"], used["corr"]
    default_eligible = {"BIL"}
    note = (f"Estimates from history: {used['months']} monthly returns "
            f"({'last 36 months' if last_36 else 'all months'}, prices {full['first_price_date']} "
            f"to {full['last_price_date']}). A five-year average is history, not a forecast.")

st.subheader(f"Inputs — {source}")
st.caption(note)

key = f"{source}|{last_36}"
cols = st.columns(len(sleeves))
returns, eligible = [], set()
for i, (col, sleeve) in enumerate(zip(cols, sleeves)):
    with col:
        r = st.number_input(f"{sleeve} — expected return (%)", value=round(start_returns[i], 2), step=0.1,
                            format="%.2f", key=f"ret|{key}|{sleeve}")
        returns.append(r)
        st.write(f"Volatility: {vols[i]:.2f}%")
        if st.checkbox("Reserve-eligible", value=sleeve in default_eligible, key=f"res|{source}|{sleeve}"):
            eligible.add(sleeve)

with st.expander("Correlation table in use"):
    st.dataframe(pd.DataFrame(corr, index=sleeves, columns=sleeves).round(2))

# ---------------------------------------------------------------- search
as_loaded = engine.lowest_risk_mix(sleeves, loaded_returns, loaded_vols, loaded_corr,
                                   eligible, objective, reserve_min)
current = engine.lowest_risk_mix(sleeves, returns, vols, corr, eligible, objective, reserve_min)


def show(column, title, result):
    with column:
        st.markdown(f"**{title}**")
        if result is None:
            st.error("No mix meets the objective.")
            return
        st.dataframe(pd.DataFrame({"Weight (%)": [round(w, 2) for w in result["weights_pct"]]}, index=sleeves))
        st.write(f"Expected return: **{result['return_pct']:.2f}%** · "
                 f"Volatility: **{result['volatility_pct']:.2f}%** · "
                 f"Reserve-eligible: **{result['reserve_pct']:.2f}%**")


st.subheader("Answer")
left, right = st.columns(2)
show(left, "Inputs as loaded" + ("" if upload is None else " (all months)"), as_loaded)
show(right, "Inputs as set on this page", current)

if as_loaded and current:
    changes = [abs(a - b) for a, b in zip(as_loaded["weights_pct"], current["weights_pct"])]
    biggest = max(range(len(sleeves)), key=lambda i: changes[i])
    st.metric("Largest weight change", f"{changes[biggest]:.0f} points", help=f"in {sleeves[biggest]}")
    if changes[biggest] > 0:
        st.caption(f"Largest change is in {sleeves[biggest]}.")
