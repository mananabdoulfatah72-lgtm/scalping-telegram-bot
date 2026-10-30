#!/usr/bin/env python3
"""Machine de veille (flux/README.md, partie 8) : chaque soir de semaine, joue sur les nouvelles seances du NQ les
strategies candidates figees (S2b, ORB 5 min, cassure de la veille, Supertrend, pivots, les regles du radar, L2, et la
zone d'origine comme reference), tient leur journal depuis le debut du suivi, les mesure contre la barre fixee d'avance et
envoie le point sur Telegram. Aucun reglage n'est change par la machine : c'est le seul test que rien ne peut biaiser (l'avenir).

Lancer : python3 flux/veille.py <minutes NQ au format du robot (t,o,h,l,c,v,contrat)>
Variables : DEBUT_SUIVI (AAAA-MM-JJ, defaut 2026-10-30), TELEGRAM_TOKEN et CHAT_ID (facultatifs)."""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import challenge_ajouts as CA  # noqa: E402
import donnees as SD  # noqa: E402  (scalping/donnees.py)
import partie_f as F  # noqa: E402
import partie_g as G  # noqa: E402
import partie_h as H  # noqa: E402

DOSSIER = ICI / "veille"
DEBUT_SUIVI = pd.Timestamp(os.getenv("DEBUT_SUIVI", "2026-10-30"))
NOMS = {"S2b": "S2b cassure ratee", "H1": "ORB 5 min", "H5": "cassure de la veille", "H12": "Supertrend 10-3",
        "F3": "pivots R1/S1", "R1": "radar : achat 13 h 30 en haut du range",
        "R2": "radar : achat 13 h au-dessus de la veille", "L2": "L2 : contre le mouvement a 15 h 30 (gamma haut)",
        "ZONE": "zone d'origine (reference)"}
BARRE_TRADES, BARRE_T = 40, 2.54            # 40 seances avec trade, t >= 2,54 (Bonferroni unilateral 5 % pour 9)
PLACE_R1 = 0.8591989517211914               # radar/resultats/scan.txt : 5e quintile de la place a 13 h 30 (2011-2018)
D_HV_R2, EFF_R2 = 0.24112540781497965, 0.12363548576831819   # radar/resultats/protocole2 : 5es quintiles a 13 h
TICK = 0.25


def s2b(d):
    """S2b (flux/README.md, partie 2) sur les tableaux de scalping/donnees.minutes : gain de chaque seance en $ par MNQ au
    prix de reference (comme les autres), frais 1 point + un tick de glissement a l'entree et aux sorties au marche."""
    O, Hh, L, C = d["o"], d["h"], d["l"], d["c"]
    ok = d["complete"] & ~d["ech"]
    prec = d["prec_meme"]
    ech = float(d["pref"]) / O[:, 0]
    g = np.full(len(O), np.nan)
    for s in range(len(O)):
        p1 = prec[s]
        if not ok[s] or p1 < 0:
            continue
        h, l, c, o = Hh[s], L[s], C[s], O[s]
        niveaux = [(Hh[p1].max(), 1, 30), (L[p1].min(), -1, 30), (h[:60].max(), 1, 60), (l[:60].min(), -1, 60)]
        sig = []
        for Lv, haut, debut in niveaux:
            for b in range(debut, 331):
                if not ((h[b] >= Lv + TICK and c[b - 1] <= Lv) if haut == 1 else (l[b] <= Lv - TICK and c[b - 1] >= Lv)):
                    continue
                for f in range(b, min(b + 5, 330) + 1):
                    if (c[f] <= Lv - TICK) if haut == 1 else (c[f] >= Lv + TICK):
                        ext = h[b:f + 1].max() if haut == 1 else l[b:f + 1].min()
                        sig.append((f, -haut, ext + TICK if haut == 1 else ext - TICK))
                        break
                break
        tot, n, libre = 0.0, 0, 0
        for t, sens, st0 in sorted(sig):
            if t > 150 or t < libre:
                continue
            e = t + 1
            ent = o[e] + sens * TICK
            st = np.floor(min(st0, ent - 3) / TICK) * TICK if sens > 0 else np.ceil(max(st0, ent + 3) / TICK) * TICK
            R = abs(ent - st)
            if R > 0.0012 * ent:
                continue
            ob = ent + sens * 2 * R
            ob = np.ceil(ob / TICK) * TICK if sens > 0 else np.floor(ob / TICK) * TICK
            sortie, x = None, min(e + 59, 389)
            for m in range(e, min(e + 59, 389) + 1):
                if sens > 0:
                    if m > e and o[m] <= st: sortie, x = o[m] - TICK, m
                    elif l[m] <= st: sortie, x = st - TICK, m
                    elif h[m] >= ob + TICK: sortie, x = ob, m
                else:
                    if m > e and o[m] >= st: sortie, x = o[m] + TICK, m
                    elif h[m] >= st: sortie, x = st + TICK, m
                    elif l[m] <= ob - TICK: sortie, x = ob, m
                if sortie is not None:
                    break
            if sortie is None:
                sortie = c[x] - sens * TICK
            tot += sens * (sortie - ent) * float(d["pt"]) * ech[s] - 2.0
            n += 1
            libre = x
        if n:
            g[s] = tot
    return g


