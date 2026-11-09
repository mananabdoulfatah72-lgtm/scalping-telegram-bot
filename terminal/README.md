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

## Station en direct

La même station, branchée sur le marché par Quantower : guide dans `bot3en1/STATION.md`.

- `direct_js.txt` : moteur de la page en direct (séances, Supertrend, zone, VWAP, bougies de 15 min, indicateurs et
  signal ML recalculés à partir des minutes envoyées par le relais ; compte, journaux des agents, reliefs 3D).
- `modele_ml.json` : poids du signal ML de 2026 (exportés par `prep2.py`), embarqués dans la page.
- `assembler_direct.py` : assemble `bot3en1/Relais.Quantower/station-direct.html` à partir de `terminal.tpl.html` et du moteur.

## Vue ARÈNE (F9, 8 novembre 2026)

- `prep3.py` : classement des bots, des variantes (étape 2) et des quatre pistes (étape 3) de `ml/arene/resultats`, courbes,
  résultats par séance pour rejouer le compte financé dans la page (contrôle : la page retrouve les chiffres du Python,
  3 011 $ par an pour le Bot 3 en 1, 3 200 $ pour B3, 3 842 $ pour la piste A), et le diagnostic des premières années.
- `prep3.py <arène> [arène après les vagues 3, 4, 5, 6, 7, 8, 9]` : les dossiers de l'arène gardés après chaque vague
  donnent les courbes ; sans eux, les lignes s'affichent sans courbe. La vague 9 (règle d'inactivité de Bulenox, nuit) lit
  aussi `ml/arene/resultats/vague9_info.json` (information calculée après coup, pas une règle).
- `assembler.py <dossier des json> <sortie.html>` : remplace `__DONNEES__`, `__DONNEES2__` et `__DONNEES3__`.
