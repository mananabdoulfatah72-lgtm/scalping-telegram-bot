"""Assemblage de Jarvis : services, outils, cerveau, voix, Telegram, présence, mesures pour l'écran. Chaque partie
qui ne peut pas démarrer (bibliothèque absente, micro introuvable, rien de configuré) est signalée et le reste
continue : Jarvis marche alors au clavier, sur Telegram ou sans voix."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any

from . import outils
from .bus import bus
from .cerveau import Cerveau
from .config import Config, dossier
from .confirmation import Confirmations
from .memoire import Memoire
from .moteurs import ErreurCerveau, creer_moteur
from .services import S


class MoteurIndisponible:
    """Remplace le moteur quand aucun n'est utilisable : Jarvis explique quoi faire au lieu de planter."""
    nom = "indisponible"

    def __init__(self, raison: str):
        self.raison = raison

    def nouvelle_conversation(self, consigne: str, outils_api: list) -> None:
        pass

    def taille(self) -> int:
        return 0

    def repondre(self, contenu, sur_texte, executer) -> str:
        raise ErreurCerveau(self.raison)


@dataclass
class Application:
    cfg: Config
    cerveau: Cerveau
    synthese: Any = None
    boucle: Any = None
    micro: Any = None
    transcripteur: Any = None
    telegram: Any = None
    problemes: list[str] = field(default_factory=list)
    arret: threading.Event = field(default_factory=threading.Event)

    @property
    def nom_moteur(self) -> str:
        return getattr(self.cerveau.moteur, "nom", "?")


def initialiser(cfg: Config | None = None, avec_voix: bool = True) -> Application:
    cfg = cfg or Config.charger()
    S.cfg = cfg
    S.memoire = Memoire(dossier() / "memoire.db")
    S.confirmations = Confirmations()
    S.port = int(cfg.get("interface.port", 8765))
    outils.charger_tous()
    problemes = []
    try:
        moteur = creer_moteur(cfg)
    except ErreurCerveau as e:
        moteur = MoteurIndisponible(str(e))
        problemes.append(str(e))
    cerveau = Cerveau(cfg, moteur, S.memoire, S.confirmations)
    S.cerveau = cerveau
    app = Application(cfg, cerveau, problemes=problemes)
    if avec_voix and cfg.get("voix.active", True):
        demarrer_voix(app)
    return app


def demarrer_voix(app: Application) -> None:
    cfg = app.cfg
    from .voix.synthese import Synthese
    try:
        from .voix.audio import Micro
        app.micro = Micro(cfg.get("voix.micro", ""))
    except Exception as e:
        app.problemes.append(f"micro indisponible ({type(e).__name__} : {e}) : Jarvis répond au clavier et sur Telegram")
    app.synthese = Synthese(cfg, app.micro)
    S.synthese = app.synthese
    try:
        from .voix.reconnaissance import Transcripteur
        app.transcripteur = Transcripteur(cfg.get("voix.modele_whisper", "small"), cfg.get("voix.peripherique", "auto"))
    except Exception as e:
        app.problemes.append(f"transcription indisponible ({e})")
    if app.micro is None or app.transcripteur is None:
        return
    reveil = None
    try:
        from .voix.reconnaissance import Reveil
        reveil = Reveil(cfg.get("voix.mot_reveil", "hey_jarvis"), float(cfg.get("voix.seuil_reveil", 0.5)))
    except Exception as e:
        app.problemes.append(f"mot de réveil indisponible ({e}) : utilise le bouton Parler de l'écran")
    from .voix.boucle import BoucleVocale
    app.boucle = BoucleVocale(cfg, app.cerveau, app.micro, reveil, app.transcripteur, app.synthese)
    app.boucle.start()


def demarrer_fond(app: Application) -> None:
    """Fils de fond : mesures du PC pour l'écran, état des modules, présence, Instagram, Telegram."""
    from .outils import pc, presence, instagram

    def mesures():
        while not app.arret.is_set():
            try:
                bus.publier("stats", **pc.mesures())
            except Exception:
                pass
            app.arret.wait(1.0)

    def modules():
        while not app.arret.is_set():
            bus.publier("modules", liste=outils.etats_modules(), moteur=app.nom_moteur, problemes=app.problemes,
                        voix=bool(app.boucle), synthese=getattr(app.synthese, "nom_moteur", "aucune"))
            app.arret.wait(20.0)

    def instagram_jour():
        while not app.arret.is_set():
            instagram.noter_chaque_jour()
            app.arret.wait(6 * 3600)

    for cible, nom in ((mesures, "mesures"), (modules, "modules"), (instagram_jour, "instagram")):
        threading.Thread(target=cible, daemon=True, name=nom).start()
    presence.SURVEILLANT.demarrer()
    if app.cfg.get("telegram.jeton", ""):
        from .telegram import Telegram
        app.telegram = Telegram(app.cfg, app.cerveau, S.confirmations, app.transcripteur)
        app.telegram.start()
    bus.publier("demarrage", t=time.time(), moteur=app.nom_moteur, problemes=app.problemes)
