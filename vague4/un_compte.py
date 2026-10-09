#!/usr/bin/env python3
"""Un seul challenge Topstep 50K (vague 4, descriptif, demande de l'utilisateur du 9 octobre 2026, ecrit apres les
resultats de partie_a.txt) : combien par mois, en combien de temps on valide, et le risque de toucher le seuil de perte.
Bots : zone seule et zone + A3 (RSI(2) de nuit seulement sur 1 MES), au niveau d'aujourd'hui :
1. le bot seul, sans compte ni limite : gains par mois du calendrier, 2023 - sept. 2026 ;
2. un challenge achete : issue, temps pour valider, premier retrait, compte finance perdu, argent net sur 12 mois ;
3. achats recents (avril - juin 2026), avec le vrai filtre ;
4. un seul compte a la fois, rachete des qu'il est perdu : gains nets par mois du calendrier ;
sans filtre, puis avec le filtre delta simule (aussi bon qu'en 2026 / inutile, TIRAGES tirages), et le vrai filtre
(avril - septembre 2026, achats recents, suivi tronque a la fin des donnees). Ecrit un_compte.txt."""
import numpy as np
import pandas as pd

import donnees4 as D4
import moteur4 as M4
import vague4 as V

S, CP, F = V.S, V.CP, V.F
NC = "Topstep"
TIRAGES = 10
MOIS = 21                                                         # seances de bourse par mois
BOTS = {"zone seule": 0, "zone + A3": 4}
H2 = 2 * M4.UN_AN                                                 # un compte suivi 24 mois au plus (comme static50k)
DEPARTS = 20


def un_achat(D, b, d, rsi):
    """Un challenge achete le jour d. Renvoie (issue, seances du challenge, finance perdu, recu net de la part, net,
    seance du 1er retrait, seances de vie du compte finance, retraits par seance apres l'achat)."""
    e, f_ = CP.COMPTES[NC][:7], F.FINANCES[NC]["f"]
    prix, mensuel, activation = F.FINANCES[NC]["prix"]
    part = F.FINANCES[NC]["part"]
    fn, fe = D4.facteurs(D, d)
    ret = np.zeros(M4.UN_AN)
    r = M4.parcours4(d, rsi, 2.0 * fn, 5.0 * fe, ret, *b, *e, *f_)
    cout = prix * (np.ceil(r[1] / MOIS) if mensuel else 1.0) + (activation if r[0] == 1 else 0.0)
    vie = r[6] - r[1] if r[0] == 1 else 0
    return r[0], r[1], r[2], r[4] * part, r[4] * part - cout, r[5], vie, ret * part


def resume(rows):
    iss = np.array([x[0] for x in rows])
    nch = np.array([x[1] for x in rows])
    recu = np.array([x[3] for x in rows])
    net = np.array([x[4] for x in rows])
    prem = np.array([x[5] for x in rows])
    vie = np.array([x[6] for x in rows], float)
    perdu = np.array([x[2] for x in rows])
    ret = np.array([x[7] for x in rows])
    ok, ko = iss == 1, iss == -1
    q = np.percentile(nch[ok], [25, 50, 75]) if ok.any() else [np.nan] * 3
    tranches = [(0, MOIS), (MOIS, 2 * MOIS), (2 * MOIS, 3 * MOIS), (3 * MOIS, 6 * MOIS), (6 * MOIS, M4.UN_AN + 1)]
    par_mois = ret[:, :12 * MOIS].reshape(len(rows), 12, MOIS).sum(axis=2).mean(axis=0)
    return {"n": len(rows), "reussi": ok.mean(), "perdu": ko.mean(), "en_cours": (iss == 0).mean(),
            "q": q, "tranches": [((nch >= a) & (nch < z) & ok).mean() for a, z in tranches],
            "perte_med": float(np.median(nch[ko])) if ko.any() else np.nan,
            "retrait": (recu > 0).mean(), "prem_med": float(np.median(prem[prem >= 0])) if (prem >= 0).any() else np.nan,
            "fin_perdu": perdu[ok].mean() if ok.any() else np.nan,
            "vie_med": float(np.median(vie[ok])) if ok.any() else np.nan,
            "en_vie": recu.sum() / (vie.sum() / MOIS) if vie.sum() > 0 else 0.0,
            "net": net.mean(), "net_med": float(np.median(net)), "net_neg": (net < 0).mean(),
            "net_pire": net.min(), "recu": recu.mean(), "par_mois": par_mois}


