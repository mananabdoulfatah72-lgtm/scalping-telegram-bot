#!/usr/bin/env python3
"""Detail de S2b (descriptif) : trades de l'historique et des seances neuves (avril - 27 octobre 2026), statistiques,
serie de pertes, pire baisse, heures, niveaux, et challenge Bulenox 50K de 1 a 3 MNQ par tirage des seances.

Lancer : KB=<copie de claude/keen-babbage-r686cl> FLUX_EXPORTS=flux/donnees python3 flux/detail_s2b.py"""
from pathlib import Path

import numpy as np
import pandas as pd

import donnees as D
import reglages as R
import systeme as Y

ICI = Path(__file__).resolve().parent
TICK = 0.25
NOMS = ("plus haut de la veille", "plus bas de la veille", "plus haut de la 1re heure", "plus bas de la 1re heure")


def signaux_s2b(m, X, d, sans_flux=True):
    """S2 sans condition d'agression (S2b), avec le niveau de chaque signal ; signaux jusqu'a 12 h."""
    h, l, c = m["h"][d], m["l"][d], m["c"][d]
    if d == 0:
        return []
    niveaux = [(m["h"][d - 1].max(), 1, 30, 0), (m["l"][d - 1].min(), -1, 30, 1), (h[:60].max(), 1, 60, 2),
               (l[:60].min(), -1, 60, 3)]
    out = []
    for L, haut, debut, k in niveaux:
        for b in range(debut, Y.FIN + 1):
            casse = (h[b] >= L + TICK and c[b - 1] <= L) if haut == 1 else (l[b] <= L - TICK and c[b - 1] >= L)
            if not casse:
                continue
            for f in range(b, min(b + 5, Y.FIN) + 1):
                if (c[f] <= L - TICK) if haut == 1 else (c[f] >= L + TICK):
                    stop = h[b:f + 1].max() + TICK if haut == 1 else l[b:f + 1].min() - TICK
                    out.append((f, -haut, stop, k))
                    break
            break
    out = sorted(out)
    signaux_s2b.niveaux[d] = {(t, s, st): k for t, s, st, k in out}
    return [(t, s, st) for t, s, st, k in out if t <= 150]


signaux_s2b.niveaux = {}


def challenge(jours_pts, taille, n, solde, haut, tirages=20000, graine=4, limite=1000.0):
    rng = np.random.default_rng(graine)
    res = np.zeros(tirages, int)
    for k in range(tirages):
        bal, hh = solde, haut
        for s in rng.integers(0, len(jours_pts), n):
            jour = 0.0
            for g in jours_pts[s]:
                jour += g * 2 * taille
                if bal + jour <= (50100.0 if hh >= 52600 else hh - 2500):
                    res[k] = -1
                    break
                if bal + jour >= 53050:
                    res[k] = 1
                    break
                if jour <= -limite:
                    break
            if res[k]:
                break
            bal += jour
            hh = max(hh, bal)
            if bal <= (50100.0 if hh >= 52600 else hh - 2500):
                res[k] = -1
                break
    return (res == 1).mean(), (res == -1).mean(), (res == 0).mean()


