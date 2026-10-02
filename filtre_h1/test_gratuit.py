#!/usr/bin/env python3
"""Test gratuit du filtre H1 (README.md, « version gratuite ») : sur les 3 465 trades de zone de 2011 a mars 2026, le
delta des 30 minutes est remplace par l'approximation P4 (mouvement du prix sur la fenetre), choisie sur avril -
septembre 2026 pour sa ressemblance au vrai delta. P1 a P3 : descriptif. Ecrit test_gratuit.txt et test_gratuit.json."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
PT = 2.0


def welch(x, y):
    return float((x.mean() - y.mean()) / np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))) if len(x) > 1 and len(y) > 1 else float("nan")


def main():
    t = pd.read_csv(ICI / "trades_zone.csv")
    m = pd.read_csv(ICI.parent / "intraday" / "donnees" / "nasdaq100_1min.csv.gz")
    m = m[m["t"].str[:10] <= "2026-03-31"]
    m["jour"] = m["t"].str[:10]
    m["minute"] = m["t"].str[11:13].astype(int) * 60 + m["t"].str[14:16].astype(int) - 570
    m = m[(m["minute"] >= 0) & (m["minute"] < 390)]
    par_jour = {j: g.set_index("minute").reindex(range(390)).ffill() for j, g in m.groupby("jour")}
    P = {k: [] for k in ("P4", "P1", "P2", "P3")}
    for r in t.itertuples():
        g = par_jour[r.jour]
        o, h, l, c, v = (g[x].to_numpy(float) for x in "ohlcv")
        cp = np.r_[o[0], c[:-1]]
        w = slice(r.minute - 29, r.minute + 1)
        rng = np.where(h[w] > l[w], h[w] - l[w], np.nan)
        P["P4"].append(c[r.minute] - cp[r.minute - 29])
        P["P1"].append(np.nansum(v[w] * np.sign(c[w] - o[w])))
        P["P2"].append(np.nansum(v[w] * (2 * c[w] - h[w] - l[w]) / rng))
        P["P3"].append(np.nansum(v[w] * np.sign(c[w] - cp[w])))
    res, L = {}, [f"Test gratuit du filtre H1 : {len(t)} trades de zone du {t['jour'].iloc[0]} au {t['jour'].iloc[-1]} (frais du robot compris).",
                  "Gain d'un trade en points de NQ ; 1 point = 2 $ pour 1 MNQ.", ""]
    for k, x in P.items():
        garde = np.sign(np.asarray(x)) == t["sens"].to_numpy()
        a, b = t["points"][garde], t["points"][~garde]
        tw = welch(a, b)
        ok = bool(tw >= 2 and a.sum() > t["points"].sum())
        res[k] = {"gardes": int(garde.sum()), "ecartes": int((~garde).sum()), "points_gardes": round(float(a.mean()), 2),
                  "points_ecartes": round(float(b.mean()), 2), "t": round(tw, 2), "zone_seule": round(float(t["points"].sum()), 1),
                  "zone_filtree": round(float(a.sum()), 1), "confirme": ok if k == "P4" else None}
        L.append(f"{k}{' (test, decision)' if k == 'P4' else ' (descriptif)'} : gardes {garde.sum()} trades a {a.mean():+.2f} pt ; ecartes"
                 f" {(~garde).sum()} ({(~garde).mean():.0%}) a {b.mean():+.2f} pt ; ecart {a.mean() - b.mean():+.2f} pt, t {tw:+.2f} ;"
                 f" zone seule {t['points'].sum():+,.0f} pt ({PT * t['points'].sum():+,.0f} $), filtree {a.sum():+,.0f} pt"
                 f" ({PT * a.sum():+,.0f} $)" + (f" -> {'CONFIRME' if ok else 'NON CONFIRME'}" if k == "P4" else ""))
        if k == "P4":
            t["garde"] = garde
    L += ["", "P4 annee par annee (points par trade) :", "annee | trades | gardes | ecartes | ecart | zone seule | zone filtree"]
    an = []
    for a_, g in t.groupby(t["jour"].str[:4]):
        x, y = g["points"][g["garde"]], g["points"][~g["garde"]]
        an.append({"annee": a_, "trades": len(g), "gardes": round(float(x.mean()), 1), "ecartes": round(float(y.mean()), 1) if len(y) else None,
                   "zone": round(float(g["points"].sum()), 0), "filtree": round(float(x.sum()), 0)})
        L.append(f"{a_} | {len(g)} | {x.mean():+.1f} | {y.mean() if len(y) else float('nan'):+.1f} ({len(y)}) | {x.mean() - y.mean():+.1f} |"
                 f" {g['points'].sum():+.0f} | {x.sum():+.0f}")
    mieux = sum(1 for x in an if x["filtree"] > x["zone"])
    L.append(f"Annees ou la zone filtree fait mieux que la zone seule : {mieux} sur {len(an)}")
    res["par_annee"], res["annees_mieux"] = an, mieux
    (ICI / "test_gratuit.txt").write_text("\n".join(L) + "\n")
    (ICI / "test_gratuit.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
    print("\n".join(L))


if __name__ == "__main__":
    main()
