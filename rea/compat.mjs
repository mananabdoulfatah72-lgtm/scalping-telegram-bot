#!/usr/bin/env node
// Tes bots fonctionneront-ils avec la version de Quantower installee ? Controle par REA, sans rien executer ni copier.
//
// Une commande, sur le PC ou tourne Quantower (Node.js est deja la, REA en a besoin) :
//     node rea/compat.mjs "C:\Quantower"
// Le script trouve la derniere bibliotheque de Quantower (TradingPlatform\<version>\bin\TradingPlatform.BusinessLayer.dll)
// et chaque bot installe (Settings\Scripts\Strategies\<bot>\*.dll), les fait lire par REA (inspect-managed-members :
// lecture statique des noms et signatures), puis verifie :
//   1. chaque appel direct d'un bot vers Quantower existe dans la version installee (sinon : plantage au chargement ou au
//      premier appel, TypeLoadException / MissingMethodException / MissingFieldException) ;
//   2. chaque nom lu par reflexion (rea/reflexion.json) existe (sinon : le bot lit une valeur vide, sans planter).
// Rapport : compat_<date>.md dans le dossier courant. Code de sortie 0 si tout est trouve, 1 sinon.
//
// Autre usage, avec des lectures REA deja faites :
//     node rea/compat.mjs --json bot.json quantower.json [autre.json ...]
// REA : REA_CMD si defini, sinon la commande `rea` si elle est installee, sinon `npx -y rea-agents@6.9.0`.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ICI = path.dirname(fileURLToPath(import.meta.url));
const ESPACE = "TradingPlatform.";
const JETON = /\b(?:class|valuetype):\d+ \(([^()]*)\)/g;
const VERSION_REA = "6.9.0";

const norm = (t) => {
  if (t == null) return null;
  let prec;
  do { prec = t; t = t.replace(JETON, "$1"); } while (t !== prec);
  return t;
};
const sansGenerique = (n) => (n || "").replace(/<.*>$/, "");
const cle = (a, b) => `${a}\u0000${b}`;
const sig = (s) => JSON.stringify([norm(s.return_type), (s.parameter_types || []).map(norm)]);

function lire(f) {
  return JSON.parse(fs.readFileSync(f, "utf8")).normalized_result;
}

class Plateforme {
  constructor(fichiers) {
    this.types = new Set(); this.methodes = new Map(); this.champs = new Map(); this.base = new Map();
    for (const f of fichiers) {
      const n = lire(f);
      const parJeton = new Map(n.types.map((t) => [t.token, t.full_name]));
      for (const t of n.types) {
        this.types.add(t.full_name);
        if (parJeton.has(t.extends_token)) this.base.set(t.full_name, parJeton.get(t.extends_token));
      }
      for (const m of n.methods) {
        const k = cle(m.declaring_type, m.name);
        if (!this.methodes.has(k)) this.methodes.set(k, []);
        this.methodes.get(k).push(sig(m.signature));
      }
      for (const c of n.fields) {
        const k = cle(c.declaring_type, c.name);
        if (!this.champs.has(k)) this.champs.set(k, []);
        this.champs.get(k).push(JSON.stringify(norm(c.signature.field_type)));
      }
    }
  }
  chaine(t) {
    const vus = [];
    while (t && !vus.includes(t)) { vus.push(t); t = this.base.get(t); }
    return vus;
  }
  membre(t, nom, genre) {
    const table = genre === "methode" ? this.methodes : this.champs;
    for (const x of this.chaine(t)) {
      const d = table.get(cle(x, nom));
      if (d) return d;
    }
    return null;
  }
  aLeNom(t, nom) {
    const types = new Set();
    const chaine = t ? new Set(this.chaine(t)) : null;
    for (const table of [this.methodes, this.champs]) {
      for (const k of table.keys()) {
        const [ty, n] = k.split("\u0000");
        if ((n === nom || n === `get_${nom}`) && (!chaine || chaine.has(ty))) types.add(ty);
      }
    }
    return [...types].sort();
  }
}

function controler(botJson, plat, reflexion) {
  const n = lire(botJson);
  const ok = [], pb = [];
  for (const r of n.member_refs) {
    const parent = sansGenerique(r.parent_name);
    if (!parent.startsWith(ESPACE)) continue;
    const s = r.signature, genre = s.kind === "field" ? "champ" : "methode";
    const attendu = genre === "champ" ? JSON.stringify(norm(s.field_type)) : sig(s);
    if (!plat.types.has(parent)) { pb.push(["type absent", parent, r.name, attendu, null]); continue; }
    const defs = plat.membre(parent, r.name, genre);
    if (!defs) pb.push(["membre absent", parent, r.name, attendu, null]);
    else if (!defs.includes(attendu)) pb.push(["signature differente", parent, r.name, attendu, defs]);
    else ok.push([parent, r.name]);
  }
  const reflOk = [], reflPb = [];
  for (const e of reflexion) (plat.aLeNom(e.type, e.membre).length ? reflOk : reflPb).push(e);
  return { ok, pb, reflOk, reflPb };
}

