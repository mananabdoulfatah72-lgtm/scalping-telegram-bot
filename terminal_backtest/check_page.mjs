// Ouvre terminal.html avec Playwright (bureau 1440 x 900 et téléphone 400 x 800, thème sombre puis clair)
// et fait les contrôles du § 7 de SPEC.md. Usage : node check_page.mjs   -> code 0 seulement si tout passe.
import { readFileSync, mkdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { createRequire } from 'node:module';
import { execSync } from 'node:child_process';

// Playwright est installé globalement : import normal, sinon depuis le dossier global de npm.
async function chargerPlaywright() {
  try { return await import('playwright'); } catch (e) {
    const require = createRequire(import.meta.url);
    try { return require('playwright'); } catch (e2) {
      const racine = execSync('npm root -g', { encoding: 'utf8' }).trim();
      return require(join(racine, 'playwright'));
    }
  }
}
const { chromium } = await chargerPlaywright();

const ICI = dirname(fileURLToPath(import.meta.url));
const X = JSON.parse(readFileSync(join(ICI, 'expected.json'), 'utf8'));
const corps = readFileSync(join(ICI, 'terminal.html'), 'utf8');
const html = '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, ' +
  'initial-scale=1, viewport-fit=cover"></head><body>' + corps + '</body></html>';
mkdirSync(join(ICI, 'captures'), { recursive: true });

// même format que la page : virgule, signe toujours affiché (vrai moins U+2212), espace insécable avant « % »
const MOINS = '−';
const grouper = s => s.replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
function nombre(x, dec) { const s = Math.abs(x).toFixed(dec), p = s.split('.'); return grouper(p[0]) + (p[1] ? ',' + p[1] : ''); }
const signe = (x, dec) => (x < 0 ? MOINS : '+') + nombre(x, dec);
const pct = x => signe(x * 100, 1) + ' %';
const norm = s => s.replace(/\s+/g, ' ').trim();
const estPolice = u => /fonts\.(googleapis|gstatic)\.com/.test(u || '');

const echecs = [];
let verifs = 0;
function verifier(ok, msg) { verifs++; if (!ok) echecs.push(msg); }

const CONFIGS = [
  { nom: 'bureau-sombre', width: 1440, height: 900, colorScheme: 'dark' },
  { nom: 'bureau-clair', width: 1440, height: 900, colorScheme: 'light' },
  { nom: 'telephone-sombre', width: 400, height: 800, colorScheme: 'dark' },
  { nom: 'telephone-clair', width: 400, height: 800, colorScheme: 'light' },
];

const navigateur = await chromium.launch();
for (const cf of CONFIGS) {
  const ctx = await navigateur.newContext({ viewport: { width: cf.width, height: cf.height }, colorScheme: cf.colorScheme, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const messages = [];
  page.on('console', m => {
    if (m.type() !== 'error' && m.type() !== 'warning') return;
    const loc = m.location() && m.location().url;
    if (estPolice(loc) || estPolice(m.text())) return;
    messages.push(`${m.type()} : ${m.text()}`);
  });
  page.on('pageerror', e => messages.push('exception : ' + e.message));
  page.on('requestfailed', r => { if (!estPolice(r.url())) messages.push('requête refusée : ' + r.url()); });
  page.on('request', r => {
    const u = r.url();
    if (!u.startsWith('data:') && !u.startsWith('about:') && !estPolice(u)) messages.push('requête réseau inattendue : ' + u);
  });

  await page.setContent(html, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__terminal !== undefined, null, { timeout: 15000 });
  await page.waitForTimeout(400);
  const t = `[${cf.nom}]`;

  // première image : ligne « acheter et conserver » remplie, sections fixes remplies
  const premiere = await page.evaluate(() => ({
    bh: [...document.querySelectorAll('#ligne-bh td')].map(td => td.textContent.trim()),
    verdict: document.querySelectorAll('#table-verdict tbody tr').length,
    bots: document.querySelectorAll('#table-bots tbody tr').length,
    methode: document.querySelectorAll('#methode li').length,
  }));
  verifier(premiere.bh.length === 5 && premiere.bh.every(x => /%/.test(x)), `${t} ligne « acheter et conserver » non remplie au chargement`);
  verifier(premiere.verdict === 8 && premiere.bots > 0 && premiere.methode > 0, `${t} sections fixes incomplètes au chargement`);

  // 3. à 1440 px, les 4 graphiques sur une ligne
  if (cf.width >= 1100) {
    const tops = await page.$$eval('.graphe', els => els.map(e => Math.round(e.getBoundingClientRect().top)));
    verifier(tops.length === 4 && tops.every(x => x === tops[0]), `${t} les 4 graphiques ne sont pas sur une même ligne (${tops})`);
  }

  // 4. toute la passe 1
  await page.evaluate(() => window.__terminal.finirPasse());
  await page.waitForTimeout(700);
  const cel = await page.evaluate(() => [...document.querySelectorAll('#table-passe td[data-s]')]
    .filter(td => Number(td.dataset.k) < 4).map(td => ({ s: +td.dataset.s, k: +td.dataset.k, txt: td.textContent, cls: td.className })));
  verifier(cel.length === 28, `${t} ${cel.length} cellules au lieu de 28`);
  let comparees = 0;
  for (const c of cel) {
    const x = X.cellules.demande[0][c.s][c.k];
    const attendu = x.trades === 0 ? 'aucun trade' : pct(x.ret);
    const lu = x.trades === 0 ? norm(c.txt) : norm(c.txt).replace(/^[▲▼]\s*/, '');
    comparees++;
    verifier(lu === norm(attendu), `${t} cellule ${c.s},${c.k} : attendu « ${attendu} », lu « ${c.txt} »`);
    const genre = x.trades === 0 ? 'aucun' : x.ret > x.bh ? 'bat' : 'perd';
    verifier(c.cls.split(' ').includes(genre), `${t} cellule ${c.s},${c.k} : classe ${c.cls}, attendu ${genre}`);
    if (genre === 'bat') verifier(c.txt.includes('▲'), `${t} cellule ${c.s},${c.k} sans ▲`);
    if (genre === 'perd') verifier(c.txt.includes('▼'), `${t} cellule ${c.s},${c.k} sans ▼`);
  }
  const nClassement = await page.$$eval('#classement li', l => l.length);
  verifier(nClassement === 8, `${t} classement : ${nClassement} lignes au lieu de 8`);

  // 5. verdict
  const verdict = await page.evaluate(() => [...document.querySelectorAll('#table-verdict tbody tr')].map(tr => ({
    id: tr.dataset.id,
    niveau: tr.querySelector('.pastille') && tr.querySelector('.pastille').dataset.niveau,
    cagr: [...tr.querySelectorAll('.v-cagr')].map(e => e.textContent),
    talpha: [...tr.querySelectorAll('.v-talpha')].map(e => e.textContent),
  })));
  verifier(verdict.length === 8, `${t} verdict : ${verdict.length} lignes au lieu de 8`);
  verdict.forEach((v, i) => {
    const lg = i === 0 ? X.acheter_conserver.demande.long : X.long.demande[i - 1];
    lg.forEach((x, k) => {
      comparees++;
      verifier(norm(v.cagr[k] || '') === norm(pct(x.cagr)), `${t} verdict ${v.id} marché ${k} : cagr « ${v.cagr[k]} » au lieu de « ${pct(x.cagr)} »`);
      if (i > 0) {
        comparees++;
        verifier(norm(v.talpha[k] || '') === norm('t ' + signe(x.t_alpha, 2)), `${t} verdict ${v.id} marché ${k} : t_alpha « ${v.talpha[k]} »`);
      }
    });
    if (i === 0) verifier(v.niveau === 'repere', `${t} verdict : la ligne repère porte une pastille`);
    else {
      const n2 = lg.filter(x => x.t_alpha >= 2).length;
      const attendu = n2 >= 2 ? 'tient' : n2 === 1 ? 'surveiller' : 'rien';
      verifier(v.niveau === attendu, `${t} verdict ${v.id} : pastille ${v.niveau}, attendu ${attendu}`);
    }
  });

  // 2. pas de défilement horizontal
  const larg = await page.evaluate(() => ({ sw: document.documentElement.scrollWidth, iw: window.innerWidth }));
  verifier(larg.sw <= larg.iw, `${t} défilement horizontal : scrollWidth ${larg.sw} > ${larg.iw}`);

  // 1. console et réseau
  verifier(messages.length === 0, `${t} console / réseau :\n    ` + messages.join('\n    '));

  // 6. capture
  await page.screenshot({ path: join(ICI, 'captures', cf.nom + '.png'), fullPage: true });
  console.log(`${t} ${comparees} valeurs comparées, largeur ${larg.sw}/${larg.iw}, ${messages.length} message(s) console`);
  await ctx.close();
}
await navigateur.close();

console.log(`Contrôles : ${verifs}, échecs : ${echecs.length}`);
if (echecs.length) { echecs.slice(0, 20).forEach(e => console.log('  ÉCHEC ' + e)); process.exit(1); }
console.log('OK : la page passe tous les contrôles. Captures dans captures/.');
