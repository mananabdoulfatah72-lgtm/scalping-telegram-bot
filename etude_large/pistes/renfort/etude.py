#!/usr/bin/env python3
"""etude_large/pistes/README.md, piste 3 (regles fixees le 22 octobre 2026, commit a6e791f, avant tout calcul) :
renfort sur le trade qui tient. Base : les positions de V1 exactement (zone/robot.py, 1 MNQ ; sur 15 ans sans filtre
delta, faute de delta ; pas de zone les jours de la Fed ni les jours courts, comme le bot et toutes les vagues de
l'etude large). Un controle tenu est un controle qui suit l'entree et ou V1 garde sa position sans sortir (un controle
ou V1 sort puis rachete n'est pas tenu : le rachat est une nouvelle entree d'une unite). A un controle tenu de 10 h 30 a
15 h 00, on ajoute 1 MNQ a la cloture de la minute du controle, dans le sens de la position ; pas de renfort a 15 h 30 ;
toutes les unites sortent a la sortie de V1 (controle ou 15 h 59). 1,5 point par aller-retour et par unite.
R1 : un renfort au premier controle tenu ; R2 : au premier et au deuxieme ; R3 : comme R1, seulement si le gain latent
au controle >= 0,5 x sigma_m x reference (max(ouverture, veille) pour un achat, min(ouverture, veille) pour une vente).
Serie testee : gain net des seules unites ajoutees, par seance, 0 sans renfort. 3 tests unilateraux (t net >= 2).
Exploration 2011-2022, coffre 2023 -> 20 octobre 2026.

Lancer : KB=<branche de recherche extraite> python3 etude_large/pistes/renfort/etude.py. Ecrit resultats.txt."""
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_CACHE_DIR", str(Path(tempfile.gettempdir()) / "numba_renfort"))

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

N, PAS, COUT = DM.N, DM.PAS, DM.COUT
PREMIER, DERNIER = 60, 330                 # renforts de 10 h 30 a 15 h 00 (pas a 15 h 30)
SEUIL_R3 = 0.5
EXPLO = ("2011-01-01", "2022-12-31")
COFFRE = ("2023-01-01", DM.FIN)
PLACEBOS, GRAINE = 200, 20261022
ES = DM.KB / "intraday" / "donnees" / "sp500_1min.csv.gz"
LUCID, BULENOX = "Lucid Flex 50K", "Bulenox Legacy 50K opt. 2"
TESTS = ["R1", "R2", "R3"]
EXPO = {"R1": 2, "R2": 3, "R3": 2}         # unites au plus pour 1 MNQ de base
LIMITE_JOUR_BULENOX = 1000.0               # README de la piste (controle d)


def heure(m):
    return DM.heure(m)


# ----------------------------------------------------------------------------- une seance
def seance(C, sg, vw, hr, br, base="V1"):
    """Trades de la base d'une seance, controles de 10 h 00 a 15 h 30, a plat a 15 h 59. base 'V1' : sortie si C repasse
    max(ub, VWAP) (achat) ou min(lb, VWAP) (vente), puis entree au meme controle si C est hors de la zone (comme
    delta_mesures zone_jour) ; base 'ZL' (controle e, information) : sortie seulement si C <= ub (achat) ou C >= lb (vente).
    Renvoie [(me, sens, pe, ms, ps, tenus)] ; tenus = controles qui suivent l'entree et ou la position est gardee."""
    out, pos, pe, me, tenus = [], 0, 0.0, -1, []
    for m in range(PAS, N):
        p = C[m]
        if m == N - 1:
            if pos:
                out.append((me, pos, pe, m, p, tenus))
            break
        if m % PAS:
            continue
        ub, lb = hr * (1 + sg[m]), br * (1 - sg[m])
        if pos:
            if base == "V1":
                sort = (pos > 0 and p <= max(ub, vw[m])) or (pos < 0 and p >= min(lb, vw[m]))
            else:
                sort = (pos > 0 and p <= ub) or (pos < 0 and p >= lb)
            if sort:
                out.append((me, pos, pe, m, p, tenus))
                pos = 0
            else:
                tenus.append(m)
        if not pos and m <= DM.DERNIERE_ENTREE:
            s = 1 if p > ub else (-1 if p < lb else 0)
            if s:
                pos, pe, me, tenus = s, p, m, []
    return out


def renforts(trade, C, sg, hr, br, regle):
    """Unites ajoutees a un trade : [(minute du renfort, sens, prix, minute de sortie, prix de sortie)]."""
    me, s, pe, ms, ps, tenus = trade
    choix = tenus[:2] if regle == "R2" else tenus[:1]
    choix = [m for m in choix if PREMIER <= m <= DERNIER]
    if regle == "R3":
        choix = [m for m in choix if s * (C[m] - pe) >= SEUIL_R3 * sg[m] * (hr if s > 0 else br)]
    return [(m, s, C[m], ms, ps) for m in choix]


def univers(z, fed, debut, fin):
    return [i for i in z["jouables"] if pd.Timestamp(debut) <= z["jours"][i] <= pd.Timestamp(fin)
            and z["jours"][i] not in fed and not DM.RB.jour_court(z["jours"][i])]


