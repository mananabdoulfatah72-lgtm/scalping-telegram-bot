"""Domotique Philips Hue (pont Hue, API locale) : allumer, éteindre, luminosité, couleur, blanc chaud/froid,
pièces et scènes (ambiances). Premier lancement : hue_appairer, après avoir appuyé sur le bouton du pont."""
from __future__ import annotations

import re

from .. import reseau
from ..services import S
from . import ErreurOutil, module, outil, p

COULEURS = {"rouge": (255, 0, 0), "vert": (0, 255, 0), "bleu": (0, 60, 255), "jaune": (255, 210, 0),
            "orange": (255, 120, 0), "violet": (140, 0, 255), "rose": (255, 60, 160), "cyan": (0, 220, 255),
            "turquoise": (0, 200, 170), "blanc": (255, 255, 255), "magenta": (255, 0, 200), "indigo": (75, 0, 200),
            "or": (255, 180, 40), "corail": (255, 110, 80), "lavande": (180, 140, 255), "pêche": (255, 170, 120)}
TEMPERATURES = {"chaud": 2700, "très chaud": 2200, "neutre": 4000, "froid": 5500, "très froid": 6500}


@module("domotique", "DOMOTIQUE")
def etat() -> tuple[str, str]:
    if not S.cfg.get("hue.bridge", ""):
        return "non_configure", "adresse du pont Hue à trouver (dis « appaire les lumières Hue »)"
    if not S.cfg.get("hue.utilisateur", ""):
        return "non_configure", "appuie sur le bouton du pont Hue puis dis « appaire les lumières »"
    return "pret", f"pont Hue {S.cfg.get('hue.bridge')}"


def rgb_xy(r: int, g: int, b: int) -> list[float]:
    """Couleur RVB -> coordonnées xy de Philips (gamut large, correction gamma)."""
    def lin(c: float) -> float:
        c /= 255
        return ((c + 0.055) / 1.055) ** 2.4 if c > 0.04045 else c / 12.92
    r_, g_, b_ = lin(r), lin(g), lin(b)
    X = r_ * 0.664511 + g_ * 0.154324 + b_ * 0.162028
    Y = r_ * 0.283881 + g_ * 0.668433 + b_ * 0.047685
    Z = r_ * 0.000088 + g_ * 0.072310 + b_ * 0.986039
    s = X + Y + Z
    return [0.3227, 0.329] if s == 0 else [round(X / s, 4), round(Y / s, 4)]


