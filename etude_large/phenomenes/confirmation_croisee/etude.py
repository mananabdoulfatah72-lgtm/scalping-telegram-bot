#!/usr/bin/env python3
"""etude_large/phenomenes/README.md, piste B (regles fixees le 22 octobre 2026, commit 929d05e, avant tout calcul) :
le mouvement simultane des autres marches au controle de la zone. Au controle tau (10 h 00 ... 15 h 30) ou V1 entre dans
le sens s, rendement de 30 minutes de chaque marche X (VXX, UUP, AUD/JPY HistData, bitcoin Coinbase, TLT), regression
sur les 720 fenetres (12 controles x 60 seances completes precedentes, au moins 300 presentes) contre le rendement du
NQ, z residuel et z brut ; seuil q = 20e centile du score des entrees de V1 des 252 seances completes precedentes (-0,84
tant qu'il y en a moins de 100) ; le trade est ecarte (virtuel et bloquant) si score <= q, garde si le score n'existe pas.
B1 indice d'appetit pour le risque (au moins 3 marches) ; B2 AUD/JPY residuel ; B3 VXX residuel ; B4 TLT brut au signe du
regime. 4 tests unilateraux (Delta = zone filtree - V1 > 0). Placebo de 200 tirages (meme controle, autre seance de la
meme annee), jumeau NQ (score = s r_NQ / ecart-type de r_NQ), criteres communs 1 a 5 (precision de la zone).

Lancer : KB=<branche de recherche extraite> python3 etude_large/phenomenes/confirmation_croisee/etude.py.
Ecrit resultats.txt : l'exploration d'abord (fichier ecrit et ferme), puis le coffre, ouvert une seule fois.
CONFIRMATION_PHASE=exploration : s'arrete apres l'exploration. CONFIRMATION_ESSAI=1 : essai du code du coffre sur
2021-2022 (donnees d'exploration seulement), ecrit dans un fichier du dossier temporaire, jamais dans resultats.txt."""
import os
import sys
import tempfile
from pathlib import Path
from zoneinfo import ZoneInfo

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_confirmation_croisee"))

ICI = Path(__file__).resolve().parent
RACINE = ICI.parent.parent.parent
sys.path = [p for p in sys.path if Path(p or ".").resolve() != ICI]       # ce fichier s'appelle aussi etude.py
sys.path.insert(0, str(RACINE / "delta_mesures"))
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import etude as DM  # noqa: E402
sys.path.insert(0, str(RACINE / "etude_large"))
import partie_d as PD  # noqa: E402
import partie_a as PA  # noqa: E402
sys.path.insert(0, str(DM.KB / "fonds"))
import fomc  # noqa: E402

RB = DM.RB
N, PAS, COUT = DM.N, DM.PAS, DM.COUT
K = 12                                        # controles 10 h 00, 10 h 30 ... 15 h 30
TAU = [600 + 30 * k for k in range(K)]         # minute du jour (New York) du controle k
POINTS = [570] + TAU                           # 9 h 30, 10 h 00 ... 15 h 30 : r du controle k = points k -> k + 1
FEN, MIN_FEN = 60, 300                         # seances de reference, fenetres presentes au minimum
HIST, MIN_HIST, CENTILE, Q_DEFAUT = 252, 100, 20.0, -0.84
RHO_MIN = 0.10
PLACEBOS = 200
MIN_PAIRES = 20                                # controle d'heure : rendements de 5 minutes presents au minimum
ETF = RACINE / "donnees_libres" / "etf_5min"
HD = DM.KB / "sessions24" / "annees"
CRYPTO = RACINE / "donnees_libres" / "crypto"
T5 = DM.KB / "tournoi5" / "donnees"
ES = DM.KB / "intraday" / "donnees" / "sp500_1min.csv.gz"
NY = ZoneInfo("America/New_York")
COUT_ES = 0.9
LUCID, BULENOX = "Lucid Flex 50K", "Bulenox Legacy 50K opt. 2"
SLOT0, NSLOT = 480, 108                        # grille de 5 minutes : barres etiquetees 8 h 00 ... 16 h 55
DEBUT_VXX = pd.Timestamp("2019-01-02")
TESTS = ["B1", "B2", "B3", "B4"]
NOMS = {"B1": "indice d'appetit pour le risque (VXX, UUP, AUD/JPY, bitcoin, TLT ; residus)",
        "B2": "AUD/JPY residuel", "B3": "VXX residuel", "B4": "TLT brut au signe du regime"}
DEBUTS = {"B1": "2016-01-04", "B2": "2012-01-02", "B3": "2019-01-02", "B4": "2016-01-04"}   # avant la 61e seance
FIN_EXPLO, DEBUT_COFFRE = "2022-12-30", "2023-01-03"
FINS = {"B1": DM.FIN, "B2": "2026-10-02", "B3": DM.FIN, "B4": DM.FIN}
SIGNES = {"VXX": -1.0, "UUP": -1.0, "AUDJPY": 1.0, "BTC": 1.0}
PHASE = os.getenv("CONFIRMATION_PHASE", "tout")
ESSAI = os.getenv("CONFIRMATION_ESSAI") == "1"
if ESSAI:                                      # essai du code du coffre sur des donnees d'exploration seulement
    FIN_EXPLO, DEBUT_COFFRE = "2020-12-31", "2021-01-04"
    FINS = {t: "2022-12-30" for t in TESTS}
    DEPARTS = ("2021-01-01", "2022-06-30")
    SORTIE = Path(tempfile.gettempdir()) / "confirmation_croisee_essai.txt"
else:
    DEPARTS = (PD.DEBUT_VERIF, None)
    SORTIE = ICI / "resultats.txt"


def heure(m):
    return DM.heure(m)


def f2(x):
    return f"{x:+.2f}"


# ----------------------------------------------------------------------------- donnees des autres marches
def lire_etf(nom):
    d = pd.read_csv(ETF / f"{nom}.csv.gz", usecols=["t", "o", "c"])
    return pd.to_datetime(d["t"]), d["o"].to_numpy(float), d["c"].to_numpy(float)


def lire_histdata(nom):
    d = pd.concat([pd.read_csv(f) for f in sorted(HD.glob(f"{nom}_*_5m.csv.gz"))], ignore_index=True)
    t = pd.to_datetime(d["t"]).dt.tz_localize("UTC").dt.tz_convert(NY).dt.tz_localize(None)
    return t, d["o"].to_numpy(float), d["c"].to_numpy(float)


def lire_btc():
    d = pd.concat([pd.read_csv(f, usecols=["t", "o", "c"]) for f in sorted(CRYPTO.glob("btc_*_5m.csv.gz"))],
                  ignore_index=True)
    return pd.to_datetime(d["t"]), d["o"].to_numpy(float), d["c"].to_numpy(float)


def grille(brut, jours):
    """Barres de 5 minutes (debut de barre, heure de New York) -> (ouvertures, clotures) : seances x 108 cases (8 h 00 ...
    16 h 55), NaN quand la barre manque."""
    t, o, c = brut
    mod = (t.dt.hour * 60 + t.dt.minute).to_numpy()
    ij = jours.get_indexer(t.dt.normalize())
    sel = (ij >= 0) & (mod >= SLOT0) & (mod < SLOT0 + 5 * NSLOT) & (mod % 5 == 0)
    Og, Cg = np.full((len(jours), NSLOT), np.nan), np.full((len(jours), NSLOT), np.nan)
    s = (mod[sel] - SLOT0) // 5
    Og[ij[sel], s] = o[sel]
    Cg[ij[sel], s] = c[sel]
    return Og, Cg


