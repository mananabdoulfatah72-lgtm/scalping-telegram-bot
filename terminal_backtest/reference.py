#!/usr/bin/env python3
"""Calcul de reference du terminal de backtest (juge du moteur JavaScript de la page).

Regles : SPEC.md. Tout est ecrit en boucles simples, dans l'ordre d'operations de SPEC.md, pour que le moteur de la
page redonne les memes nombres. Usage : python3 reference.py   -> ecrit expected.json (lit data.json).
"""
import json
import math
from pathlib import Path

ICI = Path(__file__).resolve().parent
NAN = float("nan")
N_PASSE = 252
FRAIS = {"demande": [2.0, 2.0, 2.0, 2.0], "micro": [0.3, 0.6, 0.5, 2.2]}     # points de base par ordre, par marche
STRATEGIES = ["supertrend", "zscore", "dualmom", "ema_stop", "keltner", "stoch", "rsi2"]


# ------------------------------------------------------------------ indicateurs (causaux)
def sma(x, n):
    out = [NAN] * len(x)
    for t in range(n - 1, len(x)):
        s = 0.0
        for i in range(t - n + 1, t + 1):
            s += x[i]
        out[t] = s / n
    return out


def ecart_type(x, n, m):
    out = [NAN] * len(x)
    for t in range(n - 1, len(x)):
        s = 0.0
        for i in range(t - n + 1, t + 1):
            e = x[i] - m[t]
            s += e * e
        out[t] = math.sqrt(s / n)
    return out


def ema(x, n):
    out = [NAN] * len(x)
    s = 0.0
    for i in range(n):
        s += x[i]
    out[n - 1] = s / n
    a = 2.0 / (n + 1)
    for t in range(n, len(x)):
        out[t] = a * x[t] + (1.0 - a) * out[t - 1]
    return out


def atr(h, l, c, n):
    T = len(c)
    tr = [0.0] * T
    tr[0] = h[0] - l[0]
    for t in range(1, T):
        tr[t] = max(h[t] - l[t], abs(h[t] - c[t - 1]), abs(l[t] - c[t - 1]))
    out = [NAN] * T
    s = 0.0
    for i in range(n):
        s += tr[i]
    out[n - 1] = s / n
    for t in range(n, T):
        out[t] = (out[t - 1] * (n - 1) + tr[t]) / n
    return out


# ------------------------------------------------------------------ strategies : sig[t] dans {-1, 0, +1}, decide a la cloture t
def supertrend(o, h, l, c):
    T = len(c); a = atr(h, l, c, 10); sig = [0] * T
    fub = flb = 0.0; d = 1
    for t in range(9, T):
        mid = (h[t] + l[t]) / 2.0
        ub = mid + 3.0 * a[t]; lb = mid - 3.0 * a[t]
        if t == 9:
            fub, flb, d = ub, lb, 1
        else:
            nfub = ub if (ub < fub or c[t - 1] > fub) else fub
            nflb = lb if (lb > flb or c[t - 1] < flb) else flb
            if d > 0 and c[t] < nflb:
                d = -1
            elif d < 0 and c[t] > nfub:
                d = 1
            fub, flb = nfub, nflb
        sig[t] = d
    return sig


def zscore(o, h, l, c):
    T = len(c); m = sma(c, 20); s = ecart_type(c, 20, m); sig = [0] * T; p = 0
    for t in range(19, T):
        z = 0.0 if s[t] == 0 else (c[t] - m[t]) / s[t]
        if p == 0:
            if z <= -1.5:
                p = 1
            elif z >= 1.5:
                p = -1
        elif p == 1:
            if z >= 0:
                p = 0
        elif z <= 0:
            p = 0
        sig[t] = p
    return sig


def dualmom(dates, closes):
    """Les 4 marches ensemble : a la cloture de la 1re seance de chaque mois, achat des marches dont le rendement sur
    126 seances est positif ET classe dans les 2 meilleurs des 4 (egalite : le marche liste en premier)."""
    T = len(dates); K = len(closes); sig = [[0] * T for _ in range(K)]; cur = [0] * K
    for t in range(126, T):
        if dates[t][5:7] != dates[t - 1][5:7]:
            m = [closes[k][t] / closes[k][t - 126] - 1.0 for k in range(K)]
            ordre = sorted(range(K), key=lambda k: (-m[k], k))
            cur = [0] * K
            for rang, k in enumerate(ordre):
                if rang < 2 and m[k] > 0:
                    cur[k] = 1
        for k in range(K):
            sig[k][t] = cur[k]
    return sig


