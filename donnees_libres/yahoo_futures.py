#!/usr/bin/env python3
"""Vrais futures CME chez Yahoo (gratuit) : barres d'une heure sur les 730 derniers jours, barres de 5 minutes sur les 60
derniers jours, et barres du jour depuis le debut ; plus les indices de volatilite (VIX, VVIX, MOVE...) au jour.
Contrat continu de Yahoo (=F, echeance la plus proche, sans ajustement aux changements d'echeance).
Ecrit donnees_libres/yahoo/{heure,cinq,jour}/<nom>.csv.gz (t heure de New York, o, h, l, c, v) et resume.txt.
Lance par .github/workflows/donnees-libres.yml."""
import time
from pathlib import Path

import pandas as pd
import yfinance as yf

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "yahoo"
FUTURES = ["ES", "NQ", "YM", "RTY", "CL", "NG", "RB", "HO", "BZ", "GC", "SI", "HG", "PL", "PA", "ZN", "ZB", "ZF", "ZT",
           "ZC", "ZS", "ZW", "ZL", "ZM", "KE", "LE", "HE", "GF", "6E", "6J", "6B", "6A", "6C", "6S", "6N", "6M", "BTC",
           "ETH", "MNQ", "MES", "MGC", "MCL"]
INDICES = {"VIX": "^VIX", "VIX9D": "^VIX9D", "VIX3M": "^VIX3M", "VVIX": "^VVIX", "MOVE": "^MOVE", "OVX": "^OVX",
           "GVZ": "^GVZ", "DXY": "DX-Y.NYB"}
TAILLES = {"heure": ("60m", "730d"), "cinq": ("5m", "60d"), "jour": ("1d", "max")}


def telecharger(ticker, intervalle, periode):
    for essai in range(4):
        try:
            d = yf.download(ticker, interval=intervalle, period=periode, progress=False, auto_adjust=False,
                            multi_level_index=False, threads=False)
            if d is not None and len(d):
                return d
        except Exception as e:
            print(f"{ticker} {intervalle} : essai {essai + 1} ({type(e).__name__})")
        time.sleep(3 * (essai + 1))
    return None


def propre(d, jour):
    idx = d.index
    if not jour:
        idx = (idx.tz_convert("America/New_York") if idx.tz is not None else idx.tz_localize("UTC").tz_convert("America/New_York"))
    t = pd.DatetimeIndex(idx).strftime("%Y-%m-%d" if jour else "%Y-%m-%d %H:%M")
    out = pd.DataFrame({"t": t, "o": d["Open"].to_numpy(), "h": d["High"].to_numpy(), "l": d["Low"].to_numpy(),
                        "c": d["Close"].to_numpy(), "v": d["Volume"].to_numpy() if "Volume" in d else 0})
    return out.dropna(subset=["c"])


def main():
    resume = []
    noms = {f: f"{f}=F" for f in FUTURES} | INDICES
    for dossier, (intervalle, periode) in TAILLES.items():
        (SORTIE / dossier).mkdir(parents=True, exist_ok=True)
        for nom, ticker in noms.items():
            if nom in INDICES and dossier != "jour":
                continue
            d = telecharger(ticker, intervalle, periode)
            if d is None:
                resume.append(f"{dossier} {nom} ({ticker}) : rien")
                print(f"::warning::{dossier} {nom} ({ticker}) : rien")
                continue
            out = propre(d, dossier == "jour")
            out.to_csv(SORTIE / dossier / f"{nom}.csv.gz", index=False, compression="gzip")
            ligne = f"{dossier} {nom} ({ticker}) : {len(out)} barres, {out['t'].iloc[0]} -> {out['t'].iloc[-1]}"
            print(ligne, flush=True)
            resume.append(ligne)
            time.sleep(0.5)
    (SORTIE / "resume.txt").write_text("\n".join(resume) + "\n")


if __name__ == "__main__":
    main()
