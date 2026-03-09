# Clause

## Project Overview

`fred_stats_app.py` is a Streamlit dashboard that combines Yahoo Finance stock data with FRED (Federal Reserve Economic Data) macroeconomic indicators.

## Features

- **Key Financials**: Displays Total Revenue, Gross Profit, EBIT, and EBITDA in millions for the last 5 fiscal years for any given ticker.
- **Year-over-Year Growth**: Calculates and displays percentage growth for each financial metric across years.
- **Working Capital Metrics**: Computes Days Inventory Outstanding (DIO), Days Sales Outstanding (DSO), Days Payable Outstanding (DPO), and Cash Conversion Cycle (CCC) for the last 3 years.
- **FRED Inventory/Sales Ratio**: Fetches and plots the Inventory/Sales Ratio for Building Materials & Garden Equipment Dealers (`MRTSIR444USS`) from the FRED API over a user-selected date range.

## Data Sources

| Source | Description |
|--------|-------------|
| [Yahoo Finance](https://finance.yahoo.com) | Stock financials, balance sheet, and cash flow data via `yfinance` |
| [FRED API](https://fred.stlouisfed.org) | Federal Reserve macroeconomic series data |

## Dependencies

See `requirements.txt`. Key packages:

- `streamlit` — web app framework
- `yfinance` — Yahoo Finance data
- `pandas` — data manipulation
- `matplotlib` — charting
- `requests` — FRED API calls

## Usage

```bash
pip install -r requirements.txt
streamlit run fred_stats_app.py
```

Enter a stock ticker (e.g., `HD` for Home Depot) in the input field, then optionally fetch the FRED Inventory/Sales Ratio by selecting a date range and clicking **Fetch Inventory/Sales Ratio**.

## Disclaimer

Data is sourced from Yahoo Finance and the Federal Reserve Bank of St. Louis (FRED). This dashboard is intended for informational and educational purposes only and does not constitute financial advice.
