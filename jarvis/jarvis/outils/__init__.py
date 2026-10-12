"""Registre des outils de Jarvis. Chaque outil déclare sa zone du cerveau (pour l'affichage), son schéma
d'arguments (envoyé à Claude) et, s'il a un effet difficile à défaire (mail envoyé, appel, achat, commande),
une demande de confirmation : Jarvis demande « je confirme ? » lui-même, le modèle ne peut pas se l'accorder.

Un outil renvoie du texte, ou un Resultat avec des images (capture d'écran, page web). En cas de problème il
lève ErreurOutil avec un message clair pour l'utilisateur (ex. « Hue n'est pas configuré : ... »)."""
from __future__ import annotations

import base64
import importlib
import json
import time
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable

from ..bus import bus

ZONES = ["VOIX", "VISION", "DOMOTIQUE", "STREAMING", "PC", "AGENDA", "MAIL", "DISCORD", "INSTAGRAM",
         "RESERVATIONS", "NAVIGATEUR", "APPELS", "MEMOIRE", "PERSONNALITE", "PRESENCE", "UTILITAIRES", "MCP",
         "TELEGRAM"]
MAX_TEXTE = 20000


class ErreurOutil(Exception):
    """Erreur expliquée à l'utilisateur (module non configuré, appareil injoignable...)."""


@dataclass
class Resultat:
    texte: str = ""
    images: list[tuple[bytes, str]] = field(default_factory=list)   # (octets, type MIME)

    def blocs_api(self) -> list[dict]:
        blocs: list[dict] = []
        for octets, mime in self.images:
            blocs.append({"type": "image", "source": {"type": "base64", "media_type": mime,
                                                      "data": base64.standard_b64encode(octets).decode("ascii")}})
        blocs.append({"type": "text", "text": tronquer(self.texte or "(fait)")})
        return blocs

    def resume(self) -> str:
        t = (self.texte or "").strip().replace("\n", " ")
        return (t[:140] + "…") if len(t) > 140 else t


@dataclass
class Outil:
    nom: str
    description: str
    parametres: dict
    requis: list[str]
    fonction: Callable[..., Any]
    zone: str | Callable[[dict], str]
    confirmer: bool | Callable[[dict], str | None]
    module: str

    def zone_pour(self, args: dict) -> str:
        return self.zone(args) if callable(self.zone) else self.zone

    def schema(self) -> dict:
        return {"type": "object", "properties": self.parametres, "required": list(self.requis)}

    def resume_confirmation(self, args: dict) -> str | None:
        if callable(self.confirmer):
            return self.confirmer(args)
        if self.confirmer:
            details = ", ".join(f"{k} : {v}" for k, v in args.items() if v not in (None, ""))
            return f"{self.description.split('.')[0]}" + (f" ({details})" if details else "")
        return None


REGISTRE: dict[str, Outil] = {}
MODULES: dict[str, dict] = {}       # module -> {"zone", "etat": fn() -> (etat, message)}


def outil(nom: str, description: str, zone: str | Callable[[dict], str], parametres: dict | None = None,
          requis: list[str] | tuple = (), confirmer: bool | Callable[[dict], str | None] = False):
    """Décorateur : enregistre la fonction comme outil. parametres = {nom: schéma JSON de l'argument}."""
    def deco(fn):
        module = fn.__module__.rsplit(".", 1)[-1]
        REGISTRE[nom] = Outil(nom, description, parametres or {}, list(requis), fn, zone, confirmer, module)
        return fn
    return deco


def module(nom: str, zone: str):
    """Décorateur : fonction d'état d'un module, renvoie (etat, message) avec etat parmi pret, non_configure,
    absent (bibliothèque non installée), erreur."""
    def deco(fn):
        MODULES[nom] = {"zone": zone, "etat": fn}
        return fn
    return deco


def p(type_: str, description: str, **extra) -> dict:
    """Raccourci pour décrire un argument : p("string", "Nom de la pièce", enum=[...])."""
    return {"type": type_, "description": description, **extra}


MODULES_OUTILS = ["pc", "vision", "domotique", "streaming", "agenda", "mail", "discord", "instagram",
                  "navigateur", "appels", "memoire_outils", "personnalite", "presence", "utilitaires",
                  "telegram_outils"]


def charger_tous() -> None:
    """Importe chaque module d'outils (un module dont une bibliothèque manque reste chargé : il le signale à
    l'usage et dans l'état des modules)."""
    for m in MODULES_OUTILS:
        importlib.import_module(f"{__name__}.{m}")