def main():
    m, info, _ = D.seances()
    X = Y.mesures(m, info)
    Y.DUREE = 60
    tr = Y.jouer(m, info, X, signaux_s2b)
    # controle : memes trades que la configuration 82358 de la partie 2
    ref = R.trades_config(R.tableaux(m, info), R.table_configs().iloc[82358])
    assert len(ref) == len(tr) and np.allclose(ref["net"].to_numpy(), tr["net"].to_numpy())
    # niveau du signal (si deux niveaux echouent a la meme minute dans le meme sens, le premier dans l'ordre du tri)
    tr["niveau"] = [NOMS[min((st, k) for (t, s, st), k in signaux_s2b.niveaux[r.seance].items()
                             if t == r.signal and s == r.sens)[1]] for r in tr.itertuples()]
    tr["jour"] = pd.to_datetime(tr["jour"])
    # 19 octobre : veille (17 octobre) absente de toutes les sources, S2b ne trade pas (regle du point d'etape)
    sans_veille = pd.Timestamp("2026-10-19")
    du19 = tr[tr["jour"] == sans_veille]
    tr = tr[tr["jour"] != sans_veille].reset_index(drop=True)
    jou = np.array([d for d in np.flatnonzero(X["jouable"]) if info["jour"][d] != sans_veille])
    neuves = tr["jour"] >= pd.Timestamp("2026-10-19")
    L = ["S2b : cassure ratee du plus haut ou du plus bas de la veille ou de la premiere heure, sans condition de flux ; "
         "entree contre la cassure a l'ouverture de la minute suivante ; stop au-dela de l'extreme de la cassure (3 points "
         "au moins) ; objectif 2 R ; 60 minutes au plus ; signaux de 10 h a 12 h (New York).",
         f"Periode : {info['jour'][jou[0]].date()} - {info['jour'].iloc[-1].date()} ({len(jou)} seances jouables, dont 6 neuves ; "
         "le 19 octobre est exclu, sa veille manque). "
         "Points de NQ, frais compris ; 1 point = 2 $ par MNQ.", ""]
    g, p = tr[tr["net"] > 0], tr[tr["net"] <= 0]
    L += [f"Trades : {len(tr)} ({len(tr) / len(jou):.2f} par seance, {(tr.groupby('seance').size() > 0).sum()} seances avec au moins un trade)",
          f"Gagnants : {len(g)} ({len(g) / len(tr):.0%}), gain moyen {g['net'].mean():+.1f} pt ; perdants : {len(p)}, perte moyenne "
          f"{p['net'].mean():+.1f} pt ; net moyen {tr['net'].mean():+.2f} pt",
          f"Plus gros gain {tr['net'].max():+.1f} pt, plus grosse perte {tr['net'].min():+.1f} pt",
          f"Risque R (distance au stop) : median {tr['R'].median():.1f} pt, 90 % des trades sous {tr['R'].quantile(.9):.1f} pt, "
          f"maximum {tr['R'].max():.1f} pt",
          "Sorties : " + ", ".join(f"{k} {v:.0%}" for k, v in tr["motif"].value_counts(normalize=True).items()),
          "Sens : " + ", ".join(f"{'achats' if k > 0 else 'ventes'} {v} ({tr[tr['sens'] == k]['net'].mean():+.1f} pt en moyenne)"
                                for k, v in tr["sens"].value_counts().items()),
          "Niveaux : " + " ; ".join(f"{k} {len(v)} trades, {v['net'].mean():+.1f} pt" for k, v in tr.groupby("niveau")), ""]
    tr["heure"] = (9 * 60 + 30 + tr["signal"]) // 30 * 30
    L.append("Heure du signal (New York) : " + " ; ".join(f"{h // 60}h{h % 60:02d} {len(v)} trades {v['net'].mean():+.1f} pt"
                                                          for h, v in tr.groupby("heure")))
    tr["mois"] = tr["jour"].dt.strftime("%Y-%m")
    L.append("Mois : " + " | ".join(f"{k} {v['net'].sum():+.0f} pt ({len(v)})" for k, v in tr.groupby("mois")))
    # series et baisse, trade par trade
    serie = pire = 0
    for x in tr["net"]:
        serie = serie + 1 if x <= 0 else 0
        pire = max(pire, serie)
    cum = tr["net"].cumsum()
    baisse = (cum - cum.cummax()).min()
    jours = Y.quotidien(tr, jou)
    L += [f"Plus longue serie de pertes : {pire} trades de suite ; pire baisse (trade par trade) : {baisse:.1f} pt",
          f"Pire journee : {jours.min():+.1f} pt ; meilleure : {jours.max():+.1f} pt ; journees perdantes {int((jours < 0).sum())}, "
          f"gagnantes {int((jours > 0).sum())}, sans trade {int((jours == 0).sum())}", ""]
    t_hist = Y.t_stat(tr[~neuves]["net"])
    L += [f"t par trade : historique (avril - 16 octobre, {int((~neuves).sum())} trades) {t_hist:+.2f}, choisi parmi 89 100 "
          f"configurations sur ces memes seances (donc gonfle) ; seances neuves ({int(neuves.sum())} trades) "
          f"{Y.t_stat(tr[neuves]['net']):+.2f}",
          f"Fragilite : avec le trade du 19 octobre (veille inconnue, exclu par la regle : {du19['net'].sum():+.1f} pt), les seances "
          f"neuves donneraient t {Y.t_stat(pd.concat([du19['net'], tr[neuves]['net']])):+.2f} au lieu de {Y.t_stat(tr[neuves]['net']):+.2f}", ""]
    L.append("En dollars (net, frais compris) : par trade et par seance, selon la taille")
    for taille in (1, 2, 3, 4):
        k = 2 * taille
        L.append(f"  {taille} MNQ : risque median par trade {tr['R'].median() * k:.0f} $ (90 % sous {tr['R'].quantile(.9) * k:.0f} $), "
                 f"net moyen {tr['net'].mean() * k:+.0f} $ par trade, {jours.mean() * k:+.0f} $ par seance ; pire journee "
                 f"{jours.min() * k:+.0f} $, pire baisse {baisse * k:+.0f} $ ; 6 seances neuves {tr[neuves]['net'].sum() * k:+.0f} $")
    L += ["", "Challenge Bulenox 50K (objectif 53 000 $, perte max 2 500 $ suivie en fin de journee, limite du jour 1 000 $), "
              "par tirage des seances jouables avec remise ; valide / perdu / pas fini :"]
    gj = [list(tr[tr["seance"] == s]["net"]) for s in jou]
    moitie = tr["net"].mean() / 2
    gj2 = [[x - moitie for x in v] for v in gj]
    for nom, depart, haut in (("49 900 $, plancher 48 672 $", 49900.0, 51172.0), ("compte neuf 50 000 $", 50000.0, 50000.0)):
        for n in (10, 60):
            for lib, src in (("avantage mesure", gj), ("avantage divise par 2", gj2)):
                parts = [f"{t} MNQ {v:.0%}/{pe:.0%}/{e:.0%}" for t in (1, 2, 3)
                         for v, pe, e in [challenge(src, t, n, depart, haut, tirages=6000)]]
                L.append(f"  {nom:<28} {n:3d} seances, {lib:<22} : " + " | ".join(parts))
    texte = "\n".join(L)
    (ICI / "resultats" / "detail_s2b.txt").write_text(texte + "\n")
    tr.drop(columns=["heure", "mois"]).to_csv(ICI / "resultats" / "trades_S2b.csv", index=False)
    print(texte)


if __name__ == "__main__":
    main()
