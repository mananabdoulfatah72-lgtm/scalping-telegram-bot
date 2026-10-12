# Vague 12 : une version du bot pour un challenge de 30 jours (règles fixées le 12 octobre 2026, avant le calcul)

## Demande de l'utilisateur

Bulenox limite maintenant le challenge à 30 jours. Avec le bot tel quel, seulement environ 5 % des challenges sont
validés dans ce délai (`montecarlo/trente_jours.py`). L'utilisateur demande :
- une version du bot pensée pour 30 jours : plus de contrats pendant le challenge, puis retour à 1 au compte Master ;
- une comparaison avec les firmes sans limite de temps qui tiennent dans son budget ;
- de mesurer le gain de chances de valider, mais aussi le risque de perdre, avant de payer quoi que ce soit.

## Règles des comptes (recherche du 12 octobre 2026, sites d'avis et aide des firmes, à confirmer au panier)

**Bulenox Legacy Qualification 50K option 2** (limite de 30 jours depuis le 17 août 2026) :
- challenge : objectif +3 000 $, perte max 2 500 $ en fin de journée, bloquée à +100 $, limite du jour douce de 1 100 $
  (la journée s'arrête, le compte vit) ;
- **30 jours calendaires** à partir de l'achat, sans prolongation ;
- Master : comme les vagues 10 et 11 (10 jours de trading par cycle, meilleur jour ≤ 40 % du gain du cycle, 52 600 $ à
  garder, retraits de 1 000 à 1 500 $, compte réel après 3 retraits, non simulé au-delà) ;
- prix : 19,25 $ avec un code à −89 % (peut-être expiré le 13 octobre), et 148 $ d'activation à la réussite.

**Bulenox Momentum EOD 50K** (aide de Bulenox) :
- challenge : objectif +3 000 $, perte max 2 250 $ en fin de journée, limite du jour 1 200 $, 4 mini au plus ;
  **30 jours calendaires**. Le blocage du plancher n'est pas publié : supposé à +100 $, comme le Legacy ;
- Master activé gratuitement. Ses règles ne sont pas claires, d'une source à l'autre. Supposées :
  - perte 2 250 $ bloquée à +100 $ et limite du jour 1 200 $ ;
  - 5 jours qualifiants à +150 $ au moins par cycle ;
  - meilleur jour ≤ 35 % du gain du cycle ;
  - 52 600 $ à garder, retraits de 1 000 à 1 500 $, compte réel après 3 retraits.

  Variante de contrôle : les règles du Master Legacy ;
- prix : 143 $ (85,80 $ avec la remise de lancement de 40 %, peut-être finie). Pas d'activation.

**Goat Funded Futures EOD 50K** (sans limite de temps, robots acceptés selon un guide) :
- objectif +3 000 $ (6 %), perte max 2 000 $ en fin de journée bloquée à +100 $, pas de limite du jour, meilleur jour
  ≤ 50 % du gain ;
- prix : 34,50 $ avec un code à −50 % (peut-être pas valable sur l'EOD), 59 à 69 $ sans code ;
- les règles du compte financé sont trop contradictoires selon les sources : **seul le challenge est simulé**.

**FundedNext Futures Flex 50K** (sans limite de temps, robots acceptés selon une source récente) :
- règles de `vague10/flex50k.py` :
  - challenge : objectif 2 500 $, perte max 1 500 $ en fin de journée, meilleur jour ≤ 40 % ;
  - financé : 5 jours à +200 $, retrait ≤ 50 % du gain du cycle et ≤ 1 500 $, 95 % pour le trader, garder 1 500 $,
    5 retraits ;
- prix : 69,99 $ en promotion. **Au-dessus du budget**, montré pour comparer.

**DayTraders Static 50K** (20 à 30 $, positions de nuit permises) : déjà simulé (`static50k/`, `intraday50k/`). Avec un
plancher fixe de 1 000 $, 67 % des départs de 2025 étaient perdus. Pas recalculé ici, rappelé dans le bilan.

**Hypothèse commune** : toutes ces firmes sont jouées en **mode à plat**, comme pour Bulenox :
- zone en séance ;
- RSI(2) de nuit sur MES, de 18 h à 9 h 30 (New York) ;
- pas de zone les jours de la Fed.

Les règles de nuit de Goat et de FundedNext n'ont pas été trouvées.

## Candidates (fixées maintenant)

**Bulenox, Legacy et Momentum : 8 versions chacune, soit 16.**
- **Taille pendant le challenge** : 1, 2, 3 ou 4 fois. Chaque nouvelle entrée de la zone (MNQ, ou MES sous le frein)
  et du RSI(2) de nuit (MES) est multipliée. **Retour à 1 au Master.**
- **Frein** pendant le challenge :
  - avec : la zone passe sur MES quand le coussin descend à 750 $ sous la perte max, c'est-à-dire sous 1 750 $ (Legacy)
    ou 1 500 $ (Momentum) ;
  - ou sans frein.
- Au Master, toujours : taille 1, frein, et plafond de 500 $ par jour (vague 11).

**Sans limite de temps (références, le bot tel quel, taille 1)** :
- Goat EOD : avec frein (1 250 $) ou sans ;
- FundedNext Flex : zone toujours sur MES, ou zone sur MNQ avec frein (750 $).

La vague 6 avait essayé la taille 3× en challenge sur d'autres comptes. Personne n'a encore mesuré les tailles 2 à 4
avec une limite de 30 jours.

## Mesures

**Achats** : chaque séance comme jour d'achat possible, dans le vrai calendrier, sans tirage. Les 30 jours sont
calendaires, soit 18 à 22 séances.

**Filtre delta simulé** :
- 10 tirages « aussi bon qu'en 2026 » ;
- 10 tirages « deux fois plus faible » ;
- sans filtre.

**Groupes d'achats** :

| Groupe | Achats | Rôle |
|---|---|---|
| Choix | 2012-2021 | sélection (suivi arrêté au 31 décembre 2022) |
| Vérification | 2023 - août 2026 | validation |
| 2025 | 2025 | année difficile, jamais utilisée pour choisir |

**Pour chaque candidate** :
- challenge validé, perdu ou expiré, et séances pour valider ;
- au Master : au moins un retrait dans les 24 mois, Master perdu ;
- argent net d'un achat sur 24 mois : retraits × part − prix − activation, seulement pour les achats suivis 24 mois ;
- part des achats qui perdent de l'argent.

Un challenge **perdu** et un challenge **expiré** coûtent la même chose : le prix. Ce qui compte, c'est la chance de
valider, puis ce que rapporte le Master.

## Jugement (fixé maintenant)

1. **Version 30 jours retenue**, pour chaque compte Bulenox : la candidate qui valide le plus souvent en 30 jours sur
   les achats 2012-2021 (filtre comme 2026). À égalité à 1 point près, la plus petite taille.
2. **Elle est validée** si, sur les achats 2023 - août 2026 (filtre comme 2026) :
   - elle valide au moins deux fois plus souvent que le bot tel quel (taille 1, frein) ;
   - **et** l'argent net moyen d'un achat sur 24 mois est positif (achats 2023 - septembre 2024, les seuls suivis
     24 mois), prix et activation compris.
3. **Comparaison finale** de tous les comptes :
   - argent net moyen par achat ;
   - chance de valider ;
   - part des achats perdants ;
   - prix payé avant de savoir.

   Elle est faite sur les achats 2012-2021 et 2023 - septembre 2024, avec le filtre comme 2026 et deux fois plus
   faible. Pour Goat, seuls le challenge et le prix sont comparés.
4. **Rien n'est acheté** si aucun compte dans le budget n'a un argent net moyen positif avec le filtre deux fois plus
   faible.

**À savoir avant d'y croire :**
- 2023-2026 a déjà été regardé de nombreuses fois ;
- le filtre est simulé ;
- les règles des comptes viennent de sites d'avis ;
- plus de taille veut dire plus de glissement réel que le backtest (1,5 point par aller-retour sur la zone).

## Contrôles (`test_vague12.py`)

Sur 300 achats tirés au hasard :
- une limite très longue redonne exactement le parcours sans limite (sorties et retraits) ;
- avec 30 jours, un achat est validé si et seulement si il validait dans les 30 jours sans limite. Il est alors
  identique, sinon il expire, sauf s'il était perdu avant la limite. Vérifié en taille 1 et en taille 3 ;
- un frein du compte financé égal à celui du challenge redonne l'ancien appel ;
- taille 1 Legacy : le moteur minute par minute avec la limite redonne exactement le moteur journalier du Monte Carlo
  (mêmes issues, mêmes séances pour valider).

Par défaut, le moteur reste celui d'avant : `vague8/test_vague8.py` donne 213 achats identiques, et
`montecarlo/test_montecarlo.py` repasse.

## Résultats (12 octobre 2026) : `vague12.txt`, `detail12.txt`

### Jugement fixé à l'avance

**Version 30 jours retenue, pour les deux comptes Bulenox : taille 4 sans frein en challenge**, puis taille 1, frein
et plafond de 500 $ au Master. Elle est **validée** pour les deux comptes.

| Bulenox Legacy, filtre comme 2026 | Validé en 30 jours | Perdu | Expiré | Séances pour valider | Net moyen d'un achat sur 24 mois |
|---|---|---|---|---|---|
| Bot tel quel (taille 1, frein), 2012-2021 | 5 % | 1 % | 94 % | 17 | +135 $ |
| **Taille 4 sans frein, 2012-2021 (choix)** | **41 %** | 38 % | 22 % | 9 | **+1 149 $** |
| Bot tel quel, 2023 - août 2026 | 2 % | 0 % | 98 % | 17 | +55 $ |
| **Taille 4 sans frein, 2023 - août 2026 (vérification)** | **40 %** | 45 % | 15 % | 9 | **+1 814 $** |
| Taille 4 sans frein, sans filtre, 2023 - août 2026 | 32 % | 58 % | 11 % | 8 | +1 331 $ |
| Taille 4 sans frein, achats 2025 (jamais utilisés pour choisir) | 32 % (28 % sans filtre) | 49 % | 18 % | 11 | trop tôt |

Le net est calculé sur les achats suivis 24 mois : 2012-2020 pour le choix, 2023 - septembre 2024 pour la vérification.

**Momentum** : mêmes chances de valider (38 % en vérification), net moyen +1 774 $. Mais il faut payer 143 $ avant de
savoir, contre 19,25 $ pour le Legacy. Avec les règles du Master Legacy à la place des règles supposées, le résultat
est presque le même (+1 709 $).

### Ce que devient un achat (`detail12.txt`, Legacy, taille 4 sans frein)

| Achats | Challenge raté (−19 $) | Validé puis Master perdu sans retrait (−167 $) | 1 ou 2 retraits | 3 retraits (≈ +4 300 $) | Net moyen |
|---|---|---|---|---|---|
| 2012-2020, filtre comme 2026 | 59 % | 7 % | 6 % | 27 % | +1 149 $ |
| 2012-2020, filtre deux fois plus faible | 62 % | 10 % | 5 % | 23 % | +957 $ |
| 2023 - sept. 2024, filtre comme 2026 | 52 % | 0 % | 1 % | 47 % | +1 814 $ |
| 2023 - sept. 2024, filtre deux fois plus faible | 55 % | 1 % | 4 % | 40 % | +1 600 $ |

Deux achats de suite (le second un mois plus tard si le premier rate) : environ 62 à 73 % de chances de valider au moins
une fois (approximation).

**Pourquoi plus de taille gagne ici** : un challenge perdu et un challenge expiré coûtent la même chose, le prix. Avec 30
jours, perdre plus souvent ne coûte rien de plus, alors que valider deux fois plus vite change tout. La taille 4 valide
en 9 séances médianes, quand elle valide.

### Le Master en taille 1 après la validation (`master12.py` → `master12.txt`)

Retour à 1 MNQ, avec le frein (750 $ sous le plus haut) et le plafond de 500 $ par jour.

| Validations (filtre comme 2026 / deux fois plus faible) | Master perdu avant tout retrait | 1er retrait (médiane après la validation) | 2e / 3e retrait | 3 retraits atteints |
|---|---|---|---|---|
| Achats 2012-2020 | 17 % / 24 % | 4,9 / 5,4 mois | 7,1 / 7,6 puis 8,8 / 9,8 mois | 68 % / 62 % |
| Achats 2023 - sept. 2024 | 0 % / 1 % | 4,0 / 4,5 mois | 6,3 / 7,3 puis 8,7 / 11,0 mois | 96 % / 90 % |

Il n'y a rien à retirer les premiers mois. Bulenox demande de garder 52 600 $, et le premier retrait est d'au moins
1 000 $ : le Master doit d'abord gagner environ 3 600 $. Ensuite, chaque retrait est d'au plus 1 500 $. Soit environ
4 500 $ en 9 mois quand tout va bien, puis le compte réel, non simulé.

### Comparaison avec les comptes sans limite de temps (net moyen d'un achat sur 24 mois)

| Compte | Prix avant de savoir | 2012-2020 (comme 2026 / moitié) | 2023 - sept. 2024 (comme 2026 / moitié) | Validé (vérif.) | Achats perdants (vérif.) |
|---|---|---|---|---|---|
| **Bulenox Legacy, taille 4 sans frein** | **19,25 $** (+148 $ à la réussite) | +1 149 / +957 $ | +1 814 / +1 600 $ | 40 % | 52 % |
| Bulenox Momentum, taille 4 sans frein | 143 $ | +1 092 / +884 $ | +1 774 / +1 448 $ | 38 % | 54 % |
| FundedNext Flex, zone toujours sur MES | 69,99 $ | +1 197 / +813 $ | +2 438 / +1 899 $ | 90 % | 6 % |
| FundedNext Flex, zone MNQ et frein | 69,99 $ | +1 513 / +1 016 $ | +2 262 / +1 571 $ | 72 % | 16 % |
| Goat EOD, frein (challenge seulement) | 34,50 $ | — | — | 87 % (perdu 7 %) | — |

- **FundedNext Flex (zone sur MES)** est le plus sûr sur la période récente : 90 % validés, 6 % d'achats perdants. Mais :
  - il coûte deux fois le budget ;
  - il est lent, avec 150 séances médianes pour valider (environ 7 mois) ;
  - sur 2012-2021, il perd 51 % des achats. La zone sur MES n'y marchait pas (vague 8).
- **Goat EOD** valide souvent (80 à 87 %), mais lentement (70 à 100 séances). Il perd 24 à 49 % des challenges achetés
  en 2025. Ses règles de compte financé sont trop floues pour être simulées.
- **Règle 4** : dans le budget, la version 30 jours du Legacy a un net moyen positif avec le filtre deux fois plus
  faible, sur les deux périodes.

### Revue (ce qui pourrait rendre ces chiffres trop beaux)

- **Taille 4, c'est le bord de la grille.** La taille 5 n'a pas été essayée. L'écart entre 3 et 4 est déjà faible (36 →
  41 % sur le choix), parce que les pertes montent presque autant que les validations.
- **La limite du jour de Bulenox est supposée « douce »** : la journée s'arrête, le compte vit. En taille 4, elle est
  souvent touchée. Si Bulenox la traite comme une faute qui fait perdre le compte, les challenges perdus montent. **À
  confirmer par écrit.**
- **Glissement** : 4 MNQ au marché restent petits pour le marché, mais le backtest compte 1,5 point par aller-retour et
  par contrat. Un vrai remplissage peut coûter un peu plus.
- **Moins dépendant du filtre que le bot tel quel** : sans filtre, 32 % de validés et +1 331 $ en vérification.
- 2023-2026 a déjà été regardé souvent ; le filtre est simulé ; les règles viennent de sites d'avis ; le Master est
  suivi jusqu'à 3 retraits seulement (compte réel ensuite).
- Les retraits du Master arrivent des mois après la validation. Le gain est un gain sur 24 mois, pas tout de suite.

### Réglages du bot pour cette version (`bot3en1`, sans changement de code)

| Réglage | Challenge (30 jours) | Master |
|---|---|---|
| MNQ par source | **4** | **1** |
| Frein | **0** (jamais) | 750 |
| Plafond de gain du jour | 0 | 500 |
| Limite de perte du jour | 1 050 (Legacy) ou 1 150 (Momentum) | idem |
| Perte max / blocage | 2 500 / 100 (Legacy) ou 2 250 / 100 (Momentum) | idem |

« MNQ par source » multiplie la zone (MNQ ou MES), le MES de nuit et le MES du frein, comme la simulation.
