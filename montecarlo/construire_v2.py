#!/usr/bin/env python3
"""Monte Carlo v2 : assemble les donnees de la page (donnees_v2.json) et la page (monte_carlo_bulenox.html).
- tables exactes (tables.npz) des 21 tirages du filtre (10 aussi bons qu'en 2026, 10 deux fois plus faibles, 1 sans
  filtre), dedoublonnees : pour chaque seance, les resultats distincts (12 combinaisons : gain et pire point en entiers
  de 1/100 000 $, drapeaux sur un octet) et, pour chaque tirage, le numero de son resultat ;
- mois de chaque seance, historique du bot et resultats du moteur exact (mc.json, v1) pour le controle."""
import base64
import json
from pathlib import Path

import numpy as np

ICI = Path(__file__).resolve().parent


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()


def donnees():
    z = np.load(ICI / "tables.npz")
    gi = np.round(z["gain"] * 1e5).astype("<i4")
    pi = np.round(z["pire"] * 1e5).astype("<i4")
    dr = z["drap"].astype(np.uint8)
    assert np.abs(z["gain"]).max() * 1e5 < 2 ** 31 and np.abs(z["pire"]).max() * 1e5 < 2 ** 31
    nt, ns, nk = gi.shape
    ug, up, ud, index = [], [], [], np.zeros((nt, ns), "<u2")
    for a in range(ns):
        vus = {}
        for t in range(nt):
            cle = gi[t, a].tobytes() + pi[t, a].tobytes() + dr[t, a].tobytes()
            if cle not in vus:
                vus[cle] = len(ug)
                ug.append(gi[t, a]); up.append(pi[t, a]); ud.append(dr[t, a])
            index[t, a] = vus[cle]
    assert len(ug) < 65536
    jours = [str(x) for x in z["jours"]]
    mois = [(int(d[:4]) - 2012) * 12 + int(d[5:7]) - 1 for d in jours]
    v1 = json.loads((ICI / "mc.json").read_text())
    champs = ("valide", "ch_perdu", "mois_validation", "m_perdu", "au_moins_1", "reel", "net_mediane", "net_moyenne",
              "perdants")
    ref = {k: {c: v[c] for c in champs} for k, v in v1["scenarios"].items()}
    tir = [str(x) for x in z["tirages"]]
    return {
        "ns": len(jours), "nk": 12, "caps": [float(c) for c in z["caps"]], "tirages": tir,
        "filtres": {"fort": [i for i, t in enumerate(tir) if t.startswith("fort")],
                    "moitie": [i for i, t in enumerate(tir) if t.startswith("moitie")],
                    "aucun": [i for i, t in enumerate(tir) if t.startswith("aucun")]},
        "nu": len(ug), "gain": b64(np.array(ug, "<i4")), "pire": b64(np.array(up, "<i4")), "drap": b64(np.array(ud, np.uint8)),
        "index": b64(index), "mois": mois, "premier_jour": jours[0], "dernier_jour": jours[-1],
        "historique": v1["historique"], "reference": ref, "prix": 19.25, "activation": 148.0,
        "controle": json.loads((ICI / "controle_v2.json").read_text()),
    }


def main():
    d = donnees()
    (ICI / "donnees_v2.json").write_text(json.dumps(d, separators=(",", ":"), ensure_ascii=False))
    modele = ICI / "page_v2.html"
    if modele.exists():
        moteur = (ICI / "moteur_jour.js").read_text().replace("if (typeof module", "if (false && typeof module")
        page = modele.read_text().replace("/*MOTEUR*/", moteur).replace(
            "/*DONNEES*/", json.dumps(d, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/"))
        (ICI / "monte_carlo_bulenox.html").write_text(page)
        print(f"monte_carlo_bulenox.html : {len(page) / 1e6:.2f} Mo")
    print(f"donnees_v2.json : {(ICI / 'donnees_v2.json').stat().st_size / 1e6:.2f} Mo")


if __name__ == "__main__":
    main()