def texte(nom, x):
    m = lambda s: f"{s / MOIS:.1f} mois" if s == s else "-"                      # noqa: E731
    pc = lambda p: f"{p:.0%}" if p == p else "-"                                # noqa: E731
    pm = x["par_mois"]
    return [f"{nom} ({x['n']} achats)",
            f"  challenge : reussi {x['reussi']:.0%} ; seuil de perte touche {x['perdu']:.0%} (au bout de "
            f"{m(x['perte_med'])} en mediane) ; ni l'un ni l'autre en 12 mois {x['en_cours']:.0%}",
            f"  temps pour valider (challenges reussis) : 1 sur 4 en {m(x['q'][0])}, la moitie en {m(x['q'][1])}, 3 sur 4"
            f" en {m(x['q'][2])} ; part des achats valides en moins d'1 mois {x['tranches'][0]:.0%}, 1-2 mois"
            f" {x['tranches'][1]:.0%}, 2-3 mois {x['tranches'][2]:.0%}, 3-6 mois {x['tranches'][3]:.0%}, 6-12 mois"
            f" {x['tranches'][4]:.0%}",
            f"  au moins un retrait {x['retrait']:.0%} (le 1er au bout de {m(x['prem_med'])} apres l'achat, en mediane) ;"
            f" compte finance perdu dans l'annee {pc(x['fin_perdu'])} (vie mediane {m(x['vie_med'])}) ; retraits par"
            f" mois d'un compte finance en vie {x['en_vie']:,.0f} $",
            f"  argent net sur 12 mois : moyenne {x['net']:+,.0f} $ ({x['net'] / 12:+,.0f} $ par mois) ; mediane"
            f" {x['net_med']:+,.0f} $ ; achats perdants {x['net_neg']:.0%} ; pire {x['net_pire']:+,.0f} $",
            f"  retraits moyens par mois apres l'achat : mois 1-3 {pm[:3].mean():,.0f} $ ; 4-6 {pm[3:6].mean():,.0f} $ ;"
            f" 7-12 {pm[6:].mean():,.0f} $"]


def bot_seul(D, b, rsi, d0, d1):
    """Sans compte ni limite, au niveau d'aujourd'hui : gain de chaque seance de d0 a d1 (inclus)."""
    veut, out = 0, np.zeros(d1 - d0 + 1)
    for i, d in enumerate(range(d0, d1 + 1)):
        fn, fe = D4.facteurs(D, d)
        r = M4.seance4(d, rsi, veut, 0.0, 0.0, -1e12, 0, 1e12, 1e12, 0.0, *b, 2.0 * fn, 5.0 * fe)
        veut, out[i] = r[2], r[1]
    return out


def mensuel(D, gains, d0):
    j = D["jours"]
    return pd.Series(gains).groupby(pd.PeriodIndex(j[d0:d0 + len(gains)], freq="M")).sum()


def ligne_mois(nom, s):
    return (f"{nom} : {s.mean():+,.0f} $ par mois en moyenne ; mediane {s.median():+,.0f} $ ; mois perdants"
            f" {(s < 0).mean():.0%} ; pire mois {s.min():+,.0f} $ ; meilleur {s.max():+,.0f} $")


