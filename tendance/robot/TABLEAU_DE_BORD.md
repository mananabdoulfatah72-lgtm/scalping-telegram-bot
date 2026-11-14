# Robot multi-marches : tableau de bord (argent virtuel)

Mis a jour le **2026-11-13**. Deux comptes virtuels de 50 000 $, risque vise 12 %/an (environ 6 000 $). Aucun argent reel n'est engage.

| Compte | Solde | Gain | Etat |
|---|---|---|---|
| Melange 50/50 (tendance + achat permanent) | 48,358 $ | -1,642 $ | 🟡 Dans la zone normale |
| Tendance seule | 49,497 $ | -503 $ | 🟡 Dans la zone normale |

La zone bleue de chaque graphique montre ou tombaient 8 resultats sur 10 dans l'historique 2007-2026, au meme risque. Tant que la ligne reste dedans, le compte se comporte comme prevu. Des semaines negatives sont normales : il faut plusieurs mois pour juger.

## Melange 50/50 (tendance + achat permanent)

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,78, environ +9 %/an en moyenne, pire baisse -19 %, 3 annees sur 4 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **48,358 $** (depart 50 000 $) |
| Gain depuis le depart | -1,642 $ (-3.3%) |
| Baisse depuis le plus haut | -3.8% |
| Zone normale a ce stade (8 cas sur 10) | de -2,191 $ a +3,451 $ (moyenne +630 $) |
| Challenge Phidias 50K virtuel | en cours : -1,642 $ sur +4 000 $, marge restante 582 $ |

![Gain du compte et zone normale](courbe_melange.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Achat | 10 |
| M6E | Euro | Vente | 1 |
| M6A | Dollar australien | Achat | 1 |
| MCD | Dollar canadien | Achat | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-11-13 | +18 $ | 48,358 $ |
| 2026-11-12 | +103 $ | 48,411 $ |
| 2026-11-11 | -30 $ | 48,308 $ |
| 2026-11-10 | +91 $ | 48,338 $ |
| 2026-11-09 | +39 $ | 48,247 $ |
| 2026-11-06 | -67 $ | 48,208 $ |
| 2026-11-05 | -526 $ | 48,297 $ |
| 2026-11-04 | -21 $ | 48,823 $ |
| 2026-11-03 | -17 $ | 48,844 $ |
| 2026-11-02 | +51 $ | 48,861 $ |

Journal complet : [journal_melange.csv](journal_melange.csv)

</details>

## Tendance seule

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,56, environ +7 %/an en moyenne, pire baisse -23 %, 13 annees sur 20 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **49,497 $** (depart 50 000 $) |
| Gain depuis le depart | -503 $ (-1.0%) |
| Baisse depuis le plus haut | -2.3% |
| Zone normale a ce stade (8 cas sur 10) | de -2,369 $ a +3,274 $ (moyenne +452 $) |
| Challenge Phidias 50K virtuel | perdu le 2026-10-22 |

![Gain du compte et zone normale](courbe.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Vente | 8 |
| MSF | Franc suisse | Vente | 2 |
| 10Y | Taux 10 ans | Achat | 1 |
| 30Y | Taux 30 ans | Achat | 1 |
| M6A | Dollar australien | Achat | 1 |
| MHG | Cuivre | Vente | 1 |
| MNG | Gaz naturel | Vente | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-11-13 | +363 $ | 49,497 $ |
| 2026-11-12 | +475 $ | 49,186 $ |
| 2026-11-11 | +413 $ | 48,711 $ |
| 2026-11-10 | +673 $ | 48,298 $ |
| 2026-11-09 | -468 $ | 47,625 $ |
| 2026-11-06 | +296 $ | 48,093 $ |
| 2026-11-05 | -141 $ | 47,833 $ |
| 2026-11-04 | -516 $ | 47,973 $ |
| 2026-11-03 | +330 $ | 48,489 $ |
| 2026-11-02 | +224 $ | 48,160 $ |

Journal complet : [journal.csv](journal.csv)

</details>

Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, inverse de celui des obligations. Methode et resultats historiques : [../README.md](../README.md).
