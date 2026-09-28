#!/usr/bin/env python3
"""Etapes 2 et 3 : les 4 strategies du protocole (README.md), puis les versions 5 et 6, pour le secteur classe premier a l'etape 1,
jugees par les 8 criteres fixes avant les backtests. Ecrit le journal des rejets.

Lancer depuis ce dossier, apres recherche.py : python3 strategies.py
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).parent
sys.path.insert(0, str(ICI))
import univers as U  # noqa: E402
from recherche import charger  # noqa: E402

FRAIS_ACTION, FRAIS_ETF = 5e-4, 3e-4          # par ordre, en fraction du montant echange
DEBUT_HIST = pd.Timestamp("2006-01-01")
AN, M3, M6 = 252, 63, 126
MOTEUR = {"XLE": ("hausse", "CL=F"), "XLB": ("hausse", "HG=F"), "XLI": ("hausse", "HG=F"), "XLF": ("hausse", "ecart"),
          "XLU": ("baisse", "^TNX"), "XLRE": ("baisse", "^TNX"), "XLK": ("baisse", "^TNX"), "XLC": ("baisse", "^TNX"),
          "XLY": ("baisse", "^TNX"), "XLV": ("refuge", None), "XLP": ("refuge", None)}
NOMS = {1: "Rotation (force relative du secteur)", 2: "Momentum des actions du secteur",
        3: "Faible risque (actions calmes du secteur)", 4: "Moteur macro du secteur",
        5: "Version 5 : moteur macro + filtre 200 jours vers liquidites",
        6: "Version 6 : momentum des actions + filtre 200 jours vers liquidites"}
CASH = "CASH"                                  # liquidites remunerees au taux court (sans frais)
MOMENTS = (1, 4, 5)                            # strategies qui choisissent quand etre dans le secteur
SELECTIONS = (2, 3, 6)                         # strategies qui choisissent des actions


# ----------------------------------------------------------------------------- simulation
def simuler(r, poids, frais):
    """r : rendements quotidiens (jours x titres). poids : poids cibles (dates de reequilibrage x titres),
    fixes a la cloture de ces jours. Les poids derivent avec les prix entre deux reequilibrages.
    Renvoie (rendement quotidien net de frais, contributions quotidiennes par titre)."""
    cols = list(r.columns)
    R = r.fillna(0.0).values
    cible = {r.index.get_loc(d): poids.loc[d].reindex(cols).fillna(0.0).values for d in poids.index}
    fr = frais.reindex(cols).values
    h = np.zeros(len(cols))
    net = np.zeros(len(R))
    contrib = np.zeros_like(R)
    for t in range(len(R)):
        g = h * R[t]
        contrib[t] = g
        port = g.sum()
        h = h * (1 + R[t]) / (1 + port) if 1 + port > 0 else np.zeros_like(h)
        cout = 0.0
        if t in cible:
            w = cible[t]
            cout = float(np.sum(np.abs(w - h) * fr))
            h = w.copy()
        net[t] = port - cout
    return pd.Series(net, r.index), pd.DataFrame(contrib, r.index, cols)


def fins_de_mois(index, debut):
    f = pd.DatetimeIndex(pd.Series(index, index=index).groupby(index.to_period("M")).last().values)
    return f[f >= debut]


# ----------------------------------------------------------------------------- les 4 strategies
class Etude:
    def __init__(self, secteur, retirer=()):
        adj, close = charger()
        self.adj, self.close, self.E = adj, close, secteur
        self.L = [a for a in U.ACTIONS[secteur] if a in adj.columns and a not in retirer]
        actifs = [U.MARCHE, secteur] + self.L
        self.titres = actifs + [CASH]
        self.r = adj[actifs].pct_change(fill_method=None)
        self.frais = pd.Series({t: 0.0 if t == CASH else FRAIS_ETF if t in (U.MARCHE, secteur) else FRAIS_ACTION
                                for t in self.titres})
        fins = fins_de_mois(adj.index, DEBUT_HIST - pd.Timedelta(days=40))
        self.fins = fins[fins < adj.index[-1]]          # pas de trade le dernier jour : aucune periode ne suit
        self.rf = (close["^IRX"].ffill() / 100 / AN).reindex(adj.index).fillna(0)
        self.r[CASH] = self.rf
        # l'histoire commence au plus tot en 2006, et au moins un an apres la creation de l'ETF du secteur
        self.debut = max(DEBUT_HIST, adj[secteur].first_valid_index() + pd.Timedelta(days=365))
        self._cache3 = None
        self._elig = {}

    def _etf_ou_spy(self, condition):
        w = pd.DataFrame(0.0, index=self.fins, columns=self.titres)
        for d in self.fins:
            existe = pd.notna(self.adj.at[d, self.E])
            w.loc[d, self.E if existe and condition(d) else U.MARCHE] = 1.0
        return w

    def s1(self):
        p, s = self.adj[self.E], self.adj[U.MARCHE]
        def cond(d):
            i = p.index.get_loc(d)
            if i < 200 or p.iloc[i - 199:i + 1].isna().any():
                return False
            return p.iloc[i] / p.iloc[i - M6] > s.iloc[i] / s.iloc[i - M6] and p.iloc[i] > p.iloc[i - 199:i + 1].mean()
        return self._etf_ou_spy(cond)

    def s4(self):
        sens, x = MOTEUR[self.E]
        c = self.close
        if x == "ecart":
            serie = c["^TNX"] - c["^IRX"]
        elif x is not None:
            serie = c[x]
        serie = serie.ffill() if x is not None else None
        spy = self.adj[U.MARCHE]
        def cond(d):
            i = self.adj.index.get_loc(d)
            if sens == "refuge":
                return spy.iloc[i] < spy.iloc[i - 199:i + 1].mean()
            v = serie.iloc[i] - serie.iloc[i - M3]
            return v > 0 if sens == "hausse" else v < 0
        return self._etf_ou_spy(cond)

    def eligibles(self, i):
        """Actions cotees sur toute l'annee precedente (calcule une seule fois par date)."""
        if i not in self._elig:
            ok = self.adj[self.L].iloc[i - AN:i + 1].notna().all()
            self._elig[i] = [a for a in self.L if ok[a]]
        return self._elig[i]

    def vol_propre(self, d):
        """Volatilite propre (ecart au secteur) sur 6 mois de chaque action eligible, calculee une seule fois."""
        if self._cache3 is None:
            self._cache3 = {}
        if d not in self._cache3:
            i = self.r.index.get_loc(d)
            fen = self.r.iloc[i - M6 + 1:i + 1]
            e = fen[self.E].fillna(0)
            vol = {}
            for a in self.eligibles(i):
                y = fen[a].fillna(0)
                b = np.cov(y, e)[0, 1] / e.var() if e.var() > 0 else 0.0
                vol[a] = float((y - b * e).std() * np.sqrt(AN))
            self._cache3[d] = pd.Series(vol, dtype=float)
        return self._cache3[d]

    def s2(self, hasard=None):
        w = pd.DataFrame(0.0, index=self.fins, columns=self.titres)
        p = self.adj[self.L]
        for d in self.fins:
            i = p.index.get_loc(d)
            el = self.eligibles(i)
            if len(el) < 3:
                w.loc[d, self.E] = 1.0
                continue
            if hasard is not None:
                choix = list(hasard.choice(el, size=min(5, len(el)), replace=False))
            else:
                mom = p.iloc[i - 21][el] / p.iloc[i - M6][el] - 1
                choix = list(mom.sort_values(ascending=False).index[:5])
            w.loc[d, choix] = 1.0 / len(choix)
        return w

    def s3(self, hasard=None):
        w = pd.DataFrame(0.0, index=self.fins, columns=self.titres)
        for d in self.fins:
            i = self.r.index.get_loc(d)
            el = self.eligibles(i)
            if len(el) < 3:
                w.loc[d, self.E] = 1.0
                continue
            vol = self.vol_propre(d)
            choix = list(hasard.choice(el, size=min(5, len(el)), replace=False)) if hasard is not None \
                else list(vol.sort_values().index[:5])
            inv = 1 / vol[choix]
            w.loc[d, choix] = (inv / inv.sum()).values
        return w

    def filtre(self, w):
        """Versions 5 et 6 : si SPY cloture le mois sous sa moyenne 200 jours, tout en liquidites."""
        spy = self.adj[U.MARCHE]
        w = w.copy()
        for d in w.index:
            i = spy.index.get_loc(d)
            if spy.iloc[i] < spy.iloc[i - 199:i + 1].mean():
                w.loc[d] = 0.0
                w.loc[d, CASH] = 1.0
        return w

    def poids(self, k, hasard=None):
        return {1: self.s1, 2: lambda: self.s2(hasard), 3: lambda: self.s3(hasard), 4: self.s4,
                5: lambda: self.filtre(self.s4()), 6: lambda: self.filtre(self.s2(hasard))}[k]()


