#!/usr/bin/env python3
"""Version 5 (README.md) : admission, controle 2023 - fin des donnees, candidates, placebos et paniers, comparaison au
bruit par la meme chaine. Ecrit resultats/v5/selection.txt et resultats/v5/candidats.json (liste figee pour le coffre de
l'avenir).

- Vrai : les admises des 6 graines sont reunies et les genomes en double retires (memes donnees, memes chiffres).
- Bruit : chaque graine a ses propres donnees ; une admise est le couple (graine, genome), rien n'est retire.
- Panier : moyenne des gains quotidiens de toutes les admises (seance non jouable = pas de trade, 0), sur les seances
  ou au moins une admise est jouable. Un panier de bruit sans aucune admise compte t = 0.
- Corrections de la contre-revue v5 : placebos marques suivis ou non ; paniers placebo ; constantes de calcul figees
  dans candidats.json ; JSON strict ; candidats.json non reecrit sans --force."""
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

import coffre as CO
import commun as K
import machine as MA
import vague5 as V

SORTIE = V.SORTIE
ZONE = Path(os.getenv("ZONE_TRADES", str(K.KB / "filtre_h1" / "trades_zone.csv")))


def lire(piste, marche, sorte):
    out = []
    for g in V.GRAINES:
        f = SORTIE / f"machine_{piste}_{marche}_{sorte}_{g}.npz"
        if f.exists():
            z = np.load(f)
            out.append({k: z[k] for k in z.files} | {"graine": g, "sorte": sorte})
    return out


def admises(runs, dedoublonner):
    """Liste de dict (genome, t_tr, n_tr, t_c, n_c, par_an, gains, graine)."""
    vus, out = set(), []
    for r in runs:
        for i in range(len(r["genomes"])):
            k = np.round(r["genomes"][i], 4).tobytes()
            if dedoublonner:
                if k in vus:
                    continue
                vus.add(k)
            out.append(dict(genome=r["genomes"][i], t_tr=float(r["t_tr"][i]), n_tr=int(r["n_tr"][i]),
                            t_c=float(r["t_c"][i]), n_c=int(r["n_c"][i]), par_an=r["par_an"][i], gains=r["gains"][i],
                            graine=r["graine"], sorte=r["sorte"]))
    return out


def trois_conditions(x):
    return x["t_c"] >= 1.65 and x["n_c"] >= 100 and int(np.sum(x["par_an"] > 0)) >= 3


def deux_meilleures(liste):
    out = []
    for x in sorted(liste, key=lambda y: -y["t_c"]):
        if all(int(x["genome"][0]) != int(y["genome"][0]) for y in out):
            out.append(x)
        if len(out) == 2:
            break
    return out


def panier(liste, jours):
    if not liste:
        return None
    G = np.array([x["gains"] for x in liste], dtype=float)
    jouable = np.isfinite(G).any(axis=0)
    p = np.nan_to_num(G).mean(axis=0)
    ans = jours.astype("datetime64[Y]").astype(int) + 1970
    par_an = np.array([p[jouable & (ans == a)].sum() for a in V.ANNEES])
    return dict(n=len(liste), t=K.t_stat(p[jouable]), moyenne=float(p[jouable].mean()), par_an=par_an, serie=p,
                jouable=jouable)


def constantes(piste, marche):
    """Constantes de calcul du marche, figees pour le coffre de l'avenir (le prix de reference de la nuit, par exemple,
    changerait si les caches etaient refaits avec de nouveaux mois)."""
    z = np.load(MA.fichier(piste, marche, "complet"))
    return {k: float(z[k]) for k in ("pt", "tick", "pas", "frais", "pref", "rond", "m0", "n")}


