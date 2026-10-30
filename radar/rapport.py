#!/usr/bin/env python3
"""Radar, rapport du soir (radar/README.md) : ce que la collecte a vu aujourd'hui, en une page (radar/RAPPORT.md) et en
quelques lignes sur Telegram. Mouvements inhabituels sur tous les marches, volatilite, gamma des options du Nasdaq 100,
ventes a decouvert, attention sur Wikipedia, sentiment, liquidite, ton des nouvelles, calendrier de la prochaine seance,
et etat de la strategie du radar. Ne decide aucun trade.

Lancer : python3 radar/rapport.py (TELEGRAM_TOKEN et CHAT_ID facultatifs)"""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ICI = Path(__file__).resolve().parent
DONNEES = ICI / "donnees"
NOMS = {"NQ=F": "Nasdaq 100 (NQ)", "ES=F": "S&P 500 (ES)", "YM=F": "Dow (YM)", "RTY=F": "Russell (RTY)",
        "CL=F": "Petrole", "NG=F": "Gaz", "GC=F": "Or", "SI=F": "Argent", "HG=F": "Cuivre", "ZN=F": "T-Note 10 ans",
        "ZB=F": "T-Bond", "6E=F": "Euro", "6J=F": "Yen", "6B=F": "Livre", "BTC-USD": "Bitcoin", "ETH-USD": "Ether",
        "DX-Y.NYB": "Dollar (DXY)", "^N225": "Nikkei", "^HSI": "Hang Seng", "^GDAXI": "DAX", "^FTSE": "FTSE",
        "^STOXX50E": "Euro Stoxx 50", "^SOX": "Semi-conducteurs (SOX)", "SMH": "SMH", "TLT": "TLT", "HYG": "HYG",
        "NVDA": "Nvidia", "AAPL": "Apple", "MSFT": "Microsoft", "AMZN": "Amazon", "META": "Meta", "GOOGL": "Alphabet",
        "AVGO": "Broadcom", "TSLA": "Tesla", "TQQQ": "TQQQ"}


def lire(famille):
    fs = sorted((DONNEES / "jour" / famille).glob("*.csv.gz"))[-3:]
    if not fs:
        return None
    t = pd.concat([pd.read_csv(f, dtype={"date": str, "serie": str}) for f in fs], ignore_index=True)
    t["date"] = pd.to_datetime(t["date"])
    t["valeur"] = pd.to_numeric(t["valeur"], errors="coerce")
    return t.pivot_table(index="date", columns="serie", values="valeur", aggfunc="last").sort_index()


def marches(ya):
    lignes, alertes = [], []
    univers = sorted({c.rsplit(":", 1)[0] for c in ya.columns if c.endswith(":c")})
    for s in univers:
        c = ya[f"{s}:c"].dropna()
        if len(c) < 25 or (ya.index[-1] - c.index[-1]).days > 5:
            continue
        r = np.log(c).diff().dropna()
        z = r.iloc[-1] / r.iloc[-21:-1].std()
        info = (s, c.iloc[-1], 100 * (np.exp(r.iloc[-1]) - 1), z, 100 * (c.iloc[-1] / c.iloc[-6] - 1),
                100 * (c.iloc[-1] / c.iloc[-21] - 1), c.index[-1])
        if s in NOMS:
            lignes.append(info)
        if abs(z) >= 2.5:
            alertes.append(info)
    return lignes, sorted(alertes, key=lambda x: -abs(x[3]))


def rang(s, n=252):
    s = s.dropna()
    if len(s) < 30:
        return np.nan
    x = s.iloc[-n:]
    return 100 * (x.iloc[:-1] < x.iloc[-1]).mean()


