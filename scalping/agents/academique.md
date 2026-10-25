# Prévisibilité intraday des futures sur indices (NQ / ES), horizon 1 min – 2 h : ce que dit la recherche

Agent « académique », 25 octobre 2026. Rapport en lecture seule : aucun fichier du dépôt n'a été modifié.

**Limites de cette recherche, à lire d'abord.** WebFetch était inutilisable (résolution DNS refusée sur tous les
domaines : SSRN, NBER, New York Fed, RePEc...). Tout repose sur WebSearch, c'est-à-dire sur les résumés et extraits
d'articles renvoyés par le moteur. Les chiffres marqués « (résumé) » viennent de ces extraits, pas du texte intégral.
Ceux marqués « (de mémoire) » viennent de ma connaissance des articles et n'ont pas été revérifiés en ligne. Le quota de
recherches web de la session a été épuisé avant la fin : deux pistes n'ont pas pu être creusées (prévisibilité de la
séance de jour par les séances Asie/Europe, et études intraday spécifiques au NQ).

Conversion utilisée partout : NQ ≈ 25 000 points, donc **1 point de base (bp) ≈ 2,5 points NQ ≈ 5 $ par MNQ**.
L'aller-retour MNQ à ~3 $ coûte donc **≈ 0,6 bp**.

---

## 1. Ce qu'on peut espérer : calibrage par la littérature sur la réplication et le surapprentissage

| Étude | Résultat chiffré | Ce que ça implique pour ce projet |
|---|---|---|
| McLean & Pontiff (2016, *J. Finance*), 97 anomalies | Rendement −26 % hors échantillon avant publication, −58 % après publication (de mémoire ; le −58 % est confirmé par un résumé) | Une règle publiée vaut en moyenne moins de la moitié de son backtest |
| Hou, Xue & Zhang (2020, *RFS*), « Replicating Anomalies » | 65 % des 452 anomalies échouent à t = 1,96 ; 82 % à t = 2,78 (résumé) | La plupart des « effets » publiés sont du bruit ou des microcapitalisations |
| Harvey, Liu & Zhu (2016, *RFS*) | Seuil t > 3 recommandé à cause des tests multiples (de mémoire) | Pour 600 000 stratégies essayées, le seuil est bien plus haut (voir ci-dessous) |
| Jensen, Kelly & Pedersen (2023, *J. Finance*), « Is there a replication crisis in finance? » | Avec une méthode bayésienne, la majorité des facteurs *transversaux* répliquent (de mémoire) | Nuance : ça concerne les actions en coupe transversale, pas le timing intraday d'un indice |
| Suhonen, Lennkh & Perez (2017, *J. Portfolio Mgmt*) | 215 stratégies vendues par des banques : ratio de Sharpe médian **1,20 en backtest → 0,31 en réel (−73 %)** ; 8,4 % seulement font aussi bien en réel ; les plus complexes perdent 30 % de plus (résumé) | Diviser par 3 à 4 tout Sharpe de backtest, plus encore si la règle est complexe |
| Bailey, Borwein, López de Prado & Zhu (2017), probabilité de surapprentissage ; Bailey & López de Prado (2014), Sharpe dégonflé | Essayer plus de ~45 configurations sur 5 ans suffit presque à coup sûr pour trouver un Sharpe de 1 en échantillon dont l'espérance hors échantillon est 0 (résumé CXO) | La machine évolutive (600 000 + 1,2 million d'essais) est le cas extrême : son échec hors échantillon était attendu |
| Fischer & Krauss (2018, *EJOR*), LSTM sur le S&P 500 | Avant frais : 0,46 %/jour, Sharpe 5,8 ; **depuis 2010 la rentabilité tourne autour de zéro après frais** (résumé) | Les réseaux de neurones sur données de prix publiques ont perdu leur avantage vers 2010 |
| Mesfin (2026, arXiv 2605.17724), LSTM et gradient boosting **sur le MNQ**, barres de 5 min, 2021-2025, validation glissante | Aucune configuration ne bat le taux de base de 51,8 % (50,0 % – 50,9 % ; p = 0,135 et 0,515) ; importances de variables instables (résumé) | Confirme l'échec de la régression logistique : l'OHLCV d'un seul instrument ne suffit pas |

**Seuil de chance pour la machine évolutive (mon calcul, pas une source) :** sous l'hypothèse nulle, le meilleur t parmi
N essais indépendants vaut environ √(2 ln N). Pour N = 600 000, c'est ≈ 5,2. Un t de 4 ou 5 en échantillon trouvé
par cette machine reste compatible avec le hasard pur. Pour une règle *publiée* et testée une seule fois, t > 2 hors
échantillon (2021-2026) suffit à la garder en observation.

