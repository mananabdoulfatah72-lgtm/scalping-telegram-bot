#!/usr/bin/env python3
"""Revue de fin de semaine du bot 3 en 1 (zone de bruit), sur le modèle demandé par l'utilisateur le 1er novembre 2026.

Chaque fin de semaine, l'utilisateur envoie :
  - C:\\Bot3en1\\journal.txt (toutes les décisions du bot, heures UTC) ;
  - l'export des transactions du NQ de la semaine (stratégie « Export transactions NQ », fichier transactions_NQ*.csv :
    jour, minute depuis 9 h 30, o, h, l, c, v, achats, ventes, sans_cote, contrat).

Pour chaque trade perdant, le rapport donne :
  1. les conditions exactes du déclenchement (heure, prix, niveaux, VWAP, delta, dépassement, distance au VWAP, niveau
     de sortie, réglages, taille) ;
  2. si la perte était évitable avec ce que le bot savait au moment de décider ;
  3. la règle responsable ou le filtre manquant (entrée tardive, piège du bruit, profit rendu, stop ou limite, main,
     réglages) ;
  4. la correction précise, avec son verdict sur 15 ans (audit/README.md). Une correction n'est appliquée au bot que si
     elle passe les critères du protocole sur 15 ans : sinon, elle ferait perdre plus dans les semaines suivantes.
Il vérifie aussi ce que chaque correction aurait fait aux trades gagnants de la semaine.

Lancer : python3 audit/semaine.py <journal.txt> <transactions_NQ.csv> [--debut AAAA-MM-JJ] [--fin AAAA-MM-JJ]
         [--limite 1000] [--sortie rapport.md]
"""
import argparse
import math
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pandas as pd

NY = ZoneInfo("America/New_York")
FRAIS = 3.0          # $ par MNQ aller-retour, comme le rejeu
NOMBRE = r"(-?\d+(?:[.,]\d+)?)"

# Verdicts des corrections testées sur 15 ans (audit/README.md). Mettre à jour quand une correction est adoptée.
CORRECTIONS = {
    "C1": ("pas d'entrée si le prix est déjà à plus d'une largeur de bande au-delà du niveau",
           "rejetée : sur 15 ans, +63 830 $ au lieu de +79 847 $, moins bien sur les 3 périodes"),
    "C2": ("après une sortie perdante, plus d'entrée dans le même sens pendant la séance",
           "ADOPTÉE le 1er novembre 2026 (réglage coché par défaut) : sur des challenges simulés, 51 % d'échecs au lieu de 56,5 %, autant de réussites"),
    "C3": ("le filtre delta demande |delta 30 min| ≥ 300",
           "rejetée : retire autant de gagnants que de perdants (+795 $ / −748 $ sur 7 mois)"),
    "C4": ("sortie à un contrôle si la moitié d'un gain d'au moins une largeur de bande est rendue",
           "rejetée : sur 15 ans, +74 491 $ au lieu de +79 847 $, moins bien sur 2011 - 2022 ; coupe aussi le gagnant du 14 octobre"),
    "C5": ("sortie à la minute qui clôture au-delà du niveau de sortie du dernier contrôle",
           "rejetée : sur 15 ans, +247 298 $ au lieu de +319 389 $ (4 MNQ), moins bien sur les 3 périodes (piège du bruit)"),
    "C6": ("taille réduite pour que la perte jusqu'au niveau de sortie ne dépasse pas 500 $",
           "rejetée : sur 15 ans, +232 568 $ au lieu de +319 389 $ (4 MNQ), moins bien sur les 3 périodes"),
    "C7": ("pas d'entrée à plus de 2 largeurs de bande du VWAP",
           "non adoptée : passe seule, mais avec C2 elle baisse la réussite des challenges de 2,2 points ; C2 baisse plus les échecs"),
}
REGLAGES_MODIFIES = ("A LA CASSURE", "UNE ENTREE PAR SEANCE", "STOP A", "PAS DE SORTIE AUX CONTROLES", "filtre delta decoche",
                     "SANS ENTREE TARDIVE", "Q1 (sens de l'ouverture) COCHE", "Q2 (tendance de fond) COCHE")


