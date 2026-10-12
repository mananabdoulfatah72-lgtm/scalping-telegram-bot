/* Cerveau de Jarvis : un cœur lumineux d'où partent des filaments vers 18 zones (une par compétence). Quand Jarvis
   utilise un outil, la zone s'allume et des impulsions voyagent du cœur vers elle puis reviennent ; le cœur suit la
   voix (écoute, réflexion, parole). Les événements arrivent du serveur local par websocket ; sans serveur (démo,
   page publiée), un simulateur joue des scènes réalistes. */
(() => {
"use strict";
const $ = (id) => document.getElementById(id);
const meta = (n) => (document.querySelector(`meta[name="${n}"]`) || {}).content || "";
const JETON = meta("jarvis-jeton");
const DEMO = meta("jarvis-demo") === "true" || window.JARVIS_DEMO_LOCAL === true || JETON === "__JETON__" || !/^https?:/.test(location.protocol);
const REDUIT = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const ZONES = [
  ["VOIX", "#39d8ff", "Voix"], ["VISION", "#8cf6ff", "Vision"], ["DOMOTIQUE", "#ffd166", "Domotique"],
  ["STREAMING", "#ff4d6d", "Streaming"], ["PC", "#4f9dff", "Contrôle PC"], ["AGENDA", "#a3ff7a", "Agenda"],
  ["MAIL", "#ff9f43", "Mail"], ["DISCORD", "#7c6cff", "Discord"], ["INSTAGRAM", "#ff4fd8", "Instagram"],
  ["RESERVATIONS", "#ffb3c6", "Réservations"], ["NAVIGATEUR", "#48f0b5", "Navigateur"], ["APPELS", "#ff6b3d", "Appels"],
  ["MEMOIRE", "#c77dff", "Mémoire"], ["PERSONNALITE", "#e9ecff", "Personnalité"], ["PRESENCE", "#2ee6a6", "Présence"],
  ["UTILITAIRES", "#9ad1ff", "Utilitaires"], ["MCP", "#b8c0ff", "Serveur MCP"], ["TELEGRAM", "#29b6f6", "Telegram"],
];
const NZ = ZONES.length;
const IDX = Object.fromEntries(ZONES.map((z, i) => [z[0], i]));
const MODULE_ZONE = { pc: "PC", vision: "VISION", domotique: "DOMOTIQUE", streaming: "STREAMING", agenda: "AGENDA", mail: "MAIL",
  discord: "DISCORD", instagram: "INSTAGRAM", navigateur: "NAVIGATEUR", appels: "APPELS", memoire: "MEMOIRE",
  personnalite: "PERSONNALITE", presence: "PRESENCE", utilitaires: "UTILITAIRES", telegram: "TELEGRAM" };
const ETATS = { veille: "EN VEILLE", ecoute: "J'ÉCOUTE", transcription: "JE TRANSCRIS", reflexion: "JE RÉFLÉCHIS", parle: "JE PARLE" };

function graine(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

// ------------------------------------------------------------------ scène
const canvas = $("cerveau");
let renderer;
try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: "high-performance" });
} catch (e) {
  document.body.classList.add("sans-3d");
}
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 0.1, 300);
camera.position.set(0, 1.5, 34);
const groupe = new THREE.Group();
scene.add(groupe);
let ratio = Math.min(window.devicePixelRatio || 1, 2);

const act = new Float32Array(NZ);           // activité de chaque zone (0 à 1)
const enCours = new Int16Array(NZ);         // outils en cours par zone
const couleurs = ZONES.map((z) => new THREE.Color(z[1]));
const COEUR = { veille: new THREE.Color("#9fe8ff"), ecoute: new THREE.Color("#45e0ff"), transcription: new THREE.Color("#ffd28a"),
  reflexion: new THREE.Color("#ffe2a8"), parle: new THREE.Color("#7dffcf"), erreur: new THREE.Color("#ff5470") };
const etatVisuel = { etat: "veille", coeur: new THREE.Color("#9fe8ff"), audio: 0, micro: 0, orage: 0, global: 0.15 };

const R = graine(20261012);
const v3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
const hasard = (r) => v3((R() * 2 - 1) * r, (R() * 2 - 1) * r, (R() * 2 - 1) * r);
const ELL = v3(1.38, 0.92, 1.0);             // forme de cerveau (plus large que haut)

// positions des zones : sphère de Fibonacci aplatie
const ancres = [];
for (let i = 0; i < NZ; i++) {
  const y = 1 - (i + 0.5) / NZ * 2, r = Math.sqrt(1 - y * y), phi = i * Math.PI * (3 - Math.sqrt(5));
  ancres.push(v3(Math.cos(phi) * r, y * 0.86, Math.sin(phi) * r).multiplyScalar(11.5).multiply(ELL));
}

const chemins = ancres.map(() => []);       // filaments principaux de chaque zone (pour les impulsions)
const L = { p: [], z: [], t: [] };          // segments
const P = { p: [], z: [], t: [], ph: [], s: [] };   // particules

