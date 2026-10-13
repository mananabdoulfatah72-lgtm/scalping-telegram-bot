"""Configuration de Jarvis : un fichier config.toml dans le dossier de Jarvis (%APPDATA%\\Jarvis sous Windows),
fusionné avec les valeurs par défaut ci-dessous. Les clés et jetons restent dans ce fichier local, jamais dans le
dépôt. Variables d'environnement reconnues : JARVIS_DOSSIER (autre dossier), ANTHROPIC_API_KEY (clé de l'API)."""
from __future__ import annotations

import copy
import os
import secrets
import sys
import threading
import tomllib
from pathlib import Path
from typing import Any

DEFAUTS: dict[str, Any] = {
    "general": {"nom": "Jarvis", "personnalite": "majordome", "ville": "Paris", "proprietaire": "",
                "confirmations": False},   # true = Jarvis demande ton accord avant les actions sensibles
    "cerveau": {
        "moteur": "auto",              # auto | api | claude_code
        "modele": "claude-opus-5-5",
        "effort": "low",               # low | medium | high | xhigh | max
        "max_tokens": 16000,
        "inactivite_minutes": 15,      # nouvelle conversation après ce silence
        "messages_max": 120,           # nouvelle conversation au-delà (l'historique n'est jamais raccourci)
        "cle_api": "",
    },
    "voix": {
        "active": True,
        "mot_reveil": "hey_jarvis",
        "seuil_reveil": 0.5,
        "modele_whisper": "small",
        "peripherique": "auto",        # auto | cuda | cpu (transcription)
        "synthese": "auto",            # auto | piper | windows | aucune
        "voix_piper": "fr_FR-tom-medium",
        "vitesse": 1.0,
        "suivi_secondes": 6.0,         # écoute sans mot de réveil après une réponse
        "silence_fin": 0.7,
        "micro": "",                   # nom ou numéro du micro ; vide = micro par défaut
    },
    "interface": {"port": 8765, "ouvrir_navigateur": True, "reseau": False, "cle": ""},
    "pc": {"commandes": True, "applications": {}},
    "hue": {"bridge": "", "utilisateur": ""},
    "obs": {"hote": "localhost", "port": 4455, "mot_de_passe": ""},
    "google": {"actif": False},
    "discord": {"jeton": "", "utilisateur_id": "", "salons": []},
    "instagram": {"comptes": []},
    "navigateur": {"cdp": "", "sans_tete": False},
    "twilio": {"sid": "", "jeton": "", "numero": "", "url_publique": "", "voix": "Polly.Lea"},
    "contacts": {},
    "presence": {"ip_telephone": "", "intervalle": 30, "arrivee": [], "depart": []},
    "ntfy": {"sujet": "", "serveur": "https://ntfy.sh"},
    "telegram": {"jeton": "", "chat_id": ""},
}


def dossier() -> Path:
    """Dossier de Jarvis (config, mémoire, jetons). Créé au besoin."""
    if os.environ.get("JARVIS_DOSSIER"):
        d = Path(os.environ["JARVIS_DOSSIER"])
    elif sys.platform == "win32" and os.environ.get("APPDATA"):
        d = Path(os.environ["APPDATA"]) / "Jarvis"
    else:
        d = Path.home() / ".config" / "jarvis"
    d.mkdir(parents=True, exist_ok=True)
    return d


# Réglages dont la valeur par défaut a changé : l'ancienne valeur (recopiée par l'installateur dans config.toml)
# est remplacée par la nouvelle au chargement. Une autre valeur choisie à la main est gardée.
ANCIENS_DEFAUTS = {"voix.silence_fin": (0.9, 0.7)}


def fusionner(base: dict, ajout: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in ajout.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = fusionner(out[k], v)
        else:
            out[k] = v
    return out


class Config:
    """Accès par chemin pointé : cfg.get("hue.bridge"). Les modifications faites par Jarvis (appairage Hue,
    personnalité...) sont réécrites dans config.toml par ecrire()."""

    def __init__(self, donnees: dict | None = None, fichier: Path | None = None):
        self.fichier = fichier
        self.donnees = fusionner(DEFAUTS, donnees or {})
        self._verrou = threading.Lock()

    @classmethod
    def charger(cls, fichier: Path | None = None) -> "Config":
        fichier = fichier or dossier() / "config.toml"
        donnees = {}
        if fichier.exists():
            with open(fichier, "rb") as f:
                donnees = tomllib.load(f)
        cfg = cls(donnees, fichier)
        for chemin, (ancien, nouveau) in ANCIENS_DEFAUTS.items():
            if cfg.get(chemin) == ancien:            # valeur laissée telle que l'installateur l'avait écrite
                cfg.set(chemin, nouveau, ecrire=False)
        return cfg

    def get(self, chemin: str, defaut: Any = None) -> Any:
        x: Any = self.donnees
        for morceau in chemin.split("."):
            if not isinstance(x, dict) or morceau not in x:
                return defaut
            x = x[morceau]
        return x

    def set(self, chemin: str, valeur: Any, ecrire: bool = True) -> None:
        with self._verrou:
            morceaux = chemin.split(".")
            x = self.donnees
            for m in morceaux[:-1]:
                x = x.setdefault(m, {})
            x[morceaux[-1]] = valeur
        if ecrire:
            self.ecrire_cle(chemin, valeur)

    def cle_api(self) -> str:
        return os.environ.get("ANTHROPIC_API_KEY") or self.get("cerveau.cle_api", "") or ""

    def ecrire_cle(self, chemin: str, valeur: Any) -> None:
        """Réécrit une seule clé dans config.toml en gardant le reste du fichier (et ses commentaires)."""
        if not self.fichier:
            return
        section, _, cle = chemin.rpartition(".")
        ligne = f"{cle} = {toml_valeur(valeur)}"
        texte = self.fichier.read_text(encoding="utf-8") if self.fichier.exists() else ""
        lignes = texte.splitlines()
        entete = f"[{section}]"
        i_sec = next((i for i, l in enumerate(lignes) if l.strip() == entete), None)
        if i_sec is None:
            lignes += ["", entete, ligne]
        else:
            fin = next((j for j in range(i_sec + 1, len(lignes)) if lignes[j].strip().startswith("[")), len(lignes))
            i_cle = next((j for j in range(i_sec + 1, fin)
                          if lignes[j].split("=", 1)[0].strip() == cle and not lignes[j].lstrip().startswith("#")), None)
            if i_cle is None:
                lignes.insert(fin if fin == len(lignes) else fin, ligne)
            else:
                lignes[i_cle] = ligne
        self.fichier.write_text("\n".join(lignes) + "\n", encoding="utf-8")


def toml_valeur(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, list):
        return "[" + ", ".join(toml_valeur(x) for x in v) + "]"
    raise TypeError(f"valeur non gérée dans config.toml : {v!r}")


def jeton_local() -> str:
    """Jeton aléatoire qui protège l'API locale (proxy MCP, outils) : seul un programme qui lit ce fichier, donc un
    programme de l'utilisateur, peut appeler les outils de Jarvis."""
    f = dossier() / "jeton_local.txt"
    if not f.exists():
        f.write_text(secrets.token_urlsafe(32), encoding="utf-8")
    return f.read_text(encoding="utf-8").strip()
