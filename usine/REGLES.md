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

## Ajouts du 16 novembre 2026 au soir (écrits et commités avant leur premier calcul)

Demande de l'utilisateur : lancer la bande plus large, et toutes les pistes qui peuvent aider le compte.

### Idée 8 : la zone de bruit avec une bande plus large (`zone_large`)

- **Pourquoi.** La marche en avant de l'idée 1 a choisi la plus grande largeur de sa grille (k = 1,4) à 140 de ses 145
  pas. La recherche s'était arrêtée à 1,5 (`zone_optimisation/`, branche `claude/keen-babbage-r686cl`).
- **L'avantage, et qui perd en face :** ceux de l'idée 1. L'hypothèse en plus : une cassure plus lointaine est moins
  souvent une fausse cassure. Le prix à payer est connu d'avance : moins de trades, donc plus de jours de secours.
- **Règle exacte :** celle de l'idée 1, sans rien changer au moteur.
- **Grille :** k ∈ {1,4 ; 1,6 ; 1,8 ; 2,0 ; 2,2 ; 2,4} × jours de moyenne ∈ {7, 10, 14, 20, 30} : 30 réglages.
- **Portes :** les 5, comme une idée nouvelle. Elle s'arrête à sa première porte manquée.

### Règle d'adoption : changer ou non la largeur de bande du bot

Le Bot 3 en 1 joue k = 1,0 sur 14 jours, et il n'a pas de réglage de largeur. Passer les portes ne suffit donc pas : il
faut que la bande large fasse mieux que le réglage du bot, hors de l'échantillon qui a servi à la choisir.

- **Référence :** idée 1, réglage du bot (k = 1,0 ; 14 jours).
- **Candidats :**
  - A = le milieu du plateau de l'idée 1 (k = 1,4 ; 30 jours), choisi sur 2011 - 2014 ;
  - B = le milieu du plateau de l'idée 8, choisi sur 2011 - 2014, seulement si l'idée 8 passe ses 5 portes.
- **Mesure :** de 2015 à la dernière séance, séances complètes, 1 MNQ, limite du jour de 1 000 $ (`k_dollars`).
- **Un candidat est adopté si les trois conditions sont remplies :**
  1. sa différence quotidienne de gain avec la référence est positive, avec t ≥ 1,65, et elle est positive aussi depuis
     le 1er janvier 2023 ;
  2. sur le compte (simulateur de la porte 5, Supertrend en secours), il ne perd pas plus de comptes que la référence
     (plancher + inactivité), ni pour un Master neuf sur 250 séances, ni depuis une marge de 700 $ sur 22 séances ;
  3. pour un Master neuf sur 250 séances, son premier retrait arrive au moins aussi souvent.
- Si A et B sont adoptés : celui qui perd le moins de comptes depuis une marge de 700 $ sur 22 séances.
- **Ce que l'adoption déclenche :** rien sur le compte réel. D'abord le rejoueur C# du bot avec ses vrais filtres (C2,
  Q1, VIX, Fed), que l'usine n'a pas ; puis le papier (`RISQUE.md`). Sans adoption : le bot ne change pas.
- **Déjà connu au moment d'écrire :** la porte 5 des deux réglages de l'idée 1 (calcul du 16 novembre). La différence
  quotidienne et tout ce qui touche l'idée 8 ne sont pas calculés.

### Test R : sous le frein, le secours aussi sur 1 MES (`pupitre.py`)

- **Pourquoi.** Règle des pupitres de risque des fonds : toute la taille suit le coussin, pas une seule stratégie. Sur
  le compte, le frein ne réduit que la zone. Le jour de secours, le Supertrend reste à 1 MNQ avec une limite de 400 $,
  soit plus de la moitié d'une marge de 700 $. Or le Supertrend n'a pas d'avantage prouvé (idée 2, porte 2).
- **Données :** minutes du NQ de l'usine, et minutes du S&P (`intraday/donnees/sp500_1min.csv.gz`, branche
  `claude/keen-babbage-r686cl`), du 1er janvier 2015 au 25 septembre 2026 (dernière séance du fichier S&P). Une séance
  compte si elle est complète dans les deux fichiers.
- **Stratégies, réglages du bot :** zone k = 1,0 sur 14 jours (limite du jour 1 000 $) ; Supertrend 10 et 3 (limite 400 $).
- **Version MES :** les mêmes positions, décidées sur le NQ, appliquées aux minutes du S&P.
  - 1 MES = 5 $ par point. Le niveau du S&P d'aujourd'hui n'est pas dans le dépôt : il est estimé par 28 500 × (clôture
    du S&P / clôture du NQ) du 25 septembre 2026.
  - Frais : 4,50 $ l'aller-retour (1 $ par ordre et un tick de 1,25 $ par ordre).
  - Limites du jour inchangées en dollars.
- **Compte :** celui de la porte 5. Le frein est celui du bot : il s'applique à une séance quand le solde de la veille
  est à 750 $ ou plus sous le plus haut de fin de journée.
- **Politiques :**
  - P0, sans frein : contrôle. Sur les données de l'usine, elle doit redonner la porte 5 du réglage du bot.
  - P1, la règle actuelle : zone sur 1 MES sous le frein ; secours toujours à 1 MNQ.
  - P2, la candidate : zone et secours sur 1 MES sous le frein.
