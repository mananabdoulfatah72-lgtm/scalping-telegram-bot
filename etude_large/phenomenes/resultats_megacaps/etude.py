#!/usr/bin/env python3
"""etude_large/phenomenes/README.md, piste A (regles fixees le 22 octobre 2026, commit 929d05e, avant tout calcul) :
resultats des mega-capitalisations, seance d'attente le soir de la publication (A1, A2) et seance d'information le
lendemain (A3).

A1 : pas de zone les jours E (au moins une des 10 valeurs publie le soir de la seance).
A2 : pas de zone les jours E lourds (une des six, ou au moins 2 des 10, publient pour la meme seance).
A3 : lendemain d'une publication d'une des six avec |g| >= 0,02 : la zone ne prend que les entrees dans le sens d de la
     reaction (les autres restent virtuelles et bloquantes).

ETAT DES DONNEES (constate avant tout calcul) : le calendrier Yahoo (donnees_libres/resultats/calendrier.csv) n'existe
pas. Yahoo repond 403 depuis le conteneur, yfinance n'y est pas installe, et l'etape du workflow GitHub
donnees-libres.yml exigee par le README demande de modifier un autre fichier et de pousser sur git, ce que la consigne de
cette piste interdit. Le README prevoit ce cas : « Si le calendrier Yahoo ne peut pas etre telecharge, la piste A n'est
que descriptive : la detection par l'ecart regarde la reaction d'apres la seance et jusqu'a 30 seances plus tard, ce qui
est un regard vers le futur. » Le calendrier defini par le README devient alors la detection par l'ecart pour chaque
valeur et chaque trimestre (aucun trimestre n'a de date Yahoo). Tout est calcule selon les regles, mais AUCUNE regle ne
peut etre retenue. Si le fichier Yahoo apparait, ce script l'utilise tel que le README le decrit.

Briques reutilisees sans changement : delta_mesures/etude.py (preparer, zone_jour, trades_zone, RECHERCHE, ROBOT, FIN,
N, PAS, COUT), zone/robot.py (tableaux, seances_completes, precedente, PT), etude_large/partie_d.py (chemins_zone,
tous_les_departs, limites_depart, FIRMES, DEBUT, DEBUT_VERIF), etude_large/partie_a.py (t_stat, sharpe, p_unilateral),
kb/fonds/fomc.py.

Choix d'interpretation (ecrits avant tout calcul, repris dans resultats.txt) :
- detection : mediane des |g| finies des 250 seances precedentes (il faut 250 seances de la valeur avant t : premiere
  detection possible en janvier 2017) ; maximum des |g| finies de [t - 30, t + 30], fenetre tronquee aux bords des
  donnees ; g manquant (QQQ sans barre de 15 h 55 les demi-seances, nuits de split) : pas de detection ce soir-la et
  valeur absente des medianes et des maximums ;
- « la date de la detection » d'un trimestre : s'il y a deux detections dans le meme trimestre civil, celle du plus grand
  |g| (une date par valeur et par trimestre, comme le calendrier qu'elle remplace) ;
- jour E : seance de la publication, complete et jouable pour la zone du NQ ; la Fed garde la priorite (difference
  nulle). Les jours E de la Fed ne sont ni remplaces dans le placebo, ni des candidats ;
- jour I : seance jouable t dont la seance precedente (calendrier des valeurs, verifie contre celui du NQ) est un jour
  E pour au moins une des six ; g des publiantes = g de la nuit t - 1 -> t (meme formule que la detection, QQQ deduit) ;
- placebo A3 : candidats = seances jouables non I et hors Fed de la meme annee, ecart d'ouverture du NQ non nul, tirage
  sans remise dans chaque case (annee, quintile) ; les quintiles sont ceux des seances jouables de l'annee ;
- statistique des placebos : t net d'exploration de la serie Delta (zeros compris) ; place de la somme en information ;
- controle d) : reference = ouverture de 9 h 30 du jour (normalisation de sigma) ; jours placebo = ceux des 1 000
  tirages de A1 ;
- E3 (information) : la seule definition ecrite est « la difference avec la zone seule vaut exactement 0,8 fois celle de
  E1, jour par jour » : les jours E, la zone est jouee a 0,2 fois sa taille (chemins des jours E multiplies par 0,2) ;
- regard vers le futur : la zone (bruit apres chaque controle, 300 seances) et le calendrier (les g qui suivent la
  decision remplaces par une permutation des g de la valeur, chaque soir de 2016 - 2026) ;
- le coffre n'est calcule que par « python3 etude.py coffre », qui refait l'exploration, verifie qu'elle redonne mot
  pour mot la partie deja ecrite dans resultats.txt, puis ajoute le coffre.

Lancer : export KB=<branche de recherche extraite> ; python3 etude_large/phenomenes/resultats_megacaps/etude.py
(exploration), puis ... etude.py coffre."""
import os
import sys
import tempfile

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(os.path.join(tempfile.gettempdir(), "numba_resultats_megacaps")))

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
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

RB, N, PAS, COUT, KB = DM.RB, DM.N, DM.PAS, DM.COUT, DM.KB
VALEURS = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "COST", "NFLX"]
SIX = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "META"]
CALENDRIER = RACINE / "donnees_libres" / "resultats" / "calendrier.csv"
GRANDES = KB / "vague4" / "donnees" / "grandes.csv.gz"
QQQ = RACINE / "donnees_libres" / "etf_5min" / "QQQ.csv.gz"
MINUTES_ES = KB / "intraday" / "donnees" / "sp500_1min.csv.gz"
EXPLO = ("2016-01-04", "2022-12-30")
COFFRE = ("2023-01-03", "2026-10-20")
COFFRE_A3 = ("2023-01-03", "2026-09-30")
SOUS = [("2016-2019", "2016-01-01", "2019-12-31"), ("2020-2022", "2020-01-01", "2022-12-31")]
SOUS_COFFRE = [("2023-2026", "2023-01-01", "2026-12-31")]
MEDIANE, FENETRE, FOIS, SEUIL_I = 250, 30, 3.0, 0.02
SPLITS = np.log([2, 3, 4, 5, 10, 20])
PLACEBOS, GRAINE = 1000, 1
COUT_ES, PT_ES = 0.9, 5.0
LUCID, BULENOX = "Lucid Flex 50K", "Bulenox Legacy 50K opt. 2"
TESTS = ["A1", "A2", "A3"]
NOMS = {"A1": "A1 pas de zone les jours E (10 valeurs)",
        "A2": "A2 pas de zone les jours E lourds (une des six, ou 2 des 10)",
        "A3": "A3 lendemain : zone seulement dans le sens d de la reaction"}
MARQUE = "\n" + "#" * 100 + "\nCOFFRE (ouvert une seule fois, apres l'ecriture de l'exploration ci-dessus)\n" + "#" * 100


def heure(m):
    return f"{(570 + m) // 60}h{(570 + m) % 60:02d}"


def per(s, a, b):
    return s[(s.index >= pd.Timestamp(a)) & (s.index <= pd.Timestamp(b))]


def t_de(s, a, b):
    return PA.t_stat(per(s, a, b).to_numpy())


def t_sommes(S, Q, n):
    """t de series de n valeurs (zeros compris) a partir des sommes S et des sommes de carres Q (vecteurs)."""
    var = (Q - S ** 2 / n) / (n - 1)
    return np.where(var > 0, S / n / np.sqrt(np.maximum(var, 1e-300)) * np.sqrt(n), 0.0)


