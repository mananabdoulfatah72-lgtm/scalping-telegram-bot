# Usine a strategies : tableau de bord (2026-11-16)

Regles fixees avant le calcul : [REGLES.md](REGLES.md). Chaque idee passe les portes dans l'ordre et s'arrete a la premiere manquee. La zone et le Supertrend, deja sur le compte, passent toutes les portes pour information.

| Idee | Porte 1 : 2011 - 2014 | Porte 2 : permutations | Porte 3 : marche en avant 2015 -> | Porte 4 : permutations | Porte 5 : Master neuf, un an | Verdict |
|---|---|---|---|---|---|---|
| Zone de bruit (Bot 3 en 1 sans filtres) | PF 1,018, t 1,65 ✅ | p 0,9 % ✅ | PF 1,024, +4 073 $ par an ✅ | p 0,0 % ✅ | retrait 55,4 %, perdu 32,5 % ✅ | **passe les 5 portes** |
| Zone de bruit, bande large | PF 1,022, t 1,12 ✅ | p 13,2 % ❌ | — | — | — | **rejetée à la porte 2** |
| Supertrend NQ, bougies de 5 minutes | PF 1,008, t 1,77 ✅ | p 4,0 % ❌ | PF 1,006, +5 009 $ par an ✅ | p 23,5 % ❌ | retrait 41,1 %, perdu 58,3 % ❌ | **rejetée à la porte 2** |
| Cassure du range d'ouverture (ORB) | PF 1,006, t 0,92 ❌ | — | — | — | — | **rejetée à la porte 1** |
| Momentum de la première demi-heure | PF 1,040, t 2,01 ✅ | p 2,8 % ❌ | — | — | — | **rejetée à la porte 2** |
| Cassure du plus haut ou du plus bas de la veille | PF 1,006, t 0,75 ❌ | — | — | — | — | **rejetée à la porte 1** |
| Fade du gap d'ouverture | PF 1,081, t 1,87 ❌ | — | — | — | — | **rejetée à la porte 1** |
| Mouvement de fin de séance | PF 1,076, t 1,89 ❌ | — | — | — | — | **rejetée à la porte 1** |

PF : profit factor des rendements nets par minute. p : part des permutations qui font au moins aussi bien.

## Zone de bruit (Bot 3 en 1 sans filtres)

- **L'avantage :** Quand le prix sort de sa bande de bruit habituelle, le mouvement continue plus souvent qu'il ne revient.
- **Qui perd en face :** Ceux qui vendent la cassure, et les teneurs de marché qui couvrent leur gamma en suivant le mouvement.
- **Verdict : passe les 5 portes.** Porte 2 : p = 0,9 % ; porte 4 : p = 0,0 % ; hors échantillon +4 073 $ par an ; sur un Master neuf, 55,4 % de premiers retraits.
- Meilleur reglage sur 2011 - 2014 : largeur 1,4, jours de moyenne 30 (PF 1,018) ; milieu du plateau : largeur 1,4, jours de moyenne 30 (PF 1,018).
- Reglage du bot (largeur 1,0, jours de moyenne 14) : PF 1,014 sur 2011 - 2014.
- Marche en avant, 2015 -> derniere seance : 2962 seances, t 3,70.
- Milieu du plateau, 1 MNQ, 2015 -> derniere seance : +3 686 $ par an, t 3,32 (depuis 2023 : 1,29), pire baisse -4 732 $, pire seance -1 004 $ ; trade 39,6 % des seances.
  - seule : Master neuf, un an : 1,2 % de premiers retraits, 2,1 % perdus par le plancher, 96,8 % par l'inactivite ; depuis une marge de 700 $, un mois : 76,5 % de comptes perdus, gain moyen +171 $.
  - avec le Supertrend en secours : Master neuf, un an : 55,4 % de premiers retraits, 32,5 % perdus par le plancher, 0,0 % par l'inactivite ; depuis une marge de 700 $, un mois : 38,2 % de comptes perdus, gain moyen +301 $.

## Zone de bruit, bande large

- **L'avantage :** Celui de la zone ; une cassure plus lointaine est moins souvent une fausse cassure.
- **Qui perd en face :** Ceux qui vendent la cassure, et les teneurs de marché qui couvrent leur gamma en suivant le mouvement.
- **Verdict : rejetée à la porte 2.** Fait aussi bien sur des minutes mélangées : p = 13,2 %, il faut moins de 1 %.
- Meilleur reglage sur 2011 - 2014 : largeur 2,4, jours de moyenne 30 (PF 1,022) ; milieu du plateau : largeur 2,2, jours de moyenne 30 (PF 1,009).

