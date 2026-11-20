# Asian-session anomalies: China, Hong Kong and Australia, and how they spill over to CME futures (18:00–03:00 New York time)

**How to read these notes (verification status).** This session's network allowlist only covers Hugging Face and PyTorch hosts, so WebFetch could not open any source. These hosts were tried and blocked: pureadmin.qub.ac.uk, www.sciencedirect.com, www.imf.org, papers.ssrn.com and www.snb.ch. **I did not verify any item below by opening the source document.** Everything comes from search-engine results. The tags are:
- **[S-abs]**: the paper's own abstract, or its publisher, repository or author page, as the search results showed it. This is the closest I got to the source. I did not open the document, so a number could still be a summarizer error.
- **[S-sec]**: seen only in a third-party summary (blog, news, broker or prop-firm review) or in a search-engine synthesis that I could not tie to a specific paper.
- **[Calc]**: my own arithmetic (time-zone conversions).
- **"unverified background"**: something I knew before this session and did not confirm here. It is never used as a cited finding.

Evidence grades:
- **A**: peer-reviewed in a top finance or field journal (JF, JFE, RFS, J. Financial Markets, J. Futures Markets, JIMF, JMCB).
- **B**: another peer-reviewed journal, or official central-bank, IMF or NY Fed research.
- **C**: unreviewed working paper, preprint or conference draft.
- **D**: industry body or exchange publication (WGC, CME).
- **E**: practitioner, news or blog.

Time zones: Beijing and Hong Kong are UTC+8 with no daylight saving. Tokyo is UTC+9. Sydney is UTC+10 (AEST), or UTC+11 (AEDT) from early October to early April. New York is UTC−5 (EST) from early November to mid-March, and UTC−4 (EDT) otherwise.

## 1. Intraday momentum in China and Hong Kong: does the first half-hour predict the last half-hour, and does the overnight return predict the intraday return?

### Takeaway
Intraday time-series momentum is documented in China: the first (and/or seventh) half-hour predicts the last half-hour in commodity futures, in A-shares and the CSI 300, and in stock-index futures. Most samples end in 2017–2018, and no net-of-cost result was visible. I found no Hong Kong (Hang Seng) study, and Australia shows little or no effect. Evidence from 2020–2026 shows the effect weakening (US) or coexisting with reversals (Chinese commodities). Chinese cash-equity overnight returns are negative, attributed mainly to the T+1 rule, while T+0 index futures show overnight returns near zero or positive, so "overnight predicts intraday" depends on market structure. None of the underlying contracts is tradable on CME.

