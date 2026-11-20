# US equity index futures at night (ES / NQ): overnight drift, Asian-hours patterns, and their status in 2020–2026

Verification legend: **[P]** = wording from a primary source (official abstract, the paper, a Fed post or an exchange page) as it appeared in search-engine excerpts. **[S]** = a secondary summary (blog, news, aggregator or search-engine synthesis) not checked against the original. **[C]** = sources conflict or attribution is uncertain. **Limitation:** in this session WebFetch could not reach `libertystreeteconomics.newyorkfed.org`, `www.newyorkfed.org` or `static.cambridge.org`, because the session's network allowlist blocks them. No PDF, internet appendix or full Fed post was read end to end, and every number below comes from search-result excerpts. In the strict sense nothing here is "verified at source"; [P] items come closest. All times are New York (ET) unless stated. The prop window under study is 18:00–03:00 ET, and the account must be flat before 16:59.

## 1. Boyarchenko, Larsen & Whelan, "The Overnight Drift" (RFS 2023), and the July 2026 Liberty Street post "The Disappearing Overnight Drift"

### Takeaway
From 1998 to 2019/2020, most of the E-mini S&P 500 (ES) return accrued in one hour, **02:00–03:00 ET**. That hour earned about 3.6–3.7% a year (about 1.5 bp/day), more than 60% of the contract's 5.9% annual close-to-close return. The drift was strongest after end-of-day sell-offs and negative closing order imbalances. The authors themselves say it was **not profitable after transaction costs**. Their July 2026 post finds the 02:00–03:00 window **flat in 2021–2025**, with one excerpt saying the same holds for NQ and YM. They attribute the fade to a compression of more than 50% in the dispersion of end-of-day order imbalance (standard deviation 6.5% → 2.9%), not to changes in volatility or liquidity. They predict the drift will return in the same window if imbalance dispersion widens again.