function bezier(a, b, c, d, t) {
  const u = 1 - t;
  return v3().addScaledVector(a, u * u * u).addScaledVector(b, 3 * u * u * t).addScaledVector(c, 3 * u * t * t).addScaledVector(d, t * t * t);
}
function ajouterChemin(points, zone, t0 = 0, t1 = 1, garder = false, densite = 3) {
  const n = points.length;
  for (let i = 0; i < n - 1; i++) {
    const a = points[i], b = points[i + 1];
    L.p.push(a.x, a.y, a.z, b.x, b.y, b.z);
    L.z.push(zone, zone);
    L.t.push(t0 + (t1 - t0) * i / (n - 1), t0 + (t1 - t0) * (i + 1) / (n - 1));
    for (let k = 0; k < densite; k++) {
      const q = v3().lerpVectors(a, b, R()).add(hasard(0.06));
      P.p.push(q.x, q.y, q.z); P.z.push(zone); P.t.push(t0 + (t1 - t0) * (i + R()) / (n - 1)); P.ph.push(R()); P.s.push(0.22 + R() * 0.5);
    }
  }
  if (garder) {
    const f = new Float32Array(n * 3);
    points.forEach((q, i) => { f[i * 3] = q.x; f[i * 3 + 1] = q.y; f[i * 3 + 2] = q.z; });
    chemins[zone].push(f);
  }
}

for (let z = 0; z < NZ; z++) {
  const A = ancres[z];
  for (let k = 0; k < 17; k++) {                      // filaments cœur -> zone
    const debut = hasard(1.1), fin = v3().copy(A).add(hasard(1.6));
    const dir = v3().subVectors(fin, debut);
    const c1 = v3().copy(debut).addScaledVector(dir, 0.33).add(hasard(3.6));
    const c2 = v3().copy(debut).addScaledVector(dir, 0.66).add(hasard(3.2));
    const pts = [];
    for (let i = 0; i <= 30; i++) pts.push(bezier(debut, c1, c2, fin, i / 30).add(hasard(0.07)));
    ajouterChemin(pts, z, 0, 1, true, 3);
  }
  const dehors = v3().copy(A).normalize();
  for (let k = 0; k < 40; k++) {                      // arborisation autour de la zone
    let q = v3().copy(A).add(hasard(1.3));
    const pts = [q.clone()];
    const d = v3().copy(dehors).add(hasard(0.95)).normalize();
    const pas = 6 + Math.floor(R() * 5);
    for (let i = 0; i < pas; i++) {
      d.add(hasard(0.45)).normalize();
      q = v3().copy(q).addScaledVector(d, 0.32 + R() * 0.42);
      pts.push(q.clone());
    }
    ajouterChemin(pts, z, 0.75, 1.0, false, 2);
  }
}
// synapses entre zones voisines (chaque moitié appartient à une zone)
for (let z = 0; z < NZ; z++) {
  const voisins = ancres.map((a, j) => [a.distanceTo(ancres[z]), j]).filter(([, j]) => j !== z).sort((a, b) => a[0] - b[0]).slice(0, 2);
  for (const [, j] of voisins) {
    if (j < z) continue;
    const a = ancres[z], b = ancres[j], m = v3().addVectors(a, b).multiplyScalar(0.5).multiplyScalar(1.12).add(hasard(1.2));
    const pts = [];
    for (let i = 0; i <= 24; i++) pts.push(bezier(a, v3().lerpVectors(a, m, 0.7), v3().lerpVectors(b, m, 0.7), b, i / 24).add(hasard(0.06)));
    ajouterChemin(pts.slice(0, 13), z, 1, 0.8, false, 2);
    ajouterChemin(pts.slice(12), j, 0.8, 1, false, 2);
  }
}
for (let k = 0; k < 1700; k++) {                       // cœur dense
  const r = Math.pow(R(), 1.8) * 1.9, q = hasard(1).normalize().multiplyScalar(r);
  P.p.push(q.x, q.y, q.z); P.z.push(-2); P.t.push(0); P.ph.push(R()); P.s.push(0.35 + R() * 0.9);
}
for (let k = 0; k < 2600; k++) {                       // poussière d'étoiles autour
  const q = hasard(1).normalize().multiplyScalar(6 + R() * 22).multiply(ELL);
  P.p.push(q.x, q.y, q.z); P.z.push(-1); P.t.push(1); P.ph.push(R()); P.s.push(0.18 + R() * 0.45);
}

const uniforms = {
  uAct: { value: Array.from(act) }, uCol: { value: couleurs }, uCoeur: { value: etatVisuel.coeur },
  uTemps: { value: 0 }, uGlobal: { value: 0.15 }, uAudio: { value: 0 }, uEchelle: { value: 400 },
};
const DECL = `
  attribute float aZone; attribute float aT;
  uniform float uAct[${NZ}]; uniform vec3 uCol[${NZ}]; uniform vec3 uCoeur; uniform float uTemps; uniform float uGlobal; uniform float uAudio;
  varying vec3 vC; varying float vA;
  float activite() { if (aZone < -0.5) return 0.0; int z = int(aZone + 0.5); for (int i = 0; i < ${NZ}; i++) { if (i == z) return uAct[i]; } return 0.0; }
  vec3 teinte() { if (aZone < -0.5) return uCoeur; int z = int(aZone + 0.5); for (int i = 0; i < ${NZ}; i++) { if (i == z) return uCol[i]; } return uCoeur; }`;
