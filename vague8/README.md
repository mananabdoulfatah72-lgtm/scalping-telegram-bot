# Vague 8 : la bonne taille (règles fixées le 9 octobre 2026, avant le calcul)

## Demande de l'utilisateur

Tout revérifier. Comprendre pourquoi, même avec les réglages prudents, on perd encore la moitié des challenges et la
plupart des comptes financés achetés en 2025, alors que le bot gagne à peine 1 % par mois. Viser **au moins 1 % par mois
(≈ 500 $ sur un 50K) et au moins 10 % par an, sans perdre le compte** ; si un compte doit être perdu, que ce soit après
assez de gains pour en racheter un. Chercher d'autres sources d'avantage si besoin. Rester sur des challenges 50K à prix
raisonnable (Lucid, DayTraders, les autres firmes connues). Résultats concrets, pas de fausses promesses.

## Diagnostic (fait avant de fixer ces règles, `diagnostic.py` → `diagnostic.txt`)

Le bot seul (zone 1 MNQ + RSI(2) de nuit sur 1 MES, filtre simulé aussi bon qu'en 2026, chaque trade au niveau
d'aujourd'hui), sans aucun compte autour :

| Année | Gain | Pire baisse depuis un plus haut |
|---|---|---|
| 2016 | +3 424 $ | −3 204 $ |
| 2020 | +13 346 $ | −3 619 $ |
| 2022 | +16 503 $ | −2 330 $ |
| 2025 | +9 841 $ | −2 707 $ |
| 2026 (9 mois) | +8 539 $ | −2 024 $ |

1. **Le bot gagne chaque année, mais ses baisses normales dépassent le seuil de 2 000 $.** Un compte 50K coupe à
   2 000 $ sous le plus haut. Le bot fait souvent −2 000 à −3 600 $ avant de remonter. Le problème n'est pas le manque de
   gain, c'est **la taille de la position par rapport au seuil**.
2. **1 MNQ est déjà trop gros pour ce seuil.** Au cours d'aujourd'hui (NQ 30 892), 1 MNQ vaut 61 783 $, plus que le
   compte de 50 000 $. Une séance bouge en moyenne de 865 $ par MNQ entre son plus haut et son plus bas (252 dernières séances). On ne peut pas descendre sous 1 MNQ avec le NQ.
3. **2025 :** +6 636 $ en avril (le krach), puis la zone a perdu −2 707 $ en grignotant du 21 avril au 1er août (74
   séances calmes). Ce n'est pas un jour catastrophe, c'est une longue série de petites pertes. Un compte acheté début
   2025 passe le challenge en avril, puis meurt pendant l'été ; un compte acheté à l'été le passe à l'automne, puis
   meurt en janvier 2026 (−1 815 $).
4. **Calcul simple :** avec un gain moyen de μ par mois, des écarts de σ par mois et un seuil a, la chance de toucher le
   seuil un jour est d'environ exp(−2μa/σ²). Avec μ ≈ 700 $, σ ≈ 1 500 $, a = 2 000 $ : ≈ 29 %, et plus encore quand
   les retraits empêchent le coussin de grandir. **Diviser la taille par deux** (μ et σ divisés par deux) donne ≈ 8 % ;
   **un seuil de 4 500 $** (compte 150K) avec la même taille donne ≈ 6 %.

## Pourquoi pas « 150 000 stratégies de plus »

Plus de **800 000** stratégies ont déjà été essayées dans ce projet (`fonds/essais.csv`) :
- quantitatives, sur 16 à 40 futures (machines 3 et 4 : 140 000 + 232 000) ;
- order flow (41 567) ;
- fixings de change (Tokyo, BCE, WM) et de l'or ;
- fins de mois et de trimestre au fixing de Londres ;
- Fed, stocks EIA, échéances d'options, saisonnalités, ICT, VWAP, profils de volume, VIX, GEX.

Seules la zone de bruit NQ, le filtre delta et le RSI(2) ont tenu. Essayer encore 150 000 stratégies sur les mêmes
données trouverait surtout du hasard qui ressemble à un avantage : c'est ce que les jumeaux de bruit ont montré à chaque
machine. **Cette vague ne cherche donc pas de nouvelle source : elle corrige la taille**, la vraie cause trouvée
ci-dessus.

## Les leviers (fixés maintenant)

