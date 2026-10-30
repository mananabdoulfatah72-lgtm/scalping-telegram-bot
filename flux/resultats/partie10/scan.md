# Partie 10 : scan order flow sur 131 séances (2026-04-01 - 2026-10-01)

23 variables d'order flow et de prix, 5 jours de la semaine, 3 fenêtres, 3 durées, 2 sens.
Exploration jusqu'au 2026-07-15 (75 séances), confirmation ensuite (56 séances).

Étape 1 : 11 familles à t ≥ 3.0.
Placebos : meilleur t de confirmation 0.90, 1.34, 1.52, 1.52, 1.58, 1.62, 1.90, 1.94, 2.04, 2.04, 2.04, 2.07, 2.12, 2.13, 2.21, 2.25, 2.50, 2.84, 3.56, 3.60 ; barre 3.57.
Survivantes : 0.
Figées pour les séances de FluxNQ : 5 meilleures de confirmation a t >= 2 (aucune survivante).

Les 15 meilleures familles en confirmation :

- t_E 4.09, t_C 2.92, 68 trades, +58.8 $ : achat (matin, 60 min) si ecart Q5
- t_E 4.22, t_C 1.93, 119 trades, +19.8 $ : achat (apres-midi, 60 min) si ecart Q4
- t_E 3.07, t_C 1.37, 73 trades, +24.6 $ : achat (mi-journee, 60 min) si absorption Q5
- t_E 3.84, t_C 0.90, 87 trades, +15.1 $ : achat (mi-journee, 60 min) si dcum Q2
- t_E 3.96, t_C 0.38, 36 trades, +7.3 $ : achat (mi-journee, 60 min) si r15 Q5 et absorption Q5
- t_E 3.39, t_C 0.35, 105 trades, +4.0 $ : achat (mi-journee, 30 min) si r30 Q5
- t_E 3.18, t_C -0.22, 49 trades, -3.7 $ : achat (mi-journee, 60 min) si r15 10 % haut
- t_E 3.24, t_C -0.51, 96 trades, -10.8 $ : achat (matin, 60 min) si jeudi
- t_E 3.41, t_C -0.87, 50 trades, -13.0 $ : achat (mi-journee, 30 min) si r15 Q5 et r30 Q5
- t_E 3.28, t_C -2.12, 107 trades, -23.9 $ : achat (mi-journee, 60 min) si ecart Q4
- t_E 3.05, t_C -2.49, 88 trades, -34.1 $ : vente (matin, 30 min) si mardi