def main():
    ya, alt, fin = lire("yahoo"), lire("alt"), lire("finra")
    L = ["# Radar : rapport du soir", ""]
    msg = []
    if ya is not None:
        jour = ya.index[-1].date()
        L[0] += f" ({jour})"
        msg.append(f"Radar du {jour}")
        lignes, alertes = marches(ya)
        L += ["## Marchés", "", "| Marché | Dernier | Jour | z du jour | 5 jours | 20 jours |", "|---|---|---|---|---|---|"]
        for s, c, j, z, r5, r20, _ in lignes:
            L.append(f"| {NOMS[s]} | {c:,.2f} | {j:+.2f} % | {z:+.1f} | {r5:+.1f} % | {r20:+.1f} % |")
        L += ["", f"**Mouvements inhabituels** (|z| ≥ 2,5 sur les 20 derniers jours), {len(alertes)} sur "
                  f"{len({c.rsplit(':', 1)[0] for c in ya.columns})} séries :", ""]
        for s, c, j, z, *_ in alertes[:20]:
            L.append(f"- {NOMS.get(s, s)} : {j:+.2f} % (z {z:+.1f})")
        if alertes:
            msg.append("Mouvements inhabituels : " + ", ".join(f"{NOMS.get(s, s)} {j:+.1f} %" for s, c, j, *_ in alertes[:6]))
        vol = [("VIX", "^VIX"), ("VXN (Nasdaq)", "^VXN"), ("VIX 9 jours", "^VIX9D"), ("VIX 3 mois", "^VIX3M"),
               ("VVIX", "^VVIX"), ("SKEW", "^SKEW"), ("MOVE (taux)", "^MOVE")]
        L += ["", "## Volatilité", "", "| Indice | Niveau | Rang sur 1 an |", "|---|---|---|"]
        for nom, s in vol:
            if f"{s}:c" in ya:
                L.append(f"| {nom} | {ya[f'{s}:c'].dropna().iloc[-1]:.2f} | {rang(ya[f'{s}:c']):.0f} % |")
        if "^VIX:c" in ya and "^VIX3M:c" in ya:
            tv = ya["^VIX:c"].dropna().iloc[-1] / ya["^VIX3M:c"].dropna().iloc[-1]
            L.append(f"\nVIX / VIX 3 mois : {tv:.2f} ({'courbe inversée : stress' if tv > 1 else 'courbe normale'})")
            msg.append(f"VIX {ya['^VIX:c'].dropna().iloc[-1]:.1f}, VIX/VIX3M {tv:.2f}")
    if alt is not None:
        g = [c for c in alt.columns if c.startswith("cboe:NDX:")]
        if g:
            x = alt[g].dropna(how="all").iloc[-1]
            L += ["", "## Options du Nasdaq 100 (CBOE, photo du soir)", ""]
            L.append(f"- Gamma des teneurs de marché : {x.get('cboe:NDX:gex_total', np.nan) / 1e9:+.2f} milliards $ par 1 % "
                     f"({'positif : ils freinent les mouvements' if x.get('cboe:NDX:gex_total', 0) > 0 else 'négatif : ils les amplifient'})")
            L.append(f"- Niveau de bascule {x.get('cboe:NDX:bascule', np.nan):,.0f} ; mur de calls "
                     f"{x.get('cboe:NDX:mur_call', np.nan):,.0f} ; mur de puts {x.get('cboe:NDX:mur_put', np.nan):,.0f} ; "
                     f"NDX {x.get('cboe:NDX:spot', np.nan):,.0f}")
            L.append(f"- Puts / calls : {x.get('cboe:NDX:pc_oi', np.nan):.2f} en positions ouvertes, "
                     f"{x.get('cboe:NDX:pc_volume', np.nan):.2f} en volume")
            msg.append(f"Gamma NDX {x.get('cboe:NDX:gex_total', np.nan) / 1e9:+.1f} Md$ ; murs {x.get('cboe:NDX:mur_put', np.nan):,.0f}"
                       f" / {x.get('cboe:NDX:mur_call', np.nan):,.0f}")
        if "squeeze:gex" in alt:
            gx = alt["squeeze:gex"].dropna()
            hist = sorted((ICI / "donnees" / "jour" / "alt").glob("*.csv.gz"))
            tout = pd.concat([pd.read_csv(f) for f in hist])
            tout = tout[tout["serie"] == "squeeze:gex"].assign(date=lambda x: pd.to_datetime(x["date"])).set_index("date")["valeur"].sort_index()
            avant = tout.iloc[-253:-1]
            rg = float((avant < tout.iloc[-1]).mean()) if len(avant) >= 199 else np.nan
            L += ["", "## Régime gamma (règle L2 du bot FluxNQ, règle 9)", "",
                  f"GEX de SqueezeMetrics du {gx.index[-1].date()} : rang {rg * 100:.0f} % sur 252 séances. "
                  + ("**L2 active à la prochaine séance** : à 15 h 30, contre le mouvement du jour, sortie à 16 h."
                     if rg >= 0.8 else "L2 inactive à la prochaine séance (il faut 80 %).")]
            msg.append(f"Gamma rang {rg * 100:.0f} % : L2 {'ACTIVE' if rg >= 0.8 else 'inactive'} demain")
        w = [c for c in alt.columns if c.startswith("wiki:")]
        if w:
            lv = np.log(alt[w].clip(lower=1))
            z = ((lv - lv.rolling(30, min_periods=15).mean().shift(1)) / lv.rolling(30, min_periods=15).std().shift(1))
            dz = z.dropna(how="all").iloc[-1].sort_values(ascending=False)
            L += ["", "## Attention du public (Wikipédia, veille)", ""]
            L += [f"- {k[5:].replace('_', ' ')} : z {v:+.1f}" for k, v in dz.head(6).items()]
        sent = []
        for cle, nom in (("cnn:fear_and_greed_historical", "CNN peur et avidité"),):
            if cle in alt:
                sent.append(f"- {nom} : {alt[cle].dropna().iloc[-1]:.0f} sur 100")
        if "aaii:bullish" in alt:
            b, br = alt["aaii:bullish"].dropna(), alt["aaii:bearish"].dropna()
            sent.append(f"- AAII : {100 * b.iloc[-1]:.0f} % haussiers, {100 * br.iloc[-1]:.0f} % baissiers ({b.index[-1].date()})")
        if sent:
            L += ["", "## Sentiment", ""] + sent
        fr = [("Écart de crédit à haut rendement", "fred:BAMLH0A0HYM2"), ("Taux à 10 ans", "fred:DGS10"),
              ("10 ans − 2 ans", "fred:T10Y2Y"), ("Prises en pension inversées (milliards)", "fred:RRPONTSYD"),
              ("Compte du Trésor (millions)", "fred:WTREGEN"), ("Stress financier (St. Louis)", "fred:STLFSI4"),
              ("Incertitude des politiques économiques", "fred:USEPUINDXD")]
        fl = [f"- {nom} : {alt[c].dropna().iloc[-1]:,.2f} ({alt[c].dropna().index[-1].date()})" for nom, c in fr if c in alt]
        if fl:
            L += ["", "## Liquidité et crédit (FRED)", ""] + fl
        gd = [c for c in alt.columns if c.startswith("gdelt:") and c.endswith(":ton")]
        if gd:
            L += ["", "## Ton des nouvelles du monde (GDELT, veille)", ""]
            for c in gd:
                s = alt[c].dropna()
                if len(s) > 10:
                    L.append(f"- {c.split(':')[1]} : {s.iloc[-1]:+.2f} (moyenne 30 jours {s.iloc[-31:-1].mean():+.2f})")
    if fin is not None:
        L += ["", "## Ventes à découvert (FINRA, veille)", ""]
        for s in ("QQQ", "TQQQ", "SQQQ", "NVDA", "AAPL", "MSFT"):
            if f"{s}:court" in fin and f"{s}:total" in fin:
                p = (fin[f"{s}:court"] / fin[f"{s}:total"]).dropna()
                if len(p) > 30:
                    z = (p.iloc[-1] - p.iloc[-61:-1].mean()) / p.iloc[-61:-1].std()
                    L.append(f"- {s} : {100 * p.iloc[-1]:.1f} % du volume vendu à découvert (z {z:+.1f} sur 60 jours)")
    res = DONNEES / "evenements" / "resultats.csv"
    if res.exists():
        r = pd.read_csv(res)
        t = pd.to_datetime(r["t"])
        now = pd.Timestamp.now(tz="America/New_York").tz_localize(None)
        proche = r[(t >= now - pd.Timedelta(hours=12)) & (t <= now + pd.Timedelta(days=7))]
        if len(proche):
            L += ["", "## Résultats des grandes valeurs (7 prochains jours)", ""]
            L += [f"- {x['symbole']} : {x['t']}" for _, x in proche.sort_values("t").iterrows()]
            msg.append("Résultats à venir : " + ", ".join(f"{x['symbole']} {x['t'][5:16]}" for _, x in proche.sort_values("t").head(5).iterrows()))
    etat = DONNEES / "etat.json"
    if etat.exists():
        e = json.loads(etat.read_text())
        L += ["", "## Collecte", ""] + [f"- {k} : " + ", ".join(f"{a} {b}" for a, b in v.items() if a != "heure_utc")
                                       for k, v in e.items()]
    strat = ICI / "resultats" / "STRATEGIE.md"
    if strat.exists():
        L += ["", "## Stratégie du radar", "", "Voir `radar/resultats/STRATEGIE.md`."]
    (ICI / "RAPPORT.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    jeton, chat = os.getenv("TELEGRAM_TOKEN", ""), os.getenv("CHAT_ID", "")
    if jeton and chat and msg:
        try:
            requests.post(f"https://api.telegram.org/bot{jeton}/sendMessage",
                          data={"chat_id": chat, "text": "\n".join(msg)}, timeout=20)
        except Exception as ex:
            print(f"Telegram : message non envoye ({type(ex).__name__})")


if __name__ == "__main__":
    main()
