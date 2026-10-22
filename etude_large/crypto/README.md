# Vague bitcoin : la cassure des 30 premières minutes, confirmée sur des années jamais vues puis réglée en walk-forward (règles fixées le 22 octobre 2026, avant le téléchargement des données)

## Pourquoi

Dans la partie A de l'étude large, un seul essai approche du seuil : **A3b, cassure des 30 premières minutes sur
BITO** (ETF du future bitcoin, donc MBT), t net +1,64 (octobre 2021 - 2022) et +1,87 (2023 - 2026), t avant frais +2,55
et +3,06. Le seuil fixé était 2,0. L'utilisateur demande d'en ajuster les paramètres.

Régler ces paramètres sur 2021 - 2026 rendrait le résultat faux : ces années ont déjà été regardées. Mais le bitcoin
s'échange depuis bien avant l'ETF. Coinbase donne gratuitement ses barres de 5 minutes depuis 2017 : **2017 - septembre
2021 n'a jamais été vu par aucun test de cette stratégie**. On peut donc d'abord la confirmer sur ces années, puis la
régler honnêtement, en walk-forward.

## Données

Coinbase Exchange, BTC-USD et ETH-USD, barres de 5 minutes, 2017 - 20 octobre 2026 (`donnees_libres/crypto.py`, sans
clé ; secours Binance). Coinbase est l'une des bourses du prix de référence des futures bitcoin de la CME. Séance de
9 h 30 à 16 h (New York), les jours de bourse américaine complets (calendrier de la partie A, sans les demi-séances ;
avant 2016, les jours ouvrés hors fêtes de la bourse).

**Frais** (prudents) : Micro Bitcoin (MBT, 0,1 BTC, tick de 5 $ soit 0,50 $), commission de **2,50 $ par ordre** (les
micros crypto paient plus de frais CME que les micros d'indices), plus 1 tick à l'entrée et 1 à la sortie : 6 $ par
aller-retour. Exprimés en points de base **au prix du 20 octobre 2026** : la question est de savoir si la règle marche
si on la trade aujourd'hui (le MBT n'existait pas avant mai 2021 et le bitcoin valait 10 à 100 fois moins).
Sensibilité : frais doublés. ETH : le Micro Ether (0,1 ETH, environ 400 $) coûte plus de 1 % par aller-retour et
l'Ether standard (50 ETH) est trop gros pour un compte de 50 000 $ : **ETH est seulement descriptif**.

**Périodes** : P0, **jamais vue** = 3 janvier 2017 - 30 septembre 2021 ; P1, déjà vue (BITO) = 1er octobre 2021 -
20 octobre 2026.

## Tests

1. **Confirmation, règle inchangée** : A3b exactement comme dans la partie A (plus haut et plus bas de 9 h 30 - 10 h,
   première clôture de 5 minutes au-delà de 10 h à 15 h 55, stop à l'autre extrême, à plat à 16 h), sur BTC, P0.
   **Confirmée si t net ≥ 2,0 sur P0.**
   Contrôle des données : sur P1, corrélation des séances Coinbase / BITO ≥ 0,7.
2. **Réglage honnête** : 24 variantes de la cassure sur BTC :
   - durée du range : 15, 30 ou 60 minutes ;
   - stop : l'autre extrême du range, ou son milieu ;
   - dernière entrée : 12 h ou 15 h 30 ;
   - sortie : 16 h, ou objectif de 2 fois la hauteur du range (sinon 16 h).

   Walk-forward : pour chaque année Y de 2018 à 2026, on prend la variante qui a le meilleur t net sur 2017 … Y − 1, et
   on la joue en Y. **Retenue si** le t net de la série hors échantillon 2018 - 2026 est ≥ 2,0, avec un gain positif
   sur sa partie P0 (2018 - septembre 2021) et sur P1.
   Pour information : la meilleure variante sur tout 2017 - 2026 (choisie après coup, donc gonflée) et la règle fixe sur
   2018 - 2026.
3. **Placebo d'heure** (descriptif) : la même règle fixe, avec un range de 30 minutes qui commence à minuit, 3 h
   (ouverture de Londres), 6 h, 12 h et 13 h (New York) et une fenêtre de 6 h 30. Si la cassure de 9 h 30 ne fait pas
   mieux que ces heures-là, l'effet n'est pas lié à l'ouverture américaine.
4. **Seulement si 1 ou 2 réussit** : complément de la zone (critères de la partie C : corrélation < 0,3 avec la zone du
   bot, Sharpe de zone + bitcoin à risque égal plus haut que la zone seule sur P1), puis challenges (moteur de la partie
   D, zone + 1 MBT).

## Décision (fixée maintenant)

La cassure du bitcoin entre au bot, d'abord en argent virtuel, seulement si le test 1 **ou** le test 2 réussit,
**et** si elle remplit les critères de complément du test 4. Sinon, elle n'y entre pas, quel que soit le meilleur
réglage trouvé après coup.

## Limites écrites d'avance

- Le comptant n'est pas le future : le MBT suit le comptant, avec une prime qui bouge lentement, et ferme une heure par
  jour (17 h - 18 h), en dehors de la fenêtre étudiée.
- Les frais du MBT chez les prop firms ne sont pas connus avec précision : d'où la sensibilité à frais doublés.
- Certaines prop firms limitent ou interdisent les futures crypto : à vérifier avant tout essai.
