# Vague « pistes » : 5 pistes, 17 tests, pour ajouter une précision ou une source à la zone (règles fixées le 22 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (22 octobre 2026)

Continuer à chercher, sur d'autres pistes, une source, une variante ou une précision qui s'ajoute à la zone de bruit
filtre delta. Données gratuites seulement.

## Comment les pistes ont été choisies

Trois chercheurs indépendants (littérature et pratique des fonds ; mécanique de la zone ; données gratuites disponibles)
ont proposé 15 pistes. Un juge les a confrontées aux 55 dossiers de la recherche et à `cerveau/savoir.json`, a vérifié
les données, et en a gardé 5 (17 tests). Les règles ci-dessous sont celles du juge, recopiées sans changement.

## Règle commune (fixée maintenant)

- **Benjamini-Hochberg à 10 % sur les 17 tests ensemble** (p tiré du t d'exploration, bilatéral pour les tests
  bilatéraux), en plus des critères propres à chaque piste.
- Une piste qui passe ses critères est ensuite soumise à une **contre-vérification adverse** (agents chargés de la
  réfuter : regard vers le futur, frais, erreurs de calcul) avant d'être annoncée.
- Une piste retenue entre d'abord au **robot en argent virtuel**, jamais directement en argent réel.
- Frais : 1,5 point NQ et 0,9 point ES par aller-retour ; micros des autres marchés : 1 $ par ordre + 1 tick par côté.
- À confirmer avant tout usage réel : les heures de trading permises par chaque firme (Bulenox jusqu'à 16 h 59 ?
  Lucid jusqu'à 16 h 45 ?).

## Pistes écartées par le juge (pour mémoire)

- **Minutes du FOMC à 14 h comme condition de la zone (pistes 2 et 11, partie M)** : La piste n'a jamais été testée. vague9 (29 conditions) n'a que les jours de la Fed, et annonces/ ne porte que sur 8 h 30. Les dates existent : le juge a compté 152 dates « Released » dans kb/fonds/donnees/fomc/, de 2008 à 2026. Elle est écartée pour sa faible puissance : environ 88 jours en exploration et 30 au coffre, avec une réaction aux minutes qui faiblit depuis 2008 (Rosa). Et la règle de la Fed elle-même n'est qu'« un petit plus » (vague9). C'est la 6e piste : à garder en réserve, peu chère à tester si l'une des 5 retenues échoue.
- **Adjudications longues du Trésor à 13 h (pistes 4 et 11, partie A)** : tournoi5 E1 et E2 (lus) : 0 survivante sur le ZN. La version publiée de Lou, Yan et Zhang ne montre l'effet que sur les taux. La règle A3 retire environ 13 % des séances. Les adjudications tombent souvent la semaine du chiffre de l'inflation, ce qui brouille le résultat. Chance a priori d'environ 5 %.
- **GEX de la veille et dernière demi-heure de la zone (piste 3)** : Le GEX a déjà été épuisé comme condition. vague9 et zone_optimisation : « GEX sous sa médiane » marche sur 2011-2022 mais échoue sur 2023-2026 (zone_failles). evolution2 G1 et G2 : élan ou retour selon le gamma. Le GEX vient des options du S&P 500, et les options à 0 jour faussent le chiffre de la veille depuis 2022. La tranche de 15 h 30 à 16 h est trop petite pour un t de 2. Le fichier s'arrête au 29 septembre 2026.
- **Nuit des chiffres de l'emploi, jeudi 18 h → vendredi 9 h 30 (piste 5)** : Puissance trop faible : même une vraie prime de 10 pb, avec 12 nuits par an et environ 1 % d'écart-type, ne donne qu'un t d'environ 1 à 1,5. Il y a confusion avec la dérive de nuit (nuit N1 : t 1,74, rejeté). Les primes d'annonce analogues ont échoué : veille de la Fed, Sharpe 0,34 (fonds), et +113 $ par an refusés (protection). La piste chevauche aussi le RSI(2) de nuit.
- **Entrée sur repli par ordre limite à la ligne de sortie (piste 7)** : La sélection adverse joue contre elle : entree_tardive L1 montre que les cassures fortes sans repli sont les meilleurs trades (+6,44 points contre +2,47), et ce sont celles qui ne seraient pas remplies. Des barres d'une minute ne permettent pas de modéliser la file d'attente des ordres. zone_retour C1-C3 confirme que le retour à la limite n'annonce pas de suite exploitable. Moins bonne que les 5 pistes retenues.
- **Zone de bruit de la séance européenne, 3 h - 9 h 25 (piste 13)** : sessions24 (lu) : avant frais, rien sur le Nasdaq à l'ouverture de Londres (F3 t net −2,55 et −2,84 ; F4 −3,5 ; G7 environ 0). HistData n'a pas de volume, donc pas de vrai VWAP. La piste chevauche le RSI(2) de nuit dans la même fenêtre. Chance a priori d'environ 4 %, donnée par le chercheur lui-même.
- **Écart du week-end du bitcoin sur le MBT, dimanche 18 h (piste 14)** : La famille de l'écart du week-end (sessions24 G11, 7 marchés) a échoué partout, sauf sur le dollar australien, jugé ensuite irréaliste à la réouverture. machine4, calendrier du BTC : rien. Aucune étude académique, seulement du folklore. Le MBT est peu liquide le dimanche à 18 h, coûte 7,3 pb, et les futures crypto sont souvent restreints par les prop firms.
- **Achat seul de l'heure de 16 h (piste 9, P3)** : Sa moyenne sans condition a déjà été vue sur toutes les années (nuit/resultats.txt : NQ +1,1 pb, ES +0,5 pb, 2010-2026). Il ne reste donc aucune année jamais vue, et le t après frais tombe à environ 1,5. Elle n'est gardée que comme témoin de dérive dans la piste de l'heure de 16 h (contrôle achats et ventes).
- **Retour de nuit, 18 h → 9 h 59 (piste 1, V4 et V6)** : Chevauche N1 (nuit/) et le RSI(2) de nuit (vague4, intraday50k) dans la même fenêtre. Retiré pour garder au plus 6 variantes sur une fenêtre jamais jouée.
- **Retourner la position de zone à 16 h, et prendre le sens du mouvement du jour (piste 12, P2 et P4)** : Ce sont les miroirs exacts, frais en plus, de H1 (prolonger) et de H2 (retour) : ils sont intégrés au test bilatéral de H1 et au placebo de sens, pour ne pas compter deux fois le même test.

## Piste 1 : Sortie VWAP de la zone : tenir la position ou sortir pour de bon (le bot réel et les backtests ne font pas la même chose) (`sortie_vwap/`, note du juge 7/10, precision zone)

**Règle exacte**

Base V1 : zone/robot.py zone_de_bruit. σ sur 14 séances complètes, référence max(ouverture, veille) et min(ouverture, veille), VWAP = (H+L+C)/3 pondéré par le volume depuis 9 h 30, contrôles 10 h 00, 10 h 30 … 15 h 30, à plat à la clôture de 15 h 59. Pas de zone les jours de la Fed (fonds/fomc.py annonces()) ni les jours courts (jour_court). 1 MNQ, 1,5 point par aller-retour.

Cas visé : un contrôle m où l'on est acheteur avec ub_m < C_m ≤ VWAP_m (pour une vente : VWAP_m ≤ C_m < lb_m). Aujourd'hui, V1 vend puis rachète au même prix à ce contrôle (lignes 244-251 ; même logique dans Moteur.cs ZoneDecision). Vérifié par le juge en relançant scratchpad/check/reentree.py : 382 cas sur 3 562 trades (2011 - 25 sept. 2026), 210 séances, de 10 à 43 par an.

ZL (tenir) : dans le cas visé, on ne fait rien. La position ne sort que si C ≤ ub (achat) ou C ≥ lb (vente), ou à 15 h 59. C'est exactement le stop « limite seule » de zone_optimisation (mêmes positions que V1, 1,5 point de moins par cas) : ZL sert de référence.

ZW (le bot quand le delta est contre) : dans le cas visé, sortie à C_m. Aucune nouvelle entrée dans le même sens tant qu'un contrôle n'a pas vu le prix revenu dans la zone (C ≤ ub pour un achat, C ≥ lb pour une vente). Une entrée dans l'autre sens suit la règle normale. C'est ce que fait Moteur.cs : le nouveau signal devient une ZoneVirtuelle qui bloque toute entrée tant que le prix reste hors de la zone, avec la relance décochée.

ZW+ : dans le cas visé, sortie à C_m, sans rachat à ce contrôle. À un contrôle suivant, une nouvelle entrée dans le même sens demande C > max(ub, VWAP) (C < min(lb, VWAP) pour une vente).

**Variantes**

2 tests : ZW − ZL et ZW+ − ZL (bilatéraux, le sens n'est pas connu). ZL est la référence. V1 n'est qu'un contrôle comptable : ZL = V1 + 1,5 point par cas.

**Données**

Minutes du NQ, 9 h 30 - 16 h : kb/intraday/donnees/nasdaq100_1min.csv.gz (2011-01-03 → 2026-09-25 ; colonnes t,o,h,l,c,v,contrat ; heure de New York), complétées par zone/robot/nq_1min.csv.gz (2025-09-24 → 21 oct. 2026). Moteur : delta_mesures/etude.py (preparer, trades_zone). Vrai delta, à titre descriptif : P1 Databento kb/orderflow/donnees/nq_secondes_*.csv.gz (colonnes achat et vente, 9 h 30 - 16 h) et P2 Rithmic kb/filtre_h1/donnees_rithmic/. Challenges : delta_mesures/etude.py challenge() (Bulenox, 16 séances depuis 0) et etude_large/partie_d.py (Lucid Flex, 1 MNQ).

**Contrat et frais**

MNQ (zone du bot inchangée), 1,5 point par aller-retour (1 $ par ordre + 1 tick par côté).

**Périodes**

Exploration 2011-2022 (environ 285 cas). Coffre 2023 → 20 oct. 2026 (environ 97 cas). Ces années ont déjà servi à la zone, mais jamais à une sortie VWAP effective. P1 (avril - oct. 2026) et P2 (octobre 2026) : description seulement.

**Critères de succès et décision**

Série quotidienne Δ = ZW − ZL (puis ZW+ − ZL), en points nets, 0 les jours sans cas.
1) Exploration : |t(Δ)| ≥ 2, retenu par Benjamini-Hochberg à 10 % sur les 17 tests des 5 pistes.
2) Coffre : même signe, |t| ≥ 1,5.
3) Sharpe des séances du gagnant plus haut que celui du perdant sur les deux périodes.
4) Placebo : l'écart réel est plus extrême, du côté gagnant, que 95 % de 200 placebos. Dans un placebo, la sortie ZW est appliquée au même nombre de contrôles par an, tirés au hasard parmi les contrôles tenus où C > max(ub, VWAP), avec le même blocage.
5) Challenges, départs 2023-2026 : le gagnant ne valide pas plus d'un point de moins que le perdant, ni chez Bulenox ni chez Lucid.

