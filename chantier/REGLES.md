# Chantier du 11 novembre 2026 : six modèles et la nuit (règles fixées avant tout calcul)

## Demande de l'utilisateur (11 novembre 2026)

Tester les modèles envoyés, tuer les mauvais, garder les meilleurs, et continuer à chercher s'il ne reste rien.
Les modèles du message :

| # | Modèle du message | Ce qui est testé ici, sur les futures |
|---|---|---|
| A | Un bot qui reconnaît le régime du marché (latéral, volatil, chute) et s'adapte | partie A |
| B | « Vol-crush » : vendre quand la volatilité implicite dépasse la volatilité réalisée | partie B |
| C | La machine auto-évolutive « SETS » (robots de grille à 8 gènes, 4 espèces, 70 / 30) | partie C |
| D | Le pipeline qui suit les baleines et les initiés | déjà jugé : `radar/` et `flux/` (branche `claude/optimistic-ptolemy-xs24ra`), barres non franchies ; pas refait |
| E | La session qui tourne de l'or à l'argent puis à Nvidia avec des stops suiveurs | partie E |
| F | Le bot MT5 or H1 : EMA 50 / 200, RSI, ATR, stop, objectif, stop suiveur | partie F |

Et la piste laissée ouverte par la vague 9 de l'arène (« le passage au compte financé, avec un stop, sera une vague à
part ») : la nuit, partie N.

**Ce qui est promis.** Chaque modèle est joué avec ses règles écrites ici, des frais réels et des données que la
règle n'a pas vues. Un modèle qui ne passe pas est tué et le reste. Aucun gain n'est promis : 1,5 million de
stratégies ont déjà été jugées dans ce projet et une seule a tenu 15 ans (la zone de bruit).

## Cadre commun

