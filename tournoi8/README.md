# Tournoi 8 : stratégies de plusieurs jours (NQ, ES)

Phidias autorise les positions de nuit, de week-end et de plusieurs jours. Une stratégie de plusieurs
jours, peu liée à la zone de bruit, pourrait donc tourner sur le même compte de challenge. L'utilisateur
a donné son accord le 2 octobre 2026. Ce tournoi cherche cette deuxième source de gains.

## Règles (fixées le 2 octobre 2026, avant tout calcul)

### Données et exécution

- Minutes Databento de `intraday/` : Nasdaq 100 (NQ, micro MNQ, 2 $ le point) et S&P 500 (ES, micro
  MES, 5 $ le point), séance de 9 h 30 à 16 h (New York), 2011 - septembre 2026.
- **Une décision par séance, 10 minutes avant la fin** : 15 h 50 un jour normal, 10 minutes avant la
  dernière minute un jour court.
  - Les indicateurs utilisent la clôture de la minute d'avant (15 h 49), le plus haut et le plus bas
    depuis 9 h 30.
  - L'ordre est exécuté à l'ouverture de la minute de décision.
  - On achète ou on vend toujours à ce moment-là : la position court d'une décision à la suivante, nuit
    comprise.
- **Changement d'échéance** : la position est fermée à la dernière décision de l'ancien contrat, et on
  ne rentre pas ce jour-là. Aucun rendement n'enjambe deux contrats.
- Séances de moins de 60 minutes de données, et séances tombant un jour férié de la Bourse : ignorées.
- Frais : 1 $ par ordre et 1 tick de glissement par ordre, soit 1,5 point de NQ ou 0,9 point d'ES par
  aller-retour.
- Achat seulement, comme dans les sources, 1 contrat micro.

### Les stratégies (5, chacune sur NQ et ES, soit 10 essais)

Paramètres des sources, sans réglage :

| # | Stratégie | Entrée (à la décision du jour t) | Sortie | Source |
|---|---|---|---|---|
| 1 | RSI(2) | clôture > moyenne des 200 clôtures et RSI de Wilder sur 2 clôtures < 10 | clôture > moyenne des 5 clôtures | Connors, Alvarez (2008) |
| 2 | Double 7 | clôture > moyenne des 200 et clôture = plus bas des 7 dernières clôtures | clôture = plus haut des 7 dernières | Connors, Alvarez (2009) |
| 3 | IBS | (clôture − bas) / (haut − bas) de la séance < 0,2 | à la décision suivante (gardée si le signal se répète) | Pagonidis (2014) |
| 4 | Rebond de 5 jours | variation depuis la décision précédente dans les 10 % les plus basses des 252 séances d'avant | 5 séances après le dernier signal | inversion à court terme (Jegadeesh 1990 ; Lehmann 1990), version indice |
| 5 | Veille de jour férié | la séance suivante est la dernière avant un jour férié de la Bourse de New York | à la décision suivante | Ariel (1990) ; Lakonishok, Smidt (1988) |

Jours fériés de la Bourse : jour de l'an, Martin Luther King, Presidents' Day, Vendredi saint, Memorial
Day, Juneteenth (depuis 2022), fête nationale, Labor Day, Thanksgiving et Noël, avec leurs reports.

**Déjà testé, pas repris ici** :
- le tournant du mois et la veille de la Fed (`fonds/`, rejetés) ;
- la tendance (`tendance/`, robot en virtuel) ;
- la nuit seule (`nuit/`).

### Le tri

1. **Exploration 2011-2022.** Le programme d'exploration ne charge pas les années suivantes. Deux
   conditions :
   - t ≥ 2 sur les rendements quotidiens nets (en % du prix, jours sans position compris) ;
   - **battre le hasard** : 1 000 versions où les mêmes trades, avec les mêmes durées, sont placés à
     des dates tirées au hasard, sans chevauchement ni passage d'échéance. Il faut que le t réel
     dépasse au moins 95 % des t obtenus au hasard.

     Ce contrôle est indispensable : un indice qui monte fait gagner presque n'importe quel achat. Il
     faut montrer que le moment choisi compte.
2. **Coffre 2023 - septembre 2026, ouvert une seule fois** pour les survivants. Un survivant passe s'il
   a, sur cette période :
   - un t au moins égal au seuil de Bonferroni pour m survivants (1,65 si m = 1 ; 1,96 si m = 2 ;
     2,13 si m = 3 ; 2,24 si m = 4 ; 2,33 si m = 5…) ;
   - un résultat positif au moins 3 années sur 4.
3. **Combinaison avec la zone de bruit** si un survivant passe le coffre :
   - corrélation quotidienne avec la zone ;
   - Sharpe du mélange au même risque sur 2023-2026 ;
   - simulation du challenge Phidias 50K avec les deux stratégies, comparée à la zone seule.
4. **Mesures publiées pour chaque essai** (elles décrivent, elles ne servent pas à choisir) : Sharpe,
   perte maximale pour 1 micro, temps passé en position, nombre de trades, trades gagnants, gain moyen
   et perte moyenne par trade.
5. **Robustesse, à titre descriptif seulement** : les mêmes 5 stratégies sur le Russell 2000 (RTY) et
   le Dow (YM), minutes de `zone_multi/`, 2016-2022 en exploration.
6. Les 10 essais sont inscrits dans `fonds/essais.csv`. Aucune stratégie, aucun paramètre ni aucun
   marché ne sera ajouté ou changé après avoir vu les résultats.
