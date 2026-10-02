#!/usr/bin/env python3
"""Achete chez Databento (GLBX.MDP3, schema "trades", NQ.v.0) les transactions des 30 minutes avant chaque trade de
zone de trades_zone.csv (README.md). Fenetres d'une meme seance fusionnees, cout demande avant l'achat, des plus
recentes aux plus anciennes, plafond PLAFOND $ au total ; chaque annee commence par 5 fenetres d'essai, et on s'arrete si
moins de la moitie de leur volume a un cote agresseur connu.
Ecrit donnees/minutes.csv.gz (jour, minute depuis 9 h 30, achats, ventes, sans_cote) et donnees/achats.txt.
Cle : variable DATABENTO_API_KEY (secret du depot, jamais ecrite ailleurs)."""
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import databento as db
import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
D = ICI / "donnees"
JEU, SCHEMA, SYMBOLE = "GLBX.MDP3", "trades", "NQ.v.0"
PLAFOND, FENETRE, FILS = 75.0, 30, 8


def essayer(f, essais=5):
    for k in range(essais):
        try:
            return f()
        except Exception as e:
            statut = getattr(e, "http_status", None) or 0
            if k == essais - 1 or (400 <= statut < 500 and statut != 429):     # refus (compte, cle, requete) : pas de nouvel essai
                raise
            print(f"  nouvelle tentative : {repr(e)[:150]}", flush=True)
            time.sleep(5 * (k + 1))


def fenetres(trades):
    """Une ligne par telechargement : jour, premiere et derniere minute (depuis 9 h 30) de la fenetre fusionnee."""
    out = []
    for j, g in trades.groupby("jour"):
        blocs = []
        for m in sorted(g["minute"]):
            a, b = m - FENETRE + 1, m
            if blocs and a <= blocs[-1][1] + 1:
                blocs[-1][1] = b
            else:
                blocs.append([a, b])
        out += [(j, a, b) for a, b in blocs]
    return pd.DataFrame(out, columns=["jour", "debut", "fin"])


def bornes(jour, a, b):
    o = pd.Timestamp(f"{jour} 09:30", tz="America/New_York")
    return (o + pd.Timedelta(minutes=int(a))).tz_convert("UTC").isoformat(), (o + pd.Timedelta(minutes=int(b) + 1)).tz_convert("UTC").isoformat()


def main():
    client = db.Historical()
    F = fenetres(pd.read_csv(ICI / "trades_zone.csv")).sort_values("jour", ascending=False).reset_index(drop=True)
    args = [dict(dataset=JEU, symbols=[SYMBOLE], stype_in="continuous", schema=SCHEMA,
                 start=bornes(*x)[0], end=bornes(*x)[1]) for x in F[["jour", "debut", "fin"]].itertuples(index=False)]
    float(essayer(lambda: client.metadata.get_cost(**args[0])))      # un premier appel seul : un refus arrete tout de suite
    with ThreadPoolExecutor(FILS) as ex:
        F["cout"] = list(ex.map(lambda a: float(essayer(lambda: client.metadata.get_cost(**a))), args))
    F["an"] = F["jour"].str[:4]
    par_an = F.groupby("an")["cout"].agg(["size", "sum"]).sort_index(ascending=False)
    lignes = [f"Achats Databento {SCHEMA} {SYMBOLE} ({pd.Timestamp.now(tz='UTC'):%Y-%m-%d %H:%M} UTC), plafond {PLAFOND:.0f} $",
              f"Cout de toutes les fenetres : {F['cout'].sum():.2f} $ pour {len(F)} fenetres",
              "Par annee (fenetres, cout) : " + " ; ".join(f"{a} {int(r['size'])} {r['sum']:.2f} $" for a, r in par_an.iterrows())]
    print("\n".join(lignes), flush=True)
    D.mkdir(exist_ok=True)
    pris = F[F["cout"].cumsum() <= PLAFOND]
    resultats, depense, arret = [], 0.0, ""
    for an, g in pris.groupby("an", sort=False):
        def un(i):
            df = essayer(lambda: client.timeseries.get_range(**args[i]).to_df())
            if df.empty:
                return pd.DataFrame(columns=["jour", "minute", "achats", "ventes", "sans_cote"])
            t = pd.DatetimeIndex(df.index if "ts_event" not in df.columns else df["ts_event"])
            t = (t.tz_localize("UTC") if t.tz is None else t).tz_convert("America/New_York")
            minute = ((t - t.normalize()).total_seconds() // 60 - 570).astype(int)
            q, cote = df["size"].to_numpy(np.int64), df["side"].astype(str).to_numpy()
            x = pd.DataFrame({"minute": minute, "achats": np.where(cote == "B", q, 0), "ventes": np.where(cote == "A", q, 0),
                              "sans_cote": np.where((cote != "A") & (cote != "B"), q, 0)})
            x = x.groupby("minute", as_index=False).sum()
            x.insert(0, "jour", F.loc[i, "jour"])
            return x
        def connu(morceaux):
            vol = pd.concat(morceaux, ignore_index=True)[["achats", "ventes", "sans_cote"]].sum()
            return (vol["achats"] + vol["ventes"]) / max(1, vol.sum())
        with ThreadPoolExecutor(FILS) as ex:
            essai = list(ex.map(un, g.index[:5]))          # 5 fenetres d'abord : le cote agresseur existe-t-il cette annee ?
            depense += g["cout"].iloc[:5].sum()
            if connu(essai) < 0.5:
                resultats += essai
                arret = (f"arret en {an} : cote agresseur connu pour {connu(essai):.1%} du volume sur 5 fenetres d'essai ;"
                         f" ni le reste de {an} ni les annees d'avant ne sont achetes")
                break
            morceaux = essai + list(ex.map(un, g.index[5:]))
        depense += g["cout"].iloc[5:].sum()
        resultats += morceaux
        print(f"  {an} : {len(g)} fenetres, {g['cout'].sum():.2f} $, cote connu pour {connu(morceaux):.1%} du volume", flush=True)
        lignes.append(f"{an} : {len(g)} fenetres achetees, {g['cout'].sum():.2f} $, cote agresseur connu pour {connu(morceaux):.1%} du volume")
    if arret:
        print(arret, flush=True)
    tout = pd.concat(resultats, ignore_index=True).sort_values(["jour", "minute"])
    tout.to_csv(D / "minutes.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
    if len(pris) < len(F):
        lignes.append(f"Plafond : {len(F) - len(pris)} fenetres plus anciennes non achetees (avant le {pris['jour'].min()})")
    if arret:
        lignes.append(arret)
    lignes.append(f"total depense : {depense:.2f} $ ; {tout['jour'].nunique()} seances du {tout['jour'].min()} au {tout['jour'].max()}")
    (D / "achats.txt").write_text("\n".join(lignes) + "\n")
    print("\n".join(lignes[-3:]))


if __name__ == "__main__":
    main()
