# Supertrend NQ 10-3 : rejeu détaillé et chances depuis 51 000 $ (14 novembre 2026)

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