# ----------------------------------------------------------------------------- valeurs : ecarts et calendrier
def qqq_jour():
    q = pd.read_csv(QQQ, usecols=["t", "o", "c"])
    j, hm = q["t"].str[:10], q["t"].str[11:16]
    o = pd.Series(q["o"].to_numpy()[(hm == "09:30").to_numpy()], index=pd.DatetimeIndex(j[hm == "09:30"]))
    c = pd.Series(q["c"].to_numpy()[(hm == "15:55").to_numpy()], index=pd.DatetimeIndex(j[hm == "15:55"]))
    return o, c


def ecarts():
    """Par valeur : seances (jour), seance suivante, r = ln(ouverture suivante / c390), g = r - ecart de QQQ, nuits de
    split retirees (g manquant)."""
    gr = pd.read_csv(GRANDES)
    gr["jour"] = pd.to_datetime(gr["jour"])
    qo, qc = qqq_jour()
    out = {}
    for v in VALEURS:
        x = gr[gr["valeur"] == v].sort_values("jour").reset_index(drop=True)
        suivant = x["jour"].shift(-1)
        r = np.log(x["ouverture"].shift(-1).to_numpy() / x["c390"].to_numpy())
        rq = np.log(qo.reindex(suivant).to_numpy() / qc.reindex(x["jour"]).to_numpy())
        split = (np.abs(r) > 0.25) & (np.min(np.abs(r[:, None] + SPLITS[None, :]), axis=1) < 0.05)
        g = r - rq
        g[split] = np.nan
        out[v] = pd.DataFrame({"jour": x["jour"], "suivant": suivant, "r": r, "g": g, "split": split})
    return out


def detecter(g):
    """Detection par l'ecart (README) : |g_t| >= 3 x mediane des |g| des 250 seances precedentes et |g_t| le plus grand
    de [t - 30, t + 30]. Renvoie le masque des detections et la mediane."""
    a = np.abs(np.asarray(g, float))
    n = len(a)
    med = np.full(n, np.nan)
    for t in range(MEDIANE, n):
        w = a[t - MEDIANE:t]
        w = w[np.isfinite(w)]
        if len(w):
            med[t] = np.median(w)
    det = np.zeros(n, bool)
    for t in range(n):
        if np.isfinite(a[t]) and np.isfinite(med[t]) and a[t] >= FOIS * med[t]:
            w = a[max(0, t - FENETRE):t + FENETRE + 1]
            det[t] = a[t] >= np.nanmax(w)
    return det, med


def detection_a(a, med, t):
    """Detection a la seance t avec une serie |g| donnee (pour le controle du regard vers le futur)."""
    if not (np.isfinite(a[t]) and np.isfinite(med[t]) and a[t] >= FOIS * med[t]):
        return False
    return bool(a[t] >= np.nanmax(a[max(0, t - FENETRE):t + FENETRE + 1]))


def une_par_trimestre(x, det):
    """Une date par valeur et par trimestre civil : la detection du plus grand |g|."""
    d = x.loc[det, ["jour", "g"]].copy()
    d["a"] = d["g"].abs()
    d["trim"] = d["jour"].dt.to_period("Q")
    garde = d.loc[d.groupby("trim")["a"].idxmax()]
    return pd.DatetimeIndex(garde["jour"]).sort_values(), int((d.groupby("trim").size() > 1).sum())


def yahoo(seances):
    """Calendrier Yahoo (si present) : valeur -> seances de publication, selon les regles d'horodatage du README."""
    if not CALENDRIER.exists():
        return None
    c = pd.read_csv(CALENDRIER)
    c.columns = [k.strip().lower() for k in c.columns]
    t = pd.to_datetime(c[c.columns[1]])
    if getattr(t.dt, "tz", None) is not None:
        t = t.dt.tz_convert("America/New_York").dt.tz_localize(None)
    s = seances.values
    out = {}
    for v, tt in zip(c[c.columns[0]], t):
        d = tt.normalize()
        mn = tt.hour * 60 + tt.minute
        if mn >= 16 * 60 or mn == 0:
            k = np.searchsorted(s, d.to_datetime64(), side="right") - 1          # le jour meme, sinon la precedente
        elif mn < 9 * 60 + 30:
            k = np.searchsorted(s, d.to_datetime64(), side="left") - 1           # seance precedente
        else:
            k = np.searchsorted(s, d.to_datetime64(), side="left")
            if k >= len(s) or s[k] != d.to_datetime64():
                continue
        if 0 <= k < len(s):
            out.setdefault(str(v).upper(), set()).add(pd.Timestamp(s[k]))
    return out


def calendrier(G):
    """valeur -> seances de publication. Trimestres sans date Yahoo : detection par l'ecart. Renvoie aussi les infos."""
    seances = pd.DatetimeIndex(G[VALEURS[0]]["jour"])
    y = yahoo(seances)
    cal, info = {}, {}
    for v in VALEURS:
        x = G[v]
        det, med = detecter(x["g"].to_numpy())
        dd, doubles = une_par_trimestre(x, det)
        info[v] = dict(det=det, med=med, detections=int(det.sum()), retenues=len(dd), doubles=doubles,
                       splits=x.loc[x["split"], "jour"].dt.date.tolist())
        if y is None:
            cal[v] = set(dd)
            info[v]["comblees"] = len(dd)
            continue
        yv = y.get(v, set())
        trim_y = {pd.Timestamp(d).to_period("Q") for d in yv}
        ajout = {d for d in dd if d.to_period("Q") not in trim_y and 2016 <= d.year <= 2026}
        cal[v] = set(yv) | ajout
        info[v]["comblees"] = len(ajout)
        info[v]["yahoo"] = yv
        info[v]["detectees"] = set(dd)
    return cal, info, y is not None


# ----------------------------------------------------------------------------- zone du NQ
def charger_nq():
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    return pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)   # comme chemins_zone


def zone_trades(z, fed, cout, pt, ref):
    """Trades V1 sans les jours de la Fed, avec leur valeur en $ au niveau de prix de reference (convention de
    partie_d.chemins_zone : points bruts x ref / C[minute de 9 h 30], moins les frais, x $ par point)."""
    tr = DM.trades_zone(z, "2000-01-01", DM.FIN)
    tr = tr[~tr["jour"].isin(fed)].reset_index(drop=True)
    idx = {j: i for i, j in enumerate(z["jours"])}
    tr["i"] = tr["jour"].map(idx)
    f = ref / z["C"][tr["i"].to_numpy(), 0]
    tr["brut"] = tr["sens"] * (tr["prix_sortie"] - tr["prix_entree"])
    tr["net_pts"] = tr["brut"] - cout
    tr["usd"] = (tr["brut"] * f - cout) * pt
    return tr


