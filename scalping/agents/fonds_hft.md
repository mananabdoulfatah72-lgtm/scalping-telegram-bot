# Fonds, HFT et desks de banques sur les futures d'indices : ce qu'ils font, ce qui reste accessible sur MNQ

Agent « fonds / HFT », 25 octobre 2026. Cadre : MNQ, latence de 50 à 300 ms (Rithmic), environ 3 $ par aller-retour,
barres d'une minute, positions à plat avant 17 h New York.

**Limites de cette recherche.** WebFetch échouait (DNS) et le proxy refusait curl (403). Je n'ai donc pas lu les
articles en entier : les chiffres viennent des résumés, des pages d'accueil et des sites miroirs renvoyés par le moteur de
recherche. Le quota de recherches web de la session a été épuisé en cours de route. Les chiffres que je n'ai pas pu
revérifier en ligne sont marqués **(de mémoire)** ou **(source secondaire)**.

Repère de coût. À NQ ≈ 22 000 points, 1 point de base (pb) vaut 2,2 points, soit environ 4,4 $ par MNQ. Un
aller-retour à 3 $ coûte donc environ **0,7 pb**, soit 1,5 point NQ ou 6 ticks.

---

## 0. Résumé en 8 lignes

1. Les métiers qui rapportent le plus aux professionnels sur les futures d'indices sont la tenue de marché et
   l'arbitrage de latence (ES/SPY, NQ/QQQ, futures/actions). Ils gagnent une fraction de tick par contrat, dans des
   fenêtres de 5 µs à 7 ms : c'est structurellement fermé à un particulier.
2. Le trading d'annonces au sens HFT (réagir à la publication) se joue en 5 ms, avec 50 000 $ de gain par annonce sur
   l'ES, partagés entre quelques firmes. C'est fermé aussi.
3. Ce qui reste théoriquement accessible, ce sont des **primes de risque autour d'événements programmés**, tenues
   plusieurs heures : dérive avant les annonces macro, dérive pré-FOMC, dérive de nuit. Le gain par trade est de 10 à
   50 pb, très au-dessus des 0,7 pb de frais. Mais ce n'est **pas du scalping**, il y a 8 à 36 événements par an, et deux
   de ces effets ont disparu ou faibli après publication.
4. Les données sur les particuliers sont sans appel. Moins de 1 % des day traders gagnent de façon prévisible (Taïwan).
   97 % de ceux qui persistent plus de 300 jours perdent (mini-indice brésilien). Les pertes viennent des ordres
   agressifs. Côté firmes de financement, environ 7 % des acheteurs d'évaluation touchent un paiement (sources
   secondaires).
5. Aucune étude publiée ne documente une règle de scalping sur barres d'une minute qui ait tenu après frais de détail et
   après publication. Le résultat de la machine évolutive (rien ne tient) est conforme à la littérature.
6. Règles à tester, de la plus à la moins prometteuse : (R1) achat de nuit avant NFP/ISM/PIB, sortie juste avant la
   publication ; (R2) dérive pré-FOMC les jours Fed, où la zone ne trade pas ; (R3) suivre la dérive des 30 minutes avant
   certaines annonces de 10 h (en partie couvert) ; (R4) dérive de 2 h à 3 h après une clôture vendeuse (morte depuis
   2021 selon ses auteurs) ; (R5) cycle du fixing de change sur l'euro (hors NQ).
7. Seul levier « scalping » réaliste : l'**exécution passive** des entrées du système existant, pour économiser le tick
   de glissement. C'est un levier d'exécution, pas une source d'avantage.

---

## 1. Ce que font réellement les professionnels, par famille

