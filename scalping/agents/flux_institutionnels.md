# Flux institutionnels et mouvements intraday prévisibles sur le NQ — revue (25 oct. 2026)

Angle : couverture gamma des teneurs de marché (0DTE, épinglage, vanna/charm), rééquilibrage des ETF à levier et des
fonds à volatilité cible, MOC / clôture, fins de mois, rééquilibrages d'indices, algorithmes VWAP/TWAP et effets
d'horloge, CTA, dérive de nuit et ouverture européenne, Fed.

**Limites de cette recherche (à lire avant le reste)** : WebFetch était bloqué (DNS/proxy) et le quota de recherches web
partagé entre agents a été épuisé en cours de route. Tout vient des résumés, des pages de résumé (« abstracts ») et de
synthèses secondaires renvoyés par la recherche, pas du texte intégral des articles. Les fenêtres horaires exactes et les
coefficients que je n'ai pas pu vérifier sont marqués **[non vérifié]**.

Repère de coûts utilisé partout : avec le NQ vers 25 000 points (ordre de grandeur), 1 point de base (0,01 %) vaut
2,5 points, soit ~5 $ par MNQ. Les ~3 $ de frais d'un aller-retour valent donc ~0,6 pb. Un effet de moins de ~1 pb par
trade est perdu d'avance.

---

## 0. Le message principal : pourquoi presque rien ne tient sur le NQ

Trois résultats récents expliquent bien les échecs listés dans contexte.md.

1. **Kurth, Eisler, Rej, Bouchaud (juillet 2026), « Is Trend Still Your Friend? A Microstructural Account of the Demise
   of Short-Term Trend-Following »**, arXiv 2607.01550 (https://arxiv.org/abs/2607.01550).
   - Données : ~100 futures, 1995-2025.
   - Résultat : depuis ~2009, le suivi de tendance de court terme ne rapporte plus rien sur les contrats à **petit tick
     relatif à leur volatilité**, et ce à tous les horizons de signal.
   - Mécanisme : les teneurs de marché haute fréquence retirent leur liquidité devant un flux directionnel prévisible.
     La boucle « le flux des CTA renforce la tendance » est donc cassée.
   - Pourquoi c'est central ici : le NQ est l'archétype du contrat à petit tick (0,25 point sur ~25 000, soit ~0,1 pb).
     Cela explique de façon structurelle que la machine évolutive ne trouve rien. Tout flux institutionnel prévisible
     est déjà anticipé par les teneurs de marché haute fréquence.
2. **Les effets de flux publiés s'éteignent après publication**, preuves des auteurs eux-mêmes à l'appui :
   - dérive de nuit ≈ 0 depuis 2021 (Boyarchenko-Larsen-Whelan, 2026) ;
   - dérive avant la Fed morte après 2015 (Kurov-Wolfe-Gilbert, 2021) ;
   - effet des ETF à levier en déclin (Barbon et al., 2022) ;
   - effet de tournant de mois disparu des futures S&P après 1990 (Maberly-Waggoner) ;
   - Gao-Han-Li-Zhou en déclin après 2013.
3. **Devancer des flux prévisibles ne paie pas après frais quand ces flux sont gros et connus.** Exemple : l'étude des
   ETP VIX à levier (« The Market Impact of Predictable Flows: Evidence from Leveraged VIX Products », SSRN 2020)
   conclut que passer devant le rééquilibrage n'est pas rentable après frais.

Conséquence pratique : la littérature sur les flux donne surtout **(a)** de l'information de **régime** (gamma positif →
retour à la moyenne, gamma négatif → momentum ; prévision de la volatilité), et **(b)** quelques effets **de calendrier
rares, mais gros par trade** (Fed, fin de mois). Elle ne donne pas de signal de scalping fréquent sur le NQ.

---

## 1. Règles classées, de la plus prometteuse à la moins prometteuse

### R1 — Bascule « retour à la moyenne / momentum » d'heure en heure selon le gamma des teneurs de marché

