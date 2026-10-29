#!/usr/bin/env python3
"""Selection des finalistes (README.md) puis ouverture unique du coffre 2023 - fin des donnees.
  python3 scalping/coffre.py exploration  -> resultats/exploration.txt, resultats/finalistes.json (resultats de
                                             l'exploration seulement)
  python3 scalping/coffre.py ouvrir       -> resultats/coffre.txt (une seule fois, toutes les parties ensemble)"""
import hashlib
import json
import sys
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


def decrire(g, piste="B"):
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
        p = f"k = {M.K_F3[int(g[M.PK])]}{' barres' if piste == 'D' else ''}, Q = {g[M.PY]:.2f}"
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
        if piste == "D":
            import nuit as NU
            b = int(NU.EVENEMENTS_NUIT[int(g[M.PX])])
            p = f"barre {b} ({(18 * 60 + 5 * b) // 60 % 24} h {(5 * b) % 60:02d}), k = {M.K_F9[int(g[M.PK])]} barres, z >= {g[M.PZ]:.2f}"
        else:
            p = f"minute {M.EVENEMENTS[int(g[M.PX])]}, k = {M.K_F9[int(g[M.PK])]}, z >= {g[M.PZ]:.2f}"
    fin = M.FINS[int(g[M.FIN])]
    ent = M.LIMITES[int(g[M.ENTREE])]
    if piste == "D":                     # la nuit compte en barres de 5 minutes depuis 18 h
        u_ = "barres"
        hm = lambda b: f"{(18 * 60 + 5 * b) // 60 % 24} h {(5 * b) % 60:02d}"     # noqa: E731
        fen = (f"entrees de la barre {M.DEBUTS[int(g[M.DEBUT])]} ({hm(M.DEBUTS[int(g[M.DEBUT])])}) a "
               + ("5 barres avant la fin" if fin < 0 else f"{fin} ({hm(fin)})"))
    else:
        u_ = "min"
        fen = f"entrees de la minute {M.DEBUTS[int(g[M.DEBUT])]} a {'5 avant la fin' if fin < 0 else fin}"
    return (f"{NOMS_F[fam]} ({p}) ; {'contre' if g[M.INV] > 0.5 else 'suivre'} ; "
            f"{['achats et ventes', 'achats seuls', 'ventes seules'][int(g[M.COTES])]} ; {fen} ; "
            f"regime {['tous', 'agite', 'calme'][int(g[M.REGIME])]} ; tendance {['toute', 'avec', 'contre'][int(g[M.TEND])]} ; "
            f"{'au marche' if ent == 0 else f'limite {ent} u pendant {M.FENETRES[int(g[M.FENETRE])]} {u_}'} ; "
            f"stop {g[M.STOP]:.2f} u ; objectif {'aucun' if g[M.OBJ] <= 0 else f'{g[M.OBJ]:.2f} u'} ; "
            f"duree {M.DUREES[int(g[M.DUREE])]} {u_} ; pause {M.PAUSES[int(g[M.PAUSE])]} {u_}")


def lire(piste, marche, sorte):
    out = []
    for gr in range(1, MA.GRAINES + 1):
        f = MA.SORTIE / f"machine_{piste}_{marche}_{sorte}_{gr}.npz"
        if f.exists():
            z = np.load(f)
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


def empreinte(chemin):
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def completude():
    """Ce qui manque pour ouvrir le coffre, recompte sur les fichiers (et non lu dans finalistes.json)."""
    manque = []
    for piste in ("B", "B2", "D"):
        for marche in MA.marches(piste):
            for so in MA.SORTES:
                n = sum((MA.SORTIE / f"machine_{piste}_{marche}_{so}_{gr}.npz").exists()
                        for gr in range(1, MA.GRAINES + 1))
                if n < MA.GRAINES:
                    manque.append(f"{piste} {marche} {so} : {n} graine(s) sur {MA.GRAINES}")
    for nom, fich in (("A", "partie_a.json"), ("C", "appris.json")):
        if not (MA.SORTIE / fich).exists():
            manque.append(f"partie {nom}")
    return manque


