# Radar des marchés

Le radar est une machine qui tourne 24 h sur 24. Elle a quatre rôles :
1. Elle récupère chaque soir les données de plus de 150 marchés et de sources que les traders utilisent peu, et les garde.
2. Elle cherche dans ces données, par millions de règles et par un modèle d'apprentissage, ce qui annonce le
   mouvement du NQ pendant la séance.
3. Elle ne garde que ce qui résiste à des contrôles anti-hasard fixés d'avance, et en fait une stratégie.
4. Elle suit cette stratégie en direct sur les nouvelles séances, sans argent.

| Pièce | Fichier | Quand |
|---|---|---|
| Collecte | `collecte.py` | chaque soir de semaine (`.github/workflows/radar.yml`) |
| Variables | `variables.py` | calcule, à l'heure de décision, tout ce qui est connu à ce moment-là |
| Scan des règles | `scan.py` | règles à une ou deux conditions, × 11 heures d'entrée × 5 durées × 2 sens |
| Modèle d'apprentissage | `ia.py` | régression logistique et arbres de décision boostés, réentraînés chaque année |
| Stratégie | `strategie.py` | assemble les règles qui passent le coffre, simule le challenge Bulenox |
| Suivi en direct | `../flux/veille.py` | chaque soir, sur les séances jamais vues |

## Sources collectées (`collecte.py`)

| Source | Contenu | Depuis |
|---|---|---|
| Yahoo, jour | 35 futures de la CME (indices, énergie, métaux, taux, devises, grains, bétail, bitcoin) ; 34 indices (VIX, VXN, VIX9D, VIX3M, VVIX, SKEW, MOVE, OVX, taux, dollar, Asie, Europe, Amérique latine) ; 62 ETF (secteurs, levier ×3, obligations, crédit, facteurs) ; 35 grandes valeurs ; 3 cryptos | le début de chaque série |
| Yahoo, heure | 37 marchés | 730 jours, puis chaque jour |
| Yahoo, minute | 28 marchés (NQ, ES, YM, RTY, pétrole, or, argent, cuivre, gaz, taux, euro, yen, VIX, dollar, QQQ, TQQQ, SPY, SMH, 8 grandes valeurs, bitcoin) | 28 jours, puis chaque jour (archive qui grandit) |
| FINRA | volumes vendus à découvert de 120 titres (QQQ, ETF à levier, valeurs du Nasdaq 100) : la matière du DIX, ici pour le Nasdaq ; fichier consolidé depuis 2017, somme des places de déclaration avant | août 2009 |
| SqueezeMetrics | DIX et GEX du S&P 500 | mai 2011 |
| Wikipédia | consultations de 30 pages (krach, récession, inflation, Fed, Nvidia, IA, bitcoin…) | juillet 2015 |
| FRED | 39 séries (taux, écarts de crédit, dollar, liquidité de la Fed, compte du Trésor, stress financier, incertitude des politiques économiques, chômage…) | le début de chaque série |
| Incertitude | indice quotidien d'incertitude des politiques économiques (Baker, Bloom, Davis), tiré des journaux | 1985 |
| CNN | indice peur et avidité et ses 7 composantes | **refusé** aux serveurs de GitHub (pas de réponse) |
| AAII | sentiment des particuliers (haussiers, neutres, baissiers) | 1987 |
| GDELT | volume et ton des articles du monde entier sur 8 thèmes | **rien reçu** jusqu'ici (l'outil limite les appels) |
| CBOE | photo du soir des options NDX, QQQ et SPX : gamma des teneurs de marché, niveau de bascule, murs de calls et de puts, ratios puts/calls | chaque jour à partir d'aujourd'hui |
| Résultats | dates de publication des résultats des 35 grandes valeurs | jusqu'à 25 ans |

Le planning de GitHub ne se déclenche que depuis la branche par défaut (`main`). Tant que `radar.yml` n'y est pas, la
collecte tourne à chaque envoi sur la branche de travail et à la demande (onglet Actions, « Run workflow »).

## Protocole du scan, fixé le 29 octobre 2026 avant tout calcul

Ce protocole est enregistré avant d'écrire le scan et avant de regarder un seul résultat. Rien ne sera changé
après coup. Si aucune règle ne passe, la réponse est « aucune ».

### Trades
- **Marché.** NQ en barres d'une minute, séance de 9 h 30 à 16 h (New York), du 3 janvier 2011 au 29 octobre 2026.
  Les données de la recherche vont jusqu'au 25 septembre 2026 ; le fichier du robot de la zone (`main`) prend le relais.
