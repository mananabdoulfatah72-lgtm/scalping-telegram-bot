# Robot multi-marches : tableau de bord (argent virtuel)

Mis a jour le **2026-10-26**. Deux comptes virtuels de 50 000 $, risque vise 12 %/an (environ 6 000 $). Aucun argent reel n'est engage.

| Compte | Solde | Gain | Etat |
|---|---|---|---|
| Melange 50/50 (tendance + achat permanent) | 48,894 $ | -1,106 $ | 🟡 Dans la zone normale |
| Tendance seule | 48,412 $ | -1,588 $ | 🟡 Dans la zone normale |

La zone bleue de chaque graphique montre ou tombaient 8 resultats sur 10 dans l'historique 2007-2026, au meme risque. Tant que la ligne reste dedans, le compte se comporte comme prevu. Des semaines negatives sont normales : il faut plusieurs mois pour juger.

## Melange 50/50 (tendance + achat permanent)

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,78, environ +9 %/an en moyenne, pire baisse -19 %, 3 annees sur 4 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **48,894 $** (depart 50 000 $) |
| Gain depuis le depart | -1,106 $ (-2.2%) |
| Baisse depuis le plus haut | -2.7% |
| Zone normale a ce stade (8 cas sur 10) | de -1,845 $ a +2,643 $ (moyenne +399 $) |
| Challenge Phidias 50K virtuel | en cours : -1,106 $ sur +4 000 $, marge restante 1,118 $ |

![Gain du compte et zone normale](courbe_melange.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Vente | 3 |
| M6A | Dollar australien | Achat | 2 |
| 10Y | Taux 10 ans | Achat | 1 |
| M6B | Livre sterling | Vente | 1 |
| MCD | Dollar canadien | Achat | 1 |
| MBT | Bitcoin | Achat | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-10-26 | -143 $ | 48,894 $ |
| 2026-10-23 | +88 $ | 49,037 $ |
| 2026-10-22 | -283 $ | 48,966 $ |
| 2026-10-21 | +64 $ | 49,249 $ |
| 2026-10-20 | -22 $ | 49,184 $ |
| 2026-10-19 | +204 $ | 49,206 $ |
| 2026-10-16 | -235 $ | 49,002 $ |
| 2026-10-15 | -137 $ | 49,254 $ |
| 2026-10-14 | -369 $ | 49,390 $ |
| 2026-10-13 | -93 $ | 49,759 $ |

Journal complet : [journal_melange.csv](journal_melange.csv)

</details>

## Tendance seule

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,56, environ +7 %/an en moyenne, pire baisse -23 %, 13 annees sur 20 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **48,412 $** (depart 50 000 $) |
| Gain depuis le depart | -1,588 $ (-3.2%) |
| Baisse depuis le plus haut | -4.4% |
| Zone normale a ce stade (8 cas sur 10) | de -1,958 $ a +2,530 $ (moyenne +286 $) |
| Challenge Phidias 50K virtuel | perdu le 2026-10-22 |

![Gain du compte et zone normale](courbe.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Achat | 6 |
| 10Y | Taux 10 ans | Achat | 3 |
| MSF | Franc suisse | Vente | 2 |
| 2YY | Taux 2 ans | Achat | 1 |
| M6E | Euro | Vente | 1 |
| M6A | Dollar australien | Vente | 1 |
| M6B | Livre sterling | Achat | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-10-26 | +90 $ | 48,412 $ |
| 2026-10-23 | +288 $ | 48,322 $ |
| 2026-10-22 | -905 $ | 48,057 $ |
| 2026-10-21 | +40 $ | 48,962 $ |
| 2026-10-20 | -113 $ | 48,922 $ |
| 2026-10-19 | +360 $ | 49,034 $ |
| 2026-10-16 | -492 $ | 48,675 $ |
| 2026-10-15 | -648 $ | 49,193 $ |
| 2026-10-14 | -204 $ | 49,841 $ |
| 2026-10-13 | -292 $ | 50,044 $ |

Journal complet : [journal.csv](journal.csv)

</details>

Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, inverse de celui des obligations. Methode et resultats historiques : [../README.md](../README.md).