def prix_a(g, u):
    """P_X(u) : cloture de la barre qui finit a u (etiquetee u - 5) ; a 9 h 30, ouverture de la barre de 9 h 30. Si elle
    manque : cloture de la derniere barre disponible si elle finit au plus 10 minutes avant u, sinon absent (NaN)."""
    Og, Cg = g
    if u == 570:
        p, repli = Og[:, (570 - SLOT0) // 5].copy(), [(565 - SLOT0) // 5, (560 - SLOT0) // 5, (555 - SLOT0) // 5]
    else:
        s1 = (u - 5 - SLOT0) // 5
        p, repli = Cg[:, s1].copy(), [s1 - 1, s1 - 2]
    for s in repli:
        p = np.where(np.isnan(p), Cg[:, s], p)
    return p


def prix_nq(O0, C, u):
    """P_NQ(u) : cloture de la minute etiquetee u - 1 ; a 9 h 30, ouverture de la minute de 9 h 30."""
    return O0.copy() if u == 570 else C[:, u - 570 - 1]


def rendements(lp):
    """lp : (seances, 13) logarithmes des prix aux points 9 h 30, 10 h 00 ... 15 h 30 -> r des 12 controles."""
    return lp[:, 1:] - lp[:, :-1]


def correlation_lignes(a, b, nmin):
    m = ~np.isnan(a) & ~np.isnan(b)
    n = m.sum(1)
    a0, b0 = np.where(m, a, 0.0), np.where(m, b, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        ma, mb = a0.sum(1) / n, b0.sum(1) / n
        da, db = np.where(m, a - ma[:, None], 0.0), np.where(m, b - mb[:, None], 0.0)
        r = (da * db).sum(1) / np.sqrt((da * da).sum(1) * (db * db).sum(1))
    r[n < nmin] = np.nan
    return r


def controle_heure(O0, C, gtech, complete):
    """Pour chaque seance : delta in {-60, 0, +60} minutes qui maximise la correlation des 78 rendements de 5 minutes
    (9 h 30 - 16 h) de usatechidxusd avec ceux du NQ, sur la seance complete precedente. HistData present ce jour-la si
    delta = 0. Renvoie (present, correlations de chaque seance (seances x 3))."""
    T = list(range(570, 961, 5))
    rnq = np.diff(np.log(np.column_stack([prix_nq(O0, C, u) for u in T])), axis=1)
    cor = np.column_stack([correlation_lignes(np.diff(np.log(np.column_stack([prix_a(gtech, u + dl) for u in T])), axis=1),
                                              rnq, MIN_PAIRES) for dl in (-60, 0, 60)])
    autre = np.fmax(np.where(np.isnan(cor[:, 0]), -np.inf, cor[:, 0]), np.where(np.isnan(cor[:, 2]), -np.inf, cor[:, 2]))
    ok_jour = ~np.isnan(cor[:, 1]) & (cor[:, 1] >= autre)
    prec = RB.precedente(complete)
    present = np.where(prec >= 0, ok_jour[np.maximum(prec, 0)], False)
    return present, cor


def marches_r(jours, g, O0, C, complete):
    """r_X (seances x 12) de chaque marche, NaN si absent ; HistData absent les jours ou le controle d'heure echoue ;
    VXX seulement a partir du 2 janvier 2019."""
    hist_ok, cor = controle_heure(O0, C, g["TECH"], complete)
    lp = {nom: np.log(np.column_stack([prix_a(g[nom], u) for u in POINTS])) for nom in ("VXX", "UUP", "TLT", "IEF", "BTC")}
    lp["AUDJPY"] = np.log(np.column_stack([prix_a(g["AUD"], u) for u in POINTS])) + \
        np.log(np.column_stack([prix_a(g["JPY"], u) for u in POINTS]))
    r = {nom: rendements(v) for nom, v in lp.items()}
    r["AUDJPY"][~hist_ok] = np.nan
    r["VXX"][np.asarray(jours < DEBUT_VXX)] = np.nan
    return r, hist_ok, cor


def regression(x, y):
    """Sur les seances completes (lignes) : fenetres des 60 seances precedentes x 12 controles ou y est present ; au
    moins 300. Renvoie z residuel, z brut (seances x 12), rho, beta, nombre de fenetres."""
    nc = x.shape[0]
    M = ~np.isnan(y)
    x0, y0 = np.where(M, x, 0.0), np.where(M, y, 0.0)
    lignes = np.column_stack([M.sum(1), x0.sum(1), y0.sum(1), (x0 * x0).sum(1), (x0 * y0).sum(1), (y0 * y0).sum(1)])
    cs = np.vstack([np.zeros(6), np.cumsum(lignes, axis=0)])
    p = np.arange(nc)
    W = cs[p] - cs[np.maximum(p - FEN, 0)]
    n, Sx, Sy, Sxx, Sxy, Syy = W.T
    ok = n >= MIN_FEN
    with np.errstate(invalid="ignore", divide="ignore"):
        mx, my = Sx / n, Sy / n
        cxx, cxy, cyy = Sxx - n * mx * mx, Sxy - n * mx * my, Syy - n * my * my
        beta = cxy / cxx
        a = my - beta * mx
        sde = np.sqrt((cyy - beta * cxy) / (n - 1))
        sdy = np.sqrt(cyy / (n - 1))
        rho = cxy / np.sqrt(cxx * cyy)
        zr = (y - a[:, None] - beta[:, None] * x) / sde[:, None]
        zb = y / sdy[:, None]
    zr[~ok], zb[~ok] = np.nan, np.nan
    rho, beta = np.where(ok, rho, np.nan), np.where(ok, beta, np.nan)
    return dict(zr=zr, zb=zb, rho=rho, beta=beta, n=n)


def ecart_type_nq(x):
    """Ecart-type de r_NQ sur les 720 fenetres (60 seances completes precedentes x 12 controles), pour le jumeau NQ."""
    nc = x.shape[0]
    cs = np.vstack([np.zeros(3), np.cumsum(np.column_stack([np.full(nc, K), x.sum(1), (x * x).sum(1)]), axis=0)])
    p = np.arange(nc)
    n, Sx, Sxx = (cs[p] - cs[np.maximum(p - FEN, 0)]).T
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.sqrt((Sxx - Sx * Sx / n) / (n - 1))


def matrices(x, rc):
    """Scores sans le sens (seances completes x 12) de chaque test et des variantes du controle c). rc : r_X sur les
    seances completes."""
    R = {nom: regression(x, y) for nom, y in rc.items()}
    rho_t = R["TLT"]["rho"]
    e_t = np.where(np.abs(rho_t) >= RHO_MIN, np.sign(rho_t), np.nan)          # NaN : TLT non compte
    termes = [SIGNES[n] * R[n]["zr"] for n in ("VXX", "UUP", "AUDJPY", "BTC")] + [e_t[:, None] * R["TLT"]["zr"]]
    T = np.stack(termes)
    nb = (~np.isnan(T)).sum(0)
    with np.errstate(invalid="ignore"):
        iar = np.where(nb >= 3, np.nansum(T, 0) / np.maximum(nb, 1), np.nan)
    rho_i = R["IEF"]["rho"]
    e_i = np.where(np.abs(rho_i) >= RHO_MIN, np.sign(rho_i), np.nan)
    U = {"B1": iar, "B2": R["AUDJPY"]["zr"], "B3": -R["VXX"]["zr"], "B4": e_t[:, None] * R["TLT"]["zb"],
         "B4 e=-1": -R["TLT"]["zb"], "B4 e=+1": R["TLT"]["zb"], "B4 IEF": e_i[:, None] * R["IEF"]["zb"]}
    sdx = ecart_type_nq(x)
    jum = x / sdx[:, None]
    for t in TESTS:
        U[f"{t} jumeau"] = np.where(np.isnan(U[t]), np.nan, jum)
    return U, R, nb


def seuils(p_ent, sc):
    """q de chaque entree : 20e centile des scores existants des entrees des 252 seances completes precedentes ; -0,84
    s'il y en a moins de 100. Entrees triees par seance."""
    q = np.full(len(p_ent), Q_DEFAUT)
    lo = np.searchsorted(p_ent, p_ent - HIST, "left")
    hi = np.searchsorted(p_ent, p_ent, "left")
    for j in range(len(p_ent)):
        v = sc[lo[j]:hi[j]]
        v = v[~np.isnan(v)]
        if len(v) >= MIN_HIST:
            q[j] = np.percentile(v, CENTILE)
    return q


def decisions(U, ent):
    """Pour chaque test (et variante) : score, seuil et trade ecarte de chaque entree de V1."""
    out = {}
    for nom, u in U.items():
        sc = ent["s"] * u[ent["p"], ent["k"]]
        q = seuils(ent["p"], sc)
        out[nom] = dict(sc=sc, q=q, ecarte=~np.isnan(sc) & (sc <= q))
    return out


def pipeline(jours, complete, O0, C, g, ent):
    """Toute la chaine, des prix aux decisions (servira aussi au brouillage du regard vers le futur)."""
    r, hist_ok, cor = marches_r(jours, g, O0, C, complete)
    comp = np.where(complete)[0]
    x = np.column_stack([np.log(prix_nq(O0, C, POINTS[k + 1]) / prix_nq(O0, C, POINTS[k])) for k in range(K)])[comp]
    rc = {nom: v[comp] for nom, v in r.items()}
    U, R, nb = matrices(x, rc)
    return dict(r=r, hist_ok=hist_ok, cor=cor, x=x, U=U, R=R, nb=nb, D=decisions(U, ent), comp=comp)


# ----------------------------------------------------------------------------- zone, series et challenges
def entrees(z, tr, complete):
    """Entrees de V1 (jours de la Fed retires), triees par seance et minute, avec leur position dans les seances
    completes, l'indice du controle et leur valeur en $ (1 MNQ, prix du 20 octobre 2026, convention de chemins_zone)."""
    pos_c = np.full(len(z["jours"]), -1)
    pos_c[np.where(complete)[0]] = np.arange(complete.sum())
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], N - 1])
    i = np.array([idx[j] for j in tr["jour"]])
    me = tr["minute_entree"].to_numpy(np.int64)
    s = tr["sens"].to_numpy(float)
    brut = s * (tr["prix_sortie"].to_numpy() - tr["prix_entree"].to_numpy())
    f = ref / z["C"][i, 0]
    assert (pos_c[i] >= 0).all() and (me % PAS == 0).all() and (me >= PAS).all() and (me <= DM.DERNIERE_ENTREE).all()
    return dict(i=i, p=pos_c[i], k=me // PAS - 1, s=s, me=me, ms=tr["minute_sortie"].to_numpy(np.int64),
                pe=tr["prix_entree"].to_numpy(), ps=tr["prix_sortie"].to_numpy(), jour=pd.DatetimeIndex(tr["jour"]),
                usd=(brut * f - COUT) * RB.PT, pts=brut - COUT)


