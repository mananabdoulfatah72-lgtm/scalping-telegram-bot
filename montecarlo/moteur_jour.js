/* Monte Carlo v2 : moteur journalier du bot sur un compte Bulenox (port de moteur_jour.py, ligne pour ligne).
   Chaque séance est lue dans les tables exactes (tables.py) : 12 combinaisons par séance
   k = (veut * 2 + zi) * 3 + plafond, avec gain, pire point (relatif au départ) et drapeaux (bit 0 : au moins un trade,
   bit 1 : position voulue pour la nuit suivante).
   parcoursJour(lig, G, P, D, ci, R, ret, suivi) renvoie [issue, seances du challenge, Master perdu, retraits,
   recu, seance du 1er retrait, fin], comme moteur4._parcours4. `suivi` (facultatif) recoit le solde séance par séance
   et des mesures de risque ; il ne change rien au calcul. */
function parcoursJour(lig, G, P, D, ci, R, ret, suivi) {
  const NC = 3, NK = 12, fin = lig.length;
  let cash = 0, veut = 0, picEod = 0, veille = 0, plancher = -R.e_perte, jours = 0, issue = 0, nCh = 0, s = 0;
  let a = 0, zi = 0, k = 0;
  const S = suivi || null;
  while (s < fin) {
    a = lig[s];
    zi = R.c_mnq > 0 && cash - plancher < R.c_mnq ? 1 : 0;
    k = a * NK + (veut * 2 + zi) * NC;
    if (S) S.pas(s, cash, plancher, P[k], 1);
    if (plancher - cash >= P[k]) { if (S) S.fin(s, plancher, 1); return [-1, s + 1, 0, 0, 0, -1, s + 1]; }
    cash += G[k];
    veut = D[k] >> 1;
    jours += 1;
    if (cash > picEod) picEod = cash;
    plancher = Math.min(picEod - R.e_perte, R.e_bloc);
    if (S) S.apres(s, cash, plancher, picEod, 1);
    s += 1;
    if (cash >= R.e_obj && jours >= 1) { issue = 1; nCh = s; break; }
  }
  if (issue !== 1) return [0, fin, 0, 0, 0, -1, fin];
  cash = 0; picEod = 0; veille = 0;
  let base = 0, meilleur = -1e18, qual = 0, n = 0, recu = 0, premier = -1, g = 0, gainC = 0, x = 0;
  plancher = -R.f_perte;
  while (s < fin) {
    a = lig[s];
    zi = R.c_mnq > 0 && cash - plancher < R.c_mnq ? 1 : 0;
    k = a * NK + (veut * 2 + zi) * NC + ci;
    if (S) S.pas(s, cash, plancher, P[k], 2);
    if (plancher - cash >= P[k]) { if (S) S.fin(s, plancher, 2); return [1, nCh, 1, n, recu, premier, s + 1]; }
    cash += G[k];
    veut = D[k] >> 1;
    g = cash - veille;
    veille = cash;
    if (D[k] & 1) qual += 1;
    if (g > meilleur) meilleur = g;
    if (cash > picEod) picEod = cash;
    plancher = Math.min(picEod - R.f_perte, R.f_bloc);
    s += 1;
    gainC = cash - base;
    if (qual >= R.f_jours && gainC > 0 && (R.f_regul === 0 || meilleur <= R.f_regul * gainC)) {
      x = Math.min(R.f_plaf, cash - R.f_reserve);
      if (x >= R.f_min) {
        cash -= x;
        veille = cash;
        recu += x;
        n += 1;
        ret[s - 1] = x;
        if (premier < 0) premier = s;
        base = cash; meilleur = -1e18; qual = 0;
        if (R.f_max > 0 && n >= R.f_max) { if (S) S.apres(s - 1, cash, plancher, picEod, 2); return [1, nCh, 0, n, recu, premier, s]; }
      }
    }
    if (S) S.apres(s - 1, cash, plancher, picEod, 2);
  }
  return [1, nCh, 0, n, recu, premier, fin];
}
if (typeof module !== "undefined") module.exports = {parcoursJour};
