"""Algorithme genetique de la machine n°3 (README.md, regles v2) : 256 strategies par generation, elites (4 meilleures +
la meilleure de chaque famille), 14 descendants par famille (tournoi, croisement uniforme, mutation p = 0,18), le reste
en immigrants. Fitness sur 2016-2019, porte sur 2020-2022."""
import numpy as np

import moteur3 as M

POP, QUOTA, P_MUT, SIGMA_MUT = 256, 14, 0.18, 0.12
NF = len(M.FAMILLES)
CONTINUS = ["L", "Z", "stop", "objectif", "debut", "duree"]
MARCHES = ["RTY", "YM", "GC", "CL", "6E", "NQ", "ES"]
DISCRETS = {"famille": NF, "inverse": 2, "marche": len(MARCHES), "sens": 3, "filtre": 3}
DEBUT_ENTRAINEMENT, FIN_ENTRAINEMENT = np.datetime64("2016-01-01"), np.datetime64("2019-12-31")
MIN_TRADES_FIT, MIN_TRADES_PORTE, SHARPE_PORTE = 150, 100, 0.5


def decoder(u, nbs):
    f = int(u["famille"])
    nb = nbs[MARCHES[int(u["marche"])]]
    L = 1 + int(round(u["L"] * 11)) if f == M.OUVERTURE else int(round(2 * 60 ** u["L"]))
    return {"famille": f, "inverse": int(u["inverse"]), "marche": int(u["marche"]), "L": L,
            "Z": round(0.25 + 2.75 * u["Z"], 3), "sens": int(u["sens"]), "stop": round(0.001 * 15 ** u["stop"], 5),
            "objectif": round(0.001 * 30 ** u["objectif"], 5), "debut": 1 + int(round(u["debut"] * (int(0.75 * nb) - 1))),
            "duree": int(round(3 * 20 ** u["duree"])), "filtre": int(u["filtre"])}


def cle(g):
    return tuple(sorted(g.items()))


def hasard(rng, famille=None):
    u = {k: float(rng.random()) for k in CONTINUS}
    for k, n in DISCRETS.items():
        u[k] = int(rng.integers(0, n))
    if famille is not None:
        u["famille"] = famille
    return u


def croiser(rng, a, b):
    enfant = {k: (a[k] if rng.random() < 0.5 else b[k]) for k in a}
    for k in CONTINUS:
        if rng.random() < P_MUT:
            enfant[k] = float(np.clip(enfant[k] + rng.normal(0, SIGMA_MUT), 0.0, 1.0))
    for k, n in DISCRETS.items():
        if k != "famille" and rng.random() < P_MUT:
            enfant[k] = int(rng.integers(0, n))
    return enfant


def sharpe(x):
    s = x.std()
    return float(x.mean() / s * np.sqrt(252)) if s > 0 else 0.0


def mesures(rend, dol, ntr):
    return {"sharpe": sharpe(rend), "trades": int(ntr.sum()), "dollars": float(dol.sum()),
            "jours_gagnants": float((rend[ntr > 0] > 0).mean()) if (ntr > 0).any() else 0.0}


class Evaluateur:
    """Backtest + mesures, avec memoire."""

    def __init__(self, donnees):
        self.donnees = donnees
        self.nbs = {m: int(d["nb"]) for m, d in donnees.items()}
        self.memoire = {}
        self.backtests = 0

    def evaluer(self, g):
        k = cle(g)
        if k not in self.memoire:
            d = self.donnees[MARCHES[g["marche"]]]
            rend, dol, ntr = M.lancer(d, g)
            jouable = ~d["interdit"]
            e = (d["jours"] >= DEBUT_ENTRAINEMENT) & (d["jours"] <= FIN_ENTRAINEMENT) & jouable
            v = (d["jours"] > FIN_ENTRAINEMENT) & jouable
            tr, va = mesures(rend[e], dol[e], ntr[e]), mesures(rend[v], dol[v], ntr[v])
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
        self.nes = self.morts = self.deployes = self.elimines = 0
        self.historique = {"meilleure": [], "moyenne": [], "deployes": [], "leader": [], "nes": [], "morts": [], "par_marche": []}
        self.leader = None

    def _individu(self, u, parents=(), origine="immigrant"):
        g = decoder(u, self.ev.nbs)
        r = self.ev.evaluer(g)
        self.suivant += 1
        self.nes += 1
        if r["porte"]:
            self.deployes += 1
        else:
            self.elimines += 1
        return {"id": self.suivant, "u": u, "g": g, "parents": list(parents), "origine": origine, "ne": self.gen, **r}

    @staticmethod
    def rang(x):
        return (x["porte"], x["fitness"])

    def demarrer(self):
        self.pop = [self._individu(hasard(self.rng, f % NF)) for f in range(POP)]
        self._bilan()

    def generation(self):
        self.gen += 1
        classes = sorted(self.pop, key=self.rang, reverse=True)
        elites = classes[:4]
        for f in range(NF):
            m = next((x for x in classes if x["g"]["famille"] == f), None)
            if m is not None and m not in elites:
                elites.append(m)
        enfants = []
        for f in range(NF):
            membres = [x for x in classes if x["g"]["famille"] == f]
            for _ in range(QUOTA):
                if len(membres) < 2:
                    enfants.append(self._individu(hasard(self.rng, f)))
                    continue
                t = min(3, len(membres))
                a, b = (max(self.rng.choice(len(membres), t, replace=False), key=lambda i: self.rang(membres[i])) for _ in range(2))
                pa, pb = membres[a], membres[b]
                enfants.append(self._individu(croiser(self.rng, pa["u"], pb["u"]), (pa["id"], pb["id"]), "descendant"))
        immigrants = [self._individu(hasard(self.rng, i % NF)) for i in range(POP - len(elites) - len(enfants))]
        self.morts += len(self.pop) - len(elites)
        for x in elites:
            x["origine"] = "elite"
        self.pop = elites + enfants + immigrants
        self._bilan()

    def _bilan(self):
        fits = [x["fitness"] for x in self.pop]
        passent = [x for x in self.pop if x["porte"]]
        self.leader = max(passent, key=lambda x: x["fitness"]) if passent else None
        h = self.historique
        h["meilleure"].append(round(max(fits), 4))
        h["moyenne"].append(round(float(np.mean(fits)), 4))
        h["deployes"].append(len(passent))
        h["leader"].append(self.leader["id"] if self.leader else None)
        h["nes"].append(self.nes)
        h["morts"].append(self.morts)
        h["par_marche"].append([sum(1 for x in passent if x["g"]["marche"] == m) for m in range(len(MARCHES))])