def par_jour(ent, valeurs, ju):
    """Somme par seance de l'univers ju (0 sans trade)."""
    pos = ju.get_indexer(ent["jour"])
    out = np.zeros(len(ju))
    m = pos >= 0
    np.add.at(out, pos[m], valeurs[m])
    return out


def chemins(z, Hm, Lm, ent, garde):
    """Recopie de partie_d.chemins_zone avec les seuls trades gardes (un trade ecarte reste virtuel jusqu'a sa sortie,
    donc les autres trades sont ceux de V1) ; jours de la Fed deja absents de ent."""
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= PD.DEBUT) & (jours <= DM.FIN)]
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], N - 1])
    ch, bas, haut = (np.zeros((len(jours), N)) for _ in range(3))
    pos = {j: k for k, j in enumerate(jours)}
    par = {}
    for j in np.where(garde)[0]:
        par.setdefault(ent["jour"][j], []).append(j)
    for jour, js in par.items():
        if jour not in pos:
            continue
        i = idx[jour]
        Cc, H, L = z["C"][i], Hm[i], Lm[i]
        f = ref / Cc[0]
        c, contre, pour = np.zeros(N), np.zeros(N), np.zeros(N)
        for j in js:
            me, ms, s, pe, ps = int(ent["me"][j]), int(ent["ms"][j]), ent["s"][j], ent["pe"][j], ent["ps"][j]
            c[me:ms] += s * (Cc[me:ms] - pe) * f
            c[ms:] += s * (ps - pe) * f
            c[me:] -= COUT
            w = slice(me + 1, ms + 1)
            contre[w] += ((Cc[w] - L[w]) if s > 0 else (H[w] - Cc[w])) * f
            pour[w] += ((H[w] - Cc[w]) if s > 0 else (Cc[w] - L[w])) * f
        k = pos[jour]
        ch[k], bas[k], haut[k] = c * RB.PT, (c - contre) * RB.PT, (c + pour) * RB.PT
    return jours, ch, bas, haut


def defis(ch, firme, q, q_fin=None, n_fin=0):
    obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
    jours, clo, bas, haut = ch
    sel = jours >= pd.Timestamp(DEPARTS[0])
    if DEPARTS[1]:
        sel &= jours <= pd.Timestamp(DEPARTS[1])
    verif = np.where(sel)[0]
    lim = PD.limites_depart(jours, verif, nmax)
    ok = verif + lim < len(jours)
    iss, _ = PD.tous_les_departs(clo, bas, haut, verif[ok], lim[ok], float(q), float(q_fin or q), int(n_fin), float(obj),
                                 float(dd), float(bloc), float(dll), part, True)
    return dict(n=int(ok.sum()), valide=(iss == 1).mean() * 100, perdu=(iss == -1).mean() * 100,
                expire=(iss == 0).mean() * 100)


# ----------------------------------------------------------------------------- controles
def placebo(U, D, ent, sel, comp_jours, rng, tirages=PLACEBOS):
    """Pour chaque entree selectionnee (score reel existant) : score remplace par celui du meme controle d'une autre
    seance de la meme annee ou le score existe, compare au meme seuil q que le vrai jour. Renvoie les Delta en $."""
    js = np.where(sel & ~np.isnan(D["sc"]))[0]
    ans = comp_jours.year.to_numpy()
    tir = np.zeros((tirages, len(js)))
    for a in np.unique(ans[ent["p"][js]]):
        for k in range(K):
            g = js[(ans[ent["p"][js]] == a) & (ent["k"][js] == k)]
            if not len(g):
                continue
            pool = np.where((ans == a) & ~np.isnan(U[:, k]))[0]
            propre = np.searchsorted(pool, ent["p"][g])
            assert (pool[propre] == ent["p"][g]).all()
            r = rng.integers(0, len(pool) - 1, size=(tirages, len(g)))
            r = r + (r >= propre[None, :])
            sc = ent["s"][g][None, :] * U[pool[r], k]
            tir[:, np.searchsorted(js, g)] = sc <= D["q"][g][None, :]
    reel = -ent["usd"][js][D["ecarte"][js]].sum()
    pla = -(tir * ent["usd"][js][None, :]).sum(1)
    return reel, pla, len(js)


def regard_futur_v1(z, idx, rng, n=300):
    """V1 (herite de delta_mesures) : tout ce qui suit le controle m est brouille, les entrees jusqu'a m ne changent pas."""
    erreurs = changees = essais = 0
    for i in rng.choice(idx, size=min(n, len(idx)), replace=False):
        C, sg, vw, hr, br = z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i]
        a = DM.zone_jour(C, sg, vw, hr, br)
        for m in range(PAS, N - 1, PAS):
            C2, sg2, vw2 = C.copy(), sg.copy(), vw.copy()
            k = N - m - 1
            C2[m + 1:] = C[m] * (1 + rng.normal(0, 0.02, k))
            vw2[m + 1:] = C[m] * (1 + rng.normal(0, 0.02, k))
            sg2[m + 1:] = rng.uniform(0, 0.03, k)
            b = DM.zone_jour(C2, sg2, vw2, hr, br)
            essais += 1
            erreurs += [t[:3] for t in a if t[0] <= m] != [t[:3] for t in b if t[0] <= m]
            changees += a != b
    return essais, erreurs, changees


