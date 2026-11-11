"""Partie I : tenir la regle d'inactivite de Bulenox avec la zone elle-meme (bande plus etroite les jours de secours).
Regles : REGLES.md, partie I.   Usage : python3 inactivite.py   (ecrit resultats/partie_i.txt)
"""
import json

import numpy as np
import pandas as pd

import compte as Cp
import donnees as D

N = D.N


def zone_brute(M, k, pas=30, jours=14):
    """Zone corrigee V1 sans filtre : liste de trades (seance, sens, m_debut du chemin, m_fin, entree, sortie)."""
    J, O, H, L, C, V, ok = M["J"], M["O"], M["H"], M["L"], M["C"], M["V"], M["ok"]
    S = len(J)
    mv = np.abs(C / O[:, :1] - 1)
    sigma = np.full_like(mv, np.nan)
    sigma[ok] = pd.DataFrame(mv[ok]).rolling(jours, min_periods=jours).mean().shift(1).values
    seg = np.cumsum(np.r_[0, (M["contrat"][1:] != M["contrat"][:-1]).astype(int)])
    idx = np.where(ok, np.arange(S), -1)
    prec = np.r_[-1, np.maximum.accumulate(idx)[:-1]]
    prec = np.where((prec >= 0) & (seg[np.maximum(prec, 0)] == seg), prec, -1)
    veille = np.where(prec >= 0, C[np.maximum(prec, 0), N - 1], np.nan)
    typ = (H + L + C) / 3; cv = np.cumsum(V, axis=1)
    vwap = np.where(cv > 0, np.cumsum(typ * V, axis=1) / np.where(cv > 0, cv, 1), np.cumsum(typ, axis=1) / np.arange(1, N + 1))
    out = []
    for d in range(S):
        if not ok[d] or np.isnan(veille[d]) or np.isnan(sigma[d, pas]):
            continue
        hr = max(O[d, 0], veille[d]); br = min(O[d, 0], veille[d]); pos = 0; e = 0.0; m0 = 0
        for m in range(pas, N, pas):
            p = C[d, m]; ub = hr * (1 + k * sigma[d, m]); lb = br * (1 - k * sigma[d, m])
            if pos > 0 and p <= max(ub, vwap[d, m]):
                out.append((d, 1, m0 + 1, m, e, p)); pos = 0
            elif pos < 0 and p >= min(lb, vwap[d, m]):
                out.append((d, -1, m0 + 1, m, e, p)); pos = 0
            if pos == 0:
                if p > ub:
                    pos, e, m0 = 1, p, m
                elif p < lb:
                    pos, e, m0 = -1, p, m
        if pos != 0:
            out.append((d, pos, m0 + 1, N - 1, e, C[d, N - 1]))
    return out


