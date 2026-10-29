#!/usr/bin/env python3
"""Recit, trade par trade, de ce que S2b aurait fait du 20 au 29 octobre 2026 sur l'export Rithmic de l'utilisateur
(descriptif). Memes regles et meme execution que le bot (flux/systeme.py, S2b = configuration 82358) ; minutes
manquantes recopiees a plat. Le 19 octobre est inconnu (le 17, sa veille, manque) ; le 28 a un trou de 14 h 44 a 15 h 44
(apres la fenetre de S2b) ; le 29 s'arrete a 11 h 43 (heure de l'export).

Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/semaine_s2b.py"""
from pathlib import Path

import numpy as np
import pandas as pd

import donnees as D
import systeme as Y

ICI = Path(__file__).resolve().parent
TICK = 0.25
NOMS = ("plus haut de la veille", "plus bas de la veille", "plus haut de la 1re heure", "plus bas de la 1re heure")


def jours_export():
    fichiers = [D.RITHMIC, ICI / "donnees" / "transactions_NQZ6_19-29oct.csv"]
    t = pd.concat([pd.read_csv(f) for f in fichiers], ignore_index=True).drop_duplicates(["jour", "minute"], keep="last")
    out = {}
    for j, g in t.groupby("jour"):
        g = g.set_index("minute").sort_index()
        n = int(g.index.max()) + 1
        a = {k: np.full(n, np.nan) for k in "ohlc"}
        for k in "ohlc":
            a[k][g.index.to_numpy()] = g[k].to_numpy()
        for i in range(n):                                   # minute manquante : a plat sur la cloture d'avant
            if np.isnan(a["c"][i]):
                p = a["c"][i - 1]
                for k in "ohlc":
                    a[k][i] = p
        out[pd.Timestamp(j)] = (a, 390 - len(g) - (390 - n))
    return out


def hm(t, decalage=0):
    m = 570 + t + decalage * 60
    return f"{m // 60}h{m % 60:02d}"


