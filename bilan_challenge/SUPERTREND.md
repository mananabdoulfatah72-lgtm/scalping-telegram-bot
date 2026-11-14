# Supertrend NQ 10-3 : rejeu détaillé et chances depuis 51 000 $ (14 novembre 2026)

> **Correction du 14 novembre 2026 : ton compte est en Option 2**, plancher recalculé en fin de journée. C'est toi
> qui l'as précisé. L'« Option 1 » venait d'une déduction de `audit/machine6/REGLES.md` (2 novembre). Les chiffres
> en Option 2 sont dans la dernière section : ils changent de 1 à 3 points seulement.

## Ce que fait le bot (`bot3en1/SUPERTREND.md` de `claude/optimistic-ptolemy-xs24ra`)

- Bougies de 5 minutes du NQ, de 15 h 30 à 22 h (heure de Paris). L'indicateur continue d'une séance à l'autre.
- ATR = amplitude moyenne des 10 dernières bougies (Wilder). La ligne est à 3 ATR du prix, environ 124 points en
  octobre 2026.
- Le bot est toujours dans le sens de la ligne : **achat** si elle est sous le prix, **vente** si elle est au-dessus.
  Quand une bougie clôture de l'autre côté, la position se **retourne** en un seul ordre.
- Première position à 15 h 35, plus d'entrée après 21 h 30, **tout est fermé à 21 h 55** (heure de Paris).
- Réglages : MNQ par trade, limite de perte du jour (400 $ par défaut), objectif (solde 53 000 $). ATR 10 et
  multiple 3 sont les seuls réglages testés.
- **Un compte, une stratégie** : il ne doit pas tourner sur le même compte que le Bot 3 en 1, sinon ils ferment
  mutuellement leurs positions.

Sur 15 ans : 2,4 trades par séance, 42 % de trades gagnants, gain moyen +299 $ contre une perte moyenne de −200 $
(1 MNQ). Il perd souvent un peu et gagne gros les jours de tendance.

## Comment ce calcul a été vérifié

- Données : minutes NQ de 2011 à septembre 2025 (`intraday/donnees/nasdaq100_1min.csv.gz` de
  `claude/keen-babbage-r686cl`), puis `zone/robot/nq_1min.csv.gz` de `main` jusqu'au 13 novembre 2026. Sur leurs
  99 810 minutes communes, les deux fichiers sont identiques.
- **Un seul faux prix en 15 ans, corrigé** : le 30 octobre 2026 à 15 h 03 (New York), une ouverture à 29 562 alors
  que le marché était à 28 234. C'est lui qui faisait « perdre » Supertrend le 30 octobre dans `BILAN.md`.
- Le moteur C# de la stratégie Quantower (`Supertrend.Replay`) et le modèle Python donnent les mêmes 54 trades du
  13 octobre au 13 novembre : mêmes jours, mêmes sens, mêmes minutes, mêmes prix.
- Les règles du compte sont celles de ton compte Bulenox en **Option 1** (`audit/machine6/REGLES.md`) :
  - le plancher vaut le plus haut solde **latent**, gains ouverts compris, moins 2 500 $ ; il est suivi minute par
    minute et bloqué à 50 100 $ ;
  - le compte est perdu dès qu'il touche le plancher ;
  - le côté défavorable de chaque minute est testé en premier ;
  - frais de 3 $ par MNQ, 1 point de glissement à la limite du jour, objectif atteint à 53 050 $.
- Mon simulateur Python redonne le simulateur numba de la machine v6 sur 400 fenêtres de 22 séances sur 400.

## La période du challenge (13 octobre → 13 novembre 2026, 24 séances, vrais dollars)

Départ à 50 000 $ le 13 octobre :

| Taille, limite du jour | Gain sur les 24 séances | Challenge (Option 1) |
|---|---|---|
| 1 MNQ, 400 $ (réglage par défaut) | +6 256 $ | validé le 4 nov. |
| 1 MNQ, sans limite | +5 550 $ | validé le 5 nov. |
| **2 MNQ, 800 $** | **+12 511 $** | **validé le 22 oct.** |
| 2 MNQ, 400 $ | +8 409 $ | **perdu le 29 oct.** (limite trop serrée pour 2 MNQ) |
| 3 MNQ, 1 200 $ | +18 766 $ | validé le 16 oct. |
| 4 MNQ, 1 000 $ | +18 470 $ | validé le 16 oct. |

Jour par jour à 2 MNQ avec une limite de 800 $, sans arrêt à l'objectif :

