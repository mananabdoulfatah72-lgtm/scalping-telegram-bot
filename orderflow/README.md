# Order flow sur le Nasdaq (NQ) : système d'apprentissage et de test

L'utilisateur veut maîtriser l'order flow avant de prendre un challenge Phidias 50K, et a donné son
accord le 2 octobre 2026 pour **75 $ de données au plus** (3 téléchargements de 25 $ au plus).

Ce dossier contient :
1. **les données** : chaque transaction du NQ avec son sens, agrégée ;
2. **les outils** : footprint, delta, CVD, gros ordres, absorption, VWAP, niveaux de la veille ;
3. **une page d'atelier** pour voir chaque séance comme sur une plateforme d'order flow ;
4. **un test honnête** de cinq idées, avec règles fixées ici avant de télécharger.

## Règles (fixées le 2 octobre 2026, avant tout téléchargement)

### Données

- Databento GLBX.MDP3, schéma `tbbo` : chaque transaction du **NQ** (contrat le plus échangé, NQ.v.0),
  avec son sens (acheteur ou vendeur agressif), et le meilleur prix acheteur et vendeur affichés juste
  avant, avec leurs quantités.
- Séance américaine (9 h 30 - 16 h, New York). Les jours les plus récents d'abord.
- **3 téléchargements de 25 $ au plus chacun** ; le coût est demandé à Databento avant chaque jour.
  Les montants réels sont écrits dans `donnees/achats.txt`.
- Les transactions brutes sont trop lourdes pour le dépôt. Elles sont agrégées :
  - **par seconde** : dernier prix, plus haut, plus bas, volume acheteur et vendeur agressif, nombre de
    transactions, meilleur prix acheteur et vendeur et leurs quantités, contrat ;
  - **par minute et par prix** (footprint) : volume acheteur et vendeur ;
  - **gros ordres** : toute transaction d'au moins 10 contrats NQ, avec heure, prix, sens et taille.
- **Ce qui manque** : la profondeur du carnet au-delà du premier niveau (DOM, heatmap, icebergs).
  L'historique coûte environ 100 $ par jour ; il viendra des enregistrements de la plateforme de
  l'utilisateur.

### Exécution simulée

- Ordres au marché : achat au meilleur prix vendeur, vente au meilleur prix acheteur, à la seconde qui
  suit le signal. L'écart réel est donc payé.
- Plus 1 $ par ordre (0,5 point de NQ pour un MNQ). Résultats en points de NQ par trade (1 point = 2 $
  pour un MNQ).
- Pas de trade le jour d'un changement de contrat. Une position à la fois par hypothèse. Tout est
  fermé à 15 h 59.

### Les cinq hypothèses

| # | Hypothèse | Règle exacte |
|---|---|---|
| H1 | **L'order flow comme filtre de la zone de bruit** | À chaque contrôle de la zone (10 h, 10 h 30, … 15 h 30), quand la zone donne un signal d'entrée (règle du robot), on mesure le delta des 30 minutes avant : (achat − vente) / (achat + vente). Le trade est gardé si le delta va dans son sens, écarté sinon. On compare le gain par trade des trades gardés et des trades écartés. |
| H2 | **Absorption sur un niveau clé, puis retournement** | Niveaux : plus haut et plus bas de la séance précédente, VWAP du jour. Une minute dont le prix passe à 2 ticks ou moins d'un niveau, avec un volume agressif vers le niveau au-dessus du 90e centile des minutes des 5 séances d'avant, mais qui clôture à au moins 2 ticks du niveau, du côté d'où il venait. Trade contre la poussée, sortie 15 minutes après. |
| H3 | **Suivre les gros ordres** | Une transaction d'au moins le 99,9e centile des tailles des 5 séances d'avant (au moins 10 contrats). On suit son sens, sortie 15 minutes après. Pas de nouveau signal pendant une position. |
| H4 | **Divergence du CVD sur un nouveau plus haut ou plus bas** | Nouveau plus haut de la séance (après 10 h) alors que le delta cumulé des 30 dernières minutes est négatif : vente. Symétrique sur un nouveau plus bas. Sortie 15 minutes après. |
| H5 | **Suivre le delta de 15 minutes** | Toutes les 15 minutes (de 9 h 45 à 15 h 30) : si (achat − vente) / (achat + vente) des 15 dernières minutes dépasse 0,15 en valeur absolue, on le suit pendant 30 minutes. |

### Le tri

- Les séances sont rangées par date : **les deux premiers tiers servent à l'exploration**, le dernier
  tiers est le **coffre**, ouvert une seule fois.
- **Exploration** (H2 à H5) : une hypothèse survit si elle remplit les trois conditions :
  - gain net moyen par trade positif ;
  - t ≥ 2 (sur les trades) ;
  - bat 95 % de 1 000 placements au hasard (mêmes nombres de trades, mêmes sens, mêmes durées, à des
    secondes tirées au hasard dans les mêmes séances).
- **H1** se juge sur la différence de gain par trade entre trades gardés et écartés. Avec environ un
  trade de zone par jour, l'échantillon sera petit : le résultat sera surtout descriptif, et il le
  sera dit.
- **Coffre** : pour les survivants, t ≥ seuil de Bonferroni (1,65 pour 1 survivant, 1,96 pour 2…) et
  gain net positif.
