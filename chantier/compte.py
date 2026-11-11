"""Le compte Master Bulenox 50K (Option 2) : le bot seul, puis le bot avec la nuit. Regles : REGLES.md, partie N.

Simulateur repris de la vague 10 de l'arene (ml/arene/vague10.py, `vie_contrat` et `_journees_cap`), avec en plus la
nuit : elle appartient a la journee de trading du lendemain, son resultat entame la limite du jour.

Usage : python3 compte.py   (ecrit resultats/compte.txt)
"""
import json
import re

import numba as nb
import numpy as np
import pandas as pd

import donnees as D
import nuit as Nn

DLL = 1100.0            # limite du jour de la firme
GLISSE = 1.0            # point de NQ perdu a une sortie forcee par la limite du jour
LIGNE = re.compile(r"^(\d{4}-\d{2}-\d{2}) (achat|vente|sortie|stop)\b(?: (\d+)h(\d+))?(?: (\d+)h(\d+))?.*? a ([0-9.]+)")
ARENE = D.OP / "ml/arene/donnees"


def zone_journal(J):
    """Trades de la zone C2 + Q1 (journal de rejeu du bot, sans le filtre delta) : (seance, sens, m_entree, m_sortie, entree, sortie)."""
    pos = {j: i for i, j in enumerate(J)}; out = []
    for f, de, a in ((ARENE / "c2q1.txt", "2011-01-01", "2026-10-27"), (ARENE / "zone.txt", "2026-10-28", "2026-11-02")):
        ouvert = None
        for l in f.read_text().splitlines():
            g = LIGNE.match(l)
            if not g or "ecarte" in l or "RSI" in l or not (de <= g.group(1) <= a):
                continue
            h, mi = int(g.group(5) or g.group(3)), int(g.group(6) or g.group(4))
            mm, px = h * 60 + mi - 570, float(g.group(7))
            if g.group(2) in ("achat", "vente"):
                ouvert = (g.group(1), 1 if g.group(2) == "achat" else -1, mm, px)
            elif ouvert:
                s = pos.get(ouvert[0])
                if s is not None:
                    out.append((s, ouvert[1], ouvert[2] + 1, min(389, max(ouvert[2], mm)), ouvert[3], px))
                ouvert = None
    return sorted(out, key=lambda t: (t[0], t[2]))


def fed():
    return {l.strip() for l in open(ARENE / "fomc.txt") if l.strip() and not l.startswith("#")}


@nb.njit(cache=True)
def _journees(S, ts, tsens, tdeb, tfin, te, tx, H, L, taille, limite, frais, pref, glisse, gn, cn):
    """Resultat et creux de chaque journee de trading : la nuit d'abord (gn, cn pour 1 MNQ), puis les trades de la seance.
    Limite du jour sur realise + latent ; le trade en cours est coupe a la limite, plus rien ensuite."""
    res = gn * taille; dip = np.minimum(cn * taille, 0.0)
    k = 0; n = len(ts)
    while k < n:
        s = ts[k]; real = res[s]; creux = dip[s]; arret = real <= -limite
        while k < n and ts[k] == s:
            if not arret:
                sens = tsens[k]; e = te[k]; ech = 2.0 * pref / e * taille
                for m in range(tdeb[k], tfin[k] + 1):
                    eq = real + sens * ((L[s, m] if sens > 0 else H[s, m]) - e) * ech
                    if eq < creux:
                        creux = eq
                    if eq <= -limite:
                        real = -limite - glisse * ech - frais * taille; arret = True
                        break
                if not arret:
                    real += sens * (tx[k] - e) * ech - frais * taille
                    if real <= -limite:
                        arret = True
                if real < creux:
                    creux = real
            k += 1
        res[s] = real; dip[s] = creux
    return res, dip


