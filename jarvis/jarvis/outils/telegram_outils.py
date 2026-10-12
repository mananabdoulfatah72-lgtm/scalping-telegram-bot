"""Telegram : Jarvis t'écrit sur ton téléphone (la réception des messages est dans telegram.py)."""
from __future__ import annotations

from .. import reseau
from ..services import S
from . import ErreurOutil, module, outil, p


@module("telegram", "TELEGRAM")
def etat() -> tuple[str, str]:
    if not S.cfg.get("telegram.jeton", "") or not S.cfg.get("telegram.chat_id", ""):
        return "non_configure", "[telegram] jeton (BotFather) et chat_id dans config.toml"
    return "pret", "messages reçus et envoyés"


def envoyer(texte: str) -> None:
    jeton, chat = S.cfg.get("telegram.jeton", ""), str(S.cfg.get("telegram.chat_id", ""))
    if not jeton or not chat:
        raise ErreurOutil("Telegram n'est pas configuré : crée un bot avec BotFather et mets son jeton et ton "
                          "numéro de conversation dans [telegram] de config.toml.")
    for i in range(0, len(texte), 4000):
        reseau.post(f"https://api.telegram.org/bot{jeton}/sendMessage", "Telegram",
                    json={"chat_id": chat, "text": texte[i:i + 4000]})


@outil("telegram_envoyer", "Envoie un message à l'utilisateur sur Telegram (liste, lien, résumé à garder).",
       "TELEGRAM", {"texte": p("string", "Message")}, requis=["texte"])
def telegram_envoyer(texte: str) -> str:
    envoyer(texte)
    return "Message envoyé sur Telegram."
