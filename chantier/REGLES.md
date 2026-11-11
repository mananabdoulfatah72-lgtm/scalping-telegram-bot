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
