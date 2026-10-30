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

## Le bot FluxNQ (règles fixées le 29 octobre 2026, avant tout calcul de C1)

### Demande de l'utilisateur

Les contrats passés (NQU6, NQM6...) ne sont pas proposés par sa plateforme : pas d'historique de plus. Il demande le bot
order flow branché en direct, qui décide à partir de chaque transaction (prix, taille, acheteur ou vendeur), du DOM, du
footprint, du profil de volume, du VWAP et du delta, par confluences, et les quatre points proposés : plus de vrai
tape, le DOM, un essai en simulation avec une barre fixée d'avance, des ordres passifs.

### Ce que fait le bot

1. **Il lit** chaque transaction du NQ (prix, taille, côté agresseur), le DOM sur 10 niveaux de chaque côté (une photo
   par seconde), et construit en direct : barres d'une minute avec achats et ventes agressifs, footprint (volume par prix
   et par minute), profil de volume de la séance (POC, VAH, VAL) et de la veille, VWAP et bandes, delta, CVD, delta des
   30 dernières minutes, plus gros lots. Une lecture est envoyée sur Telegram toutes les 30 minutes.
2. **Il enregistre tout** (point 1 et 2) : transactions, DOM, minutes et footprint, chaque jour, dans
   `C:\Bot3en1\flux\AAAA-MM-JJ\`. Ce sont les données qui manquent pour tester le DOM et pour relancer les vagues.
3. **Il suit en simulation, chacune dans son propre carnet virtuel** (point 3), quatre règles :
   - **S1** et **S2** : exactement celles de la partie 1 ;
   - **S2b** : la meilleure configuration de tout l'historique (partie 2 : cassure ratée des niveaux de la veille et de
     la première heure, sans condition de flux, échec en 5 minutes, objectif 2 R, 60 minutes, stop d'au moins 3 points,
     signaux jusqu'à 12 h) ;
   - **C1, confluence** (ci-dessous), la seule à utiliser le DOM.
4. **Il mesure les ordres passifs** (point 4) : pour chaque entrée virtuelle, il note si un ordre limite posé au meilleur
   prix acheteur (achat ; vendeur pour une vente) au moment du signal aurait été rempli dans les 60 secondes (une
   transaction au moins un tick au-delà de la limite), et l'amélioration de prix obtenue.
5. **Il passe des ordres MNQ** seulement pour la règle choisie dans ses réglages (aucune par défaut), au marché, avec :
   taille, limite de perte du jour, nombre maximal de trades par jour, à plat à 15 h 59, fichier `STOP`. Il refuse de
   trader si une position MNQ qu'il n'a pas ouverte existe sur le compte (le bot 3 en 1 ne doit pas tourner sur le même
   compte).

### C1 : la confluence (achat décrit ; vente : l'exact symétrique)

À la clôture de la minute t, de 10 h à 15 h :
1. **Lieu** : au moins un niveau L parmi le plus bas de la veille, la VAL, le POC et la VAH du profil de la veille,
   et VWAP − 1 écart-type (σ_V, écart-type du prix pondéré par le volume depuis 9 h 30) est **testé par le haut** : plus
   bas_t ≤ L + 2 ticks, plus bas_t ≥ L − 8 ticks, clôture_t ≥ L, clôture_{t−1} > L + 2 ticks. Vente : plus haut de la
   veille, VAH, POC, VAL de la veille, VWAP + 1 σ_V, testé par le bas.
2. **Footprint** : ventes agressives aux deux prix les plus bas de la minute ≥ leur quantile 75 des 5 séances d'avant
   (les vendeurs ont frappé le niveau) ;
3. **Delta** de la minute < 0 (vendeurs agressifs) **alors que le prix a tenu** (condition 1 : clôture au-dessus du
   niveau) ;
4. **DOM** : somme des quantités affichées sur les 10 meilleurs prix acheteurs ≥ 1,2 × celle des 10 meilleurs prix
   vendeurs, à la clôture de la minute.

Stop : plus bas_t − 2 ticks, ramené à au moins 3 points sous l'entrée. Objectif 2 R, 30 minutes au plus, pas de trade si
R > 0,12 % du prix. Exécution, frais et ordre le plus défavorable : ceux de la partie 1.

**Profil de volume** : volume (achats + ventes) par prix de la séance ; POC = prix au plus fort volume (le plus bas en
cas d'égalité) ; zone de valeur : partant du POC, on ajoute un tick à la fois du côté (au-dessus ou au-dessous) qui a le
plus de volume (au-dessus en cas d'égalité) jusqu'à 70 % du volume ; VAL et VAH en sont les bornes.

**Descriptif, avant le direct** (`confluence.py`) : C1 sans la condition 4 (aucun DOM historique) sur les séances
Databento ; publié tel quel, sans aucun réglage.

### La barre pour passer en réel (fixée maintenant)

Pour chaque règle, sur ses **trades virtuels pris en direct** depuis l'installation du bot (jamais sur l'historique) :
au moins **40 trades**, gain net moyen > 0 et **t ≥ 2,24** (Bonferroni unilatéral à 5 % pour 4 règles). Une règle qui
franchit la barre peut être choisie pour les ordres réels ; avant, c'est un essai. Le choix reste celui de l'utilisateur.

### C1 sans DOM sur l'historique (29 octobre 2026, descriptif) : `resultats/confluence_sans_dom.txt`

Contrôle : aucun regard vers le futur (15 coupures). Sur 117 séances Databento avec profil de la veille et footprint :
218 trades, **−1,98 point par trade** (−864 $ par MNQ), t par séance −2,56, perdant sur A (−1,66) comme sur B
(−2,40), 26 % de gagnants, stop médian 4,5 points ; pas mieux qu'un sens tiré au hasard (59,5 % des placebos battus).
Sans le DOM, la confluence niveau + footprint + delta perd comme S3 : un stop de quelques points sous la mèche est
emporté par le bruit d'une minute. Reste à voir si le DOM change cela : seul l'essai en direct peut le dire.

**Données du direct** : le bot enregistre transactions, DOM, minutes et footprint qu'il passe des ordres ou non. Pour
construire et tester sur les données du challenge, il suffit de le lancer en lecture (aucune règle choisie pour les
ordres) et d'envoyer le dossier `C:\Bot3en1\flux` ; un premier test du DOM, aux règles fixées avant de lire les
enregistrements, demande 20 à 30 séances.

## Séances neuves du 19 au 27 octobre 2026 (export Rithmic de l'utilisateur, règles fixées avant le calcul)

Fichier : `donnees/transactions_NQZ6_19-29oct.csv` (« Export transactions NQ » sur NQZ6, fait le 29 octobre à 11 h 44,
heure de New York). Aucune de ces séances n'a servi à aucun calcul du projet.

- **Séances** : 19, 20, 21, 22, 23, 26 et 27 octobre (complètes, 390 minutes). Écartées : le 28 (61 minutes manquent),
  le 29 (séance en cours). Le 17 octobre manque dans toutes les sources : le 19, S2 et S2b ne tradent pas (pas de veille,
  donc pas de plus haut ni de plus bas de la veille) ; S1 garde ses seuils des 5 séances présentes d'avant.
- **Mesuré** : S1, S2 et S2b exactement comme le bot les trade (C1 demande le footprint par prix, absent de l'export) ;
  trades, résultat jour par jour, et contrôle que le moteur C# du bot donne les mêmes trades que le Python.
- **Point d'étape, aucune décision** : 7 séances. La barre pour le réel (40 trades en direct, t ≥ 2,24) ne change pas.

### Résultat du point d'étape (29 octobre 2026) : `resultats/point_19_27oct.txt`

| Règle (choisie avant le 17 octobre) | Trades | Gagnants | Points | $ par MNQ |
|---|---|---|---|---|
| S1 | 2 | — | +3,5 | +7 |
| S2 | 2 | 2 | +61,0 | +122 |
| **S2b** (meilleure des 89 100 configurations de la partie 2) | **6** | **5** | **+132,0** | **+264** |
| Partie 3 : meilleure configuration au 16 octobre (G6, gros lots) | 0 | — | — | l'export n'a pas la taille de chaque transaction |
| Partie 3 : meilleure sans G6 (G7, VWAP ± 2 σ et flux en désaccord) | 8 | 4 | −76,0 | −152 |

- S2b, trade par trade (heure de New York) : 20/10 10 h 02 achat −14,0 ; 20/10 10 h 30 vente +49,5 ; 21/10 10 h 00 vente
  +17,0 ; 21/10 10 h 51 vente +29,0 ; 23/10 10 h 31 vente +32,0 ; 27/10 10 h 03 vente +18,5. t par trade 2,55 sur 6 trades.
  Sur tout l'historique et ces séances : 111 trades, +6,83 points par trade.
- Le choix « sans G6 » a été décidé après avoir vu que l'export n'a pas les gros lots, avant de voir son résultat.
- Contrôle : le moteur C# du bot donne exactement les mêmes trades que le Python, séances neuves comprises (S1 30,
  S2 71, S2b 111, C1 218 ; 0 écart).
- **Lecture** : S2b tient sur les premières séances qu'elle n'avait jamais vues, G7 non. Six trades restent un petit
  échantillon (un ou deux trades de plus dans un sens ou dans l'autre changent beaucoup le total) ; la barre pour le
  réel (40 trades en direct) n'est pas franchie. S2b n'a pas de condition d'order flow : c'est une cassure ratée des
  niveaux de la veille et de la première heure.

### Détail de S2b (29 octobre 2026, descriptif) : `detail_s2b.py` → `resultats/detail_s2b.txt`, `resultats/trades_S2b.csv`

Contrôle : mêmes trades que la configuration 82358 de la partie 2. Le 19 octobre est exclu (veille absente), comme fixé
pour le point d'étape.

- 110 trades sur 134 séances (0,82 par séance) ; 45 % de gagnants à +34,4 points, perdants à −14,7 ; **+7,17 points par
  trade**. Stop médian 13,5 points (90 % sous 29). Sorties : stop 55 %, objectif 44 %.
- Avril −97 points, puis chaque mois positif (mai +84, juin +51, juillet +191, août +182, septembre +225, octobre +153).
- Plus longue série : 9 pertes de suite ; pire baisse −141,8 points ; pire journée −37,5 points.
- **3 MNQ** : risque médian 81 $ par trade (90 % sous 174 $), +43 $ par trade et +35 $ par séance en moyenne, pire journée
  −225 $, pire baisse −850 $ ; séances neuves +792 $.
- **Fragilité** : t 2,55 sur les 6 trades neufs ; avec le trade du 19 octobre (exclu, −30,5 points), il tomberait à 1,39.
  Le t historique (2,31) est gonflé : S2b a été choisie parmi 89 100 configurations sur ces mêmes séances.
- **Challenge Bulenox** (tirage des séances) : en 10 séances, 0 % de validation à 1, 2 ou 3 MNQ (le gain moyen est trop
  petit pour faire +3 100 $) ; en 60 séances à 3 MNQ, 21 à 24 % si l'avantage mesuré tient, 4 à 5 % s'il est divisé par 2 ;
  le compte n'est presque jamais perdu (0 à 5 %). S2b protège le compte mais avance lentement.

## S2b avec un stop élargi (question de l'utilisateur, règles fixées le 29 octobre 2026 avant tout calcul)

Le 20 octobre, le stop de S2b (12,75 points) a été touché de quelques points avant une hausse de 220 points.
L'utilisateur demande d'éloigner le stop de quelques points pour que le bruit de la minute l'atteigne moins souvent.

- **Variantes** : stop de S2b éloigné de **2, 4, 6 ou 8 points** de plus (au-delà de l'extrême de la cassure), avec
  - **(a)** objectif à 2 fois le **nouveau** risque (la règle reste « 2 R ») ;
  - **(b)** objectif **inchangé** (même distance qu'avec le stop d'origine).
  Mêmes entrées que S2b (le contrôle du risque maximal de 0,12 % reste fait sur le risque d'origine), mêmes frais, même
  exécution ; le 19 octobre reste exclu.
- **Choix sans tricher** : l'écart et la variante sont choisis sur **avril - juillet** seulement (meilleur t par séance,
  S2b d'origine comprise parmi les candidats).
- **Jugement** sur **3 août - 27 octobre** (dont les séances neuves), qui n'a pas servi au choix : la variante choisie
  remplace S2b dans le bot seulement si elle fait mieux que S2b d'origine sur cette période **à la fois** en total de
  points et en t par séance. Sinon S2b reste telle quelle. Publié quoi qu'il arrive, avec le taux de stops et le risque
  en dollars par trade.
- Limite : S2b elle-même a été choisie sur avril - 16 octobre ; seul l'écart du stop est jugé ici hors échantillon.

### Résultat (29 octobre 2026) : `resultats/stop_s2b.txt`

Contrôle : sans écart, on retrouve exactement les trades de S2b.

| Variante | Août - 27 oct. : total | t par séance | Part de stops | Risque médian par MNQ |
|---|---|---|---|---|
| **S2b d'origine** | **+559,8 pts** | **+3,01** | 55 % | 27 $ |
| Stop +2 pts, objectif 2 R | +424,8 | +2,24 | 61 % | 31 $ |
| Stop +2 pts, objectif inchangé | +533,0 | +2,82 | 53 % | 31 $ |
| Stop +4 pts, objectif 2 R | +382,5 | +1,96 | 61 % | 35 $ |
| **Stop +4 pts, objectif inchangé (choisi sur avril - juillet)** | +563,5 | +2,71 | 49 % | 35 $ |
| Stop +6 pts, objectif 2 R | +311,8 | +1,47 | 61 % | 39 $ |
| Stop +6 pts, objectif inchangé | +525,8 | +2,48 | 47 % | 39 $ |
| Stop +8 pts, objectif 2 R | +234,2 | +0,99 | 63 % | 43 $ |
| Stop +8 pts, objectif inchangé | +522,2 | +2,43 | 46 % | 43 $ |

**Décision fixée à l'avance : S2b reste telle quelle.** La variante choisie sur avril - juillet (stop +4 points,
objectif inchangé) fait presque le même total sur août - octobre (+563,5 contre +559,8 points) mais un t plus faible
(+2,71 contre +3,01), avec un risque plus grand par trade.
- Garder « objectif 2 R » en élargissant le stop éloigne aussi l'objectif : **plus** de trades finissent au stop
  (61 à 63 %) et le gain fond.
- Garder l'objectif et élargir le stop fait bien baisser la part de stops (55 % → 46 %), mais chaque perte coûte plus :
  au total, rien de gagné.
- Le trade du 20 octobre aurait été stoppé même avec 8 points de plus (le prix est descendu à 29 636,75 à 10 h 04) ;
  il fallait 9 points, ce qu'on ne sait qu'après coup.

## S2b sur 15 ans de barres gratuites (règles fixées le 29 octobre 2026, avant tout calcul)

S2b n'utilise que les prix (niveaux de la veille et de la première heure, clôtures d'une minute) : elle peut être jouée
sur les barres d'une minute gratuites du NQ (`intraday/donnees/nasdaq100_1min.csv.gz` de la branche de recherche).
**Période du test : 3 janvier 2011 - 31 mars 2026**, qu'aucun choix de S2b n'a vue (S2b a été choisie sur avril -
16 octobre 2026).

- **Règle** : S2b exactement (4 niveaux, cassure d'un tick, retour dans les 5 minutes, signaux de 10 h à 12 h, entrée à
  l'ouverture suivante avec un tick de glissement, stop derrière l'extrême, objectif 2 R, 60 minutes au plus, une
  position à la fois). Séances complètes (390 minutes) ; pas de trade le premier jour d'un nouveau contrat (la veille
  est sur l'ancien).
- **Au prix d'aujourd'hui** (le NQ valait 2 200 en 2011, 30 000 en 2026) : le stop minimal de 3 points devient
  3 × ouverture ÷ 30 000 (au moins un tick) ; le risque maximal reste 0,12 % du prix ; gain d'un trade = sens × (sortie −
  entrée) × 30 000 ÷ ouverture − 1 point de commission. Le tick de glissement reste un vrai tick, donc plus coûteux
  autrefois (prudent).
- **Décision (fixée maintenant)** : S2b est **confirmée sur 15 ans** si le t des gains quotidiens sur 2011 - mars 2026
  ≥ 2 et le gain net moyen > 0. Publié quoi qu'il arrive, année par année, avec 2011 - 2022 et 2023 - mars 2026 à part
  (les périodes où la zone a t +3,75 et +2,27).

### Résultat (29 octobre 2026) : `resultats/s2b_15ans.txt` — **S2b n'est PAS confirmée sur 15 ans**

| Période | Trades | Gagnants | Net moyen | Total ($ par MNQ) | t par séance |
|---|---|---|---|---|---|
| 2011 - 2022 | 2 259 | 29 % | −4,86 pts | −21 956 $ | −7,99 |
| 2023 - mars 2026 | 670 | 33 % | −1,22 pts | −1 635 $ | −1,17 |
| **Tout (2011 - mars 2026)** | **2 929** | **30 %** | **−4,03 pts** | **−23 591 $** | **−7,65** |

**Décision fixée à l'avance : S2b non confirmée** (t −7,65 ; seuil +2). Une seule année positive sur 16 (2024, +106 $).

Contrôles (descriptif) :
- Le même programme sur avril - 27 octobre 2026 retrouve un gain (114 trades, +3,66 points par trade) : le test n'est pas
  faussé. Mais ce gain est deux fois plus petit qu'avec les minutes faites depuis Databento (+7,17) : le résultat de S2b
  dépend de la façon exacte de construire les minutes, signe de fragilité.
- Le tick pesait 13 fois plus en 2011 (NQ à 2 300). Avec un glissement ramené au prix d'aujourd'hui, S2b perd encore
  (−2,18 points par trade, 2 années positives sur 16) ; même **sans aucun frais**, elle perd (−1,18 point par trade).

**Lecture.** Les 7 mois d'avril à octobre 2026, où S2b a été choisie parmi 89 100 configurations, sont une exception
dans 15 ans d'histoire. La bonne semaine du 20 au 27 octobre (6 trades) ne pèse rien face à 2 929 trades. Comme le
prévoyait la partie 2 (le bruit atteint les mêmes scores), le meilleur réglage de 7 mois était surtout chanceux.
**S2b ne doit pas trader en réel.** La zone de bruit (version d'origine) reste la seule stratégie du projet avec un
avantage sur 15 ans (t +3,75 sur 2011 - 2022, +2,27 sur 2023 - 2026).

## Partie 4 : les meilleures combinaisons de stratégies (règles fixées le 29 octobre 2026, avant tout calcul)

### Demande de l'utilisateur

Retracer toutes les stratégies et tous les réglages du projet, les classer, et trouver les combinaisons les plus
efficaces ensemble (« c'est l'ensemble des confluences et de plusieurs stratégies qui fait la rentabilité »), avec
plusieurs agents et une contre-revue indépendante (#ultrareview).

### Les stratégies combinables (`matrice.py` → `FLUX_CALCUL/matrice.pkl`)

Toutes celles dont le code du projet régénère les gains **quotidiens** sur le NQ de 2011 à 2026 (4 041 séances,
3 janvier 2011 - 25 septembre 2026), en $ pour 1 contrat micro au prix d'aujourd'hui, frais compris :
- **ZONE** : la zone de bruit, version d'origine (contrôles de 30 minutes) ;
- **G1 - G3** : l'élan hors zone (`scalping/partie_g.py`) ;
- **H1 - H16** : le banc des stratégies simples d'analyse technique, dont l'ORB 5 min (H1), la cassure de la veille (H5)
  et le Supertrend (H12) (`scalping/partie_h.py`) ;
- **F1 - F8** : les pistes inexplorées, dont les pivots (F3) (`scalping/partie_f.py`) ;
- **S2b** (`flux/s2b_15ans.py`).
Les 10 règles de la partie E (institutions et chercheurs) demandent des données de nuit absentes du cache : elles ne sont
pas dans cette vague (aucune n'avait été retenue). Les stratégies trouvées par l'inventaire des agents hors de ces
familles feront une vague suivante, avec ses propres règles.

### Les méthodes, en walk-forward (aucune décision ne voit l'année jouée)

Chaque année Y de 2014 à 2026, avec les seules séances de 2011 à Y − 1 :
- **M1, portefeuille des solides** : toutes les stratégies dont le t des gains quotidiens (jours sans trade compris) est
  ≥ 2 et qui sont positives au moins 2 années sur 3 ; 1 MNQ chacune ; aucune → pas de trade.
- **M2, meilleure combinaison** : on part de la stratégie au meilleur t ; on ajoute, une à une, celle qui augmente le plus
  le t de la somme ; on s'arrête quand plus rien ne l'augmente, ou à 4 stratégies ; 1 MNQ chacune.
- **Témoins fixes** (sans choix) : ZONE seule ; toutes les stratégies à 1 MNQ chacune.
La combinaison choisie est jouée l'année Y. Les années jouées (2014 - 25 septembre 2026) forment la série hors échantillon.

### Contrôle du hasard

Les mêmes méthodes sont refaites 200 fois sur des stratégies **sans avantage** : toutes les séries sont décalées
ensemble (permutation circulaire) d'un nombre de séances tiré au hasard entre 252 et n − 252 (au moins un an), ce qui
garde leurs corrélations, **puis chacune est recentrée sur zéro** (sa moyenne de 2011 - 2026 retirée). Ce que M1 et M2 « gagnent » alors
hors échantillon mesure ce que la sélection seule fabrique.

### Décision (fixée maintenant)

Une méthode est **retenue** si, hors échantillon (2014 - 2026) :
1. t des gains quotidiens ≥ 2 ;
2. t plus grand que celui de ZONE seule sur les mêmes séances ;
3. au moins 9 années positives sur 13 ;
4. au-dessus du 95e centile de ses 200 tirages sans avantage.
Publié quoi qu'il arrive, avec les stratégies choisies chaque année. Pour une méthode retenue : challenge Bulenox
(descriptif), comparé à ZONE seule à risque quotidien égal.

### Contre-revue

Avant d'être publié comme « retenu », le résultat est relu par deux agents indépendants : l'un vérifie le code (regard
vers le futur, alignement des dates, recalcul indépendant), l'autre cherche à démolir la conclusion. On ne conclut que
s'ils sont d'accord.

### Résultats de la partie 4 (29 octobre 2026) : `resultats/combinaisons.txt`, `inventaire/`

**Inventaire** (agents d'inventaire, `inventaire/branche_recherche.md`, `inventaire/autres_branches.md`,
`inventaire/flux.md`) : environ 80 lignes sur la branche de recherche et 160 sur les autres branches (environ
190 stratégies et variantes, 21 configurations successives du bot 3 en 1), plus les machines (environ 2,5 millions de
configurations au total). Avec une preuve hors échantillon positive : la zone de bruit d'origine (la plus solide), le
RSI(2) de Connors (coffre t 1,95 ; **il garde la nuit et le week-end, interdit chez Bulenox**), puis des pistes faibles
(renfort de la zone : fait perdre le challenge Lucid ; or, cassure de Londres : coffre t 1,49, ajoutée à la zone elle
fait baisser la validation Lucid de 52 % à 42 % ; cassure de la veille, Supertrend, pivots : liés à la zone à 0,4 - 0,5).

**Combinaisons, walk-forward 2014 - 25 septembre 2026** (3 276 séances, $ par MNQ au prix d'aujourd'hui) :

| Méthode | t | Années positives | Pire baisse |
|---|---|---|---|
| **ZONE seule (témoin fixe)** | **+3,88** | **12 / 13** | **−6 338 $** |
| M1, portefeuille des solides | +2,14 | 9 / 13 | −20 770 $ |
| M2, meilleure combinaison | +0,54 | 8 / 13 | −34 602 $ |
| Toutes, 1 MNQ chacune | +0,73 | 8 / 13 | −237 057 $ |

**Décision fixée à l'avance : aucune méthode retenue** (M1 : t inférieur à celui de ZONE seule ; M2 : échoue à 3 critères).

**Contre-revue (#ultrareview), deux agents indépendants, d'accord sur la conclusion :**
- **Vérification du code** : chiffres reproduits exactement avec un code indépendant (ZONE +3,8825 ; M1 +2,142 ; M2 +0,543 ;
  mêmes choix chaque année) ; aucune décision ne voit l'année jouée ; la série ZONE est exactement la zone d'origine
  (identique, à 0,0001 $ près, aux 3 465 trades vérifiés de `filtre_h1/trades_zone.csv`). **Défaut relevé** : le contrôle
  sans avantage, recentré sur toute la période, est trop indulgent (médianes −0,62 et −2,99 au lieu de 0) ; avec des
  contrôles sans ce biais, le 95e centile est +1,4 à +1,6 pour M1 et +1,6 à +2,3 pour M2 : M2 ne bat pas le hasard. La
  décision ne change pas.
- **Avocat du diable** : pondération par le risque, zone + une stratégie décorrélée, zone + la meilleure du passé, en
  walk-forward : aucune ne bat ZONE seule ni en t ni en pire baisse (la meilleure : +3,08). Raison : toutes les
  stratégies positives sont de l'élan intraday sur le même NQ, liées à la zone à 0,41 - 0,49 ; les peu liées ont un t
  sous 1,5.

**Réserves écrites par les relecteurs :**
- ZONE seule est un témoin choisi après coup : classée par son passé, elle n'était que 2e à 6e de 2014 à 2018 ; la
  « meilleure stratégie seule » choisie en walk-forward fait t +2,43. Sans 2018, le t de ZONE sur 2014 - 2026 tombe à 3,01.
- **Depuis la publication de la zone (juin 2024)**, son avantage est plus faible : t +1,03, +14,2 $ par séance et par MNQ
  (contre +20,8 $ sur 2014 - 2026), avec la pire baisse de son histoire (−6 338 $ par MNQ, 21 avril 2025 - 2 février 2026).
- **Correction de « S2b sur 15 ans »** : les −4,03 points par trade (t −7,65) exagèrent la perte, car le tick de 2011 pèse
  autant que le glissement, le stop et l'objectif réunis (environ 0,5 R). Version juste (barres remises au prix
  d'aujourd'hui, tick et frais d'aujourd'hui), 2011 - 2025 : **−1,50 point par trade, t −3,04, 3 années positives sur 15** ;
  sans aucun coût : −0,33 point par trade (t −0,64). S2b n'a **aucun avantage brut** sur 15 ans ; aucune règle simple de
  régime tirée de 2026 ne la sauve (7 règles, toutes négatives sur 2011 - 2025). La conclusion ne change pas : pas de
  S2b en réel.

**Ce qu'on retient.** Rien dans le projet ne bat la zone de bruit d'origine, seule. Pour le challenge Bulenox, les
relecteurs estiment une validation autour d'une chance sur deux (68 % à 1 MNQ sans limite de temps si tout l'avantage
historique tient ; environ 50 % à toutes les tailles au niveau observé depuis juin 2024 ; 30 à 42 % sans aucun avantage).

## Partie 5 : finir le tournoi n°5 (29 octobre 2026, règles fixées le 30 septembre 2026, jamais calculées)

L'utilisateur demande de continuer à chercher des pistes nouvelles, fondées sur les études publiées. L'inventaire
(partie 4) montre que le tournoi n°5 de la branche de recherche (`tournoi5/`) a fixé le 30 septembre 2026, **avant tout
calcul**, des règles sur des rendez-vous institutionnels documentés, et figé son code le même jour ; ses données sont
arrivées le 1er octobre, mais seules les familles B (fin de séance, 5 marchés) et C (rapport EIA) ont été calculées
(0 sur 6). **Les familles A, D et E n'ont jamais été calculées.** Elles le sont ici, avec le code et les critères du
30 septembre, sans rien changer :
- **A1 / A2** : panier des 6 devises (6E, 6B, 6J, 6A, 6C, 6S) une heure avant (vente) / après (achat) le fixing de 16 h
  à Londres (Krohn, Mueller, Whelan, Journal of Finance 2024) ;
- **D1** : bitcoin CME, à 15 h 30 dans le sens de 9 h 30 - 10 h, jusqu'à 16 h (Shen, Urquhart, Wang 2022) ;
- **E1 / E2** : ZN (10 ans), vente de 9 h à 13 h les jours d'adjudication du Trésor, achat de 13 h à 15 h (Lou, Yan,
  Zhang 2013).
Critères (écrits le 30 septembre) : t ≥ 2 sur 2011 - 2022 (bitcoin 2018 - 2022) en rendements quotidiens nets ; battre
les autres heures (A), le bruit (D) ou 95 % des tirages de jours sans adjudication (E) ; puis coffre 2023 - 2026 : t ≥
seuil de Bonferroni et au moins 3 années positives sur 4.

### Résultats de la partie 5 (29 octobre 2026) : `resultats/tournoi5_exploration_ADE.csv`

`PYTHONPATH=../tournoi python3 explorer5.py A D E` dans `tournoi5/`, code du 30 septembre inchangé :

| Famille | t 2011 - 2022 (net) | 1re / 2e moitié | Contrôle | Verdict |
|---|---|---|---|---|
| A1 dollar avant le fixing | −6,31 | −3,74 / −5,20 | autres heures : au mieux −5,91 | éliminée |
| A2 dollar après le fixing | −8,01 | −4,21 / −7,21 | autres heures : au mieux −6,54 | éliminée |
| E1 ZN avant adjudication | −4,89 | −4,36 / −2,69 | jours sans adjudication : p95 −5,22 | éliminée |
| E2 ZN après adjudication | −5,17 | −1,39 / −6,54 | jours sans adjudication : p95 −7,71 | éliminée |
| D1 bitcoin CME | non calculable | — | — | minutes manquantes non gérées par le code du 30 septembre (NaN) ; le bitcoin intraday avait déjà été rejeté par la machine B2 |

**0 survivant, le coffre n'a rien à juger.** Avant frais, les heures du fixing et des adjudications ne font pas mieux que
les autres heures : après le coût d'un contrat standard (1 tick + 2,50 $ par ordre), tout est négatif.

**Bilan des recherches à ce jour** : environ 2,5 millions de configurations et toutes les familles publiées qu'on a pu
tester (tendance, retour à la moyenne, order flow, régimes, apprentissage, nuit, paires, rendez-vous institutionnels) :
la seule stratégie intraday compatible avec Bulenox qui gagne sur 15 ans reste la zone de bruit d'origine. Ce qui n'a
jamais été testé, faute de données : le DOM (enregistré par FluxNQ depuis son installation).

## Partie 6 : améliorer S2b avec l'order flow (règles fixées le 29 octobre 2026, avant tout calcul)

L'utilisateur lancera S2b et demande ce qui pourrait l'améliorer avec l'order flow. On ajoute à S2b **un seul filtre de
flux à la fois**, mesuré dans le vrai tape (achats et ventes agressifs de chaque minute) ; un signal refusé par le
filtre ne bloque pas les suivants. Pour un signal de vente (cassure ratée d'un niveau par le haut ; l'achat est
symétrique), avec b la minute de la cassure et f la minute du retour (signal) :

| Filtre | Le trade est pris seulement si… | Idée |
|---|---|---|
| **FA** (= S2) | déséquilibre de la minute b ≥ son quantile 75 des 5 séances d'avant | de vrais acheteurs ont attaqué le niveau |
| **FB** | delta de la minute f < 0 | les vendeurs prennent la main au retour |
| **FC** | somme des delta de b à f > 0 | les acheteurs ont poussé sans faire avancer le prix : ils sont piégés |
| **FD** | delta des 30 dernières minutes < 0 à f | le flux de fond va dans le sens du trade |
| **FE** | volume de la minute b ≥ 1,5 fois la médiane des 30 minutes d'avant | la cassure a attiré du monde, donc des piégés |

- **Données** : tape Databento (1er avril - 1er octobre) et exports Rithmic (2 - 16 octobre, 19 - 27 octobre) ; le
  19 octobre reste exclu.
- **Choix** sur **A** (avril - juillet) : le meilleur t par séance parmi S2b seule et S2b + chaque filtre.
- **Jugement** sur **B** (3 août - 27 octobre), qui n'a pas servi au choix : le filtre choisi est **conseillé** s'il fait
  mieux que S2b seule sur B **à la fois** en total de points et en t par séance, avec au moins 20 trades sur B.
- **Descriptif** : FE n'utilise que le volume, présent dans les barres gratuites ; il est aussi mesuré sur 2011 - 2025.
- Limite : S2b a été choisie sur avril - 16 octobre ; seul le filtre est jugé hors échantillon.

### Résultats de la partie 6 (29 octobre 2026) : `resultats/of_s2b.txt`

Contrôle : sans filtre, on retrouve exactement les trades de S2b.

| Filtre | A (avril - juillet) : trades, net moyen, t | B (3 août - 27 octobre) : trades, net moyen, t, total |
|---|---|---|
| **aucun (S2b)** | 66, +3,47, +1,15 | **44, +12,72, +3,01, +559,8 pts** |
| FA agression à la cassure (= S2) | 35, −0,50, −0,13 | 22, +19,93, +2,66, +438,5 |
| FB vendeurs au retour | 25, +3,73, +0,64 | 20, +21,39, +2,50, +427,8 |
| FC acheteurs piégés (delta b → f) | 54, +3,31, +1,02 | 33, +9,30, +2,23, +307,0 |
| FD flux de fond (delta 30 min) | 10, +8,90, +0,75 | 13, +9,46, +1,20, +123,0 |
| **FE volume de la cassure (choisi sur A)** | 21, +9,77, **+1,53** | 19, +17,17, +2,05, +326,2 |

**Décision fixée à l'avance : aucun filtre conseillé, S2b reste telle quelle.** FE, choisi sur A, gagne plus par trade
sur B mais prend deux fois moins de trades : total et t plus faibles que S2b seule. Descriptif, 2011 - 2025 (barres
gratuites, même convention que « S2b sur 15 ans ») : S2b seule −4,06 points par trade (1 année positive sur 15),
S2b + FE −4,51 (2 sur 15) : le filtre de volume ne corrige pas S2b sur la durée.

## Partie 7 : suivre les positions des géants (rapport COT de la CFTC) — règles fixées le 29 octobre 2026, avant toute donnée

### Demande de l'utilisateur

Suivre les flux et les mouvements des fonds, des institutions et des banques, et en tirer des stratégies.

### Pourquoi le COT

Le projet a déjà testé les traces indirectes des institutions qu'on peut voir avec des données publiques (gamma des
teneurs de marché, DIX, jours de Fed, rééquilibrages de fin de mois, clôture, ETF à levier, fixings, adjudications,
gros lots du tape) : rien n'a tenu. La seule source **directe** jamais utilisée est le rapport officiel de la CFTC
« Traders in Financial Futures » (futures seuls), chaque semaine depuis juin 2006 : positions acheteuses et vendeuses
sur le contrat **E-mini Nasdaq-100** des **gestionnaires d'actifs** (fonds, assureurs, fonds de pension), des **fonds à
levier** (hedge funds, CTA), et des **banques et teneurs de marché** (dealers), en pourcentage des positions ouvertes.

### Données

Fichiers officiels de la CFTC (`fin_fut_txt_2006_2016.zip`, puis `fut_fin_txt_AAAA.zip`), lignes du marché « NASDAQ »
« MINI » (pas « MICRO ») de la bourse de Chicago. Positions du mardi, publiées le vendredi à 15 h 30 : un rapport ne sert
qu'à partir de la **première séance qui suit sa publication** (mardi + 3 jours, puis la séance suivante).

### Les cinq hypothèses (biais de la semaine, valable jusqu'au rapport suivant)

| # | Règle | Idée |
|---|---|---|
| G1 | sens de la variation sur 4 semaines de la position nette des gestionnaires (÷ positions ouvertes) | suivre l'argent lent des institutions |
| G2 | sens de la variation sur 4 semaines de la position nette des fonds à levier | suivre les hedge funds et les CTA |
| G3 | contre les fonds à levier quand leur position nette est extrême (z sur 52 semaines au-delà de ± 1,5) | foule trop chargée |
| G4 | sens de la variation sur 4 semaines de la position nette des banques et teneurs de marché | suivre les dealers |
| G5 | G1 et G2 d'accord : dans leur sens ; sinon pas de trade | consensus des géants |

**Exécution compatible Bulenox** : chaque séance où le biais existe, position dans son sens de l'ouverture de 9 h 35 à
la clôture de 15 h 55 (une par jour, sans stop) ; gain au prix d'aujourd'hui comme `scalping/` (sens × (clôture 15 h 55 −
ouverture 9 h 35) × 2 $ × 30 900 ÷ ouverture de 9 h 30 − 3 $ par MNQ). Descriptif : la même chose de clôture à clôture
(avec la nuit), pour information seulement.

### Tri (fixé maintenant)

- **Exploration 2011 - 2018** : t des gains quotidiens (jours sans trade compris) ≥ 2, **et** mieux que 95 % de 1 000
  placebos où la série des signaux hebdomadaires est décalée d'un nombre de semaines tiré au hasard (au moins 8).
- **Coffre 2019 - 2026**, ouvert une fois : t ≥ seuil de Bonferroni unilatéral à 5 % pour le nombre de finalistes, gain
  moyen > 0, au moins 5 années positives sur 8. Publié quoi qu'il arrive.

### Résultats de la partie 7 (29 octobre 2026) : `resultats/cot.txt`

Données récupérées par un robot GitHub Actions (`.github/workflows/donnees-cot.yml`, `telecharger_cot.py`) :
1 063 rapports hebdomadaires du 13 juin 2006 au 20 octobre 2026 (« NASDAQ-100 STOCK INDEX (MINI) » puis « NASDAQ MINI »).

| Hypothèse | Exploration 2011 - 2018, t | 95e centile des placebos | Verdict |
|---|---|---|---|
| G1 suivre les gestionnaires d'actifs | −0,78 | +1,30 | éliminée |
| G2 suivre les fonds à levier | −0,42 | +1,13 | éliminée |
| G3 contre les fonds à levier trop chargés | +1,33 | +1,39 | éliminée |
| G4 suivre les banques et teneurs de marché | +0,67 | +1,07 | éliminée |
| G5 consensus gestionnaires + fonds à levier | −0,64 | +1,27 | éliminée |

**0 finaliste : le coffre 2019 - 2026 n'a rien à juger.** Les positions hebdomadaires des géants publiées par la CFTC ne
donnent pas le sens de la séance du NQ. La plus proche (G3, contre les fonds à levier quand leur position est extrême)
reste dans ce que donnent des signaux décalés au hasard.

## Partie 8 : radar des marchés et suivi en direct (29 - 30 octobre 2026)

Tout est dans `radar/README.md`. Le radar collecte chaque soir plus de 150 séries et des sources peu utilisées : FINRA,
Wikipédia, FRED, incertitude, AAII, options du CBOE, résultats. Il a scanné environ 27 millions de règles et 98 modèles
d'apprentissage sur le NQ, selon un protocole fixé avant le calcul.

**Une seule règle a passé la confirmation**, puis elle a échoué au coffre 2023 - 2026 (t 0,78) : acheter à 13 h 30
quand le NQ est en haut de son range, et garder 2 heures. **Aucune stratégie n'est donc constituée.**

`flux/veille.py` suit en direct, sans argent, depuis le 30 octobre 2026 :
- S2b, ORB, cassure de la veille, Supertrend et pivots ;
- la règle du radar ;
- la zone d'origine, comme référence.

Le workflow `radar.yml` fait tourner la collecte, ce suivi et le rapport du soir (`radar/RAPPORT.md`, Telegram).

## Partie 9 : vague order flow figée le 30 octobre 2026 (tape, premier niveau, DOM à 10 niveaux), avant tout calcul

Cette vague est figée **avant** d'avoir vu la séance du 30 octobre 2026 enregistrée par FluxNQ, et avant tout calcul
sur l'historique. Le code est `flux/of_fige.py`. Rien n'y sera changé après coup.

### Règles communes
- **Données.**
  - L'historique est la seconde de Databento (avril - octobre 2026, 127 séances) : dernier prix, plus haut et plus bas
    de la seconde, volumes acheteurs et vendeurs agresseurs, nombre de transactions, meilleur prix et quantité à l'achat
    et à la vente.
  - Pour les séances de FluxNQ, ces mêmes secondes sont reconstruites à partir de `tape.csv` et du premier niveau de
    `dom.csv`, plus les sommes des 10 niveaux de chaque côté.
- **Échelle.** A est la moyenne des ranges des 30 dernières minutes terminées, avec un plancher de 2 points.
- **Entrées.** De 10 h à 15 h 30, sauf la règle T7. Une seule position à la fois par règle, au plus 4 trades par jour.
- **Exécution et frais.**
  - L'entrée se fait au dernier prix de la seconde du signal, plus 1 tick contre soi.
  - Le stop sort au stop, moins 1 tick. L'objectif sort au prix exact.
  - La sortie à l'heure limite, ou à 15 h 55, se fait au dernier prix, moins 1 tick.
  - Si le stop et l'objectif sont touchés dans la même seconde, c'est le stop qui compte.
  - Commission de 2 $ par aller-retour ; gains en $ par MNQ.
- **Historique.** Une règle passe si t ≥ 2,45 (Bonferroni unilatéral à 5 % pour 7 règles) avec au moins 30 trades.

### Règles sur le tape et le premier niveau (testables sur les 127 séances)

| Règle | Signal | Sens | Stop / objectif / durée |
|---|---|---|---|
| T1 balayage | dans une seconde : range ≥ 2 points, ≥ 80 % du volume du même côté, volume ≥ 5 fois la moyenne par seconde de la séance (au moins 50 contrats), prix ≥ 1 point plus loin que la seconde d'avant dans ce sens | suivre | 1,5 A / 3 A / 15 min |
| T2 épuisement | un balayage (T1) fait le plus haut (plus bas) des 60 dernières minutes, puis, dans les 30 s, le prix repasse sous (au-dessus de) son prix d'avant le balayage | contre | 1 tick au-delà de l'extrême du balayage / 2 R / 30 min |
| T3 iceberg | sur 30 s, le meilleur achat ne bouge pas, le prix ne passe jamais dessous, et les ventes exécutées ≥ 100 contrats et ≥ 4 fois la quantité affichée en moyenne (vendeur caché au meilleur prix de vente : symétrique) | avec l'acheteur (le vendeur) caché | niveau − max(1 point ; 0,5 A) / 2 R / 20 min |
| T4 VPIN | paquets de volume (1/50 du volume moyen des 5 séances d'avant) ; VPIN = moyenne de \|achats − ventes\| / paquet sur 50 paquets ; signal à la fin d'un paquet si VPIN > son 90e centile des 5 séances d'avant | sens des 10 derniers paquets | 2 A / 4 A / 30 min |
| T5 rafale | transactions des 10 dernières secondes ≥ 4 fois leur moyenne des 10 minutes d'avant, ≥ 60 % du volume du même côté, prix ≥ 0,5 A plus loin dans ce sens | suivre | 1,5 A / 3 A / 15 min |
| T6 absorption | delta des 5 dernières minutes ≥ 2 fois sa moyenne absolue de la séance, mais le prix a bougé de moins de 0,25 A dans son sens | contre le delta | 1,5 A / 3 A / 30 min |
| T7 après-midi + flux | à 13 h 30, le NQ est dans les 14 % du haut de son range du jour (règle R1 du radar) et le delta cumulé depuis 9 h 30 est positif | achat | sortie à 15 h 30 |

### Règles sur le DOM à 10 niveaux (jugées seulement sur les séances de FluxNQ)

| Règle | Signal | Sens | Stop / objectif / durée |
|---|---|---|---|
| D1 déséquilibre | (somme des achats − somme des ventes) / total des 10 niveaux ≥ 0,30 pendant 30 s de suite, et delta des 30 s ≥ 0 (symétrique à −0,30) | côté le plus chargé | 1,5 A / 3 A / 15 min |
| D2 retrait | la somme des 10 niveaux de vente tombe à 60 % ou moins de sa moyenne des 60 s finissant 5 s plus tôt, pendant que celle des achats reste à 90 % ou plus (symétrique) | côté qui ne recule pas | 1 A / 2 A / 10 min |
| D3 rebond sur un mur | un niveau des 10 achats ≥ 5 fois la quantité médiane des 20 niveaux, présent au même prix depuis 30 s, et le meilleur achat à 2 ticks ou moins de lui (symétrique côté vente) | achat au-dessus d'un mur d'achats (vente sous un mur de ventes) | 2 ticks au-delà du mur / 2 R / 10 min |
| D4 mur cassé | un mur de ventes (comme D3, présent depuis 30 s) est traversé d'au moins 1 tick (symétrique) | suivre la cassure | 0,5 A en deçà du mur / 2 R / 15 min |

### Jugement
- **Les 7 règles du tape** sont jugées sur les 127 séances d'historique, puis suivies sur les séances de FluxNQ.
- **Les 11 règles** sont jouées telles quelles sur chaque séance que FluxNQ enregistre, à commencer par celle du
  30 octobre 2026.
- **Une seule séance ne prouve rien.** Une règle ne sera dite « qui marche » qu'après au moins 40 trades sur les séances
  de FluxNQ avec t ≥ 2,64 (Bonferroni pour 11).

### Résultats sur l'historique (131 séances de Databento, avril - octobre 2026)

Le détail est dans `resultats/partie9/historique.md`.

| Règle | Trades | Moyenne | t | Verdict |
|---|---|---|---|---|
| T1 balayage | 522 | −0,2 $ | −0,06 | échoue |
| T2 épuisement | 367 | −1,7 $ | −0,88 | échoue |
| T3 iceberg | 0 | — | — | jamais déclenchée (voir plus bas) |
| T4 VPIN | 132 | −9,4 $ | −1,13 | échoue |
| T5 rafale | 55 | −13,6 $ | −2,38 | échoue |
| T6 absorption | 119 | −10,0 $ | −1,03 | échoue |
| T7 après-midi + flux | 23 | +20,2 $ | +0,54 | échoue (trop peu de trades pour conclure) |

- **T3 ne se déclenche jamais, et ce n'est pas un défaut du code.** Sur ces séances, le meilleur prix d'achat ne
  reste jamais plus de 11 secondes au même niveau, alors que la règle demande 30 secondes.
- **Les quatre règles du DOM restent à juger.** Elles le seront sur les séances de FluxNQ, à commencer par celle du
  30 octobre 2026.
- **Un détail de calcul a été corrigé avant d'avoir la séance du 30 octobre.** Les stops et les objectifs exprimés en
  multiples de A sont arrondis au tick, du côté prudent. Le tableau ci-dessus est calculé après cette correction.

## Partie 10 : scan order flow façon radar (fixé le 30 octobre 2026 à 9 h 55 New York, avant tout calcul et avant la séance du jour)

Le code est `flux/of_scan.py`. Il applique la méthode du radar (règles à une ou deux conditions, placebos) à des
variables **d'order flow seulement**, sur les 131 séances de la seconde de Databento (avril - octobre 2026).

### Données et variables
- **Décisions.** Toutes les 15 minutes, de 9 h 45 à 15 h 30, regroupées en 3 fenêtres :
  - matin, de 9 h 45 à 11 h 30 ;
  - mi-journée, de 11 h 45 à 13 h 30 ;
  - après-midi, de 13 h 45 à 15 h 30.
- **Trades.** Entrée à l'ouverture de la minute de décision ; sortie 15, 30 ou 60 minutes plus tard (au plus tard à
  15 h 59). Frais de 3 $ par aller-retour et par MNQ.
- **Échelle.** a = range moyen des minutes de la séance jusque-là, avec un plancher de 1 point.
- **Variables**, toutes connues à la décision :

  | Groupe | Variables |
  |---|---|
  | Prix | mouvement depuis l'ouverture, sur 5, 15, 30 et 60 minutes (÷ a) ; place dans le range du jour ; range du jour ÷ a ; écart au VWAP et au POC de la séance (÷ a) ; écart d'ouverture |
  | Delta | (achats − ventes) ÷ volume sur 5, 15, 30 et 60 minutes et depuis l'ouverture ; mouvement de 15 minutes par unité de delta (absorption) |
  | Intensité | transactions et volume des 5 dernières minutes ÷ leur moyenne de la séance |
  | Carnet (premier niveau) | déséquilibre moyen (quantité à l'achat − à la vente) ÷ total, sur 5 et sur 15 minutes |
  | Gros lots (20 contrats et plus) | volume signé ÷ volume, sur 15 minutes ; nombre sur 30 minutes ÷ sa moyenne de la séance |
  | Footprint | minutes à déséquilibres empilés (au moins 3 prix de suite où les achats font au moins 3 fois les ventes), moins celles côté vente, sur 15 minutes |
  | Calendrier | jour de la semaine |

### Règles et jugement
- **Conditions et règles.** Mêmes 7 tranches par variable qu'au radar ; une ou deux conditions × fenêtre × durée ×
  sens.
- **Exploration** du 1er avril au 15 juillet 2026. Une famille (variables, fenêtre) garde sa meilleure règle si elle a
  au moins 60 trades et t ≥ 3. Les 2 000 meilleures familles passent en confirmation.
- **Confirmation** du 16 juillet au 1er octobre 2026 : au moins 30 trades, gain moyen positif, et t ≥ le 95e centile
  du meilleur t de 20 placebos (variables décalées de séances entières), avec un plancher de 3.
- **Coffre : l'avenir.**
  - Les survivantes sont figées et jouées sur les séances de FluxNQ, à commencer par celle du 30 octobre 2026.
  - S'il n'y a pas de survivante, ce sont les 5 meilleures familles de confirmation à t ≥ 2.
  - Une règle n'est dite « qui marche » qu'après 40 trades sur ces séances, avec t ≥ le seuil de Bonferroni pour le
    nombre de règles suivies.

### Résultats de la partie 10

Le détail est dans `resultats/partie10/scan.md`.
- **Données.** 131 séances : 75 pour l'exploration, 56 pour la confirmation. 23 variables, 5 jours de la semaine.
- **Étape 1.** Seulement 11 familles atteignent t ≥ 3.
- **Placebos.** Leur meilleur t de confirmation va de 0,90 à 3,60, ce qui donne une barre de 3,57.
- **Survivantes : 0.**
- **Règle figée pour les séances de FluxNQ.** Une seule des familles de confirmation atteint t ≥ 2 : acheter le
  matin, de 9 h 45 à 11 h 30 toutes les 15 minutes, pour 60 minutes, si l'écart d'ouverture est dans le
  5e quintile (t 4,09 puis 2,92 ; 68 trades ; +58,8 $). C'est une règle de prix plus que d'order flow.
- **Aucune variable d'order flow n'arrive en tête.** Delta, carnet, gros lots, footprint et intensité ne donnent pas
  de famille qui tienne en confirmation sur ces 131 séances.

### La règle de l'écart d'ouverture sur 15 ans (question de l'utilisateur, 30 octobre 2026)

Le détail est dans `flux/gap_15ans.py` et `resultats/partie10/gap_15ans.md`.
- **Les 68 trades de confirmation ne viennent que de 9 journées**, parce que la règle rachète toutes les 15 minutes le
  même matin. Compté par journée, le t tombe à 1,69. Deux journées (4 août et 21 septembre) font 3 141 $ des 4 000 $.
- **Rejouée telle quelle sur 2011 - mars 2026**, des années que le scan n'avait jamais vues : 536 journées,
  −10 950 $, t −0,43.
- **Les années alternent**, avec par exemple −12 698 $ en 2022 et −11 858 $ en 2025.
- **Pire journée** : −6 637 $ le 20 novembre 2025. **Plus forte baisse du cumul** : −23 350 $. 77 journées sur 563
  perdent plus de 1 000 $ (1 MNQ par entrée, jusqu'à 8 entrées le même matin).
- **Conclusion : 2026 est une bonne année pour cette règle, pas un avantage.** Elle n'est pas adoptée et reste
  seulement suivie, sans argent.

## Partie 11 : règles tirées de la recherche récente sur l'ère 0DTE (fixées le 30 octobre 2026 avant tout calcul)

### Ce que dit la recherche
- Depuis que les options sur le S&P 500 expirent chaque jour (mai 2022), l'élan intrajournalier s'est éteint en
  moyenne. Les retournements du flux se sont renforcés.
- Les teneurs de marché « longs en gamma » renforcent les retournements. « Courts en gamma », ils renforcent l'élan
  (Dim, Eraker et Vilkov ; Baltussen et al. 2021 ; Adams et al.).
- Le rendement de la nuit annoncerait un retournement à l'ouverture (Iwanaga et Sakemoto).

Ces études ont été lues après les résultats des parties 8 et 10 : on savait déjà que la règle R1 (13 h 30) perdait en
2025-2026. Les règles conditionnées au gamma, elles, n'ont jamais été calculées.

### Règles
**Gamma.** On prend le GEX de SqueezeMetrics de la veille. Son rang est calculé sur les 252 séances d'avant : bas =
au plus 20 %, haut = au moins 80 %. Le code est `flux/gamma_0dte.py`.

| Règle | Signal | Trade |
|---|---|---|
| L1 fin de séance, gamma bas | gamma bas | à 15 h 30, dans le sens du mouvement depuis l'ouverture ; sortie à 16 h |
| L2 fin de séance, gamma haut | gamma haut | à 15 h 30, contre le mouvement depuis l'ouverture ; sortie à 16 h |
| L3 après-midi, gamma bas | gamma au plus 40 % et, à 13 h 30, NQ dans les 14 % du haut de son range | achat à 13 h 30, sortie à 15 h 30 (symétrique : vente dans les 14 % du bas) |
| L4 après-midi, gamma haut | gamma au moins 60 % et même place qu'en L3 | contre : vente en haut du range, achat en bas ; de 13 h 30 à 15 h 30 |
| L5 ouverture après la nuit | écart d'ouverture dans les 10 % les plus forts des 252 séances d'avant (ou les plus faibles), en pourcentage | contre l'écart, de l'ouverture de 9 h 30 à celle de 10 h |

### Calcul et jugement
- **Frais.** 3 $ par aller-retour par MNQ, au prix d'aujourd'hui ; minutes du NQ.
- **Jugement sur l'ère 0DTE**, du 16 mai 2022 au 29 octobre 2026. Une règle passe si :
  - t ≥ 2,33 (Bonferroni unilatéral à 5 % pour 5 règles) ;
  - le gain moyen est positif ;
  - au moins 3 des 5 années 2022 - 2026 sont gagnantes.
- **2011 - mai 2022** est publié à titre de comparaison.
- **Une règle qui passe** va au suivi en direct, sans argent. **Une qui échoue** est publiée telle quelle.

### Résultats de la partie 11

Le détail est dans `resultats/partie11/gamma_0dte.md`. Aucune règle ne passe la barre de l'ère 0DTE.

| Règle | 2011 - mai 2022 | Ère 0DTE (mai 2022 - oct. 2026) |
|---|---|---|
| L1 fin de séance, gamma bas (élan) | 495 trades, +45,4 $, **t +2,81** | 173 trades, −7,0 $, t −0,37 |
| L2 fin de séance, gamma haut (contre) | 675 trades, −6,0 $, t −1,52 | 306 trades, **+12,8 $, t +2,06**, 4 années sur 5 gagnantes |
| L3 après-midi, gamma bas (élan) | 299 trades, +22,0 $, t +1,08 | 138 trades, +18,7 $, t +0,67 |
| L4 après-midi, gamma haut (contre) | 318 trades, −22,0 $, t −2,45 | 194 trades, −5,7 $, t −0,34 |
| L5 ouverture après la nuit (contre) | 505 trades, +43,8 $, **t +3,24** | 219 trades, −1,6 $, t −0,07 |

- **Ce qui marchait avant 2022 ne marche plus depuis.** L'élan de fin de séance (L1) et le retournement de l'ouverture
  (L5) disparaissent avec l'ère 0DTE, comme l'élan de l'après-midi des parties 8 et 10.
- **L2 est la seule règle qui gagne régulièrement depuis 2022**, et elle suit le mécanisme décrit par la recherche.
  Mais son t de 2,06 reste sous la barre de 2,33.
- **Décision : L2 n'est pas adoptée en argent réel.** Elle entre dans le bot FluxNQ (règle 9, en virtuel par défaut)
  et dans le suivi de chaque soir. Elle sera dite « qui marche » après 40 trades nouveaux avec t ≥ 2,50.

## Partie 12 : le retournement des jours de gamma haut, toute la journée (fixé le 30 octobre 2026 avant tout calcul)

### Pourquoi
- **Barbon et Buraschi (2021)** : quand les teneurs de marché sont longs en gamma, les rendements de 5 à 60 minutes
  s'enchaînent à l'envers (autocorrélation négative).
- **Baule, Schlie et Zhou (2025)** : ces retournements sont les plus forts à 15 minutes, et ils viennent de la
  couverture des teneurs de marché.
- **L2** (partie 11) n'en prend qu'une miette, à 15 h 30. Si le mécanisme est réel, il doit agir toute la journée, ce
  qui donne des trades bien plus fréquents.

### Règles
Le gamma et son rang sont ceux de la partie 11 (GEX de la veille, rang sur 252 séances). Code : `flux/gamma_jour.py`.

| Règle | Jours | Trades |
|---|---|---|
| M1 | gamma ≥ 80 % | toutes les 30 minutes de 10 h à 15 h 30 : contre le mouvement des 30 dernières minutes, tenu 30 minutes (on retourne ou on reste selon le signe) |
| M2 | gamma ≥ 60 % | comme M1 |
| M3 | gamma ≥ 80 % | toutes les 15 minutes de 9 h 45 à 15 h 45 : contre le mouvement des 15 dernières minutes, tenu 15 minutes |
| M4 (le miroir) | gamma ≤ 20 % | toutes les 30 minutes de 10 h à 15 h 30 : **dans le sens** du mouvement des 30 dernières minutes, tenu 30 minutes |

- **Trade.** Entrée et sortie à l'ouverture des minutes. Pas de trade si le mouvement est nul.
- **Frais.** 3 $ par trade (aller-retour), comme si chaque trade était fermé puis rouvert. C'est prudent : un vrai
  retournement coûte moins.

### Jugement
- **Les gains sont additionnés par journée.** Le t est calculé sur les journées, pour ne pas compter plusieurs fois les
  trades liés d'une même journée.
- **Une règle passe** si, sur l'ère 0DTE (16 mai 2022 - 29 octobre 2026), t ≥ 2,24 (Bonferroni unilatéral à 5 % pour
  4), le gain moyen est positif et au moins 3 années sur 5 sont gagnantes. 2011 - mai 2022 est publié pour comparaison.
- **Ensuite**, que quelque chose passe ou non, la demande de l'utilisateur est appliquée : combiner les meilleures
  pièces trouvées. C'est un **portefeuille de candidates**, publié avec sa limite : ses pièces ont été choisies en
  connaissant une partie de ces années. Il ne sera dit fiable qu'après le suivi en direct.

### Résultats de la partie 12

Le détail est dans `resultats/partie12/gamma_jour.md`. **Aucune règle ne passe.** Sur l'ère 0DTE :

| Règle | Résultat | Par journée | t |
|---|---|---|---|
| M1 (gamma ≥ 80 %, contre, 30 min) | −9 901 $ | −32,3 $ | −1,44 |
| M2 (gamma ≥ 60 %, contre, 30 min) | −19 881 $ | −37,8 $ | −1,91 |
| M3 (gamma ≥ 80 %, contre, 15 min) | −20 895 $ | −68,1 $ | −2,67 |
| M4 (gamma ≤ 20 %, avec, 30 min) | −20 033 $ | −115,8 $ | −1,83 |

- **Avant frais, le retournement de M1 vaut à peine +0,3 $ par trade.** Les 3 $ de frais par trade l'écrasent.
- **L'effet que capte L2 ne se multiplie pas dans la journée.** Il reste propre à la dernière demi-heure.

## Partie 13 : portefeuille des meilleures candidates (demande de l'utilisateur, règle fixée le 30 octobre 2026 avant le calcul)

Rien de nouveau ne passe ses barres. À la demande de l'utilisateur, on combine les meilleures pièces déjà figées, sans en
changer aucune.
- **Candidates.** S2b, ORB 5 min (H1), cassure de la veille (H5), Supertrend (H12), pivots (F3), zone d'origine, R1,
  R2 et L2.
- **Calcul.** Gains par séance pour 1 MNQ, au prix d'aujourd'hui, frais compris (code de `flux/veille.py`).
- **Règle d'entrée dans le portefeuille.** Sur l'ère 0DTE (16 mai 2022 - 29 octobre 2026), une candidate entre si :
  - son t (sur les séances où elle trade) est d'au moins 1 ;
  - au moins 3 de ses 5 années sont gagnantes.
- **Portefeuille.** 1 MNQ par règle retenue, tout additionné par séance. On le mesure par année et par séance (perte
  maximale), puis sur des challenges Bulenox 50K simulés avec un départ à chaque séance de l'ère 0DTE.
- **Limite, dite d'avance.** Le choix des pièces se fait sur les années mêmes où on les mesure. Le portefeuille est
  donc flatteur par construction. Il ne sera dit fiable qu'après le suivi en direct, qui le jouera chaque soir.
  Code : `flux/portefeuille.py`.

### Résultats de la partie 13

Le détail est dans `resultats/partie13/portefeuille.md`.

**Pièces retenues par la règle (8)** : R1, R2, L2, ORB 5 min, cassure de la veille, Supertrend, pivots et zone. S2b
n'est pas retenue : sur l'ère 0DTE, elle fait −1 489 $ sur 699 séances (t −0,89).

**Le portefeuille, 1 MNQ par règle (jusqu'à 8 MNQ en même temps) :**

| Période | Total | t | Pire séance | Plus forte baisse | Challenges validés (1 / 2 MNQ par règle) |
|---|---|---|---|---|---|
| Ère 0DTE (mai 2022 - oct. 2026) | +135 155 $ | 2,67 | −5 799 $ | −16 166 $ | 54 % / 61 % |
| 2023 - 2026 | +71 933 $ | 1,66 | −5 131 $ | −16 166 $ | 49 % / 56 % |
| 2025 - 2026 | +35 981 $ | 1,11 | −5 131 $ | −16 166 $ | 48 % / 53 % |

- **2022, année de fortes tendances, fait près de la moitié du gain** (+63 223 $).
- **Depuis 2023, le portefeuille ne fait guère mieux qu'un challenge joué à pile ou face**, qui en valide environ
  45 %. Ses pièces de tendance (corrélation moyenne de 0,42) sont souvent en position ensemble : 561 séances sur
  1 092 en ont au moins 5.
- **Conclusion : ce portefeuille n'est pas une stratégie fiable.** Ses pires séances (−5 000 $ à 1 MNQ par règle)
  dépassent de loin la limite du jour de Bulenox (1 100 $). Il reste suivi, sans argent.

## Partie 14 : trois sources de la recherche récente que presque personne ne teste (fixée le 30 octobre 2026 avant tout calcul)

### Les sources
- **Week-end crypto.** Une baisse des cryptos pendant le week-end annonce une baisse des actions le lundi ; une hausse
  n'annonce rien. L'effet est apparu après le krach de LUNA (mai 2022) (Mourey, Shahrour et Şoiman, *Finance Research
  Letters* 2025).
- **Liquidité nette de la Fed.** Bilan de la Fed − compte du Trésor − prises en pension inversées. C'est une mesure de
  praticiens, sans test académique trouvé.
- **Prime de variance.** C'est l'écart entre la variance implicite et la variance réalisée ; sa partie intrajournalière
  prévoit les horizons courts (Papagelis et Dotsis, *Journal of Futures Markets* 2025).

### Règles
Chaque trade va de l'ouverture (9 h 30) à la clôture (16 h) du NQ, frais de 3 $, en $ pour 1 MNQ au prix d'aujourd'hui.
Le code est `flux/recherche14.py`.

| Règle | Signal (connu avant 9 h 30) | Trade |
|---|---|---|
| W1 | rendement du bitcoin (BTC-USD, Yahoo) du vendredi 20 h au dimanche 20 h (New York) négatif | vente le lundi |
| W2 | ce rendement ≤ −2 % | vente le lundi |
| N1 | variation sur 4 semaines de la liquidité nette (séries WALCL, WTREGEN et RRPONTSYD de la FRED ; niveaux du mercredi, utilisés à partir du vendredi qui suit) positive | achat chaque séance |
| N2 | même variation : positive ou négative | achat si positive, vente si négative, chaque séance |
| V1 | prime de variance du Nasdaq (VXN² de la veille − variance réalisée du NQ sur les 21 séances d'avant, en minutes, annualisée) dans le tiers haut de ses 252 séances d'avant | achat |
| V2 | même prime : tiers haut ou tiers bas | achat dans le tiers haut, vente dans le tiers bas |

### Jugement
Le jugement se fait sur l'ère 0DTE, du 16 mai 2022 au 29 octobre 2026. C'est aussi l'après-LUNA. Une règle passe si :
- t ≥ 2,39 (Bonferroni unilatéral à 5 % pour 6 règles) ;
- le gain moyen est positif ;
- au moins 3 années sur 5 sont gagnantes ;
- pour les règles qui ne font qu'acheter (N1, V1), le gain moyen par trade bat celui d'un achat à chaque séance sur la
  même période.

**Résistance, publiée pour chaque règle** :
- le gain avec des frais doublés (6 $) ;
- le résultat de 2011 à mai 2022 (2018 à mai 2022 pour le bitcoin) ;
- le détail année par année.

Une règle qui passe va au suivi en direct.

### Résultats de la partie 14

Le détail est dans `resultats/partie14/recherche14.md`. **Aucune règle ne passe.**

| Règle | Ère 0DTE | Avant |
|---|---|---|
| W1 vente du lundi après un week-end bitcoin négatif | 99 trades, −145,8 $, t −2,38 | 157 trades, −66,0 $, t −1,16 |
| W2 idem si ≤ −2 % | 30 trades, −146,2 $, t −0,97 | 69 trades, −26,5 $, t −0,30 |
| N1 achat quand la liquidité nette monte | 529 trades, +39,8 $, t 1,26 (l'achat de chaque séance fait +24,5 $) | +7,8 $, t 0,57 |
| N2 achat ou vente selon la liquidité nette | +11,0 $, t 0,52 | −0,6 $, t −0,05 |
| V1 achat quand la prime de variance est haute | +12,0 $, t 0,27 | +6,4 $, t 0,24 |
| V2 achat ou vente selon la prime de variance | −20,9 $, t −0,79 | −8,2 $, t −0,53 |

- **Le week-end crypto marche à l'envers sur la séance du NQ.** Après un week-end de baisse du bitcoin, le NQ a plutôt
  **monté** de 9 h 30 à 16 h le lundi, avant comme depuis 2022. Le lundi s'ouvre souvent en baisse, puis la séance
  rattrape. L'étude parle du rendement du lundi d'une clôture à l'autre, qui contient l'écart d'ouverture ; ce n'est pas
  ce qu'on peut trader de 9 h 30 à 16 h.
- **L'inverse de W1 (achat du lundi après un week-end bitcoin négatif) est une idée trouvée après coup.** Elle ne peut
  pas être adoptée sur ces chiffres. Elle va au suivi en direct, sous le nom W1i, comme une hypothèse nouvelle.
- **La liquidité nette (N1)** bat l'achat de chaque séance depuis 2022, mais trop peu pour être sûr (t 1,26).

## Partie 15 : les murs d'options du Nasdaq 100 (règle fixée le 30 octobre 2026, jugée seulement sur l'avenir)

### Recherches consultées pour cette partie
Elles ne donnent pas de mécanisme nouveau testable sur l'historique :
- sur les fonds à volatilité cible, aucune étude sérieuse ;
- les rachats d'ETF à levier ont déjà été testés ;
- l'effet de fin de journée des produits VIX se retourne la nuit ;
- les niveaux de déclenchement des CTA n'ont pas d'étude ;
- une étude de juillet 2026 décrit la fin du suivi de tendance à court terme.

### La source
Le radar calcule depuis le 29 octobre 2026 les murs d'options du NDX, à partir de la photo du CBOE (`radar/collecte.py`) :
- **mur de calls** : le prix d'exercice où le gamma des calls est le plus fort ;
- **mur de puts** : le prix d'exercice où le gamma des puts est le plus fort.

Les teneurs de marché y vendent à l'approche par le bas et y achètent à l'approche par le haut. Cette source n'a pas
d'historique gratuit ; elle sera jugée sur les séances qui viennent.

### Règle MUR (`flux/veille.py`)
- **Niveaux.** On prend les murs de la dernière photo avant la séance (4 jours au plus) et on les ramène au NQ avec
  l'écart NQ − NDX de la veille.
- **Signal.** Entre 10 h et 15 h 30, au premier contact à 0,1 % près du mur de calls, vente à l'ouverture de la minute
  suivante.
- **Sortie.** Stop 0,25 % au-dessus du mur, objectif 2 R, sortie à 16 h au plus tard.
- **Mur de puts.** Achat, de façon symétrique.
- Un trade par mur et par jour ; frais de 3 $.
- **Barre.** 40 séances avec trade et t ≥ 2,61 (Bonferroni pour les 11 candidates suivies).

### Correction de la collecte
Le niveau de bascule du gamma prenait par erreur le plus petit prix d'exercice. C'est maintenant le changement de signe
du gamma cumulé, à 10 % du prix au plus. La règle MUR ne l'utilise pas.

## Partie 16 : grille order flow d'environ 200 000 réglages (fixée le 30 octobre 2026 à 11 h 20 New York, avant la séance de FluxNQ et avant tout calcul)

Le code est `flux/of_grille.py`.

### Les signaux (à chaque seconde, avec ce qui est connu à cette seconde)
A est le range moyen des minutes des 30 dernières minutes (plancher 2 points).

| Famille | Réglages | Sens |
|---|---|---|
| G1 delta | fenêtre 5, 10, 30, 60 ou 120 s ; \|achats − ventes\| ÷ volume ≥ 0,5 / 0,6 / 0,7 / 0,8 ; volume ≥ 1, 2 ou 4 fois la moyenne par seconde de la séance | suivre ou contrer le delta |
| G2 carnet | niveaux 1 (et 3, 5, 10 avec le DOM) ; (achat − vente) ÷ total ≥ 0,2 / 0,3 / 0,4 / 0,5 / 0,6 (ou ≤ l'opposé), tenu 5, 15, 30 ou 60 s | suivre ou contrer le côté chargé |
| G3 divergence | mouvement sur 30, 60 ou 300 s ≥ 0,5 A ou 1 A, avec un delta de la même fenêtre de signe opposé | suivre le delta ou suivre le prix |
| G4 balayage | dans une seconde : range ≥ 1, 2 ou 3 points ; ≥ 70, 80 ou 90 % du volume d'un côté ; volume ≥ 3, 5 ou 10 fois la moyenne | suivre ou contrer |
| G5 retrait (DOM seulement) | la somme d'un côté sur 5 niveaux tombe de 30, 40 ou 50 % en 3, 5 ou 10 s, par rapport à sa moyenne des 60 s d'avant | côté qui tient, ou l'inverse |
| G6 gros lots | volume signé des transactions de 20 contrats et plus sur 30, 60 ou 300 s ≥ 50, 100 ou 200 contrats | suivre ou contrer |

### Les sorties et les heures
- **Sorties** : stop de 0,5 / 1 / 1,5 / 2 / 3 / 4 A × objectif de 0,5 / 1 / 1,5 / 2 / 3 / 4 A × durée maximale de 2, 5,
  15, 30 ou 60 minutes.
- **Fenêtres d'entrée** : 10 h - 15 h 30, 10 h - 12 h, ou 13 h - 15 h 30.
- **Exécution** : comme la partie 9, avec une position à la fois, au plus 4 trades par jour, 1 tick de glissement et
  2 $ de commission.

### Jugement des réglages du tape et du premier niveau (G1, G2 niveau 1, G3, G4, G6), sur les 131 séances
- **Exploration** du 1er avril au 15 juillet 2026, **confirmation** du 16 juillet au 1er octobre 2026.
- **Une famille** est un signal (famille + réglages) et une fenêtre d'entrée. Elle garde sa meilleure sortie à
  l'exploration, si elle a au moins 60 trades et t ≥ 3.
- **Confirmation.** Il faut au moins 30 trades, un gain moyen positif, et t ≥ le 95e centile du meilleur t de
  confirmation de 10 placebos, avec un plancher de 3. Un placebo est la même grille avec les signaux décalés de
  séances entières.
- **Coffre : l'avenir.** Les survivantes, ou à défaut les 5 meilleures de confirmation à t ≥ 2, sont figées avant
  la séance du 30 octobre 2026 et jouées sur les séances de FluxNQ.

### Les réglages qui demandent plusieurs niveaux du DOM (G2 sur 3, 5 ou 10 niveaux ; G5)
- **Ils sont explorés sur les séances de FluxNQ seulement.** Les 20 premières séances servent à choisir, les
  20 suivantes à confirmer.
- **La séance du 30 octobre ne donne qu'un classement.** Ce n'est pas un résultat. Il est publié avec le meilleur
  résultat de 10 placebos sur cette même séance, pour montrer ce que le hasard seul produit.

### Résultats de la partie 16 sur l'historique (131 séances)

Le détail est dans `resultats/partie16/historique.md`.
- **131 760 réglages** du tape et du premier niveau.
- **Une seule famille atteint t ≥ 3 en exploration**, moins que certains placebos (jusqu'à 10 familles). Elle tombe à
  t 0,08 en confirmation.
- **Les placebos** ont un meilleur t de confirmation de 0 à 2,92 ; la barre est de 3,00. **Aucune survivante**, et
  rien à t ≥ 2 : aucune règle du tape n'est figée pour les séances de FluxNQ.
- **Conclusion.** Sur ces 131 séances, le tape et le premier niveau ne contiennent pas plus de signal exploitable que
  le hasard, une fois payés le glissement et la commission. C'est ce que dit la recherche : leur effet ne dure que 1 à
  2 ticks.
- **Les 74 520 réglages du DOM** (G2 sur 3, 5 et 10 niveaux ; G5) restent à explorer sur les séances de FluxNQ.

### Note du 30 octobre 2026 : le DOM de l'utilisateur n'affiche qu'un niveau

L'utilisateur indique que son DOM (Quantower et Rithmic, compte Bulenox) n'affiche qu'un niveau de chaque côté. Les
règles restent figées telles quelles. Voici ce que cela change pour elles, dit avant la séance :
- **D3 et D4 (murs) ne peuvent pas se déclencher.** Un mur doit faire au moins 5 fois la quantité médiane des niveaux
  visibles. Avec un seul niveau par côté, c'est impossible.
- **D1 (déséquilibre) et D2 (retrait) deviennent des règles du premier niveau.** Ce premier niveau est déjà dans
  l'historique de Databento : sa version de la grille (G2 niveau 1) n'a rien donné sur 131 séances (partie 16).
- **Les 74 520 réglages « DOM » de la grille se ramènent eux aussi au premier niveau.**
- **Pour juger de vraies règles de carnet**, il faudrait recevoir la profondeur du CME, c'est-à-dire plusieurs niveaux.
  FluxNQ l'enregistre déjà si elle arrive.