Décision :
- Si ZL gagne, le bot « tient » : dans Moteur.cs, la sortie compare le prix à la seule limite.
- Si ZW gagne, le bot reste tel quel, mais toutes les simulations du filtre (vagues 9-13, robustesse, partie D) sont refaites avec ZW comme référence.
- Sinon, ZL passe dans le robot virtuel (frais économisés) et l'écart entre backtest et bot est publié.

**Contrôles**

a) Recompter les 382 cas, et vérifier que ZL = V1 + 1,5 × 382 points exactement.
b) Vérifier sur P1, avec le vrai delta, que les 11 rachats de ce type ont tous été écartés par le filtre (delta_mesures/trades.csv). Vérifier aussi que H1 (bot, relance décochée) redonne 79 trades et +1 776,8 points.
c) Résultats séparés pour les achats et les ventes, et par heure du cas.
d) ES minute en réplication, à titre d'information (même signe).
e) Aucune donnée de delta n'est nécessaire sur 15 ans, puisque ZW reproduit le bot sous l'hypothèse « delta contre ». Il faut publier sur P1 et P2 la part réelle des rachats écartés.

**Pourquoi**

Défaut de mécanique vérifié dans le code par le juge (zone/robot.py l. 244-251 ; zone_optimisation/moteur.py zone_nb « if pos == 0: if p > ub » ; Moteur.cs ZoneDecision). Sans filtre, la partie VWAP de la sortie de l'article ne change jamais la position : elle ne coûte que des frais. Avec le filtre delta, le bot réel sort pour de bon (le nouveau signal devient une ZoneVirtuelle bloquante). Sur environ 10 % des trades, le bot réel fait donc autre chose que les 15 ans de backtest, et que toutes les simulations du filtre qui ont servi à choisir les tailles et les comptes. Le test tranche une question qui touche directement l'argent du compte. Il se tranche sur 15 ans sans données de delta, il n'a aucun paramètre libre, et chacune des deux issues donne une action dans le bot. Chance a priori d'un vainqueur net : environ 20 à 25 %. Sans vainqueur, le gain de frais de ZL dans le robot virtuel est sûr mais petit (environ 36 points par an et par MNQ).

