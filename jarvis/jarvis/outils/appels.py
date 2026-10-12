"""Appels téléphoniques par Twilio : jouer un message à quelqu'un, ou mener une vraie conversation (Jarvis parle
et écoute, tour par tour) pour un objectif précis, puis te faire le résumé. Toujours après confirmation.

La conversation a besoin d'une adresse publique qui mène au serveur de Jarvis (ngrok ou cloudflared, voir
README) et de la clé d'API Claude (les réponses doivent arriver en quelques secondes)."""
from __future__ import annotations

import re
import threading
import time
import uuid
from xml.sax.saxutils import escape

from ..services import S, annoncer
from . import ErreurOutil, module, outil, p

SESSIONS: dict[str, dict] = {}
_verrou = threading.Lock()


@module("appels", "APPELS")
def etat() -> tuple[str, str]:
    try:
        import twilio  # noqa: F401
    except ImportError:
        return "absent", "module twilio à installer (installer.bat)"
    if not (S.cfg.get("twilio.sid", "") and S.cfg.get("twilio.jeton", "") and S.cfg.get("twilio.numero", "")):
        return "non_configure", "[twilio] sid, jeton et numero dans config.toml"
    return "pret", "appels" + (" et conversations" if S.cfg.get("twilio.url_publique", "") else " (messages seulement)")


def client():
    try:
        from twilio.rest import Client
    except ImportError:
        raise ErreurOutil("Les appels ont besoin du module twilio (relance installer.bat).")
    sid, jeton = S.cfg.get("twilio.sid", ""), S.cfg.get("twilio.jeton", "")
    if not sid or not jeton or not S.cfg.get("twilio.numero", ""):
        raise ErreurOutil("Twilio n'est pas configuré : compte Twilio, numéro acheté, puis sid, jeton et numero dans "
                          "[twilio] de config.toml.")
    return Client(sid, jeton)


def numero(destinataire: str) -> tuple[str, str]:
    """(numéro E.164, nom affiché) à partir d'un nom de [contacts] ou d'un numéro."""
    contacts = {k.lower(): str(v) for k, v in (S.cfg.get("contacts", {}) or {}).items()}
    nom = destinataire.strip()
    brut = contacts.get(nom.lower(), nom)
    chiffres = re.sub(r"[^\d+]", "", brut)
    if re.fullmatch(r"0[1-9]\d{8}", chiffres):
        chiffres = "+33" + chiffres[1:]
    if not re.fullmatch(r"\+\d{8,15}", chiffres):
        raise ErreurOutil(f"Je n'ai pas de numéro pour « {destinataire} ». Ajoute-le dans [contacts] de config.toml "
                          "ou donne-moi le numéro.")
    return chiffres, (nom if nom.lower() in contacts else chiffres)


def voix() -> str:
    return S.cfg.get("twilio.voix", "Polly.Lea")


def dire(texte: str) -> str:
    return f'<Say language="fr-FR" voice="{escape(voix())}">{escape(texte)}</Say>'


def _question(args: dict) -> str:
    quoi = f"pour : {args['objectif']}" if args.get("objectif") else f"pour dire : « {args.get('message', '')[:160]} »"
    return f"Appeler {args.get('destinataire')} {quoi}"


@outil("appel_message", "Appelle quelqu'un et lui lit un message (après confirmation).", "APPELS",
       {"destinataire": p("string", "Nom d'un contact ou numéro"), "message": p("string", "Message à lire")},
       requis=["destinataire", "message"], confirmer=_question)
def appel_message(destinataire: str, message: str) -> str:
    num, nom = numero(destinataire)
    proprio = S.cfg.get("general.proprietaire", "") or "mon propriétaire"
    twiml = (f"<Response>{dire(f'Bonjour, ici l’assistant de {proprio}.')}<Pause length='1'/>{dire(message)}"
             f"<Pause length='1'/>{dire(message)}</Response>")
    appel = client().calls.create(to=num, from_=S.cfg.get("twilio.numero"), twiml=twiml)
    with _verrou:
        SESSIONS[appel.sid] = {"nom": nom, "numero": num, "objectif": "message", "sid": appel.sid, "tours": [],
                               "debut": time.time(), "statut": "lancé"}
    return f"Appel vers {nom} lancé (le message sera lu deux fois)."


