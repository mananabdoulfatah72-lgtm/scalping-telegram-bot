# Inventaire des stratégies testées — branche `claude/keen-babbage-r686cl`

Inventaire fait le 29 octobre 2026, en lecture seule, sur l'extraction
`/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad/kb` (61 dossiers).
Sauf mention contraire, les chemins sont relatifs à ce dossier. Les chiffres viennent des README et des fichiers de
résultats cités. Quand j'ai recalculé un chiffre moi-même, c'est écrit « recalculé pour cet inventaire ». Ces calculs
ont été faits hors du dépôt, et le dépôt n'a pas été modifié (`git status` vide).

Le suivi en argent virtuel n'est pas sur cette branche. Il est sur `origin/main` (`zone/robot/`, `tendance/robot/`,
`version7/robot/`), que j'ai lu avec `git show` (état au 2026-10-28).

---

## 0. Repères

**Chronologie** (`git log origin/claude/keen-babbage-r686cl`, 368 commits) :

| Dates | Étape |
|---|---|
| 24-27 sept. 2026 | tendance multi-marchés, carry, paires, intraday (Yahoo puis CME Databento), zone de bruit trouvée (t 2,55) |
| 27-28 sept. | fonds (phases 2-3), order flow ES, challenge, DOGE, secteurs (v1-v7), nuit |
| 29 sept. - 1er oct. | zone multi-marchés, évolution 1, tournois 1 à 7, zone (failles, optimisation, sources, taille, retrait), évolution 3 |
| 2 oct. | tournoi 8 (RSI(2) passe le coffre), zone_deux, comptes, tournois 9-10, order flow NQ (filtre H1 confirmé), filtre H1 sur 15 ans |
| 3 oct. | protection et pistes 2-7, machine 4 |
| 6 oct. | sources Ironbeam et LSE du filtre H1, piste 7 |
| 8-9 oct. | intraday50k, static50k, vague 3, machine 5 (sessions24, vagues 1 et 2), vagues 4 à 11 |
| 10-12 oct. | mode à plat du bot, Monte Carlo, robustesse, vagues 12-13, labo30, mc30, cerveau |
| 13-20 oct. | bot 3 en 1 (règles Bulenox), export Rithmic (filtre H1), zone neutre, relance |

**Données principales**
- NQ minute (séance 9 h 30-16 h), Databento :
  - fichier : `intraday/donnees/nasdaq100_1min.csv.gz` ;
  - période : du 2011-01-03 09:30 au 2026-09-25 15:59 ;
  - colonnes : t, o, h, l, c, v, contrat.
- ES minute : `intraday/donnees/sp500_1min.csv.gz`.
- NQ et ES en barres d'une heure : `nuit/donnees/`.
- Futures journaliers : `fonds/donnees/futures_1d.csv.gz` (40 marchés CME, depuis juin 2010).
- Autres marchés en minutes, depuis 2016 : `zone_multi/donnees/`.
- Prix de la tendance : `tendance/donnees/prix.csv.gz` (ETF et futures, depuis 2007).

**Découpage habituel**
- Exploration : 2011-2022 (2016-2022 pour les autres marchés).
- Coffre : 2023 - 25 septembre 2026, ouvert une fois.
- Le coffre 2023-2026 du NQ a servi plusieurs fois. La zone de bruit elle-même avait été mesurée sur 2011-2026 dès
  le 27 septembre. Le dépôt le signale lui-même (`zone_failles/README.md`, `zone_sources/README.md`,
  `evolution2/README.md`).

**Journal des essais** : `fonds/essais.csv` (124 lignes). Il s'arrête à la vague 12. Il ne contient pas la vague 13,
la zone neutre, la relance, labo30 et mc30.

**Dossiers sans stratégie de trading**
- `cerveau/` : page « second cerveau ».
- `jarvis/` : assistant vocal Windows.
- `lse/` : exploration d'une source de ticks. Elle sert le filtre H1.
- `research_notes/` et `reports/` : recherche sur les prop firms (« Trente dollars n'achètent que le mauvais
  challenge »).
- `bot3en1/` : la mise en œuvre C# du bot. Elle est utilisée plus bas pour la régénération.

---

## 1. Fiches des stratégies qui ont un résultat hors échantillon

### 1.1 ZB-V1 — Zone de bruit corrigée (« données propres »), NQ/MNQ, intraday (la référence du projet)

**Où et quand**
- Dossiers : `intraday/` (V0, 27 sept.), `zone_failles/` (V1, 30 sept.), `zone_optimisation/`, `zone_sources/`,
  `tournoi/`, `fonds/`, `robustesse/`.
- Marché : NQ, tradé en MNQ (2 $ le point), séance 9 h 30-16 h, barres d'une minute.

**Règle**
- Limites du jour :
  - haut = max(ouverture, veille) × (1 + σ) ;
  - bas = min(ouverture, veille) × (1 − σ) ;
  - σ = mouvement moyen |C/ouverture − 1| à la même minute sur 14 séances.
- Contrôle toutes les 30 minutes, de 10 h à 15 h 30 :
  - achat au-dessus du haut, vente sous le bas ;
  - sortie si le prix repasse la limite ou le VWAP ;
  - tout est fermé à 16 h.
- Correction V1 : la moyenne et la veille ne prennent que les séances complètes du même contrat.
- Frais : 1,5 point par aller-retour.

**Résultats chiffrés**