**Pourquoi ce n'est pas déjà testé**

zone_optimisation/README.md (lu) : les stops « limite ou VWAP » et « limite seule » y ont exactement les mêmes positions, à cause du rachat au même contrôle (moteur.py lu) ; le t de 1,8 à 2,1 ne compare que des frais. zone_failles V5 (stop VWAP seul) est une autre règle. entree_tardive E2 et S1 sortent à la minute (S1 : t +0,82 / +1,57) : c'est le bruit de la minute qui est payé, pas la sortie de 30 minutes. Aucun dossier ne relève que le filtre delta active la sortie VWAP dans le bot réel (cherché dans savoir.json et les README).

## Piste 2 : L'heure 16 h 00 - 16 h 59 permise par Bulenox : prolonger la zone, ou jouer le retour de la pression de clôture (fusion des pistes 1, 9 et 12) (`heure_16h/`, note du juge 5.5/10, source independante)

**Règle exacte**

Règles communes :
- Barre d'une heure de 16 h du NQ : kb/nuit/donnees/nasdaq100_1h.csv.gz (Databento, étiquetée par son début, heure de New York, colonne contrat).
- Entrée à l'ouverture O16 de cette barre, sortie à sa clôture C16 (environ 16 h 59 ; en réel, le bot sort à 16 h 55).
- Exclusions : jours courts (jour_court), jours de la Fed, séances sans barre de 16 h, et pour un signal sur deux séances, changement de contrat entre la veille et le jour.
- Frais : 1,5 point NQ et 0,9 point ES par aller-retour.

H1, prolonger la zone (précision) : s = sens de la position de zone V1 encore ouverte à 15 h 59 (sortie « à la clôture »). Gain ajouté = s × (C16 − C15:59), sans frais en plus. Test bilatéral : si le gain ajouté est positif, le bot prolonge ; s'il est négatif, retourner la position n'est retenu que si −s × (C16 − O16) − 1,5 point reste positif avec les mêmes critères.

H2, retour de la journée (NQ) : S = ln(C15:59_t / C15:59_{t−1}), avec la veille = dernière séance complète du même contrat. Le jour est actif si |S| ≥ 80e centile des |S| des 252 séances complètes précédentes (passé seulement). Position −signe(S), 1 MNQ, de O16 à C16.

H3, retour de la dernière demi-heure (NQ) : L = ln(C15:59 / C15:29), même seuil du 80e centile sur |L|, position −signe(L), de O16 à C16.

H4 : H2 sur l'ES (MES), avec sp500_1min et sp500_1h.

H5, version Lucid (à plat à 16 h 45) : signal de H2. Prix HistData usatechidxusd en 5 minutes (UTC converti en America/New_York) : entrée à l'ouverture de la barre de 16 h 00, sortie à la clôture de la barre de 16 h 10 (soit 16 h 15). Seulement les séances où les deux barres existent.

**Variantes**

5 : H1 (prolonger la zone), H2 (retour de la journée, NQ), H3 (retour de la dernière demi-heure, NQ), H4 (H2 sur MES), H5 (H2, sortie à 16 h 15, compatible Lucid).

**Données**

