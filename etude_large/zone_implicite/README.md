# Vague « zone implicite » : la volatilité implicite du Nasdaq (VXN) pour la largeur de la zone et pour la taille (règles fixées le 23 octobre 2026, avant tout calcul et avant le téléchargement du VXN)

## Demande de l'utilisateur (23 octobre 2026)

« oui lance la vague comme les autres et applique les conditions » : tester l'idée née de la page `volatilite/` (une
zone dont la largeur vient de la volatilité implicite) et la taille selon la volatilité implicite, la technique des
fonds accessible avec des futures.

## L'idée

La zone V1 mesure sa largeur à chaque minute m sur le passé : σ_m = moyenne de |C_m / O − 1| sur les 14 séances
complètes précédentes. Elle regarde en arrière :
- au début d'un choc, la fenêtre contient encore des séances calmes : la zone est étroite par rapport à la nouvelle
  volatilité ;
- après le choc, la fenêtre contient les séances agitées : la zone reste large alors que le marché s'est calmé.

Le VXN (volatilité implicite à 30 jours des options du Nasdaq 100, Cboe) donne chaque soir la volatilité **attendue**,
sans attendre 14 séances. Trois façons de s'en servir pour la largeur (I1 à I3).

Pour la taille, les fonds réduisent leur exposition quand la volatilité monte (ciblage de volatilité, Moreira et Muir
2017). **Ce que la recherche sait déjà, et qui va contre** : `zone_failles/` (branche de recherche) a mesuré la taille
de l'article de Zarattini (inverse de la volatilité **réalisée** sur 14 jours) : t −0,44 contre +0,62 en taille fixe,
« la zone gagne justement quand ça bouge » ; la condition « VIX haut » de la vague 9 a échoué à la vérification ; la page
`volatilite/` montre un lien entre VIX et gains de la zone qui change de forme entre 2012 - 2022 et 2023 - 2026. Les
deux sens sont donc testés, chacun unilatéral (T1, T2).

Chance a priori (avant tout calcul) : I1 à I3, environ 10 % chacune ; T1, moins de 5 % ; T2, environ 5 %.

## Données

- **VXN, clôture du jour**, téléchargé **avant tout calcul** par `.github/workflows/donnees-vxn.yml`
  (`donnees_libres/vxn.py`, sources gratuites sans clé) : fichier officiel du Cboe (`VXN_History.csv`), FRED (`VXNCLS`)
  et Yahoo (`^VXN`). **Source utilisée : le Cboe** ; s'il manque ou couvre moins de 95 % des séances du NQ de 2011 -
  2026, FRED, puis Yahoo. L'accord entre les sources est publié (part des jours avec un écart de plus de 0,1 point).
- **VXN de la veille** d'une séance d : la dernière clôture datée strictement avant d (publiée à 16 h 15, connue avant
  9 h 30).
- Minutes du NQ, jours de la Fed, frais : règle commune ci-dessous.

## Règle commune (celle de `phenomenes/`, sans changement)

- **Zone de référence V1** : `delta_mesures/etude.py` (`preparer`, `zone_jour`, `trades_zone`), minutes du NQ de la
  recherche complétées par celles du robot ; séances complètes, pas de zone les jours de la Fed (`fonds/fomc.py`), 1 MNQ.
  **Contrôle obligatoire avant tout gain** : le moteur redonne 3 572 trades et +10 721,25 points jusqu'au 19 octobre
  2026.
- **Frais** : 1,5 point par aller-retour.
- **Série de décision** : gain quotidien en $ pour 1 MNQ au niveau de prix du 20 octobre 2026 (convention de
  `partie_d.chemins_zone` : points bruts × prix de référence ÷ ouverture du jour, moins 1,5 point par aller-retour,
  × 2 $), 0 les séances sans trade.
