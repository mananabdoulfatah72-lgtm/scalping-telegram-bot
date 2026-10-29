# Système order flow : tape, footprint, carnet (règles fixées le 29 octobre 2026, avant tout calcul)

## Demande de l'utilisateur (29 octobre 2026)

Nouvelle perte de 800 $ sur le challenge Bulenox 50K, le compte est retombé sous 49 900 $ après trois semaines.
L'utilisateur juge que le problème vient de la stratégie (la zone de bruit), pas de lui ni du risque, et demande un
**nouveau système de trading fondé sur l'order flow** : tape (côté agresseur de chaque transaction), DOM, footprint.
Il a tous ces outils sur sa plateforme (Quantower, Rithmic).

## Ce qui est déjà connu, et donc pas refait ici

| Déjà testé | Où | Résultat |
|---|---|---|
| Delta 1 min, CVD 15 min, carnet au 1er niveau, OFI, footprint empilé, absorption à 5 min (ES, 23 séances) | `ordres/` (branche `claude/keen-babbage-r686cl`) | vraie information, mais moins d'un tick : perd après frais |
| H2 absorption sur un niveau (sortie 15 min, sans stop), H3 suivre les gros ordres, H4 divergence du CVD, H5 delta 15 min (NQ, avril - juillet 2026) | `orderflow/` (même branche) | aucune ne passe ; H2 : +4,2 points par trade, t 0,69 |
| Machine order flow, 41 567 stratégies (7 familles, sorties à durée fixe) | `orderflow/machine/` | la finaliste échoue au coffre (t 0,50) |
| **H1 : ne prendre une cassure de zone que si le delta des 30 minutes va dans son sens** | `orderflow/`, `filtre_h1/` | **confirmé au coffre** (t 2,34), mais sur 20 trades écartés seulement |

Deux leçons guident les règles ci-dessous :
1. l'order flow seul, à l'horizon d'une minute, vaut moins que les frais : il faut viser des mouvements de plusieurs
   points avec un risque défini, pas des scalps d'un tick ;
2. le seul effet confirmé est le **delta de 30 minutes comme contexte** : le flux persistant indique le sens, et le
   flux d'une seule minute n'a de valeur qu'à un endroit précis (un niveau, un extrême, un repli).

Aucun test précédent n'a utilisé un **stop serré posé sur la structure** (plus bas de la minute d'absorption, plus haut
de la cassure ratée) avec un **objectif à 2 fois le risque**. C'est la façon dont les traders order flow travaillent,
et c'est ce qui convient à un challenge dont la perte maximale (2 500 $) vaut à peine un tiers de l'amplitude d'une
journée de NQ en 4 MNQ.

## Données

| Source | Contenu | Séances | Rôle |
|---|---|---|---|
| Databento `tbbo` NQ (`orderflow/donnees/` de `claude/keen-babbage-r686cl`) | chaque seconde : prix, plus haut, plus bas, volume acheteur et vendeur agressif, meilleur acheteur et vendeur ; footprint par minute et par prix | 1er avril - 1er octobre 2026 | S1, S2, S3 |
| Export Rithmic du compte Bulenox (`filtre_h1/donnees_rithmic/transactions_NQZ6_rithmic.csv`) | chaque minute : ouverture, plus haut, plus bas, clôture, volume acheteur et vendeur agressif | 16 septembre - 16 octobre 2026 (sert du 2 au 16 octobre) | S1, S2 |
| Exports à venir de l'utilisateur (« Export transactions NQ », même format que Rithmic) | idem | depuis le 19 octobre 2026 | suivi de l'avenir |

- Mêmes retraits qu'`orderflow/` : jours fériés américains (clôture à 13 h), séances minces (volume sous 40 % de la
  médiane des 20 séances d'avant), séance de changement de contrat : pas de trade.
- Barres d'une minute de 9 h 30 à 16 h (heure de New York), minute t = 0 pour 9 h 30, 389 pour 15 h 59. Pour Databento,
  elles sont faites à partir des secondes (ouverture = prix de la première seconde).
- Le volume sans côté connu est ignoré (il est nul dans les deux sources).
- **Le DOM au-delà du premier niveau n'existe dans aucune donnée historique du projet** (il coûte environ 100 $ par jour
  chez Databento). Il ne peut donc pas être testé ici. Le carnet au premier niveau a déjà été testé (`ordres/`,
  `orderflow/`) : il n'est pas repris.

## Mesures à la clôture de la minute t (seulement ce qui est connu à cet instant)

- v_t = achats agressifs + ventes agressives ; delta_t = achats − ventes ; déséquilibre imb_t = delta_t ÷ v_t (0 si
  v_t = 0).