const lignesMat = new THREE.ShaderMaterial({
  uniforms, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `${DECL}
    void main() {
      float a = activite();
      vec3 c = mix(uCoeur, teinte(), smoothstep(0.04, 0.62, aT));
      float onde = 0.5 + 0.5 * sin(aT * 18.0 - uTemps * 6.0);
      vC = c * (1.0 + 0.8 * a + 0.25 * uGlobal);
      vA = 0.22 + 0.36 * a * (0.6 + 0.4 * onde) + 0.07 * uGlobal + (1.0 - smoothstep(0.0, 0.15, aT)) * 0.1 * (1.0 + 2.0 * uAudio);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }`,
  fragmentShader: `varying vec3 vC; varying float vA; void main() { gl_FragColor = vec4(vC * vA, vA); }`,
});
const pointsMat = new THREE.ShaderMaterial({
  uniforms, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `${DECL}
    attribute float aPhase; attribute float aTaille;
    uniform float uEchelle;
    void main() {
      float a = activite();
      vec4 mv = modelViewMatrix * vec4(position, 1.0);
      float scint = 0.55 + 0.45 * sin(uTemps * (1.4 + aPhase * 2.2) + aPhase * 6.2831);
      float coeur = aZone < -1.5 ? 1.0 : 0.0, poussiere = (aZone < -0.5 && aZone > -1.5) ? 1.0 : 0.0;
      vec3 c = coeur > 0.5 ? uCoeur : mix(uCoeur, teinte(), smoothstep(0.04, 0.62, aT));
      float taille = aTaille * (1.0 + 0.9 * a + coeur * (0.4 + 1.8 * uAudio));
      vC = c * (0.85 + 0.9 * a + coeur * (0.5 + 1.2 * uAudio));
      vA = poussiere > 0.5 ? 0.32 * scint : (0.42 + 0.45 * a + coeur * 0.45 + 0.08 * uGlobal) * scint;
      gl_PointSize = taille * uEchelle / -mv.z;
      gl_Position = projectionMatrix * mv;
    }`,
  fragmentShader: `varying vec3 vC; varying float vA;
    void main() { float d = length(gl_PointCoord - 0.5); float a = smoothstep(0.5, 0.0, d); a *= a; gl_FragColor = vec4(vC * a * vA, a * vA); }`,
});
function geometrie(donnees, attributs) {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(new Float32Array(donnees.p), 3));
  for (const [nom, cle] of attributs) g.setAttribute(nom, new THREE.BufferAttribute(new Float32Array(donnees[cle]), 1));
  return g;
}
const lignes = new THREE.LineSegments(geometrie(L, [["aZone", "z"], ["aT", "t"]]), lignesMat);
const geoPoints = geometrie(P, [["aZone", "z"], ["aT", "t"], ["aPhase", "ph"], ["aTaille", "s"]]);
const points = new THREE.Points(geoPoints, pointsMat);
groupe.add(lignes, points);
const nbPoints = P.z.length;

// halos (cœur et zones)
function textureHalo() {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d"), r = g.createRadialGradient(64, 64, 0, 64, 64, 64);
  r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(0.18, "rgba(255,255,255,.55)"); r.addColorStop(0.5, "rgba(255,255,255,.12)"); r.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = r; g.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}
const HALO = textureHalo();
const haloCoeur = new THREE.Sprite(new THREE.SpriteMaterial({ map: HALO, color: etatVisuel.coeur, blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
haloCoeur.scale.set(9, 9, 1);
groupe.add(haloCoeur);
const halos = ancres.map((a, i) => {
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: HALO, color: couleurs[i], blending: THREE.AdditiveBlending, depthWrite: false, transparent: true, opacity: 0.25 }));
  s.position.copy(a); s.scale.set(3, 3, 1); groupe.add(s); return s;
});

// impulsions : têtes lumineuses avec traînée, le long des filaments
const MAXI = 360, TRAINE = 5;
const geoImp = new THREE.BufferGeometry();
const impPos = new Float32Array(MAXI * TRAINE * 3), impCol = new Float32Array(MAXI * TRAINE * 3), impT = new Float32Array(MAXI * TRAINE);
geoImp.setAttribute("position", new THREE.BufferAttribute(impPos, 3).setUsage(THREE.DynamicDrawUsage));
geoImp.setAttribute("aCouleur", new THREE.BufferAttribute(impCol, 3).setUsage(THREE.DynamicDrawUsage));
geoImp.setAttribute("aTaille", new THREE.BufferAttribute(impT, 1).setUsage(THREE.DynamicDrawUsage));
const impMat = new THREE.ShaderMaterial({
  uniforms: { uEchelle: uniforms.uEchelle }, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  vertexShader: `attribute vec3 aCouleur; attribute float aTaille; uniform float uEchelle; varying vec3 vC;
    void main() { vec4 mv = modelViewMatrix * vec4(position, 1.0); vC = aCouleur; gl_PointSize = aTaille * uEchelle / -mv.z; gl_Position = projectionMatrix * mv; }`,
  fragmentShader: `varying vec3 vC; void main() { float d = length(gl_PointCoord - 0.5); float a = smoothstep(0.5, 0.0, d); gl_FragColor = vec4(vC * a * a, a); }`,
});
const impulsions = new THREE.Points(geoImp, impMat);
groupe.add(impulsions);
const vivantes = [];
const BLANC = new THREE.Color("#ffffff"), ROUGE = new THREE.Color("#ff4060");