- **Périodes** : exploration de la première séance où toutes les variantes existent (I2 demande 252 séances
  d'historique : début 2012, date publiée) au 30 décembre 2022 ; **coffre du 3 janvier 2023 au 20 octobre 2026**, ouvert
  **une seule fois**, après l'écriture des résultats d'exploration dans `resultats.txt`. V1 est mesurée sur les mêmes
  séances.
- **Graine des placebos** : `numpy.random.default_rng(1)`.

## Les 5 tests (fixés maintenant)

### Précision de la zone : la largeur (I1, I2, I3)

σ_m est remplacé par σ'_m dans les limites de la zone (UB = max(ouverture, veille) × (1 + σ'_m), LB = min(ouverture,
veille) × (1 − σ'_m)), donc pour les entrées **et** pour le stop suiveur, comme dans V1. Tout le reste est inchangé
(références, VWAP, contrôles toutes les 30 minutes de 10 h à 15 h 30, sortie).

- **I1, zone implicite par rapport** : σ'_m = σ_m × VXN de la veille ÷ moyenne des clôtures du VXN des 14 séances de la
  fenêtre de σ (les mêmes 14 séances complètes, VXN de clôture de chacune). Élargit et rétrécit.
- **I2, zone implicite pure** : σ'_m = k_m × VXN de la veille ÷ 100, avec k_m = moyenne, sur les 252 séances complètes
  précédentes j, de |C_j,m / O_j − 1| ÷ (VXN de la veille de j ÷ 100). Le niveau vient du seul VXN ; la forme de la
  journée et l'échelle, d'un an de passé.
- **I3, élargir seulement** : σ'_m = σ_m × max(1, rapport de I1). Vise les fausses cassures du début des chocs.

Mesure : **t de la différence quotidienne variante − V1** (série de décision). Sens prédit : positif (unilatéral).

### La taille selon la volatilité implicite (T1, T2)

Trades de V1 inchangés ; la série de décision de chaque séance est multipliée par un poids w. Référence : médiane du VXN
de la veille sur les 252 séances précédentes.
- **T1, ciblage de volatilité** : w = ref ÷ VXN de la veille, borné entre 0,5 et 2.
- **T2, plus gros quand ça bouge** : w = VXN de la veille ÷ ref, borné entre 0,5 et 2.

Mesure : **t de l'alpha** de la régression (moindres carrés) de la série pondérée sur la série de V1 (Moreira et Muir) ;
un alpha positif veut dire que la taille variable apporte quelque chose que la taille fixe n'a pas. Sens prédit :
positif (unilatéral).

## Critères de succès (tous exigés)

1. **Exploration** : t ≥ 2,0 **et** retenu par **Benjamini-Hochberg à 10 % sur les 5 tests** (p unilatéral tiré du t).
2. **Coffre** : même signe, t ≥ 1,5.
3. **Placebos** (200 par test et par période) : le résultat réel bat au moins 95 % de ses placebos en exploration **et**
   au coffre.
   - I1 et I3 : le rapport du jour est permuté entre les séances de la période ;
   - I2 : le VXN de la veille est permuté entre les séances de la période (k_m inchangé) ;
   - T1 et T2 : le poids w est permuté entre les séances de la période.
4. **Sharpe** des séances (série de décision) de la variante plus haut que celui de V1, en exploration **et** au coffre.
5. **Challenges**, moteur de `etude_large/partie_d.py` (chemins minute par minute, plus hauts et plus bas compris),
   départs 2023 - 2026 : **Lucid Flex 50K à 1 MNQ** et **Bulenox Legacy 50K option 2 à 3 MNQ**. Pour I1 à I3, les trades
   de la variante remplacent ceux de V1. Pour T1 et T2, nombre de MNQ du jour = taille du compte × w arrondie au plus proche (0,5 vers le haut), entre
   1 et deux fois la taille du compte (Lucid : 1 ou 2 MNQ ; Bulenox : 1 à 6). Une règle passe sur un compte si elle y
   valide **au moins 2 points de plus** que V1 à la taille du compte, **sans plus de 3 points de challenges perdus en
   plus**. Retenue si elle passe sur au moins un des deux comptes, activée seulement sur celui-là.

Une règle retenue passe ensuite par une **contre-vérification adverse** (regard vers le futur, frais, erreurs de calcul),
puis par le **robot en argent virtuel**, jamais directement en argent réel.

Pour information (pas des critères) : nombre de trades et rapport moyen des largeurs par variante, résultats par année,
VXN actuel et largeur que chaque variante donnerait aujourd'hui.

## Limites écrites d'avance

- Le VXN porte sur les options de l'indice Nasdaq 100 ; le bot trade le future NQ : même sous-jacent.
- La clôture du VXN (16 h 15) voit 15 minutes de plus que la clôture du NQ (16 h 00), mais reste connue avant
  l'ouverture suivante : pas de regard vers le futur.
- 2023 - 2026 a souvent servi pour la zone elle-même ; pour ces variantes, c'est la première mesure.
- T1 chez Lucid : 2 MNQ seulement si le VXN tombe sous les deux tiers de sa médiane d'un an, ce qui est rare ; la règle y
  sera presque toujours 1 MNQ.
- Exécution à la clôture de la minute qui décide, sans glissement en plus des frais comptés.

## Résultats (23 octobre 2026) : `resultats.txt`, `etude.py`

VXN : fichier officiel du Cboe (97,8 % des séances du NQ couvertes ; accord avec Yahoo à 0,1 point près sur 99,8 % des
jours ; FRED n'a rien renvoyé). Contrôles passés : V1 redonne 3 571 trades et +10 759,75 points jusqu'au 16 octobre
2026, le moteur rapide redonne `partie_d.chemins_zone` séance par séance, et les chemins des variantes redonnent le
moteur rapide. Exploration commitée avant l'ouverture du coffre.

| Test | Exploration 2012 - 2022 : t | Placebos battus | Coffre 2023 - 2026 : t | Placebos battus | Sharpe explo / coffre (V1 : 1,14 / 1,20) | Lucid 1 MNQ (V1 : 54,6 / 35,2 %) | Bulenox 3 MNQ (V1 : 44,7 / 31,5 %) |
|---|---|---|---|---|---|---|---|
| I1 zone implicite, rapport | −1,08 | 33 % | −1,62 | 12,5 % | 1,07 / 0,99 | 39,8 / 38,1 % | 43,1 / 33,0 % |
| I2 zone implicite pure | +0,02 | 11 % | −1,75 | 91,5 % | 1,14 / 0,83 | 36,9 / 50,1 % | 36,5 / 35,2 % |
| I3 élargir seulement | −1,02 | 38 % | −1,63 | 16,5 % | 1,11 / 1,03 | 36,1 / 38,2 % | 43,7 / 32,2 % |
| T1 ciblage de volatilité | +0,03 | 51,5 % | +1,62 | 97 % | 1,11 / 1,41 | 54,6 / 35,2 % | 45,4 / 33,5 % |
| T2 plus gros quand ça bouge | −0,72 | 24,5 % | −1,24 | 7 % | 1,05 / 0,91 | 47,8 / 42,8 % | 42,3 / 33,9 % |

(I1 à I3 : t de la différence avec V1 ; T1 et T2 : t de l'alpha. Challenges : validé / perdu, départs 2023 - 2026.)

**Décision : aucun test retenu** (0 sur 5 au critère 1).

- **La zone implicite fait moins bien que la zone actuelle**, sur les deux périodes et pour les trois versions : la
  différence avec V1 est négative au coffre (t −1,6 à −1,75), et chez Lucid elle valide 15 à 18 points de moins. La
  largeur mesurée sur les 14 dernières séances réellement jouées décrit mieux le bruit du NQ que ce que les options
  annoncent. Le VXN contient aussi la prime de volatilité (il surestime presque toujours) et le risque de la nuit, que
  la zone ne joue pas.
- **Le ciblage de volatilité (T1) n'a marché que sur 2023 - 2026** : alpha t +1,62 et Sharpe 1,41 contre 1,20 au coffre,
  mais rien sur onze ans d'exploration (t +0,03, Sharpe plus bas que V1). Au challenge, il ne change rien chez Lucid
  (1 MNQ presque toujours) et perd 2 points de comptes de plus chez Bulenox pour 0,7 point validé de plus. C'est le piège
  de la vérification seule, déjà vu avec le GEX de `zone_failles/`. Il confirme quand même, à l'envers de la vague 9,
  que **grossir quand le VXN est haut (T2) n'aide pas**.

Pour information : le VXN a fini à 28,72 le 22 octobre 2026 (24,42 la veille), soit une zone plus large et des pertes
possibles plus grandes en $ par trade dans les jours qui viennent. Rien ici ne justifie de changer la taille du
challenge en cours.
