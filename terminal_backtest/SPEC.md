# Terminal de backtest futures : cahier des charges

Une page web autonome (un seul fichier HTML, publié comme Artifact claude.ai) qui rejoue sans fin 7 stratégies sur
4 marchés de futures à la fois, avec de vraies barres quotidiennes, et qui dit honnêtement lesquelles tiennent.
Public : un trader particulier francophone, non développeur, qui regarde souvent sur téléphone. Toute la page est en
français, en phrases simples.

## 0. Fichiers

Dossier de travail : `/home/user/scalping-telegram-bot/terminal_backtest/`.

Déjà présents, **à ne jamais modifier** :

| Fichier | Rôle |
|---|---|
| `data.json` | `{source, dates[4221], marches[4]: {id, nom, contrat, o[], h[], l[], c[]}}` : barres quotidiennes réelles de NQ, ES, GC, CL (7 juin 2010 → 25 sept. 2026), prix ajustés des changements de contrat |
| `reference.py` | **La définition normative** des indicateurs, des 7 stratégies, du backtest et des passes |
| `expected.json` | Sortie de `reference.py` : `meta`, `signaux`, `cellules`, `long`, `acheter_conserver` |
| `comparatif.json` | Tableau « tes bots » déjà calculé (`lignes[]`) et la liste `conclusions[]` |
| `donnees.py`, `comparatif.py` | Scripts qui ont produit les fichiers ci-dessus |

À produire :

| Fichier | Rôle |
|---|---|
| `src/engine.js` | Moteur pur (aucun accès au DOM). Utilisable dans Node (`module.exports`) et dans la page (`window.BT`) |
| `src/ui.js`, `src/style.css`, `src/template.html` | La page |
| `build.py` | Assemble `terminal.html` : style, données (`data.json`, `comparatif.json`) et scripts en ligne |
| `terminal.html` | Le livrable, au format du « contrat de page » (§ 6) |
| `check_engine.mjs` | Lance `src/engine.js` dans Node et le compare à `expected.json` (§ 3) |
| `check_page.mjs` | Ouvre `terminal.html` avec Playwright et fait les contrôles du § 7 |

## 1. Moteur : porter `reference.py` en JavaScript, ligne à ligne

`reference.py` fait foi. S'il contredit ce document, suis `reference.py` et signale l'écart dans ton rapport.

- **Même ordre d'opérations que le Python** (mêmes boucles, mêmes parenthèses) : les sommes se font dans l'ordre des
  indices, sans somme glissante ni `reduce` réordonné, pour retrouver les mêmes nombres en double précision.
- Chaque stratégie rend `sig[t]` ∈ {−1, 0, +1}, décidé à la clôture de la barre `t` avec les seules barres ≤ `t`.
- Les 7 stratégies, dans cet ordre (identifiant → nom affiché) :

| id | Nom affiché | Règle (voir le code) | Sens |
|---|---|---|---|
| `supertrend` | Supertrend 10-3 | ATR de Wilder 10, ligne à 3 ATR ; toujours en position dans le sens de la ligne | achat / vente |
| `zscore` | Z-score 20 | écart à la moyenne 20 en écarts-types ; entrée à ±1,5, sortie au retour à 0 | achat / vente (contre le mouvement) |
| `dualmom` | Dual momentum | 1re séance du mois : achat si le rendement sur 126 séances est positif et dans les 2 meilleurs des 4 marchés | achat seul |
| `ema_stop` | EMA 20/50 + stop ATR | achat au croisement EMA 20 au-dessus d'EMA 50 ; stop suiveur à 3 ATR 14 sous le plus haut ; sortie aussi si EMA 20 repasse dessous | achat seul |
| `keltner` | Cassure de Keltner | canal EMA 20 ± 2 ATR 10 ; entrée à la cassure du canal, sortie au retour sur l'EMA 20 | achat / vente |
| `stoch` | Stochastique 14-3 | %K 14 et %D 3 ; achat au croisement sous 20, sortie au-dessus de 80 ; symétrique pour la vente | achat / vente (contre le mouvement) |
| `rsi2` | RSI(2) | règle du 2e moteur du Bot 3 en 1 : achat si clôture > moyenne 200 et RSI(2) < 10 ; sortie si clôture > moyenne 5 | achat seul |

- **Exécution** (`backtest` du Python) : la position de la barre `t` est `w[t] = sig[t−1]`, prise à l'**ouverture** de
  `t`. Rendement de la barre : `(1 + w[t−1]·(o[t]/c[t−1] − 1)) · (1 + w[t]·(c[t]/o[t] − 1)) − 1 − frais·|w[t] − w[t−1]|`.
  À plat avant la 1re barre de la fenêtre ; tout est fermé à la clôture de la dernière barre (frais de sortie comptés).
