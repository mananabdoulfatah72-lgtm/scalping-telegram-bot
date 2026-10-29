#!/usr/bin/env python3
"""Partie 7 (flux/README.md) : biais hebdomadaires tires du rapport COT de la CFTC (Traders in Financial Futures, futures
seuls, E-mini Nasdaq-100), joues en seance sur le NQ (9 h 35 - 15 h 55). Exploration 2011 - 2018, coffre 2019 - 2026.

Lancer : FLUX_COT=<dossier des zip de la CFTC> KB=<copie de claude/keen-babbage-r686cl> python3 flux/cot.py [--coffre]"""
import io
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import partie_e as E  # noqa: E402

FIN_EXPLO, DEBUT_COFFRE = pd.Timestamp("2018-12-31"), pd.Timestamp("2019-01-01")
PLACEBOS = 1000


def lire_cot(dossier):
    """Lignes E-mini Nasdaq-100 de tous les fichiers TFF futures seuls du dossier (zip ou txt)."""
    tables = []
    for f in sorted(Path(dossier).iterdir()):
        if f.suffix == ".zip":
            with zipfile.ZipFile(f) as z:
                for n in z.namelist():
                    tables.append(pd.read_csv(io.BytesIO(z.read(n)), low_memory=False))
        elif f.suffix in (".txt", ".csv"):
            tables.append(pd.read_csv(f, low_memory=False))
    t = pd.concat(tables, ignore_index=True)
    def col(exact, *mots):
        """Nom officiel de la CFTC s'il existe, sinon premiere colonne qui contient tous les mots (hors variations,
        pourcentages et nombres de traders)."""
        if exact in t.columns:
            return exact
        return next(c for c in t.columns if all(m.lower() in c.lower() for m in mots)
                    and not any(x in c.lower() for x in ("change", "pct", "traders", "conc")))
    nom = t[col("Market_and_Exchange_Names", "market", "exchange")].astype(str).str.upper()
    garde = nom.str.contains("NASDAQ") & nom.str.contains("MINI") & ~nom.str.contains("MICRO") & nom.str.contains("CHICAGO")
    t = t[garde]
    d = pd.DataFrame({
        "date": pd.to_datetime(t[col("Report_Date_as_YYYY-MM-DD", "report_date", "yyyy")]),
        "oi": t[col("Open_Interest_All", "open_interest", "all")].astype(float),
        "am": t[col("Asset_Mgr_Positions_Long_All", "asset_mgr", "long", "all")].astype(float) - t[col("Asset_Mgr_Positions_Short_All", "asset_mgr", "short", "all")].astype(float),
        "lf": t[col("Lev_Money_Positions_Long_All", "lev_money", "long", "all")].astype(float) - t[col("Lev_Money_Positions_Short_All", "lev_money", "short", "all")].astype(float),
        "dl": t[col("Dealer_Positions_Long_All", "dealer", "long", "all")].astype(float) - t[col("Dealer_Positions_Short_All", "dealer", "short", "all")].astype(float),
    })
    # plusieurs lignes la meme semaine (changement de nom du marche) : la plus grosse (le contrat principal)
    d = d.sort_values(["date", "oi"]).drop_duplicates("date", keep="last").set_index("date").sort_index()
    for k in ("am", "lf", "dl"):
        d[k] = d[k] / d["oi"]
    return d


def biais(cot):
    """Biais de chaque hypothese pour chaque rapport (+1, -1, 0), et date de debut d'usage (mardi + 3 jours)."""
    b = pd.DataFrame(index=cot.index)
    b["G1"] = np.sign(cot["am"].diff(4))
    b["G2"] = np.sign(cot["lf"].diff(4))
    z = (cot["lf"] - cot["lf"].rolling(52).mean()) / cot["lf"].rolling(52).std()
    b["G3"] = np.where(z >= 1.5, -1, np.where(z <= -1.5, 1, 0))
    b["G4"] = np.sign(cot["dl"].diff(4))
    b["G5"] = np.where(b["G1"] == b["G2"], b["G1"], 0)
    b = b.fillna(0)
    b["publication"] = b.index + pd.Timedelta(days=3)
    return b