| Mesure | Valeur | Source |
|---|---|---|
| V0, 2011-2026, MNQ | 2 326 jours de trade, +4,27 pt nets par trade, t = +2,55 (t sur les gains en $), +1 279 $/an pour 1 contrat | `intraday/resultats_cme.txt` |
| V0, années positives | 8 sur 16 (2018, 2020-2026) | `intraday/resultats_cme.txt` |
| V0 après publication (mai 2024) | +7,46 pt, t = +0,85 | `intraday/resultats_cme.txt` |
| V1, t des rendements quotidiens nets en % | 2011-2016 −2,26 ; 2017-2022 +2,78 ; 2011-2022 +0,81 ; 2023-2026 +2,00 | `zone_failles/README.md` |
| V1, 2023-2026 | +10 668 $ pour 1 MNQ | `zone_optimisation/README.md` |
| Rejeu du robot | 2 287 jours de trade | `zone_failles/README.md` |
| V1 recalculée, 2011-2022 | +9 718,5 $ (1 MNQ, prix de l'époque) ; même total 2023-2026 que la source | recalculé pour cet inventaire |
| Au prix d'aujourd'hui, 2012-2026 (zone sans les jours Fed, 1 MNQ) | +77 690 $, Sharpe 1,12, pire baisse 5 974 $, 14 années positives sur 15 (seule 2016 négative) | `robustesse/robustesse.json` |
| Pertes coupées | jours à 1 trade : +11,1 pt (t +7,6) ; jours à 2 trades ou plus : −4,5 pt (t −8,5) | `zone_failles/autopsie.txt` |

**Verdict écrit**
- Seule stratégie « validée » du fonds : Sharpe 0,40, placebo battu à 100 %, après publication +0,76
  (`fonds/resultats.txt`).
- « Validée », mais elle « échoue au premier tri » du tournoi 1 (t 0,62 sur 2011-2022) : l'avantage n'existe que
  depuis 2017 environ (`tournoi/README.md`).

**Hors échantillon**
- 2023-2026 : t 2,00. Ce n'est pas un coffre vierge pour la zone.
- Après la publication de l'article : +7,46 pt par trade, t 0,85.
- Robustesse : Sharpe 1,29 (2012-2021) puis 1,40 (2023-2026) pour le bot sans filtre. Les 14 400 variantes de
  paramètres gagnent toutes. Le sens tiré au hasard ne fait jamais aussi bien : p < 0,0001
  (`robustesse/robustesse.txt`).
- Optimisation glissante : aucune version ne bat V1 hors échantillon (`zone_optimisation/glissante.txt`).
- **Suivi virtuel (main, `zone/robot/journal.csv`)** :
  - 23 séances, du 2026-09-28 au 2026-10-28 ;
  - +497,5 $ pour 1 MNQ, alors que le backtest attendait +264 $ (voyant VERT, `zone/robot/TABLEAU_DE_BORD.md`) ;
  - compte challenge virtuel : +244,5 $.

**Régénérer les gains quotidiens** : oui, voir la section 5 (commande A et fichiers B, C, D).

**Corrélation** : c'est la référence (1).

### 1.2 RSI2 — RSI(2) de Connors sur le NQ, plusieurs jours (`tournoi8/`)

**Règle**
- Décision à 15 h 50, exécution à l'ouverture de cette minute.
- Achat si la clôture est au-dessus de la moyenne des 200 clôtures et si le RSI de Wilder sur 2 clôtures est
  sous 10.
- Vente si la clôture dépasse la moyenne des 5.
- Position gardée la nuit et le week-end. Achat seulement, 1 MNQ.

**Résultats chiffrés** (t sur les rendements quotidiens nets en %)

| Période | Résultat | Source |
|---|---|---|
| Exploration 2011-2022 | t +2,40 ; bat 95,5 % de 1 000 placements au hasard ; 100 trades ; +8 400 $ ; perte max −2 173 $ | `tournoi8/exploration8.txt` |
| Coffre 2023 - sept. 2026, ouvert une fois (seuil 1,64) | t +1,95 ; Sharpe 1,01 ; 40 trades ; +11 098 $ ; perte max −2 590 $ ; 68 % de gagnants ; 4 années sur 4 positives (+1 512 / +3 362 / +3 408 / +2 816 $) | `tournoi8/coffre8.txt` |
| 2012-2026 | t 3,05 ; +19 498 $ ; 12 années positives sur 15 | `tournoi8/sans_weekend.txt` |

**Verdict écrit**
- « PASSE ». C'est « la première stratégie qui passe toutes les étapes depuis la zone de bruit ».
- Réserves du README : sur le coffre, il ne bat que 88 % des placements au hasard (`coffre8_hasard.txt`). Il est
  passé de justesse et ne compte que 40 trades.

**Hors échantillon**
- Coffre passé.
- Robustesse : nuits du RSI(2) contre des nuits au hasard, p = 0,0003.
- **Suivi virtuel (main)** : −253 $ pour 1 MNQ depuis le 1er octobre 2026 (somme de `gain_rsi2_1_mnq`).

**Avec la zone** (`tournoi8/combinaison8.txt`)
- Corrélation quotidienne −0,06 (2011-2022) et −0,02 (2023-2026). Recalculé pour cet inventaire : −0,021.
- Sharpe 2023-2026 : zone seule 0,90, RSI(2) seul 0,94, mélange 1,31.
- Challenge Phidias, départs 2023-2024 : +254 $/an contre −22 $/an pour la zone seule.

**Régénérer** : oui (commandes A et B, section 5).

### 1.3 RSI2-EDC et RSI2-A3 — le RSI(2) à plat chaque jour

**RSI2-EDC, RSI(2) « entre deux clôtures »** (`intraday50k/`)
- Règle : mêmes signaux, achat à 18 h, à plat à 15 h 59, racheté le soir.
- Résultats (`intraday50k/README.md`) :
  - 2012-2026 : +14 802 $, t 2,29, 76 % des dollars de l'original ;
  - 2023-2026 : +8 000 $, t 1,24 ;
  - 2011-2022 : +6 802 $, t 1,93 ;
  - tout le gain se fait la nuit (+9 286 points de 18 h à 9 h 30).
- Verdict écrit : « utilisable ».

**RSI2-A3, RSI(2) de nuit seulement sur 1 MES** (`vague4/`)
- Règle : achat à 18 h, vente à 9 h 30.
- Verdict écrit : retenu chez Topstep. Gain net par achat (Topstep, 12 mois, niveau d'aujourd'hui) : +830 $ sur
  le choix 2012-2021, +803 $ en vérification 2023 - sept. 2025, contre +638 / +594 $ pour la zone seule
  (`vague4/partie_a.txt`).
- Seul, au prix d'aujourd'hui (série « nuit » de `robustesse/robustesse.json`) :
  - 2012-2026 : +19 874 $, Sharpe 0,90, pire baisse 2 369 $, 12 années positives sur 15 ;
  - 2023-2026 : +5 943 $, Sharpe 1,25.

**Hors échantillon** : les signaux viennent du RSI(2), choisi sur 2011-2022. Les vérifications 2023-2026 sont
positives.

**Corrélation avec la zone** : 0,02 à 0,03 (`robustesse/robustesse.txt`).

**Régénérer** : oui (fichiers B et C, section 5).

### 1.4 H1 — Filtre delta de 30 minutes sur la zone de bruit (`orderflow/`, `filtre_h1/`, `zone_neutre/`, `relance/`)

**Règle** : un trade de zone n'est gardé que si le delta (achats agressifs − ventes agressives) des 30 minutes qui
finissent au signal va dans son sens.

**Résultats chiffrés**

| Période | Résultat | Source |
|---|---|---|
| Exploration (84 séances, avril-juillet 2026) | 76 trades ; gardés +9,24 pt, écartés −41,25 pt ; t 1,68 | `orderflow/exploration_of.txt` |
| Coffre (43 séances, août - 1er oct. 2026) | 23 trades ; gardés (18) +67,40 pt, écartés (5) −35,15 pt ; écart +102,55 pt ; t 2,34 (seuil 1,65) | `orderflow/coffre_of.txt` |
| 6 mois (99 trades) | la zone passe de +982 à +1 777 pt, environ +1 590 $ | `orderflow/README.md` |
| Approximation P4 (prix sur 30 min), 3 465 trades 2011 - mars 2026 | t 1,62, +382 pt en 15 ans | `filtre_h1/test_gratuit.txt` |
| Delta du QQQ (Alpaca) | refusé comme remplaçant (60,7 % de signes communs) ; test descriptif t 1,82 | `filtre_h1/resultat_alpaca.txt` |
| Source LSE | refusée (85,1 % de signes communs, seuil 95 %) | `filtre_h1/README.md` |

**Verdict écrit** : filtre « confirmé » au coffre, mais « sur peu de trades écartés ». Sur 15 ans, l'approximation
n'est pas confirmée. Le filtre est dans le bot 3 en 1.

**Hors échantillon après le coffre** (export Rithmic, 7 trades, `filtre_h1/resultat_rithmic.txt`) :
- zone filtrée +220 pt contre +668 pt pour la zone seule ;
- un seul trade écarté (+447,75 pt le 16 octobre) ;
- c'est un point d'étape : il faut 150 trades pour décider.

**Régénérer sur 2011-2026** : non, faute de vrai delta avant avril 2026. On dispose de :
- les 99 trades réels d'avril à octobre 2026 : `orderflow/zone_avril_septembre_2026.csv` ;
- des versions simulées : `filtre_h1/scenario.py`, et la série `zone_f` de `robustesse/robustesse.json` (tirage
  médian, ρ 0,24).

### 1.5 REB — Rebond après une forte baisse (achat de la séance qui suit un jour dans les 10 % les plus bas)

**Où** : `tournoi4/` (stratégie 7), `zone_sources/` (piste S4), `vague7/`, robot de main.

**Résultats chiffrés**

| Mesure | Résultat | Source |
|---|---|---|
| Exploration 2011-2022 | NQ t +1,80 (2017-2022 : +2,09) ; ES t +1,48 ; bat les jours au hasard | `tournoi4/README.md` |
| S4, 2023-2026 | +8 089 $ pour 1 MNQ ; apport à la zone t 1,44 (seuil 2,33) | `zone_sources/README.md` |
| Version exécutable, 2023-2026 | +6 420 $ ; apport t 1,21 ; t de zone + rebond 1,91, contre 2,00 pour la zone seule | `zone_sources/README.md` |
| Concentration du gain | 2020 +6 408 $, 2025 +6 568 $ (dont +4 119 $ le 9 avril 2025) ; les 14 autres années ≈ +300 $ | `zone_sources/README.md` |
| Recalculé, 2012-2026, version exécutable | +13 291 $ ; 8 années positives sur 15 | recalculé pour cet inventaire |

**Verdict écrit** : rejetée selon le critère. Elle est entrée au robot sur décision de l'utilisateur, puis en est
sortie : elle est « suivie à part, hors compte ». Vague 7 : gardée sur aucun compte.

**Suivi virtuel (main)** : +854,5 $ pour 1 MNQ depuis le 1er octobre 2026 (somme de `gain_rebond_1_mnq`).

**Corrélation avec la zone** : 0,21, recalculée pour cet inventaire (séries quotidiennes à 1 MNQ, 2011-2026).

**Régénérer** : oui (commande A, colonne `rebond_1mnq`).

### 1.6 M4-ZF et M4-MYM — les deux « intéressantes » de la machine 4 (`machine4/`)

**Stratégies**
- ZF : achat d'un ZF les 5 dernières séances du mois.
- MYM : vente de MYM pendant 2 séances après une baisse du gaz naturel (NG) d'au moins 1 écart-type sur 20 séances.

**Coffre 2023-2026** (`machine4/coffre4.txt`)

| | t exploration | t coffre | $/an | Années | Corrélation avec le bot |
|---|---|---|---|---|---|
| ZF | 3,51 | +1,31 | +1 238 | −902 / +899 / +3 671 / +938 | 0,00 |
| MYM | 3,28 | +1,39 | +960 | +2 129 / +701 / +784 / −43 | +0,14 |

**Verdict écrit**
- « Intéressante », pas retenue : 26 % des 80 placebos atteignent aussi ce palier.
- ZF va au « suivi en argent virtuel ». Je n'ai trouvé ce suivi ni sur cette branche ni sur main.

**Régénérer** : pas de script prêt. Le génome est dans `machine4/coffre4.json` (clé `row`). Les fonctions
`pos_de` et `gains` sont dans `machine4/machine4.py`, sur `fonds/donnees/futures_1d.csv.gz` (2010-2026, journalier).

### 1.7 Autres résultats positifs au coffre, mais sous le seuil (rejetés)

| ID | Stratégie | Résultat sur 2023-2026 | Source |
|---|---|---|---|
| EVO1-CH | Champion de l'évolution 1 : momentum NQ, achat seul | Sharpe 0,63, t 1,21, +4 067 $ (1 micro), perte de −2 620 $ en 2025 ; « bruit 2,21 > réel 1,72 » | `evolution/README.md` |
| EVO1-CC | Cassure de canal NQ, achat seul | t 0,91, +4 708 $ | `evolution/README.md` |
| RSI2-WE | RSI(2) sans week-end | coffre t 0,90, +4 516 $ ; sur toute la période t 2,49, +12 670 $ (« utilisable ») | `tournoi8/sans_weekend.txt` |
| T10-T3 | Mardi de rebond | seconde chance : 64 trades, +1 990 $, t 0,71, bat le hasard 53,4 %, 3 années sur 4 positives ; échoue | `tournoi10/seconde_chance_mardi.txt` |
| MOF-F | Finaliste de la machine order flow | coffre 39 trades, +3,21 pt, t par séance 0,50 ; échoue | `orderflow/coffre_of.txt` |
| M5-AUD | Comblement des grands écarts du week-end sur le dollar australien | coffre t 2,58 et 2,92 : passe ; mais « non tradable sur la CME » (entrée à 18 h : t −0,49 / +0,71) | `sessions24/realisme6.txt` |
| ZB-VAR/G/S | Variantes de la zone | t 2023-2026 positifs (V2 1,48 ; V3 1,38 ; V4 2,07 ; V5 1,76 ; G1 1,56 ; G2 0,92 ; G3 1,29 ; S1 1,48 ; S2 1,64 ; S3 3,50 ; S5 1,92), mais aucune ne bat V1 selon la règle | `zone_failles/variantes.txt`, `zone_optimisation/glissante.txt`, `zone_sources/sources.txt` |

---

## 2. Tableau de toutes les stratégies et règles testées (80 lignes)

**Légende**
- **t** : t des rendements quotidiens nets en % du prix, jours sans trade compris, sauf mention contraire
  (« t $ » : sur les gains en dollars).
- **Coffre** : 2023 - sept. 2026, sauf mention.
- **Régén.** : peut-on régénérer les gains quotidiens à partir du dépôt ? (A à E : section 5 ; « fonct. » : la
  fonction existe, mais aucun export prêt.)
- **ρ zone** : corrélation quotidienne avec la zone de bruit, quand elle est mesurée.

### A. Zone de bruit et ce qui s'y greffe (NQ, intraday)

| ID | Stratégie (dossier) | Marché / UT | Règle | Périodes | Résultat clé (source) | Verdict écrit | Hors échantillon | Régén. | ρ zone |
|---|---|---|---|---|---|---|---|---|---|
| A1 ZB-V0 | Zone de bruit d'origine (`intraday/`) | NQ/MNQ, 1 min | voir 1.1, sans la correction V1 | 2011 - sept. 2026, 3 917 séances | 2 326 jours, +4,27 pt nets, t $ 2,55, +1 279 $/an, 8 années sur 16 positives (`resultats_cme.txt`) | seul résultat positif ; la limite du hasard | après publication t 0,85 ; 2023-2026 t 2,01 | fonct. `intraday/strategies.py zone_de_bruit` | 1 |
| A2 ZB-ES | Zone sur ES (`intraday/`, `zone_multi/`) | ES/MES, 1 min | même règle | 2011-2026 | −0,37 pt, t $ −0,99 ; 2023-2026 t −0,91 (`tournoi/reference_zone_coffre.txt`) | négative | 2023-2026 négative | fonct. | — |
| A3 ZB-MULTI | Zone sur 7 marchés, portefeuille à risque égal (`zone_multi/`) | RTY, YM, GC, CL, 6E (+ NQ, ES), 1 min | même règle, aucun réglage | 2016-2026 | 5 marchés sur 5 perdants (t −2,19 à −9,48) ; portefeuille Sharpe −1,45, t −4,78 (`zone_multi/README.md`) | rejeté | — | fonct. `zone_multi/analyse.py` | — |
| A4 ZB-V1 | Zone corrigée « données propres » (`zone_failles/`) | NQ/MNQ, 1 min | voir 1.1 | 2011-2022 / 2023-2026 | t +0,81 / +2,00 ; 2023-2026 +10 668 $ | **adoptée** (dans le robot et TradingView) | voir 1.1 ; virtuel +497,5 $ en 23 séances | **A, B, D, E** | 1 |
| A5 ZB-VAR | V2 1 trade par jour, V3 filtre GEX, V4 achats seuls, V5 stop sur le VWAP (`zone_failles/`) | NQ | V1 + une correction | 2011-2016 / 2017-2022 / coffre | ex. V3 t 1,99 sur 2011-2022, puis 1,38 au coffre (`variantes.txt`) | 4 rejetées | positives mais pires que V1 | fonct. `zone_failles/journal.py zone()` | ≈1 |
| A6 ZB-GLIS | Optimisation glissante G1, G2, G3 (grille de 108 réglages) (`zone_optimisation/`) | NQ | choix chaque 1er janvier | hors échantillon 2014-2022 / 2023-2026 | G1 1,97 / 1,56 ; G2 2,64 / 0,92 ; G3 2,10 / 1,29 ; V1 1,62 / 2,00 ; l'« oracle » 2,24 (`glissante.txt`) | V1 reste | toutes moins bonnes que V1 sur 2023-2026 | fonct. `zone_optimisation/moteur.py` | ≈1 |
| A7 ZB-SRC | Filtres S1 (ES), S2 (volume), S3 (tendance de fond), S5 (range de la nuit) (`zone_sources/`) | NQ | n'entre que si la condition est remplie | idem | t 2023-2026 : 1,48 / 1,64 / 3,50 / 1,92 ; t de la différence avec V1 ≤ 0 (`sources.txt`) | 4 rejetées | — | fonct. `zone_sources/sources.py` | ≈1 |
| A8 REB | Rebond après une forte baisse (`tournoi4/`, `zone_sources/` S4, robot) | NQ/MNQ, séance | voir 1.5 | 2011-2022 / 2023-2026 | t 1,80 ; S4 +8 089 $ ; version exécutable +6 420 $ | rejetée ; suivie à part | positive ; virtuel +854,5 $ | **A** | 0,21 (recalculé) |
| A9 ZB-FED | Pas de zone les jours d'annonce de la Fed (`vague9/`) | NQ | supprime ~3 % des trades | choix 2012-2021, vérification 2023-2026 | objectif tenu 66 → 68 % (choix), 87 → 88 % (vérification) ; effet petit (`vague9/README.md`) | **retenue** (petit effet), dans le mode à plat du bot | vérification positive | D (`zone_brut` l'inclut) | ≈1 |
| A10 CONF | 8 178 confluences (1 à 3 conditions parmi 29) + second jugement (`vague9/`) | NQ | trades non retenus : pas pris, ou pris sur MES | idem | seules 2 règles sur 8 178 battent le bot sur les deux périodes, les deux versions « sans Fed » ; GEX + Fed + écart d'ouverture : non retenue | rejetées sauf A9 | — | fonct. `vague9/socle9.py` | — |
| A11 H1 | Filtre delta de 30 min (`orderflow/`) | NQ, transactions | voir 1.4 | avril - oct. 2026 (84 + 43 séances) | coffre t 2,34 (5 trades écartés) | **confirmé** (dans le bot 3 en 1) | après le coffre : 7 trades Rithmic défavorables | non (E pour 2026) | filtre |
| A12 H1-APP | Approximations du delta : P1-P4 (barres minute), QQQ Alpaca, ticks LSE (`filtre_h1/`, `lse/`) | NQ, QQQ | même règle avec un delta approché | 2011 - mars 2026 (P4) ; 2016-2026 (QQQ) | P4 t 1,62 (+382 pt) ; QQQ t 1,82 ; LSE refusée (85,1 %) | non confirmé ; sources refusées | — | fonct. `filtre_h1/test_gratuit.py` | — |
| A13 N1 | « Zone neutre » : garder aussi si \|delta\| < 1 % (`zone_neutre/`) | NQ | variante de H1 | Databento 99 trades + Rithmic 7 trades | 9 trades repêchés (10 exigés) ; −368 pt sur la période Databento (`resultats.txt`) | pas de décision ; le bot garde H1 | — | non | — |
| A14 R/S | Relance R (entrer plus tard si le delta tourne), cassure forte S, R + S (`relance/`) | NQ | moteur C# du bot | P1 avril - oct. 2026, P2 2-16 oct. 2026 | R +1 860,5 pt contre H1 +1 776,8 (P1) ; +657,8 contre +220,2 (P2) ; S rejetée | R adoptée le 19 oct., **décochée le 20 oct.** (−1 002 $ en réel) | P2 positive pour R | non | — |

