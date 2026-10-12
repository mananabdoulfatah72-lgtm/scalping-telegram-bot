"""Mot de réveil (openWakeWord, modèle « hey jarvis ») et transcription locale (faster-whisper)."""
from __future__ import annotations

import re
import subprocess
import sys
import time

import numpy as np

from ..config import dossier

HALLUCINATIONS = re.compile(r"(sous-titr|amara\.org|merci d'avoir regardé|abonnez-vous|n'oubliez pas de vous abonner|"
                            r"thanks for watching|♪|merci à tous|à bientôt sur)", re.I)


class Reveil:
    def __init__(self, mot: str = "hey_jarvis", seuil: float = 0.5):
        try:
            from openwakeword.model import Model
        except ImportError:
            raise RuntimeError("openwakeword n'est pas installé (relance installer.bat)")
        try:
            self.modele = Model(wakeword_models=[mot], inference_framework="onnx")
        except Exception:
            import openwakeword.utils
            openwakeword.utils.download_models([mot])
            self.modele = Model(wakeword_models=[mot], inference_framework="onnx")
        self.seuil = seuil
        self.calme_jusqua = 0.0

    def entendu(self, trame: np.ndarray) -> bool:
        scores = self.modele.predict(trame)
        if time.time() < self.calme_jusqua:
            return False
        if max(scores.values(), default=0.0) >= self.seuil:
            self.modele.reset()
            self.calme_jusqua = time.time() + 1.5
            return True
        return False

    def remettre(self) -> None:
        self.modele.reset()


def cuda_utilisable(modele: str) -> bool:
    """Essai de la carte graphique dans un processus à part, une fois (résultat gardé dans whisper_cuda.txt) :
    sans les bibliothèques CUDA, faster-whisper peut faire planter tout le programme à la première transcription
    au lieu de lever une erreur. Supprimer whisper_cuda.txt pour refaire l'essai (nouvelle carte, pilotes)."""
    marque = dossier() / "whisper_cuda.txt"
    if marque.exists():
        return marque.read_text(encoding="utf-8").strip() == "oui"
    code = ("import numpy as np; from faster_whisper import WhisperModel; "
            f"m = WhisperModel({modele!r}, device='cuda', compute_type='float16'); "
            "s, _ = m.transcribe(np.zeros(16000, dtype=np.float32), language='fr'); list(s)")
    try:
        ok = subprocess.run([sys.executable, "-c", code], capture_output=True, timeout=300,
                            creationflags=0x08000000 if sys.platform == "win32" else 0).returncode == 0
    except Exception:
        ok = False
    marque.write_text("oui" if ok else "non", encoding="utf-8")
    return ok


class Transcripteur:
    def __init__(self, modele: str = "small", peripherique: str = "auto"):
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError("faster-whisper n'est pas installé (relance installer.bat)")
        self.modele = None
        if peripherique == "cuda" or (peripherique == "auto" and cuda_utilisable(modele)):
            try:
                self.modele = WhisperModel(modele, device="cuda", compute_type="float16")
            except Exception:
                if peripherique == "cuda":
                    raise
        if self.modele is None:
            self.modele = WhisperModel(modele, device="cpu", compute_type="int8")

    def transcrire(self, audio) -> str:
        """audio : int16 à 16 kHz, ou chemin d'un fichier (note vocale Telegram .ogg...)."""
        if isinstance(audio, np.ndarray):
            audio = audio.astype(np.float32) / 32768.0
        segments, _ = self.modele.transcribe(audio, language="fr", beam_size=1, vad_filter=not isinstance(audio, np.ndarray),
                                             condition_on_previous_text=False, initial_prompt="Jarvis,")
        texte = " ".join(s.text.strip() for s in segments).strip()
        return nettoyer(texte)


def nettoyer(texte: str) -> str:
    """Retire les phrases que Whisper invente sur du silence ; vide si rien d'utile."""
    t = texte.strip()
    if not t or HALLUCINATIONS.search(t) or len(re.sub(r"\W", "", t)) < 2:
        return ""
    return t