class Banc:
    def __init__(self, fin="2026-11-02"):
        M = D.nq_minutes(); self.M = M; J = M["J"]; self.J = J
        an = np.array([int(j[:4]) for j in J])
        self.test = np.nonzero(M["ok"] & (an >= 2014) & (J <= fin))[0]
        self.n = len(self.test); self.jours = J[self.test]
        self.d17 = int(np.searchsorted(self.jours, "2017-01-01"))
        self.gap = np.zeros(self.n, int); self.gap[1:] = np.diff(self.test) - 1
        V = D.clotures(("VIX", "VIX3M")); tous = pd.Index(J)
        veille = V.reindex(tous.union(V.index)).sort_index().ffill().shift(1).reindex(tous)
        self.inv = (veille["VIX"] - veille["VIX3M"]).to_numpy() >= 0
        F = fed(); self.fed = np.array([j in F for j in J])
        self.zone = zone_journal(J)
        self.zf = [t for t in self.zone if not self.inv[t[0]] and not self.fed[t[0]]]

    def journees(self, tr, taille, limite, gn=None, cn=None):
        S = len(self.J); z = np.zeros(S)
        a = lambda k, ty: np.array([x[k] for x in tr], dtype=ty)
        r, d = _journees(S, a(0, np.int64), a(1, np.int64), a(2, np.int64), a(3, np.int64), a(4, np.float64), a(5, np.float64),
                         self.M["H"], self.M["L"], float(taille), float(min(limite, DLL)), D.FRAIS, D.PREF, GLISSE,
                         z if gn is None else gn.copy(), z if cn is None else cn.copy())
        return r[self.test], d[self.test]

    def vie(self, R0, D0, R1, D1, T, i0, frein=750.0, inactivite=True):
        """Un Master neuf au jour i0 puis, au 3e retrait, un funded (hypotheses de la vague 10)."""
        o = dict(issue="en cours", fin=None, j1=None, j3=None, touche_m=-148.0, funded=None)
        solde = haut = base = 50000.0; meil = 0.0; jrs = 0; nret = 0; vide = 0; perte = 2500.0; phase = "M"; i_f = None; touche_f = 0.0

        def fin(cause, i):
            if phase == "M":
                o["issue"] = cause; o["fin"] = i
            else:
                o["funded"] = dict(issue=cause, touche=touche_f, fin=i, jours=i - i_f)
            return o
        for i in range(i0, self.n):
            if i > i0:
                vide += self.gap[i]
            if inactivite and vide >= 5:
                return fin("inactivité", i)
            plancher = min(haut - perte, 50000.0)
            t = 1 if frein > 0 and solde - plancher < perte - frein else 0
            R, Dp = (R1, D1) if t else (R0, D0)
            if solde + Dp[i] <= plancher:
                return fin("plancher", i)
            solde += R[i]; haut = max(haut, solde)
            if T[i]:
                jrs += 1; vide = 0
            else:
                vide += 1
                if inactivite and vide >= 5:
                    return fin("inactivité", i)
            meil = max(meil, R[i])
            dispo = solde - 52600.0
            if phase == "M" and nret < 3:
                dispo = min(dispo, 1500.0)
            if jrs >= 10 and dispo >= 1000.0 and solde - base > 0 and meil <= 0.4 * (solde - base):
                solde -= dispo; base = solde; meil = 0.0; jrs = 0; nret += 1
                if phase == "M":
                    o["touche_m"] += 0.9 * dispo
                    if nret == 1:
                        o["j1"] = i - i0
                    if nret == 3:
                        o["j3"] = i - i0; o["issue"] = "3 retraits"
                        phase = "F"; i_f = i; solde = haut = base = 50000.0; meil = 0.0; jrs = 0; nret = 0; perte = 2000.0; vide = 0
                elif i - i_f <= 252:
                    touche_f += 0.9 * dispo
            if phase == "F" and i - i_f >= 252:
                o["funded"] = dict(issue="en vie après 1 an", touche=touche_f); return o
        if phase == "F":
            o["funded"] = dict(issue="données finies", touche=touche_f)
        return o

    def series(self, T):
        out, vide = [], 0
        for i in range(self.d17, self.n):
            vide += self.gap[i] if i > self.d17 else 0
            if T[i]:
                if vide:
                    out.append(vide)
                vide = 0
            else:
                vide += 1
        if vide:
            out.append(vide)
        return out

    def mesurer(self, tr, limite=1000.0, frein=750.0, gn=None, cn=None, tn=None, inactivite=True):
        R0, D0 = self.journees(tr, 1.0, limite, gn, cn); R1, D1 = self.journees(tr, 0.5, limite, gn, cn)
        js = {t[0] for t in tr}; T = np.array([s in js for s in self.test])
        if tn is not None:
            T = T | tn[self.test]
        vs = [self.vie(R0, D0, R1, D1, T, i0, frein, inactivite) for i0 in range(self.d17, self.n, 20)]
        N = len(vs); cpt = lambda c: sum(v["issue"] == c for v in vs) / N
        j1 = [v["j1"] for v in vs if v["j1"] is not None]; j3 = [v["j3"] for v in vs if v["j3"] is not None]
        fd = [v["funded"] for v in vs if v["funded"] and v["funded"]["issue"] != "données finies"]
        pertes = sorted({v["fin"] for v in vs if v["issue"] in ("plancher", "inactivité")})
        sv = self.series(T); jw = R0[self.d17:]
        return dict(departs=N, trois=cpt("3 retraits"), plancher=cpt("plancher"), inactivite=cpt("inactivité"), en_cours=cpt("en cours"),
                    episodes=len(pertes), dates_pertes=[str(self.jours[i]) for i in pertes],
                    med_j1=float(np.median(j1)) if j1 else None, med_j3=float(np.median(j3)) if j3 else None,
                    touche_master=float(np.mean([v["touche_m"] for v in vs])),
                    funded_n=len(fd), funded_perdu=float(np.mean([f["issue"] in ("plancher", "inactivité") for f in fd])) if fd else None,
                    funded_touche=float(np.mean([f["touche"] for f in fd])) if fd else None,
                    series5=int(sum(k >= 5 for k in sv)), plus_longue=int(max(sv) if sv else 0),
                    par_seance=float(jw.mean()), t=D.tstat(jw), seances_tradees=float(T[self.d17:].mean()),
                    pire_jour=float(jw.min()), jours_sous_1000=int((jw <= -1000).sum()))


