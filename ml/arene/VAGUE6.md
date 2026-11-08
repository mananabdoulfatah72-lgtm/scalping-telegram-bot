# Arène, vague 6 : de meilleurs résultats pour le compte financé (règles fixées avant tout calcul, 9 novembre 2026)

Constat des vagues 1 à 5 : ce qui trade presque tous les jours (Supertrend, W1, cassures d'ouverture) grille environ un
compte financé neuf sur deux dans l'année en 1 MNQ ; le seul vraiment sûr, Z12, ne trade qu'une séance sur trois. Les
comptes se grillent surtout **au début**, quand le plancher suiveur (2 500 $) est encore tout près. Deux voies :

## A. Le tri par apprentissage sur d'autres signaux

Même méthode que W1 de production (`ml/arene/w1.py` : 28 variables connues à la décision, 10 graines, marche en avant
2017 - 2026, trade gardé si la probabilité dépasse la part de trades gagnants de l'apprentissage) :

| | Signaux triés | Base |
|---|---|---|
| M1 | cassure des 5 premières minutes (vague 3, V1 : trade 99 % des séances, essoufflée depuis 2023) | V1 |
| M2 | XGBoost NQ (le bot du labo) | XGBoost NQ |
| M3 | Bot 3 en 1 sans les jours de VIX inversé (Z12) | Z12 |

**Retenu** (sur 2017 - 2026) si : t d'au moins 2 et survie à Benjamini-Hochberg (q = 5 %) sur les 7 tests de A et B ;
positif sur 2017 - 2022 et 2023 - 2026 ; t d'au moins 1,5 avec 6 $ de frais ; au moins 7 années positives sur 10 ; et
- M1, M2 : trade au moins 50 % des séances, survie à 60 séances d'au moins 90 %, au plus 30 % de comptes neufs grillés
  dans l'année, au plus 0,30 master grillé par an ;
- M3 : au plus autant de masters grillés par an que Z12 et un net par an au moins égal.

## B. Le démarrage prudent (politique du compte)

Chaque séance, selon la marge du compte (solde − plancher, connue la veille au soir) : **Z12 seul** tant que la marge est
sous un seuil, **Z12 + W1** (W1 de production, hors échantillon) au-dessus. Pendant une requalification, Z12 seul.
Coussin = ce qui reste au-dessus de 50 000 $ après un retrait.

| | Seuil de marge | Coussin | Z12 + W1 |
|---|---|---|---|
| L1 | 3 500 $ | 4 000 $ | même compte, limite commune de 400 $ (P1) |
| L2 | 5 000 $ | 6 000 $ | limite commune (P1) |
| L3 | 3 500 $ | 4 000 $ | un contrat à la fois, Z12 prioritaire (P2) |
| L4 | 5 000 $ | 6 000 $ | un contrat à la fois (P2) |

**Retenue** (départs tous les 20 séances de 2017 à 2026, vie réelle de l'arène) si : survie à 60 séances d'au moins 95 %,
au plus 20 % de comptes neufs grillés dans l'année, au plus 0,15 master grillé par an, **net par an au moins 30 % au-dessus
de Z12 seul**, et au moins 50 % des séances tradées en moyenne. Une politique n'a pas de p à corriger : elle combine
deux bots déjà validés ; ses seuils sont fixés ici et ne sont pas choisis sur les résultats.

On rapporte aussi le retrait de la première année, le délai du premier retrait et la période du 11 août au 2 novembre 2026.