Vérifié par le juge :
- nasdaq100_1h.csv.gz : 6 juin 2010 → 28 sept. 2026, colonnes t,o,h,l,c,v,contrat. 4 063 barres de 16 h, dont 3 917 sur 2011-2026 jointes aux minutes. Contrat identique dans 100 % des cas, et |O16 − C15:59| ≤ 2 points dans 99,8 % des cas (médiane 0,25 point).
- Volume médian de la barre de 16 h : 24 % de celui de 15 h.
- Signal : kb/intraday/donnees/nasdaq100_1min.csv.gz et sp500_1min.csv.gz (2011 → 25 sept. 2026).
- HistData usatechidxusd (kb/sessions24/annees/) : barres de 16 h 00 à 16 h 10 présentes toutes les années (2023 : 180 séances sur 250, à signaler). Barres jusqu'à 16 h 55 seulement de 2012 à 2018 environ ; plus rien entre 16 h 15 et 17 h depuis 2019.
- Corrélation avec la zone : moteur de delta_mesures/etude.py.

**Contrat et frais**

MNQ, 1 contrat (MES pour H4). 1 $ par ordre + 1 tick par côté, soit 1,5 point NQ et 0,9 point ES par aller-retour. Sensibilité à 3 points NQ et 1,8 point ES, car la liquidité est faible après 16 h.

**Périodes**

Exploration 2011-2022 (H5 : 2012-2022). Coffre 2023 → 28 sept. 2026, fin des barres d'une heure (H5 : → 2 oct. 2026). Le gain conditionnel de cette heure n'a jamais été calculé ; seule sa moyenne sans condition a été vue (nuit/resultats.txt).

**Critères de succès et décision**

1) t net des séances (0 sans trade) ≥ 2 en exploration, retenu par Benjamini-Hochberg à 10 % sur les 17 tests. Pour H1 : t du gain ajouté, test bilatéral.
2) Coffre : même signe, t net ≥ 1,5.
3) Mécanisme, pour H2 à H5 : en exploration, les achats ET les ventes gagnent chacun au moins 0 avant frais. Sinon, ce n'est que la dérive de +1,1 pb de cette heure.
4) Placebo :
- H2 à H5 : faire mieux que 95 % de 1 000 tirages du sens au hasard, sur les mêmes séances ;
- H1 : faire mieux que 95 % de 200 tirages où s est remplacé par le sens de la zone d'une autre séance tirée au hasard dans la même année ;
- témoin d'heure : la même règle de 13 h 00 à 13 h 59, avec un signal arrêté à 12 h 59, doit faire moins bien.
5) t > 0 aux frais de sensibilité.
6) Source : corrélation des séances avec la zone < 0,3 sur 2016-2022 et Sharpe zone + source (à risque égal) plus haut que la zone seule au coffre. H1 : Sharpe zone + prolongation plus haut que la zone sur les deux périodes.
7) Challenges avec le moteur de la partie D : Bulenox 3 à 4 MNQ (H1 à H4) et Lucid Flex 1 MNQ (H5 seulement). Puis argent virtuel avant tout argent réel.

**Contrôles**

a) Refaire la vérification d'alignement (O16 contre C15:59, même contrat) dans le code, avant tout gain.
b) Avant d'utiliser H5, sur 2012-2018 : la corrélation entre le rendement HistData de 16 h 00 à 16 h 55 et celui de la barre Databento de 16 h doit être d'au moins 0,9. Sinon, H5 est abandonnée.
c) Sur 2012-2018 (HistData) : corrélation entre une sortie à 16 h 55 et une sortie à 17 h, pour savoir ce que coûte la sortie réelle à 16 h 55.
d) Publier le pire trade et les séances de résultats des grandes valeurs (16 h 05).
e) Publier à part les achats et les ventes, et les résultats par sous-période (2011-14, 2015-18, 2019-22, 2023-26).
f) Confirmer la règle de Bulenox sur sa page officielle (positions fermées à 15 h 59, heure de Chicago, soit 16 h 59 à New York, d'après des guides tiers), ainsi que l'heure de Lucid (16 h 45).

**Pourquoi**

La fenêtre de 16 h à 16 h 59 est permise chez Bulenox et n'a jamais été jouée : nuit/README.md la croyait interdite, et le bot y est toujours à plat. Deux forces documentées s'opposent.
- Le retour de la pression de clôture : ETF à levier, ordres au cours de clôture, couverture gamma (Baltussen et al. 2021 ; Barbon et al., SFI 22-40). Bogousslavsky et Muravyev trouvent que les écarts du prix de clôture reviennent entièrement pendant la nuit, et pour moitié peu après la clôture (abstract vérifié).
- La continuation de la tendance du jour, que tiennent justement les positions de zone à 16 h.
Le test est propre : l'alignement des barres est vérifié, il y a environ 600 séances actives en exploration pour H2 à H5, et environ 1 200 séances en position pour H1. Les frais sont faibles au niveau actuel du NQ (0,5 pb).
Points faibles : le future n'a pas d'enchère de clôture (les arbitragistes absorbent une partie de la pression avant 16 h), l'heure contient les résultats des grandes valeurs, et l'élan de fin de séance a disparu sur 2023-2026 (etude_large A). Chance a priori : environ 10 % pour H1, environ 10 à 15 % pour H2 et H3.

**Pourquoi ce n'est pas déjà testé**

nuit/README.md et resultats.txt (lus) : l'heure de 16 h y est seulement décrite (+1,1 pb sur le NQ, +0,5 sur l'ES, sans condition), jamais tradée (« une prop firm intraday ne la laisse pas garder »). etude_large partie A (Gao, Baltussen), tournoi4 n°4 et sessions24 G13 jouent avant 16 h, dans le sens du jour. intraday50k/ ferme à 15 h 59. zone_retour/ et entree_tardive/ ne testent que des sorties plus tôt. Aucun essai de savoir.json ne porte sur 16 h - 17 h. Écartés de la fusion : l'achat seul de cette heure (moyenne déjà vue sur toutes les années), le retour de 18 h à 9 h 59 (chevauche N1 et le RSI(2) de nuit), et les versions miroirs (« retourner » et « dans le sens », intégrées au test bilatéral de H1 et au placebo de sens).