def chaine(D, b, rsi, d, w1):
    """Un seul compte a la fois, de d a w1 : challenge achete (seance ou le RSI(2) est a plat), rachete des qu'il est perdu
    (challenge ou compte finance) ; un compte encore en vie apres H2 seances est rachete (prudent). Renvoie les flux de
    chaque seance (retraits recus, part comprise, moins abonnements et activation) et le nombre de challenges achetes."""
    e, f_ = CP.COMPTES[NC][:7], F.FINANCES[NC]["f"]
    prix, mensuel, activation = F.FINANCES[NC]["prix"]
    part = F.FINANCES[NC]["part"]
    flux, n = np.zeros(len(D["jours"])), 0
    while True:
        while d < w1 and D["ouvert"][d] != 0:
            d += 1
        if d >= w1:
            return flux, n
        fn, fe = D4.facteurs(D, d)
        h = min(H2, w1 - d)
        ret = np.zeros(h)
        r = M4.parcours4(d, rsi, 2.0 * fn, 5.0 * fe, ret, *b, *e, *f_, h)
        for k in range(int(np.ceil(r[1] / MOIS)) if mensuel else 1):
            flux[d + MOIS * k] -= prix
        if r[0] == 1:
            flux[d + r[1] - 1] -= activation
        flux[d:d + h] += ret * part
        n += 1
        d += r[6]


