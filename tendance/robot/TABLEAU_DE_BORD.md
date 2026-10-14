# Robot multi-marches : tableau de bord (argent virtuel)

Mis a jour le **2026-10-13**. Deux comptes virtuels de 50 000 $, risque vise 12 %/an (environ 6 000 $). Aucun argent reel n'est engage.

| Compte | Solde | Gain | Etat |
|---|---|---|---|
| Melange 50/50 (tendance + achat permanent) | 49,759 $ | -241 $ | 🟡 Dans la zone normale |
| Tendance seule | 50,044 $ | +44 $ | 🟡 Dans la zone normale |

La zone bleue de chaque graphique montre ou tombaient 8 resultats sur 10 dans l'historique 2007-2026, au meme risque. Tant que la ligne reste dedans, le compte se comporte comme prevu. Des semaines negatives sont normales : il faut plusieurs mois pour juger.

## Melange 50/50 (tendance + achat permanent)

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,78, environ +9 %/an en moyenne, pire baisse -19 %, 3 annees sur 4 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **49,759 $** (depart 50 000 $) |
| Gain depuis le depart | -241 $ (-0.5%) |
| Baisse depuis le plus haut | -1.0% |
| Zone normale a ce stade (8 cas sur 10) | de -1,479 $ a +1,941 $ (moyenne +231 $) |
| Challenge Phidias 50K virtuel | en cours : -241 $ sur +4 000 $, marge restante 1,983 $ |

![Gain du compte et zone normale](courbe_melange.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Vente | 3 |
| 10Y | Taux 10 ans | Achat | 2 |
| M2K | Russell 2000 | Achat | 1 |
| 30Y | Taux 30 ans | Achat | 1 |
| M6A | Dollar australien | Achat | 1 |
| MBT | Bitcoin | Achat | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-10-13 | -93 $ | 49,759 $ |
| 2026-10-12 | +5 $ | 49,852 $ |
| 2026-10-09 | +81 $ | 49,846 $ |
| 2026-10-08 | -154 $ | 49,768 $ |
| 2026-10-07 | -210 $ | 49,923 $ |
| 2026-10-06 | -144 $ | 50,132 $ |
| 2026-10-05 | +351 $ | 50,276 $ |
| 2026-10-02 | +285 $ | 49,925 $ |
| 2026-10-01 | -14 $ | 49,715 $ |
| 2026-09-30 | -37 $ | 49,728 $ |

Journal complet : [journal_melange.csv](journal_melange.csv)

</details>

## Tendance seule

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,56, environ +7 %/an en moyenne, pire baisse -23 %, 13 annees sur 20 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **50,044 $** (depart 50 000 $) |
| Gain depuis le depart | +44 $ (+0.1%) |
| Baisse depuis le plus haut | -1.2% |
| Zone normale a ce stade (8 cas sur 10) | de -1,544 $ a +1,876 $ (moyenne +166 $) |
| Challenge Phidias 50K virtuel | en cours : +44 $ sur +4 000 $, marge restante 1,901 $ |

![Gain du compte et zone normale](courbe.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Achat | 7 |
| 10Y | Taux 10 ans | Achat | 5 |
| MSF | Franc suisse | Vente | 2 |
| M2K | Russell 2000 | Achat | 1 |
| 2YY | Taux 2 ans | Achat | 1 |
| M6E | Euro | Vente | 1 |
| M6A | Dollar australien | Vente | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-10-13 | -292 $ | 50,044 $ |
| 2026-10-12 | +267 $ | 50,336 $ |
| 2026-10-09 | +112 $ | 50,069 $ |
| 2026-10-08 | -336 $ | 49,963 $ |
| 2026-10-07 | -7 $ | 50,300 $ |
| 2026-10-06 | -336 $ | 50,307 $ |
| 2026-10-05 | +296 $ | 50,643 $ |
| 2026-10-02 | +259 $ | 50,347 $ |
| 2026-10-01 | -237 $ | 50,111 $ |
| 2026-09-30 | +27 $ | 50,347 $ |

Journal complet : [journal.csv](journal.csv)

</details>

Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, inverse de celui des obligations. Methode et resultats historiques : [../README.md](../README.md).
