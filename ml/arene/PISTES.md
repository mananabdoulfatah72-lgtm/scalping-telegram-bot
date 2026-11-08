# Arène, étape 3 : quatre nouvelles pistes (règles fixées avant tout calcul, 8 novembre 2026)

Choisies avec l'utilisateur : gestion du capital, consensus et régimes, nouvelles études, autres marchés. Rien de ce qui
suit n'a été testé dans le dépôt. Cadre commun à l'étape 1 (`bots.py`), avec les corrections de la double relecture
(#ultrareview) appliquées **avant** ce calcul : séances complètes 2014 - 2 nov. 2026 (2016 - 28 sept. 2026 pour les autres
marchés), rejeu minute par minute, frais du projet, compte financé Bulenox Master 50K Option 2 (plancher suiveur de
2 500 $ en fin de journée bloqué à 50 100 $, limite de la firme 1 100 $ par jour, constance 40 % au retrait), vie réelle avec
retraits toutes les 20 séances.

## A. Gestion du capital (sur les bots existants)

Bots : Bot 3 en 1, XGBoost NQ, XGBoost NQ avec stop 1,5 ATR (la variante adoptée par l'usine), Supertrend NQ.

- **Taille selon la marge** (marge = solde − plancher, connue au début de la séance) :
  - fixe : 1 MNQ (référence) ;
  - échelle E1 : 2 MNQ dès 3 500 $ de marge, 3 MNQ dès 5 000 $ ;
  - échelle E2 : 2 MNQ dès 4 000 $, 3 MNQ dès 6 000 $ ;
  - échelle E3 : 2 MNQ dès 5 000 $, jamais plus.
  Limite du bot = 400 $ par MNQ, sans dépasser la limite de la firme (1 100 $).
- **Coussin gardé après un retrait** : 2 600, 4 000 ou 6 000 $ au-dessus de 50 000 $.

4 tailles × 3 coussins × 4 bots = 48 politiques. Mesures : retiré par an, comptes grillés, survie à 60 séances.
**Choix honnête** : chaque année de 2017 à 2026, la politique qui a retiré le plus sur les années d'avant **sans griller plus
de comptes que le Bot 3 en 1 en 1 MNQ** sur ces mêmes années est jouée l'année suivante. **Adoptée** si, hors échantillon
2017 - 2026, elle retire plus que le Bot 3 en 1 en 1 MNQ sans griller plus de comptes.

## B. Consensus et régimes

- **B1** : XGBoost NQ ne prend un signal que si le Supertrend 10-3 (5 min) va dans le même sens à la bougie du signal.
- **B2** : le Supertrend ne prend un trade que si la probabilité de XGBoost à la dernière bougie de 15 min terminée avant
  l'entrée va dans son sens (au-dessus de 50 % pour un achat, en dessous pour une vente).
- **B3** : le Bot 3 en 1 ne prend un trade que si XGBoost va dans son sens (même définition).
- **B4 : choix du bot selon le régime.** Chaque séance, régime = tiers de la volatilité réalisée des 20 séances précédentes
  (rang sur 252 séances) × tiers de la force de tendance (|rendement sur 20 séances| ÷ (volatilité × √20), rang sur 252) :
  9 cases. Chaque année de 2017 à 2026, pour chaque case, on prend parmi Bot 3 en 1, XGBoost, Supertrend ou rien le bot
  dont le gain moyen dans cette case a été le meilleur sur les années d'avant (rien si ce gain est ≤ 0 ou s'il y a moins de
  30 séances dans la case).

Chacune est jugée par les 6 règles de `VARIANTES.md` face à son bot de base (B4 face au meilleur des trois bots sur
2017 - 2026).

## C. Nouvelles études (recherche du 8 novembre 2026)

- **C1 : la VWAP en tendance** (Zarattini et Aziz, « VWAP : the Holy Grail for Day Trading Systems », SSRN 4631351,
  2023). À la clôture de chaque minute de 9 h 31 à 15 h 58 : position acheteuse si la clôture est au-dessus de la VWAP de
  la séance, vendeuse si elle est en dessous ; ordre à l'ouverture de la minute suivante ; à plat à 15 h 59. 1 MNQ.
- **C2 : le retournement de fin de séance à l'époque des options 0DTE** (Baltussen, Da et Soebhag, « End-of-Day
  Reversal », et les travaux 2025 sur la couverture des teneurs de marché). À 15 h 30 : position contre le rendement de
  la clôture de la veille à 15 h 30, sortie à 15 h 59. Testé sur 2022 - 2026 (l'époque des 0DTE quotidiennes), avec
  2014 - 2021 en contrôle, où l'hypothèse prévoit l'inverse (l'élan de fin de séance de Gao et al.).
- Écartées : « Noise-band Intraday Momentum in Nasdaq-100 Futures » (Chuk, SSRN 7609644, 2026) adapte la zone de bruit
  au NQ, c'est déjà le Bot 3 en 1 (confirmation extérieure, pas un nouveau setup) ; les études sur le gamma et l'élan
  (Park et Zhao 2025, Adams et al. 2025) recoupent les règles E1 et E1b déjà testées ; les déséquilibres d'enchères
  demandent des données que nous n'avons pas.

C1 et C2 sont jugées par les règles 1 à 4 de `VARIANTES.md` (t, deux moitiés, frais doublés, années positives) et par le
compte financé face au Bot 3 en 1. Pour C2 : retenue seulement si positive sur 2022 - 2026 avec t ≥ 2.

## D. Autres marchés : le Supertrend partout

Le Supertrend 10-3 sur barres de 5 minutes (mêmes règles qu'au NQ : décision à la clôture de la barre, ordre à
l'ouverture de la minute suivante, plus d'entrée dans les 30 dernières minutes de la fenêtre, à plat 5 minutes avant sa
fin) sur ES, RTY, YM, or, pétrole et euro, fenêtres et frais de `scalping/commun.py`, 1 micro chacun, 2016 - 2026. La zone
de bruit sur ces marchés est déjà rejetée (`zone_multi`) : pas refaite.
**Portefeuille** : les 7 Supertrend (NQ compris), chacun ramené au même risque (gain du jour ÷ écart type des 60 séances
précédentes, connu la veille). **Retenu** si : t ≥ 3 sur 2016 - 2026, positif sur 2016 - 2019, 2020 - 2022 et 2023 - 2026,
et Sharpe supérieur au Supertrend NQ seul sur la même période. Chaque marché est rapporté.

## Correction des tests multiples

Famille : B1, B2, B3, B4, C1, C2, D (portefeuille) et les 6 marchés de D (13 tests). Benjamini-Hochberg à q = 5 % ; une
piste n'est retenue que si elle passe aussi ses propres conditions. La piste A est jugée par son choix en marche avant.

## Ce qui ira dans le terminal

Les pistes retenues, et le classement de toutes les pistes, entrent dans le terminal quant (nouvelle vue), avec leurs
courbes et leur rejeu sur le compte financé. Celles qui échouent y figurent aussi, marquées comme telles.
