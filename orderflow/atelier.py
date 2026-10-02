#!/usr/bin/env python3
"""Donnees de la page « Atelier order flow » (atelier/index.html) : une fiche par seance (barres d'une minute, delta,
VWAP et ecart-type, carnet au 1er niveau, POC du jour, niveaux de la veille dont POC, VAH, VAL, HVN et LVN, footprint au
tick, plus gros ordres) et l'index avec les resultats des tests (exploration, machine, coffre).
Ecrit atelier/index.json et atelier/seances/AAAA-MM-JJ.json. Lancer depuis ce dossier : python3 atelier.py"""
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

import outils as O
import precalcul as P
import signaux as G
from explorer import decoupe

warnings.filterwarnings("ignore", category=RuntimeWarning)
ICI = Path(__file__).resolve().parent
A = ICI / "atelier"
GROS_PAR_SEANCE = 150


def noeuds(prix, volume, largeur=41, n=8):
    """Pour l'affichage seulement : les n principaux sommets (HVN) et creux (LVN) du profil lisse sur `largeur` ticks
    (la machine, elle, utilise la definition du README : lissage sur 5 ticks, noeud le plus proche de l'ouverture)."""
    if len(prix) == 0:
        return [], []
    o = np.argsort(prix)
    p, v = prix[o], volume[o]
    grille = np.arange(p[0], p[-1] + O.TICK / 2, O.TICK)
    vg = np.zeros(len(grille))
    np.add.at(vg, np.round((p - p[0]) / O.TICK).astype(int), v)
    lisse = np.convolve(vg, np.ones(largeur) / largeur, mode="same")
    i = np.arange(1, len(lisse) - 1)
    hi = i[(lisse[1:-1] > lisse[:-2]) & (lisse[1:-1] >= lisse[2:])]
    lo = i[(lisse[1:-1] < lisse[:-2]) & (lisse[1:-1] <= lisse[2:])]
    lo = lo[(lo > largeur) & (lo < len(lisse) - largeur)]          # pas les bords du profil
    def espaces(idx, ordre):
        pris = []
        for j in idx[ordre]:
            if all(abs(j - k) > 2 * largeur for k in pris):
                pris.append(j)
            if len(pris) == n:
                break
        return sorted(grille[pris].tolist())
    return espaces(hi, np.argsort(-lisse[hi])), espaces(lo, np.argsort(lisse[lo]))


def r2(x):
    return [None if not np.isfinite(v) else round(float(v), 2) for v in x]


def lire(nom):
    p = ICI / nom
    if not p.exists():
        return None
    return json.loads(p.read_text()) if nom.endswith(".json") else p.read_text()