def main():
    D = D4.charger()
    j, nj = D["jours"], len(D["jours"])
    nz = len(D["Z"])
    rho = S.rho_2026()
    gs = {"filtre aussi bon qu'en 2026 (simule)": S.gardes_simules(D, rho)[:TIRAGES],
          "filtre inutile (simule)": S.gardes_simules(D, 0.0)[:TIRAGES]}
    assert len(gs["filtre inutile (simule)"]) == TIRAGES, "static.TIRAGES < TIRAGES"
    scen = {"sans filtre": [D4.base(D)]} | {k: [D4.base(D, g) for g in v] for k, v in gs.items()}
    L = [f"Un seul challenge {NC} 50K, niveau d'aujourd'hui (descriptif, ecrit apres les resultats). Filtre simule :"
         f" rho {rho:.2f}, {TIRAGES} tirages. Donnees jusqu'au {j[-1].date()}.", ""]

    # 1. le bot seul, sans compte
    d0 = int(np.searchsorted(j, pd.Timestamp("2023-01-01")))
    L.append(f"=== 1. Le bot seul, sans compte ni limite, 1 MNQ (+ 1 MES de nuit pour A3), {j[d0].date()} - {j[-1].date()}")
    seul = {}
    for sc, bases in scen.items():
        for nb, rsi in BOTS.items():
            s = sum(mensuel(D, bot_seul(D, bb, rsi, d0, nj - 1), d0) for bb in bases) / len(bases)
            seul[(sc, nb)] = s
            L.append(ligne_mois(f"{nb}, {sc}", s))
    a3 = mensuel(D, bot_seul(D, D4.base(D, np.zeros(nz, bool)), 4, d0, nj - 1), d0)
    L.append(ligne_mois("A3 seul (sans la zone)", a3))
    # vrai filtre, avril - septembre 2026
    gv = S.garde_vrai(D)
    d26 = int(np.searchsorted(j, pd.Timestamp("2026-04-01")))
    L.append(f"--- vrai filtre delta, {j[d26].date()} - {j[-1].date()} (6 mois seulement)")
    for nb, rsi in BOTS.items():
        for nom, g in (("sans filtre", np.ones(nz, bool)), ("vrai filtre", gv)):
            s = mensuel(D, bot_seul(D, D4.base(D, g), rsi, d26, nj - 1), d26)
            L.append(ligne_mois(f"{nb}, {nom}", s) + " ; " + ", ".join(f"{p.strftime('%m/%y')} {v:+,.0f}"
                                                                         for p, v in s.items()))
    print("\n".join(L), flush=True)

    # 2. un challenge achete
    dd = [d for d in range(260, nj) if D["ouvert"][d] == 0][::5]
    G = {"verification 2023 - sept. 2025": [d for d in dd if j[d] >= pd.Timestamp("2023-01-01") and d + M4.UN_AN <= nj],
         "achats de 2025": [d for d in dd if j[d].year == 2025 and d + M4.UN_AN <= nj],
         "choix 2012-2021": [d for d in dd if pd.Timestamp("2012-01-01") <= j[d] <= pd.Timestamp("2021-12-31")]}
    for g, ds in G.items():
        for sc, bases in scen.items():
            for nb, rsi in BOTS.items():
                rows = [un_achat(D, bb, d, rsi) for bb in bases for d in ds]
                x = resume(rows)
                x["n"] = len(ds)                                  # achats distincts (chacun joue len(bases) fois)
                L += ["", f"=== 2. {g} | {sc}"] if nb == "zone seule" else []
                L += texte(nb, x)
        print("\n".join(L[-14:]), flush=True)

    # 3. achats recents, vrai filtre (suivi tronque au dernier jour des donnees)
    dr = [d for d in range(d26, nj) if D["ouvert"][d] == 0 and j[d] <= pd.Timestamp("2026-06-30")]
    L += ["", f"=== 3. Achats de chaque seance du {j[dr[0]].date()} au {j[dr[-1]].date()} ({len(dr)} achats, qui se"
              f" chevauchent), suivis jusqu'au {j[-1].date()} seulement (3 a 6 mois)"]
    for nb, rsi in BOTS.items():
        for nom, g in (("sans filtre", np.ones(nz, bool)), ("vrai filtre", gv)):
            r = [un_achat(D, D4.base(D, g), d, rsi) for d in dr]
            iss = np.array([x[0] for x in r])
            nch = np.array([x[1] for x in r])
            v = nch[iss == 1]
            L.append(f"{nb}, {nom} : reussi {(iss == 1).mean():.0%} ; seuil touche {(iss == -1).mean():.0%} ; pas fini"
                     f" {(iss == 0).mean():.0%} ; temps median pour valider "
                     + (f"{np.median(v) / MOIS:.1f} mois" if len(v) else "-"))

    # 4. un seul compte a la fois
    for w, (a, z) in {"2023 - sept. 2026": ("2023-01-01", None), "2012 - 2022": ("2012-01-01", "2023-01-01")}.items():
        w0 = int(np.searchsorted(j, pd.Timestamp(a)))
        w1 = nj if z is None else int(np.searchsorted(j, pd.Timestamp(z)))
        mc = pd.PeriodIndex(j[w0:w1], freq="M")
        ans = sorted(set(mc.year))
        L += ["", f"=== 4. Un seul compte a la fois, rachete des qu'il est perdu, {j[w0].date()} - {j[w1 - 1].date()}"
                  f" ({DEPARTS} dates de depart, une seance sur cinq a partir du {j[w0].date()}) : gains nets par mois du"
                  f" calendrier (retraits - abonnements - activation)",
              "bot | scenario | moyenne par mois | mois median | mois > 0 | mois < 0 | challenges achetes par an | "
              "moyenne par mois selon le depart (min - max) | par annee : moyenne par mois"]
        for sc, bases in scen.items():
            for nb, rsi in BOTS.items():
                M_, nbuy = [], []
                for bb in bases:
                    for k in range(DEPARTS):
                        fl, n = chaine(D, bb, rsi, w0 + 5 * k, w1)
                        M_.append(pd.Series(fl[w0:w1]).groupby(mc).sum())
                        nbuy.append(n / ((w1 - w0) / M4.UN_AN))
                tous = pd.concat(M_, axis=1)
                moy = tous.mean(axis=1)
                par_an = moy.groupby(moy.index.year).mean()
                L.append(f"{nb} | {sc} | {moy.mean():+,.0f} $ | {tous.stack().median():+,.0f} $ |"
                         f" {(tous > 0).to_numpy().mean():.0%} | {(tous < 0).to_numpy().mean():.0%} |"
                         f" {np.mean(nbuy):.1f} | {tous.mean().min():+,.0f} a {tous.mean().max():+,.0f} $ | "
                         + ", ".join(f"{y} {par_an[y]:+,.0f}" for y in ans))
                print(L[-1], flush=True)
    (D4.ICI / "un_compte.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L[-5:]))


if __name__ == "__main__":
    main()