# ----------------------------------------------------------------------------- mesures et criteres
def mesures(x, rf):
    ex = x - rf.reindex(x.index).fillna(0)
    eq = (1 + x).cumprod()
    return {"rendement": float(eq.iloc[-1] - 1), "cagr": float(eq.iloc[-1] ** (AN / len(x)) - 1),
            "sharpe": float(ex.mean() / ex.std() * np.sqrt(AN)) if ex.std() > 0 else 0.0,
            "pire_baisse": float((eq / eq.cummax().clip(lower=1.0) - 1).min())}


def juger(et, k, rng, n_placebo):
    w = et.poids(k)
    net, contrib = simuler(et.r, w, et.frais)
    net2, _ = simuler(et.r, w, et.frais * 2)
    debut = w.index[w.index >= et.debut][0]
    fin = et.r.index[-1]
    an = et.r.index[et.r.index > fin - pd.Timedelta(days=365)]
    h = net[net.index > debut]
    spy = et.r[U.MARCHE][h.index].fillna(0)
    m12, m12_2, s12 = mesures(net[an], et.rf), mesures(net2[an], et.rf), mesures(spy[an], et.rf)
    mh, sh = mesures(h, et.rf), mesures(spy, et.rf)
    c = contrib.loc[an].sum()
    part = float(c.drop([U.MARCHE, et.E, CASH], errors="ignore").max() / c.sum()) if c.sum() > 0 and k in SELECTIONS else None
    # placebo sur toute l'histoire
    if k in MOMENTS:
        ps = []
        for _ in range(n_placebo):   # la meme suite de positions (secteur / SPY / liquidites), decalee au hasard
            ordre = np.roll(np.arange(len(w)), rng.integers(12, len(w) - 12))
            wp = pd.DataFrame(w.values[ordre], index=w.index, columns=w.columns)
            ps.append(mesures(simuler(et.r, wp, et.frais)[0][h.index], et.rf)["sharpe"])
    else:
        ps = [mesures(simuler(et.r, et.poids(k, rng), et.frais)[0][h.index], et.rf)["sharpe"] for _ in range(n_placebo)]
    centile = float(np.mean(np.array(ps) < mh["sharpe"]))
    criteres = {
        "1 bat SPY sur 12 mois": m12["rendement"] > s12["rendement"],
        "2 idem avec frais doubles": m12_2["rendement"] > s12["rendement"],
        "3 pire baisse < 30 %": mh["pire_baisse"] > -0.30,
        "4 Sharpe 12 mois > 1": m12["sharpe"] > 1.0,
        "5 aucune action > 40 % des gains": part is None or part <= 0.40,
        "7 bat SPY sur toute l'histoire": mh["cagr"] > sh["cagr"],
        "8 placebo battu a 95 %": centile >= 0.95,
    }
    return {"nom": NOMS[k], "debut": str(debut.date()), "fin": str(fin.date()),
            "12_mois": m12, "12_mois_frais_doubles": m12_2, "spy_12_mois": s12, "histoire": mh, "spy_histoire": sh,
            "part_max_action": part, "placebo_centile": centile, "placebo_moyen": float(np.mean(ps)),
            "part_du_temps_dans_le_secteur": float((w.loc[w.index >= debut, et.E] > 0).mean()) if k in MOMENTS else None,
            "part_du_temps_en_liquidites": float((w.loc[w.index >= debut, CASH] > 0).mean()),
            "criteres": criteres}, net