def exploration():
    if (MA.SORTIE / "coffre_ouvert.txt").exists():
        sys.exit("Le coffre est deja ouvert : la selection des finalistes ne peut plus changer.")
    manque = []
    L = ["Machine scalping, exploration jusqu'au 31 decembre 2022 (README.md). Score = t des gains nets quotidiens sur "
         "entrainement + validation, au prix d'aujourd'hui. Eligible : t entrainement >= 2 avec 200 trades, t validation "
         ">= 1 avec 50 trades. Barriere = meilleur score eligible trouve sur les deux bruits (permutation et signe).", ""]
    finalistes, placebos = [], []
    seuils = [2.0, 2.5, 3.0, 3.5, 4.0, 4.5]
    for piste in ("B", "B2", "D"):
        lignes, table = [], []
        tot = {"reel": 0, "bruit": 0, "signe": 0}
        for marche in MA.marches(piste):
            runs = {so: lire(piste, marche, so) for so in MA.SORTES}
            for so in MA.SORTES:
                if len(runs[so]) < MA.GRAINES:
                    manque.append(f"{piste} {marche} {so} : {len(runs[so])} graine(s) sur {MA.GRAINES}")
            if not all(runs.values()):
                continue
            for so in MA.SORTES:
                tot[so] += sum(len(r["genomes"]) for r in runs[so])
            sc = {so: [r["score"][eligibles(r)] for r in runs[so]] for so in MA.SORTES}
            barriere = max([x.max() for so in ("bruit", "signe") for x in sc[so] if len(x)], default=-np.inf)
            ur = union_eligibles(runs["reel"])
            lignes.append(f"{marche:<5} eligibles par graine : reel {np.mean([len(x) for x in sc['reel']]):7.1f}, "
                          f"permutation {np.mean([len(x) for x in sc['bruit']]):7.1f}, signe "
                          f"{np.mean([len(x) for x in sc['signe']]):7.1f} ; barriere {barriere:5.2f} ; meilleur reel "
                          f"{(ur[0]['score'] if ur else float('nan')):5.2f}")
            table.append((marche, {so: [np.mean([np.sum(x >= v) for x in sc[so]]) for v in seuils] for so in MA.SORTES}))
            for x in deux_meilleures(ur):
                x.update(piste=piste, marche=marche, partie=piste, barriere=float(barriere),
                         au_dessus=bool(x["score"] > barriere), description=decrire(x["genome"], piste))
                finalistes.append(x)
            for so in ("bruit", "signe"):
                for x in deux_meilleures(union_eligibles(runs[so])):
                    x.update(piste=piste, marche=marche, partie=f"placebo {so}",
                             description=decrire(x["genome"], piste))
                    placebos.append(x)
        if not lignes:
            continue
        L.append(f"=== Partie {piste} : {tot['reel']} strategies distinctes sur les vraies donnees, {tot['bruit']} sur le "
                 f"bruit par permutation, {tot['signe']} sur le bruit par signe")
        L += lignes
        L.append("  eligibles au-dessus de chaque score, moyenne par graine : reel / permutation / signe")
        L.append("        " + "".join(f"   >= {v:<4}             " for v in seuils))
        for marche, d in table:
            L.append(f"  {marche:<5} " + "".join(f"  {a:5.1f}/{b:5.1f}/{c:5.1f}  " for a, b, c in
                                                zip(d["reel"], d["bruit"], d["signe"])))
        L.append("")
    for nom, fich, partie in (("A", "partie_a.json", "A"), ("C", "appris.json", "C")):
        f = MA.SORTIE / fich
        if not f.exists():
            L.append(f"Partie {nom} : pas encore calculee")
            manque.append(f"partie {nom}")
            continue
        res = json.loads(f.read_text())
        L.append(f"Partie {nom} : {sum(x['survivante'] for x in res)} survivante(s) sur {len(res)} (resultats/{fich})")
        for x in res:
            if x["survivante"]:
                g = np.zeros(M.NG)
                if partie == "A":
                    g[M.FAM] = x["regle"]
                finalistes.append(dict(genome=g.tolist(), score=x["t"], marche=x["marche"], partie=partie,
                                       piste=partie, au_dessus=True,
                                       description=x.get("nom", "modele appris (partie C)"),
                                       net_trade=x["net_trade"], gagnants=x["gagnants"], n_tr=x["trades"]))
    L.append("")
    L.append(f"FINALISTES ({len(finalistes)}) :")
    for x in finalistes:
        L.append(f"  {x['partie']} {x['marche']} score {x['score']:.2f}"
                 + (f" (t entrainement {x['t_tr']:.2f}, validation {x['t_v']:.2f}, {x['n_tr']} + {x['n_v']} trades)"
                    if x["partie"] in ("B", "B2", "D") else "")
                 + f", net {x['net_trade']:.2f} $ par trade, gagnants {x['gagnants']:.0%}, "
                 + ("au-dessus de la barriere du bruit" if x["au_dessus"] else "SOUS la barriere du bruit"))
        L.append(f"      {x['description']}")
    L.append("")
    L.append(f"PLACEBOS ({len(placebos)}, choisis sur bruit, joues sur le vrai coffre) :")
    for x in placebos:
        L.append(f"  {x['partie']} {x['piste']} {x['marche']} score sur bruit {x['score']:.2f} : {x['description']}")
    L.append("")
    L.append("Exploration COMPLETE." if not manque else "Exploration INCOMPLETE, le coffre ne peut pas etre ouvert : "
             + " ; ".join(manque))
    txt = "\n".join(L)
    (MA.SORTIE / "exploration.txt").write_text(txt + "\n")
    (MA.SORTIE / "finalistes.json").write_text(json.dumps(dict(finalistes=finalistes, placebos=placebos,
                                                               complet=not manque, manque=manque), indent=1,
                                                          ensure_ascii=False))
    print(txt)


