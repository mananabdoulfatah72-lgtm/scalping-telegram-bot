#!/usr/bin/env python3
"""Donnees du systeme order flow (flux/README.md) : barres d'une minute du NQ avec volume acheteur et vendeur agressif,
footprint (ventes aux deux prix les plus bas, achats aux deux prix les plus hauts de chaque minute) et secondes Databento
pour le controle d'execution.

Sources (branche de recherche, variable KB = dossier d'une copie de `claude/keen-babbage-r686cl`) :
- KB/orderflow/donnees/nq_secondes_*.csv.gz et nq_footprint_*.csv.gz (Databento, 1er avril - 1er octobre 2026) ;
- KB/filtre_h1/donnees_rithmic/transactions_NQZ6_rithmic.csv (export Rithmic du compte Bulenox), seances apres le
  dernier jour Databento ;
- FLUX_EXPORTS (facultatif) : dossier d'autres exports « Export transactions NQ » (meme format), seances suivantes."""
import os
from pathlib import Path

import numpy as np
import pandas as pd

KB = Path(os.getenv("KB", Path(__file__).resolve().parent.parent))
OF = KB / "orderflow" / "donnees"
RITHMIC = KB / "filtre_h1" / "donnees_rithmic" / "transactions_NQZ6_rithmic.csv"
NS, NM, TICK = 23400, 390, 0.25


class Secondes:
    """Secondes Databento (seance x seconde), memes retraits que orderflow/outils.py : jours feries (fin avant 13 h)."""

    def __init__(self):
        s = pd.concat([pd.read_csv(p) for p in sorted(OF.glob("nq_secondes_*.csv.gz"))], ignore_index=True)
        s = s.drop_duplicates("t").sort_values("t")
        t = pd.to_datetime(s["t"])
        jour = t.dt.normalize()
        sec = ((t - jour).dt.total_seconds() - 34200).astype(int).to_numpy()
        garde = (sec >= 0) & (sec < NS)
        s, jour, sec = s[garde], jour[garde], sec[garde]
        fin = pd.Series(sec).groupby(jour.to_numpy()).max()
        garde = ~jour.isin(fin.index[fin < 12900]).to_numpy()
        s, jour, sec = s[garde], jour[garde], sec[garde]
        self.jours = pd.DatetimeIndex(np.sort(jour.unique()))
        ij = self.jours.get_indexer(jour)
        nj = len(self.jours)

        def grille(col, remplir):
            a = np.full((nj, NS), np.nan)
            a[ij, sec] = s[col].to_numpy(float)
            return pd.DataFrame(a).ffill(axis=1).bfill(axis=1).to_numpy() if remplir else np.nan_to_num(a)
        self.prix, self.bid, self.ask = grille("prix", True), grille("bid", True), grille("ask", True)
        brut_h, brut_b = np.full((nj, NS), np.nan), np.full((nj, NS), np.nan)
        brut_h[ij, sec], brut_b[ij, sec] = s["haut"].to_numpy(float), s["bas"].to_numpy(float)
        self.haut = np.where(np.isnan(brut_h), self.prix, brut_h)
        self.bas = np.where(np.isnan(brut_b), self.prix, brut_b)
        self.achat, self.vente = grille("achat", False), grille("vente", False)
        self.contrat = pd.Series(s["contrat"].to_numpy()).groupby(ij).agg(lambda x: x.mode().iloc[0]).to_numpy()

    def minutes(self):
        """Barres d'une minute (seance x minute) : o, h, l, c, achats, ventes."""
        r = lambda a: a.reshape(len(self.jours), NM, 60)
        return dict(o=r(self.prix)[:, :, 0], h=r(self.haut).max(axis=2), l=r(self.bas).min(axis=2),
                    c=r(self.prix)[:, :, -1], achats=r(self.achat).sum(axis=2), ventes=r(self.vente).sum(axis=2))