def tout(secteur, n_placebo, graine=0):
    et = Etude(secteur)
    rng = np.random.default_rng(graine)
    res, series = {}, {}
    for k in (1, 2, 3, 4, 5, 6):
        res[k], series[k] = juger(et, k, rng, n_placebo)
    return res, series, et


def empreinte(res):
    return hashlib.sha256(json.dumps(res, sort_keys=True, default=str).encode()).hexdigest()[:16]


def tuer(et, k, net):
    """Tests pour essayer de casser une strategie qui a tout passe."""
    out = {}
    for nom, a, z in [("crise 2008", "2008-01-01", "2009-03-09"), ("krach du petrole 2014-2016", "2014-06-20", "2016-02-11"),
                      ("Covid 2020", "2020-02-19", "2020-04-30"), ("hausse des taux 2022", "2022-01-01", "2022-12-31"),
                      ("2023-2026", "2023-01-01", "2026-12-31")]:
        x = net[(net.index >= a) & (net.index <= z)]
        s = et.r[U.MARCHE][x.index].fillna(0)
        out[nom] = {"strategie": float((1 + x).prod() - 1), "spy": float((1 + s).prod() - 1)}
    if k in SELECTIONS:
        w = et.poids(k)
        _, contrib = simuler(et.r, w, et.frais)
        an = et.r.index[et.r.index > et.r.index[-1] - pd.Timedelta(days=365)]
        meilleur = contrib.loc[an].drop(columns=[U.MARCHE, et.E, CASH]).sum().idxmax()
        et2 = Etude(et.E, retirer=(meilleur,))
        w2 = et2.poids(k)
        n2, _ = simuler(et2.r, w2, et2.frais)
        s12 = (1 + et2.r[U.MARCHE][an].fillna(0)).prod() - 1
        out["sans la meilleure action (" + meilleur + ")"] = {"strategie_12_mois": float((1 + n2[an]).prod() - 1), "spy_12_mois": float(s12)}
    return out


