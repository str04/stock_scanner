import yfinance as yf
import pandas as pd
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt

# Streamlit App Header
st.title("Lifetime High Stock Scanner")
st.write(
    "This tool scans stocks for instances where they reached a lifetime high, "
    "held it as support, and experienced significant price appreciation."
)

# User Inputs for Tickers and Threshold
tickers = st.text_input(
    "Enter Stock Tickers (comma-separated, e.g., RELIANCE.NS, TCS.NS, AAPL)", 
    "RELIANCE.NS, TCS.NS, AAPL"
)
threshold = st.slider(
    "Select Appreciation Threshold (%)", min_value=5, max_value=50, value=10
)
analyze_button = st.button("Analyze Stocks")

def fetch_stock_data(ticker, period="10y", interval="1d"):
    """Fetch historical stock data using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period=period, interval=interval)
        if data.empty:
            st.warning(f"No data found for {ticker}. Skipping.")
            return None
        data.reset_index(inplace=True)  # Ensure 'Date' is a column, not an index
        return data
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")
        return None

def detect_lifetime_highs(data):
    """Detect lifetime highs from the stock data."""
    data['Lifetime_High'] = data['Close'].cummax()
    data['Is_High'] = np.where(data['Close'] == data['Lifetime_High'], 1, 0)
    return data

def find_support_and_appreciation(data, threshold=0.10):
    """Identify instances where lifetime high acted as support with appreciation."""
    opportunities = []
    for i in range(1, len(data)):
        if data['Is_High'].iloc[i - 1] == 1:  # Found a lifetime high
            support_region = data['Low'].iloc[i:i + 10].min()  # Look ahead 10 days
            if support_region >= data['Lifetime_High'].iloc[i - 1] * 0.98:  # Holds support
                future_price = data['Close'].iloc[i + 10:i + 30].max()  # Next 20 days
                appreciation = (future_price - data['Lifetime_High'].iloc[i - 1]) / data['Lifetime_High'].iloc[i - 1]
                
                if appreciation >= threshold:  # Appreciates by threshold
                    opportunities.append({
                        "Date": data['Date'].iloc[i],  # Ensure 'Date' is accessed correctly
                        "Lifetime_High": data['Lifetime_High'].iloc[i - 1],
                        "Appreciation": round(appreciation * 100, 2)
                    })
    return pd.DataFrame(opportunities)

def analyze_stocks(tickers, threshold=0.10):
    """Analyze multiple stocks and find opportunities."""
    results = []
    for ticker in tickers:
        st.write(f"Analyzing {ticker}...")
        data = fetch_stock_data(ticker)
        if data is not None:
            data = detect_lifetime_highs(data)
            opportunities = find_support_and_appreciation(data, threshold / 100)
            results.append((ticker, opportunities))
    return results

def provide_analysis_summary(ticker, opportunities):
    """Provide a detailed explanation of the analysis."""
    if opportunities.empty:
        st.write(f"No valid opportunities found for {ticker}.")
    else:
        st.write(f"### Summary for {ticker}")
        st.write(
            f"We identified **{len(opportunities)} opportunities** where the stock reached a lifetime high, "
            f"held that high as a **support level**, and appreciated by at least **{threshold}%** afterward."
        )
        st.write(
            "This pattern suggests that the stock has strong momentum and buyers are confident in maintaining the new high as a support level. "
            "Such price behavior is often seen in stocks with good growth potential."
        )

def display_results(results):
    """Display the results in Streamlit with charts and explanations."""
    total_instances = 0
    successful_instances = 0

    all_opportunities = pd.DataFrame()  # Initialize an empty DataFrame

    for ticker, opportunities in results:
        if opportunities.empty:
            st.warning(f"No valid data found for {ticker}. Skipping visualization.")
            continue

        st.subheader(f"Results for {ticker}")
        st.write(opportunities)  # Display the DataFrame to check its content

        total_instances += len(opportunities)
        successful_instances += len(opportunities[opportunities['Appreciation'] >= threshold])

        # Accumulate all opportunities for further analysis
        all_opportunities = pd.concat([all_opportunities, opportunities], ignore_index=True)

        # Provide detailed analysis for each stock
        provide_analysis_summary(ticker, opportunities)

    if total_instances == 0:
        st.error("No opportunities found for the provided tickers and threshold.")
        return

    success_rate = (successful_instances / total_instances) * 100 if total_instances > 0 else 0
    st.write(f"### Overall Summary")
    st.write(f"**Total Opportunities Identified:** {total_instances}")
    st.write(f"**Successful Instances (above threshold):** {successful_instances}")
    st.write(f"**Success Rate:** {round(success_rate, 2)}%")

    # Ensure the 'Date' column is in datetime format
    if not all_opportunities.empty:
        all_opportunities['Date'] = pd.to_datetime(all_opportunities['Date'], errors='coerce')
        valid_dates = all_opportunities['Date'].notna()  # Filter out invalid dates
        all_opportunities = all_opportunities[valid_dates]

        # Now safely access the 'Year' column
        all_opportunities['Year'] = all_opportunities['Date'].dt.year

        # Group by year and show annual opportunities
        annual_opportunities = all_opportunities.groupby('Year').size()
        st.write("### Annual Opportunities Overview")
        st.write(
            "The chart below shows the number of identified opportunities each year. "
            "This helps you see if such patterns are more frequent in certain periods."
        )
        st.bar_chart(annual_opportunities)

# Run Analysis when Button is Clicked
if analyze_button:
    ticker_list = [ticker.strip().upper() for ticker in tickers.split(",")]
    results = analyze_stocks(ticker_list, threshold)
    display_results(results)

#streamlit run scanner2.py
