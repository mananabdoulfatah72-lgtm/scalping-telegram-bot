# Robot multi-marches : tableau de bord (argent virtuel)

Mis a jour le **2026-10-30**. Deux comptes virtuels de 50 000 $, risque vise 12 %/an (environ 6 000 $). Aucun argent reel n'est engage.

| Compte | Solde | Gain | Etat |
|---|---|---|---|
| Melange 50/50 (tendance + achat permanent) | 48,811 $ | -1,189 $ | 🟡 Dans la zone normale |
| Tendance seule | 47,936 $ | -2,064 $ | 🔴 En dessous de la zone normale |

La zone bleue de chaque graphique montre ou tombaient 8 resultats sur 10 dans l'historique 2007-2026, au meme risque. Tant que la ligne reste dedans, le compte se comporte comme prevu. Des semaines negatives sont normales : il faut plusieurs mois pour juger.

## Melange 50/50 (tendance + achat permanent)

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,78, environ +9 %/an en moyenne, pire baisse -19 %, 3 annees sur 4 positives.

**🟡 Dans la zone normale : se comporte comme sur les 20 ans d'historique.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **48,811 $** (depart 50 000 $) |
| Gain depuis le depart | -1,189 $ (-2.4%) |
| Baisse depuis le plus haut | -2.9% |
| Zone normale a ce stade (8 cas sur 10) | de -1,934 $ a +2,834 $ (moyenne +450 $) |
| Challenge Phidias 50K virtuel | en cours : -1,189 $ sur +4 000 $, marge restante 1,035 $ |

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
| 2026-10-30 | -83 $ | 48,811 $ |
| 2026-10-29 | -136 $ | 48,910 $ |
| 2026-10-28 | +118 $ | 49,046 $ |
| 2026-10-27 | +34 $ | 48,928 $ |
| 2026-10-26 | -143 $ | 48,894 $ |
| 2026-10-23 | +88 $ | 49,037 $ |
| 2026-10-22 | -283 $ | 48,966 $ |
| 2026-10-21 | +64 $ | 49,249 $ |
| 2026-10-20 | -22 $ | 49,184 $ |
| 2026-10-19 | +204 $ | 49,206 $ |

Journal complet : [journal_melange.csv](journal_melange.csv)

</details>

## Tendance seule

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,56, environ +7 %/an en moyenne, pire baisse -23 %, 13 annees sur 20 positives.

**🔴 En dessous de la zone normale : pire que 9 cas sur 10 de l'historique. A surveiller.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **47,936 $** (depart 50 000 $) |
| Gain depuis le depart | -2,064 $ (-4.1%) |
| Baisse depuis le plus haut | -5.3% |
| Zone normale a ce stade (8 cas sur 10) | de -2,061 $ a +2,708 $ (moyenne +323 $) |
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
| 2026-10-30 | -355 $ | 47,936 $ |
| 2026-10-29 | -234 $ | 48,333 $ |
| 2026-10-28 | +58 $ | 48,566 $ |
| 2026-10-27 | +96 $ | 48,508 $ |
| 2026-10-26 | +90 $ | 48,412 $ |
| 2026-10-23 | +288 $ | 48,322 $ |
| 2026-10-22 | -905 $ | 48,057 $ |
| 2026-10-21 | +40 $ | 48,962 $ |
| 2026-10-20 | -113 $ | 48,922 $ |
| 2026-10-19 | +360 $ | 49,034 $ |

Journal complet : [journal.csv](journal.csv)

</details>

Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, inverse de celui des obligations. Methode et resultats historiques : [../README.md](../README.md).
