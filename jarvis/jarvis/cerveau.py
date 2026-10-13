"""Le cerveau : reçoit une demande (voix, clavier, Telegram, appel), y joint le contexte (date, canal, souvenirs
utiles), la passe au moteur (moteurs.py) qui pense et utilise les outils, et renvoie la réponse. Le texte arrive
en continu et part phrase par phrase vers la voix, pour que Jarvis commence à parler sans attendre la fin."""
from __future__ import annotations

import re
import threading
import time
from datetime import datetime
from typing import Any, Callable

from . import outils
from .bus import bus
from .moteurs import ErreurCerveau
from .personnalites import consigne

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]
CANAUX = {"voix": "voix (réponse lue à voix haute)", "clavier": "clavier de l'écran de Jarvis",
          "telegram": "Telegram (réponse écrite, sur le téléphone)", "mcp": "outil externe",
          "telephone": "appel téléphonique"}


def date_parlee(t: datetime | None = None) -> str:
    t = t or datetime.now()
    return f"{JOURS[t.weekday()]} {t.day} {MOIS[t.month - 1]} {t.year}, {t.hour} h {t.minute:02d}"


class Decoupeur:
    """Assemble le texte reçu en continu et le rend phrase par phrase (une fin de phrase suivie d'un espace ou
    d'un retour à la ligne ; « 3.5 » n'est pas coupé). Une phrase très longue est coupée à une virgule."""
    COUPE = re.compile(r"[.!?…]+[»\"')\]]*\s|\n")

    def __init__(self, sortie: Callable[[str], None] | None):
        self.sortie, self.tampon = sortie, ""
        self.premiere = True

    def ajouter(self, morceau: str) -> None:
        self.tampon += morceau
        while True:
            m = self.COUPE.search(self.tampon)
            if m:
                phrase, self.tampon = self.tampon[:m.end()], self.tampon[m.end():]
            elif self.premiere and len(self.tampon) > 90 and self.tampon.find(", ", 40) >= 0:
                i = self.tampon.find(", ", 40)           # longue première phrase : Jarvis commence à la virgule
                phrase, self.tampon = self.tampon[:i + 1], self.tampon[i + 2:]
            elif len(self.tampon) > 260:
                coupes = [i for i in (self.tampon.find(", ", 100), self.tampon.find("; ", 100)) if i >= 0]
                if not coupes:
                    break
                i = min(coupes)
                phrase, self.tampon = self.tampon[:i + 1], self.tampon[i + 2:]
            else:
                break
            self._emettre(phrase)

    def finir(self) -> None:
        if self.tampon.strip():
            self._emettre(self.tampon)
        self.tampon = ""

    def _emettre(self, phrase: str) -> None:
        if self.sortie and phrase.strip():
            self.premiere = False
            self.sortie(phrase.strip())


class Cerveau:
    def __init__(self, cfg: Any, moteur: Any, memoire: Any, confirmations: Any):
        self.cfg, self.moteur, self.memoire, self.confirmations = cfg, moteur, memoire, confirmations
        self.verrou = threading.Lock()
        self.dernier = 0.0
        self.origine = "voix"
        self.canal: Callable | None = None
        self.occupe = False
        self.nouvelle_conversation()

    # ------------------------------------------------------------------ conversation
    def consigne(self) -> str:
        return consigne(self.cfg.get("general.nom", "Jarvis"), self.cfg.get("general.proprietaire", ""),
                        self.cfg.get("general.personnalite", "majordome"),
                        bool(self.cfg.get("general.confirmations", False)))

    def nouvelle_conversation(self) -> None:
        self.moteur.nouvelle_conversation(self.consigne(), outils.definitions_api())
        bus.publier("conversation", phase="nouvelle")

    def _a_renouveler(self) -> bool:
        inactif = time.time() - self.dernier > 60 * float(self.cfg.get("cerveau.inactivite_minutes", 15))
        return (self.dernier and inactif) or self.moteur.taille() >= int(self.cfg.get("cerveau.messages_max", 120))

    def contexte(self, texte: str, origine: str) -> str:
        lignes = [f"[Contexte, ajouté par le système] Date et heure : {date_parlee()}. "
                  f"Canal : {CANAUX.get(origine, origine)}."]
        souvenirs = self.memoire.contexte(texte) if self.memoire else ""
        if souvenirs:
            lignes.append("Souvenirs utiles (numéro entre crochets) :\n" + souvenirs)
        return "\n".join(lignes)

    # ------------------------------------------------------------------ une demande
    def confirmer(self, question: str) -> bool:
        return self.confirmations.demander(question, canal=self.canal)

    def executer(self, nom: str, args: Any) -> tuple[Any, bool]:
        return outils.executer(nom, args, confirmer=self.confirmer, origine=self.origine)

    def traiter(self, texte: str, origine: str = "voix", canal: Callable | None = None,
                sur_phrase: Callable[[str], None] | None = None, images: list[dict] | None = None) -> str:
        texte = (texte or "").strip()
        if not texte and not images:
            return ""
        with self.verrou:
            self.occupe = True
            try:
                if self._a_renouveler():
                    self.nouvelle_conversation()
                self.origine, self.canal = origine, canal
                decoupe = Decoupeur(sur_phrase)
                bus.publier("transcription", texte=texte, origine=origine)
                bus.publier("etat", etat="reflexion")

                def sur_texte(morceau: str) -> None:
                    decoupe.ajouter(morceau)
                    bus.publier("reponse", morceau=morceau)

                contenu = [{"type": "text", "text": self.contexte(texte, origine)}]
                contenu += list(images or [])
                contenu.append({"type": "text", "text": texte or "(image jointe)"})
                try:
                    reponse = self.moteur.repondre(contenu, sur_texte, self.executer)
                except ErreurCerveau as e:
                    reponse = str(e)
                    decoupe = Decoupeur(sur_phrase)
                    decoupe.ajouter(reponse)
                    bus.publier("erreur", message=reponse)
                    self.nouvelle_conversation()          # historique peut-être incomplet : on repart propre
                except Exception as e:                    # erreur imprévue : Jarvis le dit et continue de vivre
                    reponse = f"J'ai eu un problème interne : {type(e).__name__}."
                    decoupe = Decoupeur(sur_phrase)
                    decoupe.ajouter(reponse)
                    bus.publier("erreur", message=f"{type(e).__name__} : {e}")
                    self.nouvelle_conversation()
                decoupe.finir()
                bus.publier("reponse_fin", texte=reponse, origine=origine)
                if self.memoire:
                    try:
                        self.memoire.journal(origine, texte, reponse)
                    except Exception:
                        pass
                self.dernier = time.time()
                return reponse
            finally:
                self.occupe = False
                self.canal = None
