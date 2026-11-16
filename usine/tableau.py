"""Tableau de bord de l'usine (etape 5 de l'article) : ce qui a ete teste, chaque porte passee ou manquee avec sa p-value,
la marche en avant, ce que ca donne sur le compte, et le verdict, en clair.

Lit le dernier dossier usine/resultats/<date>/ ; ecrit usine/TABLEAU.md et usine/tableau/donnees.json (pour la page).
Aucune donnee du compte reel ici : le depot est public.
"""
import json
import sys
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import moteur as Mo  # noqa: E402

NOMS_REGLAGES = {"k": "largeur", "jours": "jours de moyenne", "atr": "ATR", "multiple": "multiple", "duree": "durée du range (min)",
                 "derniere_entree": "dernière entrée", "fin_signal": "fin du signal", "reference": "référence",
                 "debut_position": "début de la position", "marge": "marge", "sortie": "sortie", "seuil": "seuil",
                 "duree_max": "durée maximale (min)", "debut": "début"}
VERDICTS = {"passe les 5 portes": "passe les 5 portes", "rejetee a la porte 1": "rejetée à la porte 1",
            "rejetee a la porte 2": "rejetée à la porte 2", "rejetee a la porte 3": "rejetée à la porte 3",
            "rejetee a la porte 4": "rejetée à la porte 4", "rejetee a la porte 5": "rejetée à la porte 5"}


def heure(m):
    return f"{(570 + int(m)) // 60} h {(570 + int(m)) % 60:02d}"


def joli(nom, v):
    if nom in ("derniere_entree", "fin_signal", "debut_position", "debut"):
        return heure(v)
    if nom == "reference":
        return "clôture de la veille" if v == 0 else "ouverture"
    if nom == "sortie":
        return "retour dans le range" if v == 0 else "fin de séance"
    if nom in ("marge", "seuil"):
        return f"{v * 100:.2f} %".replace(".", ",")
    return str(v).replace(".", ",")


def reglage(r):
    return ", ".join(f"{NOMS_REGLAGES.get(k, k)} {joli(k, v)}" for k, v in r.items())


def pct(x):
    return f"{x * 100:.1f} %".replace(".", ",")


def usd(x, signe=True):
    """Montant en dollars a la francaise : +4 073 $."""
    return (format(x, "+,.0f") if signe else format(x, ",.0f")).replace(",", " ") + " $"


def dec(x, k=3):
    return f"{x:.{k}f}".replace(".", ",")


def raison(R):
    p = R["portes"]; v = R["verdict"]
    if v.endswith("porte 1"):
        a = p["1"]
        if a["trop_parfait"]:
            return f"trop parfait sur 2011 - 2014 (PF {dec(a['pf_meilleur'], 2)}) : à vérifier avant tout"
        if not a["plateau"]:
            return f"pic isolé : ses voisins ne suivent pas (meilleur PF {dec(a['pf_meilleur'])})"
        return f"pas assez bon sur 2011 - 2014 : PF {dec(a['pf_meilleur'])}, t {dec(a['t_meilleur'], 2)}"
    if v.endswith("porte 2"):
        return f"fait aussi bien sur des minutes mélangées : p = {pct(p['2']['p'])}, il faut moins de 1 %"
    if v.endswith("porte 3"):
        return f"hors échantillon (2015 → aujourd'hui) : PF {dec(p['3']['pf'])}, {usd(p['3']['gain_par_an'])} par an"
    if v.endswith("porte 4"):
        return f"sa marche en avant ne bat pas le hasard : p = {pct(p['4']['p'])}, il faut moins de 1 %"
    if v.endswith("porte 5"):
        x = p["5"]["variantes"][p["5"]["jouee"]]["neuf_250"]
        return f"sur un Master neuf, {pct(x['retrait'])} de premiers retraits pour {pct(x['plancher'] + x['inactivite'])} de comptes perdus"
    return (f"porte 2 : p = {pct(p['2']['p'])} ; porte 4 : p = {pct(p['4']['p'])} ; hors échantillon {usd(p['3']['gain_par_an'])} par an ; "
            f"sur un Master neuf, {pct(p['5']['variantes'][p['5']['jouee']]['neuf_250']['retrait'])} de premiers retraits")


