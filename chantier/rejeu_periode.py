"""Les bots deja enregistres, rejoues sur les seances du challenge : du 13 octobre 2026 (premiere seance du challenge,
audit/README.md de la branche claude/optimistic-ptolemy-xs24ra) a la derniere seance des depots.

Les rejeux bruts sont dans resultats/rejeu/ (voir rejeu_periode.sh pour les refaire) :
- bot_*.txt : le Bot 3 en 1 rejoue par son propre moteur C# (Bot3en1.Replay), dans six reglages ;
- supertrend_trades.csv, W1_trades.csv, XGBoost_trades.csv : les moteurs C# Supertrend, W1 et XGBoost ;
- veille_journal.csv : la machine de veille (flux/veille.py), 11 strategies figees, $ par MNQ au prix de 30 900 points ;
- robot_*.csv : les journaux des comptes virtuels des robots de main (zone, tendance, melange, version 7).

Usage : python3 rejeu_periode.py <minutes du NQ (zone/robot/nq_1min.csv.gz de main)>   (ecrit resultats/rejeu_periode.txt)
"""
import json
import re
import sys

import numpy as np
import pandas as pd

import donnees as D

DEBUT, FIN, ENTRAINE = "2026-10-13", "2026-11-11", "2026-11-02"
DOS = D.ICI / "resultats/rejeu"
LIMITE, GLISSE, FRAIS = 1000.0, 1.0, 3.0          # limite du jour du bot, point perdu a une sortie forcee, $ par MNQ
LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b(?: (\d+)h(\d+))?(?: (\d+)h(\d+))?.*? a ([0-9.]+)")
n0 = lambda x: f"{x:+,.0f}".replace(",", " ")


def minutes(chemin):
    d = pd.read_csv(chemin, usecols=[0, 1, 2, 3, 4])
    d.columns = ["t", "o", "h", "l", "c"]
    d = d[(d.t.str[:10] >= "2026-10-01") & (d.t.str[:10] <= FIN)]
    m = d.t.str[11:13].astype(int) * 60 + d.t.str[14:16].astype(int) - 570
    d = d[(m >= 0) & (m < 390)].assign(m=m[(m >= 0) & (m < 390)])
    out = {}
    for j, g in d.groupby(d.t.str[:10]):
        H = np.full(390, np.nan); L = H.copy(); O = H.copy()
        H[g.m] = g.h; L[g.m] = g.l; O[g.m] = g.o
        out[j] = (pd.Series(O).bfill().ffill().to_numpy(), pd.Series(H).ffill().bfill().to_numpy(), pd.Series(L).ffill().bfill().to_numpy())
    return out


def trades_bot(f):
    """Trades de zone d'une sortie de Bot3en1.Replay : (jour, sens, debut du chemin, fin du chemin, entree, sortie).
    Le bot entre a la cloture de sa minute (chemin des la minute suivante), comme compte.zone_journal."""
    out, ouvert, rsi = [], None, []
    for l in open(f, encoding="utf-8"):
        if "RSI(2)" in l:
            g = re.match(r"^(\d{4}-\d{2}-\d{2}) RSI\(2\) : (achat|vente) .*? a ([0-9.]+)", l)
            if g:
                rsi.append((g.group(1), g.group(2), float(g.group(3))))
            continue
        g = LIGNE.match(l)
        if not g or "ecarte" in l:
            continue
        h, mi = int(g.group(5) or g.group(3)), int(g.group(6) or g.group(4))
        mm, px = h * 60 + mi - 570, float(g.group(7))
        if g.group(2) in ("achat", "vente"):
            ouvert = (g.group(1), 1 if g.group(2) == "achat" else -1, mm, px)
        elif ouvert:
            out.append((ouvert[0], ouvert[1], ouvert[2] + 1, min(389, max(ouvert[2], mm)), ouvert[3], px)); ouvert = None
    return out, rsi


def trades_csv(f, decale=0):
    """Trades des moteurs Supertrend, W1, XGBoost : entree a l'ouverture de m_in, sortie a l'ouverture de m_out."""
    d = pd.read_csv(f)
    return [(r.jour, int(r.sens), int(r.m_in), max(int(r.m_in), int(r.m_out) - 1), float(r.entree), float(r.sortie)) for r in d.itertuples()]