def chemins(z, Hm, Lm, tr):
    """Recopie de partie_d.chemins_zone avec une liste de trades donnee (jours de la Fed deja retires)."""
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= PD.DEBUT) & (jours <= DM.FIN)]
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], N - 1])
    ch, bas, haut = (np.zeros((len(jours), N)) for _ in range(3))
    pos = {j: k for k, j in enumerate(jours)}
    for j, g in tr.groupby("jour"):
        if j not in pos:
            continue
        i = idx[j]
        C, H, L = z["C"][i], Hm[i], Lm[i]
        f = ref / C[0]
        c, contre, pour = np.zeros(N), np.zeros(N), np.zeros(N)
        for me, ms, s, pe, ps in zip(g["minute_entree"], g["minute_sortie"], g["sens"], g["prix_entree"],
                                     g["prix_sortie"]):
            me, ms, s = int(me), int(ms), int(s)
            c[me:ms] += s * (C[me:ms] - pe) * f
            c[ms:] += s * (ps - pe) * f
            c[me:] -= COUT
            w = slice(me + 1, ms + 1)
            contre[w] += ((C[w] - L[w]) if s > 0 else (H[w] - C[w])) * f
            pour[w] += ((H[w] - C[w]) if s > 0 else (C[w] - L[w])) * f
        k = pos[j]
        ch[k], bas[k], haut[k] = c * RB.PT, (c - contre) * RB.PT, (c + pour) * RB.PT
    return jours, ch, bas, haut


def defis(ch, firme, q, q_fin=None, n_fin=0):
    obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
    jours, clo, bas, haut = ch
    verif = np.where(jours >= pd.Timestamp(PD.DEBUT_VERIF))[0]
    lim = PD.limites_depart(jours, verif, nmax)
    ok = verif + lim < len(jours)
    qf = q if q_fin is None else q_fin
    iss, _ = PD.tous_les_departs(np.ascontiguousarray(clo), np.ascontiguousarray(bas), np.ascontiguousarray(haut),
                                 verif[ok], lim[ok], float(q), float(qf), int(n_fin), float(obj), float(dd),
                                 float(bloc), float(dll), part, True)
    return dict(n=int(ok.sum()), valide=(iss == 1).mean() * 100, perdu=(iss == -1).mean() * 100,
                expire=(iss == 0).mean() * 100)


# ----------------------------------------------------------------------------- regard vers le futur
def regard_zone(z, idx, rng, n=300):
    """Chaque decision de la zone au controle m ne doit dependre que des minutes <= m : prix, VWAP et sigma apres m
    remplaces par du bruit ; les entrees et sorties jusqu'a m doivent rester les memes."""
    def ev(C, sg, vw, hr, br, m):
        out = []
        for me, s, pe, ms, ps in DM.zone_jour(C, sg, vw, hr, br):
            if me <= m:
                out.append(("entree", me, s, round(pe, 6)))
            if ms <= m:
                out.append(("sortie", ms, round(ps, 6)))
        return out

    essais = erreurs = 0
    for i in rng.choice(idx, size=min(n, len(idx)), replace=False):
        C, sg, vw, hr, br = z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i]
        for m in range(PAS, N - 1, PAS):
            C2, sg2, vw2 = C.copy(), sg.copy(), vw.copy()
            k = N - m - 1
            C2[m + 1:] = C[m] * (1 + rng.normal(0, 0.02, k))
            vw2[m + 1:] = C[m] * (1 + rng.normal(0, 0.02, k))
            sg2[m + 1:] = rng.uniform(0, 0.03, k)
            essais += 1
            erreurs += ev(C, sg, vw, hr, br, m) != ev(C2, sg2, vw2, hr, br, m)
    return essais, erreurs


def regard_calendrier(G, info, rng):
    """Detection de chaque soir t de 2016 - 2026 recalculee apres avoir remplace les g qui suivent la decision par une
    permutation des g de la valeur : A1 et A2 decident avant 10 h 00 de la seance t (g_t lui-meme est inconnu), A3 decide
    a 9 h 30 de la seance t + 1 (g_t connu, g_{t+1}... inconnus)."""
    res = {}
    for nom, decale in (("A1/A2 (decision avant 10 h de t)", 0), ("A3 (decision a 9 h 30 de t + 1)", 1)):
        perdues = nouvelles = reelles = soirs = 0
        for v in VALEURS:
            a = np.abs(G[v]["g"].to_numpy())
            det, med = info[v]["det"], info[v]["med"]
            fin = np.isfinite(a)
            for t in range(MEDIANE, len(a)):
                b = a.copy()
                s0 = t + decale
                fut = np.where(fin[s0:])[0] + s0
                b[fut] = rng.permutation(a[fin])[:len(fut)]
                d2 = detection_a(b, med, t)
                soirs += 1
                reelles += det[t]
                perdues += det[t] and not d2
                nouvelles += (not det[t]) and d2
        res[nom] = (soirs, reelles, perdues, nouvelles)
    return res


# ----------------------------------------------------------------------------- principal
def construire():
    """Tout ce qui ne depend pas de la periode : zone, calendrier, jours E, E lourds, I, series quotidiennes."""
    D = {}
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    bars = charger_nq()
    z = DM.preparer(bars)
    jours_nq, O, Hm, Lm, Cm, P, V, ech = RB.tableaux(bars)
    assert (pd.DatetimeIndex(jours_nq) == z["jours"]).all()
    ok = RB.seances_completes(P)
    prec = RB.precedente(ok, np.cumsum(ech))
    veille = np.where(prec >= 0, Cm[np.maximum(prec, 0), N - 1], np.nan)
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], N - 1])
    tr = zone_trades(z, fed, COUT, RB.PT, ref)
    jouables = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    cal = jouables[(jouables >= pd.Timestamp(EXPLO[0])) & (jouables <= pd.Timestamp(DM.FIN))]
    D.update(fed=fed, bars=bars, z=z, O=O, Hm=Hm, Lm=Lm, tr=tr, cal=cal, jouables=set(jouables), ref=ref, idx=idx,
             veille=veille)

    G = ecarts()
    calv, info, avec_yahoo = calendrier(G)
    pubs = {}
    for v in VALEURS:
        for d in calv[v]:
            pubs.setdefault(d, set()).add(v)
    E = {d for d in pubs if d in D["jouables"]}
    lourd = {d for d in E if (pubs[d] & set(SIX)) or len(pubs[d]) >= 2}
    # jours I : seance precedente (calendrier des valeurs) jour E pour une des six, |g| >= 0,02 pour une publiante
    seances = pd.DatetimeIndex(G[VALEURS[0]]["jour"])
    gnuit = {v: pd.Series(G[v]["g"].to_numpy(), index=pd.DatetimeIndex(G[v]["jour"])) for v in VALEURS}
    suiv = {v: pd.Series(pd.DatetimeIndex(G[v]["suivant"]), index=pd.DatetimeIndex(G[v]["jour"])) for v in VALEURS}
    I, detail_I, desaccord_prec = {}, {}, 0
    for k in range(1, len(seances)):
        t, p = seances[k], seances[k - 1]
        if p not in E or t not in D["jouables"]:
            continue
        six = sorted(pubs[p] & set(SIX))
        if not six:
            continue
        gs = {v: float(gnuit[v][p]) for v in six if suiv[v][p] == t and np.isfinite(gnuit[v][p])}
        q = {v: x for v, x in gs.items() if abs(x) >= SEUIL_I}
        if not q or sum(q.values()) == 0:
            continue
        i = idx[t]
        if i == 0 or z["jours"][i - 1] != p:
            desaccord_prec += 1
        I[t] = int(np.sign(sum(q.values())))
        detail_I[t] = q
    D.update(G=G, calv=calv, info=info, avec_yahoo=avec_yahoo, pubs=pubs, E=E, lourd=lourd, I=I, detail_I=detail_I,
             desaccord_prec=desaccord_prec, seances=seances)

    # series quotidiennes ($, 1 MNQ au niveau du 20 octobre 2026)
    zone = tr.groupby("jour")["usd"].sum().reindex(cal).fillna(0.0)
    achat = tr[tr["sens"] > 0].groupby("jour")["usd"].sum().reindex(cal).fillna(0.0)
    vente = tr[tr["sens"] < 0].groupby("jour")["usd"].sum().reindex(cal).fillna(0.0)
    retire = {}
    retire["A1"] = tr["jour"].isin(E).to_numpy()
    retire["A2"] = tr["jour"].isin(lourd).to_numpy()
    dI = tr["jour"].map(I).fillna(0).to_numpy()
    retire["A3"] = (dI != 0) & (tr["sens"].to_numpy() != dI)
    delta, delta_pts = {}, {}
    for k in TESTS:
        x = tr[retire[k]]
        delta[k] = -x.groupby("jour")["usd"].sum().reindex(cal).fillna(0.0)
        delta_pts[k] = -x.groupby("jour")["net_pts"].sum().reindex(cal).fillna(0.0)
    D.update(zone=zone, achat=achat, vente=vente, retire=retire, delta=delta, delta_pts=delta_pts)
    # ecart d'ouverture du NQ (placebo A3)
    gap = pd.Series(np.log(O[:, 0] / veille), index=z["jours"]).reindex(cal)
    D["gap"] = gap
    return D


