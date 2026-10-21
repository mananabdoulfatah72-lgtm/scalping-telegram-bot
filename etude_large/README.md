# Étude large : tous les marchés futures, la zone combinée sur 15 ans, et les challenges 50K (règles fixées le 22 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (21 octobre 2026)

- Partir du principe que le compte Bulenox actuel est perdu (486 $ de marge, `delta_mesures/`).
- Faire l'étude large proposée : combiner sur 15 ans ce qu'on sait déjà de la zone (heure, force de la cassure,
  volatilité, S&P 500), avec une vraie vérification sur des années que le modèle n'a pas vues.
- Tester tout ce qui est tradable en futures : actifs, produits, marchés. Tester d'autres études et variantes que la
  zone. Chercher une stratégie comme la zone, qui vienne la compenser, pour un plus gros avantage.
- Uniquement des données gratuites (`donnees_libres/`), rien de payant.
- Dire quelles stratégies et quels challenges 50K conviennent (Bulenox ou d'autres).
- Une contre-revue indépendante de tout le travail (#ultrareview), pour que le résultat ne soit pas faux.

## Ce qui est déjà fait (carte de la recherche, branche `claude/keen-babbage-r686cl`, `cerveau/savoir.json`)

Pas refait ici : zone sur NQ, ES, RTY, YM, GC, CL, 6E (`zone_multi/`) ; 75 stratégies intraday classiques sur NQ et ES
(tournois 1 à 4, dont Gao, Baltussen, OPR 5 minutes) ; 35 essais sur 5 autres marchés (tournoi 6) ; information
croisée entre 7 marchés (tournoi 7) ; 232 736 stratégies journalières sur 16 futures (machine 4) ; 526 stratégies de
sessions sur 8 marchés HistData (machine 5) ; 8 178 confluences sur la zone (vague 9) ; filtres delta, entrées en
retard, sortie au retour dans la zone (`delta_mesures/`, `zone_retour/`). Seuls la zone sur NQ, la règle « pas de zone
les jours de la Fed » et le RSI(2) de nuit ont survécu.

**Ce qui est nouveau ici :**
1. 22 marchés jamais testés en intraday, grâce aux ETF gratuits (Alpaca, 5 minutes, 2016 - 2026) : la courbe des taux
   (ZB, ZN, ZF, ZT), l'argent, le cuivre, le platine, le palladium, le Brent, le gaz, l'essence, 6 devises, le maïs, le
   soja, le blé, le bitcoin. Les 5 familles de A sur ces 22 marchés n'ont jamais été mesurées.
2. Un modèle qui combine les informations de la zone (et non des conditions prises une à une), vérifié en
   walk-forward : chaque année est prédite par un modèle qui ne l'a jamais vue.
3. Les mathématiques des challenges : quelle chance de valider, au mieux, même avec une très bonne stratégie, selon les
   règles de chaque firme.

## Partie A : 7 stratégies × 27 marchés (2016 - 2026, 5 minutes, séance 9 h 30 - 16 h de New York)

**Données** : `donnees_libres/etf_5min/` (Alpaca, flux SIP, ajusté des splits). Chaque ETF représente le future qu'il
suit (tableau dans `marches.py`). Les ETF ne couvrent que la séance américaine : toutes les stratégies de A sont
intraday, à plat à 16 h, comme l'exigent Bulenox, Topstep et les comptes « intraday ».

**Marchés** (27) : SPY→ES, QQQ→NQ, DIA→YM, IWM→RTY, TLT→ZB, IEF→ZN, IEI→ZF, SHY→ZT, GLD→GC, SLV→SI, CPER→HG,
PPLT→PL, PALL→PA, USO→CL, BNO→BZ, UNG→NG, UGA→RB, FXE→6E, FXY→6J, FXB→6B, FXA→6A, FXC→6C, FXF→6S, CORN→ZC,
SOYB→ZS, WEAT→ZW, BITO→BTC. UUP (dollar, ICE) et VXX (VIX, CFE) ne sont pas des produits CME : mesurés pour
information, hors décision.

**Frais** (par aller-retour, dans le prix du jour) : commission 1 $ par ordre sur un micro, 2,50 $ sur un contrat
standard, plus 1 tick de glissement à l'entrée et 1 à la sortie, sur le plus petit contrat CME du marché (`marches.py`).
Le niveau de prix du future vient de Yahoo (`donnees_libres/yahoo/jour/`, clôture de la veille).

**Stratégies** (paramètres des articles, aucun réglage) :

| Nom | Règle |
|---|---|
| **A1 zone** | Zone de bruit (Zarattini, Aziz et Barbon 2024), comme le bot : σ_m = moyenne sur les 14 séances complètes précédentes de \|clôture_m / ouverture − 1\| ; limites max(ouverture, veille) × (1 + σ_m) et min(ouverture, veille) × (1 − σ_m) ; contrôles de 10 h à 15 h 30 toutes les 30 minutes ; sortie à un contrôle si le prix repasse max(limite haute, VWAP) (achat) ou min(limite basse, VWAP) (vente) ; à plat à 16 h. |
| **A2a Gao** | Gao, Han, Li et Zhou (2018) : signe du rendement de la clôture de la veille à 10 h → position de 15 h 30 à 16 h. |
| **A2b Baltussen** | Baltussen, Da, Lammers et Martens (2021) : signe du rendement de la clôture de la veille à 15 h 30 → position de 15 h 30 à 16 h. |
| **A3a OPR 5 min** | Zarattini et Aziz (2023) : sens de la première barre de 5 minutes, entrée à 9 h 35, stop à l'autre extrême de la barre, objectif 10 fois le risque, à plat à 16 h. |
| **A3b OPR 30 min** | Cassure du plus haut ou du plus bas de 9 h 30 - 10 h (première cassure, une seule entrée, à la clôture de la barre qui casse), stop à l'autre extrême, à plat à 16 h. |
| **A4 périodicité** | Heston, Korajczyk et Sadka (2010) : pour chaque demi-heure de la séance, position du signe du rendement moyen de cette même demi-heure sur les 40 séances précédentes. |
| **A5 zone inversée** | Le complément naturel de la zone, qui perd sur les fausses cassures : mêmes signaux que A1, sens contraire ; sortie à un contrôle quand le prix revient au VWAP, stop à un contrôle si le prix s'écarte encore de σ_m depuis l'entrée, à plat à 16 h. |

**Mesure** : rendement net de chaque séance (0 sans trade), t de la moyenne. **Exploration** : 2016 - 2022.
**Coffre** : 2023 - 20 octobre 2026, ouvert une seule fois, après les décisions d'exploration.

**Survie (toutes les conditions) :**
1. exploration : t net ≥ 2,0, et retenu par Benjamini-Hochberg à 10 % sur les 189 essais décidables (p unilatéral) ;
2. coffre : t net ≥ 1,5, même sens.

**Contrôle de la méthode** : A1 sur QQQ doit ressembler à la zone du bot sur les minutes du NQ (corrélation des
séances 2016 - 2026 ≥ 0,6). Sinon, les 5 minutes des ETF sont jugées trop grossières pour les stratégies de type zone,
et A1 / A5 sont seulement descriptives.

## Partie C : un complément de la zone

Une survivante de A est retenue comme complément si :
1. corrélation de ses séances avec la zone du bot (NQ minute, 1 MNQ) < 0,3 sur 2016 - 2022 ;
2. zone + survivante, à risque égal (même écart-type quotidien sur 2016 - 2022), a un Sharpe plus haut que la zone
   seule sur le coffre.

Pour information : pour chacun des 189 essais, corrélation avec la zone et gain moyen les jours où la zone perd.

## Partie B : la zone combinée sur 15 ans, en walk-forward

**Trades** : zone du bot sans filtre sur le NQ (V1, minutes 2011 - 25 septembre 2026, dernier jour des minutes ES),
sans les jours d'annonce de la Fed (comme le bot). **Informations** au moment de l'entrée (rien d'après) :

| | Information |
|---|---|
| 1-3 | heure du contrôle : 10 h, 10 h 30 - 11 h 30, 12 h - 13 h 30, 14 h - 15 h 30 (3 indicatrices) |
| 4 | force de la cassure : (prix − limite) / (σ × référence), dans le sens du trade |
| 5 | volatilité : log(σ de 10 h / médiane de σ de 10 h sur les 252 séances précédentes) |
| 6 | S&P 500 : l'ES est aussi hors de sa propre zone, dans le même sens, au même contrôle (0 ou 1) |
| 7 | écart d'ouverture du NQ, dans le sens du trade, en σ de 10 h |
| 8 | tendance : rendement du NQ sur 20 séances, dans le sens du trade |
| 9 | VIX de la veille (log, Yahoo) |
| 10 | trade de la séance : premier trade du jour ou non (0 ou 1) |

**Modèle** : régression ridge (λ = nombre de trades d'apprentissage × 1,0, informations centrées réduites sur
l'apprentissage) du gain net du trade en multiples de σ × référence. **Walk-forward** : pour chaque année Y de 2016 à
2026, apprentissage sur tous les trades des années < Y (depuis 2011), puis on ne garde en Y que les trades prédits
positifs. Un trade écarté reste suivi « à blanc » jusqu'à sa sortie, comme le bot.

**Adoption (toutes les conditions)** sur 2016 - 2026, hors échantillon :
1. t de la différence quotidienne (gardés − tous) ≥ 2,0 ;
2. différence positive sur 2016 - 2022 et sur 2023 - 2026 ;
3. au moins 50 % des trades gardés.

## Partie D : les challenges 50K

**Règles supposées** (sites d'avis d'octobre 2026, les pages officielles ne répondent pas depuis la machine : à
confirmer au panier ou par écrit) :

| Compte | Prix | Objectif | Perte max (fin de journée) | Limite du jour | Délai | Meilleur jour | Bots |
|---|---|---|---|---|---|---|---|
| Bulenox Legacy 50K, option 2 | ≈ 19 $ avec code, 148 $ d'activation | 3 000 $ | 2 500 $, bloquée à +100 $ | 1 100 $ (arrête la journée) | 30 jours (22 séances) | — | permis |
| Topstep 50K Combine | 49 $ par mois, 149 $ d'activation | 3 000 $ | 2 000 $, bloquée au départ | 1 000 $ (arrête la journée) | aucun | < 50 % | Combine oui |
| Tradeify Select 50K | ≈ 159 $ | 3 000 $ | 2 000 $, bloquée à +100 $ | — | aucun | ≤ 40 % | sous conditions |
| Lucid Flex 50K | paiement unique | 3 000 $ | 2 000 $, bloquée à +100 $ | — | aucun | ≤ 50 % | permis |
| MyFundedFutures 50K | abonnement de 30 jours | 3 000 $ | 2 000 $, bloquée à +100 $ | — | aucun | ≤ 50 % | permis, supervisé |
| Phidias Fundamental 50K | ≈ 116 $, 149 $ d'activation | 4 000 $ | 2 500 $, bloquée à +100 $ | — | aucun | — | ? |
| Apex 50K EOD | — | 3 000 $ | 2 000 $ | 1 000 $ | 30 jours | — | **interdit** au compte financé |
| Take Profit Trader 50K | ≈ 150 $ par mois | 3 000 $ | 2 000 $ | — | aucun | < 50 % | **interdit** |
| Alpha Futures Advanced 50K | 139 $ par mois | 4 000 $ | 1 750 $ | — | aucun | 50 % | **interdit** |

Apex, Take Profit Trader et Alpha Futures interdisent les bots (au moins au compte financé) : ils ne conviennent pas
au bot et ne sont pas simulés. Le plancher est le plus haut de fin de journée moins la perte max ; il est touché si le
compte passe dessous **pendant** la séance. Sans délai, le challenge est suivi au plus 126 séances (6 mois).

**D1, le plafond** : séances tirées au hasard, loi normale, Sharpe annuel 0, 1, 2 et 3 ; pour chaque compte et chaque
Sharpe, l'écart-type quotidien (100 à 1 500 $) qui maximise la chance de valider. Cela dit ce que la meilleure
stratégie possible peut espérer de chaque compte.

**D2, le bot réel** : la zone du bot (sans filtre, pas de zone les jours de la Fed), minute par minute sur le NQ
2012 - 2026, au niveau de prix d'aujourd'hui (20 octobre 2026), 1,5 point de frais par aller-retour. Chaque séance
donne son gain, son point le plus bas et son point le plus haut. Taille de 1 à 10 MNQ, avec arrêt dès que l'objectif
est atteint dans la séance. Pour Bulenox, aussi la version 30 jours actuelle (4 MNQ, 6 MNQ les 5 dernières séances).
Départ à chaque séance. **Choix** de la taille sur les départs 2012 - 2021 (la plus haute chance de valider avec au plus
35 % de challenges perdus), **vérification** sur les départs 2023 - 2026.

**Classement** des comptes sur la vérification : coût moyen d'un challenge validé = (prix + abonnements des mois
utilisés) ÷ part validée. La phase financée (retraits) n'est pas simulée ici (voir vagues 5 à 13).

**Contrôle** : pour Bulenox, la version 30 jours doit redonner à ±5 points la part validée du moteur exact de la
vague 13 (53 % sur les achats 2012 - 2021, 55 % sur 2023 - 2026).

## Limites écrites d'avance

- Les ETF ne sont pas les futures : même sens et même séance, mais les ETF de matières premières (USO, UNG, CORN…)
  suivent moins bien que ceux des indices et des taux. Un résultat de A sur un ETF devrait être revérifié sur le
  future avant d'y risquer de l'argent.
- Les années 2016 - 2026 du NQ ont déjà servi à toute la recherche : pour la zone, aucune année n'est vraiment neuve.
  Le walk-forward empêche le modèle de voir l'année qu'il prédit, mais les 10 informations ont été choisies par une
  recherche qui, elle, a vu ces années.
- Les règles des firmes viennent de sites tiers et changent souvent.
- Exécution à la clôture de la barre qui décide : légèrement optimiste, le glissement compté (1 tick) peut ne pas
  suffire dans un mouvement rapide.

## Fichiers

- `marches.py` : les 29 marchés, contrats et frais.
- `partie_a.py` → `resultats_a.txt`, `essais_a.csv` (parties A et C).
- `partie_b.py` → `resultats_b.txt`.
- `partie_d.py` → `resultats_d.txt`.
