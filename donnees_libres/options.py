#!/usr/bin/env python3
"""Chaines d'options du QQQ et du SPY chez Yahoo (gratuit, photo du moment : pas d'historique), toutes les echeances
jusqu'a 400 jours, plus le cours du sous-jacent et le taux a 13 semaines (^IRX). Pour etude_large/volatilite/ (surface
de volatilite implicite). Ecrit donnees_libres/options/<sous-jacent>.csv.gz et resume.txt.
Lance par .github/workflows/donnees-options.yml."""
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "options"
SOUS_JACENTS = ["QQQ", "SPY"]
MAX_JOURS = 400


def essayer(f, *a):
    for essai in range(4):
        try:
            return f(*a)
        except Exception as e:
            print(f"essai {essai + 1} : {type(e).__name__} {e}")
            time.sleep(4 * (essai + 1))
    return None


def main():
    SORTIE.mkdir(parents=True, exist_ok=True)
    maintenant = datetime.now(timezone.utc)
    resume = [f"telechargement {maintenant:%Y-%m-%d %H:%M} UTC"]
    irx = essayer(lambda: yf.Ticker("^IRX").history(period="10d"))
    if irx is not None and len(irx):
        resume.append(f"taux ^IRX {float(irx['Close'].iloc[-1]):.3f} % ({irx.index[-1].date()})")
    for sj in SOUS_JACENTS:
        t = yf.Ticker(sj)
        h = essayer(lambda: t.history(period="10d"))
        spot = float(h["Close"].iloc[-1]) if h is not None and len(h) else float("nan")
        echeances = essayer(lambda: t.options) or ()
        lignes = []
        for e in echeances:
            jours = (pd.Timestamp(e) - pd.Timestamp(maintenant.date())).days
            if jours < 0 or jours > MAX_JOURS:
                continue
            ch = essayer(t.option_chain, e)
            if ch is None:
                continue
            for typ, d in (("C", ch.calls), ("P", ch.puts)):
                d = d.copy()
                d["type"], d["echeance"] = typ, e
                lignes.append(d)
            time.sleep(0.4)
        if not lignes:
            resume.append(f"{sj} : rien")
            continue
        d = pd.concat(lignes, ignore_index=True)
        out = pd.DataFrame({"echeance": d["echeance"], "type": d["type"], "strike": d["strike"], "bid": d["bid"],
                            "ask": d["ask"], "dernier": d["lastPrice"], "iv_yahoo": d["impliedVolatility"],
                            "volume": d["volume"], "oi": d["openInterest"],
                            "date_dernier": pd.to_datetime(d["lastTradeDate"], utc=True).dt.strftime("%Y-%m-%d %H:%M")})
        out.to_csv(SORTIE / f"{sj}.csv.gz", index=False, compression="gzip")
        resume.append(f"{sj} : cours {spot:.2f} ({h.index[-1].date() if h is not None else '?'}), {out['echeance'].nunique()} "
                      f"echeances, {len(out)} options")
    if irx is not None and len(irx):
        pd.DataFrame({"t": irx.index.strftime("%Y-%m-%d"), "c": irx["Close"].values}).to_csv(
            SORTIE / "irx.csv.gz", index=False, compression="gzip")
    for sj in SOUS_JACENTS:
        h = essayer(lambda: yf.Ticker(sj).history(period="10d"))
        if h is not None and len(h):
            pd.DataFrame({"t": h.index.strftime("%Y-%m-%d"), "c": h["Close"].values}).to_csv(
                SORTIE / f"{sj}_cours.csv.gz", index=False, compression="gzip")
    (SORTIE / "resume.txt").write_text("\n".join(resume) + "\n")
    print("\n".join(resume))


if __name__ == "__main__":
    main()
