"""Controle du moteur de l'usine contre les moteurs deja verifies du projet, avant tout resultat.

1. Zone (k = 1, 14 jours) contre zone_brute (chantier/inactivite.py, branche claude/loving-mccarthy-u21aw6), recopiee ici
   telle quelle : memes trades (seance, minute d'entree, sens, minute de sortie).
2. Zone contre le moteur C# du Bot 3 en 1 (Bot3en1.Replay, zone d'origine sans filtre), journal passe en argument.
3. Supertrend (10, 3) contre st_detail.py (branche claude/peaceful-cerf-8dowsi), dont les trades sont passes en argument
   (tableau T de st_cache.npz) : memes trades.

Usage : KB_MINUTES=... python3 usine/valider.py [journal_csharp_zone_origine.txt] [st_cache.npz]
"""
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402

N = Mo.N


def zone_brute(M, k, pas=30, jours=14):
    """Copie exacte de chantier/inactivite.py (zone corrigee V1 sans filtre)."""
    J, O, H, L, C, V, ok = M["J"], M["O"], M["H"], M["L"], M["C"], M["V"], M["ok"]
    S = len(J)
    mv = np.abs(C / O[:, :1] - 1)
    sigma = np.full_like(mv, np.nan)
    sigma[ok] = pd.DataFrame(mv[ok]).rolling(jours, min_periods=jours).mean().shift(1).values
    seg = np.cumsum(np.r_[0, (M["contrat"][1:] != M["contrat"][:-1]).astype(int)])
    idx = np.where(ok, np.arange(S), -1)
    prec = np.r_[-1, np.maximum.accumulate(idx)[:-1]]
    prec = np.where((prec >= 0) & (seg[np.maximum(prec, 0)] == seg), prec, -1)
    veille = np.where(prec >= 0, C[np.maximum(prec, 0), N - 1], np.nan)
    typ = (H + L + C) / 3; cv = np.cumsum(V, axis=1)
    vwap = np.where(cv > 0, np.cumsum(typ * V, axis=1) / np.where(cv > 0, cv, 1), np.cumsum(typ, axis=1) / np.arange(1, N + 1))
    out = []
    for d in range(S):
        if not ok[d] or np.isnan(veille[d]) or np.isnan(sigma[d, pas]):
            continue
        hr = max(O[d, 0], veille[d]); br = min(O[d, 0], veille[d]); pos = 0; e = 0.0; m0 = 0
        for m in range(pas, N, pas):
            p = C[d, m]; ub = hr * (1 + k * sigma[d, m]); lb = br * (1 - k * sigma[d, m])
            if pos > 0 and p <= max(ub, vwap[d, m]):
                out.append((d, 1, m0 + 1, m, e, p)); pos = 0
            elif pos < 0 and p >= min(lb, vwap[d, m]):
                out.append((d, -1, m0 + 1, m, e, p)); pos = 0
            if pos == 0:
                if p > ub:
                    pos, e, m0 = 1, p, m
                elif p < lb:
                    pos, e, m0 = -1, p, m
        if pos != 0:
            out.append((d, pos, m0 + 1, N - 1, e, C[d, N - 1]))
    return out


def positions_de(trades, S, ouverture=False):
    """Positions par minute (pg, pi) d'une liste de trades (seance, sens, premiere minute tenue, derniere minute tenue).
    ouverture=True (Supertrend) : la sortie se fait a l'ouverture de la minute suivante, dont l'ecart est encore tenu."""
    pg = np.zeros((S, N), np.int8); pi = np.zeros((S, N), np.int8)
    for s_, v, a, b in trades:
        pi[s_, a:b + 1] = v
        pg[s_, (a if not ouverture else a + 1):b + 1] = v
        if ouverture and b < 384:
            pg[s_, b + 1] = v
    return pg, pi


def identiques(A, B, seances):
    """Seances ou les deux jeux de positions sont identiques minute par minute."""
    return sum(int(np.array_equal(A[0][s], B[0][s]) and np.array_equal(A[1][s], B[1][s])) for s in seances)


def principal():
    D = Dn.charger()
    P = Mo.deriver(D)
    L = [f"Donnees : {len(D['J'])} seances, {int(D['complete'].sum())} completes, du {D['J'][0]} au {D['J'][-1]}.",
         "Faux prix corriges : " + ("; ".join(D["corrections"]) or "aucun"), ""]
    # 1. zone contre zone_brute
    M = dict(J=D["J"], O=D["O"], H=D["H"], L=D["L"], C=D["C"], V=D["V"], ok=D["complete"], contrat=D["seg"])
    S = len(D["J"]); comp = np.where(D["complete"])[0]
    tz = zone_brute(M, 1.0)
    ref = positions_de([(d, v, a, b) for d, v, a, b, e, x in tz], S)
    moi = Mo.STRATEGIES["zone"]["f"](P, 1.0, 14)
    jz = sorted({t[0] for t in tz})
    L.append(f"1. Zone (k = 1, 14 jours) contre zone_brute : {len(tz)} trades de reference sur {len(jz)} seances ; positions identiques "
             f"minute par minute dans {identiques(ref, moi, comp)} seances completes sur {len(comp)}.")
    # 2. zone contre le moteur C# (zone d'origine sans filtre)
    if len(sys.argv) > 1:
        idx = {j: i for i, j in enumerate(D["J"])}
        cs, ouv = set(), None
        lig = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)( 16h00)? (\d+)h(\d+) a ([0-9.]+)")
        for l in open(sys.argv[1], encoding="utf-8"):
            g = lig.match(l)
            if not g or "ecarte" in l or "RSI(2)" in l:
                continue
            mm = int(g.group(4)) * 60 + int(g.group(5)) - 570
            if g.group(2) in ("achat", "vente"):
                ouv = (g.group(1), 1 if g.group(2) == "achat" else -1, mm)
            elif ouv:
                cs.add((idx[ouv[0]], ouv[1], ouv[2] + 1, min(N - 1, mm))); ouv = None
        fin_cs = max(t[0] for t in cs)
        ref_cs = positions_de(sorted(cs), S)
        sc = [x for x in comp if x <= fin_cs]
        L.append(f"2. Zone contre le moteur C# du bot (zone d'origine sans filtre) : {len(cs)} trades C# ; positions identiques dans "
                 f"{identiques(ref_cs, moi, sc)} seances completes sur {len(sc)}. Ecarts attendus : le C# prend le contrat du "
                 f"calendrier et ne trade pas les jours courts ni les jours feries ; l'usine suit zone_brute.")
    # 3. Supertrend contre st_detail
    if len(sys.argv) > 2:
        z = np.load(sys.argv[2])
        T = z["T"]; Jst = z["J"]
        idx = {j: i for i, j in enumerate(D["J"])}
        ref = set()
        for t in T:
            s = idx.get(str(Jst[int(t[0])]))
            if s is not None:
                ref.add((s, int(t[1]), int(t[2]) + 1, int(t[3])))
        moi = Mo.STRATEGIES["supertrend"]["f"](P, 10, 3.0)
        refp = positions_de(sorted(ref), S, ouverture=True)
        L.append(f"3. Supertrend (10, 3) contre st_detail : {len(ref)} trades de reference ; positions identiques minute par minute "
                 f"dans {identiques(refp, moi, comp)} seances completes sur {len(comp)}.")
    (ICI / "resultats").mkdir(exist_ok=True)
    (ICI / "resultats/validation.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    principal()
