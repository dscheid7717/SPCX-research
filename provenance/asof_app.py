"""Lab 17 — Point-in-time audit: a FRED-style rates app.

Shows each series as it reads today (FRED) beside what was known on an earlier date (ALFRED),
and counts the values published later and the values revised since.
Data: FRED's and ALFRED's public CSV downloads, no API key. Run: streamlit run asof_app.py
"""

import io
import urllib.error
import urllib.request
from datetime import date

import pandas as pd
import streamlit as st

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
ALFRED_URL = "https://alfred.stlouisfed.org/graph/alfredgraph.csv?id={series}&vintage_date={vintage}"
FRED_PAGE = "https://fred.stlouisfed.org/series/{series}"

DEFAULT_SERIES = {
    "BAA": "Moody's Baa corporate bond yield",
    "FEDFUNDS": "Federal funds rate",
    "DGS10": "10-year Treasury yield",
    "MORTGAGE30US": "30-year mortgage rate",
}


# ---------------------------------------------------------------- data

def _read_csv(url):
    """Download one FRED/ALFRED CSV and return a date-indexed Series of floats ("." = missing day)."""
    # Default Python user agent: FRED stalls requests that claim to be a browser.
    with urllib.request.urlopen(url, timeout=30) as response:
        text = response.read().decode("utf-8")
    frame = pd.read_csv(io.StringIO(text), na_values=".")
    if frame.shape[1] < 2 or "date" not in frame.columns[0].lower():
        raise ValueError("not a FRED series")
    values = pd.Series(frame.iloc[:, 1].values, index=pd.to_datetime(frame.iloc[:, 0]), dtype="float64")
    return values.dropna()


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_today(series):
    """The series as it reads today, from FRED."""
    return _read_csv(FRED_URL.format(series=series))


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_as_known(series, vintage):
    """The series as it read on `vintage` (YYYY-MM-DD), from ALFRED."""
    return _read_csv(ALFRED_URL.format(series=series, vintage=vintage))


# ---------------------------------------------------------------- comparison

def compare(today, then):
    """Compare today's values with the values known then. Returns a dict for the table."""
    last_then = then.index.max()
    common = today.index.intersection(then.index)
    revised = int((today[common] - then[common]).abs().gt(1e-9).sum())
    return {
        "last_then": last_then,
        "value_then": then[last_then],
        "last_today": today.index.max(),
        "value_today": today[today.index.max()],
        "later": int((today.index > last_then).sum()),
        "revised": revised,
    }


def format_date(timestamp):
    return timestamp.strftime("%Y-%m-%d")


# ---------------------------------------------------------------- page

st.set_page_config(page_title="As-known-on rates", layout="wide")
st.title("Interest rates: today vs. as known on a date")
st.caption(f"Data from FRED and ALFRED, Federal Reserve Bank of St. Louis, downloaded "
           f"{date.today():%Y-%m-%d}. Built with AI help (Claude Code); a learning demonstration, "
           f"not investment advice.")

with st.sidebar:
    chosen = st.multiselect("Series", list(DEFAULT_SERIES), default=list(DEFAULT_SERIES),
                            format_func=lambda s: f"{s} — {DEFAULT_SERIES[s]}")
    extra = st.text_input("Add FRED series IDs (comma-separated)", "")
    start = st.date_input("Start date", value=date(2020, 1, 1))
    as_known_on = st.date_input("As known on", value=date.today(), max_value=date.today())

extra_ids = [s.strip().upper() for s in extra.split(",") if s.strip()]
series_ids = chosen + [s for s in extra_ids if s not in chosen]
vintage = as_known_on.isoformat()

rows = []
for series in series_ids:
    name = DEFAULT_SERIES.get(series, series)
    try:
        today = fetch_today(series)
        then = fetch_as_known(series, vintage)
    except (urllib.error.URLError, ValueError, pd.errors.ParserError) as error:
        st.error(f"{series}: could not load ({error}). Check the ID on fred.stlouisfed.org.")
        continue
    if then.empty:
        st.warning(f"{series}: no values were published by {vintage}.")
        continue

    st.subheader(f"{series} — {name}")
    st.line_chart(today[today.index >= pd.Timestamp(start)].rename(series))
    result = compare(today, then)
    st.caption(f"Last date in the data as known on {vintage}: {format_date(result['last_then'])}")
    rows.append({
        "Series": FRED_PAGE.format(series=series),
        f"Last date known on {vintage}": format_date(result["last_then"]),
        "Value then": result["value_then"],
        "Last date today": format_date(result["last_today"]),
        "Value today": result["value_today"],
        "Values published later": result["later"],
        "Values revised since": result["revised"],
    })

st.subheader(f"As known on {vintage} vs. today")
if rows:
    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        column_config={"Series": st.column_config.LinkColumn("Series", display_text=r"series/(\w+)$")},
    )
else:
    st.info("No series loaded.")