### Cited Findings
**Publication**
- Published in RFS vol. 36(9), 2023, pp. 3502–3547, DOI 10.1093/rfs/hhad020. Earlier versions are NY Fed Staff Report 917 and CEPR DP14462 (2020) [P]. Sources: [EconPapers RFS record](https://econpapers.repec.org/RePEc:oup:rfinst:v:36:y:2023:i:9:p:3502-3547.); [NY Fed SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf); [CEPR DP14462](https://repec.cepr.org/repec/cpr/ceprdp/DP14462.pdf); [OUP abstract](https://academic.oup.com/rfs/article-abstract/36/9/3502/7076616)

**Hours and size**
- Working-paper abstract: "almost 100% of the U.S. equity premium is earned during a 1-hour window between 2:00 a.m. and 3:00 a.m. (ET) which we dub the 'overnight drift'" [P]. Sources: [SSRN 3560269](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3560269); [CEPR DP14462](https://repec.cepr.org/repec/cpr/ceprdp/DP14462.pdf)
- RFS framing: US equity returns are "large and positive during the opening hours of European markets" [P]. Source: [OUP abstract](https://academic.oup.com/rfs/article-abstract/36/9/3502/7076616)
- 2021 Liberty Street post. The sample was S&P 500 futures held overnight, 1998–2019. The largest positive returns accrued between 2 a.m. and 3 a.m. ET, as European markets open, and averaged **3.6% annualized**. The post presents the drift as compensation for providing liquidity at the end of the trading day, not as a news or announcement effect [P, excerpt]. Source: [LSE, May 2021](https://libertystreeteconomics.newyorkfed.org/2021/05/the-overnight-drift-in-us-equity-returns)
- 2026 post: the 02:00–03:00 window "previously generated roughly 3.7 percent per annum". It was "previously responsible for more than 60 percent of the contract's 5.9 percent annualized close-to-close return" over the 1998–2020 ES sample [P, excerpt]. Sources: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/); [SSRN 7035838](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7035838); [RePEc](https://ideas.repec.org/p/fip/fednls/103479.html)
- Per day: about **1.48 bp/day** across all days (3.7% annualized). On non-announcement days it is **1.52 bp/day, t = 5.98** [S]. Source: [Substack summary](https://avaneendra.substack.com/p/the-stock-market-paid-37-a-year-in)
- Paper text: "the OD strategy has a Sharpe ratio of 1.1, which outperforms the market Sharpe ratio, and arises from a combination of high excess returns and low volatility during the overnight drift period" [P, excerpt]. Source: [accepted version, CBS](https://research-api.cbs.dk/ws/portalfiles/portal/101311522/nina_boyarchenko_et_al_the_overnight_drift_acceptedversion.pdf)

**Conditioning (end-of-day imbalance and sell-offs)**
- The paper reports "a strong negative relationship between end of day order imbalance, arising from market sell offs, and the overnight drift occurring at the opening of European financial markets" [P]. Sources: [SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf); [CEPR DP14462](https://repec.cepr.org/repec/cpr/ceprdp/DP14462.pdf)
- RFS abstract: the pattern fits inventory-risk models with an asymmetric reaction to demand shocks, and "market sell-offs generate robust positive overnight reversals" [P, excerpt]. Source: [OUP abstract](https://academic.oup.com/rfs/article-abstract/36/9/3502/7076616)
- Paraphrase of SR917: the drift is "highest and most positive during nights following market sell-offs" [S]. Source: [SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)
- 2026 post: "in 2007–20, large negative closing imbalances were followed by positive overnight returns, while large positive imbalances were followed by flat or negative returns" [P, excerpt]. This is asymmetric: rallies do not produce a symmetric short signal. Source: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)

**Mechanism**
- "Demand shock asymmetry can arise in inventory management models with time-varying market maker risk-bearing capacity" [P]. Source: [CEPR DP14462](https://repec.cepr.org/repec/cpr/ceprdp/DP14462.pdf)
- In the 2026 framework, the expected overnight return depends on three channels: (1) closing order imbalance, (2) return variance, and (3) the inverse of liquidity providers' risk-bearing capacity [P, excerpt]. Source: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)

**Transaction costs**
- Paper text: "with transaction costs, the OD is not profitable in practice" [P, excerpt]. Source: [accepted version, CBS](https://research-api.cbs.dk/ws/portalfiles/portal/101311522/nina_boyarchenko_et_al_the_overnight_drift_acceptedversion.pdf)
- Paper text: widening the window to **01:30–03:30** "increases the pretransaction cost Sharpe ratio to 1.3 but with an associated post-transaction Sharpe ratio equal to 0.3" [P, excerpt]. Source: [accepted version, CBS](https://research-api.cbs.dk/ws/portalfiles/portal/101311522/nina_boyarchenko_et_al_the_overnight_drift_acceptedversion.pdf)
- For 02:00–03:00, buying at the ask and selling at the bid reportedly cuts the average return to **−0.59%** (annualized) with a Sharpe of **−0.54** [S, unverified]. Source: [Substack summary](https://avaneendra.substack.com/p/the-stock-market-paid-37-a-year-in)

**Discussant critique (Bogousslavsky, FMA 2022 slides)**
- Bogousslavsky judges the pattern unlikely to be due to chance. His points:
  - A Grossman–Miller inventory model predicts a closing price impact of similar size to the drift, and that impact does not show in the paper's figures or tables.
  - The tests condition on closing imbalance, not on returns.
  - He asks "who pays the extra cost at the EU open?" [P, slides excerpt].
  Source: [Bogousslavsky discussion](https://bogousslavsky.github.io/files/FMA_2022_discussion.pdf)

**July 2026 status ("The Disappearing Overnight Drift", posted 1 July 2026, DOI 10.59576/lse.20260701)**
- The 02:00–03:00 window "has averaged close to zero since 2021" and is flat over 2021–2025 [P, excerpt]. Sources: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/); [Fed in Print](https://www.fedinprint.org/item/fednls/103479)
- One excerpt says the post finds the same pattern in **E-mini Nasdaq-100 (NQ) and E-mini Dow (YM)** [S/C]. A second search could not surface that sentence again. Source: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)
- "The standard deviation of end-of-day RSV fell from 6.5 percent to 2.9 percent—a compression of more than half." Extreme closing-imbalance days "have become markedly rarer", and in 2021–25 the imbalance-sorted return spread "is much narrower" [P, excerpt]. Source: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)
- Volatility and liquidity look roughly unchanged across the two samples, so the authors attribute the decline to compressed closing imbalances (Channel 1) [P, excerpt]. Secondary coverage adds that the VIX and the overnight share of ES volume were largely unchanged [S]. Sources: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/); [dbbnwa summary](https://www.dbbnwa.com/overnight-equity-drift-fades-new-york-fed-research-reveals-key-drivers/)
- The authors' testable prediction: "if order-imbalance dispersion widens back toward its pre-2020 range, the overnight drift should reappear in the same 2:00–3:00 window" [P, excerpt]. Source: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)
- Excerpts disagree on the framing [C]. One describes the order-imbalance–return *relationship* as having "broken down". Another says the decline comes from fewer and smaller imbalances while the channels are otherwise unchanged. Sources: [SSRN 7035838](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7035838); [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)

### Inferences
- **The numbers are consistent.** 3.7 / 5.9 = 63%, which matches "more than 60%". Also 1.48 bp × 252 ≈ 3.7%. The 3.6% figure (1998–2019) and the 3.7% figure (1998–2020) reflect different sample ends, not a contradiction. "Almost 100% of the equity premium" uses excess return as the denominator, while "more than 60% of close-to-close" uses total return.
- **Why costs killed the trade in sample, and what changed.** The figures below are my arithmetic, assuming index levels.
  - Over 1998–2012 the index mostly traded around 1,000–2,000. At those levels, one ES tick (0.25 pt) per round trip is roughly 1.3–2.5 bp, about equal to or above the ~1.5 bp/day gross drift.
  - At 2025–26 levels, assuming ES around 6,000 or higher, one tick is about 0.4 bp. For NQ, a 0.25-point tick at roughly 20,000 or higher is about 0.1 bp.
  - So the cost hurdle is now much lower, but the unconditional gross edge was about zero in 2021–2025. The project's rejection of the unconditional night long agrees with the literature.
- **The only conditional version that fits the mechanism:** go long ES/NQ **02:00–03:00 ET** (fully inside the 18:00–03:00 window) only on nights after an **extreme closing sell-off or negative closing imbalance in absolute terms**, using pre-2020 tail thresholds rather than rolling quantiles. If, as the authors argue, the fade comes from fewer extreme imbalances rather than a broken mechanism, the signal should still fire on rare stress days. Two caveats apply:
  - Trades would be infrequent.
  - "The spread is much narrower" could also mean the slope itself weakened, and that could not be resolved from the excerpts.
- **Proxy for imbalance.** Bogousslavsky notes the tests use closing imbalance, not returns, so a last-hour *return* filter may be weaker than an *order-flow* filter. Candidate proxies, untested and with availability to be checked:
  - ES signed volume from 15:30 to 16:00.
  - The exchanges' closing-auction imbalance data.
- **Do not trade the mirror image.** Large positive imbalances were followed by flat or negative overnight returns, not a robust short.
- **Daylight saving.** 02:00–03:00 ET corresponds to roughly 08:00–09:00 CET outside the weeks when US and EU daylight-saving dates differ. If the effect is tied to the European open, define the window in European local time. This depends on exchange hours I did not source here; verify.

### Gaps
- The 2026 post's figures were not readable. Missing: per-year results for 2021–2025, post-2021 returns conditional on extreme negative imbalance, the definition of "RSV" (whether it uses cash-equity or ES data), and NQ/YM numbers.
- Not retrieved: the paper's international evidence (other countries' index futures) and its exact cost assumptions (spread, commissions, fills).
- Whether the RFS hour-by-hour table shows any positive return during Asian hours (18:00–01:00) after sell-offs.

## 2. Bondarenko & Muravyev, "Market Return Around the Clock: A Puzzle" (JFQA 2023)

### Takeaway
The study uses ES tick data, 2004–2018 by most accounts (one source says 2006–2018). About **four hours around the Asian close and European open** earn the entire average return; a university news release puts the window at roughly 23:30–03:30 ET. The other 20 hours are a "noisy zero". The window's Sharpe ratio is about 1.6 and "remain[s] high after transaction costs", and an earlier version reported a Sharpe of 1.2 after costs with a high out-of-sample R². VIX futures show uncertainty building overnight and resolving around the European open, and the effect was stronger in the 2020 COVID crisis. No conditional version (after down days, at high VIX) and no post-2018 evidence was found.

### Cited Findings
- Published in JFQA 58(3), May 2023, pp. 939–967 [P]. Sources: [Cambridge abstract](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3); [IDEAS](https://ideas.repec.org/a/cup/jfinqa/v58y2023i3p939-967_1.html)
- Published abstract, quoted verbatim [P]: "We study how the market return depends on the time of the day using E-mini S&P 500 futures actively traded around the clock. Strikingly, 4 hours around European open account for the entire average market return. This period's returns have a 1.6 Sharpe ratio and remain high after transaction costs. Average returns are a noisy zero during the remaining 20 hours. High returns are consistent with European investors processing information accumulated overnight and thus resolving uncertainty. Indeed, uncertainty reflected by VIX futures prices rises overnight and falls around European open. The results are stronger during the 2020 COVID crisis." Sources: [Cambridge abstract](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3); [MSU news](https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/)
- March 2020 version (NFA): "four hours around Asian markets' close and European open account for the entire average market return". The timing strategy has a "high out-of-sample R²" and a **Sharpe ratio of 1.2 after costs** [P, working-paper abstract excerpt]. Source: [NFA 2020 abstract](https://portal.northernfinanceassociation.org/viewp.php?n=2240010836)
- A conference or working-paper abstract reports a return of **5.3%** (unclear whether cumulative or annual) and a **Sharpe of 1.4 after transaction costs** [S/C, version unclear]. Source: [NFA 2020 abstract](https://portal.northernfinanceassociation.org/viewp.php?n=2240010836)
- SSRN abstract: the window's returns are "positive every year" and "survive transaction costs". This wording is absent from the published abstract [P, excerpt]. Source: [SSRN 3596245](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3596245)
- Alpha Architect summary: tick-level ES data 2004–2018, window "around the Asian markets' close and the European open", **7.6% annualized, Sharpe 1.67, t = 6.4** [S]. Source: [Alpha Architect](https://alphaarchitect.com/market-return-around-the-clock/)
- Sample conflict: MSU says 2006–2018, while Market Trading Essentials and Alpha Architect say 2004–2018 [C]. Sources: [MSU news](https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/); [Market Trading Essentials](https://www.markettradingessentials.com/2021/04/how-to-make-money-from-stocks-while-you-sleep/)
- MSU news release [S, university PR, not the paper]:
  - The window runs roughly from **11:30 p.m. to 3:30 a.m. Eastern**, and the Asian market closes during it.
  - The authors suggest buying around 11:30 p.m., using time-specific broker orders.
  - Muravyev cautions that markets becoming more efficient could erode the pattern.
  Source: [MSU news](https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/)
- The authors used daylight-saving shifts to identify which regional open drives the effect [S]. Source: [Alpha Architect](https://alphaarchitect.com/market-return-around-the-clock/)
- VIX futures returns are reportedly "positive during the Asian session, highly negative around European open, and mildly negative during the rest of the day" [S, exact source page unidentified]. Source: [Alpha Architect](https://alphaarchitect.com/market-return-around-the-clock/)
- An internet appendix exists but could not be accessed here. Source: [JFQA supplementary PDF](https://static.cambridge.org/content/id/urn:cambridge.org:id:article:S0022109022000783/resource/name/S0022109022000783sup001.pdf)

### Inferences
- **Fit with the prop window.** If the window really is about 23:30–03:30, an account that must exit by 03:00 captures 3.5 of the 4 hours. The share of return earned 03:00–03:30, around the European cash open, is unknown, and it is the key number to extract from the internet appendix or the project's own data.
- **18:00–23:30 has no unconditional edge.** It falls in the "noisy zero" 20 hours, consistent with the project's rejection of buying at 18:00.
- **Overlap with Boyarchenko et al. (BLW).** B-M's window contains BLW's 02:00–03:00 hour, which BLW find flat in 2021–2025, so B-M's window has probably weakened too. It might keep some return if part of it accrued between 23:30 and 02:00. That is untested.
- **Why B-M survive costs and BLW do not.** A 4-hour window earning about 3 bp/day (7.6% / 252) absorbs the same one-tick cost better than a 1-hour window earning about 1.5 bp/day. Cost assumptions may also differ between the papers. This is my inference; neither paper's cost model was read.
- **The VIX pattern.** Uncertainty builds during Asian hours and resolves at the European open. That reads more like a variance or uncertainty premium than an ES direction signal, because ES returns over 18:00–23:30 are about zero. VX futures are rarely available on prop accounts.
- **Candidate conditional test (untested hypothesis).** Long ES/NQ from about 23:30 to 03:00 only in stress regimes: VIX high, or a large US-session decline. The basis is the abstract's statement that results were "stronger during the 2020 COVID crisis".

### Gaps
- Not obtained: the exact window boundaries from the paper itself, the hour-by-hour return table, any NQ or Russell results, and per-year returns.
- No conditional versions found (after down days, at high VIX, by day of week). The abstract mentions only COVID 2020.
- The cost model (spread, commissions) was not retrieved.
- No post-2018 or post-publication test by the authors or anyone else was found.

## 3. Other studies (2018–2026) on hour-by-hour or Asian-hours ES/NQ returns, conditional on the last-hour move, volatility, day of week or Asian macro releases

### Takeaway
Post-2020, peer-reviewed, hour-level evidence specific to Asian hours is thin. The only well-documented conditional signal for night hours remains BLW's end-of-day order imbalance (sell-off → 02:00–03:00 reversal), and it has weakened since 2021. Newer work is about news, jump risk premia and volatility shape, not tradable drift:
- Glasserman et al. 2025 (news topics)
- He 2026 (macro jump risk premia)
- a PKU paper on China's macro releases
- Andersen et al. on intraday volatility curves

No study was found on day-of-week or Sunday-reopen effects in ES/NQ Asian hours.

### Cited Findings
- **Glasserman, Krstovski, Laliberte & Mamaysky, "Does Overnight News Explain Overnight Returns?" (arXiv 2507.04481, 2025)** [P, excerpt]
  - Data and method: 2.4 million news articles, with topics chosen by a supervised method for how well they explain same-day returns.
  - Finding: both the prevalence of news topics and the market's response to them help explain the gap between intraday and overnight returns.
  - The method forecasts out of sample which stocks will do well overnight and poorly intraday.
  - The authors state that "nearly all the gains in the U.S. stock market" over 30 years were earned overnight.
  - This is close-to-open, stock-level work, not ES hour-by-hour.
  Source: [arXiv 2507.04481](https://arxiv.org/pdf/2507.04481)
- **Songrun He, "Interpretable Systematic Risk around the Clock" (arXiv 2604.13458, April 2026)** [P, excerpt]
  - Data: ES plus cash market at 15-minute frequency, 1997–2020.
  - "a significant component of systematic risk materializes during the overnight period".
  - Macroeconomic news commands the largest and most persistent jump risk premium.
  - Intraday-only estimates are "noisier, often mis-signed".
  - A secondary review claims that about 70% of systematic jumps occur overnight [S, unverified].
  Sources: [arXiv 2604.13458](https://arxiv.org/pdf/2604.13458); [Moonlight review](https://www.themoonlight.io/review/interpretable-systematic-risk-around-the-clock)
- **PKU working paper, "Learning, Price Discovery, and Macroeconomic Announcements"** [P, excerpt]
  - Uses China's unscheduled macro releases, with CSI 300 and ES transaction data from January 2009 to December 2020.
  - Event windows run from 10 minutes before to 240 minutes after each release.
  - Finds "fast price discovery at the market opening after macroeconomic announcements released overnight occurs even when investors do not trade".
  - The size of the ES reaction was not retrieved.
  Source: [PKU PHBS PDF](https://english.phbs.pku.edu.cn/uploadfile/2023/0330/20230330090416203.pdf)
- **Baltussen, Da & Soebhag, "End-of-Day Reversal"**
  - US stocks reverse sharply in the **last 30 minutes**. The effect is distinct from market intraday momentum and comes mainly from positive price pressure on intraday losers, attributed to attention-driven retail buying and short-sellers' risk management. Returns are measured from the previous close to 15:30 [P, excerpt]. Sources: [SSRN 5039009](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5039009); [paper PDF](https://academicweb.nd.edu/~zda/EOD.pdf)
  - A decile long-short earns about 0.24% per day in the final half hour [S]. Source: [CXO Advisory](https://www.cxoadvisory.com/technical-trading/buy-intraday-loser-stocks-in-the-last-half-hour/)
  - Won 2nd place at the Quantpedia Awards 2025 [P]. Source: [EUR news](https://www.eur.nl/en/news/end-day-reversal-pattern-second-place-quantpedia-awards-2025)
  - A pre-registered 2026 replication on post-2019 S&P 500 stocks reportedly finds the reversal "undone the following day" [S, unverified]. Source: [arXiv 2611.09286](https://arxiv.org/abs/2611.09286)
- **Andersen, Thyrsgaard & Todorov (JASA 2019)** [P, excerpt]
  - In ES, the intraday volatility pattern changes over time, even after excluding days with scheduled macro announcements.
  - In high-volatility regimes, the period before the close takes a significantly larger share of daily integrated volatility.
  Sources: [paper PDF](https://www.kellogg.northwestern.edu/faculty/todorov/htm/papers/tod.pdf); [IDEAS](https://ideas.repec.org/a/taf/jnlasa/v114y2019i528p1695-1707.html)
- **Andersen, Tan, Todorov & Zhang (Quantitative Economics 2025)**: using ES transactions 2005–2020, they reject the hypothesis that the average intraday volatility curve is stable over time, and the result is "robust over time and across the dominant regional trading zones, Asia, Europe, and North America" [P, excerpt]. Source: [Wiley, QE 2025](https://onlinelibrary.wiley.com/doi/full/10.3982/QE2644)
- **Pointers found but not examined** [S]:
  - Quantpedia, "Can Weakening Morning Order Flow Predict SPY Reversals?": holding periods cover the overnight or the next day; results not retrieved. Source: [Quantpedia](https://quantpedia.com/can-weakening-morning-order-flow-predict-spy-reversals/)
  - Practitioner blogs: [Kinlay 2019, overnight trading in ES](https://jonathankinlay.com/2019/03/overnight-trading-in-the-e-mini-sp-500-futures/) and [Blueville, Asian/London sessions in ES and NQ](https://blueville.capital/reading-the-asian-and-london-sessions-before-the-us-open/)

### Inferences
- The literature's "end-of-day move" signal for night returns is BLW's **closing order imbalance**, not the last-hour return. A last-hour-return filter is only a proxy and may be weaker (see Bogousslavsky in section 1).
- End-of-Day Reversal is a stock-level effect inside regular trading hours, before 16:00. The prop account cannot hold it into the night, so it is not usable for 18:00–03:00. The 2026 replication also suggests it unwinds the next day.
- He (2026) and Glasserman et al. (2025) point to overnight hours as where **macro and news jump risk is priced**. That suggests a risk premium earned by bearing jumps, not a predictable direction an intraday prop account can harvest with tight stops. Asian macro events such as Chinese data or BOJ decisions look like volatility events; no directional drift was documented.
- Andersen et al. imply the night-time volatility profile shifts with the volatility regime, so stop and size rules for Asian hours should scale with the current regime rather than fixed hourly averages.

### Gaps
- No 2020–2026 study was found on ES/NQ hourly returns in Asian hours conditional on any of the following:
  - the last-hour US return
  - the VIX level
  - day of week, including the Sunday 18:00 reopen and the Monday morning Asian session
  - BOJ or PBoC decisions
  - China CPI, PMI or trade releases
- No NQ-specific hour-by-hour study was found. The only NQ mention is the unconfirmed one in the 2026 post.
- One excerpt claimed that "market intraday momentum" (first half-hour predicting the last half-hour) disappears out of sample, but the underlying paper could not be identified, so it is not reported as a finding.

## 4. Volatility and volume spikes at 18:00 and at the Hong Kong / China open in E-mini futures

### Takeaway
I found **no study that measures spikes at the 18:00 ET reopen or at the Hong Kong / Shanghai open** in ES or NQ. The indirect evidence is:
- Asian-hours ES activity is a small fraction of US-hours activity (volume is more than 50 times higher in US hours).
- Overnight-session volume has its own U-shape, which implies elevated activity right after the reopen.
- The overnight share of ES volume was reportedly stable from 1998–2020 to 2021–2025.
- CME reports record non-US-hours volume during stress centred on Asia (August 2024, April 2025).

### Cited Findings
- Andersen, Bondarenko, Kyle & Obizhaeva, "Intraday Trading Invariance in the E-mini S&P 500 Futures Market": volume rises "more than fifty-fold" and the transaction count "twentyfive-fold" from Asian to American hours. There is a U-shaped pattern within the session that runs from 17:00 to 15:15 the next day (Central Time, i.e. 18:00 ET reopen) [P, excerpt]. Sources: [paper PDF](https://pages.nes.ru/aobizhaeva/ABKO-intradayinv.pdf); [ResearchGate](https://www.researchgate.net/publication/314514151_Intraday_Trading_Invariance_in_the_E-Mini_SP_500_Futures_Market)
- "Daytime vs. Overnight Trading in Equity Index Futures Markets" (ES and NQ): volumes in both the day and overnight sessions "depict separate U-shapes" [P, excerpt]. A daytime/overnight split of 66.92% / 33.08% for ES appears in the same results [S/C: attribution uncertain, sample probably before 2020]. Source: [ResearchGate](https://www.researchgate.net/publication/267858545_Daytime_vs_Overnight_Trading_in_Equity_Index_Futures_Markets)
- A practitioner guide says the ES overnight session "typically runs on 25-35% of RTH volume" and responds to Asian and European macro events [S]. Source: [NexusFi](https://nexusfi.com/a/instruments/e-mini-sp500-es-futures)
- CME figures [P, CME excerpts; the attribution of the two event records to specific pages is approximate]:
  - CME defines non-US hours as 5:00 p.m.–8:00 a.m. CT, and puts non-US-hours volume at about 16–18% of total in 2023 (S&P 500 options context). Source: [CME 2023](https://www.cmegroup.com/articles/2023/tap-into-global-markets-sp-500-options-trading-beyond-us-hours.html)
  - Record non-US-hours equity options volume: 257K contracts a day (~18% of the total) in the January 2025 report, of which ES options were 204K. Source: [CME, January 2025](https://www.cmegroup.com/news/2025/january-equity-insights-report1.html)
  - In Q1 2026 the same measure reached a new record of 277K a day (+18% y/y), of which ES options were 244K. Source: [CME, April 2026](https://www.cmegroup.com/news/2026/equity-insights-report-april-2026.html)
  - Event records: a single-day record of 5.1M equity futures and options contracts in non-US hours in early August 2024, and an all-time overnight record of more than 5.3M contracts after the April 2025 tariff pause (April 11, per the excerpt). Sources: [CME 2024](https://www.cmegroup.com/articles/2024/markets-never-sleep-the-need-for-global-liquidity-whenever-risk-spikes.html); [CME 2025](https://www.cmegroup.com/openmarkets/equity-index/2025/Why-Around-the-Clock-Liquidity-Matters.html)
- Andersen, Tan, Todorov & Zhang (2025): ES intraday volatility curves differ by regional trading zone (Asia, Europe, North America) and are not stable over time [P, excerpt]. Source: [Wiley, QE 2025](https://onlinelibrary.wiley.com/doi/full/10.3982/QE2644)
- The overnight share of ES volume and the VIX were reportedly little changed between 1998–2020 and 2021–2025 [S]. Source: [dbbnwa summary of the LSE post](https://www.dbbnwa.com/overnight-equity-drift-fades-new-york-fed-research-reveals-key-drivers/)
- The BLW staff report reportedly plots average 5-minute ES volume around the clock; the figure was not seen [S]. Source: [SR917](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr917.pdf)

### Inferences
- **Activity at the reopen.** A U-shaped overnight session implies more activity just after 18:00 ET and again near the European and US opens, with a trough in the middle of the Asian session. This is consistent with the project's earlier work on the reopen.
- **Local session times.** These come from general knowledge of exchange hours and were not sourced here; verify them, including Tokyo's 15:30 close since November 2024.

  | Event | EST (winter) | EDT (summer) |
  |---|---|---|
  | Tokyo cash open, 09:00 JST | 19:00 | 20:00 |
  | Shanghai / Hong Kong open, 09:30 local | 20:30 | 21:30 |
  | Tokyo close | about 01:30 | about 02:30 |
  | Hong Kong close, 16:00 local | 03:00 | 04:00 |
  | European cash open | about 03:00 | about 03:00 |

  So the Hong Kong / China open and the Tokyo close fall inside the 18:00–03:00 window, and the window's second half covers what B-M call the "Asian close / European open" period.
- **Liquidity and slippage.** With Asian-hours ES volume more than 50 times thinner than US hours, slippage on stops and market orders (thin book depth) matters more than the quoted spread for a scalper. Stress events such as August 2024 bring record overnight volume, but also gap risk.

### Gaps
- No minute-level study post-2020 was found on ES/NQ volatility, volume, spread or depth at 18:00, at the Tokyo open (19:00/20:00) or at the Hong Kong/Shanghai open (20:30/21:30). The project's own tick or 1-minute data will be needed.
- No ES-futures-specific (as opposed to options) share of non-US-hours volume was found in CME materials.

## 5. Is there a study showing a strategy restricted to Asian hours that is profitable after costs out of sample?

### Takeaway
Only Bondarenko & Muravyev claim after-cost profitability: a Sharpe of 1.2–1.6 for a roughly 4-hour window around the Asian close and European open. That rests on in-sample data (2004–2018) plus an out-of-sample R² measured within the same sample. BLW state that the 02:00–03:00 trade is not profitable after costs (Sharpe 0.3 after costs for 01:30–03:30), and their July 2026 update finds the window flat in 2021–2025. **No independent, post-publication, after-cost out-of-sample evidence of a profitable Asian-hours ES/NQ strategy was found.**

### Cited Findings
- B-M published abstract: a "1.6 Sharpe ratio" that "remain[s] high after transaction costs" [P]. Source: [Cambridge abstract](https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/market-return-around-the-clock-a-puzzle/089E33AC0B4D3B9A02CBA31EDF6505B3)
- B-M 2020 version: "high out-of-sample R²" and a Sharpe of 1.2 after costs [P, excerpt]. Source: [NFA 2020 abstract](https://portal.northernfinanceassociation.org/viewp.php?n=2240010836)
- B-M SSRN version: returns "positive every year" and "survive transaction costs" [P, excerpt]. Source: [SSRN 3596245](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3596245)
- BLW: "with transaction costs, the OD is not profitable in practice", and the 01:30–03:30 window has a Sharpe of 1.3 before costs and 0.3 after [P, excerpt]. Source: [accepted version, CBS](https://research-api.cbs.dk/ws/portalfiles/portal/101311522/nina_boyarchenko_et_al_the_overnight_drift_acceptedversion.pdf)
- After the spread, the reported figures are −0.59% and a Sharpe of −0.54 [S]. Source: [Substack summary](https://avaneendra.substack.com/p/the-stock-market-paid-37-a-year-in)
- Post-publication: the 02:00–03:00 window has been flat since 2021 [P, excerpt]. Source: [LSE, July 2026](https://libertystreeteconomics.newyorkfed.org/2026/07/the-disappearing-overnight-drift/)
- Related stock-level evidence (Elm Wealth, "Night Moves") [P, excerpt]:
  - A long-short overnight-versus-intraday portfolio of stocks earned about 38% a year gross, "exclusive of estimated transaction costs".
  - Elm calls it an extreme example of gross versus net returns and says it is not a strategy proposal.
  - A 2026 re-upload of the PDF exists.
  Sources: [Elm Wealth](https://elmwealth.com/night-moves-overnight-drift/); [Elm 2026 PDF](https://elmwealth.com/wp-content/uploads/2026/04/Elm-Night-Moves-Overnight-Drift.pdf)
- A third-party backtest page for that stock strategy (not ES) reports a Sharpe of **−2.46 since publication**, against 0.65 for the S&P 500, and says the effect has "faded since 2022" [S, methodology unknown]. Source: [Paperswithbacktest](https://paperswithbacktest.com/strategies/night-moves-is-the-overnight-drift-the-grandmother-of-all-market-anomalies)
- Muravyev cautions that more efficient markets could erode the pattern [S]. Source: [MSU news](https://broad.msu.edu/news/sweet-dreams-broad-research-reveals-best-times-for-overnight-market-returns/)

### Inferences
- B-M's "out-of-sample" is almost certainly a pseudo-out-of-sample (recursive) test inside 2004–2018, not post-publication evidence. I infer this from the 2020 working-paper wording.
- The post-publication record (BLW 2026: flat in 2021–2025 for ES, reportedly also NQ and YM) means **no unconditional night window has a documented edge after 2020**. This agrees with the project's rejections of the 18:00→09:30 long, the 18:00 reopen and night breakouts.
- Remaining research directions, all untested, needing the project's own 2021–2026 out-of-sample test with realistic costs (1 tick plus fees ≈ 0.4–0.6 bp a round trip for ES at current levels, an assumption):
  1. Long 02:00–03:00 ET only after extreme closing sell-offs or negative closing imbalances, using absolute thresholds.
  2. A truncated B-M window (about 23:30 → 03:00) only in stress regimes (high VIX, large prior-day decline), following B-M's "stronger during COVID 2020".
  3. Anchoring the window to European local time to handle daylight-saving mismatch weeks.
- **Selection bias.** Low trade frequency for (1) and (2) means few independent observations from 2021 to 2026. Any backtest needs strong caution about data-snooping.

### Gaps
- No peer-reviewed or reputable practitioner post-2020 out-of-sample, after-cost test of either the conditional overnight drift or a B-M-style window for ES/NQ was found.
- No Quantpedia or Alpha Architect backtest of the conditional version with post-2020 numbers was found.
- The full texts (2026 Liberty Street post, SR917/RFS tables, JFQA internet appendix) need to be read once `libertystreeteconomics.newyorkfed.org`, `www.newyorkfed.org` and `static.cambridge.org` are allowed in the session's network settings.
