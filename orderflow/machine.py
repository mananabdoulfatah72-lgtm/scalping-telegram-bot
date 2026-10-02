#!/usr/bin/env python3
"""Machine order flow (README.md, regles v2) : algorithme genetique sur les seances d'exploration (deux premiers tiers),
200 strategies par generation, 60 generations, 6 graines ; puis la meme machine, memes graines, ou le sens de chaque
trade est tire au hasard (fixe pour une seance et une minute) : le meilleur resultat que la selection produit sans
information. Le coffre (dernier tiers) n'est pas charge.
Ecrit machine/strategies_reel.csv.gz, machine/strategies_hasard.csv.gz, machine/historique.json, finalistes_of.json et
machine_of.txt. Lancer depuis ce dossier : python3 machine.py"""
import json
import os
import time
import warnings
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

import moteur_of as M
import outils as O
import precalcul as P
import signaux as G
from explorer import decoupe

warnings.filterwarnings("ignore", category=RuntimeWarning)
ICI = Path(__file__).resolve().parent
SORTIE = ICI / "machine"
POP, QUOTA, P_MUT, SIGMA_MUT = 200, 20, 0.18, 0.12
GENERATIONS = int(os.getenv("OF_GENERATIONS", 60))
GRAINES = [int(x) for x in os.getenv("OF_GRAINES", "1,2,3,4,5,6").split(",")]
NF = len(M.FAMILLES)
DISCRETS = {"famille": NF, "niveau": len(P.NIVEAUX), "confirmation": len(M.CONFIRMATIONS), "W": len(P.FENETRES),
            "sens": 2, "sortie": len(M.SORTIES), "stop": len(M.STOPS), "debut": len(M.DEBUTS), "fin": len(M.FINS)}
AVEC_W = (1, 2, 4)
B = None                                   # briques partagees avec les processus (fork)


def canon(g):
    """Les genes sans effet pour la famille sont mis a une valeur fixe : deux genomes qui donnent la meme strategie
    comptent pour une seule."""
    g = dict(g)
    f = g["famille"]
    if f != 0:
        g["niveau"], g["confirmation"] = 0, 0
    if f not in AVEC_W:
        g["W"] = P.FENETRES[0]
    if f == 0:
        g["seuil"] = round(7 * g["seuil"]) / 7
    elif f == 5:
        g["seuil"] = round(6 * g["seuil"]) / 6
    elif f == 2:
        g["seuil"] = 0.0
    else:
        g["seuil"] = round(g["seuil"], 2)
    return g


def cle(g):
    return tuple(sorted(g.items()))


def reparer(u):
    """Fenetre horaire non vide : la fin est apres le debut."""
    while M.FINS[u["fin"]] <= M.DEBUTS[u["debut"]]:
        u["fin"] += 1
    return u


def hasard(rng, famille=None):
    u = {"seuil": float(rng.random())}
    for k, n in DISCRETS.items():
        u[k] = int(rng.integers(0, n))
    if famille is not None:
        u["famille"] = famille
    return reparer(u)


def croiser(rng, a, b):
    enfant = {k: (a[k] if rng.random() < 0.5 else b[k]) for k in a}
    if rng.random() < P_MUT:
        enfant["seuil"] = float(np.clip(enfant["seuil"] + rng.normal(0, SIGMA_MUT), 0.0, 1.0))
    for k, n in DISCRETS.items():
        if k != "famille" and rng.random() < P_MUT:
            enfant[k] = int(rng.integers(0, n))
    return reparer(enfant)


