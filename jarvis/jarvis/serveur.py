"""Serveur local de Jarvis (FastAPI) : sert le cerveau à l'écran (ui/), lui envoie en direct tout ce qui se
passe (websocket), reçoit les demandes tapées, les confirmations, le bouton Parler, les appels du serveur MCP et
les webhooks Twilio.

Sécurité : chaque appel (sauf Twilio, signé par Twilio) exige le jeton local, glissé dans la page servie ; un site
web ouvert dans le navigateur ne peut donc pas commander Jarvis. Par défaut le serveur n'écoute que ce PC. La page
(donc le jeton) n'est donnée qu'à une demande vraiment locale : venue de ce PC, adressée à 127.0.0.1 ou localhost
(contre les sites qui redirigent leur nom vers le PC), et pas relayée par un tunnel ngrok ou cloudflared (ouvert
pour Twilio, il vient lui aussi de ce PC) ; sinon il faut le mode réseau et sa clé."""
from __future__ import annotations

import asyncio
import json
import secrets
import threading
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from . import __version__, outils
from .bus import bus
from .config import jeton_local
from .services import S

UI = Path(__file__).parent / "ui"
NOMS_LOCAUX = {"127.0.0.1", "localhost", "::1"}
ENTETES_RELAIS = ("x-forwarded-for", "x-forwarded-host", "forwarded", "x-real-ip", "cf-connecting-ip")


def nom_hote(entete: str) -> str:
    """« 127.0.0.1:8765 » -> « 127.0.0.1 », « [::1]:8765 » -> « ::1 »."""
    h = (entete or "").strip().lower()
    if h.startswith("["):
        return h[1:].split("]", 1)[0]
    return h.rsplit(":", 1)[0] if h.count(":") == 1 else h


def demande_locale(conn: Request | WebSocket) -> bool:
    client = conn.client.host if conn.client else ""
    if client not in ("127.0.0.1", "::1") or any(e in conn.headers for e in ENTETES_RELAIS):
        return False
    return nom_hote(conn.headers.get("host", "")) in NOMS_LOCAUX