| Famille | Qui | Horizon | Gain par trade (ordre de grandeur) | Capacité | Ce qu'il faut | Accessible (MNQ, 1 min, 300 ms, 3 $) ? |
|---|---|---|---|---|---|---|
| **Tenue de marché** | Virtu, Citadel Securities, Jump, Optiver, IMC… | ms à secondes | Menkveld (2013), un HFT sur actions néerlandaises : **0,88 € net par trade** = 1,55 € de spread − 0,68 € de perte sur position, 1 397 trades par action et par jour. E-mini : revenu HFT moyen **≈ 1,11 $ par contrat ES (source secondaire)**, soit moins de 0,1 tick ES | Limitée par la profondeur, énorme en volume | Priorité dans la file (FIFO CME), colocation, frais de membre, programmes de teneur de marché | **Non.** Spread MNQ de 0,50 $ < 2 $ de commissions par aller-retour. Sans priorité de file, on est sélectionné à tort (adverse selection) |
| **Arbitrage de latence / stat arb ultra-court** (ES↔SPY, NQ↔QQQ, futures↔actions) | Mêmes firmes (top 6 > 80 % des courses gagnées à Londres) | µs à ms | Budish et al. : seuil de 0,05 point d'indice ; durée médiane des opportunités ES-SPY passée de **97 ms (2005) à 7 ms (2011)**, profit par opportunité à peu près constant ; ≈ 75 M$ par an pour ES-SPY **(de mémoire)**. Aquilina-Budish-O'Neill : environ une course par minute et par titre, **5 à 10 µs**, environ un demi-tick par course, environ 20 % du volume, « taxe » ≈ 0,5 pb | Plafonnée, environ 5 Md$ par an pour toutes les actions mondiales | Micro-ondes Aurora↔New Jersey (> 500 M$ sur 5 ans), FPGA | **Non**, latence 10³ à 10⁵ fois trop lente |
| **Arbitrage de base / d'indice** (futures contre panier, calendaires, roll) | Desks delta-one des banques, fonds relative value | Jours à mois | Fractions de pb de financement implicite ; écarts liés à la demande de levier (Hazelkorn, Moskowitz, Vasudevan, JF 2023, **de mémoire**) | Grande, mais dépend du bilan | Panier d'actions, financement au taux repo, bilan | **Non** : pas de panier, financement au taux de détail, détention de plusieurs jours interdite par la firme de financement |
| **Trading d'annonces (réaction)** | HFT | 0 à 5 ms | Chordia, Green, Kottimukkalur (RFS 2018) : prix ES/SPY ajustés **en 5 ms** ; profit ≈ **50 000 $ par annonce sur ES**, 19 000 $ sur SPY ; le flux d'ordres est de moins en moins informatif | Fixe par annonce | Flux de données direct, colocation | **Non** pour la réaction. Les dérives *avant* l'annonce sont traitées en section 4 |
| **Trading d'annonces (dérive avant)** | Traders informés (fuites, données privées) | 30 min avant | Kurov et al. (JFQA 2019) : dérive dans le bon sens **30 min avant**, ≈ 40 % de l'ajustement total, pour 7 annonces sur 18 (ou 9 sur 20 selon la version) | Faible | Information privée ou données propriétaires | Suivre le mouvement en partie (R3), mais l'effet dépend des fuites et disparaît quand on les ferme (Royaume-Uni, 2017) |
| **Momentum intraday / CTA court terme** | Crabel, QIM, desks systématiques | Minutes à jours | Crabel Multi-Product : surtout momentum et retour à la moyenne à court terme sur **environ 200 marchés**, stops par position et sorties temporelles, ≈ 1,4 Md$. QIM a fermé son programme global de 4,5 Md$ en 2010 (performance et capacité) | Moyenne | La **diversification sur des centaines de marchés** fait le ratio de Sharpe, pas l'avantage sur un marché donné | En partie : c'est ce que fait la zone de bruit (Zarattini-Aziz-Barbon). Un seul marché, c'est un Sharpe faible |
| **Retour à la moyenne / fourniture de liquidité** | Teneurs de marché, stat arb | Heures à 1 jour | Dérive de nuit (Boyarchenko-Larsen-Whelan, RFS 2023) : rémunération des intermédiaires qui absorbent les déséquilibres de clôture, **≈ 3,6 % par an concentrés entre 2 h et 3 h** (1998-2019), plus forte après une clôture vendeuse. **≈ 0 depuis 2021** (mêmes auteurs, juillet 2026) | Moyenne | Bilan, tolérance au risque de nuit | Testable (R4) mais mort selon ses propres auteurs |
| **Trading de volatilité / dispersion / 0DTE** | Fonds de volatilité, desks d'options | Jours | Prime de variance ; dispersion = vendre la volatilité de l'indice et acheter celle des composants | Moyenne | Options sur indice **et** sur composants, données intraday d'options | **Non** : la firme de financement ne permet que des futures, et il n'y a pas de données d'options intraday. Le « pinning » 0DTE n'est pas confirmé (Dim-Eraker-Vilkov : le gamma 0DTE ne propage pas la volatilité) |
| **Flux mécaniques** (ETF à levier, ciblage de volatilité, fixing de change) | Desks qui exécutent ces flux, ou ceux qui les devancent | Dernière heure ; heures autour du fixing | ETF à levier : Ivanov-Lenkey (2018) trouvent un effet **économiquement insignifiant** une fois les flux de capitaux pris en compte ; la revue de Lenkey (2024) signale des erreurs de méthode dans la littérature. Fixing de change : rendement en W, présent les 20 années de l'échantillon, mais selon les auteurs **exploitable seulement avec des coûts inférieurs à la moyenne** | Grande | Coûts institutionnels | Fin de séance déjà testée (Baltussen, Gao), négative. Fixing : hors NQ (R5) |
| **Stat arb sur actions** (Medallion, etc.) | Renaissance, D.E. Shaw, Two Sigma | Minutes à jours | Mercer (Renaissance) : « on a raison 50,75 % du temps » (cité par Zuckerman) : un avantage minuscule par trade, sur des milliers de positions simultanées | Plafonnée (Medallion est fermé aux investisseurs externes) | Milliers de titres, coûts par action institutionnels | **Non** sur un seul contrat |

**Ce qui fait gagner les pros et que le particulier n'a pas :**
- coûts 5 à 20 fois plus bas (frais de membre, remises) ;
- vitesse (µs contre 100 ms) ;
- priorité dans la file d'attente ;
- **agrégation de centaines de signaux faibles**, chacun inférieur aux coûts de détail ;
- bilan et financement.

McLean et Pontiff (JF 2016) chiffrent en plus l'usure : −26 % de rendement hors échantillon et −58 % après publication,
sur 97 anomalies d'actions.

---

