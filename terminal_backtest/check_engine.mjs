// Compare le moteur JavaScript (src/engine.js) a expected.json (sortie de reference.py).
// Usage : node check_engine.mjs   -> code 0 seulement si tout est identique.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const ICI = dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
const BT = require(join(ICI, 'src', 'engine.js'));
const D = JSON.parse(readFileSync(join(ICI, 'data.json'), 'utf8'));
const X = JSON.parse(readFileSync(join(ICI, 'expected.json'), 'utf8'));

const t0 = Date.now();
const out = BT.tout(D);
const duree = Date.now() - t0;

const ecarts = [];
const compte = { chaines: 0, nombres: 0, entiers: 0, textes: 0, nuls: 0 };
const TOL = 1e-9;
let ecartMax = 0;

function ecart(chemin, attendu, obtenu) { ecarts.push(`${chemin} : attendu ${JSON.stringify(attendu)}, obtenu ${JSON.stringify(obtenu)}`); }

function comparer(chemin, attendu, obtenu) {
  if (attendu === null) {
    compte.nuls++;
    if (obtenu !== null) ecart(chemin, attendu, obtenu);
  } else if (Array.isArray(attendu)) {
    if (!Array.isArray(obtenu) || obtenu.length !== attendu.length) { ecart(chemin + '.length', attendu.length, obtenu && obtenu.length); return; }
    attendu.forEach((v, i) => comparer(`${chemin}[${i}]`, v, obtenu[i]));
  } else if (typeof attendu === 'object') {
    if (typeof obtenu !== 'object' || obtenu === null) { ecart(chemin, '{...}', obtenu); return; }
    for (const k of Object.keys(attendu)) {
      if (!(k in obtenu)) { ecart(`${chemin}.${k}`, attendu[k], 'absent'); continue; }
      comparer(`${chemin}.${k}`, attendu[k], obtenu[k]);
    }
  } else if (typeof attendu === 'number') {
    if (typeof obtenu !== 'number') { ecart(chemin, attendu, obtenu); return; }
    if (Number.isInteger(attendu) && /\.(trades|a|b|T|n_passe)$/.test(chemin)) {
      compte.entiers++;
      if (obtenu !== attendu) ecart(chemin, attendu, obtenu);
    } else {
      compte.nombres++;
      if (Math.abs(obtenu - attendu) > ecartMax) ecartMax = Math.abs(obtenu - attendu);
      if (!(Math.abs(obtenu - attendu) <= TOL)) ecart(chemin, attendu, obtenu);
    }
  } else if (typeof attendu === 'string') {
    if (attendu.length > 100) compte.chaines++; else compte.textes++;
    if (obtenu !== attendu) {
      let i = 0;
      while (i < attendu.length && attendu[i] === obtenu[i]) i++;
      ecarts.push(`${chemin} : chaine differente (longueur ${attendu.length} / ${obtenu && obtenu.length}), 1er ecart a l'indice ${i}`);
    }
  } else if (obtenu !== attendu) ecart(chemin, attendu, obtenu);
}

// 1. les 28 chaines de signaux
comparer('signaux', X.signaux, out.signaux);
// 2. cellules (2 jeux de frais x 15 passes x 7 x 4), long, acheter_conserver
comparer('cellules', X.cellules, out.cellules);
comparer('long', X.long, out.long);
comparer('acheter_conserver', X.acheter_conserver, out.acheter_conserver);
// 3. meta.passes (a, b, debut, fin) ; et le reste de meta
comparer('meta', X.meta, out.meta);

const total = compte.chaines + compte.nombres + compte.entiers + compte.textes + compte.nuls;
console.log(`Moteur calcule en ${duree} ms.`);
console.log(`Valeurs comparees : ${total} (signaux : ${compte.chaines} chaines de ${D.dates.length} caracteres ; ` +
  `${compte.nombres} nombres a ${TOL} pres ; ${compte.entiers} entiers exacts ; ${compte.textes} textes ; ${compte.nuls} valeurs nulles)`);
console.log(`Plus grand ecart sur un nombre : ${ecartMax}`);
if (ecarts.length) {
  console.log(`ECHEC : ${ecarts.length} ecart(s). Les 10 premiers :`);
  ecarts.slice(0, 10).forEach(e => console.log('  ' + e));
  process.exit(1);
}
console.log('OK : tout est identique a expected.json.');
process.exit(0);
