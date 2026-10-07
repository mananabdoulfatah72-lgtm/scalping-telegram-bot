# Futures prop firms allowing overnight / weekend holding (swing accounts) + fully automated trading — fact sheets as of 2026-10-07

Research method note (read first): WebFetch was blocked by the egress proxy for nearly every firm and aggregator domain tried (elitetraderfunding.com/.app, phidiaspropfirm.com, thetradingpit.com and its support site, fundedfuturesnetwork.zendesk.com, propfirmbridge.com, propfirmsfinder.com, thegodfunded.com, damnpropfirms.com, quantvps.com). So every finding below comes from **WebSearch result summaries** of the cited pages, not full-page reads. Quotes marked "quoted" are the wording the search tool returned for that page. Treat exact numbers as "reported by the cited page", and check them on the official page before buying. The shared web-search budget ran out before I could check firm status (closures, payout scandals) or some prices. Those items are listed under Gaps.

## Q0. Bottom line: could any firm host a fully automated MNQ bot holding multi-day positions including weekends, 50K, ≤ 30 USD?

### Takeaway
No firm I found meets all four conditions: (1) real CME futures, (2) weekend holding, (3) fully automated bots allowed without watching, (4) 50K for ≤ 30 USD. Only two mainstream firms allow weekend holding on CME futures: **Phidias Premium** (50K/100K/150K) and **Elite Trader Funding Diamond Hands** (100K only). Both officially forbid fully automated trading, and both cost far more than 30 USD. **Leeloo** practice accounts may allow overnight and weekend holds, but Leeloo bans full automation too. If the bot drops the weekend requirement, the best partial fits are **The Trading Pit Futures Classic** (overnight allowed, no weekend, EAs allowed) and, for budget plus automation but intraday only, **Bulenox** (50K about 19.25 USD with an 89% code, bots allowed).

