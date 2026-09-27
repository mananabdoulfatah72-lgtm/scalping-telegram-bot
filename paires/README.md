# Trading de paires (cointégration)

Méthode des vidéos : corrélation, puis test ADF sur l'écart entre deux actifs, puis on trade le
retour à la moyenne. `paires.py` la teste période par période (12 mois pour tester, 6 mois pour
trader, entrée à 2 écarts-types, sortie à la moyenne, stop à 4), frais compris.

## Résultats (2006–2026)

| | Paires futures (S&P/Nasdaq, or/argent, taux, devises) | Paires d'actions classiques (V/MA, KO/PEP…) |
|---|---|---|
| Périodes « cointégrées » avec le test naïf des vidéos | 17 % | 23 % |
| Avec le test correct (Engle-Granger) | 7 % | 8 % (le hasard seul donne 5 %) |
| Encore cointégrées les 6 mois suivants | 0 % | 6 % |
| Trades gagnants / stoppés à 4 écarts-types | 9 % / 64 % | 19 % / 59 % |
| Sharpe du portefeuille 2006–2026 | −0,45 | +0,22 (+0,43 en 2006–2012, ~0 depuis 2013) |

Visa/Mastercard est bien cointégrée si l'on regarde 2020–2024 après coup (p = 0,002), mais pas
2015–2019 (p = 0,11), et la paire ne rapporte rien en conditions réelles (+0 % sur 20 ans).