def main():
    S = O.Seances()
    n = len(S.jours)
    k = decoupe(n)
    fp = O.lire_footprint(O.D)
    gros = G.lire_gros(S, O.D)
    B = P.Briques(S, fp, gros)
    t = pd.to_datetime(fp["m"])
    fp["jour"] = t.dt.normalize()
    fp["minute"] = ((t - fp["jour"]).dt.total_seconds() // 60 - 570).astype(int)
    fp = fp[(fp["minute"] >= 0) & (fp["minute"] < 390)]
    par_jour = {j: g for j, g in fp.groupby("jour")}
    gros_jour = {j: g for j, g in gros.groupby("jour")}
    (A / "seances").mkdir(parents=True, exist_ok=True)
    index, profil_veille, noeuds_veille = [], None, ([], [])
    for d, jour in enumerate(S.jours):
        nom = f"{jour.date()}"
        g = par_jour.get(jour, fp.iloc[:0])
        tot = g.groupby("prix")[["achat", "vente"]].sum().sum(axis=1)
        profil = P.profil(tot.index.to_numpy(float), tot.to_numpy(float))
        affiches = noeuds(tot.index.to_numpy(float), tot.to_numpy(float))
        lignes = []
        for m, x in g.groupby("minute"):
            ticks = np.round(x["prix"].to_numpy() / O.TICK).astype(int)
            bas = int(ticks.min())
            a, v = np.zeros(ticks.max() - bas + 1, int), np.zeros(ticks.max() - bas + 1, int)
            np.add.at(a, ticks - bas, x["achat"].to_numpy().astype(int))
            np.add.at(v, ticks - bas, x["vente"].to_numpy().astype(int))
            lignes.append([int(m), round(bas * O.TICK, 2), a.tolist(), v.tolist()])
        gj = gros_jour.get(jour)
        gros_l = []
        if gj is not None and len(gj):
            gj = gj.nlargest(GROS_PAR_SEANCE, "taille").sort_values("seconde")
            gros_l = [[int(s), round(float(p), 2), int(e), int(q)] for s, p, e, q in gj[["seconde", "prix", "sens", "taille"]].to_numpy()]
        vw, s1 = B.niveaux[8, d], B.niveaux[9, d] - B.niveaux[8, d]
        niv = {}
        if d > 0:
            ph, pl = S.veille(d)
            niv = {"veille_haut": ph, "veille_bas": pl, "veille_cloture": round(float(S.prix[d - 1, -1]), 2)}
            if profil_veille is not None and np.isfinite(profil_veille[0]):
                poc, vah, val = profil_veille[:3]
                niv.update({"poc": poc, "vah": vah, "val": val, "hvn": noeuds_veille[0], "lvn": noeuds_veille[1],
                            "hvn_machine": float(B.niveaux[6, d, 0]), "lvn_machine": float(B.niveaux[7, d, 0])})
        niv.update({"or_haut": float(B.niveaux[13, d, 29]), "or_bas": float(B.niveaux[14, d, 29])})
        fiche = {"jour": nom, "contrat": int(S.contrat[d]), "changement": bool(S.change[d]),
                 "m": {"o": r2(B.o[d]), "h": r2(B.h[d]), "l": r2(B.l[d]), "c": r2(B.c[d]),
                       "a": B.achat[d].astype(int).tolist(), "v": B.vente[d].astype(int).tolist(),
                       "vwap": r2(vw), "sd": r2(s1), "l1": [round(float(x), 3) for x in B.l1[d]], "pocj": r2(B.niveaux[15, d])},
                 "niveaux": niv, "fp": lignes, "gros": gros_l}
        (A / "seances" / f"{nom}.json").write_text(json.dumps(fiche, separators=(",", ":")))
        index.append({"jour": nom, "fichier": f"seances/{nom}.json", "partie": "exploration" if d < k else "coffre",
                      "ouverture": round(float(B.o[d, 0]), 2), "cloture": round(float(B.c[d, -1]), 2),
                      "haut": round(float(B.h[d].max()), 2), "bas": round(float(B.l[d].min()), 2),
                      "volume": int(B.vol[d].sum()), "delta": int((B.achat[d] - B.vente[d]).sum()), "transactions": int(S.n_trades[d]),
                      "changement": bool(S.change[d])})
        profil_veille, noeuds_veille = profil, affiches
    machine = lire("finalistes_of.json")
    reel = ICI / "machine" / "strategies_reel.csv.gz"
    resultats = {"exploration": lire("survivants_of.json"), "exploration_texte": lire("exploration_of.txt"),
                 "machine": machine, "machine_texte": lire("machine_of.txt"), "coffre": lire("coffre_of.json"),
                 "coffre_texte": lire("coffre_of.txt"), "achats": lire("donnees/achats.txt")}
    if reel.exists():
        r = pd.read_csv(reel)
        h = pd.read_csv(ICI / "machine" / "strategies_hasard.csv.gz")
        bins = np.round(np.arange(-4, 4.01, 0.25), 2)
        resultats["distribution"] = {"bornes": bins.tolist(), "reel": np.histogram(r["fitness"].clip(-4, 4), bins)[0].tolist(),
                                     "hasard": np.histogram(h["fitness"].clip(-4, 4), bins)[0].tolist(),
                                     "n_reel": int(len(r)), "n_hasard": int(len(h))}
        hist = lire("machine/historique.json")
        if hist:
            resultats["historique"] = hist
    (A / "index.json").write_text(json.dumps({"genere": pd.Timestamp.now(tz="Europe/Paris").strftime("%Y-%m-%d %H:%M"),
                                              "seances": index, "resultats": resultats, "coupe": k}, ensure_ascii=False))
    print(f"{n} seances ecrites dans {A}")


if __name__ == "__main__":
    main()