def placebo_E(D, jours_E, a, b, rng):
    """A1, A2 : dans chaque annee et chaque mois, les jours E (hors Fed) remplaces par autant de seances jouables du meme
    mois qui ne sont ni des jours E ni des jours de la Fed. t de Delta = -zone sur ces seances."""
    cal = per(D["zone"], a, b)
    n = len(cal)
    zv = cal.to_numpy()
    mois = cal.index.to_period("M")
    estE = cal.index.isin(list(D["E"]))
    estF = cal.index.isin(list(D["fed"]))
    cible = cal.index.isin(list(jours_E)) & ~estF
    S, Q = np.zeros(PLACEBOS), np.zeros(PLACEBOS)
    jours_tires = []
    groupes = []
    for m in np.unique(mois):
        dans = mois == m
        k = int((dans & cible).sum())
        if k == 0:
            continue
        cand = np.where(dans & ~estE & ~estF)[0]
        groupes.append((k, cand))
    manque = sum(1 for k, c in groupes if len(c) < k)
    for p in range(PLACEBOS):
        sel = np.concatenate([rng.choice(c, size=k, replace=len(c) < k) for k, c in groupes]) if groupes else \
            np.zeros(0, int)
        x = -zv[sel]
        S[p], Q[p] = x.sum(), (x ** 2).sum()
        jours_tires.append(sel)
    return t_sommes(S, Q, n), S, jours_tires, manque


def placebo_I(D, a, b, rng):
    """A3 : chaque jour I (hors Fed) remplace par une seance non I de la meme annee dont |ecart d'ouverture du NQ| est
    dans le meme quintile de l'annee ; d = signe de l'ecart de ce jour."""
    cal = per(D["zone"], a, b)
    n = len(cal)
    gap = D["gap"].reindex(cal.index)
    ach, ven = D["achat"].reindex(cal.index).to_numpy(), D["vente"].reindex(cal.index).to_numpy()
    estI = cal.index.isin(list(D["I"]))
    estF = cal.index.isin(list(D["fed"]))
    ans = cal.index.year
    quint = np.full(n, -1)
    for y in np.unique(ans):
        m = ans == y
        ag = np.abs(gap.to_numpy()[m])
        bornes = np.quantile(ag[np.isfinite(ag)], [0.2, 0.4, 0.6, 0.8])
        quint[m] = np.searchsorted(bornes, ag, side="right")
    groupes = []
    for y in np.unique(ans):
        for qz in range(5):
            cell = (ans == y) & (quint == qz)
            k = int((cell & estI & ~estF).sum())
            if k == 0:
                continue
            cand = np.where(cell & ~estI & ~estF & np.isfinite(gap.to_numpy()) & (gap.to_numpy() != 0))[0]
            groupes.append((k, cand))
    manque = sum(1 for k, c in groupes if len(c) < k)
    dg = np.sign(gap.to_numpy())
    S, Q = np.zeros(PLACEBOS), np.zeros(PLACEBOS)
    for p in range(PLACEBOS):
        sel = np.concatenate([rng.choice(c, size=k, replace=len(c) < k) for k, c in groupes])
        x = -np.where(dg[sel] > 0, ven[sel], ach[sel])
        S[p], Q[p] = x.sum(), (x ** 2).sum()
    return t_sommes(S, Q, n), S, manque


def zone_es(D):
    """Replication ES (MES, 0,9 point), memes jours E, E lourds, I."""
    es = pd.read_csv(MINUTES_ES)
    z = DM.preparer(es)
    ref = float(z["C"][-1, N - 1]) if z["jours"][-1] <= pd.Timestamp(DM.FIN) else np.nan
    tr = zone_trades(z, D["fed"], COUT_ES, PT_ES, ref)
    jou = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    cal = jou[(jou >= pd.Timestamp(EXPLO[0])) & (jou <= pd.Timestamp(DM.FIN))]
    dI = tr["jour"].map(D["I"]).fillna(0).to_numpy()
    ret = {"A1": tr["jour"].isin(D["E"]).to_numpy(), "A2": tr["jour"].isin(D["lourd"]).to_numpy(),
           "A3": (dI != 0) & (tr["sens"].to_numpy() != dI)}
    zone = tr.groupby("jour")["usd"].sum().reindex(cal).fillna(0.0)
    delta = {k: -tr[ret[k]].groupby("jour")["usd"].sum().reindex(cal).fillna(0.0) for k in TESTS}
    return dict(cal=cal, zone=zone, delta=delta, fin=cal[-1], ref=ref)


