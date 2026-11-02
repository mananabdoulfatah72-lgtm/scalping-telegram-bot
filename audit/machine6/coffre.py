#!/usr/bin/env python3
"""Machine v6 : ouverture unique du coffre 2024 - 2026 (regles, version 2, point 3), plus le descriptif
(comptes bloques pres du plancher, avril - octobre 2026 avec le vrai delta)."""
import json
import numpy as np
import base as B
import machine as M
import sim

V1 = [dict(T=6, L=1000, G=300, B=1), dict(T=6, L=1000, G=300, S=0.5, B=1, J=1), dict(T=6, L=1000, G=300, S=0.5, F3=210),
      dict(T=6, L=1000, G=300, S=0.5, B=1)]
def genome(**kw):
    g = list(M.BASE)
    for i, (nom, vals, _, _) in enumerate(M.GENES):
        if nom in kw:
            g[i] = vals.index(kw[nom])
    return tuple(g)
fin2 = [tuple(f["genome"]) for f in json.load(open("resultats/finalistes_v2.json"))["finalistes"]]
cands = {f"v2-{i + 1}": g for i, g in enumerate(fin2)}
cands.update({f"v1-{i + 1}": genome(**d) for i, d in enumerate(V1)})
cands.update({"temoin a (4 / 1000)": genome(T=4, L=1000), "temoin b (6 / 1000)": genome(T=6, L=1000), "temoin c (2 / 500)": genome(T=2, L=500)})
# descriptif : delta reel avril - octobre 2026
SCR = B.SCR
D7 = sim.charger(f"{SCR}/risque/nq.csv", f"{SCR}/audit/f_c2q1.txt", cache=f"{SCR}/machine6_cache_f.npz")
td7 = D7["t_jour"]; nj = len(D7["jours"])
a7 = (np.searchsorted(td7, np.arange(nj), "left").astype(np.int64), np.searchsorted(td7, np.arange(nj), "right").astype(np.int64))
ARGS7 = (D7["O"], D7["H"], D7["L"], D7["C"], a7[0], a7[1], D7["t_sens"], D7["t_me"], D7["t_mx"], D7["t_e"], D7["t_x"], D7["t_w"], D7["t_niv"])
deb7 = np.arange(td7.min(), nj - 8).astype(np.int64)
lignes = ["Coffre 2024 - octobre 2026 (723 departs, ouvert une fois) ; score = P(reussite) - 0,5 x P(echec)", ""]
res = {}
for nom, g in cands.items():
    p, pris = M.parametres(g)
    r, e, x, n, bl = B.issues(p, M.PER["cof"], pris)
    gc = M.valeurs(g)["GC"]; gg = M.valeurs(g)["G"]
    seuil = max(gc, gg) + 50 if max(gc, gg) > 0 else 0
    # comptes en vie qui ne peuvent plus trader (marge <= garde + 50 $), sur les 15 ans
    deb = np.concatenate([M.PER[k] for k in ("ent", "tou", "cof")])
    rr, marge = sim.lot(deb, 8, p, 50000.0, 51500.0, *B.ARGS, pris, 53000.0, 2500.0, 50100.0)
    viv = rr == 0
    bloq = (viv & (marge <= seuil + 1e-6)).sum() / max(1, viv.sum()) * 100 if seuil else 0.0
    # delta reel (le filtre F n'utilise que dep, me, regime : on garde les trades tels quels, gestion seule)
    p7 = p.copy()
    r7, m7 = sim.lot(deb7, 8, p7, 50000.0, 51500.0, *ARGS7, np.ones(len(td7), np.bool_), 53000.0, 2500.0, 50100.0)
    res[nom] = dict(score=r - 0.5 * e, reussis=r, echoues=e, en_vie=x, bloques=bloq,
                    delta_reel=[(r7 == 1).mean() * 100, (r7 == -1).mean() * 100])
    lignes.append(f"{nom:22s} score {r - 0.5 * e:+6.1f}  reussis {r:5.1f} %  echoues {e:5.1f} %  en vie {x:5.1f} %"
                  f"  | 15 ans : en vie mais bloques {bloq:4.0f} %  | avr.-oct. 2026 vrai delta ({len(deb7)} departs) : reussis {(r7 == 1).mean() * 100:4.1f} %, echoues {(r7 == -1).mean() * 100:4.1f} %"
                  f"\n{'':22s} {M.valeurs(g)}")
best_tem = max(v["score"] for k, v in res.items() if k.startswith("temoin"))
lignes.append(f"\nmeilleur temoin au coffre : {best_tem:+.1f}")
for k, v in res.items():
    if not k.startswith("temoin"):
        lignes.append(f"controle 5 {k} : {'bat' if v['score'] > best_tem else 'ne bat pas'} le meilleur temoin")
open("resultats/coffre.txt", "w").write("\n".join(lignes) + "\n")
json.dump(res, open("resultats/coffre.json", "w"), indent=1)
print("\n".join(lignes))
