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

## Résultats (1er octobre 2026)

`glissante.py` → `glissante.txt` ; `conditions.py` → `conditions.txt`. `test_moteur.py` vérifie que le
moteur réglé redonne exactement V1.

### Optimisation glissante : la zone corrigée reste la meilleure hors échantillon

| Version | t 2014-2022 (hors échantillon) | t 2023-2026 (hors échantillon) | 2023-2026, 1 MNQ |
|---|---|---|---|
| **V1, réglage d'origine** | +1,62 | **+2,00** | **+10 668 $** |
| G1 : meilleur réglage du passé | +1,97 | +1,56 | +8 082 $ |
| G2 : meilleur des 4 dernières années | +2,64 | +0,92 | +4 722 $ |
| G3 : les 10 meilleurs du passé ensemble | +2,10 | +1,29 | +6 371 $ |

Aucune ne remplit le critère : toutes font mieux que V1 sur 2014-2022, toutes font moins bien sur
2023-2026. Les réglages qui gagnaient dans le passé (zone plus large, stop sur le VWAP, 28 jours) ne
gagnent pas ensuite. **V1 reste.**

Ce qui l'explique :
- **V1 est déjà dans le haut de la grille** : 8e sur 108 réglages sur 2023-2026. La médiane des 108 y
  fait t +1,16.
- **L'oracle** (le meilleur réglage choisi après avoir vu 2023-2026 : k 1,5, 14 jours, 30 min, stop sur
  le VWAP) ne fait que t +2,24. Même en trichant, on ne gagne presque rien. Il n'y a plus de marge à
  aller chercher dans les réglages.
- **Robustesse, sur 2023-2026** (un réglage change, les autres restent ceux d'origine) :

  | Réglage | Ce qui marche | Ce qui ne marche pas |
  |---|---|---|
  | largeur k | 1 à 1,5 (t 1,8 à 2,1) | 0,75 : t 0,58 |
  | intervalle | 30 ou 60 min (t 2,00 et 1,93) | 15 min : t 0,98 |
  | nombre de jours | 7, 14 ou 28 (t 1,5 à 2,0) | — |
  | stop | les trois (t 1,8 à 2,1) | — |

  La zone est donc solide autour de ses réglages publiés, mais une zone trop étroite ou des contrôles
  trop fréquents la font couler.

### Quand la zone marche-t-elle ? (trades de V1, 1 MNQ, frais réels)

Toujours bon dans les deux périodes (2011-2022 puis 2023-2026, t ≥ 1 dans chacune) :

| Condition | 2011-2022 | 2023-2026 |
|---|---|---|
| le 1er trade de la journée | +4,7 $/trade, t +1,48 | +13,3 $, t +1,48 |
| marché agité (mouvement moyen dans le tiers haut) | +8,7 $, t +1,62 | +13,2 $, t +1,39 |
| GEX de la veille sous sa médiane | +6,4 $, t +1,99 | +15,6 $, t +1,38 |
| grand écart d'ouverture (tiers haut) | +6,3 $, t +1,80 | +10,7 $, t +1,04 |
| trade à contre-sens de la séance de la veille | +5,6 $, t +1,95 | +17,8 $, t +1,76 |
| la veille a fini en hausse | +5,7 $, t +1,02 | +20,3 $, t +2,27 |
| achats | +3,7 $, t +1,09 | +20,4 $, t +2,07 |
| VIX moyen (tiers du milieu) | +5,0 $, t +1,26 | +10,1 $, t +1,31 |
| le vendredi | +8,2 $, t +1,77 | +17,7 $, t +1,26 |

**Aucune condition ne perd dans les deux périodes.** C'est pour cela qu'aucun filtre ne passe le
test : en 2011-2022, la zone perdait les jours calmes, à petit écart d'ouverture ou à GEX haut ; mais en
2023-2026, ces mêmes jours ont aussi gagné. Couper ces jours aurait coûté de l'argent depuis 2023.

À surveiller sans en faire une règle :
- **jours d'annonce de la Fed** : négatifs dans les deux périodes (−1,7 $ et −5,2 $ par trade), mais
  trop peu nombreux pour conclure (t −1,33 et −0,09) ;
- **2e trade de la journée** : faible partout (+2,5 $ et −1,3 $ par trade).

**En résumé**, la zone gagne surtout les jours de tendance, quand le marché bouge : forte volatilité,
grand écart d'ouverture, GEX bas. Son premier signal du jour est le meilleur. Depuis 2023, elle gagne
dans presque toutes les conditions. Aucune règle supplémentaire n'est justifiée par les données : 33
conditions ont été regardées, et quelques « bonnes » conditions sortent par hasard dans un tel lot.
