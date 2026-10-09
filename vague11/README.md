# Vague 11 : adapter le bot à Bulenox 50K pour retirer plus vite (règles fixées le 9 octobre 2026, avant le calcul)

## Demande de l'utilisateur

Il choisit Bulenox (≈ 19 $ + 148 $ d'activation), mais il trouve les gains trop petits : environ 1 400 $ tous les 3 à
4 mois, contre environ 1 100 $ tous les 1,5 mois pour FundedNext Legacy. Il veut adapter le bot à Bulenox.

## Diagnostic (`diagnostic.py` → `diagnostic.txt`)

Une règle à la fois est enlevée (achats suivis 24 mois) :

| Changement | 3e retrait (2012-21) | 3e retrait (2023-26) |
|---|---|---|
| règles Bulenox | mois 17,1 | mois 17,0 |
| **sans la règle des 40 % (meilleur jour ≤ 40 % du gain du cycle)** | **mois 13,6** | **mois 12,8** |
| minimum de retrait 500 $ au lieu de 1 000 $ | 16,6 | 15,5 |
| plafond de retrait 3 000 $ au lieu de 1 500 $ | 17,1 | 16,9 |
| 2 MNQ sur le compte Master | plus lent (18 à 26) | plus lent |

**C'est la règle des 40 % qui freine.** Les grosses journées de la zone obligent à attendre un gain de cycle 2,5 fois
plus grand avant de pouvoir retirer. Le premier retrait (vers le mois 9) est lent pour une autre raison : il faut
d'abord laisser 2 600 $ sur le compte, plus un retrait d'au moins 1 000 $.

## Le levier (fixé maintenant)

**Plafond de gain du jour, sur le compte Master seulement** :
- dès que la journée atteint +X $, tout est fermé (ordre limite au niveau du plafond) et le bot ne prend plus de trade
  jusqu'à la séance suivante ;
- X = 400, 500, 600, 750 ou 1 000 $, ou aucun plafond ;
- le challenge n'est pas plafonné (il n'a pas de règle de régularité chez Bulenox).

Reste du bot (vague 10) :
- zone 1 MNQ, frein MES dès 750 $ sous le plus haut ;
- RSI(2) de nuit sur 1 MES ;
- pas de zone les jours de la Fed.

Un seul achat. Prix : ≈ 19,25 $ + 148 $ d'activation. Le compte réel arrive après 3 retraits (non simulé au-delà).

## Jugement

1. **Choix** : sur les achats 2012-2021 suivis 24 mois, le plafond qui donne le plus d'argent net médian sur 24 mois,
   sans perdre plus souvent le compte Master dans les 12 mois que la référence + 3 points.
2. **Vérification** : sur les achats 2023 - sept. 2024 suivis 24 mois :
   - argent net médian au moins égal à la référence ;
   - Master perdu au plus référence + 3 points.
3. On donne aussi le calendrier des retraits et les achats de 2025 (challenge).

**À savoir :** le diagnostic a regardé les deux périodes ; la vérification n'est donc pas neuve.

## Contrôles

- `test_vague11.py` : le plafond ferme au bon niveau, frais compris, et ne touche pas le challenge.
- `vague8/test_vague8.py` : sans plafond, le moteur redonne exactement le moteur d'avant la vague 8.

## Résultats (9 octobre 2026) : `vague11.txt`

Un seul achat Bulenox 50K, achats suivis 24 mois :

| Plafond du jour sur le Master | Retraits aux mois (1er / 2e / 3e) | Un retrait tous les | Master perdu en 12 mois | Net médian sur 24 mois |
|---|---|---|---|---|
| aucun, 2012-2021 | 9,7 / 13,9 / 17,1 | 3,3 mois | 25 % | +2 577 $ |
| **500 $, 2012-2021** | 9,3 / 11,5 / **13,7** | **1,8 mois** | 22 % | **+3 606 $** |
| aucun, 2023 - sept. 2024 | 8,9 / 12,8 / 17,0 | 3,5 mois | 9 % | +3 835 $ |
| **500 $, 2023 - sept. 2024** | 8,2 / 10,6 / **13,0** | **1,9 mois** | 9 % | +3 744 $ |
| 600 $, 2023 - sept. 2024 (pour information) | 7,5 / 10,2 / 12,7 | 2,0 mois | 5 % | +3 980 $ |

**Verdict fixé à l'avance : choisi = plafond de 500 $, NON VALIDÉ.** En vérification, l'argent net sur 24 mois est
presque le même (+3 744 $ contre +3 835 $), alors que la règle demandait au moins autant.

**Ce que ce critère ne voit pas :** chez Bulenox, le compte passe en réel après 3 retraits, et la simulation s'arrête là.
L'argent net sur 24 mois plafonne donc vers 3 × 1 400 $ dans les deux cas. La vraie différence est la **vitesse** :
- le 3e retrait arrive **4 mois plus tôt** (mois 13 au lieu de 17) sur les deux périodes ;
- un retrait arrive tous les **1,8 à 1,9 mois au lieu de 3,3 à 3,5** ;
- le compte Master n'est pas perdu plus souvent (9 % contre 9 %, et 22 % contre 25 % sur 2012-2021).

Ce critère de vitesse n'était pas celui fixé à l'avance : à lire comme un résultat descriptif, cohérent sur les deux
périodes.