| Jour | Trades | Résultat | Pire moment | Cumul |
|---|---|---|---|---|
| 13 oct. | 4 | −804 $ (limite) | −818 $ | −804 $ |
| 14 oct. | 1 | +1 259 $ | −442 $ | +455 $ |
| 15 oct. | 4 | −804 $ (limite) | −842 $ | −349 $ |
| 16 oct. | 1 | +2 421 $ | −56 $ | +2 072 $ |
| 19 oct. | 3 | −305 $ | −485 $ | +1 767 $ |
| 20 oct. | 3 | −472 $ | −675 $ | +1 295 $ |
| 21 oct. | 2 | −40 $ | −444 $ | +1 255 $ |
| 22 oct. | 1 | +1 542 $ | −236 $ | +2 797 $ |
| 23 oct. | 3 | −804 $ (limite) | −834 $ | +1 993 $ |
| 26 oct. | 3 | −181 $ | −300 $ | +1 812 $ |
| 27 oct. | 1 | +734 $ | −532 $ | +2 546 $ |
| 28 oct. | 3 | −804 $ (limite) | −892 $ | +1 742 $ |
| 29 oct. | 1 | −804 $ (limite) | −886 $ | +938 $ |
| 30 oct. | 2 | +1 973 $ | −680 $ | +2 911 $ |
| 2 nov. | 2 | +1 741 $ | −355 $ | +4 652 $ |
| 3 nov. | 3 | −452 $ | −705 $ | +4 200 $ |
| 4 nov. | 2 | +1 235 $ | −8 $ | +5 435 $ |
| 5 nov. | 1 | +4 322 $ | −197 $ | +9 757 $ |
| 6 nov. | 2 | −804 $ (limite) | −830 $ | +8 953 $ |
| 9 nov. | 1 | +2 264 $ | −23 $ | +11 217 $ |
| 10 nov. | 4 | −804 $ (limite) | −864 $ | +10 413 $ |
| 11 nov. | 2 | +1 373 $ | −605 $ | +11 786 $ |
| 12 nov. | 3 | −804 $ (limite) | −802 $ | +10 982 $ |
| 13 nov. | 2 | +1 529 $ | −112 $ | +12 511 $ |

- 12 séances perdantes sur 24, dont **8 à la limite du jour** ; 12 gagnantes, souvent fortes (+4 322 $ le 5 nov.).
- Plus longue série perdante : 3 séances (19 au 21 oct., −817 $).
- Plus forte baisse : du sommet de +2 797 $ (22 oct.) à +938 $ (29 oct.), soit −1 859 $ en fin de journée et environ
  −1 940 $ au pire moment du 29 octobre. **Depuis 51 000 $ avec un plancher vers 49 300 $, cette baisse aurait
  perdu le compte.**

## Sur 15 ans (gains au prix d'aujourd'hui)

| | 1 MNQ, limite 400 $ | 2 MNQ, limite 800 $ |
|---|---|---|
| Gain moyen par séance | +17,2 $ (t 2,44) | +34,5 $ |
| Depuis 2023 | +12,5 $ par séance (**t 0,87** : plus distinguable du hasard) | +25,0 $ |
| Séances gagnantes | 45 % | 45 % |
| Pire séance | −428 $ | −855 $ |
| Plus longue série de séances perdantes | 10 | 10 |
| Pire série perdante | −4 067 $ | −8 134 $ |
| Plus forte baisse du cumul | −13 038 $ | −26 076 $ |
| Plus forte baisse depuis 2023 | −7 995 $ | −15 990 $ |
| Années perdantes | 2013 (−8 502 $), 2017 (−5 641 $), 2024 (−1 744 $), 2025 (−1 493 $) | les mêmes, ×2 |

## Tes chances depuis 51 000 $ (Option 1, objectif 53 000 $)

Départs à chaque séance de l'historique. Ton plancher dépend de ton plus haut latent : regarde-le sur le tableau de
bord Bulenox. En % : réussi / perdu / ni l'un ni l'autre.

| Ton plancher | Durée | 1 MNQ, 400 $ | 2 MNQ, 800 $ | 2 MNQ, 400 $ | 4 MNQ, 1 000 $ |
|---|---|---|---|---|---|
| 48 500 $ | 22 séances (1 mois) | 32 / 24 / 44 | 47 / 51 / 2 | 43 / 50 / 7 | 45 / 55 / 0 |
| 48 500 $ | 66 séances (3 mois) | 51 / 42 / 6 | 48 / 52 / 0 | 46 / 53 / 0 | 45 / 55 / 0 |
| 49 000 $ | 22 séances | 32 / 26 / 42 | 46 / 52 / 2 | 42 / 52 / 6 | 44 / 56 / 0 |
| 49 000 $ | 66 séances | 50 / 44 / 6 | 47 / 53 / 0 | 45 / 55 / 0 | 44 / 56 / 0 |
| 49 300 $ | 22 séances | 31 / 31 / 38 | 44 / 55 / 2 | 41 / 55 / 5 | 42 / 58 / 0 |
| 49 300 $ | 66 séances | 49 / 46 / 5 | 45 / 55 / 0 | 43 / 57 / 0 | 42 / 58 / 0 |