def resume(nom, m):
    f = lambda x: "—" if x is None else f"{x:.0f}"
    return (f"{nom}\n    {m['trois']:.0%} des Masters atteignent le 3e retrait ; {m['plancher']:.0%} perdus par le plancher, {m['inactivite']:.0%} par "
            f"l'inactivité ({m['episodes']} dates de perte distinctes) ; {m['en_cours']:.0%} en cours à la fin\n"
            f"    1er retrait en {f(m['med_j1'])} séances, 3e en {f(m['med_j3'])} (médianes) ; touché par Master : {m['touche_master']:,.0f} $ ; "
            f"funded : {'—' if m['funded_perdu'] is None else format(m['funded_perdu'], '.0%')} perdus dans l'année, "
            f"{'—' if m['funded_touche'] is None else format(m['funded_touche'], ',.0f')} $ touchés\n"
            f"    séries de 5 jours sans trade : {m['series5']} (la plus longue {m['plus_longue']}) ; {m['par_seance']:.1f} $ par séance, t {m['t']:.2f}, "
            f"{m['seances_tradees']:.0%} de séances tradées ; pire jour {m['pire_jour']:,.0f} $, {m['jours_sous_1000']} jours à −1 000 $ ou pire").replace(",", " ")


def principal():
    lignes = ["Partie N, dans le compte : Master Bulenox 50K Option 2, un Master neuf toutes les 20 séances depuis 2017.", ""]
    # 1. controle du simulateur contre la vague 10 (meme fenetre : jusqu'au 2 novembre 2026)
    B = Banc("2026-11-02")
    m0 = B.mesurer(B.zf)
    lignes += ["Contrôle du simulateur (fenêtre de la vague 10, jusqu'au 2 novembre 2026) :",
               f"  publié  : 123 départs, 101 séries de 5 jours (la plus longue 48), 99,2 % perdus par l'inactivité, 15,65 $ par séance, t 4,12, 35,9 % de séances tradées",
               f"  ici     : {m0['departs']} départs, {m0['series5']} séries (la plus longue {m0['plus_longue']}), {m0['inactivite']:.1%} perdus par l'inactivité, "
               f"{m0['par_seance']:.2f} $ par séance, t {m0['t']:.2f}, {m0['seances_tradees']:.1%} de séances tradées", ""]
    # 2. le bot et la nuit, fenetre commune (les nuits s'arretent le 2 octobre 2026)
    B = Banc("2026-10-02"); X = Nn.construire(); res = {}
    lignes.append("Fenêtre commune au bot et à la nuit : 2017 → 2 octobre 2026.")
    choix = json.load(open(D.ICI / "resultats/nuit.json"))["choix"]
    cas = [("T0", "T0 · le bot seul (Z12F, limite 1 000 $, frein)", None, None)]
    cas += [(f"N{k + 1}", f"N{k + 1} · le bot + la nuit {f} avec stop {s * 100:.2f} %", s, f) for k, (s, f) in enumerate(choix)]
    cas += [("Nsans", "pour information · le bot + la nuit F0 sans stop", 0.0, "F0")]
    for ident, nom, stop, f in cas:
        if f is None:
            m = B.mesurer(B.zf); ms = B.mesurer(B.zf, inactivite=False)
        else:
            g, creux, _ = Nn.gains(X, stop); garde = Nn.masque(X, f)
            gn = np.where(garde, g, 0.0); cn = np.where(garde, creux, 0.0)
            m = B.mesurer(B.zf, gn=gn, cn=cn, tn=garde); ms = B.mesurer(B.zf, gn=gn, cn=cn, tn=garde, inactivite=False)
        res[ident] = dict(nom=nom, **m, sans_regle=ms)
        lignes += [resume(nom, m), f"    sans la règle d'inactivité (pour séparer les deux risques) : {ms['trois']:.0%} au 3e retrait, {ms['plancher']:.0%} perdus par le plancher, "
                   f"touché {ms['touche_master']:,.0f} $".replace(",", " "), ""]
    for ident in [c[0] for c in cas if c[0].startswith("N") and c[0] != "Nsans"]:
        m = res[ident]
        ok = m["inactivite"] == 0 and m["plancher"] <= 0.20 and m["touche_master"] > 0
        m["adoptee"] = bool(ok)
        lignes.append(f"{ident} : {'ADOPTÉE' if ok else 'non adoptée'} (aucun Master perdu par inactivité : {'oui' if m['inactivite'] == 0 else 'non'} ; "
                      f"perdus avant le 3e retrait {m['plancher'] + m['inactivite']:.0%}, règle ≤ 20 % ; touché {m['touche_master']:,.0f} $, règle > 0 ; "
                      f"{m['episodes']} dates de perte distinctes{' : chiffre fragile' if m['episodes'] < 3 else ''})".replace(",", " "))
    (D.ICI / "resultats/compte.txt").write_text("\n".join(lignes) + "\n")
    json.dump(res, open(D.ICI / "resultats/compte.json", "w"), indent=1, ensure_ascii=False)
    print("\n".join(lignes))


