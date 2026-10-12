"""Utilitaires : météo (Open-Meteo, sans clé), minuteurs avec annonce vocale, heure et date."""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime

from .. import reseau
from ..bus import bus
from ..services import S, annoncer
from . import ErreurOutil, module, outil, p

METEO = {0: "ciel dégagé", 1: "plutôt dégagé", 2: "partiellement nuageux", 3: "couvert", 45: "brouillard",
         48: "brouillard givrant", 51: "bruine légère", 53: "bruine", 55: "bruine forte", 56: "bruine verglaçante",
         57: "bruine verglaçante forte", 61: "pluie faible", 63: "pluie", 65: "forte pluie", 66: "pluie verglaçante",
         67: "forte pluie verglaçante", 71: "neige faible", 73: "neige", 75: "forte neige", 77: "grains de neige",
         80: "averses faibles", 81: "averses", 82: "violentes averses", 85: "averses de neige",
         86: "fortes averses de neige", 95: "orage", 96: "orage avec grêle", 99: "orage avec forte grêle"}


@module("utilitaires", "UTILITAIRES")
def etat() -> tuple[str, str]:
    return "pret", f"{len(MINUTEURS.liste())} minuteur(s) en cours"


def lieu(ville: str) -> tuple[float, float, str]:
    r = reseau.get("https://geocoding-api.open-meteo.com/v1/search", "le service météo",
                   params={"name": ville, "count": 1, "language": "fr", "format": "json"})
    res = (r or {}).get("results") or []
    if not res:
        raise ErreurOutil(f"Je ne trouve pas la ville « {ville} ».")
    x = res[0]
    return x["latitude"], x["longitude"], f"{x['name']}" + (f", {x.get('country', '')}" if x.get("country") else "")


@outil("meteo", "Météo actuelle et prévisions (jusqu'à 7 jours) pour une ville.", "UTILITAIRES",
       {"ville": p("string", "Ville (par défaut celle de la configuration)"),
        "jours": p("integer", "Nombre de jours de prévision, 1 à 7 (1 = aujourd'hui)")})
def meteo(ville: str = "", jours: int = 1) -> str:
    ville = ville or S.cfg.get("general.ville", "Paris")
    jours = max(1, min(7, int(jours)))
    lat, lon, nom = lieu(ville)
    r = reseau.get("https://api.open-meteo.com/v1/forecast", "le service météo", params={
        "latitude": lat, "longitude": lon, "timezone": "auto", "forecast_days": jours,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,weather_code,wind_speed_10m,precipitation",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum"})
    c = r["current"]
    lignes = [f"{nom} maintenant : {METEO.get(c['weather_code'], 'temps inconnu')}, {c['temperature_2m']:.0f} °C "
              f"(ressenti {c['apparent_temperature']:.0f} °C), humidité {c['relative_humidity_2m']} %, "
              f"vent {c['wind_speed_10m']:.0f} km/h."]
    d = r["daily"]
    for i, jour in enumerate(d["time"]):
        pluie = d["precipitation_probability_max"][i]
        lignes.append(f"{jour} : {METEO.get(d['weather_code'][i], '?')}, de {d['temperature_2m_min'][i]:.0f} à "
                      f"{d['temperature_2m_max'][i]:.0f} °C, pluie {pluie if pluie is not None else '?'} % "
                      f"({d['precipitation_sum'][i]} mm).")
    return "\n".join(lignes)


class Minuteurs:
    def __init__(self):
        self._liste: dict[str, dict] = {}
        self._verrou = threading.Lock()

    def creer(self, secondes: float, libelle: str) -> dict:
        ident = uuid.uuid4().hex[:6]
        fin = time.time() + secondes
        t = threading.Timer(secondes, self._sonner, args=(ident,))
        t.daemon = True
        m = {"id": ident, "libelle": libelle, "fin": fin, "timer": t}
        with self._verrou:
            self._liste[ident] = m
        t.start()
        self._publier()
        return m

    def _sonner(self, ident: str) -> None:
        with self._verrou:
            m = self._liste.pop(ident, None)
        if not m:
            return
        self._publier()
        texte = f"Le minuteur {m['libelle']} est terminé." if m["libelle"] else "Le minuteur est terminé."
        annoncer(texte)
        try:
            from .presence import notifier
            notifier(texte, silencieux=True)
        except Exception:
            pass

    def annuler(self, ident: str) -> dict | None:
        with self._verrou:
            m = self._liste.pop(ident, None)
        if m:
            m["timer"].cancel()
            self._publier()
        return m

    def liste(self) -> list[dict]:
        with self._verrou:
            return sorted(({k: v for k, v in m.items() if k != "timer"} for m in self._liste.values()),
                          key=lambda m: m["fin"])

    def _publier(self) -> None:
        bus.publier("minuteurs", liste=self.liste())


MINUTEURS = Minuteurs()


def duree_parlee(s: float) -> str:
    s = int(round(s))
    h, m, sec = s // 3600, (s % 3600) // 60, s % 60
    morceaux = [f"{h} h" if h else "", f"{m} min" if m else "", f"{sec} s" if sec and not h else ""]
    return " ".join(x for x in morceaux if x) or "0 s"


@outil("minuteur_creer", "Lance un minuteur ; Jarvis l'annonce à voix haute (et sur le téléphone) à la fin.",
       "UTILITAIRES", {"secondes": p("integer", "Durée en secondes"), "libelle": p("string", "Nom (ex. pâtes)")},
       requis=["secondes"])
def minuteur_creer(secondes: int, libelle: str = "") -> str:
    if secondes <= 0 or secondes > 7 * 86400:
        raise ErreurOutil("Durée de minuteur impossible.")
    m = MINUTEURS.creer(secondes, libelle)
    return f"Minuteur {m['id']} lancé pour {duree_parlee(secondes)}" + (f" ({libelle})" if libelle else "") + "."


@outil("minuteurs", "Liste les minuteurs en cours et le temps restant.", "UTILITAIRES")
def minuteurs() -> str:
    l = MINUTEURS.liste()
    if not l:
        return "Aucun minuteur en cours."
    return "\n".join(f"{m['id']} {m['libelle'] or ''} : reste {duree_parlee(m['fin'] - time.time())}" for m in l)


@outil("minuteur_annuler", "Annule un minuteur (par son numéro, ou le plus proche si aucun numéro).", "UTILITAIRES",
       {"id": p("string", "Numéro du minuteur")})
def minuteur_annuler(id: str = "") -> str:
    l = MINUTEURS.liste()
    if not l:
        return "Aucun minuteur à annuler."
    m = MINUTEURS.annuler(id or l[0]["id"])
    if not m:
        raise ErreurOutil(f"Pas de minuteur numéro {id}.")
    return f"Minuteur {m['libelle'] or m['id']} annulé."


@outil("heure_date", "Heure, date et jour de la semaine actuels (sur le PC).", "UTILITAIRES")
def heure_date() -> str:
    from ..cerveau import date_parlee
    return date_parlee(datetime.now())
