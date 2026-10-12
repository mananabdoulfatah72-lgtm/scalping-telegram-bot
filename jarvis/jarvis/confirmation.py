"""Confirmations des actions sensibles. La question part à l'écran (boutons) et, selon le canal de la demande,
à voix haute ou sur Telegram ; la première réponse gagne. Sans réponse : refus (rien n'est fait)."""
from __future__ import annotations

import re
import threading
import uuid
from typing import Callable

from .bus import bus

OUI = re.compile(r"\b(oui|ouais|ok|okay|d'accord|vas-y|vas y|go|confirme|confirmé|je confirme|bien sûr|exact|"
                 r"c'est ça|parfait|yes|valide|envoie|lance|fais-le|fais le)\b", re.I)
NON = re.compile(r"\b(non|annule|annuler|stop|arrête|surtout pas|pas du tout|attends|no|laisse tomber|refuse|"
                 r"pas d'accord|pas ok|ne fais pas|fais pas|n'envoie pas|envoie pas)\b", re.I)

NEGATION = re.compile(r"\b(ne|n')\s*\w*[^.!?]{0,30}?\bpas\b", re.I)       # « ne l'envoie pas », « n'appelle pas »


def lire_reponse(texte: str) -> bool | None:
    """oui -> True, non -> False, autre -> None. « non » l'emporte si les deux apparaissent."""
    t = (texte or "").strip()
    if NON.search(t) or NEGATION.search(t):
        return False
    if OUI.search(t):
        return True
    return None


class Confirmations:
    def __init__(self, delai: float = 45.0):
        self.delai = delai
        self._attente: dict[str, dict] = {}
        self._verrou = threading.Lock()

    def demander(self, question: str, canal: Callable[[str, threading.Event, str], bool | None] | None = None) -> bool:
        """canal(question, deja_repondu, identifiant) : demande par la voix ou Telegram ; renvoie True/False, ou
        None si la réponse viendra autrement (bouton de l'écran, bouton Telegram) : on attend jusqu'au délai."""
        ident = uuid.uuid4().hex[:10]
        evt = threading.Event()
        etat = {"evt": evt, "ok": None}
        with self._verrou:
            self._attente[ident] = etat
        bus.publier("confirmation", id=ident, question=question, phase="attente")
        try:
            if canal is not None:
                r = canal(question, evt, ident)
                if r is not None and not evt.is_set():
                    etat["ok"] = bool(r)
                    evt.set()
            evt.wait(self.delai)
            ok = bool(etat["ok"])
        finally:
            with self._verrou:
                self._attente.pop(ident, None)
        bus.publier("confirmation", id=ident, question=question, phase="oui" if ok else "non")
        return ok

    def repondre(self, ident: str, ok: bool) -> bool:
        with self._verrou:
            etat = self._attente.get(ident)
        if not etat or etat["evt"].is_set():
            return False
        etat["ok"] = bool(ok)
        etat["evt"].set()
        return True

    def en_attente(self) -> list[str]:
        with self._verrou:
            return list(self._attente)
