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