## 2. Ce que montrent les données sur les day traders particuliers et les scalpeurs

| Étude | Marché, période | Résultat |
|---|---|---|
| Barber, Lee, Liu, Odean, *The Cross-Section of Speculator Skill*, J. Financial Markets 2014 | Actions de Taïwan, 1992-2006 | **Moins de 1 %** des day traders gagnent de façon prévisible et régulière, net de frais. Les 500 meilleurs de l'année précédente gagnent ensuite 61,3 pb par jour avant frais et 37,9 pb après (version publiée) : la compétence existe, mais elle est rarissime |
| Barber, Lee, Liu, Odean, Zhang, *Learning, Fast or Slow*, RAPS 2020 | Taïwan | 74 % du volume de day trading vient de traders qui ont déjà un historique de pertes ; 97 % perdront probablement à l'avenir |
| Barber, Lee, Liu, Odean, *Just How Much Do Individual Investors Lose by Trading?*, RFS 2009 | Taïwan | **Presque toutes les pertes des particuliers viennent de leurs ordres agressifs** ; leurs ordres passifs sont rentables à court horizon. Les institutions gagnent sur les deux types d'ordres |
| Chague, De-Losso, Giovannetti, *Day Trading for a Living?*, 2019-2020 | **Futures mini-Ibovespa** (Brésil), débutants de 2013-2015 | Parmi ceux qui ont persisté plus de 300 jours : **97 % perdent**, 1,1 % gagnent plus que le salaire minimum, 0,5 % plus qu'un guichetier de banque. Le meilleur gagne 310 $ par jour avec un écart-type de 2 560 $. Aucun apprentissage |
| Kuo et Lin, *Overconfident Individual Day Traders*, J. Banking & Finance 2013 | **Futures sur indice de Taïwan**, oct. 2007 - sept. 2008 | 3 470 day traders : perte moyenne de 61 500 TWD après frais et de **26 700 TWD avant frais** (ils perdent même sans frais). Moins de 20 % sont positifs (source secondaire). Pas d'apprentissage |
| Ferko, Mixon, Onur (CFTC, OCE), *Retail Traders in Futures Markets*, 2024 | Futures américains, févr. 2021 - nov. 2022, environ 36 500 comptes (source secondaire) | Médiane : 4 trades d'environ 4 jours. Comportement contrarien. Une grosse perte au premier trade fait quitter le marché. Les micro E-mini (MES, MNQ) sont très prisés |
| CFTC, Market Intelligence Branch (présentation au GMAC, mars 2021) | Futures, janv. 2020 - févr. 2021 | Rendements des comptes de détail « significativement négatifs » |
| Harris et Schultz, *The Trading Profits of SOES Bandits*, JFE 1998 | Nasdaq, années 1990 | Des day traders **gagnants** : petits gains, très fréquents, en prenant position **avant** que les teneurs de marché mettent à jour leurs cotations (cotations périmées). C'est un avantage de vitesse, repris depuis par les HFT |
| Garvey et Murphy (day traders d'une firme de compte propre, Island ECN) | Nasdaq | Les gagnants traitent quand des traders de liquidité sont présents et **mettent à jour leurs cotations avant les teneurs de marché** : encore la vitesse |
| Biais, Declerck, Moinas (BIS WP 563) | Euronext | Seuls les traders de compte propre parviennent à fournir de la liquidité par ordres limites sans perdre : la technologie ne suffit pas, il faut surveiller en permanence |
| Firmes de financement (chiffres déclarés par les firmes, relayés par des sites secondaires) | 2025 | Topstep : 16,8 % des évaluations (Combines) lancées en 2025 réussies ; 33,3 % des traders financés ont reçu au moins un paiement ; ≈ 0,7 % atteignent un compte réel (dénominateur incertain). Données FPFX (> 300 000 comptes, secteur) : ≈ 14 % réussissent et **≈ 7 % touchent un jour un paiement**. MyFundedFutures : 39,2 % des comptes financés ont eu au moins un paiement. Earn2Trade : 8,89 % de réussite |

**Ce qui distingue les rares gagnants, d'après ces études :**
1. un avantage de **vitesse** sur des cotations périmées (Harris-Schultz, Garvey-Murphy), aujourd'hui capté par les HFT ;
2. des ordres **passifs** plutôt qu'agressifs (Barber et al. 2009) ;
3. une compétence persistante mais très rare (moins de 1 %), qu'**aucune étude ne ramène à une règle publiable**.

Aucune de ces études ne fournit une règle de scalping sur barres d'une minute.

---

## 3. Stratégies systématiques documentées et accessibles (barres d'une minute, quelques minutes à quelques heures, NQ)

Je les ai cherchées précisément ; voici ce qui existe vraiment :

- **Momentum intraday** : Gao-Han-Li-Zhou, Baltussen et al., Zarattini-Aziz-Barbon. Déjà testé ou adopté.
- **Primes autour d'événements programmés** :
  - dérive pré-FOMC (Lucca-Moench, JF 2015) ;
  - rendements de nuit avant NFP, ISM et PIB (Hu-Pan-Wang-Zhu, JFE 2022) ;
  - dérive des 30 minutes avant certaines annonces (Kurov et al., JFQA 2019).
  
  C'est la seule famille documentée par des revues de premier rang qui ne soit ni testée ni fermée par la latence.
- **Dérive de nuit liée à l'inventaire des intermédiaires** (Boyarchenko-Larsen-Whelan) : ≈ 0 depuis 2021.
- **Fixing de change** (Krohn-Mueller-Whelan, JF 2024) : robuste, mais réservé aux coûts bas et hors NQ.
- **Paires NQ/ES conditionnelles** : je n'ai trouvé **aucune étude** de paires intraday NQ/ES avec frais. Ce qui existe
  porte sur des paires d'actions (Stübinger-Endres) ou ne sont que des exemples de courtiers sans coûts (Optimus Futures).
  L'écart NQ/ES est arbitré à la milliseconde par les HFT. Le prix de découverte est dans l'E-mini (Hasbrouck, JF 2003).
  Huth et Abergel montrent que le meneur prédit le mouvement suivant du suiveur à environ 60 %, mais qu'**une stratégie
  en ordres au marché ne gagne rien à cause du spread**. Avec deux jambes, les frais doublent (≈ 6 $). Pas de règle
  sourcée : je ne propose rien.
- **Dispersion** : impossible (options).
- **Réactions aux résultats des grandes valeurs** : déjà testé comme filtre. Je n'ai trouvé aucune étude intraday sur le
  NQ.

---

## 4. Règles concrètes et testables, de la plus à la moins prometteuse

### R1. Achat de nuit avant les grandes annonces macro (NFP, ISM, PIB), sortie juste avant la publication

- **Règle.** La veille d'une publication NFP (8 h 30), PIB (8 h 30, toutes estimations) ou ISM manufacturier (10 h) :
  achat d'1 MNQ à **18 h 00** à la réouverture Globex (et non à la clôture de 16 h, à cause de la règle « à plat avant
  17 h »). Sortie à **8 h 29** (NFP, PIB) ou **9 h 59** (ISM). Pas d'objectif, pas de stop serré : l'article mesure un
  rendement de détention, pas un trade avec stop. Un stop catastrophe large (par exemple 2 % ou 500 points) sert
  seulement à respecter la perte maximale de la firme.
