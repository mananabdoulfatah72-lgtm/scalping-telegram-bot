# Inventaire du dossier flux/ (29 octobre 2026, branche claude/optimistic-ptolemy-xs24ra)

| Id | Stratégie | Données | Résultat | Verdict |
|---|---|---|---|---|
| S1 | repli absorbé dans le sens du flux (delta 30 min + VWAP, absorption 1 min), stop structure, 2R | tape NQ avr.-16 oct. 2026 | 28 trades, +0,54 pt, t +0,20 | rejetée |
| S2 | cassure ratée PDH/PDL/IB avec agression (delta) | idem | 69 trades, +2,50 pt, t +0,79 ; séances neuves 2 trades +61 pts | rejetée |
| S3 | volume d'arrêt footprint à l'extrême | Databento avr.-1er oct. | 583 trades, −2,96 pt, t −4,08 | rejetée (perd chaque mois) |
| Partie 2 | 89 100 réglages S1/S2/S3 | A avr.-juil., coffre B | 0 finaliste (bruit ≥ réel) ; réglage glissant −552 $/MNQ | rejetée |
| S2b | meilleure config partie 2 : cassure ratée sans flux, 2R, 60 min, 10-12 h | idem | in-sample 104 trades +6,32 pt t 2,45 ; séances neuves 6 trades +264 $/MNQ ; **15 ans barres gratuites 2011-mars 2026 : 2 929 trades −4,03 pt t −7,65, 1 année + sur 16** | NON confirmée |
| S2b stop élargi | +2..+8 pts | choix A, jugement B | rien de mieux | rejetée |
| Partie 3 | 9 familles quant (Kyle, VPIN, élan du flux, ouverture, fin de journée, gros lots, VWAP+flux, absorption, Chordia-Subrahmanyam) + VPIN-BVC 15 ans | 18 180 + 1 080 configs | 0 finaliste ; réglage glissant −3 663 $/MNQ | rejetée |
| C1 | confluence niveau + footprint + delta (+ DOM en direct) | sans DOM, 117 séances | 218 trades −1,98 pt t −2,56 | rejetée sans DOM ; DOM non testable |

Gains quotidiens régénérables : S2b sur 2011-2026 (flux/s2b_15ans.py, barres gratuites) ; S1/S2/S3/C1 seulement sur avril-oct. 2026 (tape).