def ecrire_exploration(D, rng, rng_regard):
    L = []
    z, tr, cal, fed = D["z"], D["tr"], D["cal"], D["fed"]
    L.append("Piste A : resultats des mega-capitalisations (etude_large/phenomenes/README.md, commit 929d05e, regles "
             "fixees avant tout calcul)")
    L.append("Dossier etude_large/phenomenes/resultats_megacaps/, 3 tests unilateraux (sens predit : Delta = regle - zone "
             "seule > 0)")
    L.append("")
    L.append("ETAT DU CALENDRIER DES RESULTATS (constate avant tout calcul)")
    if D["avec_yahoo"]:
        L.append(f"  calendrier Yahoo present : {CALENDRIER} ; trimestres sans date comble par la detection.")
    else:
        L.append(f"  {CALENDRIER.relative_to(RACINE)} : ABSENT. Yahoo repond 403 depuis le conteneur (query1, query2, "
                 "finance.yahoo.com), yfinance n'est pas installe ;")
        L.append("  l'etape de .github/workflows/donnees-libres.yml exigee par le README demande de modifier un autre "
                 "fichier et de pousser sur git, interdit par la consigne de")
        L.append("  cette piste ; aucune branche du depot ne contient ce fichier ; les autres sources gratuites essayees "
                 "(SEC EDGAR, Nasdaq, Alpha Vantage, FMP) sont refusees par le proxy.")
        L.append("  -> REGLE DU README : « Si le calendrier Yahoo ne peut pas etre telecharge, la piste A n'est que "
                 "descriptive : la detection par l'ecart regarde la reaction")
        L.append("     d'apres la seance et jusqu'a 30 seances plus tard, ce qui est un regard vers le futur. »")
        L.append("  -> Le calendrier defini par le README est donc la detection par l'ecart pour 100 % des trimestres. "
                 "Tous les chiffres ci-dessous sont DESCRIPTIFS :")
        L.append("     aucune regle de cette piste ne peut etre retenue, quels que soient les t (critere de regard vers le "
                 "futur en echec, mesure plus bas).")
    L.append("")
    L.append("CHOIX D'INTERPRETATION (fixes avant tout calcul, detail dans l'en-tete d'etude.py)")
    for c in ("detection : mediane des |g| finies des 250 seances precedentes de la valeur (premiere detection possible en "
              "janvier 2017), maximum de [t - 30, t + 30] tronque aux bords ;",
              "deux detections dans un meme trimestre civil : celle du plus grand |g| (une date par valeur et par trimestre) ;",
              "jour E de la Fed : reste un jour de la Fed (difference nulle), ni remplace dans les placebos, ni candidat ;",
              "jour I : seance precedente des valeurs (verifiee contre le NQ) jour E pour une des six ; g de la nuit t - 1 -> t, "
              "QQQ deduit, |g| >= 0,02 ;",
              "placebo A3 : candidats non I, hors Fed, ecart d'ouverture du NQ non nul, meme annee et meme quintile de l'annee, "
              "tirage sans remise par case ;",
              "statistique des placebos : t net de la serie Delta d'exploration (zeros compris) ; place de la somme en information ;",
              "controle d) : reference = ouverture de 9 h 30 ; E3 : zone a 0,2 x sa taille les jours E (seule definition ecrite : "
              "difference = 0,8 x celle de E1).",):
        L.append("  - " + c)
    L.append("")
    L.append(f"Donnees : minutes du NQ {z['jours'][0].date()} - {z['jours'][-1].date()} (recherche + robot, {len(z['jours'])} "
             f"seances, {len(D['jouables'])} jouables) ; {GRANDES.relative_to(KB)} : {len(D['seances'])} seances "
             f"{D['seances'][0].date()} - {D['seances'][-1].date()} par valeur ; QQQ 5 minutes ; {len(fed)} jours de la Fed.")
    L.append(f"Niveau de prix de reference : cloture du NQ du {DM.FIN} a 15 h 59 = {D['ref']:.2f} ; serie de decision en $ "
             f"pour 1 MNQ (convention de partie_d.chemins_zone), {COUT} point par aller-retour.")
    # controle du moteur
    t16 = DM.trades_zone(z, "2000-01-01", "2026-10-16")
    t19 = DM.trades_zone(z, "2000-01-01", "2026-10-19")
    bon = len(t16) == 3571 and abs(t16["points"].sum() - 10759.75) < 1e-6
    L.append(f"\nControle du moteur de la zone (avant tout gain) : jusqu'au 16 octobre 2026 {len(t16)} trades "
             f"{t16['points'].sum():+.2f} points ; reference 3571 trades +10759.75 -> {'identique' if bon else 'ECART'}")
    L.append(f"  jusqu'au 19 octobre : {len(t19)} trades {t19['points'].sum():+.2f} points (README : 3 572 et +10 721,25 ; "
             f"le 19 octobre vaut ici {t19['points'].sum() - t16['points'].sum():+.2f} contre -38,50 : barre de 11 h 30 "
             "retelechargee par le robot le 20 octobre, deja note par delta_mesures/ et pistes/)")
    if not bon:
        L.append("ARRET : moteur de la zone en ecart.")
        return L, False
    # regard vers le futur
    idx_e = [i for i in z["jouables"] if pd.Timestamp(EXPLO[0]) <= z["jours"][i] <= pd.Timestamp(DM.FIN)]
    ess, err = regard_zone(z, np.array(idx_e), rng_regard)
    L.append(f"\nRegard vers le futur, zone : {ess} essais (300 seances x 12 controles), prix, VWAP et sigma brouilles "
             f"apres le controle : {err} decisions changees -> {'aucun regard vers le futur' if err == 0 else 'PROBLEME'}")
    L.append("  Les filtres A1 / A2 ne dependent que du calendrier ; A3 du calendrier et de l'ouverture de 9 h 30 (g de la "
             "nuit, connu avant le controle de 10 h).")
    rc = regard_calendrier(D["G"], D["info"], rng_regard)
    L.append("Regard vers le futur, calendrier (detection par l'ecart) : g qui suivent la decision remplaces par une "
             "permutation des g de la valeur, chaque soir 2017 - 2026 de chaque valeur")
    for nom, (soirs, reelles, perdues, nouvelles) in rc.items():
        L.append(f"  {nom:34} : {soirs} soirs, {reelles} detections ; brouillees : {perdues} detections perdues "
                 f"({perdues / max(reelles, 1) * 100:.1f} %), {nouvelles} nouvelles -> "
                 f"{'aucun regard vers le futur' if perdues + nouvelles == 0 else 'REGARD VERS LE FUTUR (attendu, README)'}")
    L.append("  -> la detection decide avec la reaction d'apres la seance (A1, A2) et avec les 29 a 30 seances suivantes "
             "(A1, A2, A3) : piste DESCRIPTIVE.")

    # controle a)
    L.append("\nCONTROLE a) accord Yahoo / detection : impossible (pas de calendrier Yahoo) ; part des trimestres combles "
             "par la detection : 100 %.")
    L.append("  valeur  detections  dates gardees (1 par trimestre)  trimestres a 2 detections  nuits de split retirees")
    for v in VALEURS:
        f = D["info"][v]
        L.append(f"  {v:6} {f['detections']:11d} {f['retenues']:12d} {f['doubles']:30d}   "
                 f"{', '.join(str(d) for d in f['splits']) or '-'}")
    tot = sum(D["info"][v]["retenues"] for v in VALEURS)
    trims = len(pd.period_range("2016Q1", "2026Q3", freq="Q"))
    L.append(f"  {tot} dates sur {10 * trims} trimestres-valeurs 2016T1 - 2026T3 ({tot / (10 * trims) * 100:.0f} %) ; "
             "aucune detection en 2016 (il faut 250 seances de mediane).")
    # controle b)
    L.append("\nCONTROLE b) jours E, E lourds et I par an (seances jouables du NQ ; aucun gain) ; jours E de la Fed")
    ans = range(2016, 2027)
    sE = pd.Series(sorted(D["E"]))
    L.append("  annee :      " + " ".join(f"{y:5d}" for y in ans))
    for nom, s in (("jours E", D["E"]), ("E lourds", D["lourd"]), ("jours I", set(D["I"])),
                   ("E et Fed", D["E"] & fed), ("I et E", set(D["I"]) & D["E"])):
        c = pd.Series([d.year for d in s]).value_counts()
        L.append(f"  {nom:12} " + " ".join(f"{int(c.get(y, 0)):5d}" for y in ans))
    hors = sum(1 for d in D["pubs"] if d not in D["jouables"])
    L.append(f"  soirs de publication hors seances jouables du NQ (pas des jours E) : {hors} ; jours I dont la seance "
             f"precedente du NQ differe de celle des valeurs : {D['desaccord_prec']}")
    L.append(f"  jours E sur toute la periode : {len(sE)} ; README : environ 33 par an, 18 lourds, 25 a 30 jours I.")

    # tests, exploration
    resultats = {}
    zone_e = per(D["zone"], *EXPLO)
    L.append("\n" + "=" * 100)
    L.append(f"EXPLORATION {EXPLO[0]} - {EXPLO[1]} : {len(zone_e)} seances jouables ; zone seule {zone_e.sum():+,.0f} $, "
             f"Sharpe {PA.sharpe(zone_e.to_numpy()):+.3f}")
    plac = {}
    for k in TESTS:
        de = per(D["delta"][k], *EXPLO)
        dp = per(D["delta_pts"][k], *EXPLO)
        x = D["tr"][D["retire"][k]]
        xe = x[(x["jour"] >= pd.Timestamp(EXPLO[0])) & (x["jour"] <= pd.Timestamp(EXPLO[1]))]
        jours_k = {"A1": D["E"], "A2": D["lourd"], "A3": set(D["I"])}[k]
        nj = sum(1 for d in jours_k if pd.Timestamp(EXPLO[0]) <= d <= pd.Timestamp(EXPLO[1]) and d not in fed)
        te = PA.t_stat(de.to_numpy())
        shz, shr = PA.sharpe(zone_e.to_numpy()), PA.sharpe((zone_e + de).to_numpy())
        L.append("")
        L.append(f"=== {NOMS[k]} (unilateral) ===")
        nfed = sum(1 for d in jours_k if pd.Timestamp(EXPLO[0]) <= d <= pd.Timestamp(EXPLO[1]) and d in fed)
        L.append(f"  jours actifs hors Fed : {nj} (et {nfed} jours de la Fed, difference nulle) ; trades retires : {len(xe)} (sur {int(((D['tr']['jour'] >= pd.Timestamp(EXPLO[0])) & (D['tr']['jour'] <= pd.Timestamp(EXPLO[1]))).sum())}) ;"
                 f" gain des trades retires {xe['usd'].sum():+,.0f} $ ({xe['usd'].mean() if len(xe) else 0:+.1f} $ par trade)")
        L.append(f"  Delta = regle - zone seule : {de.sum():+,.0f} $ ({dp.sum():+.2f} points nets non ajustes), t net "
                 f"{te:+.2f}, p unilateral {PA.p_unilateral(te):.4f}")
        L.append(f"  1) t net >= 2 : {'oui' if te >= 2 else 'non'} (Benjamini-Hochberg : sur les 11 tests de la vague)")
        L.append(f"  4) Sharpe exploration : zone seule {shz:+.3f}, regle {shr:+.3f} -> {'oui' if shr > shz else 'non'} "
                 "(coffre plus bas)")
        if k in ("A1", "A2"):
            tp, Sp, tires, manque = placebo_E(D, D["E"] if k == "A1" else D["lourd"], *EXPLO, rng)
            plac[k] = tires
        else:
            tp, Sp, manque = placebo_I(D, *EXPLO, rng)
        part = (tp < te).mean() * 100
        L.append(f"  3) placebo ({PLACEBOS} tirages, {'meme mois, ni E ni Fed' if k != 'A3' else 'meme annee, meme quintile de l ecart d ouverture du NQ, d = signe de l ecart'}) : "
                 f"t reel {te:+.2f}, placebos mediane {np.median(tp):+.2f}, 95e centile {np.quantile(tp, 0.95):+.2f} ; "
                 f"fait mieux que {part:.1f} % -> {'oui' if part >= 95 else 'non'}"
                 f"{f' ({manque} cases tirees avec remise faute de candidats)' if manque else ''}")
        L.append(f"     information : somme reelle {de.sum():+,.0f} $ ; placebos mediane {np.median(Sp):+,.0f} $ ; "
                 f"place de la somme {(Sp < de.sum()).mean() * 100:.1f} %")
        resultats[k] = dict(te=te, c1=te >= 2, c3=part >= 95, part=part, shz_e=shz, shr_e=shr)
        # controle c) sous-periodes d'exploration, par valeur, par heure, achats / ventes
        for nom, a, b in SOUS:
            s = per(D["delta"][k], a, b)
            L.append(f"  c) {nom} : Delta {s.sum():+,.0f} $, t {PA.t_stat(s.to_numpy()):+.2f}")
        L.extend(detail_c(D, k, *EXPLO))
    # controle d) mecanisme
    L.extend(mecanisme(D, plac["A1"]))
    # controle e) A3
    L.extend(controle_e(D, *EXPLO))
    # controle f) ES
    es = zone_es(D)
    D["es"] = es
    L.append(f"\nCONTROLE f) ES en replication (MES, {COUT_ES} point, memes jours ; minutes ES jusqu'au {es['fin'].date()}), "
             "exploration, information")
    ze = per(es["zone"], *EXPLO)
    for k in TESTS:
        s = per(es["delta"][k], *EXPLO)
        L.append(f"  {k} : Delta {s.sum():+,.0f} $ (1 MES), t {PA.t_stat(s.to_numpy()):+.2f} ; Sharpe zone ES "
                 f"{PA.sharpe(ze.to_numpy()):+.3f} -> regle {PA.sharpe((ze + s).to_numpy()):+.3f}")
    D["res"] = resultats
    return L, True


