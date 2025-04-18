import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# ——— FRED settings ———
API_KEY = "26c01b09f8083e30a1ee9cb929188a74"
FRED_DATA_URL = "https://api.stlouisfed.org/fred/series/observations"

# Top three FRED series to compare
FRED_SERIES = {
    "MRTSSM444USS": "Retail Sales: Building Materials & Garden Equipment",
    "MRTSMPCSM444USS": "% Change in Retail Sales (Building Materials & Garden Equipment)",
    "HOUST": "Housing Starts"
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
st.title("📊 Home Depot vs. Key Housing/DIY Indicators")

st.markdown(
    """
    This dashboard pulls in three FRED series and overlays them so you can see how:
    - Building‑materials retail sales  
    - Their month‑over‑month growth  
    - New housing starts  
    co‑move with Home Depot’s business cycle.
    """
)

# Date range
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Start Date", pd.to_datetime("2000-01-01"))
with col2:
    end_date = st.date_input("End Date", pd.to_datetime("2025-12-31"))

if st.button("Fetch & Compare"):
    # fetch each series
    dfs = {}
    for series_id, desc in FRED_SERIES.items():
        df = get_fred_data(
            series_id,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )
        if df is not None:
            dfs[series_id] = df
        else:
            st.warning(f"No data for {series_id}")

    if dfs:
        # Plot them together
        fig, ax = plt.subplots(figsize=(10, 6))
        for sid, df in dfs.items():
            ax.plot(
                df["date"],
                df["value"],
                marker="o",
                linestyle="-",
                label=FRED_SERIES[sid],
            )
        ax.set_title("FRED Series Comparison")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

        # Optionally show each table
        for sid, df in dfs.items():
            st.subheader(f"{FRED_SERIES[sid]} ({sid})")
            st.dataframe(df.set_index("date"))

    else:
        st.error("No series could be loaded.")

st.markdown(
    "Data sourced from [FRED](https://fred.stlouisfed.org/) by the Federal Reserve Bank of St. Louis."
)
