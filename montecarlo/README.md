# Monte Carlo du bot sur Bulenox 50K (11 octobre 2026)

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
