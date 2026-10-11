# Monte Carlo du bot sur Bulenox 50K (11 octobre 2026)

Page : `monte_carlo_bulenox.html` (artefact). La version 2 (plus bas) met le moteur du bot dans la page.

Demande de l'utilisateur : une simulation Monte Carlo visuelle du bot 3 en 1, avec ses réglages Bulenox, et toutes ses
données. Page : `monte_carlo_bulenox.html` (publiée en artefact).

## Méthode

- **Un achat simulé** = 24 mois (504 séances) de vraies séances du bot, tirées au hasard par **blocs de 21 séances
  consécutives** (un mois), pour garder les séries de bons et de mauvais jours.
- **Le moteur est celui du bot** : `moteur_mc.parcours_mc` reprend `vague4/moteur4._parcours4` ligne pour ligne. Chaque
  séance passe par `seance4` sans changement : nuit, zone minute par minute, plancher touché dans la séance, limite du
  jour, frein MES, plafond du jour. La seule différence : la s-ième séance du parcours est la vraie séance `idx[s]`, et
  le solde est écrit séance par séance.
- **Réglages** (README de `bot3en1`, `vague10/budget30.py`) :
  - challenge : +3 000 $, perte max 2 500 $ en fin de journée bloquée à +100 $, limite du jour 1 100 $ ;
  - Master : 10 jours de trading, meilleur jour ≤ 40 % du gain du cycle, 52 600 $ à garder, retraits de 1 000 à
    1 500 $, arrêt après 3 retraits (compte réel, non simulé) ;
  - bot : zone 1 MNQ (sur MES sous 1 750 $ de coussin), RSI(2) de nuit 1 MES, pas de zone les jours de la Fed,
    plafond de 500 $/jour sur le Master ;
  - prix : 19,25 $ + 148 $ d'activation.
- **9 scénarios de 4 000 achats** (graines fixes) :
  - **marché** : toute l'histoire (2012 - sept. 2026), régime récent (2023 - sept. 2026), stress 2025 (mois de 2025
    seulement) ;
  - **filtre delta** : aussi bon qu'en 2026 (10 tirages simulés, comme les vagues 9 à 11), deux fois plus faible (même
    part écartée, corrélation divisée par deux), aucun.

## Contrôles (`test_montecarlo.py`)

1. Sur un chemin qui suit le vrai calendrier, `parcours_mc` redonne exactement `moteur4.parcours4` (issues et retraits
   séance par séance) sur 300 achats, avec et sans filtre.
2. Traces cohérentes : phase 1 puis 2, solde au-dessus du plancher tant que le compte vit, retraits égaux à la somme
   reçue.
3. Chemins tirés par blocs de séances consécutives, dans le bon groupe.

**La longueur des blocs ne change presque rien** (5, 21, 63 ou 126 séances, toute l'histoire, filtre fort : achats
perdants 27, 23, 20 et 23 %). Tirer seulement dans 2023-2024 redonne le rejeu de la vague 11 (validé au mois 3,6
contre 3,2, achats perdants 6 % contre 8 %).

## Résultats : `montecarlo.txt`

| Marché / filtre | Validé (mois médian) | Challenge perdu | 3 retraits | Net médian 24 mois | Achats perdants |
|---|---|---|---|---|---|
| Toute l'histoire / aussi bon qu'en 2026 | 89 % (4,0) | 11 % | 64 % | +3 709 $ | 24 % |
| Toute l'histoire / deux fois plus faible | 82 % (4,5) | 17 % | 46 % | +2 433 $ | 38 % |
| Toute l'histoire / aucun | 67 % (4,5) | 32 % | 28 % | −19 $ | 58 % |
| Récent / aussi bon qu'en 2026 | 93 % (4,7) | 6 % | 69 % | +3 741 $ | 17 % |
| Récent / deux fois plus faible | 87 % (5,3) | 11 % | 48 % | +2 583 $ | 32 % |
| Récent / aucun | 70 % (5,6) | 28 % | 27 % | −19 $ | 55 % |
| Stress 2025 / aussi bon qu'en 2026 | 50 % (6,2) | 44 % | 5 % | −19 $ | 85 % |
| Stress 2025 / deux fois plus faible | 38 % (6,7) | 58 % | 2 % | −19 $ | 93 % |
| Stress 2025 / aucun | 7 % | 93 % | 0 % | −19 $ | 100 % |