@outil("appel_conversation", "Appelle quelqu'un et mène la conversation à la place de l'utilisateur pour un objectif "
       "précis (prendre rendez-vous, prévenir d'un retard, poser une question), puis en fait le résumé.", "APPELS",
       {"destinataire": p("string", "Nom d'un contact ou numéro"),
        "objectif": p("string", "Ce que Jarvis doit obtenir ou dire, avec tous les détails utiles")},
       requis=["destinataire", "objectif"], confirmer=_question)
def appel_conversation(destinataire: str, objectif: str) -> str:
    url = S.cfg.get("twilio.url_publique", "").rstrip("/")
    if not url:
        raise ErreurOutil("Pour une conversation, il faut une adresse publique vers Jarvis ([twilio] url_publique, avec "
                          "ngrok ou cloudflared, voir README). Je peux sinon appeler pour lire un message.")
    if not S.cfg.cle_api():
        raise ErreurOutil("Les conversations téléphoniques ont besoin de la clé d'API Claude (réponses en quelques secondes).")
    num, nom = numero(destinataire)
    session = uuid.uuid4().hex[:12]
    with _verrou:
        SESSIONS[session] = {"nom": nom, "numero": num, "objectif": objectif, "tours": [], "debut": time.time(),
                             "statut": "lancé", "sid": ""}
    appel = client().calls.create(to=num, from_=S.cfg.get("twilio.numero"), url=f"{url}/twilio/voix/{session}",
                                  status_callback=f"{url}/twilio/statut/{session}",
                                  status_callback_event=["completed"], machine_detection="Enable")
    SESSIONS[session]["sid"] = appel.sid
    return f"J'appelle {nom}. Je te fais le résumé dès que l'appel est terminé."


@outil("appel_etat", "État et résumé des derniers appels passés par Jarvis.", "APPELS")
def appel_etat() -> str:
    with _verrou:
        dernieres = sorted(SESSIONS.values(), key=lambda s: s["debut"], reverse=True)[:5]
    if not dernieres:
        return "Aucun appel passé depuis le démarrage."
    lignes = []
    for s in dernieres:
        lignes.append(f"{s['nom']} ({time.strftime('%H:%M', time.localtime(s['debut']))}) : {s['statut']}"
                      + (f" — {s['resume']}" if s.get("resume") else ""))
    return "\n".join(lignes)


# ------------------------------------------------------------------ conversation (appelé par le serveur web)
CONSIGNE_APPEL = """Tu es l'assistant vocal de {proprio}, au téléphone avec {nom}. Objectif de l'appel : {objectif}
Règles : français, phrases très courtes et naturelles (c'est lu par une voix de synthèse), poli et direct. Présente-toi
au début comme l'assistant de {proprio}. N'invente aucune information : si on te demande quelque chose que tu ne sais
pas, dis que tu transmettras. Ne donne jamais de données bancaires ni de mot de passe. Si la personne refuse de parler à
un assistant, excuse-toi et termine. Quand l'objectif est atteint ou que l'appel doit finir, dis au revoir et termine ta
réponse par [FIN]."""


def reponse_ia(s: dict) -> str:
    import anthropic
    proprio = S.cfg.get("general.proprietaire", "") or "mon propriétaire"
    c = anthropic.Anthropic(api_key=S.cfg.cle_api(), timeout=12.0, max_retries=1)
    r = c.messages.create(model=S.cfg.get("cerveau.modele"), max_tokens=1000, output_config={"effort": "low"},
                          system=CONSIGNE_APPEL.format(proprio=proprio, nom=s["nom"], objectif=s["objectif"]),
                          messages=messages_appel(s["tours"]))
    return " ".join(b.text for b in r.content if b.type == "text").strip() or "Pardon, pouvez-vous répéter ?"


