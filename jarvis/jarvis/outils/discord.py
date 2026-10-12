"""Discord par un bot à toi (portail développeur Discord, intention « Message Content » activée, bot invité sur
tes serveurs) : mentions, récap des messages du jour, envoi avec confirmation. Un compte utilisateur automatisé
est interdit par Discord : Jarvis passe uniquement par un bot."""
from __future__ import annotations

import time
from datetime import datetime

from .. import reseau
from ..services import S
from . import ErreurOutil, module, outil, p

API = "https://discord.com/api/v10"


@module("discord", "DISCORD")
def etat() -> tuple[str, str]:
    if not S.cfg.get("discord.jeton", ""):
        return "non_configure", "[discord] jeton du bot et utilisateur_id dans config.toml"
    return "pret", f"{len(S.cfg.get('discord.salons', []) or [])} salon(s) suivis (0 = tous)"


def dc(chemin: str, methode: str = "GET", **kw):
    jeton = S.cfg.get("discord.jeton", "")
    if not jeton:
        raise ErreurOutil("Discord n'est pas configuré : crée un bot sur le portail développeur Discord, active "
                          "« Message Content Intent », invite-le sur tes serveurs et mets son jeton dans [discord].")
    return reseau.requete(methode, API + chemin, "Discord", headers={"Authorization": f"Bot {jeton}"}, **kw)


def salons() -> list[dict]:
    voulus = [str(x) for x in S.cfg.get("discord.salons", []) or []]
    out = []
    for g in dc("/users/@me/guilds") or []:
        for c in dc(f"/guilds/{g['id']}/channels") or []:
            if c.get("type") in (0, 5) and (not voulus or str(c["id"]) in voulus):
                out.append({"id": c["id"], "nom": c.get("name", ""), "serveur": g.get("name", "")})
    return out[:40]


def messages(salon: str, depuis: float, limite: int = 100) -> list[dict]:
    """Les messages les plus récents du salon (100 au plus) postés depuis `depuis`, du plus ancien au plus récent.
    (Avec « after », Discord rendrait les 100 premiers de la période : les derniers manqueraient.)"""
    out = dc(f"/channels/{salon}/messages", params={"limit": min(100, limite)}) or []
    recents = [m for m in out if datetime.fromisoformat(m["timestamp"]).timestamp() >= depuis]
    return sorted(recents, key=lambda m: int(m["id"]))


def heure(m: dict) -> str:
    return datetime.fromisoformat(m["timestamp"]).astimezone().strftime("%H:%M")


@outil("discord_mentions", "Messages Discord où l'utilisateur est mentionné (ou @everyone) sur la période.", "DISCORD",
       {"heures": p("integer", "Période en heures (défaut 24)")})
def discord_mentions(heures: int = 24) -> str:
    moi = str(S.cfg.get("discord.utilisateur_id", ""))
    depuis = time.time() - 3600 * max(1, int(heures))
    lignes = []
    for s in salons():
        try:
            for m in messages(s["id"], depuis):
                cite = any(str(u.get("id")) == moi for u in m.get("mentions", [])) or m.get("mention_everyone") \
                       or (moi and f"<@{moi}>" in m.get("content", ""))
                if cite:
                    lignes.append(f"{s['serveur']} #{s['nom']} {heure(m)} {m['author'].get('global_name') or m['author'].get('username')} : "
                                  f"{m.get('content', '')[:400]}")
        except ErreurOutil:
            continue
    return "\n".join(lignes) or "Personne ne t'a mentionné sur la période."


@outil("discord_recap", "Messages Discord de la période (par salon) pour en faire un récap.", "DISCORD",
       {"heures": p("integer", "Période en heures (défaut 24)"), "salon": p("string", "Nom d'un salon (facultatif)")})
def discord_recap(heures: int = 24, salon: str = "") -> str:
    depuis = time.time() - 3600 * max(1, int(heures))
    blocs, total = [], 0
    for s in salons():
        if salon and salon.lower().lstrip("#") not in s["nom"].lower():
            continue
        try:
            ms = messages(s["id"], depuis)
        except ErreurOutil:
            continue
        if not ms:
            continue
        lignes = [f"== {s['serveur']} #{s['nom']} ({len(ms)} messages)"]
        for m in ms[-60:]:
            if m.get("content"):
                lignes.append(f"{heure(m)} {m['author'].get('global_name') or m['author'].get('username')} : {m['content'][:300]}")
        blocs.append("\n".join(lignes))
        total += len(ms)
    return "\n\n".join(blocs) or "Aucun message sur la période."


def _question_envoi(args: dict) -> str:
    return f"Envoyer sur Discord dans #{args.get('salon')} : « {args.get('message', '')[:200]} »"


@outil("discord_envoyer", "Envoie un message dans un salon Discord (par le bot, après confirmation).", "DISCORD",
       {"salon": p("string", "Nom du salon"), "message": p("string", "Message")}, requis=["salon", "message"],
       confirmer=_question_envoi)
def discord_envoyer(salon: str, message: str) -> str:
    n = salon.lower().lstrip("#")
    tous = salons()
    choix = next((s for s in tous if s["nom"].lower() == n), None) or next((s for s in tous if n in s["nom"].lower()), None)
    if not choix:
        raise ErreurOutil(f"Pas de salon « {salon} » : {', '.join('#' + s['nom'] for s in tous)}.")
    dc(f"/channels/{choix['id']}/messages", "POST", json={"content": message[:2000]})
    return f"Message envoyé dans #{choix['nom']}."
