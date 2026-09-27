# Stratégies intraday pour challenge futures 50K

Test des stratégies intraday les mieux documentées par la recherche, sur les micro-futures
S&P (MES) et Nasdaq (MNQ), avec les frais réels (1 $ par ordre + 1 tick de glissement).

## Résultat (septembre 2026) : aucun avantage

**Momentum de fin de séance** (Baltussen et al. 2021, règle exacte : sens du rendement entre la
clôture de la veille et 15 h 30, position de 15 h 30 à 16 h), barres horaires Yahoo de SPY et QQQ,
octobre 2023 à septembre 2026 (722 séances, toutes après la publication) :

| Marché | Gain brut par trade | Gain net par trade | Par an, 1 contrat | Test du hasard |
|---|---|---|---|---|
| S&P 500 (MES) | −1,14 point (t = −2,4) | −2,04 points | −2 544 $ | 99 % font aussi bien |
| Nasdaq 100 (MNQ) | −3,44 points (t = −1,6) | −4,94 points | −2 454 $ | 95 % font aussi bien |

La variante Gao et al. (sens donné à 10 h 30) est à peu près nulle avant frais et négative après.
Sur ces trois années, la dernière demi-heure a plutôt eu tendance à repartir en sens inverse.
Retourner la règle serait l'ajuster sur trois ans de données : ce n'est pas fait.

Sur un challenge Topstep ou Apex 50K, ces stratégies réussissent moins souvent qu'un joueur sans
aucun avantage (même risque).

L'OPR 5 minutes et la zone de bruit demandent des prix minute par minute sur plusieurs années.
Le téléchargement Dukascopy (`telecharger.sh`, `donnees-intraday.yml`) est limité par Dukascopy
à quelques requêtes par seconde et prend plusieurs heures ; il a été arrêté. Une réplication
indépendante publiée en septembre 2026 trouve l'OPR 5 minutes à peu près nul après frais.

## Fichiers

| Fichier | Rôle |
|---|---|
| `strategies.py` | Règles des 4 stratégies sur prix minute (fin de séance ×2, OPR 5 min, zone de bruit) |
| `analyse.py` | Mesures par période, avant/après publication, test du hasard |
| `challenge.py` | Simulation Topstep 50K et Apex 50K, un challenge démarré chaque jour |
| `test_yahoo.py` | Test du momentum de fin de séance sur les barres horaires Yahoo (résultat ci-dessus) |
| `heures.py` | Même test sur barres horaires Dukascopy 2014–2026 (données non téléchargées) |
| `telecharger*.sh/py`, `preparer*.py` | Téléchargement des données (Dukascopy, Yahoo) via GitHub Actions |
