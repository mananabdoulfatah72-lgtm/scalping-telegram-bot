# Vague Q : de nouveaux setups quant (règles fixées avant tout calcul, 4 novembre 2026)

Demande : « trouve-moi d'autres setups quant ». Déjà testé dans ce dépôt et donc pas refait : études publiées
intrajournalières (scalping, parties A, E, F, G, H, I), order flow (flux), COT, gamma, paires ES/NQ, avance d'autres
marchés à la minute, scan du radar (millions de règles sur ~100 variables, dont le VIX, sa courbe et le calendrier) et son
modèle d'apprentissage, le labo ML (M0 à M4, transformer). Ce qui suit est nouveau.

Cadre commun (celui du bot XGBoost NQ) : marche en avant purgée, test 2014 - 2026, chaque année prédite par des modèles
entraînés sur les années d'avant (purge de 21 séances) ; moyenne de 10 XGBoost (graines 0 à 9 ; 100 arbres, profondeur 4,
pas 0,05, sous-échantillons 0,8 / 0,8, L1 = 1, L2 = 1) ; signal à la clôture d'une bougie de 15 min, achat si
probabilité > 55 %, vente si < 45 % ; entrée à l'ouverture de la minute suivante ; une position à la fois ; 3 $ de frais par
aller-retour ; dollars au prix d'aujourd'hui.

## Les 5 setups

- **Q1 : le même assemblage sur le S&P 500.** Les 21 variables du bot, calculées sur les minutes de l'ES (2011 - 25 sept.
  2026), modèle appris sur l'ES, trades en MES (5 $ le point, prix d'aujourd'hui 7 800). Un setup sur un 2e marché, et une
  confirmation indépendante de celui du NQ.
- **Q2 : l'assemblage + le contexte macro et de volatilité.** Les 21 variables + 8 informations connues avant l'ouverture
  (clôtures de la veille, radar) : rang du VIX sur 252 jours, VIX / VIX 3 mois (courbe), rang du VVIX sur 252 jours, variation
  du VIX la veille, variation du taux à 10 ans sur 5 jours, variation du dollar sur 5 jours, crédit (HYG contre LQD sur 5 jours),
  semi-conducteurs contre Nasdaq (SMH contre QQQ sur 5 jours).
- **Q3a : l'assemblage à 30 minutes.** Les 21 variables, cible et tenue de 30 minutes (2 bougies).
- **Q3b : l'assemblage à 2 heures.** Les 21 variables, cible et tenue de 2 heures (8 bougies).
- **Q4 : la saisonnalité de la même demi-heure** (Heston, Korajczyk et Sadka 2010). Pour chaque demi-heure de la séance :
  moyenne de son rendement sur les 20 séances complètes précédentes ; si |t| de cette moyenne ≥ 1, position dans son sens
  pendant cette demi-heure (entrée à son ouverture, sortie à sa clôture).

## Décision (fixée maintenant)

Un setup est **retenu** si :
1. il survit à Benjamini-Hochberg (q = 5 %) sur ces 5 tests (p unilatérale du t des résultats par séance, 2014 - 2026) ;
2. il est positif sur 2014 - 2022 **et** sur 2023 - 2026 ;
3. il fait mieux que 99 % de 1 000 tirages où les mêmes signaux sont placés au hasard dans chaque année ;
4. pour Q2, Q3a et Q3b (variantes du bot) : il bat le bot actuel, avec un t de la différence par séance d'au moins 2 ;
   sinon ce n'est pas un nouveau setup mais une copie.

On rapporte aussi sa corrélation par séance avec le bot XGBoost NQ et avec le Supertrend. Un setup retenu n'est pas mis en
réel directement : il passe d'abord par le suivi sur des séances neuves.
