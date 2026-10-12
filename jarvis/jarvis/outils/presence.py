"""Présence : Jarvis surveille si ton téléphone est sur le wifi de la maison (ping de son adresse IP fixe) et
déclenche des actions à l'arrivée et au départ (scène Hue, message...). Envoie aussi des notifications sur le
téléphone par ntfy (application gratuite ntfy, un « sujet » secret à choisir)."""
from __future__ import annotations

import platform
import subprocess
import threading

from .. import reseau
from ..bus import bus
from ..services import S, annoncer
from . import ErreurOutil, module, outil, p


@module("presence", "PRESENCE")
def etat() -> tuple[str, str]:
    ip, sujet = S.cfg.get("presence.ip_telephone", ""), S.cfg.get("ntfy.sujet", "")
    if not ip and not sujet:
        return "non_configure", "[presence] ip_telephone et/ou [ntfy] sujet dans config.toml"
    morceaux = []
    if ip:
        morceaux.append({True: "téléphone à la maison", False: "téléphone absent", None: "présence en cours de lecture"}[SURVEILLANT.present])
    if sujet:
        morceaux.append("notifications ntfy prêtes")
    return "pret", ", ".join(morceaux)


def ping(ip: str) -> bool:
    if platform.system() == "Windows":
        cmd = ["ping", "-n", "1", "-w", "1500", ip]
    else:
        cmd = ["ping", "-c", "1", "-W", "2", ip]
    try:
        r = subprocess.run(cmd, capture_output=True, timeout=5,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (subprocess.TimeoutExpired, OSError):
        return False
    # Windows renvoie 0 même pour « hôte inaccessible » : on vérifie le TTL de la réponse
    return r.returncode == 0 and b"TTL=" in r.stdout.upper()


class Surveillant:
    """Un téléphone en veille répond mal aux pings : il faut plusieurs absences de suite (environ 5 minutes)
    pour le déclarer parti, une seule réponse pour le déclarer arrivé."""
    ABSENCES = 10

    def __init__(self):
        self.present: bool | None = None
        self.absences = 0
        self._stop = threading.Event()

    def demarrer(self) -> None:
        if S.cfg.get("presence.ip_telephone", ""):
            threading.Thread(target=self._boucle, daemon=True, name="presence").start()

    def arreter(self) -> None:
        self._stop.set()

    def _boucle(self) -> None:
        while not self._stop.is_set():
            self.observer(ping(S.cfg.get("presence.ip_telephone")))
            self._stop.wait(max(10, int(S.cfg.get("presence.intervalle", 30))))

    def observer(self, repond: bool) -> str | None:
        """Met à jour l'état avec un ping ; renvoie « arrivee » ou « depart » au changement."""
        if repond:
            self.absences = 0
            if self.present is not True:
                avant, self.present = self.present, True
                if avant is False:
                    self._changement("arrivee")
                    return "arrivee"
        else:
            self.absences += 1
            if self.present is not False and (self.absences >= self.ABSENCES or self.present is None and self.absences >= 3):
                avant, self.present = self.present, False
                if avant is True:
                    self._changement("depart")
                    return "depart"
        return None

    def _changement(self, quand: str) -> None:
        bus.publier("presence", present=self.present, evenement=quand)
        from . import executer
        for action in S.cfg.get(f"presence.{quand}", []) or []:
            if isinstance(action, dict) and action.get("outil"):
                executer(action["outil"], action.get("arguments", {}), confirmer=lambda q: False, origine="presence")
            elif isinstance(action, dict) and action.get("dire"):
                annoncer(action["dire"])
        if quand == "arrivee" and not any(isinstance(a, dict) and a.get("dire") for a in S.cfg.get("presence.arrivee", []) or []):
            annoncer("Bon retour à la maison.")


SURVEILLANT = Surveillant()


def notifier(message: str, titre: str = "Jarvis", silencieux: bool = False) -> str:
    sujet = S.cfg.get("ntfy.sujet", "")
    if not sujet:
        if silencieux:
            return ""
        raise ErreurOutil("Les notifications ne sont pas configurées : installe l'application ntfy sur le téléphone, "
                          "abonne-toi à un sujet secret et mets-le dans [ntfy] sujet de config.toml.")
    serveur = S.cfg.get("ntfy.serveur", "https://ntfy.sh").rstrip("/")
    reseau.post(f"{serveur}/{sujet}", "ntfy", data=message.encode("utf-8"),
                params={"title": titre, "tags": "robot"})     # titre en paramètre : les accents passent
    return "Notification envoyée sur le téléphone."


@outil("telephone_notifier", "Envoie une notification sur le téléphone de l'utilisateur (application ntfy).",
       "PRESENCE", {"message": p("string", "Texte de la notification"), "titre": p("string", "Titre")},
       requis=["message"])
def telephone_notifier(message: str, titre: str = "Jarvis") -> str:
    return notifier(message, titre)


@outil("presence_etat", "Dit si le téléphone de l'utilisateur est à la maison (sur le wifi) en ce moment.", "PRESENCE")
def presence_etat() -> str:
    ip = S.cfg.get("presence.ip_telephone", "")
    if not ip:
        raise ErreurOutil("La présence n'est pas configurée : mets l'adresse IP fixe du téléphone dans "
                          "[presence] ip_telephone de config.toml.")
    present = ping(ip) or SURVEILLANT.present
    return "Le téléphone est à la maison." if present else "Le téléphone n'est pas sur le wifi de la maison."