function rapport(nomBot, res) {
  const L = [`## ${nomBot}`, "",
    `- Appels directs vers Quantower : ${res.ok.length + res.pb.length}, trouves ${res.ok.length}, **problemes ${res.pb.length}**.`,
    `- Noms lus par reflexion : ${res.reflOk.length + res.reflPb.length}, trouves ${res.reflOk.length}, **absents ${res.reflPb.length}**.`, ""];
  if (res.pb.length) {
    L.push("Ce qui fera planter le bot :", "", "| Probleme | Type | Membre | Attendu par le bot | Present dans Quantower |", "|---|---|---|---|---|");
    for (const [q, t, m, a, d] of res.pb) L.push(`| ${q} | \`${t}\` | \`${m}\` | \`${a}\` | \`${d ? d.join(" ; ") : "-"}\` |`);
    L.push("");
  }
  if (res.reflPb.length) {
    L.push("Ce que le bot lira vide, sans planter :", "", "| Type | Nom | Sert a |", "|---|---|---|");
    for (const e of res.reflPb) L.push(`| \`${e.type || "n importe lequel"}\` | \`${e.membre}\` | ${e.pour || ""} |`);
    L.push("");
  }
  if (!res.pb.length && !res.reflPb.length) L.push("Tout est trouve.", "");
  return L.join("\n");
}

function commandeRea() {
  if (process.env.REA_CMD) return [process.env.REA_CMD];
  const essai = spawnSync("rea", ["--version"], { shell: process.platform === "win32", encoding: "utf8" });
  return essai.status === 0 ? ["rea"] : ["npx", "-y", `rea-agents@${VERSION_REA}`];
}

function lireAvecRea(dll, dossierSortie) {
  const [cmd, ...pre] = commandeRea();
  const q = (a) => (process.platform === "win32" ? `"${a}"` : a);
  const sortie = path.join(dossierSortie, `${path.basename(dll, ".dll")}.json`);
  const r = spawnSync(q(cmd), [...pre, "inspect-managed-members", q(dll), "--json"],
    { shell: process.platform === "win32", encoding: "utf8", maxBuffer: 1 << 30 });
  if (r.status !== 0) throw new Error(`REA n'a pas pu lire ${dll} : ${(r.stderr || "").slice(-400)}`);
  fs.writeFileSync(sortie, r.stdout);
  return sortie;
}

function trouver(base) {
  const tp = path.join(base, "TradingPlatform");
  if (!fs.existsSync(tp)) throw new Error(`Pas de dossier TradingPlatform dans ${base}`);
  const versions = fs.readdirSync(tp).map((v) => path.join(tp, v, "bin", "TradingPlatform.BusinessLayer.dll"))
    .filter((f) => fs.existsSync(f)).sort((a, b) => fs.statSync(b).mtimeMs - fs.statSync(a).mtimeMs);
  if (!versions.length) throw new Error(`TradingPlatform.BusinessLayer.dll introuvable sous ${tp}`);
  const strat = path.join(base, "Settings", "Scripts", "Strategies");
  const bots = fs.existsSync(strat)
    ? fs.readdirSync(strat).flatMap((d) => { const p = path.join(strat, d); return fs.statSync(p).isDirectory() ? fs.readdirSync(p).filter((f) => f.toLowerCase().endsWith(".dll")).map((f) => path.join(p, f)) : []; })
    : [];
  return { plateforme: versions[0], bots };
}

function principal(argv) {
  const reflexion = JSON.parse(fs.readFileSync(path.join(ICI, "reflexion.json"), "utf8"));
  const date = new Date().toISOString().slice(0, 10);
  let morceaux = [], probleme = false, entete;
  if (argv[0] === "--json") {
    const [bot, ...plats] = argv.slice(1);
    if (!bot || !plats.length) { console.log("Usage : node rea/compat.mjs --json bot.json quantower.json [autre.json ...]"); return 2; }
    const res = controler(bot, new Plateforme(plats), reflexion);
    probleme = res.pb.length > 0 || res.reflPb.length > 0;
    entete = `# Compatibilite des bots avec Quantower (${date})\n\nLectures REA : ${[bot, ...plats].map((f) => path.basename(f)).join(", ")}\n`;
    morceaux.push(rapport(path.basename(bot), res));
  } else {
    if (!argv[0]) { console.log('Usage : node rea/compat.mjs "C:\\Quantower"   (dossier d\'installation de Quantower ou d\'Optimus Flow)'); return 2; }
    const { plateforme, bots } = trouver(argv[0]);
    const tmp = fs.mkdtempSync(path.join(process.env.TEMP || process.env.TMPDIR || "/tmp", "rea-compat-"));
    console.log(`Quantower : ${plateforme}\nBots : ${bots.length ? bots.join(", ") : "aucun trouve"}\nLecture par REA (quelques secondes par DLL)...`);
    const plat = new Plateforme([lireAvecRea(plateforme, tmp)]);
    entete = `# Compatibilite des bots avec Quantower (${date})\n\nBibliotheque lue : \`${plateforme}\`\n`;
    for (const b of bots) {
      const res = controler(lireAvecRea(b, tmp), plat, reflexion);
      probleme = probleme || res.pb.length > 0 || res.reflPb.length > 0;
      morceaux.push(rapport(path.basename(b), res));
    }
  }
  const texte = [entete, ...morceaux, probleme
    ? "**A regler avant d'ouvrir le marche.** Un appel direct en defaut : relance l'installateur des bots (il les recompile contre "
      + "cette version), puis refais ce controle ; si le defaut reste, le code du bot doit etre adapte. Un nom lu par reflexion absent : "
      + "le code du bot doit etre adapte (le bot lirait une valeur vide). Dans les deux cas, garde le bot arrete (fichier STOP) d'ici la."
    : "Rien a faire : tes bots trouvent tout ce qu'ils utilisent dans cette version de Quantower."].join("\n");
  const f = `compat_${date}.md`;
  fs.writeFileSync(f, texte + "\n");
  console.log(texte + `\n\nRapport ecrit : ${path.resolve(f)}`);
  return probleme ? 1 : 0;
}

process.exitCode = principal(process.argv.slice(2));