- **Données** (déjà dans le projet, rien de neuf n'est téléchargé) :
  - minutes du NQ, séance 9 h 30 - 16 h (New York) : `intraday/donnees/nasdaq100_1min.csv.gz` (branche
    `claude/keen-babbage-r686cl`, 2011 → 25 sept. 2026), prolongées par `zone/robot/nq_1min.csv.gz` (`main`) ;
  - Nasdaq 24 h sur 24, barres de 5 minutes en UTC : `sessions24/annees/usatechidxusd_*` (Dukascopy, prix acheteur,
    2012 → 2 oct. 2026). Or : `xauusd_*` ;
  - VIX, VIX3M, VXN à la clôture : `donnees_libres/` (branche `claude/affectionate-turing-tnz0mn`) et `radar/` ;
  - minutes de ES, RTY, YM, or, pétrole, euro : `intraday/` et `zone_multi/` ;
  - bitcoin en 5 minutes : `donnees_libres/crypto/`.
- **Gain au prix d'aujourd'hui** (comme l'arène) : sens × (sortie − entrée) × 2 $ × 28 500 ÷ entrée − frais, pour 1 MNQ.
- **Frais** : 3 $ par aller-retour et par MNQ (1 $ et 1 tick par ordre). Or (MGC) : 4 $. Autres micros : tableau de
  `scalping/README.md`. Bitcoin : 4 points de base par aller-retour.
- **Périodes** : exploration jusqu'au 31 décembre 2022 ; contrôle du 1er janvier 2023 à la fin des données. Le
  coffre 2023 - 2026 a déjà été ouvert pour d'autres familles : ici c'est une période de contrôle, pas un coffre
  vierge. Le seul juge neuf reste l'avenir (suivi virtuel).
- **t** : moyenne des gains nets par séance ÷ (écart type ÷ √n), toutes les séances jouables comptées (0 $ les jours
  sans trade).
- **Tests multiples** : Benjamini-Hochberg à 5 % dans chaque partie.
- Signal à la clôture d'une barre, ordre à l'ouverture de la suivante. Dans une barre, la perte compte avant le gain.
  Un stop est rempli à son niveau moins 1 tick (ou à l'ouverture si elle est déjà au-delà). Un objectif n'est rempli
  que si le prix le traverse d'un tick.

## Partie N : la nuit avec un stop, dans le contrat Master

Sources : Kelly et Clark (2011) ; Boyarchenko, Larsen et Whelan (2023) ; vague 9 de l'arène (N1 sans stop : t 3,08,
pire nuit −3 658 $, donc « piste seulement »).

- **Règle** : achat de 1 MNQ à l'ouverture de la première barre de 5 minutes à partir de 18 h (New York), vente à
  l'ouverture de la barre de 9 h 30. Nuits du dimanche au jeudi soir. Une nuit est jouable si elle a au moins
  150 barres entre 18 h et 9 h 30 et si la séance du lendemain est complète dans les minutes du NQ.
- **Stops** (niveau fixé à l'entrée, lu sur les barres de 5 minutes) : aucun ; 0,50 % ; 0,75 % ; 1,00 % sous l'entrée.
- **Filtres** (connus à 16 h 15 le jour de l'entrée) :
  - F0 : toutes les nuits ;
  - F1 : pas de nuit si VIX ≥ VIX3M à la clôture (courbe inversée, le filtre VIX du bot) ;
  - F2 : seulement après une séance en baisse (clôture de 15 h 59 sous l'ouverture de 9 h 30) ;
  - F3 : seulement si VXN ÷ volatilité réalisée sur 20 séances dépasse sa médiane des 252 séances d'avant (« la peur
    est chère », lien avec le modèle B).
- 4 stops × 4 filtres = **16 variantes**.
- **Retenue comme module** si, à la fois :
  1. t ≥ 2 sur toute la période et retenue par Benjamini-Hochberg (16 tests) ;
  2. gain moyen positif en exploration et au contrôle ;
  3. t ≥ 1,5 avec 6 $ de frais ;
  4. au moins 10 années positives sur 15 ;
  5. pire nuit au-dessus de −1 100 $ (une nuit seule ne doit pas pouvoir toucher la limite du jour de Bulenox).
- Pour information : la séance de jour (9 h 30 → 15 h 59, achat) sur les mêmes dates, et la différence nuit − jour.

**Dans le compte** (pour 2 variantes retenues au plus : les 2 meilleurs t avec des filtres différents). Simulateur
repris de la vague 10 (`ml/arene/vague10.py`, fonction `vie_contrat`) :
- contrat Master 50K Option 2 : plancher à 2 500 $ sous le plus haut des fins de journée, arrêté à 50 000 $, contrôlé
  en temps réel ; retraits après 10 jours tradés, de 1 000 à 1 500 $, 52 600 $ gardés, meilleure journée ≤ 40 % du
  gain ; 90 % pour le trader ; activation 148 $ ; fin du Master au 3e retrait ; 5 jours de trading sans trade = compte
  perdu ;
- le bot : journal de rejeu C2 + Q1 de la zone, sans les jours de VIX inversé ni les jours de la Fed (« Z12F »),
  limite du jour 1 000 $, frein (demi-taille sous 1 750 $ de marge) ;
- la nuit appartient à la journée de trading du lendemain : sa perte entame la limite du jour, et une nuit qui
  touche la limite annule la zone ce jour-là. Un trade de nuit compte comme un trade.
- **Contrôle du simulateur** : T0 (le bot seul) doit redonner les chiffres publiés de la vague 10 (101 séries de
  5 jours sans trade, 99 % de Masters perdus par l'inactivité), à 2 points près.
- **Adoptée** si : aucun Master perdu par inactivité ; au plus 20 % de Masters perdus avant le 3e retrait ; gain moyen
  touché par Master positif. On donne le nombre de dates de perte distinctes (moins de 3 = chiffre fragile).

### Partie N, vague 2 (règles écrites le 11 novembre 2026, après le résultat de la vague 1 et avant tout calcul de la vague 2)

Résultat de la vague 1 : la nuit avec stop passe ses 5 conditions, mais à 1 MNQ chaque nuit elle bouge deux fois
plus que le bot (370 $ contre 188 $ d'écart type par séance) : 43 % des Masters sont perdus par le plancher. Elle
n'est pas adoptée. Le bot seul, lui, ne perd aucun compte par le plancher : il les perd tous par l'inactivité.

D'où trois candidats, jugés par la même règle d'adoption (aucun Master perdu par inactivité ; au plus 20 % perdus
avant le 3e retrait ; touché moyen positif) :

| | Règle |
|---|---|
| NS75 | **nuit de secours** : la nuit F0 avec stop 0,75 % n'est prise que si le compte vient de passer 3 jours de trading de suite sans trade (jours du fichier compris, comme Bulenox compte), puis chaque nuit jusqu'au premier trade |
| NS50 | la même avec le stop à 0,50 % |
| N50 | la nuit F0 avec stop 0,50 % chaque nuit (le plus petit risque retenu par la vague 1) |

- Une nuit absente du fichier (trous de 2023 dans les données de nuit) ne peut pas être jouée : le compteur continue.
  Une perte par inactivité qui vient d'un trou du fichier est comptée et signalée à part.
- Référence publiée (vague 10) : K1c, le modèle W1 en secours : 70 % au 3e retrait, 10 % perdus par le plancher,
  2 949 $ touchés par Master, 2 dates de perte distinctes.
- Réserve écrite d'avance : le contrat ne compte pas une « activité artificielle destinée uniquement à prévenir
  l'inactivité ». Une nuit de secours est une vraie stratégie (elle a passé ses conditions seule), mais elle est
  déclenchée par le compteur : comme K1, elle dépend de la réponse écrite de Bulenox.

## Partie I : tenir la règle d'inactivité avec la zone elle-même (règles écrites le 11 novembre 2026, après les parties A à F et N, avant tout calcul de cette partie)

Ce que les parties précédentes ont montré : le bot seul ne perd aucun Master par le plancher, il les perd par
l'inactivité (5 jours de trading sans trade). Une nuit en secours ne suffit pas et coûte des comptes. Ici, le secours
est la stratégie du bot elle-même, rendue plus sensible : pas de modèle d'apprentissage (section 20 du contrat non
concernée), pas de seconde stratégie.

- **Zone brute** : la zone corrigée V1 (`zone_failles/journal.py`, `zone_optimisation/moteur.py`) recodée ici avec
  ses trades : bande = k × mouvement moyen des 14 séances complètes d'avant, contrôles toutes les 30 minutes, sortie
  au retour sous la limite ou la VWAP, à plat à 16 h, pas de trade le jour d'un changement de contrat. Aucun filtre
  (ni C2, ni Q1, ni VIX, ni Fed). **Contrôle** : à k = 1, elle doit redonner les trades de `filtre_h1/trades_zone.csv`.
- **Jour de secours** : une séance qui commence après 3 jours de trading de suite sans trade (jours du fichier
  compris). Ce jour-là, le bot joue la zone brute à la bande k à la place de ses réglages habituels, 1 MNQ.
- **Candidats** : IB100 (k = 1), IB75 (k = 0,75), IB50 (k = 0,5).
- Pour chaque k, l'avantage de la zone brute est donné (t sur toute la période, exploration, contrôle) : une bande plus
  étroite trade plus souvent mais gagne moins (`zone_optimisation` : t 0,58 à k = 0,75 sur son contrôle).
- **Adoptée** : même règle que la partie N (aucun Master perdu par inactivité ; au plus 20 % perdus avant le 3e
  retrait ; touché moyen positif), sur 2017 → 2 novembre 2026. Si plusieurs passent : celle qui perd le moins de
  Masters, puis la bande la plus large.
- Même réserve : un trade déclenché par le compteur peut être vu par Bulenox comme une activité artificielle. La
  réponse écrite de Bulenox passe avant ce calcul.

## Partie A : les régimes

**Détecteur** (état de la séance, connu la veille à 16 h 15) :
- volatilité = écart type des 20 derniers rendements quotidiens (clôture à clôture), classé parmi ses 252 valeurs
  d'avant ;
- tendance = |somme des 20 rendements| ÷ (écart type × √20) ;
- inversé = VIX ≥ VIX3M ; chute = rendement sur 5 séances dans les 10 % les plus bas des 252 d'avant.

| État | Condition (dans cet ordre) |
|---|---|
| CHUTE | inversé ou chute |
| VOLATIL | volatilité dans le tiers haut |
| TENDANCE | tendance ≥ 1 |
| CALME | le reste (marché latéral) |

**Tests** (stratégies : la zone C2 + Q1 sans filtre VIX ni Fed ; la nuit F0 sans stop ; le Supertrend 10-3 ; un retour
à la moyenne fixe : à 10 h 30, position contre le mouvement depuis l'ouverture s'il dépasse 0,5 fois l'écart type
quotidien, sortie 15 h 55) :
- A1, descriptif : gain moyen et t de chaque stratégie dans chaque état, en exploration et au contrôle.
- A2, en marche avant : chaque année de 2017 à 2026, pour la zone puis pour la nuit, on coupe la stratégie dans les
  états où son gain moyen des années d'avant est négatif (au moins 60 séances dans l'état). **Adopté** si, sur
  2017 - 2026, la version filtrée fait un t et un gain total supérieurs à la version toujours active, **et** bat
  95 % de 500 placebos (les mêmes états mélangés par blocs de 20 séances).
- A3 : la même règle pour « retour à la moyenne dans l'état CALME seulement » (ce que promet le modèle A : changer de
  stratégie quand le marché est latéral). **Retenu** si t ≥ 2 sur toute la période, positif en exploration et au
  contrôle.

## Partie B : volatilité implicite contre volatilité réalisée

Les options et les futures VIX ne sont pas permis chez Bulenox : la vente de volatilité elle-même n'est pas jouable
sur le compte. Trois mesures :
- B0, descriptif : VXN moins la volatilité réalisée des 21 séances suivantes ; ce que donnerait la vente chaque
  soir d'un straddle à un jour au prix du VXN (prime 0,8 × VXN ÷ √252 moins le mouvement du lendemain), et son pire
  jour ;
- B1 : la nuit filtrée F3 (partie N) ;
- B2, la version futures de « vendre les deux côtés » : bande = ouverture ± VXN ÷ 100 ÷ √252 × ouverture. Entre
  9 h 35 et 15 h, au premier contact d'un bord : position contre (vente en haut, achat en bas), stop à 1,5 bande de
  l'ouverture, sortie 15 h 55, un trade par séance. B2a : toutes les séances ; B2b : seulement si F3 est vrai.
  **Retenue** si t ≥ 2, positive en exploration et au contrôle, et Benjamini-Hochberg sur B2a et B2b.

## Partie C : la machine auto-évolutive (SETS)

Construite comme le message la décrit, puis jugée sur des données qu'elle ne voit jamais et contre du hasard.

- **Données** : NQ en barres de 5 minutes (séance), 1 MNQ de base. Histoire de la machine : 2017 - 2022, les 70 %
  premiers en entraînement, les 30 % derniers en test. **Contrôle : 2023 → fin des données, jamais vu.**
- **Génome (8 gènes)** : espèce (élan, retour à la moyenne, cassure de volatilité, grille de fourchette) ; recul
  (6 à 78 barres) ; seuil d'entrée (0,5 à 3) ; niveaux de grille (1 à 6) ; espacement (0,25 à 2 u) ; multiplicateur
  de taille (1 à 2) ; prise de profit (0,25 à 4 u) ; stop (0,5 à 6 u). u = prix × écart type des rendements de
  5 minutes des 20 séances d'avant × √6.
- **Entrées** (à la clôture d'une barre, ordre à l'ouverture suivante) :
  - élan : rendement sur le recul ÷ (écart type × √recul) au-delà du seuil, dans son sens ;
  - retour : la même mesure, à contresens ;
  - cassure de volatilité : clôture au-delà du plus haut ou du plus bas du recul, avec une barre d'au moins seuil fois
    l'amplitude moyenne du recul, dans le sens de la cassure ;
  - grille de fourchette : écart à la moyenne du recul ÷ écart type du recul au-delà du seuil, à contresens.
- **Grille** : tant que le prix part contre la position, un niveau de plus à chaque espacement, taille multipliée à
  chaque niveau. Tout est fermé à la prise de profit ou au stop, comptés depuis le prix moyen, et à 15 h 55.
- **Boucle** : 96 stratégies par génération ; 8 nouvelles tirées au hasard ; 80 enfants des meilleurs parents
  (croisement, mutation) ; les 8 meilleures gardées ; quotas : chaque espèce a entre 12 et 48 places ; 40
  générations. Score d'entraînement : gain net ÷ pire baisse, au moins 100 trades.
- **Mort** (le texte) : sur le test, perte d'argent, ou baisse de plus de 10 % (5 000 $ pour 50 000 $), ou moins de
  la moitié de trades gagnants. L'élite = les survivantes ; le champion = le meilleur gain ÷ pire baisse du test.
- **Graines** : 6 sur les vraies données ; 6 sur chacun de deux faux marchés (rendements permutés entre séances à
  la même heure ; signes tirés au hasard). Les élites trouvées sur un faux marché sont ensuite jouées sur les
  **vraies** données de contrôle : ce sont les placebos.
- **Jugement au contrôle** :
  - part des élites en gain ; part avec t ≥ 1,65 ; gain et t du champion de chaque graine ;
  - compte Bulenox (1 MNQ de base, tailles de grille arrondies, plancher 2 500 $, limite du jour 1 100 $) : part
    des comptes neufs perdus en 60 séances (un départ toutes les 20 séances).
- **La machine trouve quelque chose** si la part des élites réelles à t ≥ 1,65 dépasse celle de chacune des
  12 machines de bruit **et** si le champion a un gain positif avec t ≥ 1,65 pour au moins 4 graines sur 6. Sinon elle
  est tuée : elle fabrique des stratégies qui ont l'air bonnes sur le test et ne valent rien après.
- **Pour information** : la même machine sur le bitcoin en 5 minutes (histoire 2019 - 2022, contrôle 2023 - 2026,
  position fermée après 24 h au plus).

## Partie E : la rotation entre marchés

Marchés : NQ, ES, RTY, YM, or, pétrole, euro (minutes, 1 micro chacun), fenêtre commune 9 h 30 - 13 h 25,
juillet 2017 → septembre 2026.
- Toutes les 15 minutes de 9 h 45 à 13 h : score = ln(prix ÷ ouverture de 9 h 30) ÷ s, où s est l'écart type du
  mouvement 9 h 30 → 13 h 25 de ce marché sur les 60 séances d'avant.
- Le meneur est le marché au plus grand |score|. Si |score| ≥ 1 : 1 micro du meneur, dans le sens de son score. On
  change de marché quand le meneur change ; sortie si son |score| repasse sous 0,5 ; stop suiveur à 0,5 s du meilleur
  prix depuis l'entrée (clôtures d'une minute) ; à plat à 13 h 25.
- **Retenue** si t ≥ 2 sur toute la période, positive en exploration et au contrôle, et au-dessus de 95 % de
  1 000 placebos (le sens de chaque trade tiré au hasard).

## Partie F : EMA 50 / 200, RSI et ATR en barres d'une heure

Marchés : or (MGC) et Nasdaq (MNQ), barres d'une heure faites des barres de 5 minutes, 2012 → octobre 2026.
- **Achat** à la clôture d'une heure si clôture > EMA 50 > EMA 200, RSI(14) ≥ 55 et ATR(14) ≥ sa médiane des
  240 heures d'avant (marché pas mort). **Vente** : le miroir (RSI ≤ 45).
- Stop à 1,5 ATR, objectif à 3 ATR ; dès 1,5 ATR de gain, le stop suit à 1,5 ATR de la meilleure clôture.
- Plus d'entrée de la journée après 3 pertes de suite. À plat de 16 h 55 à 18 h (New York), comme l'exige Bulenox.
- **Retenue** (par marché) si t ≥ 2, positive en exploration et au contrôle, au-dessus de 95 % de 1 000 placebos (sens
  de chaque trade tiré au hasard), et Benjamini-Hochberg sur les 2 marchés.

## Le système (construit dans tous les cas)

- `systeme/regime.py` : l'état du marché chaque matin (affiché ; il ne change les ordres que si la partie A passe).
- `systeme/garde.py` : le contrôle avant chaque ordre : marge avant le plancher, limite du jour (nuit comprise),
  taille maximale, jours de la Fed, compteur d'inactivité, et une limite de baisse réglable (15 % par défaut pour un
  compte personnel ; sur Bulenox, le plancher de 2 500 $ passe avant).
- `systeme/rapport_matin.py` : la revue des transactions de la veille (fichier exporté par le bot) : chaque trade,
  ce qui s'écarte des règles, le coût du glissement, la marge restante, à lire le lendemain matin.

## Contre-revue (#ultrareview)

Un relecteur indépendant recalcule avec son propre code les chiffres qui décident (partie N, partie C) et cherche
les regards vers le futur. Ses défauts sont corrigés et listés dans `RESULTATS.md`.

## Correction des données 24 h (12 novembre 2026, constat de la contre-revue)

La contre-revue indépendante a été coupée par la limite d'utilisation avant d'écrire son rapport ; ses calculs sont
repris ici. Elle a recalculé la partie N avec son propre code et retrouvé les mêmes chiffres au dollar près. Elle a
trouvé un défaut des données : depuis 2019, les fichiers 24 h du dépôt (Dukascopy) sont **en avance de 60 minutes**
pendant les semaines où les États-Unis et l'Europe n'ont pas la même heure d'été (du 2e au dernier dimanche de mars ;
du dernier dimanche d'octobre au 1er dimanche de novembre). Preuve : sur ces 139 séances, les rendements de 5 minutes
du fichier suivent le future NQ à +60 minutes (corrélation 1,00) et pas à l'heure du fichier ; aucun cas ailleurs.
Tous les marchés 24 h du dépôt ont le même décalage (réouverture du soir à 21 h UTC au lieu de 22 h).

Correction : +60 minutes sur ces barres, dans `donnees.cfd()`. Tous les résultats qui lisent ces fichiers sont
relancés **sans changer leurs règles** (partie N et compte, parties A, E et F) ; les anciens chiffres sont gardés
dans `resultats/avant_correction/`.

## Partie G : copier les institutions et les banques (règles écrites le 12 novembre 2026, avant tout calcul de cette partie)

Demande : « et si tu suivais certains gros portefeuilles, certaines institutions ou banques et si tu me faisais
copier ? »

Déjà fait dans le projet (`flux/README.md`, partie 7, 29 octobre 2026, branche `claude/optimistic-ptolemy-xs24ra`) :
les positions déclarées chaque semaine à la CFTC sur le E-mini Nasdaq-100 par les gestionnaires d'actifs, les fonds à
levier et les banques ; cinq règles G1 à G5 jouées **en séance** (9 h 35 → 15 h 55) : aucune ne passe (t de −0,78 à
+1,33 en exploration). Ce qui n'a pas été jugé : tenir la position **comme eux**, nuit comprise, alors que la hausse
du Nasdaq se fait surtout la nuit (partie N).

- **Données** : les mêmes 1 063 rapports hebdomadaires (`flux/donnees/cot/cot_nq.csv`, 13 juin 2006 → 20 octobre
  2026). Positions du mardi, publiées le vendredi à 15 h 30 : un rapport sert à partir du premier jour de trading
  qui suit sa publication (la nuit du dimanche soir, puis la séance du lundi).
- **Signaux** : les cinq de la partie 7, sans rien changer : G1 sens de la variation sur 4 semaines de la position
  nette des gestionnaires d'actifs (÷ positions ouvertes) ; G2 la même pour les fonds à levier ; G3 contre les fonds
  à levier quand leur position est extrême (z sur 52 semaines au-delà de ± 1,5) ; G4 sens de la variation sur
  4 semaines de la position nette des banques et teneurs de marché ; G5 G1 et G2 d'accord, sinon rien.
- **Deux façons de copier**, 1 MNQ dans le sens du signal (achat ou vente), rien si le signal est nul :
  - « nuit » : 18 h → 9 h 30 ;
  - « entier » : 18 h → 15 h 59 du lendemain (une position par jour de trading, 3 $ de frais).
  Sans stop : on mesure l'information du signal, pas un module.
- 5 signaux × 2 = **10 tests**, sur les nuits jouables de la partie N (2012 → 2 octobre 2026).
- **Retenu** si, à la fois : t ≥ 2 sur toute la période et retenu par Benjamini-Hochberg (10 tests) ; gain moyen
  positif en exploration et au contrôle ; **mieux que 95 % de 1 000 placebos** (la série des signaux décalée d'un
  nombre de semaines tiré au hasard, au moins 8 : mêmes nombres d'achats et de ventes, plus de lien avec le marché).
- Pour information : la différence avec « acheter tous les jours » sur la même fenêtre.
- Réserve écrite d'avance : pendant les fermetures de l'administration américaine (décembre 2018 - février 2019,
  octobre 2025 - janvier 2026) les rapports sont sortis en retard ; la règle « vendredi » regarde alors un peu dans
  le futur. Un signal qui passerait serait rejoué sans ces semaines avant d'être retenu.
- Non testable ici, et pourquoi : les portefeuilles trimestriels des fonds (formulaires 13F : des actions, publiées
  45 jours après), les portefeuilles crypto et les gros comptes de Polymarket (pas de futures ; pas de données dans
  le dépôt ; réseau fermé).

## Partie H : variantes de la nuit, pour en faire un atout utilisable (règles écrites le 12 novembre 2026, avant tout calcul de cette partie)

Demande : « teste certaines variantes, trouve-moi un atout à mettre dans mes setups ou à automatiser ».

Seule la nuit a passé ses conditions dans ce chantier ; jouée chaque soir de 18 h à 9 h 30, elle bouge trop pour le
compte. Idée : ne garder que les heures où la hausse se fait. Source : Boyarchenko, Larsen et Whelan (2023) trouvent
que la hausse de nuit des futures américains se concentre à l'ouverture de l'Europe (2 h - 3 h à New York, soit
8 h - 9 h à Paris).

Déjà vu avant d'écrire ces règles (sorties de la contre-revue, données non corrigées) : sur 2012 - 2019 la barre de
2 h 00 (New York) était parmi les plus positives de la journée (+3,2 $, t 4,7) ; elle n'est plus dans les listes des
années suivantes. Les chiffres de la partie N corrigée (t 3,62 sans stop ; 2,73 avec stop 0,50 %) sont connus aussi.

### H1 : quelles heures de la nuit ?

- **Fenêtres**, achat de 1 MNQ à l'ouverture de la première barre de 5 minutes, vente à l'ouverture de la barre de
  fin. Les bornes du milieu sont à l'heure de **Paris** (c'est l'ouverture de l'Europe qui compte, et c'est l'heure
  de l'utilisateur) :
  - A « Asie » : 18 h (New York) → 8 h (Paris) ;
  - E « ouverture de l'Europe » : 8 h → 9 h (Paris) ;
  - M « matin » : 9 h (Paris) → 9 h 30 (New York) ;
  - EM : 8 h (Paris) → 9 h 30 (New York), soit 15 h 30 à Paris.
  Une borne est la première barre à cette heure ou dans les 30 minutes qui suivent ; sinon la fenêtre n'est pas jouée
  cette nuit-là (0 $).
- **Stops** : aucun ; 0,50 % sous l'entrée de la fenêtre. 4 fenêtres × 2 = **8 variantes**.
- Mêmes nuits que la partie N (données corrigées) et mêmes cinq conditions : t ≥ 2 et Benjamini-Hochberg (8 tests) ;
  gain moyen positif en exploration et au contrôle ; t ≥ 1,5 avec 6 $ de frais ; au moins 10 années positives sur
  15 ; pire résultat au-dessus de −1 100 $.
- Pour information : le gain moyen heure par heure (Paris), exploration et contrôle.

### H2 : dans le compte Master

Modules jugés : **S50**, la nuit entière avec stop 0,50 % (partie N) ; **S75**, la même avec stop 0,75 % ; et, si H1
retient des variantes, **la meilleure** (plus grand t).

- (a) **chaque nuit** : seulement pour le module de H1 (la nuit entière chaque soir est déjà jugée : non adoptée) ;
- (b) **en secours contre l'inactivité** : le module n'est pris que si le compte vient de passer k jours de trading
  de suite sans trade, **k = 2, 3 ou 4**, puis chaque nuit jusqu'au premier trade.
- Trous du fichier de nuit : en vrai, le marché est ouvert ces nuits-là. Cette fois c'est écrit d'avance : un trade
  de secours qui tombe dans un trou compte comme un trade à 0 $, et le nombre de cas est donné. (La vague 2 de la
  partie N comptait ces nuits comme impossibles. Son chiffre « pour information » avec la convention d'ici, 69 % au
  3e retrait et 8 % perdus par le plancher pour S50 et k = 3 sur les données non corrigées, a été vu avant d'écrire
  ces règles : pour S50 et S75 à k = 3, ce calcul est une vérification sur données corrigées, pas un test neuf.)
- **Même règle d'adoption** : aucun Master perdu par inactivité ; au plus 20 % de Masters perdus avant le 3e retrait ;
  touché moyen positif ; nombre de dates de perte distinctes donné (moins de 3 = fragile).
- Références : le bot seul, avec et sans la règle d'inactivité.

### H3 : depuis l'état actuel du compte (descriptif)

Solde 50 700 $, plus haut de fin de journée 51 800 $ (marge 1 400 $), 120 séances au plus, depuis chaque séance de
2017 à 2026, **règle d'inactivité comptée** : le bot seul à 1 MNQ avec frein, puis le bot avec le module de secours
le mieux classé de H2. On donne : perdus par le plancher, perdus par l'inactivité, solde ≥ 53 600 $ (premier retrait
possible).