def ema_stop(o, h, l, c):
    T = len(c); e20 = ema(c, 20); e50 = ema(c, 50); a = atr(h, l, c, 14); sig = [0] * T
    p = 0; hh = stop = 0.0
    for t in range(50, T):
        up = e20[t] > e50[t]; avant = e20[t - 1] > e50[t - 1]
        if p == 0:
            if up and not avant:
                p = 1; hh = c[t]; stop = c[t] - 3.0 * a[t]
        elif c[t] < stop or not up:
            p = 0
        else:
            if c[t] > hh:
                hh = c[t]
            ns = hh - 3.0 * a[t]
            if ns > stop:
                stop = ns
        sig[t] = p
    return sig


def keltner(o, h, l, c):
    T = len(c); e = ema(c, 20); a = atr(h, l, c, 10); sig = [0] * T; p = 0
    for t in range(19, T):
        haut = e[t] + 2.0 * a[t]; bas = e[t] - 2.0 * a[t]
        if p == 0:
            if c[t] > haut:
                p = 1
            elif c[t] < bas:
                p = -1
        elif p == 1:
            if c[t] < e[t]:
                p = 0
        elif c[t] > e[t]:
            p = 0
        sig[t] = p
    return sig


def stoch(o, h, l, c):
    T = len(c); k = [NAN] * T; d = [NAN] * T; sig = [0] * T; p = 0
    for t in range(13, T):
        hh = h[t - 13]; ll = l[t - 13]
        for i in range(t - 12, t + 1):
            if h[i] > hh:
                hh = h[i]
            if l[i] < ll:
                ll = l[i]
        k[t] = 50.0 if hh == ll else 100.0 * (c[t] - ll) / (hh - ll)
    for t in range(15, T):
        d[t] = (k[t - 2] + k[t - 1] + k[t]) / 3.0
    for t in range(16, T):
        if p == 0:
            if k[t] > d[t] and k[t - 1] <= d[t - 1] and k[t - 1] < 20:
                p = 1
            elif k[t] < d[t] and k[t - 1] >= d[t - 1] and k[t - 1] > 80:
                p = -1
        elif p == 1:
            if k[t] > 80:
                p = 0
        elif k[t] < 20:
            p = 0
        sig[t] = p
    return sig


def rsi2(o, h, l, c):
    """RSI(2) de Connors, la regle du 2e moteur du Bot 3 en 1 (zone/robot.py) : achat seulement."""
    T = len(c); m200 = sma(c, 200); m5 = sma(c, 5); r = [NAN] * T; sig = [0] * T; p = 0
    g = pe = 0.0
    for t in range(1, T):
        v = c[t] - c[t - 1]; gain = v if v > 0 else 0.0; perte = -v if v < 0 else 0.0
        if t <= 2:
            g += gain; pe += perte
            if t == 2:
                g /= 2.0; pe /= 2.0
        else:
            g = (g + gain) / 2.0; pe = (pe + perte) / 2.0
        if t >= 2:
            r[t] = (50.0 if g == 0 else 100.0) if pe == 0 else 100.0 - 100.0 / (1.0 + g / pe)
    for t in range(199, T):
        if p == 1:
            if c[t] > m5[t]:
                p = 0
        elif c[t] > m200[t] and r[t] < 10:
            p = 1
        sig[t] = p
    return sig