def principal():
    B = Cp.Banc("2026-11-02"); M = B.M; J = B.J
    L = ["Partie I : tenir la règle d'inactivité avec la zone elle-même (Master Bulenox 50K, 2017 → 2 novembre 2026).", ""]
    # controle du moteur a k = 1 contre les trades verifies de la recherche
    ref = pd.read_csv(D.KB / "filtre_h1/trades_zone.csv"); fin_ref = ref.jour.max()
    z1 = zone_brute(M, 1.0)
    moi = {(J[t[0]], t[2] - 1, t[1]): t[1] * (t[5] - t[4]) for t in z1 if J[t[0]] <= fin_ref}
    eux = {(r.jour, int(r.minute), int(r.sens)): float(r.points) for r in ref.itertuples()}
    communs = set(moi) & set(eux); ecart = max(abs(moi[c] - eux[c]) for c in communs) if communs else float("nan")
    L += [f"Contrôle du moteur (k = 1, jusqu'au {fin_ref}) : {len(eux)} trades de référence, {len(moi)} ici, {len(communs)} identiques "
          f"(jour, minute, sens), écart maximal de gain sur ces trades {ecart:.2f} point.", ""]
    res = dict(controle=dict(reference=len(eux), ici=len(moi), communs=len(communs), ecart_max=ecart))
    m0 = B.mesurer(B.zf); ms0 = B.mesurer(B.zf, inactivite=False)
    L += [Cp.resume("T0 · le bot seul (Z12F, limite 1 000 $, frein)", m0),
          f"    sans la règle d'inactivité : {ms0['trois']:.0%} au 3e retrait, {ms0['plancher']:.0%} perdus par le plancher, touché {ms0['touche_master']:,.0f} $".replace(",", " "), ""]
    res["T0"] = dict(**m0, sans_regle=ms0)
    js = {t[0] for t in B.zf}
    for ident, k in (("IB100", 1.0), ("IB75", 0.75), ("IB50", 0.5)):
        zk = z1 if k == 1.0 else zone_brute(M, k)
        par = {}
        for t in zk:
            par.setdefault(t[0], []).append(t)
        # avantage de la zone brute a cette bande (toutes les seances completes)
        S = len(J); z = np.zeros(S); a = lambda i, ty: np.array([x[i] for x in zk], dtype=ty)
        r, _ = Cp._journees(S, a(0, np.int64), a(1, np.int64), a(2, np.int64), a(3, np.int64), a(4, np.float64), a(5, np.float64), M["H"], M["L"], 1.0, 1000.0,
                            D.FRAIS, D.PREF, Cp.GLISSE, z, z.copy())
        g = M["ok"] & (J <= "2026-11-02") & (J >= "2011-02-01"); ex = J[g] <= D.FIN_EXPLO
        brut = dict(trades=len(zk), t=D.tstat(r[g]), t_explo=D.tstat(r[g][ex]), t_controle=D.tstat(r[g][~ex]), par_seance=float(r[g].mean()),
                    seances_tradees=float(np.mean([s in par for s in np.nonzero(g)[0]])))
        # jours de secours : 3 jours de trading sans trade, jours du fichier compris
        tr = []; vide = 0; nsec = 0; nsec_trade = 0
        for i, s in enumerate(B.test):
            if i > 0:
                vide += B.gap[i]
            if vide >= 3:
                jour = par.get(s, []); nsec += 1; nsec_trade += bool(jour)
            else:
                jour = [t for t in B.zf if t[0] == s] if s in js else []
            tr += jour
            vide = 0 if jour else vide + 1
        tr.sort(key=lambda t: (t[0], t[2]))
        m = B.mesurer(tr); ms = B.mesurer(tr, inactivite=False)
        ok = m["inactivite"] == 0 and m["plancher"] <= 0.20 and m["touche_master"] > 0
        res[ident] = dict(k=k, zone_brute=brut, jours_secours=nsec, jours_secours_avec_trade=nsec_trade, **m, sans_regle=ms, adoptee=bool(ok))
        L += [f"Zone brute à k = {k} : {brut['trades']} trades, {brut['seances_tradees']:.0%} des séances, {brut['par_seance']:+.1f} $ par séance, "
              f"t {brut['t']:.2f} (exploration {brut['t_explo']:.2f}, contrôle {brut['t_controle']:.2f}).",
              Cp.resume(f"{ident} · le bot + la zone brute à k = {k} les jours de secours ({nsec} jours depuis 2014, dont {nsec_trade} avec un trade)", m),
              f"    sans la règle d'inactivité : {ms['trois']:.0%} au 3e retrait, {ms['plancher']:.0%} perdus par le plancher, touché {ms['touche_master']:,.0f} $".replace(",", " "),
              f"    → {'ADOPTÉE' if ok else 'non adoptée'} ({m['episodes']} dates de perte distinctes{' : chiffre fragile' if m['episodes'] < 3 else ''})", ""]
    (D.ICI / "resultats/partie_i.txt").write_text("\n".join(L) + "\n")
    json.dump(res, open(D.ICI / "resultats/partie_i.json", "w"), indent=1, ensure_ascii=False)
    print("\n".join(L))


if __name__ == "__main__":
    principal()