def creer_app(app_jarvis: Any = None, demo: bool = False) -> FastAPI:
    jeton = jeton_local()
    cfg = S.cfg
    reseau = bool(cfg.get("interface.reseau", False)) if cfg else False
    cle_reseau = cfg.get("interface.cle", "") if cfg else ""
    api = FastAPI(title="Jarvis", version=__version__, docs_url=None, redoc_url=None, openapi_url=None)
    api.mount("/ui", StaticFiles(directory=str(UI)), name="ui")

    def verifier(jeton_recu: str | None) -> None:
        if not jeton_recu or not secrets.compare_digest(jeton_recu, jeton):
            raise HTTPException(403, "jeton local manquant ou faux")

    def verifier_reseau(request: Request) -> None:
        if demande_locale(request):
            return
        cle = request.query_params.get("cle", "")
        if not (reseau and cle_reseau and secrets.compare_digest(cle, cle_reseau)):
            raise HTTPException(403, "accès réseau désactivé (ou clé fausse)")

    @api.get("/", response_class=HTMLResponse)
    def accueil(request: Request):
        verifier_reseau(request)
        page = (UI / "index.html").read_text(encoding="utf-8")
        return page.replace("__JETON__", jeton).replace("__DEMO__", "true" if demo else "false")

    @api.websocket("/ws")
    async def flux(ws: WebSocket):
        if ws.query_params.get("jeton") != jeton:
            await ws.close(code=4403)
            return
        await ws.accept()
        boucle = asyncio.get_running_loop()
        file: asyncio.Queue = asyncio.Queue(maxsize=2000)

        def pousser(evt: dict) -> None:
            def mettre():
                if file.qsize() < 1900 or evt["type"] not in ("audio", "micro", "reponse"):
                    try:
                        file.put_nowait(evt)
                    except asyncio.QueueFull:
                        pass
            boucle.call_soon_threadsafe(mettre)

        bus.abonner(pousser)
        try:
            for evt in bus.instantane():
                await ws.send_text(json.dumps(evt, ensure_ascii=False, default=str))
            await ws.send_text(json.dumps({"type": "modules", "liste": outils.etats_modules(),
                                           "moteur": getattr(app_jarvis, "nom_moteur", "démo" if demo else "?"),
                                           "problemes": getattr(app_jarvis, "problemes", []),
                                           "voix": bool(getattr(app_jarvis, "boucle", None))}, ensure_ascii=False))
            while True:
                evt = await file.get()
                await ws.send_text(json.dumps(evt, ensure_ascii=False, default=str))
        except (WebSocketDisconnect, RuntimeError):
            pass
        finally:
            bus.desabonner(pousser)

    async def corps(request: Request) -> dict:
        try:
            return await request.json()
        except Exception:
            return {}

    @api.post("/api/message")
    async def message(request: Request):
        verifier(request.headers.get("x-jarvis-jeton"))
        texte = str((await corps(request)).get("texte", "")).strip()[:4000]
        if not texte or app_jarvis is None:
            return {"ok": False}
        synth = app_jarvis.synthese if cfg.get("interface.parler_reponses_clavier", True) else None
        if synth is not None:
            synth.reprendre()
        threading.Thread(target=app_jarvis.cerveau.traiter, kwargs=dict(
            texte=texte, origine="clavier", sur_phrase=synth.ajouter if synth else None), daemon=True).start()
        return {"ok": True}

    @api.post("/api/confirmation")
    async def confirmation(request: Request):
        verifier(request.headers.get("x-jarvis-jeton"))
        d = await corps(request)
        return {"ok": S.confirmations.repondre(str(d.get("id", "")), bool(d.get("ok")))}

    @api.post("/api/parler")
    async def parler(request: Request):
        verifier(request.headers.get("x-jarvis-jeton"))
        if app_jarvis is not None and app_jarvis.boucle is not None:
            if app_jarvis.synthese is not None:
                app_jarvis.synthese.stop()            # Parler pendant qu'il parle : il se tait et écoute
            app_jarvis.boucle.declencher()
            return {"ok": True}
        return {"ok": False, "raison": "la voix n'est pas active"}

    @api.post("/api/stop")
    async def stop(request: Request):
        verifier(request.headers.get("x-jarvis-jeton"))
        if app_jarvis is not None and app_jarvis.synthese is not None:
            app_jarvis.synthese.stop()
        return {"ok": True}

    @api.get("/api/etat")
    def etat(request: Request):
        verifier(request.headers.get("x-jarvis-jeton") or request.query_params.get("jeton"))
        return {"version": __version__, "moteur": getattr(app_jarvis, "nom_moteur", "?"),
                "modules": outils.etats_modules(), "problemes": getattr(app_jarvis, "problemes", [])}

    # ------------------------------------------------------------------ pour le serveur MCP (même PC)
    @api.get("/api/outils")
    def liste_outils(request: Request):
        verifier(request.headers.get("x-jarvis-jeton"))
        return [{"name": d["name"], "description": d["description"], "input_schema": d["input_schema"]}
                for d in outils.definitions_api()]

    @api.post("/api/outil")
    def outil(request: Request, d: dict):
        verifier(request.headers.get("x-jarvis-jeton"))
        cerveau = getattr(app_jarvis, "cerveau", None)
        if cerveau is not None and cerveau.occupe:
            confirmer = cerveau.confirmer                 # demande en cours (moteur Claude Code) : même canal
        else:
            confirmer = lambda q: S.confirmations.demander(q)    # noqa: E731 - question à l'écran
        res, err = outils.executer(str(d.get("nom", "")), d.get("arguments") or {}, confirmer=confirmer,
                                   origine=str(d.get("origine", "mcp")))
        return {"contenu": res.blocs_api(), "erreur": err}

    # ------------------------------------------------------------------ Twilio (conversation téléphonique)
    def signature_valide(request: Request, params: dict) -> bool:
        try:
            from twilio.request_validator import RequestValidator
        except ImportError:
            return False
        url = cfg.get("twilio.url_publique", "").rstrip("/") + request.url.path
        if request.url.query:
            url += "?" + request.url.query
        return RequestValidator(cfg.get("twilio.jeton", "")).validate(url, params, request.headers.get("x-twilio-signature", ""))

    @api.post("/twilio/voix/{session}")
    async def twilio_voix(session: str, request: Request):
        params = dict((await request.form()).items())
        if not signature_valide(request, params):
            raise HTTPException(403, "signature Twilio invalide")
        from .outils import appels
        twiml = await asyncio.to_thread(appels.webhook_voix, session, params)
        return Response(twiml, media_type="application/xml")

    @api.post("/twilio/statut/{session}")
    async def twilio_statut(session: str, request: Request):
        params = dict((await request.form()).items())
        if not signature_valide(request, params):
            raise HTTPException(403, "signature Twilio invalide")
        from .outils import appels
        appels.webhook_statut(session, params)
        return JSONResponse({"ok": True})

    return api
