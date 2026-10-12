"""Services partagés par les outils (config, mémoire, confirmations, voix...). Remplis au démarrage par
demarrage.initialiser() ; les tests en créent une version avec un dossier temporaire."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class Services:
    cfg: Any = None
    memoire: Any = None
    confirmations: Any = None
    cerveau: Any = None
    synthese: Any = None          # voix de Jarvis (pour annoncer un minuteur, une arrivée...)
    port: int = 8765


S = Services()


def annoncer(texte: str) -> None:
    """Fait dire une phrase à Jarvis en dehors d'une conversation (minuteur fini, retour à la maison)."""
    from .bus import bus
    bus.publier("annonce", texte=texte)
    if S.synthese is not None:
        try:
            S.synthese.dire(texte)
        except Exception:
            pass
