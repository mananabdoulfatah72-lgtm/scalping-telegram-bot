#!/usr/bin/env python3
"""Niveau 1 (ml/REGLES.md) : ACP du radar et du NQ intrajournalier, descente de gradient / momentum / Adam sur Rosenbrock."""
import json

import numpy as np

import donnees as D

out = {}
txt = ["# Niveau 1 : fondations\n"]

# ------------------------------------------------------------------ 1a. ACP des marches du radar
EXCLUS = ("^VIX", "^VXN", "^VVIX", "^TNX", "^IRX", "^FVX", "^TYX", "^MOVE", "^SKEW", "^GVZ", "^OVX", "VXX", "SVXY")
R = D.radar("c")
R = R[(R.index >= "2015-01-02") & (R.index <= "2026-10-30")]
jours_us = R["SPY"].dropna().index
R = R.loc[jours_us]
garder = [s for s in R.columns if not s.startswith(EXCLUS) and R[s].notna().mean() >= 0.90]
X = np.log(R[garder].ffill()).diff().iloc[1:]
X = X.where(R[garder].iloc[1:].notna(), np.nan).fillna(0.0)
T, Nn = X.shape
Z = (X - X.mean()) / X.std(ddof=0)
Cm = np.corrcoef(Z.to_numpy().T)
val, vec = np.linalg.eigh(Cm)
ordre = np.argsort(val)[::-1]; val, vec = val[ordre], vec[:, ordre]
part = val / val.sum()
mp = (1 + np.sqrt(Nn / T)) ** 2
reels = int((val > mp).sum())
noms = np.array(garder)
facteurs = []
for k in range(5):
    v = vec[:, k] * np.sign(vec[:, k].sum() or 1)
    haut = np.argsort(-v)[:6]; bas = np.argsort(v)[:4]
    facteurs.append(dict(k=k + 1, part=float(part[k]), plus=[[noms[i], float(v[i])] for i in haut], moins=[[noms[i], float(v[i])] for i in bas]))
out["acp_radar"] = dict(series=int(Nn), jours=int(T), valeurs=[float(v) for v in val], part=[float(p) for p in part], borne_mp=float(mp),
                        reelles=reels, cumul={str(k): float(part[:k].sum()) for k in (1, 3, 5, 10, 20)}, facteurs=facteurs)
txt.append(f"## 1a. ACP : {Nn} marchés du radar, {T} jours (2015 - 2026)\n")
txt.append(f"- Composante 1 : {part[0]:.1%} de la variance ; 5 premières : {part[:5].sum():.1%} ; 10 premières : {part[:10].sum():.1%}.")
txt.append(f"- Borne de Marchenko-Pastur (bruit pur de même taille) : λ+ = {mp:.2f}. Valeurs propres au-dessus : **{reels}** composantes réelles.")
for f in facteurs:
    txt.append(f"- Facteur {f['k']} ({f['part']:.1%}) : en + " + ", ".join(f"{n} {w:+.2f}" for n, w in f["plus"][:5]) + " ; en − " + ", ".join(f"{n} {w:+.2f}" for n, w in f["moins"][:3]))

# ------------------------------------------------------------------ 1a bis. ACP du NQ intrajournalier (13 demi-heures)
J, O, H, L, C, V, ok = D.nq_minutes()
ref = np.column_stack([O[:, 0]] + [C[:, 30 * k - 1] for k in range(1, 13)])
fin = np.column_stack([C[:, 30 * (k + 1) - 1] for k in range(13)])
Y = np.log(fin / ref)[ok]
Cy = np.corrcoef(Y.T)
vy = np.sort(np.linalg.eigvalsh(Cy))[::-1]
mpy = (1 + np.sqrt(13 / len(Y))) ** 2
out["acp_nq"] = dict(seances=int(len(Y)), valeurs=[float(v) for v in vy], part=[float(v / vy.sum()) for v in vy], borne_mp=float(mpy), reelles=int((vy > mpy).sum()),
                     correlations=[[float(x) for x in r] for r in Cy])
