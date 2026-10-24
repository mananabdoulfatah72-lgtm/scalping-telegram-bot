#!/usr/bin/env python3
"""Selection des finalistes (README.md) puis ouverture unique du coffre 2023 - fin des donnees.
  python3 scalping/coffre.py exploration  -> resultats/exploration.txt, resultats/finalistes.json (cache de recherche seul)
  python3 scalping/coffre.py ouvrir       -> resultats/coffre.txt (une seule fois)"""
import json
import sys
from math import erf, sqrt
from statistics import NormalDist

import numpy as np

import commun as K
import machine as MA
import moteur as M

NOMS_F = {0: "choc d'une minute", 1: "mouvement de k minutes", 2: "serie de barres", 3: "micro-compression puis cassure",
          4: "ecart au VWAP", 5: "niveau franchi ou rejete", 6: "pic de volume", 7: "avance de l'autre indice",
          8: "bougie", 9: "minute d'evenement"}
NIV = ["plus haut veille", "plus bas veille", "cloture veille", "haut 5 premieres min", "bas 5 premieres min",
       "haut 15 premieres min", "bas 15 premieres min", "haut 30 premieres min", "bas 30 premieres min",
       "plus haut du jour", "plus bas du jour", "niveau rond"]


def decrire(g):
    g = np.asarray(g)
    fam = int(g[M.FAM])
    if fam >= 10:
        import partie_a
        return partie_a.REGLES[fam]
    p = ""
    if fam == 0:
        p = f"|r1| >= {g[M.PZ]:.2f} sigma"
    elif fam == 1:
        p = f"k = {M.K_F1[int(g[M.PK])]}, z >= {g[M.PZ]:.2f}"
    elif fam == 2:
        p = f"n = {int(g[M.PK])}, z >= {g[M.PZ]:.2f}"
    elif fam == 3:
        p = f"k = {M.K_F3[int(g[M.PK])]}, Q = {g[M.PY]:.2f}"
    elif fam == 4:
        p = f"z >= {g[M.PZ]:.2f}"
    elif fam == 5:
        p = f"{NIV[int(g[M.PX])]}, {'franchi' if int(g[M.PW]) == 0 else 'rejete'}, marge {g[M.PZ]:.2f}"
    elif fam == 6:
        p = f"volume >= {g[M.PY]:.2f} x mediane"
    elif fam == 7:
        p = f"k = {M.K_F7[int(g[M.PK])]}, z >= {g[M.PZ]:.2f}, retard >= {g[M.PY]:.2f}"
    elif fam == 8:
        p = (f"{'meche' if int(g[M.PX]) == 0 else 'avalement'} sur {M.TAILLE_F8[int(g[M.PW])]} min, W {g[M.PY]:.2f}, "
             f"apres k = {M.K_F8[int(g[M.PK])]}, z >= {g[M.PZ]:.2f}")
    elif fam == 9:
        p = f"minute {M.EVENEMENTS[int(g[M.PX])]}, k = {M.K_F9[int(g[M.PK])]}, z >= {g[M.PZ]:.2f}"
    fin = M.FINS[int(g[M.FIN])]
    ent = M.LIMITES[int(g[M.ENTREE])]
    return (f"{NOMS_F[fam]} ({p}) ; {'contre' if g[M.INV] > 0.5 else 'suivre'} ; "
            f"{['achats et ventes', 'achats seuls', 'ventes seules'][int(g[M.COTES])]} ; entrees de la minute "
            f"{M.DEBUTS[int(g[M.DEBUT])]} a {'5 avant la fin' if fin < 0 else fin} ; "
            f"regime {['tous', 'agite', 'calme'][int(g[M.REGIME])]} ; tendance {['toute', 'avec', 'contre'][int(g[M.TEND])]} ; "
            f"{'au marche' if ent == 0 else f'limite {ent} u pendant {M.FENETRES[int(g[M.FENETRE])]} min'} ; "
            f"stop {g[M.STOP]:.2f} u ; objectif {'aucun' if g[M.OBJ] <= 0 else f'{g[M.OBJ]:.2f} u'} ; "
            f"duree {M.DUREES[int(g[M.DUREE])]} min ; pause {M.PAUSES[int(g[M.PAUSE])]} min")


def lire(marche, sorte):
    out = []
    for gr in range(1, MA.GRAINES + 1):
        z = np.load(MA.SORTIE / f"machine_{marche}_{sorte}_{gr}.npz")
        out.append({k: z[k] for k in z.files})
    return out


def eligibles(r):
    return (r["t_tr"] >= 2) & (r["n_tr"] >= 200) & (r["t_v"] >= 1) & (r["n_v"] >= 50)


