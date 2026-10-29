#!/usr/bin/env python3
"""S2b sur les barres d'une minute gratuites du NQ, 2011 - mars 2026 (flux/README.md, « S2b sur 15 ans »).

Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/s2b_15ans.py"""
from pathlib import Path

import numpy as np
import pandas as pd

import quant as Q
import systeme as Y

ICI = Path(__file__).resolve().parent
TICK, REF = 0.25, 30000.0
DEBUT, FIN = pd.Timestamp("2011-01-03"), pd.Timestamp("2026-03-31")


def signaux(h, l, c, pdh, pdl):
    niveaux = [(pdh, 1, 30), (pdl, -1, 30), (h[:60].max(), 1, 60), (l[:60].min(), -1, 60)]
    out = []
    for L, haut, debut in niveaux:
        for b in range(debut, 331):
            casse = (h[b] >= L + TICK and c[b - 1] <= L) if haut == 1 else (l[b] <= L - TICK and c[b - 1] >= L)
            if not casse:
                continue
            for f in range(b, min(b + 5, 330) + 1):
                if (c[f] <= L - TICK) if haut == 1 else (c[f] >= L + TICK):
                    ext = h[b:f + 1].max() if haut == 1 else l[b:f + 1].min()
                    out.append((f, -haut, ext + TICK if haut == 1 else ext - TICK))
                    break
            break
    return [s for s in sorted(out) if s[0] <= 150]


def main():
    arr, jours, change = Q.barres_15_ans()
    o, h, l, c = arr["o"], arr["h"], arr["l"], arr["c"]
    m = {"o": o, "h": h, "l": l, "c": c}
    Y.DUREE = 60
    lignes, seances = [], []
    for d in range(1, len(jours)):
        if not (DEBUT <= jours[d] <= FIN) or change[d]:
            continue
        seances.append(d)
        o0 = o[d, 0]
        rmin = max(TICK, round(3.0 * o0 / REF / TICK) * TICK)
        libre = 0
        for t, sens, stop_s in signaux(h[d], l[d], c[d], h[d - 1].max(), l[d - 1].min()):
            if t < libre:
                continue
            e = t + 1
            ent = o[d, e] + sens * TICK
            st = np.floor(min(stop_s, ent - rmin) / TICK) * TICK if sens > 0 else np.ceil(max(stop_s, ent + rmin) / TICK) * TICK
            R = abs(ent - st)
            if R > Y.R_MAX * ent:
                continue
            ob = ent + sens * 2 * R
            ob = np.ceil(ob / TICK) * TICK if sens > 0 else np.floor(ob / TICK) * TICK
            x, sortie, motif = Y.suivre(m, d, e, sens, ent, st, ob)
            lignes.append(dict(seance=d, jour=jours[d], sens=sens, motif=motif,
                               net=sens * (sortie - ent) * REF / o0 - 2 * Y.COM))
            libre = x
    tr = pd.DataFrame(lignes)
    seances = np.array(seances)
    q = Y.quotidien(tr, seances)
    an = pd.Series(jours[seances].year, index=seances)
    L = [f"S2b sur les barres gratuites, {jours[seances[0]].date()} - {jours[seances[-1]].date()} : {len(seances)} seances, "
         f"{len(tr)} trades ({len(tr) / len(seances):.2f} par seance). Points au prix d'aujourd'hui (NQ a 30 000), frais compris ; "
         "1 point = 2 $ par MNQ.", ""]
    for lib, msk in (("2011 - 2022", an < 2023), ("2023 - mars 2026", an >= 2023), ("tout", an > 0)):
        s = seances[msk.to_numpy()]
        x = tr[tr["seance"].isin(s)]
        L.append(f"{lib:<17} : {len(x):5d} trades, gagnants {(x['net'] > 0).mean():.0%}, net moyen {x['net'].mean():+.2f} pt, "
                 f"total {x['net'].sum():+8.0f} pt ({2 * x['net'].sum():+,.0f} $ par MNQ), t par seance {Y.t_stat(Y.quotidien(x, s)):+.2f}")
    ok = Y.t_stat(q) >= 2 and tr["net"].mean() > 0
    L += ["", f"Decision fixee a l'avance : S2b {'CONFIRMEE' if ok else 'NON confirmee'} sur 15 ans (t {Y.t_stat(q):+.2f}, seuil 2)", "",
          "Annee par annee (points, trades, $ par MNQ) :"]
    tr["an"] = tr["jour"].dt.year
    for a, x in tr.groupby("an"):
        L.append(f"  {a} : {x['net'].sum():+7.0f} pt ({len(x)} trades, {(x['net'] > 0).mean():.0%} gagnants) = {2 * x['net'].sum():+,.0f} $")
    cum = np.cumsum(q)
    L.append(f"\nPire baisse (fin de journee) : {(cum - np.maximum.accumulate(cum)).min():.0f} pt ; annees positives : "
             f"{(tr.groupby('an')['net'].sum() > 0).sum()} sur {tr['an'].nunique()}")
    texte = "\n".join(L)
    (ICI / "resultats" / "s2b_15ans.txt").write_text(texte + "\n")
    print(texte)


def quotidien():
    """Gain de chaque seance en $ par MNQ (2011 - 28 octobre 2026), pour flux/matrice.py."""
    import reglages as R
    arr, jours, change = Q.barres_15_ans()
    o, h, l, c = arr["o"], arr["h"], arr["l"], arr["c"]
    m = {"o": o, "h": h, "l": l, "c": c}
    Y.DUREE = 60
    out = {}
    for d in range(1, len(jours)):
        if change[d]:
            continue
        o0 = o[d, 0]
        rmin = max(TICK, round(3.0 * o0 / REF / TICK) * TICK)
        libre, g, n = 0, 0.0, 0
        for t, sens, stop_s in signaux(h[d], l[d], c[d], h[d - 1].max(), l[d - 1].min()):
            if t < libre:
                continue
            e = t + 1
            ent = o[d, e] + sens * TICK
            st = np.floor(min(stop_s, ent - rmin) / TICK) * TICK if sens > 0 else np.ceil(max(stop_s, ent + rmin) / TICK) * TICK
            R_ = abs(ent - st)
            if R_ > Y.R_MAX * ent:
                continue
            ob = ent + sens * 2 * R_
            ob = np.ceil(ob / TICK) * TICK if sens > 0 else np.floor(ob / TICK) * TICK
            x, sortie, motif = Y.suivre(m, d, e, sens, ent, st, ob)
            g += 2 * (sens * (sortie - ent) * REF / o0 - 2 * Y.COM)
            n += 1
            libre = x
        out[jours[d]] = g if n else np.nan
    R.CALCUL.mkdir(parents=True, exist_ok=True)
    pd.Series(out, name="S2b").to_frame().to_pickle(R.CALCUL / "s2b_quotidien.pkl")


if __name__ == "__main__":
    import sys
    quotidien() if "--quotidien" in sys.argv else main()