def detail_c(D, k, a, b):
    L = []
    tr = D["tr"]
    x = tr[D["retire"][k]]
    x = x[(x["jour"] >= pd.Timestamp(a)) & (x["jour"] <= pd.Timestamp(b))]
    cal = per(D["zone"], a, b).index
    if k == "A3":
        par_v = {v: {d for d, q in D["detail_I"].items() if v in q} for v in SIX}
    else:
        jj = D["E"] if k == "A1" else D["lourd"]
        par_v = {v: {d for d in jj if v in D["pubs"][d]} for v in (VALEURS if k == "A1" else VALEURS)}
    morceaux = []
    for v, js in par_v.items():
        s = per(D["delta"][k], a, b)
        s = s.where(s.index.isin(list(js)), 0.0)
        nj = int(s.index.isin(list(js)).sum())
        morceaux.append(f"{v} {nj} j {s.sum():+,.0f} $ (t {PA.t_stat(s.to_numpy()):+.2f})")
    L.append(f"  c) par valeur ({a[:4]} - {b[:4]}, jours partages comptes pour chaque valeur) : " + " ; ".join(morceaux))
    h = x.groupby("minute_entree")["usd"].agg(["size", "mean", "sum"])
    L.append(f"  c) trades retires par heure d'entree : " + " ; ".join(
        f"{heure(int(m))} {int(r['size'])} tr {r['mean']:+.0f} $" for m, r in h.iterrows()))
    for sens, nom in ((1, "achats"), (-1, "ventes")):
        y = x[x["sens"] == sens]
        s = -y.groupby("jour")["usd"].sum().reindex(cal).fillna(0.0)
        L.append(f"  c) {nom} retires : {len(y)} trades, gain moyen {y['usd'].mean() if len(y) else 0:+.1f} $, Delta "
                 f"{s.sum():+,.0f} $, t {PA.t_stat(s.to_numpy()):+.2f}")
    return L