def seances():
    d = E.jour_nq()
    O, C = d["o"], d["c"]
    ok = d["complete"] & ~d["ech"]
    ech = float(d["pref"]) / O[:, 0]
    jours = pd.DatetimeIndex(d["jours"].astype("datetime64[D]"))
    jour_pts = (C[:, 384] - O[:, 5]) * float(d["pt"]) * ech                  # 1 MNQ, acheteur, avant frais
    cc = pd.Series(C[:, -1], index=jours)
    nuit_pts = (cc - cc.shift(1)).to_numpy() * float(d["pt"]) * ech          # descriptif : de cloture a cloture
    return jours, ok, jour_pts, nuit_pts, float(d["frais"])


def aligner(b, jours, h):
    """Biais en vigueur a chaque seance : dernier rapport publie strictement avant la seance."""
    s = pd.Series(b[h].to_numpy(), index=b["publication"])
    idx = s.index.searchsorted(jours, side="left") - 1
    out = np.where(idx >= 0, s.to_numpy()[np.maximum(idx, 0)], 0.0)
    return out


def t_stat(x):
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * np.sqrt(len(x))) if s > 0 else 0.0


def gains(sens, ok, pts, frais):
    return np.where(ok & (sens != 0), sens * pts - frais, 0.0)


def main():
    cot = lire_cot(os.environ["FLUX_COT"])
    b = biais(cot)
    jours, ok, pts, nuit, frais = seances()
    explo = (jours >= pd.Timestamp("2011-01-01")) & (jours <= FIN_EXPLO)
    coffre = jours >= DEBUT_COFFRE
    rng = np.random.default_rng(2026)
    L = [f"COT (E-mini Nasdaq-100) : {len(cot)} rapports du {cot.index[0].date()} au {cot.index[-1].date()} ; "
         f"seances NQ {jours[0].date()} - {jours[-1].date()}", ""]
    finalistes = []
    for h in ("G1", "G2", "G3", "G4", "G5"):
        sens = aligner(b, jours, h)
        g = gains(sens, ok, pts, frais)
        te = t_stat(g[explo])
        pl = []
        n_sem = len(b)
        for _ in range(PLACEBOS):
            k = int(rng.integers(8, n_sem - 8))
            bb = b.copy()
            bb[h] = np.roll(b[h].to_numpy(), k)
            pl.append(t_stat(gains(aligner(bb, jours, h), ok, pts, frais)[explo]))
        p95 = float(np.percentile(pl, 95))
        passe = te >= 2 and te > p95
        if passe:
            finalistes.append(h)
        gn = np.where(ok & (sens != 0), sens * nuit - frais, 0.0)
        L.append(f"{h} : exploration 2011-2018 t {te:+.2f} (placebos 95e {p95:+.2f}), {int((g[explo] != 0).sum())} seances jouees, "
                 f"{g[explo].sum():+,.0f} $ par MNQ -> {'FINALISTE' if passe else 'elimine'} ; "
                 f"descriptif cloture a cloture t {t_stat(gn[explo]):+.2f}")
    L.append(f"\nFinalistes : {finalistes or 'aucun'}")
    if "--coffre" in sys.argv and finalistes:
        from statistics import NormalDist
        seuil = NormalDist().inv_cdf(1 - 0.05 / len(finalistes))
        for h in finalistes:
            g = gains(aligner(b, jours, h), ok, pts, frais)
            gc = g[coffre]
            par_an = pd.Series(gc, index=jours[coffre]).groupby(jours[coffre].year).sum()
            ok_c = t_stat(gc) >= seuil and gc.mean() > 0 and (par_an > 0).sum() >= 5
            L.append(f"coffre {h} : t {t_stat(gc):+.2f} (seuil {seuil:.2f}), {gc.sum():+,.0f} $ par MNQ, annees positives "
                     f"{(par_an > 0).sum()}/{len(par_an)} -> {'RETENUE' if ok_c else 'non retenue'}")
    texte = "\n".join(L)
    (ICI / "resultats" / "cot.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    main()
