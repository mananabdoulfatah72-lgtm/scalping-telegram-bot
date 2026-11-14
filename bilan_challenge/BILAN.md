# Chaque bot rejoué depuis l'achat du challenge Bulenox 50K (14 novembre 2026)

> **Correctif du 14 novembre 2026.** Ce bilan contient deux erreurs, voir `SUPERTREND.md` :
> - un faux prix du 30 octobre (ouverture à 29 562 à 15 h 03, New York) fausse cette séance. Les « perdu le
>   30 oct. » à 1 MNQ et les −1 020 $ à 4 MNQ de ce jour-là sont faux. Supertrend à 1 MNQ valide le 4 novembre ;
> - ce bilan suit le plancher en fin de journée, alors que ton compte Bulenox est en Option 1 : plancher suivi
>   minute par minute sur le plus haut latent.

Période : du 13 octobre 2026 (1re séance du challenge) au 13 novembre 2026, 24 séances. Le NQ passe de 30 618 à
28 026 points. Chaque bot est rejoué par son propre code (moteurs C# de `bot3en1/` de la branche
`claude/optimistic-ptolemy-xs24ra`, machine de veille `flux/veille.py`, journaux des robots de `main`), avec les minutes
NQ de `zone/robot/nq_1min.csv.gz` à jour au 13 novembre. Jusqu'au 11 novembre, les trades sont ceux du rejeu du
12 novembre (`chantier/` de la branche `claude/loving-mccarthy-u21aw6`), à un écart de 0,5 point près le 11 novembre.

Règles du challenge appliquées (celles de `audit/risque.py`) : départ 50 000 $, objectif +3 000 $, perte max suivie de
2 500 $ en fin de journée avec plancher bloqué à 50 100 $, échec dès que le compte touche le plancher pendant la
séance, 30 jours calendaires (jusqu'au 11 - 12 novembre). Frais de 3 $ par MNQ ; à 4 MNQ, la limite du jour du bot
(1 000 $) est coupée sur les plus bas et plus hauts de chaque minute.

## Bots NQ intraday (permis chez Bulenox), rejoués trade par trade

| Bot, derniers réglages | Trades | Gain 1 MNQ | Gain 4 MNQ | Challenge à 4 MNQ | Challenge à 1 MNQ |
|---|---|---|---|---|---|
| Supertrend NQ 10-3 (5 min) | 54 | +5 418 $ | +17 782 $ | **validé le 16 oct.** | perdu le 30 oct. |
| W1 (Supertrend trié par un modèle) ¹ | 28 | +6 168 $ | +15 734 $ | **validé le 16 oct.** | **validé le 4 nov.** |
| XGBoost NQ ¹ | 23 | +3 212 $ | +8 006 $ | **validé le 16 oct.** | **validé le 9 nov.** |
| Bot 3 en 1, réglages actuels (zone + C2 + Q1), sans filtre delta ² | 17 | +1 724 $ | +7 930 $ | **validé le 16 oct.** | en cours (51 724 $) |
| Bot 3 en 1, zone d'origine sans filtre | 30 | +1 020 $ | +6 118 $ | **validé le 16 oct.** | perdu le 30 oct. |
| Bot 3 en 1, règle du 26 oct. | 15 | +294 $ | +1 382 $ | **validé le 16 oct.** | en cours |
| Bot 3 en 1, règle du 27 oct. (stop 70) | 15 | +293 $ | +690 $ | **validé le 16 oct.** | en cours |
| **Bot 3 en 1 avec le filtre delta (ton vrai réglage)**, 13 → 30 oct. seulement ³ | 6 | +544 $ | +2 092 $ | **pas validé** (52 092 $ au 30 oct.) | pas validé |
| RSI(2) du bot (tenu la nuit) | 2 | −1 019 $ | — | interdit : position de nuit | |

¹ Modèles entraînés jusqu'au 2 novembre : avant cette date, le modèle a vu les séances qu'il « trade ». Leur
validation du 16 octobre n'est pas un vrai résultat. Après le 2 novembre : W1 +3 262 $, XGBoost +232 $ (1 MNQ, rejeu
du 12 novembre).
² C2 et Q1 ont été choisis le 1er novembre, après les pertes d'octobre.
³ Les transactions Rithmic qui donnent le delta s'arrêtent au 30 octobre. **Le 16 octobre, le filtre delta a écarté
le trade de la zone** (+3 594 $ à 4 MNQ sans le filtre) : c'est ce trade qui fait valider toutes les versions sans
filtre.

