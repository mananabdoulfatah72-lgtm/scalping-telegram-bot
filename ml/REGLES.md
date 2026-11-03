# Labo ML : règles fixées avant tout calcul (3 novembre 2026)

Ce fichier est écrit et poussé **avant** de lancer le moindre calcul. Les résultats iront dans `RESULTATS.md` ; toute
déviation de ces règles y sera signalée comme telle.

Le programme suit l'article reçu (algèbre linéaire, probabilités, ML tabulaire, deep learning, marchés de prédiction),
mais **sur nos vraies données** :

- **NQ minute** : séances 9 h 30 - 16 h (New York), 3 janvier 2011 → 2 novembre 2026 (historique du robot + export Rithmic
  depuis le 13 octobre), 1,56 million de minutes.
- **Radar quotidien** : ~150 séries Yahoo (futures, ETF, ~40 grandes actions, indices, cryptos, VIX), 1988 → 2026.
- **Trades du Supertrend NQ** sur 15 ans (moteur vérifié).

Frais : **3 $ par aller-retour et par MNQ**. Dollars « au prix d'aujourd'hui » : points × 2 $ × 28 500 / prix du moment.

## Niveau 1 : fondations

**1a. ACP (PCA).** Rendements logarithmiques quotidiens des séries négociables du radar (futures, ETF, actions, indices
boursiers, cryptos ; exclus : VIX et dérivés, taux ^TNX ^IRX ^FVX ^TYX, ^MOVE, ^SKEW, ^GVZ, ^OVX) présentes à 90 % au
moins du 2 janvier 2015 au 30 octobre 2026 ; jours communs seulement (dates où les marchés américains sont ouverts),
trous restants remplis par 0. Matrice de corrélation, valeurs propres, part de variance des composantes 1, 5 et 10.
**Nombre de composantes réelles** = valeurs propres au-dessus de la borne de Marchenko-Pastur λ+ = (1 + √(N/T))²
(ce que donnerait du bruit pur de même taille). Même chose sur le NQ intrajournalier : les 13 rendements de 30 minutes de
chaque séance (2011 - 2026).

**1b. Optimisation.** Fonction de Rosenbrock, départ (-1, 1), arrêt quand la distance à (1, 1) passe sous 0,001, au plus
100 000 pas. Descente de gradient simple, avec momentum (β = 0,9) et Adam (β1 = 0,9, β2 = 0,999), chacune sur la grille
de pas {1e-4, 3e-4, 1e-3, 3e-3, 1e-2, 3e-2, 1e-1} ; on rapporte toutes les cases et la meilleure de chaque méthode.

## Niveau 2 : probabilités et statistiques

**2a. Queues épaisses.** Rendements quotidiens du NQ (NQ=F, 2000 - 2026) et rendements de 5 minutes du NQ (séances
2011 - 2026). Jarque-Bera et Kolmogorov-Smirnov contre la loi normale ajustée ; loi de Student ajustée par maximum de
vraisemblance ; comparaison des log-vraisemblances et des AIC ; probabilité d'une baisse de 3 % et de 5 % en un jour selon
la normale, la Student et la fréquence observée.

**2b. Bayes.** Supertrend NQ, résultat par séance (1 MNQ).
- Taux de séances gagnantes : a priori Beta(1, 1), mise à jour séance par séance ; P(taux > 50 %) à la fin de 2011-2022
  et de 2023-2026.
- Gain moyen par séance μ : a priori de Jeffreys (non informatif) puis a priori **sceptique** μ ~ N(0, (10 $)²) (la
  plupart des avantages réels sont minuscules) ; P(μ > 0) pour 2011-2022, 2023-2026 et 2011-2026.

**2c. Tests multiples.**
- L'expérience de l'article : 1 000 stratégies de bruit pur (252 jours, rendements N(0, 2 %), graine 42) ; combien ont
  p < 0,05, combien survivent à Bonferroni et à Benjamini-Hochberg (q = 5 %).
- La même chose sur le **vrai NQ** : 1 000 règles tirées au hasard (graine 7). Une règle = minute d'entrée tirée dans
  {0, 5, …, 300}, durée tirée dans {15, 30, 60, 120} minutes, regard en arrière tiré dans {5, 15, 30, 60} minutes, sens
  tiré dans {suivre, contrer} le mouvement du regard en arrière ; 1 MNQ chaque séance, 3 $ de frais ; test t sur les
  résultats par séance 2011 - 2026.

## Niveau 3 : ML tabulaire (le cœur)

**Échantillon.** Bougies de 15 minutes du NQ (26 par séance). **Cible** : le prix sera-t-il plus haut 1 heure (4 bougies)
plus tard ? Seulement les bougies dont l'heure suivante reste dans la séance (bougies 0 à 21).

**Variables** (toutes connues à la clôture de la bougie) :
1-11. les 11 du signal ML actuel du terminal (rendements 15 min, 1 h, 4 h ; RSI ; MACD ; position dans Bollinger ; ATR /
prix ; rang de largeur de Bollinger ; écart EMA 8 - EMA 55 ; heure en sinus et cosinus) ;
12. distance au VWAP de la séance, en ATR ; 13. rendement depuis l'ouverture ; 14. écart d'ouverture (gap) ;
15. rendement de la séance précédente ; 16. volatilité réalisée de la séance jusqu'ici / moyenne des 20 séances
précédentes à la même heure ; 17. rendement sur 5 séances ; 18. jour de la semaine ; 19. sens du Supertrend 10-3 de
5 minutes ; 20. distance à la ligne du Supertrend, en ATR ; 21. position dans la zone de bruit ;
22. **variable témoin : du bruit pur** (graine 11), pour juger l'importance des autres.

