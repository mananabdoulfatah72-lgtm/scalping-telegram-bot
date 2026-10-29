# Contexte commun aux agents (25 octobre 2026)

L'utilisateur trade le Nasdaq 100 en futures (MNQ, micro : 2 $ par point, tick 0,25 point = 0,50 $) sur des comptes de
firmes de financement (Bulenox, Lucid : perte max ~2 000-2 500 $, positions fermées avant 17 h New York, bots permis,
frais réels ~1 $ par ordre + ~1 tick de glissement par ordre, soit ~3 $ par aller-retour sur MNQ). Il a déjà un
système : la « zone de bruit » (Zarattini, Aziz, Barbon 2024, intraday momentum : cassure d'une bande autour de
l'ouverture, contrôles toutes les 30 min, stop sur VWAP/bande) + un « filtre delta » (achats agressifs − ventes
agressives des 30 dernières minutes dans le sens du trade) + un RSI(2) de nuit. Il cherche une stratégie de SCALPING
sur le NQ, autre que la zone filtrée, qui tienne vraiment hors échantillon.

Données disponibles gratuitement pour tester : barres d'une minute du NQ et de l'ES (2011 - sept. 2026, séance
9 h 30 - 16 h, OHLCV + contrat), RTY, YM, or, pétrole, euro, bitcoin CME (2016-2026), barres de 5 minutes 24 h/24 de
CFD (HistData) pour NQ/ES/or/devises depuis 2012, barres de 5 minutes d'ETF (QQQ, SPY, TLT, GLD, ...) 2016-2026,
séries quotidiennes (VIX, VIX9D, VIX3M, VVIX, VXN, MOVE, ~40 futures au jour, GEX de la veille du S&P 500). Six mois de
transactions à la seconde avec côté agresseur (avril - octobre 2026) seulement. PAS de carnet d'ordres historique,
PAS de flux d'options intraday, PAS d'imbalances MOC historiques.

## Déjà testé (ne pas reproposer tel quel ; une variante vraiment différente, argumentée, est acceptable)

- Machine évolutive de scalping (≈ 600 000 stratégies réelles + 1,2 million sur faux marchés) sur barres d'une minute,
  familles : choc d'une minute, mouvement de k minutes (suivre / contrer), séries de barres, micro-compression puis
  cassure, distance au VWAP, niveaux (plus haut/bas/clôture de la veille, range d'ouverture 5/15/30 min, plus haut/bas
  du jour, niveaux ronds), pic de volume, avance de l'autre indice (ES↔NQ), bougies (avalement, marteau...), minutes
  d'événement (8 h 30, 10 h, 14 h...) ; filtres de régime de volatilité et de tendance ; stops, objectifs, durées
  1-30 min. Sur NQ, ES, RTY, YM, or, pétrole, euro, bitcoin, et la nuit (6 marchés). Résultat : RIEN ne tient hors
  échantillon (2023-2026).
- Règles publiées testées : Grant-Wolf-Yu (premier rendement intraday), minute extrême, saut de 10 h, extrême de 10
  minutes, nombres ronds d'Osler, Gao-Han-Li-Zhou (dernière demi-heure prédite par la première), Baltussen et al.
  (fin de séance, couverture gamma), ORB 5 min (Zarattini-Aziz 2023), ORB 30 min, périodicité d'Heston-Korajczyk-Sadka,
  zone inversée, retour au VWAP dans la zone : tous négatifs après frais sur NQ (et 27 marchés en ETF).
- Modèle appris (régression logistique, 15 variables, réentraîné chaque année) : perd partout.
- Filtres sur la zone : ES, volume, tendance de fond, range de nuit, GEX, VIX, VXN, AUD/JPY, taux, dollar, bitcoin,
  soirs de résultats des grandes valeurs, annonces de 8 h 30, jours de la Fed (adopté : pas de zone), heure, force de
  la cassure, modèle ridge à 10 variables : rien d'autre ne tient.
- Carnet / flux : 6 mois de secondes avec côté agresseur (orderflow) : l'information de très court terme vaut moins
  qu'un aller-retour.
- Rebond après forte baisse (achat le lendemain d'une séance dans les 10 % les plus basses) : faible, porté par 2 krachs.
- Stratégies journalières : 232 736 sur 16 futures (rien) ; 526 stratégies de sessions (Asie/Londres/New York) sur 8
  marchés (rien) ; RSI(2) de nuit sur MES (adopté).
- Coûts : sur MNQ, un aller-retour vaut ~9 % du mouvement médian de 15 min (meilleur marché CME pour scalper) ; le
  spread (0,50 $) est inférieur aux commissions, donc capter l'écart acheteur-vendeur est impossible.

## Ce qu'on attend de chaque agent

Une liste de RÈGLES CONCRÈTES et TESTABLES sur le NQ avec les données ci-dessus (ou en disant exactement quelle donnée
manque), chacune avec : la règle exacte (entrée, sortie, horaire, paramètres tels que publiés, sans réglage), la source
(article, auteur, année, lien), la preuve disponible (période, marché, après frais ?, hors échantillon ? répliquée
après publication ?), le mécanisme économique (pourquoi quelqu'un paierait cet avantage), l'ordre de grandeur du gain
par trade comparé aux ~3 $ de frais d'un aller-retour MNQ, et si c'est déjà couvert par la liste « déjà testé ». Classer
de la plus prometteuse à la moins prometteuse, en étant honnête : dire clairement quand une idée est du marketing ou
n'a pas de preuve. Pas de règle inventée sans source.