def calculer(z, idx, base="V1", cout=COUT):
    """Pour chaque seance : trades de la base, unites de renfort de chaque regle, et reserve du placebo (controles de
    10 h 30 a 15 h 00 ou la base est en position apres sa decision, avec la sortie de cette position)."""
    res = {}
    for i in idx:
        C, sg, vw, hr, br = z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i]
        tr = seance(C, sg, vw, hr, br, base)
        r = {"trades": tr, "v1": sum(s * (ps - pe) - cout for _, s, pe, _, ps, _ in tr), "reserve": []}
        for regle in TESTS:
            r[regle] = [u for t in tr for u in renforts(t, C, sg, hr, br, regle)]
        for me, s, pe, ms, ps, tenus in tr:
            for m in [me] + tenus:
                if PREMIER <= m <= DERNIER:
                    r["reserve"].append((m, s, C[m], ms, ps))
        res[z["jours"][i]] = r
    return res


def net(u, cout=COUT):
    return u[1] * (u[4] - u[2]) - cout


def series(res, jours, regle, cout=COUT):
    return np.array([sum(net(u, cout) for u in res[j][regle]) for j in jours])


# ----------------------------------------------------------------------------- challenges (partie D)
def chemins(z, Hm, Lm, unites):
    """Recopie de partie_d.chemins_zone, avec une liste d'unites (me, sens, pe, ms, ps) par jour (jours de la Fed et
    jours courts deja absents) ; meme calendrier, memes prix ramenes au 20 octobre 2026, frais deduits a l'entree."""
    jours = pd.DatetimeIndex([z["jours"][i] for i in z["jouables"]])
    jours = jours[(jours >= PD.DEBUT) & (jours <= DM.FIN)]
    idx = {j: i for i, j in enumerate(z["jours"])}
    ref = float(z["C"][idx[pd.Timestamp(DM.FIN)], N - 1])
    ch, bas, haut = (np.zeros((len(jours), N)) for _ in range(3))
    pos = {j: k for k, j in enumerate(jours)}
    for j, us in unites.items():
        if j not in pos or not us:
            continue
        i = idx[j]
        C, H, L = z["C"][i], Hm[i], Lm[i]
        f = ref / C[0]
        c, contre, pour = np.zeros(N), np.zeros(N), np.zeros(N)
        for me, s, pe, ms, ps in us:
            c[me:ms] += s * (C[me:ms] - pe) * f
            c[ms:] += s * (ps - pe) * f
            c[me:] -= COUT
            w = slice(me + 1, ms + 1)
            contre[w] += ((C[w] - L[w]) if s > 0 else (H[w] - C[w])) * f
            pour[w] += ((H[w] - C[w]) if s > 0 else (C[w] - L[w])) * f
        k = pos[j]
        ch[k], bas[k], haut[k] = c * DM.RB.PT, (c - contre) * DM.RB.PT, (c + pour) * DM.RB.PT
    return jours, ch, bas, haut


def defis(ch, firme, q):
    obj, dd, bloc, dll, nmax, part, *_ = PD.FIRMES[firme]
    jours, clo, bas, haut = ch
    verif = np.where(jours >= PD.DEBUT_VERIF)[0]
    lim = PD.limites_depart(jours, verif, nmax)
    ok = verif + lim < len(jours)
    iss, _ = PD.tous_les_departs(clo, bas, haut, verif[ok], lim[ok], float(q), float(q), 0, float(obj), float(dd),
                                 float(bloc), float(dll), part, True)
    return dict(n=int(ok.sum()), valide=(iss == 1).mean() * 100, perdu=(iss == -1).mean() * 100,
                expire=(iss == 0).mean() * 100)


# ----------------------------------------------------------------------------- controles
def regard_futur(z, idx, rng, n=300):
    """Chaque decision au controle m (entree, sortie, renfort et son seuil R3) ne doit dependre que des minutes <= m : tout
    ce qui suit m (prix, VWAP, sigma) est remplace par du bruit, et les evenements jusqu'a m doivent rester les memes."""
    def evenements(C, sg, vw, hr, br, m):
        tr = seance(C, sg, vw, hr, br)
        ev = []
        for t in tr:
            me, s, pe, ms, ps, _ = t
            if me <= m:
                ev.append(("entree", me, s, round(pe, 6)))
            if ms <= m:
                ev.append(("sortie", ms, round(ps, 6)))
            for regle in TESTS:
                ev += [(regle, u[0], u[1], round(u[2], 6)) for u in renforts(t, C, sg, hr, br, regle) if u[0] <= m]
        return ev, tr

    erreurs = changees = essais = 0
    for i in rng.choice(idx, size=min(n, len(idx)), replace=False):
        C, sg, vw, hr, br = z["C"][i], z["sigma"][i], z["vwap"][i], z["href"][i], z["bref"][i]
        for m in range(PAS, N - 1, PAS):
            C2, sg2, vw2 = C.copy(), sg.copy(), vw.copy()
            k = N - m - 1
            C2[m + 1:] = C[m] * (1 + rng.normal(0, 0.02, k))
            vw2[m + 1:] = C[m] * (1 + rng.normal(0, 0.02, k))
            sg2[m + 1:] = rng.uniform(0, 0.03, k)
            a, ta = evenements(C, sg, vw, hr, br, m)
            b, tb = evenements(C2, sg2, vw2, hr, br, m)
            essais += 1
            erreurs += a != b
            changees += [t[:5] for t in ta] != [t[:5] for t in tb]
    return essais, erreurs, changees


