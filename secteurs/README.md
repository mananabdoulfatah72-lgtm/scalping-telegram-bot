# Secteurs américains : recherche d'abord, stratégie ensuite

Reproduction de la méthode « recherche → hypothèses → critères fixés → backtest → journal des
rejets → essayer de tuer le survivant », avec trois corrections :

1. **Le choix du secteur est lui-même testé** : on vérifie sur 25 ans si « le secteur le plus fort des
   3-6 derniers mois » continue à battre le marché ensuite (sinon l'étape 1 ne sert à rien).
2. **Chaque version essayée compte** comme un essai (fichier `fonds/essais.csv`) : plus on essaie,
   plus une version passe par hasard. On ne corrige pas une stratégie jusqu'à ce qu'elle passe.
3. **Pas d'actions ajoutées parce qu'elles ont déjà monté** : l'univers est fixé à l'avance
   (`univers.py`). Les listes d'actions sont celles d'aujourd'hui (biais de survie) : les stratégies
   sur ETF sont plus fiables que celles sur actions avant 2020.

## Protocole (fixé le 28 septembre 2026, avant de télécharger les données)

### Étape 1 — Recherche, sans stratégie

Pour chaque secteur (ETF SPDR), au 25 septembre 2026 : rendement relatif à SPY sur 3 et 6 mois,
momentum 12-1 mois, position par rapport à la moyenne 200 jours, volatilité, bêta, sensibilité aux
taux (rendements hebdomadaires sur 2 ans comparés à la variation du taux 10 ans), baisse depuis le
plus haut d'un an. Classement par la moyenne des rangs de force relative 3 mois et 6 mois.

Taux de base historique (1999-2026) : chaque mois, acheter le secteur le plus fort (et les 3 plus
forts) sur 3 et 6 mois, et mesurer l'écart avec SPY le mois suivant. Aussi : chaque fois qu'un secteur
dépasse SPY de plus de 10 points sur 3 mois, que fait-il les 1 et 3 mois suivants ?

### Étape 2 — Quatre stratégies pour le secteur classé premier

Quatre paris différents, écrits ici avant de connaître le secteur gagnant (E = ETF du secteur,
L = ses actions dans `univers.py`) :

1. **Rotation** : chaque fin de mois, détenir E si son rendement sur 6 mois dépasse celui de SPY
   **et** s'il est au-dessus de sa moyenne 200 jours ; sinon détenir SPY. Pari : la force relative
   d'un secteur persiste (Moskowitz et Grinblatt, 1999).
2. **Momentum dans le secteur** : chaque fin de mois, les 5 actions de L au meilleur rendement de
   t − 6 mois à t − 1 mois, à poids égal. Pari : les gagnants continuent de gagner (Jegadeesh et
   Titman, 1993).
3. **Faible risque** : chaque fin de mois, les 5 actions de L à la plus faible volatilité propre sur
   6 mois (écart par rapport à E), pondérées par l'inverse de leur volatilité. Pari : les actions
   calmes rapportent plus par unité de risque (Ang et al., 2006 ; Frazzini et Pedersen, 2014).
4. **Moteur macro** : détenir E quand son moteur économique est favorable (variation sur 3 mois),
   sinon SPY. Moteurs : Énergie → pétrole en hausse ; Matériaux et Industrie → cuivre en hausse ;
   Finance → écart de taux 10 ans − 3 mois en hausse ; Services publics, Immobilier, Technologie,
   Communication, Consommation cyclique → taux 10 ans en baisse ; Santé et Consommation de base →
   SPY sous sa moyenne 200 jours (refuge). Pari : le secteur suit son moteur avec retard.

Frais : 5 points de base par ordre sur les actions, 3 sur les ETF (commission + écart), doublés pour
le test de résistance. Capital de référence 100 000 $.

### Étape 3 — Critères d'acceptation (fixés avant tout backtest)

Une stratégie passe si elle remplit **tous** ces critères :

1. Bat SPY après frais sur les 12 derniers mois (26 septembre 2025 - 25 septembre 2026).
2. Bat encore SPY sur ces 12 mois avec frais et glissement doublés.
3. Pire baisse inférieure à 30 % sur toute l'histoire testée.
4. Sharpe supérieur à 1,0 sur les 12 derniers mois.
5. Aucune action ne fait plus de 40 % des gains des 12 derniers mois.
6. Résultats identiques sur deux exécutions.
7. **Ajouté** : bat SPY après frais sur **toute** l'histoire disponible (depuis 2006 au plus tôt ;
   un an seul, c'est surtout du hasard).
8. **Ajouté** : fait mieux que 95 % des placebos sur toute l'histoire (même nombre de positions,
   choisies ou datées au hasard).