- **Source.** Hu, Pan, Wang, Zhu, *Premium for Heightened Uncertainty: Explaining Pre-Announcement Market Returns*,
  Journal of Financial Economics 145(3), 2022, p. 909-936 ; NBER WP 25817 (2019).
  https://www.nber.org/papers/w25817 ; https://www.sciencedirect.com/science/article/abs/pii/S0304405X21004037
- **Preuve.** Rendements de nuit élevés avant NFP, ISM et PIB, **sans variance anormale**. Hors FOMC, le rendement
  pré-annonce vaut **3,41 % par an**, contre 0,69 pb par nuit ordinaire. Mesuré sur les futures S&P 500 ; je n'ai pas vu
  le texte intégral, ni la période exacte, ni le calcul après frais. **Rien n'est publié après 2019 sur cet effet.** Mise
  en garde importante : la dérive de nuit « générique » (R4) a disparu depuis 2021, et cet effet pourrait avoir suivi.
- **Mécanisme.** Prime d'incertitude : avant une annonce dont l'impact est incertain, les investisseurs exigent une prime
  qui se réalise à mesure que l'incertitude se dissipe, avant la publication.
- **Gain par trade.** 3,41 % par an répartis sur environ 30 à 36 événements, soit environ **10 pb par événement**,
  environ 22 points NQ ou **≈ 44 $ par MNQ, contre 3 $ de frais** (rapport d'environ 15). En revanche, l'écart-type d'une
  nuit est d'environ 150 à 200 points NQ (300 à 400 $) : c'est très bruité. Avec environ 250 événements de 2019 à 2026,
  l'erreur-type est d'environ 6 pb. On ne peut donc conclure qu'en gardant **exactement** les paramètres publiés et en
  utilisant toute la période postérieure à la publication (2019-2026), pas seulement 2023-2026.
- **Données.** Barres de 5 minutes CFD 24 h/24 (HistData) NQ et ES depuis 2012, plus un calendrier des dates NFP, ISM et
  PIB. Celui des annonces de 8 h 30 existe déjà ; il faut ajouter l'ISM de 10 h (calendriers BLS, BEA et ISM, gratuits).
- **Déjà couvert ?** Non. Les « annonces de 8 h 30 » n'ont été testées que comme *filtre de la zone* en séance, et les
  526 stratégies de sessions sont inconditionnelles. Compatible avec le RSI(2) de nuit si l'on gère le chevauchement.
- **Verdict.** La seule idée à la fois publiée dans une revue de premier rang, avec un gain par trade largement supérieur
  aux frais, accessible en latence et non testée. **Mais ce n'est pas du scalping** (une douzaine d'heures de détention),
  il y a peu d'événements, et le risque d'usure est réel.

### R2. Dérive pré-FOMC les jours de Fed (où la zone ne trade pas)

- **Règle.** Version originale : achat à 14 h 00 la veille de l'annonce FOMC, vente à 13 h 55 le jour J (annonce à
  14 h). Version compatible avec la firme : achat à **18 h 00 la veille** (ou à 9 h 30 le jour J, à tester séparément et
  sans réglage), vente à **13 h 55**. 8 événements par an.
