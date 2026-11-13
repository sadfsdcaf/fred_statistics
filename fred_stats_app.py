import os

import yfinance as yf
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# ——— Page Config ———
st.set_page_config(page_title="Financial & FRED Dashboard", layout="wide")

# ——— Constants ———
# FRED API key comes from the environment; never hardcode or display it.
API_KEY = os.environ.get("FRED_API_KEY", "").strip()
FRED_DATA_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_TIMEOUT = 30  # seconds
FRED_SERIES = {
    "MRTSIR444USS": "Inventory/Sales Ratio: Building Materials & Garden Equipment Dealers"
}
TREASURY_SERIES = {
    "DGS2": "2-Year Treasury Yield",
    "DGS10": "10-Year Treasury Yield",
}


def fred_key_available():
    """Show a clear error and return False if FRED_API_KEY is not configured."""
    if API_KEY:
        return True
    st.error(
        "FRED API key not configured. Set the FRED_API_KEY environment variable "
        "and restart the app to enable FRED data."
    )
    return False

def to_millions(x):
    return round(x/1e6, 2) if pd.notnull(x) else 0

@st.cache_data
def fetch_stock_data(ticker):
    stock = yf.Ticker(ticker)
    return stock.financials, stock.balance_sheet, stock.cashflow

@st.cache_data
def get_fred_data(series_id, start_date, end_date):
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }
    try:
        resp = requests.get(FRED_DATA_URL, params=params, timeout=FRED_TIMEOUT)
    except requests.RequestException as exc:
        # Only show the exception type: its message contains the request URL, which includes the key.
        st.error(f"Error fetching {series_id}: {type(exc).__name__}")
        return None
    if resp.status_code != 200:
        st.error(f"Error fetching {series_id}: {resp.status_code}")
        return None
    data = resp.json().get("observations", [])
    if not data:
        return None
    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df