def propre(x):
    """JSON strict : NaN et infinis deviennent null."""
    if isinstance(x, dict):
        return {k: propre(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [propre(v) for v in x]
    if isinstance(x, (float, np.floating)):
        return float(x) if np.isfinite(x) else None
    if isinstance(x, np.integer):
        return int(x)
    return x


def zone_quotidienne():
    if not ZONE.exists():
        return None
    import pandas as pd
    z = pd.read_csv(ZONE)
    s = z.groupby("jour")["points"].sum()
    return {np.datetime64(j): v for j, v in s.items()}, np.datetime64(z["jour"].max())


def correlation_zone(serie, jours, jouable, zq):
    if zq is None:
        return float("nan")
    zd, fin = zq
    m = jouable & (jours <= fin)
    if m.sum() < 30:
        return float("nan")
    zz = np.array([zd.get(j, 0.0) for j in jours[m]])
    a = serie[m]
    return float(np.corrcoef(a, zz)[0, 1]) if a.std() > 0 and zz.std() > 0 else float("nan")


def main():
    zq = zone_quotidienne()
    L = ["Version 5 (README.md) : machine sur l'entrainement seulement, choix sur le controle 2023 - fin des donnees, "
         "comparaison a la meme chaine sur les deux bruits. Gains pour 1 contrat micro, au prix d'aujourd'hui, frais "
         "compris. Admise : t entrainement >= 2 avec 200 trades. Trois conditions : t controle >= 1,65, 100 trades, 3 "
         "annees positives sur 4. Barriere : meilleur t controle des admises de bruit qui remplissent les trois conditions.",
         "", "Correlation avec la zone du bot : " + (str(ZONE) if zq else "fichier des trades de la zone introuvable"), ""]
    candidates, placebos, paniers_cand, manque, resume = [], [], [], [], []
    for piste in ("B", "B2", "D"):
        for marche in MA.marches(piste):
            runs = {so: lire(piste, marche, so) for so in MA.SORTES}
            for so in MA.SORTES:
                if len(runs[so]) < len(V.GRAINES):
                    manque.append(f"{piste} {marche} {so} : {len(runs[so])} graine(s) sur {len(V.GRAINES)}")
            if not all(runs.values()):
                continue
            jours = runs["reel"][0]["jours"]
            assert all((r["jours"] == jours).all() for so in MA.SORTES for r in runs[so])
            adm = {so: admises(runs[so], dedoublonner=(so == "reel")) for so in MA.SORTES}
            ok = {so: [x for x in adm[so] if trois_conditions(x)] for so in MA.SORTES}
            barriere = max([x["t_c"] for so in ("bruit", "signe") for x in ok[so]], default=1.65)
            pan = {so: panier(adm[so], jours) for so in MA.SORTES}
            dist = {so: int(sum(int(r["distinctes"]) for r in runs[so])) for so in MA.SORTES}
            L.append(f"=== {piste} {marche} : strategies distinctes cherchees reel {dist['reel']}, permutation "
                     f"{dist['bruit']}, signe {dist['signe']}")
            for so in MA.SORTES:
                tc = np.array([x["t_c"] for x in adm[so]])
                p = pan[so]
                L.append(f"  {so:<6} admises {len(adm[so]):6d} ; t controle median {np.median(tc) if len(tc) else np.nan:6.2f}, "
                         f"part > 0 {np.mean(tc > 0) if len(tc) else np.nan:5.0%}, meilleur {tc.max() if len(tc) else np.nan:5.2f} ; "
                         f"trois conditions {len(ok[so]):5d} ; panier t "
                         + (f"{p['t']:5.2f} ({p['moyenne']:+.2f} $/seance ; " + " ".join(f"{a}:{v:+.0f}" for a, v in
                                                                                    zip(V.ANNEES, p['par_an'])) + ")"
                            if p else "  -"))
            L.append("  graine par graine (admises / meilleur t controle / panier t) :")
            for so in MA.SORTES:
                el = []
                for r in runs[so]:
                    a = admises([r], dedoublonner=False)
                    p = panier(a, jours)
                    el.append(f"{len(a)}/{max([x['t_c'] for x in a], default=float('nan')):.2f}/"
                              f"{p['t'] if p else float('nan'):.2f}")
                L.append(f"    {so:<6} " + "  ".join(el))
            L.append(f"  barriere du bruit : {barriere:.2f}")
            cst = constantes(piste, marche)
            n_cand = 0
            for x in deux_meilleures([x for x in ok["reel"] if x["t_c"] > barriere]):
                c = correlation_zone(np.nan_to_num(x["gains"]), jours, np.isfinite(x["gains"]), zq)
                d = dict(type="candidate", piste=piste, marche=marche, genome=x["genome"].tolist(), t_tr=x["t_tr"],
                         n_tr=x["n_tr"], t_c=x["t_c"], n_c=x["n_c"], par_an=x["par_an"].tolist(), barriere=barriere,
                         corr_zone=c, constantes=cst, description=CO.decrire(x["genome"], piste))
                candidates.append(d)
                n_cand += 1
                L.append(f"  CANDIDATE t controle {x['t_c']:.2f} ({x['n_c']} trades, entrainement t {x['t_tr']:.2f}), "
                         f"correlation zone {c:+.2f} : {d['description']}")
            pr = pan["reel"]
            passe = False
            if pr:
                cz = correlation_zone(pr["serie"], jours, pr["jouable"], zq)
                bruits = [pan[so]["t"] if pan[so] else 0.0 for so in ("bruit", "signe")]   # aucun admis : t = 0
                passe = (pr["t"] >= 2 and int(np.sum(pr["par_an"] > 0)) >= 3 and all(pr["t"] > b for b in bruits))
                L.append(f"  panier reel : t {pr['t']:.2f} (paniers de bruit {bruits[0]:.2f} et {bruits[1]:.2f}), "
                         f"correlation zone {cz:+.2f}, " + ("PANIER CANDIDAT" if passe else "non retenu"))
                if passe:
                    paniers_cand.append(dict(type="panier", piste=piste, marche=marche, n=pr["n"], t_c=pr["t"],
                                             par_an=pr["par_an"].tolist(), corr_zone=cz, constantes=cst,
                                             genomes=[x["genome"].tolist() for x in adm["reel"]]))
                    for so in ("bruit", "signe"):          # panier placebo : les admises de ce bruit, jouees sur le vrai
                        if adm[so]:
                            placebos.append(dict(type="panier placebo", piste=piste, marche=marche, sorte=so,
                                                 n=len(adm[so]), t_c_bruit=pan[so]["t"], suivi=True, constantes=cst,
                                                 genomes=[x["genome"].tolist() for x in adm[so]]))
            suivi = bool(n_cand or passe)
            for x in deux_meilleures(ok["bruit"] + ok["signe"]):
                placebos.append(dict(type="placebo", piste=piste, marche=marche, genome=x["genome"].tolist(),
                                     sorte=x["sorte"], graine=int(x["graine"]), t_tr_bruit=x["t_tr"], t_c_bruit=x["t_c"],
                                     n_c_bruit=x["n_c"], par_an_bruit=x["par_an"].tolist(), suivi=suivi, constantes=cst,
                                     description=CO.decrire(x["genome"], piste)))
            resume.append((piste, marche, len(ok["reel"]), len(ok["bruit"]) + len(ok["signe"]), barriere,
                           max([x["t_c"] for x in ok["reel"]], default=float("nan"))))
            L.append("")
    m = len(candidates) + len(paniers_cand)
    seuil = float(norm.ppf(1 - 0.05 / m)) if m else float("nan")
    L.append("RESUME : couple, admises reelles aux trois conditions, admises de bruit aux trois conditions (12 graines), "
             "barriere, meilleur reel")
    for p, mm, a, b, bar, best in resume:
        L.append(f"  {p:<3} {mm:<4} {a:6d} {b:6d}   barriere {bar:5.2f}   meilleur reel {best:5.2f}")
    L.append("")
    L.append(f"CANDIDATES : {len(candidates)} ; PANIERS CANDIDATS : {len(paniers_cand)} ; PLACEBOS : "
             f"{sum(p['suivi'] for p in placebos)} suivis sur {len(placebos)} listes ; "
             f"m = {m}, seuil de Bonferroni pour le coffre de l'avenir : {seuil:.2f}")
    L.append("Selection COMPLETE." if not manque else "Selection INCOMPLETE : " + " ; ".join(manque))
    txt = "\n".join(L)
    (SORTIE / "selection.txt").write_text(txt + "\n")
    if not manque:
        if zq is None:
            sys.exit(f"Trades de la zone introuvables ({ZONE}) : donner ZONE_TRADES ; candidats.json n'est pas ecrit.")
        f = SORTIE / "candidats.json"
        texte = json.dumps(propre(dict(candidates=candidates, paniers=paniers_cand, placebos=placebos, m=m,
                                       seuil_bonferroni=seuil, debut_coffre="2026-11-01")),
                           indent=1, ensure_ascii=False, allow_nan=False)
        if f.exists() and f.read_text() != texte and "--force" not in sys.argv:
            sys.exit("candidats.json existe deja avec un autre contenu : la liste du coffre est figee (--force pour "
                     "passer outre, a justifier dans le README).")
        f.write_text(texte)
        L.append(f"candidats.json sha256 {hashlib.sha256(f.read_bytes()).hexdigest()}")
        (SORTIE / "selection.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return 0 if not manque else 1


if __name__ == "__main__":
    sys.exit(main())