## Supertrend NQ, bougies de 5 minutes

- **L'avantage :** Un jour de tendance, le mouvement court terme se prolonge.
- **Qui perd en face :** Les apporteurs de liquidité qui vendent la hausse un jour de tendance.
- **Verdict : rejetée à la porte 2.** Fait aussi bien sur des minutes mélangées : p = 4,0 %, il faut moins de 1 %.
- Meilleur reglage sur 2011 - 2014 : ATR 30, multiple 2,5 (PF 1,008) ; milieu du plateau : ATR 30, multiple 3,0 (PF 1,008).
- Reglage du bot (ATR 10, multiple 3,0) : PF 1,005 sur 2011 - 2014.
- Marche en avant, 2015 -> derniere seance : 2962 seances, t 1,82.
- Milieu du plateau, 1 MNQ, 2015 -> derniere seance : +8 162 $ par an, t 3,80 (depuis 2023 : 1,43), pire baisse -8 384 $, pire seance -405 $ ; trade 100,0 % des seances.
  - seule : Master neuf, un an : 41,1 % de premiers retraits, 58,3 % perdus par le plancher, 0,0 % par l'inactivite ; depuis une marge de 700 $, un mois : 60,9 % de comptes perdus, gain moyen +320 $.

## Cassure du range d'ouverture (ORB)

- **L'avantage :** Le déséquilibre des ordres de l'ouverture se prolonge dans la journée.
- **Qui perd en face :** Ceux qui vendent la cassure du range d'ouverture.
- **Verdict : rejetée à la porte 1.** Pic isolé : ses voisins ne suivent pas (meilleur PF 1,006).
- Meilleur reglage sur 2011 - 2014 : durée du range (min) 5, dernière entrée 11 h 00 (PF 1,006) ; milieu du plateau : durée du range (min) 5, dernière entrée 11 h 00 (PF 1,006).

## Momentum de la première demi-heure

- **L'avantage :** Le sens du début de séance prédit celui de la fin de séance (Gao, Han, Li, Zhou 2018).
- **Qui perd en face :** Les fonds et ETF à levier qui rééquilibrent en fin de séance quel que soit le prix.
- **Verdict : rejetée à la porte 2.** Fait aussi bien sur des minutes mélangées : p = 2,8 %, il faut moins de 1 %.
- Meilleur reglage sur 2011 - 2014 : fin du signal 10 h 30, référence ouverture, début de la position 15 h 30 (PF 1,040) ; milieu du plateau : fin du signal 11 h 00, référence ouverture, début de la position 15 h 30 (PF 1,034).

## Cassure du plus haut ou du plus bas de la veille

- **L'avantage :** Le plus haut et le plus bas de la veille concentrent des stops dont le déclenchement prolonge le mouvement.
- **Qui perd en face :** Les porteurs de ces stops.
- **Verdict : rejetée à la porte 1.** Pas assez bon sur 2011 - 2014 : PF 1,006, t 0,75.
- Meilleur reglage sur 2011 - 2014 : marge 0,20 %, dernière entrée 12 h 00, sortie retour dans le range (PF 1,006) ; milieu du plateau : marge 0,10 %, dernière entrée 12 h 00, sortie fin de séance (PF 1,006).

## Fade du gap d'ouverture

- **L'avantage :** Un écart de nuit en partie excessif se referme en début de séance.
- **Qui perd en face :** Ceux qui achètent ou vendent à l'ouverture sur les nouvelles de la nuit.
- **Verdict : rejetée à la porte 1.** Pic isolé : ses voisins ne suivent pas (meilleur PF 1,081).
- Meilleur reglage sur 2011 - 2014 : seuil 0,80 %, durée maximale (min) 30 (PF 1,081) ; milieu du plateau : seuil 0,80 %, durée maximale (min) 30 (PF 1,081).

## Mouvement de fin de séance

- **L'avantage :** Les ETF à levier et les vendeurs d'options achètent la hausse (vendent la baisse) du jour en fin de séance.
- **Qui perd en face :** Eux, qui paient l'impact de ces ordres forcés.
- **Verdict : rejetée à la porte 1.** Pic isolé : ses voisins ne suivent pas (meilleur PF 1,076).
- Meilleur reglage sur 2011 - 2014 : début 15 h 30, seuil 1,00 % (PF 1,076) ; milieu du plateau : début 15 h 30, seuil 1,00 % (PF 1,076).
