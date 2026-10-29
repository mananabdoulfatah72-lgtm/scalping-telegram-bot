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