- **Séances exclues.** Séances incomplètes et jours de changement de contrat.
- **Décision et entrée.** La décision se prend à la clôture de la minute e − 1, l'entrée se fait à l'ouverture de la
  minute e. Heures d'entrée : 9 h 35, 9 h 45, 10 h, 10 h 30, 11 h, 11 h 30, 12 h 30, 13 h 30, 14 h 30, 15 h, 15 h 30.
- **Sortie.** À l'ouverture de la minute e + 15, 30, 60 ou 120, ou à la clôture de 16 h. Une sortie après 15 h 59
  n'est pas permise (sauf « clôture »). Cela fait 49 couples entrée-durée.
- **Gain.** En $ pour 1 MNQ au prix d'aujourd'hui (comme tout le projet : × prix de référence ÷ ouverture de la
  séance). Frais : 1 $ et 1 tick de glissement par ordre, soit 3 $ l'aller-retour.

### Variables (calculées avec ce qui est connu à la décision)
- **Séance en cours** (20 variables) : mouvement depuis l'ouverture, sur 15, 30 et 60 minutes, place dans le range du
  jour, taille du range, écart au VWAP, volume cumulé et volume des 15 dernières minutes comparés aux 20 séances
  d'avant à la même heure, écart d'ouverture, distance au plus haut et au plus bas de la veille, place dans le range des
  30 premières minutes, efficacité du mouvement, distance aux centaines rondes au-dessus et au-dessous, ancienneté du
  plus haut et du plus bas du jour, écart NQ − ES depuis l'ouverture et sur 30 minutes.
- **Autres marchés à la même minute** (14 variables) : mouvement depuis 9 h 30 et sur 30 minutes de l'ES, du RTY, du
  YM, de l'or, du pétrole, de l'euro et du bitcoin.
- **Avant l'ouverture** (environ 70 variables) :
  - la veille et les jours d'avant : mouvement, place de la clôture, range, 5 et 20 jours, écart aux moyennes de 50
    et 200 jours, RSI(2), série de hausses ou de baisses, régime de volatilité ;
  - le calendrier : jour de la semaine, début, milieu et fin de mois, échéance des options et sa semaine, lendemain
    d'échéance, échéance du VIX, Fed (veille, jour, lendemain), premier vendredi du mois (emploi), fin de trimestre,
    veille et lendemain de jour férié ;
  - VIX, VIX3M, VIX9D ; DIX et GEX ; COT ;
  - les 10 grandes valeurs : largeur et dispersion de la veille, écarts d'ouverture du jour, résultats publiés la veille
    au soir ou le matin ;
  - les sources nouvelles :
    - FINRA : part vendue à découvert sur QQQ, sur les ETF à levier et sur les valeurs du Nasdaq 100 (un « DIX du
      Nasdaq ») ;
    - Wikipédia : 5 indices d'attention (peur, marché, IA, macro, crypto) ;
    - FRED : écart de crédit, taux, courbe, liquidité de la Fed, compte du Trésor, stress financier, incertitude des
      politiques économiques ;
    - sentiment : AAII, et CNN quand l'historique couvre l'exploration ;
    - Yahoo : SKEW, VVIX, MOVE, OVX, dollar, obligations, crédit, secteurs, Nikkei et Hang Seng du jour, écart
      d'ouverture du DAX, bitcoin, volume des ETF à levier.
- **Décalages de publication.** Chaque source n'est utilisée qu'après sa publication : FINRA, Wikipédia, CNN, DIX et
  GEX la veille, FRED quotidien deux jours ouvrés avant, séries hebdomadaires de FRED et AAII une semaine après la
  date, COT le lundi qui suit sa publication.

### Conditions et règles
- **Conditions.** Chaque variable continue donne 7 conditions : 10 % les plus bas, 1er quintile, 2e, 3e, 4e, 5e,
  10 % les plus hauts. Les seuils sont pris sur la période d'exploration seulement, puis figés. Chaque variable du
  calendrier donne 1 condition. Une valeur manquante ne remplit jamais une condition.
- **Règle.** Une condition, ou deux conditions de variables différentes (ET) ; un couple entrée-durée ; un sens (achat
  ou vente). Cela fait environ 25 millions de règles.

### Les trois périodes
| Période | Dates | Rôle |
|---|---|---|
| Exploration | 2011 - 2018 | choisir |
| Confirmation | 2019 - 2022 | trier |
| Coffre | 1er janvier 2023 - 29 octobre 2026 | ouvert une seule fois, à la fin |

### Étape 1 : exploration
- Une **famille** est l'ensemble des variables d'une règle et son heure d'entrée. Dans chaque famille, on ne garde que
  la meilleure règle d'exploration (seuils, durée, sens), et seulement si elle a au moins 120 trades.
