"""Etat en direct de l'arene : ecrit etat.json (atomique) que la page relit chaque seconde."""
import json
import math
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

PARIS = ZoneInfo("Europe/Paris")
COULEURS = ["#ffa028", "#3cc8ff", "#b48cff", "#2fd16f", "#ff7ab6", "#e6e05a", "#7ae0d0", "#ff8f5a", "#9fb4ff", "#d9d6cc"]


def propre(x):
    if isinstance(x, dict):
        return {k: propre(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [propre(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if hasattr(x, "item"):                       # nombres numpy
        return propre(x.item())
    return x


class Direct:
    def __init__(self, dossier):
        self.f = os.path.join(dossier, "etat.json")
        self.e = dict(version=0, version_relief=0, phase="", detail="", progression=0.0, jours=[], curseur=None, lignes=[], journal=[], pied=[], fini=False)
        self.dernier = 0.0

    def ligne(self, ident, nom, statut="en cours", couleur=None):
        for l in self.e["lignes"]:
            if l["id"] == ident:
                return l
        l = dict(id=ident, nom=nom, statut=statut, couleur=couleur or COULEURS[len(self.e["lignes"]) % len(COULEURS)], courbe=[], stats={}, tri=None, raison="")
        self.e["lignes"].append(l)
        return l

    def dire(self, txt, cls=""):
        self.e["journal"] = (self.e["journal"] + [dict(t=datetime.now(PARIS).strftime("%H:%M:%S"), txt=txt, cls=cls)])[-120:]
        print(txt, flush=True)

    def maj(self, relief=False, force=False, **k):
        self.e.update(k)
        self.e["version"] += 1
        if relief:
            self.e["version_relief"] += 1
        if not force and time.time() - self.dernier < 0.25:
            return
        self.dernier = time.time()
        leger = dict(self.e); leger["lignes"] = [{k: v for k, v in l.items() if k != "courbe"} for l in self.e["lignes"]]
        self._ecrire(self.f, leger)
        if self.e["version_relief"] != getattr(self, "relief_ecrit", -1) and (force or time.time() - getattr(self, "t_relief", 0) > 2):
            self.relief_ecrit = self.e["version_relief"]; self.t_relief = time.time()
            self._ecrire(os.path.join(os.path.dirname(self.f), "relief.json"),
                         dict(version_relief=self.e["version_relief"], jours=self.e["jours"], courbes={l["id"]: l["courbe"] for l in self.e["lignes"]}))

    def _ecrire(self, chemin, contenu):
        tmp = chemin + ".tmp"
        with open(tmp, "w") as f:
            json.dump(propre(contenu), f, separators=(",", ":"), allow_nan=False)
        os.replace(tmp, chemin)
