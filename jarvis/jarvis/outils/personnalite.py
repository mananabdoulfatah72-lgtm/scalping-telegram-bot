"""Personnalités de Jarvis : majordome sarcastique, neutre, concis, coach, pote."""
from __future__ import annotations

from ..bus import bus
from ..personnalites import PERSONNALITES
from ..services import S
from . import ErreurOutil, module, outil, p


@module("personnalite", "PERSONNALITE")
def etat() -> tuple[str, str]:
    nom = S.cfg.get("general.personnalite", "majordome") if S.cfg else "majordome"
    return "pret", PERSONNALITES.get(nom, PERSONNALITES["majordome"])[0]


@outil("personnalite_changer", "Change la personnalité de Jarvis (ton et style), tout de suite et pour la suite.",
       "PERSONNALITE", {"nom": p("string", "Personnalité", enum=sorted(PERSONNALITES))}, requis=["nom"])
def personnalite_changer(nom: str) -> str:
    if nom not in PERSONNALITES:
        raise ErreurOutil(f"Personnalité inconnue : {nom}.")
    S.cfg.set("general.personnalite", nom)
    titre, texte = PERSONNALITES[nom]
    bus.publier("personnalite", nom=nom, titre=titre)
    return f"Personnalité changée en « {titre} ». À partir de maintenant : {texte}"


@outil("personnalite_liste", "Liste les personnalités disponibles.", "PERSONNALITE")
def personnalite_liste() -> str:
    actuelle = S.cfg.get("general.personnalite", "majordome")
    return "\n".join(f"{k} : {t}{' (actuelle)' if k == actuelle else ''} — {d}" for k, (t, d) in PERSONNALITES.items())