- **Frais** : 2 points de base par ordre (0,0002), sur chaque entrée et chaque sortie ; un retournement = 2 ordres.
  Le moteur accepte un taux par marché (`expected.json` contient aussi le jeu « micro », à vérifier dans
  `check_engine.mjs` mais **non affiché** dans la page).
- **Acheter et conserver** : `sig ≡ +1` dans le même `backtest` (il paie donc ses 2 ordres).
- **Passes** : `n = 252` barres ; `K = (T − 252) // 252 = 15` passes ; passe `p` (0 = la plus récente) :
  `b = T − 252·p`, `a = b − 252`. Les indicateurs sont calculés sur tout l'historique, donc déjà « chauds ».
- **Période longue** : de `a` de la passe la plus ancienne à `T` (20 févr. 2012 → 25 sept. 2026), d'un seul tenant.
- **Mesures** par (stratégie, marché, fenêtre) : `ret`, `trades` (entrées), `dd` (pire baisse de la courbe), `expo`
  (part des barres en position) ; sur la période longue en plus : `cagr`, `sharpe`, `t`, `t_avant_2019`,
  `t_depuis_2019`, `t_depuis_2023` (voir `stats`).
- En plus des signaux, le moteur expose pour le dessin les séries de chaque stratégie (tableaux alignés sur `dates`,
  `NaN` avant qu'elles existent) :
  - `supertrend` : ligne (bande basse finale si achat, haute si vente) et son sens ;
  - `zscore` : moyenne 20, bandes à ±1,5 écart-type, et le z ;
  - `dualmom` : le rendement sur 126 séances du marché (%), et le prix d'il y a 126 séances ;
  - `ema_stop` : EMA 20, EMA 50, niveau du stop quand la stratégie est en position (`NaN` sinon) ;
  - `keltner` : EMA 20, bande haute, bande basse ;
  - `stoch` : %K et %D ;
  - `rsi2` : RSI(2), moyenne 200, moyenne 5.

## 2. Ce que montre la page

Ordre de haut en bas. Sur grand écran (≥ 1100 px) les 4 graphiques sont **côte à côte sur une ligne**.

1. **En-tête** : le nom « Terminal de backtest futures » ; la passe en cours (« Passe 3 sur 15 · 27 sept. 2023 →
   25 sept. 2024 ») ; la stratégie en cours ; les commandes : Lecture / Pause, vitesse (×1, ×4, ×16), « Passe suivante ».
2. **Les 4 graphiques** (NQ, ES, or, pétrole), chacun :
   - titre : nom du marché, contrat, et la stratégie testée ;
   - le prix en **bougies quotidiennes** (252 barres) ;
   - **la stratégie dessinée sur le prix** : ligne du Supertrend verte en achat et rouge en vente ; bandes ; EMA ;
     stop ; pour les oscillateurs (z, stochastique, RSI(2), momentum) une petite bande d'indicateur sous le prix avec
     ses seuils ;
   - **flèches d'entrée et de sortie** à l'ouverture de la barre où l'ordre est exécuté (▲ achat, ▼ vente, ✕ sortie) ;
   - dessous : la **barre de position** (achat, vente, à plat) ;
   - dessous : la **course des courbes** : stratégie contre acheter et conserver, avec les deux pourcentages en direct.
   Les 4 graphiques avancent ensemble, barre après barre.
3. **Tableau de la passe** : lignes = « Acheter et conserver » puis les 7 stratégies ; colonnes = NQ, ES, Or, Pétrole,
   Moyenne. Il se remplit **cellule par cellule** à la fin de chaque stratégie. Une cellule = le rendement de la
   stratégie ; fond vert + « ▲ » si elle bat acheter et conserver sur ce marché, rouge + « ▼ » sinon (jamais la
   couleur seule).
4. **Carte des rendements en 3D** : barres en relief (7 stratégies × 4 marchés), hauteur = rendement de la passe,
   vers le bas si négatif, même couleur vert / rouge que le tableau. Elle tourne lentement ; on peut la faire tourner
   au doigt ou à la souris. Dessinée à la main sur `<canvas>` (projection simple, tri par profondeur), sans librairie.
5. **Classement cumulé** : depuis le début du cycle, pour chaque stratégie et pour « Acheter et conserver » (ligne
   repère, style à part) : rendement moyen par cellule, et « bat le marché n fois sur N ». Trié par rendement moyen.
   Quand deux lignes **échangent leur place**, elles glissent (animation FLIP).
6. **Journal de l'agent** : une ligne par événement, la plus récente en haut, 60 lignes gardées. Exemples :
   « Passe 1 · Supertrend 10-3 sur le NQ : +4,2 % contre +18,8 % pour acheter et conserver. Perdu. » ;
   « Passe 1 terminée : 9 cellules sur 28 battent le marché. » ; « Cycle terminé. Je recommence à la passe 1. »
7. **Verdict sur toutes les années** (fixe, calculé par le moteur au chargement, visible sans attendre l'animation) :
   - une phrase d'en-tête avec la période longue et le nombre de backtests (7 × 4 × 15 = 420) ;
   - tableau : lignes = « Acheter et conserver » + 7 stratégies ; colonnes = NQ, ES, Or, Pétrole (rendement annuel,
     et dessous en petit « t x,xx » et « baisse −xx % ») et « Bat le marché » (n sur 60) ;
   - une pastille par ligne : « tient » si t ≥ 2 sur au moins 2 marchés, « à surveiller » si t ≥ 2 sur 1 marché,
     « rien de mesurable » sinon ; une ligne de légende explique t (« au-dessus de 2, le gain a peu de chances
     d'être dû au hasard »).
8. **Tes bots, à côté** (fixe, depuis `comparatif.json`) : tableau trié par `t` décroissant : stratégie, gain par an
   pour 1 MNQ, t, t depuis 2023, pire baisse, années perdantes (nombre), Bulenox (`bulenox`). Les lignes
   `famille = "tes bots"` sont mises en avant, `"repere"` en style repère. Sous le tableau, la liste
   `conclusions[]` telle quelle (« Ce que ça dit »).
9. **Méthode** (court, en liste) : source des données (`data.source`) et dates ; signal à la clôture, ordre à
   l'ouverture suivante, aucun regard vers le futur ; 2 points de base par ordre ; prix ajustés des changements de
   contrat ; les passes remontent le temps d'un an à chaque fois ; ces stratégies gardent la position plusieurs
   jours, ce qui est interdit sur un compte Bulenox ; un backtest ne garantit rien.

### Déroulé de l'animation

- Au chargement : la passe 1 (la plus récente) démarre seule. Pour chaque stratégie : les 4 graphiques se
  redessinent barre après barre (à ×1 : environ 6 s pour 252 barres), puis les 4 cellules se remplissent l'une après
  l'autre, la carte 3D, le classement et le journal se mettent à jour, courte pause, stratégie suivante.
- Fin de passe : ligne de bilan dans le journal, puis passe suivante (l'année d'avant). Après la passe 15 : bilan du
  cycle, le classement cumulé repart de zéro, et tout recommence à la passe 1. La page tourne ainsi sans fin.
- L'animation est pilotée par `requestAnimationFrame` avec un temps écoulé (pas de dérive si l'onglet est en
  arrière-plan : au retour, on reprend sans rattraper des minutes d'images).
- `prefers-reduced-motion: reduce` : pas de balayage ni de rotation ; chaque stratégie s'affiche d'un coup, la page
  n'avance que par les boutons « Stratégie suivante » / « Passe suivante ».
- **Première image complète** : avant même le premier pas d'animation, les 4 graphiques montrent les bougies de la
  passe 1, le tableau montre ses lignes vides avec la ligne « Acheter et conserver » remplie, et les sections 7 à 9
  sont entièrement remplies.
- Tous les nombres affichés viennent du moteur ou de `comparatif.json` ; aucun nombre écrit en dur dans le HTML.
- Format français : virgule décimale, espace avant « % », signe toujours affiché pour un rendement (« +4,2 % »,
  « −12,7 % » avec le vrai signe moins U+2212), dates « 27 sept. 2023 ».

## 3. `check_engine.mjs` (doit passer avant tout travail d'interface)

`node check_engine.mjs` charge `src/engine.js`, `data.json`, `expected.json` et vérifie :

1. les 28 chaînes de `signaux` : identiques caractère par caractère ;
2. `cellules` (2 jeux de frais × 15 passes × 7 × 4) et `long`, `acheter_conserver` : chaque nombre à 1e-9 près
   (absolu), entiers exacts ;
3. `meta.passes` (a, b, début, fin) identiques.

Il affiche le nombre de valeurs comparées et se termine par le code 0 seulement si tout est identique. En cas
d'écart, il affiche les 10 premiers avec leur chemin.

## 4. Direction visuelle

- Avant d'écrire le moindre code de graphique, charge le skill `dataviz` (outil Skill) et suis-le pour les couleurs
  de séries, les axes et les étiquettes. La carte 3D est une demande explicite de l'utilisateur : garde-la, mais
  le tableau à côté porte les valeurs exactes.
- Un terminal de salle de marché, **sombre d'abord**, avec un thème clair complet (voir § 6). Accent ambre (les
  terminaux de marché historiques), chiffres en police à chasse fixe et `tabular-nums`. Le vert et le rouge sont
  réservés au sens « bat / ne bat pas » et « achat / vente » ; ils ne servent pas d'accent.
- Dense mais lisible : pas de grand bandeau d'accueil, pas d'émojis, pas de dégradé décoratif, pas de coins ronds
  partout. Les panneaux se distinguent par des filets fins.
- Graphiques sur `<canvas>` (netteté sur écran haute densité via `devicePixelRatio`), couleurs lues dans les
  variables CSS et relues quand le thème change.
- Téléphone (400 px) : graphiques en grille 2 × 2 ou en colonne, tableaux dans un conteneur qui défile seul
  horizontalement, aucune barre de défilement horizontale sur la page.

## 5. Qualité du code

- Aucune dépendance au réseau à l'exécution, sauf les polices Google Fonts (avec une pile de repli).
  Pas de librairie graphique : tout est dessiné à la main.
- Données en ligne dans `terminal.html` (`<script type="application/json" id="...">`). Taille finale < 2 Mo.
- Pas de `localStorage` nécessaire. Pas de `alert`, `confirm`, `prompt`, téléchargement ou impression.
- Les commandes sont de vrais `<button>` avec un état de focus visible et un `id` stable.

## 6. Contrat de page de l'Artifact (obligatoire)

- `terminal.html` **ne contient pas** `<!DOCTYPE>`, `<html>`, `<head>` ni `<body>` : la plateforme les ajoute. Le
  fichier commence par `<title>Terminal Backtest Futures</title>`, puis
  `<meta name="claude:viewport-fit-sides" content="cover">`, puis `<style>`.
- Gouttière latérale sur l'enveloppe extérieure : `padding-left: max(16px, env(safe-area-inset-left, 0px))` et
  `padding-right: max(16px, env(safe-area-inset-right, 0px))` ; le remplissage vertical avec `padding-block`.
  Ne touche pas au `padding` de `:root`.
- Thèmes : toutes les couleurs sont des variables définies sur `:root` (ici les valeurs **sombres**, avec
  `color-scheme: dark`), puis redéfinies en clair sous
  `@media (prefers-color-scheme: light) { :root:not([data-theme="dark"]) { ...; color-scheme: light } }` et encore
  sous `:root[data-theme="light"] { ...; color-scheme: light }`. `body` a un `background` explicite pris dans une
  variable. Aucune couleur littérale dans les règles des composants ni dans le JavaScript.
- Scripts externes interdits sauf cdnjs (inutile ici). Feuille de style externe permise : seulement
  `https://fonts.googleapis.com`.
- Pour masquer un élément : l'attribut `hidden`, pas `style.display`.
- Un bandeau collant éventuel utilise `top: env(safe-area-inset-top, 0px)`.
- La page ne doit jamais défiler horizontalement ; `min-width: 0` sur les enfants de grille qui portent du texte ou
  un tableau.

## 7. `check_page.mjs` et critères d'acceptation

`node check_page.mjs` (Playwright est déjà installé : `require('playwright')` / `import('playwright')`,
`chromium.launch()` sans option ; ne lance jamais `playwright install`). Il enveloppe `terminal.html` dans le
squelette `<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,
initial-scale=1, viewport-fit=cover"></head><body>…</body></html>`, l'ouvre en 1440 × 900 et en 400 × 800, en thème
sombre puis clair (`colorScheme`), et vérifie :

1. aucune erreur ni avertissement dans la console, aucune requête réseau refusée hors polices ;
2. pas de défilement horizontal (`document.documentElement.scrollWidth <= innerWidth`) aux deux largeurs ;
3. à 1440 px, les 4 graphiques sont sur une même ligne ;
4. après avoir avancé toute la passe 1 à vitesse ×16 (ou via une fonction de test `window.__terminal.finirPasse()`),
   les 28 cellules du tableau affichent exactement les rendements de `expected.json` (`cellules.demande[0]`), au
   format français à une décimale, et le classement cumulé contient 8 lignes ;
5. le tableau du verdict affiche 8 lignes et des `cagr` égaux à `expected.json` (`long.demande`) ;
6. écrit 4 captures dans `captures/` (bureau et téléphone, sombre et clair), prises après l'étape 4.

Le travail est fini quand `node check_engine.mjs` et `node check_page.mjs` passent tous les deux, et que tu as
regardé toi-même les 4 captures (outil Read) pour corriger ce qui se chevauche, déborde ou est illisible.

## 8. Rapport attendu

En fin de travail, réponds avec : la liste des fichiers créés ; le résultat des deux contrôles (nombre de valeurs
comparées) ; tout écart ou ambiguïté rencontrés avec ce document ; ce qui reste imparfait.
