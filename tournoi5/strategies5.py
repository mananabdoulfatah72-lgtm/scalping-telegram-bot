"""Strategies du tournoi n°5 (README.md) : autres marches et leurs rendez-vous."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ICI = Path(__file__).resolve().parent
R = ICI.parent
sys.path.insert(0, str(R / "tournoi"))
import importlib.util  # noqa: E402

import concurrents as K1  # noqa: E402  (entree_fixe, precedente, de_la, melanger_perm, ordre_hasard)

_spec = importlib.util.spec_from_file_location("zone_multi_analyse", R / "zone_multi" / "analyse.py")   # nom deja pris par fonds/
ZM = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ZM)             # charger : minutes RTY YM GC CL 6E

NAN = np.nan
DONNEES = ICI / "donnees"
FRAIS_MICRO = 1.0                      # $ par ordre (micro-contrats, comme zone_multi)
FRAIS_STANDARD = 2.5                   # $ par ordre (devises standard, ZN)
# marche : (fichier, $ par point du micro, tick, debut et fin de seance en minutes depuis minuit, New York)
MINUTES = {"RTY": ZM.MARCHES["RTY"], "YM": ZM.MARCHES["YM"], "GC": ZM.MARCHES["GC"], "CL": ZM.MARCHES["CL"], "6E": ZM.MARCHES["6E"],
           "BTC": (DONNEES / "bitcoin_1min.csv.gz", 0.1, 5.0, 540, 990)}
# devise : (taille du contrat standard en devise, valeur du tick en $)
DEVISES = {"6E": (125_000, 6.25), "6B": (62_500, 6.25), "6J": (12_500_000, 6.25), "6A": (100_000, 5.0), "6C": (100_000, 5.0),
           "6S": (125_000, 6.25)}
ZN = (1000.0, 1 / 64)                  # $ par point, tick


def cout_micro(marche):
    _, pt, tick, _, _ = MINUTES[marche]
    return 2 * (FRAIS_MICRO + tick * pt) / pt                     # points par aller-retour


def charger_minutes(marche):
    fichier, pt, tick, m0, m1 = MINUTES[marche]
    J, O, H, L, C, P, V, ech = ZM.charger(fichier, m0, m1)
    n = m1 - m0
    complete = P[:, 0] & P[:, n - 1] & (P.sum(axis=1) >= n - 20)
    if marche == "BTC":                                           # seance de reference : 9 h 30 - 16 h
        complete = P[:, 30] & P[:, 419] & (P[:, 30:420].sum(axis=1) >= 370)
    contrat = np.cumsum(ech)                                      # meme numero = meme contrat
    return J, O, H, L, C, P, V, ech, complete, contrat


def fin_de_seance(O, H, L, C, complete, ech, contrat, cout):
    """B : 30 min avant la fin, dans le sens du mouvement depuis la cloture de la seance precedente (meme contrat)."""
    n = O.shape[1]
    ok = complete & ~ech
    prec = K1.precedente(complete, contrat)
    pc = K1.de_la(C[:, n - 1], prec)
    s = np.sign(np.nan_to_num(C[:, n - 31] / pc - 1)).astype(np.int64)
    rien = np.full(len(O), NAN)
    return K1.entree_fixe(O, H, L, C, ok, cout, s, n - 30, rien, rien, n - 1), ok


def rapport_eia(J, O, H, L, C, complete, ech, cout):
    """C (CL, seance de 9 h) : le mercredi, a 14 h, dans le sens de 10 h 30 - 11 h, jusqu'a 14 h 30."""
    ok = complete & ~ech
    mer = pd.DatetimeIndex(J).weekday.values == 2
    s = np.where(mer, np.sign(C[:, 119] / C[:, 89] - 1), 0).astype(np.int64)
    rien = np.full(len(O), NAN)
    return K1.entree_fixe(O, H, L, C, ok, cout, s, 300, rien, rien, 329), ok


def bitcoin(O, H, L, C, complete, ech, cout):
    """D (seance chargee de 9 h a 16 h 30) : a 15 h 30, dans le sens de 9 h 30 - 10 h, jusqu'a 16 h."""
    ok = complete & ~ech
    s = np.sign(C[:, 59] / O[:, 30] - 1).astype(np.int64)
    rien = np.full(len(O), NAN)
    return K1.entree_fixe(O, H, L, C, ok, cout, s, 390, rien, rien, 419), ok