class Evaluateur:
    def __init__(self, Bq, controle, signes):
        self.B, self.controle, self.signes = Bq, controle, signes
        self.memoire = {}

    def evaluer(self, g):
        k = cle(g)
        if k not in self.memoire:
            sig = M.signal(self.B, g)
            total, n = M.simuler(sig, self.B.bid, self.B.ask, g["sortie"], g["stop"], 1 if self.controle else 0, self.signes)
            fit, t = M.fitness(total, n)
            self.memoire[k] = {"fitness": round(fit, 4), "t": round(t, 3), "trades": int(n),
                               "net_pts": round(float(total.sum() / n), 3) if n else 0.0,
                               "seances_gagnantes": round(float((total > 0).sum() / max(1, (total != 0).sum())), 3)}
        return self.memoire[k]


class Evolution:
    def __init__(self, ev, graine):
        self.ev, self.rng, self.gen = ev, np.random.default_rng(graine), 0
        self.pop, self.historique = [], {"meilleure": [], "moyenne": [], "par_famille": []}

    def _individu(self, u):
        g = canon(M.decoder(u))
        return {"u": u, "g": g, **self.ev.evaluer(g)}

    def demarrer(self):
        self.pop = [self._individu(hasard(self.rng, f % NF)) for f in range(POP)]
        self._bilan()

    def generation(self):
        self.gen += 1
        classes = sorted(self.pop, key=lambda x: x["fitness"], reverse=True)
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
                a, b = (max(self.rng.choice(len(membres), t, replace=False), key=lambda i: membres[i]["fitness"]) for _ in range(2))
                enfants.append(self._individu(croiser(self.rng, membres[a]["u"], membres[b]["u"])))
        immigrants = [self._individu(hasard(self.rng, i % NF)) for i in range(POP - len(elites) - len(enfants))]
        self.pop = elites + enfants + immigrants
        self._bilan()

    def _bilan(self):
        fits = [x["fitness"] for x in self.pop]
        h = self.historique
        h["meilleure"].append(round(max(fits), 4))
        h["moyenne"].append(round(float(np.mean(fits)), 4))
        h["par_famille"].append([round(max([x["fitness"] for x in self.pop if x["g"]["famille"] == f] or [0.0]), 4) for f in range(NF)])


def lancer(args):
    graine, controle = args
    signes = np.random.default_rng(10_000 + graine).choice(np.array([-1, 1], np.int8), size=(B.nj, 390)) if controle \
        else np.zeros((B.nj, 390), np.int8)
    ev = Evaluateur(B, controle, signes)
    evo = Evolution(ev, graine)
    t0 = time.time()
    evo.demarrer()
    for _ in range(GENERATIONS):
        evo.generation()
    lignes = [{**dict(k), **r} for k, r in ev.memoire.items()]
    print(f"  graine {graine} {'hasard' if controle else 'reel'} : {len(lignes)} strategies, meilleure fitness"
          f" {evo.historique['meilleure'][-1]:.2f}, {time.time() - t0:.0f} s", flush=True)
    return graine, controle, lignes, evo.historique


def briques_exploration():
    S = O.Seances()
    n = len(S.jours)
    k = decoupe(n)
    S.restreindre(k)
    gros = G.lire_gros(S, O.D)
    gros = gros[gros["jour"] <= S.jours[-1]]
    fp = O.lire_footprint(O.D, jusqu_au=S.jours[-1])
    return P.Briques(S, fp, gros), S, n, k


def resume(df):
    """Une ligne par strategie distincte (une strategie peut apparaitre dans plusieurs graines)."""
    cles = ["famille", "niveau", "confirmation", "W", "seuil", "sens", "sortie", "stop", "debut", "fin"]
    return df.drop_duplicates(cles).sort_values("fitness", ascending=False).reset_index(drop=True)


