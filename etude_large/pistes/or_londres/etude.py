#!/usr/bin/env python3
"""etude_large/pistes/README.md, piste 4 (regles fixees le 22 octobre 2026, commit a6e791f, avant tout calcul) :
cassures de l'ouverture de Londres sur l'or (MGC) et l'argent (SIL), F3-30 et F4-16:30, code de la machine 5 inchange
(kb/sessions24/machine5.py : Marche, strategies, jouer, cassures, par_jour, t_stat, placebo).

F3-30 : fourchette des barres de 8 h 00 a 8 h 30 (Londres), premiere cloture de 5 min au-dela de 8 h 30 a 16 h 30,
        entree a l'ouverture de la barre suivante, stop a l'autre extreme, sinon sortie a l'ouverture de 16 h 30.
F4-16:30 : fourchette de 0 h 00 a 7 h 00 (Londres), cassure de 7 h 00 a 12 h 00, meme entree et meme stop, sortie a
        l'ouverture de 16 h 30.
4 tests : F3-30 or, F4-16:30 or, F3-30 argent, F4-16:30 argent.
Frais principaux : 0,96 pb (MGC) et 2,1 pb (SIL) ; sensibilite 2 pb et 3 pb ; information et critere 5 au coffre :
4 $ (MGC, 10 onces) et 12 $ (SIL, 1 000 onces) par aller-retour au prix d'entree du jour.

Briques reutilisees sans changement : machine5.py (ci-dessus), delta_mesures/etude.py (RECHERCHE, ROBOT, FIN, via
partie_a.zone_bot et partie_d.chemins_zone), etude_large/partie_a.py (zone_bot, t_stat, sharpe, p_unilateral),
etude_large/partie_d.py (chemins_zone, tous_les_departs, limites_depart, FIRMES), kb/fonds/fomc.py (par ces briques).

Choix d'interpretation fixes AVANT tout calcul (repris dans resultats.txt) :
- t net = convention de la machine 5 (t_stat de par_jour : jours avec un trade), celle des chiffres publies du
  controle a) ; le t avec 0 les jours de semaine sans trade est publie pour information ;
- frais de sensibilite exiges sur l'exploration ET le coffre ; frais fixes en dollars exiges sur le coffre ;
- placebo : 1 000 tirages du sens (machine5.placebo, graine 5), argent sur l'exploration, or sur le coffre ;
- critere 6 (partie C) : rendements quotidiens, zone = partie_a.zone_bot (points / ouverture, sans les jours de la Fed),
  calendrier = toutes les seances des minutes du NQ + les jours de trade du metal (0 sans trade), correlation et poids a
  risque egal sur 2016 - 2022, Sharpe sur le coffre de l'or (2023 -> 2 octobre 2026) ;
- critere 7 : moteur de la partie D (Lucid Flex 50K), departs 2023 -> fin du coffre de l'or, 1 MNQ + 1 MGC contre
  1 MNQ seul sur le meme calendrier (seances jouables de la zone + jours de trade du MGC), gains au prix
  d'aujourd'hui (zone : chemins_zone ; MGC : 10 onces x 4 146 $, frais 0,96 pb a l'entree) ; chaque barre de 5 min
  du MGC donne son plus bas et son plus haut a chacune de ses minutes (prudent pour le plancher) ;
- criteres 3, 6 et 7 portent sur la regle (or ET argent ; MGC pour 6 et 7) : un test n'a ses criteres propres que si
  sa regle les passe sur les deux metaux ;
- F4-16:30 : machine5.cassures cherche la cassure jusqu'a la sortie de 16 h 30 (et non jusqu'a 12 h 00 comme le dit le
  texte du README) ; le code inchange est garde, puisque le README l'exige et que le controle a) porte sur ses chiffres.

Lancer : export KB=<branche de recherche extraite> ; python3 etude_large/pistes/or_londres/etude.py
Ecrit resultats.txt dans ce dossier."""
import os
import sys
import tempfile

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", os.path.join(tempfile.gettempdir(), "numba_or_londres"))

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ICI = Path(__file__).resolve().parent
LARGE = ICI.parent.parent
RACINE = LARGE.parent
if str(ICI) in sys.path:
    sys.path.remove(str(ICI))            # ce fichier s'appelle aussi etude.py : jamais importe a la place de DM
sys.path.insert(0, str(RACINE / "delta_mesures"))
import etude as DM  # noqa: E402
sys.path.insert(0, str(LARGE))
import partie_a as PA  # noqa: E402
import partie_d as PD  # noqa: E402
KB = DM.KB
sys.path.insert(0, str(KB / "sessions24"))
import machine5 as M5  # noqa: E402

