# Pistes pour les futures : ce que ton projet a déjà fermé, ce qui reste ouvert (16 novembre 2026)

Chiffres relus le 16 novembre dans les branches de recherche du dépôt. Le dossier cité est celui de la branche où se
trouve l'étude : `claude/keen-babbage-r686cl` sauf mention contraire.

## Le constat

En deux mois, ton projet a testé, toujours avec des règles fixées avant le calcul (inventaire du 29 octobre dans
`flux/inventaire/` et radar, branche `claude/optimistic-ptolemy-xs24ra`) :
- environ 190 stratégies et variantes publiées ou classiques, et 21 réglages successifs du Bot 3 en 1 ;
- environ 2,5 millions de configurations essayées par des machines, dont 41 567 stratégies d'order flow sur le NQ ;
- environ 27 millions de règles et 98 modèles d'apprentissage dans le radar, sur plus de 150 séries ;
- le calendrier, la nuit, les autres marchés.

**La source de gain la plus solide reste la zone de bruit** (Zarattini, Aziz, Barbon, 2024), tirée d'un article et
testée sans réglage :
- « aucune machine ne l'a trouvée » (`scalping/README.md`) ;
- de 2014 à septembre 2026, seule, elle fait mieux que toutes les combinaisons de stratégies : t +3,88, 12 années
  positives sur 13 (`flux/README.md`, partie 4) ;
- le 16 novembre, l'usine l'a confirmé : sur 7 idées, la zone est la seule à passer les 5 portes.

Deux modèles d'apprentissage ont aussi passé les règles de leur labo : XGBoost NQ et W1 NQ (`bot3en1/XGBOOST.md`,
`bot3en1/W1.md`). Mais ils ont été entraînés jusqu'au 2 novembre et n'ont pas encore de recul : XGBoost NQ n'a fait que
+342 $ du 3 au 13 novembre. Ils ne sont pas passés par l'usine.

**Ce que ça veut dire pour REA.** Lire plus de logiciels ne fera pas apparaître un avantage. Les pistes qui restent
viennent de données neuves, ou d'outils qu'on fait passer aux portes. REA sert à la deuxième voie, et à la sécurité du
système.

## Déjà fermé : ne pas refaire

« Bat X % du hasard » : part des placements au hasard (ou des placebos) que la stratégie bat. La barre était à 95 %.

