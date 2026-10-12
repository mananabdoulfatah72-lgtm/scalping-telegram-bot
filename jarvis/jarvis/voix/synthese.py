"""Synthèse vocale : Piper (voix neuronale locale, gratuite) si installée, sinon la voix française de Windows.
Les phrases arrivent une par une (Jarvis parle pendant qu'il finit de penser) et passent dans une file ; le
niveau sonore est publié pour animer le cerveau à l'écran ; le micro est coupé pendant que Jarvis parle."""
from __future__ import annotations

import queue
import re
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path

import numpy as np

from ..bus import bus
from ..config import dossier

EMOJIS = re.compile("[\U0001F000-\U0001FAFF☀-➿️]")


def pour_la_voix(texte: str) -> str:
    """Texte propre à lire : sans markdown, sans adresse web, sans émoji."""
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texte)
    t = re.sub(r"https?://\S+", "le lien", t)
    t = re.sub(r"[*_`#>|~]+", " ", t)
    t = EMOJIS.sub("", t)
    t = t.replace(" - ", ", ").replace("—", ", ").replace("–", " à ")
    t = re.sub(r"\s+([.,…])", r"\1", t)
    return re.sub(r"\s+", " ", t).strip()


class MoteurPiper:
    def __init__(self, voix: str, vitesse: float = 1.0):
        from piper import PiperVoice
        modele = dossier() / "voix" / f"{voix}.onnx"
        if not modele.exists():
            raise RuntimeError(f"voix Piper absente : {modele} (relance installer.bat)")
        self.voix = PiperVoice.load(str(modele))
        self.vitesse = vitesse

    def synthetiser(self, texte: str) -> tuple[np.ndarray, int]:
        echelle = 1.0 / max(0.5, min(2.0, self.vitesse))
        try:                                                  # piper-tts 1.3 et plus
            from piper import SynthesisConfig
            morceaux, taux = [], 22050
            for m in self.voix.synthesize(texte, syn_config=SynthesisConfig(length_scale=echelle)):
                morceaux.append(m.audio_int16_array)
                taux = m.sample_rate
            audio = np.concatenate(morceaux) if morceaux else np.zeros(0, np.int16)
        except ImportError:                                   # piper-tts 1.2
            brut = b"".join(self.voix.synthesize_stream_raw(texte, length_scale=echelle))
            audio, taux = np.frombuffer(brut, dtype=np.int16), self.voix.config.sample_rate
        return audio.astype(np.float32) / 32768.0, taux


class MoteurWindows:
    """Voix SAPI de Windows (Hortense, Paul, Julie... selon les langues installées), par pyttsx3."""

    def __init__(self, vitesse: float = 1.0):
        try:                                    # SAPI passe par COM, à initialiser dans le fil qui s'en sert
            import comtypes
            comtypes.CoInitialize()
        except Exception:
            pass
        import pyttsx3
        self.moteur = pyttsx3.init()
        for v in self.moteur.getProperty("voices"):
            ident = (getattr(v, "id", "") + " " + getattr(v, "name", "")).lower()
            if "fr" in ident or "french" in ident or "français" in ident:
                self.moteur.setProperty("voice", v.id)
                break
        self.moteur.setProperty("rate", int(185 * vitesse))

    def synthetiser(self, texte: str) -> tuple[np.ndarray, int]:
        f = Path(tempfile.gettempdir()) / f"jarvis_{threading.get_ident()}.wav"
        self.moteur.save_to_file(texte, str(f))
        self.moteur.runAndWait()
        with wave.open(str(f), "rb") as w:
            taux, n, largeur, canaux = w.getframerate(), w.getnframes(), w.getsampwidth(), w.getnchannels()
            brut = w.readframes(n)
        audio = np.frombuffer(brut, dtype=np.int16 if largeur == 2 else np.uint8).astype(np.float32)
        audio = audio / 32768.0 if largeur == 2 else (audio - 128) / 128.0
        if canaux > 1:
            audio = audio.reshape(-1, canaux).mean(axis=1)
        return audio, taux


