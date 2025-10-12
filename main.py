#!/usr/bin/env python3
# main.py — test minimal pour GitHub Actions / Telegram
import os
import sys
import time
import logging
from urllib import request, parse, error

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger("gh-telegram-test")

# noms possibles de secrets (vérifie lesquels tu as mis dans GitHub)
TOKEN_NAMES = ["TELEGRAM_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT", "TELEGRAM_API_TOKEN"]
CHAT_NAMES = ["CHAT_ID", "TELEGRAM_CHAT_ID", "TELEGRAM_CHAT"]

def first_env(names):
    for n in names:
        v = os.getenv(n)
        if v:
            return n, v
    return None, None

tok_name, token = first_env(TOKEN_NAMES)
chat_name, chat_id = first_env(CHAT_NAMES)

if not token or not chat_id:
    logger.warning("Secrets manquants -> token trouvé: %s, chat trouvé: %s", bool(token), bool(chat_id))
    logger.info("Vérifie dans Settings > Secrets du dépôt que tu as bien défini un secret nommé par exemple TELEGRAM_BOT_TOKEN et TELEGRAM_CHAT_ID.")
    # Ne pas planter : on veut que le workflow passe pour debug
    sys.exit(0)

# message de test (sera affiché dans les logs GitHub)
msg = f"Test GitHub Actions -> bot OK ({time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())} UTC). token_env={tok_name}, chat_env={chat_name}"
qmsg = parse.quote_plus(msg)

url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={parse.quote_plus(chat_id)}&text={qmsg}"

try:
    logger.info("Envoi du message de test à Telegram...")
    with request.urlopen(url, timeout=15) as resp:
        body = resp.read().decode("utf-8", errors="ignore")
        logger.info("Réponse Telegram: %s", body)
except error.HTTPError as e:
    try:
        body = e.read().decode("utf-8", errors="ignore")
    except Exception:
        body = "<cannot read body>"
    logger.error("HTTPError %s -> %s", getattr(e, "code", "N/A"), body)
except Exception as e:
    logger.exception("Erreur lors de l'appel HTTP: %s", e)

logger.info("Script terminé normalement (exit 0).")
sys.exit(0)