def verifier_niveaux(bars, z, idx, rng, n=200):
    """sigma, VWAP et veille recalcules a la main, avec les seules minutes et seances connues avant la decision."""
    jours, O, H, L, C, P, V, ech = DM.RB.tableaux(bars)
    ok = DM.RB.seances_completes(P)
    seg = np.cumsum(ech)
    e_s = e_v = e_r = 0.0
    for i in rng.choice(idx, size=min(n, len(idx)), replace=False):
        m = int(rng.integers(PAS, N))
        avant = np.where(ok[:i])[0][-14:]
        s = np.mean(np.abs(C[avant, m] / O[avant, 0] - 1))
        e_s = max(e_s, abs(s - z["sigma"][i, m]))
        typ = (H[i, :m + 1] + L[i, :m + 1] + C[i, :m + 1]) / 3
        w = V[i, :m + 1]
        vw = (typ * w).sum() / w.sum() if w.sum() > 0 else typ.mean()
        e_v = max(e_v, abs(vw - z["vwap"][i, m]))
        p = np.where(ok[:i])[0]
        p = p[-1] if len(p) else -1
        veille = C[p, N - 1] if p >= 0 and seg[p] == seg[i] else np.nan
        e_r = max(e_r, abs(max(O[i, 0], veille) - z["href"][i]), abs(min(O[i, 0], veille) - z["bref"][i]))
    return e_s, e_v, e_r


def autopsie():
    """Controle a) : la zone de l'autopsie (zone_failles/journal.py, V0, 2011-2022, jours sans changement d'echeance)."""
    sys.path.insert(0, str(DM.KB / "intraday"))
    sys.path.insert(0, str(DM.KB / "zone_failles"))
    import journal as ZJ
    st = ZJ.st
    J, O, H, L, C, P, X = st.charger("nasdaq100")
    g = J.values <= np.datetime64("2022-12-31")
    X2 = {"V": X["V"][g], "echeance": X["echeance"][g], "contrat": X["contrat"][g]}
    J, O, H, L, C, P = J[g], O[g], H[g], L[g], C[g], P[g]
    t = ZJ.journal(J, O, H, L, C, P, X2)
    ok = st.journees_completes(P) & ~X2["echeance"]
    t = t[ok[t["d"].values]]
    dur = t["m_sortie"] - t["m_entree"]
    return len(t), int((dur > 30).sum()), int((dur <= 30).sum())


def periode(jours, a, b):
    return (jours >= pd.Timestamp(a)) & (jours <= pd.Timestamp(b))


