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

## Résultats (2 octobre 2026)

`comptes.py` → `comptes.txt`. Contrôle : sans frein, le simulateur redonne exactement celui de
`zone_deux/`.

### A. Plusieurs comptes

| Départs 2023-2024, 24 mois | Net moyen | Net médian | Pire cas | Perte d'argent | Challenges payés |
|---|---|---|---|---|---|
| 1 compte | +498 $ | +638 $ | −984 $ | 29 % des cas | 390 $ |
| 2 comptes le même jour | +996 $ | +1 275 $ | −1 968 $ | 29 % | 780 $ |
| 3 comptes le même jour | +1 495 $ | +1 913 $ | −2 952 $ | 29 % | 1 171 $ |
| 5 comptes le même jour | +2 491 $ | +3 188 $ | −4 920 $ | 29 % | 1 951 $ |
| 2 comptes, un tous les 3 mois | +683 $ | +1 275 $ | −1 968 $ | 39 % | 839 $ |
| 3 comptes, un tous les 3 mois | +621 $ | +990 $ | −2 952 $ | 44 % | 1 327 $ |

- Des comptes ouverts le même jour, avec les mêmes ordres, donnent **exactement N fois** le résultat
  d'un compte : ils gagnent et perdent ensemble. La chance de perdre de l'argent ne change pas.
- Les comptes échelonnés ne font pas mieux sur 24 mois : les derniers ouverts ont moins de temps pour
  arriver au premier retrait.
- **Sur les départs 2011-2020** (en échantillon), chaque compte perd en moyenne 22 $ sur 24 mois, et
  82 % des cas perdent de l'argent. Avec 5 comptes : −108 $ en moyenne, −3 280 $ dans le pire cas.
  **Multiplier les comptes multiplie l'avantage s'il existe, et la perte s'il n'existe pas.**

### B. Frein contre les comptes perdus

| Règle | 2011-2020 (choix) | 2023-2024 (contrôle) | Comptes perdus par an (contrôle) |
|---|---|---|---|
| Base | −11 $/an | +249 $/an | 0,69 |
| Sous 750 $, RSI(2) seul | +20 $/an | +304 $/an | 0,52 |
| **Sous 750 $, zone seule (choisie)** | **+70 $/an** | **+249 $/an** | **0,69** |
| Sous 1 250 $, RSI(2) seul | +67 $/an | +174 $/an | 0,94 |
| Sous 1 250 $, zone seule | −76 $/an | +228 $/an | 0,57 |

**Non adoptée** : la règle choisie fait exactement comme la base sur le contrôle. La variante « sous
750 $, RSI(2) seul » paraît meilleure sur 2023-2024, mais elle n'a pas été choisie sur 2011-2020.
L'adopter maintenant reviendrait à choisir sur le contrôle : elle n'est pas retenue.

**Conclusion** : aucun réglage testé n'évite de façon fiable la perte d'un compte. Un compte perdu
repart au challenge (environ 6 à 7 mois pour le repasser en 2023-2026). Plusieurs comptes ne protègent
pas : avec les mêmes ordres, ils perdent ensemble.
