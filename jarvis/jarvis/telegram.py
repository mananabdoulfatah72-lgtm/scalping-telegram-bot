"""Jarvis sur ton téléphone, partout : un bot Telegram à toi (créé avec @BotFather). Messages texte, notes
vocales (transcrites sur le PC) et photos (Jarvis les regarde). Seul ton numéro de conversation est écouté ;
les confirmations arrivent avec des boutons Oui / Non."""
from __future__ import annotations

import base64
import threading
import time
import uuid

import requests

from .bus import bus
from .config import dossier

API = "https://api.telegram.org"


class Telegram(threading.Thread):
    def __init__(self, cfg, cerveau, confirmations, transcripteur=None):
        super().__init__(daemon=True, name="telegram")
        self.cfg, self.cerveau, self.confirmations, self.transcripteur = cfg, cerveau, confirmations, transcripteur
        self.jeton = cfg.get("telegram.jeton", "")
        self.chat = str(cfg.get("telegram.chat_id", "") or "")
        self.arret = threading.Event()
        self.decalage = 0

    def appel(self, methode: str, **donnees):
        r = requests.post(f"{API}/bot{self.jeton}/{methode}", json=donnees, timeout=40)
        r.raise_for_status()
        return r.json().get("result")

    def envoyer(self, chat: str, texte: str, **extra) -> None:
        for i in range(0, max(1, len(texte)), 4000):
            try:
                self.appel("sendMessage", chat_id=chat, text=texte[i:i + 4000] or "…", **extra)
            except Exception:
                pass

    def fichier(self, file_id: str) -> bytes:
        info = self.appel("getFile", file_id=file_id)
        r = requests.get(f"{API}/file/bot{self.jeton}/{info['file_path']}", timeout=60)
        r.raise_for_status()
        return r.content

    def canal(self, chat: str):
        def demander(question: str, deja: threading.Event, ident: str) -> None:
            self.envoyer(chat, f"🔐 {question}", reply_markup={"inline_keyboard": [[
                {"text": "Oui", "callback_data": f"conf:{ident}:1"}, {"text": "Non", "callback_data": f"conf:{ident}:0"}]]})
            return None                          # la réponse arrive par le bouton (traitée par la boucle d'écoute)
        return demander

    def traiter(self, chat: str, texte: str, images: list[dict] | None = None) -> None:
        try:
            self.appel("sendChatAction", chat_id=chat, action="typing")
        except Exception:
            pass
        bus.publier("outil", nom="telegram", zone="TELEGRAM", phase="debut", origine="telegram")
        reponse = self.cerveau.traiter(texte, origine="telegram", canal=self.canal(chat), images=images)
        bus.publier("outil", nom="telegram", zone="TELEGRAM", phase="fin", ok=True, resume="réponse envoyée",
                    origine="telegram")
        self.envoyer(chat, reponse or "C'est fait.")

    def message(self, m: dict) -> None:
        chat = str(m["chat"]["id"])
        if not self.chat:
            self.envoyer(chat, f"Bonjour ! Ton numéro de conversation est {chat}. Mets-le dans config.toml "
                               f"([telegram] chat_id = \"{chat}\") puis redémarre Jarvis.")
            return
        if chat != self.chat:
            return                                # quelqu'un d'autre : ignoré
        # téléchargement, transcription et réponse à part : la boucle d'écoute reste libre pour les boutons Oui / Non
        threading.Thread(target=self.preparer, args=(chat, m), daemon=True).start()

    def preparer(self, chat: str, m: dict) -> None:
        try:
            texte = m.get("text") or m.get("caption") or ""
            images = None
            if m.get("voice") or m.get("audio"):
                if self.transcripteur is None:
                    self.envoyer(chat, "La transcription des notes vocales n'est pas installée sur le PC.")
                    return
                f = dossier() / f"note_vocale_{uuid.uuid4().hex[:8]}.ogg"
                try:
                    f.write_bytes(self.fichier((m.get("voice") or m.get("audio"))["file_id"]))
                    texte = self.transcripteur.transcrire(str(f))
                finally:
                    f.unlink(missing_ok=True)
                if not texte:
                    self.envoyer(chat, "Je n'ai rien compris dans la note vocale.")
                    return
                self.envoyer(chat, f"🎙️ « {texte} »")
            elif m.get("photo"):
                octets = self.fichier(m["photo"][-1]["file_id"])
                images = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                                       "data": base64.standard_b64encode(octets).decode("ascii")}}]
                texte = texte or "Regarde cette image."
            if texte:
                self.traiter(chat, texte, images)
        except Exception as e:
            self.envoyer(chat, f"Je n'ai pas pu traiter ce message ({type(e).__name__}).")

    def bouton(self, q: dict) -> None:
        donnees = q.get("data", "")
        if str(q.get("message", {}).get("chat", {}).get("id", "")) == self.chat and donnees.startswith("conf:"):
            _, ident, ok = donnees.split(":")
            self.confirmations.repondre(ident, ok == "1")
            try:
                self.appel("answerCallbackQuery", callback_query_id=q["id"], text="Confirmé" if ok == "1" else "Annulé")
            except Exception:
                pass

    def run(self) -> None:
        if not self.jeton:
            return
        while not self.arret.is_set():
            try:
                maj = self.appel("getUpdates", offset=self.decalage, timeout=30,
                                 allowed_updates=["message", "callback_query"]) or []
                for u in maj:
                    self.decalage = u["update_id"] + 1
                    if "callback_query" in u:
                        self.bouton(u["callback_query"])
                    elif "message" in u:
                        self.message(u["message"])
            except Exception as e:
                bus.publier("journal", message=f"Telegram : {type(e).__name__}")
                time.sleep(5)