- **Mesures :** Master neuf et marge de 700 $ (solde 49 900 $, plus haut 51 700 $), sur 22 et 250 séances, un départ à
  chaque séance : premier retrait, plancher, inactivité, gain moyen.
- **P2 est recommandée si :** depuis une marge de 700 $, elle perd moins de comptes que P1 sur 22 séances et sur 250
  séances ; et si, pour un Master neuf sur 250 séances, son premier retrait n'arrive pas moins souvent de plus de
  2 points. Sinon, la règle actuelle reste.

### Ce qui n'est pas relancé, et pourquoi

- La nuit, les combinaisons de stratégies, la zone sur plusieurs marchés, les tailles plus grandes, les stops de 200 et
  300 $, le filtre VIX, les jours de la Fed : déjà jugés avec des règles fixées d'avance (`rea/PISTES.md`). Les refaire
  jusqu'à obtenir un autre résultat serait tricher.
- L'order flow sur les enregistrements de FluxNQ et les outils de l'utilisateur : les données sont sur son PC.

## Idée K : Kronos, le modèle qui prévoit les prochaines bougies (écrite le 16 novembre 2026 au soir, avant tout calcul)

Demande de l'utilisateur : appliquer l'article « REA + Kronos + TradingAgents » (100 trajectoires, lecture du régime,
test avec frais avant tout argent).

- **L'avantage, d'après l'article et ses auteurs :** Kronos (Shi et al., arXiv 2508.02739, AAAI 2026) est pré-entraîné
  sur les bougies de plus de 45 bourses et prévoit les suivantes. Si la plupart des trajectoires vont dans un sens, le
  marché devrait y aller. **Qui perd en face :** ceux qui tradent contre un mouvement que le modèle verrait venir.
- **Modèle :** Kronos-small (24,7 M de paramètres) et Kronos-Tokenizer-base, poids de Hugging Face (NeoQuasar) déposés le
  30 juin 2025 (commit « add model » ; les commits suivants ne touchent que la fiche). Code : dépôt shiyu-coder/Kronos,
  commit 67b630e.
- **Période : seulement ce que le modèle n'a pas pu voir.** Séances complètes du 1er juillet 2025 au 13 novembre 2026
  (minutes du NQ de l'usine). Rien n'est mesuré avant : Kronos a pu apprendre sur ces années.
- **Bougies :** 5 minutes de la séance de New York (78 par séance), faites des minutes de l'usine (ouverture, plus haut,
  plus bas, clôture, volume). « amount » = volume × moyenne des 4 prix, comme `KronosPredictor.predict`. Heure d'une
  bougie : son début, heure de New York. L'historique n'est fait que des séances complètes.
- **3 décisions par séance, à 10 h, 12 h et 14 h (New York) :**
  - contexte : les 488 dernières bougies (environ 6 séances), normalisées comme `predict` (moyenne et écart-type du
    contexte, bornées à ±5). 488 et non 512 : avec 24 bougies prévues, contexte + horizon tiennent dans les 512 du
    modèle, et le cache (`kronos_cache.py`) redonne exactement le code d'origine (écart 0 sur 3 graines) ;
  - prévision : 100 trajectoires de 24 bougies (2 heures), température 1, top_p 0,9 (valeurs par défaut de `predict`),
    graine fixée par décision ;
  - signal : f = part des 100 trajectoires dont la clôture de la 24e bougie dépasse la dernière clôture. Achat si
    f ≥ 0,6 ; vente si f ≤ 0,4 ; sinon rien ;
  - position prise à la clôture de la minute de décision (9 h 59, 11 h 59, 13 h 59), fermée 2 heures plus tard (11 h 59,
    13 h 59, 15 h 59). Deux blocs de suite dans le même sens gardent la position, sans frais entre eux.
- **Mesure :** celle de l'usine (rendement net par minute, 3 $ l'aller-retour pour 1 MNQ ; dollars à 1 MNQ au prix
  d'aujourd'hui, limite du jour 1 000 $).
- **Portes, adaptées** (on ne peut pas relancer Kronos sur 1 000 marchés mélangés) :
  - **K1** : t des gains nets par séance ≥ 2,0, sur toutes les séances complètes de la période ;
  - **K2, pas un hasard** : les sens des trades sont mélangés 10 000 fois entre eux (même nombre d'achats et de ventes,
    mêmes heures ; chaque trade compté seul, frais compris). Passe si moins de 1 % des mélanges gagnent autant ;
  - **K3** : au moins +1 000 $ par an à 1 MNQ ;
  - si K1, K2 et K3 passent : le compte (simulateur de la porte 5, départs dans la période), puis le papier. Sinon,
    Kronos est rejeté et noté au registre.
- **Pour information seulement (aucune décision) :**
  - les seuils 0,5, 0,7 et 0,8, et la trajectoire moyenne (ce que rend `predict`) ;
  - aux mêmes heures, deux règles simples : suivre le mouvement des 2 heures précédentes (depuis l'ouverture pour
    10 h), et toujours acheter ;
  - la lecture du régime de l'article : quand les trajectoires sont d'accord (f ≥ 0,8 ou ≤ 0,2), le marché bouge-t-il
    plus, en valeur absolue, que quand elles sont dispersées ?
  - la part de bonnes directions.

## Journal

- Chaque idée, chaque réglage, chaque résultat et chaque rejet, avec sa raison : `registre.csv`.
- Rien n'est effacé : un nouveau calcul ajoute des lignes datées.
