# Terminal quant NQ (3 novembre 2026)

Page publiée : https://claude.ai/artifact/Ac9xd9zdEHsHFmzsDAEBBE (privée).

- `prep.py` : données des séances (minutes 2011 → 12 oct. 2026 + export Rithmic 13 oct. → 2 nov. 2026), trades rejoués du
  Supertrend (identiques au moteur C#) et de la zone (vrai delta depuis le 13 oct.), grille du challenge Bulenox
  (simulateur `audit/machine6`), variables du labo, calendrier exact (règles du bot).
- `prep2.py` : bougies de 15 min et indicateurs (EMA 8-89, Bollinger 20-2, RSI 14, MACD 12-26-9, ATR 14), profils de
  volume par prix, signal d'apprentissage automatique (régression logistique ré-entraînée chaque année sur le passé seul,
  jugée sur l'année suivante : t 1,21 sur 2014 - 2026, pas un atout), S&P 500 (minutes jusqu'au 25 sept. 2026).
- `terminal.tpl.html` : la page ; `__DONNEES__` et `__DONNEES2__` sont remplacés par les deux fichiers JSON produits.

Vue par défaut : la **station** (tout sur un écran, replay continu des vraies séances). Touches F1 à F8 : activité,
surveillance, signaux, stratégie et risque, labo d'hypothèses, console papier, graphique pro, IA.