def charger(dossier=None):
    racine = ICI / "resultats"
    dossier = Path(dossier) if dossier else max((d for d in racine.iterdir() if d.is_dir() and d.name[:2] == "20"), key=lambda d: d.name)
    R = {}
    for nom in Mo.STRATEGIES:
        f = dossier / f"{nom}.json"
        if f.exists():
            R[nom] = json.loads(f.read_text())
            R[nom]["titre"] = Mo.STRATEGIES[nom]["titre"]          # titre affiche : celui du moteur, avec accents
    return dossier.name, R


def markdown(date, R):
    L = [f"# Usine a strategies : tableau de bord ({date})", "",
         "Regles fixees avant le calcul : [REGLES.md](REGLES.md). Chaque idee passe les portes dans l'ordre et s'arrete a la "
         "premiere manquee. La zone et le Supertrend, deja sur le compte, passent toutes les portes pour information.", "",
         "| Idee | Porte 1 : 2011 - 2014 | Porte 2 : permutations | Porte 3 : marche en avant 2015 -> | Porte 4 : permutations | Porte 5 : Master neuf, un an | Verdict |",
         "|---|---|---|---|---|---|---|"]
    for nom, r in R.items():
        p = r["portes"]
        c1 = f"PF {dec(p['1']['pf_meilleur'])}, t {dec(p['1']['t_meilleur'], 2)} {'✅' if p['1']['passe'] else '❌'}"
        c2 = f"p {pct(p['2']['p'])} {'✅' if p['2']['passe'] else '❌'}" if "2" in p else "—"
        c3 = f"PF {dec(p['3']['pf'])}, {usd(p['3']['gain_par_an'])} par an {'✅' if p['3']['passe'] else '❌'}" if "3" in p else "—"
        c4 = f"p {pct(p['4']['p'])} {'✅' if p['4']['passe'] else '❌'}" if "4" in p else "—"
        if "5" in p:
            x = p["5"]["variantes"][p["5"]["jouee"]]["neuf_250"]
            c5 = f"retrait {pct(x['retrait'])}, perdu {pct(x['plancher'] + x['inactivite'])} {'✅' if p['5']['passe'] else '❌'}"
        else:
            c5 = "—"
        L.append(f"| {r['titre']} | {c1} | {c2} | {c3} | {c4} | {c5} | **{VERDICTS.get(r['verdict'], r['verdict'])}** |")
    L += ["", "PF : profit factor des rendements nets par minute. p : part des permutations qui font au moins aussi bien.", ""]
    for nom, r in R.items():
        s = Mo.STRATEGIES[nom]; p = r["portes"]
        L += [f"## {r['titre']}", "", f"- **L'avantage :** {s.get('avantage', '')}", f"- **Qui perd en face :** {s.get('contrepartie', '')}",
              f"- **Verdict : {VERDICTS.get(r['verdict'], r['verdict'])}.** {raison(r)[0].upper() + raison(r)[1:]}.",
              f"- Meilleur reglage sur 2011 - 2014 : {reglage(p['1']['reglage_meilleur'])} (PF {dec(p['1']['pf_meilleur'])}) ; "
              f"milieu du plateau : {reglage(p['1']['reglage_centre'])} (PF {dec(p['1']['pf_centre'])})."]
        if "reglage_bot" in p["1"]:
            L.append(f"- Reglage du bot ({reglage(p['1']['reglage_bot'])}) : PF {dec(p['1']['pf_bot'])} sur 2011 - 2014.")
        if "3" in p:
            L.append(f"- Marche en avant, 2015 -> derniere seance : {p['3']['seances']} seances, t {dec(p['3']['t'], 2)}.")
        if "5" in p:
            q = p["5"]; d = q["dollars"]
            L.append(f"- Milieu du plateau, 1 MNQ, 2015 -> derniere seance : {usd(d['gain_par_an'])} par an, t {dec(d['t'], 2)} (depuis 2023 : "
                     f"{dec(d['t_depuis_2023'], 2)}), pire baisse {usd(d['pire_baisse'])}, pire seance {usd(d['pire_seance'])} ; trade "
                     f"{pct(q['part_seances_tradees'])} des seances.")
            for var, v in q["variantes"].items():
                a, b = v["neuf_250"], v["marge_700_22"]
                L.append(f"  - {var} : Master neuf, un an : {pct(a['retrait'])} de premiers retraits, {pct(a['plancher'])} perdus par le "
                         f"plancher, {pct(a['inactivite'])} par l'inactivite ; depuis une marge de 700 $, un mois : {pct(b['plancher'] + b['inactivite'])} "
                         f"de comptes perdus, gain moyen {usd(b['gain_moyen'])}.")
        L.append("")
    (ICI / "TABLEAU.md").write_text("\n".join(L))


