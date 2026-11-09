// Demo : un faux relais qui rejoue les vraies minutes du 28 octobre 2026 ; la page du terminal ne change pas.
const DEMO = JSON.parse(document.getElementById("demo-donnees").textContent);
const DM = { t: DEMO.debutUtc + DEMO.depart * 60000, vit: 60, pause: false, dernier: performance.now(), saut: 0 };
const DM_FIN = DEMO.debutUtc + 1380 * 60000 - 1000;
function dmAvancer() { const n = performance.now(); if (!DM.pause) DM.t = Math.min(DM.t + (n - DM.dernier) * DM.vit, DM_FIN); DM.dernier = n; }
setInterval(dmAvancer, 200);
const dmI = () => Math.floor((DM.t - DEMO.debutUtc) / 60000);
const DM_B = DEMO.marches.map(m => { const B = new Array(1380).fill(null); m.barres.forEach(b => { B[b[0]] = b.slice(1); }); return { m, B }; });
const dmRep = o => ({ ok: true, status: 200, json: async () => o });
const dmNy = d => { const f = new Intl.DateTimeFormat("sv-SE", { timeZone: "America/New_York", hourCycle: "h23", year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", second: "2-digit" }); return f.format(d); };
window.fetch = async (u) => {
  dmAvancer(); const k = String(u), i = dmI();
  if (k.startsWith("/live/barres"))
    return dmRep({ utc: new Date(DM.t).toISOString(), ny: dmNy(new Date(DM.t)), marches: DM_B.map(({ m, B }) => ({ nom: m.nom, symbole: m.symbole, jour: DEMO.jour,
      barres: B.map((b, j) => b && j < i ? [j, ...b] : null).filter(Boolean), cloturePrec: m.cloturePrec, jourPrec: DEMO.jourPrec, plageMoyenne: m.plageMoyenne,
      seances: m.seances, volMoyen: m.volMoyen })) });
  if (k.startsWith("/live/etat")) {
    const nouv = DEMO.nouvelles.filter(x => Date.parse(x.date) <= DM.t);
    const cot = DEMO.cotations.map(c => { const p = c.pts.filter(x => x[0] * 1000 <= DM.t); if (!p.length) return null; const s5 = p.filter((x, j) => j % 5 === 0 || j === p.length - 1);
      return { symbole: c.symbole, nom: c.nom, dernier: p[p.length - 1][1], veille: c.veille, haut: Math.max(...p.map(x => x[1])), bas: Math.min(...p.map(x => x[1])), heure: p[p.length - 1][0],
               serie: s5.map(x => x[1]), temps: s5.map(x => x[0]) }; }).filter(Boolean);
    const marches = DM_B.map(({ m, B }) => { let d = null; for (let j = Math.min(i - 1, 1379); j >= 0; j--) if (B[j]) { d = B[j][3]; break; }
      return { nom: m.nom, jour: DEMO.jour, i, barre: null, prec: i >= 1 ? B[i - 1] : null, dernier: d, age: d == null ? null : (DM.t - (DEMO.debutUtc + i * 60000)) / 1000 }; });
    return dmRep({ utc: new Date(DM.t).toISOString(), ny: dmNy(new Date(DM.t)), marches, compte: null, journaux: [],
      versions: { n: nouv.length + 1000 * DM.saut, c: 1 + DM.saut, q: i + 100000 * DM.saut, g: DM.saut },
      nouvelles: nouv, sources: [{ source: "démo (communiqué de la Fed seulement)", ok: true, articles: nouv.length }],
      calendrier: DEMO.calendrier, etatCalendrier: { ok: true }, cotations: cot, etatCotations: { ok: true }, vixVeille: DEMO.vixVeille, gros: [] });
  }
  return { ok: false, status: 404, json: async () => ({}) };
};
const DM_ETAPES = [
  [0, 840, "La nuit Globex (18 h - 8 h à New York)", ["Passe le graphique sur « Depuis 18 h » pour voir la nuit.", "Regarde d'où part le NQ par rapport à la clôture de la veille (ligne pointillée grise).",
    "Volume de nuit faible = marché calme ; c'est normal, l'Europe et l'Asie tradent moins le Nasdaq."]],
  [840, 930, "Avant l'ouverture (8 h - 9 h 30)", ["Calendrier : la Fed annonce sa décision à 14 h. Les jours de la Fed, ton bot ne prend pas de zone.",
    "Volatilité : le filtre VIX dit si la zone serait autorisée aujourd'hui (clôtures d'hier).", "Le NQ a-t-il beaucoup bougé pendant la nuit ? Une grosse nuit prépare souvent une ouverture nerveuse."]],
  [930, 960, "L'ouverture (9 h 30 - 10 h)", ["Volume relatif : au-dessus de 100 %, le marché est plus actif que d'habitude à cette heure.", "Le VWAP (ligne cyan) se forme : le prix s'installe-t-il au-dessus ou en dessous ?",
    "Confirmation : l'ES et le Russell vont-ils dans le même sens que le NQ ?", "Delta : les achats au marché dominent-ils les ventes, ou l'inverse ?"]],
  [960, 1170, "Le milieu de séance (10 h - 13 h 30)", ["Suis la lecture du marché ligne par ligne : chaque point vert, ambre ou rouge te dit où regarder.",
    "Un mouvement de plus de 2 ATR en 30 minutes est un vrai mouvement ; en dessous, c'est du bruit.", "Vers midi, le volume retombe souvent : c'est normal, ce n'est pas un signal."]],
  [1170, 1200, "Avant la Fed (13 h 30 - 14 h)", ["L'annonce approche : la ligne « Annonce » passe au rouge à moins de 30 minutes.", "C'est le moment de ne rien ouvrir. Regarde l'ATR : c'est l'ordre de grandeur d'une bougie de 5 minutes en ce moment.",
    "Le volume baisse souvent juste avant : tout le monde attend."]],
  [1200, 1230, "La décision de la Fed (14 h - 14 h 30)", ["Le communiqué arrive dans les nouvelles et un trait ambre marque 14 h sur le graphique.", "Regarde les barres de volume passer au-dessus de la ligne ambre, et le VIX réagir.",
    "Dans quel sens le prix sort-il ? Et revient-il vers le VWAP ou s'en éloigne-t-il ?", "La conférence de presse suit en général : le marché peut changer d'avis."]],
  [1230, 1320, "Après la Fed, jusqu'à la clôture (14 h 30 - 16 h)", ["Le mouvement tient-il ? Prix du même côté du VWAP, volume encore haut, ES qui confirme.",
    "Compare la plage du jour à la plage moyenne (panneau Volatilité) : une journée de Fed dépasse souvent la moyenne.", "À 16 h, la séance US se termine."]],
  [1320, 1381, "Après 16 h", ["Fais le bilan : variation du jour, plage face à la moyenne, delta du jour.", "À 17 h le marché fait sa pause d'une heure : toute position doit être fermée chez Bulenox."]]];
let dmEtape = -1;
function dmGuide() {
  const i = dmI(), k = DM_ETAPES.findIndex(e => i >= e[0] && i < e[1]);
  const d = new Date(DM.t), ny = dmNy(d).slice(11, 16), pa = new Intl.DateTimeFormat("fr-FR", { timeZone: "Europe/Paris", hour: "2-digit", minute: "2-digit" }).format(d);
  document.getElementById("dm-heure").textContent = `${ny} New York · ${pa} Paris · ${DM.pause ? "en pause" : "×" + DM.vit}`;
  if (k === dmEtape || k < 0) return; dmEtape = k;
  document.getElementById("dg-titre").textContent = DM_ETAPES[k][2]; document.getElementById("dg-etape").textContent = `étape ${k + 1} sur ${DM_ETAPES.length}`;
  const ul = document.getElementById("dg-liste"); ul.textContent = ""; DM_ETAPES[k][3].forEach(t => { const li = document.createElement("li"); li.textContent = t; ul.appendChild(li); });
}
document.addEventListener("DOMContentLoaded", () => {
  const b = document.getElementById("dm-lecture");
  b.onclick = () => { dmAvancer(); DM.pause = !DM.pause; b.textContent = DM.pause ? "Lecture" : "Pause"; b.setAttribute("aria-pressed", DM.pause); dmGuide(); };
  document.querySelectorAll("[data-vit]").forEach(x => x.onclick = () => { dmAvancer(); DM.vit = +x.dataset.vit; document.querySelectorAll("[data-vit]").forEach(y => y.setAttribute("aria-pressed", y === x)); dmGuide(); });
  document.querySelectorAll("[data-saut]").forEach(x => x.onclick = () => { DM.t = DEMO.debutUtc + (+x.dataset.saut) * 60000; DM.dernier = performance.now(); DM.saut++;
    if (typeof chargerBarres === "function") chargerBarres().then(() => interroger()).then(() => { rendreNouvelles(); rendre(true); }).catch(() => {}); dmGuide(); });
  setInterval(dmGuide, 500); dmGuide();
});