Les critères 1 à 6 sont ceux du texte d'origine ; 7 et 8 sont ajoutés parce qu'un an de données ne
permet pas de distinguer un avantage du hasard. Aucune stratégie n'est modifiée après les résultats :
un échec est inscrit au journal des rejets.

## Versions 5 et 6 (fixées le 28 septembre 2026, après le rejet des 4 premières, avant leur test)

Les 4 stratégies échouent toutes au critère 3 (pire baisse de −51 % à −59 %, en 2008). Une seule
correction est essayée, la plus classique contre les krachs (Faber, 2007) : **quand SPY clôture le mois
sous sa moyenne 200 jours, tout passe en liquidités** (rémunérées au taux court), sinon la stratégie
s'applique normalement.

5. **Version 5** = stratégie 4 (moteur macro) + ce filtre.
6. **Version 6** = stratégie 2 (momentum des actions) + ce filtre.

Mêmes 8 critères, mêmes frais. Placebo de la version 5 : la même suite de positions décalée au hasard
dans le temps ; de la version 6 : 5 actions tirées au hasard, avec le même filtre. Ce sont les essais
5 et 6 de cette étude : s'ils échouent, on s'arrête là.

## Résultats (28 septembre 2026)

### Étape 1 — ce que dit la recherche (au 25 septembre 2026, `recherche.txt`)

| Secteur | Force relative 3 mois | 6 mois | Sensibilité à +0,10 pt de taux 10 ans |
|---|---|---|---|
| **Technologie (XLK)**, classé 1er | +2,4 pts | +28,3 pts | +0,40 % |
| Santé (XLV) | +0,8 | −2,1 | −0,35 % |
| Énergie (XLE) | **+9,8** | −18,0 | +0,74 % |
| Immobilier (XLRE) | −13,4 | −15,2 | −0,68 % |
| Services publics (XLU) | −19,9 | −31,8 | −0,47 % |

- Le marché paie la technologie (semi-conducteurs SOXX +54 pts sur 6 mois ; logiciels IGV +14 pts sur
  3 mois) et punit ce qui craint la hausse des taux (services publics, immobilier, construction ITB −20,
  solaire TAN −40, nucléaire NLR −39 sur 6 mois). L'énergie est la plus forte sur 3 mois.
- **Taux de base 1999-2026 : acheter le secteur le plus fort des 3 ou 6 derniers mois ne bat pas SPY**
  (t entre −0,6 et +0,6 ; légèrement négatif depuis 2010). Après un secteur à plus de 10 points au-dessus
  de SPY sur 3 mois : −0,70 % le mois suivant (t = −1,7), gagnant 49 % du temps sur 3 mois. La recherche
  décrit le marché ; elle ne le prédit pas.

### Journal des rejets (Technologie, `resultats.txt`)

| Version | 12 mois (SPY +18,5 %) | Sharpe 12 mois | Depuis 2006 (SPY +11,1 %/an) | Pire baisse | Placebo battu | Critères ratés |
|---|---|---|---|---|---|---|
| 1 Rotation | +33,0 % | 1,15 | +13,1 %/an | −59 % | 16 % | 3, 8 |
| 2 Momentum des actions | +145,5 % | 1,88 | +29,3 %/an | −56 % | 97 % | 3 |
| 3 Faible risque | +23,1 % | 0,94 | +17,1 %/an | −51 % | 58 % | 3, 4, 5 (une action = 49 % des gains), 8 |
| 4 Moteur macro (taux en baisse) | +19,1 % | 0,91 | +15,6 %/an | −54 % | 98 % | 3, 4 |
| 5 = 4 + filtre 200 jours | +8,1 % | 0,33 | +12,8 %/an | −22 % | 97 % | 1, 2, 4 |
| 6 = 2 + filtre 200 jours | +93,9 % | 1,46 | +24,2 %/an | −38 % | 93 % | 3, 8 |

Critère 6 (déterminisme) : deux exécutions séparées du code final, empreinte identique
(`57435f5cfcc7b7f6`). **Aucune version ne passe : pas de test « pour tuer » à faire.**

À lire avec ces réserves :
- **Versions 2 et 6 (+24 à +29 %/an depuis 2006)** : les 20 actions sont les géants d'aujourd'hui
  (NVDA, AVGO...), choisis en connaissant la suite. Ce chiffre est gonflé par le biais de survie.
- **Version 5** : son placebo (même suite de positions décalée) est trop facile, comme l'a montré la
  revue : le filtre 200 jours seul, sans moteur macro, bat déjà 97 % de ces placebos.
