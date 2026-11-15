/* Interface du terminal de backtest : animation, graphiques sur <canvas>, tableaux. Tous les nombres viennent du
   moteur (window.BT) ou de comparatif.json. Aucune couleur littérale : tout est lu dans les variables CSS. */
(function () {
  'use strict';

  var BT = window.BT;
  var D = JSON.parse(document.getElementById('donnees').textContent);
  var CMP = JSON.parse(document.getElementById('comparatif').textContent);
  var S = BT.STRATEGIES, NOMS = BT.NOMS, M = D.marches, K = M.length, T = D.dates.length;
  var calc = BT.calculer(D);
  var R = BT.tout(D, calc, ['demande']);
  var P = R.meta.passes, NP = P.length;
  var FR = BT.FRAIS.demande.map(function (x) { return x / 1e4; });
  var CEL = R.cellules.demande, BH = R.acheter_conserver.demande;
  var UN = []; for (var i0 = 0; i0 < T; i0++) UN.push(1);

  var reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function (id) { return document.getElementById(id); };

  // ------------------------------------------------------------------ formats français
  var MOINS = '−', NBSP = ' ', FINE = ' ';
  function grouper(s) { return s.replace(/\B(?=(\d{3})+(?!\d))/g, FINE); }
  function nombre(x, dec) {
    var s = Math.abs(x).toFixed(dec), p = s.split('.');
    return (x < 0 && Number(s) !== 0 ? MOINS : '') + grouper(p[0]) + (p[1] ? ',' + p[1] : '');
  }
  function signe(x, dec) { return (x < 0 ? MOINS : '+') + nombre(Math.abs(x), dec); }
  function pct(x, dec) { return signe(x * 100, dec === undefined ? 1 : dec) + NBSP + '%'; }
  function dollars(x) { return signe(x, 0) + NBSP + '$'; }
  var MOIS = ['janv.', 'févr.', 'mars', 'avr.', 'mai', 'juin', 'juil.', 'août', 'sept.', 'oct.', 'nov.', 'déc.'];
  function dateFr(d) { return Number(d.slice(8, 10)) + ' ' + MOIS[Number(d.slice(5, 7)) - 1] + ' ' + d.slice(0, 4); }
  function moisFr(d) { return MOIS[Number(d.slice(5, 7)) - 1] + ' ' + d.slice(0, 4); }

  var COURT = { NQ: 'NQ', ES: 'ES', GC: 'Or', CL: 'Pétrole' };
  var SUR = { NQ: 'sur le NQ', ES: 'sur l’ES', GC: 'sur l’or', CL: 'sur le pétrole' };
  var COURT_S = { supertrend: 'Supertrend', zscore: 'Z-score', dualmom: 'Dual mom.', ema_stop: 'EMA+stop', keltner: 'Keltner', stoch: 'Stoch.', rsi2: 'RSI(2)' };
  var REGLE = {
    supertrend: 'Suit la tendance : une ligne placée à 3 fois la volatilité moyenne (ATR 10) sous le prix en achat, au-dessus en vente. Toujours en position ; on se retourne quand la clôture traverse la ligne.',
    zscore: 'Joue le retour à la moyenne : achat quand la clôture tombe à 1,5 écart-type sous sa moyenne 20, vente quand elle monte à 1,5 au-dessus ; sortie quand elle revient sur la moyenne.',
    dualmom: 'Une fois par mois, à la 1re séance : achat des marchés dont le gain sur 126 séances est positif et parmi les 2 meilleurs des 4. Sinon, à plat.',
    ema_stop: 'Achat quand l’EMA 20 passe au-dessus de l’EMA 50. Stop suiveur à 3 ATR 14 sous le plus haut, lu sur les clôtures ; sortie au stop ou si l’EMA 20 repasse dessous.',
    keltner: 'Achat quand la clôture sort au-dessus du canal (EMA 20 + 2 ATR 10), vente quand elle sort dessous ; sortie au retour sur l’EMA 20.',
    stoch: 'Achat quand %K recoupe %D vers le haut sous 20, sortie au-dessus de 80 ; vente symétrique au-dessus de 80, sortie sous 20. Version rapide (%K non lissé).',
    rsi2: 'Achat seulement : au-dessus de la moyenne 200, quand le RSI(2) passe sous 10 ; sortie dès que la clôture repasse au-dessus de la moyenne 5.'
  };
  // Tracés sur le prix et bande d'indicateur, par stratégie
  var DESSIN = {
    supertrend: { prix: [{ type: 'supertrend' }], osc: null,
      legende: [['ligne', '--hausse', 'Supertrend en achat'], ['ligne', '--baisse', 'Supertrend en vente']] },
    zscore: { prix: [{ type: 'bande', haut: 'haut', bas: 'bas', c: '--s3' }, { type: 'ligne', d: 'moyenne', c: '--s1' }],
      osc: { nom: 'z (écarts-types)', lignes: [['z', '--s2']], seuils: [-1.5, 0, 1.5], min: -3, max: 3, dyn: true },
      legende: [['ligne', '--s1', 'Moyenne 20'], ['bande', '--s3', 'Bandes ±1,5 écart-type'], ['ligne', '--s2', 'z, sous le prix']] },
    dualmom: { prix: [{ type: 'ligne', d: 'prix_126', c: '--s2' }],
      osc: { nom: 'gain sur 126 séances (%)', lignes: [['momentum', '--s1']], seuils: [0], min: 0, max: 0, dyn: true },
      legende: [['ligne', '--s2', 'Prix d’il y a 126 séances'], ['ligne', '--s1', 'Gain sur 126 séances, sous le prix']] },
    ema_stop: { prix: [{ type: 'ligne', d: 'ema20', c: '--s1' }, { type: 'ligne', d: 'ema50', c: '--s2' }, { type: 'ligne', d: 'stop', c: '--s3' }], osc: null,
      legende: [['ligne', '--s1', 'EMA 20'], ['ligne', '--s2', 'EMA 50'], ['ligne', '--s3', 'Stop suiveur']] },
    keltner: { prix: [{ type: 'bande', haut: 'haut', bas: 'bas', c: '--s3' }, { type: 'ligne', d: 'ema20', c: '--s1' }], osc: null,
      legende: [['ligne', '--s1', 'EMA 20'], ['bande', '--s3', 'Canal ±2 ATR 10']] },
    stoch: { prix: [],
      osc: { nom: '%K et %D', lignes: [['k', '--s1'], ['d', '--s2']], seuils: [20, 80], min: 0, max: 100, dyn: false },
      legende: [['ligne', '--s1', '%K, sous le prix'], ['ligne', '--s2', '%D, sous le prix']] },
    rsi2: { prix: [{ type: 'ligne', d: 'sma200', c: '--s2' }, { type: 'ligne', d: 'sma5', c: '--s1' }],
      osc: { nom: 'RSI(2)', lignes: [['rsi', '--s3']], seuils: [10], min: 0, max: 100, dyn: false },
      legende: [['ligne', '--s1', 'Moyenne 5'], ['ligne', '--s2', 'Moyenne 200'], ['ligne', '--s3', 'RSI(2), sous le prix']] }
  };

  // ------------------------------------------------------------------ couleurs (variables CSS, relues au changement de thème)
  var NOMS_COULEURS = ['--fond', '--panneau', '--panneau-2', '--filet', '--grille', '--axe', '--encre', '--encre-2', '--discret', '--ambre',
    '--hausse', '--hausse-ombre', '--hausse-ombre-2', '--baisse', '--baisse-ombre', '--baisse-ombre-2', '--plat', '--s1', '--s2', '--s3',
    '--s3-voile', '--bougie-haut', '--bougie-bas', '--repere', '--sol', '--sur-couleur'];
  var COUL = {}, MONO = 'monospace';
  function lireCouleurs() {
    var cs = getComputedStyle(document.documentElement);
    NOMS_COULEURS.forEach(function (n) { COUL[n] = cs.getPropertyValue(n).trim(); });
    MONO = cs.getPropertyValue('--mono').trim() || 'monospace';
    toutSale();
  }

  // ------------------------------------------------------------------ état
  var etat = { p: 0, s: 0, phase: 'balayage', tPhase: 0, nf: 0, n: 0, lecture: !reduit, vitesse: 1, cellules: 0 };
  var remplies = [];          // remplies[s][k] = true quand la cellule est affichée
  var cumul = [];             // par stratégie : { somme, n, bat, joue }
  var cumulBh = { somme: 0, n: 0 };
  var cyclePasses = 0, cycleBat = 0, cycleJoue = 0;
  var dessin = null;          // données de dessin de la stratégie en cours
  var bhCourbes = [];
  var derniere = null;        // dernière cellule remplie { s, k }
  var DUREE = { balayage: 6000, cellule: 380, pause: 900, finPasse: 2600, pauseReduite: 3500 };

  function viderCumul() {
    cumul = S.map(function () { return { somme: 0, n: 0, bat: 0, joue: 0 }; });
    cumulBh = { somme: 0, n: 0 };
    cyclePasses = 0; cycleBat = 0; cycleJoue = 0;
  }

  // ------------------------------------------------------------------ construction du DOM
  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt !== undefined && txt !== null) e.textContent = txt;
    return e;
  }

  var panneaux = [];
  function construireGraphes() {
    var g = $('graphes');
    M.forEach(function (m, k) {
      var art = el('article', 'graphe');
      art.setAttribute('aria-label', 'Graphique ' + m.nom);
      var tete = el('header', 'graphe-tete');
      tete.appendChild(el('span', 'g-id', m.id));
      tete.appendChild(el('span', 'g-nom', m.nom));
      tete.appendChild(el('span', 'g-contrat', m.contrat));
      var gs = el('span', 'g-strat', '');
      tete.appendChild(gs);
      art.appendChild(tete);
      var zone = el('div', 'g-zone');
      var cv = el('canvas', 'g-prix');
      cv.setAttribute('role', 'img');
      var ib = el('div', 'infobulle'); ib.hidden = true;
      zone.appendChild(cv); zone.appendChild(ib);
      art.appendChild(zone);
      var vals = el('div', 'g-valeurs');
      var v1 = el('span'), v2 = el('span');
      var k1 = el('span', 'cle-ligne'); k1.style.background = 'var(--ambre)';
      var k2 = el('span', 'cle-ligne'); k2.style.background = 'var(--repere)';
      var b1 = el('b', 'v-strat', '+0,0' + NBSP + '%'), b2 = el('b', 'v-bh', '+0,0' + NBSP + '%');
      v1.appendChild(k1); v1.appendChild(document.createTextNode('Stratégie ')); v1.appendChild(b1);
      v2.appendChild(k2); v2.appendChild(document.createTextNode('Acheter et conserver ')); v2.appendChild(b2);
      vals.appendChild(v1); vals.appendChild(v2);
      art.appendChild(vals);
      var cc = el('canvas', 'g-course');
      cc.setAttribute('aria-hidden', 'true');
      art.appendChild(cc);
      g.appendChild(art);
      var pan = { k: k, cv: cv, cc: cc, ib: ib, gs: gs, b1: b1, b2: b2, survol: -1, geo: null };
      panneaux.push(pan);
      cv.addEventListener('pointermove', function (ev) { survoler(pan, ev); });
      cv.addEventListener('pointerdown', function (ev) { survoler(pan, ev); });
      cv.addEventListener('pointerleave', function () { pan.survol = -1; pan.ib.hidden = true; toutSale(); });
    });
  }

  function construireTablePasse() {
    var t = $('table-passe');
    var th = el('thead'), tr = el('tr');
    tr.appendChild(el('th', null, 'Stratégie'));
    M.forEach(function (m) { tr.appendChild(el('th', null, COURT[m.id] || m.id)); });
    tr.appendChild(el('th', 'col-moy', 'Moyenne'));
    th.appendChild(tr); t.appendChild(th);
    var tb = el('tbody');
    var lb = el('tr', 'ligne-repere'); lb.id = 'ligne-bh';
    lb.appendChild(el('th', null, 'Acheter et conserver'));
    for (var k = 0; k <= K; k++) { var c = el('td', 'cel bh' + (k === K ? ' col-moy' : '')); c.dataset.k = String(k); lb.appendChild(c); }
    tb.appendChild(lb);
    S.forEach(function (s, si) {
      var r = el('tr'); r.dataset.s = String(si);
      r.appendChild(el('th', null, NOMS[s]));
      for (var k = 0; k <= K; k++) {
        var c = el('td', 'cel vide' + (k === K ? ' col-moy' : ''), '·');
        c.dataset.s = String(si); c.dataset.k = String(k);
        r.appendChild(c);
      }
      tb.appendChild(r);
    });
    t.appendChild(tb);
  }

  var lignesClassement = {};
  function construireClassement() {
    var ol = $('classement');
    var ids = ['bh'].concat(S);
    ids.forEach(function (id) {
      var li = el('li', id === 'bh' ? 'repere' : '');
      li.dataset.id = id;
      li.appendChild(el('span', 'rang', ''));
      li.appendChild(el('span', 'nom', id === 'bh' ? 'Acheter et conserver (repère)' : NOMS[id]));
      li.appendChild(el('span', 'moy', '—'));
      li.appendChild(el('span', 'bat', ''));
      ol.appendChild(li);
      lignesClassement[id] = li;
    });
  }

  // ------------------------------------------------------------------ sections fixes (7 à 9)
  function niveauPastille(lg) {
    var n = 0;
    lg.forEach(function (x) { if (x.t_alpha >= 2) n++; });
    return n >= 2 ? 'tient' : n === 1 ? 'surveiller' : 'rien';
  }
  var TEXTE_PASTILLE = { tient: 'tient', surveiller: 'à surveiller', rien: 'rien de mesurable' };

  function construireVerdict() {
    var L = R.meta.long, nb = S.length * K * NP;
    $('verdict-phrase').textContent = 'Du ' + dateFr(L.debut) + ' au ' + dateFr(L.fin) + ', d’un seul tenant, et ' + nb +
      ' backtests d’un an (' + S.length + ' stratégies × ' + K + ' marchés × ' + NP + ' passes). Rendement annuel moyen, frais et changements de contrat compris.';
    var t = $('table-verdict');
    var th = el('thead'), tr = el('tr');
    tr.appendChild(el('th', null, 'Stratégie'));
    M.forEach(function (m) { tr.appendChild(el('th', null, COURT[m.id] || m.id)); });
    tr.appendChild(el('th', null, 'Bat le marché'));
    th.appendChild(tr); t.appendChild(th);
    var tb = el('tbody');
    var lignes = [{ id: 'bh', nom: 'Acheter et conserver', lg: BH.long }].concat(S.map(function (s, si) { return { id: s, si: si, nom: NOMS[s], lg: R.long.demande[si] }; }));
    lignes.forEach(function (L2) {
      var r = el('tr', L2.id === 'bh' ? 'ligne-repere' : '');
      r.dataset.id = L2.id;
      var h = el('th');
      h.appendChild(el('span', 'nom-l', L2.nom));
      var niv = L2.id === 'bh' ? 'repere' : niveauPastille(L2.lg);
      var pa = el('span', 'pastille ' + niv, L2.id === 'bh' ? 'repère' : TEXTE_PASTILLE[niv]);
      pa.dataset.niveau = niv;
      h.appendChild(pa);
      r.appendChild(h);
      L2.lg.forEach(function (x, k) {
        var td = el('td'); td.dataset.k = String(k);
        var cg = el('span', 'v-cagr', pct(x.cagr)); cg.dataset.valeur = String(x.cagr);
        td.appendChild(cg);
        if (L2.id !== 'bh') {
          var d1 = el('span', 'v-detail');
          d1.appendChild(document.createTextNode('hors marché ' + pct(x.alpha_an) + ' · '));
          var ta = el('span', 'v-talpha', 't ' + signe(x.t_alpha, 2)); ta.dataset.valeur = String(x.t_alpha);
          d1.appendChild(ta);
          td.appendChild(d1);
        }
        td.appendChild(el('span', 'v-detail', 'baisse ' + pct(x.dd, 0)));
        r.appendChild(td);
      });
      var tdb = el('td');
      if (L2.id === 'bh') tdb.textContent = '—';
      else {
        var bat = 0, joue = 0;
        CEL.forEach(function (pc) { pc[L2.si].forEach(function (c) { if (c.trades > 0) { joue++; if (c.ret > c.bh) bat++; } }); });
        tdb.textContent = bat + ' sur ' + joue;
      }
      r.appendChild(tdb);
      tb.appendChild(r);
    });
    t.appendChild(tb);
    $('verdict-legende').textContent = 'Hors marché : ce que la stratégie gagne une fois retirée la part qui vient simplement de la hausse (ou de la baisse) du marché. ' +
      'Le t dit si ce gain a des chances d’être dû au hasard : au-dessus de 2, c’est peu probable. Avec ' + (S.length * K) +
      ' tests, un t ≥ 2 sur un seul marché arrive environ une fois par hasard. Pastille : « tient » si t ≥ 2 sur au moins 2 marchés, « à surveiller » sur 1 seul, « rien de mesurable » sinon. ' +
      '« Bat le marché » : années-marchés où la stratégie fait mieux qu’acheter et conserver, parmi celles où elle a pris au moins un trade.';
  }

  function construireBots() {
    $('bots-unite').textContent = 'En ' + CMP.unite + ' · ' + dateFr(CMP.periode.debut) + ' → ' + dateFr(CMP.periode.fin);
    var t = $('table-bots');
    var th = el('thead'), tr = el('tr');
    ['Stratégie', 'Gain par an', 'Hors marché par an', 't hors marché', 't depuis 2023', 'Pire baisse', 'Années perdantes', 'Bulenox'].forEach(function (x) { tr.appendChild(el('th', null, x)); });
    th.appendChild(tr); t.appendChild(th);
    var lignes = CMP.lignes.slice().sort(function (a, b) {
      var ta = a.t_hors_marche, tb2 = b.t_hors_marche;
      if (ta === null && tb2 === null) return 0;
      if (ta === null) return 1;
      if (tb2 === null) return -1;
      return tb2 - ta;
    });
    var tb = el('tbody');
    function v(x, f) { return x === null || x === undefined ? '—' : f(x); }
    lignes.forEach(function (l) {
      var r = el('tr', l.famille === 'tes bots' ? 'tes-bots' : l.famille === 'repere' ? 'repere' : '');
      var h = el('th');
      h.appendChild(document.createTextNode(l.nom));
      if (l.famille === 'tes bots') h.appendChild(el('span', 'etiquette', 'ton bot'));
      if (l.note) h.appendChild(el('span', 'note', l.note));
      r.appendChild(h);
      r.appendChild(el('td', null, v(l.par_an, dollars)));
      r.appendChild(el('td', null, v(l.hors_marche_par_an, dollars)));
      r.appendChild(el('td', null, v(l.t_hors_marche, function (x) { return signe(x, 2); })));
      r.appendChild(el('td', null, v(l.t_depuis_2023, function (x) { return signe(x, 2); })));
      r.appendChild(el('td', null, v(l.pire_baisse, dollars)));
      var ap = el('td', null, l.annees_perdantes ? String(l.annees_perdantes.length) : '—');
      if (l.annees_perdantes && l.annees_perdantes.length) ap.title = l.annees_perdantes.join(', ');
      r.appendChild(ap);
      r.appendChild(el('td', 'bulenox', l.bulenox || '—'));
      tb.appendChild(r);
    });
    t.appendChild(tb);
    var ul = $('conclusions');
    CMP.conclusions.forEach(function (c) { ul.appendChild(el('li', null, c)); });
  }

  function construireMethode() {
    var L = R.meta.long, pb = BT.FRAIS.demande[0];
    var items = [
      'Données : ' + D.source + '. Du ' + dateFr(D.dates[0]) + ' au ' + dateFr(D.dates[T - 1]) + ', ' + grouper(String(T)) + ' séances communes aux ' + K + ' marchés ; les mesures commencent le ' + dateFr(L.debut) + ', quand tous les indicateurs sont calculés.',
      'Le signal est décidé à la clôture d’une séance, l’ordre est exécuté à l’ouverture de la suivante : aucun regard vers le futur.',
      'Frais : ' + nombre(pb, 0) + ' points de base par ordre (' + nombre(pb / 100, 2) + NBSP + '%), à l’entrée comme à la sortie ; un retournement compte 2 ordres.',
      'Prix ajustés des changements de contrat ; une position gardée à travers un changement paie 2 ordres de plus (vente de l’ancien contrat, achat du nouveau).',
      'Pas d’intérêts sur la trésorerie : à plat, l’argent ne rapporte rien.',
      'Les passes remontent le temps d’un an (' + BT.N_PASSE + ' séances) à chaque fois : la passe 1 est l’année la plus récente.',
      'Les réglages sont ceux des manuels, fixés avant le premier calcul et jamais ajustés ensuite.',
      'Le stochastique est la version rapide (%K non lissé) ; le stop de la stratégie EMA se lit sur les clôtures.',
      'La pire baisse est mesurée en fin de séance : en séance, elle a pu être plus forte.',
      'Ces stratégies gardent la position plusieurs jours, ce qui est interdit sur un compte Bulenox.',
      'Un backtest ne garantit rien : le passé ne dit pas ce que fera le marché.'
    ];
    var ul = $('methode');
    items.forEach(function (x) { ul.appendChild(el('li', null, x)); });
  }

  // ------------------------------------------------------------------ préparation d'une stratégie (données de dessin)
  function preparer(p, si) {
    var s = S[si], a = P[p].a, b = P[p].b, nb = b - a, cfg = DESSIN[s];
    var mk = M.map(function (m, k) {
      var c = calc[s][k], sig = c.sig, ser = c.series;
      var bt = BT.backtest(sig, m.o, m.c, m.r, a, b, FR[k]);
      var pos = [], ev = [];
      for (var i = 0; i < nb; i++) pos.push(sig[a + i - 1]);
      for (i = 0; i < nb; i++) {
        var prev = i === 0 ? 0 : pos[i - 1];
        if (pos[i] !== prev) ev.push({ i: i, type: pos[i] === 1 ? 'achat' : pos[i] === -1 ? 'vente' : 'sortie', y: m.o[a + i] });
      }
      if (pos[nb - 1] !== 0) ev.push({ i: nb - 1, type: 'sortie', y: m.c[b - 1], fin: true });
      // échelle du prix : barres + tracés
      var lo = Infinity, hi = -Infinity;
      for (i = a; i < b; i++) { if (m.l[i] < lo) lo = m.l[i]; if (m.h[i] > hi) hi = m.h[i]; }
      function inclure(arr) { for (var j = a; j < b; j++) { var v = arr[j]; if (isFinite(v)) { if (v < lo) lo = v; if (v > hi) hi = v; } } }
      cfg.prix.forEach(function (o) {
        if (o.type === 'supertrend') inclure(ser.ligne);
        else if (o.type === 'bande') { inclure(ser[o.haut]); inclure(ser[o.bas]); }
        else inclure(ser[o.d]);
      });
      var pad = (hi - lo) * 0.05; lo -= pad; hi += pad;
      // échelle de l'oscillateur
      var olo = null, ohi = null;
      if (cfg.osc) {
        olo = cfg.osc.min; ohi = cfg.osc.max;
        if (cfg.osc.dyn) cfg.osc.lignes.forEach(function (l) {
          var arr = ser[l[0]];
          for (var j = a; j < b; j++) if (isFinite(arr[j])) { if (arr[j] < olo) olo = arr[j]; if (arr[j] > ohi) ohi = arr[j]; }
        });
        if (cfg.osc.dyn) { var op = (ohi - olo) * 0.08; olo -= op; ohi += op; }
      }
      // échelle de la course
      var cmin = 0, cmax = 0, bhc = bhCourbes[k];
      for (i = 0; i < nb; i++) {
        var v1 = bt[2][i] - 1, v2 = bhc[i] - 1;
        cmin = Math.min(cmin, v1, v2); cmax = Math.max(cmax, v1, v2);
      }
      var cp = (cmax - cmin) * 0.1 || 0.01; cmin -= cp; cmax += cp;
      return { sig: sig, ser: ser, courbe: bt[2], pos: pos, ev: ev, lo: lo, hi: hi, olo: olo, ohi: ohi, cmin: cmin, cmax: cmax };
    });
    return { p: p, si: si, s: s, a: a, b: b, nb: nb, cfg: cfg, mk: mk };
  }

  // ------------------------------------------------------------------ canvas : outils
  function preparerCanvas(cv) {
    var r = cv.getBoundingClientRect(), dpr = window.devicePixelRatio || 1;
    var w = Math.max(1, Math.round(r.width)), h = Math.max(1, Math.round(r.height));
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); }
    var ctx = cv.getContext('2d');
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    return { ctx: ctx, w: w, h: h };
  }
  function graduations(lo, hi, n) {
    var brut = (hi - lo) / n, p10 = Math.pow(10, Math.floor(Math.log10(brut))), f = brut / p10;
    var pas = (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * p10;
    var out = [];
    for (var v = Math.ceil(lo / pas) * pas; v <= hi + 1e-9; v += pas) out.push(v);
    return { v: out, pas: pas };
  }
  function decimales(pas) { return pas >= 1 ? 0 : pas >= 0.1 ? 1 : 2; }
  function police(ctx, taille, poids) { ctx.font = (poids || '400') + ' ' + taille + 'px ' + MONO; }

  // ------------------------------------------------------------------ graphique du prix
  function dessinerPrix(pan) {
    var c = preparerCanvas(pan.cv), ctx = c.ctx, W = c.w, H = c.h;
    var d = dessin, mk = d.mk[pan.k], m = M[pan.k], a = d.a, nb = d.nb, n = etat.n;
    var padL = 4, padR = 46, haut = 6, bas = 15, bande = 9, ecart = 6;
    var oscH = d.cfg.osc ? Math.round((H - haut - bas) * 0.24) : 0;
    var yPrixBas = H - bas - bande - ecart - (oscH ? oscH + ecart : 0);
    var plotW = W - padL - padR, bw = plotW / nb;
    var X = function (i) { return padL + (i + 0.5) * bw; };
    var Y = function (v) { return haut + (mk.hi - v) / (mk.hi - mk.lo) * (yPrixBas - haut); };
    pan.geo = { padL: padL, bw: bw, nb: nb, W: W, padR: padR };

    // grille + graduations
    var g = graduations(mk.lo, mk.hi, 4), dec = decimales(g.pas);
    police(ctx, 10); ctx.textBaseline = 'middle'; ctx.textAlign = 'left';
    g.v.forEach(function (v) {
      var y = Math.round(Y(v)) + 0.5;
      if (y < haut || y > yPrixBas) return;
      ctx.strokeStyle = COUL['--grille']; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
      ctx.fillStyle = COUL['--discret'];
      ctx.fillText(nombre(v, dec), padL + plotW + 5, y);
    });

    // bandes (voile) sous les bougies
    d.cfg.prix.forEach(function (o) { if (o.type === 'bande') voile(ctx, mk.ser[o.haut], mk.ser[o.bas], a, n, X, Y, o.c); });

    // bougies
    var cw = Math.max(1, bw * 0.62);
    for (var i = 0; i < nb; i++) {
      var t = a + i, up = m.c[t] >= m.o[t];
      ctx.globalAlpha = i < n ? 1 : 0.38;
      var col = up ? COUL['--bougie-haut'] : COUL['--bougie-bas'];
      var x = X(i);
      ctx.strokeStyle = col; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(x, Y(m.h[t])); ctx.lineTo(x, Y(m.l[t])); ctx.stroke();
      var y1 = Y(Math.max(m.o[t], m.c[t])), y2 = Y(Math.min(m.o[t], m.c[t]));
      ctx.fillStyle = col;
      ctx.fillRect(x - cw / 2, y1, cw, Math.max(1, y2 - y1));
    }
    ctx.globalAlpha = 1;

    // tracés de la stratégie
    d.cfg.prix.forEach(function (o) {
      if (o.type === 'bande') { ligne(ctx, mk.ser[o.haut], a, n, X, Y, COUL[o.c], 1.25); ligne(ctx, mk.ser[o.bas], a, n, X, Y, COUL[o.c], 1.25); }
      else if (o.type === 'ligne') ligne(ctx, mk.ser[o.d], a, n, X, Y, COUL[o.c], 2);
      else if (o.type === 'supertrend') supertrendLigne(ctx, mk.ser, a, n, X, Y);
    });

    // flèches d'ordres
    mk.ev.forEach(function (e) {
      if (e.i >= n || (e.fin && n < nb)) return;
      var x = X(e.i) - (e.fin ? 0 : bw * 0.5), y = Y(e.y);
      fleche(ctx, e.type, x, y);
    });

    // bande d'indicateur
    if (oscH) {
      var o = d.cfg.osc, y0 = yPrixBas + ecart, y1b = y0 + oscH;
      var YO = function (v) { return y0 + (mk.ohi - v) / (mk.ohi - mk.olo) * oscH; };
      ctx.strokeStyle = COUL['--filet']; ctx.lineWidth = 1;
      ctx.strokeRect(padL + 0.5, y0 + 0.5, plotW - 1, oscH - 1);
      police(ctx, 9.5);
      o.seuils.forEach(function (sv) {
        var y = Math.round(YO(sv)) + 0.5;
        ctx.strokeStyle = COUL['--axe'];
        ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
        ctx.fillStyle = COUL['--discret']; ctx.textAlign = 'left';
        ctx.fillText(sv === 0 ? '0' : (o.dyn && sv > 0 ? '+' : '') + nombre(sv, sv % 1 ? 1 : 0), padL + plotW + 5, y);
      });
      ctx.save();
      ctx.beginPath(); ctx.rect(padL, y0, plotW, oscH); ctx.clip();
      o.lignes.forEach(function (l) { ligne(ctx, mk.ser[l[0]], a, n, X, YO, COUL[l[1]], 1.5); });
      ctx.restore();
      police(ctx, 9.5);
      ctx.textAlign = 'left'; ctx.textBaseline = 'top';
      var lt = ctx.measureText(o.nom).width;
      ctx.globalAlpha = 0.85; ctx.fillStyle = COUL['--panneau']; ctx.fillRect(padL + 1, y0 + 1, lt + 7, 13); ctx.globalAlpha = 1;
      ctx.fillStyle = COUL['--discret'];
      ctx.fillText(o.nom, padL + 4, y0 + 3);
      ctx.textBaseline = 'middle';
    }

    // barre de position
    var yb = H - bas - bande;
    ctx.fillStyle = COUL['--grille'];
    ctx.fillRect(padL, yb, plotW, bande);
    var debut = 0;
    for (i = 1; i <= Math.min(n, nb); i++) {
      if (i === Math.min(n, nb) || mk.pos[i] !== mk.pos[debut]) {
        var w0 = mk.pos[debut];
        var x0 = padL + debut * bw, x1 = padL + i * bw - (i < n ? 1 : 0);
        ctx.fillStyle = w0 === 1 ? COUL['--hausse'] : w0 === -1 ? COUL['--baisse'] : COUL['--plat'];
        ctx.fillRect(x0, yb, Math.max(0.5, x1 - x0), bande);
        if (w0 !== 0 && x1 - x0 >= 12) {
          ctx.fillStyle = COUL['--sur-couleur']; police(ctx, 7.5); ctx.textAlign = 'center';
          ctx.fillText(w0 === 1 ? '▲' : '▼', (x0 + x1) / 2, yb + bande / 2 + 0.5);
        }
        debut = i;
      }
    }
    police(ctx, 9.5); ctx.fillStyle = COUL['--discret']; ctx.textAlign = 'left';
    ctx.fillText('pos.', padL + plotW + 5, yb + bande / 2);

    // dates
    var yd = H - bas / 2 + 1;
    police(ctx, 9.5); ctx.fillStyle = COUL['--discret'];
    ctx.textAlign = 'left'; ctx.fillText(moisFr(D.dates[a]), padL, yd);
    ctx.textAlign = 'center'; ctx.fillText(moisFr(D.dates[a + Math.floor(nb / 2)]), padL + plotW / 2, yd);
    ctx.textAlign = 'right'; ctx.fillText(moisFr(D.dates[a + nb - 1]), padL + plotW, yd);

    // curseur du balayage
    if (n > 0 && n < nb) {
      var xc = Math.round(padL + n * bw) + 0.5;
      ctx.strokeStyle = COUL['--ambre']; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(xc, haut); ctx.lineTo(xc, yb + bande); ctx.stroke();
    }
    // réticule du survol
    if (pan.survol >= 0) {
      var xs = Math.round(X(pan.survol)) + 0.5;
      ctx.strokeStyle = COUL['--encre-2']; ctx.globalAlpha = 0.6;
      ctx.beginPath(); ctx.moveTo(xs, haut); ctx.lineTo(xs, yb + bande); ctx.stroke();
      ctx.globalAlpha = 1;
    }
    pan.cv.setAttribute('aria-label', m.nom + ' : ' + nb + ' séances en bougies, stratégie ' + NOMS[d.s] + ' dessinée sur le prix.');
  }

  function ligne(ctx, arr, a, n, X, Y, col, lw) {
    ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    ctx.beginPath();
    var ouvert = false;
    for (var i = 0; i < n; i++) {
      var v = arr[a + i];
      if (!isFinite(v)) { ouvert = false; continue; }
      if (!ouvert) { ctx.moveTo(X(i), Y(v)); ouvert = true; } else ctx.lineTo(X(i), Y(v));
    }
    ctx.stroke();
  }
  function voile(ctx, h, b, a, n, X, Y, c) {
    ctx.fillStyle = COUL[c + '-voile'] || COUL['--s3-voile'];
    var i = 0;
    while (i < n) {
      while (i < n && !(isFinite(h[a + i]) && isFinite(b[a + i]))) i++;
      var d0 = i;
      while (i < n && isFinite(h[a + i]) && isFinite(b[a + i])) i++;
      if (i - d0 < 2) continue;
      ctx.beginPath();
      for (var j = d0; j < i; j++) { if (j === d0) ctx.moveTo(X(j), Y(h[a + j])); else ctx.lineTo(X(j), Y(h[a + j])); }
      for (j = i - 1; j >= d0; j--) ctx.lineTo(X(j), Y(b[a + j]));
      ctx.closePath(); ctx.fill();
    }
  }
  function supertrendLigne(ctx, ser, a, n, X, Y) {
    ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
    var i = 0;
    while (i < n) {
      var sens = ser.sens[a + i], d0 = i;
      while (i < n && ser.sens[a + i] === sens) i++;
      ctx.strokeStyle = sens > 0 ? COUL['--hausse'] : COUL['--baisse'];
      ctx.beginPath();
      for (var j = d0; j < i; j++) { if (j === d0) ctx.moveTo(X(j), Y(ser.ligne[a + j])); else ctx.lineTo(X(j), Y(ser.ligne[a + j])); }
      if (i - d0 === 1) ctx.lineTo(X(d0) + 0.5, Y(ser.ligne[a + d0]));
      ctx.stroke();
    }
  }
  function fleche(ctx, type, x, y) {
    ctx.lineJoin = 'round';
    if (type === 'sortie') {
      var r = 3.5;
      ctx.lineCap = 'round';
      ctx.strokeStyle = COUL['--panneau']; ctx.lineWidth = 4.5;
      ctx.beginPath(); ctx.moveTo(x - r, y - r); ctx.lineTo(x + r, y + r); ctx.moveTo(x + r, y - r); ctx.lineTo(x - r, y + r); ctx.stroke();
      ctx.strokeStyle = COUL['--encre']; ctx.lineWidth = 1.6;
      ctx.beginPath(); ctx.moveTo(x - r, y - r); ctx.lineTo(x + r, y + r); ctx.moveTo(x + r, y - r); ctx.lineTo(x - r, y + r); ctx.stroke();
      return;
    }
    var hautVers = type === 'achat', dir = hautVers ? 1 : -1, tip = y + dir * 2, base = y + dir * 10;
    ctx.beginPath(); ctx.moveTo(x, tip); ctx.lineTo(x - 5, base); ctx.lineTo(x + 5, base); ctx.closePath();
    ctx.strokeStyle = COUL['--panneau']; ctx.lineWidth = 2; ctx.stroke();
    ctx.fillStyle = hautVers ? COUL['--hausse'] : COUL['--baisse']; ctx.fill();
  }

  // ------------------------------------------------------------------ course des courbes
  function dessinerCourse(pan) {
    var c = preparerCanvas(pan.cc), ctx = c.ctx, W = c.w, H = c.h;
    var d = dessin, mk = d.mk[pan.k], nb = d.nb, n = etat.n, bh = bhCourbes[pan.k];
    var padL = 4, padR = 46, haut = 8, bas = 8, plotW = W - padL - padR, bw = plotW / nb;
    var X = function (i) { return padL + (i + 0.5) * bw; };
    var Y = function (v) { return haut + (mk.cmax - v) / (mk.cmax - mk.cmin) * (H - haut - bas); };
    var y0 = Math.round(Y(0)) + 0.5;
    ctx.strokeStyle = COUL['--axe']; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(padL, y0); ctx.lineTo(padL + plotW, y0); ctx.stroke();
    police(ctx, 9.5); ctx.textBaseline = 'middle'; ctx.textAlign = 'left'; ctx.fillStyle = COUL['--discret'];
    ctx.fillText('0' + NBSP + '%', padL + plotW + 5, y0);
    var g = graduations(mk.cmin, mk.cmax, 2);
    g.v.forEach(function (v) {
      if (Math.abs(v) < 1e-12) return;
      var y = Math.round(Y(v)) + 0.5;
      if (Math.abs(y - y0) < 12) return;
      ctx.strokeStyle = COUL['--grille'];
      ctx.beginPath(); ctx.moveTo(padL, y); ctx.lineTo(padL + plotW, y); ctx.stroke();
      ctx.fillText(signe(v * 100, 0) + NBSP + '%', padL + plotW + 5, y);
    });
    function courbe(arr, col) {
      if (n <= 0) return;
      ctx.strokeStyle = col; ctx.lineWidth = 2; ctx.lineJoin = 'round'; ctx.lineCap = 'round';
      ctx.beginPath();
      for (var i = 0; i < n; i++) { if (i === 0) ctx.moveTo(X(i), Y(arr[i] - 1)); else ctx.lineTo(X(i), Y(arr[i] - 1)); }
      ctx.stroke();
      ctx.beginPath(); ctx.arc(X(n - 1), Y(arr[n - 1] - 1), 4, 0, Math.PI * 2);
      ctx.fillStyle = col; ctx.fill();
      ctx.strokeStyle = COUL['--panneau']; ctx.lineWidth = 2; ctx.stroke();
    }
    courbe(bh, COUL['--repere']);
    courbe(mk.courbe, COUL['--ambre']);
    if (pan.survol >= 0) {
      var xs = Math.round(X(pan.survol)) + 0.5;
      ctx.strokeStyle = COUL['--encre-2']; ctx.globalAlpha = 0.6; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(xs, haut); ctx.lineTo(xs, H - bas); ctx.stroke();
      ctx.globalAlpha = 1;
    }
  }

  function majValeurs() {
    var n = etat.n;
    panneaux.forEach(function (pan) {
      var mk = dessin.mk[pan.k];
      pan.b1.textContent = pct(n > 0 ? mk.courbe[n - 1] - 1 : 0);
      pan.b2.textContent = pct(n > 0 ? bhCourbes[pan.k][n - 1] - 1 : 0);
    });
  }

  // ------------------------------------------------------------------ infobulle
  function survoler(pan, ev) {
    if (!pan.geo || !dessin) return;
    var r = pan.cv.getBoundingClientRect(), x = ev.clientX - r.left;
    var i = Math.floor((x - pan.geo.padL) / pan.geo.bw);
    if (i < 0 || i >= pan.geo.nb) { pan.survol = -1; pan.ib.hidden = true; toutSale(); return; }
    pan.survol = i;
    var m = M[pan.k], t = dessin.a + i, mk = dessin.mk[pan.k];
    var ib = pan.ib;
    ib.textContent = '';
    ib.appendChild(el('div', 'ib-date', dateFr(D.dates[t])));
    var dec = m.c[t] < 200 ? 2 : 1;
    [['Ouverture', m.o[t]], ['Haut', m.h[t]], ['Bas', m.l[t]], ['Clôture', m.c[t]]].forEach(function (x2) {
      var l = el('div', 'ib-ligne'); l.appendChild(el('span', null, x2[0])); l.appendChild(el('b', null, nombre(x2[1], dec))); ib.appendChild(l);
    });
    var w = mk.pos[i];
    var lp = el('div', 'ib-ligne'); lp.appendChild(el('span', null, 'Position'));
    lp.appendChild(el('b', null, w === 1 ? '▲ achat' : w === -1 ? '▼ vente' : '— à plat')); ib.appendChild(lp);
    if (i < etat.n) {
      var l1 = el('div', 'ib-ligne'); l1.appendChild(el('span', null, 'Stratégie')); l1.appendChild(el('b', null, pct(mk.courbe[i] - 1))); ib.appendChild(l1);
      var l2 = el('div', 'ib-ligne'); l2.appendChild(el('span', null, 'Acheter et conserver')); l2.appendChild(el('b', null, pct(bhCourbes[pan.k][i] - 1))); ib.appendChild(l2);
    }
    ib.hidden = false;
    var larg = ib.offsetWidth, px = x + 14;
    if (px + larg > r.width - 2) px = Math.max(2, x - 14 - larg);
    ib.style.left = px + 'px';
    ib.style.top = '8px';
    toutSale();
  }

  // ------------------------------------------------------------------ carte 3D
  var carte = { theta: -0.62, phi: 0.62, glisse: false, x: 0, y: 0, sale: true, sc: 0, cx: 0, cy: 0, saut: true };
  function dessinerCarte() {
    var cv = $('carte'), c = preparerCanvas(cv), ctx = c.ctx, W = c.w, H = c.h;
    var p = etat.p, maxAbs = 0.05;
    CEL[p].forEach(function (lg) { lg.forEach(function (x) { maxAbs = Math.max(maxAbs, Math.abs(x.ret)); }); });
    var hU = 1.7 / maxAbs;
    var ct = Math.cos(carte.theta), st = Math.sin(carte.theta), cp = Math.cos(carte.phi), sp = Math.sin(carte.phi);
    var DX = 1.25, DZ = 0.82, HX = 0.33, HZ = 0.27;
    function projU(X, Yw, Z) {
      var x = X * ct - Z * st, z = X * st + Z * ct;
      var yUp = Yw * cp - z * sp, prof = -(z * cp + Yw * sp);
      var f = 1 / (1 + prof * 0.045);
      return [x * f, -yUp * f, prof];
    }
    function wx(k) { return (k - (K - 1) / 2) * DX; }
    function wz(si) { return (si - (S.length - 1) / 2) * DZ; }
    var gx0 = wx(0) - DX / 2, gx1 = wx(K - 1) + DX / 2, gz0 = wz(0) - DZ / 2, gz1 = wz(S.length - 1) + DZ / 2;
    var LZ = 0.75, LX = 1.05;
    // cadrage : boîte englobante du sol, des étiquettes et des barres de la passe, à l'angle courant (lissé)
    var pts = [], mnx = Infinity, mxx = -Infinity, mny = Infinity, mxy = -Infinity;
    [[gx0 - LX, gz0 - LZ], [gx1 + LX, gz0 - LZ], [gx1 + LX, gz1 + LZ], [gx0 - LX, gz1 + LZ]].forEach(function (q) { pts.push(projU(q[0], 0, q[1])); });
    CEL[p].forEach(function (lg, si2) { lg.forEach(function (x, k2) { pts.push(projU(wx(k2), x.ret * hU, wz(si2))); }); });
    pts.forEach(function (q) { mnx = Math.min(mnx, q[0]); mxx = Math.max(mxx, q[0]); mny = Math.min(mny, q[1]); mxy = Math.max(mxy, q[1]); });
    var hautTexte = 20;
    var cible = Math.min((W - 12) / (mxx - mnx), (H - hautTexte - 10) / (mxy - mny));
    var cxC = W / 2 - (mnx + mxx) / 2 * cible, cyC = hautTexte + (H - hautTexte - 4) / 2 - (mny + mxy) / 2 * cible;
    if (!carte.sc || carte.saut) { carte.sc = cible; carte.cx = cxC; carte.cy = cyC; carte.saut = false; }
    else { carte.sc += (cible - carte.sc) * 0.06; carte.cx += (cxC - carte.cx) * 0.06; carte.cy += (cyC - carte.cy) * 0.06; }
    var Sc = carte.sc, cx0 = carte.cx, cy0 = carte.cy;
    function proj(X, Yw, Z) { var u = projU(X, Yw, Z); return [cx0 + u[0] * Sc, cy0 + u[1] * Sc, u[2]]; }
    var boites = [];
    for (var si = 0; si < S.length; si++) for (var k = 0; k < K; k++) {
      if (!remplies[si] || !remplies[si][k]) continue;
      var x = CEL[p][si][k], aucun = x.trades === 0;
      var h = aucun ? 0.03 : x.ret * hU;
      if (Math.abs(h) < 0.03) h = h < 0 ? -0.03 : 0.03;
      var genre = aucun ? 'plat' : x.ret > x.bh ? 'hausse' : 'baisse';
      var ctr = proj(wx(k), h / 2, wz(si));
      boites.push({ si: si, k: k, h: h, genre: genre, prof: ctr[2] });
    }
    boites.sort(function (u, v) { return v.prof - u.prof; });
    function boite(bx) {
      var x0 = wx(bx.k) - HX, x1 = wx(bx.k) + HX, z0 = wz(bx.si) - HZ, z1 = wz(bx.si) + HZ;
      var yb = Math.min(0, bx.h), yt = Math.max(0, bx.h);
      var P8 = [[x0, yb, z0], [x1, yb, z0], [x1, yb, z1], [x0, yb, z1], [x0, yt, z0], [x1, yt, z0], [x1, yt, z1], [x0, yt, z1]].map(function (q) { return proj(q[0], q[1], q[2]); });
      var g = bx.genre;
      var cTop = g === 'plat' ? COUL['--plat'] : COUL['--' + g];
      var cX = g === 'plat' ? COUL['--axe'] : COUL['--' + g + '-ombre'];
      var cZ = g === 'plat' ? COUL['--filet'] : COUL['--' + g + '-ombre-2'];
      var faces = [
        [[4, 5, 6, 7], cTop], [[3, 2, 1, 0], cTop],
        [[0, 1, 5, 4], cZ], [[2, 3, 7, 6], cZ],
        [[1, 2, 6, 5], cX], [[3, 0, 4, 7], cX]
      ];
      faces.forEach(function (f) {
        var q = f[0].map(function (i) { return P8[i]; });
        var aire = 0;
        for (var i = 0; i < 4; i++) { var u = q[i], v = q[(i + 1) % 4]; aire += u[0] * v[1] - v[0] * u[1]; }
        if (aire >= 0) return;
        ctx.beginPath(); ctx.moveTo(q[0][0], q[0][1]);
        for (i = 1; i < 4; i++) ctx.lineTo(q[i][0], q[i][1]);
        ctx.closePath(); ctx.fillStyle = f[1]; ctx.fill();
        ctx.strokeStyle = COUL['--panneau']; ctx.lineWidth = 0.6; ctx.stroke();
      });
      if (derniere && derniere.si === bx.si && derniere.k === bx.k) {
        var tq = [4, 5, 6, 7].map(function (i) { return P8[i]; });
        ctx.beginPath(); ctx.moveTo(tq[0][0], tq[0][1]);
        for (var j = 1; j < 4; j++) ctx.lineTo(tq[j][0], tq[j][1]);
        ctx.closePath(); ctx.strokeStyle = COUL['--ambre']; ctx.lineWidth = 1.6; ctx.stroke();
      }
    }
    // barres négatives (sous le sol), puis le sol, puis les positives
    boites.forEach(function (bx) { if (bx.h < 0) boite(bx); });
    var coins = [proj(gx0, 0, gz0), proj(gx1, 0, gz0), proj(gx1, 0, gz1), proj(gx0, 0, gz1)];
    ctx.beginPath(); ctx.moveTo(coins[0][0], coins[0][1]);
    for (var i = 1; i < 4; i++) ctx.lineTo(coins[i][0], coins[i][1]);
    ctx.closePath();
    ctx.globalAlpha = 0.62; ctx.fillStyle = COUL['--panneau']; ctx.fill(); ctx.globalAlpha = 1;
    ctx.fillStyle = COUL['--sol']; ctx.fill();
    ctx.strokeStyle = COUL['--axe']; ctx.lineWidth = 1; ctx.stroke();
    ctx.strokeStyle = COUL['--filet'];
    for (k = 1; k < K; k++) { var gx = gx0 + k * DX, u1 = proj(gx, 0, gz0), u2 = proj(gx, 0, gz1); ctx.beginPath(); ctx.moveTo(u1[0], u1[1]); ctx.lineTo(u2[0], u2[1]); ctx.stroke(); }
    for (si = 1; si < S.length; si++) { var gz = gz0 + si * DZ, v1 = proj(gx0, 0, gz), v2 = proj(gx1, 0, gz); ctx.beginPath(); ctx.moveTo(v1[0], v1[1]); ctx.lineTo(v2[0], v2[1]); ctx.stroke(); }
    boites.forEach(function (bx) { if (bx.h >= 0) boite(bx); });
    // étiquettes
    police(ctx, 10, '500'); ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillStyle = COUL['--encre-2'];
    for (k = 0; k < K; k++) {
      var e1 = proj(wx(k), 0, gz1 + LZ * 0.85), e2 = proj(wx(k), 0, gz0 - LZ * 0.85);
      var e = e1[2] < e2[2] ? e1 : e2;
      ctx.fillText(COURT[M[k].id] || M[k].id, e[0], e[1]);
    }
    police(ctx, 9.5); ctx.fillStyle = COUL['--discret'];
    for (si = 0; si < S.length; si++) {
      var f1 = proj(gx0 - LX * 0.62, 0, wz(si)), f2 = proj(gx1 + LX * 0.62, 0, wz(si));
      var f = f1[2] < f2[2] ? f1 : f2;
      ctx.fillText(COURT_S[S[si]], f[0], f[1]);
    }
    police(ctx, 9.5); ctx.textAlign = 'left'; ctx.textBaseline = 'top'; ctx.fillStyle = COUL['--discret'];
    ctx.fillText('Passe ' + (p + 1) + ' · échelle : la plus grande barre vaut ' + nombre(maxAbs * 100, 0) + NBSP + '%', 6, 6);
  }
  function brancherCarte() {
    var cv = $('carte');
    cv.addEventListener('pointerdown', function (e) { carte.glisse = true; carte.x = e.clientX; carte.y = e.clientY; try { cv.setPointerCapture(e.pointerId); } catch (x) { /* rien */ } });
    cv.addEventListener('pointermove', function (e) {
      if (!carte.glisse) return;
      carte.theta += (e.clientX - carte.x) * 0.01;
      carte.phi = Math.max(0.22, Math.min(1.15, carte.phi + (e.clientY - carte.y) * 0.006));
      carte.x = e.clientX; carte.y = e.clientY; carte.sale = true;
    });
    function fin() { carte.glisse = false; }
    cv.addEventListener('pointerup', fin); cv.addEventListener('pointercancel', fin);
  }

  // ------------------------------------------------------------------ tableau, classement, journal
  function cellule(si, k) { return document.querySelector('#table-passe td[data-s="' + si + '"][data-k="' + k + '"]'); }
  function ecrireCellule(td, ret, genre) {
    td.className = 'cel ' + genre + (td.dataset.k === String(K) ? ' col-moy' : '');
    td.textContent = '';
    if (genre === 'aucun') { td.textContent = 'aucun trade'; return; }
    if (genre !== 'bh') td.appendChild(el('span', 'sym', genre === 'bat' ? '▲' : '▼'));
    td.appendChild(el('span', 'val', pct(ret)));
  }
  function remplirLigneBh() {
    var tds = $('ligne-bh').querySelectorAll('td'), s = 0;
    BH.passes[etat.p].forEach(function (x, k) { ecrireCellule(tds[k], x.ret, 'bh'); s += x.ret; });
    ecrireCellule(tds[K], s / K, 'bh');
  }
  function viderTable() {
    for (var si = 0; si < S.length; si++) for (var k = 0; k <= K; k++) {
      var td = cellule(si, k); td.className = 'cel vide' + (k === K ? ' col-moy' : ''); td.textContent = '·';
    }
    remplies = S.map(function () { return [false, false, false, false]; });
    derniere = null;
  }
  function marquerLigneCourante() {
    document.querySelectorAll('#table-passe tbody tr[data-s]').forEach(function (tr) {
      tr.classList.toggle('ligne-courante', Number(tr.dataset.s) === etat.s && etat.phase !== 'finPasse');
    });
  }

  function remplirCellule() {
    var si = etat.s, k = etat.cellules, x = CEL[etat.p][si][k];
    var genre = x.trades === 0 ? 'aucun' : x.ret > x.bh ? 'bat' : 'perd';
    document.querySelectorAll('#table-passe .neuf').forEach(function (e) { e.classList.remove('neuf'); });
    var td = cellule(si, k);
    ecrireCellule(td, x.ret, genre);
    td.classList.add('neuf');
    remplies[si][k] = true;
    derniere = { si: si, k: k };
    etat.cellules++;
    var cu = cumul[si];
    cu.somme += x.ret; cu.n++;
    if (genre !== 'aucun') { cu.joue++; cycleJoue++; if (genre === 'bat') { cu.bat++; cycleBat++; } }
    var txt = 'Passe ' + (etat.p + 1) + ' · ' + NOMS[S[si]] + ' ' + SUR[M[k].id] + ' : ';
    if (genre === 'aucun') journal(txt + 'aucun trade de toute l’année. Ni gagné ni perdu.', null);
    else journal(txt + pct(x.ret) + ' contre ' + pct(x.bh) + ' pour acheter et conserver.', genre === 'bat' ? 'gagne' : 'perdu');
    if (etat.cellules === K) {
      var sm = 0, sb = 0, nj = 0;
      CEL[etat.p][si].forEach(function (c) { sm += c.ret; sb += c.bh; if (c.trades > 0) nj++; });
      var tdm = cellule(si, K);
      ecrireCellule(tdm, sm / K, nj === 0 ? 'aucun' : sm > sb ? 'bat' : 'perd');
    }
    majClassement();
    carte.sale = true;
  }

  function majClassement() {
    var ids = ['bh'].concat(S);
    var info = {};
    ids.forEach(function (id, idx) {
      var c = id === 'bh' ? cumulBh : cumul[idx - 1];
      info[id] = { moy: c.n ? c.somme / c.n : null, c: c };
    });
    var ordre = ids.slice().sort(function (u, v) {
      var a = info[u].moy, b = info[v].moy;
      if (a === null && b === null) return ids.indexOf(u) - ids.indexOf(v);
      if (a === null) return 1;
      if (b === null) return -1;
      return b - a;
    });
    var ol = $('classement'), avant = {};
    ids.forEach(function (id) { avant[id] = lignesClassement[id].getBoundingClientRect().top; });
    ordre.forEach(function (id, r) {
      var li = lignesClassement[id], inf = info[id];
      li.children[0].textContent = String(r + 1);
      li.children[2].textContent = inf.moy === null ? '—' : pct(inf.moy);
      var bat = li.children[3];
      bat.textContent = '';
      if (id === 'bh') bat.textContent = inf.c.n ? 'repère · ' + inf.c.n + ' cellules' : 'repère';
      else if (inf.c.n) {
        bat.appendChild(document.createTextNode('bat le marché '));
        bat.appendChild(el('b', null, String(inf.c.bat)));
        bat.appendChild(document.createTextNode(' fois sur '));
        bat.appendChild(el('b', null, String(inf.c.joue)));
        if (inf.c.n > inf.c.joue) bat.appendChild(document.createTextNode(' · ' + (inf.c.n - inf.c.joue) + ' sans trade'));
      } else bat.textContent = 'pas encore testée';
      ol.appendChild(li);
    });
    if (!reduit && typeof Element.prototype.animate === 'function') {
      ids.forEach(function (id) {
        var li = lignesClassement[id], dy = avant[id] - li.getBoundingClientRect().top;
        if (Math.abs(dy) > 1) li.animate([{ transform: 'translateY(' + dy + 'px)' }, { transform: 'none' }], { duration: 480, easing: 'cubic-bezier(.2,.7,.2,1)' });
      });
    }
    $('note-classement').textContent = 'Passes 1 à ' + (etat.p + 1) + ' du cycle';
  }

  function journal(texte, genre, bilan) {
    var ol = $('journal'), li = el('li', bilan ? 'bilan' : '');
    li.appendChild(el('span', 'journal-code', 'P' + String(etat.p + 1).padStart(2, '0') + (bilan ? ' ··' : ' S' + (etat.s + 1))));
    var t = el('span', null, texte);
    if (genre) {
      t.appendChild(document.createTextNode(' '));
      t.appendChild(el('span', genre, genre === 'gagne' ? '▲ Gagné.' : '▼ Perdu.'));
    }
    li.appendChild(t);
    ol.insertBefore(li, ol.firstChild);
    while (ol.children.length > 60) ol.removeChild(ol.lastChild);
  }

  // ------------------------------------------------------------------ en-tête et légende
  function majEntete() {
    var pp = P[etat.p];
    $('etat-passe').textContent = 'Passe ' + (etat.p + 1) + ' sur ' + NP + ' · ' + dateFr(pp.debut) + ' → ' + dateFr(pp.fin);
    var es = $('etat-strat'); es.textContent = '';
    if (etat.phase === 'finPasse') es.textContent = 'Passe terminée · ' + (etat.p + 1 < NP ? 'la suivante remonte d’un an' : 'fin du cycle');
    else {
      es.appendChild(document.createTextNode('Stratégie ' + (etat.s + 1) + ' sur ' + S.length + ' : '));
      es.appendChild(el('b', null, NOMS[S[etat.s]]));
    }
    majSeance();
    $('note-passe').textContent = dateFr(pp.debut) + ' → ' + dateFr(pp.fin);
  }
  function majSeance() {
    var nb = dessin.nb, n = etat.n;
    $('etat-seance').textContent = n === 0 ? 'Séance — / ' + nb : 'Séance ' + n + ' / ' + nb + ' · ' + dateFr(D.dates[dessin.a + n - 1]);
    $('progres').style.transform = 'scaleX(' + (n / nb) + ')';
  }
  function majLegende() {
    var lg = $('legende'); lg.textContent = '';
    function cle(type, c, txt) {
      var s = el('span');
      var k = el('span', type === 'bande' ? 'cle-bande' : 'cle-ligne');
      if (type === 'bande') { k.style.borderColor = 'var(' + c + ')'; k.style.background = 'var(' + c + '-voile, transparent)'; } else k.style.background = 'var(' + c + ')';
      s.appendChild(k); s.appendChild(document.createTextNode(txt)); lg.appendChild(s);
    }
    DESSIN[S[etat.s]].legende.forEach(function (x) { cle(x[0], x[1], x[2]); });
    function sym(txt, cls, label) { var s = el('span'); s.appendChild(el('span', 'cle-sym ' + (cls || ''), txt)); s.appendChild(document.createTextNode(label)); lg.appendChild(s); }
    sym('▲', 'cle-bat', 'achat'); sym('▼', 'cle-perd', 'vente'); sym('✕', '', 'sortie');
    cle('ligne', '--ambre', 'Stratégie'); cle('ligne', '--repere', 'Acheter et conserver');
    $('regle').textContent = NOMS[S[etat.s]] + ' · ' + REGLE[S[etat.s]] + ' Barre « pos. » : position tenue (▲ achat, ▼ vente, gris à plat).';
    panneaux.forEach(function (pan) { pan.gs.textContent = 'Stratégie testée : ' + NOMS[S[etat.s]]; });
  }

  // ------------------------------------------------------------------ déroulé
  function demarrerPasse(p) {
    etat.p = p;
    bhCourbes = M.map(function (m, k) { return BT.backtest(UN, m.o, m.c, m.r, P[p].a, P[p].b, FR[k])[2]; });
    viderTable();
    remplirLigneBh();
    carte.saut = true;
    BH.passes[p].forEach(function (x) { cumulBh.somme += x.ret; cumulBh.n++; });
    journal('Passe ' + (p + 1) + ' : je rejoue ' + dateFr(P[p].debut) + ' → ' + dateFr(P[p].fin) + ' avec les ' + S.length + ' stratégies.', null, true);
    demarrerStrategie(0);
    majClassement();
  }
  function demarrerStrategie(si) {
    etat.s = si; etat.cellules = 0; etat.nf = 0; etat.n = 0; etat.tPhase = 0; etat.phase = 'balayage';
    dessin = preparer(etat.p, si);
    if (reduit) { etat.nf = etat.n = dessin.nb; while (etat.cellules < K) remplirCellule(); etat.phase = 'pause'; }
    majLegende(); majEntete(); majValeurs(); marquerLigneCourante();
    panneaux.forEach(function (pan) { pan.survol = -1; pan.ib.hidden = true; });
    toutSale(); carte.sale = true;
  }
  function finirStrategie() {
    etat.nf = etat.n = dessin.nb;
    while (etat.cellules < K) remplirCellule();
    majValeurs(); majSeance(); toutSale();
  }
  function suivante() {
    if (etat.s < S.length - 1) demarrerStrategie(etat.s + 1);
    else finDePasse();
  }
  function finDePasse() {
    etat.phase = 'finPasse'; etat.tPhase = 0;
    var bat = 0, joue = 0, aucun = 0;
    CEL[etat.p].forEach(function (lg) { lg.forEach(function (c) { if (c.trades > 0) { joue++; if (c.ret > c.bh) bat++; } else aucun++; }); });
    cyclePasses++;
    journal('Passe ' + (etat.p + 1) + ' terminée : ' + bat + ' cellules sur ' + joue + ' battent le marché' + (aucun ? ' (' + aucun + ' sans trade, non comptées).' : '.'), null, true);
    majEntete(); marquerLigneCourante();
  }
  function passeSuivante() {
    if (etat.p + 1 < NP) demarrerPasse(etat.p + 1);
    else {
      journal('Cycle terminé : sur les ' + NP + ' passes, ' + cycleBat + ' cellules sur ' + cycleJoue + ' battent le marché. Je recommence à la passe 1.', null, true);
      viderCumul();
      demarrerPasse(0);
    }
  }
  function finirPasseInterne() {
    if (etat.phase === 'finPasse') return;
    finirStrategie();
    while (etat.s < S.length - 1) { demarrerStrategie(etat.s + 1); finirStrategie(); }
    finDePasse();
  }

  function avancer(dt) {
    var garde = 0;
    while (dt > 0 && garde++ < 200) {
      var nb = dessin.nb;
      if (etat.phase === 'balayage') {
        var pasParMs = nb / DUREE.balayage, reste = (nb - etat.nf) / pasParMs;
        if (dt >= reste) { dt -= reste; etat.nf = nb; etat.phase = 'cellules'; etat.tPhase = 0; }
        else { etat.nf += dt * pasParMs; dt = 0; }
        var n = Math.floor(etat.nf);
        if (n !== etat.n) { etat.n = n; majValeurs(); majSeance(); toutSale(); }
      } else if (etat.phase === 'cellules') {
        var r = DUREE.cellule - etat.tPhase;
        if (dt >= r) { dt -= r; etat.tPhase = 0; remplirCellule(); if (etat.cellules >= K) etat.phase = 'pause'; }
        else { etat.tPhase += dt; dt = 0; }
      } else if (etat.phase === 'pause') {
        var rp = (reduit ? DUREE.pauseReduite : DUREE.pause) - etat.tPhase;
        if (dt >= rp) { dt -= rp; etat.tPhase = 0; suivante(); }
        else { etat.tPhase += dt; dt = 0; }
      } else if (etat.phase === 'finPasse') {
        var rf = DUREE.finPasse - etat.tPhase;
        if (dt >= rf) { dt -= rf; etat.tPhase = 0; passeSuivante(); }
        else { etat.tPhase += dt; dt = 0; }
      }
    }
  }

  // ------------------------------------------------------------------ boucle d'images
  var graphesSales = true;
  function toutSale() { graphesSales = true; carte.sale = true; }
  function dessinerTout() {
    panneaux.forEach(function (pan) { dessinerPrix(pan); dessinerCourse(pan); });
    graphesSales = false;
  }
  var dernierTemps = null;
  function image(now) {
    var dt = dernierTemps === null ? 0 : Math.min(now - dernierTemps, 100);
    dernierTemps = now;
    if (etat.lecture) avancer(dt * etat.vitesse);
    if (!reduit && !carte.glisse) { carte.theta += dt * 0.00016; carte.sale = true; }
    if (graphesSales) dessinerTout();
    if (carte.sale) { dessinerCarte(); carte.sale = false; }
    requestAnimationFrame(image);
  }

  // ------------------------------------------------------------------ commandes
  function majLecture() {
    var b = $('btn-lecture');
    b.textContent = etat.lecture ? 'Pause' : 'Lecture';
    b.setAttribute('aria-pressed', etat.lecture ? 'true' : 'false');
  }
  function brancherCommandes() {
    $('btn-lecture').addEventListener('click', function () { etat.lecture = !etat.lecture; majLecture(); });
    document.querySelectorAll('.btn-vitesse').forEach(function (b) {
      b.addEventListener('click', function () {
        etat.vitesse = Number(b.dataset.vitesse);
        document.querySelectorAll('.btn-vitesse').forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
      });
    });
    $('btn-strategie-suivante').addEventListener('click', function () {
      if (etat.phase === 'finPasse') passeSuivante();
      else { finirStrategie(); suivante(); }
      toutSale();
    });
    $('btn-passe-suivante').addEventListener('click', function () {
      finirPasseInterne(); passeSuivante(); toutSale();
    });
  }

  // ------------------------------------------------------------------ démarrage
  function demarrer() {
    $('marque-sous').textContent = S.length + ' stratégies · ' + K + ' marchés de futures · ' + NP + ' passes d’un an · barres quotidiennes réelles';
    construireGraphes(); construireTablePasse(); construireClassement();
    construireVerdict(); construireBots(); construireMethode();
    lireCouleurs();
    viderCumul();
    demarrerPasse(0);
    majLecture();
    brancherCommandes(); brancherCarte();
    dessinerTout(); dessinerCarte();
    window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', lireCouleurs);
    new MutationObserver(lireCouleurs).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'class', 'style'] });
    if (typeof ResizeObserver === 'function') new ResizeObserver(function () { toutSale(); }).observe(document.body);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(function () { lireCouleurs(); });
    requestAnimationFrame(image);
    window.__terminal = {
      finirPasse: function () { finirPasseInterne(); etat.lecture = false; majLecture(); dessinerTout(); dessinerCarte(); return etat.p; },
      etat: function () { return { passe: etat.p, strategie: etat.s, phase: etat.phase, barre: etat.n, lecture: etat.lecture }; }
    };
  }
  demarrer();
})();
