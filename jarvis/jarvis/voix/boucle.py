"""Boucle mains libres : « Hey Jarvis » (ou le bouton Parler de l'écran) -> écoute jusqu'à la fin de la phrase ->
transcription -> cerveau -> réponse dite phrase par phrase -> quelques secondes d'écoute sans mot de réveil
pour enchaîner naturellement. Les confirmations se font aussi à la voix."""
from __future__ import annotations

import re
import threading
import time

from ..bus import bus
from ..confirmation import lire_reponse
from .audio import BIP_ECOUTE, BIP_FIN, DetecteurParole, enregistrer_phrase

STOP = re.compile(r"^\W*(stop|tais-toi|silence|chut|arrête de parler|ça suffit)\W*$", re.I)
FIN_CONVERSATION = re.compile(r"^\W*(merci|merci jarvis|c'est tout|ce sera tout|rien|non merci|bonne nuit)\W*$", re.I)


class BoucleVocale(threading.Thread):
    def __init__(self, cfg, cerveau, micro, reveil, transcripteur, synthese):
        super().__init__(daemon=True, name="voix")
        self.cfg, self.cerveau, self.micro = cfg, cerveau, micro
        self.reveil, self.transcripteur, self.synthese = reveil, transcripteur, synthese
        self.declencheur = threading.Event()
        self.arret = threading.Event()
        self.detecteur = DetecteurParole()

    def declencher(self) -> None:
        """Bouton Parler de l'écran : comme si on avait dit « Hey Jarvis »."""
        self.declencheur.set()

    def niveau(self, x: float) -> None:
        bus.publier("micro", niveau=round(x, 3))

    def ecouter(self, attente: float) -> str:
        bus.publier("etat", etat="ecoute")
        audio = enregistrer_phrase(lambda: self.micro.lire(0.5), attente,
                                   float(self.cfg.get("voix.silence_fin", 0.9)), detecteur=self.detecteur,
                                   sur_niveau=self.niveau)
        if audio is None:
            return ""
        bus.publier("etat", etat="transcription")
        return self.transcripteur.transcrire(audio)

    def attendre_reveil(self) -> bool:
        bus.publier("etat", etat="veille")
        self.declencheur.clear()
        while not self.arret.is_set():
            if self.declencheur.is_set():
                self.declencheur.clear()
                return True
            trame = self.micro.lire(0.3)
            if trame is None:
                continue
            if self.reveil is not None and self.reveil.entendu(trame):
                return True
        return False

    def confirmer(self, question: str, deja: threading.Event, ident: str = "") -> bool | None:
        """Canal vocal des confirmations : question à voix haute, réponse oui / non (deux essais)."""
        self.synthese.attendre()
        for essai in range(2):
            if deja.is_set():
                return None
            self.synthese.dire(question + (" Tu confirmes ?" if essai == 0 else " Réponds par oui ou par non."))
            self.synthese.attendre()
            if deja.is_set():
                return None
            self.micro.vider()                  # seulement ce qui est dit après la question
            r = lire_reponse(self.ecouter(8.0))
            if r is not None:
                return r
        return False

    def run(self) -> None:
        suivi_jusqua = 0.0
        while not self.arret.is_set():
            try:
                if time.time() < suivi_jusqua:
                    if self.declencheur.is_set():      # bouton Parler pendant la réponse : bip, puis écoute
                        self.declencheur.clear()
                        self.synthese.jouer_son(BIP_ECOUTE)
                        self.micro.vider()
                        suivi_jusqua = time.time() + 6.0
                    texte = self.ecouter(max(0.5, suivi_jusqua - time.time()))
                    suivi_jusqua = 0.0
                    if not texte:
                        continue
                else:
                    if not self.attendre_reveil():
                        break
                    self.synthese.stop()
                    self.synthese.jouer_son(BIP_ECOUTE)
                    self.micro.vider()
                    texte = self.ecouter(6.0)
                    if not texte:
                        self.synthese.jouer_son(BIP_FIN)
                        continue
                if STOP.match(texte):
                    self.synthese.stop()
                    continue
                if FIN_CONVERSATION.match(texte):
                    self.synthese.dire("Je reste à l'écoute.")
                    self.synthese.attendre()
                    continue
                self.synthese.reprendre()
                self.cerveau.traiter(texte, origine="voix", canal=self.confirmer, sur_phrase=self.synthese.ajouter)
                self.synthese.attendre()
                suivi_jusqua = time.time() + float(self.cfg.get("voix.suivi_secondes", 6.0))
            except Exception as e:
                bus.publier("erreur", message=f"boucle vocale : {type(e).__name__} : {e}")
                time.sleep(1.0)