LONDRES, NY = M5.LONDRES, M5.NY
ARGENT = RACINE / "donnees_libres" / "histdata_5min"
YAHOO = RACINE / "donnees_libres" / "yahoo"
EXPLO = ("2012-01-01", "2022-12-31")
COFFRE = {"or": ("2023-01-01", "2026-10-02"), "argent": ("2023-01-01", "2026-10-16")}
FRAIS = {"or": 0.96, "argent": 2.1}                 # pb, frais principaux (README)
SENSIB = {"or": 2.0, "argent": 3.0}                 # pb, sensibilite
DOLLAR_ONCE = {"or": 4.0 / 10, "argent": 12.0 / 1000}   # frais fixes en $ par once (points de prix) : 4 $ / 10 oz, 12 $ / 1 000 oz
ONCES = {"or": 10.0, "argent": 1000.0}
PRIX_AUJ = {"or": ("GC", 4146.0), "argent": ("SI", 57.86)}  # clotures Yahoo du 21 octobre 2026 (README)
REGLES = {"F3": "F3 cassure Londres 30 min xauusd", "F4": "F4 Asie -> Londres sortie 16:30 xauusd"}
NOMS = {"F3": "F3-30", "F4": "F4-16:30"}
PUBLIE = {"F3": (2.84, 3.14, 0.92), "F4": (3.20, 2.82, 1.06)}   # avant frais (pb, t) et t a 2 pb (sessions24/README.md)
SOUS = [(2012, 2015), (2016, 2019), (2020, 2022)]
ANNEES_COFFRE = (2023, 2024, 2025, 2026)
YAHOO_DEBUT, YAHOO_FIN = "2024-05-30", "2026-10-21"
LUCID = "Lucid Flex 50K"
AVANT = 114                                         # pas de 5 min de 0 h 00 a 9 h 25 (New York) avant la zone
SEUIL_CORR_B = 0.95


# ----------------------------------------------------------------------------- donnees et trades (machine 5)
def charger():
    mo = M5.Marche("xauusd")                                         # kb/sessions24/annees/
    fichiers = sorted(ARGENT.glob("xagusd_*_5m.csv.gz"))
    d = pd.concat([pd.read_csv(x) for x in fichiers]).drop_duplicates("t", keep="last").sort_values("t")
    ma = M5.Marche("xagusd", d)                                      # meme lecture que Marche() pour un dossier annees
    return {"or": mo, "argent": ma}


def regle(k):
    s = {x["nom"]: x for x in M5.strategies()}[REGLES[k]]
    return dict(s)


def trades(s, M, debut, fin, frais, unite="pb"):
    """machine5.jouer avec les frais demandes (frais en pb, ou en points de prix si unite = 'pt')."""
    M.frais, M.unite = frais, unite
    return M5.jouer(s, M, debut, fin)


def stats(d):
    j = M5.par_jour(d)
    return dict(t=float(M5.t_stat(j)), n=int(len(j)), moy=float(j.mean() * 1e4) if len(j) else 0.0,
                somme=float(j.sum() * 1e4))


def t_zero(d, debut, fin):
    """t avec 0 les jours de semaine (Londres) sans trade (information)."""
    j = M5.par_jour(d)
    cal = M5.jours_locaux(LONDRES, debut, fin)
    return float(M5.t_stat(j.reindex(cal).fillna(0.0)))


def net_de(brut_d, M, frais, unite="pb"):
    """Rendements nets d'un tableau de trades avant frais, avec d'autres frais (meme formule que Marche.cout)."""
    M.frais, M.unite = frais, unite
    c = np.array([M.cout(e) for e in brut_d["e"].to_numpy()])
    x = brut_d.copy()
    x["r"] = brut_d["r"].to_numpy() - c
    return x


