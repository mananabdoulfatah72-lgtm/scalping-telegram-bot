# Machine évolutive v6 : finir le challenge depuis 50 000 $ avec un plancher à 49 000 $ (règles fixées le 2 novembre 2026, avant tout calcul)

## Demande de l'utilisateur (2 novembre 2026)

« lance la machine évolutive, explore, analyse, calcule, étudie des nouvelles variantes, des nouveaux atouts, des filtres…
lance une machine, des vagues, des tournois et envoie les plus robustes ».

Situation du compte le 2 novembre au soir : un trade manuel +700 $ (compte à environ +1 500 $), puis le bot touche la
limite du jour (−1 005 $), puis un trade manuel −700 $. Solde ≈ 50 000 $, **plancher monté à 49 000 $ pendant la séance**.

## Ce qui change par rapport aux simulations d'avant : la vraie règle du compte

Le plancher est monté à 49 000 $ pendant la séance (plus haut ≈ 51 500 $ − 2 500 $) : le compte est en **Option 1**
(drawdown suiveur en temps réel sur le plus haut solde **latent**, pas en fin de journée). Toutes les simulations d'avant
(audit, parties I à Q) supposaient un suivi en fin de journée. Ici :

- plancher = min(plus haut − 2 500 $, 50 100 $), plus haut = plus haut **latent** (gains ouverts compris), minute par minute ;
- départ : solde 50 000 $, plus haut 51 500 $ (plancher 49 000 $), objectif 53 000 $ (le bot ferme tout à 53 050 $),
  **8 séances** (3 au 12 novembre 2026) ;
- dans une minute : le côté défavorable (plus bas d'un achat) est testé avant le côté favorable (variante « pessimiste »
  en contrôle de robustesse : favorable d'abord, donc plancher remonté avant le creux) ;
- gains au prix d'aujourd'hui (points × 28 500 / prix d'entrée), 3 $ de frais par MNQ aller-retour, limite du jour avec
  1 point de glissement (comme `audit/risque.py`).

## Les trades de base

Ceux du bot actuel (zone + C2 + Q1, `Bot3en1.Replay`, 2011-01 → 2026-10, 1 744 trades, sans le filtre delta, comme
l'audit), rejoués minute par minute sur les vraies barres du NQ. Largeur de bande d'un trade = référence × σ du contrôle
(moyenne des 14 séances d'avant, comme le moteur).

## Le génome (gènes et valeurs, fixés maintenant)

Gestion :
- T taille : 1 à 6 MNQ ; L limite du jour : 300, 400, 500, 600, 700, 800, 900, 1 000 $ ;
- G garde-plancher : non, ou limite du jour ramenée chaque jour à (solde − plancher − marge), marge 150 ou 300 $ ;
- S stop par trade, en largeurs de bande au-delà du niveau cassé : aucun, 0,5, 1, 1,5 ;
- P objectif par trade, en largeurs de bande depuis l'entrée : aucun, 1, 2, 3 ;
- B stop au prix d'entrée après un gain latent de : jamais, 1, 2 largeurs ;
- R verrou de gain : jamais, ou sortie si la moitié du gain maximal est rendue après un gain d'au moins 1 ou 2 largeurs ;
- N trades par jour au plus : 1, 2, sans limite ; J arrêt de la journée après un trade gagnant : non / oui ;
- O objectif du jour (arrêt dès que la journée atteint) : aucun, 500, 750, 1 000, 1 500 $.

Filtres d'entrée (le trade n'est pas pris ; les trades suivants du rejeu restent, comme `audit/risque.py`) :
- F1 dépassement minimum : 0, 0,1, 0,25 ; F2 dépassement maximum : aucun, 1,5, 1 ;
- F3 dernière entrée : 15 h 30, 15 h, 14 h, 13 h (New York) ; F4 première entrée : 10 h, 10 h 30 ;
- F5 régime : toutes les séances, ou seulement σ du jour au-dessus (ou en dessous) de sa médiane sur 250 séances ;
- F6 écart d'ouverture |ouverture − veille| en largeurs du contrôle de 10 h : tous, < 1, ≥ 0,5.

Pas de gène sans mécanisme (jour de la semaine, sens seul, mois…).

## Score, périodes, vagues, tournoi

- Fenêtres : un challenge de 8 séances part de chaque séance. **Entraînement** : départs 2011 → 2019 ;
  **tournoi** : 2020 → 2023 ; **coffre** : 2024 → octobre 2026, ouvert une seule fois pour les finalistes.
- Score = P(réussite) − 0,5 × P(échec) (un échec coûte un nouveau challenge ; un compte encore en vie au 12 novembre
  peut continuer).
- Témoins : (a) le bot tel quel, 4 MNQ, limite 1 000 $ ; (b) 6 MNQ, 1 000 $ ; (c) prudent, 2 MNQ, 500 $.
- **Vagues** (algorithme génétique, 6 graines × 40 générations × 120 génomes, sélection par tournoi de 3, croisement
  uniforme, mutation d'un pas) : vague 1 gestion seule, vague 2 filtres seuls (gestion du témoin a), vague 3 tout.
  Score d'entraînement pénalisé de 0,5 point par gène qui n'est pas à sa valeur de base (moins de règles à score égal).
- **Tournoi** : les 32 meilleurs génomes distincts de toutes les vagues, en élimination directe sur 2020 → 2023
  (même fenêtres pour les deux, le meilleur score passe, à égalité le plus simple). Les 4 derniers vont aux contrôles.
- **Contrôles de robustesse** (tous obligatoires pour être « retenu ») :
  1. bat le meilleur témoin sur 2020 → 2023 ;
  2. voisins : chaque gène changé d'un pas garde au moins 90 % du score (entraînement + tournoi) ;
  3. pessimiste (favorable d'abord) + 1 tick de glissement à chaque sortie : bat toujours le meilleur témoin ;
  4. la zone garde son avantage pour le compte Master : t des journées (1 MNQ, même gestion) ≥ 3 sur 15 ans ;
  5. coffre 2024 → 2026 : bat le meilleur témoin (ouvert une fois, résultat publié quel qu'il soit).
- Descriptif, pas un test : les finalistes sur avril → octobre 2026 avec le vrai delta (`f_c2q1`).
- Nombre total de génomes évalués publié avec les résultats.