- Les 5 000 familles au t le plus haut passent à l'étape 2, à condition d'avoir t ≥ 3.

### Étape 2 : confirmation
- La règle choisie est rejouée telle quelle sur 2019 - 2022, dans le même sens et avec au moins 40 trades.
- **Barre.** t de confirmation ≥ le 95e centile, sur 20 placebos, du meilleur t de confirmation, avec un plancher de 3.
- **Placebo.** Tout le scan est refait avec les variables décalées d'un bloc de séances tiré au hasard (entre 250
  séances et la longueur moins 250). La structure des variables est gardée ; leur lien avec les gains futurs est cassé.
- **Doublons.** Deux survivantes dont les gains par séance ont une corrélation au-dessus de 0,7 comptent pour une :
  on garde celle au meilleur t de confirmation.

### Étape 3 : coffre (2023 - 2026)
Pour m survivantes, une règle passe si :
- son gain moyen est positif ;
- son t ≥ le seuil unilatéral de Bonferroni à 5 % pour m (1,645 pour m = 1) ;
- au moins 3 des 4 années 2023, 2024, 2025 et 2026 sont gagnantes.

### Modèle d'apprentissage (`ia.py`)
- **Modèles.** Pour chacun des 49 couples entrée-durée : une régression logistique (L2) et des arbres de décision
  boostés (`HistGradientBoostingClassifier`, réglages par défaut). Ils voient toutes les variables et prédisent le
  sens du mouvement.
- **Entraînement.** Il se fait sur toutes les séances avant l'année Y, pour prédire l'année Y, de 2015 à 2026.
- **Trade.** On achète (ou on vend) quand la probabilité s'écarte de 0,5 plus que pour 70 % des séances
  d'entraînement ; on ne fait rien sinon.
- **Sélection.** Un modèle passe sur ses prédictions 2015 - 2022 (jamais vues par lui) si t ≥ 3,3 (Bonferroni unilatéral
  à 5 % pour 98 modèles).
- **Coffre.** Pour m retenus, il faut sur 2023 - 2026 un t ≥ le seuil de Bonferroni pour m, et au moins 3 années
  gagnantes sur 4.

### Constitution de la stratégie (`strategie.py`)
- **Si au moins une règle ou un modèle passe le coffre :**
  - la stratégie les joue tous, 1 MNQ chacun ;
  - les positions opposées à la même minute se compensent ;
  - elle est mesurée sur les trois périodes, puis sur des challenges Bulenox 50K simulés (objectif + 3 000 $, perte
    maximale suivie 2 500 $, limite du jour 1 100 $), de 1 à 4 MNQ ;
  - elle est ajoutée au bot et au suivi en direct.
- **Si rien ne passe**, la réponse est « aucune stratégie ». Les meilleures survivantes de l'étape 2 vont au suivi en
  direct, sans argent, pour que l'avenir les juge.

### La suite, 24 h sur 24
- La collecte grossit chaque jour : minutes de 28 marchés, gamma des options du CBOE, ton des nouvelles.
- Une variable qui n'existe qu'à partir d'aujourd'hui sera scannée quand elle aura 250 séances. Les 150 premières
  serviront à choisir, les 100 suivantes à confirmer. Les survivantes seront ensuite figées et suivies en direct.

## Résultats du passage officiel (30 octobre 2026)

Fichiers : `resultats/scan.txt` (étapes 1 et 2), `resultats/scan_coffre.txt`, `resultats/ia.txt`,
`resultats/STRATEGIE.md`, `resultats/scan_familles.csv.gz` (les 227 familles), `resultats/scan_placebos.json`.

### Ce qui a été scanné
- **Séances.** 4 065 séances du NQ (2011 - 29 octobre 2026), dont 3 878 jouables.
- **Variables.** 104 variables continues, dont 35 de la séance en cours et 69 connues avant l'ouverture, plus
  20 variables du calendrier.
- **Règles.** 748 conditions, soit environ 27 millions de règles (une ou deux conditions × 49 couples entrée-durée ×
  2 sens).
- **Modèles.** 98 modèles d'apprentissage.
- **Sources absentes.** Les données de CNN et de GDELT n'ont pas pu être récupérées ; ces variables sont absentes,
  comme prévu par le protocole.