# ----------------------------------------------------------------------------- principal
def main():
    L = []
    rng = np.random.default_rng(GRAINE)
    fed = set(pd.DatetimeIndex(fomc.annonces()))
    rech = pd.read_csv(DM.RECHERCHE)
    robot = pd.read_csv(DM.ROBOT)
    bars = pd.concat([rech, robot[robot["t"] > rech["t"].iloc[-1]]], ignore_index=True)
    z = DM.preparer(bars)
    _, _, Hm, Lm, _, _, _, _ = DM.RB.tableaux(bars)
    idx = univers(z, fed, EXPLO[0], COFFRE[1])
    jours = pd.DatetimeIndex([z["jours"][i] for i in idx])
    e, c = periode(jours, *EXPLO), periode(jours, *COFFRE)
    exclus_fed = sum(1 for i in z["jouables"] if z["jours"][i] in fed and z["jours"][i] <= pd.Timestamp(DM.FIN))
    exclus_court = sum(1 for i in z["jouables"] if DM.RB.jour_court(z["jours"][i]))
    res = calculer(z, idx)

    L.append("Piste 3 : renfort sur le trade qui tient (R1, R2, R3)")
    L.append("Regles : etude_large/pistes/README.md (commit a6e791f, fixees avant tout calcul). NQ minute, base V1 a 1 MNQ")
    L.append("(sans filtre sur 15 ans), +1 MNQ par renfort, 1,5 point par aller-retour et par unite ; pas de zone les jours")
    L.append("de la Fed ni les jours courts. Exploration 2011-2022, coffre 2023 -> 20 oct. 2026. Series en points nets par")
    L.append("seance (1 MNQ), 0 les seances sans renfort ; t = moyenne / ecart-type x racine(seances).")
    L.append("")
    L.append(f"BASE : minutes de la recherche + robot jusqu'au {DM.FIN} ; {len(idx)} seances de zone ({exclus_fed} jours de la"
             f" Fed retires, {exclus_court} jour court parmi les seances completes) : exploration {int(e.sum())},"
             f" coffre {int(c.sum())}")
    # V1 recalculee = delta_mesures trades_zone, trade par trade
    tz = DM.trades_zone(z, EXPLO[0], COFFRE[1])
    tz = tz[tz["jour"].isin(set(jours))]
    mien = [(j, me, s, pe, ms, ps) for j in jours for me, s, pe, ms, ps, _ in res[j]["trades"]]
    ref = list(tz[["jour", "minute_entree", "sens", "prix_entree", "minute_sortie", "prix_sortie"]].itertuples(index=False,
                                                                                                         name=None))
    bon_v1 = len(mien) == len(ref) and all(a[:3] == b[:3] and a[4] == b[4] and abs(a[3] - b[3]) < 1e-9 and
                                           abs(a[5] - b[5]) < 1e-9 for a, b in zip(mien, ref))
    L.append(f"  V1 recalculee ici = delta_mesures trades_zone, trade par trade : {'oui' if bon_v1 else 'NON'} ({len(mien)} trades)")
    v1 = np.array([res[j]["v1"] for j in jours])
    L.append(f"  V1 : exploration {v1[e].sum():+.2f} pt, t {PA.t_stat(v1[e]):+.2f}, Sharpe {PA.sharpe(v1[e]):+.2f} ;"
             f" coffre {v1[c].sum():+.2f} pt, t {PA.t_stat(v1[c]):+.2f}, Sharpe {PA.sharpe(v1[c]):+.2f}")
    if not bon_v1:
        print("\n".join(L))
        sys.exit("V1 differente de delta_mesures : arret")
    # placement des renforts : apres l'entree, avant la sortie, a un controle de 10 h 30 a 15 h 00 ou V1 a garde la
    # position ; R1 et R3 au premier controle apres l'entree, R2 au premier et au deuxieme
    mal = 0
    for j in jours:
        for t in res[j]["trades"]:
            me, s, pe, ms, ps, tenus = t
            mal += any(m % PAS or m <= me or m >= ms for m in tenus) or tenus != list(range(me + PAS, me + PAS * (len(tenus) + 1), PAS))
            for regle in TESTS:
                us = renforts(t, z["C"][z["jours"].get_loc(j)], z["sigma"][z["jours"].get_loc(j)], z["href"][z["jours"].get_loc(j)],
                              z["bref"][z["jours"].get_loc(j)], regle)
                attendu = [m for m in ([me + PAS, me + 2 * PAS] if regle == "R2" else [me + PAS]) if m < ms and m <= DERNIER]
                mal += any(u[0] not in attendu or u[1] != s or u[3] != ms for u in us)
                mal += regle != "R3" and [u[0] for u in us] != attendu
    L.append(f"  placement des renforts (controle tenu, apres l'entree, avant la sortie, 10 h 30 - 15 h 00, meme sens, meme"
             f" sortie que V1) : {'conforme' if mal == 0 else f'{mal} ERREURS'}")

    # ------------------------------------------------------------- controle a)
    n_auto, passe_auto, trente = autopsie()
    tr_e = [t for j in jours[e] for t in res[j]["trades"]]
    passe_v1 = sum(1 for t in tr_e if t[5])
    eligible = sum(1 for t in tr_e if t[5] and PREMIER <= t[5][0] <= DERNIER)
    tr_c = [t for j in jours[c] for t in res[j]["trades"]]
    eligible_c = sum(1 for t in tr_c if t[5] and PREMIER <= t[5][0] <= DERNIER)
    bon_a = n_auto == 2789 and passe_auto == 1655
    L.append("")
    L.append("CONTROLE a) les trades qui passent le premier controle (kb/zone_failles/autopsie.txt)")
    L.append(f"  moteur de l'autopsie (zone_failles/journal.py, V0, 2011-2022, jours sans changement d'echeance) : {n_auto} trades,"
             f" {passe_auto} passent le premier controle (duree > 30 min), {trente} durent 30 min ; autopsie 2 789 et 1 655"
             f" -> {'retrouve' if bon_a else 'ECART'}")
    L.append(f"  base de la piste (V1, sans les jours de la Fed), exploration : {len(tr_e)} trades, {passe_v1} passent le premier"
             f" controle, dont {eligible} avec un premier controle tenu entre 10 h 30 et 15 h 00 (renforts R1 possibles ;"
             f" README : environ 1 655) ; coffre : {eligible_c} (README : environ 500)")
    L.append(f"  -> controle a) {'PASSE' if bon_a else 'ECHEC'}")

    # ------------------------------------------------------------- regard vers le futur
    essais, err, chg = regard_futur(z, idx, rng)
    e_s, e_v, e_r = verifier_niveaux(bars, z, idx, rng)
    L.append("")
    L.append("REGARD VERS LE FUTUR")
    L.append(f"  {essais} cas (300 seances x 12 controles) : tout ce qui suit le controle m est brouille -> {err} decision changee"
             f" jusqu'a m (entrees, sorties, renforts R1-R3 et seuil de R3) ; la suite change dans {chg} cas (le brouillage agit)")
    L.append(f"  sigma recalcule a la main (14 seances completes avant le jour) : ecart max {e_s:.1e} ; VWAP (minutes <= m) :"
             f" {e_v:.1e} ; references max/min(ouverture, veille) : {e_r:.1e}")
    L.append("  renfort : entree a la cloture de la minute du controle, apres la decision de V1 a ce controle ; seuil R3 avec le")
    L.append("  sigma et le prix de cette minute ; sortie = sortie de V1, decidee plus tard avec les memes regles.")
    sans_futur = err == 0 and e_s < 1e-12 and e_v < 1e-6 and e_r < 1e-9
    L.append(f"  -> {'aucun regard vers le futur' if sans_futur else 'PROBLEME'}")

    # ------------------------------------------------------------- challenges : controle du moteur
    unites_v1 = {j: [t[:5] for t in res[j]["trades"]] for j in jours}
    ch_v1 = chemins(z, Hm, Lm, unites_v1)
    ch_pd = PD.chemins_zone()
    bon_ch = all(np.array_equal(a, b) for a, b in zip(ch_v1[1:], ch_pd[1:])) and ch_v1[0].equals(ch_pd[0])
    ecart_ch = max(float(np.abs(a - b).max()) for a, b in zip(ch_v1[1:], ch_pd[1:]))
    L.append(f"  chemins des challenges (recopie de partie_d.chemins_zone) avec les trades de V1 = original : "
             f"{'oui' if bon_ch else 'NON'} (ecart max {ecart_ch:.1e} $)")

    base_lucid = {q: defis(ch_v1, LUCID, q) for q in (1, 2, 3)}
    base_bul = {q: defis(ch_v1, BULENOX, q) for q in (1, 2, 3)}

    # ------------------------------------------------------------- tests
    sorties = []
    for regle in TESTS:
        r = series(res, jours, regle)
        rb = series(res, jours, regle, 0.0)
        u_e = [(j, u) for j in jours[e] for u in res[j][regle]]
        u_c = [(j, u) for j in jours[c] for u in res[j][regle]]
        te, tc = PA.t_stat(r[e]), PA.t_stat(r[c])
        L.append("")
        L.append(f"=== TEST {regle} (unilateral : t net >= 2 en exploration) ===")
        L.append(f"  exploration : {len(u_e)} renforts ({sum(1 for j in jours[e] if res[j][regle])} seances), renfort seul"
                 f" {r[e].sum():+.2f} pt nets ({r[e].sum() / max(len(u_e), 1):+.2f} par renfort), t net {te:+.2f}"
                 f" (p unilateral {PA.p_unilateral(te):.4f}) ; avant frais {rb[e].sum():+.2f} pt, t {PA.t_stat(rb[e]):+.2f}")
        L.append(f"  coffre      : {len(u_c)} renforts ({sum(1 for j in jours[c] if res[j][regle])} seances), renfort seul"
                 f" {r[c].sum():+.2f} pt nets ({r[c].sum() / max(len(u_c), 1):+.2f} par renfort), t net {tc:+.2f} ;"
                 f" avant frais {rb[c].sum():+.2f} pt, t {PA.t_stat(rb[c]):+.2f}")
        ouv = np.array([z["C"][z["jours"].get_loc(j), 0] for j in jours])
        L.append(f"  information (ne sert a aucune decision ; unite du t, voir ecarts) : meme serie en rendement (points /"
                 f" ouverture du jour) : t exploration {PA.t_stat(r[e] / ouv[e]):+.2f}, coffre {PA.t_stat(r[c] / ouv[c]):+.2f}")
        c1 = te >= 2.0
        c2 = tc >= 1.5 and np.sign(tc) == np.sign(te)
        L.append(f"  1) exploration t net >= 2 : t {te:+.2f} -> {'oui' if c1 else 'non'} (Benjamini-Hochberg : calcule sur les"
                 " 17 tests ensemble)")
        L.append(f"  2) coffre t net >= 1,5, meme signe : t {tc:+.2f} -> {'oui' if c2 else 'non'}")
        # 3) Sharpe, V1 + renfort ramenee au meme ecart-type que V1 sur 2011-2022
        vr = v1 + r
        k = v1[e].std(ddof=1) / vr[e].std(ddof=1)
        se_v1, sc_v1 = PA.sharpe(v1[e]), PA.sharpe(v1[c])
        se_r, sc_r = PA.sharpe(k * vr[e]), PA.sharpe(k * vr[c])
        c3 = se_r > se_v1 and sc_r > sc_v1
        L.append(f"  3) Sharpe de V1 + renfort (x {k:.3f}, meme ecart-type que V1 sur 2011-2022) contre V1 : exploration"
                 f" {se_r:+.3f} contre {se_v1:+.3f} ; coffre {sc_r:+.3f} contre {sc_v1:+.3f} -> {'oui' if c3 else 'non'}"
                 " (le facteur ne change pas le Sharpe)")
        # 4) placebo
        ans = jours.year
        reel_an = pd.Series([j.year for j, _ in u_e]).value_counts().to_dict()
        reserve = {y: np.array([net(u) for j in jours[e & (ans == y)] for u in res[j]["reserve"]]) for y in reel_an}
        reel = sum(net(u) for _, u in u_e)
        pla = np.array([sum(rng.choice(reserve[y], size=nb, replace=False).sum() for y, nb in reel_an.items())
                        for _ in range(PLACEBOS)])
        part = (pla < reel).mean() * 100
        c4 = part >= 95.0
        taille_res = sum(len(v) for v in reserve.values())
        L.append(f"  4) placebo (exploration, {PLACEBOS} tirages, {len(u_e)} renforts par tirage, meme nombre par an, tires parmi"
                 f" {taille_res} controles de 10 h 30 a 15 h 00 en position, meme sens, meme sortie) : placebos moyenne"
                 f" {pla.mean():+.1f} pt, 95e centile {np.percentile(pla, 95):+.1f} ; reel {reel:+.1f} fait mieux que {part:.1f} %"
                 f" -> {'oui' if c4 else 'non'}")
        # placebo du coffre, a titre d'information
        reel_c = pd.Series([j.year for j, _ in u_c]).value_counts().to_dict()
        res_c = {y: np.array([net(u) for j in jours[c & (ans == y)] for u in res[j]["reserve"]]) for y in reel_c}
        rc_ = sum(net(u) for _, u in u_c)
        pla_c = np.array([sum(rng.choice(res_c[y], size=nb, replace=False).sum() for y, nb in reel_c.items())
                          for _ in range(PLACEBOS)])
        L.append(f"     information, meme placebo au coffre : reel {rc_:+.1f} pt fait mieux que {(pla_c < rc_).mean() * 100:.1f} %"
                 f" (moyenne {pla_c.mean():+.1f}, 95e centile {np.percentile(pla_c, 95):+.1f})")
        # 5) Lucid Flex
        unites_r = {j: unites_v1[j] + [u for u in res[j][regle]] for j in jours}
        ch_r = chemins(z, Hm, Lm, unites_r)
        lu = defis(ch_r, LUCID, 1)
        comp = [1, 2] + ([3] if EXPO[regle] == 3 else [])
        ok5 = []
        L.append(f"  5) Lucid Flex 50K (partie D, departs 2023-2026, {lu['n']} departs) : 1 MNQ + renforts valide {lu['valide']:.1f} %"
                 f" (perdu {lu['perdu']:.1f} %, expire {lu['expire']:.1f} %)")
        for q in comp:
            b = base_lucid[q]
            dv, dp = lu["valide"] - b["valide"], lu["perdu"] - b["perdu"]
            o = dv >= 3.0 and dp <= 3.0
            ok5.append(o)
            L.append(f"     contre V1 a {q} MNQ : valide {b['valide']:.1f} %, perdu {b['perdu']:.1f} % -> {dv:+.1f} points valides,"
                     f" {dp:+.1f} points perdus -> {'oui' if o else 'non'}")
        c5 = all(ok5)
        L.append(f"     -> {'oui' if c5 else 'non'} (au moins +3 points valides et au plus +3 points perdus contre chaque comparaison"
                 f"{' ; R2 : aussi contre V1 a 3 MNQ, meme exposition maximale' if EXPO[regle] == 3 else ''})")
        bu = defis(ch_r, BULENOX, 1)
        L.append(f"     Bulenox Legacy 50K (partie D, 30 jours, publie) : 1 MNQ + renforts valide {bu['valide']:.1f} % (perdu"
                 f" {bu['perdu']:.1f} %, {bu['n']} departs) ; V1 " + ", ".join(
                     f"{q} MNQ {base_bul[q]['valide']:.1f} % (perdu {base_bul[q]['perdu']:.1f} %)" for q in comp))
        propre = c1 and c2 and c3 and c4 and c5
        L.append(f"  -> criteres propres (hors Benjamini-Hochberg) : {'PASSENT' if propre else 'ECHEC'} (1 {'oui' if c1 else 'non'},"
                 f" 2 {'oui' if c2 else 'non'}, 3 {'oui' if c3 else 'non'}, 4 {'oui' if c4 else 'non'}, 5 {'oui' if c5 else 'non'})")
        sorties.append(dict(nom=regle, te=te, tc=tc, c=(c1, c2, c3, c4, c5), propre=propre, r=r, u_e=u_e, u_c=u_c,
                            ch=ch_r, lucid=lu, bul=bu, vr=vr))

    # ------------------------------------------------------------- controle b) ES
    L.append("")
    L.append("CONTROLE b) ES minute (2011 -> 25 sept. 2026), meme regle, avant frais : meme signe que le NQ avant frais")
    es = pd.read_csv(ES)
    ze = DM.preparer(es)
    ie = univers(ze, fed, EXPLO[0], COFFRE[1])
    je = pd.DatetimeIndex([ze["jours"][i] for i in ie])
    rese = calculer(ze, ie, cout=0.0)
    ee, ce = periode(je, *EXPLO), periode(je, *COFFRE)
    bon_b = True
    for s_ in sorties:
        rb_nq = series(res, jours, s_["nom"], 0.0)
        rb_es = series(rese, je, s_["nom"], 0.0)
        lig = []
        for nom_p, mn, me_ in (("exploration", e, ee), ("coffre", c, ce)):
            same = np.sign(rb_es[me_].sum()) == np.sign(rb_nq[mn].sum())
            bon_b &= bool(same)
            lig.append(f"{nom_p} ES {rb_es[me_].sum():+.2f} pt (t {PA.t_stat(rb_es[me_]):+.2f}), NQ {rb_nq[mn].sum():+.2f} pt"
                       f" (t {PA.t_stat(rb_nq[mn]):+.2f}) -> {'meme signe' if same else 'SIGNE OPPOSE'}")
        L.append(f"  {s_['nom']} : " + " ; ".join(lig))
    L.append(f"  ({len(ie)} seances ES hors Fed : exploration {int(ee.sum())}, coffre {int(ce.sum())})")
    L.append(f"  -> controle b) {'PASSE' if bon_b else 'ECHEC'} (meme signe sur les deux periodes)")

    # ------------------------------------------------------------- controle c) annees et heures
    L.append("")
    L.append("CONTROLE c) resultats par annee et par heure du renfort (points nets des seules unites ajoutees)")
    for s_ in sorties:
        tous = s_["u_e"] + s_["u_c"]
        df = pd.DataFrame([(j.year, u[0], net(u)) for j, u in tous], columns=["an", "m", "net"])
        L.append(f"  {s_['nom']} par annee (renforts / points / par renfort) :")
        g = df.groupby("an")["net"].agg(["size", "sum", "mean"])
        L.append("    " + " ; ".join(f"{a} {int(x['size'])} / {x['sum']:+.0f} / {x['mean']:+.2f}" for a, x in g.iterrows()))
        L.append(f"    annees positives : exploration {int((g.loc[g.index <= 2022, 'sum'] > 0).sum())} sur"
                 f" {int((g.index <= 2022).sum())}, coffre {int((g.loc[g.index >= 2023, 'sum'] > 0).sum())} sur"
                 f" {int((g.index >= 2023).sum())}")
        for nom_p, sel in (("exploration", df["an"] <= 2022), ("coffre", df["an"] >= 2023)):
            h = df[sel].groupby("m")["net"].agg(["size", "sum", "mean"])
            L.append(f"    {nom_p} par heure : " + " ; ".join(f"{heure(m)} {int(x['size'])} / {x['sum']:+.0f} / {x['mean']:+.2f}"
                                                         for m, x in h.iterrows()))

    # ------------------------------------------------------------- controle d) pire seance
    L.append("")
    L.append("CONTROLE d) pire seance avec renfort (1 MNQ de base + 1 MNQ par renfort, 2 $ par point)")
    jc = ch_v1[0]
    for s_ in sorties:
        vr = s_["vr"]
        pire_h = vr.min() * DM.RB.PT
        jp = jours[np.argmin(vr)]
        _, clo, bas, _ = s_["ch"]
        pire_auj = clo[:, -1].min()
        creux_auj = bas.min(axis=1).min()
        jcr = jc[np.argmin(bas.min(axis=1))]
        maxu = max(max_simultane(us) for us in ({j: unites_v1[j] + res[j][s_["nom"]] for j in jours}).values())
        L.append(f"  {s_['nom']} : pire seance aux prix d'epoque {pire_h:+.0f} $ ({jp.date()}) ; au prix du 20 oct. 2026 :"
                 f" pire cloture {pire_auj:+.0f} $, pire creux dans la seance {creux_auj:+.0f} $ ({jcr.date()}) ;"
                 f" unites au plus {maxu} MNQ")
        L.append(f"     limite du jour de Bulenox ({LIMITE_JOUR_BULENOX:.0f} $), aux prix d'epoque et 1 MNQ de base :"
                 f" {'depassee' if pire_h < -LIMITE_JOUR_BULENOX else 'pas depassee'}"
                 f" ; au prix d'aujourd'hui, le pire creux reste sous la limite jusqu'a {LIMITE_JOUR_BULENOX / -creux_auj:.2f} MNQ"
                 f" de base seulement ; a la taille du bot chez Bulenox (4 MNQ puis 6) : {4 * maxu} a {6 * maxu} MNQ au plus,"
                 f" creux {4 * creux_auj:+.0f} a {6 * creux_auj:+.0f} $")
    _, clo1, bas1, _ = ch_v1
    L.append(f"  V1 seule, aux prix d'epoque : pire seance {v1.min() * DM.RB.PT:+.0f} $ a 1 MNQ, {2 * v1.min() * DM.RB.PT:+.0f} $ a"
             f" 2 MNQ ({jours[np.argmin(v1)].date()}) ; au prix du 20 oct. 2026 (2012-2026) : pire cloture {clo1[:, -1].min():+.0f}"
             f" $ a 1 MNQ, {2 * clo1[:, -1].min():+.0f} $ a 2 MNQ ; pire creux {bas1.min(axis=1).min():+.0f} / "
             f"{2 * bas1.min(axis=1).min():+.0f} $")
    L.append("  (prix du 20 oct. 2026 : chemins de la partie D, seances 2012-2026, chaque seance ramenee au niveau du jour)")
    L.append("  nombre maximal de contrats d'un compte Bulenox 50K : non documente dans le depot ; guides tiers d'octobre 2026 :")
    L.append("  6 ou 7 contrats (60 a 70 micros), a confirmer sur le tableau de bord Bulenox. Le renfort reste en dessous a 1 MNQ")
    L.append("  et aux tailles du bot ; c'est la limite du jour qui borne la taille.")

    # ------------------------------------------------------------- controle e) base ZL
    L.append("")
    L.append("CONTROLE e) base ZL (information) : la piste sortie_vwap ne passe pas ses criteres propres (sortie_vwap/resultats.txt) ;")
    L.append("  sa decision prevue est alors de mettre ZL (tenir, sortie seulement a la limite) dans le robot virtuel. Renfort")
    L.append("  recalcule sur ZL, ou le controle du cas VWAP devient un controle tenu :")
    rzl = calculer(z, idx, base="ZL")
    vzl = np.array([rzl[j]["v1"] for j in jours])
    n_cas = sum(len(res[j]["trades"]) - len(rzl[j]["trades"]) for j in jours)
    L.append(f"  ZL - V1 = {vzl.sum() - v1.sum():+.2f} pt pour {n_cas} rachats evites (1,5 x {n_cas} = {1.5 * n_cas:+.2f})")
    for regle in TESTS:
        r = series(rzl, jours, regle)
        L.append(f"  {regle} sur ZL : exploration {sum(len(rzl[j][regle]) for j in jours[e])} renforts {r[e].sum():+.2f} pt,"
                 f" t {PA.t_stat(r[e]):+.2f} ; coffre {sum(len(rzl[j][regle]) for j in jours[c])} renforts {r[c].sum():+.2f} pt,"
                 f" t {PA.t_stat(r[c]):+.2f}")

    # ------------------------------------------------------------- controle f) P1 et P2
    L.append("")
    L.append("CONTROLE f) P1 (Databento, avril - 1er oct. 2026) et P2 (Rithmic, 2 - 16 oct. 2026), vrai delta, filtre B du bot")
    L.append("  (trades de zone gardes si le delta des 30 minutes va dans leur sens ; barres du robot, comme delta_mesures) :")
    rob = robot[robot["t"] <= DM.FIN + " 23:59"]
    zr = DM.preparer(rob)
    deltas = {**DM.par_jour(DM.minutes_databento()), **DM.par_jour(DM.minutes_rithmic())}
    pos_r = {j: i for i, j in enumerate(zr["jours"])}
    for per, (a, b) in (("P1", DM.P1), ("P2", DM.P2)):
        tr = DM.mesures(DM.trades_zone(zr, a, b), {j: v for j, v in deltas.items() if pd.Timestamp(a) <= j <= pd.Timestamp(b)})
        g = DM.garde(tr, "brut", 0)
        n, p = int(g.sum()), float(tr.loc[g, "points"].sum())
        rn, rp = DM.REFERENCE[("B", per)]
        L.append(f"  {per} : {n} trades gardes {p:+.2f} pt (reference {rn} trades {rp:+.2f} ->"
                 f" {'identique' if n == rn and abs(p - rp) < 1e-6 else 'ECART'}) ; dont"
                 f" {int(tr.loc[g, 'jour'].isin(fed).sum())} un jour de la Fed")
        cache = {}
        for regle in TESTS:
            us, us_hf = [], []
            for row in tr[g].itertuples():
                i = pos_r[row.jour]
                if i not in cache:
                    cache[i] = seance(zr["C"][i], zr["sigma"][i], zr["vwap"][i], zr["href"][i], zr["bref"][i])
                t = [x for x in cache[i] if x[0] == row.minute_entree][0]
                u = renforts(t, zr["C"][i], zr["sigma"][i], zr["href"][i], zr["bref"][i], regle)
                us += u
                if row.jour not in fed:
                    us_hf += u
            nets = np.array([net(x) for x in us])
            L.append(f"     {regle} : {len(us)} renforts sur les trades gardes, {nets.sum():+.2f} pt nets"
                     f" ({int((nets > 0).sum())} gagnants, moyenne {nets.mean() if len(nets) else 0.0:+.2f}, pire"
                     f" {nets.min() if len(nets) else 0.0:+.2f}, meilleur {nets.max() if len(nets) else 0.0:+.2f}) ; hors Fed"
                     f" {len(us_hf)} renforts {sum(net(x) for x in us_hf):+.2f} pt")

    # ------------------------------------------------------------- bilan
    L.append("")
    L.append("BILAN (Benjamini-Hochberg a 10 % : calcule ensuite sur les 17 tests des 5 pistes)")
    L.append("  test  t explo  p unilateral  t coffre  1 2 3 4 5  criteres propres")
    for s_ in sorties:
        L.append(f"  {s_['nom']:4}  {s_['te']:+7.2f}  {PA.p_unilateral(s_['te']):12.4f}  {s_['tc']:+8.2f}  "
                 + " ".join("o" if x else "n" for x in s_["c"]) + f"  {'passent' if s_['propre'] else 'echec'}")
    L.append("  controles : a) " + ("passe" if bon_a else "echec") + ", b) " + ("passe" if bon_b else "echec")
             + ", c) publie, d) publie, e) publie (information), f) publie ; regard vers le futur : "
             + ("aucun" if sans_futur else "PROBLEME") + " ; moteur des challenges : " + ("identique" if bon_ch else "ECART"))
    if not any(s_["propre"] for s_ in sorties):
        L.append("  Decision : aucun renfort n'est retenu ; le bot garde une taille fixee a l'entree.")
    else:
        L.append("  Decision : les tests qui passent leurs criteres propres ne sont retenus que s'ils passent aussi")
        L.append("  Benjamini-Hochberg sur les 17 tests, puis la contre-verification adverse, puis l'argent virtuel.")
    L.append("")
    L.append("INTERPRETATIONS FIXEES AVANT LE CALCUL (le README ne tranche pas)")
    L.append("  - base sur 15 ans : V1 sans filtre (pas de delta avant 2026), sans les jours de la Fed ni les jours courts,")
    L.append("    comme le bot (reglages Bulenox de cerveau/savoir.json) et toutes les vagues de l'etude large ; P1 et P2 avec le")
    L.append("    filtre B en description (controle f).")
    L.append("  - t en points nets par seance (1 MNQ), comme les autres pistes et delta_mesures ; le t en rendement est donne a")
    L.append("    titre d'information seulement.")
    L.append("  - R3 : gain latent = sens x (cloture du controle - prix d'entree), avant frais ; sigma de la minute du controle.")
    L.append("  - R2 : si le deuxieme controle tenu est 15 h 30, un seul renfort ; premier controle tenu a 15 h 30 : aucun.")
    L.append("  - placebo : reserve = controles de 10 h 30 a 15 h 00 ou V1 est en position apres sa decision (entrees, rachats")
    L.append("    et controles tenus) ; tirage sans remise par annee ; juge sur le total net de l'exploration (le coffre en")
    L.append("    information) ; 'faire mieux' = total reel strictement au-dessus d'au moins 95 % des placebos.")
    L.append("  - Lucid : +3 points valides ET au plus +3 points perdus contre chaque comparaison (V1 a 1 MNQ et a 2 MNQ ; pour R2,")
    L.append("    aussi V1 a 3 MNQ, meme exposition maximale). Bulenox publie avec le moteur de la partie D (30 jours) : le moteur")
    L.append("    de delta_mesures ne tient qu'une position de zone a la fois et ne peut pas porter d'unite ajoutee.")
    L.append("  - controle b) : signe du total avant frais de l'ES contre celui du NQ, sur chaque periode.")
    L.append("")
    L.append("LECTURE")
    L.append("  R1 et R2 passent les criteres 1 a 4 en points (t 2,65 et 2,56 ; coffre 1,72 et 1,76 ; placebo 98 % et 100 %),")
    L.append("  mais pas le critere 5 : chez Lucid, 1 MNQ + renfort valide autant que V1 a 2 MNQ (30,5 % contre 31,7 %), bien")
    L.append("  moins que V1 a 1 MNQ (54,6 %), et perd deux fois plus souvent. Le renfort ajoute du risque au moment ou la zone")
    L.append("  gagne deja, ce qui ne sert pas un challenge. Trois signaux de fragilite : en rendement (points / prix), le t")
    L.append("  d'exploration tombe a 1,37 et 1,35 (le gain vient des annees 2018-2022, ou le point du NQ vaut le plus) ; 5")
    L.append("  annees positives sur 12 en exploration ; l'ES, positif en exploration, est negatif avant frais au coffre. R3 echoue")
    L.append("  partout. Aucun renfort n'entre au robot virtuel.")

    texte = "\n".join(L)
    print(texte)
    (ICI / "resultats.txt").write_text(texte + "\n")


def max_simultane(us):
    """Nombre maximal d'unites ouvertes en meme temps dans une seance (entree a la cloture de me, sortie a celle de ms)."""
    if not us:
        return 0
    k = np.zeros(N + 1, int)
    for me, _, _, ms, _ in us:
        k[me + 1:ms + 1] += 1
    return int(k.max())


if __name__ == "__main__":
    main()
