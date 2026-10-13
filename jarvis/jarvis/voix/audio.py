"""Micro (16 kHz, mono, trames de 80 ms comme le veut openWakeWord), détection de parole et petits sons."""
from __future__ import annotations

import queue
import threading
from collections import deque

import numpy as np

TAUX = 16000
TRAME = 1280                       # 80 ms
SOUS = 320                         # 20 ms (pour le détecteur de parole)


def choisir_micro(nom: str):
    """Numéro du micro : vide = par défaut, un nombre = ce numéro, sinon le premier dont le nom contient le texte."""
    import sounddevice as sd
    if not nom:
        return None
    if str(nom).isdigit():
        return int(nom)
    for i, d in enumerate(sd.query_devices()):
        if d.get("max_input_channels", 0) > 0 and str(nom).lower() in d["name"].lower():
            return i
    return None


class Micro:
    def __init__(self, nom: str = ""):
        import sounddevice as sd
        self.file: queue.Queue = queue.Queue(maxsize=400)
        self.coupe = threading.Event()          # pendant que Jarvis parle : on n'écoute pas sa propre voix
        self.flux = sd.RawInputStream(samplerate=TAUX, channels=1, dtype="int16", blocksize=TRAME,
                                      device=choisir_micro(nom), callback=self._rappel)
        self.flux.start()

    def _rappel(self, donnees, n, temps, statut) -> None:
        if self.coupe.is_set():
            return
        trame = bytes(donnees)
        try:
            self.file.put_nowait(trame)
        except queue.Full:                      # file pleine (longue réflexion) : on jette la plus ancienne
            try:
                self.file.get_nowait()
                self.file.put_nowait(trame)
            except (queue.Empty, queue.Full):
                pass

    def lire(self, delai: float = 0.5) -> np.ndarray | None:
        try:
            return np.frombuffer(self.file.get(timeout=delai), dtype=np.int16)
        except queue.Empty:
            return None

    def vider(self) -> None:
        while True:
            try:
                self.file.get_nowait()
            except queue.Empty:
                return

    def fermer(self) -> None:
        try:
            self.flux.stop()
            self.flux.close()
        except Exception:
            pass


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(x.astype(np.float32) ** 2))) if len(x) else 0.0


class DetecteurParole:
    """webrtcvad s'il est installé (robuste au bruit), sinon un seuil d'énergie au-dessus du bruit de fond."""

    def __init__(self, agressivite: int = 2):
        self.bruit = 150.0
        try:
            import webrtcvad
            self.vad = webrtcvad.Vad(agressivite)
        except ImportError:
            self.vad = None

    def apprendre_bruit(self, trame: np.ndarray) -> None:
        self.bruit = 0.95 * self.bruit + 0.05 * max(60.0, rms(trame))

    def parle(self, trame: np.ndarray) -> bool:
        """Vrai si au moins la moitié des sous-trames de 20 ms contiennent de la voix."""
        if self.vad is not None:
            voix = sum(self.vad.is_speech(trame[i:i + SOUS].tobytes(), TAUX) for i in range(0, len(trame) - SOUS + 1, SOUS))
            return voix >= 2 and rms(trame) > self.bruit * 1.5
        return rms(trame) > max(self.bruit * 3.0, 350.0)


def enregistrer_phrase(lire, attente: float, silence_fin: float = 0.9, maximum: float = 20.0,
                       detecteur: DetecteurParole | None = None, sur_niveau=None) -> np.ndarray | None:
    """Attend le début de la parole (jusqu'à `attente` secondes), puis enregistre jusqu'à `silence_fin` secondes
    de silence. lire() rend une trame de 80 ms (ou None). Renvoie l'audio int16, ou None si personne n'a parlé."""
    det = detecteur or DetecteurParole()
    t_trame = TRAME / TAUX
    avant: deque = deque(maxlen=4)              # 320 ms gardées avant le début de la parole
    attendu, actif, silence, total = 0.0, False, 0.0, 0.0
    morceaux: list[np.ndarray] = []
    voix_de_suite = 0
    while True:
        trame = lire()
        if trame is None:
            attendu += 0.5
            if not actif and attendu > attente:
                return None
            continue
        if sur_niveau:
            sur_niveau(min(1.0, rms(trame) / 4000))
        parle = det.parle(trame)
        if not actif:
            attendu += t_trame
            avant.append(trame)
            voix_de_suite = voix_de_suite + 1 if parle else 0
            if voix_de_suite >= 2:
                actif = True
                morceaux.extend(avant)
                continue
            det.apprendre_bruit(trame)
            if attendu > attente:
                return None
        else:
            morceaux.append(trame)
            total += t_trame
            silence = 0.0 if parle else silence + t_trame
            if silence >= silence_fin or total >= maximum:
                break
    audio = np.concatenate(morceaux)
    return audio if len(audio) > TAUX * 0.35 else None


def ton(frequences: list[tuple[float, float]], volume: float = 0.18, taux: int = 24000) -> np.ndarray:
    """Petit son : suite de (fréquence, durée), avec fondu pour éviter les clics."""
    morceaux = []
    for f, d in frequences:
        t = np.arange(int(taux * d)) / taux
        s = np.sin(2 * np.pi * f * t) * volume
        n = min(len(s) // 4, int(taux * 0.012))
        if n:
            s[:n] *= np.linspace(0, 1, n)
            s[-n:] *= np.linspace(1, 0, n)
        morceaux.append(s)
    return np.concatenate(morceaux).astype(np.float32)


BIP_ECOUTE = ton([(740, 0.04), (1110, 0.05)])           # court : Jarvis écoute presque aussitôt
BIP_FIN = ton([(880, 0.06), (587, 0.08)])
