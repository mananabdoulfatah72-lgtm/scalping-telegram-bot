# Tokyo garde la dernière piste ouverte

Presque toutes les anomalies documentées entre 18 h et 3 h (heure de New York) sont fermées pour un compte Bulenox de 50 000 $. La dérive de nuit du S&P 500 est nulle sur 2021-2025 selon ses propres auteurs de la Fed de New York. Le fixing de Tokyo et le gotobi rapportent moins qu'un aller-retour sur 6J. Les achats d'ETF de la Banque du Japon ont cessé le 19 mars 2024, et le momentum intraday chinois se joue sur des contrats absents de la CME. La hausse de l'or aux heures asiatiques n'est documentée que pour le régime 2024-2026, par des sources non revues, et le projet l'a déjà rejetée sur de vrais prix MGC. **La seule famille qui garde un appui académique récent et que le projet n'a jamais testée est le momentum, ou le retournement, du Nikkei pendant la séance de Tokyo.** Quatre résultats la soutiennent :

- dans plus de 60 contrats à terme, de 1974 à 2020, le rendement de la journée prédit la dernière demi-heure ;
- en Asie, cet effet est « surtout visible en Chine et au Japon », et pendant le COVID il n'a tenu qu'au Japon ;
- la Banque du Japon a décrit dès 2016 le flux qui le nourrit : les fonds à levier rachètent des futures Nikkei après une hausse, juste après la clôture du comptant ;
- une étude de 2026 trouve que les futures du Nikkei se retournent dans leurs 30 premières minutes après une forte séance du S&P 500, puis repartent vers la clôture.

Aucune de ces études ne publie de résultat après frais sur les futures du Nikkei. Un aller-retour sur le Micro Nikkei (MNK) coûte environ 2,2 à 2,8 points de base (pb) aux niveaux de 2025-2026. La liste des contrats Bulenox trouvée dans les sources ne cite pas le Nikkei : il faut le vérifier avant tout calcul. Les données HistData du projet couvrent la séance de Tokyo presque chaque jour depuis 2012, ce qui rend testables trois règles fixées d'avance : la fin de séance d'Osaka dans le sens de la journée, l'ouverture de Tokyo contre la séance américaine, et la zone de bruit du bot transposée à la séance de Tokyo. Toutes les sources ont été lues à travers leurs résumés et extraits, jamais par leurs tableaux complets : plusieurs tailles d'effet décisives restent inconnues.

## Sur douze pistes, deux restent ouvertes, toutes deux au Japon

Le tableau ci-dessous donne, pour chaque piste :
- le mécanisme et le contrat de la CME qui la rend jouable ;
- le résultat publié, avant puis après frais ;
- la période étudiée et ce qu'on sait de l'effet après 2020 ;
- le niveau de preuve ;
- son statut dans le projet.

Les niveaux de preuve sont les suivants :
- **A** : grande revue (Journal of Finance, JFE, RFS, JFQA) et long échantillon ;
- **B** : revue de spécialité, banque centrale ou NBER ;
- **C** : article récent à l'échantillon inconnu, ou prépublication ;
- **D** : praticien, presse ou données d'industrie.

Les heures sont celles de New York : EST désigne l'heure d'hiver (novembre à mi-mars), EDT l'heure d'été. Le Japon, la Chine et Hong Kong ne changent pas d'heure, si bien qu'un événement asiatique tombe une heure plus tôt à New York en hiver.