## Piste 3 : Renfort sur le trade qui tient : ajouter 1 MNQ au premier contrôle où la zone ne sort pas (`renfort/`, note du juge 5/10, precision zone)

**Règle exacte**

Base : les positions de V1 exactement (zone/robot.py, 1 MNQ, filtre delta à l'entrée dans le bot réel).

Un « contrôle tenu » est un contrôle qui suit l'entrée et où V1 garde sa position sans sortir. Un contrôle où V1 sort puis rachète (cas VWAP) n'est pas tenu : toutes les unités sortent, et le rachat est une nouvelle entrée d'une unité.

À un contrôle tenu, de 10 h 30 à 15 h 00, on ajoute 1 MNQ à la clôture de la minute du contrôle, dans le sens de la position. Pas de renfort à 15 h 30. Toutes les unités sortent ensemble, à la sortie de V1 (contrôle ou 15 h 59).

Frais : 1,5 point par aller-retour et par unité.

R1 : un seul renfort, au premier contrôle tenu (2 unités au plus).
R2 : un renfort au premier et au deuxième contrôle tenu (3 unités au plus).
R3 : comme R1, seulement si le gain latent au contrôle est d'au moins 0,5 × σ_m × référence, la référence étant max(ouverture, veille) pour un achat et min(ouverture, veille) pour une vente.

La série « renfort seul » est le gain net des seules unités ajoutées.

**Variantes**

3 : R1, R2, R3.

**Données**

Minutes du NQ 2011 → 20 oct. 2026 (recherche + robot) ; ES minute 2011-2026 en réplication avant frais ; kb/zone_failles/autopsie.txt pour l'ordre de grandeur (vérifié : 1 655 trades sur 2 789 passent le premier contrôle sur 2011-2022) ; moteurs de challenge delta_mesures/etude.py et etude_large/partie_d.py.

**Contrat et frais**

MNQ. 1 $ par ordre + 1 tick par côté, soit 1,5 point par aller-retour et par unité.

**Périodes**

Exploration 2011-2022 (environ 1 655 renforts possibles). Coffre 2023 → 20 oct. 2026 (environ 500).

**Critères de succès et décision**

1) Série « renfort seul » : t net ≥ 2 en exploration, retenu par Benjamini-Hochberg à 10 % sur les 17 tests.
2) Coffre : t net ≥ 1,5, même signe.
3) V1 + renfort, ramenée au même écart-type quotidien que V1 sur 2011-2022, a un Sharpe plus haut que V1 sur les deux périodes.
4) Placebo : faire mieux que 95 % de 200 placebos. Dans un placebo, le même nombre de renforts par an est placé à des contrôles tirés au hasard parmi tous ceux de 10 h 30 à 15 h 00 où la zone est en position, dans le sens de la position, avec la même sortie.
5) Lucid Flex, départs 2023-2026 : 1 + 1 MNQ doit valider au moins 3 points de plus que V1 à 1 MNQ ET que V1 à 2 MNQ (même exposition maximale), sans plus de 3 points de challenges perdus en plus. Bulenox : publié.

**Contrôles**

a) Retrouver les 1 655 trades sur 2 789 qui passent le premier contrôle (autopsie).
b) Même signe avant frais sur l'ES.
c) Résultats par année et par heure du renfort.
d) Pire séance avec renfort comparée à la limite de perte du jour de Bulenox (1 000 $) et au nombre maximal de contrats du compte.
e) Si la piste « sortie VWAP » change la base, le renfort est recalculé sur la nouvelle base, à titre d'information seulement.
f) P1 et P2 avec le vrai delta : description.

**Pourquoi**

Le résultat de la zone vient des trades longs (autopsie 2011-2022, vérifiée) : trades de 30 min −13,06 points bruts, de 1 à 2 h −3,96, de plus de 2 h +32,81, avec 78 % de gagnants pour les sorties à la clôture. Passer le premier contrôle est une information connue au moment de décider, qu'aucune règle de taille n'utilise. Ajouter à une position gagnante est la pratique classique du suivi de tendance. La règle n'a pas de paramètre libre (sauf R3, fixé à 0,5 σ) et l'échantillon est grand.
Contre : le gain restant après le contrôle est plus petit que celui calculé depuis l'entrée. Le renfort double les pertes des trades de 1 à 2 h. Et les gains par heure d'entrée sont très bruités (10 h 30 : −3,08 points nets sur 2011-2022). Chance a priori : environ 15 %.

**Pourquoi ce n'est pas déjà testé**

vague8, vague10 et vague13 (taille selon le coussin et la fin du challenge), zone_failles (taille inverse de la volatilité, qui dégrade : t +0,62 → −0,44), vague9 (trades hors condition en MES) et entree_tardive L1 fixent tous la taille à l'entrée. Aucun README ni savoir.json ne contient d'ajout pendant le trade selon sa propre tenue (cherché : renfort, pyramid, ajout).

## Piste 4 : Cassures de l'ouverture de Londres sur l'or (MGC), jugées aux frais d'aujourd'hui sur leur coffre jamais ouvert, et répliquées sur l'argent (SIL) (`or_londres/`, note du juge 5/10, source independante)

