# Japanese-market anomalies in the Asian session (Tokyo hours = 18:00-03:00 New York), as tradable through CME futures

**How to read the tags.** I could not open any full source document this session: WebFetch could not resolve cmegroup.com, boj.or.jp, bankofcanada.ca or centaur.reading.ac.uk (these hosts are outside the session's network allowlist), and the permission system refused a curl fallback. Every finding below therefore comes from web-search results.
- **[A]** = the primary source's own page (journal/SSRN/NBER/arXiv abstract, author PDF, exchange spec page, central-bank page) as returned by the search tool, often with verbatim fragments. This is the closest I could get to "verified at source", but I did not read the tables or the full text.
- **[S]** = seen only in a secondary summary: a blog, news item, aggregator, citing paper, or the search tool's own paraphrase or attribution.
- **[D]** = my own calculation or inference. It appears only in the "Inferences" sections.
- Evidence grade: **A** = top-3 journal, long sample; **B** = field journal, or central-bank or NBER working paper; **C** = new paper with unknown sample, preprint or simulation; **D** = blog, practitioner backtest or GitHub.

**Clock conversion used throughout [D].** JST = UTC+9 with no daylight saving. New York is UTC−5 (EST, early Nov to mid-Mar) or UTC−4 (EDT). So an hour X:00 JST falls at (X−14):00 New York in winter and (X−13):00 in summer, on the previous calendar day.

---

## 1. Intraday momentum in Japan: does the first half-hour (or overnight) return predict the last part of the Tokyo session? (Nikkei 225 / TOPIX, cash or futures)

### Takeaway
Japan is one of the few Asia-Pacific markets where Gao-Han-Li-Zhou-style market intraday momentum shows up:
- **ETF evidence (PBFJ 2023):** the effect is "mainly evident in China and Japan", and during COVID it persisted only in Japan.
- **Futures evidence (2026):** a new paper finds a reversal-then-momentum pattern directly in Nikkei 225 futures, conditioned on the previous day's S&P 500 return.

The 16-country study (JFM 2022) gives weak or unclear results for Japan. I found no study with Japan-specific results net of costs on futures, and none run on CME NKD or MNK. The idea is open, has not been tested by the project, and is unproven after costs.

### Cited Findings
**US benchmark**
- Gao, Han, Li, Zhou, "Market intraday momentum", *JFE* 129(2), 2018, pp. 394-414 (US market ETF):
  - The first half-hour return predicts the last half-hour return.
  - Per a search summary of the SSRN version, R² ≈ 2.0% on its own and ≈ 3.5% combined with the 12th half-hour.
  - The authors attribute it to day traders and informed traders.
  - [S], grade A. Sources: [JFE record](https://ideas.repec.org/a/eee/jfinec/v129y2018i2p394-414.html); [SSRN version PDF](https://www.smallake.kr/wp-content/uploads/2015/01/SSRN-id2440866.pdf)
- The project has already rejected the US version: "Momentum de la première demi-heure, Gao, Han, Li, Zhou (2018), rejeté à la porte 2 (p = 2,8 %, 1 % exigé)". That test was on US futures, not Japan. Source: `rea/PISTES.md` (local project file).

**Japan in multi-country studies**
- Li, Sakkas, Urquhart, "Intraday time series momentum: Global evidence and links to market characteristics", *Journal of Financial Markets* 57 (2022), 100619:
  - Covers 16 developed markets with high-frequency data.
  - Intraday time-series momentum (ITSM) is "economically sizable and statistically significant both in- and out-of-sample in most countries".
  - It is stronger when liquidity is low and volatility is high.
  - [A], grade B+. Sources: [EconPapers](https://econpapers.repec.org/article/eeefinmar/v_3a57_3ay_3a2022_3ai_3ac_3as138641812100001x.htm); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S138641812100001X)
- Same study, from search summaries of the manuscript ([S]). I could not read the Japan coefficients or their significance.
  - Significant first-to-last half-hour predictability in 12 of 16 markets, stronger in recessions.
  - Japan is covered with the Nikkei 225 cash index (RIC .N225, 09:00-15:00 local).
  - The working paper says a data "problem applies to Australia and Japan as well". The authors exclude Australia and Japan from part of the analysis, and the internet appendix refers to weak ITSM evidence in those markets.
  - The published and working-paper results appear to differ for Japan.
  - Sources: [accepted manuscript](https://centaur.reading.ac.uk/95566/1/Accepted-Version.pdf); [FoFI 2020 working paper](http://wp.lancs.ac.uk/fofi2020/files/2020/04/FoFI-2020-092-Zeming-Li.pdf)
- Limkriangkrai, Chai, Zheng, "Market intraday momentum: APAC evidence", *Pacific-Basin Finance Journal* 80 (2023), 102086. Tests first half-hour → last half-hour on ETFs from China, Hong Kong, Japan, Singapore and South Korea:
  - "Intraday momentum is mainly evident in China and Japan"; weak in South Korea; "Hong Kong SAR and Singapore appear to have no intraday momentum".
  - Volatility matters more than volume, and the effect is "not as pervasive in the APAC markets when compared to the US evidence".
  - Out-of-sample R² values come from recursive regressions.
  - "Over the COVID-19 crisis period, among the APAC markets exhibiting intraday momentum, the IMOM effect only persists in Japan". Another summary of the same paper says the effect is weaker during COVID in the markets that show it.
  - Not retrieved: sample period, which Japanese ETF was used, R² values, any transaction-cost test.
  - [A], grade B. Sources: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0927538X2300152X); [Monash record](https://research.monash.edu/en/publications/market-intraday-momentum-apac-evidence/); [open-access PDF](https://researchmgt.monash.edu/ws/files/519509174/494419119_oa.pdf)
- Xu, Li, Singh, Li, "Cross-Market Intraday Time-Series Momentum" (SSRN 4651331), published as "Cross-market overnight time-series momentum", *Journal of International Financial Markets, Institutions & Money* 105 (Dec 2025), 102239:
  - The US market's last half-hour return predicts the next day's first half-hour return in international markets, in- and out-of-sample.
  - The strategy's profit "remains positive after accounting for transaction costs". It is stronger when the international market's bid-ask spread is low or information uncertainty is high.
  - Not retrieved: country list, Japan coefficients, cost model, sample.
  - [A], grade B. Sources: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1042443125001295); [IDEAS](https://ideas.repec.org/a/eee/intfin/v105y2025ics1042443125001295.html); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4651331)
- A cross-market paper citing Li et al. reports positive coefficients for predicting the last half-hour: on the overnight return in China and Hong Kong, and on the first half-hour return in Australia, **Japan**, Korea and Taiwan. The search tool attributed this; it is most likely the Xu et al. SSRN paper. [S]. Source: [SSRN 4651331](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4651331)

**Japan, futures**
- "How the prior day's S&P 500 returns influence the intraday returns of Nikkei 225 futures", *Finance Research Open* (2026):
  - After a higher prior-day S&P 500 return, Nikkei 225 futures return **less in the first 30 minutes** of Japanese trading and **more in the 30 minutes before the close**.
  - The authors attribute the momentum to different rebalancing frequencies across investors. They attribute the reversal to noise traders overreacting, then arbitrage correcting it.
  - Strong intraday reversals are less likely during financial crises.
  - Not retrieved: authors, sample, effect sizes, costs.
  - [A], grade C (new journal, details unknown). Source: [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S3050700626000204)

**Mechanism evidence from global futures**
- Baltussen, Da, Lammers, Martens, "Hedging demand and market intraday momentum", *JFE* 142(1), 2021, pp. 377-403:
  - Covers over 60 futures (equities, bonds, commodities, currencies), 1974-2020.
  - The return before the last 30 minutes predicts the last 30 minutes "everywhere", and the effect reverts over the following days.
  - Linked to the gamma hedging of options market makers and leveraged ETFs.
  - I did not find whether a Nikkei contract is in the sample, or its result.
  - [A], grade A. Sources: [EconPapers](https://econpapers.repec.org/RePEc:eee:jfinec:v:142:y:2021:i:1:p:377-403); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3760365)
- Baltussen, Da, Soebhag, "End-of-Day Reversal" (working paper, Nov 2024):
  - US-listed individual stocks show sharp cross-sectional reversals in the last 30 minutes.
  - The authors call it "complementary" to market-level intraday momentum.
  - US only. [A]. Sources: [PDF](https://www3.nd.edu/~zda/EOD.pdf); [Erasmus news](https://www.eur.nl/en/ese/news/end-day-reversal-pattern-second-place-quantpedia-awards-2025)

### Inferences
- [D] **CME clock for a Japanese intraday-momentum trade.**
  - Signal: Nikkei return from the previous Tokyo close to 9:30 JST, which is 19:30 EST / 20:30 EDT (from my recollection, below, that the first half-hour is measured from the previous close).
  - Trade: the last Tokyo half-hour. Since the Tokyo Stock Exchange (TSE) moved its close on 5 Nov 2024, that is 15:00-15:30 JST = **01:00-01:30 EST / 02:00-02:30 EDT**. Before that date it was 14:30-15:00 JST = 00:30-01:00 EST / 01:30-02:00 EDT.
  - Everything falls inside the allowed 18:00-03:00 New York window. Any backtest must switch the "last half-hour" window on 5 Nov 2024.
- [D] **Gao et al. measure the first half-hour from the previous day's close.** I recall the JFE abstract saying "the first half-hour return on the market as measured from the previous day's market close". This is my recollection, not re-verified this session. If it is right, the Japanese signal includes the overnight gap. NKD/MNK trade through that gap, so the signal is easy to compute on CME data, and the gap itself is never "captured".
- [D] **The 2026 futures paper implies a conditional rule:** after a strong US day, fade the Nikkei over its first 30 minutes, then go with the day's move into the close. It also suggests that continuation (breakout) rules at the Tokyo open should do poorly after big US days. That fits the project's own finding that breakouts tend to reverse rather than continue (`asie/README.md`).
- [D] **Hurdle for MNK.** A round trip costs about 2 ticks plus about $2 of fees ≈ 2.8 bp at Nikkei 50,000 (see section 6). The last half-hour would have to deliver well above 3 bp per trade on average. No Japan study reports net returns, so this is unknown.
- [D] **This idea is new for the project.** Testing GHLZ-style momentum on a Nikkei series (MNK/NKD, or a Nikkei CFD series if HistData offers one) is not the "breakout of the first 30/60 Tokyo minutes" already rejected. I have not checked whether HistData offers a Nikkei series.

### Gaps
- Japan coefficients, t-statistics and net results in Li-Sakkas-Urquhart (2022): the tables could not be read.
- Limkriangkrai et al. (2023): sample, ETF ticker, R², whether costs were applied.
- The 2026 *Finance Research Open* paper: authors, sample period, magnitudes.
- Xu et al. (2025): whether Japan is in the sample, and Japan-specific results.
- Baltussen et al. (2021): whether a Nikkei future is in the sample.
- I found no study testing intraday momentum on CME NKD or MNK, and none reporting Japan-specific returns net of costs on futures.
- Older classics not checked this session: Iihara, Kato, Tokunaga (1996, *J. Futures Markets*) on intraday cash-futures dynamics in Japan; Hamao, Masulis, Ng (1990, *RFS*).

---

## 2. Leveraged and inverse ETF rebalancing in Japan (NEXT FUNDS Nikkei 225 Leveraged ETF 1570 and similar): end-of-day flows and price effects on Nikkei futures

### Takeaway
The mechanism is documented: Japanese leveraged and inverse funds rebalance in Nikkei 225 futures near the close, and the trade is pro-cyclical.
- **BOJ (2016):** Nikkei futures tended to keep moving in the direction of the day during 15:00-15:15. The BOJ also judged the flow small relative to futures volume.
- **Since 2016:** the only Japan-specific work I found is a 2018 trade-press article and artificial-market simulations. There is no recent empirical measure of the price effect, no net-of-cost strategy, and no documentation of traders exploiting it.

My rough sizing for 1570 alone (in Inferences) gives about ¥9bn of futures per 1% Nikkei move, which is small.

### Cited Findings
- Bank of Japan Review 2016-E-1, "Recent Developments in Leveraged Investment Funds" (May 2016):
  - Households were rapidly increasing stock investment through leveraged funds (leveraged ETFs and mutual funds).
  - The funds rebalance their Nikkei 225 futures near the close, with transactions starting around 15:00 (the cash close at the time).
  - During 15:00-15:15, Nikkei 225 futures tended to move **in the same direction as the Nikkei 225 had moved until 15:00**, so rebalancing demand is pro-cyclical.
  - Rebalancing "may amplify volatility", but its size relative to futures trading volume "looks small". Market participants often blame large closing moves on it.
  - The paper computes the ratio of 15:00-15:15 volume to 9:00-15:15 volume, but the figure was not retrievable.
  - [A]/[S], grade B. Source: [BOJ Review](https://www.boj.or.jp/en/research/wps_rev/rev_2016/data/rev16e01.pdf)
- *Kinyū Zaisei Jijō* (金融財政事情) 69(11), 19 Mar 2018, pp. 20-23: the title translates as "Leveraged ETFs and the effect of their rebalancing on the futures market: individual investors' speculative demand widens volatility". Title only; I did not see the text. [A]. Source: [CiNii record](https://cir.nii.ac.jp/crid/1574232261571373696)
- Artificial-market simulations by Mizuta and co-authors, including Yagi, Maruyama, Mizuta. Simulation only, grade C. [A]
  - Rebalancing (buy after rises, sell after falls) can destabilise the underlying price.
  - Volatility rises with fund size.
  - Smaller minimum rebalancing orders have a larger effect on price formation.
  - In a crash, the ETF's investors benefit from futures liquidity more than futures investors do.
  - Sources: [arXiv 2010.13036](https://arxiv.org/abs/2010.13036); [JSAI 2024](https://www.jstage.jst.go.jp/article/pjsai/JSAI2024/0/JSAI2024_2F1GS504/_article/-char/ja); [JASMIN 2015](https://www.jstage.jst.go.jp/article/jasmin/2015f/0/2015f_121/_pdf/-char/en)
- Worked example from a Japanese broker. A 2x fund with ¥10bn of net assets holds ¥20bn of index futures. After a 10% rise, leverage falls to 1.83x, so the fund buys more futures to return to 2x. [A]. Source: [Matsui Securities column](https://www.matsui.co.jp/fund/column/bull-bear/)
- NEXT FUNDS 1570:
  - Tracks the Nikkei 225 Leveraged Index, twice the daily Nikkei move [A].
  - Exposure is mainly through Nikkei 225 futures plus cash [S].
  - The issuer says that at times like the close, when arbitrage works poorly, supply and demand can open temporary gaps between the ETF and its value [A].
  - Sources: [NEXT FUNDS 1570](https://nextfunds.jp/en/lineup/1570/); [NEXT FUNDS explainer (Japanese)](https://nextfunds.jp/semi/article19.html); [Twelve Data](https://twelvedata.com/markets/221417/etf/jpx/1570)
- Size of 1570. All three figures are approximate or undated. [S]
  - Nomura's filings via JPX show total net assets of roughly ¥430-457bn around 2024-2025 (the tables were hard to read).
  - TrackInsight: about €3.9bn on 5 Nov 2026.
  - TradingView: about ¥251bn under management with about ¥391bn of one-year outflows, undated.
  - Sources: [JPX filing (2025)](https://www2.jpx.co.jp/disc/15700/140120250701505507.pdf); [TrackInsight](https://www.trackinsight.com/en/fund/1570); [TradingView](https://www.tradingview.com/symbols/TSE-1570/analysis)
- US mechanism evidence. Mathis & Moerke (FoFI 2022 working paper): "a one-standard-deviation increase in leveraged ETF rebalancing flows increases end-of-day returns by 430% of the average return in the last half hour". US data. [A], grade B/C. Source: [working paper](https://wp.lancs.ac.uk/fofi2022/files/2022/08/FoFI-2022-027-Mathis-Moerke.pdf)
- Survey, *Quantitative Finance and Economics* (2024):
  - The literature consistently finds statistically significant links between ETF rebalancing demand and late-day returns and volatility.
  - Policymakers' concerns are "not supported by the overall empirical evidence".
  - Mostly US evidence. [A]. Source: [AIMS QFE survey](https://www.aimspress.com/article/doi/10.3934/QFE.2024031?viewType=HTML)
- Baltussen et al. (JFE 2021) attribute market intraday momentum partly to leveraged-ETF and options gamma hedging (see section 1). [A]
- Change in the close: the TSE has run a closing auction at 15:30 since 5 Nov 2024. For Nikkei futures, Osaka Exchange (OSE) proposed a day-session closing auction at 15:45 (see section 6). [A]

### Inferences
- [D] **Rebalancing formula.** The futures trade needed ≈ L(L−1) × r × NAV, where L is the leverage, r the index return and NAV the fund's net assets.
  - +2x fund: 2·r·NAV. −1x fund: 2·r·NAV. −2x fund: 6·r·NAV.
  - Leveraged and inverse funds therefore all **buy after up days and sell after down days**.
  - This is the standard Cheng & Madhavan (2009) result, not re-verified this session. It matches the Matsui example exactly: r = 10% and NAV = ¥10bn give ¥2bn bought.
- [D] **Sizing 1570 alone.** At NAV ≈ ¥450bn, a 1% Nikkei move requires ≈ ¥9bn of futures. That is ≈ $60m at ¥150 per dollar, or ≈ 240 NKD-equivalents at Nikkei 50,000 (NKD notional ≈ $250k). A 4% day would need ≈ ¥36bn. Inverse funds and leveraged mutual funds add to this; their size was not found. This supports the BOJ's view that the flow is "small", except on large-move days.
- [D] **Timing on the CME clock.** The flow targets the OSE futures close: 15:45 JST under the proposal = **01:45 EST / 02:45 EDT**. NKD/MNK only feel it through arbitrage with OSE. The trade that would capture it is the section-1 trade: on days with a large move by about 15:00 JST, go with the day's direction into the close. Rebalancing is the main proposed driver of Japanese last-half-hour momentum.
- [D] **The closing-auction reform may have changed the flow.** Since Nov 2024, flows can be routed into the 15:30 cash auction and the 15:45 futures auction rather than spread over 15:00-15:15. That could shrink any pre-close drift. No study tests this.
- [D] I found no evidence of a documented front-running community. The issuer's own text says arbitrage is weakest at the close.

### Gaps
- No empirical study after 2016 measuring the price impact of Japanese leveraged-ETF rebalancing on Nikkei futures in the last 15-30 minutes, and no net-of-cost strategy.
- The BOJ (2016) volume ratio and any estimated price coefficient: not retrieved.
- Current combined assets of all Japanese leveraged and inverse Nikkei products (ETFs plus mutual funds, e.g. the double-inverse ETF 1357): not found.
- The effect of the Nov 2024 closing-auction reform on rebalancing execution: not studied.
- Whether Baltussen et al.'s gamma proxy covers Japan: unknown.

---

## 3. Effects around the Tokyo cash open (9:00 JST) and the lunch break / afternoon reopen on Nikkei futures

### Takeaway
**Open.** The classic studies find that US information is absorbed at the Tokyo open, with no lagged spillover except New York→Tokyo after the 1987 crash. The "Japan rises at night" result (1986-1998) is a cash-index effect linked to stale opening prices. The only recent, futures-specific open effect is the 2026 finding that Nikkei futures reverse in their first 30 minutes after strong US days.

**Lunch.** The best-documented lunch/afternoon flow was the Bank of Japan's ETF buying after weak mornings. The BOJ placed its orders during lunch while Nikkei futures kept trading. That anomaly ended when purchases stopped on 19 March 2024. Before then it was already being anticipated: a 2026 paper finds a volume surge but little or no price movement in futures at lunch on expected intervention days.

### Cited Findings
**Tokyo open**
- Lin, Engle, Ito, "Do Bulls and Bears Move Across Borders?", *RFS* 7(3), 1994, pp. 507-538 (NBER WP 3911):
  - Tokyo daytime returns are correlated with New York overnight returns, and vice versa.
  - "Except for a lagged return spillover from New York to Tokyo for the period after the Crash, there are no significant lagged spillovers in returns or in volatilities."
  - [A], grade A. Sources: [NBER](https://www.nber.org/papers/w3911); [IDEAS](https://ideas.repec.org/a/oup/rfinst/v7y1994i3p507-38.html)
- "Stock prices in Japan rise at night" (*Japan and the World Economy*, early 2000s):
  - "Between the years of 1986 and 1998 there has been a systematic and consistent difference": the Nikkei Average tends to rise during non-trading hours.
  - Partly linked to the batch-auction opening (stale or zero-return opens).
  - [A], grade B (old). Source: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S092214250200049X)
- Knuteson (arXiv 2020): major indices worldwide, Japan included, show large positive overnight and negative intraday returns over decades; the cause is unknown. Single author, contested. [A], grade C. Source: [arXiv 2010.01727](https://arxiv.org/pdf/2010.01727)
- Nikkei 225 constituents: "A weak negative correlation between overnight and daytime return" (physics-style correlation studies). [A], grade C. Sources: [Physica A](https://www.sciencedirect.com/science/article/abs/pii/S0378437118313116); [arXiv 0903.0993](https://arxiv.org/pdf/0903.0993)
- *Finance Research Open* (2026): after strong US days, Nikkei futures fall more in the first 30 minutes (see section 1). [A]
- Xu et al. (2025): the US last half-hour predicts the next day's first half-hour in other markets, still positive after costs (see section 1). [A]

**Lunch break and afternoon (cash closes 11:30-12:30 JST; futures keep trading)**
- Ito, Lyons, Melvin, "Is There Private Information in the FX Market? The Tokyo Experiment" (*JF* 1998; NBER WP 5936). This is about the yen, not equities.
  - The Tokyo interbank FX market closed for lunch (12:00-13:30) until the restriction was lifted in 1994.
  - Afterwards, "lunch return variance doubles with the introduction of trading", and the morning U-shape in volatility disappears. The authors read this as evidence of private information.
  - [A], grade A. Sources: [NBER](https://www.nber.org/papers/w5936); [FRBSF Economic Letter 1997](https://www.frbsf.org/research-and-insights/publications/economic-letter/1997/12/explaining-trading-volume-in-foreign-exchange-lessons-from-tokyo/)
- "Intraday and interday behavior of the TOPIX" (*Pacific-Basin Finance Journal*, 1993): minute data show intraday price reversals and irregularities at the morning and afternoon closes. [S], grade B (old). Source: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/0927538X9390017C)
- "Analysis of Realized Volatility in Two Trading Sessions of the Japanese Stock Market" (arXiv 1304.6006) exists; content not retrieved. [A, title only]. Source: [arXiv](https://arxiv.org/pdf/1304.6006)

**BOJ ETF purchases: the "weak morning → afternoon buying" rule, now defunct**
- Market belief. [S] Sources: [Cogent Economics & Finance 2022](https://www.tandfonline.com/doi/full/10.1080/23322039.2022.2111782); [Bank of Japan as a Contrarian Stock Investor](https://www.researchgate.net/publication/341267437_Bank_of_Japan_as_a_Contrarian_Stock_Investor_Large-Scale_ETF_Purchases)
  - "From 2010 to 2014, it was speculated that falls of greater than 1% in the TOPIX index in the morning session triggered BoJ ETF purchases in the afternoon session."
  - For 2010-2013 this was the widely believed "1% rule".
  - Another study estimates that the cutoff changed over time.
- Fukui & Yagasaki, "The Impact of Central Bank Stock Purchases: Evidence from Discontinuities in Policy Rules" (ESRI Discussion Paper 376, Jan 2023; SSRN 4365184; 2026 draft):
  - Uses the discontinuity in the BOJ rule ("intervene when the index falls more than X% in the morning").
  - The BOJ submitted its orders during the lunch break, before the afternoon open.
  - The effect on **lunchtime returns** was positive and grew over the sample.
  - ESRI version, as summarised: purchases worth 1% → about 1-2% price rise.
  - The 2026 draft reportedly finds the stock-price impact depends on the regime ("virtually no detectable impact" in normal times). That summary was unclear.
  - [A]/[S], grade B. Sources: [ESRI DP](https://www.esri.cao.go.jp/en/esri/content/e_dis376.pdf); [author draft](https://masaofukui.github.io/BoJ_main.pdf); [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4365184)
- Harada & Okimoto (RIETI DP 19-E-014): on BOJ purchase days, afternoon returns of Nikkei 225 stocks were significantly higher than those of non-Nikkei-225 stocks. [S] Sources: [RIETI](https://www.rieti.go.jp/jp/publications/dp/19e014.pdf); [ResearchGate](https://www.researchgate.net/publication/332233888_The_BOJ's_ETF_purchases_and_its_effects_on_Nikkei_225_stocks)
- One event study in this literature; the search tool did not say which (the *JFS* 2023 or Cogent 2022 paper). [S]
  - When purchases were expected, the morning TOPIX return was deeply negative, afternoon returns were typically negative, and next-morning returns were about zero.
  - After *unexpected* operations, prices fell significantly the next morning, so the effect was temporary.
  - **Contradicted by** Charoenwong, Morck, Wiwattanakantang (NBER WP 25525): "neither panel shows any evidence of a reversal".
  - Sources: [JFS 2023](https://www.sciencedirect.com/science/article/abs/pii/S1572308923000025); [Cogent 2022](https://www.tandfonline.com/doi/full/10.1080/23322039.2022.2111782); [NBER w25525](https://www.nber.org/system/files/working_papers/w25525/revisions/w25525.rev2.pdf)
- Ko, "Market anticipation and intraday trading: Evidence from BOJ ETF purchases", *Finance Research Letters* 91 (2026), 109421:
  - Cash closes for lunch while futures stay open.
  - On anticipated intervention days, Nikkei 225 futures volume surges during lunch "despite little or no price movement".
  - Per another search summary of the same paper, overnight and morning returns are weaker on intervention days, while lunch and afternoon returns differ little.
  - [A]/[S], grade B. Source: [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1544612325026704)
- Bouffler, Kwan, Liang, Philip (*Financial Review* 58(1), 2023): stocks with more BOJ demand earn higher abnormal returns on purchase dates, only partly reverting. [A] Source: [Wiley](https://onlinelibrary.wiley.com/doi/10.1111/fire.12323)
- End of the program:
  - "No purchases of ETFs and J-REITs shall be conducted under these terms and conditions on or after March 19, 2024." [A] Sources: [BOJ terms](https://www.boj.or.jp/en/mopo/measures/term_cond/yoryo85.htm); [ETF Stream](https://www.etfstream.com/articles/bank-of-japan-halts-etf-buying-in-policy-overhaul)
  - The BOJ announced sales in Sept 2025 and began selling in Jan 2026, at ¥330bn a year at book value (more than 100 years to sell everything). [S] Source: [Jiji via Adnkronos](https://english.adnkronos.com/2026/02/03/boj-begins-unloading-etfs-in-jan/)

### Inferences
- [D] **Tokyo session on the New York clock.** The lunch times are not re-verified this session. Ko (2026) confirms that cash closes for lunch while futures trade.

| Tokyo event (JST) | NY winter (EST) | NY summer (EDT) |
|---|---|---|
| Cash open 9:00 | 19:00 | 20:00 |
| Tokyo FX fixing 9:55 | 19:55 | 20:55 |
| Morning close 11:30 | 21:30 | 22:30 |
| Afternoon reopen 12:30 | 22:30 | 23:30 |
| Cash close 15:30 (15:00 before 5 Nov 2024) | 01:30 (01:00) | 02:30 (02:00) |
| OSE futures day-session close 15:45 (proposal) | 01:45 | 02:45 |

- [D] **The lunch flow is gone.** The only mechanical, documented lunch-time flow in Nikkei futures (BOJ orders after weak mornings) has been dead since 19 March 2024. Ko (2026) indicates it was largely priced by anticipation before then. BOJ selling at ¥330bn a year is about ¥1.3bn per business day, which is not a comparable flow. This is not a current edge.
- [D] **The open.** NKD trades through US hours, so US-day information is already in its price before 9:00 JST. The Japanese "overnight premium" is a cash-index measurement (stale opens), not a futures return. What remains testable on NKD/MNK is the 19:00-19:30 EST (20:00-20:30 EDT) return conditioned on the prior S&P 500 day, which is negatively related per the 2026 paper. It is untested net of costs.
- [D] The Lin-Engle-Ito result (no lagged spillover) and the reversal result fit together: the Tokyo open may overshoot the US move and then partly correct within 30 minutes.

### Gaps
- No post-2010 study of Nikkei futures returns specifically around the 11:30 morning close or the 12:30 reopen. Behaviour after the BOJ exit is undocumented.
- The size of the 2026 first-30-minute reversal and the dates it covers: not retrieved.
- Threshold values of the BOJ rule by period (1% before 2014; later values not verified) and the frequency of purchases after the 2021 policy review: not retrieved.
- Barbon & Gianinazzi (2019, *Review of Asset Pricing Studies*) on BOJ ETFs and Covrig & Melvin (2002) on price discovery in Tokyo: not checked this session.

---

## 4. Tokyo fixing (9:55 JST) and gotobi days for USD/JPY: size before costs, and tradability on CME yen futures after costs

### Takeaway
The flow is real and well documented:
- the dollar appreciates in the run-up to the Tokyo fix and partly reverses afterwards (*JF* 2024);
- banks' fixing prices are biased toward a stronger dollar and order flow is tilted toward dollar buying (*JIE* 2017);
- gotobi days (the 5th, 10th, 15th... of the month) amplify it.

But it is small. Before costs it is about 2.5 bp for the dollar portfolio around the Tokyo/ECB fixes, and about 3-7 pips on gotobi USD/JPY in secondary sources. The JF authors say short-term profits from "trading the fix" seem "almost impossible". On CME, the round-trip cost is about 3 pips on 6J and 8 pips on MJY, so the edge is at best about zero on 6J and negative on MJY. Nothing published in 2020-2026 overturns the project's rejection.

Note on the brief: "Bessho, Ito, Yamada" appears to merge two papers. The gotobi paper is **Bessho, Sugimoto, Suzuki (2023)**; the fixing papers are **Ito & Yamada (2015/2016/2017)**.

### Cited Findings
- Krohn, Mueller, Whelan, "Foreign Exchange Fixings and Returns around the Clock", *JF* 79(1), 2024, pp. 541-578 (Bank of Canada Staff WP 2021-48):
  - "The U.S. dollar appreciates in the run-up to foreign exchange fixes and depreciates thereafter, tracing a W-shaped return pattern around the clock."
  - The fixes are Tokyo (9:55 JST = 7:55 or 8:55 pm ET in the authors' slides), Frankfurt (ECB) and London.
  - Explanation: dealers intermediate unconditional demand for dollars at the fixes and bear inventory risk.
  - [A], grade A. Sources: [EconPapers](https://econpapers.repec.org/RePEc:bla:jfinan:v:79:y:2024:i:1:p:541-578); [Bank of Canada WP](https://www.bankofcanada.ca/2021/10/staff-working-paper-2021-48/); [WRAP](https://wrap.warwick.ac.uk/id/eprint/177333)
- Krohn et al., size and sample. [S] Sources: [WU 2022 working paper](https://www.wu.ac.at/fileadmin/wu/d/ri/isk/VSFX_2022/Paper/Session_III_1a_Krohn__foreign_Exchange_Fixings_Returns_Around_The_Clock_0712.pdf); [BIS slides](https://www.bis.org/events/221213_bis_bdi_ecb_exchange_rates/mueller.pdf)
  - The dollar portfolio moves about **2.5 bp** in the run-up to the Tokyo and European fixes and recovers about as much afterwards (2022 version).
  - Sample Jan 1999 – Dec 2019, an equal-weighted portfolio of nine currencies against the dollar, with a robustness check back to 1986.
- Krohn et al., tradability. [A] Sources: [AEA 2020 version](https://www.aeaweb.org/conference/2020/preliminary/paper/2dedYfDH); [ResearchGate](https://www.researchgate.net/publication/376621580_Foreign_Exchange_Fixings_and_Returns_around_the_Clock)
  - Annualised Sharpe ratios of 0.5-0.8 "from trading the longer windows", after daily trading and transaction costs, and higher with spreads cut by 50%.
  - But "it seems almost impossible to reap short-term profits from 'trading the fix'".
- Ito & Yamada, "Puzzles in the Tokyo fixing in the forex market: Order imbalances and Bank pricing", *JIE* 109 (2017), pp. 214-234 (NBER WP 22820, 2016). Data: high-frequency USD/JPY and EUR/JPY, 1999-2013 [S]. [A], grade B+.
  - Three puzzles: price spikes at the fix despite high liquidity; order flow tilted toward buying dollars before the fix; bank-announced fixing rates tilted toward a stronger dollar.
  - "Before 2008, the fixing prices set by banks were biased upward, and higher than the highest transaction price during the fixing time window."
  - After 2008 the fixing prices were still above the median transaction price, which gives banks predictable profits.
  - "Calendar effects also matter for determination of the fixing rate and the price fluctuation around fixing time."
  - Sources: [IDEAS](https://ideas.repec.org/a/eee/inecon/v109y2017icp214-234.html); [NBER w22820](https://www.nber.org/papers/w22820); [Columbia WP 352](https://business.columbia.edu/sites/default/files-efs/imce-uploads/Research/Research_Papers/WP_352.Ito-Yamada.Tokyo_Fixing_Puzzles.pdf)
- Ito & Yamada, "Was the Forex Fixing Fixed?" (NBER WP 21518, 2015). [A] Sources: [NBER](https://www.nber.org/papers/w21518); [Columbia WP 344](https://business.columbia.edu/sites/default/files-efs/imce-uploads/Research/Research_Papers/WP_344.Ito_.Yamada.Was_Forex_Fixing_Fixed.Final_.8-26-15%20(1).pdf)
  - Little evidence of spikes around the London fix.
  - In Tokyo, banks set the fix themselves.
  - Order imbalances are positive around 00:55 GMT "almost every day, but only for the USD/JPY".
- Bessho, Sugimoto, Suzuki, "Forex Trading Strategy That Might Be Executed Due to the Popularity of Gotobi Anomaly" (arXiv 2301.13204, Jan 2023):
  - Builds on prior evidence that USD/JPY tends to rise toward 9:55 on gotobi days, and tests strategies for traders who already know about it.
  - Data: USD/JPY, 2018-2020.
  - One hypothesis enters long dollar / short yen "around 3 a.m." (time zone not stated in the summary).
  - Banks may buy dollars early to cover expected customer demand, so Japanese firms' wealth could "leak" to FX traders.
  - Detailed results were not retrieved. A blog notes the short sample and parameters chosen on the same data.
  - [A]/[S], grade C. Sources: [arXiv](https://arxiv.org/abs/2301.13204); [Forex Detox](https://forexdetox.substack.com/p/the-tokyo-fix-reversal-anomaly-on)
- Ranaldo, "Segmentation and Time-of-Day Patterns in Foreign Exchange Markets" (*JBF* 2009; SNB WP 2007-3):
  - A currency depreciates during its home trading hours and appreciates during foreign hours. The pattern is persistent and significant after calendar effects.
  - Working-paper data: 1993-2005. Japanese hours for yen/dollar are about 00:00-04:00 GMT.
  - Explanation: domestic agents are net buyers of foreign currency during their own hours (liquidity and inventory).
  - [A]/[S], grade B. Sources: [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=960209); [SNB WP 2007-3](https://pdfs.semanticscholar.org/5a5e/757c9bacaa7be6faff7328e57cbb01b3b380.pdf)
- Breedon & Ranaldo, "Intraday Patterns in FX Returns and Order Flow" (*JMCB* 45(5), 2013, pp. 953-965; SNB WP 2011-04):
  - Currencies depreciate during local trading hours across many currencies and time zones, and order flow mirrors this.
  - They find no significant pattern during foreign hours.
  - The working paper has a table for a simple open-to-close strategy; I did not see its net-of-cost results.
  - [A], grade B. Sources: [Wiley](https://onlinelibrary.wiley.com/doi/abs/10.1111/jmcb.12032); [SNB WP](https://www.snb.ch/en/mmr/papers/id/working_paper_2011_04)
- Practitioner evidence. All [S], grade D, low quality.
  - **Alpha in Academia**, 20 years of 1-minute USD/JPY data: +4.54 pips gross per gotobi trade over 1,175 windows, profit factor 1.62; about +3 pips after a 1.5-pip round trip. Results are sensitive to the exit bar, and the author cannot prove the bar close is the fixing moment. [Alpha in Academia](https://www.alphainacademia.com/p/can-you-beat-the-market-by-trading)
  - **Forex Detox**, summarising Ito-Yamada data for 1999-2013:
    - mean gotobi pre-fix moves of 7.25 pips on USD/JPY and 7.60 on GBP/JPY (start of the window not stated);
    - from 09:00 to 09:55, the cross-pair mean is only 1.21 pips;
    - the post-fix yen reversal is significant across seven yen crosses.
    - Unverified; the search tool flagged it as internally inconsistent. [Forex Detox](https://forexdetox.substack.com/p/the-tokyo-fix-reversal-anomaly-on)
  - **GitHub repo** (Exness tick data): +3.18 pips net per trade 2016-2026 (t 2.70, 55% wins, profit factor 1.33), with 1.5-2.4 pips of average spread paid. [GitHub](https://github.com/prathamesh-git9/gotobi-fx-bot)
  - **Pre-registered GitHub study:**
    - fading the move from 09:55 to 15:00 earns +0.148R per trade since 2016 (n = 771, Holm p = 0.012);
    - costs are 0.11R, about 2 pips against a 19.5-pip median stop;
    - at double costs the profit falls to +0.035R;
    - a companion study, "Tokyo fix every day vs gotobi", is labelled "UNCLEAR".
    - [PR 878](https://github.com/vazxanana/macro-dashboard/pull/878); [PR 917](https://github.com/vazxanana/macro-dashboard/pull/917)
  - **ForexFactory**, 7 years of tick data: real in-sample, but out of sample 2 of 3 robust-looking entry windows died. **YuraTrading**: "Real but Rejected". [ForexFactory](https://www.forexfactory.com/thread/1407332-gotobi-tokyo-fix-anomaly-7-years-of-usdjpy-tick); [YuraTrading](https://yuratrading.com/blogs/gotobi-tokyo-fix)
- The project's own results:
  - Tokyo fixing (machine 5): the effects exist but are 2-3 times smaller than costs.
  - Gotobi (machine 6): fails the 2023-2026 vault.
  - Source: `asie/README.md` (local project file).

### Inferences
- [D] **Direction on CME.** 6J and MJY are quoted in dollars per yen. "USD/JPY up into the fix" therefore means **short 6J/MJY** until 9:55 JST (19:55 EST / 20:55 EDT). A post-fix reversal trade means long 6J afterwards.
- [D] **Cost against edge**, at USD/JPY = 150, where 1 pip ≈ 0.67 bp and 1 bp ≈ 1.5 pips:
  - Assumptions follow the project's convention of 1 tick of slippage per order. Fees are assumed: $1 per order on micros and about $2.50 per order on 6J. These fee levels are not sourced.

| Contract | Notional | 1 tick | Round trip (2 ticks + fees) | In pips |
|---|---|---|---|---|
| 6J (¥12.5m) | ≈ $83,000 | $6.25 = 0.75 bp ≈ 1.1 pip | ≈ $17.5 ≈ 2.1 bp | ≈ 3.2 |
| MJY (¥1.25m) | ≈ $8,300 | $1.25 = 1.5 bp ≈ 2.25 pips | ≈ $4.5 ≈ 5.4 bp | ≈ 8.1 |

  - Gross edges in the sources: about 2.5 bp ≈ 3.75 pips (Krohn et al., dollar portfolio, not yen-specific); about 4.5 pips ≈ 3 bp (practitioner gotobi); 7.25 pips (blog). Net on 6J: about 0 to +1.5 pips a trade, fragile. Net on MJY: negative.
  - This is consistent with Krohn et al. ("almost impossible") and with the project's findings (effect 2-3 times smaller than costs).
- [D] **The Ranaldo pattern and the fix are probably the same flow.** The yen weakening during Tokyo hours and the pre-fix dollar demand both come from Japanese importers and investors buying dollars in their own morning. That would make the "Tokyo hours" and "pre-fix" trades largely one and the same opportunity, already rejected.
- [D] **Nothing new since the project's rejection.** Krohn et al.'s sample ends in 2019 and Bessho et al. use 2018-2020. The only 2020-2026 numbers are practitioner backtests on spot FX, where costs are lower than on CME micros. There is no new peer-reviewed evidence that would justify reopening gotobi or the fix on CME.

### Gaps
- Yen-specific size in Krohn et al. (they report the dollar portfolio), and their exact Tokyo-fix windows: not retrieved.
- Ito-Yamada's gotobi magnitudes as printed in the paper, and Bessho et al.'s strategy results: not retrieved.
- No peer-reviewed study with data after 2020 on the Tokyo fix or gotobi.
- CME 6J/MJY bid-ask spreads and depth during 19:00-21:00 New York time, and the actual fees for 6J/MJY: unknown.

---

## 5. Published evidence (2020-2026) that these effects persist or have vanished

### Takeaway
The evidence is thin and mixed.
- **Persistence:** Japanese intraday momentum survived COVID (ETF study, 2023). A 2026 paper documents an intraday momentum/reversal pattern in Nikkei futures, with unknown sample. A 2025 cross-market momentum strategy (US last half-hour → foreign first half-hour) stays profitable after costs.
- **Gone:** the BOJ "weak morning → afternoon buying" effect, since 19 March 2024; it was already anticipated before that.
- **No post-2020 academic evidence:** the Tokyo fix and gotobi (practitioner backtests show a small, fragile edge; the project's own 2023-2026 vault failed), and leveraged-ETF rebalancing (no empirical study after 2018).
- **Structural breaks** make pre-2024 backtests of "last half-hour" rules stale: the TSE close moved to 15:30 with a closing auction (Nov 2024), CME micro Nikkei contracts arrived (Oct 2024), and the BOJ exited (2024) and began selling (2026).

### Cited Findings
- **Persisting.**
  - Limkriangkrai et al. (PBFJ 2023): during COVID, intraday momentum "only persists in Japan" among the APAC markets that had it. [A] [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S0927538X2300152X)
  - *Finance Research Open* (2026): intraday momentum and reversal in Nikkei 225 futures linked to the prior S&P 500 day. [A] [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S3050700626000204)
  - Xu et al. (*JIFMIM*, Dec 2025): cross-market momentum stays profitable after costs. [A] [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1042443125001295)
- **Vanished: the BOJ effect.**
  - No ETF purchases on or after 19 March 2024 [A]. [BOJ terms](https://www.boj.or.jp/en/mopo/measures/term_cond/yoryo85.htm)
  - Sales began in Jan 2026 at ¥330bn a year [S]. [Adnkronos/Jiji](https://english.adnkronos.com/2026/02/03/boj-begins-unloading-etfs-in-jan/)
  - Already anticipated before then: futures volume surged at lunch with little or no price movement [A]. [Ko 2026](https://www.sciencedirect.com/science/article/abs/pii/S1544612325026704)
- **Fading: US-style market intraday momentum.**
  - A blog replication finds it on SPY in 2000-2012 but flat in 2013-2019. [S], grade D. [Temperance Capital](https://temperancecapital.substack.com/p/market-intraday-momentum-replicates)
  - The project rejected the US version on its own data. `rea/PISTES.md`
- **Vanished: the US overnight drift.**
  - For context only, this is US evidence. The project's notes cite Federal Reserve Bank of New York authors ("The Disappearing Overnight Drift", July 2026) finding it absent in 2021-2025, and NightShares funds closing. Source: `asie/README.md` (local project file; I did not check the paper itself).
- **Tokyo fix and gotobi.**
  - The academic samples end in 2019 (Krohn et al.) and 2020 (Bessho et al.). [S]/[A]
  - Practitioner 2016-2026 backtests: about +3 pips net in spot, fragile out of sample. [S], grade D. Sources: [GitHub](https://github.com/prathamesh-git9/gotobi-fx-bot); [ForexFactory](https://www.forexfactory.com/thread/1407332-gotobi-tokyo-fix-anomaly-7-years-of-usdjpy-tick)
  - The project's 2023-2026 gotobi vault test failed. `asie/README.md`
- **Structural changes in the Japanese market.**
  - TSE: from 5 Nov 2024, "zaraba trading will end at 15:25, and the newly introduced Closing Auction will take place at 15:30". [A] [JPX release](https://www.jpx.co.jp/english/corporate/news/news-releases/1030/20241105-01.html)
  - OSE: the night session end moved "from the current 5:30 a.m. to 6:00 am" (2020 notice). [A] [JPX notice](https://www.jpx.co.jp/english/news/2040/20200513-01.html)
  - CME: Micro Nikkei launched on 28 Oct 2024 (see section 6).

### Inferences
- [D] For a 2026 trader, the only Japanese-equity Tokyo-hours effect with any post-2020 academic support is the intraday momentum/reversal family (sections 1 and 3). Every other candidate is either gone (BOJ), smaller than costs (fix/gotobi), or unmeasured (leveraged-ETF rebalancing).
- [D] Any test must handle the Nov 2024 change of the close (15:00 → 15:30 JST), and should run the 2024-2026 data as a separate out-of-sample block.

### Gaps
- No 2020-2026 study measures Japanese last-half-hour momentum after the Nov 2024 closing-auction reform.
- No study after 2018 on leveraged-ETF rebalancing in Japan.
- No peer-reviewed study after 2020 on the Tokyo fix.

---

## 6. Which CME contracts give access: NKD, NIY, Micro Nikkei, 6J / J7 / MJY (size, dollars per point, trading hours)

### Takeaway
CME lists four Nikkei 225 futures:
- **NKD**: $5 × index, 5-point tick = **$25**;
- **NIY**: ¥500 × index, tick = ¥2,500;
- **MNK** (Micro Nikkei, dollars, launched 28 Oct 2024): $0.50 × index, tick = **$2.50**;
- **MNI** (Micro Nikkei, yen): ¥50 × index, tick = ¥250.

The yen futures are **6J** (¥12.5m, tick $6.25), **J7** E-mini (¥6.25m, tick $6.25) and **MJY** micro (¥1.25m, tick $1.25).

All trade on Globex Sunday-Friday, 18:00-17:00 ET, with a one-hour break at 17:00-18:00 ET, so the whole Tokyo session is covered. MNK is the only Nikkei contract sized for a small account: about $25k notional at Nikkei 50,000, against about $250k for NKD.

### Cited Findings
- **NKD (Nikkei/USD).**
  - Size: "$5 x Nikkei Stock Average". [A] [CME fact card](https://www.cmegroup.com/trading/equity-index/files/nikkei-225-futures-and-options-fact-card.pdf)
  - Tick: "Outrights and spreads: 5.00 index points = $25.00"; the basis-trade-at-close (BTIC) version ticks in 0.1 point = $0.50. [A] [CME Nikkei article](https://www.cmegroup.com/articles/2024/equity-trading-opportunities-in-nikkei-225-futures-at-cme-group.html)
  - Globex hours: "日曜日―金曜日: 6:00 p.m.-5:00 p.m. (米国東部時間)", i.e. Sunday-Friday, 6:00 pm - 5:00 pm US Eastern. [A] [CME Japanese contract page](https://www.cmegroup.com/ja/markets/equities/international-indices/nikkei-225-dollar.html)
- **NIY (Nikkei/Yen).** "¥500 x Nikkei Stock Average"; "5.00 index points = ¥ 2,500"; BTIC 0.1 point = ¥50. [A] [CME fact card](https://www.cmegroup.com/trading/equity-index/files/nikkei-225-futures-and-options-fact-card.pdf); [CME Nikkei article](https://www.cmegroup.com/articles/2024/equity-trading-opportunities-in-nikkei-225-futures-at-cme-group.html)
- A 2026 CME note on ratio spreads confirms that NIY and NKD outrights trade at a 5-index-point tick. [A] [CME 2026 note](https://www.cmegroup.com/news/2026/updated-nikkei-usd-jpy-futures-spread-trading-mechanism.html)
- **MNK (Micro Nikkei, USD).**
  - Product code: "CME Globex: MNK".
  - Size and tick: "Contract Unit USD 0.5; 5 index points = USD 2.50".
  - Hours: Sunday-Friday, 6:00 pm - 5:00 pm ET, with a daily 60-minute break from 5:00 pm ET.
  - Last trading day: "Trading terminates at 5:00 p.m. ET on the Thursday prior to the second Friday of the contract month".
  - [A] Sources: [CME MNK specs](https://www.cmegroup.com/markets/equities/international-indices/micro-nikkei-usd.contractSpecs.html); [CME MNK specs, Korean page](https://www.cmegroup.com/ko/markets/equities/international-indices/micro-nikkei-usd.contractSpecs.html)
- **MNI (Micro Nikkei, JPY).** "Micro Nikkei (JPY) futures | MNI | ¥50 | 5 index points (¥250)". [A] [CME MNI specs](https://cmegroup.com/markets/equities/international-indices/micro-nikkei-jpy_contract_specifications.html); [CME micro Nikkei FAQ](https://www.cmegroup.com/articles/faqs/faq-micro-nikkei-futures.html)
- **Micro Nikkei launch** (CME press release of 1 Oct 2024, as summarised):
  - Yen and dollar micros listed from **28 Oct 2024**, one-tenth the size of the standard contracts.
  - Listed in the two nearest quarterly months; final settlement on the same value as the standard contract.
  - "Nearly 75% of trades in its Nikkei futures occurred outside Tokyo cash hours" in 2024.
  - Year-to-date average daily volume of the standard Nikkei futures: 41,000 contracts, up 9% year on year.
  - [S] Sources: [CME press release](https://www.cmegroup.com/media-room/press-releases/2024/10/01/cme_group_to_launchyen-andusdollar-denominatedmicronikkeifutures.html); [FOW](https://www.fow.com/insights/3702207-cme-to-launch-micro-nikkei-futures-on-october-28)
  - CME product pages for MNK (time & sales, calendar) appear in search results, which suggests the contract is listed. I did not see an explicit confirmation of the launch date.
- **6J (Japanese yen, full size).**
  - ¥12,500,000 per contract; minimum move 0.0000005 dollars per yen = **$6.25**. [S]/[A]
  - Hours: Sunday-Friday on Globex, with a daily 60-minute break at 4:00 pm CT (= 5:00-6:00 pm ET). The search summary garbled the opening time. [S]
  - Sources: [CME 6J page](https://www.cmegroup.com/misc/iframes/activetrader/etrade/products/fx/japanese-yen-6j.html); [CME 6J contract specs](https://www.cmegroup.com/cn-s/markets/fx/g10/japanese-yen.contractSpecs.html)
- **J7 (E-mini yen).** Minimum move "$.000001 per Japanese yen, equivalent to $6.25 per contract", which implies ¥6,250,000 per contract. [A] [CME Rulebook ch. 263](https://www.cmegroup.com/rulebook/CME/III/250/263/263.pdf)
- **MJY (Micro JPY/USD).**
  - "Contract Size 1,250,000 Japanese yen". It aggregates into the position limits of the full-size JPY/USD contract. [A]
  - Tick 0.000001 = **$1.25**; quarterly months, two consecutive quarters listed. [S]
  - Sources: [CFTC filing](https://www.cftc.gov/filings/ptc/ptc01312411442.pdf); [CME MJY specs](https://cmegroup.com/markets/fx/g10/micro-jpy-usd_contract_specifications.html)
- **USD TOPIX.** CME has a "USD TOPIX trading fact card"; whether the contract is still listed was not checked. [A, title only] [CME fact card](https://www.cmegroup.com/trading/equity-index/files/usd-topix-trading-fact-card.pdf)
- **Comparison with Japan.**
  - OSE's own "Nikkei 225 micro" future is ¥10 × index with a ¥5 tick. [S] [JPX](https://www.jpx.co.jp/english/derivatives/products/domestic/225micro-futures/index.html)
  - OSE's Nikkei 225 futures proposal: day-session closing auction at 15:45 JST; night session 4:45 pm - 6:00 am JST. This comes from consultation documents, not the final rules. [A]/[S] [JPX proposal](https://www.jpx.co.jp/rules-participants/public-comment/detail/d8/cg27su00000068h0-att/jr4eth00000027c9.pdf)

### Inferences
- [D] **Size per tick**, at an illustrative Nikkei 50,000 and USD/JPY 150. The basis points per tick scale as 1/index level, so at 40,000 a tick is about 1.25 bp.

| Contract | Multiplier | Notional | 1 tick (5 points) | Round trip, project convention (1 tick per order + fees) |
|---|---|---|---|---|
| NKD | $5/point | ≈ $250,000 | $25 ≈ 1.0 bp | ≈ $50 + fees ≈ 2.1-2.2 bp |
| MNK | $0.50/point | ≈ $25,000 | $2.50 ≈ 1.0 bp | ≈ $5 + ~$2 ≈ 2.8 bp |
| NIY | ¥500/point | ≈ ¥25m | ¥2,500 ≈ 1.0 bp | n/a (yen margin) |
| MNI | ¥50/point | ≈ ¥2.5m | ¥250 ≈ 1.0 bp | n/a |

- [D] **Every Tokyo event lies inside the CME trading day and the 18:00-03:00 New York window.** The Tokyo session (≈ 19:00-01:30 EST / 20:00-02:30 EDT) contains no CME break. Positions can be flat well before the 16:59 New York cutoff.
- [D] **During Tokyo hours, Osaka sets the price.** CME says about 75% of its Nikkei trades happen outside Tokyo cash hours, so OSE is the main venue during the Tokyo session and NKD/MNK follow it. Spreads on the micro may be wider then; this needs paper-trading measurement (the project's `usine/rapprochement.py`).
- [D] The yen contracts are quoted inversely (dollars per yen). A position that expects USD/JPY to rise is short 6J/MJY.

### Gaps
- Actual bid-ask spread, depth and average daily volume of MNK and NKD between 19:00 and 02:30 New York time.
- Margins, fees, and whether the prop firm (Bulenox) allows NKD/MNK/MNI/6J/J7/MJY: not checked.
- Explicit confirmation of the daily 17:00-18:00 ET break for NKD (stated for MNK and implied by the 6:00 pm - 5:00 pm hours).
- Exact 6J hours text (the summary was garbled).
- Final post-reform OSE session times, and whether CME USD TOPIX futures still trade.