def regard_futur(jours, complete, O0, C, g, ent, D0, rng, n=40):
    """Brouillage de tout ce qui suit une decision du filtre (seance d0, controle tau) : minutes du NQ apres la minute du
    controle et seances suivantes, barres des autres marches qui finissent apres tau et seances suivantes (prix bruites,
    10 % des barres retirees) ; toute la chaine est recalculee. Aucune decision jusqu'a (d0, tau) ne doit changer."""
    cles = list(D0)
    candidats = np.where(~np.isnan(D0["B1"]["sc"]) | ~np.isnan(D0["B2"]["sc"]))[0]
    essais, changes, apres = 0, 0, 0
    for j0 in rng.choice(candidats, size=n, replace=False):
        d0, m0 = ent["i"][j0], ent["me"][j0]
        tau = 570 + m0
        C2, O2 = C.copy(), O0.copy()
        C2[d0, m0 + 1:] *= np.exp(rng.normal(0, 0.01, N - m0 - 1))
        C2[d0 + 1:] *= np.exp(rng.normal(0, 0.01, C2[d0 + 1:].shape))
        O2[d0 + 1:] *= np.exp(rng.normal(0, 0.01, len(O2) - d0 - 1))
        g2 = {}
        s_tau = (tau - SLOT0) // 5                  # premiere barre qui finit apres tau
        for nom, (Og, Cg) in g.items():
            O3, C3 = Og.copy(), Cg.copy()
            for A in (O3, C3):
                A[d0, s_tau:] *= np.exp(rng.normal(0, 0.01, NSLOT - s_tau))
                A[d0 + 1:] *= np.exp(rng.normal(0, 0.01, A[d0 + 1:].shape))
            trou = np.zeros_like(C3, bool)
            trou[d0, s_tau:] = rng.random(NSLOT - s_tau) < 0.1
            trou[d0 + 1:] = rng.random(trou[d0 + 1:].shape) < 0.1
            O3[trou], C3[trou] = np.nan, np.nan
            g2[nom] = (O3, C3)
        D2 = pipeline(jours, complete, O2, C2, g2, ent)["D"]
        avant = (ent["i"] < d0) | ((ent["i"] == d0) & (ent["me"] <= m0))
        for c in cles:
            a, b = D0[c], D2[c]
            same_sc = np.array_equal(np.isnan(a["sc"][avant]), np.isnan(b["sc"][avant])) and \
                np.allclose(np.nan_to_num(a["sc"][avant]), np.nan_to_num(b["sc"][avant]), rtol=0, atol=1e-12)
            same_q = np.allclose(a["q"][avant], b["q"][avant], rtol=0, atol=1e-12)
            changes += int(not (same_sc and same_q and np.array_equal(a["ecarte"][avant], b["ecarte"][avant])))
            apres += int(not np.array_equal(a["ecarte"][~avant], b["ecarte"][~avant]))
        essais += 1
    return essais, len(cles), changes, apres


def verifier_a_la_main(P, brut, g, rng, n=300):
    """Prix P_X(t) relus dans les barres brutes (sans la grille) pour des seances et des heures tirees au hasard."""
    jours = P["jours"]
    t, o, c = brut
    df = pd.DataFrame({"t": t, "o": o, "c": c}).set_index("t").sort_index()
    ecart, nb = 0.0, 0
    for _ in range(n):
        d = int(rng.integers(0, len(jours)))
        u = int(rng.choice(POINTS))
        j = jours[d]
        mine = prix_a(g, u)[d]
        if u == 570:
            b = df.loc[df.index == j + pd.Timedelta(minutes=570), "o"]
            if not len(b):
                w = df.loc[(df.index >= j + pd.Timedelta(minutes=555)) & (df.index <= j + pd.Timedelta(minutes=565)), "c"]
                b = w.iloc[-1:] if len(w) else b
        else:
            w = df.loc[(df.index >= j + pd.Timedelta(minutes=u - 15)) & (df.index <= j + pd.Timedelta(minutes=u - 5)), "c"]
            b = w.iloc[-1:]
        main = float(b.iloc[0]) if len(b) else np.nan
        if np.isnan(main) != np.isnan(mine) or (not np.isnan(main) and abs(main - mine) > 1e-9):
            ecart = np.inf
        elif not np.isnan(main):
            nb += 1
    return ecart, nb


def regression_a_la_main(x, y, rng, n=40):
    """z residuel, z brut et rho recalcules par moindres carres sur les fenetres explicites (60 seances precedentes)."""
    R = regression(x, y)
    ok = np.where(R["n"] >= MIN_FEN)[0]
    e = 0.0
    for p in rng.choice(ok, size=min(n, len(ok)), replace=False):
        k = int(rng.integers(0, K))
        if np.isnan(y[p, k]):
            continue
        xx, yy = x[max(p - FEN, 0):p].ravel(), y[max(p - FEN, 0):p].ravel()
        m = ~np.isnan(yy)
        xx, yy = xx[m], yy[m]
        A = np.column_stack([np.ones(len(xx)), xx])
        (a, b), *_ = np.linalg.lstsq(A, yy, rcond=None)
        eps = yy - a - b * xx
        zr = (y[p, k] - a - b * x[p, k]) / eps.std(ddof=1)
        zb = y[p, k] / yy.std(ddof=1)
        rho = np.corrcoef(xx, yy)[0, 1]
        e = max(e, abs(zr - R["zr"][p, k]), abs(zb - R["zb"][p, k]), abs(rho - R["rho"][p]))
    return e


def heures_1h(nom):
    d = pd.read_csv(T5 / f"{nom}_1h.csv.gz")
    t = pd.to_datetime(d["t"])
    return pd.DataFrame({"jour": t.dt.normalize(), "h": t.dt.hour, "c": d["c"].to_numpy(float),
                         "contrat": d["contrat"].to_numpy()})


def rendements_1h_futures(nom, jours):
    """Rendements d'une heure 10 h -> 11 h ... 15 h -> 16 h : P(h) = cloture de la barre d'une heure etiquetee h - 1
    (debut de barre, heure de New York) ; NaN si le contrat change entre les deux barres."""
    d = heures_1h(nom)
    d = d[(d["h"] >= 9) & (d["h"] <= 15)]
    c = d.pivot_table(index="jour", columns="h", values="c", aggfunc="last").reindex(index=jours, columns=range(9, 16))
    k = d.pivot_table(index="jour", columns="h", values="contrat", aggfunc="last").reindex(index=jours, columns=range(9, 16))
    lc = np.log(c.to_numpy(float))
    r = lc[:, 1:] - lc[:, :-1]
    kk = k.to_numpy(float)
    r[kk[:, 1:] != kk[:, :-1]] = np.nan
    return r


def accord(a, b, m):
    a, b = a[m].ravel(), b[m].ravel()
    v = ~np.isnan(a) & ~np.isnan(b)
    nz = v & (a != 0) & (b != 0)
    return float((np.sign(a[nz]) == np.sign(b[nz])).mean() * 100), int(nz.sum()), int((v & ~nz).sum())