def secours(B, jouable, seuil=3):
    """Nuits de secours : la nuit qui precede la seance i est prise si le compte vient de passer `seuil` jours de trading
    sans trade (jours du fichier compris). Calcul global sur les seances, comme le secours T2 de la vague 10."""
    js = {t[0] for t in B.zf}; prise = np.zeros(len(B.J), bool); vide = 0
    for i, s in enumerate(B.test):
        if i > 0:
            vide += B.gap[i]
        n = vide >= seuil and jouable[s]
        prise[s] = n
        vide = 0 if (n or s in js) else vide + 1
    return prise


def vague2():
    B = Banc("2026-10-02"); X = Nn.construire(); jouable = np.isfinite(X["entree"]); res = {}
    lignes = ["Partie N, vague 2 : la nuit de secours (2017 → 2 octobre 2026, un Master neuf toutes les 20 séances).", ""]
    for ident, nom, stop, mode in (("NS75", "NS75 · le bot + la nuit de secours (stop 0,75 %) après 3 jours sans trade", 0.0075, "secours"),
                                   ("NS50", "NS50 · le bot + la nuit de secours (stop 0,50 %) après 3 jours sans trade", 0.005, "secours"),
                                   ("N50", "N50 · le bot + la nuit chaque soir (stop 0,50 %)", 0.005, "toutes")):
        g, creux, _ = Nn.gains(X, stop)
        garde = secours(B, jouable) if mode == "secours" else jouable
        gn = np.where(garde, g, 0.0); cn = np.where(garde, creux, 0.0)
        m = B.mesurer(B.zf, gn=gn, cn=cn, tn=garde); ms = B.mesurer(B.zf, gn=gn, cn=cn, tn=garde, inactivite=False)
        nn = garde[B.test][B.d17:]; gg = gn[B.test][B.d17:]
        ok = m["inactivite"] == 0 and m["plancher"] <= 0.20 and m["touche_master"] > 0
        res[ident] = dict(nom=nom, **m, sans_regle=ms, nuits=int(nn.sum()), gain_nuits=float(gg.sum()), adoptee=bool(ok))
        trous = [d for d in m["dates_pertes"] if "2023-02-01" <= d <= "2023-07-31"]
        lignes += [resume(nom, m), f"    nuits prises depuis 2017 : {int(nn.sum())} ({nn.mean():.0%} des séances), gain total des nuits {gg.sum():,.0f} $ ; "
                   f"sans la règle d'inactivité : {ms['trois']:.0%} au 3e retrait, {ms['plancher']:.0%} perdus par le plancher, touché {ms['touche_master']:,.0f} $".replace(",", " "),
                   f"    → {'ADOPTÉE' if ok else 'non adoptée'} (inactivité {m['inactivite']:.0%}, dont dates de perte dans les trous de 2023 : {len(trous)} ; "
                   f"perdus avant le 3e retrait {m['plancher'] + m['inactivite']:.0%} ; {m['episodes']} dates de perte distinctes)", ""]
    (D.ICI / "resultats/compte2.txt").write_text("\n".join(lignes) + "\n")
    json.dump(res, open(D.ICI / "resultats/compte2.json", "w"), indent=1, ensure_ascii=False)
    print("\n".join(lignes))


if __name__ == "__main__":
    import sys
    vague2() if len(sys.argv) > 1 and sys.argv[1] == "2" else principal()