function envoyer(zone, n = 6, sens = 1, couleur = null) {
  if (zone < 0 || zone >= NZ || !chemins[zone].length) return;
  for (let k = 0; k < n && vivantes.length < MAXI; k++) {
    const ch = chemins[zone][Math.floor(Math.random() * chemins[zone].length)];
    vivantes.push({ ch, t: sens > 0 ? -Math.random() * 0.25 : 1 + Math.random() * 0.25, v: (0.45 + Math.random() * 0.55) * sens,
      c: (couleur || couleurs[zone]).clone().lerp(BLANC, 0.45), taille: 1.1 + Math.random() * 0.8 });
  }
}
function pointSur(ch, t, sortie) {
  const n = ch.length / 3, x = Math.min(n - 1.001, Math.max(0, t * (n - 1))), i = Math.floor(x), f = x - i;
  sortie[0] = ch[i * 3] + (ch[i * 3 + 3] - ch[i * 3]) * f;
  sortie[1] = ch[i * 3 + 1] + (ch[i * 3 + 4] - ch[i * 3 + 1]) * f;
  sortie[2] = ch[i * 3 + 2] + (ch[i * 3 + 5] - ch[i * 3 + 2]) * f;
}
const tmp = [0, 0, 0];
function majImpulsions(dt) {
  let k = 0;
  for (let i = vivantes.length - 1; i >= 0; i--) {
    const p = vivantes[i];
    p.t += p.v * dt;
    if (p.t > 1.12 || p.t < -0.12) { vivantes.splice(i, 1); continue; }
  }
  for (const p of vivantes) {
    for (let j = 0; j < TRAINE; j++) {
      const t = p.t - p.v * j * 0.028;
      if (t < 0 || t > 1) { impT[k] = 0; k++; continue; }
      pointSur(p.ch, t, tmp);
      impPos[k * 3] = tmp[0]; impPos[k * 3 + 1] = tmp[1]; impPos[k * 3 + 2] = tmp[2];
      const att = 1 - j / TRAINE;
      impCol[k * 3] = p.c.r * att; impCol[k * 3 + 1] = p.c.g * att; impCol[k * 3 + 2] = p.c.b * att;
      impT[k] = p.taille * (0.35 + 0.65 * att);
      k++;
    }
  }
  geoImp.setDrawRange(0, k);
  geoImp.attributes.position.needsUpdate = geoImp.attributes.aCouleur.needsUpdate = geoImp.attributes.aTaille.needsUpdate = true;
}

// étiquettes des zones
const etiquettes = ZONES.map(([id, c, nom]) => {
  const e = document.createElement("div");
  e.className = "etq"; e.textContent = nom; e.style.setProperty("--c", c);
  $("etiquettes").appendChild(e); return e;
});
const proj = new THREE.Vector3();
function majEtiquettes() {
  const w = innerWidth, h = innerHeight;
  for (let i = 0; i < NZ; i++) {
    proj.copy(ancres[i]).multiplyScalar(1.13).applyMatrix4(groupe.matrixWorld).project(camera);
    const e = etiquettes[i];
    if (proj.z > 1) { e.style.display = "none"; continue; }
    e.style.display = "";
    e.style.transform = `translate(-50%,-50%) translate(${((proj.x + 1) / 2 * w).toFixed(1)}px,${((1 - proj.y) / 2 * h).toFixed(1)}px)`;
    const actif = act[i] > 0.3;
    if (actif !== e.classList.contains("actif")) e.classList.toggle("actif", actif);
  }
}

