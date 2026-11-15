/* Moteur du terminal de backtest : portage ligne a ligne de reference.py (aucun acces au DOM).
   Memes boucles et meme ordre d'operations que le Python, pour retrouver les memes nombres en double precision. */
(function (racine) {
  'use strict';

  var NAN = NaN;
  var N_PASSE = 252;
  var FRAIS = { demande: [2.0, 2.0, 2.0, 2.0], micro: [0.3, 0.6, 0.5, 2.2] };
  var STRATEGIES = ['supertrend', 'zscore', 'dualmom', 'ema_stop', 'keltner', 'stoch', 'rsi2'];
  var NOMS = {
    supertrend: 'Supertrend 10-3', zscore: 'Z-score 20', dualmom: 'Dual momentum',
    ema_stop: 'EMA 20/50 + stop ATR', keltner: 'Cassure de Keltner', stoch: 'Stochastique 14-3', rsi2: 'RSI(2)'
  };

  function remplir(n, v) { var a = new Array(n); for (var i = 0; i < n; i++) a[i] = v; return a; }

  /* sum() de Python >= 3.12 : somme compensee de Neumaier (meme algorithme que CPython). */
  function pysum(xs) {
    var f = 0.0, c = 0.0;
    for (var i = 0; i < xs.length; i++) {
      var x = xs[i];
      var t = f + x;
      if (Math.abs(f) >= Math.abs(x)) c += (f - t) + x; else c += (x - t) + f;
      f = t;
    }
    if (c !== 0 && isFinite(c)) f += c;
    return f;
  }

  // ------------------------------------------------------------------ indicateurs (causaux)
  function sma(x, n) {
    var out = remplir(x.length, NAN);
    for (var t = n - 1; t < x.length; t++) {
      var s = 0.0;
      for (var i = t - n + 1; i < t + 1; i++) s += x[i];
      out[t] = s / n;
    }
    return out;
  }

  function ecartType(x, n, m) {
    var out = remplir(x.length, NAN);
    for (var t = n - 1; t < x.length; t++) {
      var s = 0.0;
      for (var i = t - n + 1; i < t + 1; i++) { var e = x[i] - m[t]; s += e * e; }
      out[t] = Math.sqrt(s / n);
    }
    return out;
  }

  function ema(x, n) {
    var out = remplir(x.length, NAN);
    var s = 0.0;
    for (var i = 0; i < n; i++) s += x[i];
    out[n - 1] = s / n;
    var a = 2.0 / (n + 1);
    for (var t = n; t < x.length; t++) out[t] = a * x[t] + (1.0 - a) * out[t - 1];
    return out;
  }

  function atr(h, l, c, n) {
    var T = c.length;
    var tr = remplir(T, 0.0);
    tr[0] = h[0] - l[0];
    for (var t = 1; t < T; t++) tr[t] = Math.max(h[t] - l[t], Math.abs(h[t] - c[t - 1]), Math.abs(l[t] - c[t - 1]));
    var out = remplir(T, NAN);
    var s = 0.0;
    for (var i = 0; i < n; i++) s += tr[i];
    out[n - 1] = s / n;
    for (t = n; t < T; t++) out[t] = (out[t - 1] * (n - 1) + tr[t]) / n;
    return out;
  }

  // ------------------------------------------------------------------ strategies : sig[t] dans {-1, 0, +1}, decide a la cloture t
  // Chaque fonction rend { sig, series } ; series = ce qu'il faut pour dessiner (NaN avant que ca existe).
  function supertrend(o, h, l, c) {
    var T = c.length, a = atr(h, l, c, 10), sig = remplir(T, 0);
    var ligne = remplir(T, NAN), sens = remplir(T, NAN);
    var fub = 0.0, flb = 0.0, d = 1;
    for (var t = 9; t < T; t++) {
      var mid = (h[t] + l[t]) / 2.0;
      var ub = mid + 3.0 * a[t], lb = mid - 3.0 * a[t];
      if (t === 9) { fub = ub; flb = lb; d = 1; }
      else {
        var nfub = (ub < fub || c[t - 1] > fub) ? ub : fub;
        var nflb = (lb > flb || c[t - 1] < flb) ? lb : flb;
        if (d > 0 && c[t] < nflb) d = -1;
        else if (d < 0 && c[t] > nfub) d = 1;
        fub = nfub; flb = nflb;
      }
      sig[t] = d;
      ligne[t] = d > 0 ? flb : fub; sens[t] = d;
    }
    return { sig: sig, series: { ligne: ligne, sens: sens } };
  }

  function zscore(o, h, l, c) {
    var T = c.length, m = sma(c, 20), s = ecartType(c, 20, m), sig = remplir(T, 0), p = 0;
    var zz = remplir(T, NAN), haut = remplir(T, NAN), bas = remplir(T, NAN);
    for (var t = 19; t < T; t++) {
      var z = s[t] === 0 ? 0.0 : (c[t] - m[t]) / s[t];
      if (p === 0) { if (z <= -1.5) p = 1; else if (z >= 1.5) p = -1; }
      else if (p === 1) { if (z >= 0) p = 0; }
      else if (z <= 0) p = 0;
      sig[t] = p;
      zz[t] = z; haut[t] = m[t] + 1.5 * s[t]; bas[t] = m[t] - 1.5 * s[t];
    }
    return { sig: sig, series: { moyenne: m, haut: haut, bas: bas, z: zz } };
  }

  /* Les 4 marches ensemble : a la cloture de la 1re seance de chaque mois, achat des marches dont le rendement sur
     126 seances est positif ET classe dans les 2 meilleurs des 4 (egalite : le marche liste en premier). */
  function dualmom(dates, closes) {
    var T = dates.length, K = closes.length, sig = [], cur = remplir(K, 0), k;
    var mom = [], ref = [];
    for (k = 0; k < K; k++) { sig.push(remplir(T, 0)); mom.push(remplir(T, NAN)); ref.push(remplir(T, NAN)); }
    for (var t = 126; t < T; t++) {
      for (k = 0; k < K; k++) {
        mom[k][t] = (closes[k][t] / closes[k][t - 126] - 1.0) * 100.0;
        ref[k][t] = closes[k][t - 126];
      }
      if (dates[t].slice(5, 7) !== dates[t - 1].slice(5, 7)) {
        var m = [];
        for (k = 0; k < K; k++) m.push(closes[k][t] / closes[k][t - 126] - 1.0);
        var ordre = [];
        for (k = 0; k < K; k++) ordre.push(k);
        ordre.sort(function (x, y) { return (-m[x]) - (-m[y]) || x - y; });
        cur = remplir(K, 0);
        for (var rang = 0; rang < ordre.length; rang++) {
          k = ordre[rang];
          if (rang < 2 && m[k] > 0) cur[k] = 1;
        }
      }
      for (k = 0; k < K; k++) sig[k][t] = cur[k];
    }
    var res = [];
    for (k = 0; k < K; k++) res.push({ sig: sig[k], series: { momentum: mom[k], prix_126: ref[k] } });
    return res;
  }

  function ema_stop(o, h, l, c) {
    var T = c.length, e20 = ema(c, 20), e50 = ema(c, 50), a = atr(h, l, c, 14), sig = remplir(T, 0);
    var niveau = remplir(T, NAN);
    var p = 0, hh = 0.0, stop = 0.0;
    for (var t = 50; t < T; t++) {
      var up = e20[t] > e50[t], avant = e20[t - 1] > e50[t - 1];
      if (p === 0) {
        if (up && !avant) { p = 1; hh = c[t]; stop = c[t] - 3.0 * a[t]; }
      } else if (c[t] < stop || !up) {
        p = 0;
      } else {
        if (c[t] > hh) hh = c[t];
        var ns = hh - 3.0 * a[t];
        if (ns > stop) stop = ns;
      }
      sig[t] = p;
      if (p === 1) niveau[t] = stop;
    }
    return { sig: sig, series: { ema20: e20, ema50: e50, stop: niveau } };
  }

  function keltner(o, h, l, c) {
    var T = c.length, e = ema(c, 20), a = atr(h, l, c, 10), sig = remplir(T, 0), p = 0;
    var H = remplir(T, NAN), B = remplir(T, NAN);
    for (var t = 19; t < T; t++) {
      var haut = e[t] + 2.0 * a[t], bas = e[t] - 2.0 * a[t];
      if (p === 0) { if (c[t] > haut) p = 1; else if (c[t] < bas) p = -1; }
      else if (p === 1) { if (c[t] < e[t]) p = 0; }
      else if (c[t] > e[t]) p = 0;
      sig[t] = p;
      H[t] = haut; B[t] = bas;
    }
    return { sig: sig, series: { ema20: e, haut: H, bas: B } };
  }

  function stoch(o, h, l, c) {
    var T = c.length, k = remplir(T, NAN), d = remplir(T, NAN), sig = remplir(T, 0), p = 0, t;
    for (t = 13; t < T; t++) {
      var hh = h[t - 13], ll = l[t - 13];
      for (var i = t - 12; i < t + 1; i++) { if (h[i] > hh) hh = h[i]; if (l[i] < ll) ll = l[i]; }
      k[t] = hh === ll ? 50.0 : 100.0 * (c[t] - ll) / (hh - ll);
    }
    for (t = 15; t < T; t++) d[t] = (k[t - 2] + k[t - 1] + k[t]) / 3.0;
    for (t = 16; t < T; t++) {
      if (p === 0) {
        if (k[t] > d[t] && k[t - 1] <= d[t - 1] && k[t - 1] < 20) p = 1;
        else if (k[t] < d[t] && k[t - 1] >= d[t - 1] && k[t - 1] > 80) p = -1;
      } else if (p === 1) { if (k[t] > 80) p = 0; }
      else if (k[t] < 20) p = 0;
      sig[t] = p;
    }
    return { sig: sig, series: { k: k, d: d } };
  }

  /* RSI(2) de Connors, la regle du 2e moteur du Bot 3 en 1 : achat seulement. */
  function rsi2(o, h, l, c) {
    var T = c.length, m200 = sma(c, 200), m5 = sma(c, 5), r = remplir(T, NAN), sig = remplir(T, 0), p = 0, t;
    var g = 0.0, pe = 0.0;
    for (t = 1; t < T; t++) {
      var v = c[t] - c[t - 1], gain = v > 0 ? v : 0.0, perte = v < 0 ? -v : 0.0;
      if (t <= 2) {
        g += gain; pe += perte;
        if (t === 2) { g /= 2.0; pe /= 2.0; }
      } else { g = (g + gain) / 2.0; pe = (pe + perte) / 2.0; }
      if (t >= 2) r[t] = pe === 0 ? (g === 0 ? 50.0 : 100.0) : 100.0 - 100.0 / (1.0 + g / pe);
    }
    for (t = 199; t < T; t++) {
      if (p === 1) { if (c[t] > m5[t]) p = 0; }
      else if (c[t] > m200[t] && r[t] < 10) p = 1;
      sig[t] = p;
    }
    return { sig: sig, series: { rsi: r, sma200: m200, sma5: m5 } };
  }

  // ------------------------------------------------------------------ backtest
  /* Position w[t] = sig[t-1], prise a l'OUVERTURE de la barre t. A plat avant a, tout est ferme a la cloture de b-1.
     Rend [mesures, rets, courbe] ; courbe[i] = capital apres la barre a+i (pour le dessin). */
  function backtest(sig, o, c, a, b, frais) {
    var E = 1.0, pic = 1.0, baisse = 0.0, wp = 0, trades = 0, expo = 0, rets = [], courbe = [];
    for (var t = a; t < b; t++) {
      var w = sig[t - 1];
      var g = o[t] / c[t - 1] - 1.0;
      var d = c[t] / o[t] - 1.0;
      var r = (1.0 + wp * g) * (1.0 + w * d) - 1.0;
      var cout = frais * Math.abs(w - wp);
      if (w !== wp && w !== 0) trades += 1;
      if (t === b - 1) cout += frais * Math.abs(w);
      r -= cout;
      E *= 1.0 + r;
      if (E > pic) pic = E;
      if (E / pic - 1.0 < baisse) baisse = E / pic - 1.0;
      if (w !== 0) expo += 1;
      rets.push(r); courbe.push(E); wp = w;
    }
    return [{ ret: E - 1.0, trades: trades, dd: baisse, expo: expo / (b - a) }, rets, courbe];
  }

  function stats(rets, dates) {
    var n = rets.length, m = pysum(rets) / n, i;
    var carres = [];
    for (i = 0; i < n; i++) carres.push(Math.pow(rets[i] - m, 2));
    var v = pysum(carres) / (n - 1), s = Math.sqrt(v);
    var E = 1.0;
    for (i = 0; i < n; i++) E *= 1.0 + rets[i];

    function tDe(sel) {
      var x = [];
      for (var j = 0; j < n; j++) if (sel(dates[j])) x.push(rets[j]);
      if (x.length < 30) return null;
      var mm = pysum(x) / x.length, q = [];
      for (j = 0; j < x.length; j++) q.push(Math.pow(x[j] - mm, 2));
      var ss = Math.sqrt(pysum(q) / (x.length - 1));
      return ss === 0 ? 0.0 : mm / ss * Math.sqrt(x.length);
    }
    return {
      cagr: Math.pow(E, 252.0 / n) - 1.0,
      sharpe: s === 0 ? 0.0 : m / s * Math.sqrt(252.0),
      t: s === 0 ? 0.0 : m / s * Math.sqrt(n),
      t_avant_2019: tDe(function (d) { return d < '2019-01-01'; }),
      t_depuis_2019: tDe(function (d) { return d >= '2019-01-01'; }),
      t_depuis_2023: tDe(function (d) { return d >= '2023-01-01'; })
    };
  }

  function fusion(a, b) { var r = {}, k; for (k in a) r[k] = a[k]; for (k in b) r[k] = b[k]; return r; }

  function passes(dates) {
    var T = dates.length, np = Math.floor((T - N_PASSE) / N_PASSE), ps = [];
    for (var p = 0; p < np; p++) {
      var a = T - N_PASSE * (p + 1), b = T - N_PASSE * p;
      ps.push({ a: a, b: b, debut: dates[a], fin: dates[b - 1] });
    }
    return ps;
  }

  /* Signaux et series de dessin des 7 strategies sur les K marches : calc[s][k] = { sig, series }. */
  function calculer(D) {
    var M = D.marches, K = M.length, calc = {}, s, k;
    var fns = { supertrend: supertrend, zscore: zscore, ema_stop: ema_stop, keltner: keltner, stoch: stoch, rsi2: rsi2 };
    for (var i = 0; i < STRATEGIES.length; i++) calc[STRATEGIES[i]] = remplir(K, null);
    for (k = 0; k < K; k++) {
      var m = M[k];
      for (s in fns) calc[s][k] = fns[s](m.o, m.h, m.l, m.c);
    }
    var closes = [];
    for (k = 0; k < K; k++) closes.push(M[k].c);
    var dm = dualmom(D.dates, closes);
    for (k = 0; k < K; k++) calc.dualmom[k] = dm[k];
    return calc;
  }

  /* Meme sortie que reference.py (tout()) ; modes = sous-ensemble de FRAIS (par defaut les deux). */
  function tout(D, calc, modes) {
    calc = calc || calculer(D);
    modes = modes || Object.keys(FRAIS);
    var dates = D.dates, M = D.marches, T = dates.length, K = M.length, k, i;
    var ps = passes(dates), a0 = ps[ps.length - 1].a;
    var out = {
      meta: { T: T, n_passe: N_PASSE, passes: ps, frais_pb: FRAIS, strategies: STRATEGIES,
        marches: M.map(function (m) { return m.id; }), long: { a: a0, b: T, debut: dates[a0], fin: dates[T - 1] } },
      signaux: {}, cellules: {}, long: {}, acheter_conserver: {}
    };
    STRATEGIES.forEach(function (s) {
      out.signaux[s] = [];
      for (k = 0; k < K; k++) {
        var sg = calc[s][k].sig, ch = new Array(T);
        for (var t = 0; t < T; t++) ch[t] = sg[t] > 0 ? '+' : sg[t] < 0 ? '-' : '0';
        out.signaux[s].push(ch.join(''));
      }
    });
    var un = remplir(T, 1), datesLong = dates.slice(a0, T);
    modes.forEach(function (mode) {
      var pb = FRAIS[mode], cel = [], bhP = [];
      ps.forEach(function (p) {
        var ligneBh = [];
        for (k = 0; k < K; k++) ligneBh.push(backtest(un, M[k].o, M[k].c, p.a, p.b, pb[k] / 1e4)[0]);
        bhP.push(ligneBh);
        cel.push(STRATEGIES.map(function (s) {
          var l = [];
          for (k = 0; k < K; k++) l.push(fusion(backtest(calc[s][k].sig, M[k].o, M[k].c, p.a, p.b, pb[k] / 1e4)[0], { bh: ligneBh[k].ret }));
          return l;
        }));
      });
      out.cellules[mode] = cel;
      var bhL = [], lg = [];
      for (k = 0; k < K; k++) {
        var r = backtest(un, M[k].o, M[k].c, a0, T, pb[k] / 1e4);
        bhL.push(fusion(r[0], stats(r[1], datesLong)));
      }
      for (i = 0; i < STRATEGIES.length; i++) {
        var ligne = [];
        for (k = 0; k < K; k++) {
          var rr = backtest(calc[STRATEGIES[i]][k].sig, M[k].o, M[k].c, a0, T, pb[k] / 1e4);
          ligne.push(fusion(rr[0], stats(rr[1], datesLong)));
        }
        lg.push(ligne);
      }
      out.long[mode] = lg;
      out.acheter_conserver[mode] = { passes: bhP, long: bhL };
    });
    return out;
  }

  var BT = {
    N_PASSE: N_PASSE, FRAIS: FRAIS, STRATEGIES: STRATEGIES, NOMS: NOMS,
    sma: sma, ecartType: ecartType, ema: ema, atr: atr, pysum: pysum,
    supertrend: supertrend, zscore: zscore, dualmom: dualmom, ema_stop: ema_stop, keltner: keltner, stoch: stoch, rsi2: rsi2,
    backtest: backtest, stats: stats, passes: passes, calculer: calculer, tout: tout
  };
  if (typeof module !== 'undefined' && module.exports) module.exports = BT;
  else racine.BT = BT;
})(typeof window !== 'undefined' ? window : this);
