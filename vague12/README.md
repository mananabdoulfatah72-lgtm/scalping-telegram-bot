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