def journees(tr, Mn, taille=1.0, limite=None):
    """Resultat de chaque seance en $ (2 $ par point et par MNQ, 3 $ de frais par MNQ). Avec une limite : realise + latent
    du jour ; le trade en cours est coupe a la limite (1 point de glissement), plus rien ensuite (comme compte._journees)."""
    res = {}
    for j in sorted({t[0] for t in tr}):
        real, arret = 0.0, False
        for _, sens, a, b, e, x in [t for t in tr if t[0] == j]:
            if arret:
                break
            if limite is not None and j in Mn:
                _, H, L = Mn[j]
                for m in range(a, b + 1):
                    if real + sens * ((L[m] if sens > 0 else H[m]) - e) * 2 * taille <= -limite:
                        real = -limite - GLISSE * 2 * taille - FRAIS * taille; arret = True
                        break
                if arret:
                    break
            real += sens * (x - e) * 2 * taille - FRAIS * taille
            if limite is not None and real <= -limite:
                arret = True
        res[j] = real
    return pd.Series(res, dtype=float)


def bilan(serie, ntr, seances):
    s = serie[(serie.index >= DEBUT) & (serie.index <= FIN)]
    apres = s[s.index > ENTRAINE]
    return dict(total=float(s.sum()), trades=int(ntr), seances_jouees=int((s != 0).sum()), gagnantes=int((s > 0).sum()),
                pire=float(s.min()) if len(s) else 0.0, meilleure=float(s.max()) if len(s) else 0.0, apres_2nov=float(apres.sum()),
                seances=seances)


