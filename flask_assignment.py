import os
import glob
import threading
import pandas as pd
import yfinance as yf
from flask import Flask, jsonify, request, send_file, abort
from datetime import datetime

app = Flask(__name__)

# --- CONFIG & STATE ---
TARGETS = [
    {"name": "Gold BeES", "symbol": "GOLDBEES.NS"},
    {"name": "Silver BeES", "symbol": "SILVERBEES.NS"},
    {"name": "Hindustan Copper", "symbol": "HINDCOPPER.NS"},
    {"name": "MAFANG ETF", "symbol": "MAFANG.NS"},
    {"name": "Nifty Alpha 50", "symbol": "ALPHALOW.NS"},
    {"name": "UTI Momentum 30", "symbol": "UTIMOMENTUM.NS"},
    {"name": "CPSE ETF", "symbol": "CPSEETF.NS"},
    {"name": "Nifty IT ETF", "symbol": "ITBEES.NS"},
    {"name": "Nifty Bank ETF", "symbol": "BANKBEES.NS"},
    {"name": "Nifty Auto ETF", "symbol": "AUTOBEES.NS"},
]

STATE = {
    "running": False,
    "progress": {"done": 0, "total": len(TARGETS)},
    "results": [],
    "excel_path": None
}
LOCK = threading.Lock()

# --- LOGIC FUNCTIONS ---

def compute_rsi_wilder(series, period=14):
    """Wilder's RSI: Industry standard vs simple SMA"""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).fillna(0)
    loss = (-delta.where(delta < 0, 0)).fillna(0)
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def run_scan():
    global STATE
    try:
        # Cleanup old files
        for f in glob.glob("Momentum_Report_*.xlsx"):
            try: os.remove(f)
            except: pass

        symbols = [t['symbol'] for t in TARGETS]
        data = yf.download(symbols, period="1y", interval="1d", group_by='ticker', progress=False)
        
        compiled_results = []
        for item in TARGETS:
            sym = item['symbol']
            df = data[sym].copy() if len(TARGETS) > 1 else data.copy()
            df.dropna(subset=['Close'], inplace=True)

            if len(df) < 150: continue

            close = df['Close']
            m50 = close.rolling(50).mean().iloc[-1]
            m150 = close.rolling(150).mean().iloc[-1]
            curr_p = close.iloc[-1]
            rsi = compute_rsi_wilder(close).iloc[-1]

            status = "Consolidating 🟡"
            if curr_p > m150 and m50 > m150: status = "STAGE 2 (BUY) 🟢"
            elif curr_p < m150: status = "Stage 4 (Avoid) 🔴"

            compiled_results.append({
                "Asset": item['name'], "Symbol": sym, "Price": round(float(curr_p), 2),
                "Trend": status, "RSI": round(float(rsi), 2), "MA50": round(float(m50), 2)
            })

        # Finalize Excel
        df_final = pd.DataFrame(compiled_results).sort_values(by="RSI", ascending=False)
        f_name = f"Momentum_Report_{datetime.now().strftime('%H%M%S')}.xlsx"
        df_final.to_excel(f_name, index=False)

        with LOCK:
            STATE["results"] = compiled_results
            STATE["excel_path"] = f_name
            STATE["running"] = False
    except Exception as e:
        with LOCK:
            STATE["running"] = False
            print(f"Error: {e}")

# --- ROUTES ---

@app.route("/")
def home():
    return "<h1>Momentum Scanner API</h1><p>Use /scan (POST), /status (GET), and /download (GET)</p>"

@app.post("/scan")
def start():
    with LOCK:
        if STATE["running"]: return jsonify({"error": "Scan already in progress"}), 409
        STATE["running"] = True
        threading.Thread(target=run_scan, daemon=True).start()
    return jsonify({"message": "Scan started"}), 202

@app.get("/status")
def get_status():
    return jsonify(STATE)

@app.get("/download")
def get_file():
    with LOCK:
        filename = STATE.get("excel_path")
    
    if not filename:
        abort(404, description="No report generated yet.")

    # Lead Engineer fix: Look in root directory for the file
    absolute_path = os.path.join(os.getcwd(), filename)
    
    if os.path.exists(absolute_path):
        return send_file(absolute_path, as_attachment=True)
    else:
        return jsonify({"error": "File missing on server", "path": absolute_path}), 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)