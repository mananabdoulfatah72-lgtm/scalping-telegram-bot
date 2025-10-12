
#!/usr/bin/env python3
# main.py — Bot Scalping M5 Pro pour GitHub Actions

import os
import sys
import pandas as pd
import numpy as np
import requests
from urllib import request as urlrequest, parse

# ------------------------
# 🔐 Telegram Secrets
# ------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("⚠️ TELEGRAM_TOKEN ou CHAT_ID manquant dans les secrets GitHub")
    sys.exit(0)

# ------------------------
# 📤 Envoi d'un message Telegram
# ------------------------
def send_telegram(msg: str):
    qmsg = parse.quote_plus(msg)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={parse.quote_plus(CHAT_ID)}&text={qmsg}"
    try:
        with urlrequest.urlopen(url, timeout=10) as resp:
            resp.read()
    except Exception as e:
        print("❌ Erreur envoi Telegram :", e)

# ------------------------
# 📊 Téléchargement des bougies M5 (Binance)
# ------------------------
def get_klines(symbol: str, interval="5m", limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        data = requests.get(url, timeout=10).json()
    except Exception as e:
        print(f"❌ Erreur API Binance {symbol} :", e)
        return None

    df = pd.DataFrame(data, columns=[
        'time','open','high','low','close','volume','close_time',
        'quote','trades','tb_base','tb_quote','ignore'
    ])
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['volume'] = df['volume'].astype(float)
    return df

# ------------------------
# 🧮 Indicateurs techniques
# ------------------------
def ema(series: pd.Series, period: int):
    return series.ewm(span=period, adjust=False).mean()

def rsi(series: pd.Series, period=7):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

# ------------------------
# 🚀 Logique scalping EMA/RSI/Volume
# ------------------------
def scalping_signal(symbol: str):
    df = get_klines(symbol)
    if df is None or df.empty:
        return

    df['EMA9'] = ema(df['close'], 9)
    df['EMA21'] = ema(df['close'], 21)
    df['RSI7'] = rsi(df['close'], 7)
    df['VOL_MOY'] = df['volume'].rolling(20).mean()

    last = df.iloc[-1]

    # Conditions achat scalping
    if last['EMA9'] > last['EMA21'] and last['RSI7'] > 50 and last['volume'] > last['VOL_MOY']:
        send_telegram(
            f"🟢 [Scalping M5] Signal ACHAT sur {symbol}\n"
            f"EMA9>EMA21 | RSI7={last['RSI7']:.1f} | Volume fort"
        )

    # Conditions vente scalping
    elif last['EMA9'] < last['EMA21'] and last['RSI7'] < 50 and last['volume'] > last['VOL_MOY']:
        send_telegram(
            f"🔴 [Scalping M5] Signal VENTE sur {symbol}\n"
            f"EMA9<EMA21 | RSI7={last['RSI7']:.1f} | Volume fort"
        )

    else:
        print(f"⏸ {symbol}: Aucun signal clair cette itération")

# ------------------------
# 📌 Exécution principale
# ------------------------
SYMBOLS = ["BTCUSDT", "ETHUSDT", "XAUUSDT"]

for sym in SYMBOLS:
    scalping_signal(sym)

print("✅ Script scalping exécuté avec succès")
sys.exit(0)