- **Information seulement, pas un critère** : depuis 2023, les pires baisses des versions 1, 3 et 4
  sont de −19 à −23 %. Sur une fenêtre de 3 ans (celle du texte d'origine), elles auraient passé le
  critère 3 ; sur 20 ans, 2008 les fait toutes échouer.

### Revues du code (niveau maximal, deux passes)

Corrigé avant les résultats finaux : placebo des stratégies de moments qui changeait 2,5 fois plus
souvent de position que la stratégie ; trade inutile le dernier jour ; pire baisse qui ignorait le
premier jour ; ETF du secteur acheté avant sa création (XLC, XLRE) ; comparaisons de dates décalées ;
téléchargement qui échouait sans le dire ; déterminisme vérifié dans une seule exécution ; ligne
partielle du 28 septembre ; bug pandas 3 dans le taux de base ; versions 5 et 6 non inscrites comme
essais. Données figées (`donnees/prix.csv.gz` du 28 septembre, 02 h UTC).

### Bilan

| Étape | Nombre |
|---|---|
| Stratégies testées (4 + 2 versions) | 6 |
| Battent SPY sur 12 mois après frais | 4 |
| Battent SPY sur toute l'histoire | 6 |
| Pire baisse sous 30 % | 1 |
| Passent tous les critères | **0** |

## Fenêtre de 5 ans (demandée le 28 septembre 2026, après les résultats sur 20 ans)

Règles écrites ici avant l'exécution. **Mise en garde** : la fenêtre est changée *après* avoir vu
les résultats sur 20 ans (et les baisses depuis 2023). Ce sont donc 6 nouveaux essais
(`fonds/essais.csv`) : une version qui passe sur 5 ans n'a pas la même valeur qu'une version qui
aurait passé sur 20 ans.

- Mêmes 6 versions, mêmes frais, même secteur (XLK), mêmes données figées.
- « Toute l'histoire » devient **30 septembre 2021 - 25 septembre 2026** (premier rééquilibrage
  mensuel après le 25 septembre 2021). La fenêtre contient la baisse de 2022 et celle d'avril 2025.
- Critères 1 à 8 inchangés. Les critères 3, 7 et 8 portent sur ces 5 ans. Le placebo est tiré dans ces
  5 ans. Critère 6 : deux exécutions séparées (`empreinte_5ans.txt`).
- **Tests pour tuer** (fixés maintenant) : une version qui passe les 8 critères doit aussi réussir
  T1 à T4, sinon elle est rejetée.
  - T1 : bat encore SPY sur 5 ans si chaque ordre part **le lendemain** de la fin du mois.
  - T2 : bat encore SPY sur 5 ans avec des **frais triples**.
  - T3 : pour les versions sur actions, bat encore SPY sur 12 mois **sans la meilleure action**
    des 12 mois.
  - T4 : bat SPY dans **au moins 3 des 5 années** (périodes de 12 mois finissant le 25 septembre).
- T5 (information, pas éliminatoire) : même règle de 2006 à septembre 2021, c'est-à-dire la période
  que la fenêtre de 5 ans laisse de côté. On donne le rendement par an contre SPY et la pire baisse.
