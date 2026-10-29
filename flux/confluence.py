#!/usr/bin/env python3
"""Bot FluxNQ (flux/README.md) : C1 (confluence) sans la condition du DOM sur les seances Databento (descriptif), et
fichiers de reference pour le rejeu C# (minutes, profils, trades attendus de S1, S2, S2b et C1 sans DOM).

Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/confluence.py [dossier de sortie du rejeu]"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import donnees as D
import reglages as R
import systeme as Y

ICI = Path(__file__).resolve().parent
TICK = 0.25


def profils(jours):
    """Profil de volume (achats + ventes par prix) de chaque seance Databento, depuis le footprint."""
    f = pd.concat([pd.read_csv(p) for p in sorted(D.OF.glob("nq_footprint_*.csv.gz"))], ignore_index=True)
    f = f.drop_duplicates(["m", "prix"])
    m = pd.to_datetime(f["m"])
    jour = m.dt.normalize()
    minute = ((m - jour).dt.total_seconds() // 60 - 570).astype(int)
    f = f[(minute >= 0) & (minute < D.NM) & jour.isin(jours)].assign(jour=jour)
    f["v"] = f["achat"] + f["vente"]
    return {j: g.groupby("prix")["v"].sum() for j, g in f.groupby("jour")}


def zone_valeur(p):
    """POC (le plus bas en cas d'egalite), VAL, VAH : expansion d'un tick a la fois du cote le plus fort (au-dessus en
    cas d'egalite) jusqu'a 70 % du volume."""
    k = np.round(p.index.to_numpy() / TICK).astype(np.int64)
    grille = np.arange(k.min(), k.max() + 1)
    vol = np.zeros(len(grille))
    vol[k - k.min()] = p.to_numpy()
    poc = int(np.argmax(vol))
    lo = hi = poc
    acc, tot = vol[poc], vol.sum()
    while acc < 0.7 * tot:
        up = vol[hi + 1] if hi + 1 < len(vol) else -1.0
        dn = vol[lo - 1] if lo - 1 >= 0 else -1.0
        if up >= dn:
            hi += 1
            acc += up
        else:
            lo -= 1
            acc += dn
    return grille[poc] * TICK, grille[lo] * TICK, grille[hi] * TICK


def seuils_fp(m, d):
    """Quantile 75 des ventes aux deux prix les plus bas et des achats aux deux plus hauts, 5 seances d'avant."""
    fb, fh = m["ventes_bas2"][d - 5:d, 30:].ravel(), m["achats_haut2"][d - 5:d, 30:].ravel()
    if d < 5 or not (np.isfinite(fb).all() and np.isfinite(fh).all()):
        return np.nan, np.nan
    return np.percentile(fb, 75), np.percentile(fh, 75)


def signaux_c1(m, X, d, VA, sigv):
    """Signaux de C1 sans la condition du DOM (la condition 4 est ajoutee en direct par le bot)."""
    if d == 0 or VA.get(d - 1) is None or not np.isfinite(m["ventes_bas2"][d]).all():
        return []
    fb75, fh75 = seuils_fp(m, d)
    if not np.isfinite(fb75):
        return []
    poc, val, vah = VA[d - 1]
    pdh, pdl = m["h"][d - 1].max(), m["l"][d - 1].min()
    h, l, c = m["h"][d], m["l"][d], m["c"][d]
    out = []
    for t in range(Y.DEBUT, Y.FIN + 1):
        vw, sv = X["vwap"][d, t], sigv[d, t]
        delta = X["delta"][d, t]
        bas = [pdl, val, poc, vah, vw - sv]
        haut = [pdh, vah, poc, val, vw + sv]
        if delta < 0 and m["ventes_bas2"][d, t] >= fb75 and any(
                l[t] <= L + 2 * TICK and l[t] >= L - 8 * TICK and c[t] >= L and c[t - 1] > L + 2 * TICK for L in bas):
            out.append((t, 1, l[t] - 2 * TICK))
        elif delta > 0 and m["achats_haut2"][d, t] >= fh75 and any(
                h[t] >= L - 2 * TICK and h[t] <= L + 8 * TICK and c[t] <= L and c[t - 1] < L - 2 * TICK for L in haut):
            out.append((t, -1, h[t] + 2 * TICK))
    return out


def sigma_v(m, X):
    typ = (m["h"] + m["l"] + m["c"]) / 3
    v = X["v"]
    cv = np.cumsum(v, axis=1)
    sur = np.where(cv > 0, cv, 1)
    m2 = np.where(cv > 0, np.cumsum(typ * typ * v, axis=1) / sur, typ * typ)
    return np.sqrt(np.maximum(m2 - X["vwap"] ** 2, 0.0))


def main():
    m, info, S = D.seances()
    X = Y.mesures(m, info)
    prof = profils(pd.DatetimeIndex(info["jour"]))
    VA = {d: zone_valeur(prof[j]) for d, j in enumerate(info["jour"]) if j in prof}
    sv = sigma_v(m, X)
    jours = info["jour"]
    A = (jours <= Y.FIN_A).to_numpy()
    fp_ok = np.isfinite(m["ventes_bas2"]).all(axis=1)
    tr = Y.jouer(m, info, X, lambda m_, X_, d, sans: signaux_c1(m_, X_, d, VA, sv))
    base = X["jouable"] & fp_ok & np.array([d > 0 and (d - 1) in VA for d in range(len(info))])
    L = ["C1, confluence, SANS la condition du DOM (aucun DOM historique) : descriptif, aucun reglage",
         f"seances jouables avec profil de la veille et footprint : {base.sum()} (Databento, {jours[base].min().date()} - "
         f"{jours[base].max().date()})", ""]
    for lib, cols in (("A (avril - juillet)", np.flatnonzero(base & A)), ("B (aout - 1er octobre)", np.flatnonzero(base & ~A)),
                      ("tout", np.flatnonzero(base))):
        r = Y.resume(tr[tr["seance"].isin(cols)], cols)
        L.append(f"  {lib:<24} {r['n']:4d} trades | net moyen {r['moyen']:+6.2f} pt | gagnants {r['gagnants']:5.1%} | "
                 f"t par seance {r['t_seance']:+5.2f} | total {r['total']:+8.1f} pt ({2 * r['total']:+,.0f} $ par MNQ)")
    if len(tr):
        mo = tr["motif"].value_counts(normalize=True)
        L.append(f"  sorties : objectif {mo.get('objectif', 0):.0%}, stop {mo.get('stop', 0):.0%}, temps {mo.get('temps', 0):.0%} ; "
                 f"R median {tr['R'].median():.2f} pt ; achats {(tr['sens'] > 0).mean():.0%}")
        pl = Y.placebo(tr, np.flatnonzero(base))
        L.append(f"  placebo de sens : bat {(pl < Y.resume(tr, np.flatnonzero(base))['t_seance']).mean():.1%} des tirages")
    texte = "\n".join(L)
    (ICI / "resultats" / "confluence_sans_dom.txt").write_text(texte + "\n")
    print(texte)

    if len(sys.argv) > 1:                       # fichiers du rejeu C#
        out = Path(sys.argv[1])
        out.mkdir(parents=True, exist_ok=True)
        lignes = []
        for d, j in enumerate(jours):
            for t in range(D.NM):
                lignes.append((j.strftime("%Y-%m-%d"), t, m["o"][d, t], m["h"][d, t], m["l"][d, t], m["c"][d, t],
                               m["achats"][d, t], m["ventes"][d, t], m["ventes_bas2"][d, t], m["achats_haut2"][d, t]))
        pd.DataFrame(lignes, columns=["jour", "minute", "o", "h", "l", "c", "achats", "ventes", "vb2", "ah2"]).to_csv(
            out / "minutes.csv.gz", index=False, float_format="%.10g")
        pd.DataFrame({"jour": jours.dt.strftime("%Y-%m-%d"), "jouable": X["jouable"].astype(int)}).to_csv(
            out / "seances.csv", index=False)
        pd.concat([p.rename("volume").reset_index().assign(jour=j.strftime("%Y-%m-%d")) for j, p in prof.items()])[
            ["jour", "prix", "volume"]].to_csv(out / "profils.csv.gz", index=False, float_format="%.10g")
        attendus = {"S1": Y.jouer(m, info, X, Y.signaux_s1), "S2": Y.jouer(m, info, X, Y.signaux_s2), "C1": tr}
        Xr = R.tableaux(m, info)
        cf = R.table_configs()
        attendus["S2b"] = R.trades_config(Xr, cf.iloc[82358])
        for nom, t_ in attendus.items():
            t_.assign(jour=jours[t_["seance"]].dt.strftime("%Y-%m-%d").to_numpy())[["jour", "signal", "net"]].to_csv(
                out / f"attendus_{nom}.csv", index=False, float_format="%.10g")
        assert cf.iloc[82358]["famille"] == "F2" and cf.iloc[82358]["signal"] == ("les deux", 0, 5)
        print(f"fichiers du rejeu dans {out} ; attendus : " + ", ".join(f"{k} {len(v)}" for k, v in attendus.items()))


if __name__ == "__main__":
    main()
