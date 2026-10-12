"""Gmail : mails non lus (Jarvis les résume), lecture, recherche, brouillons, envoi avec confirmation."""
from __future__ import annotations

import base64
import html
import re
from email.message import EmailMessage

from . import ErreurOutil, module, outil, p
from .google_auth import erreur_google, etat_google, service


@module("mail", "MAIL")
def etat() -> tuple[str, str]:
    return etat_google()


def gmail():
    return service("gmail", "v1").users()


def entetes(msg: dict) -> dict:
    return {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}


def lister(q: str, maximum: int) -> str:
    try:
        u = gmail()
        ids = u.messages().list(userId="me", q=q, maxResults=max(1, min(25, maximum))).execute().get("messages", [])
        lignes = []
        for m in ids:
            d = u.messages().get(userId="me", id=m["id"], format="metadata",
                                 metadataHeaders=["From", "Subject", "Date"]).execute()
            h = entetes(d)
            lignes.append(f"[{m['id']}] De : {h.get('from', '?')} | Objet : {h.get('subject', '(sans objet)')} | "
                          f"{h.get('date', '')}\n   {html.unescape(d.get('snippet', ''))}")
    except ErreurOutil:
        raise
    except Exception as e:
        raise erreur_google(e)
    return "\n".join(lignes) or "Aucun mail ne correspond."


@outil("mail_non_lus", "Mails non lus de la boîte de réception (expéditeur, objet, extrait) pour les résumer.", "MAIL",
       {"maximum": p("integer", "Nombre de mails (défaut 10)"),
        "filtre": p("string", "Filtre Gmail en plus (ex. newer_than:1d, from:banque)")})
def mail_non_lus(maximum: int = 10, filtre: str = "") -> str:
    return lister(f"is:unread in:inbox {filtre}".strip(), maximum)


@outil("mail_chercher", "Cherche des mails avec la syntaxe de recherche Gmail (from:, subject:, after:...).", "MAIL",
       {"requete": p("string", "Recherche Gmail"), "maximum": p("integer", "Nombre de résultats (défaut 10)")},
       requis=["requete"])
def mail_chercher(requete: str, maximum: int = 10) -> str:
    return lister(requete, maximum)


def corps_texte(partie: dict) -> str:
    """Texte d'un message : la partie text/plain, sinon le HTML sans balises."""
    def decoder(data: str, pt: dict) -> str:
        brut = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))
        type_ = next((h.get("value", "") for h in pt.get("headers", []) or [] if h.get("name", "").lower() == "content-type"), "")
        m = re.search(r'charset="?([\w.:-]+)', type_, re.I)
        try:
            return brut.decode(m.group(1) if m else "utf-8", "replace")
        except LookupError:                                  # jeu de caractères inconnu
            return brut.decode("utf-8", "replace")
    texte, page = [], []

    def parcourir(pt: dict) -> None:
        mime, data = pt.get("mimeType", ""), (pt.get("body") or {}).get("data")
        if data and mime == "text/plain":
            texte.append(decoder(data, pt))
        elif data and mime == "text/html":
            page.append(decoder(data, pt))
        for sous in pt.get("parts", []) or []:
            parcourir(sous)
    parcourir(partie)
    if texte:
        return "\n".join(texte)
    brut = re.sub(r"(?is)<(script|style).*?</\1>", " ", "\n".join(page))
    brut = re.sub(r"(?s)<br\s*/?>|</p>|</div>", "\n", brut)
    return html.unescape(re.sub(r"<[^>]+>", " ", brut))


@outil("mail_lire", "Lit un mail en entier (par son identifiant donné entre crochets).", "MAIL",
       {"id": p("string", "Identifiant du mail")}, requis=["id"])
def mail_lire(id: str) -> str:
    try:
        d = gmail().messages().get(userId="me", id=id, format="full").execute()
    except Exception as e:
        raise erreur_google(e)
    h = entetes(d)
    corps = re.sub(r"\n{3,}", "\n\n", corps_texte(d.get("payload", {}))).strip()
    return (f"De : {h.get('from', '?')}\nÀ : {h.get('to', '')}\nDate : {h.get('date', '')}\n"
            f"Objet : {h.get('subject', '')}\n\n{corps[:8000]}")


def preparer(destinataire: str, objet: str, texte: str, repondre_a: str) -> dict:
    msg = EmailMessage()
    msg.set_content(texte)
    corps: dict = {}
    if repondre_a:
        try:
            orig = gmail().messages().get(userId="me", id=repondre_a, format="metadata",
                                          metadataHeaders=["Message-ID", "Subject", "From", "Reply-To"]).execute()
        except Exception as e:
            raise erreur_google(e)
        h = entetes(orig)
        destinataire = destinataire or h.get("reply-to") or h.get("from", "")
        objet = objet or ("Re: " + h.get("subject", "")).replace("Re: Re:", "Re:")
        if h.get("message-id"):
            msg["In-Reply-To"] = h["message-id"]
            msg["References"] = h["message-id"]
        corps["threadId"] = orig.get("threadId")
    if not destinataire:
        raise ErreurOutil("Il me faut l'adresse du destinataire.")
    msg["To"], msg["Subject"] = destinataire, objet or "(sans objet)"
    corps["raw"] = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
    return corps


@outil("mail_brouillon", "Prépare un brouillon dans Gmail (rien n'est envoyé).", "MAIL",
       {"destinataire": p("string", "Adresse e-mail"), "objet": p("string", "Objet"), "texte": p("string", "Texte"),
        "repondre_a": p("string", "Identifiant du mail auquel répondre (facultatif)")}, requis=["texte"])
def mail_brouillon(texte: str, destinataire: str = "", objet: str = "", repondre_a: str = "") -> str:
    corps = preparer(destinataire, objet, texte, repondre_a)
    try:
        gmail().drafts().create(userId="me", body={"message": corps}).execute()
    except Exception as e:
        raise erreur_google(e)
    return "Brouillon prêt dans Gmail."


def _question_envoi(args: dict) -> str:
    return (f"Envoyer le mail à {args.get('destinataire') or 'l’expéditeur'}"
            + (f", objet « {args['objet']} »" if args.get("objet") else "") + f" : « {args.get('texte', '')[:160]} »")


@outil("mail_envoyer", "Envoie un mail depuis Gmail (après confirmation).", "MAIL",
       {"destinataire": p("string", "Adresse e-mail"), "objet": p("string", "Objet"), "texte": p("string", "Texte"),
        "repondre_a": p("string", "Identifiant du mail auquel répondre (facultatif)")}, requis=["texte"],
       confirmer=_question_envoi)
def mail_envoyer(texte: str, destinataire: str = "", objet: str = "", repondre_a: str = "") -> str:
    corps = preparer(destinataire, objet, texte, repondre_a)
    try:
        gmail().messages().send(userId="me", body=corps).execute()
    except Exception as e:
        raise erreur_google(e)
    return "Mail envoyé."
