"""Brief du matin (etape 6 de l'article) : les survivants, les rejets, la consigne du compte, et une decision pour toi.

- Lit le dernier tableau de l'usine (usine/resultats/<date>/).
- Met a jour l'etat du compte depuis Telegram : envoie au bot un message « solde 49900 » apres la cloture (16 h a New
  York), avec si besoin « haut 51700 » (plus haut de fin de journee) et « sans » si tu n'as fait aucun trade ce jour-la.
- Envoie le brief sur Telegram (secrets TELEGRAM_TOKEN et CHAT_ID).
L'etat du compte (usine/compte.json, usine/journal_reel.csv) n'est jamais commite ni imprime dans les journaux de GitHub :
le depot est public. PUBLIC=1 : n'imprime que la partie usine.
"""
import csv
import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import requests

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import tableau as Tb  # noqa: E402

TOKEN, CHAT = os.getenv("TELEGRAM_TOKEN"), os.getenv("CHAT_ID")
PUBLIC = os.getenv("PUBLIC") == "1"
EN_SERVICE = ("zone", "supertrend")


def lire_telegram(compte):
    """Derniers messages « solde ... » de la conversation, plus recents que le dernier lu. Met a jour compte.json et
    journal_reel.csv. Renvoie le nombre de messages pris en compte."""
    if not (TOKEN and CHAT):
        return 0
    try:
        r = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates", timeout=20).json()
    except Exception:
        return 0
    vus = 0
    for u in r.get("result", []):
        m = u.get("message") or {}
        if str(m.get("chat", {}).get("id")) != str(CHAT) or u["update_id"] <= compte.get("dernier_message", 0):
            continue
        t = (m.get("text") or "").lower().replace(" ", " ")
        g = re.search(r"solde\s+([\d\s.,]+)", t)
        compte["dernier_message"] = u["update_id"]
        if not g:
            continue
        solde = float(re.sub(r"[\s,]", "", g.group(1)).rstrip("."))
        h = re.search(r"haut\s+([\d\s.,]+)", t)
        if h:
            compte["plus_haut_fin_de_journee"] = float(re.sub(r"[\s,]", "", h.group(1)).rstrip("."))
        a_trade = "sans" not in t and solde != compte.get("solde")
        compte["seances_sans_trade"] = 0 if a_trade else int(compte.get("seances_sans_trade", 0)) + 1
        compte["solde"] = solde
        compte["plus_haut_fin_de_journee"] = max(compte.get("plus_haut_fin_de_journee", solde), solde)
        compte["date"] = dt.date.fromtimestamp(m.get("date", 0)).isoformat()
        f = ICI / "journal_reel.csv"; neuf = not f.exists()
        with open(f, "a", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            if neuf:
                w.writerow(["date", "solde", "a_trade"])
            w.writerow([compte["date"], solde, "oui" if a_trade else "non"])
        vus += 1
    (ICI / "compte.json").write_text(json.dumps(compte, ensure_ascii=False, indent=1))
    return vus


def partie_usine():
    date, R = Tb.charger()
    surv = [r for r in R.values() if r["verdict"] == "passe les 5 portes"]
    L = [f"USINE A STRATEGIES (calcul du {date})"]
    L.append("Survivants : " + (", ".join(r["titre"] for r in surv) if surv else "aucun"))
    for r in R.values():
        if r["verdict"] != "passe les 5 portes":
            L.append(f"- {r['titre']} : {r['verdict']} ({Tb.raison(r)})")
    return L, R, surv


def decision(R, surv, voyant, compte):
    if voyant == "rouge":
        return "DECISION : arreter le bot (fichier STOP dans C:\\Bot3en1) et chercher la cause avant de reprendre."
    if compte and int(compte.get("seances_sans_trade", 0)) >= 4:
        return "DECISION : un trade est obligatoire a la prochaine seance (Supertrend NQ, 1 MNQ), sinon le compte est perdu."
    nouveaux = [r for r in surv if r["idee"] not in EN_SERVICE]
    if nouveaux:
        return f"DECISION : mettre « {nouveaux[0]['titre']} » en papier deux semaines avant tout argent reel ? (reponds oui ou non)"
    z = R.get("zone")
    if z and z["verdict"] != "passe les 5 portes":
        return f"DECISION : la zone ne passe plus ({z['verdict']}). Reduire a 1 MES en attendant la revue ?"
    return "DECISION : rien a changer. G2 manuel, 1 MNQ, frein a 750, limites 1 000 $ / 400 $."


def principal():
    L, R, surv = partie_usine()
    compte, voyant, consigne = None, "vert", []
    f = ICI / "compte.json"
    if f.exists():
        import consigne as Cs
        compte = json.loads(f.read_text())
        lus = lire_telegram(compte)
        compte = json.loads(f.read_text())
        m, e, _ = Cs.attendu()
        consigne, voyant = Cs.consigne(compte, Cs.lire_journal(), m, e)
        if lus:
            consigne.insert(0, f"({lus} message(s) « solde » lus sur Telegram.)")
    else:
        consigne = ["Compte : pas d'etat (usine/compte.json). Envoie « solde 49900 haut 51700 » au bot Telegram, ou cree le fichier "
                    "a partir de usine/compte.exemple.json."]
    texte = "\n".join(L + [""] + ["TON COMPTE"] + consigne + ["", decision(R, surv, voyant, compte)])
    if PUBLIC:
        print("\n".join(L))
    else:
        print(texte)
    if TOKEN and CHAT:
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT, "text": texte[:4000]}, timeout=20)
            print("brief envoye sur Telegram")
        except Exception as e:
            print(f"Telegram : envoi impossible ({type(e).__name__})")


if __name__ == "__main__":
    principal()