def melanger_sans_volume(O, H, L, C, rng, tick):
    """Bruit : minutes de chaque seance remises au hasard (la 1re en place), prix au tick ; volume non utilise."""
    perm = K1.ordre_hasard(O.shape[0], rng, O.shape[1])
    return K1.melanger_perm(O, H, L, C, np.zeros_like(O), perm, tick=tick)[:4]


# ---------------------------------------------------------------- barres d'une heure : devises et ZN

def lire_heures(nom):
    h = pd.read_csv(DONNEES / f"{nom}_1h.csv.gz")
    h["t"] = pd.to_datetime(h["t"])
    return h


def heure_fixing(jours):
    """Heure de New York (0-23) du fixing de 16 h a Londres, pour chaque date."""
    j = pd.DatetimeIndex(jours)
    londres = (j + pd.Timedelta(hours=16)).tz_localize("Europe/London")
    return londres.tz_convert("America/New_York").hour.values


def barre(h, heure):
    """Par date : ouverture, cloture et contrat de la barre qui commence a l'heure donnee (tableau d'heures par date)."""
    j = h["t"].dt.normalize()
    cle = pd.MultiIndex.from_arrays([j, h["t"].dt.hour])
    return h.set_index(cle)[["o", "c", "contrat"]]


def trade_heure(heures, jours, heure_par_jour, sens):
    """Rendement net moyen du panier par date : sens (+1 achat du panier, -1 vente) pendant la barre qui commence a
    heure_par_jour. Frais du contrat standard (1 tick + 2,50 $ par ordre) rapportes au montant du contrat."""
    J = pd.DatetimeIndex(jours)
    rend = np.zeros((len(J), len(heures)))
    present = np.zeros((len(J), len(heures)), bool)
    for k, (nom, h) in enumerate(heures.items()):
        taille, tick_d = DEVISES[nom]
        b = barre(h, None)
        cle = pd.MultiIndex.from_arrays([J, heure_par_jour])
        x = b[~b.index.duplicated(keep="last")].reindex(cle)
        o, c = x["o"].values, x["c"].values
        frais = 2 * (FRAIS_STANDARD + tick_d) / (taille * o)
        r = sens * (c / o - 1) - frais
        present[:, k] = np.isfinite(r)
        rend[:, k] = np.nan_to_num(r)
    n = present.sum(axis=1)
    return np.where(n >= 4, rend.sum(axis=1) / np.maximum(n, 1), 0.0), n >= 4


def jours_ouvres(heures, debut="2010-07-01"):
    j = sorted(set().union(*[set(h["t"].dt.normalize()) for h in heures.values()]))
    j = pd.DatetimeIndex([x for x in j if x.weekday() < 5 and x >= pd.Timestamp(debut)])
    return j


def adjudications():
    a = pd.read_csv(DONNEES / "adjudications.csv")
    a = a[a["security_type"].isin(["Note", "Bond"]) & a["closing_time_comp"].astype(str).str.contains("01:00")]
    return pd.DatetimeIndex(pd.to_datetime(a["auction_date"]).unique())


def zn_trade(h, jours, h0, h1, sens):
    """ZN : sens de l'ouverture de la barre de h0 a la cloture de la barre de h1 - 1, meme contrat ; rendement net."""
    pt, tick = ZN
    b = barre(h, None)
    b = b[~b.index.duplicated(keep="last")]
    J = pd.DatetimeIndex(jours)
    deb = b.reindex(pd.MultiIndex.from_arrays([J, np.full(len(J), h0)]))
    fin = b.reindex(pd.MultiIndex.from_arrays([J, np.full(len(J), h1 - 1)]))
    ok = np.isfinite(deb["o"].values) & np.isfinite(fin["c"].values) & (deb["contrat"].values == fin["contrat"].values)
    o, c = deb["o"].values, fin["c"].values
    r = sens * (c / o - 1) - 2 * (FRAIS_STANDARD / pt + tick) / o
    return np.where(ok, r, 0.0), ok