1. **Zone exécutée sur MES au lieu de MNQ.**
   - Mêmes signaux (calculés sur le NQ), mêmes minutes d'entrée et de sortie, mais exécutés sur 1 MES aux prix de l'ES.
   - Au cours d'aujourd'hui, 1 MES vaut 39 024 $ (ES 7 805), et l'ES bouge moins que le NQ.
   - Frais : 1 $ de commission + 1 tick (1,25 $) par côté, donc **4,50 $ par aller-retour** (contre 3 $ sur MNQ).
   - Le filtre simulé est celui de la zone sur NQ (il est corrélé au trade NQ ; sur l'ES, la corrélation est un peu
     plus faible, donc ce choix est légèrement favorable).
2. **Taille selon le coussin** (coussin = solde − plancher, mesuré chaque soir). Ce levier vaut pour le challenge comme
   pour le compte financé :
   - zone sur **MES tant que le coussin est sous c**, sur MNQ au-dessus ;
   - c = 1,5 × la perte permise (3 000 $ sur un 50K), ou c = 2 × la perte permise (4 000 $ sur un 50K).
3. **Coussin gardé après un retrait.** Chaque retrait laisse au moins K $ entre le solde et le plancher bloqué :
   - K = 0 (retrait le plus grand permis, comme avant) ;
   - K = 1 × la perte permise ;
   - K = 2 × la perte permise.
4. **Comptes plus grands** (même bot à la même taille, seuil plus large) : LucidFlex 100K et 150K.
5. Le RSI(2) de nuit sur 1 MES (A3) reste partout. Taille 1× partout : plus de 2× ni de 3×, car c'est ce qui faisait
   perdre les challenges.

## Les comptes

| Compte | Objectif | Perte permise (fin de journée) | Retrait | Part | Prix |
|---|---|---|---|---|---|
| LucidFlex 50K | 3 000 $ | 2 000 $, bloquée à +100 $ | 5 jours à +150 $ ; 50 % du gain du cycle ; ≤ 2 000 $ ; ≥ 500 $ | 90 % | 146 $ une fois |
| LucidFlex 100K | 6 000 $ | 3 000 $, bloquée à +100 $ | 5 jours à +200 $ ; 50 % du gain du cycle ; ≤ 2 500 $ ; ≥ 500 $ | 90 % | 293 $ une fois |
| LucidFlex 150K | 9 000 $ | 4 500 $, bloquée à +100 $ | 5 jours à +250 $ ; 50 % du gain du cycle ; ≤ 3 000 $ ; ≥ 500 $ | 90 % | 407 $ une fois |
| Topstep 50K | règles de la vague 5 | 2 000 $ | règles de la vague 5 | 90 % | 49 $ par mois + 149 $ |
| FundedNext Legacy 50K | règles de la vague 6 | 2 000 $ | règles de la vague 6 | 80 % | 200 $ une fois |

