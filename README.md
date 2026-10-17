# Tableau de bord des robots (argent virtuel)

Chaque robot suit un compte **virtuel** de 50 000 $ : aucun ordre reel, aucun argent engage. Cette page est mise a jour chaque soir de semaine apres la cloture americaine (GitHub Actions).

| Robot | Ce qu'il fait | Demarre le | Solde virtuel | Dernier jour | Depuis le depart | Detail |
|---|---|---|---|---|---|---|
| Melange tendance + achat | futures, 19 marches, garde la nuit | 2026-09-25 | 49,002 $ | -235 $ (2026-10-16) | -998 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Tendance seule | futures, 19 marches, garde la nuit | 2026-09-25 | 48,675 $ | -492 $ (2026-10-16) | -1,325 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Version 7 | 5 actions technologie par mois, 50 % investi | 2026-09-29 | 48,844 $ | +10 $ (2026-10-15) | -1,156 $ | [detail](version7/robot/TABLEAU_DE_BORD.md) |
| Zone de bruit + challenge Phidias 50K | Nasdaq MNQ, intraday | 2026-09-28 | 50,163 $ (challenge n°1) | +1 $ (2026-10-15) | +163 $ | [detail](zone/robot/TABLEAU_DE_BORD.md) |

## Resultat de chaque jour ($)

| Date | Melange tendance + achat | Tendance seule | Version 7 | Zone de bruit + challenge Phidias 50K |
|---|---|---|---|---|
| 2026-10-16 | -235 | -492 |  |  |
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
| 2026-09-29 | +15 | +28 | +0 | +0 |
| 2026-09-28 | -188 | +335 |  | -246 |

Pour juger un robot, il faut plusieurs mois : des jours et des semaines negatifs sont normaux. Le detail de chaque robot compare son resultat a ce que donnait son historique.

Recherche et backtests : branche `claude/keen-babbage-r686cl`.