Départs depuis 2023 seulement : mêmes ordres de grandeur, à 1 ou 3 points près (`st_part2.py`).

- **À 2 MNQ, c'est presque pile ou face, un peu défavorable** : environ 45 % de réussite et 55 % d'échec, décidés
  en général en moins d'un mois. Monter à 3 ou 4 MNQ n'augmente pas la réussite : ça va seulement plus vite.
- **À 1 MNQ, le risque d'échec est plus faible sur un mois** (24 à 31 %), mais l'objectif est atteint moins souvent
  (environ 31 %). Sur trois mois, on revient à environ 50 / 45.
- **Pourquoi c'est si serré.** Il te faut +2 000 $ pour réussir, et 1 700 à 2 500 $ de baisse suffisent à perdre.
  En Option 1, le plancher monte aussi avec les gains latents que le Supertrend rend avant de se retourner.
- **Si tu le lances à 2 MNQ, mets la limite du jour à 800 $, pas 400 $.** Le 29 octobre, la limite de 400 $ à
  2 MNQ perdait le challenge, alors que celle de 800 $ le validait.

## Pour refaire

`st_detail.py` (données, faux prix, trades, contrôles), puis `st_part2.py` (période, 15 ans, chances). Les deux
fichiers attendent, à côté d'eux, les copies de travail `op` (`claude/optimistic-ptolemy-xs24ra`) et `kb`
(`claude/keen-babbage-r686cl`), ainsi que `pip install numba`.

## Sur ton compte Master (solde 51 000 $, plancher 49 200 $), le 14 novembre 2026

`st_master.py`. Le premier retrait devient possible à 53 600 $ (52 600 $ à garder plus 1 000 $ au moins, contrat du
23 octobre 2026). La question posée au simulateur : le compte atteint-il 53 600 $ avant de toucher le plancher ?

**Ce que fait la limite du jour, à 1 MNQ sur 15 ans** (gains au prix d'aujourd'hui) :

| Limite du jour | Par séance | Pire séance | Pire série perdante | Plus forte baisse | Plus forte baisse depuis 2023 |
|---|---|---|---|---|---|
| aucune | +25,6 $ | −5 453 $ | −12 326 $ | −16 541 $ | −9 095 $ |
| **400 $** | **+17,2 $** | **−428 $** | **−4 067 $** | **−13 038 $** | **−7 995 $** |
| 800 $ | +24,1 $ | −827 $ | −5 201 $ | −11 132 $ | −9 106 $ |

- La limite de 400 $ coupe chaque mauvaise journée vers −400 $, mais elle **coûte environ un tiers du gain** sur
  15 ans. Sur le mois du challenge, elle a aidé : +6 256 $ au lieu de +5 550 $, avec 8 séances coupées à la limite.
  C'est l'inverse de ce qu'elle fait en moyenne.
- **Elle n'arrête pas une série de pertes.** Avec 1 800 $ de marge, cinq séances à la limite suffisent à perdre le
  Master. Sur 15 ans, il y a eu jusqu'à 10 séances perdantes de suite.

**Tes chances depuis 51 000 $ / 49 200 $** (départs à chaque séance depuis 2011) : 53 600 $ atteint / Master perdu /
ni l'un ni l'autre, en %, et nombre médian de séances quand c'est atteint.

| Taille, limite | 1 mois (22 séances) | 3 mois (66 séances) | 1 an (250 séances) |
|---|---|---|---|
| **1 MNQ, 400 $** | **21 / 30 / 49** | **41 / 50 / 9** | **44 / 56 / 0** (23 séances) |
| 1 MNQ, sans limite | 27 / 33 / 40 | 45 / 50 / 5 | 47 / 53 / 0 (20 séances) |
| 1 MNQ, 300 $ | 18 / 26 / 56 | 39 / 49 / 12 | 44 / 56 / 0 (26 séances) |
| 2 MNQ, 800 $ | 37 / 60 / 4 | 38 / 62 / 0 | 39 / 61 / 0 (6 séances) |

- Ces chiffres supposent un plancher suivi en temps réel (Option 1). Suivi en fin de journée : 1 à 4 points de
  moins de chaque côté. Départs depuis 2023 seulement : 45 / 55 sur un an à 1 MNQ et 400 $.