### B. NQ sur plusieurs jours et la nuit

| ID | Stratégie (dossier) | Marché / UT | Règle | Périodes | Résultat clé | Verdict écrit | Hors échantillon | Régén. | ρ zone |
|---|---|---|---|---|---|---|---|---|---|
| B1 RSI2 | RSI(2) de Connors (`tournoi8/`) | NQ/MNQ, décision à 15 h 50 | voir 1.2 | 2011-2022 / coffre | t 2,40 / **1,95** ; +8 400 / +11 098 $ | **passe le coffre** (dans le bot) | coffre passé ; virtuel −253 $ | **A, B, C** | −0,06 / −0,02 |
| B2 RSI2-WE | RSI(2) fermé chaque vendredi (`tournoi8/sans_weekend.txt`) | NQ | rouvert lundi à 9 h 30 | 2012-2026 / coffre | t 2,49 (+12 670 $) / t 0,90 (+4 516 $) | « utilisable », mais faible sur 2023-2026 | coffre positif, faible | fonct. `tournoi8/sans_weekend.py` | — |
| B3 RSI2-EDC | RSI(2) entre deux clôtures (`intraday50k/`) | NQ, 18 h → 15 h 59 | voir 1.3 | 2012-2026 | t 2,29, +14 802 $ ; 2023-2026 +8 000 $ | « utilisable » | positif | **B** (`gain_v`) | — |
| B4 RSI2-A1/A2/A3 | RSI(2) entre deux clôtures sur MES (A1), de nuit seulement en MNQ (A2), de nuit seulement en MES (**A3**) (`vague4/`) | NQ/ES, nuit | 18 h → 9 h 30 | choix 2012-2021, vérification 2023 - sept. 2025 | Topstep, net par achat : A3 +830 / +803 $ ; A2 +400 / +941 $ ; A1 +531 / +563 $ | **A3 retenu** (Topstep, puis Bulenox), décoché le 13 oct. (nuit interdite chez Bulenox) | vérification positive | **D** (`nuit`) | 0,02 |
| B5 T8-AUTRES | RSI(2) sur ES, Double 7, IBS, rebond de 5 jours, veille de jour férié × NQ/ES (9 essais) (`tournoi8/`) | NQ, ES | Connors, Pagonidis… | 2011-2022 | meilleurs ratés de peu : RSI(2) ES t 2,09 (94,3 %), IBS ES t 1,97 (96,8 %) (`exploration8.txt`) | éliminés | coffre non ouvert | fonct. `tournoi8.py positions()` | — |
| B6 T10 | T1 VIX tendu, T2 RSI du VIX, T4 nuit après une fin de séance en baisse, T5 plus haut de 252 séances, T6 achat piloté par la volatilité (`tournoi10/`) | NQ | Connors, Moreira-Muir… | 2011-2022 | t 1,45 / 0,77 / 0,49 / 1,47 / alpha t 0,89 (`exploration10.txt`) | éliminés | coffre non ouvert | fonct. `tournoi10.py` | −0,04 à −0,11 |
| B7 T10-T3 | Mardi de rebond (`tournoi10/`) | NQ, lundi 15 h 50 → mardi | achat si le lundi est en baisse | 2011-2022 / seconde chance 2023-2026 | t 2,09 (94,4 %) / t 0,71, +1 990 $ | éliminé, puis échoue à la seconde chance | 2023-2026 positif en $, sous le seuil | fonct. | +0,02 |
| B8 V3 | 7 sources pour le Static : W1 échéance des options, W2 cycle de la Fed, W3/W4 fin de mois achat/vente, W5 RSI(2) vendeur, W6 écart NQ/ES, W7 novembre-avril (`vague3/`) | NQ | plusieurs jours | 2011-2022 | W2 t 2,04 mais hasard 68,6 % ; W3 t 1,59 ; W5 93,3 % (`exploration3.txt`) | aucune survivante | coffre non ouvert | fonct. `vague3/vague3.py` | non calculée |
| B9 NUIT | Dérive de nuit N1 : achat à 18 h, vente à 9 h 30 (`nuit/`) | ES, NQ, 1 h | sans condition | 2010-2026 | NQ +4,84 $ par nuit, t 1,74 ; ES +0,50 $, t 0,31 (`nuit/resultats.txt`) | rejetée | — | fonct. `nuit/analyse.py` | — |