### Étapes
| Étape | Résultat |
|---|---|
| 1. Exploration 2011 - 2018 | 227 familles à t ≥ 3 |
| Placebos (20) | meilleur t de confirmation : 1,12 à 3,53 ; barre **3,33** |
| 2. Confirmation 2019 - 2022 | **1 survivante** : achat à 13 h 30, sortie à 15 h 30, si la dernière clôture est dans les 14 % du haut du range du jour (place > 0,859) ; t 3,19 puis 3,73 ; 211 trades ; +65,84 $ par trade |
| Modèle d'apprentissage | 0 sur 98 (le meilleur : régression logistique, 11 h 30 → clôture, t 2,60 hors échantillon 2015 - 2022, pour une barre de 3,3) |
| 3. Coffre 2023 - 2026 | **échec** : 221 trades, +11,21 $ par trade, t 0,78 (il fallait 1,64) ; 2023 +3 587 $, 2024 +601 $, 2025 −413 $, 2026 −1 296 $ |

**Correction faite avant l'ouverture du coffre.** Le code jugeait le meilleur placebo sur toutes ses règles, même
celles à 3 trades : un placebo donnait ainsi t 10,24 et la barre montait à 3,87. Le protocole exige au moins 40 trades
et un gain positif des vraies règles ; les placebos sont maintenant jugés pareil, ce qui donne la barre de 3,33. Cette
correction et l'étape 2 ont été enregistrées (commit `2fc8cf9`) avant l'ouverture du coffre.

### Conclusion
**Aucune stratégie.** Rien n'a passé le coffre. Ce que le scan apprend :
1. **Un seul effet a traversé la confirmation : l'élan de l'après-midi quand le NQ est au plus haut du jour.** C'est
   une forme du momentum intrajournalier publié (Gao, Han, Li et Zhou 2018 ; Baltussen, Da, Lammers et Martens 2021).
   Il était fort de 2011 à 2023 et ne l'est plus depuis 2025.
2. **Aucune des sources peu utilisées n'a donné de règle qui tienne en confirmation.** Ces sources sont :
   - les ventes à découvert de la FINRA, dont un « DIX du Nasdaq » ;
   - l'attention sur Wikipédia ;
   - le crédit et la liquidité de la FRED ;
   - l'indice d'incertitude des politiques économiques ;
   - le sentiment AAII ;
   - les résultats des grandes valeurs ;
   - l'Asie et l'Europe avant l'ouverture ;
   - 168 marchés en données quotidiennes.
3. **Le modèle d'apprentissage qui combine tout ne passe pas sa barre.**

### Suivi
- **La règle de 13 h 30** (R1) est suivie en direct, sans argent, depuis le 30 octobre 2026 dans `flux/veille.py`.
  La barre est d'au moins 40 séances avec trade et t ≥ 2,45 (Bonferroni pour les 7 candidates suivies).
- **La collecte continue chaque soir.** Les variables qui n'existent que depuis le 29 octobre 2026 seront scannées selon
  le dernier point du protocole : minutes de 28 marchés, gamma des options du NDX et de QQQ, murs de calls et de puts.

## Lancer à la main

```
KB=<copie de claude/keen-babbage-r686cl> ROBOT=<zone/robot/nq_1min.csv.gz de main> RADAR_CALCUL=<dossier> python3 radar/variables.py
RADAR_CALCUL=<dossier> python3 radar/scan.py --placebos 20      # puis --coffre, une seule fois
RADAR_CALCUL=<dossier> python3 radar/ia.py                      # puis --coffre
RADAR_CALCUL=<dossier> python3 radar/strategie.py
```

## Protocole 2, fixé le 30 octobre 2026 avant tout calcul (`protocole2.py`)

Relancer le protocole 1 sur les mêmes données redonnerait le même résultat. Le protocole 2 élargit donc la recherche :
plus de marchés, plus d'heures d'entrée, de nouvelles variables. Le coffre devient plus sévère, parce qu'il est ouvert
une deuxième fois.

### Ce qui change
- **Marchés.** Huit marchés tradables en micro chez Bulenox : NQ, ES, RTY, YM, or (GC), pétrole (CL), euro (6E) et
  bitcoin (BTC). Chacun est pris en minutes, sur sa fenêtre de séance du projet (`scalping/commun.py`).
- **Frais.** Ceux du projet pour chaque micro, en $ par aller-retour au prix d'aujourd'hui : NQ 3, ES 4,50, RTY 3,
  YM 3, GC 4, CL 4, 6E 4,50, BTC 3.
- **Périodes.**

  | Marchés | Exploration | Confirmation | Coffre |
  |---|---|---|---|
  | NQ et ES | 2011 - 2018 | 2019 - 2022 | 2023 - 2026 |
  | Les autres | début des données (2016, 2017 pour le RTY, 2018 pour le BTC) - 2019 | 2020 - 2022 | 2023 - 2026 |