def r1(d):
    """Radar, seule survivante de la confirmation (radar/README.md, echouee au coffre 2023 - 2026) : a 13 h 30, si la
    derniere cloture est dans les 14 % du haut du range du jour, achat a l'ouverture de 13 h 30, vente a celle de
    15 h 30 ; $ par MNQ au prix de reference, frais 3 $ l'aller-retour (comme radar/scan.py)."""
    O, Hh, L, C = d["o"], d["h"], d["l"], d["c"]
    ok = d["complete"] & ~d["ech"]
    hi, lo = Hh[:, :240].max(1), L[:, :240].min(1)
    place = (C[:, 239] - lo) / np.where(hi > lo, hi - lo, np.nan)
    g = (O[:, 360] - O[:, 240]) * float(d["pref"]) / O[:, 0] * float(d["pt"]) - 3.0
    return np.where(ok & (place > PLACE_R1), g, np.nan)


def r2(d):
    """Radar, protocole 2 (echouee au coffre 2023 - 2026) : a 13 h, si le NQ est au-dessus du plus haut de la veille de
    plus de 0,241 range moyen (20 seances) et que son mouvement du jour est regulier (efficacite > 0,124), achat a
    l'ouverture de 13 h, vente a celle de 15 h."""
    O, Hh, L, C = d["o"], d["h"], d["l"], d["c"]
    ok = d["complete"] & ~d["ech"]
    rng = Hh.max(1) - L.min(1)
    a20 = pd.Series(np.where(d["complete"], rng, np.nan)).shift(1).rolling(20, min_periods=10).mean().values
    pm = d["prec_meme"]
    haut_veille = np.where(pm >= 0, Hh[np.maximum(pm, 0)].max(1), np.nan)
    dhv = (C[:, 209] - haut_veille) / np.where(a20 > 0, a20, np.nan)
    chemin = np.abs(np.diff(np.c_[O[:, :1], C], axis=1)).cumsum(1)[:, 209]
    eff = np.abs(C[:, 209] - O[:, 0]) / np.where(chemin > 0, chemin, np.nan)
    g = (O[:, 330] - O[:, 210]) * float(d["pref"]) / O[:, 0] * float(d["pt"]) - 3.0
    return np.where(ok & (dhv > D_HV_R2) & (eff > EFF_R2), g, np.nan)


def l2(d):
    """Partie 11 (flux/gamma_0dte.py) : gamma de la veille haut (rang >= 80 % sur 252 seances, donnees du radar) : a
    15 h 30, contre le mouvement depuis l'ouverture, sortie a 16 h."""
    sys.path.insert(0, str(ICI))
    import gamma_0dte as G
    O, C = d["o"], d["c"]
    ok = d["complete"] & ~d["ech"]
    jours = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
    r = G.gex().dropna()
    i = r.index.searchsorted(jours, side="left") - 1
    g = np.where(i >= 0, r.values[np.maximum(i, 0)], np.nan)
    g = np.where((jours - r.index[np.maximum(i, 0)]).days <= 7, g, np.nan)
    sens = -np.sign(C[:, 359] - O[:, 0])
    gain = sens * (C[:, 389] - O[:, 360]) * float(d["pref"]) / O[:, 0] * float(d["pt"]) - 3.0
    return np.where(ok & (g >= G.SEUIL) & (sens != 0), gain, np.nan)


