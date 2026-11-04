# Bot XGBoost NQ : remèdes contre les pertes, fixés avant calcul (4 novembre 2026)

Écrit et poussé **avant** de calculer. Le modèle (moyenne des 10 XGBoost, 21 variables) et ses signaux ne changent pas :
seule la gestion du trade et du compte est testée. Même marche en avant purgée que le dossier (`dossier.py`), 2014 - 2026,
une position à la fois, entrée à l'ouverture de la minute qui suit la bougie, 1 MNQ, 3 $ de frais, minutes du NQ.

## Les candidats (4, pas un de plus)

- **R1 : stop à 1 ATR.** Dès l'entrée, un stop à 1 × ATR 14 des bougies de 15 minutes (valeur connue à la clôture de la
  bougie du signal) ; touché sur une minute : sortie au stop moins 1 tick (0,25 point) défavorable, ou à l'ouverture de la
  minute si elle s'ouvre déjà au-delà.
- **R2 : stop à 1,5 ATR.** Pareil, à 1,5 × ATR.
- **R3 : pas de trade quand le marché est calme.** Signal ignoré quand le rang de la largeur de Bollinger (sur les 500
  dernières bougies, variable n° 8 du modèle, connue en temps réel) est sous 33 %. Attention : cette idée vient du dossier,
  qui a montré un avantage faible en marché calme ; elle est donc jugée sur ses deux moitiés comme les autres, mais elle part
  avec un soupçon de regard sur les données.
- **R4 : R2 et R3 ensemble.**

## La règle pour adopter un remède (toutes les conditions)

1. il réduit la pire baisse cumulée **et** l'écart type par séance ;
2. le t sur 2014 - 2026 reste au moins à 3,0 (l'avantage ne doit pas être détruit pour réduire le risque) ;
3. il reste positif sur 2014 - 2022 **et** sur 2023 - 2026 ;
4. il améliore la réussite du challenge rejoué sur un compte neuf (50 000 $, plancher suiveur 47 500 $, objectif 53 000 $,
   limite du jour 400 $), départ à chaque séance de 2023 à juin 2026.

Si plusieurs remèdes passent, on garde celui qui réduit le plus la pire baisse ; s'il n'y en a aucun, le bot reste tel quel.

## Réglage du compte (sans effet sur l'avantage, mesuré à part)

Limite de perte du jour à 200, 300, 400 et 800 $ : réussite du challenge rejoué sur ton compte actuel et sur un compte neuf.