def page(date, R):
    """Donnees compactes pour la page (artifact)."""
    out = {"date": date, "idees": []}
    for nom, r in R.items():
        s = Mo.STRATEGIES[nom]; p = r["portes"]
        combos, forme = Mo.combinaisons(s)
        x = {"nom": nom, "titre": r["titre"], "avantage": s.get("avantage", ""), "contrepartie": s.get("contrepartie", ""),
             "verdict": r["verdict"], "raison": raison(r), "info": nom in ("zone", "supertrend"),
             "reglages": [[NOMS_REGLAGES.get(k, k), [joli(k, v) for v in vals]] for k, vals in s["reglages"]],
             "forme": list(forme), "p1": {k: p["1"][k] for k in ("pf", "meilleur", "centre", "pf_meilleur", "t_meilleur", "plateau", "trop_parfait", "passe")}}
        x["p1"]["reglage_meilleur"] = reglage(p["1"]["reglage_meilleur"]); x["p1"]["reglage_centre"] = reglage(p["1"]["reglage_centre"])
        for g in ("2", "4"):
            if g in p:
                dist = np.array(p[g]["distribution"], float); reel = p[g]["pf_reel"]
                lo, hi = float(min(dist.min(), reel)), float(max(dist.max(), reel))
                h, b = np.histogram(dist, bins=30, range=(lo, hi + 1e-9))
                x[f"p{g}"] = dict(p=p[g]["p"], passe=p[g]["passe"], reel=reel, n=p[g]["permutations"], bords=b.tolist(), compte=h.tolist(),
                                  battues=int((dist >= reel).sum()))
        if "3" in p:
            m = p["3"]["mois"]; cum = np.cumsum([v for _, v in m])
            x["p3"] = dict(pf=p["3"]["pf"], gain_par_an=p["3"]["gain_par_an"], t=p["3"]["t"], passe=p["3"]["passe"],
                           mois=[k for k, _ in m], cumul=[round(float(c), 1) for c in cum])
        if "5" in p:
            x["p5"] = dict(jouee=p["5"]["jouee"], passe=p["5"]["passe"], dollars=p["5"]["dollars"], part=p["5"]["part_seances_tradees"],
                           variantes=p["5"]["variantes"])
        out["idees"].append(x)
    (ICI / "tableau").mkdir(exist_ok=True)
    (ICI / "tableau/donnees.json").write_text(json.dumps(out, ensure_ascii=False))
    return out


