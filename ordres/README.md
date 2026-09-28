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

## Résultats (28 septembre 2026)

**Transactions du ES** : 23 séances du 24 août au 25 septembre 2026 (2 séances écartées : Labor Day
et le jour où le contrat suivi n'était plus le plus échangé), environ 1 million de contrats par
jour, écart acheteur-vendeur de 1 tick 99 % du temps. `python3 analyse.py` refait tout
(`resultats.txt`, `resultats.json`).

Borne haute (décile le plus favorable, mouvement du prix milieu) :

| Signal | 1 minute | 5 minutes | Frais d'un aller-retour |
|---|---|---|---|
| Déséquilibre du carnet (1er niveau) | +0,83 tick | +1,62 tick | 2,6 ticks |
| OFI | +0,24 | +0,43 | 2,6 |
| Delta 1 minute | +0,20 | aucun | 2,6 |
| CVD 15 minutes | aucun | aucun | 2,6 |

Stratégies aux règles fixées (trades sans chevauchement, 1 MES) :

| Signal | Gain brut par trade | Net par trade | Placebo battu | Verdict |
|---|---|---|---|---|
| Déséquilibre du carnet, 1 min | +0,37 tick | −2,23 ticks (t = −18,9) | 100 % | non : vrai signal, trop petit |
| OFI, 1 min | +0,62 | −1,98 (t = −6,2) | 97 % | non : vrai signal, trop petit |
| Footprint empilé, 1 min | +0,69 | −1,91 (t = −3,8) | 91 % | non |
| Footprint empilé, 5 min | −2,63 | −5,23 | 1 % | non (se retourne) |
| Delta 1 minute, 5 min | +2,05 | −0,55 (t = −0,4, 47 trades) | 90 % | non |
| Absorption, 5 min | +1,54 | −1,06 (t = −0,6, 96 trades) | 80 % | non |
| CVD 15 minutes | — | — | — | trop peu de signaux |

**Bandes de VWAP (ES 2011-2026, `vwap.py`)** : 7 208 trades, 62 % de gagnants, mais −1,29 point
par trade après frais (t = −7,5), perdant chaque année ; le retour au VWAP fait moins bien que le
hasard (le marché a tendance à continuer).

### Ce qu'on en retient

- **L'order flow contient une vraie information** : le déséquilibre du carnet et l'OFI prédisent le
  mouvement de la minute suivante mieux que le hasard (placebo battu à 97-100 %), comme dans les
  études (Cont, Kukanov, Stoikov 2014 ; Gould et Bonart 2016).
- **Mais cette information vaut moins d'un tick**, alors qu'un aller-retour au marché coûte 2,6 ticks
  sur MES (1 tick d'écart + 1,6 tick de commissions). Même sur le ES (commissions 0,4 tick), le
  meilleur décile (0,83 tick) reste sous le coût (1,4 tick).
- **Seuls les acteurs à très haute fréquence peuvent l'exploiter** : ordres passifs placés en tête de
  file, remises de la bourse, serveurs à côté de la CME. Un robot en ordres limites sans cet
  avantage est surtout servi quand le prix part contre lui ; le simuler sérieusement demanderait le
  carnet complet ordre par ordre (MBO, environ 100 $ par jour).
- **Delta, CVD, absorption et footprint empilé** : pas d'information exploitable sur ces 23 séances.
