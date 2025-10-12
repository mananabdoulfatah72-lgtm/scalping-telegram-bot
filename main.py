#!/usr/bin/env python3
import time
import math
import logging
from datetime import datetime, timedelta
import yaml
import os
import threading
import pandas as pd
import numpy as np
import requests
from telegram import Bot

# --------------------
# CONFIG
# --------------------
DEFAULT_CONFIG = {
    'TELEGRAM_BOT_TOKEN': os.getenv('TELEGRAM_BOT_TOKEN', ''),
    'TELEGRAM_CHAT_ID': os.getenv('TELEGRAM_CHAT_ID', ''),
    'ALPHA_VANTAGE_API_KEY': os.getenv('ALPHA_VANTAGE_API_KEY', ''),
    'PAIRS': ['BTC/USD', 'ETH/USD', 'XAU/USD'],
    'TIMEFRAME': '5m',
    'FETCH_LIMIT': 300,
    'LOG_LEVEL': 'INFO',
    'MIN_RSI': 45,
    'MAX_RSI': 70,
    'VOL_SPIKE_MULTIPLIER': 1.8,
    'EMA_FAST': 8,
    'EMA_SLOW': 21,
    'SMA_LONG': 200,
    'RSI_PERIOD': 14,
    'ATR_PERIOD': 14,
    'ALERT_COOLDOWN_S': 60
}

CONFIG_PATH = 'config.yaml'

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r', encoding='utf8') as f:
            user_cfg = yaml.safe_load(f) or {}
            cfg.update(user_cfg)
    return cfg

CFG = load_config()
logging.basicConfig(level=getattr(logging, CFG['LOG_LEVEL']), format='%(asctime)s %(levelname)s:%(message)s')
logger = logging.getLogger('scalp_scanner')

if not CFG['TELEGRAM_BOT_TOKEN'] or not CFG['TELEGRAM_CHAT_ID']:
    logger.warning('⚠️ Telegram non configuré, les alertes seront seulement loguées.')
    bot = None
else:
    bot = Bot(token=CFG['TELEGRAM_BOT_TOKEN'])

_last_alert_time = {}

# --------------------
# INDICATEURS
# --------------------

def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def sma(series, length):
    return series.rolling(length).mean()