def messages_appel(tours: list[tuple[str, str]]) -> list[dict]:
    """Le dialogue pour le modèle : rôles alternés, toujours fini par la personne (un silence compte comme un tour)."""
    messages: list[dict] = []
    for qui, texte in tours:
        role = "user" if qui == "personne" else "assistant"
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += "\n" + texte
        else:
            messages.append({"role": role, "content": texte})
    if not messages or messages[0]["role"] != "user":
        messages.insert(0, {"role": "user", "content": "(La personne vient de décrocher.)"})
    if messages[-1]["role"] != "user":
        messages.append({"role": "user", "content": "(Silence : la personne n'a rien répondu.)"})
    return messages


def webhook_voix(session: str, params: dict) -> str:
    """Un tour de conversation : la phrase entendue arrive dans SpeechResult ; on renvoie la suite en TwiML."""
    s = SESSIONS.get(session)
    if s is None:
        return f"<Response>{dire('Désolé, cet appel a expiré.')}<Hangup/></Response>"
    if params.get("AnsweredBy", "").startswith("machine"):
        s["statut"] = "répondeur"
        return f"<Response>{dire('Bonjour, ici l’assistant de ' + (S.cfg.get('general.proprietaire', '') or 'mon propriétaire') + '. Je rappellerai plus tard, merci.')}<Hangup/></Response>"
    entendu = (params.get("SpeechResult") or "").strip()
    if entendu:
        s["tours"].append(("personne", entendu))
    elif s["tours"]:
        s["silences"] = s.get("silences", 0) + 1
        if s["silences"] >= 2:
            return f"<Response>{dire('Je n’entends plus rien, je vais raccrocher. Au revoir.')}<Hangup/></Response>"
    s["statut"] = "en cours"
    try:
        texte = reponse_ia(s)
    except Exception:
        texte = "Excusez-moi, j'ai un problème technique, je vous rappellerai. Au revoir. [FIN]"
    fin = "[FIN]" in texte
    texte = texte.replace("[FIN]", "").strip()
    s["tours"].append(("jarvis", texte))
    action = f"{S.cfg.get('twilio.url_publique', '').rstrip('/')}/twilio/voix/{session}"
    if fin:
        return f"<Response>{dire(texte)}<Hangup/></Response>"
    return (f'<Response><Gather input="speech" language="fr-FR" speechTimeout="auto" action="{escape(action)}" '
            f'method="POST">{dire(texte)}</Gather><Redirect method="POST">{escape(action)}</Redirect></Response>')


def webhook_statut(session: str, params: dict) -> None:
    s = SESSIONS.get(session)
    if s is None:
        return
    s["statut"] = {"completed": "terminé", "busy": "occupé", "no-answer": "pas de réponse", "failed": "échec",
                   "canceled": "annulé"}.get(params.get("CallStatus", ""), params.get("CallStatus", "terminé"))
    threading.Thread(target=_resumer, args=(s,), daemon=True).start()


def _resumer(s: dict) -> None:
    if not s["tours"]:
        annoncer(f"L'appel à {s['nom']} : {s['statut']}.")
        return
    dialogue = "\n".join(f"{'Jarvis' if q == 'jarvis' else s['nom']} : {t}" for q, t in s["tours"])
    try:
        import anthropic
        c = anthropic.Anthropic(api_key=S.cfg.cle_api(), timeout=30.0)
        r = c.messages.create(model=S.cfg.get("cerveau.modele"), max_tokens=800, output_config={"effort": "low"},
                              messages=[{"role": "user", "content": f"Objectif de l'appel : {s['objectif']}\n\n"
                                         f"Transcription :\n{dialogue}\n\nRésume en deux phrases à dire à voix haute "
                                         "à l'utilisateur : ce qui a été obtenu, et ce qu'il doit faire s'il y a lieu."}])
        s["resume"] = " ".join(b.text for b in r.content if b.type == "text").strip()
    except Exception:
        s["resume"] = f"{len(s['tours'])} échanges, voir l'historique."
    annoncer(f"Appel à {s['nom']} terminé. {s['resume']}")
