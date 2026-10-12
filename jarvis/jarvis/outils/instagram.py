"""Instagram par l'API officielle (Graph API) : comptes professionnels ou créateurs reliés à une page Facebook,
jeton d'accès longue durée. Abonnés et vues comparés à la veille, plusieurs comptes. Jarvis note les abonnés de
chaque jour dans sa mémoire pour faire la comparaison."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from .. import reseau
from ..services import S
from . import ErreurOutil, module, outil, p

API = "https://graph.facebook.com/v21.0"


@module("instagram", "INSTAGRAM")
def etat() -> tuple[str, str]:
    comptes = S.cfg.get("instagram.comptes", []) or []
    if not comptes:
        return "non_configure", "[[instagram.comptes]] nom, id, jeton dans config.toml"
    return "pret", f"{len(comptes)} compte(s)"


def ig(chemin: str, jeton: str, **params):
    r = reseau.get(API + chemin, "Instagram", params={**params, "access_token": jeton})
    if isinstance(r, dict) and r.get("error"):
        raise ErreurOutil(f"Instagram : {r['error'].get('message', r['error'])}")
    return r


def vues_jour(compte: dict, jour: date) -> int | None:
    """Vues du compte sur une journée (métrique views, total), None si l'API ne la donne pas."""
    debut = int(datetime.combine(jour, datetime.min.time()).timestamp())
    try:
        r = ig(f"/{compte['id']}/insights", compte["jeton"], metric="views", period="day", metric_type="total_value",
               since=debut, until=debut + 86400)
        for m in r.get("data", []):
            tv = m.get("total_value") or {}
            if "value" in tv:
                return int(tv["value"])
            vals = m.get("values") or []
            if vals:
                return int(vals[-1].get("value", 0))
    except ErreurOutil:
        return None
    return None


def fiche(compte: dict) -> str:
    if not compte.get("id") or not compte.get("jeton"):
        raise ErreurOutil(f"Compte Instagram « {compte.get('nom', '?')} » incomplet (id et jeton requis).")
    info = ig(f"/{compte['id']}", compte["jeton"], fields="username,followers_count,follows_count,media_count")
    abonnes = int(info.get("followers_count", 0))
    aujourd_hui = date.today()
    cle = f"instagram:{compte['id']}:abonnes"
    S.memoire.noter_valeur(cle, aujourd_hui.isoformat(), abonnes)
    hier = S.memoire.valeur(cle, (aujourd_hui - timedelta(days=1)).isoformat())
    ligne = f"@{info.get('username', compte.get('nom'))} : {abonnes} abonnés"
    if hier is not None:
        d = abonnes - int(hier)
        ligne += f" ({'+' if d >= 0 else ''}{d} depuis hier)"
    else:
        ligne += " (pas encore de valeur d'hier : je note chaque jour à partir de maintenant)"
    v_hier, v_avant = vues_jour(compte, aujourd_hui - timedelta(days=1)), vues_jour(compte, aujourd_hui - timedelta(days=2))
    if v_hier is not None:
        ligne += f", {v_hier} vues hier"
        if v_avant:
            ligne += f" ({(v_hier - v_avant) / v_avant * 100:+.0f} % par rapport à avant-hier)"
    try:
        medias = ig(f"/{compte['id']}/media", compte["jeton"], fields="caption,media_type,timestamp,like_count,comments_count",
                    limit=3).get("data", [])
        for m in medias:
            titre = (m.get("caption") or "").split("\n")[0][:60]
            ligne += f"\n  dernier post {m.get('timestamp', '')[:10]} ({m.get('media_type', '').lower()}) « {titre} » : " \
                     f"{m.get('like_count', 0)} j'aime, {m.get('comments_count', 0)} commentaires"
    except ErreurOutil:
        pass
    return ligne


@outil("instagram_stats", "Abonnés et vues Instagram comparés à la veille, pour un compte ou tous.", "INSTAGRAM",
       {"compte": p("string", "Nom du compte (défaut : tous)")})
def instagram_stats(compte: str = "") -> str:
    comptes = S.cfg.get("instagram.comptes", []) or []
    if not comptes:
        raise ErreurOutil("Instagram n'est pas configuré : il faut un compte professionnel ou créateur relié à une page "
                          "Facebook et un jeton de l'API Graph (voir README), dans [[instagram.comptes]].")
    if compte:
        comptes = [c for c in comptes if compte.lower() in str(c.get("nom", "")).lower()] or comptes
    return "\n".join(fiche(c) for c in comptes)


def noter_chaque_jour() -> None:
    """Appelé au démarrage puis toutes les 6 heures : garde la trace des abonnés pour la comparaison."""
    for c in S.cfg.get("instagram.comptes", []) or []:
        try:
            info = ig(f"/{c['id']}", c["jeton"], fields="followers_count")
            S.memoire.noter_valeur(f"instagram:{c['id']}:abonnes", date.today().isoformat(), int(info.get("followers_count", 0)))
        except Exception:
            pass