def nombre(x):
    return float(x.replace(",", "."))


def heure_ny(utc):
    return utc.replace(tzinfo=timezone.utc).astimezone(NY).replace(tzinfo=None)


def minute_seance(t):
    return (t.hour - 9) * 60 + t.minute - 30


def hm(m):
    return f"{(570 + m) // 60}h{(570 + m) % 60:02d}"


def lire_minutes(f):
    d = pd.read_csv(f)
    d["jour"] = pd.to_datetime(d["jour"]).dt.date
    return {j: g.set_index("minute").sort_index() for j, g in d.groupby("jour")}


def lire_journal(f, debut, fin):
    """Événements du journal par jour de séance (heure de New York)."""
    jours = defaultdict(lambda: dict(controles={}, entrees=[], evenements=[], reglages=None, taille=None))
    reglages, taille = None, None
    for l in open(f, encoding="utf-8", errors="replace"):
        m = re.match(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC (.*)", l.rstrip("\n"))
        if not m:
            continue
        t = heure_ny(datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S"))
        txt = m.group(2)
        j = t.date()
        if "version du" in txt and txt.startswith("demarre"):
            reglages = txt.split("version du", 1)[1].strip()
        x = re.search(r"taille aujourd'hui : (\d+) MNQ", txt)
        if x:
            taille = int(x.group(1))
        if (debut and j < debut) or (fin and j > fin):
            continue
        J = jours[j]
        J["reglages"] = J["reglages"] or reglages
        J["taille"] = J["taille"] or taille
        x = re.match(r"controle .*\((\d+)h(\d+) New York\) : prix " + NOMBRE + r", achat au-dessus de " + NOMBRE
                     + r", vente sous " + NOMBRE + r", VWAP " + NOMBRE + r", delta 30 min ([+-]?\d+) -> (.*)", txt)
        if x:
            mm = (int(x.group(1)) - 9) * 60 + int(x.group(2)) - 30
            J["controles"][mm] = dict(prix=nombre(x.group(3)), haut=nombre(x.group(4)), bas=nombre(x.group(5)),
                                      vwap=nombre(x.group(6)), delta=int(x.group(7)), decision=x.group(8))
            continue
        x = re.match(r"(achat|vente) (\d+)h(\d+) a " + NOMBRE + r" \((relance : )?delta 30 min ([+-]?\d+), GARDE[^)]*\)"
                     r"(?: \[depassement " + NOMBRE + r"\])?(.*)", txt)
        if x:
            mm = (int(x.group(2)) - 9) * 60 + int(x.group(3)) - 30
            J["entrees"].append(dict(t=t, minute=mm, sens=1 if x.group(1) == "achat" else -1, prix=nombre(x.group(4)),
                                     delta=int(x.group(6)), depassement=nombre(x.group(7)) if x.group(7) else None,
                                     relance=bool(x.group(5)), texte=txt, reglages=reglages, taille=taille))
            continue
        for motif, quoi in ((r"sortie (\d+)h(\d+)(?: \d+h\d+)? a " + NOMBRE, "sortie"), (r"stop (\d+)h(\d+) a " + NOMBRE, "stop")):
            x = re.match(motif, txt)
            if x:
                J["evenements"].append(dict(t=t, quoi=quoi, prix=nombre(x.group(3)), texte=txt))
                break
        else:
            for cle, quoi in (("limite de perte du jour atteinte", "limite"), ("arret du bot", "arret"),
                              ("fermee hors du bot", "main"), ("plafond du jour atteint", "plafond"),
                              ("objectif", "objectif") if "atteint" in txt else ("\0", ""),
                              ("demarrage en cours de seance", "relance_bot"), ("ordre envoye", "ordre"),
                              ("fichier STOP", "arret")):
                if cle in txt:
                    J["evenements"].append(dict(t=t, quoi=quoi, prix=None, texte=txt))
                    break
    return jours


def prix_a(minutes, j, t):
    """Clôture de la minute du NQ à l'heure t (New York)."""
    g = minutes.get(j)
    m = minute_seance(t)
    if g is None or g.empty:
        return None
    g = g[g.index <= m]
    return float(g["c"].iloc[-1]) if len(g) else None


def trades_du_jour(j, J, minutes):
    """Associe chaque entrée gardée à sa sortie (règle, stop, limite, arrêt, main, 16 h)."""
    out = []
    ev = sorted(J["evenements"], key=lambda e: e["t"])
    for k, e in enumerate(J["entrees"]):
        fin_suivante = J["entrees"][k + 1]["t"] if k + 1 < len(J["entrees"]) else None
        sortie, reouverture = None, None
        for x in ev:
            if x["t"] < e["t"] or (fin_suivante and x["t"] >= fin_suivante):
                continue
            if (x["quoi"] == "ordre" and re.search(r"\(position 0 -> -?[1-9]", x["texte"])
                    and (x["t"] - e["t"]).total_seconds() > 5):
                # la position est revenue a 0 sans ordre du bot, puis le bot l'a rouverte (ancienne version)
                sortie = dict(t=x["t"], quoi="main", prix=None, texte="position fermee a la main, rouverte aussitot par le bot")
                reouverture = x
                break
            if x["quoi"] in ("sortie", "stop", "limite", "arret", "main", "plafond", "objectif"):
                sortie = x
                break
            if x["quoi"] == "relance_bot":
                sortie = dict(x, quoi="relance_bot")
                break
        if sortie is None:
            t16 = datetime.combine(j, datetime.min.time()) + timedelta(hours=15, minutes=59)
            sortie = dict(t=t16, quoi="16h", prix=prix_a(minutes, j, t16), texte="fin de seance (16 h)")
        prix = sortie["prix"] if sortie.get("prix") is not None else prix_a(minutes, j, sortie["t"])
        out.append(dict(e, jour=j, sortie=sortie, prix_sortie=prix, reouvert=reouverture is not None, rouverte_par_bot=False))
        if reouverture is not None:
            t0 = reouverture["t"]
            s2 = next((x for x in ev if x["t"] > t0 and x["quoi"] in ("sortie", "stop", "limite", "arret", "main", "plafond", "objectif")), None)
            if s2 is None:
                t16 = datetime.combine(j, datetime.min.time()) + timedelta(hours=15, minutes=59)
                s2 = dict(t=t16, quoi="16h", prix=prix_a(minutes, j, t16), texte="fin de seance (16 h)")
            out.append(dict(e, t=t0, minute=minute_seance(t0), prix=prix_a(minutes, j, t0), depassement=None, jour=j, sortie=s2,
                            prix_sortie=s2["prix"] if s2.get("prix") is not None else prix_a(minutes, j, s2["t"]),
                            reouvert=False, rouverte_par_bot=True))
    return out


def analyser(tr, J, minutes, limite, precedent):
    j, s, p, mm = tr["jour"], tr["sens"], tr["prix"], tr["minute"]
    taille = tr["taille"] or 1
    c = J["controles"].get(mm) or {}
    g = minutes.get(j)
    haut, bas, vw = c.get("haut"), c.get("bas"), c.get("vwap")
    niveau = (max(haut, vw) if s > 0 else min(bas, vw)) if c else None
    casse = (haut if s > 0 else bas) if c else None
    largeur = None
    if tr["depassement"] and tr["depassement"] >= 0.05 and casse is not None:
        largeur = abs(p - casse) / tr["depassement"]
    elif g is not None and casse is not None:
        largeur = abs(casse) * 0.003            # repli grossier si le dépassement est presque nul
    ps = tr["prix_sortie"]
    pts = s * (ps - p) if ps is not None else float("nan")
    usd = taille * (2 * pts - FRAIS)
    estimation = re.search(r"estimation (-?\d+) \$", tr["sortie"]["texte"])
    m_sortie = minute_seance(tr["sortie"]["t"])
    mfe = mae = float("nan")
    if g is not None:
        w = g[(g.index > mm) & (g.index <= m_sortie)]
        if len(w):
            mfe = (w["h"].max() - p) if s > 0 else (p - w["l"].min())
            mae = (p - w["l"].min()) if s > 0 else (w["h"].max() - p)
    hausse30 = None
    if g is not None and (mm - 30) in g.index:
        hausse30 = s * (p - float(g.loc[mm - 30, "c"]))
    dist_vwap = s * (p - vw) / largeur if (vw is not None and largeur) else None
    dist_sortie = abs(p - niveau) if niveau is not None else None
    capacite = limite / (2 * taille)
    reglages = tr["reglages"] or ""
    modifies = [r for r in REGLAGES_MODIFIES if r in reglages]
    duree = m_sortie - mm

    causes, corrections, evitable = [], [], []
    q = tr["sortie"]["quoi"]
    if modifies:
        causes.append("réglages différents de la zone d'origine (" + ", ".join(modifies).lower() + ")")
        corrections.append("revenir à la zone d'origine (réglages par défaut du bot depuis le 31 octobre 2026)")
        evitable.append("oui : réglages")
    if (q == "main" or q == "arret") and not tr["rouverte_par_bot"]:
        causes.append("intervention à la main (" + ("bot arrêté" if q == "arret" else "position fermée hors du bot") + ")")
        corrections.append("laisser la règle gérer le trade jusqu'à sa sortie")
        evitable.append("oui : opération")
    if tr["reouvert"]:
        causes.append("position fermée à la main ; le bot l'a rouverte aussitôt (défaut de logique)")
    if tr["rouverte_par_bot"]:
        causes.insert(0, "position rouverte par le bot juste après une fermeture à la main (défaut de logique)")
        corrections.append("corrigé le 31 octobre 2026 : une position fermée hors du bot n'est plus rouverte")
        evitable.insert(0, "oui : logique")
    if q == "relance_bot":
        causes.insert(0, "bot relancé pendant le trade : il a fermé sa propre position (défaut de logique)")
        corrections.append("corrigé le 31 octobre 2026 : le trade est repris s'il est encore sur le compte")
        evitable.append("oui : logique")
    if (tr["depassement"] or 0) > 1:
        causes.append(f"entrée tardive : prix déjà à {tr['depassement']:.2f} largeur de bande au-delà du niveau")
        corrections.append("C1")
    if dist_vwap is not None and dist_vwap > 2:
        causes.append(f"entrée loin du VWAP : {dist_vwap:.1f} largeurs de bande" + (f", après {hausse30:+.0f} points en 30 minutes" if hausse30 is not None else ""))
        corrections.append("C7")
    if precedent is not None and precedent["sens"] == s and precedent["pts"] < 0:
        causes.append("piège du bruit : nouvelle entrée dans le même sens juste après une sortie perdante")
        corrections.append("C2")
        evitable.append("oui : C2 (adoptée le 1er novembre 2026) refuse ce trade")
    if abs(tr["delta"]) < 300:
        causes.append(f"delta faible ({tr['delta']:+d})")
        corrections.append("C3")
    if largeur and mfe == mfe and mfe >= largeur and pts <= mfe / 2:
        causes.append(f"profit rendu : jusqu'à {mfe:+.0f} points en cours, sorti à {pts:+.0f}")
        corrections.append("C4")
    if q in ("limite", "stop"):
        causes.append("coupé par " + ("la limite de perte du jour" if q == "limite" else "le stop") + " entre deux contrôles")
        if dist_sortie is not None and dist_sortie > capacite:
            causes.append(f"le niveau de sortie de la règle ({dist_sortie:.0f} points) était plus loin que la limite du jour ({capacite:.0f} points avec {taille} MNQ)")
            corrections.append("C6")
        else:
            corrections.append("C5")
    if duree <= 30 and pts < 0 and q in ("sortie", "limite", "stop") and "C2" not in corrections:
        causes.append(f"sorti en {duree} minutes : le prix est revenu dans la zone (bruit)")
    if not evitable:
        evitable.append("non avec ce que le bot savait : " + ("aucune correction testée ne tient sur 15 ans" if corrections else "perte normale de la stratégie"))
    return dict(tr, usd=usd, estimation=int(estimation.group(1)) if estimation else None, pts=pts, mfe=mfe, mae=mae,
                haut=haut, bas=bas, vwap=vw, niveau=niveau, largeur=largeur, dist_vwap=dist_vwap, hausse30=hausse30,
                dist_sortie=dist_sortie, capacite=capacite, causes=causes, corrections=corrections, evitable=evitable,
                modifies=modifies, duree=duree)


def effet_corrections(a, precedent):
    """Ce que chaque correction aurait fait à ce trade (approximation sur le journal et les minutes)."""
    eff = {}
    if (a["depassement"] or 0) > 1:
        eff["C1"] = "pas pris"
    if precedent is not None and precedent["sens"] == a["sens"] and precedent["pts"] < 0:
        eff["C2"] = "pas pris"
    if abs(a["delta"]) < 300:
        eff["C3"] = "pas pris"
    if a["largeur"] and a["mfe"] == a["mfe"] and a["mfe"] >= a["largeur"] and a["pts"] <= a["mfe"] / 2:
        eff["C4"] = "sorti plus tôt"
    if a["dist_sortie"]:
        n = min(a["taille"] or 1, math.floor(500 / (2 * a["dist_sortie"])))
        if n < (a["taille"] or 1):
            eff["C6"] = f"{n} MNQ au lieu de {a['taille']}"
    if a["dist_vwap"] is not None and a["dist_vwap"] > 2:
        eff["C7"] = "pas pris"
    return eff


def rapport(analyses, debut, fin):
    L = [f"# Revue de la semaine du {debut} au {fin} (bot 3 en 1, zone de bruit)", ""]
    pertes = [a for a in analyses if a["usd"] < 0]
    gains = [a for a in analyses if a["usd"] >= 0]
    tot = sum((a["estimation"] if a["estimation"] is not None else a["usd"]) for a in analyses)
    L += [f"- **Trades de zone :** {len(analyses)}, dont {len(gains)} gagnants et {len(pertes)} perdants.",
          f"- **Résultat estimé :** {tot:+,.0f} $ (prix du journal et des minutes du NQ, frais compris ; à la limite du jour, "
          "l'estimation du bot moins les trades d'avant le même jour). Le solde du compte fait foi.", ""]
    L += ["| Jour | Trade | Sortie | Points | $ estimés | Cause principale | Évitable ? |", "|---|---|---|---|---|---|---|"]
    for a in analyses:
        u = a["estimation"] if a["estimation"] is not None else a["usd"]
        quoi = "réouverture par le bot" if a["rouverte_par_bot"] else ("achat" if a["sens"] > 0 else "vente")
        L.append(f"| {a['jour']:%d/%m} | {quoi} {hm(a['minute'])} à {a['prix']:.2f} | "
                 f"{a['sortie']['quoi']} {a['sortie']['t']:%Hh%M} | {a['pts']:+.1f} | {u:+,.0f} | "
                 f"{a['causes'][0] if a['causes'] else ('—' if u >= 0 else 'perte normale')} | "
                 f"{'—' if u >= 0 else a['evitable'][0]} |")
    L += ["", "## Les pertes, une par une", ""]
    for a in pertes:
        u = a["estimation"] if a["estimation"] is not None else a["usd"]
        quoi = "réouverture par le bot de la " + ("vente" if a["sens"] < 0 else "position") if a["rouverte_par_bot"] else ("achat" if a["sens"] > 0 else "vente")
        L += [f"### {a['jour']:%d/%m}, {quoi} à {hm(a['minute'])} : {u:+,.0f} $", ""]
        c = [f"prix {a['prix']:.2f}, {a['taille']} MNQ"]
        if a["haut"] is not None:
            c.append(f"achat au-dessus de {a['haut']:.2f}, vente sous {a['bas']:.2f}, VWAP {a['vwap']:.2f}")
        c.append(f"delta 30 min {a['delta']:+d}")
        if a["depassement"] is not None:
            c.append(f"dépassement {a['depassement']:.2f} largeur de bande")
        if a["dist_vwap"] is not None:
            c.append(f"distance au VWAP {a['dist_vwap']:.1f} largeurs de bande")
        if a["hausse30"] is not None:
            c.append(f"mouvement des 30 minutes d'avant {a['hausse30']:+.0f} points dans le sens du trade")
        if a["niveau"] is not None:
            c.append(f"niveau de sortie {a['niveau']:.2f} ({a['dist_sortie']:.0f} points ; la limite du jour coupe à {a['capacite']:.0f} points)")
        c.append(f"en cours : au mieux {a['mfe']:+.0f} points, au pire {-a['mae']:+.0f} points")
        c.append(f"sortie : {a['sortie']['texte']} ({a['duree']} minutes après l'entrée)")
        c.append("réglages : " + ("zone d'origine" if not a["modifies"] else ", ".join(a["modifies"]).lower()))
        L += ["1. **Conditions exactes :** " + " ; ".join(c) + ".",
              "2. **Évitable ?** " + " ; ".join(a["evitable"]) + ".",
              "3. **Règle responsable ou filtre manquant :** " + ("; ".join(a["causes"]) if a["causes"] else "aucune : la règle a fait ce qu'elle doit") + ".",
              "4. **Correction précise :**"]
        cs = [x for x in a["corrections"]]
        if not cs:
            L.append("   - aucune : perte normale, la corriger ferait perdre plus sur 15 ans.")
        for x in cs:
            if x in CORRECTIONS:
                L.append(f"   - {x}, {CORRECTIONS[x][0]} : **{CORRECTIONS[x][1]}**.")
            else:
                L.append(f"   - {x}.")
        L.append("")
    L += ["## Ce que chaque correction aurait fait aux trades de la semaine", "",
          "Une correction qui retire plus de gains que de pertes ne doit pas être appliquée, même si elle évite une perte.", "",
          "| Correction | Pertes évitées ou réduites cette semaine | Gagnants coupés ou réduits cette semaine | Sur 15 ans |", "|---|---|---|---|"]
    for cle in CORRECTIONS:
        ev, gc = [], []
        for a in analyses:
            e = a["effets"].get(cle)
            if e:
                u = a["estimation"] if a["estimation"] is not None else a["usd"]
                (gc if u >= 0 else ev).append(f"{a['jour']:%d/%m} {hm(a['minute'])} ({u:+,.0f} $, {e})")
        if ev or gc:
            L.append(f"| {cle} | {', '.join(ev) or '—'} | {', '.join(gc) or '—'} | {CORRECTIONS[cle][1]} |")
    L += ["", "C5 (stop à la minute) n'est pas simulée ici : sur 15 ans, elle fait moins bien sur les 3 périodes.",
          "Gains sur 15 ans : 1 MNQ au prix d'aujourd'hui, frais fixes de 3 $ par aller-retour (audit/README.md).", ""]
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("journal")
    ap.add_argument("transactions")
    ap.add_argument("--debut")
    ap.add_argument("--fin")
    ap.add_argument("--limite", type=float, default=1000)
    ap.add_argument("--sortie")
    x = ap.parse_args()
    minutes = lire_minutes(x.transactions)
    debut = datetime.strptime(x.debut, "%Y-%m-%d").date() if x.debut else min(minutes)
    fin = datetime.strptime(x.fin, "%Y-%m-%d").date() if x.fin else max(minutes)
    jours = lire_journal(x.journal, debut, fin)
    analyses = []
    for j in sorted(jours):
        precedent, cumul = None, 0.0
        for tr in trades_du_jour(j, jours[j], minutes):
            a = analyser(tr, jours[j], minutes, x.limite, precedent)
            if a["estimation"] is not None:
                a["estimation"] -= cumul     # l'estimation de la limite du jour porte sur toute la journee
            cumul += a["estimation"] if a["estimation"] is not None else a["usd"]
            a["effets"] = {} if a["rouverte_par_bot"] else effet_corrections(a, precedent)
            analyses.append(a)
            precedent = a
    texte = rapport(analyses, debut, fin)
    if x.sortie:
        open(x.sortie, "w", encoding="utf-8").write(texte + "\n")
    print(texte)


if __name__ == "__main__":
    main()