# ------------------------------------------------------------------ backtest
def backtest(sig, o, c, roll, a, b, frais):
    """Position w[t] = sig[t-1], prise a l'OUVERTURE de la barre t. A plat avant a, tout est ferme a la cloture de b-1.
    Une position gardee a travers un changement de contrat (roll[t] = 1) paie 2 ordres de plus : vente de l'ancien
    contrat, achat du nouveau."""
    E = 1.0; pic = 1.0; baisse = 0.0; wp = 0; trades = 0; expo = 0; rets = []
    for t in range(a, b):
        w = sig[t - 1]
        g = o[t] / c[t - 1] - 1.0
        d = c[t] / o[t] - 1.0
        r = (1.0 + wp * g) * (1.0 + w * d) - 1.0
        cout = frais * abs(w - wp)
        if roll[t] == 1 and w == wp and w != 0:
            cout += 2.0 * frais * abs(w)
        if w != wp and w != 0:
            trades += 1
        if t == b - 1:
            cout += frais * abs(w)
        r -= cout
        E *= 1.0 + r
        if E > pic:
            pic = E
        if E / pic - 1.0 < baisse:
            baisse = E / pic - 1.0
        if w != 0:
            expo += 1
        rets.append(r); wp = w
    return {"ret": E - 1.0, "trades": trades, "dd": baisse, "expo": expo / (b - a)}, rets


def hors_marche(y, x):
    """Regression y = alpha + beta * x (x = rendement du marche de la meme barre). Renvoie alpha, beta et le t d'alpha :
    ce que la strategie gagne une fois retiree la part qui vient de sa simple exposition au marche."""
    n = len(y); sx = sy = 0.0
    for i in range(n):
        sx += x[i]; sy += y[i]
    mx = sx / n; my = sy / n; sxx = sxy = 0.0
    for i in range(n):
        dx = x[i] - mx
        sxx += dx * dx; sxy += dx * (y[i] - my)
    beta = sxy / sxx; alpha = my - beta * mx; sse = 0.0
    for i in range(n):
        e = y[i] - alpha - beta * x[i]
        sse += e * e
    se = math.sqrt(sse / (n - 2) * (1.0 / n + mx * mx / sxx))
    return alpha, beta, (0.0 if se == 0 else alpha / se)


def stats(rets, dates, marche=None):
    n = len(rets); m = sum(rets) / n
    v = sum((x - m) ** 2 for x in rets) / (n - 1); s = math.sqrt(v)
    E = 1.0
    for x in rets:
        E *= 1.0 + x

    def t_de(sel):
        x = [r for r, ok in zip(rets, sel) if ok]
        if len(x) < 30:
            return None
        mm = sum(x) / len(x); ss = math.sqrt(sum((y - mm) ** 2 for y in x) / (len(x) - 1))
        return 0.0 if ss == 0 else mm / ss * math.sqrt(len(x))
    out = {"cagr": E ** (252.0 / n) - 1.0, "sharpe": 0.0 if s == 0 else m / s * math.sqrt(252.0),
           "t": 0.0 if s == 0 else m / s * math.sqrt(n), "t_avant_2019": t_de([d < "2019-01-01" for d in dates]),
           "t_depuis_2019": t_de([d >= "2019-01-01" for d in dates]), "t_depuis_2023": t_de([d >= "2023-01-01" for d in dates])}
    if marche is not None:
        alpha, beta, ta = hors_marche(rets, marche)
        out.update({"alpha_an": alpha * 252.0, "beta": beta, "t_alpha": ta})
    return out


