import yfinance as yf
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# ——— Page Config ———
st.set_page_config(page_title="Financial & FRED Dashboard", layout="wide")

# ——— Constants ———
API_KEY = "26c01b09f8083e30a1ee9cb929188a74"
FRED_DATA_URL = "https://api.stlouisfed.org/fred/series/observations"
FRED_SERIES = {
    "MRTSIR444USS": "Inventory/Sales Ratio: Building Materials & Garden Equipment Dealers"
}

def to_millions(x):
    return round(x/1e6, 2) if pd.notnull(x) else 0

@st.cache_data
def fetch_stock_data(ticker):
    return yf.Ticker(ticker)

@st.cache_data
def get_fred_data(series_id, start_date, end_date):
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }
    resp = requests.get(FRED_DATA_URL, params=params)
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

# ——— Streamlit App ———
st.title("Annual Financials & Working Capital with FRED Metrics")

# Stock ticker input
ticker = st.text_input("Enter Ticker:", "AAPL")
if ticker:
    stock = fetch_stock_data(ticker)
    annual_financials = stock.financials
    balance_sheet = stock.balance_sheet
    cashflow = stock.cashflow

    if not annual_financials.empty:
        # Key Financials last 5 yrs
        st.subheader("Key Financials (M) — Last 5 Years")
        mets   = ["Total Revenue","Gross Profit","EBIT","EBITDA"]
        last5  = fin.columns[:5]
        kdf    = fin.reindex(mets).loc[:, last5].applymap(format_millions)
        yrs    = [pd.to_datetime(c).year for c in last5][::-1]
        kdf.columns = yrs
        st.table(kdf)
        # Growth rates
        growth_df = key_df.pct_change(axis=1).iloc[:, 1:] * 100
        growth_df.columns = [f"{curr} vs {prev}" for prev, curr in zip(years[:-1], years[1:])]
        st.subheader("Year‑over‑Year Growth (%)")
        st.table(growth_df)

        # Working Capital Metrics
        def safe(df, idx, col):
            try:
                return df.at[idx, col]
            except:
                return 0

        raw_inputs = {}
        wc_metrics = {}
        for col in last3:
            yr = pd.to_datetime(col).year
            inv = safe(balance_sheet, "Inventory", col)
            ar = safe(balance_sheet, "Accounts Receivable", col)
            ap = safe(balance_sheet, "Accounts Payable", col)
            cogs = safe(annual_financials, "Cost Of Revenue", col)
            rev = safe(annual_financials, "Total Revenue", col)

            raw_vals = [to_millions(inv), to_millions(ar), to_millions(ap), to_millions(cogs), to_millions(rev)]
            dio = round((inv/cogs)*365,1) if cogs else None
            dso = round((ar/rev)*365,1) if rev else None
            dpo = round((ap/cogs)*365,1) if cogs else None
            ccc = round(dio + dpo - (dso or 0),1) if dio is not None else None

            raw_inputs[yr] = raw_vals
            wc_metrics[yr] = [dio, dso, dpo, ccc]

        raw_df = pd.DataFrame(raw_inputs, index=["Inventory (M)", "Accounts Receivable (M)", "Accounts Payable (M)", "COGS (M)", "Revenue (M)"])
        st.subheader("Working Capital Raw Inputs (M) — Last 3 Years")
        st.table(raw_df)

        wc_df = pd.DataFrame(wc_metrics, index=["DIO", "DSO", "DPO", "CCC"])  
        st.subheader("Working Capital Metrics (Days) — Last 3 Years")
        st.table(wc_df)

        # FRED Inventory/Sales Ratio
        st.subheader("Inventory/Sales Ratio (FRED)")
        col1, col2 = st.columns(2)
        start = col1.date_input("Start Date", pd.to_datetime("2000-01-01"))
        end = col2.date_input("End Date", pd.to_datetime("2025-12-31"))
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

st.markdown("Data sourced from Yahoo Finance & FRED.")