def definitions_api() -> list[dict]:
    """Outils au format de l'API Claude, triés par nom (liste stable : le cache de prompt la réutilise)."""
    out = []
    for nom in sorted(REGISTRE):
        o = REGISTRE[nom]
        out.append({"name": o.nom, "description": o.description, "input_schema": o.schema(),
                    "eager_input_streaming": True})
    return out


TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "array": list, "object": dict}


def valider(o: Outil, args: Any) -> str | None:
    """Contrôle les arguments reçus (avec le streaming des arguments, l'API ne les valide plus elle-même)."""
    if not isinstance(args, dict):
        return "les arguments doivent être un objet JSON"
    for r in o.requis:
        if r not in args or args[r] is None:
            return f"argument obligatoire manquant : {r}"
    for k, v in args.items():
        sch = o.parametres.get(k)
        if sch is None:
            return f"argument inconnu : {k}"
        if v is None:
            continue
        typ = sch.get("type")
        if typ == "integer":
            if isinstance(v, bool) or not (isinstance(v, int) or (isinstance(v, float) and v.is_integer())):
                return f"{k} doit être un nombre entier"
        elif typ == "number":
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                return f"{k} doit être un nombre"
        elif typ in TYPES and not isinstance(v, TYPES[typ]):
            return f"{k} doit être de type {typ}"
        if "enum" in sch and v not in sch["enum"]:
            return f"{k} doit valoir l'une de ces valeurs : {', '.join(map(str, sch['enum']))}"
    return None


def normaliser(o: Outil, args: dict) -> dict:
    """Arguments validés, sans les valeurs nulles, entiers rendus entiers (3.0 -> 3)."""
    out = {}
    for k, v in args.items():
        if v is None:
            continue
        if o.parametres.get(k, {}).get("type") == "integer" and isinstance(v, float):
            v = int(v)
        out[k] = v
    return out


def tronquer(t: str, n: int = MAX_TEXTE) -> str:
    return t if len(t) <= n else t[:n] + f"\n[… {len(t) - n} caractères coupés]"


def executer(nom: str, args: Any, confirmer: Callable[[str], bool] | None = None,
             origine: str = "voix") -> tuple[Resultat, bool]:
    """Exécute un outil : validation, confirmation éventuelle, événements pour le cerveau à l'écran.
    Renvoie (résultat, est_une_erreur)."""
    o = REGISTRE.get(nom)
    if o is None:
        return Resultat(f"Outil inconnu : {nom}"), True
    erreur = valider(o, args)
    if erreur:
        return Resultat(json.dumps({"INVALID_JSON": erreur}, ensure_ascii=False)), True
    args = normaliser(o, args)
    zone = o.zone_pour(args)
    t0 = time.time()
    bus.publier("outil", nom=nom, zone=zone, phase="debut", origine=origine)
    if origine == "mcp":
        bus.publier("outil", nom=nom, zone="MCP", phase="debut", origine=origine)
    try:
        question = o.resume_confirmation(args)
        if question:
            if confirmer is None or not confirmer(question):
                res, err = Resultat("L'utilisateur n'a pas confirmé : action annulée, rien n'a été fait."), False
                bus.publier("outil", nom=nom, zone=zone, phase="fin", ok=False, resume="annulé",
                            duree=time.time() - t0, origine=origine)
                return res, err
        brut = o.fonction(**args)
        res = brut if isinstance(brut, Resultat) else Resultat("" if brut is None else str(brut))
        ok, err = True, False
    except ErreurOutil as e:
        res, ok, err = Resultat(str(e)), False, True
    except TypeError as e:
        res, ok, err = Resultat(f"Arguments incorrects pour {nom} : {e}"), False, True
    except Exception as e:                                   # erreur imprévue : on la dit sans planter Jarvis
        traceback.print_exc()
        res, ok, err = Resultat(f"Erreur pendant {nom} : {type(e).__name__} : {e}"), False, True
    bus.publier("outil", nom=nom, zone=zone, phase="fin", ok=ok, resume=res.resume(),
                duree=round(time.time() - t0, 2), origine=origine)
    return res, err


def etats_modules() -> list[dict]:
    out = []
    for nom, m in sorted(MODULES.items()):
        try:
            etat, msg = m["etat"]()
        except Exception as e:
            etat, msg = "erreur", str(e)
        out.append({"module": nom, "zone": m["zone"], "etat": etat, "message": msg})
    return out
