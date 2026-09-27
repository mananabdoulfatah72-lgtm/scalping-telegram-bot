# Stratégies intraday pour challenge futures 50K

Test des stratégies intraday les mieux documentées par la recherche, sur les micro-futures
S&P (MES) et Nasdaq (MNQ), avec les frais réels (1 $ par ordre + 1 tick de glissement).

## Résultat sur les vrais futures CME (septembre 2026)

Données : barres d'une minute des futures ES et NQ de la CME (Databento, contrat le plus échangé),
séance 9 h 30 – 16 h, janvier 2011 à septembre 2026, 3 917 séances complètes. Règles des articles,
aucun paramètre ajusté. Frais : 0,90 point par aller-retour sur MES, 1,50 point sur MNQ.
Détails : `resultats_cme.txt`, `resultats_cme_challenges.txt`, `resultats_cme_verif_zone.txt`.

| Stratégie | S&P 500 (MES), net par trade | Nasdaq 100 (MNQ), net par trade | Après publication |
|---|---|---|---|
| Fin de séance (Gao 2018) | −0,94 pt (t = −6,0) | −1,54 pt (t = −2,6) | négatif sur les deux |
| Fin de séance (Baltussen 2021) | −0,73 pt (t = −4,7) | −1,19 pt (t = −2,0) | négatif sur les deux |
| OPR 5 minutes (2023) | −0,62 pt (t = −2,6) | +0,64 pt (t = +0,6) | MES −1,03 pt ; MNQ +1,05 pt (t = +0,3) |
| Zone de bruit (2024) | −0,37 pt (t = −1,0) | **+4,27 pt (t = +2,6)** | MES −2,25 pt ; MNQ +7,46 pt (t = +0,9) |

- **Momentum de fin de séance** : nul avant frais, perdant après, sur les 15 ans (confirme le test Yahoo).
- **OPR 5 minutes** : perdant sur le S&P ; sur le Nasdaq, légèrement positif mais pas distinguable
  du hasard (7 % des sens tirés au hasard font aussi bien).
- **Zone de bruit sur le Nasdaq** : le seul résultat positif. Avant frais, environ +3 points de base
  par trade dans chaque période (2011-2014, 2015-2019, 2020-2026, depuis mai 2024). Les frais d'un
  micro-contrat étant fixes, ils sont passés de 5,3 pb (NQ à 2 500) à 0,7 pb (NQ à 30 000) : c'est
  surtout pour cela que la stratégie devient gagnante après 2018. Limites :
  - tout le gain vient de 1 % des jours (grandes journées de tendance) : sans eux, +0,13 point par jour ;
  - depuis sa publication (mai 2024), +2,2 pb par trade, t = +0,8 : pas encore significatif ;
  - 8 essais (4 stratégies × 2 marchés) : un t de 2,6 est à la limite de ce que le hasard donne.

**Challenges 50K** (un départ par jour de bourse) : sur 2011-2026, aucune stratégie ne réussit
nettement plus souvent qu'un joueur sans avantage. Meilleur cas, zone de bruit sur MNQ en ne gardant
que 2020-2026 (période favorable choisie après coup, donc un plafond) : Apex 50K avec 10 MNQ,
36 % réussis et 63 % perdus (27 % sans avantage) ; Topstep 50K avec 5 MNQ, 20 % réussis et 80 % perdus.

## Fichiers

| Fichier | Rôle |
|---|---|
| `strategies.py` | Règles des 4 stratégies sur prix minute (fin de séance ×2, OPR 5 min, zone de bruit) |
| `analyse.py` | Mesures par période, avant/après publication, test du hasard |
| `challenge.py` | Simulation Topstep 50K et Apex 50K, un challenge démarré chaque jour |
| `verif_zone.py` | Vérifications de la zone de bruit (achats/ventes, points de base, meilleurs jours) |
| `test_yahoo.py` | Test du momentum de fin de séance sur les barres horaires Yahoo 2023-2026 (négatif) |
| `heures.py` | Même test sur barres horaires Dukascopy 2014–2026 (données non téléchargées) |
| `telecharger_databento.py` | Téléchargement des barres minute ES et NQ (Databento, secret `DATABENTO_API_KEY`) |
| `telecharger*.sh/py`, `preparer*.py` | Anciens téléchargements (Dukascopy, arrêté ; Yahoo) |
