# Zone sans filtre : entrer à la cassure, sortir dès le retour dans la zone (règles fixées le 21 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (21 octobre 2026)

Le challenge Bulenox n'a plus qu'environ 500 $ de marge (`delta_mesures/`). L'utilisateur demande la zone de bruit sans
filtre delta, mais avec des pertes plus petites que les gains :
- entrer dès que le prix casse la zone ;
- laisser courir les gains ;
- couper la position dès que le prix revient dans la zone.

## Déjà mesuré (`entree_tardive/`, branche `claude/elegant-ptolemy-g94s8t`, 20 octobre 2026)

- **E2** (entrée à la minute, sortie à la minute sous max(limite, VWAP), entrée seulement au-delà de cette ligne) :
  −9 549 points sur 15 ans, t −4,68 sur 2011-2022. La moitié des trades duraient moins de 4 minutes et payaient les frais.
- **S1** (entrées aux contrôles, sortie à la minute sous max(limite, VWAP)) : t +0,82 et +1,57 contre +2,12 et +1,86
  pour la zone actuelle, mais deux fois moins de séances à −1 000 $.
- La règle demandée ici diffère : la sortie est la **limite de la zone seule**, sans le VWAP. Sur une forte tendance,
  le VWAP passe au-dessus de la limite et faisait sortir E2 et S1 plus tôt. Ici, le trade court tant que le prix reste
  hors de la zone.

## Variantes (fixées maintenant)

Pour chaque minute m, la zone est celle du bot : limite haute = max(ouverture, veille) × (1 + σ_m), limite basse =
min(ouverture, veille) × (1 − σ_m), σ_m = mouvement moyen depuis l'ouverture à la minute m sur les 14 dernières séances
complètes. Exécution à la clôture de la minute qui décide, 1,5 point de frais par aller-retour, une seule position,
tout fermé à 16 h. Sans filtre delta.

| Nom | Entrée | Sortie |
|---|---|---|
| **V1** (référence) | aux contrôles de 10 h à 15 h 30, si la clôture sort de la zone | à un contrôle, si le prix repasse max(limite, VWAP) (min pour une vente), ou à 16 h |
| **C1** (la règle demandée) | à **chaque minute** de 10 h à 15 h 30, si la clôture sort de la zone de cette minute | à la **première minute** dont la clôture revient dans la zone (achat : ≤ limite haute ; vente : ≥ limite basse), ou à 16 h |
| **C2** (couper vite seulement) | aux contrôles, comme V1 | comme C1 |
| **C3** (C1 sans allers-retours) | comme C1, mais après une sortie, pas de nouvelle entrée avant le contrôle de 30 minutes suivant | comme C1 |

## Mesures

1. **15 ans** (barres de la recherche 2011-2026, complétées par celles du robot jusqu'au 20 octobre 2026) :
   - trades, points, part de gagnants ;
   - gain moyen et perte moyenne en $ pour 4 MNQ au prix d'aujourd'hui ;
   - durée médiane des trades ;
   - t des gains quotidiens nets en points, sur toutes les séances jouables (0 sans trade), 2011-2022 et 2023-2026
     séparément ;
   - part des séances où la limite de perte de 1 000 $ coupe le bot en 4 MNQ.
2. **Challenge depuis 0, 16 séances** : Bulenox 50K option 2, 4 MNQ puis 6 MNQ les 5 dernières séances, limite du jour
   1 000 $, arrêt à l'objectif + 50 $, pas de zone les jours de la Fed. Départs à chaque séance de 2012 à 2026, et de
   2023 à 2026. Même moteur et mêmes contrôles que `delta_mesures/`.
3. **Depuis la situation estimée de l'utilisateur** (solde 49 158 $, plancher 48 672 $, 16 séances) : 1 MNQ, 2 MNQ et
   le réglage actuel.
4. Pour information : 2 - 16 octobre 2026 en points, et 13 - 20 octobre 2026 en $ pour 4 MNQ.

## Décision (fixée maintenant)

Une variante remplace la zone du bot seulement si elle remplit **tout** ce qui suit :
1. t supérieur à celui de V1 sur 2011-2022 **et** sur 2023-2026 ;
2. challenge depuis 0 : au moins 2 points de validés de plus que V1 sur les départs 2012-2026, et pas moins que V1 sur
   les départs 2023-2026.

Si plusieurs passent : celle qui valide le plus souvent sur 2012-2026. Sinon, la zone ne change pas.

**Limites écrites d'avance :**
- Une sortie à la minute se fait au marché. Dans un mouvement rapide, le glissement peut dépasser les 1,5 point comptés.
- Sur 15 ans, il n'y a pas de delta : la question du filtre reste à part.
