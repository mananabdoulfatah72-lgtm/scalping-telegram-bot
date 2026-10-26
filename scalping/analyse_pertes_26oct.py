#!/usr/bin/env python3
"""D'ou viennent les pertes de la configuration installee le 26 octobre (reglages_26oct_g.py : fenetre 5, volume x1, une entree
par seance, sortie aux controles au retour sous le niveau casse, 16 h). Descriptif, 2023 - 2026, 4 MNQ au prix d'aujourd'hui.
Compare avec la meme entree et une sortie des qu'une minute cloture sous le niveau casse. Ecrit resultats/j/analyse_pertes_26oct.txt.
Lancer : KB=<branche de recherche> MINUTES=<nq_1min de 2011 a aujourd'hui> python3 scalping/analyse_pertes_26oct.py"""
import os

import numpy as np
import pandas as pd
from numba import njit

import challenge_ajouts as CA
import donnees as D
import partie_e as E
import partie_g as G
import partie_j as J
import reglages_26oct_g as RG
import situation_bulenox as SB


@njit(cache=True)
def _sortie_immediate(C, tr, niveaux):
    """Memes entrees que tr ; sortie a la cloture de la premiere minute revenue sous le niveau casse, sinon sortie d'origine."""
    out = tr.copy()
    for i in range(len(tr)):
        s, me, e, mx = int(tr[i, 0]), int(tr[i, 1]), tr[i, 2], int(tr[i, 4])
        for m in range(me + 1, mx):
            if e * (C[s, m] - niveaux[i]) <= 0:
                out[i, 4], out[i, 5] = m, C[s, m]
                break
    return out