def couleur_xy(couleur: str) -> list[float]:
    c = couleur.strip().lower()
    m = re.fullmatch(r"#?([0-9a-f]{6})", c)
    if m:
        h = m.group(1)
        return rgb_xy(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    if c in COULEURS:
        return rgb_xy(*COULEURS[c])
    raise ErreurOutil(f"Couleur inconnue : {couleur}. Couleurs connues : {', '.join(COULEURS)}, ou un code #RRVVBB.")


def base() -> str:
    pont, user = S.cfg.get("hue.bridge", ""), S.cfg.get("hue.utilisateur", "")
    if not pont or not user:
        raise ErreurOutil("Les lumières Hue ne sont pas encore reliées : appuie sur le bouton rond du pont Hue, "
                          "puis demande-moi d'appairer les lumières.")
    return f"http://{pont}/api/{user}"


def hue(methode: str, chemin: str, corps: dict | None = None):
    r = reseau.requete(methode, f"{base()}{chemin}", "le pont Hue", json=corps)
    if isinstance(r, list) and r and isinstance(r[0], dict) and "error" in r[0]:
        raise ErreurOutil(f"Le pont Hue refuse : {r[0]['error'].get('description', r[0]['error'])}")
    return r


def cibles(nom: str) -> list[tuple[str, str, str]]:
    """Pièces et lumières qui correspondent au nom : [(type, id, nom)] ; « tout » = toutes les lumières."""
    n = nom.strip().lower()
    if n in ("", "tout", "toutes", "maison", "partout", "toutes les lumières"):
        return [("groups", "0", "toute la maison")]
    groupes = hue("GET", "/groups") or {}
    for gid, g in groupes.items():
        if g.get("name", "").lower() == n:
            return [("groups", gid, g["name"])]
    lumieres = hue("GET", "/lights") or {}
    for lid, l in lumieres.items():
        if l.get("name", "").lower() == n:
            return [("lights", lid, l["name"])]
    proches = [("groups", gid, g["name"]) for gid, g in groupes.items() if n in g.get("name", "").lower()]
    proches += [("lights", lid, l["name"]) for lid, l in lumieres.items() if n in l.get("name", "").lower()]
    if not proches:
        noms = [g.get("name") for g in groupes.values()] + [l.get("name") for l in lumieres.values()]
        raise ErreurOutil(f"Je ne trouve pas « {nom} ». Pièces et lumières : {', '.join(x for x in noms if x)}.")
    return proches[:1]


@outil("hue_lumieres", "Liste les pièces, lumières et scènes Hue avec leur état.", "DOMOTIQUE")
def hue_lumieres() -> str:
    groupes, lumieres, scenes = hue("GET", "/groups") or {}, hue("GET", "/lights") or {}, hue("GET", "/scenes") or {}
    lignes = []
    for g in groupes.values():
        if g.get("type") in ("Room", "Zone"):
            st = g.get("state", {})
            lignes.append(f"Pièce {g['name']} : {'allumée' if st.get('any_on') else 'éteinte'}")
    for l in lumieres.values():
        st = l.get("state", {})
        lum = round(st.get("bri", 0) / 254 * 100)
        lignes.append(f"Lumière {l['name']} : {'allumée à ' + str(lum) + ' %' if st.get('on') else 'éteinte'}"
                      f"{'' if st.get('reachable', True) else ' (injoignable)'}")
    noms_scenes = sorted({s.get("name", "") for s in scenes.values() if s.get("name")})
    if noms_scenes:
        lignes.append("Scènes : " + ", ".join(noms_scenes[:40]))
    return "\n".join(lignes) or "Aucune lumière trouvée sur le pont."


@outil("hue_regler", "Allume ou éteint une pièce, une lumière ou toute la maison, avec luminosité, couleur ou "
       "température de blanc.", "DOMOTIQUE",
       {"cible": p("string", "Pièce ou lumière (ex. salon, chambre, bureau) ; « tout » pour toute la maison"),
        "allumer": p("boolean", "true pour allumer, false pour éteindre"),
        "luminosite": p("integer", "Luminosité 1 à 100 %"),
        "couleur": p("string", "Couleur (rouge, bleu, violet...) ou code #RRVVBB"),
        "blanc": p("string", "Température du blanc", enum=list(TEMPERATURES)),
        "transition_secondes": p("number", "Durée du fondu en secondes")}, requis=["cible"])
def hue_regler(cible: str, allumer: bool = True, luminosite: int | None = None, couleur: str = "",
               blanc: str = "", transition_secondes: float | None = None) -> str:
    etat: dict = {"on": bool(allumer)}
    if allumer:
        if luminosite is not None:
            etat["bri"] = max(1, min(254, round(luminosite / 100 * 254)))
        if couleur:
            etat["xy"] = couleur_xy(couleur)
        elif blanc:
            etat["ct"] = max(153, min(500, round(1_000_000 / TEMPERATURES[blanc])))
    if transition_secondes is not None:
        etat["transitiontime"] = max(0, round(transition_secondes * 10))
    faits = []
    for type_, ident, nom in cibles(cible):
        hue("PUT", f"/{type_}/{ident}/{'action' if type_ == 'groups' else 'state'}", etat)
        faits.append(nom)
    if not allumer:
        return f"{', '.join(faits)} éteint."
    details = [f"{luminosite} %" if luminosite is not None else "", couleur, f"blanc {blanc}" if blanc else ""]
    return f"{', '.join(faits)} allumé" + (" (" + ", ".join(d for d in details if d) + ")" if any(details) else "") + "."


@outil("hue_scene", "Active une scène / ambiance Hue (ex. Lecture, Détente, Concentration, ou une scène créée dans "
       "l'application Hue).", "DOMOTIQUE",
       {"scene": p("string", "Nom de la scène"), "piece": p("string", "Pièce (si la scène existe dans plusieurs)")},
       requis=["scene"])
def hue_scene(scene: str, piece: str = "") -> str:
    scenes = hue("GET", "/scenes") or {}
    groupes = hue("GET", "/groups") or {}
    n, pc = scene.strip().lower(), piece.strip().lower()
    candidates = [(sid, s) for sid, s in scenes.items() if n == s.get("name", "").lower()] or \
                 [(sid, s) for sid, s in scenes.items() if n in s.get("name", "").lower()]
    if pc:
        candidates = [(sid, s) for sid, s in candidates
                      if pc in groupes.get(s.get("group", ""), {}).get("name", "").lower()] or candidates
    if not candidates:
        noms = sorted({s.get("name", "") for s in scenes.values()})
        raise ErreurOutil(f"Pas de scène « {scene} ». Scènes : {', '.join(noms[:30])}.")
    sid, s = candidates[0]
    gid = s.get("group") or "0"
    hue("PUT", f"/groups/{gid}/action", {"scene": sid})
    return f"Scène {s.get('name')} activée" + (f" ({groupes.get(gid, {}).get('name')})" if gid in groupes else "") + "."


@outil("hue_appairer", "Relie Jarvis au pont Hue (une seule fois) : l'utilisateur doit avoir appuyé sur le bouton du "
       "pont dans les 30 dernières secondes.", "DOMOTIQUE",
       {"adresse": p("string", "Adresse IP du pont (facultatif : trouvée automatiquement)")})
def hue_appairer(adresse: str = "") -> str:
    pont = adresse or S.cfg.get("hue.bridge", "")
    if not pont:
        trouves = reseau.get("https://discovery.meethue.com/", "la recherche de pont Hue") or []
        if not trouves:
            raise ErreurOutil("Aucun pont Hue trouvé sur le réseau. Donne-moi son adresse IP (application Hue, "
                              "Paramètres, Ponts Hue).")
        pont = trouves[0]["internalipaddress"]
    r = reseau.post(f"http://{pont}/api", "le pont Hue", json={"devicetype": "jarvis#pc"})
    if isinstance(r, list) and r and "success" in r[0]:
        S.cfg.set("hue.bridge", pont)
        S.cfg.set("hue.utilisateur", r[0]["success"]["username"])
        return f"Pont Hue {pont} relié. Les lumières sont prêtes."
    if isinstance(r, list) and r and "error" in r[0] and r[0]["error"].get("type") == 101:
        S.cfg.set("hue.bridge", pont)
        raise ErreurOutil("Appuie sur le gros bouton rond du pont Hue, puis redemande-moi tout de suite.")
    raise ErreurOutil(f"Réponse inattendue du pont Hue : {r}")
