# Vague 10 : freins contre les séries de pertes, un seul achat (règles fixées le 9 octobre 2026, avant le calcul)

## Demande de l'utilisateur

- **Un seul achat** de 50K : pas de rachat. Il faut savoir ce que rapporte ce compte-là et s'il survit.
- **Limiter les pertes** : se protéger quand ça tourne mal, au lieu de laisser les pertes brûler le compte.
- Ne pas faire de 2025 une année KO.

## Diagnostic (`diagnostic2025.py` → `diagnostic2025.txt`)

Comptes 50K achetés de janvier 2025 à mars 2026, bot zone 1 MNQ + RSI(2) de nuit sur 1 MES, en gardant 4 000 $ :
- **le bot a gagné en 2025** (+9 841 $), mais les comptes meurent surtout pendant le challenge, à deux moments :
  - **juillet-août 2025** (après les gains d'avril, la zone perd par petites touches pendant des semaines) ;
  - **janvier 2026** (−1 815 $ dans le mois), qui concentre la moitié des challenges perdus ;
- **ce ne sont pas de grosses pertes d'un coup** : le pire jour de 2025 est −821 $ ;
- **la règle de régularité n'y est pour rien** : sans elle, les mêmes challenges sont perdus (0 % de différence).

Un stop par trade existe déjà (la zone sort sur son stop). Contre une glissade de petites pertes, ce qui peut aider est
un **frein** déclenché par le recul du compte sous son plus haut.

## Les freins (fixés maintenant)

Tous avec la règle retenue en vague 9 (pas de zone les jours de la Fed). Le coussin est l'écart entre le solde de la
veille et le plancher : 2 000 $ au plus haut, il baisse quand le compte recule.

| Frein | Ce qu'il fait |
|---|---|
| aucun | le bot tel quel |
| MES sous 1 750, 1 500, 1 250 ou 1 000 $ de coussin | dès que le compte recule de 250, 500, 750 ou 1 000 $ sous son plus haut, la zone passe sur MES (environ deux fois moins de risque) jusqu'à ce que le coussin remonte |
| pause de 10 ou 20 séances sous 1 500 ou 1 000 $ de coussin | le bot entier s'arrête 10 ou 20 séances ; le frein se réarme quand le coussin repasse au-dessus du seuil |
| stop du jour 300 ou 500 $ | tout est fermé et le bot s'arrête jusqu'au lendemain quand la journée perd 300 ou 500 $ |
| MES sous 1 500 $ + stop du jour 500 $ | les deux |

Ces 12 freins sont essayés sur 3 comptes :
- LucidFlex 50K ;
- Topstep 50K ;
- FundedNext Legacy 50K.

Chaque compte est essayé en gardant 2 000 $ ou 4 000 $ après chaque retrait, soit **72 candidates**.

## Mesures : un seul achat, sans rachat

Un achat toutes les 5 séances, 10 tirages du filtre simulé aussi bon qu'en 2026, suivi jusqu'à 36 mois. Pour chaque
achat :
- challenge réussi ou perdu, et temps pour valider ;
- compte financé perdu dans les 12 mois ;
- retraits par mois tant que le compte vit ;
- **argent net de l'achat sur ses 24 premiers mois** (retraits × part − prix) ;
- part des achats qui perdent de l'argent.

Groupes d'achats :

| Groupe | Achats | Rôle |
|---|---|---|
| Choix | 2012-2021 (pas suivis après 2022) | sélection |
| Vérification | 2023 - mars 2026 | validation |
| 2025 | 2025 - mars 2026 | test de l'année difficile |

## Jugement

1. **Sûre** : sur les achats 2012-2021, challenge perdu ≤ 20 % et compte financé perdu dans les 12 mois ≤ 20 %.
2. **Retenue** : parmi les sûres, le plus d'argent net par achat sur 24 mois (achats 2012-2021).
3. **Validée** si, sur les achats 2023 - mars 2026 :
   - challenge perdu ≤ 25 % ;
   - compte financé perdu dans les 12 mois ≤ 25 % ;
   - argent net par achat positif ;
   - **et, pour les achats de 2025, challenge perdu ≤ 25 %** (l'année difficile, jamais utilisée pour choisir).

   Sinon, on prend la suivante.
4. On donne aussi la meilleure de chaque frein, pour voir lequel protège vraiment.

**À savoir avant d'y croire :**
- 2023-2026 a déjà été regardé de nombreuses fois ;
- le diagnostic ci-dessus a été fait sur 2025 ;
- le filtre est simulé.

## Contrôles

- `vague8/test_vague8.py` : par défaut, le moteur redonne exactement le moteur d'avant la vague 8 (213 achats,
  retraits séance par séance).
- `test_vague10.py` : la pause arrête le bot le bon nombre de séances et se réarme au bon moment (marché synthétique).

## Résultats (9 octobre 2026) : `vague10.txt`

**Verdict fixé à l'avance : aucune candidate n'est sûre sur les achats 2012-2021.** Sur cette période, toutes perdent
plus de 20 % des comptes financés dans l'année. Rien n'est donc « validé » au sens strict.

**Mais un frein change tout sur la période récente :** passer la zone sur MES dès que le compte recule de 500 $ sous son
plus haut (coussin sous 1 500 $), et revenir au MNQ quand il remonte.

FundedNext Legacy 50K, garder 4 000 $ après chaque retrait, pas de zone les jours de la Fed, **un seul achat** :

| Achats | Challenge réussi / perdu | Temps pour valider (moitié / 3 sur 4) | Financé perdu en 12 mois | Retraits par mois en vie | Net de l'achat sur 24 mois (moyenne / médiane) |
|---|---|---|---|---|---|
| Sans frein, 2023 - mars 2026 | 82 % / 18 % | 3,4 / 5,6 mois | 10 % | 435 $ | +4 672 / +6 024 $ |
| **Frein MES sous 1 500 $, 2023 - mars 2026** | **93 % / 3 %** | 5,0 / 9,0 mois | **3 %** | 388 $ | +3 980 / +3 938 $ |
| Sans frein, achats 2025 - mars 2026 | 57 % / 43 % | 7,1 / 11,3 mois | — | — | trop tôt |
| **Frein MES sous 1 500 $, achats 2025 - mars 2026** | **87 % / 6 %** (8 % pas fini) | 9,3 / 13,3 mois | — | — | trop tôt |
| Sans frein, 2012-2021 | 80 % / 20 % | 3,8 / 5,3 mois | 23 % | 531 $ | +5 814 / +4 293 $ |
| Frein MES sous 1 500 $, 2012-2021 | 81 % / 19 % | 4,3 / 6,8 mois | 25 % | 501 $ | +5 035 / +3 162 $ |

Pour les achats 2025, le net est encore négatif seulement parce que les données s'arrêtent en septembre 2026 : la
plupart de ces comptes n'ont pas encore eu le temps d'être financés.

**Ce que montrent les autres freins :**
- **La pause du bot (10 ou 20 séances) est mauvaise partout.** Elle rate les reprises et perd plus de challenges.
- **Le stop du jour (300 ou 500 $) aide un peu en 2025** (challenge perdu 35 à 49 % au lieu de 43 à 51 %), mais coûte
  beaucoup de gains. Les pertes de 2025 ne sont pas de gros jours.
- **Le frein MES est le seul qui protège nettement.** Le seuil de 1 500 $ est le meilleur compromis ; à 1 750 $, on
  protège encore plus (2 % de challenges perdus en 2025), mais on valide plus lentement.

**Limites, à dire clairement :**
- Le frein n'aide pas sur 2012-2021 : la zone exécutée sur MES y était faible (vague 8). Il marche dans le régime
  récent, où l'ES et le NQ bougent ensemble.
- La famille de freins a été choisie **après** avoir regardé comment mouraient les comptes de 2025. Seule l'année 2025
  n'a pas servi à choisir le seuil.
- Le filtre delta est simulé.
- Valider prend plus longtemps : 5 mois en médiane, 9 pour les achats de 2025.

## Budget de 30 € au plus (`budget30.py` → `budget30.txt`, descriptif)

Recherche du 9 octobre 2026 (sites d'avis) des comptes 50K à 30 € au plus avec un code, robots acceptés :

| Compte | Prix | Résultat de la recherche |
|---|---|---|
| **Bulenox 50K Qualification** | ≈ 19 $ avec un code à −89 % | robots personnels acceptés (avec accord préalable selon certaines sources) ; **148 $ d'activation à la réussite** ; paiement unique depuis le 17 août 2026 selon un article, à vérifier |
| Funded Futures Family | ≈ 27 $ | robots interdits |
| DayTraders Static 50K | 20 à 30 $ | plancher fixe de 1 000 $, déjà simulé : challenges très souvent perdus |
| Goat Funded Futures EOD | ≈ 34,50 $ avec un code à −50 % | non simulé |

Simulation de **Bulenox 50K option 2** :
- challenge : perte 2 500 $ en fin de journée, limite du jour douce de 1 100 $ ;
- compte Master : 10 jours par cycle, meilleur jour ≤ 40 %, ≤ 1 500 $ par retrait pour les 3 premiers, 100 % pour le
  trader, compte réel après 3 retraits (non simulé au-delà) ;
- un seul achat, bot de la vague 10.

| Achats | Frein | Challenge perdu | Validé (moitié en) | Master perdu en 12 mois | Net sur 24 mois (médiane, prix et activation compris) |
|---|---|---|---|---|---|
| 2023 - mars 2026 | aucun | 10 % | 3,6 mois | 22 % | +3 858 $ |
| 2023 - mars 2026 | **MES dès 750 $ sous le plus haut** | **5 %** | 4,4 mois | **13 %** | +3 835 $ |
| 2025 - mars 2026 | aucun | 25 % | 6,1 mois | — | trop tôt |
| 2025 - mars 2026 | **MES dès 750 $ sous le plus haut** | **10 %** | 8,8 mois | — | trop tôt |
| 2012-2021 | **MES dès 750 $ sous le plus haut** | 11 % | 4,1 mois | 23 % | +2 577 $ |

Retraits : le premier arrive environ 4 mois après la validation, puis environ 1 400 $ par retrait.

## FundedNext Futures Flex 50K (règles données par l'utilisateur, `flex50k.py` → `flex50k.txt`, descriptif)

Règles du Flex 50K :
- challenge : objectif 2 500 $, **perte max 1 500 $** en fin de journée, régularité 40 % ;
- compte financé : 5 jours à +200 $, retrait ≤ 50 % des profits et ≤ 1 500 $, 95 % pour le trader, revue après 5
  retraits.

Résultats :
- **Avec la zone sur MNQ**, le seuil de 1 500 $ est trop serré : challenge perdu 28 % (2023-26) et 58 % (achats 2025),
  et le frein « MES dès 500 $ sous le plus haut » n'y change presque rien.
- **Avec la zone toujours sur MES** : challenge perdu 3 % (2023-26) et 7 % (2025). Mais :
  - il faut environ 8 mois pour valider (9 en 2025) ;
  - le premier retrait arrive vers le 11e-12e mois ;
  - la 1re année financée rapporte environ 1 900 à 2 800 $ (en gardant 1 500 $) ;
  - sur 2012-2021 : 26 % de challenges perdus et environ la moitié des comptes financés perdus dans l'année.

Le Legacy 50K (perte 2 000 $) reste nettement meilleur pour ce bot.