| Piste (source principale) | Mécanisme | Contrat CME | Résultat publié : avant → après frais | Période ; après 2020 | Preuve | Dans le projet |
|---|---|---|---|---|---|---|
| Dérive de 2 h - 3 h ([Boyarchenko, Larsen, Whelan, RFS 2023](https://academic.oup.com/rfs/article-abstract/36/9/3502/7076616)) | stock des teneurs de marché après les ventes de clôture | MES, MNQ | 3,6-3,7 %/an, Sharpe 1,1 → « pas rentable » ; fenêtre 1 h 30 - 3 h 30 : Sharpe 1,3 → 0,3 | 1998-2020 ; **nulle en 2021-2025** | A | rejetée, avec ou sans baisse de la veille |
| Quatre heures autour de l'ouverture européenne ([Bondarenko, Muravyev, JFQA 2023](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3)) | incertitude de la nuit résolue par l'Europe | MES, MNQ | Sharpe 1,6 → « reste élevé » (1,2 dans la version de 2020) | 2004-2018 ; aucun test publié, heure centrale nulle en 2021-2025 | A | dérive 18 h - 9 h 30 rejetée ; 23 h 30 - 2 h jamais isolée |
| Fixing de Tokyo (9 h 55) et gotobi ([Krohn, Mueller, Whelan, JF 2024](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306)) | demande de dollars au fixing, stocks des banques | 6J, MJY, M6A | ≈ 2,5 pb (portefeuille du dollar) → Sharpe négatif à l'écart complet ; gotobi ≈ +4,5 pips bruts | 1999-2019 ; praticiens contradictoires | A (flux), D (trade) | rejeté : effet 2 à 3 fois plus petit que les frais ; gotobi échoue au coffre |
| Devise locale faible pendant ses heures ([Breedon, Ranaldo, JMCB 2013](https://onlinelibrary.wiley.com/doi/abs/10.1111/jmcb.12032)) | achats de devises étrangères par les résidents | 6J, M6A | significatif brut ; AUD : 50 % de hausses → aucun résultat net vu | 1993-2011 ; rien de récent | B | même flux que le fixing |
| Achats d'ETF de la BOJ après une matinée faible ([Fukui, Yagasaki, ESRI 2023](https://www.esri.cao.go.jp/en/esri/content/e_dis376.pdf)) | ordres de la BOJ pendant la pause de midi | futures Nikkei | rendements de midi positifs → déjà anticipés | 2010-2024 ; **morte le 19 mars 2024** | B | sans objet |
| Or acheté en Asie ([Wei, SSRN 2026](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7257240)) | demande chinoise et des banques centrales | MGC | Asie = 77,2 % de la hausse depuis juillet 2024 → aucun résultat net | 2024-2026 ; irrégulier en 2026 | C/D | rejeté ; l'or acheté à 18 h était un artefact de cotation |
| Momentum intraday chinois ([Jin et al., JFM 2020](https://onlinelibrary.wiley.com/doi/10.1002/fut.22084)) | traders informés tardifs, bruit | aucun (SHFE, CFFEX) | significatif brut → aucun résultat net | ≈ 2010-2018 ; retournements en 2017-2022 | B | injouable à la CME |
| Ouverture de Hong Kong et de Shanghai (9 h 30) | information américaine absorbée en Chine | MES, MNQ, MGC, M6A | aucune mesure publiée | — | aucune | cassure rejetée |
| Statistiques chinoises de 9 h 30 ([Baum, Kurov, Wolfe, JIMF 2015](https://ideas.repec.org/a/eee/jimfin/v59y2015icp100-122.html)) | surprises sur la croissance chinoise | M6A, HG, MCL, MES | réaction au chiffre, sens inconnu sans le consensus | 2009-2013 ; pas d'étude intraday récente | B | non testé |
| Pétrole la nuit ([Ji, Zhang, Zhao 2021](https://link.springer.com/article/10.1007/s10479-021-04097-x)) | aucun ; le brut de Shanghai est « régional » le jour | MCL | aucune dérive documentée | — | aucune | sessions rejetées |
| **Momentum de fin de séance au Japon** ([Baltussen et al., JFE 2021](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403) ; [BOJ 2016](https://www.boj.or.jp/en/research/wps_rev/rev_2016/data/rev16e01.pdf)) | couverture gamma, rééquilibrage des fonds à levier | MNK | prévisibilité brute → aucun résultat net au Japon | 1974-2020 ; a tenu au Japon pendant le COVID | A (monde), B (Japon) | **jamais testé** |
| **Retournement de l'ouverture de Tokyo** ([Finance Research Open 2026](https://www.sciencedirect.com/science/article/pii/S3050700626000204)) | sur-réaction après le S&P 500, puis arbitrage | MNK | sens documenté, taille inconnue | période inconnue ; publié en 2026 | C | **jamais testé** |

Deux constats ressortent du tableau. **Les pistes mortes ou trop petites sont celles qui touchent les actifs américains** (S&P 500, or, dollar). Leurs mouvements de nuit viennent soit d'un flux né dans un autre fuseau, soit d'un stock que les teneurs de marché doivent écouler. Ces flux ont disparu, comme les déséquilibres de clôture comprimés ou la BOJ arrêtée, ou se sont révélés des artefacts de cotation. **Les deux pistes encore ouvertes portent sur le Nikkei**, dont la séance « maison » tombe entièrement dans la fenêtre : 9 h à Tokyo correspond à 19 h EST (20 h EDT), et la clôture de 15 h 30 à 1 h 30 EST (2 h 30 EDT).

### Ce que coûte un aller-retour la nuit

La nuit, les frais décident de presque tout, mais la liquidité moyenne n'est pas en cause. Selon les statistiques de la CME, l'écart moyen entre prix acheteur et prix vendeur pendant les heures asiatiques est le même que sur la journée entière :
- micro-or : 1,98 tick contre 2,01 ([CME OpenMarkets 2025](https://cmegroup.com/openmarkets/metals/2025/Asias-Growing-Gold-Demand-Fuels-Surging-Derivatives-Market.html)) ;
- WTI : 1,34 tick contre 1,35 ([CME 2023](https://www.cmegroup.com/articles/whitepapers/leveraging-cme-group-asia-trading-hours-liquidity-for-cross-commodity-trading.html)) ;
- yen : 1,08 pip contre 1,09 ; dollar australien : 0,66 pip contre 0,65 ([CME 2023](https://www.cmegroup.com/articles/2023/unlocking-potential-during-asian-trading-hours-with-cme-fx-futures.html)).

Ces moyennes couvrent la journée de Singapour, plus large que la fenêtre, et ne disent rien des premières minutes après 18 h ni de la profondeur du MNK pendant Tokyo. **L'obstacle est la taille du tick des micros.** Le tableau ci-dessous applique la convention du projet (un tick de glissement par ordre). Les contrats viennent des fiches de la CME ([micros](https://www.cmegroup.com/markets/microsuite/fx.html), [MNK](https://www.cmegroup.com/markets/equities/international-indices/micro-nikkei-usd.contractSpecs.html), [6J](https://www.cmegroup.com/markets/fx/fx-product-guide.html)), les commissions tout compris du [barème Bulenox d'août 2026](https://bulenox.com/legal/Bulenox-Rates.pdf).

| Contrat | Taille et tick | Aller-retour : 2 ticks + commission | En points de base |
|---|---|---|---|
| MNK | 0,50 $ × indice ; 5 points = 2,50 $ | 5 $ + 2 $ supposés (absent du barème) = 7 $, soit 14 points d'indice | ≈ 2,2 à 63 000 ; ≈ 15 au niveau de 2012 |
| MNQ | — | 1,5 point (convention du projet) | ≈ 2,6 en moyenne sur 2012-2022 (`asie/README.md`) ; moins de 1 en 2026 |
| MGC | 10 onces ; 0,10 $ = 1 $ | 2 $ + 1,52 $ = 3,52 $ | ≈ 0,9 à 4 000 $ |
| 6J | 12,5 M¥ ; 6,25 $ | 12,50 $ + 4,72 $ ≈ 17 $ | ≈ 2,1, soit ≈ 3 pips à 150 ¥ |
| M6A | 10 000 AUD ; 1 $ | 2 $ + 1,00 $ = 3 $ | ≈ 4,6 à 0,65 |
| MCL | 100 barils ; 1 $ | 2 $ + 1,52 $ = 3,52 $ | ≈ 5 à 65 $ |

Le micro-or est de loin le moins cher. Le micro dollar australien et le micro pétrole coûtent 4 à 6 pb, ce qui élimine tout effet de quelques points de base. Pour le MNK, le coût en points de base dépend du niveau du Nikkei. Dans les fichiers HistData du projet, l'indice est passé d'environ 8 500 points en 2012 à plus de 60 000 en 2026, avec un maximum vers 73 500. Les mêmes 14 points d'indice valent donc environ 15 pb en 2012 et 2,2 pb en octobre 2026.

## La dérive de nuit américaine est morte deux fois

Boyarchenko, Larsen et Whelan ont montré qu'entre 1998 et 2019, le contrat E-mini S&P 500 gagnait l'essentiel de sa hausse en une seule heure. **De 2 h à 3 h (New York), à l'ouverture des marchés européens, il rapportait 3,6 % par an** ([Liberty Street Economics, 2021](https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns)). Leur mise à jour de 2026 donne 3,7 % par an sur 1998-2020, soit plus de 60 % des 5,9 % annuels du contrat, environ 1,5 pb par jour ([Liberty Street Economics, juillet 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)).

Le mécanisme est un stock à écouler. Après des ventes en fin de séance et des déséquilibres d'ordres négatifs à la clôture, les teneurs de marché portent un risque d'inventaire, qu'ils soldent quand l'Europe ouvre. Les ventes produisent des « rebonds de nuit robustes ». En revanche, les grands déséquilibres positifs ne sont suivis que de rendements plats ou négatifs : il n'y a pas de vente symétrique à jouer ([RFS 2023](https://academic.oup.com/rfs/article-abstract/36/9/3502/7076616)).

Même dans l'échantillon, la stratégie n'a jamais payé ses frais. Elle affichait un Sharpe de 1,1 avant frais, mais les auteurs écrivent qu'« avec les frais, la dérive n'est pas rentable en pratique ». Élargie à 1 h 30 - 3 h 30, elle donne un Sharpe de 1,3 avant frais et **0,3 après** ([version acceptée de l'article](https://research-api.cbs.dk/ws/portalfiles/portal/101311522/nina_boyarchenko_et_al_the_overnight_drift_acceptedversion.pdf)).

Puis le gain brut lui-même a disparu. Selon ses auteurs, l'heure de 2 h à 3 h « a fait en moyenne presque zéro depuis 2021 ». Un extrait indique le même constat sur les E-mini Nasdaq-100 et Dow, mais la phrase n'a pas pu être retrouvée une seconde fois. Ils attribuent la disparition à la compression des déséquilibres :
- **l'écart-type des déséquilibres de fin de séance est passé de 6,5 % à 2,9 %** ;
- les journées de déséquilibre extrême sont devenues rares ;
- la volatilité et la liquidité, elles, n'ont guère changé ;
- les fonds NightShares, lancés en 2022 pour capter la nuit, ont fermé environ quatorze mois plus tard.

Sources : [Liberty Street Economics, juillet 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/) ; [Fed in Print](https://fedinprint.org/item/fednls/103479). Les auteurs prédisent un retour de la dérive dans la même heure si cette dispersion retrouve son niveau d'avant 2020.

Les frais, eux, ne sont plus l'obstacle. Vers 1 000 à 2 000 points d'indice (1998-2012), un tick du ES coûtait 1,3 à 2,5 pb, autant que la dérive ; vers 6 000 points, il coûte 0,4 pb. C'est le gain brut qui manque.

Bondarenko et Muravyev élargissent le constat, sur les transactions du E-mini de 2004 à 2018. **Quatre heures autour de la clôture asiatique et de l'ouverture européenne font toute la hausse moyenne du marché, avec un Sharpe de 1,6 qui « reste élevé après frais »** ; les vingt autres heures donnent un « zéro bruité ». L'incertitude lue dans les futures sur le VIX monte pendant la nuit et retombe à l'ouverture européenne, et l'effet était plus fort pendant le COVID ([JFQA 2023](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3)). La version de 2020 annonçait un Sharpe de 1,2 après frais et un R² hors échantillon élevé ([Northern Finance Association](https://portal.northernfinanceassociation.org/viewp.php?n=2240010836)). Le communiqué de l'université place la fenêtre de 23 h 30 à 3 h 30 ([Michigan State University](https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/)).

Ce « hors échantillon » est un test récursif mené à l'intérieur de 2004-2018. Aucun test postérieur à la publication n'a été trouvé, et l'heure de 2 h à 3 h, au cœur de leur fenêtre, est nulle depuis 2021. Un compte qui doit sortir à 3 h n'en garderait de toute façon que trois heures et demie.

Le projet a déjà rejeté les formes directes de ces deux articles :
- l'achat de 18 h à 9 h 30 (NQ : t 1,74) ;
- les 173 règles de la réouverture de 18 h ;
- l'achat des indices à l'ouverture de Francfort, avec ou sans baisse de la veille.

La seule trace de l'idée de Boyarchenko est un rebond du NQ de 18 h à 19 h après une dernière heure en baisse. Il fait +0,77 pb avant frais, trois fois moins que les frais (`asie/README.md`). Seule la partie de 23 h 30 à 2 h de la fenêtre de Bondarenko et Muravyev n'a jamais été isolée. Elle mérite un contrôle bon marché sur MNQ et MES, pas le statut de piste, puisque la nuit américaine n'a plus aucune fenêtre au gain documenté après 2020. Il faut aussi compter avec la minceur du marché : de la nuit asiatique à la séance américaine, le volume du ES est multiplié par plus de cinquante ([Andersen, Bondarenko, Kyle, Obizhaeva](https://pages.nes.ru/aobizhaeva/ABKO-intradayinv.pdf)). Le glissement d'un ordre stop compte alors davantage que l'écart affiché.

## Le fixing de Tokyo rapporte moins qu'un aller-retour sur 6J

Le flux du fixing est réel et bien documenté. **Le dollar monte avant les fixings de change et rebaisse après, ce qui dessine un « W » sur 24 heures**, pour les neuf devises les plus échangées sur 21 ans. Les banques intermédient une demande de dollars inconditionnelle et se font payer le risque d'inventaire ([Krohn, Mueller, Whelan, Journal of Finance 2024](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306)). Le fixing de Tokyo, à 9 h 55 heure de Tokyo, tombe à 19 h 55 EST ou 20 h 55 EDT ; le « W » se décale d'environ une heure entre le printemps et l'automne ([UNSW BusinessThink](https://www.businessthink.unsw.edu.au/articles/forex-market-patterns-currency-fixing-times-us-dollar-demand)).

Mais l'effet est petit et ne survit pas aux frais :
- **environ 2,5 pb** pour le portefeuille du dollar dans la montée vers les fixings de Tokyo et de Francfort, sur 1999-2019, soit environ 3,75 pips de USD/JPY à 150 ([version de travail de 2022](https://www.wu.ac.at/fileadmin/wu/d/ri/isk/VSFX_2022/Paper/Session_III_1a_Krohn__foreign_Exchange_Fixings_Returns_Around_The_Clock_0712.pdf)) ;
- avec les frais complets déduits des cotations indicatives, les Sharpe deviennent négatifs ;
- le retournement de Tokyo, « nettement plus petit », perdait au début de l'échantillon ([Banque du Canada, 2021](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf)) ;
- les fenêtres longues gardaient un Sharpe de 0,5 à 0,8 après frais, mais les auteurs jugent « presque impossible » de gagner à court terme en tradant le fixing ([AEA 2020](https://www.aeaweb.org/conference/2020/preliminary/paper/2dedYfDH)).

Ito et Yamada décrivent ce qui est propre à Tokyo : les banques y fixent elles-mêmes le cours, biaisé vers un dollar fort. Les déséquilibres d'ordres autour de 9 h 55 sont positifs « presque tous les jours, mais seulement pour USD/JPY », sur des données de 1999 à 2013 ([Journal of International Economics 2017](https://ideas.repec.org/a/eee/inecon/v109y2017icp214-234.html) ; [NBER 2015](https://www.nber.org/papers/w21518)). Le gotobi amplifie ce flux les 5, 10, 15, 20 et 25 de chaque mois et en fin de mois. Il ne repose que sur une prépublication portant sur 2018-2020, dont les résultats chiffrés n'ont pas été vus ([Bessho, Sugimoto, Suzuki 2023](https://arxiv.org/abs/2301.13204)).

Après 2020, il n'y a plus que des praticiens, et ils se contredisent :
- +4,54 pips bruts par trade sur 2006-2025 ([Alpha in Academia](https://www.alphainacademia.com/p/can-you-beat-the-market-by-trading)) ;
- deux fenêtres d'entrée sur trois mortes hors échantillon ([ForexFactory](https://www.forexfactory.com/thread/1407332-gotobi-tokyo-fix-anomaly-7-years-of-usdjpy-tick)) ;
- un même dépôt GitHub résumé tantôt à +3,18 pips nets, tantôt à −0,137 R après écart sur la période réservée de 2024-2026 ([GitHub](https://github.com/prathamesh-git9/gotobi-fx-bot)).

Sur la CME, ces quelques pips ne passent pas. Un aller-retour coûte environ 3 pips sur 6J, et environ 8 sur le micro yen MJY, dont le tick vaut 2,25 pips à 150. Le gain net attendu est au mieux nul sur 6J et négatif sur MJY. Le projet l'a mesuré : les effets du fixing existent mais sont 2 à 3 fois plus petits que les frais, et le gotobi échoue au coffre 2023-2026 (`asie/README.md`).

Une devise se déprécie pendant ses propres heures ouvrables : c'est documenté sur 1993-2005, puis relié au flux d'ordres ([Ranaldo, JBF 2009](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=960209) ; [Breedon, Ranaldo, JMCB 2013](https://onlinelibrary.wiley.com/doi/abs/10.1111/jmcb.12032)). C'est très probablement le même flux que celui du fixing : les résidents achètent des devises étrangères le matin. Pour le dollar australien, la séance de Sydney n'affiche qu'un rendement minime, avec 50 % de hausses ([extrait du tableau](https://www.researchgate.net/publication/228742460_Intraday_Patterns_in_FX_Returns_and_Order_Flow)). C'est bien trop peu pour un M6A dont le tick vaut une fois et demie l'écart moyen du 6A. Les ouvertures de Tokyo et de l'Australie font monter la volatilité du change de plus de 20 % ([arXiv 2024](https://arxiv.org/pdf/2411.16244)), sans lui donner de sens.

Les statistiques chinoises posent un autre problème. Le PMI officiel sort à 9 h 30 à Pékin (20 h 30 EST, 21 h 30 EDT), à la minute où ouvrent Shanghai et Hong Kong ([investingLive](https://investinglive.com/news/economic-calendar-in-asia-monday-june-30-2025-china-official-pmis-for-june-20250629)). Trois études montrent que ces chiffres font bouger les marchés :
- de 2009 à 2013, toutes les annonces chinoises liées à l'industrie font bouger les futures d'indices mondiaux, l'énergie, les métaux industriels et les devises des matières premières, mais pas celles sur la consommation ([Baum, Kurov, Wolfe, JIMF 2015](https://ideas.repec.org/a/eee/jimfin/v59y2015icp100-122.html)) ;
- la réaction du dollar australien à ces chiffres a grandi de 2000 à 2016 ([RBA 2016](https://www.rba.gov.au/publications/bulletin/2016/dec/6.html)) ;
- une surprise de 1 % sur la production industrielle fait environ +21 pb sur les actions chinoises et +3 pb en Asie-Pacifique ([FMI 2025](https://www.imf.org/-/media/files/publications/wp/2025/english/wpiea2025133-print-pdf.pdf)).

Mais le sens de la réaction dépend de l'écart au consensus. Sans historique des consensus, que le projet n'a pas, ce n'est pas une anomalie horaire, au mieux un filtre de volatilité. Bulenox autorise d'ailleurs le trading pendant les annonces ([FAQ Bulenox](https://bulenox.com/faq)).

## L'or monte en Asie depuis 2024, mais pas sur les vrais prix MGC

La recherche revue ne place pas la formation du prix de l'or à Shanghai :
- les futures de New York la mènent sur cinq fuseaux, avec **56 % de part d'information** ([IRFA 2021](https://www.sciencedirect.com/science/article/abs/pii/S1057521921002209)) ;
- pendant les heures asiatiques, Shanghai (SHFE) ne pèse qu'environ 15 %, contre 47 % pour le COMEX et 24 % pour Londres ([IDEAS](https://ideas.repec.org/a/eee/finana/v78y2021ics1057521921002209.html)) ;
- Shanghai a ouvert une séance de nuit, qui chevauche la journée américaine, et la part chinoise a baissé depuis ([Jiang, Kellard, Liu, JFM 2020](https://econpapers.repec.org/RePEc:wly:jfutmk:v:40:y:2020:i:10:p:1486-1507)).

La seule étude revue des rendements par séance du COMEX couvre 1985-2012. Elle trouve des rendements de « nuit » significativement positifs et des rendements de jour négatifs. Mais cette nuit mêle Asie et Londres, l'asymétrie « s'est beaucoup affaiblie », et les auteurs l'attribuent à un prix « trop haut à l'ouverture » des marchés ([Blose, Gondhalekar, Kort 2018](https://ideas.repec.org/a/spr/jecfin/v42y2018i3d10.1007_s12197-017-9403-0.html)). Une étude de 2026 garde une moyenne de nuit positive pour l'ETF GLD après correction des tests multiples ; aucun résultat après frais n'y était visible ([MDPI Commodities 2026](https://www.mdpi.com/2813-2432/5/4/26)).

Le « bid asiatique » récent est mieux chiffré mais moins solide :
- une prépublication d'août 2026 trouve que depuis le 22 juillet 2024, **les heures asiatiques (0 h - 8 h UTC, soit 19 h - 3 h EST) ont fait 77,2 % de la hausse cumulée de l'or**, qui a pris 81 % sur la période ; le momentum de court terme se prolonge dans la séance asiatique (autocorrélation de +0,13), alors que celui de la séance américaine ne survit pas aux frais ([Wei, SSRN 2026](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7257240)) ;
- le World Gold Council note que les replis se font surtout aux heures américaines et les rebonds aux heures asiatiques ([WGC, juillet 2026](https://www.gold.org/goldhub/research/gold-mid-year-outlook-2026)) ;
- des données de Morgan Stanley citées par Saxo montrent −5,9 % pendant les heures de la corbeille américaine et +14,7 % en dehors, sur quatre semaines, et un bid qui disparaît pendant la fermeture chinoise du 1er mai 2025 ([Saxo](https://www.home.saxo/content/articles/commodities/gold-corrects-sharply-from-record-highs-as-chinese-demand-pauses-01052025)).

Mais en 2026, jusqu'à la mi-novembre, l'Asie ne fait que **+3,4 %, contre −28,1 % aux heures américaines**, sans constance d'un mois à l'autre ([Forex.com](https://www.forex.com/en-us/news-and-analysis/gold-outlook-asia-buys-the-dip-us-hammers-the-rip/)). Cela fait environ 1,5 pb par séance asiatique, pour un aller-retour MGC d'environ 0,9 pb.

Le projet a déjà tranché sur la forme simple de cette idée. L'or acheté hors des heures de New York a été rejeté. L'or acheté à 18 h et revendu à 23 h 30 passait sur les cotations HistData (t 3,49 sur 2023-2026), puis a échoué sur 474 soirs de vrais MGC (t 0,95). L'essentiel du gain tenait dans les cinq premières minutes, quand le prix acheteur remonte parce que l'écart se resserre, sans que personne ait pu acheter à ce prix (`asie/README.md`). Les chiffres de 2026 cités par la presse reposent probablement sur des barres horaires du comptant, exposées au même piège.

Ce qui reste n'est pas une stratégie mais un test de mécanisme. Si le bid vient de la demande chinoise, il doit disparaître quand Shanghai est fermé : Nouvel An lunaire, 1er mai, semaine dorée. Si un flux réel apparaît, le MGC est le contrat où il coûterait le moins à jouer, avec 42 % de son volume pendant les heures asiatiques de la CME ([CME OpenMarkets 2025](https://cmegroup.com/openmarkets/metals/2025/Asias-Growing-Gold-Demand-Fuels-Surging-Derivatives-Market.html)). Aucune étude ne teste si la prime de Shanghai prédit le COMEX.

## La Chine documente un momentum que la CME ne permet pas de jouer

La référence est l'article de Gao, Han, Li et Zhou, sur le SPY de 1993 à 2013. La première demi-heure, mesurée depuis la clôture de la veille, prédit la dernière : R² de 1,6 %, 2,6 % avec l'avant-dernière demi-heure, 1,2 % hors échantillon. La stratégie de timing affichait un Sharpe de 1,08, contre 0,29 pour l'achat simple, et environ 6,5 % par an ([JFE 2018](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414) ; [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)), soit à peine 2,6 pb par jour. Aux États-Unis, l'effet s'est éteint après publication :
- une réplication indépendante trouve une pente de 0,003 (t 0,20) sur 2013-2019 ([Temperance Capital](https://temperancecapital.substack.com/p/market-intraday-momentum-replicates)) ;
- le projet l'a rejeté sur les futures américains à la porte 2 (p = 2,8 %, 1 % exigé) (`rea/PISTES.md`).

La Chine est l'endroit où ce momentum a été le plus étudié :
- dans quatre futures de matières premières chinois (cuivre, acier, soja, tourteau de soja), la première demi-heure prédit la dernière, surtout dans les métaux après une première séance agitée ([Jin, Kearney, Li, Yang, JFM 2020](https://onlinelibrary.wiley.com/doi/10.1002/fut.22084)) ;
- l'effet existe aussi dans les futures sur indices ([Li et al., FRL 2020](https://ideas.repec.org/a/eee/finlet/v35y2020ics1544612319304337.html)) ;
- dans les actions, les première et septième demi-heures prédisent la dernière, dans et hors échantillon ([Economic Modelling 2019](https://www.sciencedirect.com/science/article/abs/pii/S0264999318306692)) ;
- sur le CSI 300 et son ETF de 2012 à 2017, il s'accompagne d'un retournement à la deuxième demi-heure ([FRL 2019](https://www.sciencedirect.com/science/article/abs/pii/S1544612318307414)).

Ces résultats ont trois limites :
- aucun de ces travaux ne donne de résultat après frais ;
- leurs échantillons traversent les restrictions de 2015-2019 sur les futures d'indices, avec des dépôts portés jusqu'à 40 % de la valeur des contrats ([FIA](https://www.fia.org/marketvoice/articles/2019-shaping-be-big-year-chinese-equity-index-futures)) ;
- les travaux plus récents trouvent des retournements dans les futures de matières premières sur 2017-2022 ([PBFJ 2024](https://www.sciencedirect.com/science/article/abs/pii/S0927538X24002865)), ou un prédicteur passé à la séance de nuit pour l'or et l'argent de Shanghai ([Ma et al., GFJ 2025](https://www.sciencedirect.com/science/article/abs/pii/S1044028325000110)).

Le rendement de nuit des actions chinoises est même négatif, d'environ 14 pb, à cause de la règle T+1 ([Qiao, Dam, JFM 2020](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3418356)). Hong Kong n'a fait l'objet d'aucune étude, et ne montre aucun momentum dans l'étude Asie-Pacifique ([PBFJ 2023](https://www.sciencedirect.com/science/article/pii/S0927538X2300152X)). L'Australie n'en montre pas non plus ([PBFJ 2021](https://sciencedirect.com/science/article/pii/S0927538X21000068)).

Rien de tout cela ne se trade à la CME. Le CSI 300, l'A50, le Hang Seng et le SPI 200 n'y sont pas cotés, et le E-mini FTSE China 50 y est suspendu depuis le 23 novembre 2020 ([CME SER-8670](https://www.cmegroup.com/notices/ser/2020/10/SER-8670.html)). Aucune étude ne montre que la dernière demi-heure chinoise (1 h 30 - 2 h EST, 2 h 30 - 3 h EDT) se transmet au MES, au MNQ, au M6A ou au cuivre.

L'ouverture de Hong Kong et de Shanghai (9 h 30, soit 20 h 30 EST ou 21 h 30 EDT) n'a fait l'objet d'aucune étude d'effet sur les futures de la CME. L'information circule surtout des États-Unis vers la Chine ([Economic Modelling 2015](https://www.sciencedirect.com/science/article/abs/pii/S0264999315003211)). La même minute réunit l'ouverture des deux bourses, celle des futures CSI 300 et, certains jours, le PMI officiel, ce qui rend tout « effet d'ouverture » impossible à isoler. Le projet a d'ailleurs rejeté la cassure de l'ouverture de Hong Kong sur le NQ, le ES, l'or et les devises.

Le pétrole n'offre pas davantage :
- aucune dérive horaire du WTI n'est documentée ;
- le brut de Shanghai se comporte en marché « régional » pendant sa séance de jour, qui tombe dans la fenêtre ([Ji, Zhang, Zhao 2021](https://link.springer.com/article/10.1007/s10479-021-04097-x)) ;
- son retournement intraday est lié aux annonces de stocks ([Wen, Wang, Zhang 2021](https://ideas.repec.org/a/eee/ecmode/v96y2021icp209-219.html)) ;
- un aller-retour MCL coûte environ 5 pb.

## Le Nikkei réunit les seules preuves récentes encore intactes

### Trois sources pointent vers un momentum de fin de séance au Japon

- **Asie-Pacifique.** L'étude des ETF d'Asie-Pacifique trouve que le momentum de la première à la dernière demi-heure est « surtout visible en Chine et au Japon ». Il est absent à Hong Kong et à Singapour, faible en Corée, et **pendant le COVID, il n'a tenu qu'au Japon** ([Limkriangkrai, Chai, Zheng, PBFJ 2023](https://www.sciencedirect.com/science/article/pii/S0927538X2300152X)). L'échantillon, l'ETF japonais utilisé et un éventuel test des frais n'ont pas pu être lus.
- **Seize marchés développés.** Le momentum y est significatif dans douze marchés, et plus fort quand la liquidité est faible et la volatilité forte ([Li, Sakkas, Urquhart, Journal of Financial Markets 2022](https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html)). Mais la version de travail signale un problème de données pour l'Australie et le Japon, écartés d'une partie de l'analyse, et l'annexe y décrit un momentum faible ([manuscrit accepté](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf)). Sur le Japon, ce papier est au mieux neutre.
- **Plus de 60 contrats à terme.** Le résultat le plus solide est mondial. Dans des contrats sur actions, taux, matières premières et devises, de 1974 à 2020, **le rendement de la journée jusqu'à 30 minutes de la clôture prédit les 30 dernières minutes « partout »**, puis se retourne les jours suivants. Les auteurs relient l'effet à la couverture gamma des teneurs de marché d'options et aux ETF à levier ([Baltussen, Da, Lammers, Martens, JFE 2021](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)). La présence d'un contrat Nikkei dans l'échantillon n'a pas pu être vérifiée.

### Les fonds à levier japonais donnent un mécanisme identifié

En 2016, la Banque du Japon décrivait des ménages qui investissent de plus en plus par des fonds à levier. Ces fonds rééquilibrent leurs futures Nikkei près de la clôture, à partir de 15 h, l'heure de clôture du comptant à l'époque. **De 15 h 00 à 15 h 15, les futures avaient tendance à bouger dans le sens pris par le Nikkei jusqu'à 15 h** : la demande suit le marché, mais la BOJ la jugeait petite par rapport au volume des futures ([BOJ Review 2016-E-1](https://www.boj.or.jp/en/research/wps_rev/rev_2016/data/rev16e01.pdf)).

La raison est arithmétique. Pour garder un levier L, un fonds doit traiter L(L−1) × r × actif net en futures, où r est la variation du jour. Les fonds à levier et les fonds inverses achètent donc tous après une hausse et vendent tous après une baisse. Un courtier japonais en donne un exemple : un fonds 2x de 10 milliards de yens rachète 2 milliards après une hausse de 10 % ([Matsui](https://www.matsui.co.jp/fund/column/bull-bear/)).

Le NEXT FUNDS 1570 réplique 2 fois le Nikkei par des futures ([NEXT FUNDS](https://nextfunds.jp/en/lineup/1570/)). Il pesait environ 430 à 457 milliards de yens en 2024-2025 ([dépôt JPX](https://www2.jpx.co.jp/disc/15700/140120250701505507.pdf)). Cela fait environ 9 milliards de yens de futures par point de pourcentage de variation du Nikkei, soit 60 millions de dollars ou 240 NKD à 50 000 points : peu de chose, sauf les jours de forte variation. Aux États-Unis, un écart-type de flux de rééquilibrage des ETF à levier ajoute 430 % du rendement moyen de la dernière demi-heure ([Mathis, Moerke 2022](https://wp.lancs.ac.uk/fofi2022/files/2022/08/FoFI-2022-027-Mathis-Moerke.pdf)).

### L'ouverture de Tokyo sur-réagit à la séance américaine

Les rendements de journée à Tokyo sont corrélés aux rendements de nuit de New York. On ne trouve pas de débordement décalé significatif, sauf de New York vers Tokyo après le krach de 1987 ([Lin, Engle, Ito, RFS 1994](https://www.nber.org/papers/w3911)). La hausse « nocturne » du Nikkei de 1986-1998 tenait aux ouvertures figées du comptant ([Japan and the World Economy](https://www.sciencedirect.com/science/article/abs/pii/S092214250200049X)). Le NKD, coté toute la nuit, ne laisse pas capter cet effet.

Une étude de 2026 sur les futures du Nikkei trouve qu'**après une séance plus haute du S&P 500, ces futures rapportent moins dans les 30 premières minutes de la séance japonaise et plus dans les 30 minutes avant la clôture** ([Finance Research Open 2026](https://www.sciencedirect.com/science/article/pii/S3050700626000204)) :
- le retournement du début vient d'une sur-réaction des traders non informés, corrigée par l'arbitrage ;
- le momentum de la fin vient de rééquilibrages faits à des fréquences différentes selon les investisseurs ;
- les retournements forts sont moins probables en crise.

Ses auteurs, son échantillon et ses tailles d'effet n'ont pas pu être lus (preuve C).

Une autre étude trouve un momentum « croisé » : la dernière demi-heure américaine prédit la première demi-heure étrangère, avec un gain positif après frais ([Xu et al., JIFMIM 2025](https://www.sciencedirect.com/science/article/abs/pii/S1042443125001295)). Mais elle porte sur des indices au comptant, dont la première demi-heure contient l'écart de la nuit, que les futures ont déjà absorbé. Ce gain n'est pas accessible sur NKD.

### Deux flux japonais ont disparu

Ces deux flux ne doivent pas être confondus avec les pistes ci-dessus.

- **Les achats d'ETF de la BOJ.** La règle « matinée faible, achats de la BOJ l'après-midi » passait ses ordres pendant la pause de midi et a fait monter les rendements de midi ([Fukui, Yagasaki, ESRI 2023](https://www.esri.cao.go.jp/en/esri/content/e_dis376.pdf)). Elle était déjà anticipée : le volume des futures montait à midi « sans presque aucun mouvement de prix » ([Ko, FRL 2026](https://www.sciencedirect.com/science/article/abs/pii/S1544612325026704)). La BOJ a cessé tout achat le 19 mars 2024 ([BOJ](https://www.boj.or.jp/en/mopo/measures/term_cond/yoryo85.htm)). Elle vend depuis janvier 2026, à 330 milliards de yens par an ([Jiji via Adnkronos](https://english.adnkronos.com/2026/02/03/boj-begins-unloading-etfs-in-jan/)), soit environ 1,3 milliard par jour : un flux sans commune mesure.
- **La dérive avant la clôture, peut-être.** La structure de la clôture a changé. Depuis le 5 novembre 2024, la Bourse de Tokyo ferme à 15 h 30 avec une enchère de clôture ([JPX](https://www.jpx.co.jp/english/corporate/news/news-releases/1030/20241105-01.html)). Selon le projet de JPX, la séance de jour des futures d'Osaka finit par une enchère à 15 h 45 ([consultation JPX](https://www.jpx.co.jp/rules-participants/public-comment/detail/d8/cg27su00000068h0-att/jr4eth00000027c9.pdf)). Les rééquilibrages peuvent désormais passer dans ces enchères ; aucune étude ne dit si la dérive avant la clôture a rétréci.

### Le MNK, à condition que Bulenox l'ouvre

Pour un compte Bulenox, le contrat adapté est le Micro Nikkei en dollars (MNK), lancé le 28 octobre 2024 :
- 0,50 $ par point d'indice, tick de 5 points (2,50 $) ;
- coté du dimanche au vendredi, de 18 h à 17 h (New York), avec une pause d'une heure ([CME](https://www.cmegroup.com/markets/equities/international-indices/micro-nikkei-usd.contractSpecs.html)).

Le NKD (5 $ par point, tick de 25 $, [CME](https://www.cmegroup.com/articles/2024/equity-trading-opportunities-in-nikkei-225-futures-at-cme-group.html)) représente 250 000 à 315 000 $ de nominal, trop pour un compte de 50 000 $. Le NIY et le Micro Nikkei en yens règlent leurs gains en yens.

La CME indique que près de 75 % des transactions sur ses futures Nikkei ont lieu hors des heures du comptant de Tokyo ([communiqué CME 2024](https://www.cmegroup.com/media-room/press-releases/2024/10/01/cme_group_to_launchyen-andusdollar-denominatedmicronikkeifutures.html)). Pendant la séance de Tokyo, c'est Osaka qui fait le prix, et la profondeur du MNK entre 1 h et 3 h du matin (New York) est inconnue.

Deux vérifications s'imposent avant tout test :
- **Le contrat chez Bulenox.** La FAQ de Bulenox annonce 41 contrats et cite le ES, le NQ, le YM, le RTY, le EMD, le CL, le NG, le RB, le GC, le SI, le HG, le PL, le 6E, le 6B et le 6J, mais pas le Nikkei ([FAQ Bulenox](https://bulenox.com/faq)). La liste Yahoo du projet, elle aussi de 41 contrats, ne le contient pas non plus. Il faut demander à Bulenox si le MNK est ouvert, et à quelle commission.
- **Les données.** Une mesure faite pour ce rapport sur les fichiers HistData du Nikkei (`donnees_libres/histdata_5min`, branche `claude/affectionate-turing-tnz0mn`) donne de bons résultats :
  - une barre existe à 9 h 00, 9 h 30 et 15 h 00 (heure de Tokyo) pour 97 à 100 % des jours de semaine, chaque année de 2012 à 2026 ;
  - à 15 h 30, la couverture tombe à 84-94 % en 2012-2014 ;
  - la volatilité culmine dans l'heure de 9 h.

  Ce sont des cotations au prix acheteur. Mais les fenêtres proposées tombent en pleine séance d'Osaka, loin du resserrement de l'écart de 18 h qui a trompé le projet sur l'or. Le projet n'a en revanche aucun vrai prix de futures Nikkei.

## Trois règles à figer avant de lancer la machine 9

Les trois règles suivantes sont fixées avant tout calcul, avec les conventions de `asie/machine9.py`, qui gère déjà les jours de Bourse de Tokyo et le changement d'heure de clôture. Elles partagent les conventions suivantes :
- **C** est l'heure de clôture de la Bourse de Tokyo : 15 h 00 avant le 5 novembre 2024, 15 h 30 depuis.
- **C + 15 minutes** est la fin de la séance de jour des futures d'Osaka : 15 h 15 avant la réforme, 15 h 45 après selon le projet de JPX (à confirmer).
- **Prix** : l'ouverture de la barre de 5 minutes qui commence à l'heure dite, sans stop ni seuil.
- **Frais décisifs** : ceux déjà codés pour le Nikkei, 2,8 pb par aller-retour (un MNK à 50 000 points). Pour information seulement, la même mesure avec 14 points d'indice (le vrai coût d'un MNK à chaque date), puis avec des frais doublés.
- **Horaires** : toutes les positions sont fermées avant 3 h (New York). La journée de trading de Bulenox commence à 18 h, et le compte doit être à plat avant 16 h 59 ([Bulenox](https://bulenox.com/help-center/qualification)).

| | Piste 1 : fin de séance d'Osaka dans le sens de la journée | Piste 2 : ouverture de Tokyo contre le S&P 500 | Piste 3 : zone de bruit à Tokyo |
|---|---|---|---|
| Appui | Baltussen et al. 2021 (A) ; BOJ 2016 (B) ; Limkriangkrai et al. 2023 (B) | Finance Research Open 2026 (C), cohérent avec Lin, Engle, Ito 1994 (A) | règle du bot, validée par l'usine sur le NQ ; mécanisme de Baltussen et al. ; aucune étude au Japon |
| Signal | R = variation du Nikkei de C + 15 min la veille à C − 15 min le jour même | S = variation du S&P 500 de 16 h à 16 h (New York) sur la dernière séance américaine finie avant 9 h à Tokyo | bande de bruit autour de l'ouverture de 9 h 00 et de la clôture de la veille |
| Trade | achat si R > 0, vente si R < 0, de C − 15 min à C + 15 min | vente si S > 0, achat si S < 0, de 9 h 00 à 9 h 30 (Tokyo) | contrôle toutes les 30 min de 9 h 30 à C − 30 min ; achat au-dessus de la bande, vente au-dessous ; tout fermé à C |
| Heures de New York | avant la réforme : 0 h 45 - 1 h 15 EST (1 h 45 - 2 h 15 EDT) ; après : 1 h 15 - 1 h 45 EST (2 h 15 - 2 h 45 EDT) | 19 h 00 - 19 h 30 EST (20 h 00 - 20 h 30 EDT) | de 19 h EST (20 h EDT) à 1 h ou 1 h 30 EST (2 h ou 2 h 30 EDT) |
| Variante déclarée d'avance | signal de Gao et al. : variation de C + 15 min la veille à 9 h 30 | même S, dans le même sens, de C − 15 min à C + 15 min | aucune |
| Données | HistData JPXJPY, 5 min, 2012 → octobre 2026 | JPXJPY et HistData S&P 500 (usa500idxusd) | JPXJPY |

### Piste 1 : la fin de séance d'Osaka

C'est la traduction la plus directe des preuves. La fenêtre est la dernière demi-heure de la séance de jour des futures d'Osaka, celle de Baltussen et al. Elle contient exactement la fenêtre de 15 h 00 à 15 h 15 où la BOJ a vu les futures suivre la journée. Dans `machine9.py`, elle s'écrit :

```
entree ("TSE", -15), sortie ("TSE", 15), signal (("veille", ("TSE", 15)), ("TSE", -15)), sens de continuation
```

Le mécanisme donne deux prédictions, à lire pour information sans en faire des critères de décision :
- le gain doit croître avec |R|, puisque le rééquilibrage est proportionnel à la variation du jour ;
- la période postérieure au 5 novembre 2024 doit être lue à part, puisque l'enchère de clôture a pu absorber le flux.

La barre réaliste est celle de Gao et al. aux États-Unis : environ 2,6 pb bruts par jour, de l'ordre des frais d'un MNK. Il faut donc un effet japonais nettement plus fort que l'effet américain.

### Piste 2 : l'ouverture de Tokyo contre la séance américaine

Elle ne lit que le sens de la séance américaine et joue le retournement de la première demi-heure de Tokyo, la moitié « retour » de l'article de 2026. Sa variante joue la moitié « momentum » du même article, sur la fenêtre de la piste 1. La fenêtre de 9 h 00 à 9 h 30 a été fixée sans avoir pu lire la définition exacte de l'article, alors que les futures d'Osaka ouvrent à 8 h 45. Si le texte complet en donne une autre, il faut la corriger avant le calcul, jamais après. Elle demande une petite extension de `jouer` dans `machine9.py`, pour lire le signal sur un autre marché que celui qu'on trade. Elle a pour elle une observation du projet : les cassures de début de séance, à Tokyo comme à la réouverture de 18 h, se retournent plus souvent qu'elles ne continuent. Elle a contre elle la faiblesse de sa source unique.

### Piste 3 : la zone de bruit à Tokyo

Elle transpose la seule source de gain validée du projet, la zone de bruit du bot (Zarattini, Aziz, Barbon 2024 ; t +3,88 sur 2014-2026, 12 années positives sur 13, `rea/PISTES.md`), à la séance « maison » du Nikkei. La machine 8 l'a jouée la nuit sur le NQ, le ES et l'or, et l'a vue perdre même avant frais : la nuit, un prix qui sort de sa bande revient au lieu de continuer (`asie/README.md`). Mais la nuit n'est pas la séance de ces actifs. La séance de 9 h à 15 h 30 à Tokyo est celle du Nikkei : c'est là que vivent les couvertures des teneurs de marché d'options d'Osaka et les rééquilibrages des fonds à levier.

Les règles sont celles de la machine 8 (`asie/zone_nuit.py`), avec l'horloge de Tokyo :
- **Références** : O = ouverture de la barre de 9 h 00 ; C' = prix à la clôture de Tokyo de la veille.
- **Bruit** à l'heure h : moyenne, sur les 14 séances précédentes, de |prix à h ÷ O − 1|.
- **Bande**, de largeur 1,0 (la bande plus large a été rejetée par l'usine) : haut = max(O, C') × (1 + bruit), bas = min(O, C') × (1 − bruit).
- **Prix moyen** : moyenne des clôtures de 5 minutes depuis 9 h 00, faute de volume.
- **Contrôles** : au prix de clôture de la barre qui finit à l'heure du contrôle, pause de midi comprise, puisque les futures cotent pendant la pause.
- **Entrées** : achat si le prix passe au-dessus du haut, vente s'il passe sous le bas. Pas de nouvelle entrée au dernier contrôle.
- **Sorties** : en achat, sortie si le prix ≤ max(haut, prix moyen) ; en vente, sortie si le prix ≥ min(bas, prix moyen). Tout est fermé à l'ouverture de la barre de C.

### Le tri commun, puis les vrais prix

Les cinq règles (les trois pistes et deux variantes) passent ensemble le tri des machines 7 et 8 :
- **Exploration 2012-2022** : t ≥ 2 après frais ; placebo de 1 000 tirages au hasard du sens de chaque trade, battu à 95 % ; gain positif dans au moins 2 des 3 sous-périodes ; Benjamini-Hochberg à 10 % sur les cinq.
- **Coffre** du 1er janvier 2023 au 2 octobre 2026, ouvert une seule fois : seuil de Bonferroni, 3 années positives sur 4.

Une survivante devra ensuite passer de vrais prix, que le projet n'a pas pour le Nikkei :
- ajouter le futures NKD de Yahoo (code NKD=F, s'il est disponible) au téléchargement, pour comparer ses barres de 5 minutes sur 60 jours aux cotations HistData, comme pour l'or ;
- puis 3 à 4 semaines de MNK en papier avec `usine/rapprochement.py`, pour mesurer l'écart réel entre 1 h et 3 h du matin.

Si Bulenox n'ouvre pas le Nikkei, aucune des trois pistes n'a d'objet pour ce compte. Il ne resterait que le contrôle de Bondarenko et Muravyev sur MNQ et MES : achat de 23 h 30 à 3 h, alors que l'heure centrale de cette fenêtre est nulle depuis 2021.

## Conclusion

Ce bilan déplace la question. La nuit n'offre plus d'anomalie propre aux actifs américains. Leurs mouvements de 18 h à 3 h sont des flux venus d'un autre fuseau, ou des stocks que les teneurs de marché doivent écouler. Ils s'éteignent quand le flux s'arrête, ou se révèlent des artefacts de cotation. Le projet et la littérature convergent : hors de leur séance, le NQ, le ES et l'or reviennent au lieu de continuer. La seule séance « maison » que la fenêtre contient en entier, et que la CME rend accessible, est celle de Tokyo. C'est là, et seulement là, que les flux de couverture qui font fonctionner la zone de bruit à New York ont une chance d'exister pendant les heures où l'utilisateur trade. Un mécanisme identifié a aussi une vertu que les anomalies purement statistiques n'ont pas : il dit à quoi ressemblerait un faux positif. Un gain de fin de séance qui ne grandirait pas avec la variation du jour, ou qui changerait de nature sans raison au passage de la clôture à 15 h 30, serait suspect même s'il passait le coffre.

L'ordre des opérations compte autant que les règles. La vérification la moins chère est administrative : une réponse de Bulenox sur le MNK vaut davantage que n'importe quel calcul, puisque toute la recherche en dépend. La dérive de Boyarchenko et al. n'est pas à rejouer mais à surveiller, comme un indicateur de régime. Ses auteurs ont nommé la variable qui la ferait revenir, la dispersion des déséquilibres de clôture. Le projet peut suivre cette variable, par exemple à travers les déséquilibres publiés des enchères de clôture, sans engager un dollar, et rouvrir la piste le jour où cette dispersion retrouverait ses niveaux d'avant 2020.