def main():
    J = jours_export()
    jours = sorted(J)
    L = ["S2b, semaine du 20 au 29 octobre 2026 (export Rithmic du compte), trade par trade. Heures de New York, avec Paris "
         "entre parenthèses. Points de NQ nets de frais (1,5 point par aller-retour) ; 1 point = 2 $ par MNQ.", ""]
    total, details = 0.0, []
    for k, j in enumerate(jours):
        if j < pd.Timestamp("2026-10-19"):
            continue
        if j == pd.Timestamp("2026-10-19"):
            L += ["19/10 : inconnu. La veille (vendredi 17) manque dans l'export : sans son plus haut et son plus bas, on ne peut "
                  "pas savoir ce que le bot aurait fait.", ""]
            continue
        (a, manque), (v, _) = J[j], J[jours[k - 1]]
        n = len(a["c"])
        paris = 6 if j <= pd.Timestamp("2026-10-23") else 5
        h, l, c, o = a["h"], a["l"], a["c"], a["o"]
        pdh, pdl = v["h"].max(), v["l"].min()
        ibh, ibl = (h[:60].max(), l[:60].min()) if n >= 60 else (np.nan, np.nan)
        niveaux = [(pdh, 1, 30, 0), (pdl, -1, 30, 1), (ibh, 1, 60, 2), (ibl, -1, 60, 3)]
        entete = (f"{j:%a %d/%m} : veille haut {pdh:.2f} / bas {pdl:.2f} ; 1re heure haut {ibh:.2f} / bas {ibl:.2f}"
                  + (f" ; {manque} minute(s) manquante(s)" if manque else "") + (f" ; donnees jusqu'a {hm(n - 1)}" if n < 390 else ""))
        sig = []
        for L_, haut, debut, i in niveaux:
            if np.isnan(L_):
                continue
            for b in range(debut, min(Y.FIN, n - 1) + 1):
                casse = (h[b] >= L_ + TICK and c[b - 1] <= L_) if haut == 1 else (l[b] <= L_ - TICK and c[b - 1] >= L_)
                if not casse:
                    continue
                for f in range(b, min(b + 5, Y.FIN, n - 1) + 1):
                    if (c[f] <= L_ - TICK) if haut == 1 else (c[f] >= L_ + TICK):
                        ext = h[b:f + 1].max() if haut == 1 else l[b:f + 1].min()
                        sig.append((f, -haut, ext + TICK if haut == 1 else ext - TICK, i, b, L_, ext))
                        break
                break
        sig.sort(key=lambda x: (x[0], x[1], x[2]))
        lignes, libre = [], 0
        for f, sens, stop_s, i, b, L_, ext in sig:
            if f > 150 or f < libre or f + 1 >= n:
                continue
            e = f + 1
            nv = Y.niveaux_trade(o[e], sens, stop_s)
            if nv is None:
                lignes.append(f"   {hm(f)} : signal ecarte (risque au-dela de 0,12 % du prix)")
                continue
            ent, st, obj, R = nv
            fin = min(e + 59, n - 1)
            x, sortie, motif = None, None, None
            for t in range(e, fin + 1):
                if sens > 0:
                    if t > e and o[t] <= st:
                        x, sortie, motif = t, o[t] - TICK, "stop"
                    elif l[t] <= st:
                        x, sortie, motif = t, st - TICK, "stop"
                    elif h[t] >= obj + TICK:
                        x, sortie, motif = t, obj, "objectif"
                else:
                    if t > e and o[t] >= st:
                        x, sortie, motif = t, o[t] + TICK, "stop"
                    elif h[t] >= st:
                        x, sortie, motif = t, st + TICK, "stop"
                    elif l[t] <= obj - TICK:
                        x, sortie, motif = t, obj, "objectif"
                if x is not None:
                    break
            en_cours = x is None and fin < e + 59
            if x is None:
                x, sortie, motif = fin, c[fin] - sens * TICK, "temps" if not en_cours else "en cours a la fin des donnees"
            net = sens * (sortie - ent) - 1.0
            if not en_cours:
                total += net
            libre = x
            sens_txt = "VENTE" if sens < 0 else "ACHAT"
            pourquoi = (f"le prix a casse le {NOMS[i]} ({L_:.2f}) a {hm(b)} ({hm(b, paris)}), jusqu'a {ext:.2f}, puis une minute a "
                        f"cloture de nouveau {'en dessous' if sens < 0 else 'au-dessus'} a {hm(f)} : les "
                        f"{'acheteurs' if sens < 0 else 'vendeurs'} de la cassure sont pieges")
            lignes.append(f"   {sens_txt} a {hm(e)} ({hm(e, paris)} a Paris) a {ent:.2f} ; stop {st:.2f} ({R:.2f} pts), objectif {obj:.2f}\n"
                          f"      pourquoi : {pourquoi}\n"
                          f"      sortie : {motif} a {hm(x)} ({hm(x, paris)}) a {sortie:.2f} -> {net:+.2f} pts ({2 * net:+.0f} $ par MNQ)"
                          + (" [non compte]" if en_cours else ""))
            details.append((j, f, sens, motif, net, en_cours))
        L.append(entete)
        L += lignes if lignes else ["   aucun trade : aucun de ces niveaux n'a ete casse puis repris dans les 5 minutes entre 10 h et 12 h"]
        L.append("")
    fini = [d for d in details if not d[5]]
    L.append(f"Total des trades termines : {len(fini)} trade(s), {sum(d[4] for d in fini):+.2f} pts = {2 * sum(d[4] for d in fini):+.0f} $ par MNQ ; "
             f"{sum(1 for d in fini if d[3] == 'stop')} stop(s), {sum(1 for d in fini if d[3] == 'objectif')} objectif(s)")
    texte = "\n".join(L)
    (ICI / "resultats" / "semaine_s2b.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    main()
