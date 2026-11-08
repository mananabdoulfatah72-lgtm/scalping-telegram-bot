# Labo zipline (8 novembre 2026)

La recette « zipline + pandas + Lightweight Charts » essayée de bout en bout, avec les règles écrites avant le calcul
(`REGLES.md`). Écran publié : https://claude.ai/artifact/2FJUnGWWYUnTTGo6sQtcPo (privé).

## Résultat

Sur tout l'historique (2016 - oct. 2026), la règle « tendance EMA 20/50 + stop 2 ATR + objectif 4 ATR » réduit la pire
baisse sur les 9 actifs, mais **ne bat l'achat-conservation sur aucun** : Sharpe plus bas partout sauf l'ETH, où elle
perd sur la seconde moitié (−28 %). Détail complet, transactions comprises : `resultats.txt`.

| Actif | Sharpe stratégie | Sharpe achat-conservation | Pire baisse stratégie | Pire baisse achat-conservation |
|---|---|---|---|---|
| BTC | 0,84 | 1,06 | −64 % | −83 % |
| ETH | 0,72 | 0,61 | −57 % | −86 % |
| SOL | 1,07 | 1,16 | −79 % | −96 % |
| QQQ | 0,73 | 0,88 | −27 % | −36 % |
| SPY | 0,74 | 0,78 | −17 % | −34 % |
| IWM | 0,17 | 0,50 | −36 % | −42 % |
| GLD | 0,48 | 0,78 | −20 % | −28 % |
| TLT | −0,21 | −0,18 | −38 % | −55 % |
| SMH | 0,70 | 1,01 | −34 % | −45 % |

## Lancer

```bash
python3 -m venv venv && venv/bin/pip install zipline-reloaded pandas scipy
venv/bin/python labo_zipline/lancer.py /chemin/travail        # CSV du radar, zipline ingest, 18 x zipline run
venv/bin/python labo_zipline/lire.py /chemin/travail /chemin/travail/labo.json
python3 labo_zipline/ecran.py /chemin/travail/labo.json labo-zipline.html
```

- `extraire.py` : bougies journalières gratuites du radar (`radar/donnees/jour/yahoo`) au format du bundle csvdir.
- `extension.py` : bundles `crypto` (calendrier 24/7) et `etf` (Bourse de New York).
- `strategie.py` : la règle, lancée par `zipline run`.
- `sonde.py` : imprime ce que la stratégie voit à chaque séance (contrôle des dates).
- `lire.py` : lecture des pickles avec pandas, achat-conservation, verdict et Benjamini-Hochberg.
- `ecran.py` + `ecran.tpl.html` : l'écran Lightweight Charts.

## Pièges de zipline trouvés en vérifiant

1. **Parts entières seulement** : avec 10 000 $ et un BTC à 44 000 $, l'ordre valait 0 part, et il n'y avait aucun trade
   sans message d'erreur. Une part vaut ici 0,001 BTC et 0,01 ETH (rendements inchangés).
2. **Calendrier 24/7 décalé d'un jour** : à la clôture du jour J, `data.current()` rendait la bougie de J−1 (vu avec
   `sonde.py`). Les dates des bougies crypto sont recalées d'un jour dans `extraire.py`, contrôlé de nouveau par la sonde.
3. **Frais** : `transactions[...]["commission"]` vaut toujours `None` ; les frais réels sont dans les ordres.
4. **Fin des données** : zipline ferme la position le dernier jour d'un actif ; ce trade est marqué « fin des données ».

Kraken n'a pas été utilisé : son API n'est pas joignable depuis l'environnement de Claude, et elle ne rend que les
720 dernières bougies journalières.
