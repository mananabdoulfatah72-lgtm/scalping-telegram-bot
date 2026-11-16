# Usine à stratégies : règles fixées avant tout calcul (16 novembre 2026)

Demande de l'utilisateur : appliquer la méthode de l'article « La bonne façon d'utiliser Fable 5.2 » (usine à stratégies,
4 portes de validation, tableau de bord, brief du matin, couche de risque) pour l'aider à sauver son compte Master Bulenox
50K. Situation au 16 novembre 2026 : marge de 700 $ au-dessus du plancher.

Ces règles sont écrites et commitées **avant** le premier calcul. L'historique git le montre.

## Partage du travail (règle 3 de l'article)

- Le moteur (`moteur.py`, compilé avec numba) fait tous les calculs. Il donne la même réponse à chaque fois.
- Claude choisit les idées, écrit les règles et lit les résultats. Il ne calcule aucun résultat lui-même et n'invente aucun
  chiffre. Si une donnée manque, il le dit.
- **QuantPilot**, le labo proposé par l'article, n'est pas utilisé :
  - il trade de la crypto (Hyperliquid, Binance, Bybit), pas les futures CME du compte Bulenox ;
  - il n'est pas connecté à cette session : sa connexion demande le compte de l'utilisateur.

## Données

- Minutes du NQ, séance de New York (9 h 30 → 16 h), du 3 janvier 2011 à la dernière séance disponible (13 novembre 2026
  au moment d'écrire ces règles) :
  - `intraday/donnees/nasdaq100_1min.csv.gz` (branche `claude/keen-babbage-r686cl`) jusqu'au 23 septembre 2025 ;
  - puis `zone/robot/nq_1min.csv.gz` (main, mis à jour chaque soir par le robot zone).
- Faux prix corrigés par la règle de `bilan_challenge/st_detail.py` (branche `claude/peaceful-cerf-8dowsi`) : une minute à
  plus de 300 points et à plus de 1 % de la clôture d'avant et de sa propre clôture. Un seul cas connu : le 30 octobre 2026
  à 15 h 03.
- **Séance complète** : première et dernière minute présentes, au moins 370 minutes. On ne trade que les séances
  complètes. Une minute absente reprend la clôture d'avant.
- **Aucune position la nuit** (règle Bulenox) : tout est à plat à 16 h au plus tard.

## Mesure : chaque barre, pas chaque trade (comme l'article)

- Position sur chaque minute : 1 (achat), −1 (vente) ou 0 (à plat).
- Rendement net d'une minute = position × rendement log − frais, en deux parties :
  - l'écart d'ouverture de la minute (ouverture / clôture de la minute d'avant), tenu par la position d'avant ;
  - la minute elle-même (clôture / ouverture), tenue par la position prise à l'ouverture.
  Une entrée à la clôture d'une minute (zone, ORB…) tient les deux parties de la minute suivante. Une entrée à
  l'ouverture d'une minute (Supertrend) ne tient que la seconde.
- **Frais** : 3 $ par aller-retour pour 1 MNQ au prix d'aujourd'hui (28 500 points), soit 2,63 × 10⁻⁵ par côté.
- **Mesure de chaque porte** : le profit factor des rendements nets par minute = somme des minutes gagnantes / somme des
  minutes perdantes (en valeur absolue).
- **Dollars** (portes 3 et 5) : 1 MNQ au prix d'aujourd'hui, soit 57 000 $ × rendement net.

## Les idées (étape 2 de l'article : l'avantage en une phrase, et qui perd en face)

| # | Idée | L'avantage | Qui perd en face | Grille (réglages testés) |
|---|---|---|---|---|
| 1 | **Zone de bruit** (le Bot 3 en 1 sans ses filtres) | Quand le prix sort de sa bande de bruit habituelle, le mouvement continue plus souvent qu'il ne revient | Ceux qui vendent la cassure, et les teneurs de marché qui couvrent leur gamma en suivant le mouvement | largeur k ∈ {0,6 ; 0,8 ; 1,0 ; 1,2 ; 1,4} × jours de moyenne ∈ {7, 10, 14, 20, 30} : 25 (le bot : 1,0 et 14) |
| 2 | **Supertrend NQ** (bougies de 5 min) | Un jour de tendance, le mouvement court terme se prolonge | Les apporteurs de liquidité qui vendent la hausse un jour de tendance | ATR ∈ {7, 10, 14, 20, 30} × multiple ∈ {2 ; 2,5 ; 3 ; 3,5 ; 4} : 25 (le bot : 10 et 3) |
| 3 | **Cassure du range d'ouverture** (ORB) | Le déséquilibre des ordres de l'ouverture se prolonge dans la journée | Ceux qui vendent la cassure du range d'ouverture | durée du range ∈ {5, 10, 15, 30, 45, 60} min × dernière entrée ∈ {11 h, 12 h, 13 h 30, 15 h} : 24 |
| 4 | **Momentum de la première demi-heure** (Gao, Han, Li, Zhou 2018) | Le sens du début de séance prédit celui de la fin de séance | Les fonds et ETF à levier qui rééquilibrent en fin de séance quel que soit le prix | fin du signal ∈ {10 h, 10 h 30, 11 h} × référence ∈ {clôture de la veille, ouverture} × début de la position ∈ {15 h, 15 h 30, 15 h 45} : 18 |
| 5 | **Cassure de la veille** | Le plus haut et le plus bas de la veille concentrent des stops dont le déclenchement prolonge le mouvement | Les porteurs de ces stops | marge ∈ {0 ; 0,1 ; 0,2 ; 0,3 %} × dernière entrée ∈ {12 h, 15 h} × sortie ∈ {retour dans le range, fin de séance} : 16 |
| 6 | **Fade du gap d'ouverture** | Un écart de nuit en partie excessif se referme en début de séance | Ceux qui achètent ou vendent à l'ouverture sur les nouvelles de la nuit | seuil ∈ {0,3 ; 0,5 ; 0,8 ; 1,0 %} × durée maximale ∈ {30, 60, 120 min} : 12 |
| 7 | **Mouvement de fin de séance** | Les ETF à levier et les vendeurs d'options achètent la hausse (vendent la baisse) du jour en fin de séance | Eux, qui paient l'impact de ces ordres forcés | début ∈ {14 h 30, 15 h, 15 h 30} × seuil ∈ {0 ; 0,25 ; 0,5 ; 1,0 %} : 12 |

**Non testables avec les données du dépôt** (on le dit, on ne devine pas) :

| # | Idée | Pourquoi |
|---|---|---|
| 8 | Delta / order flow (filtre H1 du bot) | Transactions disponibles seulement d'avril à octobre 2026, pas 4 ans |
| 9 | Murs d'options, gamma des teneurs de marché | Pas d'historique d'options suffisant |
| 10 | La nuit (achat 18 h, vente 9 h 30) | Le fichier n'a que la séance de New York ; la nuit du projet est lue sur un CFD |

La rotation NQ / ES a déjà été testée sans résultat (`paires/` de la recherche) : elle n'est pas relancée.

### Règles exactes de chaque idée (heures de New York, minute 0 = 9 h 30)

1. **Zone** (`zone_brute` de `chantier/inactivite.py`, branche `claude/loving-mccarthy-u21aw6`, recodée) :
   - contrôles aux minutes 30, 60, …, 360 (10 h à 15 h 30) ;
   - bruit au contrôle m = moyenne, sur les `jours` séances complètes précédentes, de |clôture(m) / ouverture − 1| ;
   - veille = clôture de la dernière séance complète du même contrat (pas de trade sinon) ;
   - haut = max(ouverture, veille) × (1 + k × bruit) ; bas = min(ouverture, veille) × (1 − k × bruit) ;
   - à chaque contrôle : en achat, sortie si la clôture ≤ max(haut, VWAP) ; en vente, sortie si la clôture ≥ min(bas,
     VWAP) ; à plat, achat si la clôture > haut, vente si < bas. Entrées et sorties à la clôture du contrôle. Sortie à 16 h.
2. **Supertrend** (`st_detail.py`, identique au moteur C# sur 9 628 trades) :
   - bougies de 5 minutes mises bout à bout d'une séance à l'autre, ATR de Wilder ;
   - la position suit le sens de la ligne, à l'ouverture de la minute qui suit la clôture de la bougie ;
   - pas d'entrée après 15 h 30, à plat à la clôture de 15 h 54.
3. **ORB** : range = plus haut et plus bas des `durée` premières minutes. Ensuite, jusqu'à la dernière entrée, achat à la
   clôture de la première minute au-dessus du range, vente sous le range. Une seule entrée par séance. Sortie à la clôture
   d'une minute de l'autre côté du range, sinon à 16 h.
4. **Momentum de la première demi-heure** : signal = signe de (prix à la fin du signal / référence − 1). La position est
   prise à la clôture de la minute qui finit au début de la position, et tenue jusqu'à 16 h.
5. **Cassure de la veille** : plus haut et plus bas de la dernière séance complète du même contrat. Achat à la clôture de
   la première minute au-dessus du plus haut × (1 + marge), vente sous le plus bas × (1 − marge), jusqu'à la dernière
   entrée. Une seule entrée par séance. Sortie : à la clôture d'une minute revenue dans le range de la veille (« retour »),
   ou à 16 h (« fin de séance »).
6. **Fade du gap** : gap = ouverture / clôture de la dernière séance complète − 1. Si |gap| ≥ seuil, position contraire
   prise à la clôture de 9 h 30. Sortie à la clôture de la minute où le prix repasse la clôture de la veille, sinon après
   la durée maximale.
7. **Fin de séance** : mouvement = prix au début / clôture de la dernière séance complète − 1. Si |mouvement| ≥ seuil,
   position dans son sens, prise à la clôture de la minute qui finit au début, et tenue jusqu'à 16 h.

## Les portes (dans l'ordre : une stratégie qui en manque une s'arrête là)

**Fenêtres.**
- Développement (portes 1 et 2) : du 3 janvier 2011 au 31 décembre 2014.
- Marche en avant (portes 3 et 4) : du 1er janvier 2015 à la dernière séance. Tous les 30 jours, on choisit le réglage au
  meilleur profit factor sur les 4 années précédentes, puis on le trade les 30 jours suivants.

**Porte 1 : excellence dans l'échantillon (2011 - 2014).**
- Profit factor du meilleur réglage > 1,00, et t de ses gains par séance > 1,0.
- Pas un pic isolé : au moins 2/3 de ses voisins (un cran de plus ou de moins sur un seul réglage) ont un profit factor
  > 1,00. La médiane de leurs profit factors dépasse 1 + (PF du meilleur − 1) / 2.
- Pas trop parfait : profit factor < 3. Au-delà, on cherche une fuite du futur avant d'aller plus loin.
- **Réglage retenu pour la suite** (étape 3 de l'article : le milieu du plateau) : celui dont la médiane des profit
  factors (lui et ses voisins) est la plus haute.

**Porte 2 : permutation dans l'échantillon.**
- 1 000 permutations des minutes de 2011 - 2014, et la grille entière ré-optimisée sur chacune.
- p = part des permutations dont le meilleur profit factor atteint ou dépasse le vrai.
- Passe si p < 1 %.

**Porte 3 : marche en avant.**
- Sur 2015 → la dernière séance.
- Passe si le profit factor > 1,00 et le gain ≥ +1 000 $ par an (1 MNQ, frais compris).

**Porte 4 : permutation de la marche en avant.**
- 200 permutations des minutes à partir du 1er janvier 2015. Les 4 premières années restent vraies.
- Marche en avant complète sur chaque permutation.
- p = part des permutations dont le profit factor hors échantillon atteint ou dépasse le vrai.
- Plus de deux ans hors échantillon : passe si p < 1 %, soit au plus 1 permutation sur 200.

**Porte 5 : ton compte (ajoutée pour ce projet ; pas dans l'article).**
- Réglage du milieu du plateau, rejoué sur 2015 → la dernière séance.
- Compte Master, Option 2 :
  - plancher = plus haut de fin de journée − 2 500 $, arrêté à 50 000 $ ;
  - compte perdu si sa valeur touche le plancher pendant la séance, ou après 5 séances de suite sans trade.
- Limite de perte du jour : 400 $ pour le Supertrend (son réglage), 1 000 $ pour les autres (celle du Bot 3 en 1).
- Si la stratégie trade moins de 4 séances sur 5, elle est aussi jouée avec un secours : le Supertrend (10 et 3,
  limite 400 $) seul, la séance qui suit 2 séances sans trade (G2 manuel).
- Départ à chaque séance. Mesures pour un Master neuf (50 000 $, plancher 47 500 $) et pour la situation actuelle (marge
  700 $), sur 22 et 250 séances.
- Passe si, sur un Master neuf et 250 séances, le premier retrait (53 600 $) arrive plus souvent que la perte du compte.

### La permutation (« intrabar et écarts mélangés séparément », adaptée à une séance de bourse)

- Dans chaque séance complète, les écarts d'ouverture des minutes 1 à 389 sont mélangés entre eux.
- Séparément, les formes des minutes (plus haut, plus bas et clôture par rapport à l'ouverture, avec leur volume) sont
  mélangées entre elles.
- La minute 0 et l'écart de la nuit ne bougent pas. Chaque séance garde son ouverture, sa clôture, ses mouvements de
  minute et sa volatilité : seul l'ordre des minutes est détruit.
- Cela détruit aussi la forme habituelle de la journée (agitée à l'ouverture et à la clôture, calme à midi). Une stratégie
  qui n'exploite que cette forme échoue : c'est voulu.
- Graines fixées : chaque calcul est reproductible.

## Ce que ces tests ne corrigent pas

- Le projet a déjà regardé 2011 - 2026 pour choisir la zone et le Supertrend.
  - Les p-values contrôlent le choix du réglage dans la grille.
  - Elles ne contrôlent pas le choix de l'idée après avoir vu 15 ans.
- La seule donnée vraiment neuve, c'est l'avenir : le papier, puis le réel.

## Pour information (pas des portes)

- La zone et le Supertrend tournent déjà sur le compte : ils passent toutes les portes, même après un échec, pour qu'on
  voie où ils en sont. Le verdict reste celui de la première porte manquée.
- Les autres idées s'arrêtent à leur première porte manquée.

## Journal

- Chaque idée, chaque réglage, chaque résultat et chaque rejet, avec sa raison : `registre.csv`.
- Rien n'est effacé : un nouveau calcul ajoute des lignes datées.