### C. Intraday classique, autres marchés (tournois)

| ID | Stratégie (dossier) | Marché / UT | Règle | Périodes | Résultat clé | Verdict écrit | Hors échantillon | Régén. | ρ zone |
|---|---|---|---|---|---|---|---|---|---|
| C1 FDS | Momentum de fin de séance (Gao 2018, Baltussen 2021), sur Yahoo puis sur la CME (`intraday/`) | ES, NQ, SPY, QQQ | 30 dernières minutes dans le sens du jour | 2011-2026 | CME, t $ : Gao ES −6,0, Gao NQ −2,6, Baltussen ES −4,7, Baltussen NQ −2,0 | rejetés (8 essais) | négatif après publication | fonct. `intraday/strategies.py` | — |
| C2 OPR5 | Range d'ouverture de 5 minutes (`intraday/`) | ES, NQ | Zarattini 2023 | 2011-2026 | NQ +0,64 pt, t $ +0,6 ; ES t −2,6 | rejeté | NQ après publication t 0,28 | fonct. | — |
| C3 T1 | 14 stratégies intraday × NQ, ES = 28 essais (`tournoi/`) | NQ, ES, 1 min | ORB 15/30/60, Williams, Crabel, gap, VWAP, Fed… | 2011-2022 | 0 sur 28 ; meilleure : Williams NQ t 0,81 (`exploration.txt`) | aucun rival | coffre non ouvert | fonct. `tournoi/concurrents.py` | Williams 0,59 ; Crabel 0,49 ; ORB 0,49-0,52 ; VWAP 0,52 |
| C4 T2 | 15 stratégies (7 indicateurs sur 5 min, 8 schémas, paire NQ/ES) = 29 essais (`tournoi2/`) | NQ, ES | réglages standards | 2011-2022 | 0 sur 29 ; ORB 5 min + volume NQ t 1,54 ; paire t −6,15 | aucun survivant | — | fonct. `concurrents2.py` | ORB5 0,28 |
| C5 T3 | GEX, DIX, VIX, profil de volume : 9 × 2 = 18 essais (`evolution2/`) | NQ, ES | G1-G3, D1, V1-V2, P1-P3 | 2011-2022 | 0 sur 18 ; G3 (zone en gamma bas) NQ t 1,86 ; D1 ES t 1,73 (`exploration3_sans_murs.txt`) | aucun survivant | — | fonct. `tournoi3.py` | G3 ≈ zone |
| C6 T4 | 8 pistes × 2 marchés (périodicité des demi-heures, fin de mois, fin de séance, range de la nuit, rebond, modèle) + paire en continuation (`tournoi4/`) | NQ, ES | — | 2011-2022 ; paire jugée sur le coffre | 0 sur 17 ; paire au coffre t −1,52 (`coffre4.txt`) | aucun survivant | paire négative | fonct. `strategies4.py` | — |
| C7 T4-ML | Modèle appris à 10 h (régression logistique), et version apprise sur le bruit (`tournoi4/modele_bruit.py`) | NQ, ES | 8 variables | 2013-2022 / 2023-2026 | vraies données t 1,09 ; appris sur le bruit = achat simple 10 h-16 h (t +1,38 sur 2023-2026) | éliminé | — | fonct. | — |
| C8 T5 | B1-B5 fin de séance sur RTY, YM, GC, CL, 6E ; C1 rapport EIA (`tournoi5/`) | autres marchés | Baltussen ; Wen et al. | 2016-2022 | 0 sur 6 (t −1,36 à −15,82) | aucun survivant | — | fonct. | — |
| C9 T6 | 7 familles × 5 marchés = 35 essais (`tournoi6/`) | RTY, YM, GC, CL, 6E | règles des tournois 1 et 4 | 2016-2022 | 0 sur 35 à t ≥ 2 ; 15 à t ≤ −2 ; rebond YM t 1,80 | aucune source | — | fonct. `tournoi6.py` | ≈0 |
| C10 T7 | Information croisée entre 7 marchés : 84 essais (`tournoi7/`) | 7 marchés | 9 h 30-10 h 30 d'une source → reste de la séance d'une cible | 2016-2022 | meilleur t +0,45 ; sous le hasard (médiane du maximum +1,03) | 0 retenu | — | fonct. `tournoi7.py` | — |
| C11 T9 | RSI(2), Double 7, rebond de 5 jours symétriques ; fin de mois ZN : 13 essais (`tournoi9/`) | GC, CL, 6E, ZN, journalier | Connors ; Hartley-Schwarz | 2011-2022 | aucun t ≥ 2 ; meilleur Double 7 euro t 1,06 | aucun survivant | — | fonct. `tournoi9.py` | — |
| C12 V7F | Version 7 adaptée aux futures : MNQ de l'ouverture à la clôture, stop 0,5 %, avec filtre (A) et sans (B) (`challenge/`) | NQ, séance | momentum mensuel | 2011-2026 | A : 3 063 trades, +1,43 $, t 0,43 ; B : 3 732 trades, +3,75 $, t 1,22 | rejetée | — | fonct. `version7_futures.py` | — |
| C13 V4B | Largeur des 10 plus grosses valeurs du Nasdaq 100 : B1-B3 (`vague4/`) | NQ + actions (Alpaca) | à 10 h, 11 h, 10 h 30 | 2016-2022 | t +0,79 / −0,13 / −0,75 | aucune survivante | coffre non ouvert | fonct. `sources_b.py` | — |

