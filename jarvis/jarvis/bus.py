"""Bus d'événements : tout ce que fait Jarvis (écoute, réflexion, outil utilisé, réponse, stats du PC) est publié
ici. L'interface (le cerveau à l'écran) s'y abonne par websocket. Sûr entre threads."""
from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any, Callable

Abonne = Callable[[dict], None]


class Bus:
    def __init__(self, memoire: int = 60):
        self._abonnes: list[Abonne] = []
        self._verrou = threading.Lock()
        self.dernier: dict[str, dict] = {}            # dernier événement de chaque type « état » (pour un nouvel écran)
        self.recents: deque[dict] = deque(maxlen=memoire)

    def abonner(self, fn: Abonne) -> None:
        with self._verrou:
            self._abonnes.append(fn)

    def desabonner(self, fn: Abonne) -> None:
        with self._verrou:
            if fn in self._abonnes:
                self._abonnes.remove(fn)

    def publier(self, type_: str, **donnees: Any) -> dict:
        evt = {"type": type_, "t": time.time(), **donnees}
        if type_ in ("etat", "stats", "modules", "personnalite", "minuteurs", "presence"):
            self.dernier[type_] = evt
        if type_ in ("transcription", "reponse_fin", "outil", "erreur"):
            self.recents.append(evt)
        with self._verrou:
            abonnes = list(self._abonnes)
        for fn in abonnes:
            try:
                fn(evt)
            except Exception:                         # un écran fermé ne doit jamais casser Jarvis
                pass
        return evt

    def instantane(self) -> list[dict]:
        return list(self.dernier.values()) + list(self.recents)


bus = Bus()