- **Sources.**
  - Lucca et Moench, *The Pre-FOMC Announcement Drift*, Journal of Finance 2015 :
    https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf. En moyenne **+49 pb sur les 24 h
    précédant l'annonce**, 1994-2011 **(de mémoire, chiffre classique)**.
  - Mise à jour de la Fed de New York (2018) : l'effet persiste, mais seulement pour les réunions avec conférence de
    presse. Il y en a à **toutes** les réunions depuis 2019.
  - Kurov, Wolfe, Gilbert, *The Disappearing Pre-FOMC Announcement Drift*, Finance Research Letters 40, 2021 :
    **l'effet disparaît pratiquement après 2015**.
    https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf
  - BIS WP 1079 : après 2011, la dérive s'est déplacée vers l'avant-veille et réduite à environ 22 pb.
    https://www.bis.org/publ/work1079.pdf
  - Ignatieva et Ohashi, Applied Economics 2024-2025 : la dérive existe, mais l'effet des conférences de presse est
    éphémère.
- **Preuve.** Mitigée et contestée après publication, ce qui est le cas typique d'usure à la McLean-Pontiff.
- **Mécanisme.** Prime d'incertitude (Hu et al. 2022), ou résolution d'information avant l'annonce.
- **Gain par trade.** Entre 0 et 50 pb selon la période, soit de 0 à environ 220 $ par MNQ, contre 3 $.
- **Puissance statistique.** Faible : 24 événements entre 2023 et 2026 donnent une erreur-type d'environ 20 pb, donc
  impossible de valider. Il faut au moins 2016-2026 (≈ 85 événements) avec la règle publiée telle quelle.
- **Déjà couvert ?** En partie seulement : les « jours de la Fed » ont servi de filtre (pas de zone), et la machine a
  testé les minutes d'événement de 14 h. La détention de la veille à 13 h 55 n'a pas été testée. L'intérêt pratique est
  d'**occuper des jours où le système actuel ne trade pas**.

### R3. Suivre la dérive des 30 minutes qui précèdent certaines annonces de 10 h