// rotation : automatique, ou à la souris / au doigt
let rotY = 0, rotX = 0.1, vitesseRot = 0.05, glisse = null, dernierGeste = 0;
canvas.addEventListener("pointerdown", (e) => { glisse = { x: e.clientX, y: e.clientY, ry: rotY, rx: rotX }; canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener("pointermove", (e) => {
  if (!glisse) return;
  rotY = glisse.ry + (e.clientX - glisse.x) * 0.006; rotX = Math.max(-0.7, Math.min(0.7, glisse.rx + (e.clientY - glisse.y) * 0.004));
  dernierGeste = performance.now();
});
canvas.addEventListener("pointerup", () => { glisse = null; });
canvas.addEventListener("wheel", (e) => { camera.position.z = Math.max(18, Math.min(60, camera.position.z + e.deltaY * 0.02)); }, { passive: true });

function redimensionner() {
  if (!renderer) return;
  renderer.setPixelRatio(ratio);
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth / innerHeight;
  camera.position.z = innerWidth < 700 ? 44 : (camera.position.z < 30 ? 34 : camera.position.z);
  camera.updateProjectionMatrix();
  uniforms.uEchelle.value = innerHeight * ratio * 0.5;
}
addEventListener("resize", redimensionner);
redimensionner();

// boucle d'animation (qualité réduite automatiquement si le PC peine)
let avant = performance.now(), cumul = 0, images = 0, reduit = false, ambiance = 0;
function image(maintenant) {
  requestAnimationFrame(image);
  const dt = Math.min(0.05, (maintenant - avant) / 1000);
  avant = maintenant;
  cumul += dt; images++;
  if (cumul > 2.5) {
    if (!reduit && images / cumul < 38) {
      reduit = true; ratio = 1; geoPoints.setDrawRange(0, Math.floor(nbPoints * 0.6)); redimensionner();
    }
    cumul = 0; images = 0;
  }
  for (let i = 0; i < NZ; i++) {
    const cible = enCours[i] > 0 ? 0.9 : 0;
    act[i] = cible > act[i] ? act[i] + (cible - act[i]) * Math.min(1, dt * 8) : act[i] * Math.exp(-dt / 1.4);
    uniforms.uAct.value[i] = Math.max(act[i], i === IDX.VOIX ? Math.max(etatVisuel.audio, etatVisuel.micro) * 0.9 : 0);
    halos[i].material.opacity = 0.22 + act[i] * 0.55;
    const s = 2.4 + act[i] * 3.2; halos[i].scale.set(s, s, 1);
  }
  // ambiance : impulsions au repos, orage pendant la réflexion
  const taux = REDUIT ? 0.3 : (etatVisuel.etat === "reflexion" ? 26 : etatVisuel.etat === "parle" ? 7 : 1.6);
  ambiance += dt * taux;
  while (ambiance >= 1) {
    ambiance -= 1;
    const z = etatVisuel.etat === "parle" ? IDX.VOIX : Math.floor(Math.random() * NZ);
    envoyer(z, 1, Math.random() < 0.6 ? 1 : -1);
  }
  etatVisuel.global += ((etatVisuel.etat === "reflexion" ? 1 : etatVisuel.etat === "veille" ? 0.12 : 0.4) - etatVisuel.global) * Math.min(1, dt * 2);
  uniforms.uGlobal.value = etatVisuel.global;
  etatVisuel.audio *= Math.exp(-dt / 0.25); etatVisuel.micro *= Math.exp(-dt / 0.3);
  uniforms.uAudio.value = Math.max(etatVisuel.audio, etatVisuel.micro * 0.8);
  const cible = COEUR[etatVisuel.etat] || COEUR.veille;
  etatVisuel.coeur.lerp(cible, Math.min(1, dt * 3));
  haloCoeur.material.color.copy(etatVisuel.coeur);
  const respire = 1 + Math.sin(maintenant / 900) * 0.06;
  const sc = (8 + uniforms.uAudio.value * 9 + etatVisuel.global * 2.5) * respire;
  haloCoeur.scale.set(sc, sc, 1);
  uniforms.uTemps.value = maintenant / 1000;
  if (!glisse && maintenant - dernierGeste > 4000) rotY += dt * vitesseRot * (REDUIT ? 0.2 : 1);
  groupe.rotation.y = rotY; groupe.rotation.x = rotX + Math.sin(maintenant / 7000) * 0.05;
  majImpulsions(dt);
  groupe.updateMatrixWorld();
  majEtiquettes();
  if (renderer) renderer.render(scene, camera);
}
requestAnimationFrame(image);

// ------------------------------------------------------------------ HUD
function horloge() {
  const d = new Date();
  $("horloge").textContent = d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}
setInterval(horloge, 1000); horloge();

const modulesEtat = {};
function construireModules() {
  const ul = $("modules"); ul.innerHTML = "";
  for (const [id, c, nom] of ZONES) {
    const li = document.createElement("li");
    li.id = "m-" + id; li.style.setProperty("--c", c);
    li.innerHTML = `<span class="d"></span><span>${nom}</span><span class="e">—</span>`;
    ul.appendChild(li);
  }
}
construireModules();
const ETIQ = { pret: "PRÊT", non_configure: "À CONFIG.", absent: "À INSTALLER", erreur: "ERREUR" };
function majModules(liste, voix) {
  for (const m of liste || []) {
    const z = MODULE_ZONE[m.module]; if (z) modulesEtat[z] = m;
  }
  if (modulesEtat.NAVIGATEUR) modulesEtat.RESERVATIONS = modulesEtat.NAVIGATEUR;
  modulesEtat.VOIX = { etat: voix ? "pret" : "non_configure", message: voix ? "mains libres" : "voix inactive" };
  modulesEtat.MCP = modulesEtat.MCP || { etat: "pret", message: "serveur MCP" };
  let prets = 0;
  for (const [id] of ZONES) {
    const m = modulesEtat[id], li = $("m-" + id); if (!li || !m) continue;
    li.className = m.etat + (act[IDX[id]] > 0.3 ? " actif" : "");
    li.querySelector(".e").textContent = ETIQ[m.etat] || m.etat;
    li.title = m.message || "";
    if (m.etat === "pret") prets++;
  }
  $("compte-modules").textContent = `${prets}/${NZ}`;
}
setInterval(() => { for (const [id] of ZONES) { const li = $("m-" + id); if (li) li.classList.toggle("actif", act[IDX[id]] > 0.3); } }, 300);

function journal(zone, texte, ok = true) {
  const ol = $("journal"), li = document.createElement("li");
  const z = ZONES[IDX[zone]] || ZONES[0];
  li.className = ok ? "" : "ko"; li.style.setProperty("--c", z[1]);
  li.innerHTML = `<span class="h">${new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}</span><span class="z">${z[2].toUpperCase()}</span><span class="r"></span>`;
  li.querySelector(".r").textContent = texte;
  ol.prepend(li);
  while (ol.children.length > 7) ol.lastChild.remove();
}
function toast(texte, genre = "") {
  const t = document.createElement("div"); t.className = "toast " + genre; t.textContent = texte;
  $("toasts").appendChild(t); setTimeout(() => t.remove(), 7000);
}
const histoCpu = [];
function majStats(s) {
  const jauge = (id, v, txt) => { const el = $(id); if (v == null) return; el.hidden = false; el.querySelector(".v").textContent = txt; el.querySelector("b").style.width = Math.max(0, Math.min(100, v)) + "%"; };
  jauge("j-cpu", s.cpu, `${Math.round(s.cpu)} %`);
  jauge("j-ram", s.ram, s.ram_go != null ? `${s.ram_go} / ${s.ram_total} Go` : `${Math.round(s.ram)} %`);
  if (s.gpu != null) jauge("j-gpu", s.gpu, `${Math.round(s.gpu)} %`); else { const g = $("j-gpu"); g.querySelector(".v").textContent = "non mesuré"; }
  if (s.batterie != null) jauge("j-bat", s.batterie, `${s.batterie} %${s.secteur ? " ⚡" : ""}`);
  histoCpu.push(s.cpu || 0); if (histoCpu.length > 60) histoCpu.shift();
  const c = $("trace"), g = c.getContext("2d"), w = c.width, h = c.height;
  g.clearRect(0, 0, w, h);
  g.beginPath();
  histoCpu.forEach((v, i) => { const x = i / 59 * w, y = h - 2 - v / 100 * (h - 4); i ? g.lineTo(x, y) : g.moveTo(x, y); });
  g.strokeStyle = "#45e0ff"; g.lineWidth = 1.5; g.stroke();
  g.lineTo(w * (histoCpu.length - 1) / 59, h); g.lineTo(0, h); g.closePath();
  const grad = g.createLinearGradient(0, 0, 0, h); grad.addColorStop(0, "rgba(69,224,255,.28)"); grad.addColorStop(1, "rgba(69,224,255,0)");
  g.fillStyle = grad; g.fill();
}
let minuteurs = [];
function majMinuteurs() {
  const ul = $("minuteurs"), now = Date.now() / 1000;
  minuteurs = minuteurs.filter((m) => m.fin > now - 1);
  if (!minuteurs.length) { ul.innerHTML = '<li class="vide">aucun</li>'; return; }
  ul.innerHTML = "";
  for (const m of minuteurs) {
    const r = Math.max(0, Math.round(m.fin - now)), li = document.createElement("li");
    li.innerHTML = `<span></span><span>${String(Math.floor(r / 60)).padStart(2, "0")}:${String(r % 60).padStart(2, "0")}</span>`;
    li.firstChild.textContent = m.libelle || "minuteur";
    ul.appendChild(li);
  }
}
setInterval(majMinuteurs, 1000);

let reponse = "", confirmationId = null, confirmationFin = 0;
function majEtat(e) {
  etatVisuel.etat = e;
  const el = $("etat"); el.dataset.etat = e;
  $("etat-texte").textContent = ETATS[e] || e.toUpperCase();
}
function montrerConfirmation(id, question) {
  confirmationId = id; confirmationFin = Date.now() + 45000;
  $("conf-q").textContent = question; $("confirmation").hidden = false;
  const b = $("conf-temps"); b.style.transition = "none"; b.style.width = "100%";
  requestAnimationFrame(() => { b.style.transition = "width 45s linear"; b.style.width = "0%"; });
  $("conf-oui").focus();
}

// ------------------------------------------------------------------ événements
function evenement(e) {
  switch (e.type) {
    case "etat": majEtat(e.etat); break;
    case "transcription": {
      $("toi").textContent = e.texte; reponse = ""; $("jarvis").textContent = "…";
      const z = e.origine === "telegram" ? IDX.TELEGRAM : IDX.VOIX;
      act[z] = 1; envoyer(z, 10, -1);
      break;
    }
    case "reponse":
      reponse += e.morceau; $("jarvis").textContent = reponse;
      if (Math.random() < 0.5) envoyer(IDX.VOIX, 1, 1);
      break;
    case "reponse_fin": if (e.texte) $("jarvis").textContent = e.texte; break;
    case "outil": {
      const z = IDX[e.zone]; if (z == null) break;
      if (e.phase === "debut") { enCours[z]++; act[z] = 1; envoyer(z, 12, 1); }
      else {
        enCours[z] = Math.max(0, enCours[z] - 1); act[z] = 1;
        envoyer(z, 8, -1, e.ok === false ? ROUGE : null);
        journal(e.zone, `${e.nom} ${e.ok === false ? "✗" : "✓"} ${e.resume || ""}`, e.ok !== false);
      }
      break;
    }
    case "stats": majStats(e); break;
    case "modules":
      majModules(e.liste, e.voix);
      if (e.moteur) $("moteur").textContent = e.moteur === "api" ? "Claude · API" : e.moteur === "claude_code" ? "Claude Code" : e.moteur;
      (e.problemes || []).forEach((p) => { if (!toast.vus) toast.vus = new Set(); if (!toast.vus.has(p)) { toast.vus.add(p); toast(p, "erreur"); } });
      break;
    case "audio": etatVisuel.audio = Math.max(etatVisuel.audio, e.niveau || 0); break;
    case "micro": etatVisuel.micro = Math.max(etatVisuel.micro, e.niveau || 0); break;
    case "minuteurs": minuteurs = e.liste || []; majMinuteurs(); break;
    case "confirmation":
      if (e.phase === "attente") montrerConfirmation(e.id, e.question);
      else if (e.id === confirmationId) { $("confirmation").hidden = true; confirmationId = null; }
      break;
    case "annonce": $("jarvis").textContent = e.texte; toast(e.texte, "annonce"); act[IDX.UTILITAIRES] = 1; envoyer(IDX.VOIX, 8, 1); break;
    case "erreur": toast(e.message, "erreur"); etatVisuel.coeur.copy(COEUR.erreur); break;
    case "personnalite": $("personnalite").textContent = e.titre || e.nom; act[IDX.PERSONNALITE] = 1; envoyer(IDX.PERSONNALITE, 10, 1); break;
    case "presence": act[IDX.PRESENCE] = 1; envoyer(IDX.PRESENCE, 14, 1); toast(e.present ? "Téléphone de retour à la maison" : "Téléphone parti", "annonce"); break;
    case "conversation": break;
  }
}

// ------------------------------------------------------------------ liaison avec le serveur
async function api(chemin, corps) {
  if (DEMO) return { ok: true };
  try {
    const r = await fetch(chemin, { method: "POST", headers: { "Content-Type": "application/json", "x-jarvis-jeton": JETON }, body: JSON.stringify(corps || {}) });
    return await r.json();
  } catch (e) { toast("Jarvis ne répond pas (le programme est-il lancé ?)", "erreur"); return { ok: false }; }
}
let attenteReco = 1000;
function connecter() {
  const ws = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}/ws?jeton=${encodeURIComponent(JETON)}`);
  ws.onopen = () => { attenteReco = 1000; };
  ws.onmessage = (m) => { try { evenement(JSON.parse(m.data)); } catch (e) { /* message illisible ignoré */ } };
  ws.onclose = () => { $("moteur").textContent = "reconnexion…"; setTimeout(connecter, attenteReco); attenteReco = Math.min(15000, attenteReco * 1.6); };
}

$("saisie").addEventListener("submit", (e) => {
  e.preventDefault();
  const t = $("texte").value.trim(); if (!t) return;
  $("texte").value = "";
  if (DEMO) { demo.demande(t); return; }
  api("/api/message", { texte: t });
});
$("parler").addEventListener("click", async () => {
  if (DEMO) { demo.demande(); return; }
  const r = await api("/api/parler");
  if (r && r.ok === false && r.raison) toast(r.raison, "erreur");
});
$("stop").addEventListener("click", () => api("/api/stop"));
$("conf-oui").addEventListener("click", () => { if (confirmationId) api("/api/confirmation", { id: confirmationId, ok: true }); if (DEMO) evenement({ type: "confirmation", id: confirmationId, phase: "oui" }); });
$("conf-non").addEventListener("click", () => { if (confirmationId) api("/api/confirmation", { id: confirmationId, ok: false }); if (DEMO) evenement({ type: "confirmation", id: confirmationId, phase: "non" }); });
function pleinEcran() { if (!document.fullscreenElement) document.documentElement.requestFullscreen?.().catch(() => {}); else document.exitFullscreen?.(); }
$("plein").addEventListener("click", pleinEcran);
$("masquer").addEventListener("click", () => document.body.classList.toggle("sans-hud"));
addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  if (e.key === "f" || e.key === "F") pleinEcran();
  if (e.key === "h" || e.key === "H") document.body.classList.toggle("sans-hud");
  if (e.key === " ") { e.preventDefault(); $("parler").click(); }
});

// ------------------------------------------------------------------ démo : scènes jouées sans serveur
const demo = (() => {
  const SCENES = [
    { dit: "Allume le salon en violet, à quarante pour cent.", outils: [["hue_regler", "DOMOTIQUE", "Salon allumé (40 %, violet)."]], rep: "C'est fait, monsieur. Le salon est en violet, à quarante pour cent." },
    { dit: "C'est quoi cette erreur sur mon écran ?", outils: [["voir_ecran", "VISION", "Capture de l'écran 1 (1568 x 882)."]], rep: "C'est une erreur Python : le module requests n'est pas installé. Tape pip install requests et relance." },
    { dit: "Résume-moi mes mails non lus.", outils: [["mail_non_lus", "MAIL", "7 mails non lus."]], rep: "Sept mails. Le plus important : ta banque confirme le virement. Deux newsletters, un message de Lucas pour samedi, le reste est de la pub." },
    { dit: "Lance le stream sur OBS.", outils: [["obs_direct", "STREAMING", "Direct lancé."]], conf: "Lancer le direct sur OBS", rep: "Direct lancé. Bon stream, monsieur." },
    { dit: "Qu'est-ce que j'ai demain ?", outils: [["agenda_evenements", "AGENDA", "3 événements demain."]], rep: "Demain : cours à neuf heures, dentiste à quatorze heures trente, et le match à vingt heures." },
    { dit: "Réserve une table pour deux ce soir vers vingt heures, dans un italien près d'ici.", outils: [["reservation_demarrer", "RESERVATIONS", "Mode réservation. TheFork."], ["nav_elements", "RESERVATIONS", "42 éléments."], ["nav_remplir", "RESERVATIONS", "Champ rempli avec « 2 personnes »."], ["nav_cliquer", "RESERVATIONS", "Cliqué."]], conf: "Cliquer sur « Réserver » sur www.thefork.fr", rep: "Table réservée chez Da Vinci à vingt heures pour deux. La confirmation arrive par mail." },
    { dit: "Combien j'ai d'abonnés Instagram par rapport à hier ?", outils: [["instagram_stats", "INSTAGRAM", "@monstudio : 12 480 abonnés (+37 depuis hier)."]], rep: "Douze mille quatre cent quatre-vingts abonnés, trente-sept de plus qu'hier, et tes vues ont pris dix-huit pour cent." },
    { dit: "Mets un minuteur de dix minutes pour les pâtes.", outils: [["minuteur_creer", "UTILITAIRES", "Minuteur lancé pour 10 min (pâtes)."]], minuteur: ["pâtes", 600], rep: "Minuteur de dix minutes lancé pour les pâtes." },
    { dit: "Qu'est-ce qui s'est passé sur Discord aujourd'hui ?", outils: [["discord_mentions", "DISCORD", "2 mentions."], ["discord_recap", "DISCORD", "3 salons actifs."]], rep: "Deux mentions : Yanis te demande pour la session de ce soir, et Sarah a partagé le planning. Sur le serveur, surtout des discussions sur le tournoi." },
    { dit: "Appelle le garage pour savoir si ma voiture est prête.", outils: [["appel_conversation", "APPELS", "J'appelle le garage."]], conf: "Appeler garage pour : savoir si la voiture est prête", rep: "J'appelle le garage. Je te fais le résumé dès que c'est fini." },
    { dit: "Retiens que ma sœur s'appelle Inès et que son anniversaire est le trois mai.", outils: [["memoire_retenir", "MEMOIRE", "Retenu (souvenir 42)."]], rep: "C'est noté. Je te le rappellerai le moment venu." },
    { dit: "Monte le son et mets la musique suivante.", outils: [["pc_volume", "PC", "Volume à 60 %."], ["pc_media", "PC", "Piste suivante."]], rep: "Volume à soixante pour cent, piste suivante." },
    { dit: "Envoie-moi la liste de courses sur Telegram.", outils: [["memoire_chercher", "MEMOIRE", "Liste de courses trouvée."], ["telegram_envoyer", "TELEGRAM", "Message envoyé sur Telegram."]], rep: "Envoyé sur ton téléphone." },
    { dit: "Passe en mode concis.", outils: [["personnalite_changer", "PERSONNALITE", "Personnalité changée en « Concis »."]], perso: "Concis", rep: "Mode concis." },
    { dit: "Résume la page que j'ai ouverte et traduis le titre.", outils: [["nav_lire", "NAVIGATEUR", "Onglet : Nvidia unveils… — techcrunch.com"]], rep: "L'article annonce la nouvelle génération de cartes graphiques, trente pour cent plus rapides. Le titre : Nvidia dévoile sa nouvelle puce." },
    { dit: "Comment va le PC ?", outils: [["pc_stats", "PC", "Processeur 23 %, mémoire 61 %."]], rep: "Tout va bien : processeur à vingt-trois pour cent, mémoire à soixante et un. Chrome est le plus gourmand." },
  ];
  let i = 0, occupe = false;
  const pause = (ms) => new Promise((r) => setTimeout(r, ms));
  async function parler(texte) {
    majEtat("parle"); reponse = "";
    const mots = texte.split(" ");
    for (const m of mots) {
      evenement({ type: "reponse", morceau: m + " " });
      for (let k = 0; k < 3; k++) { evenement({ type: "audio", niveau: 0.25 + Math.random() * 0.6 }); await pause(55); }
    }
    evenement({ type: "reponse_fin", texte });
  }
  async function jouer(s, tape) {
    occupe = true;
    if (!tape) {
      majEtat("ecoute");
      for (let k = 0; k < 24; k++) { evenement({ type: "micro", niveau: 0.2 + Math.random() * 0.7 }); await pause(70); }
      majEtat("transcription"); await pause(450);
    }
    evenement({ type: "transcription", texte: s.dit, origine: s.dit.includes("Telegram") ? "telegram" : "voix" });
    majEtat("reflexion"); await pause(900);
    for (const [nom, zone, resume] of s.outils) {
      evenement({ type: "outil", nom, zone, phase: "debut" });
      await pause(700 + Math.random() * 700);
      if (s.conf && s.outils[s.outils.length - 1][0] === nom) {
        const id = "demo" + Date.now();
        evenement({ type: "confirmation", id, question: s.conf, phase: "attente" });
        await pause(2600);
        evenement({ type: "confirmation", id, question: s.conf, phase: "oui" });
      }
      evenement({ type: "outil", nom, zone, phase: "fin", ok: true, resume });
      if (s.minuteur) { minuteurs = [{ libelle: s.minuteur[0], fin: Date.now() / 1000 + s.minuteur[1] }]; majMinuteurs(); }
      if (s.perso) evenement({ type: "personnalite", titre: s.perso });
      await pause(250);
    }
    await parler(s.rep);
    await pause(1200); majEtat("veille");
    occupe = false;
  }
  function stats() {
    const t = Date.now() / 1000;
    evenement({ type: "stats", cpu: 18 + 14 * Math.abs(Math.sin(t / 7)) + Math.random() * 6, ram: 58 + 4 * Math.sin(t / 30), ram_go: 9.4, ram_total: 16, gpu: 12 + 20 * Math.abs(Math.sin(t / 11)), batterie: 86, secteur: true });
  }
  function demarrer() {
    $("moteur").textContent = "démonstration";
    const b = document.createElement("div");
    b.className = "bandeau-demo hud";
    b.textContent = "Démonstration : ici Jarvis ne t'entend pas et joue des scènes préparées. Installé sur ton PC, il t'écoute et te répond pour de vrai.";
    document.body.appendChild(b);
    $("personnalite").textContent = "Majordome sarcastique";
    majModules(Object.keys(MODULE_ZONE).map((m) => ({ module: m, etat: "pret", message: "démo" })), true);
    setInterval(stats, 1000); stats();
    setTimeout(async function boucle() {
      if (!occupe && !document.hidden) await jouer(SCENES[i++ % SCENES.length], false);
      setTimeout(boucle, 2600);
    }, 1800);
  }
  return {
    demarrer,
    demande(texte) {
      if (occupe) return;
      if (!texte) { toast("Dans la démo, Jarvis ne peut pas utiliser ton micro : voici une scène préparée."); jouer(SCENES[i++ % SCENES.length], false); return; }
      jouer({ dit: texte, outils: [["memoire_chercher", "MEMOIRE", "Recherche faite."]], rep: "En démonstration, je joue des scènes préparées. Installe-moi sur ton PC pour que je fasse vraiment tout ça." }, true);
    },
  };
})();

if (DEMO) demo.demarrer(); else connecter();
window.__jarvis = { evenement, act, nbPoints, segments: L.z.length / 2 };
})();
