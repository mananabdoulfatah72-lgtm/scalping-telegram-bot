import os
import requests

# Récupération des secrets
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("CHAT_ID")

# Vérifie que les secrets existent
if not token or not chat_id:
    raise Exception("Erreur : Token ou Chat ID manquant !")

# Envoie un message de test sur Telegram
requests.get(f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text=Bot actif ✅")
print("Message envoyé, le bot fonctionne !")

