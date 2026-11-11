"""Rapport du matin : revue des trades de la veille, a partir du journal du bot et des minutes du NQ.

    python3 rapport_matin.py --journal journal.txt [--jour 2026-11-10] [--taille 4] [--solde 51800] [--plus-haut 51800]
                             [--minutes ../../zone/robot/nq_1min.csv.gz] [--sans-trade 0] [--sortie rapport.md] [--telegram]

Le journal est celui du Bot 3 en 1 (lignes « AAAA-MM-JJ achat 10h30 a 30123.50 ... » puis « ... sortie 11h00 a 30150.25 »).
--solde et --plus-haut sont ceux du compte AVANT la seance revue. Avec --telegram, le rapport part sur Telegram si les
variables TELEGRAM_TOKEN et CHAT_ID existent. Dependances : aucune (numpy seulement pour l'etat du marche).
"""
import argparse
import csv
import gzip
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path

from garde import Garde

LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b(?: (\d+)h(\d+))?(?: (\d+)h(\d+))?.*? a ([0-9.]+)")
FRAIS = 3.0          # $ par aller-retour et par MNQ
POINT = 2.0          # $ par point et par MNQ
ICI = Path(__file__).resolve().parent


def lire_journal(chemin):
    """Trades du journal : dict par jour -> liste de (sens, minute d'entree, prix, minute de sortie, prix, motif)."""
    jours, ouvert = {}, None
    for l in Path(chemin).read_text(encoding="utf-8", errors="replace").splitlines():
        g = LIGNE.match(l)
        if not g or "ecarte" in l or "RSI" in l:
            continue
        h, mi = int(g.group(5) or g.group(3)), int(g.group(6) or g.group(4))
        mm, px = h * 60 + mi - 570, float(g.group(7))
        if g.group(2) in ("achat", "vente"):
            ouvert = (g.group(1), 1 if g.group(2) == "achat" else -1, mm, px)
        elif ouvert:
            jours.setdefault(ouvert[0], []).append((ouvert[1], ouvert[2], ouvert[3], max(ouvert[2], mm), px, g.group(2)))
            ouvert = None
    return jours


def lire_minutes(chemin):
    """Minutes du NQ : dict jour -> {minute depuis 9 h 30 : (o, h, l, c)}."""
    out = {}
    ouvrir = gzip.open if str(chemin).endswith(".gz") else open
    with ouvrir(chemin, "rt") as f:
        for r in csv.DictReader(f):
            j, hm = r["t"][:10], r["t"][11:16]
            m = int(hm[:2]) * 60 + int(hm[3:]) - 570
            if 0 <= m < 390:
                out.setdefault(j, {})[m] = (float(r["o"]), float(r["h"]), float(r["l"]), float(r["c"]))
    return out


def n(x, d=0, signe=False):
    """Nombre avec une espace pour les milliers."""
    return f"{x:{'+' if signe else ''},.{d}f}".replace(",", " ")


def heure(m):
    return f"{(570 + m) // 60} h {(570 + m) % 60:02d}"


def etat_du_marche(minutes):
    """Etat pour la prochaine seance (sans le VIX : la courbe inversee n'est pas testee ici)."""
    try:
        import numpy as np
        from regime import etats
    except Exception:
        return None
    cl = [minutes[j][389][3] for j in sorted(minutes) if 0 in minutes[j] and 389 in minutes[j] and len(minutes[j]) >= 370]
    if len(cl) < 274:
        return None
    nan = np.full(len(cl) + 1, np.nan)
    return etats(np.r_[cl, cl[-1]], nan, nan)[-1]


