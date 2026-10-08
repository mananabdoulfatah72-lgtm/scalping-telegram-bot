# Robot multi-marches : tableau de bord (argent virtuel)

Mis a jour le **2026-10-07**. Deux comptes virtuels de 50 000 $, risque vise 12 %/an (environ 6 000 $). Aucun argent reel n'est engage.

| Compte | Solde | Gain | Etat |
|---|---|---|---|
| Melange 50/50 (tendance + achat permanent) | 49,923 $ | -77 $ | 🟡 Dans la zone normale |
| Tendance seule | 50,300 $ | +300 $ | 🟡 Dans la zone normale |

La zone bleue de chaque graphique montre ou tombaient 8 resultats sur 10 dans l'historique 2007-2026, au meme risque. Tant que la ligne reste dedans, le compte se comporte comme prevu. Des semaines negatives sont normales : il faut plusieurs mois pour juger.

## Melange 50/50 (tendance + achat permanent)

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,78, environ +9 %/an en moyenne, pire baisse -19 %, 3 annees sur 4 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **49,923 $** (depart 50 000 $) |
| Gain depuis le depart | -77 $ (-0.2%) |
| Baisse depuis le plus haut | -0.7% |
| Zone normale a ce stade (8 cas sur 10) | de -1,242 $ a +1,550 $ (moyenne +154 $) |
| Challenge Phidias 50K virtuel | en cours : -77 $ sur +4 000 $, marge restante 2,147 $ |

![Gain du compte et zone normale](courbe_melange.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Vente | 3 |
| 10Y | Taux 10 ans | Achat | 2 |
| M2K | Russell 2000 | Achat | 1 |
| 30Y | Taux 30 ans | Achat | 1 |
| M6A | Dollar australien | Achat | 1 |
| MCD | Dollar canadien | Achat | 1 |
| MBT | Bitcoin | Achat | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-10-07 | -210 $ | 49,923 $ |
| 2026-10-06 | -144 $ | 50,132 $ |
| 2026-10-05 | +351 $ | 50,276 $ |
| 2026-10-02 | +285 $ | 49,925 $ |
| 2026-10-01 | -14 $ | 49,715 $ |
| 2026-09-30 | -37 $ | 49,728 $ |
| 2026-09-29 | +15 $ | 49,765 $ |
| 2026-09-28 | -188 $ | 49,750 $ |
| 2026-09-25 | +0 $ | 49,938 $ |

Journal complet : [journal_melange.csv](journal_melange.csv)

</details>

## Tendance seule

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,56, environ +7 %/an en moyenne, pire baisse -23 %, 13 annees sur 20 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **50,300 $** (depart 50 000 $) |
| Gain depuis le depart | +300 $ (+0.6%) |
| Baisse depuis le plus haut | -0.7% |
| Zone normale a ce stade (8 cas sur 10) | de -1,285 $ a +1,507 $ (moyenne +111 $) |
| Challenge Phidias 50K virtuel | en cours : +300 $ sur +4 000 $, marge restante 2,157 $ |

![Gain du compte et zone normale](courbe.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Achat | 7 |
| 10Y | Taux 10 ans | Achat | 5 |
| M2K | Russell 2000 | Achat | 1 |
| 2YY | Taux 2 ans | Achat | 1 |
| M6E | Euro | Vente | 1 |
| M6A | Dollar australien | Vente | 1 |
| MCD | Dollar canadien | Vente | 1 |
| MSF | Franc suisse | Vente | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-10-07 | -7 $ | 50,300 $ |
| 2026-10-06 | -336 $ | 50,307 $ |
| 2026-10-05 | +296 $ | 50,643 $ |
| 2026-10-02 | +259 $ | 50,347 $ |
| 2026-10-01 | -237 $ | 50,111 $ |
| 2026-09-30 | +27 $ | 50,347 $ |
| 2026-09-29 | +28 $ | 50,320 $ |
| 2026-09-28 | +335 $ | 50,292 $ |
| 2026-09-25 | +0 $ | 49,958 $ |

Journal complet : [journal.csv](journal.csv)

</details>

Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, inverse de celui des obligations. Methode et resultats historiques : [../README.md](../README.md).