txt.append(f"\n## 1a bis. ACP des 13 demi-heures du NQ ({len(Y)} séances complètes, 2011 - 2026)\n")
txt.append(f"- Valeurs propres : " + ", ".join(f"{v:.2f}" for v in vy) + f" ; borne de bruit {mpy:.3f}.")
txt.append(f"- Composantes au-dessus du bruit : **{int((vy > mpy).sum())}** ; la première porte {vy[0] / vy.sum():.1%} de la variance "
           f"(13 demi-heures indépendantes donneraient 7,7 % chacune).")
off = Cy[np.triu_indices(13, 1)]
txt.append(f"- Corrélation entre demi-heures d'une même séance : moyenne {off.mean():+.3f}, de {off.min():+.3f} à {off.max():+.3f}.")


# ------------------------------------------------------------------ 1b. Optimisation sur Rosenbrock
def f_ros(p): return (1 - p[0]) ** 2 + 100 * (p[1] - p[0] ** 2) ** 2
def g_ros(p): return np.array([-2 * (1 - p[0]) - 400 * p[0] * (p[1] - p[0] ** 2), 200 * (p[1] - p[0] ** 2)])


def optimiser(methode, lr, max_pas=100_000, garder_chemin=False):
    p = np.array([-1.0, 1.0]); m = np.zeros(2); v = np.zeros(2); chemin = [p.copy()]
    for t in range(1, max_pas + 1):
        g = g_ros(p)
        if methode == "GD":
            p = p - lr * g
        elif methode == "Momentum":
            m = 0.9 * m + g; p = p - lr * m
        else:
            m = 0.9 * m + 0.1 * g; v = 0.999 * v + 0.001 * g * g
            p = p - lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
        if not np.all(np.isfinite(p)) or np.abs(p).max() > 1e6:
            return "diverge", None, chemin
        if garder_chemin and (t < 2000 or t % 50 == 0):
            chemin.append(p.copy())
        if np.hypot(p[0] - 1, p[1] - 1) < 1e-3:
            return t, f_ros(p), chemin
    return "non", f_ros(p), chemin


GRILLE = [1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1]
tab = {}
for meth in ("GD", "Momentum", "Adam"):
    tab[meth] = {str(lr): optimiser(meth, lr)[0] for lr in GRILLE}
meilleur = {}
for meth, r in tab.items():
    ok_ = {lr: n for lr, n in r.items() if isinstance(n, int)}
    meilleur[meth] = min(ok_.items(), key=lambda x: x[1]) if ok_ else None
chemins = {}
for meth, b in meilleur.items():
    if b:
        _, _, ch = optimiser(meth, float(b[0]), garder_chemin=True)
        chemins[meth] = [[round(float(a), 4), round(float(c), 4)] for a, c in ch[::max(1, len(ch) // 600)]]
# le code de l'article : GD, pas 0,001, 10 000 pas
p = np.array([-1.0, 1.0])
for _ in range(10000):
    p = p - 0.001 * g_ros(p)
out["optim"] = dict(grille=GRILLE, pas=tab, meilleur={k: (v and [float(v[0]), v[1]]) for k, v in meilleur.items()}, chemins=chemins, article=[float(p[0]), float(p[1])])
txt.append("\n## 1b. Rosenbrock, départ (-1, 1) : nombre de pas pour arriver à 0,001 de (1, 1)\n")
txt.append("| pas | " + " | ".join(str(lr) for lr in GRILLE) + " |")
txt.append("|---|" + "---|" * len(GRILLE))
for meth, r in tab.items():
    txt.append(f"| {meth} | " + " | ".join(str(r[str(lr)]) for lr in GRILLE) + " |")
txt.append("\n(« non » = pas arrivé en 100 000 pas ; « diverge » = explose.) Meilleur de chaque méthode : "
           + " ; ".join(f"{k} {v[1]} pas (pas {v[0]})" for k, v in meilleur.items() if v) + ".")
txt.append(f"\nLe code de l'article (GD, pas 0,001, 10 000 pas) s'arrête en ({p[0]:.4f}, {p[1]:.4f}).")

json.dump(out, open(D.SORTIE / "n1.json", "w"))
D.ecrire("n1.md", "\n".join(txt) + "\n")
