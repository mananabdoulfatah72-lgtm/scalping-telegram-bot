# L'article « REA + Kronos + TradingAgents », appliqué à ton compte (16 novembre 2026)

Tu as demandé de suivre l'article et son schéma (le « bureau de recherche d'une seule personne »). Voici ce qui a été fait,
étape par étape, avec les preuves, et ce qui n'a pas été fait, avec la raison.

## Le schéma de l'article, et où il se trouve dans ton système

L'article demande 6 briques. Ton système les a toutes ; deux ont été ajoutées aujourd'hui.

| Brique de l'article | Ce qu'elle exige | Chez toi |
|---|---|---|
| Collecte des preuves | Noter ce qui est observé, ce qui est déduit, ce qui reste inconnu | `rea/ENQUETES.md`, `usine/INSTITUTIONS.md`, ce document |
| Données de marché | Horodatage vérifié, provenance connue | `usine/donnees.py` : minutes du NQ, faux prix corrigés, séances complètes seulement |
| Laboratoire | Code versionné et reproductible | `usine/moteur.py` (calcul déterministe), `usine/kronos_cache.py` (ajouté aujourd'hui) |
| Validation indépendante | Périodes jamais vues, frais réalistes, contrôle du hasard | `usine/portes.py` (5 portes), `usine/kronos_nq.py` (ajouté aujourd'hui) |
| Couche de risque | Limites séparées de la stratégie | `usine/RISQUE.md`, `consigne.py`, limites du jour et frein des bots, fichier `STOP`, règles de Bulenox côté serveur |
| Registre des expériences | Toutes, échecs compris | `usine/registre.csv` |

**L'équation (1) de l'article**, gain net = gain brut − frais − glissement − impact − autres coûts, chez toi :
- frais et glissement : 3 $ l'aller-retour sur MNQ (1 $ et 1 tick par ordre), dans tous les calculs ;
- glissement réel : pas encore mesuré, d'où `usine/rapprochement.py` ;
- impact du marché : négligeable à 1 contrat ;
- autres coûts (abonnement Bulenox, données) : hors des calculs.

## Étape 1 de l'article : REA cartographie un terminal pro (Bloomberg). Non fait.

- Le terminal Bloomberg est sous licence ; le reconstruire à partir de son logiciel est interdit par sa licence, et REA
  l'interdit aussi ([rea/README.md](../rea/README.md), la ligne rouge).
- Il n'y en a pas besoin : le terminal construit aujourd'hui (plus bas) ne copie rien. Il affiche tes données et les
  prévisions de Kronos.

## Étapes 3 à 7 : Kronos

### Ce que dit le code de Kronos (dépôt shiyu-coder/Kronos, commit `67b630e`, licence MIT)

- **Le modèle de l'article existe** : Kronos-small, 24,7 M de paramètres, contexte de 512 bougies (`README.md`, lignes
  77 - 82). Ses poids ont été déposés sur Hugging Face le 30 juin 2025 (commit « add model » de NeoQuasar/Kronos-small ;
  les commits suivants ne touchent que la fiche).
- **`predict` ne rend pas 100 trajectoires** : il les tire puis en fait la moyenne (`model/kronos.py`, ligne 467 :
  `preds = np.mean(preds, axis=1)` ; `README.md`, ligne 161 : « Number of forecast paths to generate and average »). Par
  défaut, il n'en tire qu'une (`sample_count=1`). Pour dessiner 100 trajectoires comme l'article, il faut appeler le modèle
  autrement : c'est ce que fait `usine/kronos_cache.py`.
- **Il recalcule toute la fenêtre à chaque bougie prévue** (`model/kronos.py`, lignes 420 - 454 : `decode_s1` sur toute la fenêtre, ligne 436). Sur un processeur à 4
  cœurs, 100 trajectoires de 24 bougies prennent 4 min 17 s par décision (mesuré ici), soit environ 70 heures pour 344
  séances à 3 décisions. `kronos_cache.py` calcule le contexte une seule fois : 4 secondes par décision, avec exactement
  les mêmes trajectoires que le code d'origine (écart 0, vérifié sur 3 graines).
- **Le « 93 % » de l'article** n'est pas dans le dépôt de Kronos. Il viendrait de l'article scientifique (arXiv
  2508.02739), que je n'ai pas lu ici. Et c'est une mesure de prévision, pas un gain de trading.

### Le test (règles fixées et commitées avant le calcul : `usine/REGLES.md`, idée K)

**Verdict : Kronos est rejeté** (`usine/resultats/2026-11-16/kronos.json`, ligne « kronos » de `usine/registre.csv`).

344 séances du 1er juillet 2025 au 13 novembre 2026, 1 032 décisions, 100 trajectoires chacune.

| Porte | Exigé | Kronos | |
|---|---|---|---|
| K1 : t des gains nets par séance | 2,0 au moins | −0,61 | échoue |
| K2 : mélanges des sens qui font aussi bien | moins de 1 % | 70,8 % | échoue |
| K3 : gain par an, 1 MNQ, frais compris | +1 000 $ au moins | −3 305 $ | échoue |

- 974 trades : 395 achats, 579 ventes. Kronos a vendu plus souvent qu'il n'a acheté,
  pendant une période où le NQ est passé d'environ 22 800 à 28 000 points.
