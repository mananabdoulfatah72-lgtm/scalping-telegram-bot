# Supertrend NQ : la stratégie (2 novembre 2026)

Stratégie Quantower à part, indépendante du bot 3 en 1. Elle s'installe avec la même ligne PowerShell et apparaît dans
le Strategies manager sous le nom **Supertrend NQ (10-3, 5 min)**.

## Ce qu'elle fait

- Bougies de 5 minutes du NQ, de 15 h 30 à 22 h (heure de Paris), l'indicateur continuant d'une séance à l'autre.
- **ATR** = amplitude moyenne des 10 dernières bougies (méthode de Wilder) ; la **ligne du Supertrend** est à 3 ATR du prix
  (environ 124 points en octobre 2026) : sous le prix en tendance haussière, au-dessus en tendance baissière.
- À la clôture de chaque bougie, la position suit le sens du Supertrend : **achat** si la ligne est sous le prix, **vente**
  si elle est au-dessus. Quand une bougie clôture de l'autre côté de la ligne, la position se **retourne** (un seul ordre).
- Première position à 15 h 35, plus de nouvelle position après 21 h 30, **tout est fermé à 21 h 55** (heure de Paris).
- Ordres au marché sur MNQ (prix lus sur le NQ).

## Vérifications

- Le moteur C# (`Supertrend.Core`) refait **exactement** les 9 628 trades du test sur 15 ans (`audit/machine6/supertrend.py`,
  règle H12 de `scalping/partie_h.py`) : mêmes jours, mêmes sens, mêmes minutes, mêmes prix (`Supertrend.Replay`).
- La stratégie Quantower (`Supertrend.TestQuantower`, imitation de l'API) passe les mêmes ordres que le moteur sur 64
  séances (août - octobre 2026, 0 différence), à 1 et 2 MNQ, et réagit comme prévu : limite du jour, objectif, fichier
  STOP, position fermée à la main (pas rouverte avant le prochain retournement), relance en pleine séance (position reprise).

## Les chiffres (1 MNQ, au prix d'aujourd'hui, 3 $ de frais par aller-retour)

| Période | Séances | Par séance | t |
|---|---|---|---|
| 2011 - 2026 | 3 940 | +27,0 $ | 2,79 |
| 2011 - 2022 | 2 989 | +29,8 $ | 2,67 |
| 2023 - 2026 | 951 | +18,2 $ | **0,94** |

- 2,4 trades par séance, 42 % de trades gagnants (les gagnants sont plus grands que les perdants), une séance sur deux
  gagnante. Années perdantes : 2013, 2016, 2017.
- Le **t** mesure si le gain moyen est plus grand que le hasard : au-dessus de 2 à 3, le gain a peu de chances d'être de la
  chance. Sur 15 ans il fait 2,79 ; depuis 2023 il ne fait que 0,94 : le gain continue, mais il est devenu trop petit par
  rapport aux variations pour être sûr qu'il n'est pas dû au hasard.
- Challenge Bulenox depuis 50 000 $ avec un plancher à 49 000 $ suivi en temps réel (8 séances,
  `audit/machine6/resultats/supertrend.txt`) : 1 MNQ 3 à 8 % réussis / 32 à 46 % échoués ; 2 MNQ 14 à 22 % / 63 à 74 % ;
  4 à 6 MNQ environ 20 % / 77 à 80 %. Avec peu de marge au-dessus du plancher, elle est plus risquée que la zone.

## Réglages à remplir

| Réglage | Valeur |
|---|---|
| Compte | le compte qui tradera le Supertrend (**jamais le même que le bot 3 en 1 en même temps**) |
| NQ (prix et barres) | NQZ6 (contrat du moment) |
| MNQ (ordres) | MNQZ6 (même échéance) |
| MNQ par trade | **1** |
| Limite de perte du jour | **400** (par défaut) ; tout est fermé et plus de trade jusqu'au lendemain |
| Objectif | solde à atteindre (53 000 sur un challenge 50K), 0 sur un compte financé |
| Supertrend : ATR / multiple | **10 et 3** (seuls réglages testés : ne pas changer) |
| Dossier | C:\SupertrendNQ |
| Telegram | jeton et numéro de conversation (facultatif) |

## À savoir

- **Un compte, une stratégie.** La stratégie aligne la position MNQ du compte sur la sienne : si le bot 3 en 1 tourne sur le
  même compte, ils se ferment mutuellement leurs positions. De même, un trade manuel en MNQ sur ce compte est fermé.
- **La lancer avant 15 h 30 (heure de Paris).** Lancée plus tard, elle rejoue la séance sans ordre ; si sa position est déjà
  sur le compte, elle la reprend, sinon elle attend le prochain retournement (pas d'entrée au milieu d'une tendance).
- Position fermée à la main ou fichier `C:\SupertrendNQ\STOP` : position fermée, pas de nouvelle position dans le même sens
  avant le prochain retournement. Arrêter la stratégie ferme aussi la position.
- Journal : `C:\SupertrendNQ\journal.txt` ; état (résultat du jour, limite, objectif) : `C:\SupertrendNQ\etat.json`.
- Messages Telegram : lancement, chaque achat, vente et sortie (points et $), limite du jour, objectif, fin de séance,
  alertes (flux NQ coupé, symbole d'une autre échéance).
