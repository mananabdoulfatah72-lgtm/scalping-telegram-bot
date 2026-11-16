"""Idee K de usine/REGLES.md : Kronos-small sur le NQ, 3 decisions par seance, 100 trajectoires, periode jamais vue par le modele.

Usage :
    KB_MINUTES=<nasdaq100_1min.csv.gz> python3 usine/kronos_nq.py calculer   # les trajectoires (environ 1 h 15 sur 4 coeurs)
    KB_MINUTES=<...> python3 usine/kronos_nq.py juger                        # les portes K1 a K3 et l'information
Reprend ou il s'est arrete (usine/.cache/kronos/decisions.jsonl). Ecrit usine/resultats/<date>/kronos.json.
"""
import datetime as dt
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import donnees as Dn  # noqa: E402
import moteur as Mo  # noqa: E402

DEBUT, CONTEXTE, HORIZON, TRAJ, SEUIL = "2025-07-01", 488, 24, 100, 0.6
BLOCS = (6, 30, 54)                       # bougie de 5 min qui suit la decision : 10 h, 12 h, 14 h (New York)
SORTIE = ICI / ".cache" / "kronos"
FICHIER = SORTIE / "decisions.jsonl"


def bougies(D):
    """Bougies de 5 minutes des seances completes, a la suite : tableau (n, 6) et heures de debut, plus l'indice de la
    premiere bougie de chaque seance complete."""
    O, H, L, C, V, ok, J = D["O"], D["H"], D["L"], D["C"], D["V"], D["complete"], D["J"]
    lignes, heures, debut = [], [], {}
    for s in np.where(ok)[0]:
        debut[s] = len(lignes)
        for b in range(78):
            m = slice(5 * b, 5 * b + 5)
            o, h, l, c, v = O[s, 5 * b], H[s, m].max(), L[s, m].min(), C[s, 5 * b + 4], V[s, m].sum()
            lignes.append((o, h, l, c, v, v * (o + h + l + c) / 4))
            heures.append(pd.Timestamp(str(J[s])) + pd.Timedelta(minutes=570 + 5 * b))
    return np.array(lignes, np.float64), pd.Series(heures), debut


def stamps(h):
    return np.stack([h.dt.minute, h.dt.hour, h.dt.weekday, h.dt.day, h.dt.month], 1).astype(np.float32)


def calculer():
    import torch
    import kronos_cache as KC
    torch.set_num_threads(4)
    D = Dn.charger(); J, ok = D["J"], D["complete"]
    X, heures, debut = bougies(D)
    seances = [s for s in np.where(ok)[0] if J[s] >= DEBUT]
    SORTIE.mkdir(parents=True, exist_ok=True)
    faites = set()
    if FICHIER.exists():
        faites = {json.loads(l)["jour"] for l in FICHIER.read_text().splitlines() if l.strip()}
    tok, mod = KC.charger()
    t0 = time.time(); n = 0
    for s in seances:
        jour = str(J[s])
        if jour in faites:
            continue
        xs, xst, yst, moy, ect, der = [], [], [], [], [], []
        for b0 in BLOCS:
            fin = debut[s] + b0                                    # premiere bougie prevue
            x = X[fin - CONTEXTE:fin]
            mu, sd = x.mean(0), x.std(0)
            xs.append(np.clip((x - mu) / (sd + 1e-5), -5, 5).astype(np.float32))
            xst.append(stamps(heures.iloc[fin - CONTEXTE:fin])); yst.append(stamps(heures.iloc[fin:fin + HORIZON]))
            moy.append(mu); ect.append(sd); der.append(x[-1, 3])
        graine = int(jour.replace("-", ""))
        z = KC.trajectoires(tok, mod, np.stack(xs), np.stack(xst), np.stack(yst), TRAJ, HORIZON, graine=graine)
        lignes = []
        for i, b0 in enumerate(BLOCS):
            clot = z[i, :, :, 3] * (ect[i][3] + 1e-5) + moy[i][3]           # (100, 24) clotures prevues
            fins = clot[:, -1]
            lignes.append(dict(bloc=b0, derniere=float(der[i]), f=float(np.mean(fins > der[i])),
                               moyenne=float(fins.mean()), fins=[round(float(v), 2) for v in fins],
                               chemins=([[round(float(v), 2) for v in c] for c in clot] if jour >= "2026-11-09" else None)))
        with open(FICHIER, "a") as fh:
            fh.write(json.dumps(dict(jour=jour, decisions=lignes)) + "\n")
        n += 1
        if n % 10 == 0:
            print(f"{n} seances ({jour}) en {time.time() - t0:.0f} s", flush=True)
    print(f"fini : {len(seances)} seances dans la periode", flush=True)


def positions(D, sens_par_jour):
    """Positions de l'usine (pg, pi) : bloc de la minute 30 a 149, 150 a 269, 270 a 389."""
    S = D["C"].shape[0]
    pg = np.zeros((S, Mo.N), np.int8); pi = np.zeros_like(pg)
    pos = {j: i for i, j in enumerate(D["J"])}
    for jour, sens in sens_par_jour.items():
        s = pos[jour]
        for k, sg in enumerate(sens):
            m0 = 30 + 120 * k
            pg[s, m0:m0 + 120] = sg; pi[s, m0:m0 + 120] = sg
    return pg, pi


