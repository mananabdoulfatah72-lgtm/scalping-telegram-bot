"""Appels HTTP des outils (Hue, Discord, Instagram, météo...) avec des erreurs claires en français."""
from __future__ import annotations

from typing import Any

import requests

from .outils import ErreurOutil

DELAI = 12


def requete(methode: str, url: str, service: str, **kw: Any) -> Any:
    kw.setdefault("timeout", DELAI)
    try:
        r = requests.request(methode, url, **kw)
    except requests.Timeout:
        raise ErreurOutil(f"{service} ne répond pas (délai dépassé).")
    except requests.ConnectionError:
        raise ErreurOutil(f"Impossible de joindre {service} (réseau ou adresse).")
    if r.status_code in (401, 403):
        raise ErreurOutil(f"{service} refuse l'accès : jeton ou droits à vérifier dans la configuration.")
    if r.status_code == 404:
        raise ErreurOutil(f"{service} : élément introuvable.")
    if r.status_code == 429:
        raise ErreurOutil(f"{service} limite les demandes, réessaie dans un moment.")
    if r.status_code >= 400:
        raise ErreurOutil(f"{service} a répondu une erreur {r.status_code} : {r.text[:200]}")
    if not r.content:
        return None
    try:
        return r.json()
    except ValueError:
        return r.text


def get(url: str, service: str, **kw: Any) -> Any:
    return requete("GET", url, service, **kw)


def post(url: str, service: str, **kw: Any) -> Any:
    return requete("POST", url, service, **kw)


def put(url: str, service: str, **kw: Any) -> Any:
    return requete("PUT", url, service, **kw)
