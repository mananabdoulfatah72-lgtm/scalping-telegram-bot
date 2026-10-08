#!/usr/bin/env python3
"""Realisme de l'ecart du week-end sur le dollar australien (README.md, vague 2) : entree a la premiere cotation du
comptant ou a 18 h (reouverture du 6A a la CME), frais de 1,5 / 3 / 5 pb. Ecrit realisme6.txt."""
import numpy as np
import pandas as pd

import machine5 as M5
import machine6 as M6

ICI = M6.ICI


def ecart(M, sortie, entree_18h, frais_pb):
    """Comblement des grands ecarts du week-end (ecart > mediane des 26 semaines d'avant). Renvoie les trades."""
    v = pd.date_range(M6.DEBUT, M6.FIN, freq="W-FRI")
    c = M6.cloture_avant(M, M5.heure_utc(v, M5.NY, "17:00"))
    depart = M5.heure_utc(v + pd.Timedelta(days=2), M5.NY, "18:00" if entree_18h else "15:00")
    o, io = M6.ouverture_apres(M, depart)
    g = o / c - 1
    sg = -np.sign(g)
    sg = np.where(np.abs(g) > M6.seuil_glissant(g, 26, 0.5, 13), sg, 0)
    lundi = v + pd.Timedelta(days=3)
    t_e = pd.DatetimeIndex(M.t0 + np.where(io >= 0, io, 0) * M5.PAS).where(io >= 0)
    d = M6.trades(M, t_e, M5.heure_utc(lundi, M5.NY, sortie), sg, lundi)
    d["r"] = d["r"] + M.cout(1.0) - frais_pb * 1e-4                     # frais remplaces
    d["heure_entree"] = t_e[np.isin(lundi, d["jour_local"])].tz_convert(M5.NY).strftime("%a %H:%M") if len(d) else []
    return d


def main():
    M = M5.Marche("audusd")
    L = ["Ecart du week-end, dollar australien, comblement des grands ecarts : realisme (descriptif)", "",
         "sortie | entree | frais (pb) | 2012-2022 : t / pb par trade / trades | 2023-2026 : t / pb par trade / somme (pb)"]
    decision = {}
    for sortie in ("03:00", "09:30"):
        for e18 in (False, True):
            for f in (1.5, 3.0, 5.0):
                d = ecart(M, sortie, e18, f)
                a = M6.periode(d, "2012-01-01", "2022-12-31")
                b = M6.periode(d, "2023-01-01", "2026-12-31")
                ja, jb = M6.par_jour(a), M6.par_jour(b)
                L.append(f"lundi {sortie} | {'18 h (6A)' if e18 else 'comptant'} | {f} | {M5.t_stat(ja):+.2f} / "
                         f"{ja.mean() * 1e4:+.2f} / {len(ja)} | {M5.t_stat(jb):+.2f} / {jb.mean() * 1e4:+.2f} / "
                         f"{jb.sum() * 1e4:+.0f}")
                if e18 and f == 3.0:
                    decision[sortie] = (M5.t_stat(ja) >= 2 and jb.sum() > 0, M5.t_stat(ja), jb.sum() * 1e4)
    d = ecart(M, "09:30", True, 3.0)
    h = d["heure_entree"].value_counts().head(3).to_dict()
    L += ["", f"heures d'entree les plus frequentes avec l'entree a 18 h : {h}", ""]
    for sortie, (ok, t, s) in decision.items():
        L.append(f"-> sortie lundi {sortie} : {'TRADABLE' if ok else 'NON TRADABLE'} sur la CME selon la regle"
                 f" (entree 18 h, 3 pb : t 2012-2022 {t:+.2f}, 2023-2026 {s:+.0f} pb)")
    (ICI / "realisme6.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