### D. Machines évolutives et grandes vagues

| ID | Machine (dossier) | Marchés / UT | Nombre de stratégies | Périodes | Résultat clé | Verdict écrit | Hors échantillon | Régén. |
|---|---|---|---|---|---|---|---|---|
| D1 EVO1 | Machine évolutive n°1 (`evolution/`) | NQ, ES, 5 min | 22 892 réelles + 23 381 sur bruit | entraînement 2011-2018, validation 2019-2022, coffre | bruit 2,21 > réel 1,72 ; champion t 1,21 au coffre | aucune retenue | 4 finalistes, voir 1.7 | fonct. `evolution/moteur.py` |
| D2 EVO2 | Machine n°2 (`evolution2/`) | NQ, ES | non lancée | — | lancée seulement si une stratégie survit au tournoi 3 | **non lancée** | — | — |
| D3 EVO3 | Machine n°3, v2.1 (`evolution3/`) | 7 marchés, 5 min, 16 familles | 139 876 réelles + 139 915 sur bruit | 2016-2019 / 2020-2022 / coffre | le bruit fait au moins aussi bien partout ; CL leader au coffre : t −0,95, −745 $ | aucun survivant | négatif | fonct. |
| D4 M4 | Machine 4 (`machine4/`) | 16 futures tradables (40 sources), journalier | 232 736 + jumeau de bruit (8 graines) | 2011-2022 / coffre | à tous les seuils, le bruit fait mieux ; 10 candidates au coffre | aucune retenue ; 2 « intéressantes » (ZF, MYM) | voir 1.6 | fonct. |
| D5 MOF | Machine order flow (`orderflow/`) | NQ, transactions | 41 567 + 42 231 au hasard | 84 séances / 43 au coffre | 1 finaliste ; coffre t 0,50 | échoue | positif, faible | non |
| D6 M5-1 | Machine 5, vague 1 : sessions (`sessions24/`) | 8 marchés HistData, 5 min | 158 | 2012-2022 | meilleur t après frais 1,21 ; effets avant frais à l'ouverture de Londres (t 2,6-3,6) | aucune survivante | coffre non ouvert (vierge) | fonct. `machine5.py` |
| D7 M5-2 | Machine 5, vague 2 : événements (`sessions24/`) | 8 marchés | 368 (352 testables) | 2012-2022 / coffre | 9 survivantes ; 2 passent le coffre (écart du week-end AUD) | non tradables sur la CME | t 2,58 / 2,92 sur le comptant | fonct. `machine6.py` |
| D8 V9 | Confluences de la vague 9 (= A10) | NQ | 8 178 | — | voir A10 | — | — | — |

### E. Order flow (en dehors du filtre H1)

| ID | Stratégie (dossier) | Marché / UT | Règle | Périodes | Résultat clé | Verdict écrit | Régén. |
|---|---|---|---|---|---|---|---|
| E1 ORD | Delta 1 min, CVD 15 min, carnet au 1er niveau, OFI, footprint empilé, absorption (6) + bandes de VWAP (`ordres/`) | ES/MES, transactions ; VWAP sur minutes 2011-2026 | suivre le signal 1 ou 5 min | 23 séances (août-sept. 2026) | carnet : −2,23 ticks nets (t −18,9) ; OFI : −1,98 ; VWAP : 7 208 trades, −1,29 pt, t −7,5 (`ordres/README.md`) | « vrai signal, trop petit » ; rejetés | fonct. `vwap.py` |
| E2 ORD-COND | Les 6 signaux × 2 durées × 15 conditions = 180 cas (`ordres/CONDITIONS.md`) | ES | t ≥ 3,45 exigé | 23 séances | 0 sur 180 ; meilleur t 1,58 | aucune case efficace | — |
| E3 OF-H2-5 | Absorption, gros ordres, divergence du CVD, delta 15 min (`orderflow/`) | NQ | idées fixées d'avance | 84 séances | H2 t 0,69 ; H3 t −2,97 ; H4 t 0,01 ; H5 : 2 trades | éliminées | — |

