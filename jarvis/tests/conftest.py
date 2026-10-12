"""Chaque test tourne avec un dossier Jarvis temporaire (config, mémoire, jeton) et des services propres."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(autouse=True)
def dossier_jarvis(tmp_path, monkeypatch):
    monkeypatch.setenv("JARVIS_DOSSIER", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from jarvis import outils
    from jarvis.config import Config
    from jarvis.confirmation import Confirmations
    from jarvis.memoire import Memoire
    from jarvis.services import S
    (tmp_path / "config.toml").write_text("[general]\nproprietaire = \"Manan\"\n", encoding="utf-8")
    S.cfg = Config.charger(tmp_path / "config.toml")
    S.memoire = Memoire(tmp_path / "memoire.db")
    S.confirmations = Confirmations(delai=0.5)
    S.synthese = None
    S.cerveau = None
    outils.charger_tous()
    yield tmp_path


class FauxRequests:
    """Remplace requests.request : renvoie des réponses préparées selon l'adresse, et garde les appels."""

    def __init__(self, routes):
        self.routes, self.appels = routes, []

    def __call__(self, methode, url, **kw):
        self.appels.append((methode, url, kw))
        for motif, rep in self.routes.items():
            if motif in url:
                r = rep(methode, url, kw) if callable(rep) else rep
                return Reponse(r)
        return Reponse({"erreur": "inconnu"}, 404)


class Reponse:
    def __init__(self, donnees, code=200):
        import json
        self.status_code = code
        self._d = donnees
        self.content = json.dumps(donnees).encode() if donnees is not None else b""
        self.text = self.content.decode()

    def json(self):
        return self._d

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")