- VWAP_t de la séance : somme de ((plus haut + plus bas + clôture) ÷ 3 × v) ÷ somme de v, de 9 h 30 à t.
- D30_t = somme des delta des minutes t − 29 à t (depuis 9 h 30 si t < 29).
- **Seuils glissants**, calculés sur les minutes de 10 h à 15 h 59 des **5 séances précédentes** présentes dans les
  données (aucun seuil, donc aucun trade, pendant les 5 premières séances) :
  - q10, q25, q75, q90 de imb ;
  - footprint (Databento seulement) : q90 des ventes agressives aux **deux prix les plus bas** de chaque minute
    (plus bas et plus bas + 1 tick), et q90 des achats agressifs aux deux prix les plus hauts.

## Les trois setups (achat décrit ; vente : l'exact symétrique)

### S1 : repli absorbé dans le sens du flux (contexte initiatif, entrée sur absorption)

À la clôture de la minute t, avec 30 ≤ t ≤ 330 (de 10 h à 15 h) :
1. **contexte** : clôture_t > VWAP_t **et** D30_t > 0 (le flux des 30 dernières minutes est acheteur, comme H1) ;
2. **repli** : plus bas_t ≤ le plus bas des 5 minutes d'avant (t − 5 à t − 1) ;
3. **absorption** : imb_t ≤ q10 (ventes agressives fortes) **et** v_t ≥ médiane des v des 30 minutes d'avant ;
4. **les vendeurs n'avancent pas** : clôture_t ≥ (plus haut_t + plus bas_t) ÷ 2.

Stop : plus bas_t − 1 tick.

### S2 : cassure ratée, acheteurs piégés

Niveaux : plus haut et plus bas de la séance précédente (PDH, PDL) ; plus haut et plus bas de la première heure
(IBH, IBL, minutes 0 à 59), actifs à partir de 10 h 30. Pour un niveau L au-dessus du prix (PDH ou IBH), **vente** :
1. **cassure** : la première minute b de la fenêtre (b ≥ 30 pour PDH, b ≥ 60 pour IBH, b ≤ 330) dont le plus haut
   ≥ L + 1 tick alors que la clôture de b − 1 est ≤ L ;
2. **agression à la cassure** : imb_b ≥ q75 (les acheteurs ont attaqué le niveau) ;
3. **échec** : la première minute f de b à b + 5 qui clôture ≤ L − 1 tick ; signal à la clôture de f (f ≤ 330) ;
4. si l'une des conditions manque, le niveau est abandonné pour la séance (une seule tentative par niveau et par
   séance).

Stop : le plus haut de b à f + 1 tick. Pour PDL et IBL : achat, symétrique.

### S3 : volume d'arrêt à l'extrême (footprint, Databento seulement)

À la clôture de la minute t, 30 ≤ t ≤ 330 :
1. plus bas_t < tous les plus bas de la séance avant t (nouveau plus bas du jour) ;
2. ventes agressives aux deux prix les plus bas de la minute t ≥ q90 de cette mesure ;
3. clôture_t ≥ plus bas_t + 1 point (4 ticks de rejet).

Stop : plus bas_t − 1 tick.

## Exécution simulée (commune), en points de NQ

