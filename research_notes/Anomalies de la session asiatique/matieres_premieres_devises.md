# Asian-hours patterns in COMEX gold, NYMEX crude oil and CME FX futures (JPY, AUD), and how tradable they are for a small prop account (micros, costs, Bulenox)

**How these notes were collected (read first).** WebFetch was blocked in this session: cmegroup.com, www.cmegroup.com, nber.org and arxiv.org are not on the session's allowed network list. So **no page was opened and read in full**, and in the strict sense nothing below is "verified at the source". Every item comes from search-engine extracts of the cited page. Each item carries one of these tags:
- **[P]**: wording or figures taken from the primary source's own page (exchange, firm, journal or abstract page, or the paper or working paper itself), seen through a search extract. This is the best evidence available here.
- **[S]**: a claim about a study or page seen only in a third-party summary, a citing paper or a search paraphrase, not matched to primary text.
- **[B]**: practitioner blog, backtest, vendor or market commentary. Not peer-reviewed.
- **[Calc]**: my own arithmetic from the cited contract specs. The price levels used are assumptions and are stated each time.

Search summaries sometimes made arithmetic or sign errors, which I corrected. For example, one summary gave MGC's 2-tick spread as "2 cents/oz"; it is actually 2 × $0.10 = $0.20/oz. Another summary turned a US-hours gold *decline* into a gain.

**Time mapping for the 18:00–03:00 New York window.** EST is UTC−5 (Nov–Mar) and EDT is UTC−4 (Mar–Nov).
- Tokyo fix at 09:55 JST falls at **19:55 NY in winter (EST) and 20:55 NY in summer (EDT)**. Japan has no daylight saving time. [Calc]
- CME Globex reopens at 17:00 CT (18:00 ET) after the daily 60-minute halt (16:00–17:00 CT). See section 5.
- CME's own "Asian hours" statistics use **06:00–18:00 Singapore time**, which is 17:00–05:00 NY (EST) or 18:00–06:00 NY (EDT). That is wider than the 18:00–03:00 window and includes the London open. [Calc from CME's definition, section 4]

---

## 1. Gold: is there a documented Asian-hours drift or a Shanghai-session effect in COMEX gold (time-of-day returns 2010–2026, London fix, "rises in Asia, falls in New York")?

### Takeaway
- **What peer-reviewed work shows.** The only peer-reviewed study found on COMEX gold session returns is Blose, Gondhalekar & Kort (2018), covering 1985–2012. It finds significantly positive "overnight" returns and significantly negative NY "day" returns. Their "overnight" bundles Asian and London hours, and the asymmetry "has weakened substantially over the years".
- **What is missing.** No peer-reviewed study found isolates 18:00–03:00 NY or covers 2020–2026 with costs.
- **Shanghai.** The research points to New York futures leading global gold price discovery (about 56% information share), not to a Shanghai-driven drift.
- **2026 "Asia buys, US sells".** This pattern appears only in market commentary, with no statistics, no costs and no control for the reopen quote artifact.

