"""Algorithme genetique de l'evolution n°2 : celui de evolution/genetique.py (boucle de SETS : 96 strategies par
generation, environ 80 descendants par tournoi dans chaque espece, croisement uniforme, mutation gaussienne p = 0,18,
elites : 4 meilleures + la meilleure de chaque espece, le reste en immigrants), avec 7 ou 9 especes et 9 filtres.
Fitness sur 2011-2018, porte sur 2019-2022 (README.md)."""
import numpy as np

import moteur2 as M

POP, DESCENDANTS, P_MUT, SIGMA_MUT = 96, 80, 0.18, 0.12
CONTINUS = ["L", "Z", "stop", "objectif", "debut"]
DISCRETS = {"espece": 7, "marche": 2, "sens": 3, "filtre": len(M.FILTRES)}
N_ESPECES, QUOTA = 7, DESCENDANTS // 7


def configurer(n_especes):
    """7 especes sans les murs d'options, 9 avec."""
    global N_ESPECES, QUOTA
    N_ESPECES, QUOTA = n_especes, DESCENDANTS // n_especes
    DISCRETS["espece"] = n_especes
MARCHES = ["NQ", "ES"]
FIN_ENTRAINEMENT = np.datetime64("2018-12-31")
MIN_TRADES_FIT, MIN_TRADES_PORTE, SHARPE_PORTE = 150, 100, 0.5


def decoder(u):
    """Genes normalises -> parametres de la strategie."""
    esp = int(u["espece"])
    L = 1 + int(round(u["L"] * 11)) if esp == M.OUVERTURE else int(round(6 * 20 ** u["L"]))
    return {"espece": esp, "marche": int(u["marche"]), "L": L, "Z": round(0.25 + 2.75 * u["Z"], 3),
            "sens": int(u["sens"]), "stop": round(0.001 * 15 ** u["stop"], 5), "objectif": round(0.001 * 30 ** u["objectif"], 5),
            "debut": 1 + int(round(u["debut"] * 53)), "filtre": int(u["filtre"])}


def cle(g):
    return tuple(sorted(g.items()))


def hasard(rng, espece=None):
    u = {k: float(rng.random()) for k in CONTINUS}
    for k, n in DISCRETS.items():
        u[k] = int(rng.integers(0, n))
    if espece is not None:
        u["espece"] = espece
    return u


def croiser(rng, a, b):
    enfant = {k: (a[k] if rng.random() < 0.5 else b[k]) for k in a}
    for k in CONTINUS:
        if rng.random() < P_MUT:
            enfant[k] = float(np.clip(enfant[k] + rng.normal(0, SIGMA_MUT), 0.0, 1.0))
    for k, n in DISCRETS.items():
        if k != "espece" and rng.random() < P_MUT:
            enfant[k] = int(rng.integers(0, n))
    return enfant


def sharpe(x):
    s = x.std()
    return float(x.mean() / s * np.sqrt(252)) if s > 0 else 0.0


def mesures(rend, dol, ntr):
    eq = np.cumsum(rend)
    dd = float((eq - np.maximum.accumulate(np.r_[0.0, eq])[1:]).min()) if len(eq) else 0.0
    return {"sharpe": sharpe(rend), "trades": int(ntr.sum()), "rendement": float(rend.sum()), "pire_baisse": dd,
            "dollars": float(dol.sum()), "jours_gagnants": float((rend[ntr > 0] > 0).mean()) if (ntr > 0).any() else 0.0}


class Evaluateur:
    """Backtest + mesures, avec memoire : une strategie identique n'est testee qu'une fois."""

    def __init__(self, donnees):
        self.donnees = donnees            # {"NQ": dict, "ES": dict} (recherche seulement, ou donnees melangees)
        self.memoire = {}
        self.backtests = 0

    def evaluer(self, g):
        k = cle(g)
        if k not in self.memoire:
            d = self.donnees[MARCHES[g["marche"]]]
            rend, dol, ntr, _ = M.lancer(d, g)
            e = d["jours"] <= FIN_ENTRAINEMENT
            tr, va = mesures(rend[e], dol[e], ntr[e]), mesures(rend[~e], dol[~e], ntr[~e])
            fit = tr["sharpe"] * min(1.0, tr["trades"] / MIN_TRADES_FIT)
            porte = va["sharpe"] >= SHARPE_PORTE and va["trades"] >= MIN_TRADES_PORTE
            self.memoire[k] = {"fitness": fit, "porte": bool(porte), "entrainement": tr, "validation": va}
            self.backtests += 1
        return self.memoire[k]


class Evolution:
    def __init__(self, evaluateur, graine):
        self.ev = evaluateur
        self.rng = np.random.default_rng(graine)
        self.gen = 0
        self.suivant = 0
        self.pop = []
        self.nes = 0
        self.morts = 0
        self.historique = {"meilleure": [], "moyenne": [], "survivants": [], "leader": []}
        self.leader = None

    def _individu(self, u, parents=(), origine="immigrant"):
        g = decoder(u)
        r = self.ev.evaluer(g)
        self.suivant += 1
        self.nes += 1
        return {"id": self.suivant, "u": u, "g": g, "parents": list(parents), "origine": origine, "ne": self.gen, **r}

    @staticmethod
    def rang(x):
        return (x["porte"], x["fitness"])

    def demarrer(self):
        self.pop = [self._individu(hasard(self.rng, i % N_ESPECES)) for i in range(POP)]
        self._bilan()

    def generation(self):
        self.gen += 1
        classes = sorted(self.pop, key=self.rang, reverse=True)
        elites = classes[:4]
        for esp in range(N_ESPECES):
            meilleur = next((x for x in classes if x["g"]["espece"] == esp), None)
            if meilleur is not None and meilleur not in elites:
                elites.append(meilleur)
        enfants = []
        for esp in range(N_ESPECES):
            membres = [x for x in classes if x["g"]["espece"] == esp]
            for _ in range(QUOTA):
                if len(membres) < 2:
                    enfants.append(self._individu(hasard(self.rng, esp)))
                    continue
                t = min(3, len(membres))
                a, b = (max(self.rng.choice(len(membres), t, replace=False), key=lambda i: self.rang(membres[i])) for _ in range(2))
                pa, pb = membres[a], membres[b]
                enfants.append(self._individu(croiser(self.rng, pa["u"], pb["u"]), (pa["id"], pb["id"]), "descendant"))
        immigrants = [self._individu(hasard(self.rng, i % N_ESPECES)) for i in range(POP - len(elites) - len(enfants))]
        self.morts += len(self.pop) - len(elites)
        for x in elites:
            x["origine"] = "elite"
        self.pop = elites + enfants + immigrants
        self._bilan()

    def _bilan(self):
        fits = [x["fitness"] for x in self.pop]
        passent = [x for x in self.pop if x["porte"]]
        self.leader = max(passent, key=lambda x: x["fitness"]) if passent else None
        self.historique["meilleure"].append(round(max(fits), 4))
        self.historique["moyenne"].append(round(float(np.mean(fits)), 4))
        self.historique["survivants"].append(len(passent))
        self.historique["leader"].append(self.leader["id"] if self.leader else None)
