# Arène, vague 7 : le modèle pour régler la taille de Z12 (règles fixées avant tout calcul, 9 novembre 2026)

**Idée née des résultats de la vague 6** (dit d'avance) : M3, les trades de Z12 gardés par le modèle (W1 de production
appliqué aux signaux de Z12, marche en avant 2017 - 2026), n'a grillé aucun compte financé neuf dans l'année, mais
rapporte moins que Z12 parce qu'il ne garde qu'un trade sur deux. Au lieu de jeter les autres, on s'en sert pour la
**taille** : les trades jugés bons reçoivent un contrat de plus.

## Les 3 tests (2017 - 2026, cadre de l'arène, vie réelle, coussin 2 600 $)

| | Règle |
|---|---|
| S1 | Z12 : 1 MNQ sur chaque trade, **2 MNQ sur ceux que le modèle garde** ; limite du jour 800 $ |
| S2 | M3 (seulement les trades gardés) en **2 MNQ** ; limite 800 $ |
| S3 | M3 en 1 MNQ, **2 MNQ dès que la marge du compte atteint 3 500 $** (limite 400 $ puis 800 $) |

Les probabilités viennent de la même marche en avant que la vague 6 (pour chaque année, le modèle n'a appris que sur
les années d'avant).

## Retenu si (face à Z12 seul en 1 MNQ, 2017 - 2026)

1. t des résultats par séance d'au moins 2 et survie à Benjamini-Hochberg (q = 5 %) sur les 3 ;
2. positif sur 2017 - 2022 et 2023 - 2026 ; t d'au moins 1,5 avec 6 $ de frais par MNQ ; au moins 7 années positives sur 10 ;
3. compte financé : survie à 60 séances d'au moins 95 %, au plus 20 % de comptes neufs grillés dans l'année, au plus
   0,15 master grillé par an ;
4. **net par an au moins 30 % au-dessus de Z12 seul** ;
5. retrait de la première année au moins égal à celui de Z12 seul.
