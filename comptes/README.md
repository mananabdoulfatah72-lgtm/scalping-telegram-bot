# Plusieurs comptes Phidias, et moins de comptes perdus

L'utilisateur demande deux choses (2 octobre 2026) :
- ce que donnent **plusieurs comptes Phidias en même temps** avec la zone de bruit et le RSI(2) ;
- comment **éviter de repartir de zéro** quand un compte est perdu.

## Règles (fixées le 2 octobre 2026, avant tout calcul)

Base : zone de bruit + RSI(2), gestion actuelle du robot (f = 0,15, chaque source à f × coussin / √2,
au moins 1 MNQ), règles Phidias 50K Fundamental publiques, challenge à 164 $. Simulateur de
`zone_deux/` (vérifié égal à celui de `zone_retrait/`, lui-même égal au robot). Un compte perdu est
remplacé le lendemain par un nouveau challenge.

### A. Plusieurs comptes (description : aucun choix à faire)

- **Comptes ouverts le même jour** (N = 1, 2, 3, 5), qui reçoivent les mêmes ordres. Leurs résultats
  sont exactement N fois ceux d'un compte : gains, pertes et nombre de challenges payés sont
  multipliés. La simulation le vérifie.
- **Comptes échelonnés** : N = 2 ou 3, le k-ième ouvert k × 3 mois (63 séances) après le premier,
  chacun relancé après une perte. Départs du premier compte en 2023-2024, suivi de 24 mois après
  l'ouverture du premier compte. Mesures :
  - gain net total (retraits − challenges) ;
  - part des cas où l'on perd de l'argent, et pire cas ;
  - part du temps avec au moins un compte financé ;
  - délai avant le premier retrait, tous comptes confondus.
- Pour information : les mêmes mesures sur les départs 2011-2020.

### B. Une règle pour perdre moins de comptes (choix sur 2011-2020, contrôle sur 2023-2024)

- **Base** : la gestion actuelle.
- **Frein** : quand le coussin (solde − limite de perte) passe sous T, **une seule source est
  tradée**, à 1 MNQ. Les deux reprennent quand le coussin repasse au-dessus de T. Quatre règles :
  - T = 750 $ ou 1 250 $ ;
  - source gardée : le RSI(2) seul, ou la zone seule.
- **Choix** : la meilleure des 5 (base comprise) en gain net par an sur les départs 2011-2020, suivis
  24 mois.
- **Adoption dans le robot seulement si, sur les départs 2023-2024 suivis 24 mois**, la règle choisie
  fait un meilleur gain net par an que la base **et** ne perd pas plus de comptes par an.

Tous les essais sont inscrits dans `fonds/essais.csv`.
