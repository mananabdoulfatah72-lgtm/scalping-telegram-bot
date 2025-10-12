#!/usr/bin/env python3
# main.py — Scalping une seule itération pour GitHub Actions
import os
import sys
import time
import json
from urllib import request, parse, error

# ------------------------
# ⚙️ Secrets
# ------------------------
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    print("⚠️ TELEGRAM_TOKEN ou CHAT_ID manquant dans les secrets GitHub")
    sys.exit(0)  # on ne plante pas

# ------------------------
# 📈 Paramètres
# ------------------------
SYMBOLS = {
    "bitcoin": "BTC/USD",
    "ethereum": "ETH/USD",
    "gold": "XAU/USD"
}
CHANGE_ALERT = 0.2  # % variation

# cache des prix dans un fichier JSON temporaire pour comparer d'un run à l'autre
CACHE_FILE = "price_cache.json"

try:
    with open(CACHE_FILE, "r") as f:
        PRICE_CACHE = json.load(f)
except Exception:
    PRICE_CACHE = {}

# ------------------------
# 📊 Récupération prix Coingecko
# ------------------------
def get_price(symbol_id):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol_id}&vs_currencies=usd"
    try:
        with request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data[symbol_id]["usd"]
    except Exception as e:
        print(f"❌ Erreur API Coingecko {symbol_id} :", e)
        return None

# ------------------------
# 📤 Envoi Telegram
# ------------------------
def send_telegram(msg):
    qmsg = parse.quote_plus(msg)
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage?chat_id={parse.quote_plus(CHAT_ID)}&text={qmsg}"
    try:
        with request.urlopen(url, timeout=10) as resp:
            resp.read()
    except Exception as e:
        print("❌ Erreur envoi Telegram :", e)

# ------------------------
# 🚀 Exécution unique
# ------------------------
alerts = []
for symbol_id, display_name in SYMBOLS.items():
    price = get_price(symbol_id)
    if price is None:
        continue

    last_price = PRICE_CACHE.get(symbol_id)
    if last_price:
        change = ((price - last_price) / last_price) * 100
        if abs(change) >= CHANGE_ALERT:
            alerts.append(f"📊 {display_name} : {price}$ ({change:.2f}%)")
    PRICE_CACHE[symbol_id] = price

# envoie une alerte s'il y a eu mouvement
if alerts:
    send_telegram("\n".join(alerts))
else:
    print("Aucune alerte détectée cette itération ✅")

# sauvegarde le cache pour la prochaine exécution
with open(CACHE_FILE, "w") as f:
    json.dump(PRICE_CACHE, f)

print("Script terminé normalement ✅")
sys.exit(0)




