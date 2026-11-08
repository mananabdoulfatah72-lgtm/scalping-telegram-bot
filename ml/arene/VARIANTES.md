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

## Addendum du 8 novembre 2026 : corrections de la double relecture, écrites avant le nouveau calcul

La première exécution (`resultats/etape2.json`) a été relue par deux relecteurs indépendants (code et conclusions). Leurs
défauts sont corrigés **avant** de relancer ; ce nouveau calcul vient donc après avoir vu un premier résultat, ce qui est
dit dans le rapport.

**Moteur (`bots.py`)**
- Le stop sort au prix du stop et le chemin du trade s'arrête à la minute d'avant (le prix extrême de la minute du stop
  n'est plus compté) ; une ouverture déjà au-delà du stop sort à cette ouverture.
- Le Bot 3 en 1 entre à la clôture de sa minute : son chemin commence à la minute suivante.
- Une sortie forcée par la limite du jour perd en plus 1 point de glissement ; le creux du jour inclut le résultat final.
- Une seule règle pour le Bot 3 en 1 sur toute la période : zone + C2 + Q1 sans le filtre delta (journal jusqu'au 27
  octobre 2026, puis la séance du 2 novembre).
- Les assemblages ont bien une limite **commune** de 400 $ : équité minute par minute des deux bots (pire prix de chacun à
  la même minute, donc prudent), tout coupé à −400 $.

**Vie réelle du compte** (remplace « retrait de tout au-dessus de 52 600 $ toutes les 20 séances, compte neuf gratuit »)
- Règles de retrait documentées dans `audit/README.md`, à vérifier chez Bulenox : 10 jours de trading par retrait, au
  moins 1 000 $, 52 600 $ gardés, les trois premiers retraits plafonnés à 1 500 $, constance 40 % depuis le dernier retrait.
- Un Master grillé oblige à repasser une qualification **avec le même bot** en 1 MNQ (objectif 53 000 $), payée 100 $
  toutes les 20 séances, plus 148 $ d'activation (hypothèses). Mesure principale : **net par an** = retiré − frais.
- Un seul parcours est trop instable (un décalage de quelques séances change les comptes grillés) : la vie est **moyennée
  sur des départs toutes les 20 séances**, chacun joué jusqu'à la fin de la période. On rapporte aussi la part des
  comptes neufs grillés dans l'année (250 séances).

**Variantes et règles**
- Doublons retirés : « pas avant 10 h » ne change rien au Bot 3 en 1 (première entrée à 10 h), « pas après 15 h » ne
  change rien à XGBoost (dernière entrée à 15 h). Les réglages de base sont marqués « (base) ».
- Règle 5 : survie à 60 séances au moins égale à celle du bot de base, et masters grillés par an pas plus nombreux.
- Pause : somme des 20 derniers trades du bot, pris ou non (sinon la pause ne pourrait jamais se lever).
- Sur une période passée (usine), la règle 2 devient « positive sur ses deux moitiés » et la règle 4 « au moins 9 années
  positives sur 13 en proportion » ; Benjamini-Hochberg est appliqué sur les p des 219 réglages, puis croisé avec les
  autres règles.
- **Adoption** d'une usine : net par an au moins **10 %** au-dessus du bot de base **et** pas plus de masters grillés par
  an, sur 2017 - 2026 (marge exigée, l'écart de la première exécution étant du bruit). L'usine globale est comparée au
  Bot 3 en 1 de base, fixé maintenant comme référence.