- **Entrée au marché** à l'ouverture de la minute qui suit le signal, avec 1 tick de glissement contre soi.
- **Stop** : celui du setup, ramené au plus à entrée − 3 points (stop d'au moins 3 points), arrondi au tick vers la perte.
  Risque R = |entrée − stop|. **Pas de trade si R > 0,12 % du prix d'entrée** (environ 35 points à 29 000).
- **Objectif** : entrée + 2 R (vente : − 2 R), arrondi au tick en s'éloignant de l'entrée.
- **Chaque minute, l'ordre le plus défavorable** : ouverture au-delà du stop → sortie à l'ouverture − 1 tick ; sinon
  stop touché → sortie au stop − 1 tick ; sinon objectif **traversé** d'un tick → sortie à l'objectif. Une minute qui
  touche le stop et l'objectif sort au stop.
- **Sortie au temps** : à la clôture de la 30e minute du trade (minute d'entrée + 29), au plus tard à 15 h 59, au
  marché avec 1 tick de glissement.
- **Commission** : 1 $ par ordre MNQ = 0,5 point de NQ par ordre. Un aller-retour coûte donc environ 1,5 point
  (comme la zone dans tout le projet).
- Une position à la fois par setup ; un nouveau signal est possible à la clôture de la minute de sortie.
- Résultat en points de NQ par trade ; 1 point = 2 $ par MNQ.

## Découpage, placebos, décision

- **A** : 1er avril - 31 juillet 2026 (déjà parcouru par la machine order flow d'`orderflow/`, avec d'autres règles).
- **B** : 3 août - 16 octobre 2026 (S3 : jusqu'au 1er octobre). Aucun des trois setups n'y a jamais été calculé.
- **t par séance** : t des gains nets quotidiens sur toutes les séances jouables (0 les jours sans trade).
- **Placebo de sens** : 2 000 tirages ; chaque trade garde sa minute d'entrée et son risque R, mais son sens est tiré à
  pile ou face (stop et objectif symétriques). Mesure : part des tirages dont le t par séance est battu.
- **Jumeau sans order flow** (descriptif) : le même setup sans sa condition d'order flow (S1 sans la condition 3,
  S2 sans la condition 2, S3 sans la condition 2). Il dit si le flux ajoute quelque chose au seul prix.

**Décision (fixée maintenant).** Un setup est **retenu pour le suivi en simulation** s'il remplit tout :
1. gain net moyen par trade > 0 sur A **et** sur B ;
2. t par séance sur A + B ≥ **2,13** (Bonferroni unilatéral à 5 % pour 3 setups) ;
3. bat **95 %** des placebos de sens ;
4. au moins 60 trades sur A + B.

**Argent réel** : jamais directement. Un setup retenu passe d'abord par le suivi de l'avenir (exports de l'utilisateur
ou compte de simulation, depuis le 19 octobre 2026) ; il n'est conseillé en vrai qu'après **au moins 40 trades suivis
avec un gain net moyen positif**. Publié quoi qu'il arrive.

**Descriptif, sans décision** : résultat mois par mois ; contrôle de l'exécution à la seconde sur Databento (entrée
au meilleur vendeur de la première seconde, stop et objectif suivis seconde par seconde) ; les trois setups ensemble ;
le challenge Bulenox 50K (perte max 2 500 $ suivie en fin de journée, objectif 53 000 $, limite du jour 1 000 $) de
1 à 4 MNQ, par tirage des séances.

## Résultats (29 octobre 2026, calcul lancé une seule fois) : `resultats/systeme.txt`

Contrôles faits avant le calcul (`test_flux.py`) : aucun regard vers le futur (40 coupures, 953 signaux identiques
quand les minutes suivantes et les séances suivantes sont remplacées par du hasard) ; exécution la plus défavorable
vérifiée sur des minutes fabriquées. Un trade de chaque setup a été revérifié à la main sur les minutes brutes (niveaux,
seuils, stop, objectif, frais) : conforme.

138 séances (127 Databento, 11 export Rithmic), 128 jouables : A = 76 séances (avril - juillet), B = 52 (août - 16 octobre).

| Setup | Trades A / B | Net moyen A / B (points) | Net moyen A + B | t par séance | Placebo battu | Décision |
|---|---|---|---|---|---|---|
| S1 repli absorbé dans le sens du flux | 14 / 14 | +4,07 / −2,98 | +0,54 | +0,20 | 56 % | non retenu |
| S2 cassure ratée (piégés) | 44 / 25 | −1,73 / +9,94 | +2,50 | +0,79 | 87 % | non retenu |
| S3 volume d'arrêt à l'extrême (footprint) | 391 / 192 | −3,27 / −2,32 | **−2,96** | **−4,08** | 47 % | non retenu |

**Décision fixée à l'avance : aucun setup n'est retenu.**

- **S1** se déclenche rarement (28 trades en 7 mois) et ne gagne rien : +0,5 point par trade.
- **S2** perd d'avril à juillet et gagne d'août à octobre ; sur l'ensemble, t +0,79. Descriptif, après coup : le même
  setup **sans** la condition d'agression (128 trades) fait +4,55 points par trade (t +2,03). Le flux n'ajoute rien à la
  seule cassure ratée ; ce chiffre-là a été vu après le calcul et n'est pas une preuve.
- **S3**, le « volume d'arrêt » qu'on voit sur le footprint, **perd chaque mois** (−1 723 points en 7 mois, soit
  −3 447 $ par MNQ) et ne fait pas mieux qu'un sens tiré au hasard : acheter le gros volume vendeur au plus bas du jour
  n'apporte rien, et un stop de 5 points en médiane est mangé par le bruit d'une minute de NQ (amplitude médiane
  12,5 points) et par les frais (1,5 point).
- Exécution à la seconde (Databento) : mêmes conclusions (S1 +0,31, S2 +3,88, S3 −3,12 points par trade).
- Les trois ensemble : 664 trades, −2,24 points par trade, −2 972 $ par MNQ sur 7 mois. Dans le challenge, aucun
  ne valide (S1 et S2 gagnent trop peu pour atteindre 53 000 $ en 30 séances ; S3 perd le compte à 4 MNQ dans 75 à
  93 % des tirages).

### Ce qu'on retient

C'est la même conclusion que `ordres/` (ES) et `orderflow/` (NQ, 41 567 stratégies), maintenant avec des stops serrés
sur la structure et des objectifs à 2 R, comme les traders order flow : **ce que montrent le tape et le footprint est
réel, mais trop petit pour payer les frais et le bruit d'une minute de NQ**. Un bot qui « voit » le flux ne gagne pas
pour autant : voir n'est pas prévoir.

Ce qui reste vraiment non testé, faute de données, c'est **le DOM** (profondeur du carnet, ordres posés et retirés,
icebergs). Aucune donnée historique n'existe dans le projet. Le seul moyen honnête de le tester est de l'enregistrer
en direct depuis la plateforme de l'utilisateur, puis de fixer les règles avant de lire les enregistrements.