### Cited Findings
**Peer-reviewed overnight versus day asymmetry (COMEX)**
- [P] Blose, Gondhalekar & Kort, "Overnight versus day returns in gold and gold related assets", *Journal of Economics and Finance* 42(3), 2018. In the COMEX front-month gold contract, overnight returns are significantly positive and day returns significantly negative, over **1985 through 2012**. — [IDEAS/RePEc](https://ideas.repec.org/a/spr/jecfin/v42y2018i3d10.1007_s12197-017-9403-0.html); [Springer](https://link.springer.com/article/10.1007/s12197-017-9403-0)
- [P] The same pattern appears in the gold spot market (London Fix), gold-mining stocks, and gold-related closed-end funds and ETFs. — [ResearchGate abstract](https://www.researchgate.net/publication/318356821_Overnight_versus_day_returns_in_gold_and_gold_related_assets)
- [P] "The asymmetry has weakened substantially over the years, but it is still present." The authors interpret the findings as "consistent with gold price being (too) high at the opening of the various markets". — [IDEAS/RePEc](https://ideas.repec.org/a/spr/jecfin/v42y2018i3d10.1007_s12197-017-9403-0.html)
- [S] **The two search summaries conflict on transaction costs.** One summary said the authors find the pattern "economically important even with transaction costs" ([Springer](https://link.springer.com/article/10.1007/s12197-017-9403-0)). Another found no source that tests costs ([ResearchGate](https://www.researchgate.net/publication/318356821_Overnight_versus_day_returns_in_gold_and_gold_related_assets)). This is unverified, and effect sizes were not visible in any extract.
- [S] A search summary attributed the same COMEX-gold 1985–2012 finding to Lou, Polk & Skouras, "A Tug of War". This looks like a mix-up with Blose et al.; the Tug of War paper is about equities. It was not verified. — [LSE PDF](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)

**Recent robustness test on ETFs (overnight = US close to US open, which includes Asia and London)**
- [P] "Overnight and Daytime Returns in Commodity ETFs: Do Session Anomalies Survive Trading Costs and Multiple Testing?", *Commodities* (MDPI) 5(4):26, 2026. — [MDPI](https://www.mdpi.com/2813-2432/5/4/26)
  - After adjusting nine overnight-mean tests, positive overnight means remain significant at 5% for DBA, DBP, **GLD** and SLV.
  - **No daytime mean is significant.** Daytime means are negative for seven funds and small and positive for GLD and USO.
  - The overnight-minus-daytime difference survives a nine-fund Holm adjustment only for DBA and SLV, and only DBA survives joint adjustment across all 27 tests.
  - The trading-cost results were **not visible** in the extract.

**London fix effects (London hours, outside the Asian window)**
- [P] Caminschi & Heaney, "Fixing a Leaky Fixing: Short-Term Market Reactions to the London PM Gold Price Fixing", *Journal of Futures Markets* 34(11):1003–1039, 2014. — [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1002/fut.21636); [UWA release](https://www.news.uwa.edu.au/archive/201410067021/research/uwa-research-finds-gold-and-silver-price-setting-open-exploitation/)
  - GC futures and GLD show significantly higher volume and volatility immediately after the start of the PM fixing, well before the result is published.
  - Informed traders had statistically significant return advantages in the 4 minutes after the fixing started.
  - There are no significant returns after publication.
  - The study covers the old telephone-auction fix, before the procedure changed.

**Shanghai, SHFE and price discovery**
- [P] Jiang et al., "Night trading and market quality: Evidence from Chinese and US precious metal futures markets", *Journal of Futures Markets* 40:1486–1507, 2020. — [Wiley](https://onlinelibrary.wiley.com/doi/full/10.1002/fut.22147); [Essex repository](https://repository.essex.ac.uk/27740/1/fut.22147.pdf)
  - The SHFE night session "crucially overlapp[ed] with the COMEX daylight trading period". It lets SHFE capture US price information in real time.
  - For gold, SHFE's price-discovery share **falls** relative to the US after night trading was introduced.
  - Liquidity in Shanghai rose, and volatility at the open fell.
  - A search summary said the data run to about 2013. That is unverified.
- [P] Jin et al., "Price Discovery in the Chinese Gold Market" (SHFE futures versus SGE spot). The night session alone contributes **55.20%** of price discovery (information share), and price discovery in both markets occurs more in the night session. — [Hull repository](https://hull-repository.worktribe.com/preview/1389564/document.pdf); [ResearchGate](https://www.researchgate.net/publication/325195484_Price_Discovery_in_the_Chinese_Gold_Market)
- [P] "How do macroeconomic news surprises affect round-the-clock price discovery of gold?", *International Review of Financial Analysis*, 2021. **New York gold futures lead across five time zones with 56% information share.** SHFE futures hold only 9.3% ($6.19bn) of gold-derivatives volume (World Gold Council, 2020). — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1057521921002209)
- [P] Ma, Bouri, Xu & Zhou, "The 'night effect' of intraday trading: Evidence from Chinese gold and silver futures markets", *Global Finance Journal*, 2025. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1044028325000110); [ResearchGate](https://www.researchgate.net/publication/388428082_The_night_effect_of_intraday_trading_Evidence_from_Chinese_gold_and_silver_futures_markets)
  - In SHFE gold and silver futures, intraday momentum follows intraday reversals, and the shift is linked to the launch of night trading.
  - Before night trading, large SHFE gold moves mostly came from overnight moves in international gold futures.
- [P] World Gold Council: the international gold price is set by the highest-volume markets, namely the London gold market and COMEX futures. — [WGC](https://www.gold.org/gold-market-structure/global-gold-market-old)
- [B] The SGE introduced the yuan-priced, twice-daily Shanghai Gold Price benchmark in 2016. In 2026 there were sessions where London rose in USD while Shanghai fell in CNY. — [Money Metals](https://www.moneymetals.com/price/who-sets-the-gold-price)

**2026 "Asia buys, US sells" claims (commentary, no statistics)**
- [B] FOREX.com / Investing.com, "Gold Outlook: Asia Buys the Dip, US Hammers the Rip" (about 16 Nov 2026), using hourly prices. — [FOREX.com](https://www.forex.com/en-us/news-and-analysis/gold-outlook-asia-buys-the-dip-us-hammers-the-rip/); [Investing.com](https://www.investing.com/analysis/gold-outlook-asia-buys-the-dip-us-hammers-the-rip-200691610)
  - Since early September 2026: **+2.7% cumulative in Asian hours, −2.5% in Europe, −12.2% in the US session.**
  - Year to date 2026: **+3.4% in Asia, −0.9% in Europe, −28.1% in the US.**
  - The pattern "hasn't been consistent every month".
  - One search summary rendered the US figure as a gain. The headline and a second summary indicate a decline.
- [B] FXStreet, 13 July 2026: "A strange dichotomy: Gold up on the year in Asian markets, down big in the West". — [FXStreet](https://www.fxstreet.com/analysis/a-strange-dichotomy-gold-up-on-the-year-in-asian-markets-down-big-in-the-west-202607131959)
- [P, news] Bloomberg, 4 Aug 2026. Chinese dip-buying helped keep gold above $4,000. Chinese gold ETFs saw 14 straight days of inflows, the longest streak since March. — [Bloomberg](https://www.bloomberg.com/news/articles/2026-08-04/chinese-dip-buying-bolsters-gold-as-prices-find-floor-at-4-000)
- [P, news] Bloomberg, 7 Jul 2026. The PBOC bought the most gold since October 2023, extending its buying streak to 20 months. — [Bloomberg](https://www.bloomberg.com/news/articles/2026-07-07/china-s-pboc-buys-most-gold-since-2023-as-bullion-swings)
- [B] An opinion column says gold's rally "now depends on China as US buying fades". — [Investing.com](https://www.investing.com/analysis/golds-rally-now-depends-on-china-as-us-buying-fades-from-the-drivers-seat-200673823)

**Reopen and rollover quote artifact (the project's finding)**
- [B] Only broker blogs document spread widening at the 17:00 NY rollover. — [FXNX XAUUSD log](https://fxnx.com/en/blog/xauusd-spread-dated-log-measured-cost-changes); [FXNX rollover](https://fxnx.com/en/blog/spread-widening-rollover-hourly-cost-pattern-measured)
  - Recorded XAUUSD rollover feeds show spreads of **$2.00–2.80 for 5–10 minutes**.
  - Major FX pairs are back to 1.2–1.5× their baseline spread by 17:45 EST.
  - No academic study of the reopen artifact was found.
- [S] A Quantpedia piece is titled "Dangers of Relying on OHLC Prices: The Case of Overnight Drift in GDX ETF". The title signals that measured overnight drift can be a price-data artifact. Its content was not reviewed. — [Quantpedia](https://quantpedia.com/dangers-of-relying-on-ohlc-prices-the-case-of-overnight-drift-in-gdx-etf/)

### Inferences
- **Blose et al. do not test the Asian window.** In 1985–2012 COMEX "day" meant pit hours, so "overnight" covers Asia, London and the London AM fix. Their result fits "gold rises outside NY, falls in NY", but it cannot attribute the gain to 18:00–03:00. Their "too high at the opening" reading also suggests the measured asymmetry partly reflects how opening prices are recorded. That is the same family of concern as the project's reopen artifact.
- **The 2026 commentary split probably uses spot XAU/USD hourly bars.** It is therefore exposed to the 18:00 spread-narrowing artifact the project found. COMEX trade prices are less exposed, because Globex halts 17:00–18:00 ET and reopens with real trades. However, the first minutes after reopen have thin books, and no CME data cover that sub-window (section 4).
- **The 2026 size is thin even if real.** [Calc] +3.4% over about 225 Asian sessions is about 1.5 bp per session. Since September it is about 5 bp per session (+2.7% over about 55 sessions). The micro-gold round trip costs about 0.9 bp (section 4). The pattern is regime-dependent: it coincides with documented Chinese ETF and central-bank buying in 2026 and is not shown as structural.
- **A Shanghai effect would be a flow effect, not a price-discovery effect.** The evidence says New York leads, and the SHFE night session overlaps US daytime, outside the Asian window. Any Shanghai effect in COMEX during 18:00–03:00 would be a demand-flow effect, for example Chinese buying in the SGE/SHFE day session. That kind of effect can vanish when the flows stop.
- **London fix effects do not bear on the window.** The fix and auction times are in London hours: AM 10:30 London is about 05:30 ET. They matter only as endpoints of older "overnight" measures.

### Gaps
- No peer-reviewed hour-of-day study of COMEX gold that isolates 18:00–03:00 NY over 2010–2026, with or without costs, was found.
- Blose et al.'s effect sizes and cost treatment are unverified (full text not reachable). The MDPI paper's sample period and cost results are unseen.
- No study tests "gold rises in Asia, falls in New York" on futures *trade* prices while controlling for the reopen spread artifact.
- No Bloomberg or WGC quantitative analysis of Asian-hours gold returns for 2024–2025 was found.

---

## 2. Crude oil: are there Asian-hours patterns in NYMEX WTI (Chinese data releases, Singapore or Shanghai trading)?

### Takeaway
- **No direction found.** No study documents a directional Asian-hours drift in NYMEX WTI, or an intraday WTI response to Chinese macro releases.
- **What the research covers instead.** Asian-hours crude research is about Shanghai INE crude. INE co-moves more with WTI and Brent during its night session, which overlaps US hours, and behaves "more like a regional market" during its day session, which falls in the Asian window.
- **Liquidity.** CME reports WTI's Asian-hours spread at the all-hours average (1.34 versus 1.35 ticks), with slightly thinner top-of-book.

### Cited Findings
- [P] Ji, Zhang & Zhao (2021), "Intra-day co-movements of crude oil futures: China and the international benchmarks", *Annals of Operations Research*. INE shows more integrated co-movements with WTI and Brent during the **night** session and behaves more like a regional market during the **day** session. — [Kent repository](https://kar.kent.ac.uk/93920/1/INEnet_final.pdf); [Springer](https://link.springer.com/article/10.1007/s10479-021-04097-x)
- [P] Renmin University IMI working paper on return and volatility transmission between INE and international crude futures, using intraday data. "All three oil futures returns are substantially more volatile during the INE trading session." The exact comparison was not in the extract. — [IMI WP2003](http://www.imi.ruc.edu.cn/EN/uploads/2020/03/WP2003.pdf)
- [P] "China's crude oil futures: Introduction and some stylized facts", *Finance Research Letters*. INE shows multiple-U-shaped intraday seasonality and jumps in realized volatility, but the sample is only the first two months after the March 2018 launch. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1544612318303751)
- [P] Wen, Wang & Zhang (2021), "Intraday return predictability in China's crude oil futures market", *Economic Modelling* 96:209–219. INE crude shows a strong intraday **reversal**, not momentum, linked to the timing of two routine intraday crude-inventory announcements. — [IDEAS](https://ideas.repec.org/a/eee/ecmode/v96y2021icp209-219.html); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0264999321000134)
- [P] Ye & Karali (2016), *Energy Economics*. Unexpected API and EIA inventory changes move crude futures returns and volatility intraday. These are US-hours events. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0140988316302110)
- [P] A functional GARCH-X study of WTI intraday return curves finds overnight cumulative intraday return curves serially uncorrelated but conditionally long-range heteroscedastic. That means volatility is predictable and direction is not. — [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S240585132300051X)
- [P] A 2026 *Energy* paper compares structural breaks in intraday volatility across INE, WTI and Brent using 5-minute data. Its findings were not seen. — [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0360544226002847)
- [P] China PMI event-study evidence exists for **Chinese stocks**: positive PMI surprises have a significantly positive effect, negative ones no significant effect. No equivalent crude-oil intraday study was found. — [arXiv 1806.04347](https://arxiv.org/pdf/1806.04347)
- [P] CME whitepaper "Leveraging CME Group Asia Trading Hours Liquidity for Cross Commodity Trading" (2023). — [CME](https://www.cmegroup.com/articles/whitepapers/leveraging-cme-group-asia-trading-hours-liquidity-for-cross-commodity-trading.html)
  - Asia hours were about **17% of global futures volume** across six commodity benchmarks in 2022.
  - WTI averaged close to **150,000 lots per day in Asia hours** in 2022, a 12% compound annual growth rate since 2012.
  - In Q1 2023, the most-active WTI contract's average best bid/ask was **1.34 ticks in Asia hours versus 1.35 across all hours**. Average best bid/ask size was **6.71 versus 7.00 lots**.

### Inferences
- The INE night session (21:00–02:30 Beijing; background knowledge, not verified here) maps to US morning hours. The INE day session maps to the 18:00–03:00 NY window. The cited evidence says INE follows the international benchmarks during the overlap and is "regional" during its day session. So Shanghai trading during Asian hours carries little information for WTI, and there is no mechanism-backed reason to expect a directional WTI drift then.
- Chinese releases (background knowledge, not verified: official PMI and CPI around 09:30 Beijing, which is about 20:30–21:30 NY) fall in the window but are **untested** for WTI. The equity evidence (asymmetric PMI response) cannot be transferred to crude.
- **[Calc] Costs are a high hurdle.** At an assumed $60–70/bbl WTI, one MCL tick ($0.01) is about 1.5 bp of notional. A round trip of about $2.5–3.0 (spread plus Bulenox commission, section 4) is about 4–5 bp. Any Asian-hours crude edge would need to clear that. No such edge is documented.

### Gaps
- No peer-reviewed hour-of-day *return* study of NYMEX WTI focused on Asian hours (2010–2026) was found.
- No study of WTI or Brent intraday reactions to Chinese PMI, trade or CPI data, or to Singapore pricing windows, was found.
- No MCL-specific Asian-hours spread or depth data exist; the CME figures are for standard CL in Q1 2023.

---

## 3. Yen and Australian dollar futures: Tokyo fixing effect, gotobi effect (net of costs), Asian-hours seasonality in AUD

### Takeaway
Three academic results matter:
- **Home currencies weaken during their own business hours** (Ranaldo 2009; Breedon & Ranaldo 2013). This implies JPY and AUD weakness in Tokyo and Sydney hours.
- **The USD appreciates into FX fixes, including the Tokyo 09:55 fix, then reverses** (Krohn, Mueller & Whelan 2024, *Journal of Finance*). Reversal strategies have **negative Sharpe ratios once the full bid-ask cost is charged**, and the Tokyo reversal is the weaker one.
- **The Tokyo fixing rate is biased by order imbalances** (Ito & Yamada 2017; data 1999–2013).

On gotobi specifically, peer-reviewed work supports the fixing mechanism but not a net-of-cost trade. Every 2022–2026 out-of-sample test found is practitioner work, and these tests are mixed to negative after spreads. That is consistent with the project's 2023–2026 failure.

### Cited Findings
**Time-of-day segmentation (structural pattern)**
- [P] Ranaldo (2009), "Segmentation and Time-of-Day Patterns in Foreign Exchange Markets", *Journal of Banking & Finance* 33:2199–2206. — [ResearchGate](https://www.researchgate.net/publication/222525830_Segmentation_and_Time-of-Day_Patterns_in_Foreign_Exchange_Markets); [SNB WP 2007-03 (IDEAS)](https://ideas.repec.org:443/p/snb/snbwpa/2007-03.html)
  - Home currencies systematically depreciate during domestic working hours and appreciate during foreign working hours.
  - The pattern is "statistically and economically highly significant".
  - Proposed mechanism: domestic agents are net buyers of foreign currency and trade mostly in their own working hours.
  - [S] The sample predates 2007.
- [P] Breedon & Ranaldo (2013), "Intraday Patterns in FX Returns and Order Flow", *Journal of Money, Credit and Banking* 45(5):953–965. — [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/jmcb.12032); [SNB WP 2011-04](https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04)
  - Currencies tend to fall during home-market trading hours, across several currencies and time zones.
  - The same pattern shows in order flow: dealers in each region are net buyers of foreign currency in their own hours.
  - Data from a single market maker support this explanation.
- [S] "Intraday patterns in foreign exchange returns and realized volatility", *Finance Research Letters* 27:99–104 (2018). Citing work summarizes it as finding that home currencies weaken during domestic sessions and strengthen offshore. — [IDEAS](https://ideas.repec.org/a/eee/finlet/v27y2018icp99-104.html)
- [S] Z. Jiang, "Currency Returns in Different Time Zones" (2015). Content not reviewed. — [CICF PDF](https://www.cicfconf.org/sites/default/files/paper_67.pdf)

**Fixings (Tokyo 09:55 JST = 19:55 NY in winter, 20:55 NY in summer)**
- [P] Krohn, Mueller & Whelan, "Foreign Exchange Fixings and Returns around the Clock", *Journal of Finance* 79(1):541–578, 2024. — [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/jofi.13306); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3521370)
  - "The U.S. dollar appreciates in the run-up to FX fixes and depreciates thereafter, tracing a W-shaped return pattern around the clock."
  - The study covers the top nine currencies over 21 years. The reversals are pervasive and highly significant, and imply daily swings of more than $1bn based on spot volumes.
  - Proposed mechanism: inventory risk, as dealers intermediate unconditional USD demand at the fixes.
- [P] The Tokyo fix (09:55 Tokyo) is one of three major fixes studied, with the ECB fix (14:15 Frankfurt) and the London 16:00 fix. The W-pattern around the Tokyo fix **shifts by about one hour between spring and autumn**. — [UNSW BusinessThink](https://www.businessthink.unsw.edu.au/articles/forex-market-patterns-currency-fixing-times-us-dollar-demand)
- [P, working-paper versions; figures may differ from the published paper] Strategy results. — [Bank of Canada SWP 2021-48](https://www.bankofcanada.ca/wp-content/uploads/2021/10/swp2021-48.pdf); [INSEAD version](https://sites.insead.edu/facultyresearch/research/file.cfm?fid=66802)
  - Gross Sharpe ratios are "positive and very high".
  - With the full transaction costs implied by indicative quotes, Sharpe ratios are **negative**.
  - With 50% of the quoted spread, a EUR strategy around the London fix more than triples over 1999–2018, with a net Sharpe of 0.65.
  - The Tokyo-fix reversal is "notably smaller but remains statistically significant" in the 2019 sample. One version notes that trading the Tokyo reversal gave **negative returns in the early part of the sample**.
- [P] Ito & Yamada, "Puzzles in the Tokyo fixing in the forex market: Order imbalances and bank pricing", *Journal of International Economics* 109:214–234, 2017 (NBER WP 22820, 2016). — [IDEAS (NBER)](https://ideas.repec.org/p/nbr/nberwo/22820.html); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0022199617301204)
  - When the customer order imbalance is particularly high, the fixing rate has an upward bias (USD/JPY).
  - Banks' fixing price-setting depends on the order imbalances.
  - The model's cost is the gap between the inventory price and the transaction price at 9:55. In calibration, banks that fix can profit by submitting most orders at 9:55.
  - [S] The data are high-frequency USD/JPY and EUR/JPY, 1999–2013.

**Gotobi (5th, 10th, 15th, 20th, 25th and month-end settlement days)**
- [P] Bessho, Sugimoto & Suzuki, "Forex Trading Strategy That Might Be Executed Due to the Popularity of Gotobi Anomaly", arXiv:2301.13204 (Jan 2023). — [arXiv](https://arxiv.org/abs/2301.13204)
  - The paper uses **USD/JPY 2018–2020** and frames the anomaly as a possible arbitrage opportunity.
  - Proposed mechanism: exporters wait for payment, so yen buying does not happen on gotobi days, and the yen is relatively cheap.
  - The numeric results were not visible in the extract.
- [B] Alpha in Academia: USD/JPY 1-minute data **2006–2025**, 1,175 windows, **+4.54 pips average, profit factor 1.62, gross of spread**. It gives no split for recent years and warns that a 1-minute bar close is not the fixing instant. — [alphainacademia](https://www.alphainacademia.com/p/can-you-beat-the-market-by-trading)
- [B] Yura Trading: tuned on 2019–2022, held out 2022–2026. The edge is "real" but was rejected by the author's out-of-sample gates; the survivor's profit factor was 1.36 out of sample. — [Yura Trading](https://yuratrading.com/blogs/gotobi-tokyo-fix)
- [B] ForexFactory, "7 years of USDJPY tick data". Two of three robust-looking entry windows died out of sample. The survivor had a profit factor of 1.36 but failed the author's rule of keeping at least 70% of the in-sample profit factor. This may be the same author as Yura Trading. — [ForexFactory](https://www.forexfactory.com/thread/1407332-gotobi-tokyo-fix-anomaly-7-years-of-usdjpy-tick)
- [B] GitHub research log, Exness tick data: 2019–2023 used to select, **2024 to Sep 2026 held out**. The USDJPY pooled average is about **−0.137R after spread** and −0.026R before, with a spread cost of about 0.111R per trade. — [GitHub prathamesh-git9](https://github.com/prathamesh-git9/gotobi-fx-bot)
- [B] Another GitHub study: the USD/JPY fade passes 1 of 4 tests, costs are 0.11R per trade, and the edge is thin at twice the costs. — [GitHub PR #878](https://github.com/vazxanana/macro-dashboard/pull/878)
- [B] Substack: the post-fix reversal is positive and statistically significant across seven JPY crosses, but the gotobi increment is not isolated from an ordinary Tokyo-fix pattern. — [Forex Detox](https://forexdetox.substack.com/p/the-tokyo-fix-reversal-anomaly-on)

**AUD**
- [P] arXiv 2411.16244 models 5-minute AUD returns over 2017–2023 against 117 Australian and US events (Bloomberg calendar timestamps). It is a volatility study, and **Chinese releases are not included**. — [arXiv](https://arxiv.org/pdf/2411.16244)
- [B] News accounts describe the AUD reaction to Chinese CPI and GDP as often muted, or overshadowed by the RBA, the Fed or risk sentiment. — [FXStreet (Nov 2026)](https://www.fxstreet.com/news/australian-dollar-holds-gains-following-chinas-cpi-data-202611090202); [FXStreet (Oct 2026)](https://www.fxstreet.com/news/australian-dollar-remains-stronger-following-stronger-china-data-202610190213)
- [P] CME, FY2022 data: Asian hours account for **19% of AUD/USD futures ADV and 21% of USD/JPY futures ADV**. — [CME 2023](https://www.cmegroup.com/articles/2023/unlocking-potential-during-asian-trading-hours-with-cme-fx-futures.html)

### Inferences
- **Direction in futures terms.** Ranaldo and Breedon & Ranaldo imply that 6A/M6A and 6J/MJY (quoted in USD per AUD and USD per JPY) tend to drift **down** during Sydney and Tokyo hours. Krohn, Mueller & Whelan imply that MJY falls into 19:55 or 20:55 NY and rebounds after. All these samples end around 2019–2020 or earlier, so nothing establishes persistence through 2020–2026.
- **The cost evidence argues against retail exploitation.** The authors' own cost test turns fix-reversal Sharpe ratios negative at the full spread. Micro FX ticks are coarse (section 5), so a micro trader pays at least the full one-tick spread.
- **Gotobi on MJY is close to break-even before any decay.** [Calc] At USD/JPY 150, one MJY tick (0.000001 JPY/USD = $1.25) equals about **2.25 USD/JPY pips**. A one-tick spread plus about $1 commission is a round-trip cost of about **4 pips**. The best long-run gross gotobi figure found is +4.54 pips (2006–2025). The expected net edge is therefore about zero, before any decay after 2022. This matches the project's 2023–2026 failure and the 2022–2026 and 2024–2026 holdout results above.
- **Why the effect may have shifted.** Bessho et al. hypothesize that the anomaly's popularity drives front-running strategies. Ito & Yamada show the bank pricing depends on order imbalances. Both mechanisms imply the pre-fix move can shift earlier or shrink, which is a reason the effect is unstable.
- **AUD events in the window.** RBA decisions (14:30 Sydney) and Chinese data (around 09:30–10:00 Beijing) fall inside 18:00–03:00 NY (background knowledge, not verified here). No study of AUD *direction* around them was found.

### Gaps
- No peer-reviewed gotobi study covering 2020–2026, on CME futures, net of costs, was found.
- No AUD-specific Asian-hours return-seasonality study was found, and no event study of AUD futures around Chinese data or RBA decisions.
- The Tokyo-specific magnitudes (bp per day) and the exact sample in Krohn, Mueller & Whelan were not visible.
- One citing summary said Breedon & Ranaldo find **no** significant pattern during *foreign* hours, contradicting Ranaldo (2009) on that side. The citing paper was not identified, so this is unverified.
- Cornett, Schwarz & Szakmary (1995, *Journal of Banking & Finance*), on intraday seasonality in CME currency futures, was not retrieved.

---

## 4. Microstructure at night on CME: spreads, depth and round-trip cost in micro gold, micro crude and micro FX, Asian versus US hours

### Takeaway
- **Spreads.** CME's self-reported statistics show Asian-hours top-of-book spreads essentially equal to all-day averages: MGC 1.98 versus 2.01 ticks, CL 1.34 versus 1.35 ticks, 6J 1.08 versus 1.09 pips, 6A 0.66 versus 0.65 pips.
- **Depth and volume.** Depth is slightly thinner (CL 6.71 versus 7.00 lots). Volume share is lower for crude (about 17% across commodity benchmarks) and FX (19–21% of ADV), but high for MGC (about 42%).
- **What is not covered.** No independent or academic study of CME micro spreads by hour was found, and CME's "Asia hours" averages do not isolate the first minutes after the 18:00 reopen.

### Cited Findings
- [P] CME OpenMarkets 2025, "Asia's Growing Gold Demand Fuels Surging Derivatives Market". — [CME OpenMarkets](https://cmegroup.com/openmarkets/metals/2025/Asias-Growing-Gold-Demand-Fuels-Surging-Derivatives-Market.html); [Kitco, 27 Aug 2025](https://www.kitco.com/news/article/2025-08-27/chinese-and-indian-gold-demand-are-fueling-asias-surging-derivatives-market); [IBKR reprint](https://www.interactivebrokers.eu/campus/traders-insight/securities/commodities/asias-growing-gold-demand-fuels-surging-derivatives-market/)
  - **Micro Gold's average bid/offer was 2.01 ticks across all hours and 1.98 ticks in Asian hours.** CME defines Asian hours as 06:00–18:00 Singapore time.
  - **Asian hours were about 42% of global MGC volume** as of Q2 2025.
- [P] CME (2018), "Liquidity of COMEX Gold & Silver is Excellent during Asia hours": GC had a tight **one-tick** bid/ask during almost all trading hours. — [CME](https://www.cmegroup.com/education/articles-and-reports/liquidity-of-comex-gold-and-silver-is-excellent-during-asia-hours)
- [B] Contradiction: third-party trading guides claim MGC can widen to **2–3 ticks in Asian hours versus 1 tick at US peak**, without citing data. This conflicts with CME's 1.98-tick Asian average, which is itself an average over the whole Singapore day. — [eltraderfinanciado](https://www.eltraderfinanciado.com/en/blog/gold-futures); [damnpropfirms](https://damnpropfirms.com/trading-guides/mgc-tick-value-micro-gold-futures-contract-specs/)
- [P] CME whitepaper (2023), WTI (standard CL, most-active month, Q1 2023): **1.34 ticks in Asia hours versus 1.35 all hours**, and best bid/ask size **6.71 versus 7.00 lots**. Asia hours were about 17% of the volume of six commodity benchmarks in 2022. — [CME](https://www.cmegroup.com/articles/whitepapers/leveraging-cme-group-asia-trading-hours-liquidity-for-cross-commodity-trading.html)
- [P] CME (2023, FY2022 data), FX futures (standard contracts). — [CME](https://www.cmegroup.com/articles/2023/unlocking-potential-during-asian-trading-hours-with-cme-fx-futures.html)
  - USD/JPY: Asian-hours average top-of-book spread **1.08 pips versus 1.09 full day**, ranging 1.03–1.15 pips during Asian hours. Asian hours were 21% of ADV.
  - AUD/USD: **0.66 pips versus 0.65 full day**, ranging 0.65–0.70. Asian hours were 19% of ADV.
- [P] CME's FX Market Profile tool shows order-book depth out to 10 levels, and the CME Liquidity Tool exists. No Asian-hours depth figures were published in the results. — [CME FX Market Profile](https://www.cmegroup.com/trading/fx/cme-fx-market-profile-tool.html); [CME Liquidity Tool](https://www.cmegroup.com/tools-information/cme-liquidity-tool.html)
- [P] Bulenox all-in commissions per side (Aug 2026): **MGC $0.76, MCL $0.76, M6A $0.50, 6J $2.36**. — [Bulenox Rates PDF](https://bulenox.com/legal/Bulenox-Rates.pdf)
- [B] Rollover (17:00 NY) spread widening for spot FX and gold is documented only by brokers (see section 1). No CME or academic source covers the futures reopen at 18:00 ET.

### Inferences
**[Calc] Round-trip cost estimates.** Each assumes one full spread crossed per round trip plus the Bulenox all-in commission, with no extra slippage.

| Contract | Spread cost | Commission (RT) | Total RT | In price terms | As share of notional |
|---|---|---|---|---|---|
| MGC | about 1.98 ticks ≈ $1.98 | $1.52 | **≈ $3.50** | ≈ $0.35/oz | **≈ 0.9 bp** at an assumed $3,800/oz |
| MCL | about 1–1.5 ticks (no micro data; CL averages 1.34) | $1.52 | **≈ $2.5–3.0** | — | **≈ 4–5 bp** at an assumed $60–70/bbl |
| M6A | at least 1 tick = $1.00 | $1.00 | **≥ $2.00** | ≈ 2 pips | **≈ 3 bp** at an assumed 0.65 |
| MJY | at least 1 tick = $1.25 | not found on the Bulenox sheet; ~$1 assumed | **≈ $2.25** | ≈ 4 USD/JPY pips | **≈ 2.7 bp** at an assumed 150 |
| 6J (standard) | 1 tick = $6.25 | $4.72 | **≈ $11** | — | ≈ 1.3 bp, but 10× the size |

- **Micro FX costs more relative to price.** The M6A tick (1 pip) is about 1.5 times the standard 6A's *average* Asian-hours spread (0.66 pip). The MJY tick (about 2.25 pips at 150) is about twice 6J's average (1.08 pips).
- **Gold is the cheapest micro to trade.** One tick is about 0.26 bp of notional for MGC, against about 1.5 bp for MCL, M6A and MJY. MGC is by far the least cost-constrained micro for small intraday edges.
- **The reopen window is not covered.** CME's "Asia hours" averages span 17:00/18:00–05:00/06:00 NY and include the more liquid London open. Spreads and depth in the first 15–60 minutes after the 18:00 ET reopen are probably worse than these averages, but no data were found. Strategies that enter at the reopen should measure their own fills.

### Gaps
- No independent or academic microstructure study of CME **micro** contracts (MGC, MCL, M6A, MJY) by hour of day was found.
- No CME-published Asian-hours spread or depth data exist for MCL, M6A or MJY; the available figures are for the standard contracts or for MGC.
- Data vintage: FX is FY2022, CL is Q1 2023, MGC is around Q2 2025. Spreads may differ in 2026.

---

## 5. Practical tradability: micro contract specifications and Bulenox product and session rules

### Takeaway
**Contract specs:**
- **MGC:** 10 oz, tick $0.10 = $1.00.
- **MCL:** 100 bbl, tick $0.01 = $1.00.
- **M6A:** AUD 10,000, tick 0.0001 = $1.00.
- **MJY:** JPY 1,250,000, tick 0.000001 = $1.25. MJY was relisted in February 2024. The older USD-denominated M6J was scheduled for delisting in March 2024.

**Bulenox (official pages):**
- It offers 41 CME Group futures, including metals, energies and FX.
- Its August 2026 rate sheet lists MGC, MCL, M6A and 6J. **MJY was not confirmed.**
- The trading day runs 17:00–16:00 CT. Positions must be flat by 15:59 CT, and overnight holding is prohibited (stated for Qualification and Fast Track Option 2). News trading is allowed.

### Cited Findings
**CME specifications**
- [P] **MGC (Micro Gold)** — [CME Micro Metals](https://www.cmegroup.com/markets/microsuite/metals.html); [CME Micro Gold & Silver overview](https://www.cmegroup.com/education/lessons/micro-gold-and-micro-silver-futures-product-overview); [CME Micro Metals brochure](https://www.cmegroup.com/trading/metals/files/PM264-e-micro-gold-and-silver-futures.pdf)
  - Contract: 10 troy ounces, one-tenth of GC.
  - Tick: $0.10/oz = **$1.00** per contract.
  - Delivery is physical through an "ACE" (Accumulated Certificate of Exchange).
  - Hours: Sunday 17:00 to Friday 16:00 CT, with a 60-minute daily break starting 16:00 CT.
  - Older fact cards list a Sunday 18:00 start and a 17:00 CT break, so check the current page. — [CME gold fact card](https://www.cmegroup.com/trading/metals/files/fact-card-gold-futures-options.pdf)
- [P] **MCL (Micro WTI)** — [CME fact card](https://www.cmegroup.com/trading/energy/files/micro-wti-crude-oil-futures-fact-card.pdf); [CME FAQ](https://www.cmegroup.com/education/articles-and-reports/micro-wti-crude-oil-futures-faq)
  - Contract: 100 barrels.
  - Tick: $0.01/bbl = **$1.00**.
  - Hours: Sunday to Friday 17:00–16:00 CT, with a daily 60-minute halt from 16:00 CT.
- [P] **M6A (Micro AUD/USD)**: AUD 10,000, tick 0.0001 USD per AUD = **$1.00**. — [CME Micro FX](https://www.cmegroup.com/markets/microsuite/fx.html)
- [P] **MJY (Micro JPY/USD)**: JPY 1,250,000, tick 0.000001 = **$1.25**. — [CME Micro FX](https://www.cmegroup.com/markets/microsuite/fx.html)
- [P] **Standard contracts:** 6J is JPY 12,500,000 with a 0.0000005 outright tick. 6A is AUD 100,000 with a 0.00005 tick. — [CME FX Product Guide 2026](https://www.cmegroup.com/markets/fx/fx-product-guide.html)

**Micro yen listing history**
- [P] An earlier MJY version stopped being listed after March 2022, with permanent delisting on 15 Mar 2022 (SER-8890, 1 Dec 2021). The USD/JPY micro (**M6J**) kept trading. — [CME SER-8890](https://www.cmegroup.com/notices/ser/2021/12/SER-8890.pdf); [CME Globex notice 21 Feb 2022](https://www.cmegroup.com/notices/electronic-trading/2022/02/20220221.html)
- [P] A Globex notice of 16 Oct 2023 set M6J's **permanent delisting for 18 Mar 2024**, subject to regulatory review. — [CME notice](https://www.cmegroup.com/notices/electronic-trading/2023/10/20231016.html)
- [P] SER-9326 (Jan 2024): MJY listed on Globex **effective 25 Feb 2024**, JPY 1,250,000, quarterly expiries. — [CME SER-9326](https://www.cmegroup.com/notices/ser/2024/01/SER-9326.pdf)

**Bulenox (official sources only)**
- [P] FAQ — [Bulenox FAQ](https://bulenox.com/faq)
  - **41 futures contracts on CME, CBOT, NYMEX and COMEX**: equity indices, energies, metals, FX, grains, livestock, plus Micro Bitcoin and Micro Ether.
  - Examples given: ES, NQ, YM, RTY, EMD, **CL**, NG, RB, **GC**, SI, HG, PL, 6E, 6B, **6J**.
  - Micro versions exist for most products, and standard and micro contracts can be mixed (1 standard = 10 micros).
  - **News trading is allowed**: no blackout windows and no forced closings around CPI, FOMC or NFP.
- [P] Rate sheet, "COMMISSIONS & INSTRUMENTS, All-in rates, per side (USD), Updated Aug/11/2026". — [Bulenox Rates PDF](https://bulenox.com/legal/Bulenox-Rates.pdf)
  - **M6A $0.50 per side ($1.00 round trip)**.
  - **MCL $0.76 per side ($1.52 round trip)**.
  - **MGC $0.76 per side ($1.52 round trip)**.
  - **6J $2.36 per side ($4.72 round trip)**.
  - Commissions are charged on entry and exit and are all-in (exchange and clearing fees included). They count toward drawdown and the daily loss limit.
  - **MJY did not appear in the excerpt**, which may have been truncated.
- [P] The Russian-language help page lists "E-micro Japanese Yen (M6J)" next to 6J. — [Bulenox RU help](https://bulenox.com/ru/help/)
- [P] Qualification account: the trading day runs **17:00 to 16:00 CT the next day**, and **all positions must be closed by 15:59 CT**. Weekends and holidays are not trading days, and **overnight holding is strictly prohibited**. The FAQ repeats the 15:59 CT close. — [Bulenox Qualification](https://bulenox.com/help-center/qualification); [Bulenox FAQ](https://bulenox.com/faq)
- [P] Fast Track Option 2 (end-of-day drawdown): same overnight prohibition, close before the 15:59 CT session end. — [Bulenox Fast Track](https://bulenox.com/help-center/fast-track)
- [P] The Funded account page covers account transitions, not hours or overnight rules. — [Bulenox Funded](https://bulenox.com/help-center/funded)

### Inferences
- **Asian-hours trading looks permitted.** The 18:00–03:00 ET Asian window sits at the start of Bulenox's trading day (17:00 CT = 18:00 ET). A trade opened in Asian hours and closed by 15:59 CT (16:59 ET) the same trading day does not appear to be "overnight holding" under the quoted rule. This is an inference from the rule text; confirm with Bulenox support.
- **MJY at Bulenox is unconfirmed.** The FAQ names 6J, and the Russian page lists M6J. CME scheduled M6J for delisting in March 2024 and relisted MJY, so the Russian page is probably outdated. The rate sheet excerpt shows no MJY. Ask Bulenox whether MJY is enabled on Rithmic accounts.
- **Commissions are a large share of the cost.** [Calc] The Bulenox commission is about 43% of the MGC round-trip cost ($1.52 of about $3.50) and about 50% for M6A.

### Gaps
- The full list of Bulenox's 41 contracts was not seen in an official English source. Whether **MJY** (and 1OZ gold) is enabled is unconfirmed.
- Funded and Master account rules on overnight holding, any restrictions at the 17:00 CT reopen or on holidays, and per-product contract limits were not found.
- Current CME Globex hours for metals and energy should be checked on the live contract pages, because older fact cards conflict with newer pages.