### Cited Findings
- Phidias is described as "the only major futures prop firm that allows overnight and weekend holding on Swing accounts" — [thegodfunded.com swing 2026](https://thegodfunded.com/en/blog/best-prop-firms-for-swing-trading-in-2026/); the same claim appears in the Aug-2026 list summary, which also names ETF Diamond Hands as "built for overnight and weekend holding" — [propfirmbridge weekend list](https://propfirmbridge.com/education/which-prop-firms-allow-weekend-holding-2026-complete-verified-list), [tradingfunder (last updated Aug 16, 2026)](https://tradingfunder.com/best/prop-firms-for-weekend-holding/)
- Futures programs that require being flat before the daily or Friday cutoff include Tradeify, The5ers Futures, Blueberry Futures, Atlas Futures, FundedNext Futures and Top One Futures — [propfirmbridge weekend list](https://propfirmbridge.com/education/which-prop-firms-allow-weekend-holding-2026-complete-verified-list)
- One aggregator lists 9 firms that allow "fully automated trading via EAs, bots, or external signal providers as of September 2026": Lucid Trading, FundedNext, Tradeify, Phidias, TradeDay, Topstep, Blusky, IQ Capital, Bulenox — [damnpropfirms algo list (Sept 2026)](https://damnpropfirms.com/best-prop-firms-for-algo-trading/). Phidias's own rules contradict this (see Q2).
- Forex/CFD firms (FundedNext Stellar, The5ers, FTMO Swing, Alpha Capital Swing, Goat Funded Trader, AI Prop) do allow weekend holding, but on CFDs, not CME futures — [elitetraderfunding.app swing blog](https://elitetraderfunding.app/blog/swing-trading-prop-firms-which-allow-overnight-holds-2026), [thegodfunded FundedNext news](https://thegodfunded.com/en/news/fundednext-reinstates-weekend-holding-for-trading-accounts)

### Inferences
- For a bot that is truly unattended and holds over weekends on CME futures, I found no compliant prop-firm option in October 2026. The realistic choices are:
  - (a) Phidias Premium 50K with a "semi-automated, actively monitored" setup (the trader watches and manually adjusts). This is about 131.60 USD per month plus a 149 USD activation fee, or 144.60 USD one-time on promo.
  - (b) Redesign the bot to go flat on Friday and run on The Trading Pit Futures Classic, which allows weekday overnight holds and EAs. The Classic 50K price was not found.
  - (c) Stay intraday on Bulenox (bots allowed, about 19.25 USD).
- AI Prop's "unrestricted bots including weekend" offer appears to be on CFDs (MT5/cTrader/TradeLocker), not real CME futures, so it does not meet the "CME futures only" constraint.

### Gaps
- Firm status (closures, payout scandals) could not be checked for any firm, because the search budget ran out. See Q5.
- No official page could be fully read. All wording comes from search summaries.

## Q1. Overnight and weekend holding: allowed on evaluation and funded? Size limits or fees?

### Takeaway
Weekend holding on CME futures: **Phidias Premium** (yes, evaluation and funded), **ETF Diamond Hands** (yes, 100K only, max 2 minis/20 micros), and **Leeloo** practice accounts (reportedly yes, with conflicting wording; funded "Performance" accounts limited to 3 micros through the close unless an admin approves). Overnight on weekdays but no weekend: **The Trading Pit Futures Classic**, **The5ers Futures Swing** (max 1 mini/10 micros overnight on 50K), **Earn2Trade funded (LiveSim/Live)** only (conflicting), and possibly **Goat Funded Futures** EOD/FLEX (conflicting). Every other firm on the list is intraday only.

### Cited Findings
**Phidias Propfirm — Premium (ex-Swing)**
- In Phidias 2.0, "Premium replaces the former Swing family". Premium "allows overnight and over-week positions, uses EOD trailing drawdown, can fund the CASH account in 1 trading day after evaluation pass", with a progressive split from 75% to 100% over the first 5 payouts — [lucaspropfirm.fr Phidias 2.0](https://lucaspropfirm.fr/en/phidias.html), [phidiaspropfirm.com/phidias-2-0](https://phidiaspropfirm.com/phidias-2-0)
- Premium is "the only Phidias plan that allows overnight and weekend holds" — [propscope.net Phidias prices](https://propscope.net/en/prices/phidias/), [thepropfirmguide Phidias](https://thepropfirmguide.com/phidias-prop-firm/)
- Premium accounts (50K, 100K, 150K) let you hold overnight and over the weekend — [phidiaspropfirm.com/swing-allowed](https://phidiaspropfirm.com/swing-allowed). No overnight size cap was reported in any source I saw (gap).

**Elite Trader Funding — Diamond Hands**
- "The Diamond Hands is the only ETF evaluation that lets you hold futures positions across the overnight session and through the weekend". Every other evaluation (1 Step, Static, EOD, Fast Track) requires you "to flatten one minute before the instrument close on every trading day" — [elitetraderfunding.com/diamondhands](https://elitetraderfunding.com/diamondhands/), [elitetraderfunding.app/evaluations](https://elitetraderfunding.app/evaluations)
- Diamond Hands is 100K only, with a maximum position of 2 minis or 20 micros. "While you hold an overnight position the floor does not chase you" (EOD drawdown updates on realized P&L at session close) — [elitetraderfunding.com/diamondhands](https://elitetraderfunding.com/diamondhands/); "Diamond Hands is only available in a $100K size, not $50K" — [blog.traderspost.io ETF](https://blog.traderspost.io/article/how-to-get-funded-with-elite-trader-funding)
- The revamped Diamond Hands rules apply to accounts bought on or after September 17, 2025 — [help.elitetraderfunding.com Diamond Hands](https://help.elitetraderfunding.com/help/how-the-diamond-hands-plan-works)

**Leeloo Trading**
- Support portal: "Unless permission is granted by the admin, all trades must be flat 15 minutes before the market close" (e.g. ES flat by 16:45 EST) — [support.leelootrading.com: Holding positions during the close](https://support.leelootrading.com/kb/a103/2_-holding-positions-during-the-close.aspx)
- Same support portal, per the search summary: Practice accounts may hold during the overnight close and the weekend close. Performance accounts (real funds) may hold "up to 3 micros through the close"; larger positions need admin permission — [support.leelootrading.com: Carrying Positions](https://support.leelootrading.com/kb/a56/carrying-positions.aspx). **Conflicts** with the flat-15-minutes rule above. Third-party reviews also say Leeloo allows weekend holds — [tradersunion Leeloo](https://tradersunion.com/brokers/prop/view/leeloo-trading/)

**The Trading Pit**
- Futures Classic: "overnight allowed but no weekend"; "You must close any open positions by Friday at market closing"; leaving positions open over the weekend "will be regarded as a breach of our rules" — [support.thetradingpit.com overnight FAQ](https://support.thetradingpit.com/can-i-leave-positions-open-overnight-in-futures-challenges)
- Futures Prime: overnight not allowed; positions still open 5 minutes before the new trading day may be force-closed; no weekend — [luxalgo Trading Pit Futures](https://www.luxalgo.com/prop-firms/the-trading-pit-futures/), [thegodfunded Trading Pit Futures](https://thegodfunded.com/en/firms/thetradingpitfutures)

**The5ers Futures — Swing**
- Swing allows an overnight carry of up to 1 mini / 10 micros on smaller sizes (including 50K), 2 minis / 20 micros on 100K and 3 minis / 30 micros on 150K. Weekend holding is not allowed: "The Swing program still closes before the weekend" — [helloweekends The5ers rules](https://www.helloweekends.com/firms/the5ers-futures/rules), [propfirmito The5ers Futures](https://propfirmito.com/the5ers-futures/), [proplens Swing 50K](https://proplens.trading/firms/the5ers-futures/the5ers-swing-50k/)

**Earn2Trade (re-check)**
- Evaluation: intraday only; all positions and working orders closed by 3:50 PM CT — [tradingfinder Earn2Trade](https://tradingfinder.com/props/earn2trade/)
- "On Live and LiveSim funded accounts you can hold overnight", with at least one new unique position per week required — [pickmytrade Earn2Trade FAQ](https://pickmytrade.trade/prop-firm-faq/earn2trade-faq/), [propfirmmap Earn2Trade](https://propfirmmap.com/firms/earn2trade). **Conflicts** with another summary saying there is "no overnight or weekend holding on any evaluation or funded account" — [tradingfinder Earn2Trade](https://tradingfinder.com/props/earn2trade/)

**Goat Funded Futures (extra find, conflicting)**
- One source says overnight is allowed on the EOD and FLEX plans. Others say the EOD Challenge does not permit overnight holding, with positions closed at 15:55 CT. Weekend holding is not permitted — [thetrustedprop Goat overnight](https://thetrustedprop.com/blogs/goat-funded-futures-overnight-weekend-trading-rules-what-s-allowed), [help.goatfundedfutures.com EOD specs](https://help.goatfundedfutures.com/en/articles/14095302-what-are-the-eod-challenge-specifications), [capitalcritic Goat](https://www.capitalcritic.ai/futures-prop-firms/goat-funded-futures)

**Intraday-only firms (no overnight, no weekend)**
- Bulenox: positions must be closed by 3:59 PM CT; no overnight, no weekend. Applies to all sizes ($10K–$250K) and all options (Qualification, Fast Track, Momentum) — [quantvps Bulenox vs Apex](https://www.quantvps.com/blog/bulenox-vs-apex), [propfirm201 Bulenox](https://propfirm201.com/firms/bulenox). One source instead gives 3:30 PM CST (conflict) — [thegodfunded Bulenox](https://thegodfunded.com/en/firms/bulenox/)
- OneUp Trader: positions closed by 3:15 PM CT or the product's electronic close, whichever comes first; no trading from 3:15 PM CT Friday to 5:00 PM CT Sunday — [tradingfunder OneUp rules](https://tradingfunder.com/oneup-trader-rules/), [propfirmmap OneUp](https://propfirmmap.com/firms/oneuptrader)
- Legends Trading: no overnight, no weekend; sim accounts must flatten before the sector-specific end-of-day deadline — [propvault Legends](https://propvault.co/firms/legends-trading), [blog.traderspost.io Legends](https://blog.traderspost.io/article/legends-trading-review)
- Funded Futures Family: positions closed by 4:15 PM EST daily, no weekend; the system auto-closes, and that "does not count as a rule violation" — [fundedfuturesfamily.com FAQ](https://www.fundedfuturesfamily.com/faq/can-i-hold-positions-overnight/)
- Funded Futures Network: flat by 4:50 PM EST on weekdays and Friday; reopen Sunday 6:00 PM EST; auto-flatten at 4:50 PM EST — [FFN Help Article 3.4](https://fundedfuturesnetwork.zendesk.com/hc/en-us/articles/46870363111451-Article-3-4-Permitted-Trading-Hours-and-Position-Closing-Rules)
- Hola Prime Futures: "Overnight holding of positions is not permitted; all trades must be closed before 3:30 PM CT Monday through Friday". Weekend holding "is considered a hard breach" — [holaprime.com futures trading rules](https://holaprime.com/futures/futures-trading-rules/), [holaprime swing FAQ](https://holaprime.com/futures/faqs/challenge/is-swing-trading-allowed/)
- forTraders Futures: "Open positions are automatically closed at 3:50 PM CT" — [fortraders.com FAQ](https://fortraders.com/faq)
- FundedNext Futures: no overnight or weekend on any plan; close by 3:10 PM CT — [helpfutures.fundednext.com](https://helpfutures.fundednext.com/en/articles/14268506-does-fundednext-futures-allow-overnight-and-weekend-trade-holding)
- UProfit: weekend swing trading is prohibited; weekday overnight policy not stated in the summaries — [tradingfinder UProfit](https://tradingfinder.com/props/uprofit/list/), [tradingfinder UProfit rules](https://tradingfinder.com/props/uprofit/rules/)

**Not CME futures / out of scope**
- AI Prop (Dubai): announced "fully automated AI trading bots without restrictions, even during the evaluation phase … any bot type, strategy, or holding period, including weekend positions" — [TradingView/Reuters press release, 2025-06-19](https://www.tradingview.com/news/reuters.com,2025-06-19:newsml_GNX5bsKgD:0-ai-prop-announces-unrestricted-use-of-automated-ai-bots-for-prop-traders). Its platforms are MT5, cTrader and TradeLocker; its blog claims access to CME/CBOT/NYMEX/COMEX — [aiprop.com blog](https://aiprop.com/5-best-futures-prop-trading-firms-in-2025/). PropFirmMap tracks it among CFD firms — [propfirmmap AI Prop](https://propfirmmap.com/firms/aiprop)
- Funded Trading Plus: overnight on most programs; weekend allowed except Advanced, Master Trader and Instant Funding; automation only via cTrader. This is a forex/CFD firm, and no CME futures program was found — [fxempire FTP](https://www.fxempire.com/prop-firms/fundedtradingplus), [tradingfinder FTP rules](https://tradingfinder.com/props/funded-trading-plus/rules/)
- Trade The Pool: a stock (shares) prop firm. Swing plans allow overnight and weekend holds; overnight stock positions need ≥500,000 shares average daily volume. No CME futures product was found — [h2tfunding TTP](https://h2tfunding.com/reviews/trade-the-pool/), [lunefi TTP](https://lunefi.com/blog/trade-the-pool-complete-guide-to-rules-and-payouts)

### Inferences
- An MNQ bot on Phidias Premium could legally hold over weekends. On ETF Diamond Hands it could too, but capped at 20 micros and only on the 100K plan.
- On The Trading Pit Classic, a bot could hold Monday to Thursday overnight but must flatten before the Friday close (16:00 CT). The bot would have to build in a "flat by Friday 15:55 CT" rule.
- The5ers Swing caps overnight holds at 10 MNQ on 50K, and bans bots anyway.
- None of the sources mentioned an extra fee for overnight or weekend holding at any firm.

### Gaps
- Phidias Premium overnight/weekend size limits: not found.
- Leeloo: which rule is current (flat 15 minutes before close vs. practice overnight/weekend allowed) could not be resolved without reading the official pages.
- ETF Direct to Funded (DTF) overnight policy: not confirmed. ETF says all its evaluations except Diamond Hands must be flat, but DTF is not an evaluation, so this needs a check.
- Trading Pit Classic: holding rules on the funded stage (vs. evaluation) not confirmed.

## Q2. Automation: fully automated bots allowed without manual monitoring? Exact wording, written approval, funded accounts

### Takeaway
Among the firms that allow weekend holding, **all ban fully automated trading**: Phidias (semi-automated only, on Premium only, with active monitoring), ETF (bots banned unless authorized in writing), and Leeloo (no auto-entry plus auto-exit). Firms that do allow bots (Bulenox, The Trading Pit futures, Funded Futures Network, Goat Funded Futures, reportedly forTraders) are intraday only, or at best allow weekday overnight holds (Trading Pit Classic). AI Prop allows everything, but on CFDs.

### Cited Findings
**Phidias**
- Official rules (quoted): "The use of robots, fully automated trading algorithms, or any other form of automated trading is not permitted. Only semi-automated software is permitted, provided the trader actively monitors and manually adjusts all trades." — [phidiaspropfirm.com/rules](https://phidiaspropfirm.com/rules)
- Phidias 2.0 version (quoted in summary): "Semi-automated software is allowed when the trader actively monitors and manually adjusts every trade, and this is allowed only on Premium". Prohibited practices: "automated scalping systems exceeding 200 trades per day, AI, bots and fully automated trading mechanisms (all account types), and hands-off, continuous day-and-night trading or complete automation" — [fundedtrading.com Phidias review, updated May 18, 2026](https://fundedtrading.com/propfirm/phidias-propfirm/)
- "Automated and HFT trading is prohibited — only semi-automated strategies you actively monitor are allowed, though DCA is permitted" — [damnpropfirms Phidias review](https://damnpropfirms.com/futures-prop-firms/phidias-prop-firm/)
- **Conflict:** damnpropfirms' "9 Algo Trading Futures Prop Firms — Verified for September 2026" includes Phidias among firms allowing fully automated trading, and another summary claimed Phidias "allows fully automated systems with no manual oversight requirement" — [damnpropfirms algo list](https://damnpropfirms.com/best-prop-firms-for-algo-trading/). This contradicts Phidias's own rules page. The official rules should prevail.
- Re-check as of October 2026: the newest dated evidence (May 2026 review of Phidias 2.0, plus the rules page as indexed) still shows the ban. I found nothing showing the ban was lifted by October 2026.

**Elite Trader Funding**
- ToS (quoted in summary): ETF prohibits "artificial intelligence (AI), bots, automated trading systems, trade copiers, or other automated trading strategies that are not expressly authorized in writing by ETF", with approved programs listed on the trade-copier disclaimer page — [help.elitetraderfunding.com ToS](https://help.elitetraderfunding.com/help/terms-of-service), [elitetraderfunding.app/terms-of-service](https://elitetraderfunding.app/terms-of-service)
- "Trades placed by a bot, script, or any automated system are not allowed and do not qualify as genuine trading, even when the orders look real" — [elitetraderfunding.app help, via search](https://elitetraderfunding.app/elite)
- "Permits semi-automated trading only as of March 2026"; fully automated "set-and-forget" strategies "need written approval from Elite Trader Funding case-by-case". TradersPost users "must actively monitor and manage all trades"; 10-second minimum hold — [blog.traderspost.io ETF review](https://blog.traderspost.io/article/elite-trader-funding-review), [sentinel.redclawey.com policy guide 2026](https://sentinel.redclawey.com/blog/automated-trading-allowed-prop-firms-policy-guide-2026)
- Approved copiers only: Tradesyncer, Tradecopia, Affordable Indicators, Replikanto Flowbot (PropFirm Compliance Edition), plus built-in Tradovate group trading and the Motivewave / Quantower copier features — [elitetraderfunding.app trade-copier disclaimer](https://elitetraderfunding.app/trade-copier-disclaimer)

**Leeloo**
- Support portal (quoted in summary): "if you're using an algorithm to place or manage trades, it must not be fully automated"; "full automation (auto-entry and auto-exit) and any system that places or manages trades without manual input" is not allowed on Practice or Performance Accounts. Signal-based trades are allowed if executed manually — [support.leelootrading.com: DCA or Algo Trading](https://support.leelootrading.com/kb/a205/is-dca-or-algo-trading-allowed-at-leeloo.aspx)

**The Trading Pit (futures)**
- EAs and automated trading are permitted on all The Trading Pit Futures accounts, "except those using tick scalping, latency/reverse/hedge arbitrage, rollover scalping, emulators, or that copy other traders' trades" — [luxalgo Trading Pit Futures](https://www.luxalgo.com/prop-firms/the-trading-pit-futures/), [thegodfunded Trading Pit](https://thegodfunded.com/en/firms/thetradingpit/)
- "The Trading Pit is the only one that explicitly allows VPS" among the futures firms studied for automation — [prop-memo.com automation routes (Sept 2026)](https://prop-memo.com/en/articles/futures-prop-automated-trading-how-to-2026-09)
- No "must be present" or "must monitor" rule surfaced for Trading Pit futures (gap: not verified on the official page).

**The5ers Futures**
- "Bots & automated trading are not allowed"; "HFT, algorithmic trading, and hedging are not allowed on The5ers Futures — manual discretionary trading only" — [proplens The5ers Swing 50K](https://proplens.trading/firms/the5ers-futures/the5ers-swing-50k/), [propfirmbook The5ers Swing 50K](https://propfirmbook.com/challenge/the5ers-futures-swing-1-step-50k)

**Bulenox**
- "EAs, bots, TradingView Pine strategies, NinjaScript, and external APIs all permitted", but only "user-built for personal use"; "commercial, shared, rented, or publicly distributed automation tools are not allowed" — [tradingfinder Bulenox (Aug 2026)](https://tradingfinder.com/props/bulenox/), [crosstrade Bulenox](https://crosstrade.io/prop-firms/bulenox)

**Others**
- Funded Futures Network: bots and automated strategies are allowed unless they are HFT or arbitrage systems exploiting the demo environment — [FFN Help Article 3.4 / search summary](https://fundedfuturesnetwork.zendesk.com/hc/en-us/articles/46870363111451-Article-3-4-Permitted-Trading-Hours-and-Position-Closing-Rules), [h2tfunding FFN](https://h2tfunding.com/reviews/funded-futures-network/)
- Funded Futures Family: prohibits third-party automated tools including TradersPost; bots and algorithmic trading prohibited — [blog.traderspost.io FFF automation](https://blog.traderspost.io/article/automate-funded-futures-family-with-traderspost)
- Hola Prime Futures (quoted): "It is not allowed to employ any kind of semi or fully automated trading like Bots, AI, etc. on all accounts." — [holaprime.com prohibited practices](https://holaprime.com/futures/prohibited-trading-practices/)
- Legends Trading: "Automated trading / EAs are not allowed"; TradersPost via Tradovate is reportedly possible within platform limits (unclear) — [propvault Legends](https://propvault.co/firms/legends-trading), [blog.traderspost.io Legends](https://blog.traderspost.io/article/legends-trading-review)
- OneUp Trader: does not publish an explicit EA/bot policy, so confirm with support. 10-second minimum hold; no martingale — [tradingfunder OneUp rules](https://tradingfunder.com/oneup-trader-rules/)
- UProfit: T&C "Improper Use of Technology" prohibits automated software, AI, HFT or bulk-entry tools used "to manipulate results or gain unfair advantages" — [uprofit.com T&C](https://uprofit.com/terms-and-conditions). Whether ordinary bots are banned is unclear.
- Earn2Trade (re-check): conflicting. One source says automation and EAs are permitted if each strategy is unique to the trader. Another says semi-automated is allowed but "fully unattended algos are restricted". No trade copiers on any program. TradingView directly supported since March 2026 — [tradingfinder Earn2Trade](https://tradingfinder.com/props/earn2trade/), [crosstrade Earn2Trade](https://crosstrade.io/prop-firms/earn2trade), [algofunded Earn2Trade](https://algofunded.com/firms/earn2trade/)
- forTraders: EAs allowed on the Two-Step Challenge and Instant Funding (likely forex programs). Grid, martingale and HFT/latency-arbitrage are banned — [fortraders.com blog](https://www.fortraders.com/blog/trading-bots-passed-funded-challenges). Not confirmed for the futures product.
- Goat Funded Futures: "Personal automated strategies and EAs are allowed, provided they are consistent with the trader's style and do not exploit system vulnerabilities" — [thetrustedprop Goat](https://thetrustedprop.com/blogs/goat-funded-futures-overnight-weekend-trading-rules-what-s-allowed)
- AI Prop: unrestricted bots including weekend holds, on CFD platforms — [TradingView/Reuters](https://www.tradingview.com/news/reuters.com,2025-06-19:newsml_GNX5bsKgD:0-ai-prop-announces-unrestricted-use-of-automated-ai-bots-for-prop-traders)

### Inferences
- ETF is the only weekend-capable firm with a stated route to written approval for full automation, case by case. In practice that means a 100K Diamond Hands at about 365–397 USD.
- Phidias's wording ("actively monitors and manually adjusts all trades", plus the ban on "hands-off, continuous day-and-night trading") rules out an unattended weekend bot even on Premium.
- Of the bot-friendly firms, The Trading Pit Futures Classic is the closest to a multi-day bot: overnight is allowed and EAs are allowed, but there is no weekend holding.

### Gaps
- Whether the automation rules differ between evaluation and funded stages: not stated for most firms. Phidias's ban says "all account types". ETF's ToS applies firm-wide.
- Whether ETF has actually granted written approval for full automation to anyone: no evidence found.
- forTraders futures-specific automation policy: not confirmed.

## Q3. Platforms and data: Rithmic, CQG, Tradovate, ProjectX? Quantower?

### Takeaway
Quantower was confirmed only for **Bulenox** and **The Trading Pit** (both via Rithmic), and indirectly for **ETF** (its approved-copier list mentions the Quantower copier). Phidias offers Rithmic, Tradovate, NinjaTrader, TradingView and DeepCharts; Quantower was not confirmed.

### Cited Findings
- Phidias: Tradovate, NinjaTrader, TradingView, Rithmic and DeepCharts, depending on account and connection — [phidiaspropfirm.com Rithmic vs Tradovate](https://phidiaspropfirm.com/education/rithmic-vs-tradovate). Old Swing listing: "CME/ICE via Rithmic, Tradovate, DeepCharts" — [thetrustedprop Phidias](https://thetrustedprop.com/prop-firms/phidias-propfirm). Phidias 2.0 launch sale mentioned "New Platforms" — [fundedprogramfinder](https://fundedprogramfinder.com/phidias-2-0-launch-sale/)
- The Trading Pit Futures: NinjaTrader, Tradovate, R|Trader Pro, ATAS and Quantower, all via Rithmic — [propfirmmatch Trading Pit Futures](https://propfirmmatch.com/futures/prop-firms/the-trading-pit-futures), [thetraderstack TTP 50K](https://www.thetraderstack.com/reviews/thetradingpit-50k)
- Bulenox: NinjaTrader, Tradovate, Rithmic, Quantower, ATAS; Rithmic data for CME, CBOT, NYMEX, COMEX — [tradingfinder Bulenox](https://tradingfinder.com/props/bulenox/)
- ETF: the approved-copier page explicitly permits "trade copier functionality in Motivewave and Quantower" — [elitetraderfunding.app trade-copier disclaimer](https://elitetraderfunding.app/trade-copier-disclaimer). Supported platforms page exists but was not read — [elitetraderfunding.app supported platforms](https://elitetraderfunding.app/help/supported-platforms-and-data-feed)
- Leeloo: Rithmic; up to 10 accounts under one Rithmic ID — [nexusfi Leeloo](https://nexusfi.com/d/prop-firms/leeloo-trading/)
- The5ers Futures: CME/CBOT/NYMEX futures via the "Black Arrow" platform, per one summary — [propfirmito The5ers Futures](https://propfirmito.com/the5ers-futures/) (single source, unverified)
- Legends: NinjaTrader and Tradovate — [blog.traderspost.io Legends](https://blog.traderspost.io/article/legends-trading-review)
- AI Prop: MT5, cTrader, TradeLocker (CFD platforms) — [aiprop.com blog](https://aiprop.com/5-best-futures-prop-trading-firms-in-2025/)

### Inferences
- A Rithmic-based bot (the project already built one for a Rithmic platform) would fit Phidias (Rithmic), The Trading Pit (Rithmic/Quantower), Bulenox (Rithmic/Quantower) and Leeloo (Rithmic).

### Gaps
- CQG and ProjectX support: no data found for any of these firms.
- Quantower at Phidias, ETF (as a trading platform, not just a copier), Leeloo and Goat: not confirmed.

## Q4. 50K account: price (list and Oct-2026 promo), activation fee, rules, payouts

### Takeaway
Of the weekend-capable options, the cheapest is **Phidias Premium 50K**: about 131.60 USD per month plus a 149 USD activation fee, or 144.60 USD one-time (no activation fee), with promo codes. That is still about 4–5 times the 30 USD budget. **ETF Diamond Hands** has no 50K; the 100K costs 365–397 USD. **Leeloo**'s cheapest 50K is reported at 38 USD per month. **Bulenox 50K** is the only option under 30 USD (19.25 USD with an 89% code), but it is intraday only.

### Cited Findings
**Phidias Premium 50K (overnight + weekend)**
- Monthly: 329 USD list, 131.60 USD with 60% off. Activation fee 149 USD (one-time, lifetime per account). Profit target 4,000 USD. EOD trailing drawdown 2,500 USD. Minimum 1 evaluation day. Payout cap 2,000 USD per cycle — [propscope.net Phidias](https://propscope.net/en/phidias/), [tradingfunder Phidias](https://tradingfunder.com/firms/phidias-propfirm/), [phidiaspropfirm.com/rules](https://phidiaspropfirm.com/rules) (search summary combined these; check per-number on the official site)
- One-time payment: 723 USD list, 144.60 USD with 80% off. "On the one-time route there is no activation fee and the evaluation and cash account are lifetime" — [propscope.net Phidias prices](https://propscope.net/en/prices/phidias/), [thepropfirmguide Phidias](https://thepropfirmguide.com/phidias-prop-firm/)
- Premium: 30% consistency rule; news trading allowed; one-time Cash Account Reset; payouts every 5 qualifying days; split 75% rising to 100% from the 5th payout — [fundedtrading.com Phidias (May 18, 2026)](https://fundedtrading.com/propfirm/phidias-propfirm/), [lucaspropfirm.fr](https://lucaspropfirm.fr/en/phidias.html)
- Daily loss limit: old Swing had "no daily loss limit" — [thetrustedprop Phidias](https://thetrustedprop.com/prop-firms/phidias-propfirm). Not confirmed for Premium.
- Old Swing 50K (pre-2.0, outdated): 110 USD/month, 4,000 USD target, 2,500 USD EOD drawdown, 80% split — [fundedtrading.com](https://fundedtrading.com/propfirm/phidias-propfirm/), [propgame Phidias](https://propgame.net/info/phidias)

**ETF Diamond Hands (100K only)**
- 3,500 USD EOD trailing drawdown. 1,500 USD daily loss limit, measured from the prior day's ending balance; an intraday breach by an open trade fails the account immediately. 5,000 USD target; 2 minis / 20 micros; minimum 5 days (ODTP add-on skips this); 8 qualified days for the first payout; split up to 100%; up to 2,500 USD per payout cycle — [elitetraderfunding.com/diamondhands](https://elitetraderfunding.com/diamondhands/), [help.elitetraderfunding.com](https://help.elitetraderfunding.com/help/how-the-diamond-hands-plan-works)
- Price: "$397 for a 100K account" per the ETF page summary — [elitetraderfunding.com/diamondhands](https://elitetraderfunding.com/diamondhands/); vs "$365/month for a $100K account" — [blog.traderspost.io ETF](https://blog.traderspost.io/article/elite-trader-funding-review) (**conflict**; may be legacy vs revamped pricing)

**Leeloo 50K**
- "Launch LE ($50K)" Entry Level reported at 38 USD per month. "Foundation Launch $50K" at 280 USD per month: 8 minis / 80 micros, 3,000 USD target, 2,500 USD trailing drawdown. The activation fee amount was unclear — [nexusfi Leeloo](https://nexusfi.com/d/prop-firms/leeloo-trading/), [propfirmsfinder Leeloo challenges](https://propfirmsfinder.com/prop-firm/leeloo-trading/challenges/)

**The Trading Pit 50K**
- Futures Prime 50K (no overnight): 99 USD, 3,000 USD target, 2,000 USD EOD trailing (computed around 16:15 CT), 1,000 USD daily loss limit, minimum 3 days, 40% consistency (excess added to the target), 80% split — [propfirmmatch TTP Futures](https://propfirmmatch.com/futures/prop-firms/the-trading-pit-futures), [thetraderstack TTP 50K](https://www.thetraderstack.com/reviews/thetradingpit-50k), [luxalgo](https://www.luxalgo.com/prop-firms/the-trading-pit-futures/)
- Futures Classic 50K (overnight allowed): price and rules not found (gap). Luxalgo shows "10% OFF" — [luxalgo](https://www.luxalgo.com/prop-firms/the-trading-pit-futures/)

**The5ers Futures Swing 50K**: 120 USD; 3,000 USD target; 2,000 USD EOD trailing; 40% consistency; 4 minis / 40 micros (1 mini / 10 micros overnight); 80% split — [proplens](https://proplens.trading/firms/the5ers-futures/the5ers-swing-50k/), [propfirmbook](https://propfirmbook.com/challenge/the5ers-futures-swing-1-step-50k)

**Bulenox 50K (intraday only)**: Qualification Option 1 is 175 USD list, **19.25 USD** with the 89% code PROPSCOPE (TRADINGSTRATEGY and LUMI also reported at 89% off), as of Sept 2026. 100% of the first 10,000 USD of profit, then 90/10. Up to 5 Master accounts. Trailing or EOD drawdown choice — [propscope.net Bulenox (Sept 2026)](https://propscope.net/en/bulenox/), [tradingfinder Bulenox](https://tradingfinder.com/props/bulenox/), [thegodfunded Bulenox](https://thegodfunded.com/en/firms/bulenox/). Buffers (25K–250K): 1,600 / 2,600 / 3,100 / 4,600 / 5,600 USD — [thegodfunded Bulenox](https://thegodfunded.com/en/firms/bulenox/)

**Other 50K data points (all intraday)**
- Funded Futures Family 50K: Classic 79 USD/month; Straight-to-Funded 499 USD; Evaluation-to-Live 429 USD/month — [lunefi FFF](https://lunefi.com/blog/funded-futures-family-complete-guide-to-rules-and-payouts), [propfirmplanet FFF S2F](https://www.propfirmplanet.com/challenges/funded-futures-family-straight-to-funded-s2f-accelerate-instant-50k)
- Legends 50K: Apprentice has a 3,000 USD target and 2,000 USD drawdown. Elite has a 2,700 USD target and 2,200 USD EOD drawdown. Both use EOD trailing — [propvault Legends](https://propvault.co/firms/legends-trading), [propfirmgorilla](https://propfirmgorilla.com/blog/legends-apprentice-50k-vs-legends-elite-50k)
- Goat Funded Futures EOD 50K: 134 USD; 6% target; 3–4% EOD trailing max loss; 2.5% daily loss (funded); 50% consistency in evaluation, 30% funded; 80% split — [capitalcritic Goat](https://www.capitalcritic.ai/futures-prop-firms/goat-funded-futures)
- UProfit: 50K/100K/150K sizes; 30% consistency in evaluation only; 80% split; 150 USD activation fee on EOD accounts; one Static account added in May 2026 — [tradingfinder UProfit](https://tradingfinder.com/props/uprofit/list/)
- AI Prop: cheapest evaluation 198 USD (CFD) — [propfirmmap AI Prop](https://propfirmmap.com/firms/aiprop)

### Inferences
- With a 30 USD budget, the only weekend-capable CME option found (Phidias Premium) is out of reach, even on promo. Bulenox is the only 50K under 30 USD, and it is intraday only.
- A 2,500 USD EOD trailing drawdown (Phidias Premium 50K) leaves little room for weekend gaps on MNQ. At about 2 USD per point per micro, a 300-point Monday gap on 4 MNQ is about 2,400 USD. That is my own calculation, not sourced.

### Gaps
- October 2026 coupon codes: the latest dated promos found are from Sept 2026 (Bulenox) and May 2026 (Phidias 2.0 launch sale). October-specific codes were not verified.
- Prices not found: OneUp 50K, Funded Futures Network 50K, Trading Pit Classic 50K, forTraders futures 50K, Hola Prime futures 50K, Earn2Trade 50K.
- Phidias Premium 50K daily loss limit and minimum days to payout: not confirmed.

## Q5. Is each firm still operating in October 2026 (closures, payout scandals)?

### Takeaway
I could not do a proper status check because the search budget ran out. Two warning signs did surface: **AI Prop** has a Trustpilot guideline-breach warning (Sept 23, 2026), a D safety grade and no license found. **The Trading Pit** is tagged "TrustPilot Suspended" by PropFirmMap. All other firms appear in 2026-dated reviews, which suggests they were still operating in mid or late 2026.

### Cited Findings
- AI Prop: "as of September 23, 2026, Trustpilot displays a warning on AI Prop's profile stating 'This company's rating is unavailable due to a breach of our guidelines'". D safety grade; no license found; founded January 2024, UAE — [propfirmmap AI Prop](https://propfirmmap.com/firms/aiprop), [trustpilot aiprop.com](https://www.trustpilot.com/review/aiprop.com)
- The Trading Pit: PropFirmMap headline "Grade C · TrustPilot Suspended · 80% Split" — [propfirmmap Trading Pit](https://propfirmmap.com/firms/thetradingpit). Details and reason not retrieved.
- Recent dated sources show these firms active in 2026: Phidias (2.0 launched; review updated May 18, 2026) — [fundedtrading.com](https://fundedtrading.com/propfirm/phidias-propfirm/); Bulenox (Sept 2026 coupon page) — [propscope.net](https://propscope.net/en/bulenox/); ETF (2026 blog posts on its own site) — [elitetraderfunding.app blog](https://elitetraderfunding.app/blog/swing-trading-prop-firms-which-allow-overnight-holds-2026); Earn2Trade (TradingView added March 2026) — [tradingfinder](https://tradingfinder.com/props/earn2trade/); UProfit (Static account added May 2026) — [tradingfinder UProfit](https://tradingfinder.com/props/uprofit/list/)

### Inferences
- With a Trustpilot warning, no license, CFD-only products and a 198 USD minimum, AI Prop is a poor fit on every count.

### Gaps
- No closure or payout-scandal checks were done for Phidias, ETF, Leeloo, The Trading Pit, The5ers, OneUp, Legends, FFF, FFN, forTraders, Hola Prime, UProfit, Earn2Trade or Goat Funded Futures. The web-search budget (200 calls per turn, shared by all agents) ran out. A follow-up search pass is recommended, especially "Phidias payout complaints 2026" and "The Trading Pit Trustpilot suspended reason".