def _gains_coffre(x, cache):
    """Gains quotidiens d'une finaliste ou d'un placebo sur le coffre (seances du 1er janvier 2023 a la fin)."""
    import appris as AP
    piste, marche = x["piste"], x["marche"]
    cle_ = (piste if piste in ("D", "C") else "B", marche)
    if cle_ not in cache:
        if piste == "D":
            d = dict(np.load(MA.fichier("D", marche, "complet")))
        elif piste == "C":
            d = AP.charger(marche, quoi="complet")
        else:
            d = dict(np.load(K.CACHE / f"complet_{marche}.npz"))
        cache[cle_] = (d, M.indicateurs(d))
    d, f = cache[cle_]
    s0 = int(np.searchsorted(d["jours"], K.DEBUT_COFFRE))
    s1 = len(d["jours"])
    if piste == "C":
        _, prem = AP.periode(marche)
        p = AP.walk_forward(f, [2023, 2024, 2025, 2026], prem)
        gain, n, w = AP.executer(p, s0, s1, f["O"], f["H"], f["L"], f["C"], f["sig"], f["jouable"], f["echelle"],
                                 f["pt"], f["tick"], f["pas"], f["frais"], AP.SEUIL, AP.T0, f["C"].shape[1] - AP.FIN_AVANT,
                                 AP.H_CIBLE, np.zeros((1, 6)))
    else:
        gain, n, w, _, _ = M.jouer(np.asarray(x["genome"], float), f, s0, s1)
    return gain, n, w, d["jours"][s0:]


def ouvrir():
    drapeau = MA.SORTIE / "coffre_ouvert.txt"
    sel_f = MA.SORTIE / "finalistes.json"
    emp = empreinte(sel_f)
    if drapeau.exists():
        avant = drapeau.read_text().split()[-1]
        if "--relire" not in sys.argv or avant != emp:
            sys.exit("Le coffre a deja ete ouvert (resultats/coffre_ouvert.txt). --relire refait le meme calcul, et "
                     "seulement si finalistes.json n'a pas change.")
    sel = json.loads(sel_f.read_text())
    manque = completude()
    if manque or not sel.get("complet"):
        sys.exit("Exploration incomplete (" + " ; ".join(manque or sel.get("manque", ["?"])) + ") : le coffre reste ferme.")
    fichiers = sorted(MA.SORTIE.glob("machine_*.npz")) + [MA.SORTIE / "partie_a.json", MA.SORTIE / "appris.json"]
    if any(f.stat().st_mtime > sel_f.stat().st_mtime for f in fichiers):
        sys.exit("Un resultat d'exploration est plus recent que finalistes.json : relancer `exploration` d'abord.")
    fin, plac = sel["finalistes"], sel["placebos"]
    m = max(len(fin), 1)
    seuil = NormalDist().inv_cdf(1 - 0.05 / m)
    drapeau.write_text(f"coffre ouvert ; empreinte sha256 de finalistes.json : {emp}\n")
    cache = {}

    def jouer(x):
        gain, n, w, jours = _gains_coffre(x, cache)
        ok = np.isfinite(gain)
        an = jours.astype("datetime64[Y]").astype(int) + 1970
        ans = {a: float(np.nansum(gain[an == a])) for a in (2023, 2024, 2025, 2026)}
        return dict(t=K.t_stat(gain[ok]), trades=int(n), net_trade=float(np.nansum(gain) / max(n, 1)),
                    gagnants=float(w / max(n, 1)), total=float(np.nansum(gain)), annees=ans,
                    positives=int(sum(v > 0 for v in ans.values())), fin=str(jours[ok][-1]))

    L = [f"Coffre {K.DEBUT_COFFRE} - fin des donnees, ouvert une fois pour toutes les parties. m = {len(fin)} finalistes,"
         f" seuil de Bonferroni t >= {seuil:.2f} ; palier interessant : t >= 1,65 ; et au moins 3 annees positives sur "
         f"4. Gains pour 1 contrat micro, au prix d'aujourd'hui, frais compris.", ""]
    res_f, res_p = [], []
    for x in fin:
        r = jouer(x)
        r["retenue"] = bool(x["au_dessus"] and r["t"] >= seuil and r["positives"] >= 3)
        r["interessante"] = bool(r["t"] >= 1.65 and r["positives"] >= 3)
        res_f.append(r)
        L.append(f"{x['partie']} {x['marche']} exploration {x['score']:.2f} -> coffre t {r['t']:.2f}, {r['trades']} trades,"
                 f" net {r['net_trade']:.2f} $ par trade, total {r['total']:,.0f} $, annees "
                 + ", ".join(f"{a} {v:+,.0f}" for a, v in r["annees"].items())
                 + f" -> {'RETENUE' if r['retenue'] else ('interessante' if r['interessante'] else 'rejetee')}")
        L.append(f"      {x['description']}")
    L.append("")
    for x in plac:
        r = jouer(x)
        r["interessante"] = bool(r["t"] >= 1.65 and r["positives"] >= 3)
        r["bonferroni"] = bool(r["t"] >= seuil and r["positives"] >= 3)
        res_p.append(r)
        L.append(f"{x['partie']} {x['piste']} {x['marche']} : coffre t {r['t']:.2f}, {r['trades']} trades, total "
                 f"{r['total']:,.0f} $, {r['positives']} annees positives -> "
                 f"{'passe le palier interessant' if r['interessante'] else 'non'}")
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