- Mesures publiées pour chaque hypothèse : trades, gain brut et net par trade (points et $ pour 1 MNQ),
  part de trades gagnants, écart payé.
- Les essais sont inscrits dans `fonds/essais.csv`.

### Rappel de ce qui est déjà connu (`ordres/`, ES, 23 séances)

Le déséquilibre du premier niveau du carnet et l'OFI contiennent une vraie information à 1 minute,
mais elle vaut moins que les frais d'un aller-retour au marché. Delta 1 minute, CVD 15 minutes,
footprint empilé et absorption à 5 minutes : rien d'exploitable. Ici, on cherche donc sur des horizons
plus longs (15 à 30 minutes), sur le NQ, et autour de niveaux.

## Version 2 des règles (2 octobre 2026, avant l'arrivée des données) : la machine order flow

L'utilisateur demande d'utiliser **tous les outils** de l'order flow, dont le volume profile (POC,
VAH, VAL, HVN, LVN), et de tester **des milliers de stratégies**. Les données ne sont pas encore
arrivées : les règles sont élargies ici, avant tout calcul. Les 5 hypothèses ci-dessus restent
testées telles quelles.

### Ce que nos données permettent, et ce qu'elles ne permettent pas

| Outil | Disponible | D'où |
|---|---|---|
| Tape, delta, CVD, footprint, déséquilibres empilés | oui | chaque transaction avec son sens |
| Volume profile : POC, VAH, VAL (70 % du volume), HVN, LVN | oui | footprint (volume par prix) |
| VWAP et bandes de VWAP | oui | transactions |
| Gros ordres | oui | transactions d'au moins 10 contrats |
| Carnet au 1er niveau (meilleur acheteur / vendeur et quantités) | oui | schéma tbbo |
| **DOM au-delà du 1er niveau, heatmap, icebergs, ordres retirés** | **non** | il faut le carnet complet : enregistrements de la plateforme de l'utilisateur |

### Les briques (toutes calculées avec les seules données connues à la fin de la minute)

- **Niveaux** (16) :
  - de la veille : plus haut, plus bas, clôture, POC, VAH, VAL, HVN et LVN les plus proches ;
  - du jour : VWAP, VWAP ± 1 écart-type, VWAP ± 2 écarts-types, plus haut et plus bas des 30
    premières minutes, POC du jour en cours.
- **HVN et LVN de la veille** : maxima et minima locaux du profil de volume lissé sur 5 ticks.
- **Value area** : la plus petite zone autour du POC qui contient 70 % du volume.
- **Mesures d'order flow sur W minutes** (W = 1, 3, 5, 10, 15, 30 ou 60) :
  - déséquilibre (achat − vente) / (achat + vente) ;
  - divergence entre le prix et le CVD ;
  - déséquilibre du carnet au 1er niveau (moyenne des 10 dernières secondes de la minute) ;
  - volume net des gros ordres ;
  - déséquilibres empilés du footprint (au moins 3 prix de suite où l'achat dépasse r fois la vente
    du prix juste en dessous, ou l'inverse) ;
  - pic de volume par rapport à la même minute des 5 séances d'avant.

### Le génome (une stratégie = une combinaison)

| Gène | Valeurs |
|---|---|
| famille | toucher d'un niveau, déséquilibre, divergence CVD, carnet 1er niveau, gros ordres, empilement, pic de volume |
| niveau | les 16 niveaux (famille « toucher d'un niveau ») |
| confirmation | aucune ; delta de la minute dans le sens du mouvement ; delta contre le mouvement (absorption) |
| W | 1, 3, 5, 10, 15, 30, 60 minutes |
| seuil | un nombre de 0 à 1, traduit selon la famille (déséquilibre 0,05 à 0,5 ; ratio 2 à 5 ; multiple 1,5 à 5 ; tolérance de 1 à 8 ticks pour toucher un niveau) |
| sens | suivre, contrer |
| sortie | après 5, 10, 15, 30 ou 60 minutes, ou à la fin de la séance |
| stop | aucun, 10, 20 ou 40 ticks |
| heures | début 9 h 35, 10 h, 11 h ou 13 h ; fin 11 h, 13 h, 15 h ou 15 h 45 |

Décision à la clôture de la minute, exécution à la seconde suivante au meilleur prix du côté payé,
sortie au meilleur prix du côté reçu, + 0,5 point par ordre. Une position à la fois.

### La boucle, le contrôle et le coffre

- **Algorithme génétique** sur les séances d'exploration (deux premiers tiers) : 200 stratégies par
  génération, 60 générations, 6 graines. Élites, descendants par famille et immigrants, comme la
  machine n°3.
- **Fitness** : t du gain net **par séance** (les trades d'une même séance ne sont pas indépendants),
  réduit en proportion sous 60 trades.
- **Contrôle sur hasard** : la même machine, mêmes graines, où le sens de chaque trade est remplacé par
  un sens tiré au hasard (fixe pour une séance et une minute données). On mesure ainsi le meilleur
  résultat que la sélection produit sans aucune information de sens.
- **Finalistes** : les 5 meilleures stratégies réelles de familles différentes, si leur fitness dépasse
  la meilleure obtenue sur hasard.
- **Coffre, une seule fois** (dernier tiers des séances) : t par séance ≥ seuil de Bonferroni pour les
  finalistes, et gain net positif.

Toutes les stratégies évaluées sont comptées dans `fonds/essais.csv`.
