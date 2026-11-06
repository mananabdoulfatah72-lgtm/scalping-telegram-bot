# Robot multi-marches : tableau de bord (argent virtuel)

Mis a jour le **2026-11-05**. Deux comptes virtuels de 50 000 $, risque vise 12 %/an (environ 6 000 $). Aucun argent reel n'est engage.

| Compte | Solde | Gain | Etat |
|---|---|---|---|
| Melange 50/50 (tendance + achat permanent) | 48,297 $ | -1,703 $ | 🟡 Dans la zone normale |
| Tendance seule | 47,833 $ | -2,167 $ | 🟡 Dans la zone normale |

La zone bleue de chaque graphique montre ou tombaient 8 resultats sur 10 dans l'historique 2007-2026, au meme risque. Tant que la ligne reste dedans, le compte se comporte comme prevu. Des semaines negatives sont normales : il faut plusieurs mois pour juger.

## Melange 50/50 (tendance + achat permanent)

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,78, environ +9 %/an en moyenne, pire baisse -19 %, 3 annees sur 4 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **48,297 $** (depart 50 000 $) |
| Gain depuis le depart | -1,703 $ (-3.4%) |
| Baisse depuis le plus haut | -3.9% |
| Zone normale a ce stade (8 cas sur 10) | de -2,054 $ a +3,108 $ (moyenne +527 $) |
| Challenge Phidias 50K virtuel | en cours : -1,703 $ sur +4 000 $, marge restante 521 $ |

![Gain du compte et zone normale](courbe_melange.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Vente | 4 |
| MCD | Dollar canadien | Achat | 2 |
| 10Y | Taux 10 ans | Achat | 1 |
| M6E | Euro | Vente | 1 |
| M6A | Dollar australien | Achat | 1 |
| MBT | Bitcoin | Achat | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-11-05 | -526 $ | 48,297 $ |
| 2026-11-04 | -21 $ | 48,823 $ |
| 2026-11-03 | -17 $ | 48,844 $ |
| 2026-11-02 | +51 $ | 48,861 $ |
| 2026-10-30 | -83 $ | 48,811 $ |
| 2026-10-29 | -136 $ | 48,910 $ |
| 2026-10-28 | +118 $ | 49,046 $ |
| 2026-10-27 | +34 $ | 48,928 $ |
| 2026-10-26 | -143 $ | 48,894 $ |
| 2026-10-23 | +88 $ | 49,037 $ |

Journal complet : [journal_melange.csv](journal_melange.csv)

</details>

## Tendance seule

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,56, environ +7 %/an en moyenne, pire baisse -23 %, 13 annees sur 20 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **47,833 $** (depart 50 000 $) |
| Gain depuis le depart | -2,167 $ (-4.3%) |
| Baisse depuis le plus haut | -5.5% |
| Zone normale a ce stade (8 cas sur 10) | de -2,202 $ a +2,959 $ (moyenne +378 $) |
| Challenge Phidias 50K virtuel | perdu le 2026-10-22 |

![Gain du compte et zone normale](courbe.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| 2YY | Taux 2 ans | Achat | 2 |
| M6A | Dollar australien | Vente | 2 |
| MCD | Dollar canadien | Achat | 2 |
| MSF | Franc suisse | Vente | 2 |
| MET | Ether | Achat | 2 |
| 10Y | Taux 10 ans | Achat | 1 |
| 30Y | Taux 30 ans | Achat | 1 |
| M6E | Euro | Vente | 1 |
| MNG | Gaz naturel | Vente | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-11-05 | -141 $ | 47,833 $ |
| 2026-11-04 | -516 $ | 47,973 $ |
| 2026-11-03 | +330 $ | 48,489 $ |
| 2026-11-02 | +224 $ | 48,160 $ |
| 2026-10-30 | -355 $ | 47,936 $ |
| 2026-10-29 | -234 $ | 48,333 $ |
| 2026-10-28 | +58 $ | 48,566 $ |
| 2026-10-27 | +96 $ | 48,508 $ |
| 2026-10-26 | +90 $ | 48,412 $ |
| 2026-10-23 | +288 $ | 48,322 $ |

Journal complet : [journal.csv](journal.csv)

</details>

Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, inverse de celui des obligations. Methode et resultats historiques : [../README.md](../README.md).