def union_eligibles(runs):
    vus = {}
    for gr, r in enumerate(runs, start=1):
        for i in np.flatnonzero(eligibles(r)):
            k = np.round(r["genomes"][i], 4).tobytes()
            if k not in vus or r["score"][i] > vus[k]["score"]:
                vus[k] = dict(genome=r["genomes"][i].tolist(), score=float(r["score"][i]), t_tr=float(r["t_tr"][i]),
                              t_v=float(r["t_v"][i]), n_tr=int(r["n_tr"][i]), n_v=int(r["n_v"][i]),
                              net_trade=float(r["net_trade"][i]), gagnants=float(r["gagnants"][i]), graine=gr)
    return sorted(vus.values(), key=lambda x: -x["score"])


def deux_meilleures(liste):
    out = []
    for x in liste:
        if all(int(x["genome"][M.FAM]) != int(y["genome"][M.FAM]) for y in out):
            out.append(x)
        if len(out) == 2:
            break
    return out


def exploration():
    L = ["Machine scalping, exploration 2017-2022 (README.md). Score = t des gains nets quotidiens 2017-2022 au prix "
         "d'aujourd'hui. Eligible : t entrainement >= 2 avec 200 trades, t validation >= 1 avec 50 trades.", ""]
    finalistes, placebos = [], []
    total_reel = total_bruit = 0
    L.append("marche  distinctes reel / bruit   eligibles reel / bruit (moyenne par graine)   barriere du bruit   "
             "meilleur score reel")
    seuils = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    table = []
    for marche in K.MARCHES:
        reel, bruit = lire(marche, "reel"), lire(marche, "bruit")
        nr = sum(len(r["genomes"]) for r in reel)
        nb = sum(len(r["genomes"]) for r in bruit)
        total_reel += nr
        total_bruit += nb
        er = [r["score"][eligibles(r)] for r in reel]
        eb = [r["score"][eligibles(r)] for r in bruit]
        barriere = max([x.max() for x in eb if len(x)], default=-np.inf)
        ur = union_eligibles(reel)
        ub = union_eligibles(bruit)
        meilleur = ur[0]["score"] if ur else float("nan")
        L.append(f"{marche:<6}  {nr:9d} / {nb:9d}   {np.mean([len(x) for x in er]):10.1f} / "
                 f"{np.mean([len(x) for x in eb]):6.1f}                       {barriere:8.2f}          {meilleur:8.2f}")
        table.append((marche, [np.mean([np.sum(x >= s) for x in er]) for s in seuils],
                      [np.mean([np.sum(x >= s) for x in eb]) for s in seuils]))
        for x in deux_meilleures(ur):
            x.update(marche=marche, partie="B", barriere=float(barriere), au_dessus=bool(x["score"] > barriere),
                     description=decrire(x["genome"]))
            finalistes.append(x)
        for x in deux_meilleures(ub):
            x.update(marche=marche, partie="placebo", description=decrire(x["genome"]))
            placebos.append(x)
    L.append(f"total : {total_reel} strategies distinctes sur les vraies donnees, {total_bruit} sur bruit")
    L.append("")
    L.append("Fausses pistes : eligibles au-dessus de chaque score, moyenne par graine, vraies donnees / bruit")
    L.append("marche  " + "".join(f"   >= {s:<4}       " for s in seuils))
    for marche, a, b in table:
        L.append(f"{marche:<6}  " + "".join(f"  {x:6.1f} / {y:6.1f}" for x, y in zip(a, b)))
    pa = json.loads((MA.SORTIE / "partie_a.json").read_text())
    for x in pa:
        if x["survivante"]:
            g = np.zeros(M.NG)
            g[M.FAM] = x["regle"]
            finalistes.append(dict(genome=g.tolist(), score=x["t"], marche=x["marche"], partie="A", au_dessus=True,
                                   description=x["nom"], net_trade=x["net_trade"], gagnants=x["gagnants"],
                                   n_tr=x["trades"]))
    L.append("")
    L.append(f"Partie A : {sum(x['survivante'] for x in pa)} survivante(s) sur {len(pa)} (resultats/partie_a.txt)")
    L.append("")
    L.append(f"FINALISTES ({len(finalistes)}) :")
    for x in finalistes:
        L.append(f"  {x['marche']} [{x['partie']}] score {x['score']:.2f}"
                 + (f" (t entrainement {x['t_tr']:.2f}, validation {x['t_v']:.2f}, {x['n_tr']} + {x['n_v']} trades)"
                    if x["partie"] == "B" else "")
                 + f", net {x['net_trade']:.2f} $ par trade, gagnants {x['gagnants']:.0%}, "
                 + ("au-dessus de la barriere du bruit" if x["au_dessus"] else "SOUS la barriere du bruit"))
        L.append(f"      {x['description']}")
    L.append("")
    L.append(f"PLACEBOS ({len(placebos)}, choisis sur bruit, joues sur le vrai coffre) :")
    for x in placebos:
        L.append(f"  {x['marche']} score sur bruit {x['score']:.2f} : {x['description']}")
    txt = "\n".join(L)
    (MA.SORTIE / "exploration.txt").write_text(txt + "\n")
    (MA.SORTIE / "finalistes.json").write_text(json.dumps(dict(finalistes=finalistes, placebos=placebos), indent=1,
                                                          ensure_ascii=False))
    print(txt)


