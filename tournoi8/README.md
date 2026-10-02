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

## Résultats (2 octobre 2026) : un survivant, le RSI(2) sur le NQ

`tournoi8.py` → `exploration8.txt` ; `coffre8.py` → `coffre8.txt` ; `combinaison8.py` → `combinaison8.txt` ;
contrôle descriptif → `coffre8_hasard.txt`. Tests : `test_tournoi8.py` (5 contrôles, tous passés).

**Exploration 2011-2022** (t ≥ 2 et battre 95 % des placements au hasard) :

| Stratégie | NQ : t / bat le hasard | ES : t / bat le hasard |
|---|---|---|
| RSI(2) | **+2,40 / 95,5 % → survit** | +2,09 / 94,3 % (échoue de peu) |
| Double 7 | +1,91 / 68 % | +1,50 / 58 % |
| IBS | +1,22 / 78 % | +1,97 / 96,8 % (échoue de peu) |
| Rebond de 5 jours | +1,43 / 39 % | +0,79 / 20 % |
| Veille de jour férié | +1,22 / 84 % | +1,41 / 91 % |

Robustesse, à titre descriptif, sur 2016-2022 : RSI(2) sur le Dow t +1,42, sur le Russell t −0,08.

**Coffre 2023 - septembre 2026, ouvert une fois (m = 1, seuil t ≥ 1,64) : le RSI(2) NQ passe.**
- t +1,95, Sharpe 1,01 ;
- 40 trades, **+11 098 $ pour 1 MNQ** ;
- perte maximale −2 590 $, en position 14 % du temps ;
- 68 % de trades gagnants, gain moyen +603 $, perte moyenne −399 $ ;
- 2023 +1 512 $, 2024 +3 362 $, 2025 +3 408 $, 2026 +2 816 $.

Contrôle descriptif, qui n'est pas une règle du tri : sur le coffre, les mêmes 40 trades placés au
hasard donnent un t médian de +0,85, car le marché a beaucoup monté. Le RSI(2) bat **88 %** de ces
placements, pas 95 % : une partie de son gain récent vient de la hausse du marché. Il reste en position
seulement 14 % du temps.

**Avec la zone de bruit** :
- corrélation quotidienne −0,06 (2011-2022) et −0,02 (2023-2026) : **les deux sources sont
  indépendantes** ;
- Sharpe 2023-2026 : zone seule 0,90, RSI(2) seul 0,94, **mélange au même risque 1,31**.

Challenge Phidias 50K (gestion du robot, chaque source à f × coussin / √2, au moins 1 MNQ chacune) :

| Départs | Zone seule | Zone + RSI(2) |
|---|---|---|
| 2023-2024, suivis 24 mois | −22 $/an net, rien reçu dans 79 % des cas | **+254 $/an net, rien reçu dans 27 % des cas** |
| 2023-2025, suivis 12 mois | −114 $/an, 87 % | −115 $/an, 78 % |
| 2011-2020, 24 mois (en échantillon) | −183 $/an, 85 % | −6 $/an, 81 % |

**Lecture.** Le RSI(2) est la première stratégie qui passe toutes les étapes depuis la zone de bruit.
Elle est indépendante de la zone et améliore nettement le mélange. Mais :
- elle a passé l'exploration de justesse ;
- son coffre ne compte que 40 trades ;
- une partie de son gain récent vient de la hausse du marché ;
- avec 1 MNQ par source, le challenge reste peu rentable : environ +250 $/an sur 24 mois, et rien sur
  12 mois.

C'est une deuxième source plausible, pas une certitude.

## RSI(2) sans week-end (règles fixées le 2 octobre 2026, avant le calcul)

**Pourquoi.** L'utilisateur cherche une propfirm futures qui accepte à la fois la zone, le filtre delta et le
RSI(2) dans un robot qui trade seul. Aucune trouvée : celles qui acceptent les robots et la nuit (The Trading
Pit Classic Futures, Bulenox 10K) imposent de tout fermer avant le week-end, et le RSI(2) passe un week-end
dans environ 6 trades sur 10 depuis 2012. On mesure ce que coûte une fermeture chaque vendredi.

**Variante.**
- Mêmes signaux que le RSI(2) ci-dessus (`positions(s, 0)`), sur `nasdaq100_1min.csv.gz`, de 2011 à la
  dernière séance disponible de 2026.
- Si la position est tenue à la décision de la dernière séance de la semaine (la séance suivante tombe dans
  une autre semaine), elle est fermée à cette décision (15 h 50, prix `P`).
- Elle est rouverte à l'ouverture de 9 h 30 de la séance suivante, puis suit la règle d'origine.
- Deux ordres de plus par week-end, au même coût que les autres (1 $ + 1 tick par ordre).

**Décision.** La variante est utilisable dans le robot si, sur toute la période :
1. le t des rendements nets quotidiens est au moins 2 (même mesure que l'exploration) ;
2. elle garde au moins la moitié des dollars du RSI(2) d'origine (1 MNQ).

Publié dans tous les cas : les deux versions sur toute la période et sur le coffre 2023-2026, année par
année, et le nombre de fermetures du vendredi.

### Résultat (2 octobre 2026) : `sans_weekend.txt`

| | Original | Sans week-end |
|---|---|---|
| 2012 - septembre 2026 | t 3,05, +19 498 $ | **t 2,49, +12 670 $ (65 %)** |
| Coffre 2023 - 2026 | t 1,95, +11 098 $ | t 0,90, +4 516 $ (41 %) |

- L'original redonne exactement le coffre ci-dessus (+11 098 $, t 1,95) : même code, mêmes données.
- **Selon la règle fixée, la variante est utilisable** (t 2,49 ≥ 2, et 65 % des dollars gardés).
- Mais elle est faible là où le RSI(2) avait été validé : sur 2023 - 2026, elle ne garde que 41 % des
  dollars, avec t 0,90. Une grosse part du gain récent se fait pendant le week-end : en moyenne +32 points
  du vendredi 15 h 50 au lundi 9 h 30, sur 101 week-ends.
- Elle ne fait mieux que l'original que 5 années sur 15 (2012, 2015, 2019, 2021, 2022).