def gains(d):
    jours = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
    out = {"S2b": s2b(d), "R1": r1(d), "R2": r2(d), "L2": l2(d)}
    h = H.toutes(d)
    out.update({"H1": h["H1"][0], "H5": h["H5"][0], "H12": h["H12"][0], "F3": F.toutes(d)["F3"][0]})
    _, _, _, _, tr = G.calcul(d)
    clo, _ = CA.chemins(d, CA.trades_zone(d, tr))
    z = clo[:, -1].copy()
    a = np.zeros(len(z), bool)
    for s, *_ in tr:
        a[s] = True
    z[~a] = np.nan
    out["ZONE"] = z
    return pd.DataFrame(out, index=jours)


def t_stat(x):
    x = np.asarray(x, float)
    s = x.std(ddof=1) if len(x) > 1 else 0.0
    return float(x.mean() / s * np.sqrt(len(x))) if s > 0 else 0.0


def main():
    d = SD.minutes("NQ", chemin=sys.argv[1], debut="2025-06-01")
    M = gains(d)
    ok = pd.Series(d["complete"] & ~d["ech"], index=M.index)
    suivi = M[(M.index >= DEBUT_SUIVI) & ok]
    DOSSIER.mkdir(parents=True, exist_ok=True)
    journal = suivi.stack(future_stack=True).rename("gain_dollars_par_mnq").reset_index()
    journal.columns = ["jour", "strategie", "gain_dollars_par_mnq"]
    journal.to_csv(DOSSIER / "journal.csv", index=False, float_format="%.2f")
    L = [f"# Machine de veille : suivi des stratégies candidates depuis le {DEBUT_SUIVI.date()}", "",
         f"Mise à jour avec les minutes du NQ jusqu'au {M.index[-1].date()} ({len(suivi)} séance(s) suivie(s)). $ pour 1 MNQ au "
         "prix de référence du projet (30 900 points), frais compris. Barre fixée d'avance pour parler d'une stratégie "
         f"qui marche : au moins {BARRE_TRADES} séances avec trade, gain moyen > 0, t ≥ {BARRE_T}.", "",
         "| Stratégie | Séances avec trade | Gagnantes | Total | Moyenne par séance jouée | t | Barre |", "|---|---|---|---|---|---|---|"]
    msg = [f"Veille du {M.index[-1].date()} (suivi depuis le {DEBUT_SUIVI.date()}, 1 MNQ) :"]
    for k, nom in NOMS.items():
        x = suivi[k].dropna()
        tz = t_stat(suivi[k].fillna(0)) if len(suivi) > 1 else 0.0
        franchie = len(x) >= BARRE_TRADES and x.mean() > 0 and tz >= BARRE_T
        etat = "FRANCHIE" if franchie else (f"{max(0, BARRE_TRADES - len(x))} séances manquent" if len(x) < BARRE_TRADES else "non")
        L.append(f"| {nom} | {len(x)} | {(x > 0).sum()} | {x.sum():+,.0f} $ | {x.mean() if len(x) else 0:+,.0f} $ | {tz:+.2f} | {etat} |")
        dernier = M[k].iloc[-1]
        msg.append(f"- {nom} : {'pas de trade' if np.isnan(dernier) else f'{dernier:+,.0f} $'} aujourd'hui ; total suivi {x.sum():+,.0f} $ ({len(x)} séances)")
    L += ["", "Dernière séance :", ""] + [f"- {m[2:]}" for m in msg[1:]]
    (DOSSIER / "TABLEAU.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    jeton, chat = os.getenv("TELEGRAM_TOKEN", ""), os.getenv("CHAT_ID", "")
    if jeton and chat:
        try:
            requests.post(f"https://api.telegram.org/bot{jeton}/sendMessage", data={"chat_id": chat, "text": "\n".join(msg)}, timeout=20)
        except Exception as e:
            print(f"Telegram : message non envoye ({type(e).__name__})")


if __name__ == "__main__":
    main()
