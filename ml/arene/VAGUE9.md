# Arène, vague 9 : la règle d'inactivité de Bulenox, et la nuit (règles fixées avant tout calcul, 9 novembre 2026)

Le contrat du compte Master (annexe A, transmis le 9 novembre 2026) impose **au moins une transaction tous les 5 jours de
trading**, sinon le compte est suspendu et le solde confisqué ; une activité artificielle « seulement pour éviter
l'inactivité » ne compte pas. Il permet aussi de garder une position **de 18 h à 16 h 59** (New York) : la nuit est permise,
il faut être à plat de 17 h à 18 h.

Constat (rejeu 2014 - 2026) : le Bot 3 en 1 a environ 8 séries par an de 5 séances ou plus sans trade ; avec le filtre VIX et
sans les jours de la Fed (« ton bot », Z12F), environ 10 par an, jusqu'à 48 séances de suite.

## A. Rester actif avec une vraie stratégie (2017 - 2026)

Référence **Z12F** : Bot 3 en 1, sans les jours de VIX inversé ni les jours de la Fed, 1 MNQ, limite 400 $.

| | Règle du 5e jour |
|---|---|
| K1 | après 4 séances de suite sans aucun trade, le 5e jour le bot prend aussi les signaux de **W1** (Supertrend trié, production, hors échantillon) ; si W1 n'en garde aucun ce jour-là, ceux du **Supertrend NQ** ; Z12F reste prioritaire (un contrat à la fois) |
| K2 | même règle avec seulement le **Supertrend NQ** |

Retenu si : **aucune série de 5 séances sans trade** sur 2017 - 2026 ; survie à 60 séances d'au moins 95 % ; au plus 20 % de
comptes neufs grillés dans l'année ; au plus 0,15 master grillé par an ; net par an au moins 90 % de celui de Z12F (rester
actif peut coûter un peu, pas plus de 10 %).

## B. La nuit (2011 - 2026)

Données : ouverture de 18 h de la session Globex (barre journalière de Yahoo, vérifiée sur les barres d'une heure du radar)
et ouverture de 9 h 30 des minutes du projet ; séances où les deux sources ne sont pas sur le même contrat (écart de plus de
0,6 % entre la clôture de la veille de Yahoo et celle des minutes) écartées.

| | Règle (1 MNQ, 3 $ de frais) |
|---|---|
| N1 | « La dérive de nuit » (Kelly et Clark 2011 ; Boyarchenko, Larsen et Whelan 2023) : achat à 18 h, vente à 9 h 30, chaque nuit |
| N2 | la même chose, seulement après une séance (9 h 30 - 16 h) en baisse (la dérive viendrait des déséquilibres de fin de séance) |

Retenu (comme piste, avant tout compte financé) si : t d'au moins 2 sur 2011 - 2026 et survie à Benjamini-Hochberg (q = 5 %)
sur N1 et N2 ; positif sur 2011 - 2022 et sur 2023 - 2026 (après la publication de 2023) ; t d'au moins 1,5 avec 6 $ de
frais ; au moins 11 années positives sur 16. On rapporte la pire nuit en $ pour 1 MNQ : sans le chemin minute par minute de
la nuit avant 2024, le passage au compte financé (avec un stop) sera une vague à part.

## Après le calcul (9 novembre 2026, `vague9.py`, `resultats/vague9.txt`)

Verdict des règles ci-dessus : **K1 retenu**, K2 tué, **N1 et N2 passent leurs règles** (piste seulement).

- Z12F : 94 séries de 5 séances ou plus sans trade sur 2017 - 2026 (9,7 par an, la plus longue 48 séances).
- K1 : aucune série ; 157 jours de secours (117 avec W1, 40 avec le Supertrend), +69 $ de plus par jour de secours ; survie 98 %,
  15 % de comptes neufs grillés dans l'année (Z12F : 4 %), 0,08 master grillé par an, net 3 285 $ par an (Z12F : 3 030 $).
- K2 : 28 % de comptes neufs grillés dans l'année, 0,21 master grillé par an, net 2 041 $ : tué.
- N1 : t 3,08 (2011 - 2022 : 2,46 ; depuis 2023 : 1,92), t 2,63 à 6 $ de frais, 13 années positives sur 16, 5 190 $ par an en
  1 MNQ ; **pire nuit −3 658 $, 46 nuits sous −1 100 $, 5 sous −2 500 $, pire baisse −15 065 $** : sans stop, une nuit peut griller
  le compte. N2 : t 2,14, 12 années sur 16. La journée 9 h 30 → 16 h sur les mêmes séances : t 0,88.

**Information écrite après coup** (`vague9_info.py`, pas une règle fixée d'avance) : le rejeu compte les séances complètes ;
si l'on compte aussi les demi-journées et jours fériés courts du fichier comme des jours sans trade (ce que Bulenox pourrait
faire), K1 garde 4 séries de 5 jours (la plus longue 6). Déclenché après 3 jours sans trade, aucune série ne reste (et le compte
fait mieux : 0 % de comptes grillés dans l'année, 5 943 $ par an, mais ces chiffres de compte bougent beaucoup pour un petit
changement de règle : à confirmer sur les séances neuves). Pour le vrai bot : compter les jours comme Bulenox et déclencher
après 3 jours sans trade, pour la marge.

## Relecture (#ultrareview, 9 novembre 2026) : K1 n'est pas prêt pour le vrai compte

Deux relecteurs indépendants (contrat contre résumé ; contrat contre simulateur et vrai bot). Chiffres revérifiés :

- **Le vrai bot n'est pas le bot simulé.** Le README règle la limite de perte du jour à 1 000 $ sur le Master ; l'arène
  simule 400 $. À 1 000 $, K1 grille **27 %** des comptes neufs dans l'année (règle : 20 % au plus), 0,14 master par an ;
  Z12F reste à 4 %. L'arène simule aussi la zone sans le filtre delta, sans le frein et sans plafond, que le README coche
  (et se contredit sur le filtre delta et le plafond).
- **Compteur du calendrier** (demi-journées comptées, `vague9_info.py`) : K1 après 4 jours garde 4 séries de 5 jours et
  0,21 master grillé par an (règle : 0,15) : il échoue aussi ainsi.
- **Peu d'épisodes** : les comptes grillés de K1 viennent de 3 épisodes (janvier 2022, décembre 2023, mars 2026), ceux de
  Z12F d'un seul. Les écarts de comptes grillés entre variantes (après 3 ou 4 jours) ne sont pas départageables.
- **Le contrat** : le Master s'arrête au 3e retrait (passage en funded, plancher initial de 2 000 $, ou fermeture) ; la
  part de 90 % n'était pas appliquée ; un trade déclenché par le compteur d'inactivité risque d'être vu comme « activité
  artificielle destinée uniquement à prévenir l'inactivité » (Annexe A) ; W1 est un modèle d'apprentissage (section 20,
  accord écrit). Sur un Master seul jusqu'au 3e retrait (limite 400 $) : K1 grillé avant le 3e retrait 17 %, Z12F 4 %.

Conclusion : K1 reste une piste ; ne pas le mettre en réel sans accord écrit de Bulenox et sans re-simuler le bot tel
qu'il est réglé.