def mecanisme(D, tires):
    """Controle d) : amplitude 10 h - 15 h 59 / (sigma de 15 h 59 x ouverture) les jours E et les jours placebo."""
    z, idx = D["z"], D["idx"]
    cal = per(D["zone"], *EXPLO)

    def ampl(j):
        i = idx[j]
        hh, ll = D["Hm"][i, PAS:N].max(), D["Lm"][i, PAS:N].min()
        return (hh - ll) / (z["sigma"][i, N - 1] * D["O"][i, 0])

    a_cal = np.array([ampl(j) for j in cal.index])
    estE = cal.index.isin(list(D["E"])) & ~cal.index.isin(list(D["fed"]))
    pool = np.concatenate(tires)
    L = ["\nCONTROLE d) mecanisme, exploration : amplitude (plus haut - plus bas de 10 h a 15 h 59) / (sigma de 15 h 59 x "
         "ouverture du jour)"]
    L.append(f"  jours E (hors Fed) : {estE.sum()} jours, moyenne {a_cal[estE].mean():.3f}, mediane "
             f"{np.median(a_cal[estE]):.3f} ; jours placebo (1 000 tirages de A1) : moyenne {a_cal[pool].mean():.3f}, "
             f"mediane {np.median(a_cal[pool]):.3f} ; autres jours : moyenne {a_cal[~estE].mean():.3f}")
    zE = cal[estE]
    trE = D["tr"][D["tr"]["jour"].isin(zE.index)]
    trA = D["tr"][D["tr"]["jour"].isin(cal.index[~estE])]
    L.append(f"  gain de la zone : jours E {zE.mean():+.1f} $ par seance ({len(trE)} trades, {trE['usd'].mean():+.1f} $ "
             f"par trade) ; autres seances {cal[~estE].mean():+.1f} $ ({len(trA)} trades, {trA['usd'].mean():+.1f} $ "
             f"par trade) ; jours placebo {cal.to_numpy()[pool].mean():+.1f} $ par seance")
    return L


def controle_e(D, a, b):
    tr = D["tr"]
    L = [f"\nCONTROLE e) A3, {a[:4]} - {b[:4]} : trades pris contre d (retires) et dans le sens de d"]
    x = tr[(tr["jour"] >= pd.Timestamp(a)) & (tr["jour"] <= pd.Timestamp(b))]
    dI = x["jour"].map(D["I"]).fillna(0).to_numpy()
    contre = x[(dI != 0) & (x["sens"].to_numpy() != dI)]
    avec = x[(dI != 0) & (x["sens"].to_numpy() == dI)]
    for nom, y in (("contre d (retires)", contre), ("dans le sens de d", avec)):
        u = y["usd"].to_numpy()
        L.append(f"  {nom:20} : {len(y)} trades, gain moyen {u.mean() if len(u) else 0:+.1f} $, t des trades "
                 f"{PA.t_stat(u) if len(u) > 1 else 0:+.2f}")
    gmax = {d: max(abs(v) for v in q.values()) for d, q in D["detail_I"].items()}
    for nom, f in (("|g| de 2 a 5 %", lambda g: g <= 0.05), ("|g| > 5 %", lambda g: g > 0.05)):
        js = {d for d, g in gmax.items() if f(g)}
        y = contre[contre["jour"].isin(js)]
        s = per(D["delta"]["A3"], a, b)
        s = s.where(s.index.isin(list(js)), 0.0)
        nj = int(per(D["zone"], a, b).index.isin(list(js)).sum())
        L.append(f"  {nom:15} (plus grand |g| des publiantes) : {nj} jours I, {len(y)} trades retires, gain moyen "
                 f"{y['usd'].mean() if len(y) else 0:+.1f} $, Delta {s.sum():+,.0f} $, t {PA.t_stat(s.to_numpy()):+.2f}")
    jI = [d for d in D["I"] if pd.Timestamp(a) <= d <= pd.Timestamp(b)]
    L.append(f"  jours I : {len(jI)}, dont jours E aussi : {sum(1 for d in jI if d in D['E'])} ; d = +1 : "
             f"{sum(1 for d in jI if D['I'][d] > 0)}, d = -1 : {sum(1 for d in jI if D['I'][d] < 0)}")
    return L