- **Règle (comme publiée, sans réglage)**
  - Toutes les heures pleines de la séance (10 h 30, 11 h 30, 12 h 30, 13 h 30, 14 h 30, 15 h 30 si on démarre à
    9 h 30), calculer r = rendement du NQ sur les 60 dernières minutes.
  - Si le gamma des teneurs de marché est positif (proxy : GEX S&P 500 de la veille > 0) : se positionner **contre**
    r et garder 60 min (ou jusqu'à 16 h).
  - Si le GEX de la veille est < 0 : se positionner **dans le sens** de r et garder 60 min.
  - Pas de stop dans la version publiée (c'est une régression d'heure en heure).
  - Variante de robustesse non réglée : ne garder que les terciles extrêmes du GEX sur 250 jours glissants.
- **Variante fin de séance (R1b)**
  - À 15 h 30, prendre r = rendement de la clôture de la veille à 15 h 30 (définition de Baltussen et al.).
  - Si GEX > 0 : se positionner **contre** r jusqu'à 16 h.
  - Le cas GEX < 0 (suivre r) revient à Baltussen et al., déjà testé et négatif. Seul le côté « contre » est nouveau.
- **Sources**
  - Dim, Eraker, Vilkov (2023-2024), « 0DTEs: Trading, Gamma Risk and Volatility Propagation »,
    https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4692190 :
    - le gamma net des teneurs de marché est **positif en moyenne** ;
    - un gamma positif renforce le **retour à la moyenne** intraday, un gamma négatif renforce le **momentum** ;
    - les 0DTE n'amplifient pas la volatilité.
  - Adams, Dim, Eraker, Fontaine, Ornthanalai, Vilkov (2025-2026), « Do S&P 500 Options Increase Market Volatility?
    Evidence from 0DTEs », https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5641974 (version PDF :
    https://www.jean-sebastienfontaine.com/papers/0dte-options-volatility.pdf) :
    - le gamma net prédit la volatilité réalisée intraday du S&P 500 ;
    - il prédit aussi **des retours de flux d'ordres plus forts sur le E-mini** ;
    - le momentum d'une heure à l'autre est positif quand les besoins de couverture sont faibles, et s'inverse quand ils
      sont élevés.
  - Barbon & Buraschi, « Gamma Fragility » (https://abarbon.com/papers/gamma-fragility) et Barbon, Beckmeyer, Buraschi,
    Moerke (SFI 22-40, https://papers.ssrn.com/abstract=3925725) : gamma très négatif (positif) → momentum (retour) en
    fin de séance ; l'effet gamma **persiste** sur l'échantillon, l'effet des ETF à levier décline.
- **Preuve**
  - Indice S&P 500 / E-mini, échantillons d'environ 2016 à 2023-2024 [non vérifié].
  - Gamma mesuré sur les **positions réelles des teneurs de marché** (données Cboe Open-Close), pas sur un proxy.
  - Pas de test après frais ni hors échantillon de trading publié : ce sont des régressions.
  - Reproduit par plusieurs équipes (Dim et al. ; Adams et al. ; Barbon et al. ; Baltussen et al. pour le côté
    momentum).
- **Mécanisme** : un teneur de marché long gamma vend la hausse et achète la baisse pour rester neutre en delta, ce qui
  dessine un retour à la moyenne. Celui qui paie, c'est le trader directionnel qui a poussé le prix. Attention : on se
  met du même côté que les teneurs de marché, donc en concurrence avec eux. L'avantage attendu est faible.
- **Gain par trade [estimation, non publiée]**
  - L'écart-type horaire du NQ est d'environ 0,25-0,35 %. Un coefficient de retour de −0,05 à −0,1 donnerait ~1,5 à
    3 pb par trade, soit **~7 à 15 $ par MNQ brut** contre 3 $ de frais.
  - C'est juste au-dessus des frais, à condition que le proxy GEX capte bien le vrai gamma.
- **Données**
  - Testable tout de suite : barres 1 min du NQ + GEX S&P 500 de la veille.
  - Donnée manquante pour la version fidèle : Cboe Open-Close Volume Summary (SPX/XSP/NDX, ventilation teneur de
    marché / client, payant sur Cboe DataShop). Le GEX de SqueezeMetrics suppose que les clients vendent les calls et
    achètent les puts ; ce n'est pas validé contre les vraies positions (https://slopeofhope.com/wp-content/uploads/2020/11/GEX-white_paper.pdf).
  - C'est le gamma du **S&P 500**, pas du NDX.
- **Déjà couvert ?** Partiellement.
  - Le GEX a été testé comme **filtre de la zone** (une stratégie de momentum) : rien.
  - Le mouvement de k minutes (suivre / contrer) a été testé avec des filtres de **volatilité et de tendance**, pas de
    gamma.
  - La bascule « contrer si gamma positif, suivre si gamma négatif » à l'horizon de l'heure **n'est pas dans la liste**.
- **Verdict** : la meilleure piste « flux » pour du trading intraday fréquent sur l'indice. C'est la seule qui ait de la
  littérature récente (2023-2026) sur le E-mini lui-même. Probabilité modérée-faible de passer les frais avec un proxy
  GEX.

### R2 — Jours de Fed : le mouvement de l'énoncé de 14 h annonce celui de la conférence de presse

- **Règle**
  - Uniquement les jours de réunion du FOMC avec conférence de presse (toutes les réunions depuis 2019, une sur deux
    de 2011 à 2018).
  - Fenêtre de l'énoncé : r_E = rendement du NQ de 13 h 55 à 14 h 25.
  - À 14 h 30 (début de la conférence) : prendre position **dans le sens** de r_E, sortie à 15 h 30 (fin de
    conférence).
  - Les fenêtres exactes de l'article ne sont pas vérifiées [non vérifié] : les caler sur le texte avant de tester.
  - Attention aux horaires de 2011-2012 : énoncé à 12 h 30, conférence à 14 h 15 [de mémoire, à vérifier].
- **Source** : Gómez-Cram & Grotteria (2022), « Real-time Price Discovery via Verbal Communication: Method and
  Application to Fedspeak », Journal of Financial Economics 143(3),
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3613702. Les mouvements autour de l'énoncé prédisent ceux de la
  conférence : **corrélation de 44 % pour le S&P 500** (58 % pour les Eurodollars à moyen terme).
- **Preuve**
  - Dans l'échantillon (conférences depuis 2011 ; fin d'échantillon vers 2019-2020 [non vérifié]).
  - Pas de test hors échantillon ni après frais connu.
  - Peu d'événements : environ 90 à 100 de 2011 à 2026, dont environ 55 après 2019.
- **Mécanisme** : traitement lent de l'information. Le marché attend que le président clarifie les changements de
  l'énoncé, et la volatilité et le volume explosent quand il en parle. Ce n'est pas un flux institutionnel au sens
  strict. Celui qui paie, c'est le trader qui sur-réagit ou sous-réagit pendant la conférence.
- **Gain par trade** : la fenêtre de conférence a un écart-type de ~0,4 à 0,6 % sur le NQ. Avec ρ ≈ 0,44, l'espérance
  vaut ~0,44 × σ × 0,8 ≈ 15 à 20 pb, soit **~75 à 100 $ par MNQ brut**. Les frais sont négligeables ; le problème est
  le très petit nombre d'événements et la forte variance.
- **Déjà couvert ?** Partiellement.
  - Les minutes d'événement (14 h) ont été testées en mouvements de 1 à 30 min.
  - La logique « fenêtre de l'énoncé → fenêtre de la conférence » (horizon de 60 min, seulement les jours de
    conférence) ne l'est probablement pas.
  - Ces jours sont **libres** pour l'utilisateur, puisque la zone est coupée les jours de Fed.
- **Verdict** : facile à tester (barres 1 min + calendrier du FOMC). L'avantage est gros par trade mais statistiquement
  fragile. Juger sur 2019-2026 (après publication).

### R3 — Fin de mois : rééquilibrage des fonds de pension 60/40

- **Règle (signal « calendrier », N = 5 comme publié)**
  - Pendant chacun des 5 derniers jours ouvrés du mois, calculer le poids actions d'un portefeuille 60/40 rééquilibré à
    la fin du mois précédent : w = 0,6(1+R_act) / [0,6(1+R_act) + 0,4(1+R_obl)].
    - R_act = rendement depuis le début du mois de l'ES/SPX (ou du NQ).
    - R_obl = rendement depuis le début du mois du ZN ou du TLT.
  - Si w > 0,60 : **vendre** le NQ pour la journée suivante. Si w < 0,60 : **acheter**.
  - Version compatible avec la règle de la firme : de 18 h (réouverture Globex) à 16 h 59 le lendemain, ce qui capte
    l'essentiel du rendement de clôture à clôture. Sinon : séance seule de 9 h 30 à 16 h.
  - Signal « seuil » (plus lourd) : simuler un 60/40 rééquilibré dès que |w − 0,6| > δ, faire la moyenne sur
    δ = 0 à 2,5 % par pas de 0,1 %, et trader le signe le lendemain.
- **Source** : Harvey, Mazzoleni, Melone, « The Unintended Consequences of Rebalancing », NBER w33554 (mars 2025,
  révisé janv. 2026), https://www.nber.org/papers/w33554. Quand les actions sont en surpoids, le rendement des actions
  du lendemain baisse de **~16-17 pb** et celui des obligations monte de 2-4 pb. L'effet se résorbe en deux semaines. Il
  est significatif sur les ~30 dernières années, nul avant. Coût estimé pour les investisseurs : ~16 Md$ par an.
- **Preuve** : quotidienne, avant frais, en échantillon.
  - Reproductions contradictoires :
    - QuantReturns, positif jusqu'en 2023 (https://quantreturns.com/strategy-review/front-running-the-rebalancers/) ;
    - Paperswithbacktest, **Sharpe −0,20 sur 1990-2026** (https://paperswithbacktest.com/strategies/the-unintended-consequences-of-rebalancing).
  - Discussion critique de Kent Daniel : https://kentdaniel.net/discuss/2025/HMM.pdf.
  - Après publication (2025-2026) : rien de connu.
- **Mécanisme** : les fonds de pension, les fonds à date cible et les fonds souverains (~20 000 Md$) ont des politiques de
  rééquilibrage rigides et publiques. Ils exécutent souvent à la clôture (MOC) et paient la pression de prix.
- **Gain par trade** : 16-17 pb ≈ **80 $ par MNQ brut** (ES ; un peu plus sur le NQ). Mais l'écart-type journalier est
  de ~130 pb : le ratio signal / bruit est d'environ 0,13 par trade. Il faut des centaines de trades (~60 par an).
- **Déjà couvert ?** Probablement pas sous cette forme : le signal croise actions et obligations, conditionné par le
  calendrier. Ce n'est **pas** du scalping.
- **Verdict** : bon mécanisme, documenté par un auteur sérieux (Harvey), mais quotidien, bruité, et avec une reproduction
  négative. À tester en complément de portefeuille, pas comme stratégie de scalping.

### R4 — Retour après la clôture de la pression du « closing cross »

- **Règle (adaptation, paramètres à moi, non publiés)**
  - À 16 h 00, mesurer r = rendement du NQ de 15 h 50 à 16 h 00. 15 h 50 est l'heure de publication des déséquilibres
    du Nasdaq (NOII) et du NYSE.
  - Si |r| est dans les 20 % les plus forts des 250 derniers jours : se positionner **contre** r à 16 h 01, sortie à
    16 h 15 ou à 16 h 59.
- **Source** : Bogousslavsky & Muravyev, « Who Trades at the Close? » (JFM ; ancien titre « Should We Use Closing
  Prices? Institutional Price Pressure at the Close »), https://aeaweb.org/conference/2021/preliminary/paper/H9T4hef7.
  - L'écart entre le prix de clôture et le milieu de fourchette se résorbe **à moitié juste après la clôture**, et
    totalement pendant la nuit.
  - Le volume de clôture vient des fonds indiciels et des ETF (7,5 % du volume en 2018).
- **Preuve** : **au niveau des actions individuelles**. Pas de preuve trouvée au niveau de l'indice ou du future.
- **Mécanisme** : les fonds indiciels et les ETF demandent de la liquidité à la clôture et paient une concession de
  prix temporaire.
- **Gain par trade** : inconnu. Le mouvement typique de 15 h 50 à 16 h 00 sur le NQ fait ~0,1-0,15 % (25-35 points). Si
  une fraction se résorbe, ~2-5 points, soit 4-10 $ par MNQ, contre 3 $ de frais **plus** une fourchette plus large
  après 16 h.
- **Données** : les barres 1 min s'arrêtent à 16 h. Il faut les barres 5 min de CFD (HistData) pour 16 h-17 h. Données
  manquantes pour la version fidèle : historique des déséquilibres MOC/NOII.
- **Déjà couvert ?** Non : Baltussen (dernière demi-heure, suivre) a été testé, pas le retour après 16 h.
- **Verdict** : faible a priori, puisque l'effet est prouvé sur les actions et non sur l'indice. Test bon marché.

### R5 — Dérive de nuit autour de l'ouverture européenne, conditionnée à une clôture vendeuse

- **Règle (comme publiée)**
  - Acheter le NQ à 2 h 00 ET, revendre à 3 h 00 ET.
  - Version conditionnelle : seulement après une séance US dont la dernière heure (15 h-16 h) est vendeuse.
    - Mesure publiée : volume signé relatif sur la dernière heure.
    - Proxy possible : rendement de 15 h à 16 h dans le tercile le plus bas, ou classification du volume par barres.
  - Variante Bondarenko-Muravyev : être long de 23 h 30 à 3 h 30 ET.
- **Sources**
  - Boyarchenko, Larsen, Whelan, « The Overnight Drift », Review of Financial Studies 36(9), 2023
    (https://ideas.repec.org/a/oup/rfinst/v36y2023i9p3502-3547..html ; NY Fed SR 917) : ~3,6-3,7 % par an gagnés entre
    2 h et 3 h ET (1998-2019). Retour fort après les ventes massives, faible après les hausses.
  - **Les mêmes auteurs, « The Disappearing Overnight Drift », Liberty Street Economics, 1er juillet 2026**
    (https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/ ; SSRN 7035838) :
    - la fenêtre de 2 h à 3 h rapporte **≈ 0 depuis 2021** ;
    - cause : la dispersion des déséquilibres de clôture s'est comprimée (les algorithmes découpent les ordres plus
      finement) ;
    - l'effet devrait revenir si cette dispersion s'élargit.
  - Bondarenko & Muravyev, « Market Return Around the Clock: A Puzzle », JFQA 2023
    (https://ideas.repec.org/a/cup/jfinqa/v58y2023i3p939-967_1.html) : la fenêtre de 23 h 30 à 3 h 30 ET capte toute la
    prime actions sur l'ES de 2004 à 2018 (Sharpe ~1,6, positive chaque année).
- **Preuve** : solide avant 2020, **éteinte après publication** selon les auteurs eux-mêmes. Une note Cboe indique
  qu'avec la fourchette acheteur-vendeur, la version horaire devient négative.
- **Gain par trade** : ~1,4 pb par nuit avant 2021 (≈ 7 $ par MNQ brut), ≈ 0 depuis. Il faut retirer 3 $ de frais plus
  une fourchette de nuit plus large.
- **Déjà couvert ?** Largement.
  - Les 526 stratégies de sessions (Asie / Londres / New York) couvrent la version non conditionnelle.
  - Le RSI(2) de nuit adopté (acheter la nuit après une baisse) capte déjà la version « après vente massive ».
- **Verdict** : ne pas reproposer comme stratégie. À la rigueur, un **contrôle** : séparer 2012-2020 et 2021-2026 sur
  les barres 5 min de CFD pour vérifier que l'extinction se voit aussi sur le NQ.

---

## 2. Pistes à écarter (pas de preuve, éteintes, ou intestables avec nos données)

| Piste | Ce que dit la littérature | Verdict |
|---|---|---|
| Rééquilibrage des ETF à levier (TQQQ/SQQQ) en fin de séance | Shum et al. (Rev. Finance 2016, https://ideas.repec.org/a/oup/revfin/v20y2016i6p2379-2409..html) : lien avec la volatilité de la dernière heure en 2006-2011. Ivanov & Lenkey (JFM 2018, https://pure.psu.edu/en/publications/do-leveraged-etfs-really-amplify-late-day-returns-and-volatility/) : une fois les flux de souscription pris en compte, l'effet sur les rendements de fin de séance est **économiquement négligeable**. Revue de Lenkey 2024 (https://www.aimspress.com/article/doi/10.3934/QFE.2024031) : erreurs de méthode fréquentes. Barbon et al. 2022 : effet en **déclin**, retour dès l'ouverture suivante. Tuzun (Fed 2013, https://www.federalreserve.gov/pubs/feds/2013/201348/201348pap.pdf) : ~1 Md$ par mouvement de 1 %, petit face au volume du NQ, de l'ES et du QQQ. | Déjà testé via Baltussen ; mort ou négligeable. |
| Fonds à volatilité cible / risk parity | Aucune étude empirique trouvée qui isole leur impact intraday. Seulement des notes de banques (flux estimés par modèles propriétaires). | Pas de preuve ; intestable. |
| CTA : « niveaux de déclenchement » et flux | Kurth et al. 2026 : le court terme est mort sur les contrats à petit tick. Les niveaux des banques et des vendeurs de données ne sont pas vérifiables. | Marketing / sans preuve. |
| Épinglage sur les prix d'exercice, 0DTE | Golez & Jackwerth (JFE 2012, https://ideas.repec.org/a/eee/jfinec/v106y2012i3p566-585.html) : épinglage de l'ES à l'échéance des options sur futures, mais seulement ~115 M$ de notionnel déplacé par échéance. Pour les 0DTE : une étude SPY 2016-2025 relayée sur Substack ne trouve **aucun** épinglage (5 tests, 2 294 jours) (https://harbourfrontquant.substack.com/p/from-pinning-to-amplification-evidence ; source faible). Sans intérêt ouvert, on retombe sur les niveaux ronds (Osler), déjà testés. | Écarter. |
| Semaine d'expiration (OPEX), « vanna/charm » | Stivers & Sun (JBF 2013, https://ideas.repec.org/a/eee/jbfina/v37y2013i11p4226-4240.html) : actions du S&P 100, indice en 1983-2008. Schaeffer's : semaines de « triple witching » légèrement négatives depuis 2017. Vanna/charm : **aucune étude académique**, uniquement des scripts TradingView et des vendeurs de données (SpotGamma...). | Marketing / sans preuve récente. |
| Collier trimestriel de JPMorgan (JHEQX) | Aucun travail académique ; la presse (Reuters) rapporte des avis contradictoires. | Sans preuve. |
| Dérive avant la Fed (Lucca-Moench) | Disparue après 2015 (Kurov, Wolfe, Gilbert, FRL 2021, https://www.skidmore.edu/economics/documents/KurovWolfeGilbert-TheDisappearingPre-FOMC-Announce-Drift-200914.pdf). | Morte (et les jours de Fed sont déjà exclus). |
| Tournant de mois / « Dash for cash » | Etula et al. (RFS 2020, https://academic.oup.com/rfs/article/33/1/75/5494694) : effet quotidien autour des paiements de fin de mois. Maberly & Waggoner (Fed d'Atlanta 2000, https://www.atlantafed.org/research/publications/wp/2000/11.aspx) : disparu des futures S&P après 1990 ; à l'ère des ETF, concentré sur le 1er jour. | Quotidien, douteux, sans doute couvert par les 232 736 stratégies journalières. |
| Effets d'horloge (:00 / :30), VWAP/TWAP | Broussard & Nikiforov : volume +20 % aux heures rondes, **sans** effet de coût ni de prix (https://rpc.cfainstitute.org/research/cfa-digest/2014/07/intraday-periodicity-in-algorithmic-trading-digest-summary). Choi-Larsen-Seppi (2021, https://arxiv.org/pdf/1803.08336) : modèle théorique de pression VWAP/TWAP, sans test empirique. Sur l'ES, rendement nul en moyenne aux minutes de 8 h 30 et 10 h (annexe JFQA). | Pas de preuve de prix ; déjà couvert (Heston-Korajczyk-Sadka, minutes d'événement). |
| Déséquilibres MOC (NOII) | Seulement des études par action (mémoire d'Imperial College, résultats mitigés). Pas d'historique des déséquilibres dans nos données. | Intestable (donnée manquante). |
| Reconstitution du Nasdaq 100 (décembre), rééquilibrages trimestriels | Les achats des entrées et les ventes des sorties se compensent au niveau de l'indice : pas de flux directionnel net sur le NQ. | Non pertinent pour le future. |
| Retour en fin de séance dans le cross-section (Baltussen-Da-Soebhag 2025, https://www3.nd.edu/~zda/EOD.pdf) | Effet sur les actions perdantes contre gagnantes, pas sur l'indice. | Non transposable au NQ. |
| Règlement du VIX (Griffin & Shams, RFS 2018) | Pression sur les options SPX hors de la monnaie pendant l'enchère de 8 h 15 ; rien d'exploitable sur le NQ. | Écarter. |
| Momentum de fin de séance par la couverture gamma (Baltussen-Da-Lammers-Martens 2021) | Déjà testé : négatif. Gao et al. en déclin après 2013. | Couvert. |

---

## 3. Classement honnête et ordre de test conseillé

1. **R1 (gamma → retour ou momentum d'heure en heure, et R1b à 15 h 30)** : seule piste intraday fréquente adossée à
   une littérature récente sur l'indice lui-même. Faisable immédiatement (barres 1 min du NQ + GEX de la veille).
   Échantillon d'apprentissage 2012-2020, hors échantillon 2021-2026. Chance modérée-faible : le proxy GEX est
   imparfait et le gain estimé est proche des frais.
2. **R2 (énoncé de la Fed → conférence de presse)** : gros gain par trade, frais négligeables, trades les jours où la
   zone est coupée. Mais seulement ~8 trades par an, d'où une fragilité statistique. Juger uniquement sur 2019-2026.
3. **R3 (60/40 en fin de mois, Harvey et al.)** : mécanisme réel et documenté, mais quotidien, bruité, avec une
   reproduction indépendante négative. Ce n'est pas du scalping.
4. **R4 (retour après 16 h de la pression du closing cross)** : extrapolé depuis les actions ; test bon marché sur les
   barres 5 min de CFD.
5. **R5 (dérive de nuit de 2 h à 3 h)** : éteinte depuis 2021 de l'aveu même des auteurs, et déjà captée par les
   sessions et le RSI(2) de nuit. À tester seulement comme contrôle.

Conclusion : aucune piste « flux institutionnels » n'offre un avantage de scalping crédible et fréquent sur le NQ après
~3 $ de frais. Le résultat de Kurth-Eisler-Rej-Bouchaud (2026) donne une explication structurelle cohérente avec les
600 000 stratégies négatives : sur un contrat à petit tick, les teneurs de marché haute fréquence neutralisent les flux
directionnels prévisibles. L'usage le plus réaliste de cette littérature est de **choisir le régime** (gamma positif →
ne pas jouer le momentum, ou jouer le retour) et de **jouer les rares fenêtres de calendrier où l'information arrive
lentement** (conférence de presse de la Fed), pas de scalper des flux.