Le déséquilibre acheteurs / vendeurs n'existe que depuis le 13 octobre 2026 : trop court pour entraîner quoi que ce soit.

**Validation.** Marche en avant purgée, par année : test sur l'année Y (Y = 2014 … 2026), entraînement sur tout ce qui
finit **21 séances avant** le début de Y (purge d'un mois), modèle ré-entraîné chaque année.

**5 modèles, pas un de plus :**
- M0 : régression logistique, les 11 variables actuelles (la base) ;
- M1 : régression logistique L1 (C = 0,1), les 22 variables ;
- M2 : XGBoost de l'article (100 arbres, profondeur 4, pas 0,05, sous-échantillons 0,8 / 0,8, L1 = 1, L2 = 1) ;
- M3 : XGBoost « simple » (50 arbres, profondeur 3, mêmes autres réglages) ;
- M4 : XGBoost « complexe » (1 000 arbres, profondeur 6, mêmes autres réglages).

**Règle de trading (identique pour tous).** À la clôture d'une bougie : probabilité > 0,55 → achat 1 MNQ pour 1 heure ;
< 0,45 → vente 1 MNQ pour 1 heure ; entrée et sortie aux clôtures ; 3 $ de frais. Les positions peuvent se chevaucher
(chaque signal compte pour lui-même).

**Statistique principale** : t de Student du résultat **par séance** (somme des signaux de la séance, 0 sans signal) sur
2014 - 2026, hors échantillon. On rapporte aussi la précision, l'AUC, le Sharpe annualisé, et 2014-2022 / 2023-2026.
Garde-fou de l'article : une précision hors échantillon au-dessus de 60 % = un bug à chercher.

**Importance des variables** : valeurs SHAP exactes des arbres (XGBoost `pred_contribs`) du modèle M2 entraîné pour 2026,
sur les bougies de 2026 ; une variable dont l'importance moyenne ne dépasse pas celle du **bruit témoin** est du bruit.

**Bollinger + ML.** Retour à la moyenne sur 15 minutes : clôture sous la bande basse (20, 2) → achat ; au-dessus de la
bande haute → vente ; sortie au retour à la moyenne mobile, après 8 bougies (2 h) ou à la fin de la séance ; 1 MNQ, 3 $.
Variante filtrée : on ne prend le trade que si M2 est d'accord (probabilité > 0,5 pour un achat, < 0,5 pour une vente).
Résultats bruts et nets de frais.

## Niveau 4 : deep learning

**4a. Transformer causal à quantiles (TFT allégé), codé à la main en PyTorch.** Entrée : les 32 dernières bougies de
15 minutes (les 21 variables, standardisées sur l'entraînement). Réseau : sélection de variables (porte softmax par
bougie, comme le TFT), plongement de dimension 32, position apprise, 2 couches d'attention causale à 4 têtes (attention
écrite à la main, masque du futur), sortie : quantiles 10 %, 50 % et 90 % du rendement de l'heure suivante (en points de
base). Perte : perte quantile (pinball). Adam, pas 1e-3, 6 époques, lots de 512, graine 3.
Bases : régression linéaire quantile sur les variables de la dernière bougie, et quantiles fixes de l'entraînement.
Marche en avant purgée comme au niveau 3, test Y = 2019 … 2026.
Mesures : perte pinball hors échantillon ; couverture de l'intervalle 10-90 % (cible 80 %) ; trading : achat ou vente
1 MNQ pour 1 heure selon le signe de la médiane quand |médiane| > 1 point de base, 3 $ de frais.

**4b. Perte de Sharpe : allocation de portefeuille de bout en bout.** 16 ETF du radar (SPY, QQQ, IWM, EFA, EEM, TLT, IEF,
SHY, LQD, HYG, TIP, GLD, SLV, USO, VNQ, UUP ; prix sans dividendes). Réseau : rendements des 60 derniers jours →
couches denses → poids positifs de somme 1 (softmax). Perte = − Sharpe de lots de 63 jours consécutifs. Ré-entraîné
chaque année (Adam, 1e-3, 30 époques, graine 5), test 2012 - 2026.
Comparé à : poids égaux, inverse de la volatilité, Markowitz variance minimale et Markowitz Sharpe maximal (estimations sur
252 jours, covariance rétrécie Ledoit-Wolf, sans vente à découvert), tous rebalancés chaque jour.
Frais : 5 points de base par unité de rotation. Mesure : Sharpe annualisé net ; différence avec les poids égaux testée par
bootstrap par blocs (blocs de 21 jours, 2 000 tirages, graine 9).

## Partie V : marchés de prédiction (LMSR)

Teneur de marché LMSR de Hanson : fonction de coût, prix = softmax, vérification de la perte maximale b·ln(n) ; 2 000
traders simulés avec des informations privées bruitées sur une vraie probabilité → le prix converge-t-il ? Simulation
seulement, aucun pari réel.

## Correction des tests multiples (pour tout le labo)

La **famille** des tests d'avantage de trading : M0 à M4, Bollinger seul, Bollinger + ML, transformer, quantile
linéaire, allocation à perte de Sharpe (10 tests, p unilatérales). Benjamini-Hochberg à q = 5 % sur cette famille.
Un résultat n'est appelé **avantage** que s'il survit à cette correction **et** reste positif en 2014-2022 **et** en
2023-2026 (transformer : 2019-2022 ; allocation : 2012-2022). Seul un avantage pourrait ensuite être proposé pour le bot ou la station.
