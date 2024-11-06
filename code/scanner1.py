import logging
from fastapi import FastAPI, Query, Response
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import os
from apscheduler.schedulers.background import BackgroundScheduler
import requests

# Initialize logger
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Directory to store historical results
HISTORY_DIR = "./scan_history"
os.makedirs(HISTORY_DIR, exist_ok=True)

def get_tickers():
    """Fetch tickers dynamically for S&P 500, NIFTY 50, and BSE SENSEX."""
    tickers = []

    try:
        # Fetch S&P 500 tickers
        sp500_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        sp500_table = pd.read_html(sp500_url)[0]
        sp500_tickers = sp500_table["Symbol"].tolist()
        tickers.extend(sp500_tickers)
        logging.info(f"Fetched {len(sp500_tickers)} S&P 500 tickers.")

        # Fetching NIFTY 50 tickers (use "Symbol" instead of "Company Name")
        nifty50_url = "https://en.wikipedia.org/wiki/NIFTY_50"
        nifty50_table = pd.read_html(nifty50_url)[1]
        logging.info(f"NIFTY 50 Table Columns: {nifty50_table.columns}")
        nifty50_tickers = nifty50_table["Symbol"].tolist()
        tickers.extend([f"{ticker}.NS" for ticker in nifty50_tickers])
        logging.info(f"Fetched {len(nifty50_tickers)} NIFTY 50 tickers.")

        # Fetching BSE SENSEX tickers from Wikipedia
        sensex_url = "https://en.wikipedia.org/wiki/List_of_BSE_SENSEX_companies"
        sensex_table = pd.read_html(sensex_url)[0]
        logging.info(f"SENSEX Table Columns: {sensex_table.columns}")

        # Extract symbols and ensure ".BO" is added only if missing
        sensex_tickers = [
            f"{ticker}.BO" if not ticker.endswith(".BO") else ticker
            for ticker in sensex_table["Symbol"].tolist()
        ]
        tickers.extend(sensex_tickers)
        logging.info(f"Fetched {len(sensex_tickers)} BSE SENSEX tickers.")

        return tickers
    
    except Exception as e:
        logging.error(f"Failed to fetch tickers: {str(e)}")

    return tickers

def get_file_name():
    """Generate filename with the current date and day."""
    now = datetime.now()
    return f"{now.strftime('%Y-%m-%d_%A')}.csv"

def save_scan_results(df):
    """Save the scan results to a CSV file."""
    file_name = get_file_name()
    file_path = os.path.join(HISTORY_DIR, file_name)
    df.to_csv(file_path, index=False)
    logging.info(f"Results saved to {file_path}")

def get_scan_history():
    """Get the list of saved scan files."""
    return [f for f in os.listdir(HISTORY_DIR) if f.endswith(".csv")]

@app.get("/")
def read_root():
    """Display available scan history."""
    history_files = get_scan_history()
    return {
        "message": "Welcome to the Stock Scanner API.",
        "history": [{"file_name": f, "url": f"/download/{f}"} for f in history_files]
    }

@app.get("/scan")
async def scan_stocks(
    min_return: float = Query(0.0, description="Minimum return over the period (e.g., 0.0 for 0%)"),
    years: int = Query(7, description="Number of years for the scan")
):
    """Perform a stock scan and save the results."""
    try:
        tickers = get_tickers()
        today = datetime.today()
        start_date = today - timedelta(days=years * 365)

        logging.info(f"Scanning stocks from {start_date.date()} to {today.date()}")
        results = []

        for ticker in tickers:
            logging.info(f"Fetching data for: {ticker}")
            data = yf.download(ticker, start=start_date, end=today, progress=False)

            if isinstance(data.columns, pd.MultiIndex):
                data.columns = ['_'.join(col).strip() for col in data.columns]

            adj_close_column = f"Adj Close_{ticker}" if f"Adj Close_{ticker}" in data.columns else "Adj Close"
            if adj_close_column not in data.columns:
                logging.warning(f"No valid '{adj_close_column}' data for {ticker}. Skipping...")
                continue

            data = data.dropna(subset=[adj_close_column])
            if len(data) < 2:
                logging.warning(f"Not enough data points for {ticker}. Skipping...")
                continue

            start_price = data[adj_close_column].iloc[0]
            end_price = data[adj_close_column].iloc[-1]
            percent_return = ((end_price - start_price) / start_price) * 100

            logging.info(f"{ticker}: Start Price = {start_price}, End Price = {end_price}, Return = {percent_return}%")
            if percent_return <= min_return:
                results.append({"Ticker": ticker, "Return": round(percent_return, 2)})

        df = pd.DataFrame(results)
        logging.info(f"Total matching stocks: {len(df)}")
        save_scan_results(df)
        return {"status": "success", "data": df.to_dict(orient="records")}

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/download/{file_name}")
def download_file(file_name: str, response: Response):
    """Download a specific scan result file."""
    file_path = os.path.join(HISTORY_DIR, file_name)
    if not os.path.exists(file_path):
        return {"status": "error", "message": "File not found."}

    response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
    with open(file_path, "rb") as f:
        return Response(f.read(), media_type="text/csv")

def run_daily_scan():
    """Function to run the scan automatically at a scheduled time."""
    logging.info("Running daily scan...")
    try:
        response = requests.get("http://127.0.0.1:8000/scan?min_return=0&years=7")
        logging.info(f"Daily scan completed with status: {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to run daily scan: {str(e)}")

# Schedule the scan to run at 4:30 PM daily
scheduler = BackgroundScheduler()
scheduler.add_job(run_daily_scan, 'cron', hour=16, minute=30)
scheduler.start()

#uvicorn scanner1:app --reload