**Lecture :**
- **Le filtre décide presque tout.** S'il est réel, environ 3 achats sur 4 rapportent de l'argent. S'il ne vaut rien,
  plus d'un achat sur deux perd.
- **Le régime récent valide plus lentement que les achats de 2023-2024** (4,7 mois contre 3,2). Il mélange les mois de
  2025 et de janvier 2026, durs pour le bot.
- **Les gains du bot sont concentrés** (avril 2025 : +6 393 $ à lui seul). Un chemin qui ne tire pas ces mois-là
  avance lentement. C'est pourquoi le stress 2025 est si mauvais alors que l'année 2025 entière a gagné ~9 900 $.

## Version 2 : le moteur du bot dans la page (11 octobre 2026)

Demande de l'utilisateur : une page encore plus complète. La page fait maintenant tourner le moteur elle-même :
l'utilisateur règle le marché (période), le filtre, le frein, le plafond, les règles du compte (objectif, perte
maximale, somme à garder, retraits, jours, règle des 40 %, arrêt ou suite après 3 retraits), le nombre d'achats et la
longueur des blocs, et voit des milliers d'achats recalculés en ~0,2 s.

**Comment c'est exact :**
1. `tables.py` rejoue à l'avance chaque séance du 3 janvier 2012 au 25 septembre 2026 avec `moteur4.seance4`
   (inchangé, limite du jour 1 100 $), pour les 21 tirages du filtre (10 aussi bons qu'en 2026, 10 deux fois plus
   faibles, 1 sans filtre) et 12 combinaisons :
   - position de nuit tenue ou non en entrant ;
   - zone sur MNQ ou MES ;
   - plafond 0, 500 ou 750 $.
   Pour chacune : le gain, le pire point de la séance (trouvé par bisection sur le plancher : la séance est perdue si
   et seulement si plancher − solde ≥ pire point), le jour de trade et la position voulue pour la nuit.
2. `moteur_jour.py` refait `parcours_mc` en lisant ces tables. `test_v2.py` : **5 040 achats sur 5 040 identiques**
   au moteur minute par minute (21 tirages, 4 réglages de frein et de plafond, chemins tirés au hasard).
3. `moteur_jour.js` est le port JavaScript ligne pour ligne. `test_js.mjs` : **600 vecteurs sur 600 identiques** au
   moteur Python.
4. Les tables sont dédoublonnées (1,8 résultat distinct par séance en moyenne sur les 21 tirages) : 1,2 Mo.

**Pourquoi 21 tirages :** avec seulement 3 tirages, le scénario « stress 2025 » donnait 5 % d'achats rentables au lieu
de 15 %. Sur une seule année, le résultat dépend énormément des trades que le filtre simulé écarte. Avec le moteur
exact, selon le tirage, on obtient de 0 % à 64 % (`fort` 0 à 9 : 8, 4, 2, 34, 64, 0, 9, 2, 24, 11 %). Avec les
mêmes 10 tirages que le moteur exact, la page redonne les 9 scénarios de contrôle (bouton dans la page).

**Ce qu'ajoute la page :**
- machine animée avec curseur de temps et vitesse ;
- relief 3D (three.js) : la diffusion du challenge entre ses deux murs absorbants, les dents de scie du Master,
  l'escalier de l'argent ;
- calendrier si l'achat est fait le 12 octobre 2026 ;
- étapes, temps entre retraits, issues sur 100 achats ;
- risque : mois de la mort du compte, passage le plus près du plancher, plus longue période sans nouveau plus haut,
  pire baisse ;
- carte frein × plafond, recalculée pour les réglages choisis (avec un avertissement : choisir la meilleure case sur
  les mêmes données est de l'optimisation sur le passé) ;
- convergence du Monte Carlo et contrôle contre le moteur exact ;
- épingle pour comparer deux réglages.

Construction : `python3 tables.py && python3 test_v2.py && python3 construire_v2.py && node test_js.mjs`.