**Règle exacte**

Code de la machine 5 inchangé (kb/sessions24/machine5.py, fonction cassures). Barres HistData de 5 minutes en UTC, converties en Europe/London, jours de semaine.

F3-30 : fourchette = plus haut et plus bas des barres de 8 h 00 à 8 h 30 (heure de Londres). De 8 h 30 à 16 h 30, première clôture de 5 minutes au-dessus (achat) ou au-dessous (vente) de la fourchette. Entrée à l'ouverture de la barre suivante. Stop à l'autre extrême : sortie au stop, ou à l'ouverture si elle est déjà au-delà. Sinon, sortie à l'ouverture de la barre de 16 h 30. Un trade par jour.

F4-16:30 : fourchette de 0 h 00 à 7 h 00 (Londres), cassure cherchée de 7 h 00 à 12 h 00. Entrée et stop identiques, sortie à 16 h 30 (Londres).

Frais principaux (convention de la partie D, en pb au prix d'aujourd'hui) :
- MGC : 2 × 1 $ + 2 ticks × 1 $ = 4 $ sur 41 460 $, soit 0,96 pb ;
- SIL : 2 × 1 $ + 2 × 5 $ = 12 $ sur 57 860 $, soit 2,1 pb.
Sensibilité : 2 pb MGC et 3 pb SIL. Pour information : frais fixes en dollars au prix de chaque jour.

**Variantes**

4 : F3-30 or, F4-16:30 or, F3-30 argent, F4-16:30 argent. Aucun réglage nouveau.

**Données**

Vérifié par le juge :
- kb/sessions24/annees/xauusd_2012..2026_5m.csv.gz (UTC, colonnes t,o,h,l,c, jusqu'au 2 oct. 2026) ;
- donnees_libres/histdata_5min/xagusd_2012..2026_5m.csv.gz (même format ; 2023 incomplet d'environ 13 %, d'après le chercheur) ;
- donnees_libres/yahoo/jour/GC et SI (clôtures du 21 oct. 2026 : 4 146 $ et 57,86 $) ;
- donnees_libres/yahoo/heure/GC, SI et MGC, pour le contrôle.

**Contrat et frais**

MGC (10 onces, tick 0,10 $ = 1 $) et SIL (1 000 onces, tick 0,005 $ = 5 $), 1 contrat. Position de 3 h - 7 h à environ 11 h 30 (New York), dans la fenêtre permise de 18 h à 16 h 59.

**Périodes**

Or : l'exploration 2012-2022 a déjà servi à choisir ces deux règles (avant frais : F3 t 3,14, F4 t 2,82). Elle n'est donc rejugée qu'aux nouveaux frais. Coffre 2 janv. 2023 → 2 oct. 2026, jamais ouvert (sessions24 : « il reste vierge »).
Argent : jamais testé en séance. Exploration 2012-2022, coffre 2023 → 16 oct. 2026.

**Critères de succès et décision**

1) Or, exploration aux nouveaux frais : t net ≥ 2. Argent, exploration : t net ≥ 2. Tous deux retenus par Benjamini-Hochberg à 10 % sur les 17 tests.
2) Coffre : t net ≥ 1,5 sur l'or et sur l'argent, même signe, et au moins 3 années positives sur 4 pour l'or.
3) Une règle n'est retenue que si elle passe sur l'or ET sur l'argent : la réplication tient compte de la sélection parmi 158 stratégies. Si l'or passe seul, la règle n'est que suivie en argent virtuel.
4) Placebo : faire mieux que 95 % de 1 000 tirages du sens au hasard, aux mêmes heures, sur l'argent en exploration et sur l'or au coffre.
5) t > 0 aux frais de sensibilité, et aux frais fixes en dollars au prix du jour sur le coffre.
6) Partie C : corrélation des séances avec la zone < 0,3, et Sharpe zone + MGC (à risque égal) plus haut que la zone seule au coffre.
7) Lucid Flex 50K, zone 1 MNQ + 1 MGC : au moins 3 points de validés de plus, sans plus de 3 points de challenges perdus en plus.

**Contrôles**

a) Avant d'ouvrir le coffre, le code doit redonner les chiffres publiés de l'or en exploration (F3 +2,84 pb, t 3,14 ; F4 +3,20 pb, t 2,82).
b) Corrélation d'au moins 0,95 entre les rendements HistData de 3 h à 11 h (New York) et les barres d'une heure Yahoo GC et SI (30 mai 2024 → 21 oct. 2026). Sinon, arrêt.
c) Compter les barres manquantes par année (argent 2023), et vérifier le changement d'heure à Londres.
d) Publier F3 par sous-période (déclin connu : environ +0,7 pb avant frais en 2020-2022).
e) Avant tout essai réel : vérifier que les métaux sont permis chez Bulenox et Lucid, la commission réelle et l'écart à 3 h du matin sur le MGC.

**Pourquoi**

Ce sont les deux effets avant frais les plus nets de la machine 5 sur l'or (placebo p ≤ 0,002, retenus par Benjamini-Hochberg), rejetés seulement parce que 2 pb de frais les mangeaient (t net 0,92 et 1,06). Au prix actuel de l'or, un MGC coûte 0,96 pb. Le recalcul à partir des chiffres publiés donne un t net d'environ 2 en exploration : (2,84 − 0,96) / 2,84 × 3,14 ≈ 2,1 pour F3, environ 1,9 pour F4.
Le coffre de l'or n'a jamais été ouvert, et l'argent offre une réplication sur un marché frère (place de Londres), sur des années jamais vues. C'est une source sur un autre marché et à un autre moment, avant 10 h, donc peu liée à la zone.
Contre : il y a eu sélection parmi 158 stratégies, F3 décline, le coffre est court (t attendu d'environ 1,1 à 1,2 si l'effet est réel), et les prix sont ceux du comptant. Chance a priori : environ 8 à 10 %.