def ecrire_coffre(D, rng):
    L = [MARQUE]
    fed = D["fed"]
    res = D["res"]
    # controle du moteur des challenges
    z = D["z"]
    ch_v1 = chemins(z, D["Hm"], D["Lm"], D["tr"])
    ch_pd = PD.chemins_zone()
    bon_ch = ch_v1[0].equals(ch_pd[0]) and all(np.abs(a_ - b_).max() < 1e-6 for a_, b_ in zip(ch_v1[1:], ch_pd[1:]))
    base = {(LUCID, 1): defis(ch_v1, LUCID, 1), (BULENOX, 3): defis(ch_v1, BULENOX, 3),
            (BULENOX, "4-6"): defis(ch_v1, BULENOX, 4, 6, 5)}
    vu = [(base[(BULENOX, 3)]["n"], round(base[(BULENOX, 3)]["valide"]), round(base[(BULENOX, 3)]["perdu"])),
          (base[(BULENOX, "4-6")]["n"], round(base[(BULENOX, "4-6")]["valide"]), round(base[(BULENOX, "4-6")]["perdu"])),
          (base[(LUCID, 1)]["n"], round(base[(LUCID, 1)]["valide"]), round(base[(LUCID, 1)]["perdu"]))]
    att = [(908, 45, 31), (908, 50, 45), (804, 55, 35)]
    L.append(f"Controle du moteur des challenges : chemins recopies = partie_d.chemins_zone : {'oui' if bon_ch else 'NON'} ;"
             f" zone seule, departs 2023 - 2026 : Bulenox 3 MNQ {vu[0]}, 4 puis 6 MNQ {vu[1]}, Lucid 1 MNQ {vu[2]} "
             f"(departs, valide %, perdu %) ; partie D {att} -> {'identique' if vu == att and bon_ch else 'ECART'}")
    synthese = []
    for k in TESTS:
        CO = COFFRE_A3 if k == "A3" else COFFRE
        zc = per(D["zone"], *CO)
        dc = per(D["delta"][k], *CO)
        dpc = per(D["delta_pts"][k], *CO)
        tc = PA.t_stat(dc.to_numpy())
        te = res[k]["te"]
        x = D["tr"][D["retire"][k]]
        xc = x[(x["jour"] >= pd.Timestamp(CO[0])) & (x["jour"] <= pd.Timestamp(CO[1]))]
        L.append("")
        L.append(f"=== {NOMS[k]} : coffre {CO[0]} - {CO[1]} ({len(zc)} seances) ===")
        L.append(f"  trades retires : {len(xc)}, gain {xc['usd'].sum():+,.0f} $ ; Delta {dc.sum():+,.0f} $ "
                 f"({dpc.sum():+.2f} points nets non ajustes), t net {tc:+.2f}")
        c2 = np.sign(tc) == np.sign(te) and tc >= 1.5
        shz, shr = PA.sharpe(zc.to_numpy()), PA.sharpe((zc + dc).to_numpy())
        c4 = res[k]["shr_e"] > res[k]["shz_e"] and shr > shz
        L.append(f"  2) coffre meme signe, t >= 1,5 : {'oui' if c2 else 'non'} (exploration {te:+.2f}, coffre {tc:+.2f})")
        L.append(f"  4) Sharpe zone seule / regle : exploration {res[k]['shz_e']:+.3f} / {res[k]['shr_e']:+.3f}, coffre "
                 f"{shz:+.3f} / {shr:+.3f} -> {'oui' if c4 else 'non'}")
        # placebo au coffre, information
        if k in ("A1", "A2"):
            tp, Sp, _, _ = placebo_E(D, D["E"] if k == "A1" else D["lourd"], *CO, rng)
        else:
            tp, Sp, _ = placebo_I(D, *CO, rng)
        L.append(f"     information, meme placebo au coffre : t reel {tc:+.2f} fait mieux que {(tp < tc).mean() * 100:.1f} % "
                 f"(95e centile {np.quantile(tp, 0.95):+.2f})")
        # challenges
        if k == "A3":
            tr_r = D["tr"][~D["retire"]["A3"]]
            ch_r = chemins(z, D["Hm"], D["Lm"], tr_r)
        else:
            garde = ~D["retire"][k]
            ch_r = chemins(z, D["Hm"], D["Lm"], D["tr"][garde])
        r_l, r_b, r_b46 = defis(ch_r, LUCID, 1), defis(ch_r, BULENOX, 3), defis(ch_r, BULENOX, 4, 6, 5)
        passe = {}
        for nom, r, b in (("Lucid Flex 50K, 1 MNQ", r_l, base[(LUCID, 1)]), ("Bulenox 50K, 3 MNQ", r_b, base[(BULENOX, 3)])):
            dv, dp = r["valide"] - b["valide"], r["perdu"] - b["perdu"]
            passe[nom] = dv >= 2.0 and dp <= 3.0
            L.append(f"  5) {nom} ({r['n']} departs 2023 - 2026) : zone seule valide {b['valide']:.1f} % perdu "
                     f"{b['perdu']:.1f} % ; regle valide {r['valide']:.1f} % perdu {r['perdu']:.1f} % -> {dv:+.1f} points "
                     f"valides, {dp:+.1f} perdus -> {'passe' if passe[nom] else 'ne passe pas'}")
        b46 = base[(BULENOX, "4-6")]
        L.append(f"     information, Bulenox 4 puis 6 MNQ (version 30 jours) : zone seule {b46['valide']:.1f} / "
                 f"{b46['perdu']:.1f} % ; regle {r_b46['valide']:.1f} / {r_b46['perdu']:.1f} %")
        c5 = any(passe.values())
        L.append(f"     -> critere 5 : {'oui (' + ', '.join(n for n, p in passe.items() if p) + ')' if c5 else 'non'}")
        for nom, a, b in SOUS_COFFRE:
            s = per(D["delta"][k], a, b)
            L.append(f"  c) {nom} : Delta {s.sum():+,.0f} $, t {PA.t_stat(s.to_numpy()):+.2f}")
        L.extend(detail_c(D, k, *CO))
        if k == "A3":
            L.extend(controle_e(D, *CO))
        es = D["es"]
        ce = (CO[0], min(CO[1], str(es["fin"].date())))
        s = per(es["delta"][k], *ce)
        ze = per(es["zone"], *ce)
        L.append(f"  f) ES (MES), {ce[0]} - {ce[1]} : Delta {s.sum():+,.0f} $, t {PA.t_stat(s.to_numpy()):+.2f} ; Sharpe "
                 f"zone ES {PA.sharpe(ze.to_numpy()):+.3f} -> regle {PA.sharpe((ze + s).to_numpy()):+.3f}")
        tous = res[k]["c1"] and c2 and res[k]["c3"] and c4 and c5
        synthese.append(dict(k=k, te=te, tc=tc, c1=res[k]["c1"], c2=c2, c3=res[k]["c3"], part=res[k]["part"], c4=c4,
                             c5=c5, passe=passe, tous=tous, shz=(res[k]["shz_e"], shz), shr=(res[k]["shr_e"], shr)))
    # E3 information
    jours, clo, bas, haut = ch_v1
    m = jours.isin(list(D["E"]))
    ch_e3 = (jours, clo * np.where(m, 0.2, 1.0)[:, None], bas * np.where(m, 0.2, 1.0)[:, None],
             haut * np.where(m, 0.2, 1.0)[:, None])
    e3l, e3b, e3b46 = defis(ch_e3, LUCID, 1), defis(ch_e3, BULENOX, 3), defis(ch_e3, BULENOX, 4, 6, 5)
    L.append("\nE3 (information, README : « difference = 0,8 x celle de E1 jour par jour » : zone a 0,2 x sa taille les jours "
             "E) :")
    L.append(f"  Lucid 1 MNQ : valide {e3l['valide']:.1f} % perdu {e3l['perdu']:.1f} % ; Bulenox 3 MNQ : {e3b['valide']:.1f} / "
             f"{e3b['perdu']:.1f} % ; Bulenox 4 puis 6 : {e3b46['valide']:.1f} / {e3b46['perdu']:.1f} %")
    # synthese
    L.append("\n" + "=" * 100)
    L.append("SYNTHESE (Benjamini-Hochberg a 10 % sur les 11 tests de la vague : calcule ensuite ; p unilateral du t "
             "d'exploration)")
    for s in synthese:
        L.append(f"  {s['k']} : t exploration {s['te']:+.2f} (p {PA.p_unilateral(s['te']):.4f}), t coffre {s['tc']:+.2f} ; "
                 f"1 t>=2 {'oui' if s['c1'] else 'non'} ; 2 coffre {'oui' if s['c2'] else 'non'} ; 3 placebo "
                 f"{'oui' if s['c3'] else 'non'} ({s['part']:.1f} %) ; 4 Sharpe {'oui' if s['c4'] else 'non'} ; 5 "
                 f"challenges {'oui' if s['c5'] else 'non'} ; criteres chiffres hors BH : {'tous' if s['tous'] else 'non'}")
    L.append("DECISION : " + ("aucune regle retenue. Calendrier Yahoo absent : la piste A est DESCRIPTIVE (regard vers le "
                              "futur de la detection par l'ecart, README)." if not D["avec_yahoo"] else
                              "selon les criteres ci-dessus et Benjamini-Hochberg sur la vague."))
    D["synthese"] = synthese
    return L


def main():
    coffre = len(sys.argv) > 1 and sys.argv[1] == "coffre"
    rng = np.random.default_rng(GRAINE)
    rng_regard = np.random.default_rng(GRAINE + 1000)
    D = construire()
    L, ok = ecrire_exploration(D, rng, rng_regard)
    texte = "\n".join(L) + "\n"
    f = ICI / "resultats.txt"
    if not coffre:
        f.write_text(texte)
        print(texte)
        return
    deja = f.read_text()
    if not deja.startswith(texte):
        print("ARRET : l'exploration recalculee differe de celle deja ecrite dans resultats.txt ; coffre non ouvert.")
        sys.exit(1)
    if MARQUE in deja:
        print("ARRET : le coffre a deja ete ouvert (resultats.txt le contient).")
        sys.exit(1)
    if not ok:
        sys.exit(1)
    C = ecrire_coffre(D, rng)
    f.write_text(texte + "\n".join(C) + "\n")
    print("\n".join(C))


if __name__ == "__main__":
    main()