def bornes(s, M, debut, fin):
    """Memes bornes que machine5.jouer (genres cassure et asie)."""
    if s["genre"] == "cassure":
        fz, h0, h1 = M5.SESSIONS[s["session"]]
        j = M5.jours_locaux(fz, debut, fin)
        a = M.indice(M5.heure_utc(j, fz, h0))
        b = np.where(a >= 0, a + s["r"] // 5, -1)
        f = M.indice(M5.heure_utc(j, fz, h1))
        nb = s["r"] // 5 - 1
    else:
        j = M5.jours_locaux(LONDRES, debut, fin)
        a = M.indice(M5.heure_utc(j, LONDRES, "00:00"))
        b = M.indice(M5.heure_utc(j, LONDRES, "07:00"))
        f = M.indice(M5.heure_utc(j, LONDRES, s["sortie"]))
        nb = 60
    return j, a, b, f, nb


def detail(s, M, debut, fin, d_brut):
    """Trades detailles (barre d'entree et de sortie) : machine5.cassures, plus la barre d'entree retrouvee par la meme
    regle ; verifie l'identite avec machine5.jouer et l'absence de regard vers le futur."""
    j, a, b, f, nb = bornes(s, M, debut, fin)
    sens, pe, ps, bs = M5.cassures(M.O, M.H, M.L, M.C, a, b, f, nb)
    ok = np.where(sens != 0)[0]
    lignes = []
    for k in ok:
        hh, ll = np.nanmax(M.H[a[k]:b[k]]), np.nanmin(M.L[a[k]:b[k]])
        ie = sg = -1
        for i in range(b[k], f[k]):
            if i + 1 >= f[k] or not np.isfinite(M.C[i]):
                continue
            if M.C[i] > hh and np.isfinite(M.O[i + 1]):
                ie, sg = i + 1, 1
                break
            if M.C[i] < ll and np.isfinite(M.O[i + 1]):
                ie, sg = i + 1, -1
                break
        # regard vers le futur : fourchette [a, b) finie avant le signal (barre ie - 1 >= b), entree a l'ouverture
        # de la barre suivante, sortie a la barre de l'entree ou apres, au plus tard 12 barres apres 16 h 30
        assert sg == sens[k] and M.O[ie] == pe[k] and ie - 1 >= b[k] and bs[k] >= ie and bs[k] <= f[k] + 12
        lignes.append(dict(date=j[k], sens=int(sens[k]), pe=float(pe[k]), ps=float(ps[k]), ie=int(ie),
                           bs=int(bs[k]), stop=bool(bs[k] < f[k]), signal=int(ie - 1)))
    x = pd.DataFrame(lignes)
    r = x["sens"] * (x["ps"] / x["pe"] - 1)
    assert len(x) == len(d_brut) and np.allclose(r.to_numpy(), d_brut["r"].to_numpy(), atol=1e-15)
    jt = M5.jour_de_trading(pd.DatetimeIndex(M.t0 + x["bs"].to_numpy() * M5.PAS))
    assert (pd.DatetimeIndex(jt) == pd.DatetimeIndex(x["date"])).all()      # jour de trading = jour de Londres
    return x


# ----------------------------------------------------------------------------- controles
def controle_b(M):
    """Correlation des rendements de 3 h a 11 h (New York) : HistData contre les barres d'une heure de Yahoo."""
    out = {}
    jours = M5.jours_locaux(NY, YAHOO_DEBUT, YAHOO_FIN)
    for metal, codes in (("or", ("GC", "MGC")), ("argent", ("SI",))):
        m = M[metal]
        i3, i11 = m.indice(M5.heure_utc(jours, NY, "03:00")), m.indice(M5.heure_utc(jours, NY, "11:00"))
        o3 = np.where(i3 >= 0, m.O[np.clip(i3, 0, m.n - 1)], np.nan)
        o11 = np.where(i11 >= 0, m.O[np.clip(i11, 0, m.n - 1)], np.nan)
        rh = pd.Series(o11 / o3 - 1, index=jours)
        for c in codes:
            y = pd.read_csv(YAHOO / "heure" / f"{c}.csv.gz")
            y["t"] = pd.to_datetime(y["t"])
            o = y.set_index("t")["o"]
            a3 = o.reindex(jours + pd.Timedelta(hours=3)).to_numpy()
            a11 = o.reindex(jours + pd.Timedelta(hours=11)).to_numpy()
            ry = pd.Series(a11 / a3 - 1, index=jours)
            ok = rh.notna() & ry.notna() & np.isfinite(rh) & np.isfinite(ry)
            out[(metal, c)] = (float(np.corrcoef(rh[ok], ry[ok])[0, 1]), int(ok.sum()), rh[ok].index[0].date(),
                               rh[ok].index[-1].date())
    return out


def controle_c(M):
    """Barres presentes par annee (fenetre 0 h 00 - 16 h 30, Londres) et verification du changement d'heure."""
    L = []
    for metal, m in M.items():
        L.append(f"  {metal} : annee | jours de semaine | jours avec des barres | barres presentes 0 h - 16 h 30 (Londres)"
                 " sur les jours avec barres")
        for an in range(2012, 2027):
            fin = COFFRE[metal][1] if an == 2026 else f"{an}-12-31"
            j = M5.jours_locaux(LONDRES, f"{an}-01-01", fin)
            a = m.indice(M5.heure_utc(j, LONDRES, "00:00"))
            pres = np.array([np.isfinite(m.C[k:k + 198]).sum() if k >= 0 else 0 for k in a])
            avec = pres > 0
            L.append(f"    {an} : {len(j):4d} | {int(avec.sum()):4d} | {pres[avec].mean() / 198 * 100:5.1f} %"
                     f" ({int((198 - pres[avec]).sum()):6d} barres manquantes)")
    # changement d'heure : conversion des heures de Londres
    ex = [("2024-01-15", "08:00"), ("2024-07-15", "08:00"), ("2024-03-12", "08:00"), ("2024-10-29", "16:30")]
    conv = []
    for dte, h in ex:
        u = M5.heure_utc(pd.DatetimeIndex([dte]), LONDRES, h)[0]
        conv.append(f"{dte} {h} Londres = {u.strftime('%H:%M')} UTC = {u.tz_convert(NY).strftime('%H:%M')} New York")
    L.append("  conversion : " + " ; ".join(conv))
    attendu = ["08:00", "07:00", "08:00", "16:30"]
    ok_conv = all(c.split(" = ")[1][:5] == e for c, e in zip(conv, attendu))
    # empirique : le pic des chiffres americains de 8 h 30 (New York) tombe a 13 h 30 a Londres, sauf les semaines ou
    # les deux pays n'ont pas encore change d'heure ensemble (12 h 30 a Londres)
    ok_emp = True
    for metal, m in M.items():
        j = M5.jours_locaux(LONDRES, "2012-01-01", COFFRE[metal][1])
        midi_l = M5.heure_utc(j, LONDRES, "12:00")
        midi_ny = M5.heure_utc(j, NY, "07:00")                       # 12 h a Londres = 7 h a New York (5 h d'ecart)
        decale = np.asarray(midi_l != midi_ny)                       # semaines a 4 h d'ecart
        res = {}
        for h in ("12:30", "13:30"):
            i = m.indice(M5.heure_utc(j, LONDRES, h))
            r = np.where(i >= 0, np.abs(m.C[np.clip(i, 0, m.n - 1)] / m.O[np.clip(i, 0, m.n - 1)] - 1), np.nan) * 1e4
            res[h] = (np.nanmean(r[~decale]), np.nanmean(r[decale]))
        i = m.indice(M5.heure_utc(j, LONDRES, "12:00"))
        base = np.nanmean(np.abs(m.C[np.clip(i, 0, m.n - 1)] / m.O[np.clip(i, 0, m.n - 1)] - 1)) * 1e4
        bon = res["13:30"][0] > res["12:30"][0] and res["12:30"][1] > res["13:30"][1]
        ok_emp &= bon
        L.append(f"  {metal} : |rendement| moyen de la barre de 5 min (pb) ; semaines normales ({int((~decale).sum())} j) :"
                 f" 12 h 30 {res['12:30'][0]:.2f}, 13 h 30 {res['13:30'][0]:.2f} ; semaines decalees ({int(decale.sum())} j) :"
                 f" 12 h 30 {res['12:30'][1]:.2f}, 13 h 30 {res['13:30'][1]:.2f} ; repere 12 h 00 {base:.2f}"
                 f" -> pic de 8 h 30 (New York) a sa place : {'oui' if bon else 'NON'}")
    return L, ok_conv and ok_emp


# ----------------------------------------------------------------------------- chemins du MGC pour le challenge
def chemins_metal(x, M, V, frais_pb):
    """Par jour de trade : gain cumule en $ (1 contrat de V $ au prix d'aujourd'hui) sur AVANT pas de 5 min (0 h 00 -
    9 h 25, New York) puis 390 minutes (9 h 30 - 15 h 59) ; cloture, plus bas, plus haut de chaque pas. Frais a
    l'entree. Une minute de 9 h 30 a 15 h 59 recoit le plus bas et le plus haut de sa barre de 5 min."""
    off = np.r_[np.arange(AVANT), (570 + np.arange(DM.N)) // 5]
    Cf = pd.Series(M.C).ffill().to_numpy()
    Hf = np.where(np.isfinite(M.H), M.H, Cf)
    Lf = np.where(np.isfinite(M.L), M.L, Cf)
    fee = frais_pb * 1e-4 * V
    jours, clo, bas, haut = [], [], [], []
    for t in x.itertuples():
        minuit = pd.Timestamp(t.date).tz_localize(NY).tz_convert("UTC")
        i0 = int((minuit - M.t0) / M5.PAS)
        g = i0 + off
        assert t.ie >= i0 and t.bs <= g[-1]
        s, pe = t.sens, t.pe

        def val(p):
            return s * (p / pe - 1) * V - fee
        dedans, a_bs, apres = (g >= t.ie) & (g < t.bs), g == t.bs, g > t.bs
        vo, reel = val(M.O[t.bs]), val(t.ps)
        c = np.where(dedans, val(Cf[g]), 0.0)
        lo = np.where(dedans, val(Lf[g]) if s > 0 else val(Hf[g]), 0.0)
        hi = np.where(dedans, val(Hf[g]) if s > 0 else val(Lf[g]), 0.0)
        c = np.where(a_bs | apres, reel, c)
        lo = np.where(a_bs, min(vo, reel), np.where(apres, reel, lo))
        hi = np.where(a_bs, max(vo, reel), np.where(apres, reel, hi))
        jours.append(pd.Timestamp(t.date))
        clo.append(c)
        bas.append(lo)
        haut.append(hi)
    return pd.DatetimeIndex(jours), np.array(clo), np.array(bas), np.array(haut)


def lucid(cal, zone, metal, departs_debut, q=1.0):
    """Parts validees / perdues chez Lucid Flex 50K (moteur de la partie D) pour des chemins quotidiens donnes."""
    obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[LUCID]
    clo, bas, haut = (zone[i] + metal[i] for i in range(3))
    dep = np.where(cal >= pd.Timestamp(departs_debut[0]))[0]
    if departs_debut[1] is not None:
        dep = dep[cal[dep] <= pd.Timestamp(departs_debut[1])]
    lim = PD.limites_depart(cal, dep, nmax)
    ok = dep + lim < len(cal)
    dep, lim = dep[ok], lim[ok]
    iss, nb = PD.tous_les_departs(clo, bas, haut, dep, lim, q, q, 0, float(obj), float(dd), float(bloc), float(dll),
                                  part, True)
    return (iss == 1).mean() * 100, (iss == -1).mean() * 100, (iss == 0).mean() * 100, len(dep)


# ----------------------------------------------------------------------------- principal
def main():
    L = ["Piste 4 (etude_large/pistes/README.md, regles fixees le 22 octobre 2026, commit a6e791f) : cassures de "
         "l'ouverture de Londres sur l'or et l'argent, F3-30 et F4-16:30.",
         "Code de la machine 5 inchange (kb/sessions24/machine5.py). Barres HistData de 5 min (UTC -> Europe/London), "
         "jours de semaine. Rendements en points de base (pb) du prix ; t = t de la machine 5 (jours avec un trade).",
         f"Frais principaux : or {FRAIS['or']} pb (MGC), argent {FRAIS['argent']} pb (SIL) ; sensibilite "
         f"{SENSIB['or']} / {SENSIB['argent']} pb ; fixes : 4 $ (MGC) et 12 $ (SIL) au prix d'entree du jour.", ""]
    M = charger()
    S = {k: regle(k) for k in REGLES}

    # ------------------------------------------------------------- controle a (avant le coffre)
    L.append("CONTROLE a) l'or en exploration 2012 - 2022 doit redonner les chiffres publies (sessions24/README.md)")
    ok_a = True
    for k in REGLES:
        d0 = trades(S[k], M["or"], *EXPLO, 0.0)
        d2 = trades(S[k], M["or"], *EXPLO, 2.0)
        s0, s2 = stats(d0), stats(d2)
        p = PUBLIE[k]
        bon = abs(s0["moy"] - p[0]) < 0.006 and abs(s0["t"] - p[1]) < 0.006 and abs(s2["t"] - p[2]) < 0.006
        ok_a &= bon
        L.append(f"  {NOMS[k]} or : avant frais {s0['moy']:+.2f} pb par jour, t {s0['t']:+.2f} ; a 2 pb t {s2['t']:+.2f}"
                 f" ({s0['n']} jours) ; publie {p[0]:+.2f} pb, t {p[1]:+.2f}, t {p[2]:+.2f} a 2 pb -> "
                 f"{'identique' if bon else 'ECART'}")
    # ------------------------------------------------------------- controle b
    L.append(f"CONTROLE b) correlation des rendements de 3 h a 11 h (New York), HistData contre Yahoo une heure "
             f"({YAHOO_DEBUT} -> {YAHOO_FIN}), seuil {SEUIL_CORR_B}")
    cb = controle_b(M)
    ok_b = True
    for (metal, c), (r, n, d1, d2) in cb.items():
        decide = c in ("GC", "SI")
        if decide:
            ok_b &= r >= SEUIL_CORR_B
        L.append(f"  {metal} HistData / {c} Yahoo : {r:.3f} sur {n} jours ({d1} -> {d2})"
                 f"{' -> ' + ('passe' if r >= SEUIL_CORR_B else 'ECHEC') if decide else ' (information)'}")
    if not (ok_a and ok_b):
        L.append("ARRET : controle a) ou b) en echec, le coffre n'est pas ouvert.")
        (ICI / "resultats.txt").write_text("\n".join(L) + "\n")
        print("\n".join(L))
        sys.exit(1)
    # ------------------------------------------------------------- controle c
    L.append("CONTROLE c) barres manquantes par annee et changement d'heure a Londres")
    lc, ok_c = controle_c(M)
    L += lc
    L.append(f"  -> changement d'heure : {'verifie' if ok_c else 'ECHEC'}")
    L.append("")

    # ------------------------------------------------------------- exploration
    R = {}
    for metal in ("or", "argent"):
        m = M[metal]
        for k in REGLES:
            b = trades(S[k], m, *EXPLO, 0.0)
            net = net_de(b, m, FRAIS[metal])
            R[(metal, k)] = dict(brut_e=b, net_e=net, st_e=stats(net), b_e=stats(b), tz_e=t_zero(net, *EXPLO),
                                 sens_e=stats(net_de(b, m, SENSIB[metal])),
                                 dol_e=stats(net_de(b, m, DOLLAR_ONCE[metal], "pt")),
                                 det_e=detail(S[k], m, *EXPLO, b))
    L.append("EXPLORATION 2012 - 2022 (or : deja vue avant frais, rejugee aux nouveaux frais ; argent : jamais testee)")
    L.append("  test              jours  avant frais (pb, t)   net (pb, t)      t net (0 sans trade)  t sensibilite  "
             "t frais fixes $  p unilateral")
    for (metal, k), r in R.items():
        b, n = r["b_e"], r["st_e"]
        r["p"] = PA.p_unilateral(n["t"])
        L.append(f"  {NOMS[k]:8} {metal:7} {n['n']:5d}   {b['moy']:+6.2f} ({b['t']:+.2f})      {n['moy']:+6.2f} ({n['t']:+.2f})"
                 f"   {r['tz_e']:+6.2f}                {r['sens_e']['t']:+6.2f}          {r['dol_e']['t']:+6.2f}"
                 f"         {r['p']:.4f}")
    # placebo de l'argent en exploration (et de l'or, information)
    L.append("  placebo (1 000 tirages du sens, memes heures, machine5.placebo, frais principaux) :")
    for (metal, k), r in R.items():
        m = M[metal]
        m.frais, m.unite = FRAIS[metal], "pb"
        p, n = M5.placebo(S[k], m, r["net_e"])
        r["plac_e"] = p
        L.append(f"    {NOMS[k]} {metal} : part des placebos au moins aussi bons {p * 100:.1f} % ({n})"
                 f"{' (critere 4)' if metal == 'argent' else ' (information : l or est juge au coffre)'}")
    # controle d : sous-periodes
    L.append("CONTROLE d) par sous-periode (pb par jour avant frais / net aux frais principaux, t net, jours)")
    for (metal, k), r in R.items():
        b = M5.par_jour(r["brut_e"])
        nt = M5.par_jour(r["net_e"])
        cases = []
        for a1, a2 in SOUS:
            mk = (b.index.year >= a1) & (b.index.year <= a2)
            cases.append(f"{a1}-{a2 % 100:02d} {b[mk].mean() * 1e4:+.2f} / {nt[mk].mean() * 1e4:+.2f} "
                         f"(t {M5.t_stat(nt[mk]):+.2f}, {int(mk.sum())} j)")
        L.append(f"  {NOMS[k]} {metal} : " + " ; ".join(cases))
    L.append("  achats et ventes (exploration, net pb par trade) : " + " ; ".join(
        f"{NOMS[k]} {metal} achats {r['net_e'][r['det_e']['sens'].to_numpy() > 0]['r'].mean() * 1e4:+.2f}, ventes "
        f"{r['net_e'][r['det_e']['sens'].to_numpy() < 0]['r'].mean() * 1e4:+.2f}" for (metal, k), r in R.items()))
    L.append("  part des trades sortis au stop (exploration) : " + " ; ".join(
        f"{NOMS[k]} {metal} {r['det_e']['stop'].mean() * 100:.0f} %" for (metal, k), r in R.items()))
    L.append("")
    if len(sys.argv) > 1 and sys.argv[1] == "exploration":
        print("\n".join(L))
        return

    # ------------------------------------------------------------- coffre (ouvert une seule fois)
    for metal in ("or", "argent"):
        m = M[metal]
        for k in REGLES:
            r = R[(metal, k)]
            b = trades(S[k], m, *COFFRE[metal], 0.0)
            net = net_de(b, m, FRAIS[metal])
            r.update(brut_c=b, net_c=net, st_c=stats(net), b_c=stats(b), tz_c=t_zero(net, *COFFRE[metal]),
                     sens_c=stats(net_de(b, m, SENSIB[metal])), dol_c=stats(net_de(b, m, DOLLAR_ONCE[metal], "pt")),
                     det_c=detail(S[k], m, *COFFRE[metal], b))
    L.append("COFFRE (ouvert une seule fois) : or 2023-01-01 -> 2026-10-02, argent 2023-01-01 -> 2026-10-16")
    L.append("  test              jours  avant frais (pb, t)   net (pb, t)      t net (0 sans trade)  t sensibilite  "
             "t frais fixes $  annees 2023/24/25/26 (pb nets)")
    for (metal, k), r in R.items():
        b, n = r["b_c"], r["st_c"]
        j = M5.par_jour(r["net_c"])
        ans = [float(j[j.index.year == y].sum() * 1e4) for y in ANNEES_COFFRE]
        r["ans"] = ans
        L.append(f"  {NOMS[k]:8} {metal:7} {n['n']:5d}   {b['moy']:+6.2f} ({b['t']:+.2f})      {n['moy']:+6.2f} ({n['t']:+.2f})"
                 f"   {r['tz_c']:+6.2f}                {r['sens_c']['t']:+6.2f}          {r['dol_c']['t']:+6.2f}"
                 f"         {' / '.join(f'{a:+.0f}' for a in ans)}")
    L.append("  placebo de l'or au coffre (critere 4) :")
    for (metal, k), r in R.items():
        if metal != "or":
            continue
        m = M[metal]
        m.frais, m.unite = FRAIS[metal], "pb"
        p, n = M5.placebo(S[k], m, r["net_c"])
        r["plac_c"] = p
        L.append(f"    {NOMS[k]} or : part des placebos au moins aussi bons {p * 100:.1f} % ({n})")
    L.append("  achats et ventes (coffre, net pb par trade) : " + " ; ".join(
        f"{NOMS[k]} {metal} achats {r['net_c'][r['det_c']['sens'].to_numpy() > 0]['r'].mean() * 1e4:+.2f}, ventes "
        f"{r['net_c'][r['det_c']['sens'].to_numpy() < 0]['r'].mean() * 1e4:+.2f}" for (metal, k), r in R.items()))
    # ecart de texte : le README decrit une cassure cherchee de 7 h a 12 h pour F4, mais machine5.cassures (code
    # inchange, celui des chiffres publies du controle a) la cherche jusqu'a la sortie de 16 h 30 : simple comptage
    cpt = []
    for metal in ("or", "argent"):
        m = M[metal]
        for per in ("e", "c"):
            x = R[(metal, "F4")][f"det_{per}"]
            h = pd.DatetimeIndex(m.t0 + x["signal"].to_numpy() * M5.PAS).tz_convert(LONDRES).hour
            cpt.append(f"{metal} {'exploration' if per == 'e' else 'coffre'} {int((h >= 12).sum())} sur {len(x)}")
    L.append("  ECART DE TEXTE F4-16:30 (comptage seulement, aucun calcul de gain) : trades dont la cloture de cassure "
             "tombe a 12 h 00 (Londres) ou apres : " + " ; ".join(cpt))
    L.append("")

    # ------------------------------------------------------------- critere 6 : partie C
    L.append("CRITERE 6 (partie C) : correlation avec la zone du bot (NQ minute, sans les jours de la Fed) sur 2016 - 2022,"
             " Sharpe zone + metal a risque egal (ecart-type 2016 - 2022) contre la zone seule au coffre de l'or")
    rech = pd.read_csv(DM.RECHERCHE, usecols=["t"])
    robot = pd.read_csv(DM.ROBOT, usecols=["t"])
    t_nq = pd.concat([rech["t"], robot["t"][robot["t"] > rech["t"].iloc[-1]]])
    seances_nq = pd.DatetimeIndex(pd.to_datetime(t_nq.str[:10]).unique())
    fin_c = pd.Timestamp(COFFRE["or"][1])
    JT = {}
    for (metal, k), r in R.items():
        jt = pd.concat([M5.par_jour(trades(S[k], M[metal], "2016-01-01", EXPLO[1], FRAIS[metal])),
                        M5.par_jour(r["net_c"])])
        JT[(metal, k)] = jt[(jt.index >= pd.Timestamp("2016-01-01")) & (jt.index <= fin_c)]
    tous = seances_nq
    for jt in JT.values():
        tous = tous.union(jt.index)
    tous = tous[(tous >= pd.Timestamp("2016-01-01")) & (tous <= fin_c)]
    zb_tous = pd.Series(PA.zone_bot(tous)[0], index=tous)
    C6 = {}
    for (metal, k), jt in JT.items():
        cal = seances_nq[(seances_nq >= pd.Timestamp("2016-01-01")) & (seances_nq <= fin_c)].union(jt.index)
        zb = zb_tous.reindex(cal).to_numpy()
        assert not np.isnan(zb).any()
        rs = jt.reindex(cal).fillna(0.0).to_numpy()
        e = cal <= pd.Timestamp(EXPLO[1])
        c = cal >= pd.Timestamp(COFFRE["or"][0])
        corr = float(np.corrcoef(rs[e], zb[e])[0, 1])
        w = zb[e].std() / rs[e].std()
        comb = zb + w * rs
        sz, sc = PA.sharpe(zb[c]), PA.sharpe(comb[c])
        C6[(metal, k)] = (corr < 0.3 and sc > sz, corr, sz, sc)
        L.append(f"  {NOMS[k]} {metal} : {len(cal)} seances, corr {corr:+.3f}, Sharpe coffre zone {sz:+.2f} -> zone + "
                 f"{metal} {sc:+.2f} (Sharpe du metal seul au coffre {PA.sharpe(rs[c]):+.2f}) : "
                 f"{'passe' if C6[(metal, k)][0] else 'echoue'}{'' if metal == 'or' else ' (information : le critere porte sur le MGC)'}")
    L.append("")

    # ------------------------------------------------------------- critere 7 : Lucid Flex
    L.append(f"CRITERE 7 : {LUCID} (moteur de la partie D), 1 MNQ + 1 MGC contre 1 MNQ seul, gains au prix d'aujourd'hui")
    jz, ch, bz, hz = PD.chemins_zone()
    v_ctrl, p_ctrl, e_ctrl, n_ctrl = lucid(jz, (ch, bz, hz), (0 * ch, 0 * ch, 0 * ch), ("2023-01-01", None))
    L.append(f"  controle : zone seule sur le calendrier de la partie D ({len(jz)} seances jusqu'au {jz[-1].date()}), "
             f"departs 2023 - 2026 : {n_ctrl} departs, valide {v_ctrl:.0f} %, perdu {p_ctrl:.0f} % ; partie D : 804 "
             f"departs, 55 % / 35 % -> {'identique' if (n_ctrl == 804 and round(v_ctrl) == 55 and round(p_ctrl) == 35) else 'ECART'}")
    prix = {}
    for metal, (c, attendu) in PRIX_AUJ.items():
        y = pd.read_csv(YAHOO / "jour" / f"{c}.csv.gz")
        assert y["t"].iloc[-1] == "2026-10-21" and abs(y["c"].iloc[-1] - attendu) < 0.01
        prix[metal] = attendu
    C7 = {}
    for k in REGLES:
        for metal in ("or", "argent"):
            r = R[(metal, k)]
            V = ONCES[metal] * prix[metal]
            det = pd.concat([detail(S[k], M[metal], *EXPLO, trades(S[k], M[metal], *EXPLO, 0.0)), r["det_c"]])
            det = det[(det["date"] >= jz[0]) & (det["date"] <= fin_c)]
            jm, cm, bm, hm = chemins_metal(det, M[metal], V, FRAIS[metal])
            keep = jz <= fin_c
            cal = pd.DatetimeIndex(jz[keep]).union(jm)
            Z = [np.zeros((len(cal), AVANT + DM.N)) for _ in range(3)]
            G = [np.zeros((len(cal), AVANT + DM.N)) for _ in range(3)]
            iz, im = cal.get_indexer(jz[keep]), cal.get_indexer(jm)
            for a_, src in zip(Z, (ch, bz, hz)):
                a_[iz, AVANT:] = src[keep]
            for a_, src in zip(G, (cm, bm, hm)):
                a_[im] = src
            zero = [0 * Z[0]] * 3
            res = {}
            for per, dd in (("verif", ("2023-01-01", None)), ("choix", ("2012-01-01", "2021-12-31"))):
                res[per] = (lucid(cal, Z, zero, dd), lucid(cal, Z, G, dd))
            (vz, pz, ez, nz), (vg, pg, eg, ng) = res["verif"]
            ok7 = vg >= vz + 3 and pg <= pz + 3
            C7[(metal, k)] = (ok7, vz, pz, vg, pg, nz)
            (vz2, pz2, _, nz2), (vg2, pg2, _, _) = res["choix"]
            lab = "MGC" if metal == "or" else "SIL (information)"
            L.append(f"  {NOMS[k]} + 1 {lab} : {len(cal)} seances ; departs 2023 -> {cal[-1].date()} ({nz}) : zone seule "
                     f"valide {vz:.1f} % / perdu {pz:.1f} %, zone + metal {vg:.1f} % / {pg:.1f} % -> "
                     f"{'passe' if ok7 else 'echoue'} ; departs 2012 - 2021 ({nz2}, information) : {vz2:.1f} / {pz2:.1f} "
                     f"-> {vg2:.1f} / {pg2:.1f}")
            if metal == "or":
                gj = cm[:, -1]
                L.append(f"     MGC seul : {len(jm)} jours de trade, gain moyen {gj.mean():+.2f} $ par trade, pire jour "
                         f"{gj.min():+.0f} $, ecart-type {gj.std():.0f} $ (zone 1 MNQ : {ch[:, -1].std():.0f} $)")
    L.append("")

    # ------------------------------------------------------------- criteres et synthese
    L.append("=" * 110)
    L.append("CRITERES PAR TEST (BH a 10 % calcule ensuite sur les 17 tests des 5 pistes ; p unilateral du t d'exploration)")
    propres = {}
    for k in REGLES:
        crit = {}
        for metal in ("or", "argent"):
            r = R[(metal, k)]
            c = {}
            c["1 t explo >= 2"] = r["st_e"]["t"] >= 2
            c["2 coffre t >= 1,5"] = r["st_c"]["t"] >= 1.5
            if metal == "or":
                c["2 coffre 3 annees sur 4 positives"] = sum(a > 0 for a in r["ans"]) >= 3
                c["4 placebo coffre (or) < 5 %"] = r["plac_c"] <= 0.05
            else:
                c["4 placebo exploration (argent) < 5 %"] = r["plac_e"] <= 0.05
            c["5 sensibilite t > 0 (explo et coffre)"] = r["sens_e"]["t"] > 0 and r["sens_c"]["t"] > 0
            c["5 frais fixes $ t > 0 (coffre)"] = r["dol_c"]["t"] > 0
            crit[metal] = c
        seul = {metal: all(crit[metal].values()) for metal in crit}
        c6, c7 = C6[("or", k)][0], C7[("or", k)][0]
        for metal in ("or", "argent"):
            autre = "argent" if metal == "or" else "or"
            c = dict(crit[metal])
            c[f"3 la regle passe aussi sur l'{autre}"] = seul[autre]
            c["6 partie C (MGC)"] = c6
            c["7 Lucid Flex zone + MGC"] = c7
            propres[(metal, k)] = c
    L.append("  test               t explo  bilateral  p        t coffre  criteres propres")
    for k in REGLES:
        for metal in ("or", "argent"):
            r, c = R[(metal, k)], propres[(metal, k)]
            ok = all(c.values())
            L.append(f"  {NOMS[k]:8} {metal:7}   {r['st_e']['t']:+6.2f}   non        {r['p']:.4f}   {r['st_c']['t']:+6.2f}"
                     f"    {'PASSE' if ok else 'echec'}")
            L.append("      " + " ; ".join(f"{n} {'oui' if v else 'non'}" for n, v in c.items()))
    L.append("")
    L += ["REGARD VERS LE FUTUR (verifie dans le code, assertions de detail()) : la fourchette ne lit que les barres "
          "[debut, fin de fourchette) ; le signal est la cloture d'une barre apres la fourchette ; l'entree est a",
          "  l'ouverture de la barre suivante ; le stop est l'autre extreme de la fourchette (connu a l'entree) ; la "
          "sortie est au stop ou a l'ouverture de 16 h 30 (Londres) ; les frais fixes en $ utilisent le prix d'entree ;",
          "  le poids a risque egal (critere 6) vient de 2016 - 2022 seulement ; le jour de trade (machine 5 : jour CME "
          "de la barre de sortie) est le jour de Londres de la fourchette pour tous les trades.",
          "CONTROLE e) (metaux permis chez Bulenox et Lucid, commission reelle, ecart a 3 h du matin sur le MGC) : sans "
          "objet tant qu'aucune regle ne passe. Recherche web du 22 octobre 2026 : Lucid, guides tiers seulement",
          "  (proptradingvibes.com) : GC, MGC, SI, SIL, PL, HG dans la liste des produits permis ; Bulenox, un guide "
          "tiers seulement : metaux du COMEX (GC, SI et micros) permis. Aucune page officielle lue : A CONFIRMER.",
          "  Commission reelle et ecart du MGC a 3 h du matin : non verifiables avec les donnees du depot (pas de prix "
          "acheteur et vendeur) ; le tick du SIL (0,005 $ = 5 $, README) n'a pas ete reverifie.",
          "",
          "CHOIX D'INTERPRETATION (fixes avant tout calcul) :",
          "  - t net = t de la machine 5 (jours avec un trade, chiffres publies du controle a) ; t avec 0 sans trade publie "
          "pour information ;",
          "  - frais principaux 0,96 pb et 2,1 pb (chiffres ecrits dans le README) ; frais fixes : 0,40 $ par once (MGC) "
          "et 0,012 $ par once (SIL) divises par le prix d'entree (Marche.cout, unite 'pt') ;",
          "  - sensibilite exigee sur l'exploration ET le coffre ; frais fixes exiges sur le coffre ;",
          "  - critere 3 : chaque test exige que sa regle passe aussi sur l'autre metal ; criteres 6 et 7 calcules avec le "
          "MGC pour la regle (SIL publie pour information) ;",
          "  - critere 7 : departs 2023 -> fin du coffre de l'or (2 octobre 2026), calendrier = seances jouables de la zone "
          "+ jours de trade du metal, 126 seances au plus (partie D) ;",
          "  - controle b : ouverture de la barre de 3 h et de la barre de 11 h (New York) des deux sources ; seuil exige "
          "sur GC et SI, MGC pour information ;",
          "  - F4-16:30 : le README dit « cassure cherchee de 7 h 00 a 12 h 00 », mais aussi « code de la machine 5 "
          "inchange » et exige (controle a) qu'il redonne les chiffres publies ; machine5.cassures cherche la",
          "    cassure jusqu'a la sortie (16 h 30). Le code inchange est garde (c'est lui qui redonne +3,20 pb et t 2,82) ; "
          "le nombre de trades touches est publie ci-dessus, sans autre calcul."]
    n_ok = sum(all(c.values()) for c in propres.values())
    L.append("")
    L.append("DECISION fixee a l'avance (critere 3), avant Benjamini-Hochberg :")
    for k in REGLES:
        po = {n: v for n, v in propres[("or", k)].items() if not n.startswith("3 ")}
        pa = all(v for n, v in propres[("argent", k)].items() if not n.startswith("3 "))
        if all(po.values()) and pa:
            dec = "retenue (or ET argent) -> robot en argent virtuel apres contre-verification adverse"
        elif all(po.values()):
            dec = "l'or passe seul -> la regle est seulement suivie en argent virtuel"
        else:
            dec = "non retenue (l'or ne passe pas ses criteres" + (", l'argent non plus)" if not pa else ")")
        L.append(f"  {NOMS[k]} : {dec}")
    L.append(f"CONCLUSION : {n_ok} test(s) sur 4 passent leurs criteres propres (avant Benjamini-Hochberg).")
    texte = "\n".join(L)
    (ICI / "resultats.txt").write_text(texte + "\n")
    print(texte)


if __name__ == "__main__":
    main()
