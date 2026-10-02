#!/usr/bin/env python3
"""Tests des outils d'order flow sur des donnees fabriquees : execution au bid/ask, delta et VWAP, detecteurs sans
regard vers le futur. Lancer depuis ce dossier : python3 test_orderflow.py [dossier de donnees reelles]"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

import outils as O
import signaux as G


def fabriquer(dossier, n_jours=8, graine=1):
    rng = np.random.default_rng(graine)
    lignes, gros = [], []
    prix = 20000.0
    for k, j in enumerate(pd.bdate_range("2026-06-01", periods=n_jours)):
        for s in range(0, O.NS, 2):                    # une seconde sur deux a des transactions
            prix += rng.normal(0, 0.5)
            p = round(prix * 4) / 4
            biais = 12 if (s // 900) % 3 == 0 else 0      # un quart d'heure sur trois deseq, pour que H5 ait des signaux
            a, v = int(rng.integers(0, 30)) + biais, int(rng.integers(0, 30))
            t = j + pd.Timedelta(seconds=34200 + s)
            lignes.append((t.strftime("%Y-%m-%d %H:%M:%S"), p, p + 0.25, p - 0.25, a, v, int(rng.integers(1, 9)), p - 0.25, p, 5, 6, 100 + (k >= 6)))
            if rng.random() < 0.002:
                gros.append((t.strftime("%Y-%m-%d %H:%M:%S.000"), p, int(rng.choice([-1, 1])), int(rng.integers(10, 60))))
    cols = ["t", "prix", "haut", "bas", "achat", "vente", "n", "bid", "ask", "bid_q", "ask_q", "contrat"]
    pd.DataFrame(lignes, columns=cols).to_csv(Path(dossier) / "nq_secondes_1.csv.gz", index=False)
    pd.DataFrame(gros, columns=["t", "prix", "sens", "taille"]).to_csv(Path(dossier) / "nq_gros_1.csv.gz", index=False)


with tempfile.TemporaryDirectory() as tmp:
    fabriquer(tmp)
    S = O.Seances(tmp)
    assert len(S.jours) == 8 and S.change[6] and not S.change[5]
    # 1. execution : achat au meilleur vendeur a la seconde suivante, vente au meilleur acheteur apres la duree
    tr = pd.DataFrame({"seance": [2], "seconde": [1000], "sens": [1], "duree": [900]})
    x = O.executer(S, tr).iloc[0]
    assert x["entree"] == S.ask[2, 1001] and x["sortie"] == S.bid[2, 1901]
    assert np.isclose(x["net"], S.bid[2, 1901] - S.ask[2, 1001] - 1.0)
    tr = pd.DataFrame({"seance": [2], "seconde": [1000], "sens": [-1], "duree": [900]})
    x = O.executer(S, tr).iloc[0]
    assert np.isclose(x["net"], S.bid[2, 1001] - S.ask[2, 1901] - 1.0)
    print("1. execution : achat au vendeur, vente a l'acheteur, a la seconde suivante, + 0,5 point par ordre : OK")
    # 2. barres d'une minute : delta, CVD, VWAP
    m = S.minutes(3)
    assert np.isclose(m["delta"].sum(), S.achat[3].sum() - S.vente[3].sum()) and np.isclose(m["cvd"].iloc[-1], m["delta"].sum())
    vol = S.achat[3] + S.vente[3]
    assert np.isclose(m["vwap"].iloc[-1], (S.prix[3] * vol).sum() / vol.sum())
    print("2. minutes : delta, CVD et VWAP exacts : OK")
    # 3. aucun regard vers le futur : modifier la fin d'une seance ne change pas les signaux d'avant
    gros = G.lire_gros(S, tmp)
    for nom, f in (("H2", lambda S_: G.h2_absorption(S_, [5])), ("H3", lambda S_: G.h3_gros_ordres(S_, gros, [5])),
                   ("H4", lambda S_: G.h4_divergence(S_, [5])), ("H5", lambda S_: G.h5_delta15(S_, [5]))):
        avant = f(S)
        coupe = 12000
        for a in ("prix", "haut", "bas", "bid", "ask"):
            getattr(S, a)[5, coupe:] += 37.0
        S.achat[5, coupe:] *= 3
        apres = f(S)
        for a in ("prix", "haut", "bas", "bid", "ask"):
            getattr(S, a)[5, coupe:] -= 37.0
        S.achat[5, coupe:] /= 3
        av = avant[avant["seconde"] < coupe - 1].reset_index(drop=True)
        ap = apres[apres["seconde"] < coupe - 1].reset_index(drop=True)
        assert len(av) == len(ap) and (av.to_numpy() == ap.to_numpy()).all(), (nom, av.head(), ap.head())
        print(f"3. {nom} : {len(avant)} signaux sur une seance fabriquee ; la fin de seance ne change pas les signaux d'avant : OK")
    # 4. jour de changement de contrat : aucun signal
    assert G.h5_delta15(S, [6]).empty and G.h4_divergence(S, [6]).empty
    print("4. aucun signal le jour d'un changement de contrat : OK")
    # 5. hasard : memes seances, sens et durees
    ts = O.hasard(S, G.h4_divergence(S, [3, 4, 5]), n=50)
    assert len(ts) == 50 and np.isfinite(ts).all()
    print("5. placements au hasard : OK")
