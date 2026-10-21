# Tableau de bord des robots (argent virtuel)

Chaque robot suit un compte **virtuel** de 50 000 $ : aucun ordre reel, aucun argent engage. Cette page est mise a jour chaque soir de semaine apres la cloture americaine (GitHub Actions).

| Robot | Ce qu'il fait | Demarre le | Solde virtuel | Dernier jour | Depuis le depart | Detail |
|---|---|---|---|---|---|---|
| Melange tendance + achat | futures, 19 marches, garde la nuit | 2026-09-25 | 49,184 $ | -22 $ (2026-10-20) | -816 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Tendance seule | futures, 19 marches, garde la nuit | 2026-09-25 | 48,922 $ | -113 $ (2026-10-20) | -1,078 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Version 7 | 5 actions technologie par mois, 50 % investi | 2026-09-29 | 48,131 $ | -36 $ (2026-10-20) | -1,869 $ | [detail](version7/robot/TABLEAU_DE_BORD.md) |
| Zone de bruit + challenge Phidias 50K | Nasdaq MNQ, intraday | 2026-09-28 | 50,210 $ (challenge n°1) | +830 $ (2026-10-19) | +210 $ | [detail](zone/robot/TABLEAU_DE_BORD.md) |

## Resultat de chaque jour ($)

| Date | Melange tendance + achat | Tendance seule | Version 7 | Zone de bruit + challenge Phidias 50K |
|---|---|---|---|---|
| 2026-10-20 | -22 | -113 | -36 |  |
| 2026-10-19 | +204 | +360 | +409 | +830 |
| 2026-10-16 | -235 | -492 | -1,086 | -784 |
| 2026-10-15 | -137 | -648 | +10 | +1 |
| 2026-10-14 | -369 | -204 | -698 | +410 |
| 2026-10-13 | -93 | -292 | -281 | +0 |
| 2026-10-12 | +5 | +267 | -604 | -166 |
| 2026-10-09 | +81 | +112 | +43 | +0 |
| 2026-10-08 | -154 | -336 | -633 | -54 |
| 2026-10-07 | -210 | -7 | +74 | +0 |
| 2026-10-06 | -144 | -336 | +186 | +0 |
| 2026-10-05 | +351 | +296 | -2 | +248 |
| 2026-10-02 | +285 | +259 | +209 | +0 |
| 2026-10-01 | -14 | -237 | +553 | +0 |
| 2026-09-30 | -37 | +27 | -12 | -30 |

Pour juger un robot, il faut plusieurs mois : des jours et des semaines negatifs sont normaux. Le detail de chaque robot compare son resultat a ce que donnait son historique.

Recherche et backtests : branche `claude/keen-babbage-r686cl`.