## Partie 2 : chercher les réglages optimaux (règles fixées le 29 octobre 2026, après la partie 1, avant ce calcul)

### Demande de l'utilisateur

Puisqu'aucun setup ne passe avec ses réglages d'origine, trouver les réglages optimaux de l'order flow, pour un bot
qui trade en direct sur le challenge Bulenox à partir du tape, du DOM, du footprint et du VWAP.

**Le piège.** Avec 89 100 réglages essayés sur 76 séances, le meilleur aura toujours l'air excellent, même sur des
données sans aucune information. La recherche mesure donc ce que la même optimisation « trouve » dans du bruit, juge
les réglages choisis sur des mois qui n'ont pas servi au choix, et simule ce qu'aurait donné un bot réglé chaque mois
sur son seul passé.

### Les réglages essayés (grille complète, 89 100 configurations)

Gestion, commune aux trois familles (180 combinaisons) :

| Gène | Valeurs |
|---|---|
| objectif | 1 ; 1,5 ; 2 ; 3 fois le risque, ou aucun (sortie au temps ou au stop) |
| durée maximale | 10, 30 ou 60 minutes |
| stop minimum | 3, 6 ou 10 points (le stop de structure est éloigné jusque-là s'il est plus près) |
| fenêtre des signaux | 10 h - 15 h, ou 10 h - 12 h |
| sens | celui du setup, ou l'inverse (même risque, stop et objectif de l'autre côté) |

Signal :

| Famille | Gènes | Combinaisons |
|---|---|---|
| F1 repli absorbé (S1) | delta de contexte sur 15, 30 ou 60 min ; VWAP exigé ou non ; repli sur 3, 5 ou 10 min ; déséquilibre au-delà du quantile 5, 10, 20 ou 30 ; volume ≥ 0, 1 ou 1,5 fois la médiane des 30 min ; clôture dans la moitié favorable exigée ou non | 432 × 180 = 77 760 |
| F2 cassure ratée (S2) | niveaux de la veille, de la première heure, ou les deux ; agression à la cassure : aucune, ou au-delà du quantile 60, 75 ou 90 ; échec dans les 2, 5 ou 10 minutes | 36 × 180 = 6 480 |
| F3 volume d'arrêt (S3) | extrême de la séance, des 30 ou des 60 dernières minutes ; footprint au-delà du quantile 80, 90 ou 95 ; rejet d'au moins 0,5, 1 ou 2 points | 27 × 180 = 4 860 |

Le reste (mesures, seuils glissants des 5 séances d'avant, exécution, frais, R maximal de 0,12 %, une position à la
fois) est celui de la partie 1. Les réglages d'origine de S1, S2 et S3 font partie de la grille.

### Le jumeau de bruit (4 graines)

À partir de la 2e minute de chaque séance, chaque minute est retournée avec la probabilité 1/2 : ses mouvements par
rapport à la clôture précédente changent de signe (plus haut et plus bas échangés), achats et ventes agressifs sont
échangés, et le footprint aussi (ventes aux deux prix les plus bas ↔ achats aux deux prix les plus hauts). Les prix sont
enchaînés à partir de la vraie première minute. Le bruit garde la volatilité, le volume, la saisonnalité de la journée et
le lien entre le flux et le prix **dans la même minute**, mais détruit tout lien entre une minute et les suivantes :
ce que l'optimisation y trouve est du hasard.

### Sélection, coffre et réglage glissant (fixés maintenant)

1. **Exploration sur A seulement** (avril - juillet, 76 séances jouables). Score = t par séance sur A × min(1,
   trades ÷ 40). Éligible : au moins 40 trades sur A et gain net moyen > 0.
2. **Barrière du bruit**, par famille : le meilleur score éligible obtenu sur les 4 graines de bruit.
3. **Finalistes** : dans chaque famille, la meilleure configuration réelle si son score dépasse la barrière (0 à 3
   finalistes, m = leur nombre). Leur liste est écrite avec son empreinte avant la lecture de B.
