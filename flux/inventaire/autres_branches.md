# Inventaire des stratégies testées hors `claude/keen-babbage-r686cl` et hors `flux/`

Branches lues le 29 octobre 2026 (après `git fetch`, sans checkout) : `claude/exciting-fermat-sea2l2` (dossiers
`scalping/`, `bot3en1/`), `claude/elegant-ptolemy-g94s8t` (`entree_tardive/`), `claude/fervent-wright-21hspi`
(`delta_mesures/`, `zone_retour/`, `donnees_libres/`), `claude/affectionate-turing-tnz0mn` (`etude_large/` et ses vagues),
`main` (`zone/`, `tendance/`, `version7/`, `bot3en1/`, `README.md`, `main.py`).

Conventions des chiffres (celles des fichiers) :
- « t » = t des gains **quotidiens** nets (séances jouables, 0 sans trade) sauf mention ; « t 11-22 / 23-26 » = deux
  périodes ; MNQ = 2 $ par point ; « prix d'aujourd'hui » = gains ramenés au niveau du NQ récent (≈ 29 700 à 30 900).
- « Validé % » sans précision dans les sections `scalping/` = challenge Bulenox depuis 49 500 $, marge 1 000 $, 13
  séances, 4 puis 6 MNQ, départs 2012-2026 (fichiers `scalping/resultats/j/*.txt`).
- Les chiffres marqués **(calculé ici)** ne viennent pas d'un fichier du dépôt : ils sortent des commandes de
  régénération de la section 6, lancées le 29 octobre 2026 pour les vérifier (elles redonnent les chiffres publiés).
- « non trouvé » = absent des fichiers lus.
- Volume : **159 lignes d'inventaire** (sections 1 à 3 ; environ 190 stratégies ou variantes en dépliant les lignes
  groupées), plus les machines évolutives comptées chacune sur une ligne (v4 : 593 125 stratégies sur vraies données ;
  v5 : environ 890 000).

---

## 1. Robots virtuels de `main` : résultats réels depuis leur démarrage (vrai hors échantillon)

Sources : `README.md`, `zone/robot/journal.csv`, `zone/robot/etat.json`, `zone/robot/TABLEAU_DE_BORD.md`,
`tendance/robot/journal.csv`, `tendance/robot/journal_melange.csv`, `tendance/robot/TABLEAU_DE_BORD.md`,
`version7/robot/journal.csv`, `version7/robot/TABLEAU_DE_BORD.md` (mis à jour le 2026-10-28). Les colonnes t, écart-type,
pire baisse et corrélations sont **(calculé ici)** sur les journaux (`outils/live.py`) : trop peu de séances pour conclure.

| Robot (source de la règle) | Départ | Séances | Résultat depuis le départ | Détail | Ce qu'attendait l'historique | Voyant / état |
|---|---|---|---|---|---|---|
| **Zone de bruit V1, NQ, 1 MNQ** (`zone/robot.py`) | 2026-09-28 | 23 | **+497,5 $** pour 1 MNQ (`etat.json` `gain_1_mnq`) | 14 jours non nuls, 5 + / 9 − ; meilleur +895,5 $ (16/10), pire −364,5 $ ; pire baisse 718,5 $ ; t +0,39 (calculé ici) | +264 $ attendus après 23 séances ; alerte sous −1 333 $ (`TABLEAU_DE_BORD.md`) | **VERT** ; bilan à 60 séances vers le 21/12/2026 |
| **RSI(2) Connors NQ** (second moteur dans le compte, depuis 2026-10-01) | 2026-10-01 | 20 | **−253,0 $** pour 1 MNQ (`etat.json` `gain_rsi2_1_mnq`) | 6 jours en position : +907 / −1 679 (16/10) / −222,5 / +742 … | coffre 2023-2026 : +11 098 $, t 1,95 (`zone/README.md`) | pas de voyant propre |
| Compte Phidias 50K virtuel (zone + RSI(2), taille f = 0,15) | 2026-09-28 | 23 | **+244,5 $** (solde 50 244,5 $), challenge n°1 en cours, marge 2 293 $ | pire jour −783,5 $ (16/10) | zone + RSI(2) : +254 $/an nets, 27 % de départs sans rien (rejeu Phidias) | en cours |
| Rebond après forte baisse (suivi à part, hors compte) | 2026-10-01 | 20 | **+854,5 $** pour 1 MNQ (`etat.json`) | 3 trades : +787,5 / −116 / +183 | « non validé statistiquement » ; ≈ 24 achats/an | — |
| Filtre delta H1 (suivi à part) | 2026-10-01 | — | **non mesuré** : « Pas encore de trade de zone mesuré depuis le 2026-10-01 » (Databento bloqué, solde impayé 88,01 $) | — | coffre t 2,34 | en attente |
| Bot 3 en 1 virtuel (zone filtrée delta + RSI(2), 1 MNQ chacun, `journal_combine.csv`) | 2026-10-02 | 1 jouée | **+0 $** ; **EN PAUSE**, 18 séances en attente du vrai delta | — | rejeu avr.-sept. 2026 : challenge réussi en 3-4 mois, marge mini 50 $ | pause |
| **Mélange tendance 50/50 + achat**, 19 futures (`tendance/robot.py`) | 2026-09-25 | 24 | **−954 $ (−1,9 %)**, solde 49 046 $ ; baisse depuis le plus haut −2,4 % | moy. −32,6 $/j, écart-type 174 $, pire jour −368,7 $, pire baisse 1 346 $ (calculé ici, frais du 1er jour à part) | zone normale à ce stade : −1 891 à +2 740 $ | 🟡 zone normale ; challenge Phidias en cours, marge 1 270 $ |
| **Tendance seule**, 19 futures | 2026-09-25 | 24 | **−1 434 $ (−2,9 %)**, solde 48 566 $ | pire jour −905,5 $ (22/10), pire baisse 2 554 $ (calculé ici) | zone normale : −2 011 à +2 620 $ | 🟡 ; **challenge Phidias perdu le 2026-10-22** |
| **Version 7** (5 actions tech, 50 % investi) | 2026-09-28 (1er rééquilibrage 30/09) | 22 | **−1 060 $ (−2,1 %)**, solde 48 940 $ | pire jour −1 086 $ (16/10), pire baisse 3 594 $ (calculé ici) | backtest 2021-2026 +21,6 %/an ; « rejetée par le critère 8 » | challenge CFD en cours, −1 048 $ |

Corrélations quotidiennes depuis le départ (calculé ici, 22-23 séances, non significatives) : zone / tendance −0,47,
zone / mélange −0,30, zone / version 7 −0,65, zone / RSI(2) −0,72 (20 séances, dont 6 en position).

`main.py` (« Bot Scalping M5 Pro », EMA9/21 + RSI7 + volume sur BTC, ETH, XAU en 5 minutes, signaux Telegram toutes les
5 minutes via `.github/workflows/bot.yml`) : **jamais backtesté** (aucun résultat trouvé).

---

## 2. Configurations successives du bot 3 en 1 (Quantower)