- **Règle des 40 %** (meilleure journée au plus 40 % du gain depuis le dernier retrait) : à 1 MNQ / 400 $, quand
  53 600 $ est atteint, le retrait est permis tout de suite 73 fois sur 100, sinon environ 2 séances plus tard.
- **Ce qui joue pour lui** : il trade chaque séance, donc il ne risque pas la règle d'inactivité.
- **Ce qui joue contre lui** : depuis ta situation, il perd le Master plus souvent qu'il n'atteint le premier
  retrait. Pour comparaison, dans `chantier/` de `claude/loving-mccarthy-u21aw6` (autre simulateur, plancher suivi
  en fin de journée, 1 400 $ de marge) : ton Bot 3 en 1 avec le secours d'une heure fait 11 % de comptes perdus et
  55 % avec au moins un retrait en un an.

## Plafond de gain du jour : règle fixée avant le calcul (14 novembre 2026)

**La demande.** Ajouter à Supertrend un plafond de gain du jour, pour que les trades gagnants ne soient pas rendus aux
perdants, avec la limite de perte de 400 $.

**La règle testée.** 1 MNQ, limite de perte du jour de 400 $. À la clôture de chaque minute, si le résultat du jour
(réalisé + latent, frais compris) atteint le plafond, la position est fermée au prix de clôture et le bot ne trade
plus ce jour-là. Plafonds testés : 300, 500, 800, 1 200 et 2 000 $, aucun autre.

**Critère d'adoption, fixé avant le calcul.** Depuis ton Master (51 000 $, plancher 49 200 $, plancher suivi en temps
réel), sur 250 séances, un plafond est adopté s'il fait à la fois plus de premiers retraits (53 600 $ atteint) et
moins de Masters perdus que « sans plafond ». Il doit le faire pour les départs depuis 2011 et pour ceux depuis 2023.
Le gain par séance sur 15 ans est publié pour information.

### Résultats (calculés après avoir fixé la règle) : `st_plafond.py`

1 MNQ, limite de perte de 400 $ :

| Plafond du jour | Par séance, 15 ans (t) | Depuis 2023 (t) | Plus forte baisse, 15 ans | Séances plafonnées | Mois du challenge (vrais $) | Master sur 250 séances, départs 2011+ | Départs 2023+ |
|---|---|---|---|---|---|---|---|
| aucun | +17,2 $ (2,44) | +12,5 $ (0,87) | −13 038 $ | 0 % | +6 256 $ | 44 / 56 | 45 / 55 |
| 300 $ | +1,2 $ (0,23) | +2,5 $ (0,24) | −25 898 $ | 41 % | +894 $ | 36 / 64 | 47 / 53 |
| 500 $ | +12,6 $ (2,12) | +10,6 $ (0,86) | −11 659 $ | 24 % | +2 333 $ | 41 / 59 | 44 / 56 |
| 800 $ | +19,0 $ (2,88) | +8,9 $ (0,66) | −10 753 $ | 10,5 % | +4 552 $ | 45 / 54 | 44 / 56 |
| 1 200 $ | +16,1 $ (2,35) | +12,1 $ (0,86) | −13 038 $ | 3 % | +5 422 $ | 45 / 55 | 46 / 54 |
| 2 000 $ | +17,8 $ (2,52) | +13,2 $ (0,91) | −13 038 $ | 0,5 % | +6 148 $ | 44 / 56 | 45 / 55 |

Les deux dernières colonnes donnent, en %, le premier retrait atteint / le Master perdu.

**Verdict**
- **300 $ et 500 $ sont rejetés.** Ils cassent l'avantage du bot : +1,2 $ par séance à 300 $. À 300 $, il y a plus
  de Masters perdus depuis 2011 (64 % au lieu de 56 %).
- **800 $ est rejeté** : mieux sur les départs depuis 2011, moins bien sur ceux depuis 2023.
- **1 200 $ passe la règle écrite, mais d'un seul point de chaque côté** (45 / 55 et 46 / 54, contre 44 / 56 et
  45 / 55). C'est dans le bruit : il ne plafonne que 3 % des séances. Mon critère n'exigeait pas d'écart minimum,
  c'est une faiblesse de la règle. Il ne change rien de concret au risque du Master. Son seul avantage pratique : il
  garde la meilleure journée sous 40 % du gain avant le premier retrait (1 200 $ ≤ 40 % de 3 600 $).
- Pourquoi : les gains de Supertrend viennent de quelques grosses journées de tendance, et ses pertes tombent surtout
  **d'autres jours**. Un plafond ne protège pas des jours perdants ; il coupe les journées qui les paient.