def fichiers_page(date, R):
    """Les sources de la page « Data » (artifact) : un JSON {rows, meta} par source, avec le code qui les a faits."""
    meta = [{"label": "tableau.py", "value": Path(__file__).read_text(), "type": "code", "lang": "python"},
            {"label": "Entree", "value": f"usine/resultats/{date}/*.json, ecrits par usine/portes.py (moteur usine/moteur.py), "
                                        "branche claude/hopeful-shannon-xkvqo1"},
            {"label": "Calcul", "value": date}]
    idees, grille, perms, marche, compte = [], [], [], [], []
    for nom, r in R.items():
        s = Mo.STRATEGIES[nom]; p = r["portes"]
        combos, forme = Mo.combinaisons(s)
        passees = 0
        for g in "12345":
            if g in p and p[g]["passe"]:
                passees += 1
            else:
                break
        a = p["1"]
        row = dict(idee=nom, titre=s["titre"], avantage=s.get("avantage", ""), contrepartie=s.get("contrepartie", ""),
                   verdict=r["verdict"], verdict_texte=VERDICTS.get(r["verdict"], r["verdict"]), raison=raison(r), portes_passees=passees, en_service=nom in ("zone", "supertrend"),
                   date_calcul=date, p1_pf=a["pf_meilleur"], p1_t=a["t_meilleur"], p1_passe=a["passe"],
                   p1_texte=f"PF {dec(a['pf_meilleur'])}, t {dec(a['t_meilleur'], 2)}", plateau="oui" if a["plateau"] else "non",
                   reglage_meilleur=reglage(a["reglage_meilleur"]), reglage_centre=reglage(a["reglage_centre"]))
        for g in ("2", "4"):
            if g in p:
                q = p[g]; dist = np.array(q["distribution"], float); reel = q["pf_reel"]
                lo, hi = float(min(dist.min(), reel)), float(max(dist.max(), reel))
                h, b = np.histogram(dist, bins=30, range=(lo, hi + 1e-9))
                for k in range(len(h)):
                    perms.append(dict(idee=nom, porte=g, bas=float(b[k]), haut=float(b[k + 1]), nombre=int(h[k])))
                row.update({f"p{g}_p": q["p"], f"p{g}_passe": q["passe"], f"p{g}_texte": f"p = {pct(q['p'])}", f"p{g}_reel": reel,
                            f"p{g}_battues": int((dist >= reel).sum()), f"p{g}_n": q["permutations"]})
            else:
                row.update({f"p{g}_p": None, f"p{g}_passe": None, f"p{g}_texte": "", f"p{g}_reel": None, f"p{g}_battues": None, f"p{g}_n": None})
        if "3" in p:
            q = p["3"]
            row.update(p3_pf=q["pf"], p3_gain_an=q["gain_par_an"], p3_passe=q["passe"], p3_texte=f"PF {dec(q['pf'])}, {usd(q['gain_par_an'])} par an")
            cum = 0.0
            for mois, v in q["mois"]:
                cum += v
                marche.append(dict(idee=nom, mois=mois, cumul=round(cum, 1)))
        else:
            row.update(p3_pf=None, p3_gain_an=None, p3_passe=None, p3_texte="")
        if "5" in p:
            q = p["5"]; x = q["variantes"][q["jouee"]]["neuf_250"]
            row.update(p5_retrait=x["retrait"], p5_perdu=x["plancher"] + x["inactivite"], p5_passe=q["passe"], p5_jouee=q["jouee"],
                       p5_texte=f"{pct(x['retrait'])} de retraits, {pct(x['plancher'] + x['inactivite'])} perdus")
            for var, v in q["variantes"].items():
                for cle, scen, dur in (("neuf_22", "Master neuf", "un mois"), ("neuf_250", "Master neuf", "un an"),
                                       ("marge_700_22", "Marge de 700 $", "un mois"), ("marge_700_250", "Marge de 700 $", "un an")):
                    y = v[cle]
                    compte.append(dict(cle=f"{nom}|{var}|{cle}", idee=nom, variante=var, depart=scen, duree=dur, retrait=y["retrait"],
                                       plancher=y["plancher"], inactivite=y["inactivite"], gain_moyen=y["gain_moyen"],
                                       retrait_texte=pct(y["retrait"]), plancher_texte=pct(y["plancher"]),
                                       inactivite_texte=pct(y["inactivite"]), gain_texte=usd(y["gain_moyen"])))
        else:
            row.update(p5_retrait=None, p5_perdu=None, p5_passe=None, p5_jouee="", p5_texte="")
        idees.append(row)
        noms = [n for n, _ in s["reglages"]]
        for i, c in enumerate(combos):
            lab = lambda k: f"{NOMS_REGLAGES.get(noms[k], noms[k])} {joli(noms[k], c[noms[k]])}" if len(noms) > k else ""  # noqa: E731
            grille.append(dict(idee=nom, ligne=lab(0), colonne=lab(1), facette=lab(2), pf=float(a["pf"][i]), t=float(a["t_grille"][i]),
                               meilleur=i == a["meilleur"], centre=i == a["centre"], pf_texte=dec(a["pf"][i]),
                               ligne_nom=NOMS_REGLAGES.get(noms[0], noms[0]), colonne_nom=NOMS_REGLAGES.get(noms[1], noms[1]) if len(noms) > 1 else ""))
    d = ICI / "tableau"; d.mkdir(exist_ok=True)
    for nom, rows in (("idees", idees), ("grille", grille), ("permutations", perms), ("marche", marche), ("compte", compte)):
        (d / f"{nom}.json").write_text(json.dumps({"rows": rows, "meta": meta}, ensure_ascii=False, allow_nan=False))
    return {k: len(v) for k, v in (("idees", idees), ("grille", grille), ("permutations", perms), ("marche", marche), ("compte", compte))}


if __name__ == "__main__":
    date, R = charger(sys.argv[1] if len(sys.argv) > 1 else None)
    markdown(date, R); page(date, R); print(fichiers_page(date, R))
    print(f"Tableau du {date} : {len(R)} idees ; {sum(r['verdict'] == 'passe les 5 portes' for r in R.values())} passent les 5 portes.")