Sources : `main:bot3en1/README.md` (version d'origine), `exciting-fermat:bot3en1/README.md`, `scalping/README.md`,
`scalping/resultats/j/*.txt`, `entree_tardive/`, `delta_mesures/`. Points = points bruts 1 MNQ frais déduits, 2011 - 23 oct.
2026. « Validé » = Bulenox 49 500 $, marge 1 000 $, 13 séances ; « neuf » = challenge neuf 21 séances.

| # | Configuration (date) | Trades 15 ans | Points | t 11-22 / 23-26 | Journées à −1 000 $ (4 MNQ) | Validé / perdu | Neuf 21 s. | Autres chiffres | Source |
|---|---|---|---|---|---|---|---|---|---|
| B0 | **Origine (3 oct.)** : zone V1 aux contrôles de 30 min (10 h - 15 h 30) + filtre delta H1 + RSI(2), 1 MNQ par source | — | — | — | — | — | — | avr.-25 sept. 2026 vrai delta : zone 77 gardés / 20 écartés +3 830 $, RSI(2) 5 trades +536 $, **total +4 366 $** ; 2023-25 sept. 2026 sans filtre **+21 767 $**, RSI(2) +11 098,5 $ (40 trades) | `main:bot3en1/README.md` |
| B0' | Zone aux contrôles **sans filtre** (« bot d'avant ») | 3 577 | +10 558 | **+3,75 / +2,27** | 638 | 24,2 % / 67,6 % | 48,0 % | 4 MNQ : 2023 +32 301 $, 2024 +16 655 $, 2025 −4 531 $, 2026 +2 926 $ ; autre convention (`entree_tardive`) : 3 572 trades, +10 721 pts, t +2,12 / +1,86, challenge 16 séances 44,9 % | `reglages_26oct_g.txt`, `partie_j.txt` |
| B1 | Filtre delta H1 coché (défaut jusqu'au 26 oct.) | 79 trades P1 | P1 +1 776,8 ; P2 +220,2 | explo (avr.-juil.) t 1,68 ; coffre (août-1er oct.) **t 2,34** ; 15 ans par approximation t 1,62 | — | — | — | sans filtre : P1 +982,2 (99 trades), P2 **+669,5** ; Lucid simulé « filtre aussi bon qu'en 2026 » 76,4 % contre 56,2 % (hypothétique) | `delta_mesures/resultats.txt`, `main:zone/README.md`, `lucid_27oct_filtre.txt` |
| B2 | Mode à plat Bulenox (10 oct.) : RSI(2) de nuit sur MES, frein, pas de zone les jours de la Fed, plafond 500 $ au Master | — | — | — | — | vague 13 version D : 53-55 % (avec filtre simulé) ; 49 % sans filtre (départs 2023-2026) | — | — | `bot3en1/README.md`, `etude_large/README.md` |
| B3 | RSI(2) de nuit **décoché** (13 oct.) | — | — | — | — | 54,4 % sans contre 54,6 % avec (2012-2026) | — | 2025 : 41,5 % contre 44,7 % | `bot3en1/README.md` |
| B4 | **Relance** du filtre (19 oct., décochée le 20 oct.) | 83 (P1) | P1 +1 860,5 ; P2 +657,0 | — | — | P1 : 39,4 % contre 41,7 % | — | 5 relances en 136 séances ; 20 oct. −1 002 $ réel | `entree_tardive/resultats_delta.txt` |
| B5 | Filtre delta **décoché** (26 oct.) = zone seule aux contrôles | voir B0' | | | | | | 7 trades Rithmic depuis le 2 oct. : zone seule +668 pts, filtrée +220 | `bot3en1/README.md` |
| B6 | **Entrée à la cassure** J0 (26 oct.) | 5 921 | +2 629 | +2,55 / +0,93 | 789 | 24,3 % / 70,5 % | 45,4 % | 2025 −1 412 pts, 2026 −424 pts | `partie_j.txt`, `reglages_26oct_b.txt` |
| B7 | **Laisser courir** L1a (26 oct.) | 2 769 | +5 120 | +2,31 / +0,88 | 585 | 25,1 % / 68,7 % | 45,8 % | 2026 +232 $ (4 MNQ) | `partie_l.txt`, `partie_p.txt` |
| B8 | Cassure **confirmée par le volume ×2** M1V (26 oct.) | 2 521 | +6 387 | +2,86 / +1,09 | 594 | 23,7 % | — | | `partie_m.txt` (README) |
| B9 | Sortie dès retour au niveau cassé N1 (ajoutée puis retirée) | 2 769 | +4 043 | +2,22 / +1,28 | 148 | 21,7 % / 59,2 % | — | 2026 −4 036 $ | `partie_n.txt`, `reglages_26oct.txt` |
| B9' | N1 + volume ×2 (« CHOIX » du 26 oct. matin) | 2 521 | +4 563 | +2,71 / +0,97 | 195 | 21,0 % / 63,0 % | — | 2026 −7 147 $ | `reglages_26oct.txt` |
| B10 | **Version A** : cassure + volume ×2, sorties d'origine (installée le 26 oct. soir) | 4 445 | +8 569 | **+3,39 / +1,88** | 677 | **25,2 % / 67,6 %** | 46,9 % | 2025 +5 157 $, 2026 +1 131 $ ; Lucid 1 MNQ 55,5 % / 57,5 % | `reglages_26oct_b.txt`, `lucid_27oct.txt` |
| B10b | Version B : 1 entrée/jour + volume, tenue jusqu'à 16 h ou −1 000 $ | 2 264 | — | +2,22 / +2,11 | 932 | 23,0 % / 69,8 % | 44,6 % | 2026 +6 359 $ ; 42 % des journées coupées à −1 000 $ | `reglages_26oct_c.txt` |
| B10c | A2 : A sans entrée tardive (non retenue) | 1 412 | +3 018 | +1,66 / +1,16 | 126 | 11,8 % / 44,0 % | 25,7 % | 2025 +12 839 $, 2026 −451 $ | `reglages_26oct_d.txt` |
| B11 | **Règle de l'utilisateur**, volume ×1, fenêtre 0 (26 oct. soir) | 2 247 | +2 833 | +0,57 / +1,50 | 335 | 19,7 % / 65,8 % (22,6 % départs depuis 2025) | 38,6 % | 2025 +19 898 $, 2026 +10 664 $ ; ×1,5 : t +1,12/+0,64 ; ×2 : t +1,64/+1,14, 12,6 % | `reglages_26oct_f.txt` |
| B12 | **Fenêtre de confirmation 5 min** (installée, « configuration installée ») | 2 400 | +1 968 | +0,66 / +1,04 | 383 | 19,9 % / 68,0 % (20,4 % depuis 2025) | 38,2 % | 2011-2026 +55 071 $ (4 MNQ, prix d'aujourd'hui), pire baisse −37 294 $, années perdantes 2013, 2016, 2020, 2021, 2022, 2025 ; fenêtres 3 / 10 : t +0,54/+0,96 et +0,75/+1,21 | `reglages_26oct_g.txt`, `reglages_26oct_annees.txt` |
| B13 | Filtres **Q1** (sens de l'ouverture) / **Q2** (tendance de fond 20 j) / Q1+Q2, décochés par défaut (27 oct.) | 1 624 / 1 219 / 824 | +3 978 / +4 924 / +4 155 (calculé ici) | **+2,08 / +1,54** ; **+1,22 / +2,08** ; +1,60 / +2,44 | 240 / 205 / 126 | 17,5 / 15,9 / 11,5 % | 33,8 / 32,5 / 23,6 % | Q3 VWAP +0,66/+1,12 ; Q4 +0,15/+1,05 ; Q5 +1,00/+1,26 ; Q6 +0,76/+0,88 : aucun ne passe (règle fixée) | `partie_q.txt`, `reglages_27oct_q12.txt` |
| B14 | **Pas de sortie aux contrôles** (27 oct., cochée) | 2 400 | +6 284 (calculé ici) | +1,44 / +1,17 | 1 071 | 21,9 % / 72,3 % | — | 4 MNQ : 2011-2026 +119 380 $, 2023-2026 +54 514 $ ; 48 % des journées 2023-2026 touchent −1 000 $ | `reglages_27oct_sans_sortie.txt` |
| B15 | **Stop 70 points** au-delà du niveau cassé (27 oct., 70 par défaut) + pas de sortie | 2 400 | +1 102 pts « fixes » (calculé ici) | +0,85 / +1,43 | 167 | 21,7 % / 70,9 % | — | 4 MNQ : 2011-2026 +73 967 $, 2026 +7 963 $, **avril-octobre 2026 −2 480 $** ; stop 50 : t +0,85/+1,37 ; stop 100 : +0,81/+1,48 ; stop depuis l'entrée ±70 : +0,88/+1,53 | `reglages_27oct_stop.txt`, `reglages_27oct_stop_entree.txt` |
| B15q | Stop 70 + Q1 / Q2 / Q1+Q2 | 1 624 / 1 219 / 824 | — | +1,85/+1,83 ; +0,78/**+2,87** ; +0,65/**+3,07** | 100 / 91 / 58 | 18,1 / 17,4 / 12,3 % | — | 2023-26 : +43 470 / +62 836 / +54 378 $ | `reglages_27oct_q12_stop.txt` |

Comptes simulés avec ces configurations (descriptif) :
- **LucidFlex 50K** sans limite de temps (`lucid_27oct.txt`) : installée 1 MNQ validé 42,4 % (départs 2012-2025) /
  62,6 % (2023-sept. 2025) ; bot d'avant 1 MNQ 56,2 / 55,9 % ; version A 55,5 / 57,5 % ; Q2 1 MNQ 35,8 / 65,3 % (22,2 %
  perdus) ; Q1+Q2 2 MNQ 29,8 / 60,2 %.
- **Compte Master Bulenox** un an (`master_27oct.txt`) : installée 1 MNQ plafond 500 $ : perdu 55,3 %, reçu 454 $ ;
  Q2 1 MNQ plafond 500 $ : perdu 31,6 % (2012-2025) / **0,0 %** (2023-2025), reçu 463 / 864 $ ; Q1+Q2 1 MNQ plafond 500 $ :
  perdu 9,9 % / 0,0 %, reçu 324 / 919 $.
- Bulenox sans limite de temps (`i/sans_limite_bulenox.txt`) : zone 1 MNQ 70,1 % validé depuis un compte neuf ;
  2 MNQ 51,9 %.

**Résultat réel (argent du challenge Bulenox)** : connu seulement par bribes dans les README (+1 172 $, puis −1 002 $ le
20/10, −1 012 $ le 21/10 estimés ; +1 800 $ le 22/10 ; −1 000 $ le 26/10 ; situation de 49 500 $ le 26/10). Pas de
journal complet trouvé. Essai Optimus Flow / Ironbeam (7-16 oct.) : critères écrits, **résultats non trouvés**.

---

## 3. Inventaire détaillé par branche

Colonnes : ID | stratégie et règle | marché, unité de temps | données, périodes | résultats | verdict écrit et hors
échantillon | gains quotidiens (régénération, voir section 6) | corrélation avec la zone.

### 3.1 `claude/exciting-fermat-sea2l2:scalping/` — machine scalping (24-27 octobre 2026)

Données : minutes Databento de la branche de recherche (`KB/intraday/donnees/nasdaq100_1min.csv.gz` etc., `commun.py`),
frais 1 $ + 1 tick par ordre, gain « au prix d'aujourd'hui ». Machine v4 : entraînement 2017-2020, validation 2021-2022,
**coffre 2023 - 25 sept. 2026 ouvert une fois** (m = 16, Bonferroni t ≥ 2,73).

| ID | Stratégie | Marché, UT | Données / périodes | Résultat | Verdict, hors échantillon | Quotidien | Corr. zone |
|---|---|---|---|---|---|---|---|
| SA1 | Grant-Wolf-Yu : contre une grande ouverture (9 h 44), tenue jusqu'à la fin | NQ, ES ; 1 min | explo 2017-2022 | NQ 188 trades, −111,28 $/trade, t −1,52 ; ES t −0,61 | 0 survivante (`partie_a.txt`) | `partie_a.py` (pas de CSV) | non mesurée |
| SA2 | Minute extrême (99,9e centile), contre 1 min | NQ, ES ; 1 min | idem | NQ 1 022 trades, −7,80 $, t −2,31 ; ES t −2,81 | rejetée | idem | — |
| SA3 | Saut de 10 h 00, suivre 10 h 01-10 h 02 | NQ, ES | idem | NQ t +0,92 (+5,04 $) ; ES t −1,84 | rejetée | idem | — |
| SA4 | Mouvement de 10 min > 2 σ, contre 10 min (Peng-Wang) | NQ, ES | idem | NQ 3 414 trades, +3,09 $, t +1,10 (meilleure de A) ; ES t −2,06 | rejetée | idem | — |
| SA5a | Niveaux ronds, rebond (ordre limite, Osler) | NQ, ES | idem | NQ t −1,94 ; ES t −5,89 | rejetée | idem | — |
| SA5b | Niveaux ronds, cassure (Osler) | NQ, ES | idem | NQ 4 748 trades, t −1,72 ; ES t −5,08 | rejetée | idem | — |
| SB | **Machine évolutive v4, jour (B)** : familles F0-F9, génome, 60 générations × 200, 4 graines vrai + 4 × 2 bruits | NQ, ES, RTY, YM, GC, CL, 6E ; 1 min | entr. 2017-2020, valid. 2021-2022, coffre 2023-2026 | **296 488 stratégies** (vrai) ; finalistes NQ 4,28 → coffre t −1,51 (−3 453 $) ; NQ 3,27 → +0,11 ; ES 4,21 → −1,89 ; ES 4,15 → −1,25 ; YM 3,86 → −1,40 ; RTY, YM, GC −0,51 à −3,23 | **0 retenue, 0 intéressante** ; placebos 0/29 (`coffre.txt`) ; éligibles NQ au coffre : t médian 0,77, meilleure 2,08 (`apres_coffre.txt`) | `machine.py`, `coffre.py` (pas de CSV quotidien) | non mesurée |
| SB2 | Machine v4, bitcoin CME | BTC (MBT) ; 1 min | entr. 2020-06/2021, valid. 07/2021-2022 | **42 510 stratégies** ; finalistes 3,01 → t −0,39 ; 2,45 → +0,21 (+242 $) | rejetées | idem | — |
| SC | Modèle appris (logistique L2) réentraîné chaque année | 8 marchés ; 1 min | 2017-2022 | t de −2,37 (NQ) à −29,79 (6E) | 0 sur 8 (`appris.txt`) | `appris.py` | — |
| SD | Machine v4, **nuit** (18 h - 9 h 20) | NQ, ES, GC, 6E, 6B, 6A ; 5 min CFD HistData | entr. 2013-2018, valid. 2019-2022, coffre 2023-oct. 2026 | **254 127 stratégies** ; NQ 6,54 → coffre **t +0,40 (+1 522 $)** ; NQ 4,37 → +0,01 ; ES 3,72 → −0,06 ; GC 3,08 / 2,86 → −0,24 / −0,50 | rejetées ; 4 639 éligibles NQ nuit : aucune ≥ 2,73 au coffre, 3,5 % « intéressantes » contre 3,8 % et 3,3 % sur bruit | idem | — |
| SPv4 | Panier des éligibles v4 (descriptif) | NQ, ES, YM jour et nuit | coffre déjà ouvert | NQ jour t 5,05 → **0,74** ; NQ nuit 5,95 → 0,25 ; ES 4,75 → −2,90 | « ne sauve rien » (`ensemble_v4.txt`) | `ensemble_v4.py` | — |
| SV5 | **Machine v5** (tout l'historique jusqu'à sept. 2026 ; choix sur 2023-2026 ; coffre = l'avenir dès le 2 nov. 2026) | 14 couples piste-marché ; 1 min / 5 min | entr. 2017-2022 ; contrôle 2023-2026 | **≈ 890 000 stratégies** (vrai), 1,78 M sur bruit ; 6 candidates, 0 panier ; empreinte `candidats.json` sha256 3aee9308… | coffre de l'avenir pas commencé (2 nov. 2026) | `selection5.py`, `suivi5.py` | candidates −0,07 à +0,03 |
| SV5-1 | Candidate NQ « 3,28 » : micro-compression puis cassure, contre, ventes seules | NQ ; 1 min | contrôle 2023-2026 : 133 trades, t 3,28 | **coffre du passé 2011-2016 : 209 trades, −1 895 $, t −1,33** ; suivi 28/09-23/10 : 3 trades, −131 $ | **ÉCARTÉE** (`v5/coffre_passe.txt`) | `coffre_passe.py`, `suivi5.py` | +0,01 |
| SV5-2 | Candidate NQ « 2,81 » : mouvement de 15 min, suivre, ventes seules | NQ ; 1 min | 104 trades, t 2,81 | coffre du passé : 133 trades, +36 $, t +0,05 ; suivi : 0 trade | « pas de conclusion (rien) », suivi « sans objet » | idem | 0,00 |
| SV5-3 | Candidate GC : mouvement de 30 min, suivre, achats seuls | or ; 1 min | 158 trades, t 2,07 | pas de coffre du passé (données dès 2016) ; pas de relevé de minutes | **pas fini** | `suivi5.py` (outil Yahoo à écrire) | +0,03 |
| SV5-4 | Candidate GC : série de 7 barres, suivre | or ; 1 min | 211 trades, t 2,03 | idem | pas fini | idem | −0,03 |
| SV5-5 | Candidate CL : niveau rond franchi, suivre, ventes seules | pétrole ; 1 min | 139 trades, t 2,30 | idem | pas fini | idem | −0,07 |
| SV5-6 | Candidate RTY : pic de volume, suivre, achats seuls | Russell ; 1 min | 149 trades, t 1,95 | idem | pas fini | idem | +0,01 |
| SE1 | Gamma d'heure en heure (GEX S&P) | NQ ; 1 min | 2011-2026 (explo ≤ 2022, ≥ 2023) | 3 773 séances, −32,5 $/séance, **t −3,92** ; ≥2023 −1,40 | rejetée (`e/partie_e.txt`) | `partie_e.toutes` (besoin GEX, FOMC, ETF) | — |
| SE1b | Gamma en fin de séance | NQ | idem | t −1,48 ; ≤2022 −2,74 ; ≥2023 +1,74 | rejetée | idem | — |
| SE2 | Conférence de presse de la Fed, suivre 14 h - 14 h 30 jusqu'à 15 h 30 | NQ | 2013-2026 | 70 trades, +75,8 $, t +1,10 ; ≥2023 +1,06 | rejetée (bat 85 % du bruit) | idem | — |
| SE3 | Retournement de l'annonce de la Fed | NQ | 2013-2026 | 94, t +0,42 ; ≥2023 −1,39 | rejetée | idem | — |
| SE4 | Rééquilibrage 60/40 de fin de mois | NQ | 2016-2026 | 569, +37,6 $, t +1,24 ; ≥2023 +0,01 | rejetée | idem | — |
| SE5 | Nuit avant NFP et ISM, achat | NQ nuit ; 5 min CFD | 2012-2026 | 318, t +0,57 | rejetée | idem | — |
| SE6 | Dérive 2 h - 3 h après une fin de séance vendeuse | NQ nuit | idem | 1 171, t **+2,75** ; ≤2022 +3,25 ; **≥2023 −0,26** | rejetée : « morte depuis 2023 » | idem | — |
| SE7 | Règle des 80 % (Market Profile) | NQ | 2011-2026 | 885, t +0,35 ; ≥2023 −0,47 | rejetée | idem | — |
| SE8 | « Oops » de Larry Williams | NQ | idem | 1 001, +20,0 $, t +1,16 ; ≥2023 +0,57 | rejetée (sous 1,65) | idem | — |
| SE9 | Cassure des extrêmes de la nuit | NQ | idem | 3 252, +11,2 $, t +1,13 ; ≥2023 +0,54 | rejetée | idem | — |
| SF1 | Cassure du plus haut/bas de la semaine précédente | NQ ; 1 min | 2011-2026 | 787, t +0,20 ; ≥2023 +0,96 | rejetée (`f/partie_f.txt`) | **`serie_regles.py`** | — |
| SF2 | Cassure du mois précédent | NQ | idem | 173, +39,6 $, t +1,13 ; ≥2023 +1,35 | rejetée (sous 1,65) | **oui** (t +1,13, calculé ici) | +0,10 (calculé ici) |
| SF3 | **Pivots R1/S1, version tendance** | NQ ; 1 min | idem | 1 912, +20,6 $, **t +1,69** ; ≤2022 +1,83 ; **≥2023 +0,21** ; 2022 = +31 779 $ sur ≈ +39 000 $ | **« intéressante »** → coffre de l'avenir (virtuel) ; suivi 28/09-23/10 : 9 trades **+839 $** ; 12 derniers mois +4 223 $ | **oui** | **+0,35** (README) ; +0,44 (calculé ici, toutes séances) |
| SF4 | Turtle Soup | NQ | idem | 133, t −0,71 | rejetée | oui | — |
| SF5 | Retournement d'un grand mouvement à fort volume | NQ | idem | 1 343, t −1,41 | rejetée | oui | — |
| SF6 | Régime du matin (ratio de variance) | NQ | idem | 3 840, t −1,22 | rejetée | oui | — |
| SF7 | Frog in the pan (10 h 30) | NQ | idem | 2 862, +14,0 $, t +1,45 ; ≤2022 +0,80 ; **≥2023 +1,64** ; bat 100 % du bruit | rejetée (sous 1,65) | **oui** | +0,36 (calculé ici) |
| SF8 | Open-Drive (Dalton) | NQ | idem | 138, +41,5 $, t +1,20 | rejetée | oui | — |
| SG0 | Carte de l'élan (descriptif) | NQ | ≤2022 / ≥2023 | élan seulement quand la zone est en position : +1,05 pb t 4,05 / +1,16 pb t 2,39 | « la zone capte déjà tout l'élan » | `partie_g.py` | — |
| SG1 | Élan dans la bande, zone à plat, 30 min | NQ | 2011-2026 | 3 378 séances, t −2,69 | rejetée (`g/partie_g.txt`) | `partie_g.py` | +0,04 |
| SG2 | Idem, 1re fois, jusqu'à 15 h 55 | NQ | idem | t +0,71 | rejetée | idem | +0,21 |
| SG3 | Élan du matin sans trade de zone, 12 h - 15 h 55 | NQ | idem | t +0,95 ; ≥2023 −0,22 | rejetée | idem | +0,09 |
| SH1 | **ORB 5 min** (Zarattini-Aziz 2023) | NQ ; 5 min | 2011-2026 | 3 804 séances, +12,9 $, **t +2,25** ; ≤2022 +2,42 ; **≥2023 +0,19** | **intéressante** → coffre de l'avenir ; suivi 19 séances **+825 $** ; 12 derniers mois −837 $ | **oui** | +0,39 |
| SH2 | ORB 15 min | NQ | idem | t +0,67 ; ≥2023 +1,43 | rejetée | oui | +0,54 |
| SH3 | ORB 30 min | NQ | idem | t +0,18 ; ≥2023 +1,45 | rejetée | oui | +0,55 |
| SH4 | ORB 60 min (initial balance) | NQ | idem | t +0,55 | rejetée | oui | +0,53 |
| SH5 | **Cassure du plus haut/bas de la veille** | NQ ; 1 min | idem | 3 363, +9,9 $, **t +1,97** ; ≤2022 +1,32 ; **≥2023 +1,68** | **intéressante** → coffre de l'avenir ; suivi 17 séances **+281 $** ; 12 derniers mois +2 009 $ | **oui** | **+0,50** |
| SH6 | Donchian 20/10 | NQ ; 5 min | idem | t −0,51 | rejetée | oui | +0,44 |
| SH7 | EMA 9/21 | NQ ; 5 min | idem | t +1,53 ; ≤2022 +2,44 ; ≥2023 −1,10 | rejetée | oui | +0,38 |
| SH8 | MACD 12-26-9 | NQ ; 5 min | idem | t −2,51 | rejetée | oui | +0,01 |
| SH9 | Bollinger, retour à la moyenne | NQ ; 5 min | idem | t −2,74 | rejetée | oui | −0,41 |
| SH10 | Bollinger, cassure | NQ ; 5 min | idem | t +0,39 | rejetée | oui | +0,41 |
| SH11 | RSI(2) intraday | NQ ; 5 min | idem | t −2,69 | rejetée | oui | −0,24 |
| SH12 | **Supertrend 10-3** | NQ ; 5 min | idem | 3 855 séances, +28,6 $, **t +2,92** ; ≤2022 +2,69 ; ≥2023 **+1,18** ; 12 années sur 16 positives | **« RETENUE »** au palier, mais « avec la zone, il n'apporte rien » (zone + H12 t 3,87 < zone 4,21) ; suivi 20 séances **+217 $** ; 12 derniers mois +7 613 $ | **oui** | **+0,44** |
| SH13 | Gap and go | NQ | idem | t +0,47 ; ≥2023 −0,77 | rejetée | oui | +0,19 |
| SH14 | Comblement de gap | NQ | idem | t −0,93 | rejetée | oui | −0,27 |
| SH15 | Jour intérieur | NQ | idem | 373, t +0,72 | rejetée | oui | +0,17 |
| SH16 | NR7 + ORB 30 | NQ | idem | 524, t +0,59 | rejetée | oui | +0,15 |
| SI | Zone + ajout (H12, H1, H5, F3 à 2 ou 4 MNQ, ou les 4 à 1 MNQ), challenge Bulenox 30 j | NQ | départs 2012-2026 (3 761) | zone seule 48,0 % / 49,9 % (2023-26) ; meilleur ajout ORB5 2 MNQ 50,2 % / 51,3 % ; H12 46,9 / 42,9 % ; témoin sans avantage 41,3 % | **aucun ajout** (`i/challenge_ajouts.txt`) | `challenge_ajouts.py` | les 4 / zone sur 20 séances : +0,75 |
| SJ0 | Entrée à la cassure (chaque minute) sans objectif | NQ ; 1 min | 2011-23 oct. 2026 | voir B6 | rejetée | trades : `partie_j.py` ; E1 : `entree_tardive` | variante de zone |
| SJ2 / SJ3 | Cassure + objectif 2× / 3× le risque (ligne de sortie) | NQ | idem | −7 820 / −5 737 pts ; t −1,24/−0,86 et −0,32/−0,47 | rejetées (`j/partie_j.txt`) | `partie_j.py` | idem |
| SJ2s / SJ3s | Idem + vrai stop (information) | NQ | idem | −9 072 / −6 706 pts | information | idem | idem |
| SJV2 / SJV3 | Risque mesuré au VWAP, objectif 2× / 3× | NQ | idem | −3 808 / −2 307 pts ; t +1,64/−0,25 et +1,57/+0,19 | rejetées | idem | idem |
| SJM2 / SJM3 | Risque = largeur de la zone, 2× / 3× | NQ | idem | −462 / +2 023 pts ; t +2,29/+0,63 et +2,84/+0,93 | rejetées | idem | idem |
| SK1a, SK1b, SK2a, SK2b | Cassure, coupure au retour dans la zone (clôture / vrai stop), réentrée ou attente | NQ | idem | −7 552 / +920 / −20 876 / −2 230 pts ; t +1,18/+1,15 ; +2,06/+1,41 ; −1,50/+0,13 ; +1,29/+1,40 | rejetées (`j/partie_k.txt`) | `partie_k.py` | idem |
| SL1a…SL3b | Première cassure, laisser courir ; sortie niveau cassé / VWAP / retour fort ; 1 trade ou réentrée (6 variantes) | NQ | idem | L1a +5 120 (t +2,31/+0,88) ; L1b +5 000 ; L2a +4 642 (+2,79/+0,32) ; L2b +3 932 ; L3a +4 954 ; L3b +3 831 | aucune ne bat le bot d'avant (`j/partie_l.txt`) | `partie_l.py` | idem |
| SM5, SM15, SM1V, SM5V | Confirmation par bougie 5 / 15 min, volume ×2 (1 min), volume ×1,5 (5 min) | NQ | idem | +4 377 / +5 882 / +6 387 / +6 426 pts ; t +2,36/+0,72 ; +3,16/+0,44 ; +2,86/+1,09 ; +3,17/+1,02 | aucune (`j/partie_m.txt`) | `partie_m.py` | idem |
| SN1 / SN2 | 1 entrée/jour, sortie au retour sous le niveau (clôture / vrai stop) | NQ | idem | +4 043 / +2 371 pts ; t +2,22/+1,28 et +2,19/+0,91 | rejetées (`j/partie_n.txt`) | `partie_n.py` ; N1+vol2 : `reglages_26oct_trades.csv` | idem |
| SP | Stop pour L1a (8 candidats : 0,10 à 0,40 %, niveau − 0,25/0,5/1 largeur) | NQ | choix 2011-2022, jugé 2023-2026 | choisi : niveau − 0,5 largeur, t +2,71 (choix) → **+0,62** (contrôle) contre +0,88 sans stop | rejeté (`j/partie_p.txt`) | `partie_p.py` | idem |
| SQ1…SQ6 | Filtres d'entrée sur la configuration installée | NQ | 2011-2026 | voir B13 | aucun ne passe | Q1, Q2, Q1+Q2 : CSV de trades | idem |
| SS | Situation du challenge à 49 500 $ (descriptif) | NQ | départs 2012-2026 | plus haut 51 172 $ : 20,7 % validés ; 50 600 $ : 29,2 % | descriptif | `situation_bulenox.py` | — |

### 3.2 `claude/elegant-ptolemy-g94s8t:entree_tardive/` — entrées en retard (20 octobre 2026)

Données : minutes de la recherche 2011 - 25 sept. 2026 + robot jusqu'au 19 oct. 2026 ; P1 = vrai delta Databento
(1er avril - 1er oct. 2026) ; P2 = Rithmic (2-16 oct. 2026). Sources : `resultats_15ans.txt`, `resultats_delta.txt`,
`resultats_challenge.txt`, `decision.txt`.

| ID | Stratégie | Résultat 15 ans (sans filtre) | Vrai delta P1 / P2 (points) | Challenge 16 séances (2012-26 / 2023-26) | Verdict | Quotidien | Corr. zone |
|---|---|---|---|---|---|---|---|
| ET-H1 | Zone V1 (bot, relance décochée) | 3 572 trades, +10 721 pts, **t +2,12 / +1,86**, 130 séances à −125 pts | +1 776,8 / +220,2 | **44,9 %** / 46,5 % | référence gardée | **`jours_15ans.csv` col. H1** (2011-01-24 → 2026-10-19) | 1 |
| ET-E1 | Entrée à la cassure à chaque minute | 5 525, +3 037, t +0,22 / +0,65 | +935,2 / +112,5 | 44,4 / 47,9 % | rejetée | col. E1 | variante |
| ET-E2 | Tout à la minute | 13 711, −9 549, t −4,68 / +0,52 | +449,0 / +469,2 | 38,4 / 40,6 % | rejetée | col. E2 | variante |
| ET-S1 | Sortie à la minute | 5 188, +6 093, t +0,82 / +1,57 ; 59 séances à −125 pts | +495,5 / +567,2 | 41,0 / 41,8 % | rejetée | col. S1 | variante |
| ET-L1 | Pas de poursuite (dépassement ≤ 1) | 3 090, +7 619, t +1,66 / +1,47 | +853,5 / +220,2 | 40,3 / 41,8 % | rejetée (les 482 refusées : +6,44 pts en moyenne) | col. L1 | variante |
| ET-R / RL | Relance du filtre (information) | — | +1 860,5 / +657,0 (RL +664,2) | P1 : 39,4 % contre 41,7 % | information | `trades/R_P1.csv` … | — |

### 3.3 `claude/fervent-wright-21hspi` — filtre delta, zone sans filtre, données gratuites (21 octobre 2026)

| ID | Stratégie | Données / périodes | Résultat | Verdict | Quotidien | Corr. zone |
|---|---|---|---|---|---|---|
| DM-B | Filtre delta brut (le bot) : delta 30 min dans le sens du trade | P1 Databento, P2 Rithmic | P1 79 trades +1 776,75 ; P2 6 trades +220,25 ; pire baisse 760 | gardé | `delta_mesures/trades.csv` (106 trades) | — |
| DM-P | Delta en proportion du volume ≥ 1 % | idem | P1 72 / +1 977,75 ; P2 4 / +19,25 | rejeté (9 écartés en plus, somme nulle) | idem | — |
| DM-Z | z-score de la séance ≥ 1 | idem | P1 41 / +2 075,75 ; P2 2 / +97,5 ; 42 écartés en plus à −4,2 pts | rejeté | idem | — |
| DM-S | Zone sans filtre (référence) | idem | P1 99 / +982,25 ; P2 7 / +669,5 | — | idem | — |
| ZR-V1 | Zone V1 (référence) | 2011 - 20 oct. 2026 | 3 573 trades, +10 582 pts, t +2,12 / +1,82 ; challenge 16 s. 44,8 % | référence | `zone_retour/etude.py` | 1 |
| ZR-C1 | Entrée à chaque minute, sortie au retour dans la zone | idem | 13 006, −7 719, t −4,11 / +0,72 ; perte moyenne −208 $ (4 MNQ), 14 % gagnants | rejetée | idem | variante |
| ZR-C2 | Entrées aux contrôles, sortie au retour dans la zone | idem | 4 568, +7 065, t +1,17 / +1,61 ; 9,8 % de séances à −1 000 $ | rejetée | idem | variante |
| ZR-C3 | C1 sans allers-retours | idem | 7 575, +1 150, t −1,01 / +1,05 | rejetée | idem | variante |
| DL | `donnees_libres/` : ETF 5 min (Alpaca, 29 ETF 2016-2026), Yahoo futures et volatilité, HistData 5 min | — | **données seulement, aucune stratégie** | — | — | — |

### 3.4 `claude/affectionate-turing-tnz0mn:etude_large/` — étude large et vagues (22-23 octobre 2026)

Exploration / coffre ouvert une fois, précisés pour chaque vague. Sources : `etude_large/README.md`, `resultats_a.txt`,
`resultats_b.txt`, `resultats_d.txt`, `<vague>/resultats.txt`.

| ID | Stratégie | Marché, UT | Périodes | Résultat | Verdict, hors échantillon | Quotidien | Corr. zone |
|---|---|---|---|---|---|---|---|
| LA1 | Zone de bruit sur 27 marchés (ETF Alpaca) | 27 futures via ETF ; 5 min | explo 2016-2022, coffre 2023 - 20 oct. 2026 | QQQ t +2,12 → **coffre +2,57** (Sharpe 1,33) ; tous les autres négatifs après frais (médiane explo −7,00) ; BITO +0,16 → +1,18 | 0 sur 189 ne passe BH (il faudrait 3,27) ; QQQ = le bot lui-même | `partie_a.py` → `essais_a.csv` (pas de série quotidienne) | QQQ 0,86 (contrôle 0,88) |
| LA2a | Gao (clôture veille → 10 h, position 15 h 30 - 16 h) | 27 marchés | idem | négatif après frais | rejetée | idem | voir `essais_a.csv` |
| LA2b | Baltussen (élan de fin de séance) | 27 marchés | idem | avant frais TLT t +3,2 → +2,6, or +2,3 → +3,0 ; après frais négatif | rejetée (frais ZB, MGC) | idem | idem |
| LA3a | ORB 5 min | 27 marchés | idem | négatif après frais | rejetée | idem | idem |
| LA3b | ORB 30 min | 27 marchés | idem | BITO→MBT t net **+1,64 → +1,87** (le plus proche) | rejetée ; étudiée dans `crypto/` | idem | idem |
| LA4 | Périodicité intraday (Heston-Korajczyk-Sadka) | 27 marchés | idem | négatif après frais | rejetée | idem | idem |
| LA5 | Zone inversée | 27 marchés | idem | QQQ t −5,6 ; gagne +26 pb les jours où la zone perd | « miroir, pas un complément » | idem | négative |
| LB | Zone combinée : régression ridge (10 informations), walk-forward annuel | NQ ; 1 min | 2016-2026 hors échantillon | tous les trades **t +3,05** (+48 427 $) ; gardés (43 %) t +2,60 ; différence t −1,59 | **non adopté** (`resultats_b.txt`) | `partie_b.py` | — |
| LD | Mathématiques des challenges (D1 hasard, D2 bot réel) | — | départs 2012-2026 | Bulenox 30 j : 50 % sans avantage ; bot Lucid 1 MNQ 55 % (27 % au hasard), 256 $ par validation | descriptif (choix de compte) | `partie_d.py` (`chemins_zone`) | — |
| LCR | Cassure 30 min du bitcoin (A3b) sur années jamais vues + walk-forward 24 variantes | BTC Coinbase ; 5 min | P0 2017 - sept. 2021 (jamais vu), P1 oct. 2021-2026 | P0 **t net +0,70** ; P1 +2,37 ; walk-forward 2018-2026 t +0,73 ; 2025 −0,29, 2026 −1,07 ; placebo d'heure : 9 h 30 +2,10, autres heures −3,4 à −4,5 | **non confirmée** | `crypto/etude.py` | non mesurée |
| LCR-E | Même règle sur l'ether (descriptif) | ETH | idem | avant frais t +1,92 / +4,17 ; net −27,7 / −34,1 (frais 209 pb) | intradable | idem | — |
| LBR | Bruit dans la zone : retour au VWAP dans la zone, stop sur sa limite (3 seuils) | NQ, ES ; 1 min | explo 2011-2022, coffre 2023-2026 | NQ 0,50 : t −11,91 → +0,39 ; ES t −17 à −21 | **0 sur 6** | `bruit/etude.py` | −0,01 à −0,09 |
| LAN-S | Pas de zone les jours de choc du dollar à 8 h 30 | NQ | 2012-2026 | Sharpe explo 1,01 / coffre 0,93 (zone 1,13 / 1,18) ; bat 68 % des placebos | non retenue | `annonces/etude.py` | — |
| LAN-D | 2 MNQ les jours de choc | NQ | idem | Sharpe 1,01 / 1,23 ; bat 23 % | non retenue | idem | — |
| LP-ZW | Sortie VWAP pour de bon (ZW − ZL, ZW+ − ZL) | NQ | explo 2011-2022, coffre 2023-2026 | t −0,37 → +0,78 ; −0,62 → +0,24 | échoue (« les backtests restent valables ») | `pistes/sortie_vwap/etude.py` | variante |
| LP-H1…H5 | Heure 16 h - 16 h 59 : prolonger la zone, retours de clôture NQ / ES, version Lucid | NQ, ES | idem | H1 −0,36 → +1,49 ; H2 −0,49 → −0,20 ; H3 −2,12 → −1,96 ; H4 −2,22 → −1,60 ; H5 +0,61 → +0,18 | échouent | `pistes/heure_16h/etude.py` | — |
| **LP-R1** | **Renfort : +1 MNQ au premier contrôle où la zone tient** | NQ ; 1 min | explo 2011-2022, coffre 2023 - 20 oct. 2026 | explo **t +2,65** (1 511 renforts, +3,0 pts) ; **coffre t +1,72** (469, +10,02 pts) ; placebo 98 % ; BH oui | **échoue au critère 5** (Lucid 1+1 MNQ 30,5 % contre 54,6 %) ; en rendement t explo +1,37 | `pistes/renfort/etude.py` (série interne) | ajout à la zone (corrélée par construction) |
| LP-R2 | Renfort aux deux premiers contrôles tenus | NQ | idem | explo +2,56 ; **coffre +1,76** ; placebo 100 % | échoue au critère 5 | idem | idem |
| LP-R3 | Renfort si gain latent ≥ 0,5 σ | NQ | idem | +1,04 → +0,23 | échoue | idem | idem |
| LP-F3or | Cassure de l'ouverture de Londres, 30 min, or | MGC ; 5 min HistData | explo 2012-2022, coffre 2023 - 2 oct. 2026 | +2,07 → +0,38 | échoue | `pistes/or_londres/etude.py` | +0,04 |
| **LP-F4or** | **Cassure de Londres jusqu'à 16 h 30, or** | MGC ; 5 min | idem (coffre jamais ouvert avant) | explo **t +1,97** (net 2 pb) ; **coffre t +1,49**, placebo 2,8 % (bat 97,2 %) ; années coffre −941 / +545 / +750 / +2 586 $ | échoue « de justesse » : ne se réplique pas sur l'argent, Lucid 1 MNQ + 1 MGC 42,4 % contre 52,2 % | idem (série interne, données `KB/sessions24`) | **−0,03** ; Sharpe zone + or au coffre 1,21 contre 1,04 |
| LP-F3ag / F4ag | Mêmes règles sur l'argent (SIL) | SIL | idem | −2,58 → −1,34 ; −0,41 → −0,01 | échouent | idem | +0,05 / +0,04 |
| LP-D15 / D10 / D20 | Copies décalées de la zone (:15 / :45 …) | NQ | idem | +1,09 → +1,16 ; +1,52 → +1,80 ; +1,32 → +1,55 | échouent (zone +2,17) | `pistes/zones_decalees/etude.py` | variantes |
| LT | Taille par programmation dynamique (état du compte) | NQ | départs 2012-2026 | Bulenox +2,2 points (52 % contre 50 %) ; Lucid moins bien que 1 MNQ fixe | non retenue | `taille/etude.py` | — |
| LT-c | Taille selon la confiance (sens de l'écart d'ouverture) | NQ | départs 2012-2026 (descriptif) | 54,2 / 33,1 % contre 54,1 / 36,5 % (validé / perdu) | « à coder et suivre en virtuel » | `taille/situation.py` | — |
| LPH-A1…A3 | Soirs de résultats des méga-capitalisations | NQ | explo 2016-2022, coffre 2023-2026 | −1,23 → +0,24 ; −1,19 → −0,79 ; −1,43 → −1,31 | échouent (descriptif : calendrier regardant le futur) | `phenomenes/resultats_megacaps/etude.py` | — |
| LPH-B1…B4 | Confirmation par les autres marchés (risque global, AUD/JPY, VXX, TLT) | NQ + 5 marchés | idem | B1 −1,53 → −1,08 ; **B2 −3,40** → −0,79 ; B3 −1,75 → +0,09 ; B4 −1,28 → −1,50 | échouent | `phenomenes/confirmation_croisee/etude.py` | — |
| LPH-I1 | Hypothèse inversée de B2 (entrées non confirmées par l'AUD/JPY) | NQ | fixée après l'explo, coffre 2023 - 2 oct. 2026 | explo +47 $ contre +17 $ (Welch +1,85) ; **coffre +23 $ contre +19 $, t +0,12** | non confirmée | `confirmation_croisee/inverse.py` | — |
| LPH-N1 / N2 | Nombres ronds du NQ, contre le 1er franchissement 15 / 30 min | NQ | explo 2011-2022 | +1,22 → −2,45 ; +0,85 → −1,47 | échouent | `phenomenes/nombres_ronds/etude.py` | — |
| LPH-F1 / F2 | Forme de la cassure (régulière / sans saut) | NQ | explo 2012-2022 | −1,31 → −1,18 ; −1,05 → −1,01 | échouent | `phenomenes/forme_cassure/etude.py` | — |
| LZI-I1 | Zone implicite (σ × VXN / moyenne VXN) | NQ ; 1 min | explo 2012-2022, coffre 2023 - 20 oct. 2026 | diff. avec V1 −1,08 → **−1,62** ; Lucid 39,8 % contre 54,6 % | non retenue (`zone_implicite/resultats.txt`) | `zone_implicite/etude.py` | variante |
| LZI-I2 | Zone implicite pure (k × VXN) | NQ | idem | +0,02 → −1,75 | non retenue | idem | variante |
| LZI-I3 | Élargir seulement | NQ | idem | −1,02 → −1,63 | non retenue | idem | variante |
| **LZI-T1** | **Ciblage de volatilité (taille = médiane VXN / VXN)** | NQ | idem | alpha t **+0,03** (explo) → **+1,62** (coffre), Sharpe 1,41 contre 1,20, placebo 97 % | non retenue (« piège de la vérification seule ») | idem | taille sur la zone |
| LZI-T2 | Plus gros quand le VXN est haut | NQ | idem | −0,72 → −1,24 | non retenue | idem | idem |
| LVOL | Relief et surface de volatilité implicite (SPX, QQQ, SPY) | — | 2011-2026 hebdo ; photo du 22/10/2026 | contango 93,2 % des semaines ; prime de variance +3,4 pts ; zone par sextile de VIX instable | **descriptif, pas un test** | `volatilite/donnees.py`, `surface.py` | — |

### 3.5 `main` — robots de recherche déjà publiés (résultats historiques)

| ID | Stratégie | Marché, UT | Données / périodes | Résultat historique | Verdict écrit | Quotidien | Corr. zone |
|---|---|---|---|---|---|---|---|
| M-Z | **Zone de bruit V1** (Zarattini-Aziz-Barbon 2024) | NQ (MNQ) ; contrôles 30 min | minutes Databento 2011-2026 | t 2011-2016 −2,26 ; 2017-2022 +2,78 ; 2023-2026 +2,00 (`zone/README.md`) ; 2023-2026 t +2,07, depuis la publication (juin 2024) **t +1,05** (`v5/zone_annees.txt`) ; Sharpe 0,9 (2023-2026) ; Phidias : rien reçu dans 79 % des départs | gardée (seule source qui tienne) ; virtuel +497,5 $ | **`serie_zone.py`** / `jours_15ans.csv` H1 | 1 |
| M-RSI | **RSI(2) Connors** (étude `tournoi8/` sur la branche de recherche) | NQ ; décision 15 h 50, tenue la nuit | explo 2011-2022, coffre 2023-2026 | explo t 2,40 ; **coffre t 1,95**, Sharpe 1,01, +11 098 $, 4 années positives, 40 trades | « passé de justesse » ; dans le compte virtuel ; virtuel −253 $ | **`serie_zone.py` avec `ROBOT_DEBUT_RSI2=2011-01-01`** | « ≈ 0 » ; −0,06 (calculé ici) |
| M-RB | Rebond après forte baisse (piste S4) | NQ ; ouverture → clôture | 2011-2026 | exécutable : 2011-2022 +6 871 $, 2023-2026 +6 420 $ ; apport t 1,21 ; 2020 +6 408 $ et 2025 +6 568 $, 9 avril 2025 +4 119 $ | « non validé » ; suivi à part ; virtuel +854,5 $ | **`serie_zone.py`** col. `rebond` | +0,21 (calculé ici) |
| M-H1 | Filtre delta H1 sur la zone (suivi à part) | NQ | avr.-oct. 2026 | voir B1 | suivi à part, décision au bilan | `delta_mesures/trades.csv` | — |
| M-T | **Tendance multi-marchés** EWMAC 16/64, 32/128, 64/256 | 19 futures ; quotidien, rééquilibrage le vendredi | 2007-2026 | Sharpe 0,56, +10,9 %/an pour 19,5 % de risque, pire baisse −36 %, 65 % d'années positives ; **2023-2026 Sharpe −0,16** ; challenge Phidias 8-23 % validés | « réel et robuste » mais compte 50K trop petit ; virtuel −1 434 $ | **`serie_tendance.py`** col. `tendance` | −0,05 (calculé ici) |
| M-MEL | **Mélange 50/50 tendance + achat permanent** | 19 futures | 2007-2026 | Sharpe **0,78**, pire baisse −19 % (12 % de risque), **2023-2026 Sharpe 0,37** ; corr. tendance / achat 0,03 | compte principal du robot ; virtuel −954 $ | **`serie_tendance.py`** col. `melange` | −0,06 (calculé ici) |
| M-ACH | Achat permanent (à risque égal), composant du mélange | 19 futures | 2007-2026 | Sharpe 0,56 ; 2023-2026 0,58 (calculé ici) | composant | `serie_tendance.py` col. `achat` | −0,02 (calculé ici) |
| M-V7 | **Version 7** : 5 actions tech au meilleur rendement 6 mois - 1 mois, 10 % chacune | actions ; mensuel | 2006-2026 (étude `secteurs/` sur la branche de recherche) | 2021-2026 +21,6 %/an (choisie sur cette période), pire baisse ≈ −23 % ; 2006-2021 +12,8 %/an, ≈ −32 % | **« pas une stratégie validée »** (critère 8 : placebo 93 % pour 95 %) ; virtuel −1 060 $ | `ROBOT_PRIX=… ROBOT_DEBUT=… python3 version7/robot.py` (prix sur la branche de recherche) | −0,65 sur 22 séances virtuelles (calculé ici) |
| M-PH | Scalping M5 Pro (`main.py`) : EMA9 > EMA21, RSI7 > 50, volume > moyenne | BTC, ETH, XAU ; 5 min | aucune | **jamais testé** | — | — | — |

---

## 4. Stratégies « pas finies »

1. **Coffre de l'avenir v5 et règles F3, H1, H5, H12** : premières séances le 2 novembre 2026 ; points de lecture
   1er février, 1er mai… 2027. `workflow_suivi_scalping.yml` est « à placer sur `main` avec l'accord de l'utilisateur » :
   **le suivi ne tourne pas** (seul un aperçu de 20 séances, `v5/suivi_apercu.txt`). Candidates or, pétrole, Russell :
   « outil à écrire » pour relever les minutes Yahoo.
2. **Filtre delta H1** : 106 trades seulement mesurés avec le vrai delta ; décision à 150 trades « vers fin 2027 » ;
   suivi du robot et bot 3 en 1 virtuel **en pause** depuis le 2 octobre (Databento verrouillé, 88,01 $ impayés).
   L'enregistrement du delta par le bot lui-même est « à décider ».
3. **Zone et RSI(2) virtuels** : bilan à 60 séances vers le 21 décembre 2026, puis 120 ; « il faudrait environ 1 200
   séances, soit 5 ans » pour prouver l'avantage de la zone.
4. **Tendance, mélange, version 7 virtuels** : « il faut plusieurs mois ».
5. **Taille selon la confiance** (`taille/`) : « à coder et à suivre en argent virtuel ».
6. **Or à Londres F4** : la version coupée à 12 h (texte du README) « n'a pas été calculée ».
7. **Piste A des phénomènes** (soirs de résultats) : seulement descriptive (calendrier approché regardant le futur).
8. **Partie E** : « relecture indépendante arrêtée à la demande de l'utilisateur ».
9. **Q1 + Q2** : mesuré « hors des règles fixées » ; conseillé pour le Master, jamais jugé sur un coffre.
10. **Règle de l'utilisateur / fenêtre 5 / stop 70** : « seul le suivi des prochaines semaines dira ce qu'elle vaut ».
11. **Essai Optimus Flow / Ironbeam** (7-16 octobre) : critères fixés, résultat non trouvé.
12. **Règles des firmes** (`etude_large` partie D) : « à confirmer par écrit avant tout achat ».
13. **Bitcoin 30 min** : « à revoir si les frais du MBT baissent, et sur les données de 2027 ».
14. **`main.py` Scalping M5 Pro** : envoie des signaux sans aucun backtest.

---

## 5. Classement des stratégies avec une preuve hors échantillon positive (de la plus solide à la moins solide)

« Hors échantillon » = coffre ouvert une fois, années jamais vues, walk-forward, ou suivi virtuel/réel après la
publication de la règle. Les 20 séances de suivi (28 sept. - 23 oct. 2026) et les 23 séances virtuelles ne prouvent rien
seules (« bien trop tôt pour conclure »).

| Rang | Stratégie (ID) | Preuve hors échantillon | Faiblesses | Corr. zone | Gains quotidiens 2011-2026 régénérables ? |
|---|---|---|---|---|---|
| 1 | **Zone de bruit V1 NQ** (M-Z, référence) | walk-forward 2016-2026 **t +3,05** (`resultats_b.txt`) ; coffre 2023-2026 t +2,07 à +2,27 ; ETF QQQ coffre +2,57 ; virtuel **+497,5 $** en 23 séances (vert) | depuis la publication t +1,05 ; avantage « diminué de moitié depuis 2024 » ; 2011-2016 négatif | 1 | **oui** (2011-03 → 2026-10-28) |
| 2 | **RSI(2) Connors NQ** (M-RSI) | **coffre 2023-2026 t 1,95**, +11 098 $, 4/4 années positives (`zone/README.md`) | 40 trades au coffre ; « passé de justesse » ; virtuel −253 $ (6 jours) | ≈ 0 (−0,06 calculé ici) | **oui** |
| 3 | **Renfort R1 / R2** (LP-R1/R2) | coffre **t +1,72 / +1,76** après explo +2,65 / +2,56, BH passé, placebos 98-100 % | c'est du levier sur la zone ; fait perdre le challenge Lucid ; t en rendement +1,37 | ajout à la zone | partiel (série interne de `pistes/renfort/etude.py`) |
| 4 | **Or, cassure de Londres jusqu'à 16 h 30** (LP-F4or) | coffre jamais ouvert **t +1,49**, placebo 2,8 % ; Sharpe zone + or 1,21 contre 1,04 | explo 1,97 sous 2 ; pas répliqué sur l'argent ; Lucid moins bon | **−0,03** | partiel (2012-2026, série interne ; HistData `KB/sessions24`) |
| 5 | **H5 cassure de la veille** | ≥ 2023 **t +1,68** (≤ 2022 +1,32) ; suivi +281 $ (17 séances) | t global 1,97 sur 16 tests | +0,50 | **oui** |
| 6 | **H12 Supertrend 10-3** | ≥ 2023 t +1,18 (≤ 2022 +2,69) ; suivi +217 $ | combinée à la zone : t 3,87 < 4,21 ; Bulenox moins bon | +0,44 | **oui** |
| 7 | **T1 ciblage de volatilité VXN** (LZI-T1) | coffre alpha **t +1,62**, Sharpe 1,41 contre 1,20, placebo 97 % | exploration t +0,03 | taille sur la zone | partiel (`zone_implicite/etude.py`) |
| 8 | **Mélange tendance 50/50 + achat** (M-MEL) | réglages fixés d'avance ; 2023-2026 Sharpe **0,37** | virtuel **−954 $** ; pas de coffre formel | −0,06 (calculé ici) | **oui** (2007-2026) |
| 9 | **Rebond après forte baisse** (M-RB) | positif 2011-2022 (+6 871 $) et 2023-2026 (+6 420 $) ; virtuel **+854,5 $** (3 trades) | gain venu de 2 krachs ; « non validé » | +0,21 (calculé ici) | **oui** |
| 10 | **F3 pivots R1/S1** | « intéressante » ; suivi **+839 $** (9 séances) | ≥ 2023 t +0,21 ; gain = 2022 | +0,35 | **oui** |
| 11 | H1 ORB 5 min | suivi +825 $ | ≥ 2023 (après publication) t +0,19 | +0,39 | oui |
| 12 | F7 frog in the pan | ≥ 2023 t +1,64, bat 100 % du bruit | t global 1,45, ≤ 2022 +0,80 | +0,36 (calculé ici) | oui |
| 13 | BTC cassure 30 min | coffre ETF +1,87 | années jamais vues 2017-2021 **+0,70** ; 2025-2026 négatif | non mesurée | partiel |
| — | Filtre delta H1 | coffre t 2,34 (5 écartés) | **démenti ensuite** : P2 Rithmic filtrée +220 contre +670 sans filtre ; 15 ans t 1,62 | — | non (pas de delta avant avril 2026) |

Pas de preuve hors échantillon positive (pour mémoire) : toute la machine scalping v4/v5 (0/16 au coffre, candidates
NQ écartées par le coffre du passé), tendance seule (2023-2026 Sharpe −0,16, virtuel −1 434 $, challenge perdu),
version 7 (rejetée, virtuel −1 060 $), E6 (morte depuis 2023), zone implicite, modèle ridge, phénomènes, bruit, annonces,
variantes d'entrée/sortie J, K, L, M, N, P, C1-C3, E1, E2, S1, L1 (toutes sous la zone d'origine sur les deux périodes).

### Régénérables sur 2011-2026 pour combiner avec la zone (même calendrier de séances)

| Série | Commande (section 6) | Période obtenue | Vérification |
|---|---|---|---|
| Zone V1, rebond, RSI(2) | `serie_zone.py` (+ `ROBOT_DEBUT_RSI2=2011-01-01`) | 2011-03-02 → 2026-10-28 (3 933 séances) | rebond 2011-2022 +6 871 $ = README ; RSI(2) 2023-2026 +10 856 $ (README : +11 098 $ jusqu'au 25/09) |
| Zone (partie G), H1-H16, F1-F8 | `serie_regles.py` | 2011-01-03 → 2026-10-28 | zone t +4,22 (publié 4,21), H12 +2,92, H1 +2,29 (2,25 publié jusqu'en sept.), H5 +1,97, F3 +1,75, F7 +1,43 |
| Tendance, achat, mélange | `serie_tendance.py` | 2007 → 2026-10 | Sharpe 0,56 / 0,56 / 0,78 ; 2023-2026 −0,16 / 0,58 / 0,37 = README |
| Zone H1, E1, E2, S1, L1 (`entree_tardive`) | `quotidien.py … jours_15ans.csv <col>` | 2011-01-24 → 2026-10-19 | H1 +10 721,25 pts = publié |
| Bot 3 en 1 : N1+vol2, version A, A2, règle ×1/×1,5/×2, fenêtre 5, Q1, Q2, Q1+Q2, sans sortie, stop 70 | `quotidien.py … scalping/resultats/j/<fichier>_trades.csv` | 2011-01-24 → 2026-10-23 | totaux identiques aux tableaux (ex. fenêtre 5 +1 968 pts, version A +8 569) |
| Renfort, or Londres, T1, BTC 30 min | scripts des vagues (séries internes, à écrire en CSV) | 2011/2012-2026 (BTC 2017-2026) | non lancé ici |

---

## 6. Commandes de régénération (testées le 29 octobre 2026)

Scripts dans `/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad/inventaire/outils/`,
séries produites dans `…/inventaire/donnees/` (`zone_rsi2_quotidien.csv`, `regles_quotidien.csv`, `tendance_quotidien.csv`).
Rien n'est écrit dans le dépôt (lecture par `git show` / `git archive`).

```bash
R=/home/user/scalping-telegram-bot
S=/tmp/claude-0/-home-user-scalping-telegram-bot/73d2fc28-0760-5668-987b-2a927564efe7/scratchpad/inventaire
# données : minutes NQ de la recherche (2011 - 25/09/2026) + minutes du robot (24/09/2025 -> aujourd'hui)
git -C $R show origin/claude/keen-babbage-r686cl:intraday/donnees/nasdaq100_1min.csv.gz > $S/donnees/nq_recherche.csv.gz
git -C $R show origin/main:zone/robot/nq_1min.csv.gz > $S/donnees/nq_robot.csv.gz
git -C $R show origin/main:zone/robot.py > $S/code_main/zone_robot.py

# 1) zone V1 + rebond + RSI(2), $ pour 1 MNQ par séance (code du robot de main, serie_du_bot)
ROBOT_DEBUT_RSI2=2011-01-01 python3 -I $S/outils/serie_zone.py $S/code_main $S/donnees/nq_recherche.csv.gz \
    $S/donnees/nq_robot.csv.gz > $S/donnees/zone_rsi2_quotidien.csv

# 2) règles E-H (scalping/) : H1-H16, F1-F8 et zone partie G, $ pour 1 MNQ au prix d'aujourd'hui
git -C $R archive origin/claude/exciting-fermat-sea2l2 scalping | tar -x -C $S/code_fermat
(cd $S/code_fermat/scalping && python3 $S/outils/serie_regles.py $S/donnees/nq_2011_2026.csv.gz > $S/donnees/regles_quotidien.csv)
#    nq_2011_2026.csv.gz = les deux fichiers de minutes mis bout à bout, à faire AVANT cette étape :
#    (cd $S/donnees && python3 -I -c "import pandas as pd; a=pd.read_csv('nq_recherche.csv.gz'); b=pd.read_csv('nq_robot.csv.gz'); \
#      pd.concat([a, b[b.t > a.t.max()]], ignore_index=True).to_csv('nq_2011_2026.csv.gz', index=False)")

# 3) tendance, achat permanent, mélange (code et prix de main)
for f in systeme.py challenge_phidias.py; do git -C $R show origin/main:tendance/$f > $S/code_main/tendance/$f; done
git -C $R show origin/main:tendance/donnees/prix.csv.gz > $S/code_main/tendance/donnees/prix.csv.gz
python3 -I $S/outils/serie_tendance.py $S/code_main/tendance $S/donnees/zone_rsi2_quotidien.csv > $S/donnees/tendance_quotidien.csv

# 4) séries déjà publiées (aucune donnée de marché) : points nets 1 MNQ par jour
python3 $S/outils/quotidien.py origin/claude/elegant-ptolemy-g94s8t entree_tardive/jours_15ans.csv H1   # ou E1, E2, S1, L1
python3 $S/outils/quotidien.py origin/claude/exciting-fermat-sea2l2 scalping/resultats/j/reglages_26oct_g_trades.csv
#   autres fichiers : reglages_26oct_trades (N1+vol2), _b (version A), _d (A2), _f_trades_x1 / x1.5 / x2,
#   reglages_27oct_q1 / q2 / q7 (Q1+Q2), _sans_sortie, _stop70_fixe (points recalculés : sens x (sortie - entrée) - 1,5)
#   Attention : entree_tardive/trades/L1_15ans.csv contient aussi les trades non pris (colonne garde) : utiliser jours_15ans.csv.

# 5) bot 3 en 1 en C# (trades jour par jour, .NET 8) : variables CASSURE, COURIR, VOLUME, VOLMULT, SANS_TARDIVE,
#    FENETRE, Q1, Q2, SANS_SORTIE, STOP, SANS_FILTRE, RELANCE (bot3en1/Bot3en1.Replay/Program.cs)
#    SANS_FILTRE=1 CASSURE=1 VOLUME=1 VOLMULT=1 SANS_TARDIVE=1 COURIR=1 FENETRE=5 SANS_SORTIE=1 STOP=70 \
#      dotnet run -c Release --project Bot3en1.Replay -- nq_2011_2026.csv.gz - 2011-01-03 2026-10-23

# 6) vagues etude_large (séries internes, pas de CSV quotidien publié) :
#    KB=<recherche extraite> python3 etude_large/pistes/renfort/etude.py ; .../or_londres/etude.py ;
#    .../zone_implicite/etude.py exploration|coffre ; python3 etude_large/crypto/etude.py
```

Corrélations de la zone **(calculé ici sur 2011-2026)** : RSI(2) −0,06 ; rebond +0,21 ; tendance −0,05 ; mélange −0,06 ;
achat −0,02 ; H12 +0,44 ; H1 +0,39 ; H5 +0,50 ; F3 +0,44 ; F7 +0,36 ; F2 +0,10.