- **Règle (construite à partir de l'article, sans paramètre publié pour trader).** Pour les annonces de 10 h où l'article
  trouve une dérive (ISM manufacturier et services, Conference Board, ventes de logements anciens ou en attente…) : à
  9 h 59, prendre position dans le sens de la variation entre 9 h 30 et 9 h 59 ; sortie à 10 h 05. Durée de sortie non
  publiée : choisir 5 minutes *a priori* et ne pas la régler.
- **Source.** Kurov, Sancetta, Strasser, Wolfe, *Price Drift before U.S. Macroeconomic News: Private Information about
  Public Announcements?*, JFQA 54(1), 2019, p. 449-479.
  https://www.skidmore.edu/economics/documents/KSSW2017-PriceDriftBeforeUSMacroeconomicNews.pdf ; ECB WP 1901.
- **Preuve.** E-mini S&P et T-note à la seconde, 2008-2014. Les prix partent dans le « bon » sens **environ 30 minutes
  avant** pour 7 annonces sur 18 (ou 9 sur 20 selon la version). La dérive représente **environ 40 %** de l'ajustement
  total. Il n'y a pas de règle de trading après frais.
- **Mécanisme.** Fuites et collecte de données propriétaires. Au Royaume-Uni, la dérive **s'affaiblit dès que l'accès
  anticipé aux chiffres est supprimé** (2017) (Kurov, Sancetta, Wolfe, *Drift Begone!*, JIMF 2022). L'effet américain a
  donc pu faiblir avec le durcissement des embargos.
- **Gain par trade.** Inconnu. Il ne reste en moyenne que 60 % de l'ajustement à capter, et seulement quand le signe de
  la dérive est juste. Ordre de grandeur plausible : 5 à 20 $ par MNQ, contre 3 $. Non démontré.
- **Déjà couvert ?** **En grande partie** : la machine a testé « minutes d'événement 10 h » × « mouvement de k minutes,
  suivre ou contrer ». Seule nouveauté : restreindre aux annonces précises de l'article et ouvrir la fenêtre à 30 minutes.

### R4. Dérive de nuit de 2 h à 3 h, conditionnée à une clôture vendeuse

- **Règle.** Achat à 2 h 00 ET, vente à 3 h 00 ET, de préférence les nuits qui suivent une fin de séance américaine en
  baisse (déséquilibre vendeur à la clôture ; dernière heure négative, à défaut des imbalances MOC qui manquent).
- **Source.** Boyarchenko, Larsen, Whelan, *The Overnight Drift*, Review of Financial Studies 36(9), 2023, p. 3502-3547.
  https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf
- **Preuve.** Futures américains 1998-2019 : environ **3,6 % par an** sur cette heure, effet asymétrique (fort après des
  ventes). **Les auteurs eux-mêmes**, dans *The Disappearing Overnight Drift* (Liberty Street Economics, 1er juillet
  2026), constatent que la fenêtre 2 h - 3 h **rapporte en moyenne presque zéro depuis 2021**.
  https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/
- **Mécanisme.** Rémunération des intermédiaires qui portent l'inventaire de clôture pendant la nuit.
- **Gain par trade.** Environ 1,4 pb par nuit avant 2021, soit ≈ 6 $ par MNQ contre 3 $ ; environ 0 depuis.
- **Déjà couvert ?** Largement (526 stratégies de sessions, dont l'ouverture de Londres, et le RSI(2) de nuit). À ne
  tester que dans sa version conditionnelle, pour confirmer. **Probablement morte.**

### R5. Cycle du fixing de change sur l'euro (hors NQ)

- **Règle.** Le dollar monte avant chaque grand fixing (Tokyo, BCE à Francfort à 14 h 15 CET, WM/Reuters à Londres à
  16 h, soit 11 h ET) et redescend après. D'où : vendre 6E ou M6E pendant les heures qui précèdent le fixing de Londres
  et le racheter après (ou acheter l'euro après le fixing).
- **Source.** Krohn, Mueller, Whelan, *Foreign Exchange Fixings and Returns around the Clock*, Journal of Finance 79(1),
  2024, p. 541-578 ; Bank of Canada SWP 2021-48.
  https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf
- **Preuve.** 9 devises du G10 sur 21 ans, présent **chaque année, chaque jour de la semaine et chaque mois**. Mais les
  auteurs écrivent que l'effet n'est exploitable que **par des investisseurs aux coûts de transaction inférieurs à la
  moyenne**. Je n'ai pas pu récupérer l'amplitude en pb.
- **Mécanisme.** Gestion d'inventaire des courtiers face à une demande structurelle de dollars aux fixings.
- **Gain par trade.** Probablement 1 à 3 pb. Sur un M6E à 1,10, 1 pb ≈ 1,4 $, **inférieur aux 3 $ de frais**. Sur un 6E
  à taille pleine, ce serait marginal.
- **Déjà couvert ?** L'euro a été traité par la machine (minutes d'événement), sans règle explicite de fixing. Ce n'est
  pas du NQ : **priorité basse**.

### Idées sans preuve, ou relevant du marketing (à ne pas tester en priorité)

- **Paires NQ/ES intraday « conditionnelles »** : aucune étude avec frais sur les futures d'indices. Les rendements
  publiés concernent des paires d'actions. Le co-mouvement NQ/ES est arbitré en millisecondes. **Pas de preuve.**
- **Niveaux de gamma, « pinning », 0DTE** :
  - Golez-Jackwerth (JFE 2012) montrent un pinning de l'ES à l'échéance des options mensuelles sur futures, mais il
    faudrait l'open interest par strike, qu'on n'a pas ;
  - en 0DTE, la recherche récente penche pour une **amplification** plutôt qu'un pinning (étude indépendante sur
    2016-2025, Dim-Eraker-Vilkov) ;
  - les « niveaux SpotGamma » relèvent du **marketing**, et le filtre GEX a déjà été testé sans effet.
- **« Niveaux de déclenchement » des CTA et flux des ETF à levier** : estimations de courtiers non publiées. Pour les ETF
  à levier, l'effet est économiquement insignifiant une fois les flux pris en compte (Ivanov-Lenkey 2018), et la fin de
  séance est déjà testée.
- **Tendance au-dessus du VWAP** (Zarattini-Aziz, *VWAP: The Holy Grail*, QQQ 2018-2023, Sharpe 2,1 « net de
  commissions » d'ETF) :
  - une réplication QuantConnect compte **environ 24 400 ordres en 5,7 ans** (≈ 17 par jour) ;
  - sur MNQ, cela ferait environ 25 $ de frais par jour et par contrat ;
  - la famille « distance au VWAP » est déjà testée et négative.
  
  **Le titre relève du marketing.**
- **Déséquilibre du carnet (OFI)** : Cont-Kukanov-Stoikov montrent que l'OFI explique les variations de prix
  *simultanées* à court horizon. C'est une relation contemporaine, pas prédictive, et elle demande le carnet complet. Le
  test sur 6 mois de flux, négatif, est cohérent avec cela.

---

## 5. Ce qui est impossible pour un particulier (et pourquoi)

| Idée | Pourquoi c'est impossible | Ordre de grandeur décisif |
|---|---|---|
| Tenue de marché sur NQ/MNQ (capter le spread) | **Frais** : spread de 0,50 $ < 2 $ de commissions par aller-retour. **Latence et file** : à 1 tick sur une file FIFO, le passif n'est rempli que quand le prix va contre lui, et les HFT agressifs gagnent justement en piégeant les passifs lents (Baron et al.) | Gain HFT : moins de 0,1 tick ES par contrat (source secondaire), soit 12 fois moins que le coût de détail |
| Arbitrage ES↔SPY, NQ↔QQQ, futures↔mégacapitalisations | **Latence** : 7 ms en 2011, 5 à 10 µs dans les courses récentes ; micro-ondes à plus de 500 M$ ; 6 firmes gagnent plus de 80 % des courses | Rithmic, 50 à 300 ms : 10⁴ fois trop lent |
| Réagir aux chiffres macro (8 h 30, 10 h, 14 h) | **Latence** : prix ajusté en 5 ms ; le flux d'ordres ne porte plus l'information | 50 000 $ par annonce sur ES, partagés entre quelques firmes |
| Prédire la minute suivante à partir du carnet ou du flux | **Données et latence** : OFI contemporain ; prédiction du meneur à 60 % mais non rentable en ordres au marché (Huth-Abergel) ; pas de carnet historique | Déjà vérifié : l'information vaut moins qu'un aller-retour |
| Arbitrage de base, calendaires, roll | Il faut le **panier d'actions et un financement au taux repo** ; écarts de quelques pb ; détention de plusieurs jours, interdite par la firme | – |
| Dispersion, prime de variance, gamma 0DTE | **Instruments** : options interdites par la firme. **Données** : pas de flux d'options intraday | – |
| Imbalances MOC (15 h 50) | **Données** : pas d'historique. **Latence** : publication consommée en millisecondes | – |
| Stat arb sur actions du Nasdaq-100 | **Échelle** : milliers de positions, frais par action institutionnels, emprunt de titres ; l'avantage par trade est d'environ 50,75 % contre 49,25 % | – |
| Fixing de change | **Frais** : selon les auteurs, réservé aux participants à coûts inférieurs à la moyenne | 1 pb sur M6E ≈ 1,4 $ < 3 $ |
| Dérives avant annonces fondées sur des fuites | **Information** : l'avantage appartient à qui a la fuite. Le suiveur arrive tard, et l'effet meurt quand on ferme les fuites (Royaume-Uni, 2017) | – |
| Momentum « CTA court terme » sur un seul marché | **Diversification** : le Sharpe des CTA court terme vient de quelque 200 marchés ; un seul marché ne porte qu'une petite part d'un avantage déjà faible | – |

---

## 6. Conclusion honnête

- Rien de ce que les HFT et les desks gagnent **en scalping** n'est accessible avec 300 ms, 3 $ et des barres d'une
  minute. La littérature (Budish, Aquilina, Chordia, Huth-Abergel) explique *pourquoi* la machine évolutive n'a rien
  trouvé : l'information de très court terme est intégrée en millisecondes.
- Les seuls avantages documentés et accessibles en latence sont des **primes de risque autour d'événements
  programmés**, tenues plusieurs heures :
  - R1 (avant NFP/ISM/PIB) et R2 (pré-FOMC) : gain par trade 10 à 50 fois les frais, mais 8 à 36 événements par an,
    usure après publication probable (prouvée pour le pré-FOMC après 2015 et pour la dérive de nuit après 2021), et
    validation statistique difficile ;
  - R3 et R4 : largement couvertes ou mortes ;
  - R5 : hors NQ et trop chère.
- **Réponse franche à « une stratégie de scalping NQ qui tienne hors échantillon » : aucune dans la littérature des
  fonds et HFT.** Les gagnants particuliers documentés gagnaient par la vitesse (avantage disparu) ou par des ordres
  passifs.
- Le seul levier réaliste à 1 minute est donc d'**exécuter les entrées du système actuel en ordres limites** au lieu
  d'ordres au marché, pour économiser jusqu'à 1 tick (0,50 $) par ordre. Il faut le tester avec les 6 mois de
  transactions à la seconde (taux de remplissage, coût des trades manqués), car les ordres passifs ne sont remplis que
  si le prix revient (sélection adverse).

---

## Sources (liens)

- Menkveld (2013), *High Frequency Trading and the New Market Makers*, JFM : https://research.vu.nl/en/publications/high-frequency-trading-and-the-new-market-makers/ ; résumé CXO : https://www.cxoadvisory.com/?p=10919
- Baron, Brogaard, Hagströmer, Kirilenko (2019), *Risk and Return in High-Frequency Trading*, JFQA : https://ideas.repec.org/a/cup/jfinqa/v54y2019i03p993-1024_00.html ; version CFTC : https://www.cftc.gov/sites/default/files/idc/groups/public/@economicanalysis/documents/file/oce_riskandreturn0414.pdf ; Baron, Brogaard, Kirilenko (2012) : https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2106158
- Budish, Cramton, Shim (2015), QJE : https://ericbudish.org/files/high_frequency_trading_arms_race.pdf ; Richmond Fed : https://www.richmondfed.org/publications/research/econ_focus/2015/q3/research_spotlight
- Aquilina, Budish, O'Neill (2022), QJE : https://ericbudish.org/wp-content/uploads/2022/02/Quantifying-the-High-Frequency-Trading-Arms-Race.pdf ; FCA OP 50 : https://www.fca.org.uk/publications/occasional-papers/occasional-paper-no-50-quantifying-high-frequency-trading-arms-race-new-methodology
- Laughlin, Aguirre, Grundfest, *Information Transmission Between Financial Markets in Chicago and New York* : https://ar5iv.arxiv.org/html/1302.5966
- Chordia, Green, Kottimukkalur (2018), RFS : https://ideas.repec.org/a/oup/rfinst/v31y2018i12p4650-4687..html
- Kurov, Sancetta, Strasser, Wolfe (2019), JFQA : https://www.skidmore.edu/economics/documents/KSSW2017-PriceDriftBeforeUSMacroeconomicNews.pdf ; *Drift Begone!* : https://pure.royalholloway.ac.uk/en/publications/drift-begone-release-policies-and-preannouncement-informed-tradin/
- Hu, Pan, Wang, Zhu (2022), JFE : https://www.nber.org/papers/w25817 ; https://econpapers.repec.org/article/eeejfinec/v_3a145_3ay_3a2022_3ai_3a3_3ap_3a909-936.htm
- Lucca, Moench (2015) : https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf ; mise à jour 2018 : https://libertystreeteconomics.newyorkfed.org/2018/11/the-pre-fomc-announcement-drift-more-recent-evidence.html ; Kurov, Wolfe, Gilbert (2021) : https://ideas.repec.org/a/eee/finlet/v40y2021ics1544612320315956.html ; BIS WP 1079 : https://www.bis.org/publ/work1079.pdf ; Ignatieva, Ohashi : https://www.tandfonline.com/doi/full/10.1080/00036846.2024.2322573
- Boyarchenko, Larsen, Whelan (2023), RFS : https://www.newyorkfed.org/research/staff_reports/sr917 ; *The Disappearing Overnight Drift* (2026) : https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/
- Krohn, Mueller, Whelan (2024), JF : https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf
- Golez, Jackwerth (2012), JFE : https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html ; test indépendant du pinning : https://harbourfrontquant.substack.com/p/from-pinning-to-amplification-evidence ; Dim, Eraker, Vilkov (résumé) : https://harbourfrontquant.substack.com/p/the-rise-of-0dte-options-cause-for
- Ivanov, Lenkey (2018) : https://pure.psu.edu/en/publications/do-leveraged-etfs-really-amplify-late-day-returns-and-volatility/ ; Lenkey (2024), revue : https://pure.psu.edu/en/publications/the-market-impact-of-leveraged-etfs-a-survey-of-the-literature/
- Hasbrouck (2003), JF : https://ideas.repec.org/a/bla/jfinan/v58y2003i6p2375-2400.html ; Huth, Abergel : https://www.arxiv.org/abs/1111.7103v1 ; Cont, Kukanov, Stoikov : https://arxiv.org/abs/1011.6402
- Zarattini, Aziz, *VWAP* : https://concretumgroup.com/volume-weighted-average-price-vwap-the-holy-grail-for-day-trading-systems/ ; Zarattini, Aziz, Barbon (2024) : https://www.sfi.ch/fr/publications/n-24-97-beat-the-market-an-effective-intraday-momentum-strategy-for-s-p500-etf-spy
- Crabel : https://www.rcmalternatives.com/?p=4510 ; QIM : https://www.institutionalinvestor.com/article/b18bkg7f726hym/qim-shuts-largest-strategies-to-new-capital-liquidates-smaller-offerings-magazine-version
- Virtu (1 jour perdant sur 1 238) : https://qz.com/186209/the-high-frequency-trading-firm-thats-about-to-go-public-only-had-one-day-of-trading-losses-in-four-years
- Mercer, « 50,75 % » (Zuckerman, *The Man Who Solved the Market*) : https://www.goodreads.com/notes/44698571-the-man-who-solved-the-market/58027759-thomas-wolf/800f9239-07c1-4032-a735-d1e2b9f74842
- McLean, Pontiff (2016), JF : https://ivey.uwo.ca/media/3775549/pontiff.pdf
- Barber, Lee, Liu, Odean (2014) : https://faculty.haas.berkeley.edu/odean/papers/day%20traders/Day%20Trading%20Skill%20110523.pdf ; *Learning, Fast or Slow* (2020) : https://ideas.repec.org/a/oup/rasset/v10y2020i1p61-93..html ; *Just How Much…* (2009) : https://faculty.haas.berkeley.edu/odean/papers%20current%20versions/justhowmuchdoindividualinvestorslose_rfs_2009.pdf ; *Do Individual Day Traders Make Money?* : http://www.econ.yale.edu/~shiller/behfin/2004-04-10/barber-lee-liu-odean.pdf
- Chague, De-Losso, Giovannetti : https://repositorio.fgv.br/items/e87d04fc-4b4c-4a56-ab5a-1c84c1afde1b/full ; https://quantpedia.com/retail-day-trading-is-an-uphill-battle/
- Kuo, Lin (2013), JBF : https://repository.hku.hk/bitstream/10722/184789/1/content.pdf ; CXO : https://www.cxoadvisory.com/individual-investing/performance-of-futures-day-traders/
- Ferko, Mixon, Onur (CFTC 2024) : https://www.cftc.gov/sites/default/files/2024-11/Retail_Traders_Futures_V2_new_ada.pdf ; CFTC MIB (2021) : https://www.cftc.gov/media/5761/GMAC_031121MIB/download
- Harris, Schultz (1998), JFE : https://ideas.repec.org/a/eee/jfinec/v50y1998i1p39-62.html ; Biais, Declerck, Moinas : https://www.bis.org/publ/work563.htm
- Statistiques des firmes de financement (secondaires) : https://www.propfirmbacktester.com/prop-firm-statistics ; https://tradecovex.com/guides/how-many-combines-passed-express-topstep-2025 ; https://bestpropfirms.us.com/prop-firm-statistics/
- Paires (absence de preuve sur futures d'indices) : https://www.iwf.rw.fau.de/files/2015/12/10-2017.pdf ; https://optimusfutures.com/blog/micro-futures-pairs-trading