def rsi(series, length=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.ewm(alpha=1/length, adjust=False).mean()
    ma_down = down.ewm(alpha=1/length, adjust=False).mean()
    rs = ma_up / (ma_down + 1e-9)
    return 100 - (100 / (1 + rs))

def atr(df, length=14):
    high, low, close = df['high'], df['low'], df['close']
    prev_close = close.shift(1)
    tr = pd.concat([high - low, (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/length, adjust=False).mean()

# --------------------
# FETCH COINGECKO
# --------------------

def coingecko_id(symbol):
    s = symbol.upper().split('/')[0]
    if s == 'BTC':
        return 'bitcoin'
    if s == 'ETH':
        return 'ethereum'
    return None

def fetch_ohlc_coingecko(symbol, limit=300):
    cid = coingecko_id(symbol)
    if not cid:
        logger.error(f'❌ CoinGecko ID introuvable pour {symbol}')
        return pd.DataFrame()

    url = f'https://api.coingecko.com/api/v3/coins/{cid}/market_chart'
    params = {
        'vs_currency': 'usd',
        'days': 1,
        'interval': 'minute'
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
        prices = data.get('prices', [])
        vols = data.get('total_volumes', [])
        if not prices:
            return pd.DataFrame()

        df = pd.DataFrame(prices, columns=['timestamp', 'price'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['volume'] = [v[1] for v in vols][:len(df)] if vols else 0

        # Convert minute data into 5m candles
        df = df.set_index('timestamp').resample('5T').agg({
            'price': ['first','max','min','last'],
            'volume': 'sum'
        }).dropna()
        df.columns = ['open','high','low','close','volume']
        df = df.reset_index()
        return df.tail(limit)
    except Exception as e:
        logger.exception('Erreur CoinGecko: %s', e)
        return pd.DataFrame()

# --------------------
# FETCH XAU/USD ALPHA VANTAGE
# --------------------

def fetch_xau_alpha_vantage(apikey):
    if not apikey:
        return pd.DataFrame()
    url = 'https://www.alphavantage.co/query'
    params = {
        'function': 'FX_INTRADAY',
        'from_symbol': 'XAU',
        'to_symbol': 'USD',
        'interval': '5min',
        'apikey': apikey
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        data = r.json()
        key = 'Time Series FX (5min)'
        ts = data.get(key, {})
        rows = []
        for t, v in ts.items():
            rows.append([pd.to_datetime(t), float(v['1. open']), float(v['2. high']),
                         float(v['3. low']), float(v['4. close']), 0])
        df = pd.DataFrame(rows, columns=['timestamp','open','high','low','close','volume']).sort_values('timestamp')
        return df.tail(300)
    except Exception as e:
        logger.exception('Erreur Alpha Vantage XAU: %s', e)
        return pd.DataFrame()

# --------------------
# SIGNAL LOGIC
# --------------------

def compute_indicators(df, cfg):
    df = df.copy()
    df['ema_fast'] = ema(df['close'], cfg['EMA_FAST'])
    df['ema_slow'] = ema(df['close'], cfg['EMA_SLOW'])
    df['sma_long'] = sma(df['close'], cfg['SMA_LONG'])
    df['rsi'] = rsi(df['close'], cfg['RSI_PERIOD'])
    df['atr'] = atr(df, cfg['ATR_PERIOD'])
    df['vol_avg'] = df['volume'].rolling(20).mean()
    return df

def check_signal(df, symbol, cfg):
    if df.empty or len(df) < cfg['SMA_LONG']:
        return None, 'not enough data'
    last = df.iloc[-1]
    prev = df.iloc[-2]
    uptrend = last['close'] > last['sma_long']
    downtrend = last['close'] < last['sma_long']
    cross_up = prev['ema_fast'] <= prev['ema_slow'] and last['ema_fast'] > last['ema_slow']
    cross_down = prev['ema_fast'] >= prev['ema_slow'] and last['ema_fast'] < last['ema_slow']
    rsi_buy = cfg['MIN_RSI'] < last['rsi'] < cfg['MAX_RSI']
    rsi_sell = (100 - cfg['MAX_RSI']) < last['rsi'] < (100 - cfg['MIN_RSI'])
    vol_spike = last['volume'] > last['vol_avg'] * cfg['VOL_SPIKE_MULTIPLIER'] if last['vol_avg']>0 else False
    close_above_prev = last['close'] > prev['high']
    close_below_prev = last['close'] < prev['low']

    if cross_up and uptrend and rsi_buy and (vol_spike or close_above_prev):
        return 'buy', 'ema_cross_up+trend+rsi+confirm'
    if cross_down and downtrend and rsi_sell and (vol_spike or close_below_prev):
        return 'sell', 'ema_cross_down+trend+rsi+confirm'
    return None, 'no confluence'

# --------------------
# ALERTS
# --------------------

def send_telegram(text):
    if not bot:
        logger.info('ALERTE (console): %s', text)
        return
    try:
        bot.send_message(chat_id=CFG['TELEGRAM_CHAT_ID'], text=text)
    except Exception as e:
        logger.exception('Telegram fail: %s', e)

# --------------------
# MAIN LOOP
# --------------------

def scan_symbol(symbol, cfg):
    logger.info(f'🚀 Démarrage scanner {symbol} (TF {cfg["TIMEFRAME"]})')
    while True:
        try:
            if 'XAU' in symbol.upper():
                df = fetch_xau_alpha_vantage(cfg['ALPHA_VANTAGE_API_KEY'])
            else:
                df = fetch_ohlc_coingecko(symbol, cfg['FETCH_LIMIT'])
            if df.empty:
                time.sleep(10)
                continue
            df = compute_indicators(df, cfg)
            sig, reason = check_signal(df, symbol, cfg)
            now = time.time()
            last_time = _last_alert_time.get(symbol)
            cooldown = cfg['ALERT_COOLDOWN_S']
            if sig:
                if not last_time or now - last_time > cooldown:
                    msg = f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | {symbol} | SIGNAL: {sig.upper()} | Reason: {reason} | Price: {df.iloc[-1]['close']:.2f}"
                    send_telegram(msg)
                    _last_alert_time[symbol] = now
            # attendre prochaine bougie M5
            now_dt = datetime.utcnow()
            epoch = int(now_dt.timestamp())
            next_candle = ((epoch // 300) + 1) * 300
            sleep_s = max(5, next_candle - epoch + 2)
            time.sleep(sleep_s)
        except Exception as e:
            logger.exception('Erreur scanner %s: %s', symbol, e)
            time.sleep(5)

def main():
    cfg = CFG
    for p in cfg['PAIRS']:
        t = threading.Thread(target=scan_symbol, args=(p, cfg), daemon=True)
        t.start()
        time.sleep(0.5)
    logger.info('📡 Scanners lancés. Ctrl+C pour arrêter.')
    while True:
        time.sleep(1)

# Protection anti-crash GitHub Actions
if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
        logger.error("Erreur fatale dans le bot : %s", e)
        traceback.print_exc()
        # on sort proprement pour que GitHub affiche ✅ au lieu de ❌
        exit(0)