class Synthese:
    def __init__(self, cfg, micro=None):
        self.cfg, self.micro = cfg, micro
        self.file: queue.Queue = queue.Queue()
        self.parle = threading.Event()
        self.interrompre = threading.Event()
        self.ignorer = False                    # après Stop : le reste de la réponse en cours n'est pas dit
        self.moteur = None
        self.nom_moteur = "aucune"
        self._fil = threading.Thread(target=self._boucle, daemon=True, name="synthese")
        self._fil.start()

    def _creer_moteur(self) -> None:
        choix = self.cfg.get("voix.synthese", "auto")
        vitesse = float(self.cfg.get("voix.vitesse", 1.0))
        essais = {"piper": ["piper"], "windows": ["windows"], "aucune": [], "auto": ["piper", "windows"]}.get(choix, ["piper", "windows"])
        for e in essais:
            try:
                if e == "piper":
                    self.moteur = MoteurPiper(self.cfg.get("voix.voix_piper", "fr_FR-tom-medium"), vitesse)
                elif e == "windows" and sys.platform == "win32":
                    self.moteur = MoteurWindows(vitesse)
                else:
                    continue
                self.nom_moteur = e
                return
            except Exception as ex:
                bus.publier("journal", message=f"synthèse {e} indisponible : {ex}")
        self.moteur, self.nom_moteur = None, "aucune"

    # ------------------------------------------------------------------ appelé par les autres fils
    def ajouter(self, phrase: str) -> None:
        """Une phrase de la réponse en cours (ignorée si on a demandé le silence pendant cette réponse)."""
        if not self.ignorer:
            self.dire(phrase)

    def dire(self, texte: str) -> None:
        """Toujours dit : annonces, minuteurs, questions de confirmation."""
        t = pour_la_voix(texte)
        if t:
            self.interrompre.clear()
            self.file.put(t)

    def reprendre(self) -> None:
        """Nouvelle demande : ses phrases seront dites."""
        self.ignorer = False

    def attendre(self, maximum: float = 120.0) -> None:
        """Attend que tout soit dit (file vide et plus rien en cours)."""
        fin = time.time() + maximum
        time.sleep(0.05)
        while (not self.file.empty() or self.parle.is_set()) and time.time() < fin:
            time.sleep(0.05)

    def stop(self) -> None:
        self.ignorer = True
        self.interrompre.set()
        while True:
            try:
                self.file.get_nowait()
            except queue.Empty:
                break

    # ------------------------------------------------------------------ fil de la voix
    def _boucle(self) -> None:
        self._creer_moteur()                    # dans ce fil : la voix Windows (COM) doit y rester
        bus.publier("journal", message=f"synthèse vocale : {self.nom_moteur}")
        while True:
            texte = self.file.get()
            if self.moteur is None or self.interrompre.is_set():
                continue
            self.parle.set()
            if self.micro is not None:
                self.micro.coupe.set()
            bus.publier("etat", etat="parle")
            try:
                audio, taux = self.moteur.synthetiser(texte)
                self._jouer(audio, taux)
            except Exception as e:
                bus.publier("erreur", message=f"synthèse vocale : {type(e).__name__} : {e}")
            finally:
                if self.file.empty():
                    time.sleep(0.25)            # la fin de la phrase ne doit pas déclencher le micro
                    if self.micro is not None:
                        self.micro.vider()
                        self.micro.coupe.clear()
                    self.parle.clear()
                    bus.publier("audio", niveau=0.0)

    def _jouer(self, audio: np.ndarray, taux: int) -> None:
        import sounddevice as sd
        bloc = int(taux * 0.04)
        with sd.OutputStream(samplerate=taux, channels=1, dtype="float32") as sortie:
            for i in range(0, len(audio), bloc):
                if self.interrompre.is_set():
                    break
                morceau = audio[i:i + bloc]
                sortie.write(morceau.reshape(-1, 1))
                niveau = float(np.sqrt(np.mean(morceau ** 2))) if len(morceau) else 0.0
                bus.publier("audio", niveau=round(min(1.0, niveau * 4), 3))

    def jouer_son(self, son: np.ndarray, taux: int = 24000) -> None:
        try:
            import sounddevice as sd
            sd.play(son, taux, blocking=True)
        except Exception:
            pass