Notes sur les comptes :
- LucidFlex : régularité de 50 % pendant l'évaluation, pas de limite du jour, pas de régularité sur le compte financé.
- Prix LucidFlex : prix affichés sans limite du jour (août 2026, sites d'avis) ; un code de 30 à 40 % les baisse
  (≈ 92 / 190 / 258 $).
- Topstep et FundedNext en 100K et 150K ne sont pas testés : leurs plafonds de retrait se contredisent d'une source à
  l'autre.

Il y a donc 5 comptes × 4 règles de zone (MNQ toujours, MES toujours, MES sous 1,5×, MES sous 2×) × 3 coussins gardés,
soit **60 candidates**.

## Mesures

Elles sont prises sur deux groupes d'achats :
- achats de la **fenêtre de choix** : 2012-2021 ;
- achats de la **vérification** : 2023 - mars 2026, dont 2025.

Pour chaque groupe, un achat toutes les 5 séances, 10 tirages du filtre simulé aussi bon qu'en 2026 :
- **challenge perdu** : part des achats qui touchent le plancher avant de réussir ;
- **compte financé perdu dans les 12 mois** : parmi les challenges réussis et suivis au moins 12 mois ;
- temps pour valider, retraits par mois d'un compte financé en vie.

On mesure aussi le **gain net par mois** d'un seul compte à la fois, racheté s'il est perdu. C'est la méthode de la
vague 6 : retraits × part − prix, mois du calendrier, choix 2012-2022, vérification 2023 - sept. 2026.

## Jugement (sécurité d'abord)

1. **Sûre** : sur les achats 2012-2021, challenge perdu ≤ 20 % **et** compte financé perdu dans les 12 mois ≤ 20 %.
2. **Retenue** : parmi les sûres, la meilleure en gain net par mois sur le choix 2012-2022.
3. **Validée** si, sur la vérification :
   - challenge perdu ≤ 25 % **et** compte financé perdu dans les 12 mois ≤ 25 % (achats 2023 - mars 2026) ;
   - gain net positif chaque année (2023-2026).

   Sinon, on prend la suivante sur le choix.
4. **Objectif atteint** si la retenue validée fait au moins **+500 $ par mois** en vérification.
5. On donnera aussi :
   - la meilleure candidate de chaque compte et la plus sûre ;
   - les achats de 2025 seuls ;
   - les résultats sans filtre (si le filtre ne vaut rien).

**À savoir avant d'y croire :**
- la vérification 2023-2026 a déjà été regardée de nombreuses fois, y compris dans ce diagnostic ;
- les règles des comptes viennent de sites d'avis ;
- le filtre est simulé.

## Contrôles (`test_vague8.py`)

1. Avec les réglages par défaut (zone sur MNQ, pas de seuil), le moteur redonne les résultats d'avant :
   - `test_vague4.py` à `test_vague7.py` passent ;
   - `vague7/prudent.txt` est redonné à l'identique.
2. Un trade de zone sur MES, sur un marché synthétique, vaut à la main : sens × (sortie − entrée de l'ES) × 5 $ − 4,50 $.
3. La règle du coussin : sous c, la zone passe sur MES ; au-dessus, sur MNQ (marché synthétique).
4. Le coussin gardé : aucun retrait ne laisse moins de K $ au-dessus du plancher bloqué.
5. Les paramètres des comptes 100K et 150K sont ceux écrits ici.

## Ajouts et corrections avant le calcul final (9 octobre 2026)

**Ajout descriptif** (après un essai à 2 tirages qui servait seulement à vérifier que le code tourne) :
- part des achats qui perdent de l'argent ;
- réponse à la condition de l'utilisateur : si un compte est perdu, que ce soit après avoir gagné de quoi en racheter.

**Revue indépendante du code.** Elle n'a trouvé **aucune erreur qui change les résultats** dans le moteur :
- zone sur MES, positions vendeuses, frais, limite du jour ;
- taille selon le coussin, coussin gardé ;
- prix des comptes.

Elle a relevé des biais de mesure, corrigés avant le calcul final :
1. **Challenges pas finis.** Pour les achats récents, un challenge encore en cours à la fin des données comptait comme
   « pas perdu ». On mesure maintenant la part des challenges **perdus parmi ceux qui sont terminés**, ce qui est plus
   sévère.
2. **Suivi trop court pour les comptes lents.** Avec 24 mois de suivi, la perte du compte financé dans les 12 mois ne
   comptait que les comptes validés en moins d'un an. Le suivi passe à **36 mois au plus**.
3. **Fenêtre de choix.** Les achats de fin 2021 étaient suivis jusque dans la vérification (2023). Ils sont maintenant
   arrêtés au 31 décembre 2022.
4. **Contrôle 1 bis.** Il comparait le nouveau moteur à lui-même. Il compare maintenant aux sorties du moteur d'avant la
   vague 8 : 213 achats, retraits séance par séance compris, `ref_moteur_avant.json`.
5. Détails sans effet sur les résultats :
   - avec c = 0, la zone ne peut plus passer sur MES ;
   - la plus sûre de chaque compte traite une valeur inconnue comme un échec ;
   - le gain net par achat est mesuré sur ses 24 premiers mois au plus.

## Résultats (calcul final après la revue) : `vague8.txt`, `sensibilite.txt`

Filtre simulé aussi bon qu'en 2026 (10 tirages). « Gain net par mois » = un seul compte à la fois, racheté s'il est
perdu, retraits × part − prix.

**Verdict fixé à l'avance : aucune candidate sûre et validée ; l'objectif de 500 $ par mois n'est pas atteint.**
- 23 candidates sur 60 sont sûres sur les achats 2012-2021, toutes des LucidFlex 100K ou 150K.
- Sur la vérification, elles gardent le compte :
  - challenge perdu 0 à 1 % ;
  - compte financé perdu dans les 12 mois 0 à 5 %.
- Mais elles échouent à « chaque année positive » : 2023, première année, est négative (prix payé, puis 8 à 12 mois de
  challenge sans retrait). Elles rapportent +233 $ par mois au mieux.

| Système (zone + RSI(2) de nuit sur 1 MES, taille 1×) | Gain net par mois (choix / vérification) | Challenge perdu (achats 2012-21 / 2023-26 / 2025) | Financé perdu en 12 mois (2012-21 / 2023-26 / 2025) | Temps pour valider | Prix |
|---|---|---|---|---|---|
| **LucidFlex 100K, zone 1 MNQ, garder 3 000 $** | +316 / +233 $ | 6 / 1 / 3 % | 17 / 5 % / pas encore mesurable | 7,8 mois (10,9 pour les achats 2025) | 293 $ |
| LucidFlex 150K, zone 1 MNQ | +312 / +234 $ | 1 / 0 / 0 % | 5 / 3 % / pas encore mesurable | 11,7 mois (14,1) | 407 $ |
| LucidFlex 50K, zone 1 MNQ, garder 4 000 $ | +324 / +255 $ | 20 / 19 / 46 % | 27 / 7 / 88 % | 3,6 mois | 146 $ |
| FundedNext Legacy 50K, zone 1 MNQ, garder 4 000 $ | +562 / +471 $ | 20 / 18 / 46 % | 26 / 8 / 100 % | 3,9 mois | 200 $ |
| Topstep 50K, zone 1 MNQ, garder 4 000 $ | +596 / +421 $ | 19 / 22 / 54 % | 28 / 20 / 88 % | 3,6 mois | 49 $ par mois + 149 $ |
| LucidFlex 50K, zone sur MES jusqu'à 3 000 $ de coussin | +308 / +172 $ | 21 / 0 / 1 % | 46 / 4 % / pas encore mesurable | 6,5 à 8 mois (10,9) | 146 $ |

**Ce qu'on apprend :**
1. **Garder un coussin après chaque retrait est le levier qui marche.** Sur Topstep 50K (achats 2012-2021), le compte
   financé perdu dans les 12 mois passe de 75 % (retrait maximal) à 43 % (garder 2 000 $), puis 28 % (garder 4 000 $).
   Le gain monte aussi (+386, +525, +596 $ par mois), parce qu'on rachète moins de comptes.
2. **La zone sur MES n'est pas une solution solide.** Elle protège le challenge en 2023-2026 (0 % perdu), pas en
   2012-2021 (21 %) : le signal du NQ exécuté sur l'ES y est plus faible.
3. **Les comptes plus grands gardent le compte.** Leur seuil de 3 000 à 4 500 $ est au-dessus des baisses normales du
   bot. Mais :
   - il faut 8 à 12 mois pour valider (objectif de 6 000 à 9 000 $) ;
   - la règle de retrait de LucidFlex, lue prudemment (50 % du gain de chaque cycle), laisse la moitié des gains sur le
     compte.
4. **Achats de 2025 :** sur un 50K à 1 MNQ, environ la moitié des challenges sont perdus et presque tous les comptes
   financés dans l'année. Aucun réglage sur 50K ne l'évite, sauf la zone sur MES, qui tombe à moins de 200 $ par mois.

**Sensibilité : la règle des 50 % de LucidFlex** (`sensibilite.py`, descriptif). Les sources se contredisent :
- 50 % du gain du **cycle** (lecture prudente, utilisée partout jusqu'ici) ;
- 50 % du gain **total** sur le compte (exemple de pipback : 1 600 $ de gain → 800 $ de retrait).

Les chances de perdre le compte ne changent presque pas ; le revenu presque double :

| Gain net par mois (choix / vérification) | 50 % du gain du cycle | 50 % du gain total |
|---|---|---|
| LucidFlex 100K, zone 1 MNQ, garder 3 000 $ | +316 / +233 $ | **+599 / +487 $** (financé perdu en 12 mois : 18 / 5 %) |
| LucidFlex 150K, zone 1 MNQ | +312 / +234 $ | +474 / +420 $ (financé perdu en 12 mois : 12 / 11 %) |
| LucidFlex 50K, zone 1 MNQ, garder 4 000 $ | +324 / +255 $ | +640 / +534 $ (mais challenge perdu 20 % ; 46 % en 2025) |

**Conclusion honnête :**
- Avec ce bot, sur ces comptes, on ne peut pas avoir à la fois 500 $ par mois et une faible chance de perdre le compte,
  sauf si LucidFlex applique les 50 % au gain total.
- Le meilleur compromis entre sécurité et revenu est **LucidFlex 100K**, zone sur 1 MNQ et RSI(2) de nuit sur 1 MES, en gardant 3 000 $ de
  coussin après chaque retrait :
  - environ +230 à +320 $ par mois en moyenne avec la lecture prudente, +490 à +600 $ avec la lecture large ;
  - il faut 8 à 11 mois pour valider.
- **À faire confirmer par Lucid avant d'acheter :**
  1. la règle des 50 % : gain du cycle ou gain total ;
  2. ce qui se passe après 5 retraits (passage à un compte LucidLive, non simulé) ;
  3. le prix du 100K (293 $ affiché sans limite du jour, environ 190 $ avec un code de 30 à 40 %).
- **Tout suppose le filtre delta aussi bon qu'en 2026.** Sans filtre, LucidFlex 100K perd 30 % des challenges et 39 %
  des comptes financés dans les 12 mois (achats 2012-2021).
