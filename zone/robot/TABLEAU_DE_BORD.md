# Robot zone de bruit (MNQ) : tableau de bord (argent virtuel)

Mis a jour le **2026-09-29**. Demarre le 2026-09-25. Aucun argent reel n'est engage.

Historique : backtest 2011-2026 au meme reglage : une tentative de challenge reussit 39 % du temps et saute 4 % (les autres n'ont pas fini) ; environ 1 chance sur 3 de valider en 12 mois ; une fois finance, environ 680 $ recus par an en moyenne, rien dans 86 % des cas.

**Challenge n°1 en cours : -246 $ sur +4 000 $ ; marge avant la limite 2,254 $**

| Mesure | Valeur |
|---|---|
| Tentatives de challenge | 1 (n°1 en cours) |
| Recu en retraits virtuels (80 %) | 0 $ |
| Gain de la strategie pour 1 MNQ depuis le depart | -246 $ |

## Pour la seance du 2026-09-30 (a utiliser en direct)

Cloture de la veille (16 h New York) : **30,617.50**. Apres l'ouverture de 9 h 30 : haut = max(ouverture, veille) x (1 + mouvement) ; bas = min(ouverture, veille) x (1 - mouvement). A chaque heure ci-dessous : cloture de la minute au-dessus du haut -> achat ; sous le bas -> vente ; en position, sortie si le prix repasse la limite ou le VWAP. Tout fermer a 15 h 59 (New York).

| Controle (New York) | Heure de Paris | Mouvement moyen | Haut = x | Bas = x |
|---|---|---|---|---|
| 10h00 | 16h00 | 0.262% | 1.00262 | 0.99738 |
| 10h30 | 16h30 | 0.403% | 1.00403 | 0.99597 |
| 11h00 | 17h00 | 0.420% | 1.00420 | 0.99580 |
| 11h30 | 17h30 | 0.451% | 1.00451 | 0.99549 |
| 12h00 | 18h00 | 0.482% | 1.00482 | 0.99518 |
| 12h30 | 18h30 | 0.494% | 1.00494 | 0.99506 |
| 13h00 | 19h00 | 0.577% | 1.00577 | 0.99423 |
| 13h30 | 19h30 | 0.574% | 1.00574 | 0.99426 |
| 14h00 | 20h00 | 0.532% | 1.00532 | 0.99468 |
| 14h30 | 20h30 | 0.530% | 1.00530 | 0.99470 |
| 15h00 | 21h00 | 0.530% | 1.00530 | 0.99470 |
| 15h30 | 21h30 | 0.584% | 1.00584 | 0.99416 |

Taille : un jour normal = 216 $ de risque pour 1 MNQ. Sur un compte neuf : f = 0.15 -> Phidias (coussin 2 500 $) 1 MNQ, Topstep (coussin 2 000 $) 1 MNQ ; f = 0.25 -> Phidias (coussin 2 500 $) 2 MNQ, Topstep (coussin 2 000 $) 2 MNQ ; f = 0.35 -> Phidias (coussin 2 500 $) 4 MNQ, Topstep (coussin 2 000 $) 3 MNQ. **En cours de challenge : MNQ = f x (solde - limite de perte) / 216, arrondi en dessous** (exemple : f = 0,25, coussin 1 500 $ -> 1 MNQ).

Le VWAP est celui de la seance americaine, calcule depuis 9 h 30 (pas depuis la reouverture de 18 h). On ne regarde le prix qu'aux heures de controle : pas de stop place dans le marche.

## Derniers jours

| Date | Phase | MNQ | Resultat du jour | Solde | Pour 1 MNQ | Evenement |
|---|---|---|---|---|---|---|
| 2026-09-29 | challenge n°1 | 1 | +0 $ | 49,754 $ | +0 $ |  |
| 2026-09-28 | challenge n°1 | 1 | -246 $ | 49,754 $ | -246 $ |  |
