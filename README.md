# Tableau de bord des robots (argent virtuel)

Chaque robot suit un compte **virtuel** de 50 000 $ : aucun ordre reel, aucun argent engage. Cette page est mise a jour chaque soir de semaine apres la cloture americaine (GitHub Actions).

| Robot | Ce qu'il fait | Demarre le | Solde virtuel | Dernier jour | Depuis le depart | Detail |
|---|---|---|---|---|---|---|
| Melange tendance + achat | futures, 19 marches, garde la nuit | 2026-09-25 | 48,894 $ | -143 $ (2026-10-26) | -1,106 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Tendance seule | futures, 19 marches, garde la nuit | 2026-09-25 | 48,412 $ | +90 $ (2026-10-26) | -1,588 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Version 7 | 5 actions technologie par mois, 50 % investi | 2026-09-29 | 48,231 $ | +499 $ (2026-10-26) | -1,769 $ | [detail](version7/robot/TABLEAU_DE_BORD.md) |
| Zone de bruit + challenge Phidias 50K | Nasdaq MNQ, intraday | 2026-09-28 | 50,404 $ (challenge n°1) | -48 $ (2026-10-23) | +404 $ | [detail](zone/robot/TABLEAU_DE_BORD.md) |

## Resultat de chaque jour ($)

| Date | Melange tendance + achat | Tendance seule | Version 7 | Zone de bruit + challenge Phidias 50K |
|---|---|---|---|---|
| 2026-10-26 | -143 | +90 | +499 |  |
| 2026-10-23 | +88 | +288 | +319 | -48 |
| 2026-10-22 | -283 | -905 | -1,067 | +364 |
| 2026-10-21 | +64 | +40 | +349 | +378 |
| 2026-10-20 | -22 | -113 | -36 | -500 |
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

Pour juger un robot, il faut plusieurs mois : des jours et des semaines negatifs sont normaux. Le detail de chaque robot compare son resultat a ce que donnait son historique.

Recherche et backtests : branche `claude/keen-babbage-r686cl`.
