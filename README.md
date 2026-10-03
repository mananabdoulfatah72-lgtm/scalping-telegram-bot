# Tableau de bord des robots (argent virtuel)

Chaque robot suit un compte **virtuel** de 50 000 $ : aucun ordre reel, aucun argent engage. Cette page est mise a jour chaque soir de semaine apres la cloture americaine (GitHub Actions).

| Robot | Ce qu'il fait | Demarre le | Solde virtuel | Dernier jour | Depuis le depart | Detail |
|---|---|---|---|---|---|---|
| Melange tendance + achat | futures, 19 marches, garde la nuit | 2026-09-25 | 49,715 $ | -14 $ (2026-10-01) | -285 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Tendance seule | futures, 19 marches, garde la nuit | 2026-09-25 | 50,111 $ | -237 $ (2026-10-01) | +111 $ | [detail](tendance/robot/TABLEAU_DE_BORD.md) |
| Version 7 | 5 actions technologie par mois, 50 % investi | 2026-09-29 | 50,540 $ | +553 $ (2026-10-01) | +540 $ | [detail](version7/robot/TABLEAU_DE_BORD.md) |
| Zone de bruit + challenge Phidias 50K | Nasdaq MNQ, intraday | 2026-09-28 | 49,724 $ (challenge n°1) | +0 $ (2026-10-01) | -276 $ | [detail](zone/robot/TABLEAU_DE_BORD.md) |

## Resultat de chaque jour ($)

| Date | Melange tendance + achat | Tendance seule | Version 7 | Zone de bruit + challenge Phidias 50K |
|---|---|---|---|---|
| 2026-10-01 | -14 | -237 | +553 | +0 |
| 2026-09-30 | -37 | +27 | -12 | -30 |
| 2026-09-29 | +15 | +28 | +0 | +0 |
| 2026-09-28 | -188 | +335 |  | -246 |
| 2026-09-25 | +0 | +0 |  |  |

Pour juger un robot, il faut plusieurs mois : des jours et des semaines negatifs sont normaux. Le detail de chaque robot compare son resultat a ce que donnait son historique.

Recherche et backtests : branche `claude/keen-babbage-r686cl`.