**Pourquoi ce n'est pas déjà testé**

sessions24/README.md (lu) : F3 et F4 sur l'or ont été jugés à 2 pb fixes, sans ouvrir le coffre. L'argent n'est pas dans la machine 5 : il a été téléchargé après, pour l'étude large, et n'a jamais été testé en séance. zone_multi (zone sur le GC aux heures du COMEX, t −2,19), tournoi5 B3 et etude_large A2b (GLD de 15 h 30 à 16 h) portent sur d'autres heures et d'autres règles. evolution3 (cassures sur le GC en 5 minutes) se limite aux heures du COMEX, pas à l'ouverture de Londres.

## Piste 5 : Copies décalées de la zone : contrôles à :00 et :30 plus une copie à :15 et :45, pour diversifier la chance de l'horaire (`zones_decalees/`, note du juge 4.5/10, precision zone)

**Règle exacte**

D0 = V1 (contrôles de 10 h 00 à 15 h 30).

D15 = la même règle exacte (σ de la minute du contrôle sur 14 séances complètes, mêmes limites, VWAP, sortie si C repasse max(ub, VWAP) ou min(lb, VWAP), et même mécanique de rachat que V1), avec des contrôles à 10 h 15, 10 h 45 … 15 h 45 et à plat à 15 h 59.

Pour E3 : D10 (10 h 10 … 15 h 40) et D20 (10 h 20 … 15 h 50), construites de la même façon.

Chaque copie a sa propre position de 1 MNQ et ses propres frais (1,5 point par aller-retour). Dans le bot, son filtre delta porte sur les 30 minutes qui finissent à SON contrôle. Pas de zone les jours de la Fed ni les jours courts. La compensation des ordres entre copies dans le même compte n'est pas comptée (prudent).

**Variantes**

E2 = D0 + D15 (2 MNQ), comparée à V1 à 2 MNQ. E3 = D0 + D10 + D20 (3 MNQ), comparée à V1 à 3 MNQ. Tests comptés dans Benjamini-Hochberg : D15 seule, D10 seule, D20 seule (3).

**Données**

Minutes du NQ 2011 → 20 oct. 2026 (σ disponible à chaque minute dans preparer() de delta_mesures/etude.py) ; P1 et P2 avec le vrai delta ; moteurs de challenge Bulenox et Lucid (partie D).

**Contrat et frais**

MNQ, 1 par copie, 1,5 point par aller-retour (1 $ par ordre + 1 tick par côté).

**Périodes**

Exploration 2011-2022, coffre 2023 → 20 oct. 2026. Les grilles décalées n'ont jamais été calculées : leurs trades sont jamais vus sur toutes les années.

**Critères de succès et décision**

1) Chaque copie décalée seule : t net ≥ 2 en exploration (Benjamini-Hochberg à 10 % sur les 17 tests) et t net ≥ 1,5 au coffre. Repère : V1 fait +2,12 et +1,86 (entree_tardive).
2) Sharpe quotidien de E2 plus haut que celui de V1 à 2 MNQ sur les deux périodes (E3 contre V1 à 3 MNQ).
3) Lucid Flex, départs 2023-2026 : E2 valide au moins 2 points de plus que la meilleure de V1 à 1 MNQ et V1 à 2 MNQ, sans plus de 2 points de challenges perdus en plus.
Pas de placebo de sens pertinent pour une diversification : il est remplacé par l'exigence que chaque copie passe seule, comme une stratégie complète. Bulenox (30 jours) : publié.

**Contrôles**

a) D0 recalculée doit redonner V1 exactement (3 572 trades, +10 721 points).
b) Publier la corrélation quotidienne D0/D15 (le gain de Sharpe n'existe que si elle est nettement sous 1).
c) Résultats par heure de contrôle, pour voir si :00 et :30 a un avantage propre (annonces de 10 h).
d) P1 et P2 avec le vrai delta : description.
e) Rapprocher du rang de 99 % de la grille de robustesse : si les copies décalées sont nettement moins bonnes, une partie du résultat de V1 tient à l'horaire.

**Pourquoi**

L'horaire des contrôles est arbitraire. Les gains par heure d'entrée s'inversent d'une période à l'autre (autopsie : 10 h 30 à −3,08 points nets, 11 h 30 à +5,97), ce qui est la marque d'une chance liée à l'horaire (Hoffstein, Faber et Braun 2020). Une copie décalée a en principe la même espérance, mais d'autres trades. La jouer à côté baisse la variance sans rien régler sur le passé, et chez Lucid Flex le Sharpe décide (partie D1). La règle n'a aucun paramètre libre : les décalages sont fixés par symétrie.
Contre : V1 est au 99e centile de la grille, donc une partie de son résultat peut venir de l'horaire :00 et :30. Les copies seront très corrélées, et le gain attendu est modeste (environ 10 à 20 % de Sharpe). Chance a priori que tout passe : environ 15 %.

**Pourquoi ce n'est pas déjà testé**

zone_optimisation/README.md (lu) : l'intervalle de 15 minutes (t 0,98) est UNE position contrôlée deux fois plus souvent, pas une seconde grille au rythme de 30 minutes. G3 réunissait 10 réglages différents choisis sur le passé (t 1,29 au coffre). robustesse/ fait varier l'intervalle, pas le décalage de départ. Aucun README ne contient de grille décalée (cherché : décalage, :15, 10 h 15).