def main():
    d = D.minutes("NQ", chemin=os.environ["MINUTES"], debut="2011-01-01")
    S = d["c"].shape[0]
    sigma, vwap, href, bref, jouable = G.zone_tableaux(d)
    C, H, L = d["c"], d["h"], d["l"]
    fed = np.isin(d["jours"], E.fomc())
    jo = jouable & ~fed
    ech = float(d["pref"]) / d["o"][:, 0]
    t = RG._zone_fw(C, d["v"], sigma, href, bref, jouable, 1.0, 5, 30)
    s_ = t[:, 0].astype(int)
    me, mx, e = t[:, 1].astype(int), t[:, 4].astype(int), t[:, 2]
    ctl = (me // 30) * 30
    niv = np.where(e > 0, href[s_] * (1 + sigma[s_, ctl]), bref[s_] * (1 - sigma[s_, ctl]))
    usd = 8.0 * ech[s_]                                           # $ par point du NQ en 4 MNQ, au prix d'aujourd'hui
    pts = e * (t[:, 5] - t[:, 3]) - 1.5
    an = d["jours"][s_].astype("datetime64[Y]").astype(int) + 1970
    r = an >= 2023
    perd, gagn = r & (pts < 0), r & (pts > 0)
    au_dessus = e * (t[:, 3] - niv) * usd                          # entree au-dela du niveau, en $
    sous = -e * (t[:, 5] - niv) * usd                              # sortie au-dela du niveau dans le mauvais sens, en $
    retour = np.array([next((m for m in range(a + 1, b) if ee * (C[ss, m] - nv) <= 0), -1)
                       for ss, a, b, ee, nv in zip(s_, me, mx, e, niv)])
    pire = np.array([(L[ss, a + 1:b + 1].min() - p) if ee > 0 else (p - H[ss, a + 1:b + 1].max())
                     for ss, a, b, ee, p in zip(s_, me, mx, e, t[:, 3])]) * usd
    p_usd = pts * usd
    lignes = [f"2023 - 2026 : {r.sum()} trades, {gagn.sum()} gagnants ({gagn.sum() / r.sum():.0%}) a {p_usd[gagn].mean():+,.0f} $ en moyenne, "
              f"{perd.sum()} perdants a {p_usd[perd].mean():+,.0f} $ en moyenne (4 MNQ, prix d'aujourd'hui, frais compris).", "",
              "Perdants, decomposition de la perte moyenne :",
              f"  entree deja au-dela du niveau casse : {au_dessus[perd].mean():,.0f} $ en moyenne (mediane {np.median(au_dessus[perd]):,.0f} $)",
              f"  sortie au controle, au-dela du niveau dans le mauvais sens : {sous[perd].mean():,.0f} $ en moyenne (mediane {np.median(sous[perd]):,.0f} $)",
              f"  frais : {12 * 1:.0f} $",
              f"  prix revenu sous le niveau avant la sortie : {(retour[perd] >= 0).mean():.0%} des perdants ; attente jusqu'au controle : "
              f"{np.median((mx - retour)[perd & (retour >= 0)]):.0f} minutes en mediane",
              f"  pire moment pendant le trade : {np.median(pire[perd]):,.0f} $ en mediane",
              f"  pertes de plus de 400 $ : {(p_usd[perd] < -400).mean():.0%} ; de plus de 800 $ : {(p_usd[perd] < -800).mean():.0%}",
              f"  journees touchant -1 000 $ pendant le trade : {(pire[r] <= -1000).sum()} sur {r.sum()} trades", ""]
    # exemples d'octobre 2026
    lignes.append("Exemples d'octobre 2026 (heure de New York, 4 MNQ) :")
    h = lambda m: f"{(570 + int(m)) // 60}h{(570 + int(m)) % 60:02d}"
    for i in np.flatnonzero(d["jours"][s_] >= np.datetime64("2026-10-01")):
        lignes.append(f"  {d['jours'][s_[i]]} {'achat' if e[i] > 0 else 'vente'} {h(me[i])} a {t[i, 3]:.2f} (niveau casse {niv[i]:.2f}, "
                      f"{au_dessus[i]:+,.0f} $ au-dela), retour sous le niveau a {h(retour[i]) if retour[i] >= 0 else '-'}, sortie {h(mx[i])} a "
                      f"{t[i, 5]:.2f} -> {p_usd[i]:+,.0f} $ (pire {pire[i]:+,.0f} $)")
    # meme entree, sortie immediate
    ti = _sortie_immediate(C, t, niv)
    zero = np.zeros_like(C)
    dep = np.flatnonzero(d["jours"] >= np.datetime64("2012-01-01"))
    dep13 = dep[dep <= S - 13]
    lignes += ["", "Meme entree, deux sorties (4 MNQ, prix d'aujourd'hui, limite du jour 1 000 $) :"]
    for nom, tt in (("sortie au controle (installee)", t), ("sortie des la cloture sous le niveau", ti)):
        pp = (tt[:, 2] * (tt[:, 5] - tt[:, 3]) - 1.5) * usd
        Zc, Zw = CA.chemins(d, [(int(x[0]), int(x[1]), float(x[2]), x[3], int(x[4]), x[5], 4) for x in tt])
        x = pd.Series(np.where(jo, np.where((4 * Zw <= -1000).any(axis=1), -1000.0, 4 * Zc[:, -1]), 0.0), index=pd.to_datetime(d["jours"]))
        ch = SB._depuis(Zc, Zw, zero, zero, fed, dep13, 13, 4.0, 6.0, 0.0, 49500.0, 51000.0, 1000.0)
        lignes.append(f"  {nom:<38} gagnants {(pp[r] > 0).mean():.0%}, gain moyen {pp[r & (pp > 0)].mean():+,.0f} $, perte moyenne "
                      f"{pp[r & (pp < 0)].mean():+,.0f} $, 2023-2026 {x[x.index >= '2023-01-01'].sum():+,.0f} $, 2026 "
                      f"{x[x.index.year == 2026].sum():+,.0f} $, valide {(ch == 1).mean():.1%} / perdu {(ch == -1).mean():.1%}")
    (J.SORTIE / "analyse_pertes_26oct.txt").write_text("\n".join(lignes) + "\n")
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
