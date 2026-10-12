"""Agenda Google : tous les agendas du compte, y compris les agendas abonnés (iCal) ; création d'événement avec
confirmation."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from . import ErreurOutil, module, outil, p
from .google_auth import erreur_google, etat_google, fuseau, service

JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]


@module("agenda", "AGENDA")
def etat() -> tuple[str, str]:
    return etat_google()


def jour_fr(d: datetime) -> str:
    return f"{JOURS[d.weekday()]} {d.day} {MOIS[d.month - 1]}"


def lire_date(texte: str, tz: ZoneInfo) -> datetime:
    try:
        d = datetime.fromisoformat(texte.strip().replace("Z", "+00:00"))
    except ValueError:
        raise ErreurOutil(f"Date illisible : {texte} (format attendu AAAA-MM-JJTHH:MM).")
    return d if d.tzinfo else d.replace(tzinfo=tz)


def agendas() -> list[dict]:
    try:
        return service("calendar", "v3").calendarList().list().execute().get("items", [])
    except ErreurOutil:
        raise
    except Exception as e:
        raise erreur_google(e)


@outil("agenda_evenements", "Événements à venir sur tous les agendas (y compris les agendas abonnés).", "AGENDA",
       {"jours": p("integer", "Nombre de jours à couvrir à partir du début (défaut 1 = aujourd'hui)"),
        "debut": p("string", "Premier jour, AAAA-MM-JJ (défaut aujourd'hui)"),
        "recherche": p("string", "Mot à chercher dans les événements (facultatif)")})
def agenda_evenements(jours: int = 1, debut: str = "", recherche: str = "") -> str:
    tz = ZoneInfo(fuseau())
    d0 = lire_date(debut, tz) if debut else datetime.now(tz)
    d0 = d0.replace(hour=0, minute=0, second=0, microsecond=0)
    d1 = d0 + timedelta(days=max(1, min(60, int(jours))))
    cal = service("calendar", "v3")
    evts = []
    try:
        for a in agendas():
            if a.get("hidden"):
                continue
            kw = dict(calendarId=a["id"], timeMin=d0.isoformat(), timeMax=d1.isoformat(), singleEvents=True,
                      orderBy="startTime", maxResults=100)
            if recherche:
                kw["q"] = recherche
            for e in cal.events().list(**kw).execute().get("items", []):
                if e.get("status") == "cancelled":
                    continue
                s, f = e.get("start", {}), e.get("end", {})
                if "dateTime" in s:
                    ds, df = datetime.fromisoformat(s["dateTime"]).astimezone(tz), datetime.fromisoformat(f["dateTime"]).astimezone(tz)
                    quand, cle = f"{jour_fr(ds)} {ds:%H:%M}–{df:%H:%M}", ds
                else:
                    ds = datetime.fromisoformat(s["date"]).replace(tzinfo=tz)
                    quand, cle = f"{jour_fr(ds)} (journée)", ds
                lieu = f" · {e['location']}" if e.get("location") else ""
                evts.append((cle, f"{quand} · {e.get('summary', '(sans titre)')} [{a.get('summary', '')}]{lieu}"))
    except ErreurOutil:
        raise
    except Exception as e:
        raise erreur_google(e)
    if not evts:
        return "Rien dans l'agenda sur cette période."
    return "\n".join(t for _, t in sorted(evts, key=lambda x: x[0]))


def _question_creer(args: dict) -> str:
    return (f"Créer l'événement « {args.get('titre')} » le {args.get('debut', '').replace('T', ' à ')}"
            + (f" dans l'agenda {args['agenda']}" if args.get("agenda") else ""))


@outil("agenda_creer", "Crée un événement dans l'agenda Google (après confirmation).", "AGENDA",
       {"titre": p("string", "Titre"), "debut": p("string", "Début, AAAA-MM-JJTHH:MM (ou AAAA-MM-JJ pour la journée)"),
        "fin": p("string", "Fin, même format (sinon durée)"), "duree_minutes": p("integer", "Durée (défaut 60)"),
        "agenda": p("string", "Nom de l'agenda (défaut : principal)"), "lieu": p("string", "Lieu"),
        "description": p("string", "Description"), "rappel_minutes": p("integer", "Rappel avant, en minutes")},
       requis=["titre", "debut"], confirmer=_question_creer)
def agenda_creer(titre: str, debut: str, fin: str = "", duree_minutes: int = 60, agenda: str = "", lieu: str = "",
                 description: str = "", rappel_minutes: int | None = None) -> str:
    tz = ZoneInfo(fuseau())
    cal_id = "primary"
    if agenda:
        modifiables = [a for a in agendas() if a.get("accessRole") in ("owner", "writer")]
        choix = next((a for a in modifiables if agenda.lower() in a.get("summary", "").lower()), None)
        if not choix:
            raise ErreurOutil(f"Pas d'agenda modifiable nommé « {agenda} » : {', '.join(a.get('summary', '') for a in modifiables)}.")
        cal_id = choix["id"]
    corps: dict = {"summary": titre}
    if len(debut.strip()) == 10:
        jour = lire_date(debut, tz).date()
        corps["start"] = {"date": jour.isoformat()}
        corps["end"] = {"date": (lire_date(fin, tz).date() if fin else jour + timedelta(days=1)).isoformat()}
    else:
        ds = lire_date(debut, tz)
        df = lire_date(fin, tz) if fin else ds + timedelta(minutes=int(duree_minutes))
        if df <= ds:
            raise ErreurOutil("La fin de l'événement doit être après le début.")
        corps["start"] = {"dateTime": ds.isoformat(), "timeZone": fuseau()}
        corps["end"] = {"dateTime": df.isoformat(), "timeZone": fuseau()}
    if lieu:
        corps["location"] = lieu
    if description:
        corps["description"] = description
    if rappel_minutes is not None:
        corps["reminders"] = {"useDefault": False, "overrides": [{"method": "popup", "minutes": int(rappel_minutes)}]}
    try:
        e = service("calendar", "v3").events().insert(calendarId=cal_id, body=corps).execute()
    except Exception as ex:
        raise erreur_google(ex)
    return f"Événement « {titre} » créé ({e.get('htmlLink', '')})."