Contrôle des données : refait en pourcentage (plus de 1 % d'écart à la clôture d'avant et à sa propre clôture), il ne
trouve aucun autre faux prix en 15 ans. Les minutes extrêmes sont de vrais événements (mars 2020, 9 avril 2025). La
meilleure séance d'un bot plafonné peut dépasser le plafond en une minute, comme le 16 mars 2020 : réouverture 4 % plus
bas après un arrêt des échanges, +2 317 $ en une minute à 1 MNQ.

## En Option 2, faut-il baisser la limite de perte du jour ? (`st_option2.py`)

Ton Master : 51 000 $, plancher 49 200 $, plancher recalculé en fin de journée et fixe pendant la séance. Le compte
est perdu si sa valeur touche le plancher pendant la séance. Supertrend à 1 MNQ.

| Limite du jour | Par séance, 15 ans (t) | Séances coupées | Plus longue série perdante | Master sur 1 an, départs 2011+ : retrait / perdu | Départs 2023+ |
|---|---|---|---|---|---|
| 150 $ | +5,8 $ (1,14) | 69 % | 30 | 36 / 61 | 30 / 70 |
| 200 $ | +4,4 $ (0,79) | 61 % | 20 | 35 / 64 | 34 / 66 |
| 250 $ | +10,5 $ (1,72) | 52 % | 17 | 41 / 59 | 38 / 62 |
| 300 $ | +11,3 $ (1,75) | 46 % | 17 | 42 / 57 | 42 / 58 |
| **400 $** | **+17,2 $ (2,44)** | **34 %** | **10** | **43 / 55** | **44 / 56** |
| 500 $ | +19,3 $ (2,60) | 25 % | 10 | 45 / 55 | 47 / 53 |
| 800 $ | +24,1 $ (3,01) | 10 % | 10 | 48 / 52 | 46 / 54 |
| aucune | +25,6 $ (2,86) | 0 % | 10 | 46 / 54 | 48 / 52 |
| 400 $ + garde du plancher | — | — | — | 41 / 0, figés 59 % | 42 / 0, figés 58 % |

- **Baisser la limite ne protège pas davantage, au contraire.** Un trade normal de Supertrend perd de 140 à 540 $
  avant de se retourner (10 novembre : −463 $ puis −538 $). Sous 400 $, la limite coupe la journée avant la tendance
  qui l'aurait payée. Le gain fond, les séries perdantes s'allongent, et le Master est perdu plus souvent : 64 % à
  200 $ contre 55 % à 400 $.
- **La garde du plancher** (limite du jour ramenée à la marge moins 150 $) n'est pas une solution. Elle empêche le
  plancher d'être touché, mais elle **fige** le compte près du plancher : sans marge, le bot ne trade plus, et la
  règle d'inactivité (5 jours sans trade) finit par perdre le Master.
- **Le risque vient des séries de mauvaises journées, pas d'une seule journée.** Aucune limite du jour ne le règle.
- Plancher en fin de journée ou en temps réel : à 1 à 3 points près, les chiffres sont les mêmes.

## Un mois normal, et la limite à 800 $ (`st_mois.py`)

Supertrend à 1 MNQ, toutes les périodes de 24 séances depuis 2011 (3 929 périodes), gains au prix d'aujourd'hui.
Pour le Master : Option 2, 51 000 $, plancher 49 200 $, sur un an.

| | Limite 400 $ | Limite 800 $ |
|---|---|---|
| Mois moyen | +385 $ | +552 $ |
| Mois médian (la moitié fait moins) | +272 $ | +340 $ |
| 1 mois sur 4 fait moins de | −821 $ | −757 $ |
| 1 mois sur 4 fait plus de | +1 568 $ | +1 897 $ |
| 1 mois sur 10 fait plus de | +2 786 $ | +3 119 $ |
| Mois perdants | 43 % | 42 % |
| Mois à +6 000 $ ou plus | 0,3 % | 0,5 % |
| Pire mois | −4 897 $ | −5 978 $ |
| Master : 1er retrait / perdu | 43 % / 55 % | 48 % / 52 % |
| Master perdu dès le 1er mois | 26 % | 29 % |
| Quand le Master est perdu, au bout de (médiane) | 24 séances | 19 séances |

Le mois du challenge (+6 256 $ à 400 $) est l'un des 0,2 % meilleurs depuis 2011. La limite de 800 $ fait un peu
mieux en moyenne et donne quelques points de plus pour le retrait. En contrepartie, une mauvaise journée coûte deux
fois plus, et quand le compte est perdu, il l'est plus vite.