**Conclusion de calibrage.** Aux horizons 1 min – 2 h, la littérature récente ne documente **aucune règle directionnelle
continue** (qui trade tous les jours) sur futures d'indice qui tienne après frais et après publication. Ce qui reste
crédible est **événementiel** (FOMC), **lié à des flux forcés** (rééquilibrages, couvertures) ou **de la fourniture de
liquidité après un choc de flux**. Tous ces cas donnent **peu de trades** (8 à 12 par an), donc une preuve statistique
faible même s'ils sont vrais. La prévisibilité « continue » qui existe (Huddleston et al. 2023, Aleti et al. 2025)
exige les rendements de centaines d'actions toutes les 5 minutes, et son gain par trade est inférieur au coût MNQ.

---

## 2. Règles testables, classées de la plus prometteuse à la moins prometteuse

### Règle 1 : continuation de la conférence de presse du FOMC (la plus prometteuse)

- **Règle exacte.** Jours de réunion FOMC avec conférence de presse (toutes les réunions depuis 2019 ; une sur deux
  d'avril 2011 à 2018). Mesurer le rendement du NQ dans la fenêtre du communiqué : de 13 h 59 à 14 h 29 ET
  (approximation : la fenêtre exacte de l'article n'a pas pu être lue). À 14 h 30, au début de la conférence, entrer
  dans le **même sens** que ce rendement. Sortir à la fin de la conférence (≈ 15 h 15 – 15 h 30 ; prendre 15 h 30
  fixe). Pas de stop dans la version publiée, qui mesure une corrélation entre fenêtres.
- **Source.** Gómez-Cram, R. & Grotteria, M. (2022), « Real-time price discovery via verbal communication: Method and
  application to Fedspeak », *Journal of Financial Economics* 143(3), 993-1025.
  [LBS](https://lbsresearch.london.edu/id/eprint/2203) ;
  [résumé Alpha Architect](https://alphaarchitect.com/2022/04/gaining-an-edge-via-textual-analysis-of-fomc-meetings/).
- **Preuve.** 41 conférences, avril 2011 – janvier 2020. Corrélation entre le mouvement pendant le communiqué et le
  mouvement pendant la conférence : **44 % pour le S&P 500**, 58 % pour les eurodollars. Selon le résumé d'Alpha
  Architect, pour SPY, l'avantage de la stratégie commence 10 minutes après le début des questions-réponses et se
  stabilise vers 20 minutes. Pas de frais dans l'article (c'est une étude de découverte des prix). **Aucune réplication
  après publication trouvée** : 2020 – sept. 2026 donne ≈ 52 réunions hors échantillon, testables avec les barres
  d'une minute du NQ.
- **Mécanisme.** Le marché n'intègre pas tout le communiqué en 30 minutes ; le président explique ensuite les
  changements de texte, et les minutes où il en parle portent la corrélation. C'est une diffusion lente
  d'information verbale, pas un flux forcé. Rien n'oblige quelqu'un à payer cet avantage, ce qui le rend plus fragile
  qu'un effet de flux.
- **Ordre de grandeur (mon estimation).** Pour deux rendements normaux de corrélation ρ, gain moyen en suivant le
  signe ≈ ρ × σ × √(2/π) ≈ 0,35 σ. Si la fenêtre de la conférence a un écart-type de 40 à 60 bp sur le NQ, le gain
  brut est de 14 à 21 bp, soit **≈ 70 à 100 $ par MNQ contre 3 $ de frais**. Après la décote habituelle de 50 à 75 %,
  il reste 20 à 50 $ par trade. Avec seulement 8 trades par an, la variance est énorme.
- **Déjà testé ?** Non. La zone est coupée les jours de Fed, et la machine évolutive avait des « minutes
  d'événement 14 h » et des règles « suivre un mouvement de k minutes », mais apparemment sans condition « jour FOMC
  avec conférence, entrée à 14 h 30 ». À vérifier dans le code.
- **Données.** Calendrier FOMC (public) et barres d'une minute du NQ et de l'ES. Rien ne manque.

### Règle 2 : retournement à l'annonce du FOMC (Baglioni & Ribeiro), et pression de flux après l'annonce

- **Règle exacte (2a).** Jour FOMC, à 13 h 50 ET : acheter si le rendement des 24 heures précédentes (13 h 50 la
  veille → 13 h 50) est **négatif**, vendre s'il est **positif**. Clôturer en fin de séance (15 h 59 ou 16 h 00). Les
  auteurs achètent au prix vendeur et vendent au prix acheteur.
- **Règle (2b), variante de flux.** Après l'annonce, prendre le contre-pied du mouvement 14 h 00 – 14 h 15 (substitut
  du déséquilibre d'ordres) et le garder jusqu'à 16 h 00. Cette variante n'est pas la règle publiée : l'article mesure
  le déséquilibre acheteurs/vendeurs, pas le prix.
- **Sources.**
  - Baglioni, T. & Ribeiro, R. (2022), « The FOMC Announcement Reversal », document de travail
    ([résumé CXO](https://cxoadvisory.com/calendar-effects/stock-market-return-reversal-after-fomc-announcements) ;
    [thèse Insper](https://repositorio.insper.edu.br/handle/11224/7532)).
  - Boguth, O., Grégoire, V. & Martineau, C. (2019), « Price Pressure and Efficiency on FOMC Announcements »
    ([résumé](https://ies.keio.ac.jp/upload/20190716macro_Martineau_abstract-1.pdf)).
- **Preuve.**
  - 2a : 180 annonces FOMC programmées, oct. 1997 – janv. 2020, sur l'E-mini S&P 500, avec frais d'écart
    acheteur-vendeur. Le rendement moyen et le Sharpe n'ont pas pu être lus. L'article lie la performance au VIX et à
    l'incertitude de politique monétaire.
  - 2b : sur l'E-mini, les déséquilibres d'ordres après l'annonce provoquent des **retournements allant jusqu'à 60 bp
    sur plusieurs heures** (pression de prix, pas information).
  - Aucune réplication après publication.
- **Mécanisme.** Avant l'annonce, les positions se construisent dans un sens (la dérive pré-FOMC). L'annonce lève
  l'incertitude, ces positions se débouclent et la pression de prix se résorbe ensuite. Le payeur est celui qui doit
  ajuster sa position immédiatement après la nouvelle et cède de la liquidité.
- **Ordre de grandeur.** Jusqu'à 60 bp, soit ≈ 300 $ par MNQ, pour les plus gros déséquilibres. La moyenne est
  inconnue mais très probablement supérieure à 0,6 bp de frais.
- **Attention.** La règle 2b va en sens inverse de la règle 1 sur une partie de la même fenêtre : l'une suit
  l'information, l'autre efface la pression de flux. Les tester séparément et **ne pas adopter les deux sans un test
  joint**. Sans historique du côté agresseur (6 mois seulement), 2b est une approximation.
- **Déjà testé ?** Non sous cette forme (la zone est coupée les jours de Fed).

### Règle 3 : rééquilibrage des fonds de pension en fin de mois (Harvey, Mazzoleni & Melone)

- **Règle exacte.** Calculer, depuis le dernier jour ouvré du mois précédent, l'écart d'un portefeuille 60/40
  (S&P 500 / obligations à 10 ans) à sa cible. Si les actions sont **surpondérées** (elles ont battu les obligations
  sur le mois), vendre les actions sur les derniers jours du mois ; acheter dans le cas inverse. L'article combine un
  signal calendaire (dernier jour ouvré du mois) et un signal de seuil (δ non lu). La version publiée trade un écart
  E-mini S&P long ou court contre future T-note à 10 ans, tenu jusqu'à ~2 semaines. Version NQ seul, adaptée à la
  contrainte de clôture avant 17 h : le dernier jour ouvré du mois, entrer à 9 h 30 dans le sens du rééquilibrage
  attendu et sortir à 15 h 59.
- **Source.** Harvey, C., Mazzoleni, M. & Melone, A. (2025, rév. janv. 2026), « The Unintended Consequences of
  Rebalancing », NBER WP 33554. [NBER](https://www.nber.org/papers/w33554) ;
  [PDF](https://www.nber.org/system/files/working_papers/w33554/w33554.pdf) ;
  [diapositives EDHEC](https://www.edhec.edu/sites/default/files/2026-03/slides_EDHEC_Michele%20Mazzoleni%20%281%29.pdf).
- **Preuve.**
  - Futures quotidiens de sept. 1997 à mars 2023. Quand les actions sont surpondérées, le rendement des actions baisse
    de **17 bp le jour suivant**. La pression disparaît presque entièrement en deux semaines.
  - La stratégie long-court S&P/T-note a un **Sharpe > 1** et une asymétrie de 5,23 (résumés). Frais : non lus.
  - Une étude indépendante sur Zagreb (2003-2025) trouve le même signe, avec un meilleur moment environ 5 jours avant la
    fin du mois ([Hrčak](https://hrcak.srce.hr/index.php/clanak/480642)).
  - Trop récent pour une preuve après publication.
- **Mécanisme.** Il est solide : des milliers de milliards gérés en 60/40 doivent revenir à leur cible par calendrier
  ou par seuil, quel que soit le prix. Les auteurs estiment ce coût à ~16 milliards $ par an. C'est le type d'effet
  qu'un tiers *paie* vraiment.
- **Ordre de grandeur.** 17 bp ≈ **85 $ par MNQ** par signal si tout l'effet tombe pendant la séance (inconnu) ; 12
  signaux par an.
- **Limite.** Ce n'est **pas du scalping**, et l'effet est d'abord quotidien. La contrainte de clôture avant 17 h
  oblige à ne capter que la partie intraday.
- **Déjà testé ?** Probablement pas avec ce signal conditionnel actions-contre-obligations. Les 232 736 stratégies
  journalières contenaient sans doute des effets de calendrier, mais pas cette condition. Les données suffisent : NQ ou
  ES au jour, et TLT ou un future obligataire au jour (dans les ~40 futures quotidiens).

### Règle 4 : dérive pré-FOMC, seulement quand l'incertitude est élevée

- **Règle exacte.** Jour FOMC, acheter le NQ à l'ouverture (9 h 30) et vendre à 13 h 59, juste avant l'annonce.
  Version conditionnelle : seulement si le VIX de la veille est au-dessus de sa médiane mobile sur un an. Hu et al.
  utilisent le VIX comme mesure de l'incertitude, et le seuil de médiane est mon choix.
- **Sources.**
  - Lucca & Moench (2015, *J. Finance*) : +49 bp sur le S&P 500 dans les 24 h avant le FOMC, 1994-2011 (de mémoire).
  - Kurov, Wolfe & Gilbert (2021, *Finance Research Letters* 40), « The Disappearing Pre-FOMC Announcement Drift » :
    l'effet **disparaît après 2015**, avec ou sans conférence de presse
    ([PDF](https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf)).
  - Un document de travail de la BRI ([WP 1079](https://www.bis.org/publ/work1079.pdf)) : depuis 2011, la dérive
    s'est déplacée **au deuxième jour avant l'annonce** et réduite à 22 bp (résumé).
  - Hu, Pan, Wang & Zhu (2022, *JFE* 145(3)), « Premium for heightened uncertainty » : les rendements avant annonce
    (FOMC, emploi, ISM, PIB) sont surtout **de nuit** et plus forts quand l'incertitude est haute
    ([PDF](https://www.mit.edu/~zhuh/HuPanWangZhu_preannouncement.pdf)).
  - Ignatieva & Ohashi (2025, *Applied Economics* 57(17)) : dérive présente mais de courte durée.
- **Preuve.** Effet fort jusqu'en 2011-2015, puis ≈ 0 en moyenne. La version conditionnelle n'a pas été répliquée
  hors échantillon.
- **Mécanisme.** Prime de risque pour porter l'incertitude jusqu'à l'annonce. Elle n'existe que si l'incertitude est
  élevée.
- **Ordre de grandeur.** Si 20 à 50 bp survivent les jours d'incertitude élevée : 100 à 250 $ par MNQ, sur ~4 trades
  par an. Sinon, rien.
- **Limite.** Hu et al. montrent qu'une grande partie du gain se fait **de nuit**, hors de la fenêtre 9 h 30 – 14 h.
- **Déjà testé ?** Seulement comme filtre de la zone (« jours de Fed »), pas comme règle autonome.

### Règle 5 : dérive de nuit à l'ouverture européenne (Boyarchenko, Larsen & Whelan)

- **Règle exacte.** Acheter le NQ à 2 h 00 ET et vendre à 3 h 00 ET, tous les jours de semaine. Variante publiée
  conditionnelle : seulement après une séance américaine en baisse (rendement clôture-clôture négatif, ou
  déséquilibre vendeur à la clôture). Les ventes massives provoquent des retournements de nuit robustes, les hausses
  des retournements bien plus faibles.
- **Source.** Boyarchenko, N., Larsen, L. C. & Whelan, P. (2023), « The Overnight Drift », *Review of Financial
  Studies* 36(9), 3502-3547 ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3546173)). Suite par les
  mêmes auteurs : « The Disappearing Overnight Drift » (Liberty Street Economics, 1er juillet 2026,
  [lien](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/) ;
  [SSRN 7035838](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7035838)).
- **Preuve.**
  - E-mini S&P, 1998-2019 : la fenêtre 2 h – 3 h rapporte ≈ 3,6 – 3,7 % par an, soit plus de 60 % du rendement
    clôture-clôture de 5,9 % par an. Le motif existait aussi sur NQ et YM.
  - **Selon les auteurs eux-mêmes, la fenêtre est plate de janvier 2021 à décembre 2025.**
  - Un résumé CXO indique que l'écart acheteur-vendeur rend négatif le rendement de l'heure de nuit, et que la fenêtre
    8 h 30 – 10 h sur l'ES rapporte −3,9 % par an.
  - Selon un résumé de moteur de recherche (non vérifié), les vendeurs écouleraient de plus en plus leurs stocks à
    l'ouverture asiatique, et la dérive aurait migré vers cette ouverture.
- **Mécanisme.** Prime de stockage des teneurs de marché (Grossman-Miller) : ils absorbent les ventes de fin de
  séance et sont payés quand les acheteurs européens arrivent.
- **Ordre de grandeur.** 3,6 % / 252 ≈ 1,4 bp ≈ **7 $ brut par MNQ** avant 2021, contre 3 $ de frais. Depuis 2021,
  ≈ 0.
- **Déjà testé ?** Partiellement (les 526 stratégies de sessions Asie/Londres/New York). Ce test est très peu coûteux
  avec les barres de 5 min HistData 24 h/24. Il sert surtout à **confirmer la disparition** et à vérifier si la
  dérive s'est déplacée vers 18 h – 21 h ET, l'ouverture asiatique.

### Règle 6 : prévision à 5 minutes par les rendements retardés des composants (apprentissage automatique)

- **Règle exacte.** Toutes les 5 minutes, prédire le rendement des 5 minutes suivantes de l'indice à partir des
  rendements retardés des **composants** (Huddleston et al.) ou des portefeuilles de facteurs du « factor zoo » (Aleti
  et al.), par des modèles régularisés (LASSO, ridge, forêts, ensembles). Trader le signe de la prévision.
- **Sources.**
  - Huddleston, D., Liu, F. & Stentoft, L. (2023), « Intraday Market Predictability: A Machine Learning Approach »,
    *Journal of Financial Econometrics* 21(2), 485-527 ([SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3726765)).
  - Aleti, S., Bollerslev, T. & Siggaard, M. (2025), « Intraday Market Return Predictability Culled from the Factor
    Zoo », *Management Science* 71(9), 7731-7751 ([DOI](https://dx.doi.org/10.1287/mnsc.2023.01657)).
- **Preuve.**
  - Huddleston et al. : SPY, 2001-2016, R² hors échantillon de **0,24 %** à 5 minutes, Sharpe de **0,98 après
    frais** (frais d'ETF).
  - Aleti et al. : Sharpe et alphas hors échantillon positifs après frais sur ETF. La prévisibilité a **baissé après
    la décimalisation** ; elle est plus forte en milieu de séance et les jours volatils, peu liquides ou de crise.
- **Mécanisme.** Capital lent : l'information arrive d'abord dans certaines actions ou certains facteurs, puis
  l'arbitrage panier-indice la transmet avec retard.
- **Ordre de grandeur (mon calcul).** Un R² de 0,24 % correspond à une corrélation de ≈ 0,05. Avec un écart-type de
  ≈ 10 bp à 5 minutes, le gain moyen vaut ≈ 0,05 × 10 × 0,8 ≈ 0,4 bp ≈ **2 $ par MNQ, inférieur aux 3 $ de frais**.
  Le résultat « après frais » de l'article repose sur le coût de SPY (≈ 0,2 bp l'aller-retour), environ trois fois
  moins cher que le MNQ.
- **Données manquantes.** Les rendements de 5 minutes des ~100 composants du Nasdaq 100 (ou les facteurs haute
  fréquence construits depuis TAQ). Un substitut grossier : les ETF sectoriels de 5 minutes, si la base contient
  XLK, SMH, etc.
- **Déjà testé ?** Le modèle logistique à 15 variables ressemble à cette approche, mais sans les composants. Ne
  vaut le coup que si les données des composants sont disponibles, et seulement en ne tradant que les prévisions les
  plus extrêmes.

### Règle 7 : aimantation vers le prix d'exercice le jour d'expiration (« pinning »)

- **Règle exacte.** Le jour d'expiration des options mensuelles (3e vendredi), de 14 h à 16 h : acheter si le NQ
  est sous le prix d'exercice rond le plus proche à forte position ouverte, vendre s'il est au-dessus. Sortir à la
  clôture.
- **Sources.**
  - Golez, B. & Jackwerth, J. (2012), « Pinning in the S&P 500 futures », *JFE* 106(3), 566-585
    ([RePEc](https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html)).
  - Ni, Pearson & Poteshman (2005, *JFE*) sur les actions.
- **Preuve.**
  - Golez et Jackwerth : le future S&P est attiré vers le prix d'exercice à la monnaie les jours d'expiration des
    options sérielles sur futures. **Il s'en écarte** juste avant l'expiration des options SPX (anti-aimantation).
    Déplacement d'au moins 115 M$ de valeur notionnelle par expiration. Données des années 1990-2000.
  - Une étude récente sur SPY (2016-2025, 1,6 million de contrats, 2 294 jours), connue seulement par un blog donc
    non vérifiée, ne trouve **aucune aimantation** mais une **amplification** : plus de position ouverte à la monnaie
    donne des ranges plus larges ([Harbourfront](https://harbourfrontquant.substack.com/p/from-pinning-to-amplification-evidence)).
  - Dim, Eraker & Vilkov (« 0DTEs: Trading, Gamma Risk and Volatility Propagation ») : le gamma des options 0DTE ne
    laisse pas de volatilité résiduelle et n'amplifie pas les rendements récents.
- **Mécanisme.** Rééquilibrage des couvertures delta des teneurs de marché quand le gamma à la monnaie est élevé.
- **Ordre de grandeur.** Quelques points à quelques dizaines de points si l'effet existe, mais la preuve récente va
  dans l'autre sens.
- **Données manquantes.** La position ouverte par prix d'exercice des options QQQ/NDX (sans elle, on approxime par
  des multiples de 100 ou 250 points du NDX).
- **Déjà testé ?** En grande partie : niveaux ronds (machine évolutive), nombres ronds d'Osler, GEX. La seule
  nouveauté serait la restriction aux après-midi d'expiration.

### Règle 8 : suivre la dérive avant une annonce macro (fuites d'information)

- **Règle exacte.** Pour les annonces de 8 h 30 et 10 h qui font bouger le marché : à T−1 minute, prendre la
  position dans le sens du mouvement T−30 → T−1, et sortir à T+5 ou T+15 minutes.
- **Sources.**
  - Kurov, Sancetta, Strasser & Wolfe (2019), « Price Drift before U.S. Macroeconomic News: Private Information about
    Public Announcements? », *JFQA* 54(1), 449-479
    ([PDF](https://www.skidmore.edu/economics/documents/KSSW2017-PriceDriftBeforeUSMacroeconomicNews.pdf)).
  - Kurov, Sancetta & Wolfe, « Drift Begone! » ([PDF](https://pure.royalholloway.ac.uk/files/45897404/ReleasePoliciesInformedTrading.pdf)).
- **Preuve.**
  - E-mini S&P et T-note, 2003/2008 – 2014 : 7 annonces sur 18 qui font bouger le marché (selon la version)
    montrent des échanges informés environ **30 min avant** la publication. Cette dérive représente **≈ 40-50 %** de
    l'ajustement total.
  - Au Royaume-Uni, la dérive **s'affaiblit** après la fin de l'accès anticipé des fonctionnaires aux données (2017).
  - Le contrôle de la diffusion américaine a lui aussi été resserré après 2013-2014. Effet probablement affaibli,
    non mesuré après 2014.
- **Mécanisme.** Fuites ou meilleure prévision à partir de données propriétaires : on suit des initiés.
- **Ordre de grandeur.** Pour les rares annonces concernées, la dérive pré-annonce vaut quelques bp. Le gain vient
  surtout du saut à l'annonce, mais le sens du saut n'est connu qu'à ≈ 50 %.
- **Déjà testé ?** Oui en grande partie : minutes d'événement 8 h 30 et 10 h, et « mouvement de k minutes, suivre »
  dans la machine évolutive.

---

## 3. Pistes examinées et écartées (absence de preuve, ou déjà testé)

**Avance-retard entre marchés : rien d'exploitable avec des barres d'une minute.**
- **QQQ → NQ, SPY → ES.** La découverte des prix se fait surtout **dans les E-mini**, et les ETF suivent (Hasbrouck
  2003, *J. Finance*, « Intraday price formation in U.S. equity index markets » ;
  [document NYU](https://archive.nyu.edu/jspui/bitstream/2451/27374/2/FIN-00-046.pdf)). Le décalage restant se
  compte en millisecondes (Budish, Cramton & Shim 2015, de mémoire), invisible en barres d'une minute.
- **Grandes valeurs (Apple, Nvidia, Microsoft) → NQ.** Je n'ai trouvé **aucune étude** montrant une avance à la
  minute pour les futures. Chinco, Clark-Joseph & Ye (2019, *J. Finance*, « Sparse signals in the cross-section of
  returns », de mémoire) prédisent à 1-3 minutes les rendements d'*actions individuelles* à partir des rendements
  retardés d'autres actions, avant frais. Ce n'est pas l'indice. Aleti et al. (2025) et Huddleston et al. (2023)
  constituent la version « indice » (règle 6) : gain par trade inférieur au coût MNQ.
- **Obligations, dollar, pétrole, bitcoin → NQ.** Aucune étude trouvée qui établisse une avance directionnelle
  intraday exploitable. Une étude sur des bougies d'une heure (arXiv 1504.06235) trouve une co-évolution des extrêmes
  avec 5 à 10 minutes de décalage, présentée comme « une tendance plutôt qu'un timing absolu ». Rien non plus sur
  « bitcoin du week-end → NQ du lundi ». Le contexte indique que ES↔NQ, bitcoin, taux et dollar ont été testés sans
  succès, ce qui concorde.
- **VIX et futures sur VIX.** Bollen, O'Neill & Whaley (2017, *J. Futures Markets*) et Frijns et al. (2016) montrent
  que les futures sur VIX mènent l'*indice* VIX, pas l'ES. Aucune règle pour le NQ.
- **Europe et Asie → États-Unis.** Seule la piste de la dérive de nuit (règle 5) est documentée. Levy & Lieberman
  (2013) montrent qu'en sens inverse, le S&P domine les ETF pays quand leurs marchés sont fermés. Recherche incomplète
  (quota épuisé).

**Momentum et retournement intraday : couverts, et fragiles.**
- Li, Sakkas & Urquhart (2022, *J. Financial Markets* 57) : momentum intraday dans 16 pays, en et hors échantillon ;
  plus fort quand la liquidité est faible, la volatilité forte et l'information discrète. Frais non lus.
- Rosa (2022, *J. Futures Markets* 42(12)) : la prévision de la dernière demi-heure par le rendement de nuit
  **disparaît hors échantillon**. Version avec seuil d'entrée meilleure qu'une version toujours active.
- Un résumé CXO sur SPY 1999-2012 donne un R² hors échantillon de 0,018 pour « première demi-heure → dernière ».
- Retournements après de gros mouvements à l'ouverture : Fung, Mok & Lam (2000), Grant, Wolf & Yu (2005, testé). La
  significativité **chute avec les frais**.
- Rebalancement des ETF à levier (TQQQ) en fin de séance : même règle que Baltussen et al., déjà testée.
- Autocorrélation des indices : Baltussen, van Bekkum & Da (2019, *JFE*) montrent qu'elle est devenue **négative**
  depuis les années 2000 dans 20 indices, avec la montée des produits indiciels. Cela plaide pour le contre-pied
  plutôt que le suivi, mais à l'horizon du jour (le rebond après forte baisse a déjà été testé et reste faible).
- Badshah et al. (2016) : relation rendement-volatilité asymétrique de 1 à 60 min ; c'est de la volatilité, pas du
  sens.

**Saisonnalités fines : rien de stable.**
- Minutes et demi-heures : CXO (SPY 2007-2008, puis 2012-2014) trouve que le creux de milieu d'après-midi ne se
  confirme pas ensuite, et qu'il n'y a « aucun motif de rendement stable », seulement la volatilité en U.
- Heston-Korajczyk-Sadka et Bogousslavsky (2016) portent sur la *coupe transversale* des actions. Testé, négatif.
- Tournant du mois : Maberly & Waggoner (2000) le voient disparaître sur le future S&P après 1990.
- Semaine d'expiration : Stivers & Sun (2013, *JBF*) trouvent des rendements élevés pour le S&P 500 en 1983-2008, sans
  réplication après publication. C'est un effet hebdomadaire.
- Cycle FOMC en semaines paires : Cieslak, Morse & Vissing-Jorgensen (2019, *J. Finance*), aucune réplication
  après 2019 trouvée. Effet journalier, probablement couvert par les tests journaliers.

**Nuit contre jour.** L'essentiel de la prime des actions est gagné la nuit, et le rendement moyen de la séance de jour
est nul ou négatif (arXiv 2507.04481 ; Lou, Polk & Skouras 2019). Pour le scalping, cela signifie **aucun biais
acheteur gratuit en séance**. C'est cohérent avec l'adoption du RSI(2) de nuit.

**Options 0DTE et gamma.** Dim, Eraker & Vilkov : un gamma 0DTE élevé va avec **moins** de volatilité réalisée, et les
chocs de volume 0DTE n'amplifient pas les rendements. Le GEX a déjà été testé. Pas de règle directionnelle.

**Marketing à signaler.** Les blogs de vendeurs de gamma (SpotGamma, RTGamma), les analyses d'un seul jour et les
backtests « Quantified Strategies » ne constituent pas des preuves.

---

## 4. Recommandation de test (ordre, coût, critère d'arrêt)

1. **FOMC, règles 1 et 2a** (≈ 120 lignes de code, données disponibles). Tester sur avril 2011 – janvier 2020 pour
   reproduire le signe publié, puis février 2020 – sept. 2026 hors échantillon (≈ 52 réunions). Critère : signe
   identique hors échantillon, gain moyen > 10 $ par MNQ après 3 $ de frais, et résultat qui ne repose pas sur 2 ou 3
   réunions (refaire le test sans les 3 meilleures).
2. **Rééquilibrage de fin de mois, règle 3** (données quotidiennes et barres d'une minute du dernier jour). Hors
   échantillon naturel : avril 2023 – sept. 2026, après la fin de l'échantillon publié.
3. **Dérive de nuit, règle 5** : uniquement pour confirmer la disparition annoncée par les auteurs (2021-2026) et
   vérifier un éventuel déplacement vers l'ouverture asiatique. Peu coûteux avec les barres de 5 min HistData.
4. Règle 4 ensuite. Les règles 6 à 8 seulement si les données manquantes deviennent disponibles.

Ces règles donnent toutes au plus ~8 à 12 trades par an. Même vraies, elles ne remplacent pas un système de scalping
quotidien. La littérature ne permet pas d'en promettre un : elle prédit plutôt que tout système quotidien sur barres
d'une minute sera, en moyenne, mangé par 0,6 bp de frais.

---

## Sources principales (liens)

- Boyarchenko, Larsen & Whelan, The Overnight Drift, RFS 2023 : https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3546173 ;
  The Disappearing Overnight Drift (2026) : https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/
- Gómez-Cram & Grotteria, JFE 2022 : https://lbsresearch.london.edu/id/eprint/2203
- Baglioni & Ribeiro, The FOMC Announcement Reversal : https://cxoadvisory.com/calendar-effects/stock-market-return-reversal-after-fomc-announcements
- Boguth, Grégoire & Martineau, Price Pressure and Efficiency on FOMC Announcements : https://ies.keio.ac.jp/upload/20190716macro_Martineau_abstract-1.pdf
- Harvey, Mazzoleni & Melone, NBER w33554 : https://www.nber.org/papers/w33554
- Kurov, Wolfe & Gilbert, FRL 2021 : https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf
- Hu, Pan, Wang & Zhu, JFE 2022 : https://www.mit.edu/~zhuh/HuPanWangZhu_preannouncement.pdf
- BIS WP 1079 (pre-FOMC drift shift) : https://www.bis.org/publ/work1079.pdf
- Kurov, Sancetta, Strasser & Wolfe, JFQA 2019 : https://www.skidmore.edu/economics/documents/KSSW2017-PriceDriftBeforeUSMacroeconomicNews.pdf
- Huddleston, Liu & Stentoft, JFEc 2023 : https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3726765
- Aleti, Bollerslev & Siggaard, Management Science 2025 : https://dx.doi.org/10.1287/mnsc.2023.01657
- Aït-Sahalia, Fan, Xue & Zhou, NBER w30366 (prévisibilité à quelques secondes, disparaît après ~5 min) : https://www.nber.org/papers/w30366
- Mesfin, arXiv 2605.17724 (ML sur MNQ, résultat nul) : https://arxiv.org/pdf/2605.17724
- Golez & Jackwerth, JFE 2012 : https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html
- Li, Sakkas & Urquhart, JFM 2022 : https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html
- Rosa, JFM 2022 : https://ideas.repec.org/a/wly/jfutmk/v42y2022i12p2218-2234.html
- Baltussen, van Bekkum & Da, JFE 2019 : https://personal.eur.nl/vanbekkum/2018%20JFE%20BaltussenVanBekkumDa.pdf
- Suhonen, Lennkh & Perez : https://alphaarchitect.com/?p=36892
- Hou, Xue & Zhang, RFS 2020 : https://ideas.repec.org/a/oup/rfinst/v33y2020i5p2019-2133..html
- Bailey et al., Probability of Backtest Overfitting : https://papers.ssrn.com/abstract=2326253 ; Deflated Sharpe Ratio : https://papers.ssrn.com/abstract=2460551
- Fischer & Krauss (LSTM, fin de l'avantage après 2010), résumé : https://arxiv.org/pdf/1902.03125
- Grant, Wolf & Yu, JBF 2005 : https://ideas.repec.org/a/eee/jbfina/v29y2005i5p1311-1327.html
- Stivers & Sun, JBF 2013 : https://ideas.repec.org/a/eee/jbfina/v37y2013i11p4226-4240.html
- Hasbrouck / E-mini et ETF : https://archive.nyu.edu/jspui/bitstream/2451/27374/2/FIN-00-046.pdf