## Résultats (22 octobre 2026)

Cinq agents ont codé chacun une piste selon les règles ci-dessus (`<dossier>/etude.py` → `<dossier>/resultats.txt`),
avec les contrôles demandés. Chaque moteur redonne la zone de `delta_mesures/` trade par trade, et le moteur des
challenges redonne la partie D. Chaque agent a fait un recalcul indépendant et un test de regard vers le futur
(brouiller tout ce qui suit la décision ne change aucune décision). Benjamini-Hochberg à 10 % sur les 17 tests :
seuil p ≤ 0,0052, **2 tests retenus** (R1 et R2).

| Piste | Test | t exploration | t coffre | BH | Autres critères | Verdict |
|---|---|---|---|---|---|---|
| 1 Sortie VWAP | ZW − ZL (sortir pour de bon, contre tenir) | −0,37 | +0,78 | non | non | échoue |
| | ZW+ − ZL | −0,62 | +0,24 | non | non | échoue |
| 2 Heure de 16 h | H1 prolonger la zone | −0,36 (retourner : −1,81) | +1,49 | non | non | échoue |
| | H2 retour de la journée, NQ | −0,49 | −0,20 | non | non | échoue |
| | H3 retour de la dernière demi-heure | −2,12 | −1,96 | non | non | échoue |
| | H4 retour de la journée, ES | −2,22 | −1,60 | non | non | échoue |
| | H5 version Lucid (16 h - 16 h 15) | +0,61 | +0,18 | non | placebo oui, le reste non | échoue |
| **3 Renfort** | **R1 : 1 MNQ de plus au premier contrôle tenu** | **+2,65** | **+1,72** | **oui** | coffre, Sharpe, placebo (98 %) oui ; **challenge Lucid non** | **échoue au critère 5** |
| | **R2 : renfort aux deux premiers contrôles tenus** | **+2,56** | **+1,76** | **oui** | coffre, Sharpe, placebo (100 %) oui ; **challenge Lucid non** | **échoue au critère 5** |
| | R3 : renfort si le gain latent ≥ 0,5 σ | +1,04 | +0,23 | non | non | échoue |
| 4 Or à Londres | F3-30 or (MGC) | +2,07 | +0,38 | non | non | échoue |
| | F4-16:30 or (MGC) | +1,97 | +1,49 | non | placebo du coffre 2,8 %, Sharpe zone + MGC 1,21 contre 1,04 ; argent et Lucid non | échoue de justesse |
| | F3-30 argent (SIL) | −2,58 | −1,34 | non | non | échoue |
| | F4-16:30 argent (SIL) | −0,41 | −0,01 | non | non | échoue |
| 5 Zones décalées | D15 | +1,09 | +1,16 | non | non | échoue |
| | D10 | +1,52 | +1,80 | non | non | échoue |
| | D20 | +1,32 | +1,55 | non | non | échoue |

**Décision fixée d'avance : aucune piste ne passe tous ses critères.** Rien n'entre au bot. La contre-vérification
adverse n'a pas eu lieu, puisqu'aucun test ne l'atteignait.

### Ce qu'on apprend quand même

1. **Le renfort est la seule idée qui tienne au niveau des trades.** Ajouter 1 MNQ au premier contrôle où la zone tient
   rapporte +3,0 points nets par renfort sur 2011 - 2022 (1 511 renforts), puis +10 points au coffre (469 renforts).
   Il bat 98 % des placebos, qui ajoutent un renfort à un contrôle tiré au hasard. **Mais il échoue au challenge** :
   - chez Lucid Flex, 1 + 1 MNQ valide 30,5 % des challenges (68 % de perdus), contre 54,6 % pour le bot à 1 MNQ et
     31,7 % à 2 MNQ ;
   - le renfort ajoute de l'avantage, mais il ajoute surtout du risque, comme une taille plus grande ;
   - en rendement (points ÷ prix), son t d'exploration tombe à +1,37 : il vient surtout de 2018 - 2022, quand un point
     du NQ valait le plus, et seules 5 années d'exploration sur 12 sont positives.
2. **La sortie au VWAP n'a pas d'effet mesurable.** Le juge avait trouvé que le bot réel (filtre delta) sort vraiment
   dans ces cas, alors que les backtests tiennent la position (382 cas en 15 ans). Les deux font la même chose à
   peu près (t −0,37 et +0,78) : **les backtests restent valables pour le bot réel**. Sur avril - octobre 2026, les
   11 rachats de ce type ont tous été écartés par le filtre ; sans filtre, ils auraient coûté 340 points.
3. **L'or à l'ouverture de Londres passe près du seuil** (F4 : +1,97 puis +1,49, coffre jamais ouvert jusqu'ici, bat
   97 % des placebos au coffre), mais il ne se réplique pas sur l'argent et il fait baisser la réussite chez Lucid.
   Ambiguïté signalée : le code inchangé de la machine 5 cherche la cassure jusqu'à 16 h 30 (Londres), le README
   écrivait 12 h ; la version coupée à 12 h n'a pas été calculée pour ne pas ajouter de variante.
4. **L'heure de 16 h à 16 h 59 ne donne rien**, ni pour prolonger la zone, ni pour jouer le retour de la clôture.
5. **Les copies décalées sont moins bonnes que la zone** (t +1,1 à +1,5 contre +2,17) : les contrôles à :00 et :30
   ne sont pas une chance de l'horaire à diversifier.
