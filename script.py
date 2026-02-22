import pandas as pd
import yfinance as yf
import requests
from datetime import datetime

def calculate_indicators(df):
    # 50 & 200 SMA
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    df['SMA200'] = df['Close'].rolling(window=200).mean()
    
    # Stochastic RSI (SMI %K) Logic
    rsi_period = 14
    stoch_period = 14
    k_period = 3
    
    # Calculate RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Calculate Stochastic RSI
    min_rsi = df['RSI'].rolling(window=stoch_period).min()
    max_rsi = df['RSI'].rolling(window=stoch_period).max()
    df['stoch_rsi'] = (df['RSI'] - min_rsi) / (max_rsi - min_rsi)
    df['SMI_K'] = df['stoch_rsi'].rolling(window=k_period).mean() * 100
    df['SMI_D'] = df['SMI_K'].rolling(window=3).mean() # Signal line
    return df

# Fetch Sector List from NiftyIndices (Using placeholder for stability)
# Note: Real-time web scraping can be fragile; we use major NSE sector indices
sectors = {"Nifty Bank": "^NSEBANK", "Nifty IT": "^CNXIT", "Nifty Auto": "^CNXAUTO", 
           "Nifty Pharma": "^CNXPHARMA", "Nifty FMCG": "^CNXFMCG"}

sector_above = []
sector_below = []

for name, symbol in sectors.items():
    df = yf.download(symbol, period="1y", interval="1d", progress=False)
    if not df.empty:
        df = calculate_indicators(df)
        curr = df.iloc[-1]
        data = {"Sector": name, "Price": round(curr['Close'], 2), "SMA50": round(curr['SMA50'], 2)}
        if curr['Close'] > curr['SMA50']: sector_above.append(data)
        else: sector_below.append(data)

# --- GENERATE CLEAN HTML ---
html = f"""
<html>
<head>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <style> body {{ padding: 20px; background: #f8f9fa; }} .card {{ margin-bottom: 20px; }} </style>
</head>
<body>
    <h2 class="text-center">NSE Dashboard - {datetime.now().strftime('%Y-%m-%d')}</h2>
    <div class="row">
        <div class="col-md-6">
            <div class="card border-success"><div class="card-header bg-success text-white">Sectors ABOVE SMA 50</div>
            <div class="card-body">{pd.DataFrame(sector_above).to_html(classes='table', index=False)}</div></div>
        </div>
        <div class="col-md-6">
            <div class="card border-danger"><div class="card-header bg-danger text-white">Sectors BELOW SMA 50</div>
            <div class="card-body">{pd.DataFrame(sector_below).to_html(classes='table', index=False)}</div></div>
        </div>
    </div>
</body>
</html>
"""

with open("index.html", "w") as f:
    f.write(html)
