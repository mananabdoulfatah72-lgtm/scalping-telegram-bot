# Tableau de bord des robots (argent virtuel)

Chaque robot suit un compte **virtuel** de 50 000 $ : aucun ordre reel, aucun argent engage. Cette page est mise a jour chaque soir de semaine apres la cloture americaine (GitHub Actions).

| Robot | Ce qu'il fait | Demarre le | Solde virtuel | Dernier jour | Depuis le depart | Detail |
|---|---|---|---|---|---|---|
| Melange tendance + achat | futures, 19 marches, garde la nuit | 2026-09-25 | 48,068 $ | -39 $ (2026-11-20) | -1,932 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Tendance seule | futures, 19 marches, garde la nuit | 2026-09-25 | 50,432 $ | -144 $ (2026-11-20) | +432 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Version 7 | 5 actions technologie par mois, 50 % investi | 2026-09-29 | 40,623 $ | -1,953 $ (2026-11-20) | -9,377 $ | [detail](version7/robot/TABLEAU_DE_BORD.md) |
| Zone de bruit + challenge Phidias 50K | Nasdaq MNQ, intraday | 2026-09-28 | 53,582 $ (challenge n°2) | +1,706 $ (2026-11-20) | +1,533 $ | [detail](zone/robot/TABLEAU_DE_BORD.md) |

## Resultat de chaque jour ($)

| Date | Melange tendance + achat | Tendance seule | Version 7 | Zone de bruit + challenge Phidias 50K |
|---|---|---|---|---|
| 2026-11-20 | -39 | -144 | -1,953 | +1,706 |
| 2026-11-19 | -66 | +204 | -825 | +278 |
| 2026-11-18 | +3 | +634 | +159 | +0 |
| 2026-11-17 | -8 | -94 | -338 | -454 |
| 2026-11-16 | -135 | +377 | -1,227 | -266 |
| 2026-11-13 | +18 | +363 | -771 | +34 |
| 2026-11-12 | +103 | +475 | -70 | +0 |
| 2026-11-11 | -30 | +413 | +1,445 | -191 |
| 2026-11-10 | +91 | +673 | -75 | +0 |
| 2026-11-09 | +39 | -468 | +1,638 | +2,436 |
| 2026-11-06 | -67 | +296 | +1,010 | +40 |
| 2026-11-05 | -526 | -141 | -3,041 | -1,376 |
| 2026-11-04 | -21 | -516 | -604 | -357 |
| 2026-11-03 | -17 | +330 | +549 | +107 |
| 2026-11-02 | +51 | +224 | -972 | -636 |

Pour juger un robot, il faut plusieurs mois : des jours et des semaines negatifs sont normaux. Le detail de chaque robot compare son resultat a ce que donnait son historique.

Recherche et backtests : branche `claude/keen-babbage-r686cl`.
