# Machine v6 : résultats (2 novembre 2026)

Règles : `REGLES.md` (fixées avant calcul, version 2 écrite après la vague 1, coffre fermé jusqu'à la fin).
Fichiers : `resultats/vagues_tournoi.txt` (vague 1), `resultats/vagues_tournoi_v2.txt` (vagues 1 à 4, tournoi,
contrôles), `resultats/coffre.txt` (coffre ouvert une fois), `resultats/plateau.txt` (descriptif après le coffre).

## Vérification du simulateur

Avec la règle de fin de journée et le départ de l'audit (50 900 $, plus haut 51 000 $, 9 séances), il retrouve les
chiffres de l'audit : 6 MNQ 29,9 % réussis / 24,6 % échoués (audit : 29,9 / 24,7), 4 MNQ 22,9 / 12,2 (audit : 22,9 /
12,2). Prix d'entrée et de sortie identiques au rejeu du bot pour les 1 744 trades.

## La situation réelle : 50 000 $, plancher 49 000 $ suivi en temps réel, 8 séances

| Témoin | 2011 - 2019 | 2020 - 2023 | Coffre 2024 - 2026 |
|---|---|---|---|
| a. le bot tel quel, 4 MNQ, limite 1 000 $ | 14,4 % réussis / 35,9 % échoués | 17,9 / 51,3 | 15,6 / 48,5 |
| b. 6 MNQ, limite 1 000 $ | 20,7 / 52,8 | 20,6 / 63,8 | 20,3 / 63,5 |
| c. prudent, 2 MNQ, limite 500 $ | 2,4 / 11,2 | 5,6 / 17,9 | 2,1 / 15,1 |

## Ce que la machine a trouvé (25 133 génomes distincts, 4 vagues × 6 graines)

- **Un seul ingrédient compte : le garde-plancher.** Toutes les vagues qui y ont accès convergent dessus, quelle que soit
  la graine. Le champion est le plus simple : **6 MNQ, limite 1 000 $, tout fermer et arrêter la journée si le compte
  arrive à 350 $ du plancher (plancher suivi en temps réel)**.
- **Aucun filtre d'entrée ne survit** (dépassement, heure, régime de volatilité, écart d'ouverture) : la vague « filtres
  seuls » ne fait pas mieux que le témoin, et aucun finaliste n'en garde un qui compte. Même conclusion que toutes les
  recherches précédentes : la zone + C2 + Q1 reste l'entrée.
- Stops, objectifs par trade, stop à l'entrée, verrou de gain, arrêt après un gain : bruit autour du champion.

| Champion (6 MNQ, garde 350 $ en temps réel) | 2011 - 2019 | 2020 - 2023 | Coffre 2024 - 2026 | Avril - octobre 2026, vrai delta |
|---|---|---|---|---|
| Réussis / échoués | 16,3 / 1,7 | 15,6 / 4,9 | 14,9 / 3,3 | 20,3 / 2,1 (143 départs) |

Contrôles : 1 (bat les témoins sur 2020 - 2023) oui ; 3 (pessimiste + 1 tick) oui ; 4 (t des journées 4,10) oui ;
5 (coffre) oui. **Contrôle 2 (voisins) : non**, dans les deux lectures, parce que le voisin « objectif par trade à 1
largeur » (ou « objectif du jour 500 $ ») est une autre règle, pas un petit pas. Le plateau des vrais réglages
(`resultats/plateau.txt`) est lisse : marge 200 → 500 $ et taille 4 → 6 MNQ font varier réussite et échec
régulièrement, sans pic isolé. **Au sens strict des règles écrites, aucun finaliste n'est « retenu ».**

## Le prix du garde : des comptes sauvés mais bloqués

Le garde transforme les échecs en comptes en vie, mais sur 15 ans **83 % des comptes encore en vie au 12 novembre sont
bloqués à moins de 400 $ du plancher** : après une journée perdue de ~650 $, le garde interdit de retrader. Le garde ne
crée pas de réussite : il en coûte même 4 à 5 points (20 % → 15 %). Il protège le compte, c'est tout.

| 6 MNQ | Réussis (coffre) | Échoués (coffre) |
|---|---|---|
| sans garde, limite 1 000 $ | 20,3 % | 63,5 % |
| garde temps réel 200 $ | 16,9 % | 10,9 % |
| garde temps réel 350 $ | 14,9 % | 3,3 % |
| garde temps réel 500 $ | 12,2 % | 1,8 % |
| règle à la main : limite du jour = solde − plancher − 350 $, chaque matin | 15,2 % | 6,8 % |
| limite fixe 650 $ (sans la recalculer) | 18,5 % | 60,2 % |

La règle à la main suffit tant que le compte ne dépasse pas 51 500 $ (le plancher ne bouge pas avant) ; au-delà, seul
le garde en temps réel (à coder dans le bot) suit le plancher qui monte pendant la séance.
