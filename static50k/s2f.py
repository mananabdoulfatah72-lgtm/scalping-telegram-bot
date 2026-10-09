#!/usr/bin/env python3
"""S2F 50K et plafond de ce que le bot peut verser (descriptif, demande de l'utilisateur du 9 octobre 2026), au niveau
d'aujourd'hui :
1. le bot seul (sans compte, sans limite), mois par mois : ce qu'il gagne un mois donne, c'est le maximum qu'un compte
   peut verser ce mois-la ;
2. un seul S2F 50K (regles de README.md, « Le S2F ») : retraits dans les 12 mois, compte perdu, retraits par mois.
Variantes montrees a titre descriptif (aucune n'est choisie ici). Ecrit s2f.txt."""
import numpy as np
import pandas as pd

import donnees as DN
import moteur_static as M
import outils as U
import static as S

INF = 1e12
PRIX_S2F = (570.0, 342.0)          # prix catalogue ; avec la promotion de 40 %
TIRAGES = 10


def bot_seul(D, b, dd):
    """Gain du bot sur les 21 seances qui suivent chaque depart (un mois), sans compte."""
    out = []
    for d in dd:
        tr = np.zeros(21)
        U.achat(D, b, d, "E0", h1=21, h2=21, perte=INF, objectif=INF, trace=tr)
        out.append(tr[-1])
    return np.array(out)


def un_s2f(D, b, dd, v, cap):
    rows = []
    for d in dd:
        ret = np.zeros(S.H1)
        r = U.achat(D, b, d, v, plafond=cap, h2=S.H1, retraits=ret, s2f=True)
        rows.append((r, ret))
    return rows


def resume(rows):
    R = np.array([r for r, _ in rows])
    P = np.array([p for _, p in rows])
    recu = R[:, M.RECU1]
    perdu = (R[:, M.PRO_PERDU] == 1) & (R[:, M.FIN_PRO] <= S.H1)
    prem = R[:, M.PREMIER]
    prem = prem[prem > 0]
    trim = [P[:, a:b].sum(axis=1).mean() / ((b - a) / 21) for a, b in ((0, 63), (63, 126), (126, 252))]
    vie = np.where(perdu, R[:, M.FIN_PRO], S.H1) / 21.0
    return {"achats": len(R), "recu": recu.mean(), "mediane": np.median(recu), "retrait": (recu > 0).mean(),
            "perdu": perdu.mean(), "premier": np.median(prem) if len(prem) else np.nan,
            "net570": (recu - PRIX_S2F[0]).mean(), "net342": (recu - PRIX_S2F[1]).mean(),
            "plus_que_prix": (recu > PRIX_S2F[0]).mean(), "trim": trim, "par_mois_vivant": recu.sum() / vie.sum()}


def ligne(nom, x):
    p = "-" if np.isnan(x["premier"]) else f"{x['premier'] / 21:.1f} mois"
    return (f"{nom} | {x['achats']} | {x['retrait']:.0%} | {x['recu']:,.0f} $ (mediane {x['mediane']:,.0f}) | "
            f"{x['trim'][0]:,.0f} / {x['trim'][1]:,.0f} / {x['trim'][2]:,.0f} $ | {x['par_mois_vivant']:,.0f} $ | "
            f"{x['perdu']:.0%} | {p} | {x['net570']:+,.0f} $ / {x['net342']:+,.0f} $ | {x['plus_que_prix']:.0%}")


def main():
    D = DN.charger()
    j, nj = D["jours"], len(D["jours"])
    b0 = U.base(D)
    bon = [U.base(D, g) for g in S.gardes_simules(D, S.rho_2026())[:TIRAGES]]
    inutile = [U.base(D, g) for g in S.gardes_simules(D, 0.0)[:TIRAGES]]
    dd = [d for d in U.departs(D) if j[d] >= pd.Timestamp("2012-01-01") and d + S.H1 <= nj]
    G = {"2012-2021": [d for d in dd if j[d] <= pd.Timestamp("2021-12-31")],
         "2023 - sept. 2025": [d for d in dd if j[d] >= pd.Timestamp("2023-01-01")],
         "2025": [d for d in dd if j[d].year == 2025]}
    L = ["S2F 50K et bot seul, au niveau d'aujourd'hui (descriptif)", ""]
    # 1. bot seul, un mois
    L += ["=== 1. Le bot seul (zone + RSI(2), 1 MNQ chacun), sans compte : gain sur un mois (21 seances)",
          "periode | zone | moyenne | mediane | mois perdants | 1 mois sur 10 sous | 1 mois sur 10 au-dessus"]
    dm = [d for d in U.departs(D, 1) if j[d] >= pd.Timestamp("2012-01-01") and d + 21 <= nj][::21]
    for nom, bases in (("sans filtre", [b0]), ("filtre aussi bon qu'en 2026 (simule)", bon), ("filtre inutile (simule)", inutile)):
        for per, a, z in (("2012-2021", "2012", "2021"), ("2023-2026", "2023", "2026"), ("2025-2026", "2025", "2026")):
            ds = [d for d in dm if a <= str(j[d].year) <= z]
            g = np.concatenate([bot_seul(D, b, ds) for b in bases])
            L.append(f"{per} | {nom} | {g.mean():+,.0f} $ | {np.median(g):+,.0f} $ | {(g < 0).mean():.0%} |"
                     f" {np.quantile(g, 0.1):+,.0f} $ | {np.quantile(g, 0.9):+,.0f} $")
    # 2. un S2F
    L += ["", "=== 2. Un seul S2F 50K, 12 mois (prix 570 $ catalogue / 342 $ avec 40 % de reduction)",
          "variante | achats | au moins un retrait | retraits moyens en 12 mois | retraits par mois : mois 1-3 / 4-6 / 7-12 |"
          " retraits par mois d'un compte en vie | compte perdu | 1er retrait (mediane) | net moyen (570 $ / 342 $) |"
          " rembourse au moins 570 $"]
    for per, ds in G.items():
        L.append(f"--- achats {per}")
        for v, c in (("E0", "P0"), ("E0", "P500"), ("E1", "P500"), ("E2", "P500"), ("E4", "P500")):
            L.append(ligne(f"{v} {c} sans filtre", resume(un_s2f(D, b0, ds, v, S.CAPS[c]))))
        for nom, bases in (("filtre aussi bon qu'en 2026", bon), ("filtre inutile", inutile)):
            rows = sum((un_s2f(D, b, ds, "E0", 500.0) for b in bases), [])
            x = resume(rows)
            x["achats"] = len(ds)
            L.append(ligne(f"E0 P500 {nom} (simule)", x))
        print("\n".join(L[-8:]), flush=True)
    (DN.ICI / "s2f.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
