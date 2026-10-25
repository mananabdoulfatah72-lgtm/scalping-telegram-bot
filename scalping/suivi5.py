#!/usr/bin/env python3
"""Suivi virtuel du coffre de l'avenir (README.md, version 5 et parties F, H) sur les minutes du NQ que le robot de la zone
enregistre chaque jour (zone/robot/nq_1min.csv.gz de main). Aucun ordre : chaque strategie est jouee par le moteur de la
recherche, avec les genomes et les constantes figes dans resultats/v5/candidats.json. Suivies sur le NQ : les 2 candidates
et les placebos de la version 5, et H12 (Supertrend), H1 (ORB 5 min), H5 (cassure de la veille), F3 (pivots).
Lancer : python3 scalping/suivi5.py <nq_1min.csv.gz> [premier jour, defaut 2026-11-02] ; ecrit resultats/v5/suivi.txt.
Variables TELEGRAM_TOKEN et CHAT_ID : envoie le resume sur Telegram le samedi (ou toujours avec ENVOYER_TOUJOURS=1)."""
import datetime
import json
import os
import sys

import numpy as np

import commun as K
import donnees as D
import moteur as M
import partie_f as F
import partie_h as H

ICI = K.ICI


def charger(chemin):
    d = D.minutes("NQ", chemin=chemin, debut="2025-01-01")
    cst = json.loads((ICI / "resultats" / "v5" / "candidats.json").read_text())["candidates"][0]["constantes"]
    for k in ("pt", "tick", "pas", "frais", "pref", "rond"):        # constantes figees du coffre (README v5)
        d[k] = np.float64(cst[k])
    return d


def strategies():
    j = json.loads((ICI / "resultats" / "v5" / "candidats.json").read_text())
    out = []
    for x in j["candidates"]:
        if x["marche"] == "NQ" and x["piste"] == "B":
            out.append(("candidate", f"NQ t {x['t_c']:.2f} : {x['description'][:60]}", np.asarray(x["genome"], float)))
    for x in j["placebos"]:
        if x["marche"] == "NQ" and x["piste"] == "B" and x.get("suivi") and x["type"] == "placebo":
            out.append(("placebo", f"placebo {x['sorte']} : {x['description'][:60]}", np.asarray(x["genome"], float)))
    return j["seuil_bonferroni"], out


def main():
    chemin = sys.argv[1]
    debut = np.datetime64(sys.argv[2] if len(sys.argv) > 2 else "2026-11-02")
    d = charger(chemin)
    f = M.indicateurs(d)
    s0 = int(np.searchsorted(d["jours"], debut))
    s1 = len(d["jours"])
    seuil, liste = strategies()
    jouables = int(f["jouable"][s0:s1].sum())
    L = [f"Suivi virtuel du NQ depuis le {debut} : {s1 - s0} seances, dont {jouables} jouables (completes, hors changement "
         f"de contrat) ; derniere seance {d['jours'][-1] if s1 else '-'}. Gains pour 1 MNQ au prix d'aujourd'hui, frais "
         "compris. Aucun ordre passe.", "",
         f"{'strategie':<84} {'seances':>7} {'trades':>6} {'total $':>9} {'t':>6}  verdict"]
    for typ, nom, g in liste:
        gain, n, w, brut, _ = M.jouer(g, f, s0, s1)
        x = gain[np.isfinite(gain)]
        x = x[np.abs(x) > 0]
        t = K.t_stat(x) if len(x) > 2 and x.std() > 0 else float("nan")
        v = "ecartee" if (n >= 50 and t <= -1) else ("RETENUE" if (n >= 150 and t >= seuil) else
                                                      ("interessante" if (n >= 100 and t >= 1.65) else "en cours"))
        L.append(f"{typ + ' ' + nom:<84} {len(x):7d} {n:6d} {x.sum():+9.0f} {t:6.2f}  {v}")
    out = {**H.toutes(d), **F.toutes(d)}
    for r, nom in (("H12", "Supertrend 10-3 (5 min)"), ("H1", "ORB 5 min"), ("H5", "cassure de la veille"),
                   ("F3", "pivots R1/S1, tendance")):
        g = out[r][0][s0:s1]
        x = g[np.isfinite(g)]
        t = K.t_stat(x) if len(x) > 2 and x.std() > 0 else float("nan")
        v = "ecartee" if (len(x) >= 50 and t <= -1) else ("interessante" if (len(x) >= 100 and t >= 1.65) else "en cours")
        L.append(f"{'regle ' + r + ' ' + nom:<84} {len(x):7d} {len(x):6d} {x.sum():+9.0f} {t:6.2f}  {v}")
    L += ["", f"Regles (README.md v5) : ecartee si t <= -1 avec au moins 50 trades ; retenue si t >= {seuil:.2f} avec au moins 150 "
          "trades et 2 trimestres positifs sur 3 ; interessante si t >= 1,65 avec 100 trades. Les placebos doivent faire "
          "moins bien que les candidates. Or, petrole et Russell : pas encore de releve des minutes."]
    txt = "\n".join(L)
    sortie = ICI / "resultats" / "v5" / "suivi.txt"
    sortie.write_text(txt + "\n")
    print(txt)
    jeton, chat = os.getenv("TELEGRAM_TOKEN"), os.getenv("CHAT_ID")
    hebdo = datetime.datetime.now(datetime.timezone.utc).weekday() == 5          # le samedi : resume de la semaine
    if jeton and chat and (hebdo or os.getenv("ENVOYER_TOUJOURS")):
        import requests
        requests.post(f"https://api.telegram.org/bot{jeton}/sendMessage",
                      data={"chat_id": chat, "text": "Suivi virtuel scalping NQ\n" + "\n".join(
                          l[:200] for l in L if l.startswith(("candidate", "placebo", "regle", "Suivi")))}, timeout=20)


if __name__ == "__main__":
    main()