def tout():
    D = json.loads((ICI / "data.json").read_text())
    dates = D["dates"]; M = D["marches"]; T = len(dates); K = len(M)
    npasses = (T - N_PASSE) // N_PASSE
    passes = [{"a": T - N_PASSE * (p + 1), "b": T - N_PASSE * p} for p in range(npasses)]
    for p in passes:
        p["debut"] = dates[p["a"]]; p["fin"] = dates[p["b"] - 1]
    sig = {s: [None] * K for s in STRATEGIES}
    for k, m in enumerate(M):
        for s, f in (("supertrend", supertrend), ("zscore", zscore), ("ema_stop", ema_stop), ("keltner", keltner),
                     ("stoch", stoch), ("rsi2", rsi2)):
            sig[s][k] = f(m["o"], m["h"], m["l"], m["c"])
    dm = dualmom(dates, [m["c"] for m in M])
    for k in range(K):
        sig["dualmom"][k] = dm[k]
    a0 = passes[-1]["a"]
    marche = [[M[k]["c"][t] / M[k]["c"][t - 1] - 1.0 for t in range(a0, T)] for k in range(K)]   # rendement brut du marche
    out = {"meta": {"T": T, "n_passe": N_PASSE, "passes": passes, "frais_pb": FRAIS, "strategies": STRATEGIES,
                    "marches": [m["id"] for m in M], "long": {"a": a0, "b": T, "debut": dates[a0], "fin": dates[T - 1]}},
           "signaux": {s: ["".join("+" if v > 0 else "-" if v < 0 else "0" for v in sig[s][k]) for k in range(K)] for s in STRATEGIES},
           "cellules": {}, "long": {}, "acheter_conserver": {}}
    un = [1] * T
    for mode, pb in FRAIS.items():
        cel = []; bh_p = []
        for p in passes:
            ligne_bh = [backtest(un, M[k]["o"], M[k]["c"], M[k]["r"], p["a"], p["b"], pb[k] / 1e4)[0] for k in range(K)]
            bh_p.append(ligne_bh)
            cel.append([[dict(backtest(sig[s][k], M[k]["o"], M[k]["c"], M[k]["r"], p["a"], p["b"], pb[k] / 1e4)[0], bh=ligne_bh[k]["ret"])
                         for k in range(K)] for s in STRATEGIES])
        out["cellules"][mode] = cel
        lg = []; bh_l = []
        for k in range(K):
            r, rets = backtest(un, M[k]["o"], M[k]["c"], M[k]["r"], a0, T, pb[k] / 1e4)
            bh_l.append(dict(r, **stats(rets, dates[a0:T])))
        for s in STRATEGIES:
            ligne = []
            for k in range(K):
                r, rets = backtest(sig[s][k], M[k]["o"], M[k]["c"], M[k]["r"], a0, T, pb[k] / 1e4)
                ligne.append(dict(r, **stats(rets, dates[a0:T], marche[k])))
            lg.append(ligne)
        out["long"][mode] = lg
        out["acheter_conserver"][mode] = {"passes": bh_p, "long": bh_l}
    return out, sig, D


if __name__ == "__main__":
    out, sig, D = tout()
    (ICI / "expected.json").write_text(json.dumps(out, separators=(",", ":")))
    m = out["meta"]
    print(f"{m['T']} seances, {len(m['passes'])} passes de {N_PASSE} ; long : {m['long']['debut']} -> {m['long']['fin']}")
    for mode in FRAIS:
        print(f"\nfrais « {mode} » {FRAIS[mode]} pb : rendement annuel (t) sur toute la periode | cellules battant acheter-conserver")
        bh = out["acheter_conserver"][mode]["long"]
        print("  acheter-conserver   " + "  ".join(f"{mk}: {b['cagr'] * 100:+6.1f} % (t {b['t']:.2f}, baisse {b['dd'] * 100:.0f} %)" for mk, b in zip(m["marches"], bh)))
        for i, s in enumerate(STRATEGIES):
            lg = out["long"][mode][i]
            bat = sum(c["ret"] > c["bh"] for p in out["cellules"][mode] for c in p[i])
            joue = sum(c["trades"] > 0 for p in out["cellules"][mode] for c in p[i])
            bat = sum(c["trades"] > 0 and c["ret"] > c["bh"] for p in out["cellules"][mode] for c in p[i])
            print(f"  {s:11s} " + "  ".join(f"{mk}: {x['cagr'] * 100:+5.1f} % t {x['t']:+.2f} | hors marche {x['alpha_an'] * 100:+5.1f} % t {x['t_alpha']:+.2f} beta {x['beta']:+.2f}" for mk, x in zip(m["marches"], lg))
                  + f"  | bat {bat}/{joue}")
        p0 = out["cellules"][mode][0]
        print("  passe 1 (la plus recente) : " + " ; ".join(f"{s} " + "/".join(f"{c['ret'] * 100:+.1f}" for c in p0[i]) for i, s in enumerate(STRATEGIES)))
        print("  acheter-conserver passe 1 : " + "/".join(f"{b['ret'] * 100:+.1f}" for b in out["acheter_conserver"][mode]["passes"][0]))
