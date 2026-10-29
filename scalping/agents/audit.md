# Audit de toute la recherche intraday et scalping sur NQ/ES : inventaire et trous (agent d'audit, 25 octobre 2026)

Lecture seule des README et fichiers de résultats de la branche de recherche (`claude/keen-babbage-r686cl`), de
`claude/affectionate-turing-tnz0mn` (étude large), de `claude/elegant-ptolemy-g94s8t` (entrées en retard), de la
machine scalping (v4, v5) et du registre `fonds/essais.csv`.

## 1. Inventaire condensé

| Étude | Testé | Résultat |
|---|---|---|
| `scalping/` v4 | 6 règles publiées (A), machine sur minutes F0-F9 × 7 marchés (B), bitcoin (B2), logistique (C), nuit sur CFD (D) | 0/12 en A, 0/8 en C, 16 finalistes : 0 au coffre, placebos 0/29 ; panier NQ 5,05 → 0,74 |
| `scalping/` v5 | même machine sur tout l'historique, coffre = l'avenir | en cours |
| `intraday` | Gao, Baltussen, ORB 5 min, zone, NQ/ES 2011-2026 | seule la zone NQ (t 2,55) |
| `tournoi` | 14 classiques × NQ/ES (ORB 15/30/60, Williams, Crabel, cassure de la veille, momentum 1re heure, VWAP, gaps, retournement 30 min, tournant du mois, Fed) | 0/28 |
| `tournoi2` | 15 stratégies × NQ/ES (EMA, Supertrend, MACD, Bollinger, RSI(2), Donchian sur 5 min ; NR7 + ORB, jour intérieur, ORB + volume relatif, paire NQ/ES, lundi/vendredi, échéance, emploi, mi-journée) | 0/29 |
| `evolution2` (tournoi 3) | GEX, DIX, VIX/VIX3M, profil de volume (règle des 80 %, acceptation, rejet des bords) | 0/18 ; murs d'options jamais lancés |
| `tournoi4` | périodicité des demi-heures, fin de mois, fin de séance après grand mouvement, range de nuit, rebond, logistique de 10 h | 0/16 |
| `evolution`, `evolution3` | machines génétiques 5 min (jusqu'à 16 familles, ICT, FVG, order flow estimé) | le bruit fait au moins aussi bien ; rejeté |
| `tournoi5-7` | fin de séance sur 5 marchés, EIA, information croisée entre 7 marchés | 0 ; 0/35 ; 0/84 |
| `zone_multi`, `zone_failles`, `zone_optimisation`, `zone_sources` | la zone ailleurs, ses failles, 108 réglages, 33 conditions, confirmations | seule la correction des données reste |
| `ordres`, `orderflow` | ES 23 séances et NQ 127 séances avec côté agresseur, 180 cas et 41 567 stratégies d'order flow | information réelle mais inférieure à 1 tick ; aucune stratégie autonome ; filtre H1 confirmé sur 5 trades écartés |
| `filtre_h1`, `zone_neutre`, `relance`, `delta_mesures`, `zone_retour`, `entree_tardive` | filtre delta et mécanique de la zone | rien ne bat la zone avec le filtre brut |
| `sessions24` | 526 stratégies de sessions sur 8 marchés HistData | rien de tradable |
| `vague4`, `vague9`, `nuit`, `challenge` | largeur des méga-capitalisations, 8 178 confluences, dérive de nuit, ouverture-clôture | seul « pas de zone les jours de la Fed » reste |
| `etude_large` (+ crypto, bruit, annonces, pistes, phénomènes, zone implicite, taille) | 7 stratégies × 27 marchés, modèle ridge, bitcoin, retour dans la zone, annonces, 5 pistes, 11 phénomènes, VXN | 0 partout |

## 2. Les trous (jamais testé, ou seulement comme filtre de la zone)

**Jamais testé, donnée disponible :** niveaux multi-jours (pivots, semaine et mois précédents, VWAP ancré, extensions de
l'initial balance) ; retour ou suite selon le volume (Campbell-Grossman-Wang) ; forme du chemin en stratégie autonome ;
saisonnalité à la minute de l'horloge ; VPIN et barres de volume ; montages de praticiens jamais codés à la lettre
(Raschke-Connors, « Oops » de Williams, types d'ouverture de Dalton) ; classeur de régime (ratio de variance, Hurst) ;
apprentissage non linéaire.

**Seulement comme filtre ou en règle journalière :** avance d'autres actifs vers le NQ à la minute ; niveaux de la nuit
en scalping court ; indicateurs internes du marché (TICK, ADD : données absentes) ; calendrier jamais joué en intraday
sur le NQ (minutes du FOMC, quatre sorcières, roll, reconstitutions). Deux tests passés sont faussés et seraient à
refaire : les soirs de résultats (`phenomenes` A, calendrier remplacé par une détection qui regarde vers le futur) et
`annonces` (le fichier `udxusd` était le Dow Jones de 2012 à 2018).

**Impossible avec les données gratuites :** murs d'options et 0DTE (intérêt ouvert payant) ; microstructure (MBO,
environ 100 $ par jour) ; nuit sur de vraies minutes du future.

Rappel honnête de l'agent : les jumeaux de bruit de toutes les machines donnent une probabilité a priori faible à toute
nouvelle famille sur les mêmes barres.
