# Tokyo garde la dernière piste ouverte

Presque toutes les anomalies documentées entre 18 h et 3 h (heure de New York) sont fermées pour un compte Bulenox de 50 000 $ : la dérive de nuit du S&P 500 est nulle sur 2021-2025 selon ses propres auteurs, sur le blog de la Fed de New York ; le fixing de Tokyo et le gotobi rapportent moins qu'un aller-retour sur 6J ; les achats d'ETF de la Banque du Japon ont cessé le 19 mars 2024 ; le momentum intraday chinois se joue sur des contrats absents de la CME ; et la hausse de l'or aux heures asiatiques n'est documentée que pour le régime 2024-2026, par des sources non revues, alors que le projet l'a déjà rejetée sur de vrais prix MGC. **Une seule famille garde un appui académique récent sans avoir jamais été testée par le projet : le momentum, ou le retournement, du Nikkei pendant la séance de Tokyo.** Dans plus de 60 contrats à terme, de 1974 à 2020, le rendement de la journée prédit la dernière demi-heure ; en Asie, cet effet est « surtout visible en Chine et au Japon » et n'a tenu qu'au Japon pendant le COVID ; la Banque du Japon a décrit dès 2016 le flux qui le nourrit, des fonds à levier qui rachètent des futures Nikkei après une hausse, juste après la clôture du comptant ; et une étude de 2026 trouve que ces futures se retournent dans leurs 30 premières minutes après une forte séance du S&P 500, puis repartent vers la clôture. Aucune de ces études ne publie de résultat après frais sur les futures du Nikkei, alors qu'un aller-retour sur le Micro Nikkei (MNK) coûte environ 2,2 à 2,8 points de base (pb) aux niveaux de 2025-2026, et la liste des contrats Bulenox trouvée dans les sources ne cite pas le Nikkei, ce qu'il faut vérifier avant tout calcul. Les données HistData du projet couvrent la séance de Tokyo presque chaque jour depuis 2012 et rendent testables trois règles fixées d'avance : la fin de séance d'Osaka dans le sens de la journée, l'ouverture de Tokyo contre la séance américaine, et la zone de bruit du bot transposée à la séance de Tokyo. Toutes les sources ont été lues à travers leurs résumés et extraits, jamais par leurs tableaux complets, et plusieurs tailles d'effet décisives restent inconnues.

## Sur douze pistes, deux restent ouvertes, toutes deux au Japon

Le tableau ci-dessous donne, pour chaque piste, le mécanisme, le contrat de la CME qui la rend jouable, le résultat publié avant puis après frais, la période étudiée et ce qu'on sait de l'effet après 2020, le niveau de preuve et le statut de la piste dans le projet. Le niveau A désigne une grande revue (Journal of Finance, JFE, RFS, JFQA) avec un long échantillon ; B, une revue de spécialité, une banque centrale ou le NBER ; C, un article récent à l'échantillon inconnu ou une prépublication ; D, un praticien, la presse ou des données d'industrie. Les heures sont celles de New York : EST désigne l'heure d'hiver (de novembre à mi-mars) et EDT l'heure d'été ; comme le Japon, la Chine et Hong Kong ne changent pas d'heure, un événement asiatique tombe une heure plus tôt à New York en hiver.