@st.cache_data
def fetch_fred_series(series_id, start, end):
    """Fetch one FRED series as a DataFrame with 'date' and 'value' columns.

    `start`/`end` may be dates or "YYYY-MM-DD" strings. Missing values (".")
    become NaN. Returns None on error or if there is no data.
    """
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": pd.to_datetime(start).strftime("%Y-%m-%d"),
        "observation_end": pd.to_datetime(end).strftime("%Y-%m-%d"),
    }
    try:
        resp = requests.get(FRED_DATA_URL, params=params, timeout=FRED_TIMEOUT)
    except requests.RequestException as exc:
        st.error(f"Error fetching {series_id}: {type(exc).__name__}")
        return None
    if resp.status_code != 200:
        st.error(f"Error fetching {series_id}: {resp.status_code}")
        return None
    data = resp.json().get("observations", [])
    if not data:
        return None
    df = pd.DataFrame(data)[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df

# ——— Streamlit App ———
st.title("Annual Financials & Working Capital with FRED Metrics")

ticker = st.text_input("Enter Ticker:", "HD")
if ticker:
    annual_financials, balance_sheet, cashflow = fetch_stock_data(ticker)

    if not annual_financials.empty:
        st.subheader("Key Financials (M) — Last 5 Years")
        mets    = ["Total Revenue","Gross Profit","EBIT","EBITDA"]
        last5   = annual_financials.columns[:5]
        kdf_raw = annual_financials.reindex(mets).loc[:, last5]
        yrs     = [pd.to_datetime(c).year for c in last5]
        kdf     = kdf_raw.map(to_millions)
        kdf.columns = yrs
        st.table(kdf)

        growth_df = kdf_raw.pct_change(axis=1).iloc[:, 1:] * 100
        growth_df.columns = [f"{yrs[i]} vs {yrs[i-1]}" for i in range(1, len(yrs))]
        st.subheader("Year‑over‑Year Growth (%)")
        st.table(growth_df.round(1))

        def safe(df, idx, col):
            try:
                return df.at[idx, col]
            except Exception:
                return 0

        last3 = annual_financials.columns[:3]
        raw_inputs = {}
        wc_metrics = {}
        for col in last3:
            yr   = pd.to_datetime(col).year
            inv  = safe(balance_sheet, "Inventory", col)
            ar   = safe(balance_sheet, "Accounts Receivable", col)
            ap   = safe(balance_sheet, "Accounts Payable", col)
            cogs = safe(annual_financials, "Cost Of Revenue", col)
            rev  = safe(annual_financials, "Total Revenue", col)

            raw_vals = [to_millions(inv), to_millions(ar), to_millions(ap), to_millions(cogs), to_millions(rev)]
            dio = round((inv/cogs)*365,1) if cogs else None
            dso = round((ar/rev)*365,1) if rev else None
            dpo = round((ap/cogs)*365,1) if cogs else None
            ccc = round(dio + (dso or 0) - dpo,1) if dio is not None else None

            raw_inputs[yr] = raw_vals
            wc_metrics[yr] = [dio, dso, dpo, ccc]

        raw_df = pd.DataFrame(raw_inputs, index=["Inventory (M)", "Accounts Receivable (M)", "Accounts Payable (M)", "COGS (M)", "Revenue (M)"])
        st.subheader("Working Capital Raw Inputs (M) — Last 3 Years")
        st.table(raw_df)

        wc_df = pd.DataFrame(wc_metrics, index=["DIO", "DSO", "DPO", "CCC"])
        st.subheader("Working Capital Metrics (Days) — Last 3 Years")
        st.table(wc_df)

        st.subheader("Inventory/Sales Ratio (FRED)")
        if fred_key_available():
            col1, col2 = st.columns(2)
            start = col1.date_input("Start Date", pd.to_datetime("2000-01-01"))
            end   = col2.date_input("End Date", pd.to_datetime("2025-12-31"))
            if st.button("Fetch Inventory/Sales Ratio"):
                sid, desc = next(iter(FRED_SERIES.items()))
                df_fred = get_fred_data(sid, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
                if df_fred is not None:
                    st.subheader(desc)
                    st.dataframe(df_fred.set_index("date"))
                    fig, ax = plt.subplots(figsize=(10,5))
                    ax.plot(df_fred["date"], df_fred["value"], marker="o", linestyle="-")
                    ax.set_title(desc)
                    ax.set_xlabel("Date")
                    ax.set_ylabel("Ratio")
                    ax.grid(True)
                    st.pyplot(fig)
                else:
                    st.warning("No FRED data found for the given range.")

# ——— Treasury Yields (FRED) ———
st.subheader("Treasury Yields: 2-Year vs 10-Year (FRED)")
if fred_key_available():
    tcol1, tcol2 = st.columns(2)
    t_start = tcol1.date_input("Yield Start Date", pd.to_datetime("2000-01-01"), key="yield_start")
    t_end   = tcol2.date_input("Yield End Date", pd.Timestamp.today().normalize(), key="yield_end")
    if st.button("Fetch Treasury Yields"):
        fig, ax = plt.subplots(figsize=(10,5))
        plotted = False
        for sid, label in TREASURY_SERIES.items():
            df_y = fetch_fred_series(sid, t_start, t_end)
            if df_y is None or df_y["value"].dropna().empty:
                st.warning(f"No FRED data found for {sid} in the given range.")
                continue
            df_y = df_y.dropna(subset=["value"])
            ax.plot(df_y["date"], df_y["value"], linewidth=1.2, label=f"{label} ({sid})")
            plotted = True
        if plotted:
            ax.set_title("2-Year vs 10-Year Treasury Yields")
            ax.set_xlabel("Date")
            ax.set_ylabel("Yield (%)")
            ax.grid(True)
            ax.legend()
            st.pyplot(fig)
        plt.close(fig)

st.markdown("Data sourced from Yahoo Finance & FRED.")
