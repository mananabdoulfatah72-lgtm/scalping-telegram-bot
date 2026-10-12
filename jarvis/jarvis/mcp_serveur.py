"""Serveur MCP de Jarvis (stdio) : expose ses outils (domotique, PC, OBS, agenda, mémoire...) à Claude Desktop, à
Claude Code ou à tout client MCP. Si Jarvis tourne, chaque appel lui est transmis par l'API locale (même état,
confirmations à l'écran ou à la voix, neurones allumés) ; sinon l'outil s'exécute ici, sans les actions qui
demandent une confirmation.

Configuration de Claude Desktop (claude_desktop_config.json) :
  {"mcpServers": {"jarvis": {"command": "<python de Jarvis>", "args": ["-m", "jarvis", "--mcp"]}}}"""
from __future__ import annotations

import anyio
import requests

from . import __version__, outils
from .config import Config, jeton_local
from .services import S


def adresse() -> str:
    return f"http://127.0.0.1:{int(S.cfg.get('interface.port', 8765))}"


def jarvis_actif() -> bool:
    try:
        return requests.get(adresse() + "/api/etat", headers={"x-jarvis-jeton": jeton_local()}, timeout=1.5).ok
    except requests.RequestException:
        return False


def definitions() -> list[dict]:
    if jarvis_actif():
        r = requests.get(adresse() + "/api/outils", headers={"x-jarvis-jeton": jeton_local()}, timeout=5)
        r.raise_for_status()
        return r.json()
    return [{"name": d["name"], "description": d["description"], "input_schema": d["input_schema"]}
            for d in outils.definitions_api()]


def appeler(nom: str, arguments: dict) -> tuple[list[dict], bool]:
    if jarvis_actif():
        r = requests.post(adresse() + "/api/outil", headers={"x-jarvis-jeton": jeton_local()},
                          json={"nom": nom, "arguments": arguments, "origine": "mcp"}, timeout=180)
        r.raise_for_status()
        d = r.json()
        return d["contenu"], bool(d["erreur"])
    res, err = outils.executer(nom, arguments, confirmer=None, origine="mcp")
    return res.blocs_api(), err


def preparer_local() -> None:
    from .config import dossier
    from .confirmation import Confirmations
    from .memoire import Memoire
    S.cfg = S.cfg or Config.charger()
    S.memoire = S.memoire or Memoire(dossier() / "memoire.db")
    S.confirmations = S.confirmations or Confirmations()
    outils.charger_tous()


def creer_serveur():
    import mcp_types as types
    from mcp.server.lowlevel import Server

    async def lister(ctx, params):
        defs = await anyio.to_thread.run_sync(definitions)
        return types.ListToolsResult(tools=[types.Tool(name=d["name"], description=d["description"],
                                                        input_schema=d["input_schema"]) for d in defs])

    async def executer(ctx, params):
        contenu, err = await anyio.to_thread.run_sync(appeler, params.name, dict(params.arguments or {}))
        blocs = []
        for b in contenu:
            if b.get("type") == "image":
                blocs.append(types.ImageContent(type="image", data=b["source"]["data"], mime_type=b["source"]["media_type"]))
            else:
                blocs.append(types.TextContent(type="text", text=b.get("text", "")))
        return types.CallToolResult(content=blocs, is_error=err)

    return Server("jarvis", version=__version__, instructions="Outils de Jarvis : PC, maison, OBS, agenda, mail, "
                  "mémoire et plus. Les actions sensibles sont confirmées par l'utilisateur sur l'écran de Jarvis.",
                  on_list_tools=lister, on_call_tool=executer)


async def servir() -> None:
    from mcp.server.stdio import stdio_server
    serveur = creer_serveur()
    async with stdio_server() as (lecture, ecriture):
        await serveur.run(lecture, ecriture, serveur.create_initialization_options())


def lancer() -> None:
    preparer_local()
    anyio.run(servir)