### Cited Findings
**US and global baseline (needed to judge the China results)**
- Gao, Han, Li & Zhou, "Market intraday momentum", JFE 129(2) 394–414 (2018). Data: SPY, 1993–2013. The first half-hour return, *measured from the previous day's close* (so overnight plus the first 30 minutes), predicts the last half-hour return. The same pattern appears in ten other heavily traded domestic and international ETFs. [A][S-abs] — [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:129:y:2018:i:2:p:394-414); [working-paper copy](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- Working-paper figures (I did not see the published numbers): predictive R² is 1.6%, or 2.6% with an added predictor or condition, and the out-of-sample R² is 1.2%. The timing strategy has a Sharpe ratio of 1.08, against 0.29 for buy-and-hold. The annual return is 6.67% in one version and 6.34% in an earlier one. [S-sec] — [Alpha Architect](https://alphaarchitect.com/2014/08/attention-prop-traders-the-first-half-hour-of-trading-predicts-the-last-half-hour/); [working-paper copy](https://c.mql5.com/forextsd/forum/173/intraday_momentum_-_the_first_half-hour_return_predicts_the_last_half-hour_return.pdf)
- Persistence in the US after publication: an independent replication finds a flat SPY slope in 2013–2019 (0.003, t = 0.20). It also finds that the average absolute last-half-hour move is small relative to plausible trading costs. [E][S-sec] — [Temperance Capital](https://temperancecapital.substack.com/p/market-intraday-momentum-replicates). A QuantConnect implementation had a lower Sharpe ratio than the S&P 500 over its test period. [E][S-sec] — [QuantConnect](https://www.quantconnect.com/learning/articles/investment-strategy-library/intraday-etf-momentum)
- Baltussen, Da, Lammers & Martens, "Hedging demand and market intraday momentum", JFE 142(1) 377–403 (2021). Data: more than 60 futures on equities, bonds, commodities and currencies, 1974–2020. The return over the rest of the day positively predicts the last 30 minutes. The effect is economically and statistically highly significant and reverses over the following days. The proposed mechanism is gamma hedging by option market makers and leveraged ETFs. The results for Asian index futures were not shown separately in what I saw. [A][S-abs] — [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)
- Li, Sakkas & Urquhart, "Intraday time series momentum: Global evidence and links to market characteristics", J. Financial Markets 57 (2022) 100619.
  - Data: high-frequency data on 16 developed markets.
  - Results: 12 of the 16 markets show statistically significant intraday momentum, in- and out-of-sample in most countries. The effect is stronger when liquidity is low, volatility is high and news arrives in discrete bursts. Global portfolios add gains.
  - I could not see whether Hong Kong or Australia is among the 12. [A][S-abs] — [IDEAS](https://ideas.repec.org/a/eee/finmar/v57y2022ics138641812100001x.html); [accepted version](https://centaur.reading.ac.uk/95566)
- A futures study that came up in search reports two findings. The last half-hour return negatively predicts the next overnight and intraday returns. Most intraday momentum and reversal strategies "may not be feasible after transactions costs, especially in bond and currency futures". [S-sec; I could not tie this to a specific paper — the result set included [Finance Research Letters vol. 58 (2023)](https://ideas.repec.org/a/eee/finlet/v58y2023ipas154461232300394x.html)]

**China: commodity futures, A-shares and index futures**
- Jin, Kearney, Li & Yang, "Intraday time-series momentum: Evidence from China", J. Futures Markets 40(4) 632–650 (2020). Data: four Chinese commodity futures (copper, steel, soybean, soybean meal).
  - The first half-hour return positively predicts the last half-hour return in all four.
  - In the metals, the effect is strongest after first sessions with high volume or volatility.
  - A timing strategy beats always-long and buy-and-hold benchmarks.
  - I did not see the coefficients, the sample period or how costs were treated. [A][S-abs] — [Wiley](https://onlinelibrary.wiley.com/doi/10.1002/fut.22084); [EconPapers](http://econpapers.repec.org/RePEc:wly:jfutmk:v:40:y:2020:i:4:p:632-650); [QUB record](https://pure.qub.ac.uk/en/publications/intraday-time-series-momentum-evidence-from-china)
- Li, Shen, Wang & Zhang, "Does intraday time-series momentum exist in Chinese stock index futures market?", Finance Research Letters 35 (2020). The abstract says the results hold across other index futures, other sample periods and both signs of the first-session return. I did not see the magnitudes. [B][S-abs] — [IDEAS](https://ideas.repec.org/a/eee/finlet/v35y2020ics1544612319304337.html); [EconBiz](https://www.econbiz.de/Record/does-intraday-time-series-momentum-exist-in-chinese-stock-index-futures-market/10012438384)
- A search synthesis made two further claims that I could not tie to a specific paper; treat both as unverified. [S-sec] — [result set](https://www.researchgate.net/publication/335769128_Does_Intraday_Time-Series_Momentum_Exist_in_Chinese_Stock_Index_Futures_Market)
  - For CSI 300 and CSI 500 index futures, the first half-hour after the open predicts the last half-hour before the close.
  - Another Chinese index-futures paper finds intraday momentum *insignificant*, but finds that option order imbalance in the first 10 minutes predicts index and index-futures returns for the rest of the day.
- "Intraday momentum and stock return predictability: Evidence from China", Economic Modelling (2019): the first and/or seventh (second-to-last) half-hour returns significantly predict the last half-hour, both in- and out-of-sample, in the Chinese stock market. [B][S-sec] — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0264999318306692)
- "Intraday momentum and reversal in Chinese stock market", Finance Research Letters (2019). Data: the CSI 300 and its ETF, 2012–2017. It finds last-hour momentum (the sixth or seventh half-hour predicts the next one) and a reversal in the second half-hour. [B][S-sec, attribution from the search synthesis] — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1544612318307414); [ResearchGate](https://www.researchgate.net/publication/332273151_Intraday_Momentum_and_Reversal_in_Chinese_Stock_Market)
- "Intraday momentum in Chinese commodity futures markets", Research in International Business and Finance: the first half-hour and the second-to-last half-hour predict the last half-hour. The effect grows with volatility, volume and trade size. Mechanisms proposed in this literature (attribution uncertain): late-informed trading by institutional and foreign investors, and noise trading. [B][S-sec] — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0275531919311328)
- "Is there an intraday reversal effect in commodity futures and options? Evidence from the Chinese market", Pacific-Basin Finance Journal (2024). Data: 2017–2022. It finds a significant intraday reversal. An overnight-plus-opening factor (ONFH) and an intraday factor (ROD) predict the last half-hour. [B][S-sec] — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0927538X24002865)
- "The 'night effect' of intraday trading: Evidence from Chinese gold and silver futures markets" (2025). The journal is probably Global Finance Journal, which I inferred from ISSN 1044-0283.
  - Data: 1-minute SHFE data.
  - Before night trading started, the first daytime half-hour predicted later returns. After it started, the first half-hour of the *night* session became the predictor.
  - The paper finds both momentum and reversal. [B][S-sec] — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1044028325000110)
- A lead I did not read: "Night trading momentum and determinants of predictability" (Zhou, AUT conference paper). [C] — [PDF](https://acfr.aut.ac.nz/__data/assets/pdf_file/0008/686816/4a-Z-Ivy-Zhou.pdf)

**Hong Kong and Australia**
- I found no study that tests whether the first half-hour predicts the last half-hour on the Hang Seng Index or HSI futures. Searches returned only daily market reports. These are anecdotes, such as a morning decline that continued into the afternoon on 20 Nov 2026, or morning rallies that faded. [E][S-sec] — [Futu midday review](https://news.futunn.com/en/post/1005131744/hong-kong-stock-market-midday-review-hang-seng-index-falls)
- "Market intraday momentum in Australia", Pacific-Basin Finance Journal (2021): there is little evidence of market intraday momentum in Australia. The first-half-hour coefficient is statistically insignificant. The daily number of trades matters for whether momentum forms. [B][S-sec] — [ScienceDirect](https://sciencedirect.com/science/article/pii/S0927538X21000068)

**Overnight versus intraday in China**
- Qiao & Dam, "The overnight return puzzle and the 'T+1' trading rule in Chinese stock markets", J. Financial Markets 50 (2020) 100534:
  - Overnight returns on Chinese stocks are on average statistically and economically significantly negative.
  - This holds across exchanges, share types and sample periods, and appears to be unique to China.
  - The average T+1 discount is estimated at 14 bp. [A][S-abs] — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3418356); [ResearchGate](https://www.researchgate.net/publication/338810937_The_overnight_return_puzzle_and_the_T1_trading_rule_in_Chinese_stock_markets)
- "Overnight returns under T+0 mechanisms, such as China's stock index futures, Hong Kong stocks, and major international indices, all have around 0 or positive overnight returns." [S-sec; this sentence may come from "T+1 trading mechanism causes negative overnight return", Economic Modelling] — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0264999319307023)
- Follow-up work:
  - Chinese stocks have strongly positive intraday returns, especially in the last 15 minutes. [B][S-sec] — [Frontiers in Energy Research 2021](https://www.frontiersin.org/journals/energy-research/articles/10.3389/fenrg.2021.807881/full)
  - A competing explanation is investor structure. [B][S-sec] — [JRFM (MDPI) 2022](https://www.mdpi.com/1911-8074/15/11/534)
  - Anomaly profits are concentrated at the open and the close, and are weaker in the last half-hour. [S-sec] — same result set ([Macquarie WP](https://research-management.mq.edu.au/ws/portalfiles/portal/397611310/397269748.pdf))
- Overnight spillovers among Chinese sector indices are larger than daytime spillovers (2011–2022). US intraday returns transmit to Asian markets through the Asian overnight return. [B][S-sec] — [Pacific-Basin Finance Journal 2024](https://www.sciencedirect.com/science/article/abs/pii/S0927538X24003378)

**Market-structure context that affects the costs and feasibility of CSI 300 futures strategies**
- In August–September 2015, CFFEX required everyone trading index futures, hedgers included, to raise deposits from 10% to 40% of contract value, and imposed very strict trading restrictions. [S-sec] — [FIA MarketVoice](https://www.fia.org/marketvoice/articles/2019-shaping-be-big-year-chinese-equity-index-futures)
- How the curbs were relaxed:
  - 2017: margins for non-hedging accounts on CSI 300 and SSE 50 futures fell from 40% to 20%; curbs were relaxed twice that year. [S-sec] — [Caixin Feb 2017](https://www.caixinglobal.com/2017-02-17/china-relaxes-curbs-on-stock-index-futures-trading-101056068.html)
  - December 2018: CSI 300 and SSE 50 margins fell from 15% to 10%, and CSI 500 margins from 30% to 15%. [S-sec] — [Caixin Dec 2018](https://www.caixinglobal.com/2018-12-03/china-further-rolls-back-curbs-on-trading-stock-index-futures-101354956.html)
  - April 2019: the CSI 500 margin fell from 15% to 12% and some fees were cut; CSI 300 stayed at 10%. [S-sec] — [Caixin Apr 2019](https://www.caixinglobal.com/2019-04-22/china-further-relaxes-curbs-on-tool-for-betting-against-stocks-101407176.html)
- CSI 300 futures volume reached 12.3 million contracts in H1 2019, up 365% year on year, largely because the 2015 curbs were unwound. [S-sec] — [FIA](https://www.fia.org/marketvoice/articles/2019-shaping-be-big-year-chinese-equity-index-futures)

### Inferences
- Most China intraday-momentum samples (roughly 2010–2018) span the 2015–2019 restriction regime: margins up to 40%, a collapse in volume, then recovery. Coefficients estimated in that period may not describe the market after 2019. The 2024–2025 papers on Chinese commodity and precious-metal futures find reversals and session-dependent predictors alongside momentum, so the sign of the effect depends on the regime and the session.
- None of the China papers I could see reports net-of-cost results. The only cost-aware evidence comes from outside China (the SPY replication and the cross-asset futures study), and it suggests that gross edges are small relative to costs. Treat "survives costs" as unproven.
- [Calc] Key Chinese and Hong Kong half-hours in New York time:

  | Half-hour | Local time | New York (EST) | New York (EDT) |
  |---|---|---|---|
  | China, first half-hour | 09:30–10:00 Beijing | 20:30–21:00 | 21:30–22:00 |
  | China, last half-hour | 14:30–15:00 Beijing | 01:30–02:00 | 02:30–03:00 |
  | Hong Kong, last half-hour | 15:30–16:00 HKT | 02:30–03:00 | 03:30–04:00 (outside the 18:00–03:00 window) |
- For a trader limited to CME, a CSI 300 or Hang Seng intraday-momentum signal could at best condition trades in MES, MNQ, M6A or MHG between about 01:30 and 03:00 ET. No study shows that the Chinese last-half-hour effect carries over to CME products, so this would need its own backtest.
- Qiao & Dam imply that an "overnight predicts intraday" signal built on Chinese cash indices partly captures a T+1 artefact rather than information. Using CSI 300 futures (T+0) as the reference avoids that bias.

### Gaps
- No intraday momentum study on the Hang Seng or HSI futures. No country-level breakdown for Hong Kong or Australia was visible in Li-Sakkas-Urquhart or Baltussen et al.
- No out-of-sample replication for CSI 300 or CSI 500 futures over 2020–2026. I did not see the coefficient sizes, sample periods or cost treatment of Jin et al. (2020) or Li et al. (2020).
- I could not verify the CFFEX fee for closing an intraday position, either in 2015–2019 or today. It is critical for any cost analysis.
- I could not confirm the authors of the Economic Modelling 2019, FRL 2019, RIBAF and PBFJ 2024 papers.

## 2. Effects of the Hong Kong and Shanghai cash opens (09:30 local = 20:30 EST / 21:30 EDT) on US index futures, gold and the AUD

### Takeaway
I found no study that treats the 09:30 Shanghai or Hong Kong open as a return or volatility event for E-mini or Micro equity futures, COMEX gold or AUD futures. The documented evidence is indirect:
- Information flows mainly from the US to China: US news is priced at the Chinese open.
- There is a contemporaneous link between US and Chinese index futures in each other's overnight returns.
- FX volatility jumps at the Tokyo and Australian openings.
- The USD rises into the Tokyo fix and falls afterwards.
- The best-known ES overnight anomaly, the drift at the European open (02:00–03:00 ET), disappeared in 2021–25.

### Cited Findings
- "Information transmission between U.S. and China index futures markets: An asymmetric DCC GARCH approach", Economic Modelling (2015): daytime moves in one market affect the other market's overnight return contemporaneously. The authors read this as foreign futures trading affecting the domestic open. [B][S-sec] — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0264999315003211)
- CSI 300 futures in extended hours: price discovery before the cash open reflects overnight US news (the US-to-China direction). [S-sec] — [ResearchGate](https://www.researchgate.net/publication/271065542_Information_Content_of_CSI_300_Index_Futures_during_Extended_Trading_Hours_Evidence_from_China)
- "Half-day trading and spillovers": US effects on Chinese stocks show up mainly in the Chinese morning session. [S-sec] — [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7887722/)
- Asian ADRs: intraday ADR returns reflect US news, while overnight returns are driven mainly by local Asian markets. [C][S-sec] — [arXiv 1611.03110](https://arxiv.org/pdf/1611.03110)
- The search synthesis concluded that spillovers from the US to China are the stronger and better-documented direction. It found no recent evidence that quantifies spillovers from China to Globex index futures. [S-sec]
- Anecdote (no causal evidence): on 20 Nov 2026 the CSI 300 and the Shanghai Composite fell 2.2% and 1.7% in an Asian-hours tech selloff, while US futures also fell. [E][S-sec] — [Investing.com](https://investing.com/news/stock-market-news/asia-stocks-slide-to-7mth-low-with-skorea-taiwan-worst-hit-by-ai-rout-5040572)
- SGX FTSE China A50 futures versus CSI 300 futures:
  - Using May–November 2011 data, CSI 300 futures dominate A50 futures in intraday price discovery and volatility transmission. [B][S-abs] — [Emerging Markets Finance & Trade 2013](https://www.tandfonline.com/doi/abs/10.2753/REE1540-496X4905S414)
  - Cao, Wang, Yap & Zhou (2016) say SGX index futures generally lead their home markets, but also report that CSI 300 futures dominate the A50. [C][S-sec] — [iFRoGS 2016](https://ifrogs.org/PDF/CONF_2016/Cao_Wang_Yap_Zhou_2016.pdf)
  - CSI 300 and CSI 500 futures lead the cash index by about 32 seconds on average. [C][S-sec] — [arXiv 2501.03171](https://arxiv.org/pdf/2501.03171)
- FX: seasonal FX volatility rises by more than 20% at the Tokyo and Australian openings. This comes from a general model, not an AUD-specific one. [C][S-sec] — [arXiv 2411.16244](https://arxiv.org/pdf/2411.16244)
- Krohn, Mueller & Whelan, "Foreign exchange fixings and returns around the clock", JF 79(1) 541–578 (2024):
  - The USD appreciates in the run-up to FX fixes and depreciates afterwards, giving a W-shaped 24-hour pattern.
  - This holds across the top nine traded currencies over 21 years. It is pervasive and highly significant, implying daily swings of more than USD 1bn.
  - Tokyo is the main fix in Asian hours. Returns around the Tokyo fix are positive in at least 70% of sample months (aggregated monthly).
  - The mechanism is inventory risk: dealers intermediate demand for USD at the fixes. [A][S-abs] — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306); [IDEAS](https://ideas.repec.org/a/bla/jfinan/v79y2024i1p541-578.html); [BoC WP 2021-48](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf)
  - The trade press puts the Tokyo fix at 9:55 am Tokyo time. [S-sec] — [UNSW BusinessThink](https://www.businessthink.unsw.edu.au/articles/forex-market-patterns-currency-fixing-times-us-dollar-demand)
- Boyarchenko, Larsen & Whelan, "The overnight drift", RFS 36(9) 3502–3547 (2023): over 1998–2019 the largest positive S&P 500 futures returns accrue between 02:00 and 03:00 ET, at the European open, averaging about 3.6% a year. The explanation is that dealers carry inventory risk after order imbalances at the US close. [A][S-abs] — [Liberty Street 2021](https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns); [NY Fed SR 917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- Persistence: "The Disappearing Overnight Drift" (same authors, Liberty Street, 1 Jul 2026) [B][S-abs] — [Liberty Street 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/); [FedInPrint](https://fedinprint.org/item/fednls/103479)
  - E-mini returns at the European open were flat in 2021–25: roughly zero, against roughly 3.7% a year before.
  - The authors link the change to closing order imbalances, return variance and the risk-bearing capacity of liquidity providers.
  - NightShares' NSPY and NIWM ETFs closed about 14 months after their 2022 launch.
- Costs: a summary of the working paper notes that the drift returns turn negative after paying the bid-ask spread. [E][S-sec] — [CXO Advisory](https://www.cxoadvisory.com/?p=33743)
- Conflict: one search synthesis claims that the 2021 Liberty Street work says the drift later moved towards the Asian openings. I could not confirm this, and it contradicts the authors' main framing (the European open). Low confidence. [S-sec] — [Liberty Street ?p=40](https://libertystreeteconomics.newyorkfed.org/?p=40)
- Gold: during SHFE night hours, both the spillover from the US to China and the total spillover are larger. [A][S-sec; probably Jiang, Kellard & Liu 2020] — [JFM 40(10)](https://econpapers.repec.org/RePEc:wly:jfutmk:v:40:y:2020:i:10:p:1486-1507)
- Context: Nasdaq is moving towards 24-hour trading of US equities, including Asian hours. [E][S-sec, headline only] — [SCMP 2026](https://www.scmp.com/business/markets/article/3373745/can-hong-kong-hold-its-ground-nasdaq-brings-wall-street-asian-hours)

### Inferences
- [Calc] On days when the NBS publishes, the 01:30 UTC minute (20:30 EST / 21:30 EDT) bundles three events: the Shanghai, Shenzhen and Hong Kong cash opens, the CSI 300 futures open, and the official PMI or CPI release. Any "open effect" on ES, NQ, 6A or GC is confounded with scheduled data unless release days are analysed separately.
- No directional anomaly in ES or NQ at the China or Hong Kong open is documented. The well-documented ES overnight anomaly sits at 02:00–03:00 ET, the European open at the end of the 18:00–03:00 window, and its own authors say it has been gone since 2021.
- [Calc] The Tokyo fix at 09:55 JST is 00:55 UTC, so 19:55 EST / 20:55 EDT. If the AUD is among the nine currencies, Krohn et al. imply a stronger USD (a weaker AUD/USD, so short 6A/M6A) into about 19:55 or 20:55 ET, followed by a partial reversal. The AUD-specific size is unknown.
- Because information at the Chinese open flows mostly from the US to China, a CME trader is more likely to see the Chinese open *react to* the overnight ES move than lead it. This is a testable hypothesis, not a documented edge.

### Gaps
- No event study of the 09:30 Beijing or Hong Kong open on ES, NQ, GC or 6A returns or volatility. I found no volume or volatility profile for CME products at 20:30 or 21:30 ET.
- I did not see the AUD-specific Tokyo-fix sizes, or whether the fix pattern persisted after 2020.
- No study of how the Hong Kong lunch break (12:00–13:00 HKT) or the Chinese lunch break affects CME products.

## 3. Gold during Shanghai hours: the "Asian bid", the SGE premium and the link to COMEX intraday returns

### Takeaway
Peer-reviewed work shows that COMEX leads gold price discovery. Chinese venues contribute a minority share, about 15% in Asian hours in one 2021 study, and within China SHFE futures lead SGE spot. The "Asian bid", with gold rising in Asian hours and falling in US hours, has only 2024–2026 evidence: industry and practitioner data (WGC, Morgan Stanley via Saxo, Forex.com, CME volume data) and one unreviewed SSRN paper. That paper finds Asia produced 77.2% of gold's cumulative log return since July 2024. The pattern depends on the regime, varies from month to month, and was overwhelmed by US-hours selling in 2026. I found no study that tests whether the SGE premium predicts COMEX intraday returns.

### Cited Findings
**Price discovery (peer-reviewed)**
- Hauptfleisch, Putniņš & Lucey, "Who sets the price of gold? London or New York", JFM 36(6) 564–586 (2016): price-discovery shares vary within the day and across years, linked to market structure, liquidity, daylight hours and macro announcements. [A][S-abs] — [UTS](https://opus.lib.uts.edu.au/handle/10453/41414); [EconPapers](https://econpapers.repec.org/article/wlyjfutmk/v_3a36_3ay_3a2016_3ai_3a6_3ap_3a564-586.htm)
- Jin, Li, Wang & Yang, "Price discovery in the Chinese gold market" (MPRA WP 71135, 2016): price discovery happens mainly in SHFE futures rather than SGE spot. This holds for information share, component share and information leadership share, in every trading session, and mostly in the night session. [C][S-abs] — [MPRA](https://mpra.ub.uni-muenchen.de/71135/1/MPRA_paper_71135.pdf)
- Jiang, Kellard & Liu, "Night trading and market quality: Evidence from Chinese and US precious metal futures markets", JFM 40(10) 1486–1507 (2020): this studies the SHFE night session, which overlaps with COMEX daytime trading. [A][S-abs] — [EconPapers](https://econpapers.repec.org/RePEc:wly:jfutmk:v:40:y:2020:i:10:p:1486-1507); [Essex](https://repository.essex.ac.uk/27740/); [vLex](https://law-journals-books.vlex.com/vid/night-trading-and-market-855669398); [core.ac.uk](https://core.ac.uk/download/326518807.pdf)
  - After night trading began, China's share of gold price discovery fell relative to the US. Before, the information share was about 0.5.
  - Liquidity rose and volatility at the open fell: the Roll spread, the Amihud measure and realized volatility were all lower.
  - Volatility spillovers became two-way.
- "How do macroeconomic news surprises affect round-the-clock price discovery of gold?", IRFA 78 (2021) 101893. I did not see the authors. [B][S-sec] — [IDEAS](https://ideas.repec.org/a/eee/finana/v78y2021ics1057521921002209.html)

  | Session | SHFE futures | COMEX | London OTC |
  |---|---|---|---|
  | Asian hours | ~15% | ~47% | ~24% |
  | New York session | ~26% | not given | ~14% |
- Older cross-market evidence: information shares of 37.09% for COMEX, 34.66% for MCX and 28.25% for TOCOM. [C][S-sec] — [David Publishing](http://www.davidpublisher.com/Public/uploads/Contribute/552e24b49235b.pdf)

**The 2024–2026 "Asian bid"**
- Wei, "Who moves the price? Trading-session return decomposition and cross-session momentum in gold and silver markets", SSRN 7257240 (posted August 2026). Unreviewed. [C][S-abs] — [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7257240)
  - Data: hourly XAU/USD and XAG/USD spot prices from 22 Jul 2024.
  - Sessions: Asia 00:00–08:00 UTC, Europe 08:00–14:30, US 14:30–24:00.
  - Over a period when gold rose about 81% and silver about 119%, Asia produced 77.2% of gold's cumulative log return and 61.7% of silver's.
  - Short-horizon momentum carries into the Asian session (lag-1 autocorrelation of +0.13 for gold and +0.12 for silver).
  - Momentum inside the US session does not survive costs.
  - The author concludes that marginal pricing shifted east in the post-2022 regime of central-bank buying.
- WGC, Gold Mid-Year Outlook 2026, "Point break" (1 Jul 2026): "many of the pullbacks occurred during US hours and, conversely, gold's rebounds generally occurred during Asian hours". The WGC describes this as the growing relevance of Asian markets in price discovery. [D][S-abs] — [gold.org](https://www.gold.org/goldhub/research/gold-mid-year-outlook-2026); coverage: [IndexBox](https://www.indexbox.io/blog/asian-markets-drive-gold-price-trends-world-gold-council-reports/), [The Asset](https://www.theasset.com/article/56645/asia-reshaping-global-gold-demand-price-discovery)
- Session totals that a search synthesis attributed to the WGC: Asia about +12.9%, North America about −15%, Europe about −1.3%, labelled "first half of 2025". **This label does not fit gold's strong gain in H1 2025** (unverified background: roughly +25%), so the period or the numbers are probably mis-attributed; they would fit H1 2026 better. Check gold.org before using them. [D][S-sec] — surfaced alongside [Kitco Aug 2025](https://www.kitco.com/news/article/2025-08-27/chinese-and-indian-gold-demand-are-fueling-asias-surging-derivatives-market) and [CME OpenMarkets 2025](https://www.cmegroup.com/openmarkets/metals/2025/Asias-Growing-Gold-Demand-Fuels-Surging-Derivatives-Market.html)
- Morgan Stanley data via Saxo (1 May 2025): over four weeks, COMEX gold futures fell 5.9% during US "pit" hours and gained 14.7% outside them, mostly in Asian and European trading. When Chinese markets closed for the Labour Day holiday, the bid temporarily disappeared. [E][S-sec] — [Saxo 1 May 2025](https://www.home.saxo/content/articles/commodities/gold-corrects-sharply-from-record-highs-as-chinese-demand-pauses-01052025); [Saxo 6 May 2025](https://www.home.saxo/en-hk/content/articles/commodities/gold-rises-as-chinese-demand-rebounds-post-holiday-06052025)
- 2026 year to date (to mid-November): gold gained 3.4% in Asian hours, lost 0.9% in European hours and lost 28.1% in US hours. The pattern was not consistent every month. [E][S-sec] — [Forex.com](https://www.forex.com/en-us/news-and-analysis/gold-outlook-asia-buys-the-dip-us-hammers-the-rip/); [Investing.com copy](https://www.investing.com/analysis/gold-outlook-asia-buys-the-dip-us-hammers-the-rip-200691610)
- Flows: in H1 2026, mainland Chinese gold funds took in 28.7 t while US gold ETFs shed 60.7 t. [E][S-sec] — [Sound Money Report](https://soundmoneyreport.substack.com/p/asia-bought-the-hour-america-sold)
- Liquidity on CME: Asian hours accounted for about 25% of volume, rising to over a third in Q2 2025, according to a CME article on Asian gold demand. [D][S-sec] — [CME OpenMarkets](https://www.cmegroup.com/openmarkets/metals/2025/Asias-Growing-Gold-Demand-Fuels-Surging-Derivatives-Market.html)
- Late-2026 context:
  - Gold hit a 14-month low below $3,650 on 19 Nov 2026 on hawkish Fed signals. [E][S-sec] — [FXStreet](https://www.fxstreet.com/news/gold-falls-to-14-month-low-below-3-650-on-hawkish-fed-signals-202611192321)
  - Per the WGC, SGE withdrawals were 94 t in October 2026 (+2% month on month), Chinese wholesale demand was 24% lower year on year, and the PBoC extended its buying to a 24th straight month, with reserves at 2,435 t. [E][S-sec] — [ad-hoc-news](https://ad-hoc-news.de/boerse/news/unternehmensnachrichten/china-extends-gold-buying-streak-to-24-months-as-beijing-bucks-the-price-slump/70535784)
  - The WGC is counting on Asian buyers to limit the fall. [E][S-sec] — [SCMP](https://www.scmp.com/economy/article/3358998/upside-potential-world-gold-council-counts-asian-buyers-curb-price-plunge)

**The SGE premium**
- Definition used by trackers: the SGE Au9999 price (CNY per gram), converted to USD per ounce at the live USD/CNY rate, minus COMEX or spot. [E][S-sec] — [MetalMetric](https://metalmetric.com/tools/shanghai-gold-premium)
- Levels:
  - A record of about $121 per ounce on 14 Sep 2023 (a blog citing the WGC), and mostly within ±1% of COMEX through July 2026. [E][S-sec] — [Bullion Trading LLC](https://bulliontradingllc.com/blog/shanghai-gold-premium/)
  - +0.3% over the London PM fix on 26 Oct 2026. [E][S-sec] — [The Vault Report](https://thevaultreport.com/tools/shanghai-premium)
  - A jump during the 2025 trade war. [E][S-sec] — [BullionVault](https://www.bullionvault.com/gold-news/gold-price-news/china-gold-premium-trade-war-040820251)
- A tracker claims that "academic research" found a statistically significant lead from the SGE premium to later LBMA spot moves, but cites no paper. Unsupported. [E][S-sec] — [MetalMetric](https://metalmetric.com/tools/shanghai-gold-premium)
- SGE trading hours according to a broker blog: 09:00–11:30 and 13:30–15:30, plus a night session 20:00–02:30 CST. Another broker blog gives different hours, so the sources conflict. [E][S-sec] — [HW Online](https://hw.online/faq/global-gold-trading-opening-hours-market-schedule/)

### Inferences
- [Calc] Wei's Asia window (00:00–08:00 UTC) is 19:00–03:00 EST or 20:00–04:00 EDT, almost exactly the 18:00–03:00 New York window. This is the anomaly most directly reachable on CME, since GC and MGC trade continuously then.
- [Calc] If the SGE day sessions are 09:00–11:30 and 13:30–15:30 Beijing, they fall at 20:00–22:30 and 00:30–02:30 EST (21:00–23:30 and 01:30–03:30 EDT). The Chinese night sessions (20:00 or 21:00 to 02:30 Beijing) fall in the New York morning and midday, outside the window.
- The peer-reviewed price-discovery evidence, up to about 2019–2020, does not support "Shanghai leads COMEX intraday". The Asian-bid evidence is newer and not peer-reviewed, and it measures *returns by session*, not lead-lag. Both can be true at once: a flow-driven drift in Asian hours while COMEX still dominates price discovery.
- The Asian bid is a regime phenomenon tied to Chinese and central-bank demand in 2024–2026. In 2026, US-hours selling overwhelmed it (Asia +3.4% against US −28.1% year to date), so a long-in-Asia, flat-otherwise MGC strategy would have made only a small gross gain in 2026. As a placebo, the effect should be re-tested on 2015–2023 data, before the regime began.
- Chinese holidays (Lunar New Year, Labour Day, Golden Week) are a natural experiment. If the bid comes from Chinese demand, it should disappear while mainland markets are closed, as the May 2025 anecdote suggests. This is a cheap robustness test.

### Gaps
- No peer-reviewed study of gold returns by session (Asian versus US hours). No study tests whether the SGE premium predicts COMEX returns over the next hour or session.
- I did not see the authors or sample of the IRFA 2021 paper, the exact WGC session figures and periods, or whether Wei reports net-of-cost results for an Asian-session strategy.
- The SGE benchmark auction times (believed to be 10:15 and 14:15 Beijing, unverified background) have not been studied for fix effects on COMEX.

## 4. The Australian dollar and the ASX open (10:00 Sydney)

### Takeaway
I found no study that treats the ASX open as an AUD return anomaly. In New York time it falls at 18:00 EST in the northern winter and at 19:00–20:00 EDT otherwise. What is documented:
- Currencies tend to depreciate during their own local trading hours (Breedon & Ranaldo), but the AUD version of this is weak.
- FX volatility jumps at the Tokyo and Australian openings.
- AUD/USD volatility is highest when London and New York overlap.
- The USD appreciates into the Tokyo fix and depreciates afterwards (Krohn et al.).
- The Australian equity market itself shows little intraday momentum.

### Cited Findings
- Breedon & Ranaldo, "Intraday patterns in FX returns and order flow" (JMCB 2013; SNB WP 2011-04): currencies tend to depreciate during local trading hours and show no significant pattern during foreign hours. This does not reproduce Ranaldo's (2009) finding that currencies appreciate in foreign hours. The authors link the pattern to order flow: local investors trade during their own hours. [A][S-abs] — [SNB WP](https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04); [IDEAS](https://ideas.repec.org/p/snb/snbwpa/2011-04.html); [AEA 2009 draft](https://www.aeaweb.org/conference/2009/retrieve.php?pdfid=301)
- In their table, the AUD session (10:00–16:00 Sydney) has a mid-quote return of about −0.028 (units unclear) and a 0.50 share of positive returns. The effect is small and weak. [S-sec, table fragment] — [ResearchGate](https://www.researchgate.net/publication/228742460_Intraday_Patterns_in_FX_Returns_and_Order_Flow)
- On close-to-close returns, the AUD is the only currency studied with more than 51% of days positive. [B][S-sec] — [BoC WP 2021-48](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf)
- Krohn, Mueller & Whelan (JF 2024) document the W-shaped USD pattern around the fixes, including the Tokyo fix (see section 2). [A][S-abs] — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306). An earlier draft, "FX premia around the clock", dates from 2018. [C] — [AUT](https://acfr.aut.ac.nz/__data/assets/pdf_file/0007/190753/Krohn_Mueller_Whelan_Jun2018_FXPremiaAroundTheClock.pdf)
- RBA Bulletin, December 2007, "Intraday currency market volatility and turnover": AUD/USD volatility is highest outside Sydney hours, especially when London and New York are both open. Volatility spikes at Australian and US data releases and at the London fix. [B][S-abs] — [RBA](https://www.rba.gov.au/publications/bulletin/2007/dec/1.html)
- Seasonal FX volatility rises by more than 20% at the Tokyo and Australian openings. [C][S-sec] — [arXiv 2411.16244](https://arxiv.org/pdf/2411.16244)
- RBA Bulletin, April 2008: within the hour after a release, the AUD rises after positive Australian data surprises and falls after negative ones. [B][S-abs] — [RBA](https://www.rba.gov.au/publications/bulletin/2008/apr/pdf/bu-0408-1.pdf)
- Batten, Ellis & Hogan study intraday dependence in AUD/USD using tick data from 2000. The abstract does not cover session seasonality. [C][S-abs] — [arXiv math/0412344](https://arxiv.org/pdf/math/0412344)
- There is little market intraday momentum in Australia (see section 1). [B][S-sec] — [PBFJ 2021](https://sciencedirect.com/science/article/pii/S0927538X21000068)

### Inferences
- [Calc] ASX open (10:00 Sydney) in New York time:

  | Period | Sydney | UTC | New York |
  |---|---|---|---|
  | Early Nov to mid-Mar | AEDT | 23:00 | 18:00 EST |
  | Mid-Mar to early Apr, and early Oct to early Nov | AEDT | 23:00 | 19:00 EDT |
  | Early Apr to early Oct | AEST | 00:00 | 20:00 EDT |

  In the northern winter the ASX open coincides with the CME Globex reopen at 18:00 ET, when CME liquidity is thinnest.
- [Calc] The Tokyo open (09:00 JST) is at 19:00 EST / 20:00 EDT, and the Tokyo fix at 19:55 EST / 20:55 EDT. Both fall inside the window, and very close to the ASX open in summer.
- On the evidence I could see, a "short AUD during Sydney hours" rule based on Breedon-Ranaldo is too weak for the AUD to survive M6A or 6A spreads and commissions. The Tokyo-fix reversal is the more credible FX timing effect in this window, with A-grade evidence on the USD in general, but it needs testing on the AUD specifically.

### Gaps
- No study of the ASX open's effect on the AUD, ES or NQ. No recent (post-2016) RBA analysis of AUD intraday seasonality found.
- I did not see AUD-specific figures from Krohn et al., or an hour-by-hour liquidity and spread profile for 6A or M6A.

## 5. Spillover from Chinese data releases (PMI, CPI, activity, trade) to CME futures

### Takeaway
The best intraday evidence is Baum, Kurov & Wolfe (2015), using futures data from 2009–2013. Chinese manufacturing and output releases (PMI, industrial production, GDP) move global stock-index futures, energy and industrial commodities, and commodity currencies such as the AUD. Consumption news does not. The RBA (2016) finds that the AUD's volatility response to Chinese releases rose over 2000–2016, and the IMF (2025) confirms that the releases spill over to equities through growth expectations. These are announcement effects driven by the surprise (the direction depends on the actual figure versus consensus), not time-of-day anomalies. I found no intraday study for 2020–2026 on CME products.

### Cited Findings
- Baum, Kurov & Wolfe, "What do Chinese macro announcements tell us about the world economy?", JIMF 59 (2015) 100–122. Data: intraday financial and commodity futures, 30 Sep 2009 to 31 Dec 2013. [A][S-abs] — [IDEAS](https://ideas.repec.org/a/eee/jimfin/v59y2015icp100-122.html); [WP version](https://ideas.repec.org/p/boc/bocoec/834.html); [Skidmore PDF](https://www.skidmore.edu/economics/documents/WhatDoChineseMacroAnnouncementsTellUsAboutTheWorldEconomy.pdf)
  - Chinese announcements have a substantial effect on world markets compared with similar US and Japanese announcements.
  - Every announcement related to manufacturing and industrial output moves stock markets, energy and industrial commodities, and commodity currencies.
  - News about domestic consumption leaves most markets unaffected.
  - Markets read strong output as good news for the world economy, not as a signal of tighter policy.
  - Along with GDP, the PMI has the strongest influence. [S-sec] — [ResearchGate](https://www.researchgate.net/publication/280308109_What_do_Chinese_Macro_Announcements_Tell_Us_About_the_World_Economy)
- Gutierrez, Turen & Vicondoa, "Global financial spillovers of Chinese macroeconomic surprises", IMF WP/25/133. [B][S-abs/S-sec] — [IMF](https://www.imf.org/-/media/files/publications/wp/2025/english/wpiea2025133-print-pdf.pdf); [Aug 2026 version](https://economia.uc.cl/wp-content/uploads/2026/08/GTV_China_News.pdf); [Wright Research blog](https://www.wrightresearch.in/blog/do-chinas-macro-surprises-actually-impact-global-and-indian-markets/)
  - A 1% positive industrial-production surprise raises Chinese stocks by about 21 bp and Asia-Pacific stocks by about 3 bp on average, through a growth-expectations channel.
  - A summary also cites about 19 bp for global stock returns. This does not square with the 3 bp figure, so check the units and definitions.
  - According to a blog summary, the industrial-production effect survives controls for same-day Japanese and UK releases.
- RBA Bulletin, December 2016 (T. Mathews), "The effect of Chinese macroeconomic news on Australian financial markets". Per-release figures not seen. [B][S-abs] — [RBA](https://www.rba.gov.au/publications/bulletin/2016/dec/6.html)
  - Method: compares volatility around Chinese releases with volatility at the same time on days without a release, January 2000 to November 2016, starting with AUD/USD in a 20-minute window.
  - The AUD's response to Chinese news has grown over time, while its response to US releases has barely changed.
  - A stronger AUD can partly offset good export news for Australian equities.
- Positive PMI announcements raise Chinese stock returns, while negative ones produce no significant reaction (daily windows). [C][S-abs] — [arXiv 1806.04347](https://arxiv.org/pdf/1806.04347)
- Release-time issues: NBS PMI release times have varied in the past; a Peking University working paper cites times "as early as 8:20 AM and as late as 8:00 PM". Some Chinese releases fall on weekends, when US futures are closed. [C][S-sec] — [PHBS WP](https://english.phbs.pku.edu.cn/uploadfile/2023/0330/20230330090416203.pdf)
- Current timing:
  - The official NBS PMIs come out at 01:30 GMT (09:30 Beijing). [E][S-sec] — [investingLive](https://investinglive.com/news/economic-calendar-in-asia-monday-june-30-2025-china-official-pmis-for-june-20250629)
  - The private PMI comes out at 01:45 GMT (09:45 Beijing) and is now published as "RatingDog" (formerly Caixin). [E][S-sec] — [investingLive preview](https://investinglive.com/news/china-pmis-preview-official-manufacturing-seen-back-above-50-before-holiday/); [FXStreet Nov 2026](https://www.fxstreet.com/news/australian-dollar-holds-gains-following-chinas-ratingdog-services-pmi-data-202611040228)
  - A calendar site still lists "Caixin" at 09:45 CST, so the naming conflicts. [E] — [Finance Calendar](https://www.financecalendar.com/?p=2453)
- SUERF policy brief (2023): international markets price Chinese macro developments immediately, but Chinese spillovers are smaller than those from US macro news. [B][S-sec] — [SUERF](https://www.suerf.org/publications/suerf-policy-notes-and-briefs/macroeconomic-news-the-financial-cycle-and-the-commodity-cycle-the-chinese-footprint/)
- High-frequency moves in LME copper are used to identify PBoC policy shocks, which spill over to global commodities. [C][S-sec] — [Ricco et al.](https://www.giovanni-ricco.com/single-post/a-conductive-measure-of-chinese-monetary-policy)
- Practitioner reports from 2026: the AUD's reaction to Chinese data is often muted when US or Australian factors dominate.
  - November 2026: the AUD held its gains after China's October CPI. [E][S-sec] — [FXStreet 9 Nov 2026](https://www.fxstreet.com/news/australian-dollar-holds-gains-following-chinas-cpi-data-202611090202)
  - 19 Oct 2026: AUD/USD extended its gains to about 0.6970 after China's Q3 GDP and activity data beat expectations. [E][S-sec] — [FXStreet 19 Oct 2026](https://www.fxstreet.com/news/australian-dollar-remains-stronger-following-stronger-china-data-202610190213)
  - A weak PMI was offset by a Fed decision on one day. [E][S-sec, attribution uncertain] — [Pip Theory](https://piptheory.com/research/china-pmi-july-2026-preview-aussie-kiwi-aud-nzd)
- The reverse direction, for context: US macro news affects Chinese commodity futures. [B][S-sec, title only] — [Quantitative Finance 2020](https://ideas.repec.org/a/taf/quantf/v20y2020i12p1927-1966.html)

### Inferences
- [Calc] Releases at 09:30 Beijing (NBS PMI, plus CPI and PPI if they keep that slot) fall at 20:30 EST / 21:30 EDT. The private PMI at 09:45 falls at 20:45 EST / 21:45 EDT. These match the "21:00–22:00 New York" slot only in the months when New York is on EDT.
- CME instruments with documented sensitivity to Chinese releases:
  - 6A/M6A: the strongest response, and rising according to the RBA.
  - HG/MHG copper and CL/MCL crude: industrial and energy commodities, per Baum et al.
  - ES/NQ and MES/MNQ: stock-index futures per Baum et al., but the moves are probably small (compare the IMF's ~3 bp for Asia-Pacific per 1% industrial-production surprise).
  - Gold: I saw no description of how it responds.
- Trading these effects needs the actual figure and the consensus in real time, plus fast execution. Any edge comes from speed or post-announcement drift, not from a time-of-day anomaly. Check the prop firm's rules on news trading.

### Gaps
- No intraday event study for 2020–2026 on how CME products react to Chinese releases. I did not see the per-asset magnitudes in Baum et al. or the per-release figures in RBA 2016.
- Current release times are unverified background: GDP and activity data believed to be at 10:00 Beijing, customs trade data variable (often around 11:00 Beijing).
- I found nothing on how gold (GC/MGC) responds to Chinese data.

## 6. Which of these are reachable with CME products on a Bulenox account

### Takeaway
These are directly reachable:
- COMEX gold (GC/MGC), for the Asian-hours gold drift.
- AUD futures (6A/M6A), for the Tokyo-fix pattern, local-hours effects and Chinese data.
- E-mini and Micro E-mini equity futures (ES/NQ, MES/MNQ), for the European-open drift (now faded) and reactions to Chinese data.
- Copper (HG/MHG), for Chinese growth news.

These are not reachable: CSI 300, SGX A50, HSI and SPI 200 futures themselves. CME's E-mini FTSE China 50, launched in October 2015, was placed under a temporary suspension of trading and clearing in November 2020. No official source confirmed that Bulenox supports 6A, M6A, MGC, HG or MHG.

### Cited Findings
- CME E-mini FTSE China 50 Index futures: rulebook chapter 388; trading started on 12 Oct 2015. [S-abs] — [CME rulebook ch. 388](https://www.cmegroup.com/rulebook/CME/IV/350/388.pdf). SER-8670 (October 2020) set out amendments and a temporary suspension of trading and clearing, effective 23 Nov 2020. [S-abs] — [CME SER-8670](https://www.cmegroup.com/notices/ser/2020/10/SER-8670.html); [clearing advisory 20-419](https://www.cmegroup.com/notices/clearing/2020/10/Chadv20-419.html). Current status not confirmed.
- CME delisted the E-mini FTSE/Xinhua China 25 futures on 16 May 2011 [S-abs] — [CME SER-5759](https://www.cmegroup.com/tools-information/lookups/advisories/market-regulation/SER-5759.html), and the E-mini CNX Nifty futures [S-abs] — [CME SER-7355](https://www.cmegroup.com/tools-information/lookups/advisories/ser/SER-7355.html).
- The (undated) China 50 product page gives Globex hours of Sunday to Friday, 18:00–17:00 ET. [S-sec] — [CME product page (KR)](https://www.cmegroup.com/ko/markets/equities/international-indices/e-mini-ftse-china-50-index.html)
- Bulenox, according to third-party reviews only: about 40 or more futures across CME, CBOT, NYMEX and COMEX. GC and SI are listed, and 6E and 6J are tradeable. Not every Rithmic contract is supported, and the exact codes should be reconfirmed. [E][S-sec] — [Propvator](https://propvator.com/blog/?p=5279); [Bulenox futures list (third party)](https://ptv-dev.pages.dev/blog/bulenox-futures-list)
- Bulenox trading day: 17:00 to 16:00 CT, with positions closed before 15:59 CT. One source says there is no fixed trading-hours restriction, which conflicts. An overnight exception for micros on the $10k EOD account (MES, MNQ, M2K, MYM, up to 5 contracts) is reported but unverified. [E][S-sec] — [TradingToolsHub](https://tradingtoolshub.com/blog/bulenox-rules-explained/); [Propvator hours](https://propvator.com/blog/bulenox-trading-hours/); [TradingFunder](https://tradingfunder.com/?p=13715)
- Asian hours were about 25% of volume, and over a third in Q2 2025, per CME's article on Asian gold demand. [D][S-sec] — [CME OpenMarkets](https://www.cmegroup.com/openmarkets/metals/2025/Asias-Growing-Gold-Demand-Fuels-Surging-Derivatives-Market.html)

### Inferences
**Time map [Calc] (New York window 18:00–03:00)**

| Event | Local time | UTC | New York (EST, Nov–mid-Mar) | New York (EDT) | CME instrument(s) | Best evidence (grade) |
|---|---|---|---|---|---|---|
| Globex reopen | 18:00 ET | 23:00 (EST) / 22:00 (EDT) | 18:00 | 18:00 | all | — |
| ASX cash open | 10:00 Sydney | 23:00 (AEDT) / 00:00 (AEST) | 18:00 | 19:00 (transition weeks) / 20:00 (Apr–Oct) | 6A/M6A | no study; FX volatility +20% at the Australian open (C) |
| Tokyo open | 09:00 JST | 00:00 | 19:00 | 20:00 | 6A/M6A, MES/MNQ | FX volatility +20% at the Tokyo open (C) |
| Tokyo FX fix | 09:55 JST | 00:55 | 19:55 | 20:55 | 6A/M6A | USD up into the fix, down after (A, JF 2024) |
| NBS PMI and 09:30 releases; China and Hong Kong cash open; CSI 300 futures open | 09:30 Beijing/HKT | 01:30 | 20:30 | 21:30 | 6A/M6A, HG/MHG, MES/MNQ, GC/MGC | announcement effects 2009–2016 (A/B); no documented open effect |
| Private (RatingDog) PMI | 09:45 Beijing | 01:45 | 20:45 | 21:45 | same | as above |
| China lunch break | 11:30–13:00 Beijing | 03:30–05:00 | 22:30–00:00 | 23:30–01:00 | — | none found |
| Hong Kong lunch break | 12:00–13:00 HKT | 04:00–05:00 | 23:00–00:00 | 00:00–01:00 | — | none found |
| China last half-hour and close | 14:30–15:00 Beijing | 06:30–07:00 | 01:30–02:00 | 02:30–03:00 | MES/MNQ, M6A as proxies | Chinese intraday momentum (A/B, no evidence it transfers) |
| European-open drift (ES) | — | 07:00–08:00 (EST) / 06:00–07:00 (EDT) | 02:00–03:00 | 02:00–03:00 | ES/MES | A historically; gone in 2021–25 |
| Gold "Asia session" (Wei) | — | 00:00–08:00 | 19:00–03:00 | 20:00–04:00 | GC/MGC | C/D/E, 2024–2026 only |

**Ranking of CME-reachable candidates (my judgment)**
1. **GC/MGC Asian-hours drift.** This is the most direct and has improving liquidity, but the evidence is grade C/D/E and specific to the 2024–26 regime. In 2026, US-hours selloffs overwhelmed the Asian gains. It needs testing on 2015–2026 data, with Chinese-holiday placebo tests and realistic MGC costs.
2. **6A/M6A around the Tokyo fix (19:55/20:55 ET).** The evidence for the USD fix pattern is A-grade, but the AUD-specific size is unknown. Moves are small relative to the spread, so costs on micro contracts decide whether it works.
3. **6A/M6A, HG/MHG and MES/MNQ at 20:30/21:30 ET on Chinese release days.** The A/B evidence is about *reactions*, which have a direction only if you have the surprise. It is better used as a volatility and risk filter (stand aside or widen stops) than as an anomaly.
4. **ES/MES European-open drift at 02:00–03:00 ET.** A-grade historically, but its own authors document that it disappeared in 2021–25, and the bid-ask spread turns it negative.
5. **Chinese and Hong Kong intraday momentum, and T+1 overnight effects.** Not tradable on CME. At most they are conditioning signals, with no evidence that they carry over.

### Gaps
- Not verified (only third-party reviews): the official Bulenox instrument list (6A, M6A, MGC, HG, MHG), its commissions, and its rules on news trading and trading during the Asian session.
- Not checked: the current status of CME's E-mini FTSE China 50 after the 2020 suspension, and the status of CME USD/CNH futures and whether Bulenox offers them.
- CME micro contract specifications were not verified in this session. My unverified background is that MGC is 10 oz with a $1 tick, M6A is AUD 10,000 with a $1 tick, the MES tick is $1.25 and the MNQ tick is $0.50. Hour-by-hour spreads during 18:00–03:00 ET were not checked either.
- Verifying these items at the source requires adding hosts to this environment's network allowlist:
  - Tried and blocked: papers.ssrn.com, www.sciencedirect.com, www.imf.org, www.snb.ch, pureadmin.qub.ac.uk.
  - Probably also needed: onlinelibrary.wiley.com, www.rba.gov.au, www.gold.org, libertystreeteconomics.newyorkfed.org, www.cmegroup.com and the Bulenox help center.