def juger():
    D = Dn.charger(); P = Mo.deriver(D); J, ok = D["J"], D["complete"]
    dec = [json.loads(l) for l in FICHIER.read_text().splitlines() if l.strip()]
    dec = {d["jour"]: d["decisions"] for d in dec}
    sel = ok & (J >= DEBUT)
    jours = [str(j) for j in J[sel]]
    manquent = [j for j in jours if j not in dec]
    if manquent:
        sys.exit(f"{len(manquent)} seances sans calcul (premiere : {manquent[0]}) : lancer d'abord « calculer ».")
    C = D["C"]; pos = {j: i for i, j in enumerate(J)}

    def bloc_brut(jour, k):
        s = pos[jour]; m0 = 30 + 120 * k
        return math.log(C[s, m0 + 119] / C[s, m0 - 1])

    def evaluer(regle):
        sens = {j: [regle(j, k, d) for k, d in enumerate(dec[j])] for j in jours}
        pg, pi = positions(D, sens)
        sp, sn, tot, joue = Mo.k_stats(P["lg"], P["lb"], pg, pi, ok)
        g, pire, _ = Mo.k_dollars(P["lg"], P["lb"], P["O"], P["H"], P["L"], pg, pi, ok, 1000.0)
        x = tot[sel]; xd = g[sel]
        t = float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))) if x.std(ddof=1) > 0 else 0.0
        trades = [(sg, bloc_brut(j, k)) for j in jours for k, sg in enumerate(sens[j]) if sg != 0]
        bons = [1.0 if sg * r > 0 else 0.0 for sg, r in trades]
        return dict(t=t, gain_par_an=float(xd.mean() * 252), seances=int(len(x)), trades=len(trades),
                    achats=sum(1 for sg, _ in trades if sg > 0), ventes=sum(1 for sg, _ in trades if sg < 0),
                    bonnes_directions=float(np.mean(bons)) if bons else None, pf=float(sp[sel].sum() / sn[sel].sum()),
                    pire_seance=float(xd.min())), trades

    seuil = lambda q: (lambda j, k, d: 1 if d["f"] >= q else (-1 if d["f"] <= 1 - q else 0))  # noqa: E731
    R = {"periode": [jours[0], jours[-1]], "decisions": 3 * len(jours)}
    principal, trades = evaluer(seuil(SEUIL))
    # K2 : les sens melanges entre les trades (chaque trade seul, frais compris)
    sg = np.array([a for a, _ in trades], float); r = np.array([b for _, b in trades])
    reel = float((sg * r).sum()); rng = np.random.default_rng(20261116)
    perm = np.array([(rng.permutation(sg) * r).sum() for _ in range(10000)])
    p = float(np.mean(perm >= reel))
    principal.update(K1=bool(principal["t"] >= 2.0), K2_p=p, K2=bool(p < 0.01), K3=bool(principal["gain_par_an"] >= 1000.0))
    principal["passe"] = bool(principal["K1"] and principal["K2"] and principal["K3"])
    R["regle"] = principal
    info = {}
    for q in (0.5, 0.7, 0.8):
        info[f"seuil_{q}"] = evaluer(seuil(q))[0]
    info["trajectoire_moyenne"] = evaluer(lambda j, k, d: 1 if d["moyenne"] > d["derniere"] else -1)[0]

    def momentum(j, k, d):
        s = pos[j]; m0 = 30 + 120 * k
        ref = D["O"][s, 0] if k == 0 else C[s, m0 - 121]
        return 1 if C[s, m0 - 1] > ref else -1
    info["suivre_les_2_heures_d_avant"] = evaluer(momentum)[0]
    info["toujours_acheter"] = evaluer(lambda j, k, d: 1)[0]
    # le regime de l'article : accord des trajectoires contre mouvement absolu du bloc
    acc = [(abs(d["f"] - 0.5) >= 0.3, abs(bloc_brut(j, k))) for j in jours for k, d in enumerate(dec[j])]
    fort = [a for c, a in acc if c]; faible = [a for c, a in acc if not c]
    info["regime"] = dict(blocs_accord=len(fort), blocs_disperses=len(faible),
                          mouvement_moyen_accord_pct=float(np.mean(fort) * 100) if fort else None,
                          mouvement_moyen_disperses_pct=float(np.mean(faible) * 100) if faible else None)
    R["information"] = info
    R["verdict"] = "passe K1, K2 et K3 : compte puis papier" if principal["passe"] else "rejete"
    d = ICI / "resultats" / dt.date.today().isoformat(); d.mkdir(parents=True, exist_ok=True)
    (d / "kronos.json").write_text(json.dumps(R, ensure_ascii=False, indent=1, default=float))
    import csv
    reg = ICI / "registre.csv"
    with open(reg, newline="", encoding="utf-8") as fh:
        champs = next(csv.reader(fh))
    ligne = {c: "" for c in champs}
    ligne.update(date=dt.date.today().isoformat(), idee="kronos", titre="Kronos-small, 100 trajectoires (periode jamais vue)",
                 reglage_dev=json.dumps({"seuil": SEUIL, "horizon": HORIZON, "trajectoires": TRAJ}),
                 pf_hors_echantillon=f"{principal['pf']:.3f}", gain_an_hors_echantillon=f"{principal['gain_par_an']:.0f}",
                 verdict=f"{R['verdict']} (K1 t {principal['t']:.2f} ; K2 p {p:.3f} ; K3 {principal['gain_par_an']:.0f} $ par an)")
    with open(reg, "a", newline="", encoding="utf-8") as fh:
        csv.DictWriter(fh, fieldnames=champs).writerow(ligne)
    print(json.dumps(R, ensure_ascii=False, indent=1, default=float))


if __name__ == "__main__":
    {"calculer": calculer, "juger": juger}[sys.argv[1]]()