def principal(chemin):
    Mn = minutes(chemin)
    jours = sorted(j for j in Mn if DEBUT <= j <= FIN); res = {}
    dans = lambda tr: [t for t in tr if DEBUT <= t[0] <= FIN]
    L = [f"Les bots enregistrés, rejoués sur les séances du challenge : du {DEBUT} au {FIN} ({len(jours)} séances).",
         "Dollars réels pour 1 MNQ (2 $ par point), frais compris (3 $ par aller-retour). « À 4 MNQ » : avec la limite du jour de 1 000 $.", ""]
    # 1. le Bot 3 en 1, par son moteur C#
    BOT = [("actuel_sans_delta", "réglages actuels (zone d'origine + C2 + Q1), sans le filtre delta", FIN),
           ("origine_sans_delta", "zone d'origine sans filtre (réglages du début du challenge, sans le delta)", FIN),
           ("regle_26oct", "ta règle du 26 octobre (cassure + volume + une entrée, laisser courir)", FIN),
           ("regle_27oct", "ta règle du 27 octobre (la même + pas de sortie aux contrôles + stop 70 points)", FIN),
           ("actuel_avec_delta", "réglages actuels avec le filtre delta (données Rithmic : jusqu'au 30 octobre)", "2026-10-30"),
           ("origine_avec_delta", "zone d'origine avec le filtre delta (jusqu'au 30 octobre)", "2026-10-30")]
    L += ["1. Ton Bot 3 en 1, rejoué par son propre moteur C# (Bot3en1.Replay), partie zone :", ""]
    rsi_vu = None
    for cle, nom, fin in BOT:
        tr, rsi = trades_bot(DOS / f"bot_{cle}.txt"); tr = dans(tr)
        un = journees(tr, Mn); quatre = journees(tr, Mn, 4.0, LIMITE)
        b = bilan(un, len(tr), len([j for j in jours if j <= fin])); b["quatre_mnq"] = float(quatre.sum())
        b["pire_quatre"] = float(quatre.min()) if len(quatre) else 0.0; b["nom"] = nom; res[f"bot_{cle}"] = b
        L.append(f"   {nom} : {b['trades']} trades, {n0(b['total'])} $ à 1 MNQ, {n0(b['quatre_mnq'])} $ à 4 MNQ ; "
                 f"{b['gagnantes']} séances gagnantes sur {b['seances_jouees']} jouées ; pire séance {n0(b['pire'])} $ (à 4 MNQ : {n0(b['pire_quatre'])} $)"
                 + ("" if fin == FIN else f" ; période du {DEBUT} au {fin}"))
        if cle == "actuel_sans_delta":
            rsi_vu = rsi
    # RSI(2) : achat puis vente, tenu la nuit
    g, ouv = [], None
    for j, sens, px in rsi_vu:
        if sens == "achat":
            ouv = (j, px)
        elif ouv:
            g.append((ouv[0], j, (px - ouv[1]) * 2 - FRAIS)); ouv = None
    res["rsi2"] = dict(total=float(sum(x[2] for x in g)), trades=len(g), detail=g)
    L += ["", f"   RSI(2), le second moteur du bot (tenu la nuit, décoché chez Bulenox) : {len(g)} trades, {n0(res['rsi2']['total'])} $ à 1 MNQ "
          f"({' ; '.join(f'{a} → {b} : {n0(x)} $' for a, b, x in g)}).", ""]
    # 2. Supertrend, W1, XGBoost (moteurs C#)
    L += ["2. Les autres bots C# du dépôt (rejoués par leur moteur) :", ""]
    for cle, nom, ml in (("supertrend", "Supertrend NQ (10-3, bougies de 5 minutes)", False), ("W1", "W1 (Supertrend trié par un modèle)", True),
                         ("XGBoost", "XGBoost NQ (modèle)", True)):
        tr = dans(trades_csv(DOS / f"{cle}_trades.csv")); un = journees(tr, Mn); quatre = journees(tr, Mn, 4.0, LIMITE)
        b = bilan(un, len(tr), len(jours)); b["quatre_mnq"] = float(quatre.sum()); b["nom"] = nom; b["modele"] = ml; res[cle] = b
        L.append(f"   {nom} : {b['trades']} trades, {n0(b['total'])} $ à 1 MNQ, {n0(b['quatre_mnq'])} $ à 4 MNQ ; {b['gagnantes']} séances gagnantes sur "
                 f"{b['seances_jouees']} ; pire séance {n0(b['pire'])} $"
                 + (f" ; modèle entraîné jusqu'au {ENTRAINE} : seulement {n0(b['apres_2nov'])} $ sur les 7 séances d'après (le reste est dans l'entraînement)" if ml else ""))
    # 3. la machine de veille (flux/veille.py)
    v = pd.read_csv(DOS / "veille_journal.csv"); v = v[(v.jour >= DEBUT) & (v.jour <= FIN)].dropna()
    noms = {"S2b": "S2b cassure ratée", "H1": "ORB 5 minutes", "H5": "cassure de la veille", "H12": "Supertrend 10-3 (veille)",
            "F3": "pivots R1/S1", "R1": "radar : achat 13 h 30 en haut du range", "R2": "radar : achat 13 h au-dessus de la veille",
            "L2": "L2 : contre le mouvement à 15 h 30", "W1i": "W1i : lundi après un week-end bitcoin négatif",
            "MUR": "murs d'options du NDX", "ZONE": "zone d'origine (référence de la veille)"}
    L += ["", "3. Les stratégies figées de la machine de veille (flux/veille.py), converties au prix du jour :", ""]
    for k, nom in noms.items():
        x = v[v.strategie == k]
        reel = [(g + FRAIS) * Mn[j][0][0] / 30900.0 - FRAIS for j, g in zip(x.jour, x.gain_dollars_par_mnq) if j in Mn]
        s = pd.Series(reel, index=[j for j in x.jour if j in Mn], dtype=float)
        b = bilan(s, len(s), len(jours)); b["nom"] = nom; res[f"veille_{k}"] = b
        L.append(f"   {nom} : {b['seances_jouees']} séances jouées, {n0(b['total'])} $ à 1 MNQ, {b['gagnantes']} gagnantes, pire séance {n0(b['pire'])} $")
    # 4. les robots virtuels de main
    L += ["", "4. Les robots virtuels de main (leur propre compte de 50 000 $, mis à jour chaque soir par GitHub Actions) :", ""]
    for cle, nom, col in (("zone", "Robot zone : la zone seule (1 MNQ)", "gain_1_mnq"), ("zone", "Robot zone : le RSI(2) (1 MNQ, valeur chaque soir)", "gain_rsi2_1_mnq"),
                          ("zone", "Robot zone : le rebond (1 MNQ)", "gain_rebond_1_mnq"), ("zone", "Robot zone : son compte de challenge Phidias", "gain"),
                          ("tendance", "Tendance seule (19 marchés à terme, garde la nuit)", "gain"),
                          ("melange", "Mélange tendance + achat", "gain"), ("version7", "Version 7 (5 actions de la technologie)", "gain")):
        d = pd.read_csv(DOS / f"robot_{cle}.csv"); d = d[(d.date >= DEBUT) & (d.date <= FIN)]
        s = pd.Series(d[col].to_numpy(float), index=d.date)
        b = bilan(s, int((s != 0).sum()), len(d)); b["nom"] = nom; res[f"robot_{cle}_{col}"] = b
        L.append(f"   {nom} : {n0(b['total'])} $ sur la période ({b['seances']} séances, pire jour {n0(b['pire'])} $)")
    L += ["", "Non rejouable ici : FluxNQ (il lui faut les transactions Rithmic, absentes du dépôt après le 30 octobre), et le filtre VIX du",
          "bot après le 30 octobre (VIX absent du dépôt après cette date ; jusque-là il n'aurait coupé aucune séance)."]
    (D.ICI / "resultats/rejeu_periode.txt").write_text("\n".join(L) + "\n")
    json.dump(res, open(D.ICI / "resultats/rejeu_periode.json", "w"), indent=1, ensure_ascii=False, default=str)
    print("\n".join(L))


if __name__ == "__main__":
    principal(sys.argv[1])
