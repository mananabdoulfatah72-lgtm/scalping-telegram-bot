# Arène, étape 2 : les variantes des bots (règles fixées avant tout calcul, 8 novembre 2026)

But : trouver des versions des trois bots (Supertrend NQ, Bot 3 en 1, XGBoost NQ) qui risquent moins le compte financé
Bulenox (Master 50K, Option 2 : plancher suiveur de 2 500 $ calculé en fin de journée et bloqué à 50 100 $, limite de la
firme 1 100 $ par jour, constance 40 % au retrait), en **tuant les mauvais trades**. Même rejeu que l'étape 1 : séances
complètes 2014 - 2 nov. 2026, minute par minute, 1 MNQ, 3 $ de frais, dollars au prix d'aujourd'hui.

## Les variantes (pour chacun des trois bots)

| Réglage | Valeurs |
|---|---|
| Limite de perte du jour du bot | 200, 300, 400 $ |
| Stop par trade | aucun ; 1,5 ATR (ATR 14 des bougies de 15 min, dernière bougie terminée avant l'entrée) |
| Heures d'entrée (New York) | toutes ; pas avant 10 h ; pas après 15 h |
| Marché calme (rang de la largeur de Bollinger sous 33 % à l'entrée) | tradé ; évité |
| Pause après une mauvaise série | aucune ; pas de nouvelle entrée tant que la somme des 20 derniers trades du bot est négative |

3 × 2 × 3 × 2 × 2 = 72 variantes par bot, 216 en tout, plus 3 **assemblages** (deux bots de base sur le même compte, 1 MNQ
chacun, limite commune de 400 $ : Supertrend + Bot 3 en 1, Supertrend + XGBoost, Bot 3 en 1 + XGBoost) : **219 variantes**.
Un trade évité laisse le bot à plat jusqu'à son trade suivant ; après un stop, le bot attend son trade suivant.

## Une variante est tuée si une seule de ces conditions manque (sur 2014 - 2026)

1. t des résultats par séance d'au moins 2,0, et elle survit à Benjamini-Hochberg (q = 5 %) sur les 219 ;
2. positive sur 2014 - 2022 **et** sur 2023 - 2026 ;
3. avec 6 $ de frais par aller-retour au lieu de 3 $, t d'au moins 1,5 ;
4. au moins 9 années positives sur 13 ;
5. sur le compte financé : survie à 60 séances au moins égale à celle de son bot de base, et pas plus de comptes grillés que
   lui dans la vie réelle (retraits toutes les 20 séances au-dessus de 52 600 $) ;
6. pire baisse cumulée pas plus de 25 % plus profonde que celle de son bot de base.

Les assemblages sont comparés au meilleur des deux bots qui les composent.

## Le vrai test : l'usine à variantes en marche avant

Choisir les variantes survivantes sur tout l'historique, c'est les choisir en regardant les réponses. Le seul test honnête :
pour chaque année Y de 2017 à 2026, on applique les règles 1 à 6 **sur 2014 → Y − 1 seulement**, on prend parmi les
survivantes celle qui a retiré le plus par an sur cette période (à égalité, la meilleure survie), et on la joue en Y.
Bout à bout, ces années donnent l'usine **hors échantillon**, pour chaque bot et pour l'ensemble des 219.

**Décision** : les variantes ne remplacent un bot que si l'usine, sur 2017 - 2026, fait **à la fois** mieux que le bot de
base en retiré par an **et** pas plus de comptes grillés. Sinon, les variantes ne sont qu'un ajustement au passé et le bot
de base reste. Une variante gardée passe ensuite par le suivi sur les séances neuves avant l'argent réel.

## Réserve écrite d'avance

Les probabilités de XGBoost NQ sont hors échantillon (marche en avant). Les règles du Supertrend et du Bot 3 en 1 sont
fixes, mais elles ont été choisies en regardant ce même historique : leurs chiffres sur 15 ans sont un peu flatteurs.
