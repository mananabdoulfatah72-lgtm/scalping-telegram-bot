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

### Note du 2 octobre 2026, à l'arrivée des données (avant tout calcul de résultat)

- Reçu : **131 séances** du 1er avril au 1er octobre 2026, pour **74,46 $** (`donnees/achats.txt`).
- **4 jours fériés américains** (25 mai, 19 juin, 3 juillet, 7 septembre) : le marché ferme à 13 h et le
  volume vaut 6 à 11 % d'une séance normale. Ces séances sont **retirées**. Il reste 127 séances.
- **Séances minces** : volume sous 40 % de la médiane des 20 séances d'avant. Ce sont les veilles de
  changement de contrat, où le symbole suit encore l'ancien contrat presque abandonné (15 et 16 juin,
  15 septembre). **Pas de trade** ces jours-là, comme un jour de changement de contrat.
- Découpage : **exploration = 84 séances** (1er avril - 31 juillet), **coffre = 43 séances**
  (3 août - 1er octobre).

### Ajout du 2 octobre 2026, après l'exploration des cinq idées, avant l'ouverture du coffre

L'exploration (`exploration_of.txt`) ne laisse aucun survivant parmi H2 à H5. Pour H1, sur 76 trades de
la zone de bruit, les trades dont le delta des 30 minutes va dans leur sens gagnent +9,24 points en
moyenne (61 trades), les autres perdent −41,25 points (15 trades) ; écart +50,49 points, t = 1,68.
C'est en dessous de 2, et l'échantillon est petit.

H1 est donc **ajoutée au coffre comme test de confirmation**, avec une règle fixée ici : sur les séances
du coffre, le filtre est confirmé si l'écart de gain par trade (gardés − écartés) est positif avec
**t ≥ 1,65** (un seul test). Le gain par trade de la zone avec et sans filtre est publié dans tous les cas.

## Résultats (2 octobre 2026)

### Exploration (84 séances, 1er avril - 31 juillet 2026) : `exploration_of.txt`

| # | Trades | Net par trade | t | Bat le hasard | Verdict |
|---|---|---|---|---|---|
| H2 absorption sur un niveau | 199 | +4,20 pt | +0,69 | 84 % | éliminée |
| H3 suivre les gros ordres | 1 680 | −4,48 pt | −2,97 | 3 % | éliminée (suivre les gros ordres perd) |
| H4 divergence du CVD | 61 | +0,07 pt | +0,01 | 94 % | éliminée |
| H5 suivre le delta de 15 min | 2 | −12,88 pt | −0,42 | 26 % | éliminée (le seuil de 0,15 n'est presque jamais atteint sur le NQ) |
| H1 filtre de la zone | 76 trades de zone | gardés +9,24 pt, écartés −41,25 pt | 1,68 | | descriptif, ajoutée au coffre |

### Machine : `machine_of.txt`, `machine/`

- **41 567 stratégies distinctes** testées sur les vraies données, **42 231** sur des sens tirés au hasard.
- Meilleure fitness obtenue au hasard : **3,53**. Meilleure réelle : **3,74**. Seules 9 stratégies réelles font
  mieux que le hasard, toutes de la famille « déséquilibre ».
- Dans 4 familles sur 7 (divergence CVD, gros ordres, empilement, pics de volume), le hasard fait aussi bien
  ou mieux que les vraies données.
- 1 finaliste : contrer un déséquilibre d'une minute au-delà de 0,35, sortie 60 minutes, 11 h - 15 h 45
  (70 trades, +35,8 points nets par trade, t = 3,74 sur l'exploration).

### Coffre (43 séances, 3 août - 1er octobre 2026), ouvert une fois : `coffre_of.txt`

- **Finaliste de la machine : échoue.** 39 trades, +3,21 points nets par trade, t par séance = 0,50
  (seuil 1,64). L'avantage vu en exploration a presque disparu.
- **H1, filtre delta de la zone de bruit : confirmé.** 23 trades de zone : delta des 30 minutes dans le sens
  du trade, 18 trades à +67,40 points ; contre, 5 trades à −35,15 points. Écart +102,55 points, t = 2,34
  (seuil 1,65).
- Contrôle : le delta s'arrête à la seconde exacte où la zone entre (barres du robot alignées sur les
  transactions), donc le filtre ne voit pas le futur.

### Lecture

- **Aucune stratégie order flow autonome** ne bat le hasard après frais, ni parmi les cinq idées fixées
  d'avance, ni parmi plus de 40 000 combinaisons. Cela rejoint `ordres/` (ES) : l'information de
  l'order flow existe, mais elle est plus petite que l'écart payé et les frais.
- **L'order flow sert comme filtre** : ne prendre un trade de zone que si le delta des 30 dernières
  minutes va dans son sens. Sur les 6 mois (99 trades de zone), cela écarte 20 trades à −39,7 points en
  moyenne. La zone passe de +982 à +1 777 points, soit environ +1 590 $ pour 1 MNQ.
- **Descriptif, après le coffre** : le filtre marche aussi avec un delta sur 15, 45, 60 ou 90 minutes
  (t de 1,7 à 2,5), pas sur 5 ou 10 minutes.
- **Prudence** : la confirmation repose sur 5 trades écartés dans le coffre, et 20 en tout. L'effet réel est
  probablement plus petit que celui mesuré. Le filtre doit être suivi en virtuel avec la zone avant
  d'être utilisé en vrai.

## Le filtre H1 avec d'autres durées de delta (3 octobre 2026, descriptif)

Question de l'utilisateur : le filtre marche-t-il sur toutes les durées ? Mêmes 97 trades de zone (avril -
25 septembre 2026), même règle (gardé si le delta va dans le sens du trade), seule la durée change. C'est
**descriptif** : la durée de 30 minutes avait été fixée avant le coffre, et les autres durées réutilisent les
mêmes trades et les mêmes mois.

| Durée du delta | Gardés | Écartés | Points gardés | Points écartés | t | Zone filtrée (1 MNQ) |
|---|---|---|---|---|---|---|
| 5 min | 56 | 41 | +25,3 | −7,3 | 1,14 | +2 836 $ |
| 10 min | 58 | 39 | +17,7 | +2,4 | 0,53 | +2 052 $ |
| 15 min | 66 | 31 | +28,6 | −24,7 | 2,15 | +3 772 $ |
| 20 min | 72 | 25 | +20,9 | −15,5 | 1,52 | +3 015 $ |
| **30 min** | 77 | 20 | +24,9 | −39,7 | **2,56** | **+3 830 $** |
| 45 min | 74 | 23 | +23,6 | −27,2 | 1,98 | +3 494 $ |
| 60 min | 77 | 20 | +22,7 | −31,4 | 2,14 | +3 499 $ |
| 90 min | 74 | 23 | +22,4 | −23,5 | 1,82 | +3 322 $ |

Zone seule : +2 241 $.
- De 15 à 90 minutes, l'effet va dans le même sens et garde une taille voisine. Le choix de 30 minutes n'est
  donc pas un réglage fragile.
- Sur 5 et 10 minutes, l'effet est faible.
- Limite : ce sont les mêmes 6 mois et les mêmes trades. Ces durées se recoupent et ne confirment pas le filtre
  sur d'autres périodes. Ce test-là n'a toujours pas été fait, faute de vraies données d'avant avril 2026.
