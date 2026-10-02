#!/usr/bin/env python3
"""Filtre H1, version Alpaca (README.md) : delta du QQQ (regle du tick) a la place du delta du NQ.
Etape 1, validation sur avril - septembre 2026 contre le vrai delta du NQ (orderflow/donnees) : meme signe dans au moins
85 % des 300 fenetres de controle et meme decision que le vrai filtre dans au moins 90 % des 99 trades de zone.
Etape 2, test sur les trades de zone de 2016 a mars 2026 : confirme si t >= 2 (Welch) et zone filtree > zone seule,
seulement si la validation est reussie (sinon descriptif). Ecrit resultat_alpaca.txt et resultat_alpaca.json."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "orderflow"))
DA = ICI / "donnees_alpaca"
PT = 2.0


def welch(x, y):
    return float((x.mean() - y.mean()) / np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))) if len(x) > 1 and len(y) > 1 else float("nan")


def delta_qqq(minutes, jour, m):
    """Achats - ventes du QQQ sur les minutes m - 29 a m (fenetre du filtre) ; None si aucune transaction."""
    g = minutes.get(jour)
    if g is None:
        return None
    w = g[(g["minute"] >= m - 29) & (g["minute"] <= m)]
    return float(w["achats"].sum() - w["ventes"].sum()) if len(w) and w["transactions"].sum() > 0 else None


def main():
    import outils as O
    v = pd.read_csv(DA / "validation.csv.gz")
    mv = {j: g for j, g in v.groupby("jour")}
    zone = pd.read_csv(ICI.parent / "orderflow" / "zone_avril_septembre_2026.csv")
    controle = pd.read_csv(DA / "controle.csv")
    S = O.Seances()
    L = ["Filtre H1, version Alpaca : delta du QQQ (regle du tick) a la place du delta du NQ.", "",
         "Etape 1 : validation sur avril - septembre 2026, contre le vrai delta du NQ"]
    # fenetres de controle : signe du delta du QQQ contre le signe du vrai delta du NQ
    accords = []
    for r in controle.itertuples():
        d = S.jours.get_indexer([pd.Timestamp(r.jour)])[0]
        q = delta_qqq(mv, r.jour, r.minute)
        if d < 0 or q is None or q == 0:
            continue
        fin = (r.minute + 1) * 60
        vrai = S.achat[d, fin - 1800:fin].sum() - S.vente[d, fin - 1800:fin].sum()
        if vrai != 0:
            accords.append(np.sign(q) == np.sign(vrai))
    a1 = float(np.mean(accords)) if accords else float("nan")
    # 99 trades de zone : meme decision que le vrai filtre ?
    dec = []
    for r in zone.itertuples():
        q = delta_qqq(mv, r.jour, r.minute)
        dec.append(None if q is None else bool(np.sign(q) == r.sens))
    zone["garde_qqq"] = dec
    z = zone.dropna(subset=["garde_qqq"])
    a2 = float((z["garde_qqq"].astype(bool) == z["garde"].astype(bool)).mean()) if len(z) else float("nan")
    valide = bool(a1 >= 0.85 and a2 >= 0.90)
    L += [f"- meme signe que le vrai delta du NQ : {a1:.1%} sur {len(accords)} fenetres de controle (seuil 85 %)",
          f"- meme decision que le vrai filtre : {a2:.1%} sur {len(z)} trades de zone (seuil 90 %)",
          f"-> remplacant {'ACCEPTE : le test decide' if valide else 'REFUSE : le test est seulement descriptif'}", ""]
    # etape 2 : test 2016 - mars 2026
    t = pd.read_csv(ICI / "trades_zone.csv")
    t = t[t["jour"] >= "2016-01-01"].reset_index(drop=True)
    te = pd.read_csv(DA / "test.csv.gz")
    mt = {j: g for j, g in te.groupby("jour")}
    q = [delta_qqq(mt, r.jour, r.minute) for r in t.itertuples()]
    t["mesure"] = [x is not None for x in q]
    t["garde"] = [x is not None and np.sign(x) == s for x, s in zip(q, t["sens"])]
    m = t[t["mesure"]]
    a, b = m["points"][m["garde"]], m["points"][~m["garde"]]
    tw = welch(a, b)
    ok = bool(valide and tw >= 2 and a.sum() > m["points"].sum())
    L += [f"Etape 2 : test sur {len(m)} trades de zone mesures ({len(t) - len(m)} sans transaction QQQ) du {m['jour'].min()} au {m['jour'].max()}",
          f"- gardes : {len(a)} trades a {a.mean():+.2f} pt ; ecartes : {len(b)} ({len(b) / len(m):.0%}) a {b.mean():+.2f} pt",
          f"- ecart {a.mean() - b.mean():+.2f} pt, t {tw:+.2f}",
          f"- zone seule {m['points'].sum():+,.0f} pt ({PT * m['points'].sum():+,.0f} $ pour 1 MNQ) ; zone filtree {a.sum():+,.0f} pt"
          f" ({PT * a.sum():+,.0f} $)",
          f"-> {'CONFIRME' if ok else ('NON CONFIRME' if valide else 'descriptif (remplacant refuse)')}", "",
          "Annee par annee (points par trade) : annee | trades | gardes | ecartes (nombre) | zone seule | zone filtree"]
    an = []
    for y, g in m.groupby(m["jour"].str[:4]):
        x, w = g["points"][g["garde"]], g["points"][~g["garde"]]
        an.append({"annee": y, "trades": len(g), "gardes": round(float(x.mean()), 1), "ecartes": round(float(w.mean()), 1) if len(w) else None,
                   "n_ecartes": len(w), "zone": round(float(g["points"].sum())), "filtree": round(float(x.sum()))})
        L.append(f"{y} | {len(g)} | {x.mean():+.1f} | {w.mean() if len(w) else float('nan'):+.1f} ({len(w)}) | {g['points'].sum():+.0f} | {x.sum():+.0f}")
    mieux = sum(1 for x in an if x["filtree"] > x["zone"])
    L.append(f"Annees ou la zone filtree fait mieux : {mieux} sur {len(an)}")
    res = {"validation": {"accord_signe": a1, "fenetres": len(accords), "accord_decision": a2, "trades": len(z), "valide": valide},
           "test": {"trades": len(m), "gardes": len(a), "ecartes": len(b), "points_gardes": float(a.mean()), "points_ecartes": float(b.mean()),
                    "t": tw, "zone_seule": float(m["points"].sum()), "zone_filtree": float(a.sum()), "confirme": ok},
           "par_annee": an, "annees_mieux": mieux}
    (ICI / "resultat_alpaca.txt").write_text("\n".join(L) + "\n")
    (ICI / "resultat_alpaca.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
