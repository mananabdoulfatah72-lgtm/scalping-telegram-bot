#!/usr/bin/env python3
"""etude_large/annonces/README.md (regles fixees le 22 octobre 2026, avant tout calcul) : la zone du bot les jours
ou l'indice du dollar saute entre 8 h 30 et 8 h 40 (HistData 5 minutes). Regles S (pas de zone ces jours-la) et D
(2 MNQ ces jours-la), placebo de 200 tirages de jours au hasard, challenges pour information.

Lancer : python3 etude_large/annonces/etude.py (numba, numpy, pandas ; variable KB comme delta_mesures). Ecrit
resultats.txt."""
import sys
from pathlib import Path

sys.dont_write_bytecode = True
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent
sys.path.insert(0, str(ICI.parent))
import partie_d as PD  # noqa: E402

DOLLAR = RACINE / "donnees_libres" / "histdata_5min"
EXPLO = ("2012-01-01", "2022-12-31")
COFFRE = ("2023-01-01", "2026-10-20")
CENTILE, FENETRE, PLACEBOS = 0.80, 250, 200


def chocs(jours):
    """Choc de 8 h 30 de chaque seance : |ln(cloture de la barre 8 h 35 / cloture de la barre 8 h 25)| du dollar, et
    jour de choc s'il depasse le 80e centile des 250 seances precedentes."""
    d = pd.concat([pd.read_csv(f) for f in sorted(DOLLAR.glob("udxusd_*_5m.csv.gz"))], ignore_index=True)
    t = pd.to_datetime(d["t"]).dt.tz_localize("UTC").dt.tz_convert("America/New_York")
    d = pd.DataFrame({"jour": t.dt.tz_localize(None).dt.normalize(), "hm": t.dt.strftime("%H:%M"), "c": d["c"].values})
    avant = d[d["hm"] == "08:25"].groupby("jour")["c"].last()
    apres = d[d["hm"] == "08:35"].groupby("jour")["c"].last()
    x = np.abs(np.log(apres / avant)).reindex(jours)
    seuil = x.rolling(FENETRE, min_periods=100).quantile(CENTILE).shift(1)
    return x.values, (x > seuil).fillna(False).values


def sharpe(r):
    return float(r.mean() / r.std(ddof=1) * np.sqrt(252)) if r.std(ddof=1) > 0 else 0.0


def t_stat(r):
    return float(r.mean() / r.std(ddof=1) * np.sqrt(len(r))) if r.std(ddof=1) > 0 else 0.0


def main():
    jours, clo, bas, haut = PD.chemins_zone()
    pnl = clo[:, -1]
    x, choc = chocs(jours)
    e = (jours >= EXPLO[0]) & (jours <= EXPLO[1])
    c = (jours >= COFFRE[0]) & (jours <= COFFRE[1])
    vendredi1 = (jours.dayofweek == 4) & (jours.day <= 7)
    L = ["Vague annonces de 8 h 30 (etude_large/annonces/README.md, regles fixees le 22 octobre 2026 avant tout calcul)",
         f"{len(jours)} seances {jours[0].date()} - {jours[-1].date()} (zone du bot, 1 MNQ, $ au prix d'aujourd'hui, "
         f"jours de la Fed a 0) ; dollar a 8 h 30 connu {int((~np.isnan(x)).sum())} seances ; jours de choc "
         f"{int(choc.sum())} ({choc.mean() * 100:.0f} %), dont {int((choc & c).sum())} au coffre.",
         f"CONTROLE : premiers vendredis du mois (emploi) marques jours de choc : {choc[vendredi1].mean() * 100:.0f} % "
         f"-> {'conforme (>= 60 %)' if choc[vendredi1].mean() >= 0.6 else 'ECART (< 60 %)'}", ""]
    for nom, m in (("jours de choc", choc), ("autres jours", ~choc)):
        L.append(f"  zone, {nom:<14} : exploration t {t_stat(pnl[e & m]):+.2f}, moyenne {pnl[e & m].mean():+6.1f} $ ; "
                 f"coffre t {t_stat(pnl[c & m]):+.2f}, moyenne {pnl[c & m].mean():+6.1f} $")
    L.append(f"  zone seule : Sharpe exploration {sharpe(pnl[e]):+.2f}, coffre {sharpe(pnl[c]):+.2f}")
    regles = {"S (pas de zone les jours de choc)": lambda m: pnl * (1 - m),
              "D (2 MNQ les jours de choc)": lambda m: pnl * (1 + m)}
    rng = np.random.default_rng(22)
    ans = jours.year.values
    retenues = []
    L.append("")
    for nom, f in regles.items():
        r = f(choc.astype(float))
        se, sc = sharpe(r[e]), sharpe(r[c])
        plac = []
        for _ in range(PLACEBOS):
            m = np.zeros(len(jours))
            for y in np.unique(ans[e]):
                ix = np.where(ans == y)[0]
                k = int(choc[ix].sum())
                m[rng.choice(ix, size=k, replace=False)] = 1.0
            plac.append(sharpe(f(m)[e]))
        rang = float((np.array(plac) < se).mean())
        ok = se > sharpe(pnl[e]) and sc > sharpe(pnl[c]) and rang >= 0.95
        if ok:
            retenues.append((se, nom))
        L.append(f"  {nom} : Sharpe exploration {se:+.2f}, coffre {sc:+.2f} ; bat {rang * 100:.0f} % des placebos -> "
                 f"{'RETENUE' if ok else 'non retenue'}")
    L.append("")
    L.append(f"DECISION : {'retenue : ' + max(retenues)[1] if retenues else 'aucune regle retenue'}")
    # information : challenges, departs 2023 - 2026
    L.append("\nPour information, challenges (departs 2023 - 2026, moteur corrige de la partie D) : valide / perdu")
    dep = np.where(jours >= PD.DEBUT_VERIF)[0]
    for firme, q in (("Lucid Flex 50K", 1.0), ("Bulenox Legacy 50K opt. 2", 3.0)):
        obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
        lim = PD.limites_depart(jours, dep, nmax)
        ok = dep + lim < len(jours)
        arg = (q, q, 0, float(obj), float(dd), float(bloc), float(dll), part, True)
        txt = []
        for lab, mult in (("zone", np.ones(len(jours))), ("S", 1 - choc), ("D", 1 + choc)):
            w = mult[:, None]
            a = PD.tous_les_departs(clo * w, bas * w, haut * w, dep[ok], lim[ok], *arg)[0]
            txt.append(f"{lab} {(a == 1).mean() * 100:.0f} / {(a == -1).mean() * 100:.0f} %")
        L.append(f"  {firme} ({q:.0f} MNQ) : " + " ; ".join(txt))
    (ICI / "resultats.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
