#!/usr/bin/env python3
"""Modele M2 fige pour le bot XGBoost NQ.
1. Meme marche en avant purgee que le niveau 3, sans la variable temoin (21 variables) : le resultat doit rester le meme.
2. Modele final : entraine sur toutes les bougies utilisables jusqu'a la derniere seance du fichier.
3. Exports : arbres (JSON compact lu par le C#), et reference (variables + probabilite) pour verifier le C# a l'identique."""
import json
import os

import numpy as np
import xgboost as xgb
from scipy import stats

import caracteristiques as K
import donnees as D

X = K.construire()
F, y, c, o, fut, sess, b, an, okb, ok, J = (X[k] for k in ("F", "y", "c", "o", "fut", "sess", "b", "an", "okb", "ok", "J"))
F21 = F[:, :21]
an_j = np.array([int(j[:4]) for j in J])
PARAMS = dict(n_estimators=100, max_depth=4, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8, reg_alpha=1.0, reg_lambda=1.0,
              tree_method="hist", n_jobs=4, random_state=0)
ok21 = ok[sess] & X["meme"] & np.isfinite(F21).all(1) & np.isfinite(fut)

# 1. la marche en avant (graines 0 a 9, et moyenne des 10 modeles) est dans xgb_graines.py
wf = json.load(open(D.SORTIE / "xgb_graines.json"))["21 variables (sans témoin)"]["ensemble"]
GRAINES = list(range(10))

# 2. modele final
tr = ok21
finals, modeles = [], []
for g in GRAINES:
    final = xgb.XGBClassifier(**{**PARAMS, "random_state": g}).fit(F21[tr], y[tr], verbose=False)
    m_ = json.loads(final.get_booster().save_raw("json").decode())
    base = float(str(m_["learner"]["learner_model_param"]["base_score"]).strip("[]"))
    arbres = [dict(g=t["left_children"], d=t["right_children"], v=t["split_indices"], s=t["split_conditions"], m=[bool(x) for x in t["default_left"]])
              for t in m_["learner"]["gradient_booster"]["model"]["trees"]]
    finals.append(final); modeles.append(dict(graine=g, base=base, arbres=arbres))


def predire(x):                                   # meme parcours que le C# (flottants 32 bits, NaN -> branche par defaut), moyenne des modeles
    x32 = np.asarray(x, dtype=np.float32); ps = []
    for md in modeles:
        tot = np.float32(0)
        for a in md["arbres"]:
            n = 0
            while a["g"][n] != -1:
                v = x32[a["v"][n]]
                n = (a["g"][n] if a["m"][n] else a["d"][n]) if np.isnan(v) else (a["g"][n] if v < np.float32(a["s"][n]) else a["d"][n])
            tot = np.float32(tot + np.float32(a["s"][n]))
        ps.append(1 / (1 + np.exp(-(np.log(md["base"] / (1 - md["base"])) + float(tot)))))
    return float(np.mean(ps))


ref = an >= 2023
pf = np.mean([f.predict_proba(F21[ref])[:, 1] for f in finals], 0)
pm = np.array([predire(x) for x in F21[ref][:1000]])
print("parcours maison contre XGBoost (1 000 bougies) : ecart max", float(np.abs(pm - pf[:1000]).max()))
dossier = D.RACINE / "bot3en1/XGBoost.Core"
dossier.mkdir(exist_ok=True)
json.dump(dict(modeles=modeles, variables=K.NOMS[:21], entraine_jusqua=J[int(sess[tr].max())], bougies=int(tr.sum()),
               reglages="moyenne de 10 modeles (graines 0 a 9) ; chacun 100 arbres, profondeur 4, pas 0,05, sous-echantillons 0,8 / 0,8, L1 = 1, L2 = 1"),
          open(dossier / "modele_xgb.json", "w"), separators=(",", ":"))
# reference pour le C# : jour, bougie, 21 variables, probabilite du modele final
with open(os.environ.get("REFERENCE_XGB", "reference_xgb.csv"), "w") as f:
    f.write("jour,bougie," + ",".join(f"f{k}" for k in range(21)) + ",p\n")
    idx = np.nonzero(ref)[0]
    for i, pp in zip(idx, pf):
        f.write(f"{J[sess[i]]},{b[i]}," + ",".join("nan" if not np.isfinite(v) else repr(float(v)) for v in F21[i]) + f",{float(pp)!r}\n")
json.dump(dict(marche_avant=wf, entraine_jusqua=J[int(sess[tr].max())], bougies=int(tr.sum())), open(D.SORTIE / "xgb_final.json", "w"))
print("modele final entraine jusqu'au", J[int(sess[tr].max())], "sur", int(tr.sum()), "bougies")