- **Entrées.** Une toutes les 15 minutes, de la 15e minute de la fenêtre jusqu'à 30 minutes avant sa fin (24 heures
  d'entrée sur le NQ). Sorties à 15, 30, 60 ou 120 minutes, ou à la clôture de la fenêtre.
- **Nouvelles variables de séance** :
  - mouvement sur 5 et sur 120 minutes ;
  - range des 30 dernières minutes ;
  - écart à la clôture de la veille ;
  - place dans le range des 60 premières minutes ;
  - distance au plus haut et au plus bas des 20 séances d'avant ;
  - niveaux ronds au pas de chaque marché.
- **Variables des autres marchés.** Les 7 autres marchés, à la même heure de New York.
- **Variables d'avant l'ouverture.** Les mêmes qu'au protocole 1.
- **Modèle d'apprentissage.** Régression logistique seule (les arbres n'ont rien donné au protocole 1 et coûtent
  20 fois plus de calcul), sur chaque marché et chaque couple entrée-durée.
  - Elle est entraînée sur toutes les séances avant l'année Y, dès qu'il y en a 500.
  - Sélection sur les années hors échantillon avant 2023 : t ≥ le seuil de Bonferroni unilatéral à 5 % pour tous les
    modèles.

### Ce qui ne change pas
Les conditions (7 tranches figées sur l'exploration, calendrier), les règles à une ou deux conditions, les familles, et
l'étape 1 (t ≥ 3, au moins 120 trades, au plus 5 000 familles par marché). L'étape 2 aussi : 20 placebos par marché,
jugés avec les mêmes exigences que les vraies règles, une barre au moins égale à 3, et les doublons au-dessus de 0,7 de
corrélation.

### Coffre 2023 - 2026
Pour m règles et modèles retenus par le protocole 2, une règle passe si :
- t ≥ le seuil de Bonferroni unilatéral à 5 % pour m + 1 (le « + 1 » compte la règle déjà ouverte au protocole 1) ;
- son gain moyen est positif ;
- au moins 3 années sur 4 sont gagnantes, ou 2 sur 3 pour un marché dont les données s'arrêtent en 2025.

Ce qui passe est assemblé comme au protocole 1 (`strategie.py`) et ajouté au suivi en direct. Ce qui échoue est
publié tel quel.

### Résultats du protocole 2 (30 octobre 2026)

Fichiers : `resultats/protocole2/` (un `scan_<marché>.txt` par marché, `resume.txt`, `resume_coffre.txt`,
`logistique.csv`, placebos).

| Marché | Séances | Familles d'exploration | Barre des placebos | Survivantes |
|---|---|---|---|---|
| NQ | 4 065 | 654 | 3,52 | 2 |
| ES | 4 041 | — | 3,00 | 0 |
| RTY | 2 378 | — | 3,00 | 0 |
| YM | 2 769 | — | 3,00 | 0 |
| Or (GC) | 2 771 | — | 3,00 | 0 |
| Pétrole (CL) | 2 770 | — | 3,00 | 0 |
| Euro (6E) | 2 774 | — | 3,00 | 0 |
| Bitcoin (BTC) | 2 269 | — | 3,00 | 0 |

Les familles d'exploration des autres marchés sont dans leur `scan_<marché>.txt`.

**Régressions logistiques.** Aucune sur 828 (barre 3,84). Les meilleures : ES, 12 h 15 → clôture, t 3,07 ; NQ,
11 h 15 → clôture, t 3,02.

**Coffre** (seuil 2,13 : Bonferroni pour 3, dont la règle du protocole 1) :

| Règle | Trades | Moyenne | t | 2023 | 2024 | 2025 | 2026 | Verdict |
|---|---|---|---|---|---|---|---|---|
| NQ : achat à 13 h 30 pour 2 h si en haut du range | 221 | +11,21 $ | 0,78 | +3 587 | +601 | −413 | −1 296 | échoue |
| NQ : achat à 13 h pour 2 h si loin au-dessus du plus haut de la veille et mouvement régulier | 82 | +30,69 $ | 1,30 | +1 550 | +1 940 | −779 | −195 | échoue |

**Conclusion du protocole 2 : aucune stratégie.**
- Sur 8 marchés, la seule famille qui traverse la confirmation est l'élan de l'après-midi du NQ : acheter vers 13 h
  quand il est fort dans sa journée.
- Elle gagnait de 2011 à 2024 et perd en 2025 et en 2026.
- Les deux règles sont suivies en direct, sans argent (`flux/veille.py`, R1 et R2, barre t ≥ 2,50 pour 8 candidates).
- Tout nouveau protocole jugé sur ce coffre devra compter ces 3 règles dans son Bonferroni.