| Idée | Source | Verdict | Où |
|---|---|---|---|
| Zone de bruit (Bot 3 en 1) | Zarattini, Aziz, Barbon (2024) | **Passe les 5 portes** | `usine/` (branche actuelle) |
| Supertrend 5 min | classique | Rejeté à la porte 2 (p = 4 %, 1 % exigé). Sa marche en avant gagne (+5 000 $ par an), mais pas mieux que le hasard (p = 23,5 %). À garder comme secours contre l'inactivité, pas comme source de gain. | `usine/` |
| ORB, cassure de la veille, fade du gap, fin de séance | classiques | Rejetés à la porte 1 | `usine/` |
| Momentum de la première demi-heure | Gao, Han, Li, Zhou (2018) | Rejeté à la porte 2 (p = 2,8 %, 1 % exigé) | `usine/` |
| Veille de la Fed | Lucca, Moench (2015) | Bat 87 % des placebos : rejetée | `fonds/` |
| Tournant du mois | McConnell, Xu (2008) | Sharpe 0,14, bat 52 % des placebos : rejeté | `fonds/` |
| Veille de jour férié | Ariel (1990) | NQ : t +1,22, bat 84 % du hasard : rejetée | `tournoi8/` |
| Semaine d'échéance des options | Stivers, Sun (2013) | t −0,03 : éliminée | `vague3/` |
| Calendrier complet (jour, mois, fenêtres, échéances) | — | Aucune règle retenue ; 2 intéressantes, autant que sur des données au hasard | `machine4/` |
| Même demi-heure que les jours précédents | Heston, Korajczyk, Sadka (2010) | Perd : t −5,73 | `ml/VAGUE_Q.md` (branche `optimistic-ptolemy`) |
| Order flow (delta, CVD, carnet, OFI, footprint) | — | Vraie information, mais elle vaut moins d'un tick quand un aller-retour coûte 2,6 ticks. Sur le NQ, 41 567 stratégies : la finaliste échoue au coffre (t 0,50). | `ordres/`, `orderflow/` |
| Machines évolutives | — | Sur des séances mélangées au hasard, la même machine trouve mieux (Sharpe 2,21) que sur les vraies (1,72) : elle fabrique de belles stratégies à partir de rien | `evolution/` |
| Radar (27 millions de règles, 98 modèles) | — | Une seule règle passe la confirmation, puis échoue au coffre (t 0,78) | `radar/` (branche `optimistic-ptolemy`) |
| Suivre les institutions (rapports de la CFTC) | — | Aucun signal ne passe | `chantier/` partie G (branche `loving-mccarthy`) |
| Retour à la moyenne en marché calme | — | Perd (t −2,34) | `chantier/` partie A (branche `loving-mccarthy`) |
| Trading de paires (S&P/Nasdaq, or/argent, taux, devises) | méthode des vidéos | Sharpe −0,45 sur 2006 - 2026 ; aucune paire « cointégrée » ne l'est encore 6 mois plus tard | `paires/` |
| Suivi de tendance sur 40 futures | méthode des CTA | Sharpe −0,01, bat 59 % des placebos : rejeté. En plus, il garde la nuit et ses contrats sont trop gros pour 50K. | `fonds/`, `tendance/` |
| RSI(2) sur plusieurs jours | Connors | Passe son coffre (t +1,95), mais il garde la nuit et le week-end : interdit chez Bulenox | `tournoi8/` |

## Encore ouvert, par ordre d'intérêt

| Piste | Pourquoi elle reste ouverte | Ce qu'il faut | REA ? |
|---|---|---|---|
| 1. **Une bande plus large pour la zone** | La marche en avant de l'usine a choisi la plus grande largeur de sa grille (1,4) à 140 de ses 145 pas. La recherche s'était arrêtée à 1,5 (`zone_optimisation/`). Le plateau continue peut-être au-delà. | Une grille de 1,4 à 2,4, règles fixées avant le calcul, puis les 5 portes. Données déjà là. | Non |
| 2. **Un secours qui gagne vraiment** | Le Supertrend tient la règle d'inactivité, mais sans avantage prouvé. Un moteur qui trade chaque jour et passe les portes améliorerait G2 directement. | Une recherche dédiée dans l'usine. XGBoost NQ et W1 NQ peuvent y passer en premier. | Non |
| 3. **La nuit en module** : achat à 18 h, stop 0,5 %, vente à 9 h 30, seulement à partir de 2 600 $ de marge | Elle améliore le compte, mais n'a pas atteint la barre fixée : +10 % d'argent touché par mois, pour 25 % exigés (`chantier/RESULTATS.md`, branche `loving-mccarthy`). | À coder dans le bot, puis à suivre en papier. | Non |
| 4. **L'order flow sur tes propres enregistrements** | FluxNQ enregistre à chaque séance où il tourne les transactions, le carnet sur 10 niveaux et le footprint du NQ (`C:\Bot3en1\flux\`). Chaque mois enregistré, c'est un mois de données que la recherche n'a jamais vues : un vrai hors échantillon. | Laisser FluxNQ enregistrer, puis rejouer les idées d'order flow sur ces données. | Enquête n° 3 (même définition du delta) |
| 5. **Un outil que tu utilises déjà** (indicateur, bot d'un ami) | Jamais passé aux portes. | Observation, puis spécification, puis l'usine. | Enquête n° 5 |

Ce qui ne relève pas de la recherche, mais compte pour l'argent : plusieurs comptes Master (règles Bulenox à confirmer).
Ce n'est pas un avantage, juste plus de plafonds de retrait, avec un risque lié : une mauvaise période touche tous les
comptes en même temps.
