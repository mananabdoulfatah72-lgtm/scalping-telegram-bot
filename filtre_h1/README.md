# Filtre H1 sur 15 ans : le grand backtest

L'utilisateur veut un vrai backtest du filtre H1 avant de s'y fier. Il a donné son accord le 2 octobre 2026
pour acheter les données Databento nécessaires (« utilise tout ce qu'il te faut »).

Le filtre a été trouvé et confirmé dans `orderflow/` (avril - octobre 2026) : **un trade de la zone de
bruit n'est gardé que si le delta des 30 minutes qui finissent à la clôture de la minute du signal va dans
son sens**. Le delta, ce sont les contrats achetés au prix vendeur moins les contrats vendus au prix
acheteur. Sur ces 6 mois, il a écarté 20 trades sur 99. C'est trop peu pour connaître la taille réelle de
l'effet. Les +67 points des trades gardés dans le coffre portent sur 18 trades : c'est un chiffre très
incertain, pas une promesse.

## Règles (fixées le 2 octobre 2026, avant tout téléchargement)

### Les trades

- Trades de la zone de bruit calculés avec le code du robot (`zone/robot.py` sur main, `zone_de_bruit`,
  version V1), sur les barres d'une minute du NQ de la recherche (`intraday/donnees/nasdaq100_1min.csv.gz`).
- Période : **24 janvier 2011 - 31 mars 2026**. La période d'avril à octobre 2026, déjà utilisée pour
  trouver et confirmer le filtre, est exclue.
- `trades_zone.csv` : **3 465 trades** sur 2 218 séances. Gain de chaque trade en points de NQ, après les
  frais du robot (1,5 point par aller-retour).

### Les données à acheter

- Databento GLBX.MDP3, schéma `trades` (chaque transaction avec son côté agresseur), symbole NQ.v.0.
- Pour chaque trade : les 30 minutes qui finissent à la clôture de la minute du signal. Si deux fenêtres
  d'une même séance se touchent ou se chevauchent, elles sont fusionnées en un seul téléchargement.
- Le coût de chaque fenêtre est demandé à Databento avant l'achat. Les fenêtres sont achetées **des plus
  récentes aux plus anciennes**, avec un **plafond de 75 $ au total**. Si le plafond est atteint, le test
  porte sur les années achetées.
- **Garde-fou** : si, pour une année, moins de la moitié du volume a un côté agresseur connu, on s'arrête
  là. Les années plus anciennes ne sont pas achetées.
- On garde, par séance et par minute, le volume acheteur agressif, le volume vendeur agressif et le
  volume sans côté connu. Les montants réels sont écrits dans `donnees/achats.txt`.

### Le test

- Règle **exactement** celle d'`orderflow/` : gardé si le signe de (achats − ventes) sur les 30 minutes
  est celui du trade, écarté sinon (un delta nul écarte le trade).
- Une fenêtre dont plus de 10 % du volume n'a pas de côté connu est exclue du test, et son nombre est
  publié.
- **Le filtre est confirmé si**, sur tous les trades mesurés :
  1. le gain moyen des trades gardés dépasse celui des trades écartés, avec **t ≥ 2** (test de Welch) ;
  2. la zone filtrée gagne plus que la zone seule au total.
- Publié dans tous les cas : le résultat année par année, la zone seule et la zone filtrée (points et $
  pour 1 MNQ), et la part de trades écartés.
- Descriptif seulement (aucune décision) : les mêmes mesures avec un delta sur 5, 10, 15 et 20 minutes,
  qui sont contenues dans les fenêtres achetées.
- Le filtre n'est pas réglé sur ces données. Une version différente (seuil, autre fenêtre) devrait être
  testée sur d'autres données avant d'être utilisée.

## Ce qui s'est passé : Databento verrouillé, version gratuite (2 octobre 2026)

Le téléchargement n'a pas eu lieu : Databento répond « account locked » à toute demande. **Rien n'a été
acheté.** L'utilisateur a demandé d'exploiter les données gratuites. Les barres d'une minute du NQ de
2011 à 2026 sont déjà dans le dépôt, mais elles ne disent pas qui achète et qui vend. On remplace donc le
delta par une approximation, et on vérifie d'abord qu'elle ressemble au vrai delta.

### Choix de l'approximation (sur avril - septembre 2026 seulement, là où le vrai delta est connu)

Quatre approximations du delta des 30 minutes, calculées sur les barres d'une minute :

| Approximation | Même signe que le vrai delta (1 463 fenêtres de 30 min) | Même décision que le vrai filtre (99 trades de zone) |
|---|---|---|
| P1 : volume × sens de la bougie | 71,3 % | 89 % |
| P2 : volume × position de la clôture dans la bougie | 67,7 % | 90 % |
| P3 : volume × sens de clôture à clôture | 71,8 % | 89 % |
| **P4 : mouvement du prix sur les 30 minutes** | **75,7 %** | **92 %** |

**P4 est retenue**, parce qu'elle a le même signe que le vrai delta le plus souvent sur toutes les fenêtres.
Ce choix ne regarde aucun gain, et aucune donnée de 2011 à mars 2026.

### Règles du test gratuit (fixées le 2 octobre 2026, avant de le lancer)

- Trades : les 3 465 trades de zone de `trades_zone.csv` (24 janvier 2011 - 31 mars 2026).
- Règle : le trade est gardé si la clôture de la minute du signal moins la clôture de la minute qui précède
  la fenêtre de 30 minutes va dans le sens du trade ; sinon il est écarté (un mouvement nul écarte).
- **Le filtre approché est confirmé si** les trades gardés battent les trades écartés avec **t ≥ 2** (test
  de Welch), et si la zone filtrée gagne plus que la zone seule au total.
- Publié dans tous les cas : le résultat année par année, la zone seule et la zone filtrée (points et $
  pour 1 MNQ), et la part de trades écartés. P1 à P3 : mêmes mesures, à titre descriptif seulement.
- Limite : c'est un test de l'**approximation**, qui prend la même décision que le vrai filtre dans 92 % des
  99 trades connus. Pas un test du vrai delta.

## Résultat du test gratuit (2 octobre 2026) : `test_gratuit.txt`

| | Gardés | Écartés | Écart | t | Zone seule | Zone filtrée |
|---|---|---|---|---|---|---|
| **P4 (test)** | 3 148 trades, +3,01 pt | 317 (9 %), −1,20 pt | +4,22 pt | **1,62** | +9 108 pt | +9 490 pt |
| P1 (descriptif) | 3 024, +2,75 pt | 441 (13 %), +1,80 pt | +0,95 pt | 0,39 | +9 108 pt | +8 314 pt |
| P2 (descriptif) | 2 922, +2,89 pt | 543 (16 %), +1,23 pt | +1,66 pt | 0,67 | +9 108 pt | +8 440 pt |
| P3 (descriptif) | 3 024, +2,78 pt | 441 (13 %), +1,56 pt | +1,22 pt | 0,48 | +9 108 pt | +8 418 pt |

- **Le filtre approché n'est pas confirmé** (t = 1,62 < 2). Il va dans le bon sens, mais l'effet est petit :
  +382 points en 15 ans pour 1 MNQ (environ +760 $, soit 50 $ par an). La zone filtrée fait mieux que la
  zone seule 8 années sur 16.
- Les approximations par le volume (P1 à P3) n'ont aucun effet.
- **Lecture** : sur 15 ans, rien ne ressemble aux +67 points du coffre d'`orderflow/`. Deux explications sont
  possibles, et ces données ne permettent pas de trancher :
  1. l'effet mesuré sur avril - octobre 2026 tenait en partie à la chance (20 trades écartés) ;
  2. l'effet vient du vrai delta, que les barres d'une minute ne voient pas (l'approximation ne reprend
     que 12 des 20 trades écartés par le vrai filtre).
- Seul l'historique du vrai delta trancherait (Databento, ou l'historique tick par tick de la plateforme de
  l'utilisateur quand il aura un compte, par exemple via Rithmic). En attendant, le filtre reste **suivi à
  part** dans le robot, hors du compte virtuel.

## Version Alpaca : les vraies transactions du QQQ (règles fixées le 2 octobre 2026, avant tout téléchargement)

Le test gratuit ci-dessus ne prouve pas que le filtre est faux : il n'utilisait pas le vrai delta. Pour
approcher le vrai delta sans Databento, on utilise les **transactions réelles du QQQ** (le fonds coté qui
suit le Nasdaq 100, des centaines de milliers de transactions par jour), gratuites chez Alpaca depuis 2016
(offre Basic : données SIP, 200 requêtes par minute).

- Données : Alpaca Market Data API, flux SIP, chaque transaction du QQQ (prix, taille, conditions). Les
  transactions hors marché normal sont retirées (conditions B, C, G, H, M, N, P, Q, R, T, U, V, W, Z, 4, 7, 9).
- **Côté acheteur ou vendeur par la règle du tick** : une transaction plus haute que la précédente est un
  achat, plus basse une vente, au même prix elle garde le côté de la précédente. Delta du QQQ = achats −
  ventes sur les mêmes 30 minutes que le filtre.
- **Étape 1, validation** (avril - septembre 2026, où le vrai delta du NQ est connu) : les fenêtres des
  99 trades de zone, plus 300 fenêtres de contrôle tirées au hasard (graine 1) parmi les heures de contrôle
  de la zone. Le delta du QQQ est **accepté comme remplaçant** s'il a le même signe que le vrai delta du NQ
  dans **au moins 85 %** des 300 fenêtres, **et** s'il prend la même décision que le vrai filtre dans
  **au moins 90 %** des 99 trades.
- **Étape 2, test** : les trades de zone du 4 janvier 2016 au 31 mars 2026 (`trades_zone.csv`), même règle
  qu'H1. Si le remplaçant est accepté, le filtre est confirmé avec **t ≥ 2** (Welch) et une zone filtrée
  meilleure que la zone seule. S'il n'est pas accepté, le test est publié à titre descriptif seulement.

## Résultat de la version Alpaca (2 octobre 2026) : `resultat_alpaca.txt`

Données reçues : 20,3 millions de transactions du QQQ pour la validation (124 séances d'avril à octobre 2026)
et 79,3 millions pour le test (1 481 séances de 2016 à mars 2026). Gratuit.

**Étape 1, validation : le remplaçant est refusé.**
- Le delta du QQQ a le même signe que le vrai delta du NQ dans **60,7 %** des 300 fenêtres de contrôle
  (seuil 85 %). C'est à peine mieux que le hasard (50 %), et moins bien que la simple approximation par le
  prix (75,7 %).
- Il prend la même décision que le vrai filtre dans **62,6 %** des 99 trades de zone (seuil 90 %).
- Raisons probables : le QQQ n'a pas les mêmes acheteurs que le contrat NQ, et la règle du tick devine mal
  le côté de chaque transaction sur un flux consolidé de plusieurs bourses.

**Étape 2, à titre descriptif seulement** (2 346 trades de zone) : gardés +6,00 points, écartés (30 %)
+0,19 point, t = 1,82. Mais la zone filtrée gagne un peu moins que la zone seule (+9 863 contre +9 999
points), et ne fait mieux que 5 années sur 11. Ce filtre-là n'est pas le filtre H1, puisque son delta ne
ressemble pas au vrai.

**Conclusion** : aucune donnée gratuite testée (barres d'une minute, transactions du QQQ) ne reproduit le
delta du contrat NQ. Le filtre H1 reste confirmé seulement sur avril - octobre 2026 (coffre t = 2,34, 5 trades
écartés). Pour le tester sur des années, il faut le vrai côté agresseur des transactions NQ : Databento (compte
à débloquer), ou l'historique tick par tick de la plateforme de l'utilisateur quand il aura un compte.