def ouvrir():
    drapeau = MA.SORTIE / "coffre_ouvert.txt"
    if drapeau.exists() and "--relire" not in sys.argv:
        sys.exit("Le coffre a deja ete ouvert (resultats/coffre_ouvert.txt). --relire pour refaire le meme calcul.")
    sel = json.loads((MA.SORTIE / "finalistes.json").read_text())
    fin, plac = sel["finalistes"], sel["placebos"]
    m = max(len(fin), 1)
    seuil = NormalDist().inv_cdf(1 - 0.05 / m)
    drapeau.write_text("coffre ouvert\n")
    cache = {}

    def jouer(marche, g):
        if marche not in cache:
            d = dict(np.load(K.CACHE / f"complet_{marche}.npz"))
            f = M.indicateurs(d)
            s0 = int(np.searchsorted(d["jours"], K.DEBUT_COFFRE))
            cache[marche] = (d, f, s0)
        d, f, s0 = cache[marche]
        gain, n, w, brut, _ = M.jouer(np.asarray(g, float), f, s0, len(d["jours"]))
        jours = d["jours"][s0:]
        ok = np.isfinite(gain)
        ans = {int(a): float(np.nansum(gain[jours.astype("datetime64[Y]").astype(int) + 1970 == a]))
               for a in (2023, 2024, 2025, 2026)}
        return dict(t=K.t_stat(gain[ok]), trades=int(n), net_trade=float(np.nansum(gain) / max(n, 1)),
                    gagnants=float(w / max(n, 1)), total=float(np.nansum(gain)), annees=ans,
                    positives=int(sum(v > 0 for v in ans.values())), fin=str(jours[ok][-1]))

    L = [f"Coffre {K.DEBUT_COFFRE} - fin des donnees, ouvert une fois. m = {len(fin)} finalistes, seuil de "
         f"Bonferroni t >= {seuil:.2f} ; palier interessant : t >= 1,65 ; et au moins 3 annees positives sur 4.", ""]
    res_f, res_p = [], []
    for x in fin:
        r = jouer(x["marche"], x["genome"])
        r["retenue"] = bool(x["au_dessus"] and r["t"] >= seuil and r["positives"] >= 3)
        r["interessante"] = bool(r["t"] >= 1.65 and r["positives"] >= 3)
        res_f.append(r)
        L.append(f"{x['marche']} [{x['partie']}] exploration {x['score']:.2f} -> coffre t {r['t']:.2f}, {r['trades']} trades,"
                 f" net {r['net_trade']:.2f} $ par trade, total {r['total']:,.0f} $ pour 1 contrat, annees "
                 + ", ".join(f"{a} {v:+,.0f}" for a, v in r["annees"].items())
                 + f" -> {'RETENUE' if r['retenue'] else ('interessante' if r['interessante'] else 'rejetee')}")
        L.append(f"      {x['description']}")
    L.append("")
    for x in plac:
        r = jouer(x["marche"], x["genome"])
        r["interessante"] = bool(r["t"] >= 1.65 and r["positives"] >= 3)
        r["bonferroni"] = bool(r["t"] >= seuil and r["positives"] >= 3)
        res_p.append(r)
        L.append(f"placebo {x['marche']} : coffre t {r['t']:.2f}, {r['trades']} trades, total {r['total']:,.0f} $, "
                 f"{r['positives']} annees positives -> {'passe le palier interessant' if r['interessante'] else 'non'}")
    L.append("")
    L.append(f"Bilan : {sum(r['retenue'] for r in res_f)} retenue(s), {sum(r['interessante'] for r in res_f)} "
             f"interessante(s) sur {len(fin)} finalistes ; placebos : {sum(r['interessante'] for r in res_p)} sur "
             f"{len(plac)} passent le palier interessant, {sum(r['bonferroni'] for r in res_p)} le seuil de Bonferroni.")
    txt = "\n".join(L)
    (MA.SORTIE / "coffre.txt").write_text(txt + "\n")
    (MA.SORTIE / "coffre.json").write_text(json.dumps(dict(finalistes=res_f, placebos=res_p), indent=1))
    print(txt)


if __name__ == "__main__":
    {"exploration": exploration, "ouvrir": ouvrir}[sys.argv[1]]()
