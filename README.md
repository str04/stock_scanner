# Stock Scanner Applications

This repository contains two distinct stock scanner applications:

1. **Daily Stock Return Scanner** (Built with FastAPI) - Identifies stocks with specific historical return patterns.
2. **Lifetime High Stock Scanner** (Built with Streamlit) - Detects stocks that have previously reached a lifetime high, used it as a support level, and subsequently appreciated in value.

## 1. Daily Stock Return Scanner

### Description

This application scans a dynamic list of stocks daily to find those with zero or custom-defined returns over a specified number of years. It uses FastAPI for the backend and provides endpoints to trigger scans, retrieve scan history, and download results. The application fetches stock data from the S&P 500, NIFTY 50, and BSE SENSEX indices.

### Use Case

This scanner helps traders and analysts identify stagnant stocks (those with 0% returns) over a specific period, providing insights for value-based or contrarian investing strategies. Analysts can adjust the `return` and `years` parameters to customize the screening process.

### Setup

1. Clone this repository.
2. Start the server:
   ```bash
   uvicorn scanner1:app --reload
   ```

### API Endpoints

- **GET `/scan`** - Runs the scan with adjustable parameters (`min_return`, `years`).
- **GET `/download/{file_name}`** - Downloads a specific scan result.
- **GET `/`** - Lists available scan history files.

## 2. Lifetime High Stock Scanner

### Description

This application detects instances where stocks have reached a lifetime high, held that high as support, and experienced significant price appreciation afterward. It leverages Streamlit for the frontend, allowing users to input tickers and set appreciation thresholds to filter for high-potential opportunities.

### Use Case

This tool helps in finding stocks with strong bullish momentum, where price levels previously marked as highs now act as support, signaling confidence from investors. The scanner analyzes data over a 10-year period, presenting annual opportunities and success rates for each stock.

### Setup

1. Clone this repository
2. Run the Streamlit app:
   ```bash
   streamlit run scanner2.py
   ```

### Features

- **Lifetime High Detection** - Identifies lifetime highs and examines if they act as support.
- **Threshold-Based Filtering** - Screens for stocks that appreciate beyond a user-defined threshold.
- **Annual Analysis** - Provides yearly insights into the frequency and success rate of identified opportunities.

---

Feel free to add additional details, such as API documentation, user instructions, or troubleshooting steps, as needed. Let me know if you need further customization!