def main():
    global B
    t0 = time.time()
    B, S, n, k = briques_exploration()
    print(f"briques : {k} seances d'exploration du {S.jours[0].date()} au {S.jours[-1].date()} ({time.time() - t0:.0f} s)", flush=True)
    M.simuler(np.zeros((2, 390), np.int8), B.bid[:2], B.ask[:2], 5, 0, 0, np.zeros((2, 390), np.int8))   # compilation
    taches = [(g, False) for g in GRAINES] + [(g, True) for g in GRAINES]
    with Pool(min(len(taches), os.cpu_count() or 1)) as pool:
        res = pool.map(lancer, taches)
    SORTIE.mkdir(exist_ok=True)
    reel = resume(pd.DataFrame([l for _, c, ls, _ in res if not c for l in ls]))
    nul = resume(pd.DataFrame([l for _, c, ls, _ in res if c for l in ls]))
    reel.to_csv(SORTIE / "strategies_reel.csv.gz", index=False)
    nul.to_csv(SORTIE / "strategies_hasard.csv.gz", index=False)
    (SORTIE / "historique.json").write_text(json.dumps(
        {"familles": M.FAMILLES, "runs": [{"graine": g, "hasard": c, **h} for g, c, _, h in res]}, ensure_ascii=False))
    meilleur_nul = float(nul["fitness"].max())
    finalistes = []
    for _, x in reel.iterrows():
        if x["fitness"] <= meilleur_nul or len(finalistes) == 5:
            break
        if all(int(x["famille"]) != f["g"]["famille"] for f in finalistes):
            g = {c: (float(x[c]) if c == "seuil" else int(x[c])) for c in ["famille", "niveau", "confirmation", "W", "seuil", "sens", "sortie", "stop", "debut", "fin"]}
            finalistes.append({"g": g, "description": M.decrire(g), "exploration": {c: (int(x[c]) if c == "trades" else float(x[c])) for c in ["fitness", "t", "trades", "net_pts", "seances_gagnantes"]}})
    (ICI / "finalistes_of.json").write_text(json.dumps({"finalistes": finalistes, "meilleure_fitness_hasard": meilleur_nul,
                                                        "seances_exploration": k, "seances_total": n}, indent=1, ensure_ascii=False))
    L = [f"Machine order flow NQ, exploration : {k} seances du {S.jours[0].date()} au {S.jours[-1].date()} ; le coffre ({n - k} seances) n'est pas charge.",
         f"{len(GRAINES)} graines x {GENERATIONS} generations x {POP} strategies, sur les vraies donnees puis sur des sens tires au hasard.",
         f"Strategies distinctes evaluees : {len(reel)} sur les vraies donnees, {len(nul)} sur le hasard.",
         "Fitness = t du gain net par seance, reduit sous 60 trades. Execution au marche (ecart paye) + 1 point par aller-retour.", "",
         f"Meilleure fitness obtenue sur le hasard (sans aucune information de sens) : {meilleur_nul:.2f}",
         f"Strategies reelles au-dessus : {int((reel['fitness'] > meilleur_nul).sum())}", "",
         "Meilleure strategie par famille (vraies donnees | hasard) :"]
    for f, nom in enumerate(M.FAMILLES):
        r, h = reel[reel["famille"] == f], nul[nul["famille"] == f]
        if r.empty:
            continue
        x = r.iloc[0]
        g = {c: (float(x[c]) if c == "seuil" else int(x[c])) for c in ["famille", "niveau", "confirmation", "W", "seuil", "sens", "sortie", "stop", "debut", "fin"]}
        L.append(f"- {nom} : fitness {x['fitness']:.2f} (t {x['t']:+.2f}, {int(x['trades'])} trades, {x['net_pts']:+.2f} pt net par trade)"
                 f" | hasard {h['fitness'].max():.2f}\n    {M.decrire(g)}")
    L += ["", f"Finalistes (au plus 5, familles differentes, au-dessus du hasard) : {len(finalistes)}"]
    for i, f in enumerate(finalistes, 1):
        e = f["exploration"]
        L.append(f"{i}. {f['description']}\n   fitness {e['fitness']:.2f}, t {e['t']:+.2f}, {e['trades']} trades, {e['net_pts']:+.2f} pt net par trade")
    L.append(f"\nDuree : {time.time() - t0:.0f} s")
    (ICI / "machine_of.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
