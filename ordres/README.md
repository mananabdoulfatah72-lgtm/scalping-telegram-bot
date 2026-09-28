# Order flow : delta, CVD, carnet, footprint, VWAP

Peut-on gagner de l'argent avec ce que montrent les outils d'order flow (delta, CVD, footprint,
DOM, Bookmap, VWAP) sur le future E-mini S&P 500, en tradant des micro-contrats MES ?

## Données

- **Transactions du ES** (Databento, schéma `tbbo`, contrat le plus échangé) : chaque transaction
  avec son sens (acheteur ou vendeur agressif) et le meilleur prix acheteur / vendeur affiché juste
  avant, avec les quantités. Séance américaine (9 h 30 - 16 h), jours les plus récents, 25 $ au plus.
  Agrégées par seconde et par minute × prix (footprint) par `telecharger_ordres.py`.
- **Barres d'une minute du ES 2011-2026** (déjà téléchargées, dossier `intraday/`) pour le VWAP.
- **Non testé : le carnet profond** (DOM au-delà du premier niveau, carte de chaleur Bookmap). Il faut
  les schémas MBP-10 ou MBO, de l'ordre de 100 $ par jour de données : hors budget.

## Signaux (fixés le 28 septembre 2026, avant de télécharger les données)

Décision à la fin de chaque minute, de 9 h 31 à 15 h 54. Mouvement mesuré sur le prix milieu
(moyenne du meilleur acheteur et du meilleur vendeur), en ticks (1 tick = 0,25 point).

1. **Delta 1 minute** : (volume acheteur agressif − volume vendeur agressif) / volume total de la
   minute. Suivre son sens si |delta| ≥ 0,3.
2. **CVD 15 minutes** : delta cumulé des 15 dernières minutes, divisé par le volume des 15 minutes.
   Suivre son sens si |CVD| ≥ 0,15.
3. **Déséquilibre du carnet (1er niveau)** : (quantité au meilleur acheteur − quantité au meilleur
   vendeur) / somme, à la dernière seconde de la minute. Suivre son sens si |déséquilibre| ≥ 0,5.
4. **OFI** (Cont, Kukanov, Stoikov 2014) : flux d'ordres au premier niveau sur la minute, calculé
   seconde par seconde ; divisé par son écart-type des 60 minutes précédentes. Suivre son sens si
   |OFI| ≥ 2.
5. **Footprint, déséquilibres empilés** (réglages par défaut des logiciels : 300 %, 3 niveaux) :
   achat au prix p ≥ 3 × vente au prix p − 1 tick (et au moins 20 contrats), sur 3 prix consécutifs
   ou plus dans la minute → achat ; symétrique pour la vente.
6. **Absorption (divergence de delta)** : clôture de la minute au plus haut des 15 dernières minutes
   alors que le delta des 15 minutes est négatif → vente ; au plus bas avec un delta positif → achat.
7. **Bandes de VWAP** (barres minute 2011-2026) : clôture au-dessus du VWAP + 2 écarts-types (écart-type
   pondéré par les volumes depuis l'ouverture) → vente ; en dessous de VWAP − 2 écarts-types → achat ;
   sortie au retour au VWAP ou à 15 h 55 ; pas d'entrée avant 10 h.

Signaux 1 à 6 : position gardée 1 minute ou 5 minutes, puis sortie ; pas de nouveau trade pendant
qu'une position est ouverte.

## Frais (MES, ordres au marché)

On traverse l'écart acheteur-vendeur à l'entrée et à la sortie (≈ 1 tick au total, du milieu au milieu),
plus 1 $ par ordre (0,2 point par ordre sur MES) : **2,6 ticks (0,65 point) par aller-retour** pour les
signaux 1 à 6. Pour le VWAP, mêmes frais que les autres tests intraday sur barres minute (0,9 point).

## Règles de verdict

Un signal est **exploitable** s'il gagne après frais en moyenne, avec t ≥ 2, **et** s'il fait mieux
que 95 % des placebos (mêmes moments de trade, sens tiré au hasard). Chaque signal testé est inscrit
dans `fonds/essais.csv`.

Borne haute : pour chaque signal continu (1 à 4), le mouvement moyen du décile le plus favorable.
Si même ce meilleur décile ne dépasse pas les frais, aucun seuil ne peut rendre le signal rentable
avec des ordres au marché.