4. **Coffre B** (3 août - 16 octobre, 52 séances), lu une seule fois : une finaliste est **retenue** si son t par séance
   sur B ≥ 1,645 (m = 1), 1,96 (m = 2) ou 2,13 (m = 3), son gain net moyen sur B > 0, au moins 20 trades sur B, et si
   elle bat 95 % des placebos de sens sur B. Limite : les réglages d'origine ont déjà été joués sur B dans la partie 1.
5. **Réglage glissant** (ce que ferait un bot réoptimisé chaque mois), sur les vraies données et sur les 4 bruits : au
   début de chaque mois de mai à octobre, on prend la configuration au meilleur score sur toutes les séances
   précédentes (depuis avril ; score = t par séance × min(1, trades ÷ (0,5 × séances)), gain net moyen > 0), et on la
   joue le mois suivant. Les mois joués sont tous hors de l'optimisation. Le réglage glissant est jugé **utile** si son t
   par séance hors échantillon (mai - 16 octobre) ≥ 1,65, avec un gain net positif, et s'il fait mieux que sur chacun des
   4 bruits.

**Ce que le bot FluxNQ utilisera** : une finaliste retenue s'il y en a une ; sinon, si le réglage glissant est utile, la
configuration qu'il choisit aujourd'hui (réoptimisée chaque mois) ; sinon, la meilleure configuration de tout
l'historique, **marquée « non validée »**, en virtuel par défaut. Le passage en réel reste le choix de l'utilisateur, avec
ce résultat sous les yeux.

### Résultats de la partie 2 (29 octobre 2026) : `resultats/partie2_exploration.txt`, `partie2_coffre.txt`, `partie2_glissant.txt`

Contrôle : avec les réglages d'origine, la machine redonne exactement les trades de la partie 1 (28, 69 et 583 trades :
mêmes séances, mêmes minutes, mêmes gains). Le bruit garde la volatilité d'une minute (13,58 points dans les deux) et le
lien entre le flux et le prix dans la même minute (corrélation 0,564 dans les deux).

**Exploration sur A : le bruit trouve mieux que les vraies données, dans les trois familles.**

| Famille | Meilleur score réel | Meilleur score sur bruit (4 graines) | Finaliste |
|---|---|---|---|
| F1 repli absorbé | 2,15 | 2,48 ; 1,88 ; 2,44 ; 2,09 | non |
| F2 cassure ratée | 1,64 | 1,34 ; 1,16 ; 1,15 ; 2,38 | non |
| F3 volume d'arrêt | 0,73 | 1,62 ; 1,93 ; 2,11 ; 1,14 | non |

**0 finaliste : le coffre n'a rien à juger.**

**Réglage glissant (le bot réoptimisé chaque mois sur son passé) : il perd.**

| | Hors échantillon (mai - 16 octobre, 112 séances) | t par séance |
|---|---|---|
| **Vraies données** | **−276 points (−552 $ par MNQ)**, 5 mois perdants sur 6 | **−1,77** |
| Bruit, graines 11 à 14 | −203, −257, −122, −165 points | −1,20 ; −0,74 ; −0,69 ; −1,06 |

Chaque mois, le réglage « optimal » du passé (score de 2,2 à 3,0 sur le passé) perd le mois suivant. **Décision fixée à
l'avance : réglage glissant pas utile.**

**Meilleure configuration sur tout l'historique** (descriptif, chiffres optimistes puisqu'elle est choisie sur ces
mêmes séances) : F2, cassure ratée des niveaux de la veille et de la première heure, **sans condition d'order flow**,
échec en 5 minutes, objectif 2 R, 60 minutes au plus, stop d'au moins 3 points, signaux jusqu'à 12 h : 104 trades,
+6,32 points par trade, t +2,45. C'est du niveau de ce que le bruit atteint (2,38 à 2,48 sur A seul), et ce n'est pas de
l'order flow.

### Ce qu'on retient de la partie 2

Chercher « les réglages optimaux » de l'order flow, c'est ici trouver le réglage qui a eu de la chance sur les mois
passés : il ne dure pas le mois suivant, et le hasard en produit d'aussi beaux. **Aucun réglage optimal de l'order flow
n'existe dans ces 7 mois de tape réel du NQ**, ni pour le repli absorbé, ni pour la cassure ratée, ni pour le volume
d'arrêt du footprint.

## Suite (29 octobre 2026)

