// Controle du port JavaScript : moteur_jour.js redonne moteur_jour.py sur les vecteurs de test (test_v2.py).
// Lancer depuis ce dossier : node test_js.mjs
import fs from "fs";
import {createRequire} from "module";
const require = createRequire(import.meta.url);
const {parcoursJour} = require("./moteur_jour.js");
const D = JSON.parse(fs.readFileSync("donnees_v2.json", "utf8"));
const V = JSON.parse(fs.readFileSync("vecteurs_test.json", "utf8"));
const dec = (b, T) => { const u = Buffer.from(b, "base64"); return new T(u.buffer, u.byteOffset, u.byteLength / T.BYTES_PER_ELEMENT); };
const gi = dec(D.gain, Int32Array), pi = dec(D.pire, Int32Array), dr = dec(D.drap, Uint8Array), ix = dec(D.index, Uint16Array);
const taille = D.ns * D.nk, G = [], P = [], DD = [];
for (let t = 0; t < D.tirages.length; t++) {
  const g = new Float64Array(taille), p = new Float64Array(taille), d = new Uint8Array(taille);
  for (let a = 0; a < D.ns; a++) { const u = ix[t * D.ns + a]; for (let k = 0; k < D.nk; k++) { g[a * D.nk + k] = gi[u * D.nk + k] / 1e5; p[a * D.nk + k] = pi[u * D.nk + k] / 1e5; d[a * D.nk + k] = dr[u * D.nk + k]; } }
  G.push(g); P.push(p); DD.push(d);
}
const PAGE = D.tirages.map((_, i) => i);
let ok = 0, n = 0;
for (const v of V) {
  const t = PAGE.indexOf(v.t);
  if (t < 0) continue;
  const R = Object.assign({}, v.regles), ci = {0: 0, 500: 1, 750: 2}[R.cap];
  const ret = new Float64Array(504);
  const r = parcoursJour(Int32Array.from(v.lignes), G[t], P[t], DD[t], ci, R, ret);
  const memes = [0, 1, 2, 3, 5, 6].every(i => Math.round(r[i]) === Math.round(v.r[i])) && Math.abs(r[4] - v.r[4]) < 0.01 &&
    v.ret.every(([s, x]) => Math.abs(ret[s] - x) < 0.01) && ret.filter(x => x > 0).length === v.ret.length;
  n++; if (memes) ok++; else if (n - ok <= 3) console.log("ecart", v.r, r);
}
console.log(`port JavaScript = moteur journalier Python : ${ok} / ${n} achats identiques`);
if (ok !== n) process.exit(1);