def footprint(jours):
    """Par seance et minute : ventes agressives aux deux prix les plus bas, achats aux deux prix les plus hauts, plus bas
    et plus haut traites (NaN si la minute n'a pas de footprint)."""
    f = pd.concat([pd.read_csv(p) for p in sorted(OF.glob("nq_footprint_*.csv.gz"))], ignore_index=True)
    f = f.drop_duplicates(["m", "prix"])
    m = pd.to_datetime(f["m"])
    jour = m.dt.normalize()
    minute = ((m - jour).dt.total_seconds() // 60 - 570).astype(int).to_numpy()
    garde = (minute >= 0) & (minute < NM) & jour.isin(jours).to_numpy()
    f, jour, minute = f[garde], jour[garde], minute[garde]
    cle = jours.get_indexer(jour) * NM + minute
    f = f.assign(cle=cle)
    g = f.groupby("cle")["prix"]
    bas, haut = g.transform("min"), g.transform("max")
    # deux prix les plus bas = plus bas et plus bas + 1 tick ; deux plus hauts = plus haut et plus haut - 1 tick
    v_bas = f["vente"].where(f["prix"] <= bas + TICK + TICK / 2, 0).groupby(f["cle"]).sum()
    a_haut = f["achat"].where(f["prix"] >= haut - TICK - TICK / 2, 0).groupby(f["cle"]).sum()
    out = {k: np.full(len(jours) * NM, np.nan) for k in ("ventes_bas2", "achats_haut2", "fp_bas", "fp_haut")}
    out["ventes_bas2"][v_bas.index] = v_bas.to_numpy()
    out["achats_haut2"][a_haut.index] = a_haut.to_numpy()
    out["fp_bas"][g.min().index] = g.min().to_numpy()
    out["fp_haut"][g.max().index] = g.max().to_numpy()
    return {k: v.reshape(len(jours), NM) for k, v in out.items()}


def exports(apres):
    """Seances des exports Rithmic (et FLUX_EXPORTS) posterieures a `apres`, completes (390 minutes)."""
    fichiers = [RITHMIC] + (sorted(Path(os.environ["FLUX_EXPORTS"]).glob("*.csv")) if os.getenv("FLUX_EXPORTS") else [])
    t = pd.concat([pd.read_csv(p).assign(fichier=i) for i, p in enumerate(fichiers)], ignore_index=True)
    t = t[pd.to_datetime(t["jour"]) > apres]
    t = t.sort_values("fichier").drop_duplicates(["jour", "minute"], keep="last")   # le dernier fichier l'emporte
    jours = []
    for j, g in t.groupby("jour"):
        g = g.sort_values("minute")
        if len(g) == NM and (g["minute"].to_numpy() == np.arange(NM)).all():
            jours.append((pd.Timestamp(j), g))
    return jours


def seances():
    """Toutes les seances dans l'ordre : dict de tableaux (seance x minute) et informations par seance."""
    S = Secondes()
    m = S.minutes()
    fp = footprint(S.jours)
    src = ["databento"] * len(S.jours)
    contrat = [str(c) for c in S.contrat]
    jours = list(S.jours)
    ex = exports(S.jours[-1])
    for j, g in ex:
        for k, col in (("o", "o"), ("h", "h"), ("l", "l"), ("c", "c"), ("achats", "achats"), ("ventes", "ventes")):
            m[k] = np.vstack([m[k], g[col].to_numpy(float)[None, :]])
        for k in fp:
            fp[k] = np.vstack([fp[k], np.full((1, NM), np.nan)])
        jours.append(j)
        src.append("export")
        contrat.append(str(g["contrat"].iloc[0]))
    m.update(fp)
    jours = pd.DatetimeIndex(jours)
    vol = m["achats"].sum(axis=1) + m["ventes"].sum(axis=1)
    # seance mince (volume < 40 % de la mediane des 20 seances d'avant) et premiere seance d'un nouveau contrat (dans
    # une meme source) : pas de trade (orderflow/README.md)
    mince = np.array([d > 0 and vol[d] < 0.4 * np.median(vol[max(0, d - 20):d]) for d in range(len(jours))])
    change = np.array([d > 0 and src[d] == src[d - 1] and contrat[d] != contrat[d - 1] for d in range(len(jours))])
    info = pd.DataFrame({"jour": jours, "source": src, "contrat": contrat, "mince": mince, "change": change})
    return m, info, S
