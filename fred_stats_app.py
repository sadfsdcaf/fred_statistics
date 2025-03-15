import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# FRED API Key (Replace with your own)
API_KEY = "26c01b09f8083e30a1ee9cb929188a74"
FRED_DATA_URL = "https://api.stlouisfed.org/fred/series/observations"

# Predefined list of common FRED indicators (ID: Description)
FRED_SERIES = {
    "GDP": "Gross Domestic Product (GDP)",
    "CPIAUCSL": "Consumer Price Index (Inflation)",
    "UNRATE": "Unemployment Rate",
    "SP500": "S&P 500 Index",
    "FEDFUNDS": "Federal Funds Rate",
    "M2SL": "M2 Money Supply",
    "DGS10": "10-Year Treasury Yield",
    "PAYEMS": "Total Nonfarm Payrolls",
    "PCE": "Personal Consumption Expenditures",
    "CSUSHPISA": "Case-Shiller Home Price Index",
    "DEXUSEU": "US Dollar to Euro Exchange Rate",
    "BAA": "Moody’s Baa Corporate Bond Yield",
    "GDPC1": "Real GDP (Chained Dollars)",
    "CIVPART": "Labor Force Participation Rate",
    "ISRATIO": "Inventory to Sales Ratio",
    "BUSINV": "Total Business Inventories",
    "RETAILSMSA": "Retail Sales (Seasonally Adjusted)",
    "PPIACO": "Producer Price Index (All Commodities)",
    "HOUST": "Housing Starts",
    "DFF": "Effective Federal Funds Rate",
    "MORTGAGE30US": "30-Year Fixed Mortgage Rate",
}

# Function to fetch FRED data
def get_fred_data(series_id, start_date="2000-01-01", end_date="2025-12-31"):
    params = {
        "series_id": series_id,
        "api_key": API_KEY,
        "file_type": "json",
        "observation_start": start_date,
        "observation_end": end_date,
    }

    response = requests.get(FRED_DATA_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        observations = data.get("observations", [])

        if not observations:
            return None

        # Convert to DataFrame
        df = pd.DataFrame(observations)
        df = df[["date", "value"]]
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df["date"] = pd.to_datetime(df["date"])

        return df
    else:
        st.error(f"Error {response.status_code}: {response.text}")
        return None

# Streamlit App
st.title("📊 FRED Economic Data Viewer")

# Dropdown menu for FRED Series Selection
series_id = st.selectbox(
    "Select a FRED Economic Indicator:",
    options=list(FRED_SERIES.keys()),
    format_func=lambda x: FRED_SERIES[x]  # Show descriptions
)

# Date range selection
start_date = st.date_input("Start Date", pd.to_datetime("2000-01-01"))
end_date = st.date_input("End Date", pd.to_datetime("2025-12-31"))

# Fetch and display data
if st.button("Fetch Data"):
    df = get_fred_data(series_id, start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))

    if df is not None:
        st.subheader(f"Data for {FRED_SERIES[series_id]} ({series_id})")
        st.dataframe(df)  # Display table

        # Plot data
        st.subheader("📈 Data Visualization")
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df["date"], df["value"], marker="o", linestyle="-", color="blue", label=FRED_SERIES[series_id])
        ax.set_title(f"{FRED_SERIES[series_id]} Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Value")
        ax.legend()
        ax.grid()
        st.pyplot(fig)
    else:
        st.warning("No data found for the given series ID and date range.")

# Footer
st.markdown("Data sourced from [FRED](https://fred.stlouisfed.org/) by the Federal Reserve Bank of St. Louis.")
