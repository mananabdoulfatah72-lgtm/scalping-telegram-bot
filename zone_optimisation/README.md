# Zone de bruit NQ : optimiser sans se tromper, et savoir quand elle marche

L'utilisateur veut un meilleur t hors échantillon et savoir dans quelles conditions la zone fonctionne.
Régler la zone sur 2023-2026 rendrait ces années « dans l'échantillon » et gonflerait le t : c'est ce
qu'a montré le filtre GEX, meilleur sur le passé et moins bon ensuite (`zone_failles/`). On utilise donc
l'optimisation glissante, la seule façon d'avoir un vrai chiffre hors échantillon.

## Règles (fixées le 1er octobre 2026, avant tout calcul)

Base : la zone corrigée V1 (`zone_failles/journal.py`), NQ, frais réels de 1,5 point par aller-retour
(MNQ), séances complètes, pas de trade le jour d'un changement de contrat.

### 1. La grille (108 réglages)

| Réglage | Valeurs | Dans la zone d'origine |
|---|---|---|
| largeur de la zone (k × mouvement moyen) | 0,75 ; 1,0 ; 1,25 ; 1,5 | 1,0 |
| nombre de jours de la moyenne | 7 ; 14 ; 28 | 14 |
| intervalle entre deux contrôles | 15, 30 ou 60 min | 30 |
| stop suiveur | limite ou VWAP (le plus serré) ; VWAP seul ; limite seule | limite ou VWAP |

### 2. Optimisation glissante

Chaque 1er janvier, de 2014 à 2026, on choisit selon les seules années passées, puis on joue l'année
qui commence :

| Version | Choix |
|---|---|
| G1 | le meilleur réglage sur toutes les années passées (depuis 2011) |
| G2 | le meilleur réglage sur les 4 dernières années |
| G3 | les 10 meilleurs réglages sur toutes les années passées, joués ensemble à parts égales (chacun pour un dixième) |

« Meilleur » = plus haut t des rendements quotidiens nets.

**Critère d'adoption** : une version glissante remplace V1 dans le robot si elle remplit tout ce qui
suit :
- t hors échantillon supérieur à V1 sur 2014-2022 **et** sur 2023-2026 ;
- t de la différence quotidienne avec V1 d'au moins 1,65 sur 2014-2026.

Sinon, V1 reste.

**Pour information seulement** : le réglage qui aurait été le meilleur sur 2023-2026 lui-même
(« l'oracle »). Il montre de combien une optimisation faite après coup gonfle le résultat.

### 3. Quand la zone marche-t-elle ?

Analyse descriptive des trades de V1, sur 2011-2022 et sur 2023-2026 séparément. Une condition n'est
dite **stable** que si elle aide (ou nuit) dans les deux périodes. Conditions examinées :
- heure du contrôle d'entrée ;
- jour de la semaine ;
- volatilité du moment (mouvement moyen, par tiers) ;
- niveau du VIX (par tiers) et structure du VIX (déport ou contango) ;
- GEX de la veille (sous ou au-dessus de sa médiane) ;
- écart d'ouverture (par tiers) ;
- séance de la veille (hausse ou baisse) ;
- sens du trade dans le sens de la séance de la veille, ou contre ;
- jours d'annonce de la Fed.

Aucune condition n'est transformée en règle ici : une condition stable ne serait qu'une piste à
confirmer sur les mois à venir (suivi en argent virtuel).

Tous les essais sont inscrits dans `fonds/essais.csv`.
