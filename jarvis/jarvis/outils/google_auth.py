"""Connexion Google (Agenda et Gmail) : identifiants OAuth « application de bureau » créés une fois dans la
console Google Cloud (voir README), enregistrés dans le dossier de Jarvis sous google_identifiants.json. Au premier
usage, le navigateur s'ouvre pour autoriser Jarvis ; le jeton est gardé dans google_jeton.json."""
from __future__ import annotations

import threading

from ..config import dossier
from ..services import S
from . import ErreurOutil

PORTEES = ["https://www.googleapis.com/auth/calendar",
           "https://www.googleapis.com/auth/gmail.readonly",
           "https://www.googleapis.com/auth/gmail.compose",
           "https://www.googleapis.com/auth/gmail.send"]
_verrou = threading.Lock()
_services: dict = {}


def etat_google() -> tuple[str, str]:
    try:
        import googleapiclient  # noqa: F401
        import google_auth_oauthlib  # noqa: F401
    except ImportError:
        return "absent", "modules Google à installer (installer.bat)"
    if not (dossier() / "google_identifiants.json").exists():
        return "non_configure", "google_identifiants.json à créer (voir README)"
    if not (dossier() / "google_jeton.json").exists():
        return "non_configure", "autorisation à donner au premier usage (le navigateur s'ouvrira)"
    return "pret", "compte Google relié"


def identifiants():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        raise ErreurOutil("Agenda et Gmail ont besoin des modules Google (relance installer.bat).")
    fichier_id, fichier_jeton = dossier() / "google_identifiants.json", dossier() / "google_jeton.json"
    creds = None
    if fichier_jeton.exists():
        creds = Credentials.from_authorized_user_file(str(fichier_jeton), PORTEES)
    if creds and creds.valid:
        return creds
    if creds and creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            fichier_jeton.write_text(creds.to_json(), encoding="utf-8")
            return creds
        except Exception:
            creds = None
    if not fichier_id.exists():
        raise ErreurOutil("Google n'est pas configuré : crée des identifiants OAuth « application de bureau » dans la "
                          "console Google Cloud et enregistre-les sous google_identifiants.json dans le dossier de Jarvis "
                          "(étapes dans le README).")
    flow = InstalledAppFlow.from_client_secrets_file(str(fichier_id), PORTEES)
    try:                                         # 5 minutes pour autoriser, sinon Jarvis reprend la main
        creds = flow.run_local_server(port=0, open_browser=True, timeout_seconds=300,
                                      authorization_prompt_message="Autorise Jarvis dans la page qui vient de s'ouvrir.",
                                      success_message="Jarvis est relié à ton compte Google. Tu peux fermer cette page.")
    except Exception as e:
        raise ErreurOutil(f"L'autorisation Google n'a pas été donnée ({type(e).__name__}). Redemande pour réessayer.")
    if creds is None:
        raise ErreurOutil("L'autorisation Google n'a pas été donnée à temps. Redemande pour réessayer.")
    fichier_jeton.write_text(creds.to_json(), encoding="utf-8")
    return creds


def service(nom: str, version: str):
    with _verrou:
        if nom not in _services:
            from googleapiclient.discovery import build
            _services[nom] = build(nom, version, credentials=identifiants(), cache_discovery=False)
        return _services[nom]


def erreur_google(e: Exception) -> ErreurOutil:
    texte = str(e)
    if "invalid_grant" in texte or "Token has been expired" in texte:
        (dossier() / "google_jeton.json").unlink(missing_ok=True)
        _services.clear()
        return ErreurOutil("L'autorisation Google a expiré : redemande, le navigateur s'ouvrira pour la renouveler.")
    return ErreurOutil(f"Google a répondu une erreur : {texte[:300]}")


def fuseau() -> str:
    return S.cfg.get("general.fuseau", "Europe/Paris")