def jours_830(jours, complete, g, hist_ok):
    """Jours de chiffres de 8 h 30 (description seulement) : saut du dollar de 8 h 30 a 8 h 40 (moyenne de USD/JPY et de
    -EUR/USD HistData, clotures des barres de 8 h 25 et de 8 h 35) au-dessus du 80e centile des 250 seances completes
    precedentes. NaN : dollar absent."""
    a = {nom: np.log(g[nom][1][:, (535 - SLOT0) // 5] / g[nom][1][:, (505 - SLOT0) // 5]) for nom in ("JPY", "EUR")}
    x = pd.Series(np.where(hist_ok, np.abs(0.5 * (a["JPY"] - a["EUR"])), np.nan))
    xc = x[complete].reset_index(drop=True)
    seuil = xc.rolling(250, min_periods=100).quantile(0.80).shift(1)
    out = np.full(len(jours), np.nan)
    v = np.where(xc.isna() | seuil.isna(), np.nan, (xc > seuil).astype(float))
    out[np.where(complete)[0]] = v
    return out


def t_jour(ju, ent, m_ent, m_jour):
    """t net de la serie quotidienne Delta ($) des entrees m_ent sur les seances m_jour."""
    s = par_jour({"jour": ent["jour"][m_ent]}, -ent["usd"][m_ent], ju)
    return float(s[m_jour].sum()), PA.t_stat(s[m_jour])


# ----------------------------------------------------------------------------- principal
def main():
    L = []
    rng = np.random.default_rng(1)                 # graine des placebos (regle commune)
    rng_c = np.random.default_rng(20261022)        # controles (brouillage, verifications a la main)
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    jours, O, Hm, Lm, C, Pm, V, ech = RB.tableaux(bars)
    complete = RB.seances_completes(Pm)
    assert np.array_equal(C, z["C"]) and jours.equals(z["jours"])
    O0 = O[:, 0]
    tous = DM.trades_zone(z, "2000-01-01", DM.FIN)
    tr = tous[~tous["jour"].isin(fed)].sort_values(["jour", "minute_entree"]).reset_index(drop=True)
    ent = entrees(z, tr, complete)
    ju = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    ju = ju[(ju <= pd.Timestamp(DM.FIN)) & ~ju.isin(fed)]
    v1 = par_jour(ent, ent["usd"], ju)
    v1_pts = par_jour(ent, ent["pts"], ju)

    L.append("Piste B : mouvement simultane des autres marches au controle de la zone (B1 a B4)")
    L.append("Regles : etude_large/phenomenes/README.md (commit 929d05e, fixees avant tout calcul). Zone V1 (delta_mesures) sur")
    L.append("les minutes du NQ de la recherche + robot, seances completes, pas de zone les jours de la Fed, 1 MNQ, 1,5 point par")
    L.append("aller-retour. Un trade ecarte reste virtuel jusqu'a la sortie de V1 et bloque : les trades gardes sont ceux de V1.")
    L.append("Serie de decision : Delta = zone filtree - V1, en $ par seance pour 1 MNQ au prix du 20 octobre 2026 (convention")
    L.append("de partie_d.chemins_zone), 0 les seances sans difference ; t = moyenne / ecart-type x racine(seances).")
    if ESSAI:
        L.append("*** ESSAI DU CODE DU COFFRE : 'coffre' = 2021-2022 (donnees d'exploration), departs 2021 - juin 2022 ***")
    L.append("")

    # ------------------------------------------------------------- controle de la zone
    L.append("CONTROLE DE LA ZONE (obligatoire avant tout gain)")
    b19 = bars[bars["t"] <= "2026-10-19 23:59"]
    z19 = DM.preparer(b19)
    t19 = DM.trades_zone(z19, "2000-01-01", "2026-10-19")
    t16 = t19[t19["jour"] <= pd.Timestamp("2026-10-16")]
    bon16 = len(t16) == 3571 and abs(t16["points"].sum() - 10759.75) < 1e-6
    d19 = t19[t19["jour"] == pd.Timestamp("2026-10-19")]
    L.append(f"  moteur jusqu'au 19 octobre 2026 : {len(t19)} trades {t19['points'].sum():+.2f} pt ; entree_tardive : 3 572 trades"
             f" +10 721,25 pt. Jusqu'au 16 octobre : {len(t16)} trades {t16['points'].sum():+.2f} pt contre 3 571 et +10 759,75"
             f" (entree_tardive sans le 19, -38,50 pt) -> {'identique' if bon16 else 'ECART'}")
    L.append(f"  le 19 octobre ici : {len(d19)} trade {d19['points'].sum():+.2f} pt (barre de 11 h 30 retelechargee par le robot"
             " le 20 octobre, deja note par delta_mesures et zones_decalees : 29 944,75 -> 29 945,75)")
    ch_pd = PD.chemins_zone()
    ch_v1 = chemins(z, Hm, Lm, ent, np.ones(len(ent["s"]), bool))
    bon_ch = ch_v1[0].equals(ch_pd[0]) and all(np.array_equal(a, b) for a, b in zip(ch_v1[1:], ch_pd[1:]))
    s_pd = pd.Series(ch_pd[1][:, -1], index=ch_pd[0])
    bon_serie = np.allclose(s_pd.to_numpy(), pd.Series(v1, index=ju).reindex(ch_pd[0]).fillna(0.0).to_numpy(), atol=1e-9)
    L.append(f"  chemins des challenges recalcules ici avec tous les trades de V1 = partie_d.chemins_zone : {'oui' if bon_ch else 'NON'} ;"
             f" serie de decision de V1 = derniere minute de ces chemins (2012-2026) : {'oui' if bon_serie else 'NON'}")
    L.append(f"  V1 hors jours de la Fed jusqu'au {DM.FIN} : {len(ent['s'])} trades, {ent['pts'].sum():+.2f} pt nets ;"
             f" {len(ju)} seances de zone ({len([j for j in z['jouables'] if z['jours'][j] in fed])} jours de la Fed retires)")
    if not (bon16 and bon_ch and bon_serie):
        print("\n".join(L))
        sys.exit("controle de la zone : ECART")

    # ------------------------------------------------------------- donnees des autres marches
    brut = {"VXX": lire_etf("VXX"), "UUP": lire_etf("UUP"), "TLT": lire_etf("TLT"), "IEF": lire_etf("IEF"),
            "AUD": lire_histdata("audusd"), "JPY": lire_histdata("usdjpy"), "TECH": lire_histdata("usatechidxusd"),
            "EUR": lire_histdata("eurusd"), "BTC": lire_btc()}
    g = {nom: grille(b, jours) for nom, b in brut.items()}
    P = pipeline(jours, complete, O0, C, g, ent)
    comp = P["comp"]
    cj = jours[comp]
    U, R, D = P["U"], P["R"], P["D"]

    L.append("")
    L.append("DONNEES DES AUTRES MARCHES (presence des scores, seances completes du NQ)")
    hist = P["hist_ok"][comp]
    cor = P["cor"][comp]
    delta = np.where(np.isnan(cor[:, 1]), np.nan, np.argmax(np.where(np.isnan(cor), -np.inf, cor), axis=1) * 60 - 60)
    for a in sorted(set(cj.year)):
        m = np.asarray(cj.year == a)
        pres = {nom: (~np.isnan(R[nom]["zr"][m])).any(1).mean() * 100 for nom in ("VXX", "UUP", "AUDJPY", "BTC", "TLT", "IEF")}
        L.append(f"  {a} : {int(m.sum())} seances ; HistData a l'heure (delta = 0) {hist[m].mean() * 100:5.1f} %"
                 f" (delta -60 : {(delta[m] == -60).sum()}, +60 : {(delta[m] == 60).sum()}, indecis : {np.isnan(cor[m, 1]).sum()})"
                 " ; z present (au moins un controle) : " + ", ".join(f"{n} {v:3.0f} %" for n, v in pres.items()))
    e_v, n_v = 0.0, 0
    for nom in ("VXX", "UUP", "TLT", "AUD", "JPY", "TECH", "BTC"):
        e_, n_ = verifier_a_la_main({"jours": jours}, brut[nom], g[nom], rng_c, 150)
        e_v, n_v = max(e_v, e_), n_v + n_
    e_r = max(regression_a_la_main(P["x"], P["r"][nom][comp], rng_c) for nom in ("VXX", "UUP", "AUDJPY", "BTC", "TLT"))
    L.append(f"  prix P_X(t) relus a la main dans les barres brutes (7 marches, 1 050 tirages, {n_v} presents) : "
             f"{'identiques' if e_v == 0 else 'ECART'} ; regression des 720 fenetres refaite par moindres carres (z residuel, z"
             f" brut, rho) : ecart max {e_r:.1e}")

    # ------------------------------------------------------------- regard vers le futur
    L.append("")
    L.append("REGARD VERS LE FUTUR")
    idx_u = [i for i in z["jouables"] if z["jours"][i] not in fed]
    ess, err, chg = regard_futur_v1(z, idx_u, rng_c)
    L.append(f"  V1 (entrees) : {ess} cas (300 seances x 12 controles), tout ce qui suit le controle brouille -> {err} entree"
             f" changee jusqu'au controle ; la suite change dans {chg} cas")
    ess2, ncles, chg2, apres2 = regard_futur(jours, complete, O0, C, g, ent, D, rng_c)
    L.append(f"  filtre : {ess2} coupures (entree tiree au hasard) x {ncles} regles (4 tests, variantes, jumeaux) ; minutes du NQ"
             f" apres la minute du controle, barres qui finissent apres tau et seances suivantes bruitees (10 % des barres"
             f" retirees), chaine recalculee -> {chg2} regle-coupure avec une decision changee jusqu'a la coupure ; apres la"
             f" coupure, decisions changees dans {apres2} cas (le brouillage agit)")
    L.append("  le score lit les barres de 5 minutes qui finissent au plus tard a tau et la minute du NQ etiquetee tau - 1 ; V1")
    L.append("  entre a la cloture de la minute etiquetee tau (une minute plus tard). Fenetres et seuil : seances precedentes.")
    sans_futur = err == 0 and chg2 == 0 and apres2 > 0
    L.append(f"  -> {'aucun regard vers le futur' if sans_futur else 'PROBLEME'}")
    if not sans_futur:
        print("\n".join(L))
        sys.exit("regard vers le futur")

    # ------------------------------------------------------------- controle b) (donnees seulement, aucun gain)
    L.append("")
    L.append("CONTROLE b) le bot lirait les futures : accord de signe des rendements d'une heure (10 h - 16 h, 2016 -> 30 sept. 2026)")
    jb = (jours >= pd.Timestamp("2016-01-04")) & (jours <= pd.Timestamp("2026-09-30")) & complete
    lpt = np.log(np.column_stack([prix_a(g["TLT"], 60 * h) for h in range(10, 17)]))
    r_tlt = lpt[:, 1:] - lpt[:, :-1]
    r_zn = rendements_1h_futures("ZN", jours)
    acc_t, n_t, z_t = accord(r_tlt, r_zn, jb)
    lpa = np.log(np.column_stack([prix_a(g["AUD"], 60 * h) * prix_a(g["JPY"], 60 * h) for h in range(10, 17)]))
    r_aj = lpa[:, 1:] - lpa[:, :-1]
    r_aj[~P["hist_ok"]] = np.nan
    r_fut = rendements_1h_futures("6A", jours) - rendements_1h_futures("6J", jours)
    acc_a, n_a, z_a = accord(r_aj, r_fut, jb)
    ok_tlt, ok_aj = acc_t >= 90.0, acc_a >= 90.0
    L.append(f"  TLT contre ZN : {acc_t:.1f} % ({n_t} heures ; {z_t} heures ou l'un des deux ne bouge pas, retirees) ->"
             f" {'au moins 90 %' if ok_tlt else 'MOINS DE 90 % : B4 (et le TLT de B1) seulement descriptif'}")
    L.append(f"  AUD/JPY HistData contre 6A / 6J : {acc_a:.1f} % ({n_a} heures ; {z_a} retirees) ->"
             f" {'au moins 90 %' if ok_aj else 'MOINS DE 90 % : B2 (et l AUD/JPY de B1) seulement descriptif'}")
    L.append("  VXX et UUP ne sont pas des produits CME : le bot devrait les lire par l'API gratuite d'Alpaca (a verifier) ;")
    L.append("  c'est rappele a cote des resultats de B1 et de B3.")
    descriptif = {"B1": not (ok_tlt and ok_aj), "B2": not ok_aj, "B3": False, "B4": not ok_tlt}

    # ------------------------------------------------------------- periodes
    per = {}
    for t in TESTS:
        i0 = np.searchsorted(cj, pd.Timestamp(DEBUTS[t]))
        d61 = cj[i0 + FEN]
        e = np.asarray((ju >= d61) & (ju <= pd.Timestamp(FIN_EXPLO)))
        c = np.asarray((ju >= pd.Timestamp(DEBUT_COFFRE)) & (ju <= pd.Timestamp(FINS[t])))
        ee = np.asarray((ent["jour"] >= d61) & (ent["jour"] <= pd.Timestamp(FIN_EXPLO)))
        ec = np.asarray((ent["jour"] >= pd.Timestamp(DEBUT_COFFRE)) & (ent["jour"] <= pd.Timestamp(FINS[t])))
        per[t] = dict(d61=d61, e=e, c=c, ee=ee, ec=ec)
    j8 = jours_830(jours, complete, g, P["hist_ok"])[ent["i"]]
    rho_ent = R["TLT"]["rho"][ent["p"]]

    def serie(nom):
        return par_jour({"jour": ent["jour"][D[nom]["ecarte"]]}, -ent["usd"][D[nom]["ecarte"]], ju)

    def serie_pts(nom):
        return par_jour({"jour": ent["jour"][D[nom]["ecarte"]]}, -ent["pts"][D[nom]["ecarte"]], ju)

    # ------------------------------------------------------------- EXPLORATION
    L.append("")
    L.append("=" * 118)
    L.append(f"EXPLORATION (jusqu'au {FIN_EXPLO}) - ecrite dans le fichier avant l'ouverture du coffre")
    L.append("=" * 118)
    res = {}
    for t in TESTS:
        pr = per[t]
        e, ee = pr["e"], pr["ee"]
        d = serie(t)
        dp = serie_pts(t)
        sc_ok = ~np.isnan(D[t]["sc"])
        n_sc, n_ec = int((ee & sc_ok).sum()), int((ee & D[t]["ecarte"]).sum())
        te = PA.t_stat(d[e])
        L.append("")
        L.append(f"=== TEST {t} : {NOMS[t]} (unilateral, sens predit Delta > 0) ===")
        L.append(f"  exploration du {pr['d61'].date()} (61e seance complete depuis le {DEBUTS[t]}) au {FIN_EXPLO} : {int(e.sum())}"
                 f" seances, {int(ee.sum())} entrees de V1, score present pour {n_sc} ({n_sc / max(int(ee.sum()), 1) * 100:.1f} %),"
                 f" {n_ec} ecartees ({n_ec / max(n_sc, 1) * 100:.1f} % des entrees notees, {n_ec / max(int(ee.sum()), 1) * 100:.1f} % de toutes)")
        L.append(f"  V1 sur ces seances : {v1[e].sum():+,.0f} $ ({v1_pts[e].sum():+.2f} pt nets), Sharpe {PA.sharpe(v1[e]):+.3f} ;"
                 f" trades ecartes : {-d[e].sum():+,.0f} $ ({-dp[e].sum():+.2f} pt nets, {-dp[e].sum() / max(n_ec, 1):+.2f} pt par trade)")
        L.append(f"  Delta = zone filtree - V1 : {d[e].sum():+,.0f} $ ({dp[e].sum():+.2f} pt nets, information), t net {te:+.2f},"
                 f" p unilateral {PA.p_unilateral(te):.4f}")
        c1 = te >= 2.0
        L.append(f"  1) t net >= 2 : {'oui' if c1 else 'non'} (Benjamini-Hochberg a 10 % : calcule ensuite sur les 11 tests de la vague)")
        reel, pla, npl = placebo(U[t], D[t], ent, ee, cj, rng)
        part = (reel > pla).mean() * 100
        c3 = part >= 95.0
        L.append(f"  3) placebo ({PLACEBOS} tirages, {npl} entrees notees ; score du meme controle d'une autre seance de la meme annee,"
                 f" meme seuil q) : placebos moyenne {pla.mean():+,.0f} $, 95e centile {np.percentile(pla, 95):+,.0f} $ ; reel"
                 f" {reel:+,.0f} $ fait mieux que {part:.1f} % -> {'oui' if c3 else 'non'}")
        se_f, se_v = PA.sharpe(v1[e] + d[e]), PA.sharpe(v1[e])
        c4e = se_f > se_v
        L.append(f"  4) Sharpe des seances, zone filtree contre V1 (exploration) : {se_f:+.3f} contre {se_v:+.3f} -> {'oui' if c4e else 'non'}")
        dj = serie(f"{t} jumeau")
        tj = PA.t_stat(dj[e])
        nje = int((ee & D[f"{t} jumeau"]["ecarte"]).sum())
        jum_e = tj < te
        L.append(f"  jumeau NQ (score = s r_NQ / ecart-type de r_NQ sur les 720 fenetres, memes entrees notees, meme regle de"
                 f" seuil) : {nje} ecartees, Delta {dj[e].sum():+,.0f} $, t {tj:+.2f} -> le test fait {'mieux' if jum_e else 'MOINS BIEN'}")
        accord_j = (D[t]["ecarte"][ee & sc_ok] == D[f"{t} jumeau"]["ecarte"][ee & sc_ok]).mean() * 100
        L.append(f"     accord de decision avec le jumeau sur les entrees notees : {accord_j:.1f} %")
        res[t] = dict(te=te, c1=c1, c3=c3, c4e=c4e, jum_e=jum_e, d=d, dp=dp, part=part)
        # controle a) par annee
        an = ent["jour"].year.to_numpy()
        lig = []
        for a in sorted(set(an[ee])):
            m = ee & (an == a)
            ns = int((m & sc_ok).sum())
            lig.append(f"{a} {int((m & D[t]['ecarte']).sum())}/{ns} ({(m & D[t]['ecarte']).sum() / max(ns, 1) * 100:.0f} %)")
        L.append("  a) ecartees / notees par annee : " + " ; ".join(lig))
        # controle d)
        lig = []
        for s_, nom_s in ((1, "achats"), (-1, "ventes")):
            m = ee & (ent["s"] == s_)
            tot, tt = t_jour(ju, ent, m & D[t]["ecarte"], e)
            lig.append(f"{nom_s} : {int((m & D[t]['ecarte']).sum())} ecartes sur {int((m & sc_ok).sum())} notes, Delta {tot:+,.0f} $ (t {tt:+.2f})")
        L.append("  d) " + " ; ".join(lig))
        lig = []
        for k in range(K):
            m = ee & (ent["k"] == k)
            lig.append(f"{heure(PAS * (k + 1))} {int((m & D[t]['ecarte']).sum())}/{int((m & sc_ok).sum())}"
                       f" {-ent['usd'][m & D[t]['ecarte']].sum():+,.0f} $")
        L.append("     par controle (ecartes / notes, Delta) : " + " ; ".join(lig))
        lig = []
        for nom_j, m_j in (("jours de chiffres de 8 h 30", j8 == 1), ("autres jours", j8 == 0), ("dollar absent", np.isnan(j8))):
            m = ee & m_j
            tot, tt = t_jour(ju, ent, m & D[t]["ecarte"], e)
            lig.append(f"{nom_j} : {int((m & D[t]['ecarte']).sum())}/{int((m & sc_ok).sum())}, Delta {tot:+,.0f} $ (t {tt:+.2f})")
        L.append("     " + " ; ".join(lig))
        if t in ("B1", "B4"):
            lig = []
            for nom_r, m_r in (("rho_TLT < 0", rho_ent < 0), ("rho_TLT > 0", rho_ent > 0), ("rho_TLT absent", np.isnan(rho_ent))):
                m = ee & m_r
                tot, tt = t_jour(ju, ent, m & D[t]["ecarte"], e)
                lig.append(f"{nom_r} : {int((m & D[t]['ecarte']).sum())}/{int((m & sc_ok).sum())}, Delta {tot:+,.0f} $ (t {tt:+.2f})")
            L.append("  c) " + " ; ".join(lig))
        if t == "B4":
            lig = []
            for v in ("B4 e=-1", "B4 e=+1", "B4 IEF"):
                dv = serie(v)
                lig.append(f"{v} : {int((ee & D[v]['ecarte']).sum())} ecartees, Delta {dv[e].sum():+,.0f} $, t {PA.t_stat(dv[e]):+.2f}")
            L.append("     information : " + " ; ".join(lig))
        if descriptif[t]:
            L.append("  (controle b : ce test n'est que descriptif)")
        if t in ("B1", "B3"):
            L.append("  (VXX et UUP hors CME : lecture par l'API gratuite d'Alpaca a verifier)")

    L.append("")
    L.append("FIN DE L'EXPLORATION : t net, p unilateral (Benjamini-Hochberg ensuite sur les 11 tests de la vague)")
    for t in TESTS:
        L.append(f"  {t} : t {res[t]['te']:+.2f}, p {PA.p_unilateral(res[t]['te']):.4f}, placebo {res[t]['part']:.1f} %,"
                 f" Sharpe {'plus haut' if res[t]['c4e'] else 'pas plus haut'}, jumeau {'battu' if res[t]['jum_e'] else 'NON battu'}")
    SORTIE.write_text("\n".join(L) + "\n")
    print("\n".join(L), flush=True)
    if PHASE == "exploration":
        return

    # ------------------------------------------------------------- COFFRE (ouvert une seule fois)
    L = ["", "=" * 118, f"COFFRE ({DEBUT_COFFRE} -> fin de chaque test), ouvert apres l'ecriture de l'exploration ci-dessus",
         "=" * 118]
    base = {"Lucid 1 MNQ": defis(ch_v1, LUCID, 1), "Bulenox 3 MNQ": defis(ch_v1, BULENOX, 3),
            "Bulenox 4 puis 6 MNQ (information)": defis(ch_v1, BULENOX, 4, 6, 5)}
    L.append("  V1 seule aux challenges (partie D, departs " + (f"{DEPARTS[0]} - {DEPARTS[1]}" if DEPARTS[1] else "2023-2026")
             + ") : " + " ; ".join(f"{k} valide {v['valide']:.1f} %, perdu {v['perdu']:.1f} % ({v['n']} departs)"
                                     for k, v in base.items()))
    for t in TESTS:
        pr = per[t]
        c, ec = pr["c"], pr["ec"]
        d, dp = res[t]["d"], res[t]["dp"]
        sc_ok = ~np.isnan(D[t]["sc"])
        n_sc, n_ec = int((ec & sc_ok).sum()), int((ec & D[t]["ecarte"]).sum())
        tc = PA.t_stat(d[c])
        L.append("")
        L.append(f"=== TEST {t} : {NOMS[t]} - coffre {DEBUT_COFFRE} -> {FINS[t]} ===")
        L.append(f"  {int(c.sum())} seances, {int(ec.sum())} entrees, notees {n_sc}, ecartees {n_ec} ({n_ec / max(n_sc, 1) * 100:.1f} %"
                 f" des notees) ; V1 {v1[c].sum():+,.0f} $, Sharpe {PA.sharpe(v1[c]):+.3f}")
        L.append(f"  Delta : {d[c].sum():+,.0f} $ ({dp[c].sum():+.2f} pt nets), t net {tc:+.2f}")
        c2 = tc >= 1.5 and np.sign(tc) == np.sign(res[t]["te"])
        L.append(f"  2) coffre meme signe, t net >= 1,5 : {'oui' if c2 else 'non'}")
        se_f, se_v = PA.sharpe(v1[c] + d[c]), PA.sharpe(v1[c])
        c4c = se_f > se_v
        c4 = res[t]["c4e"] and c4c
        L.append(f"  4) Sharpe au coffre : {se_f:+.3f} contre {se_v:+.3f} -> {'oui' if c4c else 'non'} ; sur les deux periodes :"
                 f" {'oui' if c4 else 'non'}")
        dj = serie(f"{t} jumeau")
        tj = PA.t_stat(dj[c])
        jum = res[t]["jum_e"] and tj < tc
        L.append(f"  jumeau NQ au coffre : Delta {dj[c].sum():+,.0f} $, t {tj:+.2f} -> le test fait {'mieux' if tj < tc else 'MOINS BIEN'} ;"
                 f" sur les deux periodes : {'oui' if jum else 'non'}")
        reel_c, pla_c, _ = placebo(U[t], D[t], ent, ec, cj, rng)
        L.append(f"     information, meme placebo au coffre : reel {reel_c:+,.0f} $ fait mieux que {(reel_c > pla_c).mean() * 100:.1f} %"
                 f" (moyenne {pla_c.mean():+,.0f}, 95e centile {np.percentile(pla_c, 95):+,.0f})")
        ch_f = chemins(z, Hm, Lm, ent, ~D[t]["ecarte"])
        ok5 = {}
        for nom_c, (firme, q, qf, nf) in (("Lucid 1 MNQ", (LUCID, 1, None, 0)), ("Bulenox 3 MNQ", (BULENOX, 3, None, 0)),
                                          ("Bulenox 4 puis 6 MNQ (information)", (BULENOX, 4, 6, 5))):
            r_ = defis(ch_f, firme, q, qf, nf)
            b_ = base[nom_c]
            dv, dpp = r_["valide"] - b_["valide"], r_["perdu"] - b_["perdu"]
            o = dv >= 2.0 and dpp <= 3.0
            if "information" not in nom_c:
                ok5[nom_c] = o
            L.append(f"  5) {nom_c} : valide {r_['valide']:.1f} % (V1 {b_['valide']:.1f} %), perdu {r_['perdu']:.1f} % (V1"
                     f" {b_['perdu']:.1f} %) -> {dv:+.1f} points valides, {dpp:+.1f} points perdus"
                     + ("" if "information" in nom_c else f" -> {'passe' if o else 'ne passe pas'}"))
        c5 = any(ok5.values())
        L.append(f"     -> critere 5 : {'oui (' + ', '.join(k for k, v in ok5.items() if v) + ')' if c5 else 'non'}")
        an = ent["jour"].year.to_numpy()
        lig = []
        for a in sorted(set(an[ec])):
            m = ec & (an == a)
            ns = int((m & sc_ok).sum())
            lig.append(f"{a} {int((m & D[t]['ecarte']).sum())}/{ns} ({(m & D[t]['ecarte']).sum() / max(ns, 1) * 100:.0f} %)")
        L.append("  a) ecartees / notees par annee : " + " ; ".join(lig))
        lig = []
        for s_, nom_s in ((1, "achats"), (-1, "ventes")):
            m = ec & (ent["s"] == s_)
            tot, tt = t_jour(ju, ent, m & D[t]["ecarte"], c)
            lig.append(f"{nom_s} : {int((m & D[t]['ecarte']).sum())}/{int((m & sc_ok).sum())}, Delta {tot:+,.0f} $ (t {tt:+.2f})")
        L.append("  d) " + " ; ".join(lig))
        lig = []
        for k in range(K):
            m = ec & (ent["k"] == k)
            lig.append(f"{heure(PAS * (k + 1))} {int((m & D[t]['ecarte']).sum())}/{int((m & sc_ok).sum())}"
                       f" {-ent['usd'][m & D[t]['ecarte']].sum():+,.0f} $")
        L.append("     par controle : " + " ; ".join(lig))
        lig = []
        for nom_j, m_j in (("jours de chiffres de 8 h 30", j8 == 1), ("autres jours", j8 == 0), ("dollar absent", np.isnan(j8))):
            m = ec & m_j
            tot, tt = t_jour(ju, ent, m & D[t]["ecarte"], c)
            lig.append(f"{nom_j} : {int((m & D[t]['ecarte']).sum())}/{int((m & sc_ok).sum())}, Delta {tot:+,.0f} $ (t {tt:+.2f})")
        L.append("     " + " ; ".join(lig))
        if t in ("B1", "B4"):
            lig = []
            for nom_r, m_r in (("rho_TLT < 0", rho_ent < 0), ("rho_TLT > 0", rho_ent > 0), ("rho_TLT absent", np.isnan(rho_ent))):
                m = ec & m_r
                tot, tt = t_jour(ju, ent, m & D[t]["ecarte"], c)
                lig.append(f"{nom_r} : {int((m & D[t]['ecarte']).sum())}/{int((m & sc_ok).sum())}, Delta {tot:+,.0f} $ (t {tt:+.2f})")
            L.append("  c) " + " ; ".join(lig))
        if t == "B4":
            lig = []
            for v in ("B4 e=-1", "B4 e=+1", "B4 IEF"):
                dv = serie(v)
                lig.append(f"{v} : {int((ec & D[v]['ecarte']).sum())} ecartees, Delta {dv[c].sum():+,.0f} $, t {PA.t_stat(dv[c]):+.2f}")
            L.append("     information : " + " ; ".join(lig))
        propre = res[t]["c1"] and c2 and res[t]["c3"] and c4 and c5 and jum and not descriptif[t]
        res[t].update(tc=tc, c2=c2, c4=c4, c5=c5, jum=jum, propre=propre)
        L.append(f"  -> criteres propres (hors Benjamini-Hochberg) : {'PASSENT' if propre else 'ECHEC'} (1 t>=2"
                 f" {'oui' if res[t]['c1'] else 'non'}, 2 {'oui' if c2 else 'non'}, 3 {'oui' if res[t]['c3'] else 'non'},"
                 f" 4 {'oui' if c4 else 'non'}, 5 {'oui' if c5 else 'non'}, jumeau {'oui' if jum else 'non'},"
                 f" controle b {'descriptif' if descriptif[t] else 'oui'})")

    # ------------------------------------------------------------- controle e) P1 et P2
    L.append("")
    L.append("CONTROLE e) accord avec le vrai filtre delta (delta_mesures/trades.csv : 99 trades de P1, 7 de P2 ; barres du robot)")
    vrai = pd.read_csv(RACINE / "delta_mesures" / "trades.csv", parse_dates=["jour"])
    cle = {(j, int(m), int(s)): n for n, (j, m, s) in enumerate(zip(ent["jour"], ent["me"], ent["s"]))}
    for perio in ("P1", "P2"):
        x = vrai[vrai["periode"] == perio]
        idxs = [cle.get((r.jour, int(r.minute_entree), int(r.sens))) for r in x.itertuples()]
        trouves = [(n, bool(r.B)) for n, r in zip(idxs, x.itertuples()) if n is not None]
        L.append(f"  {perio} : {len(x)} trades, {len(trouves)} retrouves dans V1 ici (meme jour, minute, sens), {sum(1 for _, b in trouves if b)}"
                 " gardes par le vrai delta")
        for t in TESTS:
            note = [(n, b) for n, b in trouves if not np.isnan(D[t]["sc"][n])]
            if not note:
                L.append(f"     {t} : aucun score (marche absent)")
                continue
            garde_t = np.array([not D[t]["ecarte"][n] for n, _ in note])
            garde_d = np.array([b for _, b in note])
            L.append(f"     {t} : {len(note)} notes, {int((~garde_t).sum())} ecartes ; accord avec le vrai delta"
                     f" {(garde_t == garde_d).mean() * 100:.0f} % ; ecartes par les deux {int((~garde_t & ~garde_d).sum())},"
                     f" par le test seul {int((~garde_t & garde_d).sum())}, par le delta seul {int((garde_t & ~garde_d).sum())}")

    # ------------------------------------------------------------- controle f) ES
    L.append("")
    L.append("CONTROLE f) ES en replication (information) : zone V1 de l'ES (sp500_1min, -> 25 sept. 2026), 0,9 point,")
    L.append("  residus contre r_ES, memes marches et memes regles ; Delta en points ES nets par seance")
    es = pd.read_csv(ES)
    ze = DM.preparer(es)
    je, Oe, _, _, Ce, Pe, _, _ = RB.tableaux(es)
    comp_e = RB.seances_completes(Pe)
    tre = DM.trades_zone(ze, "2000-01-01", DM.FIN)
    tre = tre[~tre["jour"].isin(fed)].sort_values(["jour", "minute_entree"]).reset_index(drop=True)
    pos_c = np.full(len(je), -1)
    pos_c[np.where(comp_e)[0]] = np.arange(comp_e.sum())
    ie = np.array([je.get_loc(j) for j in tre["jour"]])
    ente = dict(p=pos_c[ie], k=tre["minute_entree"].to_numpy() // PAS - 1, s=tre["sens"].to_numpy(float),
                jour=pd.DatetimeIndex(tre["jour"]),
                pts=tre["sens"].to_numpy() * (tre["prix_sortie"].to_numpy() - tre["prix_entree"].to_numpy()) - COUT_ES)
    ge = {nom: grille(b, je) for nom, b in brut.items()}
    Pes = pipeline(je, comp_e, Oe[:, 0], Ce, ge, ente)
    jue = pd.DatetimeIndex([ze["jours"][i] for i in ze["jouables"]])
    jue = jue[~jue.isin(fed)]
    for t in TESTS:
        de = par_jour({"jour": ente["jour"][Pes["D"][t]["ecarte"]]}, -ente["pts"][Pes["D"][t]["ecarte"]], jue)
        lig = []
        for nom_p, a, b in (("exploration", per[t]["d61"], pd.Timestamp(FIN_EXPLO)),
                            ("coffre", pd.Timestamp(DEBUT_COFFRE), pd.Timestamp(FINS[t]))):
            m = np.asarray((jue >= a) & (jue <= b))
            lig.append(f"{nom_p} {de[m].sum():+.2f} pt (t {PA.t_stat(de[m]):+.2f})")
        sg_nq = [np.sign(res[t]["d"][per[t]["e"]].sum()), np.sign(res[t]["d"][per[t]["c"]].sum())]
        L.append(f"  {t} : " + " ; ".join(lig) + f" ; signe du NQ : {'+' if sg_nq[0] > 0 else '-'} / {'+' if sg_nq[1] > 0 else '-'}")

    # ------------------------------------------------------------- bilan
    L.append("")
    L.append("BILAN (Benjamini-Hochberg a 10 % : calcule ensuite sur les 11 tests de la vague)")
    L.append("  test  t explo  p unilateral  t coffre  1 2 3 4 5 jumeau  b)          criteres propres")
    for t in TESTS:
        r_ = res[t]
        L.append(f"  {t:4}  {r_['te']:+7.2f}  {PA.p_unilateral(r_['te']):12.4f}  {r_['tc']:+8.2f}  "
                 + " ".join("o" if x else "n" for x in (r_["c1"], r_["c2"], r_["c3"], r_["c4"], r_["c5"]))
                 + f" {'o' if r_['jum'] else 'n'}       {'descriptif' if descriptif[t] else 'oui':11} {'passent' if r_['propre'] else 'echec'}")
    L.append("  controles : zone identique, regard vers le futur : aucun ; a) c) d) e) f) publies ; b) "
             + f"TLT/ZN {acc_t:.1f} %, AUD/JPY / 6A÷6J {acc_a:.1f} %")
    if not any(res[t]["propre"] for t in TESTS):
        L.append("  Decision : aucun filtre croise n'est retenu ; le bot garde la zone filtree par le seul delta.")
    else:
        L.append("  Decision : un test qui passe ses criteres propres n'est retenu que s'il passe aussi Benjamini-Hochberg sur la")
        L.append("  vague, puis la contre-verification adverse, puis l'argent virtuel.")
    with SORTIE.open("a") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