## Stratégies de la machine de veille (résultat de fin de journée seulement, pas de chemin dans la séance)

| Stratégie | Séances jouées | Gain 1 MNQ | Gain 4 MNQ | Challenge à 4 MNQ | Challenge à 1 MNQ |
|---|---|---|---|---|---|
| ORB 5 minutes | 23 | +3 269 $ | +13 872 $ | validé le 16 oct. | validé le 13 nov. (hors délai de 30 jours) |
| Cassure de la veille | 20 | +3 114 $ | +12 456 $ | perdu le 4 nov. | validé le 9 nov. |
| Pivots R1/S1 | 8 | +1 015 $ | +4 058 $ | validé le 16 oct. | en cours |
| W1i (lundi après un week-end bitcoin négatif) | 1 | +420 $ | +1 678 $ | en cours | en cours |
| S2b cassure ratée | 12 | +55 $ | +220 $ | en cours | en cours |
| Radars 13 h et 13 h 30, L2 15 h 30 | 1 à 3 | −19 à −64 $ | −74 à +46 $ | en cours | en cours |

## Robots virtuels de `main` (leur propre compte, résultat de chaque soir)

| Robot | Gain depuis le 13 oct. | Challenge Bulenox |
|---|---|---|
| Robot zone, la zone seule (1 MNQ) | +1 024 $ | en cours |
| Robot zone, le rebond (1 MNQ) | +735 $ | en cours |
| Robot zone, son compte de challenge (zone + RSI(2) + rebond) | +518 $ | perdu le 5 nov. (comme dans son journal) |
| Robot zone, le RSI(2) (1 MNQ, tenu la nuit) | −1 032 $ | perdu le 5 nov. ; interdit (nuit) |
| Tendance seule (19 marchés) | −660 $ | perdu le 9 nov. ; interdit (garde la nuit) |
| Mélange tendance + achat | −1 350 $ | en cours ; interdit (garde la nuit) |
| Version 7 (5 actions de la technologie) | −5 007 $ | perdu le 29 oct. ; ce sont des actions, pas des futures |

Non rejouables : FluxNQ et le filtre delta après le 30 octobre (pas de transactions Rithmic dans le dépôt), le filtre
VIX après le 30 octobre. Le bot Telegram `main.py` (signaux BTC, ETH, or) n'a pas de compte : rien à compter.

## Ce qu'il faut retenir

- **À 4 MNQ, presque tous les bots NQ auraient validé dès le 16 octobre**, sur une seule grosse journée de tendance.
  Ton bot réel ne l'a pas prise, parce que son filtre delta a écarté ce trade.
- **Le plus crédible est Supertrend 10-3** : une règle fixe, sans modèle entraîné sur la période. Il valide à 4 MNQ
  (+17 782 $ sur la période) mais perd le challenge à 1 MNQ.
- **Ces 24 séances ne suffisent pas à classer les bots.** Sur 15 ans, les bots de tendance (Supertrend, W1, cassures)
  perdent environ un compte financé neuf sur deux dans l'année à 1 MNQ (`ml/arene/VAGUE6.md`) ; la zone non.
- **Les réglages choisis après coup** (C2, Q1, règles des 26 et 27 octobre, modèles entraînés jusqu'au 2 novembre)
  profitent du recul : un vrai challenge les aurait joués avant de les connaître.

Pour refaire : `challenge_bots.py` (il lit les rejeux bruts de `rejeu/`). Les rejeux viennent de `rejeu_periode.sh` de
`claude/loving-mccarthy-u21aw6` avec `FIN=2026-11-13`, plus un petit programme C# qui écrit `bot.Trades` de W1.Core et
XGBoost.Core.
