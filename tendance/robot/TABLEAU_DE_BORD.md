# Robot multi-marches : tableau de bord (argent virtuel)

Mis a jour le **2026-09-29**. Deux comptes virtuels de 50 000 $, risque vise 12 %/an (environ 6 000 $). Aucun argent reel n'est engage.

| Compte | Solde | Gain | Etat |
|---|---|---|---|
| Melange 50/50 (tendance + achat permanent) | 49,765 $ | -235 $ | ⚪ Trop tot pour juger |
| Tendance seule | 50,320 $ | +320 $ | ⚪ Trop tot pour juger |

La zone bleue de chaque graphique montre ou tombaient 8 resultats sur 10 dans l'historique 2007-2026, au meme risque. Tant que la ligne reste dedans, le compte se comporte comme prevu. Des semaines negatives sont normales : il faut plusieurs mois pour juger.

## Melange 50/50 (tendance + achat permanent)

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,78, environ +9 %/an en moyenne, pire baisse -19 %, 3 annees sur 4 positives.

**⚪ Trop tot pour juger : le compte vient de demarrer.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **49,765 $** (depart 50 000 $) |
| Gain depuis le depart | -235 $ (-0.5%) |
| Baisse depuis le plus haut | -0.5% |
| Zone normale a ce stade (8 cas sur 10) | de -755 $ a +858 $ (moyenne +51 $) |
| Challenge Phidias 50K virtuel | en cours : -235 $ sur +4 000 $, marge restante 2,265 $ |

![Gain du compte et zone normale](courbe_melange.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Achat | 10 |
| MCD | Dollar canadien | Achat | 4 |
| 30Y | Taux 30 ans | Achat | 2 |
| MES | S&P 500 | Achat | 1 |
| 10Y | Taux 10 ans | Achat | 1 |
| M6A | Dollar australien | Vente | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-09-29 | +15 $ | 49,765 $ |
| 2026-09-28 | -188 $ | 49,750 $ |
| 2026-09-25 | +0 $ | 49,938 $ |

Journal complet : [journal_melange.csv](journal_melange.csv)

</details>

## Tendance seule

Demarre le 2026-09-25. Historique 2007-2026 au meme risque : Sharpe 0,56, environ +7 %/an en moyenne, pire baisse -23 %, 13 annees sur 20 positives.

**⚪ Trop tot pour juger : le compte vient de demarrer.**

| Mesure | Valeur |
|---|---|
| Solde virtuel | **50,320 $** (depart 50 000 $) |
| Gain depuis le depart | +320 $ (+0.6%) |
| Baisse depuis le plus haut | 0.0% |
| Zone normale a ce stade (8 cas sur 10) | de -769 $ a +843 $ (moyenne +37 $) |
| Challenge Phidias 50K virtuel | en cours : +320 $ sur +4 000 $, marge restante 2,500 $ |

![Gain du compte et zone normale](courbe.svg)

| Contrat | Marche | Sens | Nombre |
|---|---|---|---|
| MET | Ether | Achat | 5 |
| 10Y | Taux 10 ans | Achat | 4 |
| M2K | Russell 2000 | Achat | 1 |
| 2YY | Taux 2 ans | Achat | 1 |
| M6B | Livre sterling | Vente | 1 |
| MSF | Franc suisse | Vente | 1 |

<details><summary>10 derniers jours</summary>

| Date | Resultat du jour | Solde |
|---|---|---|
| 2026-09-29 | +28 $ | 50,320 $ |
| 2026-09-28 | +335 $ | 50,292 $ |
| 2026-09-25 | +0 $ | 49,958 $ |

Journal complet : [journal.csv](journal.csv)

</details>

Contrats de taux (2YY, 10Y, 30Y) : le sens indique est celui de l'ordre sur le contrat, inverse de celui des obligations. Methode et resultats historiques : [../README.md](../README.md).