### F. Multi-marchés, fonds, actions, crypto

| ID | Stratégie (dossier) | Marché / UT | Résultat clé | Verdict écrit | Hors échantillon / virtuel | Régén. | ρ zone |
|---|---|---|---|---|---|---|---|
| F1 TEND | Tendance EWMAC 16/64, 32/128, 64/256 sur 19 marchés + 15 variantes (`tendance/`) | ETF et futures, journalier | 2007-2026 Sharpe 0,56, pire baisse −36 % ; 2023-2026 Sharpe −0,16 ; 40 futures Sharpe −0,01 (`fonds/resultats.txt`) | système « réel et robuste », compte de 50K trop petit ; fonds : rejetée ; ajoutée au bot (piste 6) : refusée | **virtuel main : −1 434 $** (au 2026-10-28) | fonct. `tendance/systeme.py`, `protection/piste6.py tendance()` | −0,07 / −0,08 |
| F2 MEL | Mélange 50/50 tendance + achat (`tendance/`, piste 7) | idem | Sharpe 0,78, pire baisse −19 %, 0,37 sur 2023-2026 ; ajouté au bot : M100 +3 617 $/an mais pire jour −2 739 $ | robot principal virtuel ; ajouté au bot : refusé | **virtuel main : −954 $** | fonct. `systeme.positions_melange`, `piste7.py` | 0,11 (avec le bot) |
| F3 ACHAT | Acheter tout, tout le temps (parité des risques) ; achat de 40 futures (`fonds/`) | 40 futures, journalier | Sharpe 0,24, t 0,96, après publication +0,29 | **validée** (prime de risque) | — | fonct. `fonds/sources.py achat40()` | −0,03 |
| F4 CARRY-FX | Carry sur 6 devises, signe et croisé (`tendance/carry.py`) | devises | Sharpe −0,16, pire baisse −70 % | rejeté | — | fonct. | — |
| F5 FONDS-REJ | Momentum croisé, valeur sur 5 ans, tournant du mois, tendance sur 40 futures (`fonds/`) | 40 futures / actions | Sharpe −0,04 / −0,75 / 0,14 / −0,01 ; placebo 49 / 1 / 52 / 59 % | rejetées | après publication ≤ +0,19 | fonct. `fonds/sources.py` | −0,05 / 0,06 / −0,01 / −0,07 |
| F6 FONDS-FED | Veille de la Fed (Lucca-Moench), 125 annonces (`fonds/`) ; ajoutée au bot en 1 MES (piste 6) | ES, journalier | Sharpe 0,34, placebo 87 % ; dans le bot : +113 $/an | rejetée (règle 4) ; dans le bot : refusée | après publication +0,50 (11,6 ans) | fonct. `sources.veille_fomc()`, `piste6.veille_fed()` | −0,00 |
| F7 FONDS-VOL | Actions pilotées par la volatilité (Moreira-Muir) (`fonds/`) | actions | Sharpe 0,50, t 2,63, placebo 86 % | rejetée (règle 4) | après publication +0,51 | fonct. `vol_geree()` | −0,10 |
| F8 FONDS-CARRY | Carry croisé sur 40 futures (KMPV 2018) (`fonds/`) | 40 futures | Sharpe 0,25, placebo 88 % | rejetée (règle 4) | après publication +0,02 | fonct. `carry40()` | −0,00 |
| F9 PAIRES | Paires cointégrées, futures et actions (`paires/`) | ETF, actions | Sharpe −0,45 / +0,22 (≈0 depuis 2013) | rejetées | — | fonct. | — |
| F10 SECT | Secteurs : v1-v4 + v5, v6 (filtre 200 jours) + v7 (moitié v2, moitié liquidités), 20 ans et 5 ans (`secteurs/`) | XLK et actions, mensuel | v7 sur 5 ans : +23,8 %/an, pire baisse −23 %, placebo 93 % (95 % exigé) | 0 version ne passe | **virtuel main (version7) : −1 060 $** | fonct. `secteurs/strategies.py` | — |
| F11 DOGE | DOGE à 2 h, 13 h et 23 h : 3 heures × 4 règles (`doge/`) | DOGE/USDT, 5 min | les 12 perdent après frais | rejeté | — | fonct. | — |
| F12 MULTI | Bot « multi » : zone + panier de nuit (tendance + achat, Fed, vol pilotée, carry) (`challenge/`) | — | f 0,15 : 86 % réussis sans limite de temps, en 20 mois médians | descriptif, « optimiste » | — | fonct. `challenge/finance.py` | — |

### G. Gestion du compte, de la taille et des comptes (pas des sources d'avantage)