def main():
    premier = json.loads((ICI / "recherche.json").read_text())["premier"]
    print(f"Secteur classe premier a l'etape 1 : {premier} ({U.SECTEURS[premier]})\n", flush=True)
    res, series, et = tout(premier, n_placebo=300)
    emp = empreinte(res)
    f_emp = ICI / "empreinte.txt"
    avant = f_emp.read_text().strip() if f_emp.exists() else None
    f_emp.write_text(emp + "\n")
    meme = (avant == emp) if avant else None
    print(f"Empreinte des resultats : {emp} ; execution precedente : {avant or 'aucune'} -> "
          + ("identiques" if meme else ("DIFFERENTES" if meme is False else "a relancer pour verifier")) + "\n", flush=True)
    journal = {}
    for k, v in res.items():
        v["criteres"]["6 deterministe (2 executions identiques)"] = bool(meme)
        ok = all(v["criteres"].values())
        m, s = v["12_mois"], v["spy_12_mois"]
        mh, sh = v["histoire"], v["spy_histoire"]
        print(f"Strategie {k} - {v['nom']} : {'PASSE' if ok else 'REJETEE'}")
        print(f"   12 derniers mois : {m['rendement']:+.1%} (SPY {s['rendement']:+.1%}) | frais doubles {v['12_mois_frais_doubles']['rendement']:+.1%}"
              f" | Sharpe {m['sharpe']:.2f} | part max d'une action "
              + (f"{v['part_max_action']:.0%}" if v["part_max_action"] is not None else "sans objet"))
        print(f"   depuis {v['debut']} : {mh['cagr']:+.1%}/an (SPY {sh['cagr']:+.1%}/an) | Sharpe {mh['sharpe']:.2f} (SPY {sh['sharpe']:.2f})"
              f" | pire baisse {mh['pire_baisse']:.0%} (SPY {sh['pire_baisse']:.0%}) | placebo battu {v['placebo_centile']:.0%}"
              + (f" | dans le secteur {v['part_du_temps_dans_le_secteur']:.0%} du temps" if v["part_du_temps_dans_le_secteur"] is not None else ""))
        rates = [c for c, b in v["criteres"].items() if not b]
        print("   criteres rates : " + (", ".join(rates) if rates else "aucun"), flush=True)
        if ok:
            v["tests_pour_tuer"] = tuer(et, k, series[k])
            for nom, t in v["tests_pour_tuer"].items():
                print(f"   test pour tuer - {nom} : " + " | ".join(f"{a} {b:+.1%}" for a, b in t.items()), flush=True)
        journal[k] = v
        print(flush=True)
        (ICI / "resultats.json").write_text(json.dumps({"secteur": premier, "empreinte": emp, "strategies": journal},
                                                        indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
