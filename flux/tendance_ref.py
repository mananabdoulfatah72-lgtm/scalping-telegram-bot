#!/usr/bin/env python3
"""Fichiers de reference pour le rejeu C# des regles de tendance du bot FluxNQ (H1 ORB 5 min, H5 cassure de la veille,
H12 Supertrend 10-3, F3 pivots R1/S1) : minutes du NQ 2011 - 2026, seances et gains attendus par seance, calcules avec
le code de la recherche (scalping/partie_h.py, scalping/partie_f.py).

Lancer : KB=<copie de claude/keen-babbage-r686cl> python3 flux/tendance_ref.py <dossier de sortie>"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI.parent / "scalping"))
import partie_e as E  # noqa: E402
import partie_f as F  # noqa: E402
import partie_h as H  # noqa: E402


def main(sortie):
    out = Path(sortie)
    out.mkdir(parents=True, exist_ok=True)
    d = E.jour_nq()
    jours = pd.DatetimeIndex(d["jours"].astype("datetime64[D]")).strftime("%Y-%m-%d")
    S, N = d["c"].shape
    ok = d["complete"] & ~d["ech"]
    pd.DataFrame({"jour": jours, "ok": ok.astype(int), "prec": d["prec_meme"],
                  "ech": float(d["pref"]) / d["o"][:, 0]}).to_csv(out / "seances.csv", index=False, float_format="%.17g")
    idx = np.repeat(np.arange(S), N)
    pd.DataFrame({"s": idx, "minute": np.tile(np.arange(N), S), "o": d["o"].ravel(), "h": d["h"].ravel(),
                  "l": d["l"].ravel(), "c": d["c"].ravel()}).to_csv(out / "minutes.csv.gz", index=False, float_format="%.10g")
    h, f = H.toutes(d), F.toutes(d)
    att = {"H1": h["H1"], "H5": h["H5"], "H12": h["H12"], "F3": f["F3"]}
    pd.DataFrame({"s": np.arange(S), **{k: v[0] for k, v in att.items()},
                  **{k + "_sens": v[1] for k, v in att.items()}, **{k + "_entree": v[2] for k, v in att.items()}}).to_csv(
        out / "attendus_tendance.csv", index=False, float_format="%.17g")
    print(f"{S} seances ({jours[0]} - {jours[-1]}) ; seances jouees : " + ", ".join(
        f"{k} {int(np.isfinite(v[0]).sum())}" for k, v in att.items()))


if __name__ == "__main__":
    main(sys.argv[1])