def revue(journal, minutes, jour, taille, solde, plus_haut, sans_trade=0, fed=()):
    trades = journal.get(jour, []); mn = minutes.get(jour, {})
    g = Garde(solde=solde, plus_haut=plus_haut, sommet=max(solde, plus_haut), jours_sans_trade=sans_trade)
    L = [f"# Rapport du matin : séance du {jour}", "",
         f"Compte avant la séance : solde {n(solde)} $, plancher {n(g.plancher)} $, marge {n(solde - g.plancher)} $. Taille : {taille} MNQ.", ""]
    ecarts, total, creux_jour, cumul = [], 0.0, 0.0, 0.0
    if not trades:
        L += ["Aucun trade.", ""]
    for k, (sens, m0, e, m1, x, motif) in enumerate(trades, 1):
        pts = sens * (x - e); gain = pts * POINT * taille - FRAIS * taille
        chemin = [mn[m] for m in range(m0 + 1, m1 + 1) if m in mn]
        pire = min([sens * ((b[2] if sens > 0 else b[1]) - e) for b in chemin], default=min(pts, 0.0))
        meilleur = max([sens * ((b[1] if sens > 0 else b[2]) - e) for b in chemin], default=max(pts, 0.0))
        creux_jour = min(creux_jour, cumul + pire * POINT * taille); cumul += gain; total += gain
        L += [f"## Trade {k} : {'achat' if sens > 0 else 'vente'} à {heure(m0)} à {n(e, 2)}, sortie à {heure(m1)} à {n(x, 2)} ({motif})",
              f"- Résultat : {pts:+.2f} points, **{n(gain, signe=True)} $**.",
              f"- Pire moment : {pire:+.1f} points ({n(pire * POINT * taille, signe=True)} $). Meilleur moment : {meilleur:+.1f} points ({n(meilleur * POINT * taille, signe=True)} $)."]
        if m0 % 30 != 0:
            ecarts.append(f"trade {k} : entrée à {heure(m0)}, hors d'un contrôle de 30 minutes (entrée à la main ou réglage modifié ?)")
        if meilleur * POINT * taille >= 300 and gain <= 0:
            ecarts.append(f"trade {k} : il a été en gain de {n(meilleur * POINT * taille)} $ et finit à {n(gain, signe=True)} $ (gain rendu : c'est la règle de sortie de la zone, pas une faute)")
        if mn and not chemin:
            ecarts.append(f"trade {k} : pas de minutes entre l'entrée et la sortie dans le fichier (prix non vérifiés)")
        elif chemin:
            b = mn.get(m0)
            if b and not (b[2] - 0.25 <= e <= b[1] + 0.25):
                ecarts.append(f"trade {k} : prix d'entrée {n(e, 2)} hors de la minute de {heure(m0)} ({n(b[2], 2)} - {n(b[1], 2)}) : glissement ou heure décalée")
        L.append("")
    if jour in fed and trades:
        ecarts.append("trade un jour d'annonce de la Fed (le bot ne doit pas trader ce jour-là)")
    if creux_jour <= -g.limite_bot:
        ecarts.append(f"la limite du jour ({n(g.limite_bot)} $) a été touchée : pire moment de la journée {n(creux_jour, signe=True)} $")
    if taille > g.taille_max:
        ecarts.append(f"taille de {taille} MNQ au-dessus du maximum du garde ({g.taille_max})")
    if solde - g.plancher < g.limite_bot and trades:
        ecarts.append(f"la marge avant la séance ({n(solde - g.plancher)} $) était plus petite que la limite du jour : une perte normale pouvait coûter le compte")
    alertes = g.fin_de_journee(total, bool(trades))
    L += ["## Bilan de la journée",
          f"- {len(trades)} trade(s), résultat **{n(total, signe=True)} $**, pire moment {n(creux_jour, signe=True)} $.",
          f"- Compte après la séance : solde {n(g.solde)} $, plus haut de fin de journée {n(g.plus_haut)} $, plancher {n(g.plancher)} $, **marge {n(g.solde - g.plancher)} $**.",
          f"- Jours de trading de suite sans trade : {g.jours_sans_trade}.", "",
          "## Ce qui s'écarte des règles"] + ([f"- {x}" for x in ecarts] or ["- Rien : le bot a suivi ses règles."])
    L += ["", "## Pour la prochaine séance"] + ([f"- {x}" for x in alertes] or ["- Pas d'alerte sur le compte."])
    rep = g.verifier(taille, 0, "10:30")
    L.append(f"- Taille permise par le garde : {rep.taille} MNQ" + (f" ({' ; '.join(rep.raisons)})" if rep.raisons else "") + ".")
    et = etat_du_marche(minutes)
    if et:
        L.append(f"- État du marché (sans le VIX) : {et}. Affiché pour information : aucun régime n'a prouvé qu'il fallait changer de stratégie.")
    texte = "\n".join(L)
    return texte, dict(jour=jour, trades=len(trades), resultat=total, creux=creux_jour, solde=g.solde, plancher=g.plancher, marge=g.solde - g.plancher,
                       ecarts=ecarts, alertes=alertes)


def telegram(texte):
    tok, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("CHAT_ID")
    if not (tok and chat):
        return False
    d = urllib.parse.urlencode({"chat_id": chat, "text": texte[:3900]}).encode()
    urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=d), timeout=20)
    return True


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--journal", required=True); a.add_argument("--jour"); a.add_argument("--taille", type=int, default=1)
    a.add_argument("--solde", type=float, default=50000.0); a.add_argument("--plus-haut", type=float, default=None)
    a.add_argument("--minutes", default=str(ICI.parent.parent / "zone/robot/nq_1min.csv.gz")); a.add_argument("--sans-trade", type=int, default=0)
    a.add_argument("--fed", default=None, help="fichier des jours de la Fed, une date par ligne"); a.add_argument("--sortie"); a.add_argument("--telegram", action="store_true")
    o = a.parse_args()
    J = lire_journal(o.journal); M = lire_minutes(o.minutes)
    jour = o.jour or max(set(J) | set(M))
    fed = {l.strip() for l in open(o.fed) if l.strip() and not l.startswith("#")} if o.fed else set()
    texte, resume = revue(J, M, jour, o.taille, o.solde, o.plus_haut if o.plus_haut is not None else max(o.solde, 50000.0), o.sans_trade, fed)
    print(texte)
    if o.sortie:
        Path(o.sortie).write_text(texte + "\n", encoding="utf-8"); Path(o.sortie).with_suffix(".json").write_text(json.dumps(resume, ensure_ascii=False, indent=1))
    if o.telegram:
        print("\nTelegram :", "envoyé" if telegram(texte) else "TELEGRAM_TOKEN ou CHAT_ID absent, rien envoyé")
