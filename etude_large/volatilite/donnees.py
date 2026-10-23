#!/usr/bin/env python3
"""Relief de la volatilite implicite : donnees de la page (etude_large/volatilite/page.html).

Courbe des volatilites implicites du S&P 500 (VIX9D, VIX, VIX3M, fin de semaine), VVIX, volatilite realisee du ES sur
21 seances, prime de variance (VIX moins la volatilite realisee du mois suivant), et gain moyen de la zone (V1 sans
filtre, pas de zone les jours de la Fed, 1 MNQ) selon le VIX de la veille et la pente VIX / VIX3M de la veille
(sextiles, seances 2012 - 2026). Description, pas une regle testee.

Lancer depuis la racine : KB=<branche de recherche extraite> python3 etude_large/volatilite/donnees.py.
Ecrit donnees.json et relief.html (page.html avec les donnees inserees)."""
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import partie_d as PD  # noqa: E402

YAHOO = ICI.parent.parent / "donnees_libres" / "yahoo" / "jour"
PERIODES = (("2012-2022", "2012", "2022-12-31"), ("2023-2026", "2023", "2026-12-31"))


def lire(nom):
    d = pd.read_csv(YAHOO / f"{nom}.csv.gz", usecols=["t", "c"])
    d["t"] = pd.to_datetime(d["t"])
    return d.dropna().set_index("t")["c"]


def main():
    df = pd.concat({"v9": lire("VIX9D"), "v30": lire("VIX"), "v93": lire("VIX3M"), "vv": lire("VVIX"),
                    "es": lire("ES")}, axis=1, sort=True).dropna()
    df = df[df.index >= "2011-01-03"]
    r = np.log(df["es"]).diff()
    df["rv"] = r.rolling(21).std() * np.sqrt(252) * 100
    df["rv_fwd"] = r.rolling(21).std().shift(-21) * np.sqrt(252) * 100
    wk = df.resample("W-FRI").last().dropna(subset=["v9", "v30", "v93"])
    vrp = (df["v30"] - df["rv_fwd"]).dropna()

    jours, clo, _, _ = PD.chemins_zone()
    z = pd.Series(clo[:, -1], index=jours)
    reg = df[["v30", "v93"]].shift(1).reindex(jours)  # la veille : connu avant l'ouverture
    ok = reg.notna().all(axis=1) & (z.index >= pd.Timestamp("2012-01-01"))
    zz, rg = z[ok], reg[ok]
    pente = rg["v30"] / rg["v93"]
    qv, bv = pd.qcut(rg["v30"], 6, labels=False, retbins=True)
    qp, bp = pd.qcut(pente, 6, labels=False, retbins=True)
    g = pd.DataFrame({"z": zz, "qv": qv, "qp": qp})
    grp = g.groupby(["qv", "qp"])["z"]
    six = dict(index=range(6), columns=range(6))
    moy = grp.mean().unstack().reindex(**six)
    n = grp.size().unstack().reindex(**six).fillna(0)
    t = moy / (grp.std().unstack().reindex(**six) / np.sqrt(n))

    out = dict(
        semaines=[d.strftime("%Y-%m-%d") for d in wk.index], v9=wk.v9.round(2).tolist(), v30=wk.v30.round(2).tolist(),
        v93=wk.v93.round(2).tolist(), vvix=wk.vv.round(1).tolist(), rv=wk.rv.round(2).fillna(-1).tolist(),
        grille=dict(moy=moy.round(1).fillna(0).values.tolist(), n=n.astype(int).values.tolist(),
                    t=t.round(2).fillna(0).values.tolist(), bornes_vix=[round(x, 1) for x in bv],
                    bornes_pente=[round(x, 3) for x in bp]),
        par_periode={lab: dict(vix=g[(g.index >= a) & (g.index <= b)].groupby("qv")["z"].mean().round(1).tolist(),
                               pente=g[(g.index >= a) & (g.index <= b)].groupby("qp")["z"].mean().round(1).tolist())
                     for lab, a, b in PERIODES},
        vrp=dict(moyenne=round(float(vrp.mean()), 2), positive=round(float((vrp > 0).mean() * 100), 1)),
        zone=dict(seances=int(ok.sum()), moyenne=round(float(zz.mean()), 1)))
    texte = json.dumps(out, separators=(",", ":"))
    (ICI / "donnees.json").write_text(texte + "\n")
    page = (ICI / "page.html").read_text()
    assert "/*DONNEES*/null" in page
    (ICI / "relief.html").write_text(page.replace("/*DONNEES*/null", texte))
    print(f"{len(wk)} semaines ({wk.index[0].date()} -> {wk.index[-1].date()}), contango "
          f"{(wk.v30 < wk.v93).mean() * 100:.1f} % ; prime de variance {out['vrp']} ; zone {out['zone']}")


if __name__ == "__main__":
    main()
