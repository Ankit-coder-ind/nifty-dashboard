import pandas as pd
import yfinance as yf
import pandas_ta as ta
import requests
from datetime import datetime

# --- CONFIGURATION & DATA SOURCE LINKS ---
# These are the direct CSV links from niftyindices.com
NIFTY_500_URL = "https://niftyindices.com/IndexConstituent/ind_nifty500list.csv"
FNO_LIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"] # Add all FnO tickers here

SECTOR_MAP = {
    "NIFTY BANK": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY REALTY": "^CNXREALTY"
}

def get_data(ticker):
    try:
        df = yf.download(ticker, period="1y", interval="1d", progress=False)
        if df.empty: return None
        # Indicators
        df['SMA50'] = ta.sma(df['Close'], length=50)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        # Stoch RSI (SMI %K)
        stoch = ta.stochrsi(df['Close'], length=14, rsi_length=14, k=3, d=3)
        df = pd.concat([df, stoch], axis=1)
        return df
    except: return None

# 1) SECTOR ANALYSIS
sectors_above = []
sectors_below = []
for name, symbol in SECTOR_MAP.items():
    df = get_data(symbol)
    if df is not None:
        curr = df.iloc[-1]
        data = {"Sector": name, "Value": round(curr['Close'], 2), "SMA50": round(curr['SMA50'], 2)}
        if curr['Close'] >= curr['SMA50']: sectors_above.append(data)
        else: sectors_below.append(data)

# 2) MARKET BREADTH (Sample of Nifty 500 for speed)
try:
    n500_df = pd.read_csv(NIFTY_500_URL)
    n500_tickers = (n500_df['Symbol'] + ".NS").tolist()[:50] # Taking first 50 for demo
except:
    n500_tickers = ["RELIANCE.NS", "TCS.NS"]

breadth_bull = []
breadth_bear = []
for t in n500_tickers:
    df = get_data(t)
    if df is not None:
        curr = df.iloc[-1]
        row = {"Stock": t, "SMA50": round(curr['SMA50'], 2), "SMA200": round(curr['SMA200'], 2)}
        if curr['Close'] > curr['SMA200'] and curr['Close'] >= curr['SMA50']: breadth_bull.append(row)
        elif curr['Close'] < curr['SMA200'] and curr['Close'] <= curr['SMA50']: breadth_bear.append(row)

# 3 & 4) BULLISH & BEARISH FnO
fno_bull = []
fno_bear = []
for t in FNO_LIST:
    df = get_data(t)
    if df is not None:
        curr, prev = df.iloc[-1], df.iloc[-2]
        k, d = 'STOCHRSIk_14_14_3_3', 'STOCHRSId_14_14_3_3'
        
        # Bullish Logic
        if curr['Close'] > curr['SMA200'] and curr['Close'] >= curr['SMA50']:
            if prev[k] <= prev[d] and curr[k] > curr[d]: fno_bull.append(t)
        # Bearish Logic
        if curr['Close'] < curr['SMA200'] and curr['Close'] <= curr['SMA50']:
            if prev[k] >= prev[d] and curr[k] < curr[d]: fno_bear.append(t)

# --- GENERATE HTML ---
html_content = f"""
<html>
<head>
    <title>NSE Dashboard</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
</head>
<body class="bg-light p-4">
    <h1 class="text-center mb-4">NSE Market Analysis Dashboard</h1>
    <p class="text-center text-muted">Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    
    <div class="row">
        <div class="col-md-6">
            <h3>Sectors Above SMA50</h3>
            {pd.DataFrame(sectors_above).to_html(classes='table table-success table-striped', index=False)}
        </div>
        <div class="col-md-6">
            <h3>Sectors Below SMA50</h3>
            {pd.DataFrame(sectors_below).to_html(classes='table table-danger table-striped', index=False)}
        </div>
    </div>

    <hr>
    <h3>Market Breadth (Bullish/Bearish Trends)</h3>
    <div class="row">
        <div class="col-md-6">
            <h5>Greater than SMA200 & SMA50 (Count: {len(breadth_bull)})</h5>
            {pd.DataFrame(breadth_bull).to_html(classes='table table-sm table-bordered', index=False)}
        </div>
        <div class="col-md-6">
            <h5>Less than SMA200 & SMA50 (Count: {len(breadth_bear)})</h5>
            {pd.DataFrame(breadth_bear).to_html(classes='table table-sm table-bordered', index=False)}
        </div>
    </div>

    <hr>
    <div class="row text-center">
        <div class="col-md-6">
            <div class="card bg-success text-white">
                <div class="card-body"><h3>Bullish FnO Stocks</h3><p>{", ".join(fno_bull)}</p></div>
            </div>
        </div>
        <div class="col-md-6">
            <div class="card bg-danger text-white">
                <div class="card-body"><h3>Bearish FnO Stocks</h3><p>{", ".join(fno_bear)}</p></div>
            </div>
        </div>
    </div>
</body>
</html>
"""

with open("dashboard.html", "w") as f:
    f.write(html_content)
print("Dashboard generated: dashboard.html")