- T6 (versions 2 et 6, éliminatoire) : **contre le biais de survie**, on remplace les 20 actions
  d'aujourd'hui par les 20 plus grosses de XLK à la fin septembre 2021 (`univers.XLK_2021`, liste de
  mémoire, poids approximatifs). Cette liste contient V, MA et PYPL (passées en finance en 2023),
  PYPL (−79 % depuis) et INTC (−63 % au plus bas en 2025, puis +151 % à la fin : pas seulement une perdante,
  comme l'a relevé la revue). La version doit encore battre SPY sur 5 ans et garder une pire
  baisse inférieure à 30 %. Les deux actions manquantes (INTC, PYPL) sont téléchargées à part
  (`donnees/prix_2021.csv.gz`), sans toucher aux données figées.

### Version 7 (fixée le 28 septembre 2026, après le premier passage sur 5 ans, avant son test)

Au premier passage sur 5 ans, aucune version ne passe. La version 2 échoue seulement au critère 3
(pire baisse −42 %). **Version 7 = moitié version 2, moitié liquidités** (rééquilibrée chaque fin de
mois). Pas de nouvelle règle de choix des actions : on met moins d'argent en jeu. 50 % est choisi
parce que c'est la moitié, pas après optimisation, et il n'y aura pas d'autre fraction.

- Fenêtre de 5 ans seulement, mêmes 8 critères, puis tests T1 à T6. Placebo : 5 actions au hasard,
  aussi à 50 %.
- **Essai trouvé après coup** : il est inscrit comme tel dans `fonds/essais.csv`. S'il passe, on le
  lit comme un candidat à suivre en argent virtuel, pas comme une preuve.
- Les tests pour tuer sont aussi calculés, **pour information**, pour les versions déjà rejetées :
  le verdict ne change pas.

### Journal des rejets, fenêtre de 5 ans (Technologie, `resultats_5ans.txt`)

Du 30 septembre 2021 au 25 septembre 2026 : SPY +14,1 %/an, pire baisse −24 %.

| Version | 12 mois (SPY +18,5 %) | Sharpe 12 mois | 5 ans | Pire baisse | Placebo battu | Critères ratés |
|---|---|---|---|---|---|---|
| 1 Rotation | +33,0 % | 1,15 | +17,2 %/an | −30 % | 43 % | 8 |
| 2 Momentum des actions | +145,5 % | 1,88 | +42,8 %/an | −42 % | 95 % | 3 |
| 3 Faible risque | +23,1 % | 0,94 | +16,9 %/an | −26 % | 35 % | 4, 5, 8 |
| 4 Moteur macro | +19,1 % | 0,91 | +16,6 %/an | −26 % | 50 % | 4, 8 |
| 5 = 4 + filtre 200 jours | +8,1 % | 0,33 | +8,9 %/an | −22 % | 17 % | 1, 2, 4, 7, 8 |
| 6 = 2 + filtre 200 jours | +93,9 % | 1,46 | +24,9 %/an | −37 % | 88 % | 3, 8 |
| 7 = moitié 2 + moitié liquidités | +66,1 % | 1,90 | +23,8 %/an | −23 % | **93 %** | **8 seulement** |

Critère 6 : deux exécutions séparées, empreinte identique (`c321542facd781f6`, tests pour tuer
compris). **Aucune version ne passe les 8 critères, même sur 5 ans.**

Tests pour tuer (information, puisque toutes sont rejetées) :

| Version | T1 lendemain | T2 frais ×3 | T3 sans MU (12 mois) | T4 années gagnées | T6 univers 2021 | T5 2006-2021 |
|---|---|---|---|---|---|---|
| 2 | +42,4 %/an | +41,6 %/an | +107,6 % | 4 sur 5 | +33,3 %/an, baisse **−44 %** ✗ | +25,3 %/an, baisse −56 % |
| 6 | +23,8 %/an | +23,9 %/an | +58,7 % | 3 sur 5 | **+14,5 %/an (SPY +14,1 %)** ✗ | +23,9 %/an, baisse −38 % |
| 7 | +23,6 %/an | +23,3 %/an | +51,7 % | 3 sur 5 | +19,7 %/an, baisse −24 % ✓ | +13,4 %/an, baisse −32 % |

Ce qu'il faut en retenir :
- **Version 7, la plus proche d'un gagnant.** Elle passe tout sauf le placebo : 93 % pour 95 %
  exigés. Autrement dit, 5 actions tirées au hasard dans la même liste, à 50 %, font aussi bien qu'elle
  dans 7 % des cas. La revue a montré que ce chiffre dépend des tirages : avec les tirages de la version
  2, il vaut 95,0 %, et l'erreur due au hasard des tirages est d'environ ±1,3 point. **Le verdict fixé
  reste « rejetée »** : refaire les tirages jusqu'à passer serait exactement ce que le protocole
  interdit. Honnêtement, l'avantage de la règle sur la liste d'actions n'est pas prouvé ; il n'est pas
  non plus exclu.
- **Univers de 2021 (biais de survie)** : avec les grosses actions connues en 2021, la version 6 ne
  bat plus SPY (+14,5 % contre +14,1 %/an). La version 2 garde +33 %/an mais baisse de 44 %. La
  version 7 garde +19,7 %/an avec une baisse de 24 %.
- **Avant la fenêtre (2006-2021)**, la même version 7 aurait perdu 32 % au pire (2008).
- Essais inscrits dans `fonds/essais.csv` (6 versions rejugées + version 7 trouvée après coup).

### Revue du code de la fenêtre de 5 ans (niveau maximal)

Corrigé : les deux nouveaux essais n'étaient pas inscrits dans `fonds/essais.csv` ; T6 tournait aussi
sur la version 3 (non prévu) et avec la liste technologie quel que soit le secteur ; il pouvait aussi
perdre une action sans le dire (vérification ajoutée) ; `prix_2021.csv.gz` pouvait être retéléchargé
(le workflow est maintenant manuel) ; l'empreinte ne couvrait pas les tests pour tuer ; la description
d'INTC était fausse. Non changé : tirages du placebo partagés entre versions (le changer après coup
modifierait les verdicts) ; lenteurs sans effet sur les résultats. Résultats sur 20 ans vérifiés
inchangés (empreinte `57435f5cfcc7b7f6`).