| ID | Règle (dossier) | Résultat clé et verdict écrit (source) |
|---|---|---|
| G1 | Taille par coussin f = 0,15 / 0,25 / 0,35 (`challenge/`) | Phidias 36 % validés en 12 mois (20 % sans avantage) ; descriptif, f choisi sur les mêmes données |
| G2 | Tout miser sur un trade (`challenge/audace.py`) | 31-34 % de réussite, sans avantage ; rejeté |
| G3 | 1 MNQ minimum (`zone_taille/`) | validé en 12 mois : 21 → 32 % (2011-2021), 42 → 67 % (2023-2025) ; ~0,9 compte perdu de plus par an ; adopté à la demande |
| G4 | 128 gestions de retrait, Phidias (`zone_retrait/`) | la gestion choisie échoue au contrôle (−70 contre −22 $/an) ; gestion actuelle gardée |
| G5 | 128 gestions zone + RSI(2) (`zone_deux/`) | contrôle : choisie −7 $/an contre +254 $/an ; f 0,15 gardé |
| G6 | Plusieurs comptes ; frein contre les comptes perdus (4 règles) (`comptes/`) | N comptes = N fois un compte ; frein non adopté |
| G7 | Protections A-D : coupe-circuit, stop du RSI(2), plafond (`protection/`) | aucune retenue ; le stop du RSI(2) supprime ses rebonds |
| G8 | Pistes 2-4 : zone d'abord, 2 MNQ, plafond de 500 $ (`protection/`) | Z et 2 MNQ refusés ; plafond 500 $ : 1 081 $ reçus contre 249 $, mais 45 % de comptes Pro perdus (seuil 40 %) |
| G9 | Piste 5 : comptes DayTraders (`protection/`) | S2F + plafond 500 $ : 83 % de retraits, +1 826 $ en 12 mois (descriptif) |
| G10 | Pistes 6-7 : T100, T30, F (Fed), M100, M30 en 4e source | toutes refusées |
| G11 | Comptes 50K intraday et phase financée (`intraday50k/`) | Topstep seul paie : 55 % de retraits, +152 $ nets |
| G12 | Static 50K : 14 candidates E0-E6 × P0/P500 (`static50k/`) | **E0 P500 retenue et validée** : +875 / +690 $ par achat ; achats 2025 −60 $ |
| G13 | Un compte Topstep (`vague4/un_compte.py`) | +141 $/mois sans filtre, +410 $/mois avec le filtre simulé (descriptif) |
| G14 | Vague 5 : 40 candidates (`vague5/`) | **Topstep zone + A3, challenge 2×, financé 2×, retenue et validée** : +557 / +388 $ par mois |
| G15 | Vague 6 : 42 candidates + suite S2L (`vague6/`) | LucidFlex zone + A3, 3× / 2× : +593 / +481 $ par mois (retenue) |
| G16 | Vague 7 : le rebond sur 5 comptes ; réglage prudent (`vague7/`) | rebond gardé sur aucun compte ; LucidFlex reste en tête |
| G17 | Vague 8 : 60 candidates de taille (`vague8/`) | aucune sûre et validée ; LucidFlex 100K +316 / +233 $ par mois |
| G18 | Vague 10 : 72 freins (`vague10/`) | aucune sûre sur 2012-2021 ; frein MES sous 1 500 $ (descriptif) |
| G19 | Vague 11 : plafond sur le Master Bulenox (`vague11/`) | 500 $ choisi, non validé au net (+3 744 $ contre +3 835 $) |
| G20 | Vague 12 : taille 1 à 4 pour un challenge de 30 jours (`vague12/`) | **taille 4 sans frein, retenue et validée** : 41 % / 40 % validés en 30 jours, contre 5 % / 2 % |
| G21 | Vague 13 : versions A-F (`vague13/`) | **D (arrêt à l'objectif + fin de course) retenue** : 53 % (2012-2021) / 55 % (2023-2026) / 45 % (2025) |
| G22 | Monte Carlo, labo30, mc30, robustesse | descriptifs ; robustesse : PBO 30 %, walk-forward 5 829 $/an contre 6 943 $/an pour le bot fixe |

**Nombre de lignes** : 80 (A 14, B 9, C 13, D 8 dont 1 qui renvoie à A10, E 3, F 12, G 22). Avec les machines,
elles couvrent ≈ 446 000 stratégies réelles évaluées (22 892 + 139 876 + 232 736 + 41 567 + 526 + 8 178), sans
compter les versions sur bruit.

---

## 3. Corrélations avec la zone de bruit (mesurées)

| Stratégie | Corrélation quotidienne | Source |
|---|---|---|
| RSI(2) NQ | −0,06 (2011-2022), −0,02 (2023-2026) ; −0,021 recalculé (2023-2026) | `tournoi8/combinaison8.txt` |
| RSI(2) de nuit sur MES (A3) | 0,022 (zone filtrée), 0,03 (zone sans filtre) | `robustesse/robustesse.json` |
| Tendance multi-marchés | −0,068 ; −0,07 (tendance sur 40 futures) | `robustesse.json`, `fonds/resultats.txt` |
| Achat permanent NQ | −0,045 | `robustesse.json` |
| Rebond après une forte baisse | 0,21 | recalculé pour cet inventaire |
| Fonds : achat40, carry, vol pilotée, tournant du mois, Fed, momentum, valeur | −0,03 / −0,00 / −0,10 / −0,01 / −0,00 / −0,05 / +0,06 | `fonds/resultats.txt` |
| Tournoi 1 : Williams, Crabel, ORB, VWAP, continuation du gap, 1re heure | 0,59 / 0,49 / 0,49-0,52 / 0,52 / 0,31-0,32 / 0,35 | `tournoi/exploration.txt` |
| Tournoi 10 : T1-T6 | −0,04 / −0,06 / +0,02 / −0,10 / −0,11 / −0,07 | `tournoi10/README.md` |
| Machine 4 : ZF, MYM | 0,00 / +0,14 (avec le bot, 2023-2026) | `machine4/coffre4.txt` |
| Veille de la Fed (1 MES), mélange (avec le bot) | +0,09 / +0,11 | `protection/piste6.txt`, `piste7.txt` |

---

## 4. Stratégies « pas finies »

1. **Filtre H1 sur des années** : le vrai delta n'existe qu'à partir d'avril 2026.
   - La décision est fixée à 150 trades hors avril - octobre 2026 ; 7 sont mesurés (Rithmic, 18 oct.).
   - Il manque l'export des contrats expirés NQU6, NQM6, NQH6…
   - Databento est verrouillé (« account locked »).
2. **Zone neutre N1** : pas de décision (9 trades repêchés sur 10). L'étude est à relancer avec de nouveaux exports.
3. **Bot 3 en 1 virtuel (main)** : en pause depuis le 2 octobre (18 séances en attente du vrai delta Databento).
4. **ZF fin de mois (machine 4)** : « va au suivi en argent virtuel ». Le suivi n'a pas été trouvé sur main ni sur la
   branche.
5. **Rebond après une forte baisse** : suivi à part dans le robot de main, +854,5 $ depuis le 1er octobre.
6. **Suivis virtuels jeunes** (main, démarrés les 25-28 septembre) :
   - zone +497,5 $ ;
   - RSI(2) −253 $ (depuis le 1er octobre) ;
   - tendance −1 434 $ ;
   - mélange −954 $ ;
   - version 7 −1 060 $.

   Le dépôt dit « trop tôt pour juger ». Le prochain bilan de la zone est prévu à 60 séances.
7. **Tournoi 5, familles A1/A2 (fixings des devises), D1 (bitcoin CME), E1/E2 (adjudications ZN)** : les règles
   sont fixées et les données ont été téléchargées le 1er octobre (`tournoi5/donnees/`). Je n'ai trouvé aucun
   résultat.
8. **Tournoi 7** : les sources ZN, dollar et bitcoin, ainsi que la partie B (familles du tournoi 6 sur le bitcoin),
   « attendent le téléchargement du tournoi 5 ». Le code existe (`tournoi7/partie_b.py`). Résultats non trouvés.
9. **Tournoi 3, murs d'options W1-W3** : en attente des données. Seuls des échantillons sont présents
   (`evolution2/donnees/echantillon_*`). La machine évolutive n°2 n'est pas lancée, par décision de l'utilisateur.
10. **Machine 5, vague 1** : le coffre 2023-2026 n'a pas été ouvert. Il reste vierge pour ces 158 stratégies.
11. **Essai en démo Optimus / Ironbeam du bot (7-16 octobre)** : les critères du « feu vert » sont écrits
    (`bot3en1/README.md`). Le bilan n'a pas été trouvé.
    - Trading réel mentionné : le 16 octobre, aucun prix reçu, une vente de 449 points manquée ; le 20 octobre,
      −1 002 $ (Bulenox, 4 MNQ).
12. **Vague 13** : elle n'est pas dans `fonds/essais.csv` (journal arrêté à la vague 12). Les leviers ont été
    proposés après avoir vu la vague 12.

---

## 5. Régénérer les gains quotidiens (NQ 2011-2026)

| Clé | Ce qu'on obtient | Commande / fichier | Période | Vérifié |
|---|---|---|---|---|
| **A** | Zone V1 (`zone_v1_1mnq`), RSI(2) d'origine (`rsi2_1mnq`), rebond exécutable (`rebond_1mnq`) ; $ pour 1 MNQ, prix de l'époque | voir le bloc ci-dessous | du 2011-03-02 au 2026-09-25 (3 910 séances) | oui : 2023-2026 zone +10 668,5 $, RSI(2) +11 098,5 $, rebond +6 420 $ ; RSI(2) 2012-2026 +19 498 $, comme le dépôt |
| **B** | RSI(2) d'origine (`gain_o`) et entre deux clôtures (`gain_v`), $ pour 1 MNQ | fichier : `intraday50k/rsi2_entre_deux.csv.gz` ; refaire : `cd intraday50k && python3 rsi2_jour.py` (lit aussi `nuit/donnees/nasdaq100_1h.csv.gz` ; réécrit le fichier dans le dépôt) | du 2011-01-03 au 2026-09-25 | oui : gain_o 2012-2026 +19 498 $ ; gain_v +14 802 $ |
| **C** | Bot zone V1 + RSI(2), 1 MNQ chacun, sans filtre | fichier : `machine4/bot_quotidien.csv` ; refaire : `cd machine4 && python3 bot_quotidien.py` (réécrit le fichier) | du 2012-01-05 au 2026-09-25 | oui : 2023-2026 +21 767 $, comme le rejeu C# ; total +40 358,5 $ |
| **D** | Au prix d'aujourd'hui (NQ ≈ 30 900) : `zone_brut` (zone 1 MNQ sans les jours Fed), `nuit` (RSI(2) de nuit 1 MES = A3), `zone_f` (zone filtrée simulée, tirage médian), `bot`, `bot_brut` | `robustesse/robustesse.json` → `equite.series` (cumuls arrondis au dollar ; prendre la différence jour par jour) ; refaire : `cd robustesse && python3 robustesse.py` (long ; réécrit le JSON) | du 2012-01-03 au 2026-09-25 (3 783 séances) | totaux du JSON : zone_brut +77 690 $, nuit +19 874 $ |
| **E** | Liste des trades de zone V1 (points nets) | `filtre_h1/trades_zone.csv` ; refaire : `cd filtre_h1 && ROBOT_ZONE=../protection/robot_main.py python3 trades_zone.py` | 3 465 trades, du 2011-01-24 au 2026-03-31 | lu |
| — | Trades de zone avec le vrai delta | `orderflow/zone_avril_septembre_2026.csv` (99 trades) ; `filtre_h1/donnees_rithmic/` + `python3 filtre_h1/test_rithmic.py` | du 2026-04-01 au 2026-10-02 ; du 2026-09-16 au 2026-10-16 | lu |
| — | Bot C# exact (zone, filtre, RSI(2), mode à plat) | `dotnet run -c Release --project bot3en1/Bot3en1.Replay -- intraday/donnees/nasdaq100_1min.csv.gz - 2011-01-03 2026-09-25` avec `SANS_FILTRE=1` (il faut .NET 8 ; l'exemple du dépôt part du 2023-01-03, une période plus longue n'est pas vérifiée) | 2023-2026 vérifié dans le dépôt (+21 767 $) | non exécuté ici |

**Commande A** (lecture seule ; le script est dans le scratchpad, hors du dépôt) :

```
cd /tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad/inventaire/outils
PYTHONDONTWRITEBYTECODE=1 ROBOT_DEBUT_RSI2=2000-01-01 ROBOT_DOSSIER=/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad/inventaire/robot_tmp \
  python3 series_nq.py <dossier kb> series_nq_quotidiennes.csv
```

- Le script appelle `serie_du_bot` de `protection/robot_main.py`, qui est la copie du robot de main (commit a3c585f).
- Résultat déjà produit : `.../scratchpad/inventaire/outils/series_nq_quotidiennes.csv`.
- Sans `ROBOT_DEBUT_RSI2=2000-01-01`, le RSI(2) ne commence que le 1er octobre 2026.

**Autres régénérations possibles** (la fonction existe, mais aucun export n'est prêt)

| Stratégie | Fonction | Données |
|---|---|---|
| Zone V0 | `intraday/strategies.py zone_de_bruit` | minutes du NQ |
| Variantes de la zone | `zone_failles/journal.py zone()`, `zone_optimisation/moteur.py` | minutes du NQ |
| Rebond S4 | `zone_sources/sources.py rebond()` | minutes du NQ |
| Tournois 8 et 10 | `positions()` dans chaque script | minutes du NQ |
| RSI(2) sans week-end | `tournoi8/sans_weekend.py` | minutes du NQ |
| Veille de la Fed (1 MES) | `protection/piste6.py veille_fed()` | minutes de l'ES |
| Tendance, mélange | `protection/piste6.py tendance()`, `piste7.py` | prix de la tendance (2007-2026) |
| Sources du fonds | `fonds/sources.py` (rendements en %) | futures journaliers |
| ZF, MYM | `machine4/machine4.py` (génome dans `coffre4.json`) | futures journaliers |
| Champion de l'évolution 1 | `evolution/moteur.py` (génome dans `resultats_coffre.json`) | barres de 5 minutes |

**Prix de l'époque ou prix d'aujourd'hui** : pour combiner des sources, il faut prendre toutes les séries dans le même
référentiel (A, B, C, ou bien D).

---

## 6. Classement des stratégies avec une preuve hors échantillon positive (de la plus solide à la moins solide)

| Rang | Stratégie | Chiffre clé hors échantillon | Pourquoi ce rang | Régén. 2011-2026 |
|---|---|---|---|---|
| 1 | **Zone de bruit V1, NQ** (A4) | 2023-2026 t 2,00, +10 668 $ ; virtuel +497,5 $ en 23 séances (attendu +264 $) | plusieurs preuves qui se recoupent : après publication, robustesse (OOS 1,29 → 1,40, 14 400 variantes gagnantes, p < 0,0001), virtuel positif. Réserves : 2023-2026 déjà vu, gains seulement depuis 2017-2018 | **A** (2011-03 → 2026-09), D, E |
| 2 | **RSI(2), NQ** (B1) | vrai coffre passé : t 1,95, +11 098 $, 4 années sur 4 | seule stratégie qui ait passé un coffre fermé. Réserves : 40 trades, 88 % contre le hasard au coffre, virtuel −253 $ | **A**, **B** (2011-01 → 2026-09) |
| 3 | **RSI(2) de nuit sur MES (A3)** (B4) | vérification 2023-2025 : +803 $ par achat (Topstep) ; nuit 2023-2026 Sharpe 1,25 | mêmes signaux que le 2 ; règle choisie sur 2012-2021, vérifiée ensuite | **D** (2012-01 → 2026-09) |
| 4 | **RSI(2) entre deux clôtures** (B3) | 2023-2026 +8 000 $ (t 1,24) | dérivé du 2, positif mais t plus faible | **B** |
| 5 | **Filtre delta H1** (A11) | coffre t 2,34 (5 trades écartés) | confirmé sur très peu de trades ; non confirmé sur 15 ans (approximation) ; après le coffre, 7 trades défavorables | non (2026 seulement) |
| 6 | **Rebond après une forte baisse** (A8) | 2023-2026 +6 420 $ ; virtuel +854,5 $ | positif mais fait de krachs (2020, 2025) ; critère raté (t 1,21-1,44) | **A** |
| 7 | **ZF, fin de mois** (D4) | coffre t 1,31, +1 238 $/an, 3 années sur 4 | sens économique, ρ 0 avec le bot ; mais autant de passages que les placebos (26 %) | non (fonct.) |
| 8 | **MYM contre le gaz** (D4) | coffre t 1,39, +960 $/an | sans sens économique clair ; ne fait mieux qu'en échantillon une fois ajouté au bot | non (fonct.) |
| 9 | **Champion de l'évolution 1** (momentum NQ, achat seul) | coffre t 1,21, +4 067 $ ; 2025 −2 620 $ | battu par le bruit ; le gain suit la hausse du Nasdaq | non (fonct.) |
| 10 | **RSI(2) sans week-end** (B2) | coffre t 0,90, +4 516 $ | variante du 2, faible sur 2023-2026 | fonct. |

**Hors classement**
- Mardi de rebond (t 0,71, +1 990 $) : échoue.
- Finaliste order flow (t 0,50).
- Écart du week-end sur l'AUD : passe le coffre sur le comptant, mais non tradable sur la CME.
- Veille de la Fed et vol pilotée : positives seulement après publication (+0,50 et +0,51 de Sharpe).
- Tendance, mélange, version 7 : virtuels négatifs.

**Règles de gestion validées sur la période de vérification** (pas des sources d'avantage) :
- E0 P500 (Static) : +690 $ par achat ;
- Topstep zone + A3, 2× / 2× : +388 $/mois ;
- LucidFlex : +481 $/mois ;
- vague 12, taille 4 : 40 % validés en 30 jours ;
- vague 13, D : 55 % ;
- pas de zone les jours de la Fed.

**Séries quotidiennes 2011-2026 disponibles pour les combiner**
- Zone V1, RSI(2), rebond : A, de 2011 à 2026, prix de l'époque.
- RSI(2) d'origine et entre deux clôtures : B.
- Bot zone + RSI(2) : C, depuis 2012.
- Au prix d'aujourd'hui (zone, nuit A3, zone filtrée simulée) : D, depuis 2012.

Aucune série réelle 2011-2026 n'existe pour le filtre H1. ZF, MYM et le champion de l'évolution 1 demandent un
script à écrire.
