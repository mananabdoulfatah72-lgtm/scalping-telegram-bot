# Tableau de bord des robots (argent virtuel)

Chaque robot suit un compte **virtuel** de 50 000 $ : aucun ordre reel, aucun argent engage. Cette page est mise a jour chaque soir de semaine apres la cloture americaine (GitHub Actions).

| Robot | Ce qu'il fait | Demarre le | Solde virtuel | Dernier jour | Depuis le depart | Detail |
|---|---|---|---|---|---|---|
| Melange tendance + achat | futures, 19 marches, garde la nuit | 2026-09-25 | 48,411 $ | +103 $ (2026-11-12) | -1,589 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Tendance seule | futures, 19 marches, garde la nuit | 2026-09-25 | 49,186 $ | +475 $ (2026-11-12) | -814 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Version 7 | 5 actions technologie par mois, 50 % investi | 2026-09-29 | 45,648 $ | +1,445 $ (2026-11-11) | -4,352 $ | [detail](version7/robot/TABLEAU_DE_BORD.md) |
| Zone de bruit + challenge Phidias 50K | Nasdaq MNQ, intraday | 2026-09-28 | 52,285 $ (challenge n°2) | -191 $ (2026-11-11) | +236 $ | [detail](zone/robot/TABLEAU_DE_BORD.md) |

## Resultat de chaque jour ($)

| Date | Melange tendance + achat | Tendance seule | Version 7 | Zone de bruit + challenge Phidias 50K |
|---|---|---|---|---|
| 2026-11-12 | +103 | +475 |  |  |
| 2026-11-11 | -30 | +413 | +1,445 | -191 |
| 2026-11-10 | +91 | +673 | -75 | +0 |
| 2026-11-09 | +39 | -468 | +1,638 | +2,436 |
| 2026-11-06 | -67 | +296 | +1,010 | +40 |
| 2026-11-05 | -526 | -141 | -3,041 | -1,376 |
| 2026-11-04 | -21 | -516 | -604 | -357 |
| 2026-11-03 | -17 | +330 | +549 | +107 |
| 2026-11-02 | +51 | +224 | -972 | -636 |
| 2026-10-30 | -83 | -355 | -1,334 | -31 |
| 2026-10-29 | -136 | -234 | -1,908 | +0 |
| 2026-10-28 | +118 | +58 | +377 | +0 |
| 2026-10-27 | +34 | +96 | +332 | +74 |
| 2026-10-26 | -143 | +90 | +499 | -233 |
| 2026-10-23 | +88 | +288 | +319 | -48 |

Pour juger un robot, il faut plusieurs mois : des jours et des semaines negatifs sont normaux. Le detail de chaque robot compare son resultat a ce que donnait son historique.

Recherche et backtests : branche `claude/keen-babbage-r686cl`.
