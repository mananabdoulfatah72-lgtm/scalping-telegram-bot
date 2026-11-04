# Dossier de preuves du bot XGBoost NQ (moyenne de 10 modèles)

Marche en avant purgée 2014 - 2026 (3196 séances), une position à la fois, entrée à la bougie suivante, 1 MNQ, 3 $ de frais.

- 7285 trades (2.3 par séance, 23% des séances sans trade) ; +22.7 $ par séance ; t = 3.61 ; Sharpe annuel 1.01
- trades gagnants 55.9% ; gain moyen +141 $, perte moyenne -156 $ ; facteur de profit 1.14
- écart type par séance 355 $ ; pire séance -3361 $ ; meilleure +3655 $ ; pire baisse cumulée -8595 $
- mois positifs 64% ; pire mois -4885 $ ; séances perdantes d'affilée au pire 18

## Année par année

| année | séances | $ | $ par séance | t |
|---|---|---|---|---|
| 2014 | 243 | +2,486 | +10.2 | +0.68 |
| 2015 | 250 | +3,769 | +15.1 | +0.90 |
| 2016 | 251 | -259 | -1.0 | -0.06 |
| 2017 | 249 | +705 | +2.8 | +0.25 |
| 2018 | 248 | -10 | -0.0 | -0.00 |
| 2019 | 249 | +3,223 | +12.9 | +0.79 |
| 2020 | 251 | +33,632 | +134.0 | +3.84 |
| 2021 | 251 | +9,160 | +36.5 | +2.11 |
| 2022 | 250 | +3,224 | +12.9 | +0.37 |
| 2023 | 248 | +2,234 | +9.0 | +0.41 |
| 2024 | 249 | +3,297 | +13.2 | +0.78 |
| 2025 | 247 | +4,319 | +17.5 | +0.55 |
| 2026 | 210 | +6,664 | +31.7 | +1.68 |

## Calibration

| probabilité annoncée | bougies | moyenne annoncée | hausse réelle |
|---|---|---|---|
| 0% - 40% | 304 | 37.4% | 42.4% |
| 40% - 45% | 2,748 | 43.3% | 48.5% |
| 45% - 50% | 16,105 | 48.1% | 50.3% |
| 50% - 55% | 34,026 | 52.5% | 52.9% |
| 55% - 60% | 14,434 | 56.9% | 56.6% |
| 60% - 100% | 2,695 | 62.3% | 58.7% |

## Contre le hasard (1 000 tirages, mêmes signaux placés au hasard dans chaque année)

t du modèle 3.61 ; hasard : moyenne -0.69, 99e centile +1.30, maximum +1.97 ; p = 0.000

## Seuil et frais

seuil 0.52 : 15074 trades, +5.8 $ par trade, t +3.13 ; seuil 0.53 : 12253 trades, +7.4 $ par trade, t +3.57 ; seuil 0.55 : 7285 trades, +9.9 $ par trade, t +3.61 ; seuil 0.57 : 3925 trades, +13.5 $ par trade, t +3.29 ; seuil 0.6 : 1255 trades, +20.1 $ par trade, t +2.96
Frais par aller-retour : 1.5 $ : t +4.15 ; 3.0 $ : t +3.61 ; 4.5 $ : t +3.07 ; 6.0 $ : t +2.53

## Achats, ventes, volatilité

achats : 6079 trades, +9.7 $ par trade, t +3.65 ; ventes : 1206 trades, +11.3 $ par trade, t +1.22 ; calme : 2505 trades, +3.1 $ par trade, t +1.29 ; normale : 2310 trades, +6.0 $ par trade, t +1.74 ; agitee : 2470 trades, +20.6 $ par trade, t +2.95

Corrélation avec le Supertrend (par séance) : -0.03 ; les deux ensemble (1 MNQ chacun) : +49.2 $ par séance, t 4.11, Sharpe 1.15.