- Bon sens dans **46,5 %** des trades : moins qu'une pièce lancée.
- Aucune variante ne gagne, et le seuil 70 % ou 80 % ne sauve rien :

| Règle, aux mêmes heures | t | $ par an, 1 MNQ | Bonnes directions |
|---|---|---|---|
| Kronos, règle du test (seuil 60 %) | −0,61 | −3 305 $ | 46,5 % |
| Kronos, trajectoire moyenne (ce que rend `predict`) | −0,68 | −3 953 $ | 46,8 % |
| Kronos, seuil 50 % | −0,67 | −3 854 $ | 46,8 % |
| Kronos, seuil 70 % | −0,37 | −1 881 $ | 46,7 % |
| Kronos, seuil 80 % | −0,72 | −3 683 $ | 46,4 % |
| Suivre le mouvement des 2 heures d'avant | −0,80 | −6 049 $ | 50,2 % |
| Toujours acheter | −0,55 | −1 607 $ | 52,1 % |

- **La lecture du régime de l'article ne tient pas.** Les trajectoires sont « d'accord » (au moins 80 % dans le même sens)
  dans 861 blocs sur 1 032. Le NQ y bouge en moyenne de 0,33 % en 2 heures, contre
  0,30 % quand elles sont dispersées : presque pareil. Kronos est presque toujours sûr de lui, et se trompe une
  fois sur deux.
- **Ce que ça change pour ton compte : rien.** Aucun bot ne trade sur Kronos. Il rejoint la liste des pistes fermées
  (`rea/PISTES.md`).

## Étapes 5 et 6 : TradingAgents. Étudié, pas lancé.

### Ce que dit son code (dépôt TauricResearch/TradingAgents, commit `9fa1196`, licence Apache 2.0)

- **La chaîne de l'article existe** (`tradingagents/graph/setup.py`, lignes 145 - 185) :
  1. 4 analystes en même temps : marché, sentiment, actualités, fondamentaux (`graph/trading_graph.py`, ligne 56) ;
  2. un débat entre un chercheur haussier et un chercheur baissier, puis un responsable de la recherche ;
  3. un trader ;
  4. trois analystes de risque (agressif, neutre, prudent) ;
  5. un gérant de portefeuille qui décide.
- **Chaque agent est un grand modèle de langage payant** : OpenAI par défaut (`tradingagents/default_config.py`, lignes
  92 - 94), données de Yahoo Finance (lignes 158 - 160). Une décision demande plus de 10 appels de modèle.
- **Son propre « backtest » n'est pas une simulation de trading** (`tradingagents/backtest.py`, lignes 9 - 14) : « It is
  not a portfolio simulator, and must not grow one ». Il note des avis (acheter, garder, vendre), sans quantité, sans prix
  d'exécution, sans frais.
- **Ses auteurs le disent :** « designed for research purposes […] not intended as financial, investment, or trading
  advice » (`README.md`, ligne 74).

### Pourquoi il n'a pas été lancé

- **Il ne peut pas être testé sur le passé honnêtement.** Un modèle de langage connaît l'histoire jusqu'à sa date de
  coupure : il « sait » déjà ce que le marché a fait. La version 0.4.0 a corrigé les fuites des données (`README.md`,
  ligne 43), pas la mémoire du modèle. Seul un suivi en papier, jour après jour, le mesurerait.
- **Il est fait pour des actions, une décision par jour** (bilans, actualités d'entreprise). Ton compte trade le NQ
  pendant la séance, et tes bots décident toutes les 5 ou 30 minutes.
- **Il faut une clé d'API payante.** Je ne l'ai pas, et l'utiliser dépenserait ton argent.

**Ce qui serait possible**, si tu le veux : un suivi en papier de 2 mois. Chaque matin, TradingAgents donne un avis sur le
Nasdaq ; on note s'il aurait amélioré la zone (règle fixée avant de commencer). Il faudra une clé d'API (OpenAI, Anthropic
ou autre), saisie dans un formulaire sécurisé et jamais dans la conversation.

## Le terminal

Page publiée : https://claude.ai/artifact/4oWnCFoPxK95TF5maxWVS7 (privée ; partage-la depuis son menu si tu veux la
montrer). Source : `usine/terminal/modele.html` et `usine/terminal.py`, page générée `usine/terminal/page.html`.

- Pour chacune des 5 dernières séances (9 au 13 novembre 2026) et chaque décision (10 h, 12 h, 14 h) : les bougies du NQ,
  les 100 trajectoires de Kronos, leur médiane, et ce que le NQ a vraiment fait.
- La lecture de la décision (part des trajectoires en hausse, ce que la règle aurait fait, le résultat du trade).
- Le verdict du test et la comparaison avec les deux règles simples.
- Seul le NQ y figure : ton compte ne trade que lui, avec des bots testés. Les panneaux crypto, devises et matières
  premières de l'article n'aident pas ton challenge.

## Ce qui reste incertain

- Kronos a été testé sur 344 séances seulement (juillet 2025 → novembre 2026), la seule période qu'il n'a pas pu voir.
- Une seule façon de lire Kronos a été jugée (décision à 10 h, 12 h et 14 h, horizon de 2 heures, seuil de 60 %).
  D'autres réglages sont donnés pour information, mais en chercher un qui marche après coup serait tricher.
- Le contexte fait 488 bougies au lieu des 512 de l'article, pour que le calcul accéléré reste exact.