Le bot FluxNQ (lecture en direct du tape, du DOM et du footprint, enregistrement, suivi des setups) n'est **pas
construit** : l'utilisateur a demandé à quoi servirait un bot si aucun réglage ne passe, et la réponse honnête est qu'en
réel il ne ferait que perdre plus vite. Seule pièce encore utile : un enregistreur du DOM (aucun ordre), pour tester un
jour le carnet profond, jamais disponible dans les données. Décision laissée à l'utilisateur.

## Partie 3 : vague quant (règles fixées le 29 octobre 2026, avant tout calcul de cette vague)

### Demande de l'utilisateur

Continuer : d'autres manières de construire un système order flow sur le NQ, fondées sur les formules quantitatives,
avec toutes les sources de données gratuites, sans s'arrêter si des milliers de réglages échouent ; l'utilisateur
connectera ensuite le bot en direct sur son challenge.

**Ce qui ne change pas** : la barre. Chercher « jusqu'à ce que ça passe » sans tenir compte du nombre d'essais
garantit de trouver un réglage chanceux, qui perd ensuite en direct. Chaque famille est donc jugée contre ce que la
même recherche trouve dans le bruit, sur des mois qui n'ont pas servi au choix.

### Sources gratuites (recherche du 29 octobre 2026)

Aucune source gratuite ne donne les transactions du NQ avec le côté agresseur : seulement des fournisseurs payants
(AlgoSeek, IQFeed, Kibot, Databento, CME DataMine) ou quelques jours d'historique (Tradovate, CME). Les substituts
gratuits déjà essayés (barres d'une minute, transactions du QQQ chez Alpaca, ticks de London Strategic Edge) ont été
refusés dans `filtre_h1/` : leur delta ne ressemble pas assez au vrai. Les sources de cette vague sont donc :
- le vrai tape du NQ déjà dans le projet (Databento, avril - 1er octobre 2026 ; export Rithmic du compte, 2 - 16 octobre) ;
- les barres d'une minute gratuites du NQ, 2011 - 2026 (`intraday/donnees/nasdaq100_1min.csv.gz` de la branche de
  recherche, complétées par `zone/robot/nq_1min.csv.gz`), pour la seule famille qui a été conçue pour des barres : le
  VPIN avec classification du volume par barres (BVC, Easley, López de Prado, O'Hara 2012).
- La source gratuite la plus riche reste **la plateforme de l'utilisateur** : « Export transactions NQ » peut exporter les
  transactions Rithmic des contrats passés (NQU6, NQM6, NQH6, NQZ5...) si Rithmic les garde. Ce sera le coffre suivant.

### Notations (à la clôture de la minute t, seulement ce qui est connu)

Δc_t = clôture_t − clôture_{t−1} ; σ1_t = écart-type des Δc des 60 dernières minutes de la séance ; **u_t = σ1_t × √30**
(mouvement typique de 30 minutes, environ 75 points) ; δ_t = achats − ventes agressifs ; Σδ_W = somme des δ des W
dernières minutes. « Quantile » = rang parmi les mêmes valeurs des 5 séances précédentes (minutes de 10 h à 16 h), sauf
mention. « Au croisement » = la condition est vraie à t et fausse à t − 1.

### Les familles (signaux de 10 h à 15 h 30 sauf mention)

| # | Famille (référence) | Signal | Sens de base | Combinaisons |
|---|---|---|---|---|
| G1 | **Lambda de Kyle** (Kyle 1985 ; Hasbrouck 2007) | λ = Σ Δc·δ ÷ Σ δ² sur les L dernières minutes (L = 30 ou 60) ; mouvement expliqué par le flux π = λ Σδ_W (W = 5, 15, 30). Type « résidu » : z = (c_t − c_{t−W} − π) ÷ (σ1 √W) ; type « flux informé » : z = π ÷ (σ1 √W). Au croisement de \|z\| ≥ k (k = 1 ; 1,5 ; 2) | signe du résidu, ou du flux | 36 |
| G2 | **VPIN** (Easley, López de Prado, O'Hara 2012), vrai côté agresseur | seaux de volume de 1/50 du volume médian des 5 séances d'avant ; VPIN = moyenne de \|achats − ventes\| ÷ volume sur les n derniers seaux (n = 10, 25, 50). Tous les quarts d'heure : régime haut (VPIN ≥ quantile 50, 75 ou 90) ou bas (≤ quantile 25 ou 50) | signe du flux de ces n seaux | 15 |
| G3 | **Élan du flux** | aux contrôles toutes les C minutes (C = 5, 15, 30) : Σδ_W (W = 15, 30, 60) au-delà du quantile q ou en deçà de 100 − q (q = 80, 90, 95) ; prix sur W : libre, d'accord avec le flux, ou en désaccord | signe du flux | 81 |
| G4 | **Flux de l'ouverture** | à 10 h, 10 h 30 ou 11 h : delta depuis 9 h 30, comparé aux 20 séances d'avant (signe seul, ou au-delà du quantile 70 ou 85) ; prix depuis l'ouverture : libre, d'accord, en désaccord | signe du flux | 27 |
| G5 | **Flux de fin de journée** (élan intrajournalier, Gao, Han, Li, Zhou 2018, version flux) | à 15 h ou 15 h 30 : delta du jour, des 60 dernières minutes, ou de la première demi-heure, comparé aux 20 séances d'avant (signe, quantile 70 ou 85) ; prix libre ou d'accord ; sortie à 15 h 59 | signe du flux | 36 |
| G6 | **Gros lots nets** (Databento) | flux net des transactions d'au moins S contrats (S = 10, 25, 50) sur W minutes (5, 15, 30), au croisement du quantile q ou 100 − q (q = 90, 95, 99) | signe du flux des gros lots | 27 |
| G7 | **Bandes de VWAP et flux** | clôture qui franchit VWAP ± k σ_V (σ_V = écart-type du prix pondéré par le volume depuis 9 h 30 ; k = 1 ; 1,5 ; 2) ; flux sur W (5, 15, 30) : en désaccord avec le franchissement (retour), d'accord (cassure), ou libre (retour, sans flux) | retour ou cassure | 27 |
| G8 | **Absorption quantifiée** | au croisement : \|Σδ_W\| ≥ quantile q de \|Σδ_W\| (q = 90, 95) et \|c_t − c_{t−W}\| ≤ k σ1 √W (k = 0,25 ; 0,5), W = 5, 15, 30 ; lieu : partout, près d'un extrême du jour (à moins de 0,5 u), près du VWAP (à moins de 0,5 u) | contre le flux absorbé | 36 |
| G2b | **VPIN par barres, 15 ans** (barres gratuites) | comme G2, avec achats = volume × Φ(Δc ÷ σΔ) (BVC ; σΔ = écart-type des Δc des 5 séances d'avant) | signe du flux estimé | 15 |

Ajout avant tout calcul (même jour, demande de l'utilisateur d'explorer les études publiées et les « écarts ») :

| # | Famille (référence) | Signal | Sens de base | Combinaisons |
|---|---|---|---|---|
| G9 | **Déséquilibre de la veille** (Chordia et Subrahmanyam 2004, JFE : le déséquilibre d'ordres d'un jour prédit le rendement du lendemain) | déséquilibre (achats − ventes) ÷ volume de toute la séance précédente, ou de sa dernière heure, comparé aux 20 séances d'avant (signe, quantile 70 ou 85) ; mouvement du prix de la veille : libre, d'accord, en désaccord. Entrée à l'ouverture de 9 h 31, sortie à 15 h 59, sans stop | signe du déséquilibre | 18 × 2 sens = 36 |

Écarté, avec la raison : écart ES/NQ en paires (déjà testé dans `paires/` : Sharpe −0,45 sur 2006 - 2026), avance de
l'ES sur le NQ à la minute (famille F7 de `scalping/`, rien), arbitrage NQ/QQQ (microsecondes, hors de portée d'un PC),
retournement du flux après la Fed (Boguth, Grégoire, Martineau 2019 : 4 annonces seulement dans le tape disponible).

**Gestion** (toutes sauf G5 et G9, 72 combinaisons) : durée 15, 30, 60 minutes ou jusqu'à 15 h 59 ; stop aucun, 0,5 u ou 1 u ;
objectif aucun, 1 u ou 2 u ; sens de base ou inverse. G5 : sortie à 15 h 59, stop aucun, 0,5 u ou 1 u, sens de base ou
inverse (6). Stops et objectifs arrondis au tick (stop vers la perte, objectif en s'éloignant). Exécution, frais et ordre
le plus défavorable : ceux de la partie 1. Une position à la fois. Soit **17 928 + 216 + 36 = 18 180** configurations sur le
vrai tape et **1 080** pour G2b.

**G2b au prix d'aujourd'hui** (comme `scalping/`) : gain d'un trade = sens × (sortie − entrée), avec le tick de
glissement de l'entrée et des sorties au marché, × (30 000 ÷ ouverture de la séance) − 1 point de commission.

### Bruit, sélection, coffre (fixés maintenant)

- **Bruit par signe, 8 graines** (comme la partie 2 ; les gros lots nets changent de signe avec la minute ; pour G2b, la
  minute retournée donne un BVC retourné).
- **Tape (G1 - G9)** : exploration sur A (avril - juillet). Score = t par séance × min(1, trades ÷ n_min), n_min = 40
  (25 pour G4, G5 et G9, qui tradent au plus une fois par jour). Éligible : au moins n_min trades et gain net moyen > 0.
  Barrière par famille = meilleur score éligible sur les 8 bruits. Finaliste = meilleure configuration réelle de la
  famille si elle dépasse la barrière.
- **G2b** : exploration 2012 - 2022 (2011 pour les seuils), même score avec n_min = 200, barrière sur 8 bruits ; coffre
  2023 - 28 octobre 2026.
- **Coffre, une seule fois pour toute la vague** (B pour le tape, 2023 - 2026 pour G2b) : m = nombre total de
  finalistes ; retenue si t par séance ≥ seuil de Bonferroni unilatéral à 5 % pour m, gain net moyen > 0, au moins 15
  trades (10 pour G4, G5 et G9 ; 100 pour G2b), et bat 95 % des placebos de sens.
- **Réglage glissant** (G1 - G9 ensemble), comme la partie 2, contre les 8 bruits.
- **Si une configuration est retenue**, elle devient le réglage du bot FluxNQ ; elle reste à confirmer sur les
  exports de l'utilisateur (contrats passés, puis l'avenir). Sinon, rien n'est construit pour le direct, et c'est dit.

### Résultats de la partie 3 (29 octobre 2026) : `resultats/partie3_exploration.txt`, `partie3_coffre.txt`, `partie3_glissant.txt`

Contrôles avant calcul (`test_quant.py`) : aucun regard vers le futur (6 coupures sur le tape, 592 920 signaux
identiques ; 22 367 sur les barres de 15 ans) ; gestion vérifiée sur des minutes fabriquées ; un signal de G1 (lambda,
z, croisement) et un de G9 (déséquilibre de la veille contre ses quantiles) revérifiés à la main.

**Exploration : aucune famille ne sort du bruit.**

| Famille | Meilleur score réel | Bruit : moyenne des 8 meilleurs (barrière = le plus haut) | Finaliste |
|---|---|---|---|
| G1 lambda de Kyle | 2,61 | 2,67 (3,07) | non |
| G2 VPIN (vrai tape) | 1,96 | 2,50 (2,91) | non |
| G3 élan du flux | 2,19 | 2,91 (3,67) | non |
| G4 flux de l'ouverture | 2,69 | 2,37 (2,91) | non |
| G5 flux de fin de journée | 1,71 | 1,93 (2,93) | non |
| G6 gros lots nets | 2,87 | 2,72 (3,14) | non |
| G7 bandes de VWAP et flux | 2,30 | 2,83 (3,67) | non |
| G8 absorption quantifiée | 1,93 | 2,90 (3,36) | non |
| G9 déséquilibre de la veille (Chordia-Subrahmanyam) | 1,67 | 1,76 (3,13) | non |
| G2b VPIN par barres, 2012 - 2022 (3 910 séances gratuites) | 1,33 | 1,39 (2,11) | non |

**0 finaliste : le coffre n'a rien à juger.** Sur les vraies données, le meilleur réglage de chaque famille fait au
mieux ce que fait en moyenne le meilleur réglage trouvé dans du bruit.

**Réglage glissant : −1 832 points (−3 663 $ par MNQ) hors échantillon, t −1,05**, dans la fourchette des 8 bruits
(de −3 990 $ à +4 498 $). Décision fixée à l'avance : pas utile. En mai, le réglage choisi avait un score de 4,83 sur
son passé (le genre de backtest qui « passe crème ») ; mai et juin ont gagné, puis juillet, août, septembre et octobre
ont tous perdu.

### Bilan de la journée

| Vague | Configurations | Retenues |
|---|---|---|
| Partie 1 : setups order flow classiques, stop sur la structure | 3 | 0 |
| Partie 2 : réglages optimaux de ces setups | 89 100 | 0 (réglage glissant −552 $ par MNQ) |
| Partie 3 : familles quant publiées + VPIN sur 15 ans | 19 260 | 0 (réglage glissant −3 663 $ par MNQ) |

Plus de 108 000 configurations order flow, toutes sur le vrai côté agresseur des transactions du NQ (ou, pour G2b,
sur 15 ans de barres gratuites) : aucune ne fait mieux que ce que la même recherche trouve dans du bruit. Des réglages
au beau backtest, il y en a des centaines (score > 2,5) ; le bruit en produit autant. En choisir un et le lancer en
direct revient à jouer à pile ou face en payant les frais.

**Ce qui changerait la donne : plus de vrai tape.** La seule source gratuite est la plateforme de l'utilisateur :
« Export transactions NQ » sur les contrats passés (NQU6, NQM6, NQH6, NQZ5...). Si Rithmic les fournit, toutes les vagues
se relancent telles quelles, avec ces mois-là comme nouveau coffre, jamais vu par aucune des 108 000 configurations.