| Piste (source principale) | Mécanisme | Contrat CME | Résultat publié : avant → après frais | Période ; après 2020 | Preuve | Dans le projet |
|---|---|---|---|---|---|---|
| Dérive de 2 h - 3 h ([Boyarchenko, Larsen, Whelan, RFS 2023](https://academic.oup.com/rfs/article-abstract/36/9/3502/7076616)) | stock des teneurs de marché après les ventes de clôture | MES, MNQ | 3,6-3,7 %/an, Sharpe 1,1 → « pas rentable » ; fenêtre 1 h 30 - 3 h 30 : Sharpe 1,3 → 0,3 | 1998-2020 ; **nulle en 2021-2025** | A | rejetée, avec ou sans baisse de la veille |
| Quatre heures autour de l'ouverture européenne ([Bondarenko, Muravyev, JFQA 2023](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3)) | incertitude de la nuit résolue par l'Europe | MES, MNQ | Sharpe 1,6 → « reste élevé » (1,2 après frais dans la version de 2020) | 2004-2018 ; aucun test publié, heure centrale nulle en 2021-2025 | A | dérive 18 h - 9 h 30 rejetée ; 23 h 30 - 2 h jamais isolée |
| Fixing de Tokyo (9 h 55) et gotobi ([Krohn, Mueller, Whelan, JF 2024](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306)) | demande de dollars au fixing, stocks des banques | 6J, MJY, M6A | ≈ 2,5 pb (portefeuille du dollar) → Sharpe négatif à l'écart complet ; gotobi ≈ +4,5 pips bruts | 1999-2019 ; praticiens contradictoires | A (flux), D (trade) | rejeté : effet 2 à 3 fois plus petit que les frais ; gotobi échoue au coffre |
| Devise locale faible pendant ses heures ([Breedon, Ranaldo, JMCB 2013](https://onlinelibrary.wiley.com/doi/abs/10.1111/jmcb.12032)) | achats de devises étrangères par les résidents | 6J, M6A | significatif brut ; AUD : 50 % de hausses → aucun résultat net vu | 1993-2005 ; rien de récent | B | même flux que le fixing |
| Achats d'ETF de la BOJ après une matinée faible ([Fukui, Yagasaki, ESRI 2023](https://www.esri.cao.go.jp/en/esri/content/e_dis376.pdf)) | ordres de la BOJ pendant la pause de midi | futures Nikkei | rendements de midi positifs → déjà anticipés | 2010-2024 ; **morte le 19 mars 2024** | B | sans objet |
| Or acheté en Asie ([Wei, SSRN 2026](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7257240)) | demande chinoise et des banques centrales | MGC | Asie = 77,2 % de la hausse depuis juillet 2024 → aucun résultat net | 2024-2026 ; irrégulier en 2026 | C/D | rejeté ; l'or acheté à 18 h était un artefact de cotation |
| Momentum intraday chinois ([Jin et al., JFM 2020](https://onlinelibrary.wiley.com/doi/10.1002/fut.22084)) | traders informés tardifs, bruit | aucun (SHFE, CFFEX) | significatif brut → aucun résultat net | ≈ 2010-2018 ; retournements en 2017-2022 | B | injouable à la CME |
| Ouverture de Hong Kong et de Shanghai (9 h 30) | information américaine absorbée en Chine | MES, MNQ, MGC, M6A | aucune mesure publiée | — | aucune | cassure rejetée |
| Statistiques chinoises de 9 h 30 ([Baum, Kurov, Wolfe, JIMF 2015](https://ideas.repec.org/a/eee/jimfin/v59y2015icp100-122.html)) | surprises sur la croissance chinoise | M6A, HG, MCL, MES | réaction au chiffre, sens inconnu sans le consensus | 2009-2013 ; pas d'étude intraday récente | B | non testé |
| Pétrole la nuit ([Ji, Zhang, Zhao 2021](https://link.springer.com/article/10.1007/s10479-021-04097-x)) | aucun ; le brut de Shanghai est « régional » le jour | MCL | aucune dérive documentée | — | aucune | sessions rejetées |
| **Momentum de fin de séance au Japon** ([Baltussen et al., JFE 2021](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403) ; [BOJ 2016](https://www.boj.or.jp/en/research/wps_rev/rev_2016/data/rev16e01.pdf)) | couverture gamma, rééquilibrage des fonds à levier | MNK | prévisibilité brute → aucun résultat net au Japon | 1974-2020 ; a tenu au Japon pendant le COVID | A (monde), B (Japon) | **jamais testé** |
| **Retournement de l'ouverture de Tokyo** ([Finance Research Open 2026](https://www.sciencedirect.com/science/article/pii/S3050700626000204)) | sur-réaction après le S&P 500, puis arbitrage | MNK | sens documenté, taille inconnue | période inconnue ; publié en 2026 | C | **jamais testé** |

Deux constats ressortent du tableau. **Les pistes mortes ou trop petites sont celles qui touchent les actifs américains** : S&P 500, or, dollar. Leurs mouvements de nuit viennent soit d'un flux né dans un autre fuseau, soit d'un stock que les teneurs de marché doivent écouler. Ils ont disparu, comme les déséquilibres de clôture aujourd'hui comprimés ou les achats de la BOJ, ou se sont révélés des artefacts de cotation. **Les deux pistes encore ouvertes portent sur le Nikkei**, dont la séance « maison » tombe entièrement dans la fenêtre. 9 h à Tokyo correspond à 19 h EST (20 h EDT), et la clôture de 15 h 30 à 1 h 30 EST (2 h 30 EDT).

### Ce que coûte un aller-retour la nuit

La nuit, les frais décident de presque tout. La liquidité moyenne, elle, n'est pas en cause : selon la CME, l'écart moyen entre prix acheteur et prix vendeur pendant les heures asiatiques est le même que sur la journée entière.

| Contrat | Écart moyen, heures asiatiques | Écart moyen, journée entière | Source |
|---|---|---|---|
| Micro-or | 1,98 tick | 2,01 ticks | [CME OpenMarkets 2025](https://cmegroup.com/openmarkets/metals/2025/Asias-Growing-Gold-Demand-Fuels-Surging-Derivatives-Market.html) |
| WTI | 1,34 tick | 1,35 tick | [CME 2023](https://www.cmegroup.com/articles/whitepapers/leveraging-cme-group-asia-trading-hours-liquidity-for-cross-commodity-trading.html) |
| Yen | 1,08 pip | 1,09 pip | [CME 2023](https://www.cmegroup.com/articles/2023/unlocking-potential-during-asian-trading-hours-with-cme-fx-futures.html) |
| Dollar australien | 0,66 pip | 0,65 pip | [CME 2023](https://www.cmegroup.com/articles/2023/unlocking-potential-during-asian-trading-hours-with-cme-fx-futures.html) |

Ces moyennes couvrent toute la journée asiatique telle que la CME la définit (de 6 h à 18 h à Singapour pour l'or), plus large que la fenêtre étudiée ici. Elles ne disent rien des premières minutes après 18 h, ni de la profondeur du MNK pendant Tokyo. **L'obstacle est la taille du tick des micros.**

Le tableau suivant applique la convention du projet (un tick de glissement par ordre) aux fiches de la CME ([micros](https://www.cmegroup.com/markets/microsuite/fx.html), [MNK](https://www.cmegroup.com/markets/equities/international-indices/micro-nikkei-usd.contractSpecs.html), [6J](https://www.cmegroup.com/markets/fx/fx-product-guide.html)) et aux commissions tout compris du [barème Bulenox d'août 2026](https://bulenox.com/legal/Bulenox-Rates.pdf).

| Contrat | Taille et tick | Aller-retour : 2 ticks + commission | En points de base |
|---|---|---|---|
| MNK | 0,50 $ × indice ; 5 points = 2,50 $ | 5 $ + 2 $ supposés (absent du barème) = 7 $, soit 14 points d'indice | ≈ 2,2 à 63 000 ; ≈ 15 au niveau de 2012 |
| MNQ | — | 1,5 point (convention du projet) | ≈ 2,6 en moyenne sur 2012-2022 (`asie/README.md`) ; moins de 1 en 2026 |
| MGC | 10 onces ; 0,10 $ = 1 $ | 2 $ + 1,52 $ = 3,52 $ | ≈ 0,9 à 4 000 $ |
| 6J | 12,5 M¥ ; 6,25 $ | 12,50 $ + 4,72 $ ≈ 17 $ | ≈ 2,1, soit ≈ 3 pips à 150 ¥ |
| M6A | 10 000 AUD ; 1 $ | 2 $ + 1,00 $ = 3 $ | ≈ 4,6 à 0,65 |
| MCL | 100 barils ; 1 $ | 2 $ + 1,52 $ = 3,52 $ | ≈ 5 à 65 $ |

Le micro-or est de loin le moins cher. Le micro dollar australien et le micro pétrole coûtent 4 à 6 pb, ce qui élimine tout effet de quelques points de base.

Pour le MNK, le coût en points de base dépend du niveau du Nikkei. Dans les fichiers HistData du projet, l'indice est passé d'environ 8 500 points en 2012 à plus de 60 000 en 2026, avec un maximum vers 73 500. Les mêmes 14 points d'indice valent donc environ 15 pb en 2012, et 2,2 pb en octobre 2026.

## La dérive de nuit américaine est morte deux fois

### L'heure de l'ouverture européenne ne payait déjà pas ses frais

Boyarchenko, Larsen et Whelan ont montré qu'entre 1998 et 2019, le contrat E-mini S&P 500 gagnait l'essentiel de sa hausse en une seule heure. **De 2 h à 3 h (New York), à l'ouverture des marchés européens, il rapportait 3,6 % par an** ([Liberty Street Economics, 2021](https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns)). Leur mise à jour de 2026 donne 3,7 % par an sur 1998-2020, soit plus de 60 % des 5,9 % annuels du contrat, environ 1,5 pb par jour ([Liberty Street Economics, juillet 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)).

Le mécanisme est un stock à écouler. Après des ventes en fin de séance et des déséquilibres d'ordres négatifs à la clôture, les teneurs de marché portent un risque d'inventaire. Ils le soldent quand l'Europe ouvre. Les ventes produisent des « rebonds de nuit robustes ». Les grands déséquilibres positifs, eux, ne sont suivis que de rendements plats ou négatifs : il n'existe donc pas de vente symétrique à jouer ([RFS 2023](https://academic.oup.com/rfs/article-abstract/36/9/3502/7076616)).

Même dans l'échantillon, la stratégie n'a jamais payé ses frais. Son Sharpe était de 1,1 avant frais, mais selon les auteurs, « avec les frais, la dérive n'est pas rentable en pratique ». Élargie à 1 h 30 - 3 h 30, elle donne un Sharpe de 1,3 avant frais et **0,3 après** ([version acceptée de l'article](https://research-api.cbs.dk/ws/portalfiles/portal/101311522/nina_boyarchenko_et_al_the_overnight_drift_acceptedversion.pdf)).

### Puis le gain brut a disparu après 2021

Selon ses auteurs, l'heure de 2 h à 3 h « a fait en moyenne presque zéro depuis 2021 ». Un extrait étend ce constat aux E-mini Nasdaq-100 et Dow, mais la phrase n'a pas pu être retrouvée une seconde fois. Les auteurs l'attribuent à la compression des déséquilibres : **l'écart-type des déséquilibres de fin de séance est passé de 6,5 % à 2,9 %**, et les journées extrêmes sont devenues rares. La volatilité et la liquidité, elles, n'ont guère changé. Les fonds NightShares, lancés en 2022 pour capter la nuit, ont fermé environ quatorze mois plus tard ([Liberty Street Economics, juillet 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/) ; [Fed in Print](https://fedinprint.org/item/fednls/103479)). Les auteurs prédisent que la dérive reviendra dans la même heure si la dispersion des déséquilibres retrouve son niveau d'avant 2020.

Les frais, eux, ne sont plus l'obstacle. Vers 1 000 à 2 000 points d'indice (1998-2012), un tick du ES coûtait 1,3 à 2,5 pb, autant que la dérive. Vers 6 000 points, il ne coûte que 0,4 pb. C'est le gain brut qui manque.

### La fenêtre élargie de Bondarenko et Muravyev n'a pas été retestée

Bondarenko et Muravyev élargissent le constat, sur les transactions du E-mini de 2004 à 2018. **Quatre heures autour de la clôture asiatique et de l'ouverture européenne font toute la hausse moyenne du marché, avec un Sharpe de 1,6 qui « reste élevé après frais ».** Les vingt autres heures donnent un « zéro bruité ». L'incertitude lue dans les futures sur le VIX monte pendant la nuit et retombe à l'ouverture européenne. L'effet était plus fort pendant le COVID ([JFQA 2023](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3)). La version de 2020 annonçait un Sharpe de 1,2 après frais et un R² hors échantillon élevé ([Northern Finance Association](https://portal.northernfinanceassociation.org/viewp.php?n=2240010836)). Le communiqué de l'université place la fenêtre de 23 h 30 à 3 h 30 ([Michigan State University](https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/)).

Ce « hors échantillon » est très probablement un test récursif mené à l'intérieur de 2004-2018. Aucun test postérieur à la publication n'a été trouvé, et l'heure de 2 h à 3 h, au cœur de leur fenêtre, est nulle depuis 2021. Un compte qui doit sortir à 3 h n'en garderait de toute façon que trois heures et demie.

### Ce que le projet a déjà fermé

Le projet a déjà rejeté les formes directes de ces deux articles : l'achat de 18 h à 9 h 30 (NQ : t 1,74), les 173 règles de la réouverture de 18 h, et l'achat des indices à l'ouverture de Francfort, avec ou sans baisse de la veille. La seule trace de l'idée de Boyarchenko est un rebond du NQ de 18 h à 19 h après une dernière heure en baisse, qui fait +0,77 pb avant frais, trois fois moins que les frais (`asie/README.md`). Une seule partie n'a jamais été isolée, de 23 h 30 à 2 h dans la fenêtre de Bondarenko et Muravyev ; elle mérite un contrôle bon marché sur MNQ et MES, pas le statut de piste, car aucune fenêtre inconditionnelle de la nuit américaine n'a de gain documenté après 2020. Il faut enfin compter avec la minceur du marché : entre la nuit asiatique et la séance américaine, le volume du ES est multiplié par plus de cinquante ([Andersen, Bondarenko, Kyle, Obizhaeva](https://pages.nes.ru/aobizhaeva/ABKO-intradayinv.pdf)), si bien que la nuit, le glissement d'un ordre stop compte plus que l'écart affiché.

## Le fixing de Tokyo rapporte moins qu'un aller-retour sur 6J

### Un flux réel mais petit

Le flux du fixing est réel et bien documenté. **Le dollar monte avant les fixings de change et rebaisse après, ce qui dessine un « W » sur 24 heures.** Le constat vaut pour les neuf devises les plus échangées, sur 21 ans. Les banques intermédient une demande de dollars inconditionnelle et se font payer le risque d'inventaire ([Krohn, Mueller, Whelan, Journal of Finance 2024](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306)). Le fixing de Tokyo, à 9 h 55 heure de Tokyo, tombe à 19 h 55 EST ou 20 h 55 EDT. Le « W » se décale d'environ une heure entre le printemps et l'automne ([UNSW BusinessThink](https://www.businessthink.unsw.edu.au/articles/forex-market-patterns-currency-fixing-times-us-dollar-demand)).

L'effet est petit et ne survit pas aux frais. Sur 1999-2019, il vaut **environ 2,5 pb** pour le portefeuille du dollar, dans la montée vers les fixings de Tokyo et de Francfort ([version de travail de 2022](https://www.wu.ac.at/fileadmin/wu/d/ri/isk/VSFX_2022/Paper/Session_III_1a_Krohn__foreign_Exchange_Fixings_Returns_Around_The_Clock_0712.pdf)), soit environ 3,75 pips de USD/JPY à 150. Avec les frais complets déduits des cotations indicatives, les Sharpe deviennent négatifs. Le retournement de Tokyo, « nettement plus petit », perdait même au début de l'échantillon ([Banque du Canada, 2021](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf)). Les fenêtres longues gardaient un Sharpe de 0,5 à 0,8 après frais. Mais les auteurs jugent « presque impossible » de gagner à court terme en tradant le fixing ([AEA 2020](https://www.aeaweb.org/conference/2020/preliminary/paper/2dedYfDH)).

### Le gotobi n'a pas de preuve récente solide

Ito et Yamada décrivent ce qui est propre à Tokyo : les banques y fixent elles-mêmes le cours, biaisé vers un dollar fort. Autour de 9 h 55, les déséquilibres d'ordres sont positifs « presque tous les jours, mais seulement pour USD/JPY », sur des données de 1999 à 2013 ([Journal of International Economics 2017](https://ideas.repec.org/a/eee/inecon/v109y2017icp214-234.html) ; [NBER 2015](https://www.nber.org/papers/w21518)).

Le gotobi amplifie ce flux les 5, 10, 15, 20 et 25 du mois, et en fin de mois. Il ne repose que sur une prépublication portant sur 2018-2020, dont les résultats chiffrés n'ont pas été vus ([Bessho, Sugimoto, Suzuki 2023](https://arxiv.org/abs/2301.13204)).

Après 2020, on ne trouve plus que des praticiens, et ils se contredisent : +4,54 pips bruts par trade sur 2006-2025 ([Alpha in Academia](https://www.alphainacademia.com/p/can-you-beat-the-market-by-trading)), deux fenêtres d'entrée sur trois mortes hors échantillon ([ForexFactory](https://www.forexfactory.com/thread/1407332-gotobi-tokyo-fix-anomaly-7-years-of-usdjpy-tick)), et un même dépôt GitHub résumé tantôt à +3,18 pips nets, tantôt à −0,137 R après écart sur la période réservée de 2024-2026 ([GitHub](https://github.com/prathamesh-git9/gotobi-fx-bot)).

### Sur la CME, ces quelques pips ne passent pas

Un aller-retour coûte environ 3 pips sur 6J. Sur le micro yen MJY, dont le tick vaut 2,25 pips à 150, il en coûte environ 8. Le gain net attendu est donc au mieux nul sur 6J, et négatif sur MJY. Le projet l'a mesuré : les effets du fixing existent, mais ils sont 2 à 3 fois plus petits que les frais, et le gotobi échoue au coffre 2023-2026 (`asie/README.md`).

Une devise se déprécie aussi pendant ses propres heures ouvrables : c'est documenté sur 1993-2005, puis relié au flux d'ordres ([Ranaldo, JBF 2009](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=960209) ; [Breedon, Ranaldo, JMCB 2013](https://onlinelibrary.wiley.com/doi/abs/10.1111/jmcb.12032)). C'est très probablement le même flux que celui du fixing : les résidents achètent des devises étrangères le matin.

Pour le dollar australien, la séance de Sydney n'affiche qu'un rendement minime, avec 50 % de hausses ([extrait du tableau](https://www.researchgate.net/publication/228742460_Intraday_Patterns_in_FX_Returns_and_Order_Flow)). C'est bien trop peu pour un M6A, dont le tick vaut une fois et demie l'écart moyen du 6A. Les ouvertures de Tokyo et de l'Australie font monter la volatilité du change de plus de 20 % ([arXiv 2024](https://arxiv.org/pdf/2411.16244)), mais sans lui donner de sens.

### Les statistiques chinoises demandent le consensus

Le PMI officiel chinois sort à 9 h 30 à Pékin (20 h 30 EST, 21 h 30 EDT), à la minute où ouvrent Shanghai et Hong Kong ([investingLive](https://investinglive.com/news/economic-calendar-in-asia-monday-june-30-2025-china-official-pmis-for-june-20250629)). Ces chiffres font bouger les marchés. De 2009 à 2013, les annonces chinoises liées à l'industrie font bouger les futures d'indices mondiaux, l'énergie, les métaux industriels et les devises des matières premières. Celles sur la consommation, non ([Baum, Kurov, Wolfe, JIMF 2015](https://ideas.repec.org/a/eee/jimfin/v59y2015icp100-122.html)). La réaction du dollar australien a grandi de 2000 à 2016 ([RBA 2016](https://www.rba.gov.au/publications/bulletin/2016/dec/6.html)). Une surprise de 1 % sur la production industrielle fait environ +21 pb sur les actions chinoises et +3 pb en Asie-Pacifique ([FMI 2025](https://www.imf.org/-/media/files/publications/wp/2025/english/wpiea2025133-print-pdf.pdf)).

Mais le sens de la réaction dépend de l'écart au consensus. Le projet n'a pas l'historique des consensus : ce n'est donc pas une anomalie horaire, au mieux un filtre de volatilité. Bulenox autorise d'ailleurs le trading pendant les annonces ([FAQ Bulenox](https://bulenox.com/faq)).

## L'or monte en Asie depuis 2024, mais pas sur les vrais prix MGC

### Le prix de l'or se forme à New York

Les études revues ne placent pas la formation du prix de l'or à Shanghai. Les futures de New York la mènent sur cinq fuseaux horaires, avec **56 % de part d'information** ([IRFA 2021](https://www.sciencedirect.com/science/article/abs/pii/S1057521921002209)). Pendant les heures asiatiques, Shanghai (SHFE) ne pèse qu'environ 15 %, contre 47 % pour le COMEX et 24 % pour Londres ([IDEAS](https://ideas.repec.org/a/eee/finana/v78y2021ics1057521921002209.html)). Shanghai a ouvert une séance de nuit, qui chevauche la journée américaine, et elle a même réduit la part chinoise ([Jiang, Kellard, Liu, JFM 2020](https://econpapers.repec.org/RePEc:wly:jfutmk:v:40:y:2020:i:10:p:1486-1507)).

La seule étude revue des rendements du COMEX par séance couvre 1985-2012. Elle trouve des rendements de « nuit » significativement positifs et des rendements de jour négatifs. Mais sa « nuit » mêle Asie et Londres, l'asymétrie « s'est beaucoup affaiblie », et les auteurs l'attribuent à un prix « trop haut à l'ouverture » des marchés ([Blose, Gondhalekar, Kort 2018](https://ideas.repec.org/a/spr/jecfin/v42y2018i3d10.1007_s12197-017-9403-0.html)). Une étude de 2026 garde une moyenne de nuit positive pour l'ETF GLD après correction des tests multiples, sans résultat après frais visible ([MDPI Commodities 2026](https://www.mdpi.com/2813-2432/5/4/26)).

### Le bid asiatique est récent et irrégulier

Le « bid asiatique » récent est mieux chiffré, mais moins solide. Une prépublication d'août 2026 trouve que depuis le 22 juillet 2024, **les heures asiatiques (0 h - 8 h UTC, soit 19 h - 3 h EST) ont fait 77,2 % de la hausse cumulée de l'or**, qui a pris 81 % sur la période. Le momentum de court terme se prolonge dans la séance asiatique (autocorrélation de +0,13). Celui de la séance américaine, lui, ne survit pas aux frais ([Wei, SSRN 2026](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7257240)).

Le World Gold Council note que les replis se font surtout aux heures américaines, et les rebonds aux heures asiatiques ([WGC, juillet 2026](https://www.gold.org/goldhub/research/gold-mid-year-outlook-2026)). Des données de Morgan Stanley citées par Saxo montrent, sur quatre semaines, −5,9 % pendant les heures de la corbeille américaine et +14,7 % en dehors. Le bid a disparu pendant la fermeture chinoise du 1er mai 2025 ([Saxo](https://www.home.saxo/content/articles/commodities/gold-corrects-sharply-from-record-highs-as-chinese-demand-pauses-01052025)).

Mais en 2026, jusqu'à la mi-novembre, l'Asie ne fait que **+3,4 %, contre −28,1 % aux heures américaines**, sans constance d'un mois à l'autre ([Forex.com](https://www.forex.com/en-us/news-and-analysis/gold-outlook-asia-buys-the-dip-us-hammers-the-rip/)). Cela fait environ 1,5 pb par séance asiatique, pour un aller-retour MGC d'environ 0,9 pb.

### Le projet a déjà tranché sur la forme simple

L'or acheté hors des heures de New York a été rejeté. L'or acheté à 18 h et revendu à 23 h 30 passait sur les cotations HistData (t 3,49 sur 2023-2026), puis a échoué sur 474 soirs de vrais MGC (t 0,95). L'essentiel du gain tenait dans les cinq premières minutes : le prix acheteur remonte quand l'écart se resserre, sans que personne ait pu acheter à ce prix (`asie/README.md`). Les chiffres de 2026 cités par la presse reposent probablement sur des barres horaires du comptant, exposées au même piège.

Ce qui reste n'est pas une stratégie mais un test de mécanisme. Si le bid vient de la demande chinoise, il doit disparaître quand Shanghai est fermé : au Nouvel An lunaire, le 1er mai, pendant la semaine dorée. Si un flux réel apparaît, le MGC est le contrat où il coûterait le moins : 42 % de son volume se traite pendant les heures asiatiques de la CME ([CME OpenMarkets 2025](https://cmegroup.com/openmarkets/metals/2025/Asias-Growing-Gold-Demand-Fuels-Surging-Derivatives-Market.html)). Aucune étude ne teste si la prime de Shanghai prédit le COMEX.

## La Chine documente un momentum que la CME ne permet pas de jouer

### La référence américaine s'est éteinte après publication

La référence est l'article de Gao, Han, Li et Zhou, sur le SPY de 1993 à 2013. La première demi-heure, mesurée depuis la clôture de la veille, y prédit la dernière, avec un R² de 1,6 à 2 % selon les versions (1,2 % hors échantillon). La stratégie de timing affichait un Sharpe de 1,08, contre 0,29 pour l'achat simple, et environ 6,5 % par an, soit à peine 2,6 pb par jour ([JFE 2018](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414) ; [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/)).

Aux États-Unis, l'effet s'est éteint après publication. Une réplication indépendante trouve une pente de 0,003 (t 0,20) sur 2013-2019 ([Temperance Capital](https://temperancecapital.substack.com/p/market-intraday-momentum-replicates)). Le projet l'a rejeté sur les futures américains à la porte 2 (p = 2,8 %, 1 % exigé) (`rea/PISTES.md`).

### La Chine est l'endroit où ce momentum a été le plus étudié

Dans quatre futures de matières premières chinois (cuivre, acier, soja, tourteau de soja), la première demi-heure prédit la dernière, surtout dans les métaux après une première séance agitée ([Jin, Kearney, Li, Yang, JFM 2020](https://onlinelibrary.wiley.com/doi/10.1002/fut.22084)). L'effet existe aussi dans les futures sur indices ([Li et al., FRL 2020](https://ideas.repec.org/a/eee/finlet/v35y2020ics1544612319304337.html)). Dans les actions, les première et septième demi-heures prédisent la dernière, dans et hors échantillon ([Economic Modelling 2019](https://www.sciencedirect.com/science/article/abs/pii/S0264999318306692)). Sur le CSI 300 et son ETF, de 2012 à 2017, le momentum s'accompagne d'un retournement à la deuxième demi-heure ([FRL 2019](https://www.sciencedirect.com/science/article/abs/pii/S1544612318307414)).

Ces résultats ont trois limites. Aucun ne donne de résultat après frais. Leurs échantillons traversent les restrictions de 2015-2019 sur les futures d'indices, quand les dépôts exigés sont montés jusqu'à 40 % de la valeur des contrats ([FIA](https://www.fia.org/marketvoice/articles/2019-shaping-be-big-year-chinese-equity-index-futures)). Enfin, les travaux plus récents trouvent autre chose : des retournements dans les futures de matières premières sur 2017-2022 ([PBFJ 2024](https://www.sciencedirect.com/science/article/abs/pii/S0927538X24002865)), et un prédicteur passé à la séance de nuit pour l'or et l'argent de Shanghai ([Ma et al., GFJ 2025](https://www.sciencedirect.com/science/article/abs/pii/S1044028325000110)).

Le rendement de nuit des actions chinoises est même négatif. Qiao et Dam l'attribuent à la règle T+1, qui interdit de revendre le jour de l'achat ; ils en estiment le coût moyen à 14 pb ([JFM 2020](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3418356)). Aucune étude ne teste ce momentum à Hong Kong, qui n'en montre aucun dans l'étude Asie-Pacifique ([PBFJ 2023](https://www.sciencedirect.com/science/article/pii/S0927538X2300152X)). L'Australie n'en montre pas non plus ([PBFJ 2021](https://sciencedirect.com/science/article/pii/S0927538X21000068)).

### Rien de tout cela ne se trade à la CME

Le CSI 300, l'A50, le Hang Seng et le SPI 200 ne sont pas cotés à la CME. Le E-mini FTSE China 50 y a été suspendu le 23 novembre 2020 ([CME SER-8670](https://www.cmegroup.com/notices/ser/2020/10/SER-8670.html)), et son statut actuel n'est pas confirmé. Aucune étude ne montre que la dernière demi-heure chinoise (1 h 30 - 2 h EST, 2 h 30 - 3 h EDT) se transmet au MES, au MNQ, au M6A ou au cuivre.

L'ouverture de Hong Kong et de Shanghai (9 h 30, soit 20 h 30 EST ou 21 h 30 EDT) n'a fait l'objet d'aucune étude d'effet sur les futures de la CME. L'information circule surtout des États-Unis vers la Chine ([Economic Modelling 2015](https://www.sciencedirect.com/science/article/abs/pii/S0264999315003211)). La même minute réunit l'ouverture des deux bourses, celle des futures CSI 300 et, certains jours, le PMI officiel : un « effet d'ouverture » y est impossible à isoler. Le projet a d'ailleurs rejeté la cassure de l'ouverture de Hong Kong sur le NQ, le ES, l'or et les devises.

Le pétrole n'offre pas davantage. Aucune dérive horaire du WTI n'est documentée. Le brut de Shanghai se comporte en marché « régional » pendant sa séance de jour, qui tombe dans la fenêtre ([Ji, Zhang, Zhao 2021](https://link.springer.com/article/10.1007/s10479-021-04097-x)). Son retournement intraday tient aux annonces de stocks ([Wen, Wang, Zhang 2021](https://ideas.repec.org/a/eee/ecmode/v96y2021icp209-219.html)). Et un aller-retour MCL coûte environ 5 pb.

## Le Nikkei réunit les seules preuves récentes encore intactes

### Trois sources pointent vers un momentum de fin de séance au Japon

L'étude des ETF d'Asie-Pacifique trouve que le momentum de la première à la dernière demi-heure est « surtout visible en Chine et au Japon ». Il est absent à Hong Kong et à Singapour, et faible en Corée. **Pendant le COVID, il n'a tenu qu'au Japon** ([Limkriangkrai, Chai, Zheng, PBFJ 2023](https://www.sciencedirect.com/science/article/pii/S0927538X2300152X)). L'échantillon, l'ETF japonais utilisé et un éventuel test des frais n'ont pas pu être lus.

L'étude des seize marchés développés trouve un momentum significatif dans douze d'entre eux, plus fort quand la liquidité est faible et la volatilité forte ([Li, Sakkas, Urquhart, Journal of Financial Markets 2022](https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html)). Mais sa version de travail signale un problème de données pour l'Australie et le Japon, écartés d'une partie de l'analyse. L'annexe y décrit un momentum faible ([manuscrit accepté](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf)). Sur le Japon, ce papier est au mieux neutre.

Le résultat le plus solide est mondial. Dans plus de 60 contrats à terme sur actions, taux, matières premières et devises, de 1974 à 2020, **le rendement de la journée jusqu'à 30 minutes de la clôture prédit les 30 dernières minutes « partout »**. L'effet se retourne ensuite les jours suivants. Les auteurs le relient à la couverture gamma des teneurs de marché d'options et aux ETF à levier ([Baltussen, Da, Lammers, Martens, JFE 2021](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403)). La présence d'un contrat Nikkei dans l'échantillon n'a pas pu être vérifiée.

### Les fonds à levier japonais donnent un mécanisme identifié

En 2016, la Banque du Japon décrivait des ménages qui investissaient de plus en plus par des fonds à levier. Ces fonds rééquilibrent leurs futures Nikkei près de la clôture, à partir de 15 h, l'heure de clôture du comptant à l'époque. **De 15 h 00 à 15 h 15, les futures avaient tendance à bouger dans le sens pris par le Nikkei jusqu'à 15 h.** Cette demande suit le marché, mais la BOJ la jugeait petite par rapport au volume des futures ([BOJ Review 2016-E-1](https://www.boj.or.jp/en/research/wps_rev/rev_2016/data/rev16e01.pdf)).

La raison est arithmétique. Pour garder un levier L, un fonds doit traiter L(L−1) × r × actif net en futures, où r est la variation du jour. Les fonds à levier comme les fonds inverses achètent donc tous après une hausse et vendent tous après une baisse. Un courtier japonais en donne l'exemple : un fonds 2x de 10 milliards de yens rachète 2 milliards de futures après une hausse de 10 % ([Matsui](https://www.matsui.co.jp/fund/column/bull-bear/)).

Le NEXT FUNDS 1570 réplique 2 fois le Nikkei par des futures ([NEXT FUNDS](https://nextfunds.jp/en/lineup/1570/)). Il pesait environ 430 à 457 milliards de yens en 2024-2025 ([dépôt JPX](https://www2.jpx.co.jp/disc/15700/140120250701505507.pdf)). Cela fait environ 9 milliards de yens de futures par point de pourcentage de variation du Nikkei, soit 60 millions de dollars, ou 240 NKD à 50 000 points. C'est peu de chose, sauf les jours de forte variation. Aux États-Unis, une hausse d'un écart-type des flux de rééquilibrage des ETF à levier ajoute 430 % du rendement moyen de la dernière demi-heure ([Mathis, Moerke 2022](https://wp.lancs.ac.uk/fofi2022/files/2022/08/FoFI-2022-027-Mathis-Moerke.pdf)).

### L'ouverture de Tokyo sur-réagit à la séance américaine

Les rendements de journée à Tokyo sont corrélés aux rendements de nuit de New York. On ne trouve pas de débordement décalé significatif, sauf de New York vers Tokyo après le krach de 1987 ([Lin, Engle, Ito, RFS 1994](https://www.nber.org/papers/w3911)). La hausse « nocturne » du Nikkei de 1986-1998 tenait aux ouvertures figées du comptant ([Japan and the World Economy](https://www.sciencedirect.com/science/article/abs/pii/S092214250200049X)). Le NKD, coté toute la nuit, ne permet pas de capter cet effet.

Une étude de 2026 sur les futures du Nikkei trouve qu'**après une séance plus haute du S&P 500, ces futures rapportent moins dans les 30 premières minutes de la séance japonaise, et plus dans les 30 minutes avant la clôture** ([Finance Research Open 2026](https://www.sciencedirect.com/science/article/pii/S3050700626000204)). Les auteurs expliquent le retournement du début par une sur-réaction des traders non informés, corrigée par l'arbitrage. Ils attribuent le momentum de la fin à des investisseurs qui rééquilibrent à des fréquences différentes. Les retournements forts y sont moins probables en crise. Les auteurs, l'échantillon et les tailles d'effet de cette étude n'ont pas pu être lus (preuve C).

Une autre étude trouve un momentum « croisé » : la dernière demi-heure américaine prédit la première demi-heure étrangère, avec un gain positif après frais ([Xu et al., JIFMIM 2025](https://www.sciencedirect.com/science/article/abs/pii/S1042443125001295)). Mais elle porte sur des indices au comptant. Leur première demi-heure contient l'écart de la nuit, que les futures ont déjà absorbé : ce gain n'est pas accessible sur NKD.

### Deux changements japonais à ne pas confondre avec ces pistes

**La fin des achats d'ETF de la BOJ.** La règle « matinée faible, achats de la BOJ l'après-midi » passait ses ordres pendant la pause de midi, et a fait monter les rendements de midi ([Fukui, Yagasaki, ESRI 2023](https://www.esri.cao.go.jp/en/esri/content/e_dis376.pdf)). Elle était déjà anticipée : le volume des futures montait à midi « sans presque aucun mouvement de prix » ([Ko, FRL 2026](https://www.sciencedirect.com/science/article/abs/pii/S1544612325026704)). La BOJ a cessé tout achat le 19 mars 2024 ([BOJ](https://www.boj.or.jp/en/mopo/measures/term_cond/yoryo85.htm)). Elle vend depuis janvier 2026, à 330 milliards de yens par an ([Jiji via Adnkronos](https://english.adnkronos.com/2026/02/03/boj-begins-unloading-etfs-in-jan/)), soit environ 1,3 milliard par jour : un flux sans commune mesure.

**La réforme de la clôture.** Depuis le 5 novembre 2024, la Bourse de Tokyo ferme à 15 h 30, avec une enchère de clôture ([JPX](https://www.jpx.co.jp/english/corporate/news/news-releases/1030/20241105-01.html)). Selon le projet de JPX, la séance de jour des futures d'Osaka se termine par une enchère à 15 h 45 ([consultation JPX](https://www.jpx.co.jp/rules-participants/public-comment/detail/d8/cg27su00000068h0-att/jr4eth00000027c9.pdf)). Les rééquilibrages peuvent désormais passer dans ces enchères. Aucune étude ne dit si la dérive d'avant-clôture a rétréci depuis.

### Le MNK, à condition que Bulenox l'ouvre

Pour un compte Bulenox, le contrat adapté est le Micro Nikkei en dollars (MNK), lancé le 28 octobre 2024. Il vaut 0,50 $ par point d'indice, avec un tick de 5 points (2,50 $). Il cote du dimanche au vendredi, de 18 h à 17 h (New York), avec une pause d'une heure ([CME](https://www.cmegroup.com/markets/equities/international-indices/micro-nikkei-usd.contractSpecs.html)). Le NKD (5 $ par point, tick de 25 $, [CME](https://www.cmegroup.com/articles/2024/equity-trading-opportunities-in-nikkei-225-futures-at-cme-group.html)) représente 250 000 à 315 000 $ de nominal, trop pour un compte de 50 000 $. Le NIY et le Micro Nikkei en yens règlent leurs gains en yens.

La CME indique que près de 75 % des transactions sur ses futures Nikkei ont lieu hors des heures du comptant de Tokyo ([communiqué CME 2024](https://www.cmegroup.com/media-room/press-releases/2024/10/01/cme_group_to_launchyen-andusdollar-denominatedmicronikkeifutures.html)). Pendant la séance de Tokyo, c'est Osaka qui fait le prix. La profondeur du MNK entre 1 h et 3 h du matin (New York) est inconnue.

Deux vérifications s'imposent avant tout test. La première porte sur Bulenox. Sa FAQ annonce 41 contrats et cite le ES, le NQ, le YM, le RTY, le EMD, le CL, le NG, le RB, le GC, le SI, le HG, le PL, le 6E, le 6B et le 6J, mais pas le Nikkei ([FAQ Bulenox](https://bulenox.com/faq)). La liste Yahoo du projet, elle aussi de 41 contrats, ne le contient pas non plus. Il faut demander à Bulenox si le MNK est ouvert, et à quelle commission.

La seconde porte sur les données. Une mesure faite pour ce rapport sur les fichiers HistData du Nikkei (`donnees_libres/histdata_5min`, branche `claude/affectionate-turing-tnz0mn`) trouve une barre à 9 h 00, 9 h 30 et 15 h 00 (heure de Tokyo) pour 97 à 100 % des jours de semaine, chaque année de 2012 à 2026 ; la couverture tombe à 84-94 % à 15 h 30 en 2012-2014, et la volatilité culmine dans l'heure de 9 h. Ce sont des cotations au prix acheteur. Mais les fenêtres proposées tombent en pleine séance d'Osaka, loin du resserrement de l'écart de 18 h qui a trompé le projet sur l'or. Le projet n'a en revanche aucun vrai prix de futures Nikkei.

## Trois règles à figer avant de lancer la machine 9

Les trois règles suivantes sont fixées avant tout calcul, avec les conventions de `asie/machine9.py`. Ce fichier gère déjà les jours de Bourse de Tokyo et le changement d'heure de clôture. Les trois règles partagent les conventions suivantes.

| Convention | Valeur |
|---|---|
| C | heure de clôture de la Bourse de Tokyo : 15 h 00 avant le 5 novembre 2024, 15 h 30 depuis |
| C + 15 minutes | fin de la séance de jour des futures d'Osaka : 15 h 15 avant la réforme ; 15 h 45 après, selon le projet de JPX (à confirmer) |
| Prix | ouverture de la barre de 5 minutes qui commence à l'heure dite ; ni stop ni seuil |
| Frais décisifs | ceux déjà codés pour le Nikkei : 2,8 pb par aller-retour (un MNK à 50 000 points) |
| Frais pour information | 14 points d'indice (le vrai coût d'un MNK à chaque date), puis frais doublés |
| Horaires Bulenox | toutes les positions sont fermées avant 3 h (New York) ; la journée de trading commence à 18 h, et le compte doit être à plat avant 16 h 59 ([Bulenox](https://bulenox.com/help-center/qualification)) |

| | Piste 1 : fin de séance d'Osaka dans le sens de la journée | Piste 2 : ouverture de Tokyo contre le S&P 500 | Piste 3 : zone de bruit à Tokyo |
|---|---|---|---|
| Appui | Baltussen et al. 2021 (A) ; BOJ 2016 (B) ; Limkriangkrai et al. 2023 (B) | Finance Research Open 2026 (C), cohérent avec Lin, Engle, Ito 1994 (A) | règle du bot, validée par l'usine sur le NQ ; mécanisme de Baltussen et al. ; aucune étude au Japon |
| Signal | R = variation du Nikkei de C + 15 min la veille à C − 15 min le jour même | S = variation du S&P 500 de 16 h à 16 h (New York), sur la dernière séance américaine finie avant 9 h à Tokyo | bande de bruit autour de l'ouverture de 9 h 00 et de la clôture de la veille |
| Trade | achat si R > 0, vente si R < 0, de C − 15 min à C + 15 min | vente si S > 0, achat si S < 0, de 9 h 00 à 9 h 30 (Tokyo) | contrôle toutes les 30 min, de 9 h 30 à C − 30 min ; achat au-dessus de la bande, vente au-dessous ; tout fermé à C |
| Heures de New York | avant la réforme : 0 h 45 - 1 h 15 EST (1 h 45 - 2 h 15 EDT) ; après : 1 h 15 - 1 h 45 EST (2 h 15 - 2 h 45 EDT) | 19 h 00 - 19 h 30 EST (20 h 00 - 20 h 30 EDT) | de 19 h EST (20 h EDT) à 1 h ou 1 h 30 EST (2 h ou 2 h 30 EDT) |
| Variante déclarée d'avance | signal de Gao et al. : variation de C + 15 min la veille à 9 h 30 | même S, dans le même sens, de C − 15 min à C + 15 min | aucune |
| Données | HistData JPXJPY, 5 min, 2012 → octobre 2026 | JPXJPY et HistData S&P 500 (usa500idxusd) | JPXJPY |

### La piste 1 traduit le plus directement les preuves

Sa fenêtre est la dernière demi-heure de la séance de jour des futures d'Osaka, celle de Baltussen et al. Elle contient exactement la fenêtre de 15 h 00 à 15 h 15 où la BOJ a vu les futures suivre la journée. Dans `machine9.py`, la règle s'écrit `entree ("TSE", -15)`, `sortie ("TSE", 15)`, `signal (("veille", ("TSE", 15)), ("TSE", -15))`, avec un sens de continuation.

Le mécanisme donne deux prédictions, à lire pour information sans en faire des critères de décision. D'abord, le gain doit croître avec |R|, puisque le rééquilibrage est proportionnel à la variation du jour. Ensuite, la période postérieure au 5 novembre 2024 doit être lue à part, puisque l'enchère de clôture a pu absorber le flux.

La barre réaliste est celle de Gao et al. aux États-Unis : environ 2,6 pb bruts par jour, de l'ordre des frais d'un MNK. Il faut donc un effet japonais nettement plus fort que l'effet américain.

### La piste 2 joue le retournement de la première demi-heure de Tokyo

Elle ne lit que le sens de la séance américaine, et joue la moitié « retour » de l'article de 2026. Sa variante joue la moitié « momentum » du même article, sur la fenêtre de la piste 1.

La fenêtre de 9 h 00 à 9 h 30 a été fixée sans avoir pu lire la définition exacte de l'article, alors que les futures d'Osaka ouvrent à 8 h 45. Si le texte complet en donne une autre, il faut la corriger avant le calcul, jamais après. La règle demande aussi une petite extension de `jouer` dans `machine9.py`, pour lire le signal sur un autre marché que celui qu'on trade.

Une observation du projet plaide pour elle : les cassures de début de séance, à Tokyo comme à la réouverture de 18 h, se retournent plus souvent qu'elles ne continuent. Sa faiblesse est de reposer sur une seule source.

### La piste 3 transpose la zone de bruit à la séance « maison » du Nikkei

La zone de bruit du bot (Zarattini, Aziz, Barbon 2024) est la seule source de gain validée du projet : t de +3,88 sur 2014-2026, 12 années positives sur 13 (`rea/PISTES.md`). La machine 8 l'a jouée la nuit sur le NQ, le ES et l'or, et l'a vue perdre même avant frais : la nuit, un prix qui sort de sa bande revient au lieu de continuer (`asie/README.md`). Mais la nuit n'est pas la séance de ces actifs. Tokyo, de 9 h à 15 h 30, est celle du Nikkei. C'est là que vivent les couvertures des teneurs de marché d'options d'Osaka et les rééquilibrages des fonds à levier.

Les règles sont celles de la machine 8 (`asie/zone_nuit.py`), avec l'horloge de Tokyo.

| Élément | Règle de la piste 3 |
|---|---|
| Références | O = ouverture de la barre de 9 h 00 (Tokyo) ; C' = prix à la clôture de Tokyo de la veille |
| Bruit à l'heure h | moyenne, sur les 14 séances précédentes, de \|prix à h ÷ O − 1\| |
| Bande | largeur 1,0 (la bande plus large a été rejetée par l'usine) : haut = max(O, C') × (1 + bruit) ; bas = min(O, C') × (1 − bruit) |
| Prix moyen | moyenne des clôtures de 5 minutes depuis 9 h 00, faute de volume dans HistData |
| Contrôles | toutes les 30 minutes, de 9 h 30 à C − 30 min, pause de midi comprise (les futures cotent), au prix de clôture de la barre qui finit à l'heure du contrôle |
| Entrées | à plat : achat au-dessus du haut, vente sous le bas ; pas de nouvelle entrée au dernier contrôle |
| Sorties | achat soldé si le prix ≤ max(haut, prix moyen) ; vente soldée si le prix ≥ min(bas, prix moyen) ; tout fermé à l'ouverture de la barre de C |

### Le même tri pour les trois, puis les vrais prix

Les cinq règles (les trois pistes et les deux variantes) passent ensemble le tri des machines 7 et 8. L'exploration porte sur 2012-2022 : une règle y survit avec un t ≥ 2 après frais, un placebo de 1 000 tirages au hasard du sens de chaque trade battu à 95 %, un gain positif dans au moins 2 des 3 sous-périodes et le passage de Benjamini-Hochberg à 10 % sur les cinq règles. Le coffre, du 1er janvier 2023 au 2 octobre 2026, n'est ouvert qu'une seule fois et exige le seuil de Bonferroni et 3 années positives sur 4.

Une survivante devra ensuite passer l'épreuve des vrais prix, que le projet n'a pas pour le Nikkei. Il faudra d'abord ajouter le futures NKD de Yahoo (code NKD=F, s'il est disponible) au téléchargement, et comparer ses barres de 5 minutes sur 60 jours aux cotations HistData, comme pour l'or. Il faudra ensuite 3 à 4 semaines de MNK en papier avec `usine/rapprochement.py`, pour mesurer l'écart réel entre 1 h et 3 h du matin.

Si Bulenox n'ouvre pas le Nikkei, aucune des trois pistes n'a d'objet pour ce compte. Il ne resterait que le contrôle de Bondarenko et Muravyev sur MNQ et MES (achat de 23 h 30 à 3 h), dont l'heure centrale est pourtant nulle depuis 2021.

## Conclusion

Ce bilan change la question à poser. La nuit n'offre plus d'anomalie propre aux actifs américains : entre 18 h et 3 h, leurs mouvements sont des flux venus d'un autre fuseau ou des stocks que les teneurs de marché doivent écouler, qui s'éteignent quand le flux s'arrête ou se révèlent des artefacts de cotation, et le projet comme la littérature constatent que, hors de leur séance, le NQ, le ES et l'or reviennent au lieu de continuer. La seule séance « maison » que la fenêtre contient en entier, et que la CME rend accessible, est celle de Tokyo ; c'est la seule où les flux de couverture qui font fonctionner la zone de bruit à New York peuvent jouer pendant les heures où l'utilisateur trade. Un mécanisme identifié a de plus une vertu que les anomalies purement statistiques n'ont pas, puisqu'il dit à quoi ressemblerait un faux positif : si le gain de fin de séance vient du rééquilibrage, il doit grandir avec la variation du jour et suivre la clôture quand elle passe de 15 h à 15 h 30 en novembre 2024, et un gain resté collé à l'ancienne heure serait suspect, même s'il passait le coffre.

L'ordre des opérations compte autant que les règles. La vérification la moins chère est administrative : une réponse de Bulenox sur le MNK vaut plus que n'importe quel calcul, puisque toute la suite en dépend. Quant à la dérive de Boyarchenko et al., il ne faut pas la rejouer mais la surveiller comme un indicateur de régime : ses auteurs ont nommé la variable qui la ferait revenir, la dispersion des déséquilibres de clôture, que le projet peut suivre sans engager un dollar, par exemple à travers les déséquilibres publiés des enchères de clôture, pour rouvrir la piste le jour où elle retrouverait ses niveaux d'avant 2020.
