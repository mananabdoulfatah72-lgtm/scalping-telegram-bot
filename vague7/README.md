# Vague 7 : le mélange de tout ce qui a marché, puis le meilleur challenge 50K (règles fixées le 9 octobre 2026, avant le calcul)

## Demande de l'utilisateur

Continuer à chercher. Au pire, additionner les sources d'avantage qui ont marché (zone de bruit, filtre delta…),
ne garder que celles qui rapportent le plus, puis voir quel challenge 50K à prix raisonnable convient le mieux au bot.

## Ce qui a marché, et ce qui n'a pas marché (recherches déjà faites, `fonds/essais.csv`)

Plus de 500 000 stratégies ont été essayées dans ce projet. Seules ces sources ont tenu :

| Source | Preuve | Déjà dans le bot ? |
|---|---|---|
| Zone de bruit NQ | t 2,55 (2011-2026) | oui |
| Filtre delta des 30 minutes sur la zone | t 2,34 au coffre (peu de trades) ; simulé ici, ρ 0,24 | oui |
| RSI(2) NQ de plusieurs jours | seul survivant du tournoi 8 (t 3,05) ; versions A3 (nuit, MES) et E4 (MES gardé) | oui |
| **Rebond après forte baisse** | achat de 1 MNQ de 9 h 30 à 16 h le lendemain d'une séance dans les 10 % les plus basses ; +6 420 $ sur 2023-2026 ; apport t 1,2 (2023-2026), 1,9 (2011-2022) ; surtout deux krachs (2020, 2025) | **non** (suivi à part depuis le 1er octobre) |

Rejetés, avec la raison :
- **Zone de bruit sur d'autres marchés** (ES, Russell, Dow, or, pétrole, euro) : perdante après frais partout sauf NQ
  (`zone_multi/`).
- **Robot de tendance multi-marchés** et mélange 50/50 : refusés comme 4e source (`protection/` pistes 6 et 7), car
  beaucoup plus de challenges perdus (pire jour −2 739 $). Ils ne sont pas refaits ici.
- **Veille de la Fed** : +113 $ par an et plus de pertes (`protection/`).
- Tout le reste n'a pas survécu : tournois 1 à 10, machines 3 à 5, order flow, sessions, largeur, vagues 3 et 4.

**La seule source qui reste à additionner est donc le rebond.**

## La règle du rebond (celle du robot, `zone/robot.py` sur main, version exécutable)

Achat de 1 MNQ à l'ouverture de 9 h 30, vente à la clôture de la dernière minute, le jour qui suit une séance dont le
mouvement ouverture → clôture est dans les 10 % les plus bas :
- la séance de référence est la dernière séance complète ;
- le seuil est le 10e centile des 252 valeurs précédentes de cette référence ;
- pas de rebond un jour court.

Pour le calcul :
- frais de 3 $ par MNQ et par aller-retour, comme la zone ;
- au niveau d'aujourd'hui du jour ;
- même taille que la zone (1×, 2× ou 3× selon le challenge ou le compte financé) ;
- fermé avec le reste si la limite du jour ou le plafond du jour est touché, et pas d'achat ce jour-là si le bot est
  déjà arrêté.

## Les candidates (fixées maintenant)

Pour chaque compte, le meilleur système de la vague 6 (fenêtre de choix), avec et sans le rebond :

| Compte | Système (vague 6) | Prix |
|---|---|---|
| Topstep | zone + A3, challenge 3×, financé 2× | 49 $ par mois + 149 $ |
| LucidFlex | zone + A3, challenge 3×, financé 2× | 140 $ une fois |
| FundedNext Legacy | zone + A3, challenge 3×, financé 2× | 200 $ une fois |
| DayTraders Static | E4, challenge 3×, financé 2× | 30 $ + 130 $ |
| DayTraders S2L | E4, challenge 1×, live 2×, réserve 6 000 $ | 229 $ |

Cela fait 10 candidates. La méthode est celle de la vague 6 :
- un seul compte à la fois ;
- chaque trade au niveau d'aujourd'hui de son jour d'entrée ;
- un compte est gardé tant qu'il vit ;
- règle d'activité de DayTraders ;
- filtre simulé aussi bon qu'en 2026.

## Le jugement (fixé maintenant)

1. **Le rebond reste sur un compte** s'il augmente le gain net par mois sur la fenêtre de choix (2012-2022) **et** sur la
   vérification (2023 - sept. 2026).
2. **Le meilleur challenge** est le système final de chaque compte qui a le gain le plus haut sur la fenêtre de choix. Il
   est validé si, en vérification :
   - il fait au moins +410 $ par mois (S2L, vague 6, le meilleur validé jusqu'ici) ;
   - chaque année est positive.

   Sinon, on passe au suivant.
3. **Objectif atteint** si le système validé fait au moins 500 $ par mois en vérification.
4. **Publié aussi** :
   - sans filtre et filtre inutile ;
   - le rebond seul par année ;
   - le prix total d'un essai ;
   - le classement de tous les comptes, pour choisir en connaissance de cause.

## Contrôles (`test_vague7.py`)

1. Le signal du rebond est exactement celui du robot (`zone/robot.py`, fonction `rebond`) sur toutes les séances, et il
   ne dépend que du passé.
2. Sans rebond, les moteurs redonnent leurs résultats d'avant :
   - `vague5_regles.txt` et `vague6.txt` sont redonnés à l'identique ;
   - les contrôles des vagues 4, 5, 6 et du Static passent.
3. Le gain d'un jour de rebond sans limite = (clôture − ouverture) × 2 $ × facteur du jour − 3 $, par MNQ, sur les deux
   moteurs.
