import yfinance as yf
import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt

# ——— Page Config ———
st.set_page_config(page_title="Financial & FRED Dashboard", layout="wide")

# ——— Constants ———
API_KEY = "26c01b09f8083e30a1ee9cb929188a74"
FRED_DATA_URL = "<https://api.stlouisfed.org/fred/series/observations>"
FRED_SERIES = {
    "MRTSIR444USS": "Inventory/Sales Ratio: Building Materials & Garden Equipment Dealers"
}

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
                return <<df.at>>[idx, col]
            except:
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

st.markdown("Data sourced from Yahoo Finance & FRED.")
