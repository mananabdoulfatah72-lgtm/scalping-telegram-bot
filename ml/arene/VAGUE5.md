# Arène, vague 5 : l'activité de W1 avec la sécurité de Z12 (règles fixées avant tout calcul, 9 novembre 2026)

Vague 4 : W1 (signaux du Supertrend NQ triés par apprentissage) est le meilleur Supertrend trouvé, trade 3 séances sur 4,
mais grille encore environ un compte financé neuf sur deux dans l'année ; Z12 (Bot 3 en 1 sans les jours de VIX inversé)
est le plus sûr (un sur six) mais ne trade qu'une séance sur trois. Question : les deux sur le même compte donnent-ils
l'activité de l'un et la sécurité de l'autre ?

**W1 désormais = moyenne des probabilités de 10 graines du modèle** (la version prudente vue au diagnostic de la vague 4,
et celle qu'utilisera le bot), même marche en avant, même seuil (part de trades gagnants de l'apprentissage).
Code commun : `ml/arene/w1.py` (variables, apprentissage, tri), qui sert aussi de référence au bot Quantower.

## Les 3 tests (mesure sur 2017 - 2026, cadre de l'arène)

| | Test | Règle |
|---|---|---|
| P1 | Z12 + W1, limite commune | les deux bots sur le même compte, 1 MNQ chacun, positions simultanées possibles, limite commune de 400 $ (moteur d'ensemble de l'arène) |
| P2 | Z12 + W1, un contrat à la fois | Z12 est prioritaire : W1 ne prend un signal que si Z12 n'a pas de position ouverte à ce moment-là ; jamais plus de 1 MNQ, limite 400 $ |
| P3 | W1 sans la variable VIX | W1 appris sans l'écart VIX − VIX à 3 mois (pour un bot qui n'a pas besoin du VIX), seul |

## Verdict

**P1, P2** (« l'activité de W1, une sécurité proche de Z12 ») : toutes ces conditions sur 2017 - 2026 :
1. t des résultats par séance d'au moins 2 et survie à Benjamini-Hochberg (q = 5 %) sur les 3 tests ;
2. positif sur 2017 - 2022 et sur 2023 - 2026 ; 3. t d'au moins 1,5 avec 6 $ de frais ; 4. au moins 7 années positives sur 10 ;
5. trade au moins 75 % des séances ;
6. compte financé : survie à 60 séances d'au moins 90 %, au plus 30 % de comptes neufs grillés dans l'année, au plus
   0,30 master grillé par an ;
7. net par an au moins égal à celui de Z12 seul sur 2017 - 2026.

**P3** : les règles de la vague 4 face au Supertrend NQ (t, deux moitiés, frais, 7 années sur 10, survie + 10 points,
20 % de masters grillés en moins, pire baisse, net au moins égal), avec 75 % des séances au lieu de 80 %.

On rapporte aussi les séances, semaines et mois positifs, et la période du 11 août au 2 novembre 2026 (sans valeur de preuve).
