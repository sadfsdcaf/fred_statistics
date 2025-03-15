import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt

# FRED API Key (Replace with your own)
API_KEY = "26c01b09f8083e30a1ee9cb929188a74"
FRED_SERIES_LIST_URL = "https://api.stlouisfed.org/fred/series/search"
FRED_DATA_URL = "https://api.stlouisfed.org/fred/series/observations"

# Function to fetch ALL available FRED economic indicators
@st.cache_data
def fetch_all_fred_indicators():
    params = {
        "search_text": "",  # Empty search text returns all indicators
        "api_key": API_KEY,
        "file_type": "json",
    }

    response = requests.get(FRED_SERIES_LIST_URL, params=params)

    if response.status_code == 200:
        data = response.json()
        series_list = data.get("seriess", [])

        # Extract only ID and Title
        series_dict = {s["id"]: s["title"] for s in series_list}
        return series_dict
    else:
        st.error(f"Error {response.status_code}: {response.text}")
        return {}

# Function to fetch FRED data for a selected indicator
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

# Load all economic indicators dynamically
st.text("Fetching available economic indicators from FRED...")
fred_series_dict = fetch_all_fred_indicators()

# Dropdown menu for FRED Series Selection
if fred_series_dict:
    series_id = st.selectbox(
        "Select a FRED Economic Indicator:",
        options=list(fred_series_dict.keys()),
        format_func=lambda x: fred_series_dict[x]  # Show descriptions
    )

    # Date range selection
    start_date = st.date_input("Start Date", pd.to_datetime("2000-01-01"))
    end_date = st.date_input("End Date", pd.to_datetime("2025-12-31"))

    # Fetch and display data
    if st.button("Fetch Data"):
        df = get_fred_data(series_id, start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))

        if df is not None:
            st.subheader(f"Data for {fred_series_dict[series_id]} ({series_id})")
            st.dataframe(df)  # Display table

            # Plot data
            st.subheader("📈 Data Visualization")
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(df["date"], df["value"], marker="o", linestyle="-", color="blue", label=fred_series_dict[series_id])
            ax.set_title(f"{fred_series_dict[series_id]} Over Time")
            ax.set_xlabel("Date")
            ax.set_ylabel("Value")
            ax.legend()
            ax.grid()
            st.pyplot(fig)
        else:
            st.warning("No data found for the given series ID and date range.")

else:
    st.warning("No economic indicators found. Please check your FRED API key.")

# Footer
st.markdown("Data sourced from [FRED](https://fred.stlouisfed.org/) by the Federal Reserve Bank of St. Louis.")
