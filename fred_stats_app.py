import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# ——— FRED settings ———
API_KEY = "26c01b09f8083e30a1ee9cb929188a74"
FRED_DATA_URL = "https://api.stlouisfed.org/fred/series/observations"

# Single FRED series: Inventory/Sales Ratio for Building Materials & Garden Equipment Dealers
FRED_SERIES = {
    "MRTSIR444USS": "Inventory/Sales Ratio: Building Materials & Garden Equipment Dealers"
}

def get_fred_data(series_id, start_date="2000-01-01", end_date="2025-12-31"):
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
    df = df[["date", "value"]]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df

# ——— Streamlit layout ———
st.title("📊 Inventory/Sales Ratio: Building Materials & Garden Equipment Dealers")

st.markdown(
    """
    This dashboard shows the Inventory‑to‑Sales ratio for the Building Materials & Garden Equipment dealer segment,
    as a direct indicator of how inventories are tracking relative to sales in Home Depot’s industry.
    """
)

# Date range selection
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", pd.to_datetime("2000-01-01"))
with col2:
    end_date = st.date_input("End Date", pd.to_datetime("2025-12-31"))

if st.button("Fetch Data"):
    series_id, desc = list(FRED_SERIES.items())[0]
    df = get_fred_data(
        series_id,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d"),
    )

    if df is not None:
        st.subheader(f"{desc} ({series_id})")
        st.dataframe(df.set_index("date"))

        st.subheader("📈 Inventory/Sales Ratio Over Time")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["date"], df["value"], marker="o", linestyle="-")
        ax.set_title(desc)
        ax.set_xlabel("Date")
        ax.set_ylabel("Ratio")
        ax.grid(True)
        st.pyplot(fig)
    else:
        st.warning("No data found for the given date range.")

st.markdown(
    "Data sourced from [FRED](https://fred.stlouisfed.org/) by the Federal Reserve Bank of St. Louis."
)
