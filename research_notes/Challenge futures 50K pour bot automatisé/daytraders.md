# DayTraders.com (daytraders.com) — every 50K account, checked for a fully automated MNQ bot that holds overnight and over weekends (as of 2026-10-07)

> **How these notes were gathered.** WebFetch was blocked by the egress proxy for every site tried: daytraders.com, intercom.help, blog.traderspost.io, prop50k.com, quantvps.com, dontpayfull.com, funded.now, pipback.com, propfirmmatch.com, damnpropfirms.com, thepropfirmguide.com, saveonpropfirms.com and canadianfuturestrader.ca. So every finding below comes from **WebSearch result summaries** of the cited pages, not from verbatim page reads. Quoted wording is the wording as the search tool reported it. The one exception is the Rithmic aggressor field, which was checked directly in a package downloaded from PyPI. Treat exact figures as "reported by the source", and read the conflicts flagged below as real uncertainty.
>
> Old names: "Full" accounts are the older name for Trail accounts ([DayTraders help: Static vs Full](https://daytraders.com/help/articles/9855034-what-s-the-difference-between-static-and-full-accounts)). "DTG" is an official DayTraders code for free ArcTrader crypto demo accounts. It is **not** the third-party code "DGT".

## 1. Automation policy (evaluation and funded/Pro/S2F): what is banned, any "must monitor" or approval clause, any hold-time or frequency limit?

### Takeaway
DayTraders' written rules ban only **automated high-frequency trading** (described as "hundreds or thousands of trades per second or minute"), hedging across accounts, and abusive or "unfair advantage" software. No help-center text found requires the trader to monitor a bot, to get approval, or to hold trades for a minimum time. A normal-frequency MNQ bot that holds for hours or days appears allowed on every account line. The one real ambiguity is a broad Terms of Use clause that names "software, AI … or other programs" that "manipulate or abuse" the sim environment.

### Cited Findings
- Official HFT article: "It is prohibited to use automated high-frequency trading. Automated high-frequency trading is prohibited on all accounts. This is monitored across all accounts and will be flagged by our system without discretion." — [DayTraders help: No High Frequency Trading](https://daytraders.com/help/articles/9918227-no-high-frequency-trading)
- Definition in the same article: HFT means "strategies that rely on the rapid execution of multiple trades within very short time intervals … including trading systems or algorithms designed to execute hundreds or thousands of trades per second or minute." The stated rationale is that all traders should have "an equal opportunity to succeed." — [DayTraders help: No High Frequency Trading](https://help.daytraders.com/en/articles/9918227-no-high-frequency-trading)
- Penalty: an account "found to be engaging in High Frequency Trading … will be immediately suspended pending a review. If HFT activity is confirmed, your account may be permanently closed, and any profits from HFT trades may be forfeited." — [DayTraders help: No High Frequency Trading](https://daytraders.com/help/articles/9918227-no-high-frequency-trading)
- Funded rules (Pro and S2F): "Automated high-frequency trading is prohibited." It is also "prohibited to be long in one account and short in another account" (no hedging). Search summaries say scalping and dollar-cost averaging (DCA) are allowed. — [DayTraders help: Funded Account Trading Rules (Pro + S2F)](https://daytraders.com/help/articles/14367899-funded-account-trading-rules-pro-s2f)
- Terms of Use (broad clause): users "are prohibited from using software, AI, high frequency automated trading, mass data entry, or other programs that manipulate or abuse the Pro Accounts or the simulated trading environment or give customers an unfair advantage." Remedies: DayTraders "may remove the transactions that violate the prohibition, or immediately cancel all Services and terminate the Agreement and Account." — [DayTraders Terms of Use](https://help.daytraders.com/en/articles/10024167-terms-of-use)
- TradersPost, a third-party automation vendor and DayTraders partner, says the policy "supports standard algorithmic strategies but prohibits high-frequency trading, hedging across accounts, and martingale strategies". It says standard automation through TradersPost webhooks is supported and that up to 15 evaluation accounts can run at once. The martingale ban did **not** appear in any official snippet I retrieved. — [TradersPost blog: Automate DayTraders](https://blog.traderspost.io/article/automate-day-traders-with-traderspost)
- PickMyTrade, another automation vendor, says DayTraders offers ProjectX at daytraders.projectx.com "with full API support" and also Rithmic, "with both platforms allowing automation." — [PickMyTrade blog](https://blog.pickmytrade.io/projectx-vs-rithmic-automation-bulenox-daytrader/)
- DayTraders' own comparison page (vs Bulenox) says Bulenox "explicitly allows EAs, trading bots, copy trading, and algorithmic strategies with no restrictions", while for DayTraders it lists only the HFT ban. The search tool added that DayTraders "requires more manual trading approaches". That phrase looks like the search model's own inference, not page text; no official rule says so. — [DayTraders vs Bulenox](https://daytraders.com/daytraders-vs-bulenox)
- Copy trading is officially documented (ONYX Trade Copier with a Lead/Follower model; Rithmic rTrader Pro Copier), so placing orders from software across accounts is an expected workflow. — [DayTraders help: Trade Copier (ONYX)](https://daytraders.com/help/articles/13064204-trade-copier-onyx); [DayTraders help: rTrader Pro Copier](https://daytraders.com/help/articles/11003488-rtrader-pro-copier)
- Hold times: a third-party review says DayTraders support confirmed the firm "will not penalize you for incredibly short trades that last for less than a minute." The only short-trade restriction it cites is HFT-like activity. No minimum hold time was found. News trading has no restriction. — [PipBack review blog](https://pipback.com/blogs/daytraders-review/); [DayTraders: News Trading Rules by Prop Firm](https://daytraders.com/news-trading-rules-by-prop-firm)

### Inferences
- A bot that trades a few times a day on MNQ and holds for hours or days is nowhere near the stated HFT threshold. The policy text sets **no** trades-per-day limit below "hundreds or thousands per second or minute", requires no approval, and has no "must be present/monitoring" clause.
- The Terms of Use clause is the residual risk. It is subjective ("unfair advantage", "abuse the simulated environment"). It would most plausibly be used against latency-arbitrage or sim-exploit bots, not a slow directional MNQ bot, but nothing written excludes discretionary enforcement.
- The same automation rules apply to evaluation, Pro and S2F accounts: the HFT article says "all accounts", and the funded-rules article repeats the ban.

### Gaps
- No official snippet explicitly says "bots/EAs are allowed". Permission is implied: only HFT is banned, copiers are documented, and TradersPost/ProjectX automation is advertised by partners.
- I could not verify whether DayTraders lets a **custom program log in directly through Rithmic's R|Protocol API**, which normally needs a Rithmic-approved app name, as opposed to automating through Quantower or another approved platform.
- No official confirmation of the martingale ban that TradersPost mentions.
- No numeric HFT threshold beyond the "per second or minute" wording.

## 2. Overnight and weekend holding: rule violation or just mark-to-market risk? Same for S2F, Pro and S2L?

### Takeaway
Holding overnight and over weekends is **not a rule violation** on evaluation, Pro or S2F accounts. DayTraders' help center says plainly that the account is not failed for holding through the close or the weekend. It fails only if the mark-to-market (MTM) value of the open position breaches the max-loss or drawdown level. The "close by 4:59 PM ET" line is guidance, softened in the same article. DayTraders does not auto-flatten. No weekend fee was found.

### Cited Findings
- "All trades must be closed by 4:59 PM ET. Trading reopens at 6:00 PM ET." In the same article: "you may hold trades beyond 4:59 PM ET, however, be aware position(s) will be subject to Mark-to-Market adjustments and could cause your account to hit the trailing/maximum loss limit." Also: "DayTraders.com will not close your positions for you at market close. Traders are responsible for managing all open positions and pending orders." Agricultural markets close earlier, and holiday early closes apply. — [DayTraders help: Closing Trades: Key Cutoff Times and Holiday Considerations](https://daytraders.com/help/articles/9854981-closing-trades-key-cutoff-times-and-holiday-considerations)
- Evaluation rules: "Traders are allowed to hold positions through market close, overnight, or over the weekend. However, open positions are subject to mark-to-market adjustments, which may affect your account balance." Also: "Your account will not be failed if you hold a position through market close or over the weekend. It will be failed if it hits the drawdown because of M-to-M adjustment." — [DayTraders help: Evaluation Account Rules](https://daytraders.com/help/articles/14368378-evaluation-account-rules); same wording reported for [S2F help article](https://daytraders.com/help/articles/11583644-s2f-straight-to-sim-funded)
- Funded rules (Pro and S2F) carry the same permission: positions may be held "through market close, overnight, or over the weekend", subject to MTM adjustments. — [DayTraders help: Funded Account Trading Rules (Pro + S2F)](https://daytraders.com/help/articles/14367899-funded-account-trading-rules-pro-s2f)
- DayTraders' marketing page "allows overnight holding on all account types, with S2F using EOD (end-of-day) drawdown designed for this purpose", and notes that S2L live accounts use an intraday trailing drawdown. — [DayTraders: Live Funded Trading](https://daytraders.com/live-funded-trading)
- **Conflict (likely outdated):** a third-party review says "DayTrader automatically closes trades at the end of the day, and they do not penalise accounts when you leave the system to be closed automatically." This contradicts the official "will not close your positions" text. — [PipBack review blog](https://pipback.com/blogs/daytraders-review/) vs [DayTraders help: Closing Trades](https://daytraders.com/help/articles/9854981-closing-trades-key-cutoff-times-and-holiday-considerations)
- How MTM interacts with each drawdown type: the Trail drawdown "trails from the account's highest unrealized or realized balance (intraday, including open trade highs)". Static is "fixed at account creation and does not move". EOD and S2F drawdowns update "only … at the end of the trading day". — [DayTraders help: Drawdown & Threshold Guide](https://daytraders.com/help/articles/9855052-drawdown-threshold-guide-trailing-static-eod); [Evaluation Account Rules](https://daytraders.com/help/articles/14368378-evaluation-account-rules); [S2F help](https://daytraders.com/help/articles/11583644-s2f-straight-to-sim-funded)

### Inferences
- For an overnight and weekend MNQ bot, the real constraint is how far each drawdown type sits from the open position:
  - **Static 50K:** a fixed $1,000 floor. At $2 per point per MNQ, that is 500 NQ points of adverse move on 1 MNQ, gap included.
  - **Trail 50K:** an intraday trailing floor that ratchets up with *unrealized* overnight peaks, so a position that runs up overnight and gives it back can breach the floor without any rule being "broken".
  - **EOD and S2F:** the trailing floor updates only at the daily close, which DayTraders itself calls the design suited to overnight holding. But they add a **$1,250 daily loss limit**, which closes an open trade automatically when hit (see section 3).
- The 4:59 PM ET line only matters as the MTM and settlement point and the 5:00-6:00 PM ET maintenance break. A bot holding through it carries gap risk over the break, and over the weekend from Friday 5 PM to Sunday 6 PM ET.
- **For the report writer:** an earlier internal simulation in this project treated the EOD 1,250 $ limit as "account lost". The official EOD article (section 3) describes it as a soft pause for the day.

### Gaps
- No source found on how MTM is computed: CME settlement price or last trade at 4:59/5:00 PM ET.
- No source on which "day" the EOD/S2F daily loss limit and drawdown use for positions held across the 5 PM roll.
- Overnight and weekend rules on the **S2L live** brokerage account (real broker overnight margin, any firm restriction) were not found.
- No weekend-holding fee or restriction was found. That is absence of evidence, not confirmation.

## 3. The 50K accounts one by one: target, max loss (type and lock), daily loss limit, consistency, minimum days, contracts, fees

### Takeaway
There are six 50K paths. Trail and Static are evaluations leading to a Pro account with a $130 activation fee. EOD is an evaluation leading to an EOD Pro account, with a disputed activation fee. S2F skips the evaluation, has no activation fee and an EOD drawdown. S2L Core is an evaluation leading to a real live brokerage account. Contract limits for Static and S2F, the EOD drawdown and the EOD Pro fee have **conflicting figures** across sources.

### Cited Findings

#### Trail 50K (evaluation, formerly "Full")
- Target $3,000. Max loss $2,500, **intraday trailing** from the highest unrealized or realized balance. **No daily loss limit.** — [Evaluation Account Rules](https://daytraders.com/help/articles/14368378-evaluation-account-rules); [TradersPost blog](https://blog.traderspost.io/article/automate-day-traders-with-traderspost)
- Contracts: 5 mini / 50 micro. — [Canadian Futures Trader: Evaluation info](https://canadianfuturestrader.ca/daytraders-com-evaluation-account-information/) (summarizing Evaluation Account Rules); the help article snippet says "50K Full Size: 50 Micros" — [DayTraders help: Overview of All Accounts: Mini and Micro Contract Sizes](https://daytraders.com/help/articles/9855092-overview-of-all-accounts-mini-and-micro-contract-sizes)
- Minimum 2 qualifying days. A qualifying day is a day whose net profit is at least the minimum daily profit ($200 for 50K) and that stays within the consistency rule. Consistency is 50%: the best day may be at most 50% of total profit. — [Evaluation Account Rules](https://daytraders.com/help/articles/14368378-evaluation-account-rules)
- List price $379 (see section 5 for promos). Pro activation $130, one time. — [DayTraders help: Pro Account: Activation And Fees](https://daytraders.com/help/articles/9856887-pro-account-activation-and-fees); [DamnPropFirms (Oct 2026)](https://damnpropfirms.com/cheapest-prop-firms/)

#### Static 50K (evaluation)
- Target $3,750. Max loss $1,000 **static**: the floor stays at $49,000 even if equity reaches $55,000-60,000. **No daily loss limit.** — [Evaluation Account Rules](https://daytraders.com/help/articles/14368378-evaluation-account-rules); [DayTraders: Trailing Drawdown Explained](https://daytraders.com/trailing-drawdown-explained)
- 2 qualifying days, $200 minimum daily profit, 50% consistency. — [Evaluation Account Rules](https://daytraders.com/help/articles/14368378-evaluation-account-rules)
- **Contracts: conflict.** 3 mini / 30 micro per [Canadian Futures Trader (Evaluation Account Rules summary)](https://canadianfuturestrader.ca/daytraders-com-evaluation-account-information/) and one version of the [help article on contract sizes](https://daytraders.com/help/articles/9855092-overview-of-all-accounts-mini-and-micro-contract-sizes) ("50K Static: 30 Micros"). Versus **6 mini / 60 micro** per [The Prop Firm Guide](https://thepropfirmguide.com/daytraders/), [DamnPropFirms](https://damnpropfirms.com/account-plans/50k/) and another rendering of the same help article ("6 contracts [60 Micros]").
- List price $200. Pro activation $130. — [DayTraders help: Pro Account: Activation And Fees](https://daytraders.com/help/articles/9856887-pro-account-activation-and-fees); [PropTradingVibes discount page (Apr 2026)](https://www.proptradingvibes.com/blog/daytraders-discount-code)

#### EOD 50K (evaluation)
- Target $3,000. Daily loss limit $1,250. Drawdown is end-of-day trailing, **$2,000 per most sources but $2,500 per one**: the search summary reports both "Total Drawdown is $2,500" and "$2,000 EOD Trailing Threshold". — [DayTraders help: EOD Account Rules](https://daytraders.com/help/articles/14473672-eod-account-rules) (as summarized); figures also echoed via [prop50k.com](https://www.prop50k.com/review/daytraders/)
- **The daily loss limit is soft:** "Breaching the daily loss limit on any day results in your account being paused for the day, and if you have an open trade that causes you to hit your daily loss limit, the trade will automatically close." — [DayTraders help: EOD Account Rules](https://daytraders.com/help/articles/14473672-eod-account-rules)
- 2 qualifying days, 50% consistency in the evaluation. EOD Pro: 30% consistency, payout every 8 qualifying days, at most 5 Pro EOD accounts, $200 minimum daily profit, free real-time data. — [DayTraders help: EOD Account Rules](https://daytraders.com/help/articles/14473672-eod-account-rules)
- Contracts reported as 10 mini / 100 micro. This comes from a search summary over the EOD rules article and third-party reviews and was not verified verbatim. — [EOD Account Rules](https://intercom.help/daytraders/en/articles/14473672-eod-account-rules)
- **EOD Pro activation fee conflict:** $5 one time per one search summary, described as the "more recent pricing"; $99 per another summary; $130 per [DamnPropFirms (Oct 2026)](https://damnpropfirms.com/cheapest-prop-firms/). — [EOD Account Rules](https://daytraders.com/help/articles/14473672-eod-account-rules); [Pro Activation and Fees](https://daytraders.com/help/articles/9856887-pro-account-activation-and-fees)
- List price $469 per [DamnPropFirms (Oct 2026)](https://damnpropfirms.com/cheapest-prop-firms/). The official promo page shows EOD sale prices from $80 (25K) to $400 (300K); the 50K sale price was not captured. — [DayTraders: Evaluation Pricing](https://daytraders.com/promo)

#### S2F 50K, "Straight to (sim) Funded" (no evaluation)
- No evaluation or pass target: trading starts in a funded sim account on day one. No activation fee. EOD trailing drawdown of $2,500. — [DayTraders help: S2F](https://daytraders.com/help/articles/11583644-s2f-straight-to-sim-funded); [PropTradingVibes account types](https://www.proptradingvibes.com/blog/daytraders-account-types)
- Daily loss limit $1,250, **soft**: "upon reaching it, positions are liquidated and the trading account is locked until the following trading day." — [DayTraders help: S2F](https://daytraders.com/help/articles/11583644-s2f-straight-to-sim-funded)
- 20% consistency (no day above 20% of total profit in a cycle). 10 qualifying days per payout, each needing at least $200 simulated profit. — [DayTraders help: Funded Account Trading Rules](https://daytraders.com/help/articles/14367899-funded-account-trading-rules-pro-s2f); [QuantVPS overview](https://www.quantvps.com/prop-firms/day-traders)
- **Contracts: conflict.** The official S2F article lists 25K = 1, 50K = **5**, 150K = 12 contracts. Third parties say **10 minis / 100 micros**. — [DayTraders help: S2F](https://daytraders.com/help/articles/11583644-s2f-straight-to-sim-funded) vs [The Prop Firm Guide](https://thepropfirmguide.com/daytraders/)
- At most 5 S2F accounts within the 15-funded-account cap. — [PropTradingVibes review](https://www.proptradingvibes.com/prop-firms/daytraders)
- List price $570 (sizes: $370 / $570 / $825 for 25K / 50K / 150K). — [DayTraders: Evaluation Pricing](https://daytraders.com/promo)

#### S2L "Straight to Live", Core plan ($50K buying power)
- Evaluation: 8 qualifying days, $3,000 target, $2,000 **intraday trailing** drawdown, 25% consistency in the evaluation only, 2 contracts (20 micros), at most 5 S2L accounts. — [DayTraders help: Straight to Live Evaluations (S2L)](https://intercom.help/daytraders/en/articles/14037676-straight-to-live-evaluations-s2l)
- Live account: Core has a $1,000 daily loss limit and an intraday trailing $2,000 drawdown. No consistency rule and no minimum daily profit after passing. Free activation, free real-time data, setup in 1-5 business days, a real brokerage account. — [DayTraders: Live Funded Trading](https://daytraders.com/live-funded-trading); [PipBack S2L review](https://pipback.com/blogs/daytraders-review/)
- Several passed S2L accounts are activated one at a time, each "until the drawdown has been locked or the account is blown". — [DayTraders help: Live Accounts & Payouts](https://intercom.help/daytraders/en/articles/14038700-live-accounts-payouts)
- Price: $329 list; $229 on sale (April 2026). The official promo page says S2L "starts at $179", plan not specified. — [PropTradingVibes account types](https://www.proptradingvibes.com/blog/daytraders-account-types); [DayTraders: Evaluation Pricing](https://daytraders.com/promo)

#### Pro, Pro Static, Pro Trailing (funded stage after a Trail or Static pass)
- $130 one-time activation for all sizes, Trail or Static. Activated within 30 minutes. Must be set up within 30 days of the last evaluation trade or it may be forfeited. — [DayTraders help: Pro Account: Activation And Fees](https://daytraders.com/help/articles/9856887-pro-account-activation-and-fees)
- **Pro Trailing:** "the trailing stops when your Auto Liquidate Threshold Value reaches the initial account balance". For 50K, the floor locks at $50,000 once the peak reaches $52,500. **Pro Static** keeps the fixed evaluation drawdown ($1,000 for 50K). — [DayTraders help: Drawdown & Threshold Guide](https://daytraders.com/help/articles/9855052-drawdown-threshold-guide-trailing-static-eod)
- 8 qualifying days per payout cycle, 30% consistency, $200 minimum daily profit. Hedging and HFT banned (section 1). — [DayTraders help: Funded Account Trading Rules](https://daytraders.com/help/articles/14367899-funded-account-trading-rules-pro-s2f)
- At most 15 funded accounts in total, of which at most 5 EOD and at most 5 S2F. — [PropTradingVibes review](https://www.proptradingvibes.com/prop-firms/daytraders)
- **Activity rule:** every account must be traded at least once per rolling 30 days. Per the search summary, that day "must meet the minimum daily profit for your account size" ($200 on 50K); consistency is not required for it. An inactive account can be interrupted, may have to be repurchased, or may block withdrawals. — [DayTraders help: Keep Your Accounts Active – Minimum Activity Policy](https://daytraders.com/help/articles/9854806-keep-your-accounts-active-minimum-activity-policy)
- **No pass deadline or monthly fee was documented** in what I retrieved. DamnPropFirms calls the Static price a "one-time fee", and S2F is described as "pay once". — [DamnPropFirms 50K plans](https://damnpropfirms.com/account-plans/50k/); [PropTradingVibes review](https://www.proptradingvibes.com/prop-firms/daytraders)

### Inferences
Compiled from the findings above. "?" marks a conflict between sources.

| 50K account | Target | Max loss | Daily loss limit | Consistency | Min days | Contracts | Extra fee |
|---|---|---|---|---|---|---|---|
| Trail (eval) | $3,000 | $2,500 intraday trailing, unrealized peaks | none | 50% | 2 QD (≥$200) | 5 / 50 micro | Pro $130 |
| Static (eval) | $3,750 | $1,000 fixed (floor $49,000) | none | 50% | 2 QD | 3/30 **or** 6/60 ? | Pro $130 |
| EOD (eval) | $3,000 | $2,000 ? ($2,500 per one source), end-of-day trailing | $1,250 soft (pause, open trade closed) | 50% | 2 QD | 10 / 100 micro (unverified) | EOD Pro $5 / $99 / $130 ? |
| S2F (funded now) | none to pass; payout targets in section 4 | $2,500 end-of-day trailing | $1,250 soft (liquidate, lock to next day) | 20% | 10 QD per payout | 5 **or** 10/100 ? | none |
| S2L Core | $3,000 (eval) | $2,000 intraday trailing | $1,000 (live) | 25% (eval only) | 8 QD | 2 / 20 micro | none (free activation) |
| Pro Trailing | per cycle (section 4) | trails until floor = $50,000, then locked | none found | 30% | 8 QD per cycle | not found | none |
| Pro Static | per cycle | $1,000 fixed | none found | 30% | 8 QD per cycle | not found | none |

- **Best fit for overnight and weekend holding:** Static and Pro Static never ratchet up, but the cushion is only $1,000. S2F and EOD ratchet only at the close but carry a $1,250 daily loss limit that force-closes positions. Trail, Pro Trailing (before the lock) and S2L ratchet intraday on unrealized gains, which is the worst fit for long holds.
- The 50% (evaluation), 30% (Pro) and 20% (S2F) consistency rules penalize a bot whose profits come in a few large overnight moves. One big winning weekend can block a payout cycle until enough other qualifying days accumulate.
- The 30-day activity rule, if it really needs a $200-profit day, is a hazard for a bot that can sit out a month. An automatic "at least one trade" is not necessarily enough.

### Gaps
- Contract limits for Static 50K and S2F 50K, the EOD 50K drawdown ($2,000 vs $2,500) and the EOD Pro activation fee ($5 / $99 / $130) could not be settled without reading the pages verbatim.
- Whether the **evaluation** Trail drawdown locks (the official lock text is about Pro accounts) was not confirmed.
- Contract limits on Pro accounts, and any scaling plan, were not found.
- No S2F drawdown lock level was found.
- The 50K EOD sale price for October 2026 was not found.

## 4. Payout rules for S2F and Pro accounts

### Takeaway
Pro and S2F both pay 100% of simulated profit, in $500 steps, up to **$2,000 per request** on 50K, with automated approval in minutes. Pro 50K needs 8 qualifying days per cycle, 30% consistency and a $52,600 balance to request (floor $52,000 after the withdrawal). S2F 50K needs 10 qualifying days per cycle, 20% consistency, and fixed profit targets of $3,500, then $3,000, then $2,500 from cycle 3 on. S2L live pays 80/20, daily.

### Cited Findings
- **Pro 50K:** maximum $2,000 per request. Minimum balance to request $52,600; minimum balance after the withdrawal $52,000. For comparison, 25K is $26,600 / $26,000 and 100K is $103,100 / $103,000. — [DayTraders help: Payout FAQ (Pro Accounts + S2F)](https://daytraders.com/help/articles/14363990-payout-faq-pro-accounts-s2f)
- Pro: minimum request $500, in $500 increments. To qualify, "complete qualifying days (QDays) during your payout cycle and reach the profit target required for your account size and cycle". Payouts "can be requested once the trailing drawdown has reached the initial account balance." — [DayTraders help: Payout FAQ](https://daytraders.com/help/articles/14363990-payout-faq-pro-accounts-s2f)
- Pro: 8 qualifying days per cycle, 30% consistency (no single day above 30% of total simulated profit in the payout period). — [DayTraders help: Funded Account Trading Rules](https://daytraders.com/help/articles/14367899-funded-account-trading-rules-pro-s2f)
- **S2F 50K:** Profit Target 1 = $3,500, Target 2 = $3,000, Target 3+ = $2,500. Maximum $2,000 per request. Minimum request $500. 10 qualifying days between payouts. 20% consistency. — [DayTraders help: Payout FAQ](https://daytraders.com/help/articles/14363990-payout-faq-pro-accounts-s2f); [QuantVPS overview](https://www.quantvps.com/prop-firms/day-traders)
- Split: "Pro accounts and S2F accounts enjoy a 100% simulated profit split." — [DayTraders help: Payout FAQ](https://daytraders.com/help/articles/14363990-payout-faq-pro-accounts-s2f)
- Speed: automated approval, average 32 minutes (via Plane), with funds in the bank within 24-48 hours after approval. — [PropTradingVibes review](https://www.proptradingvibes.com/prop-firms/daytraders); [DayTraders help: Funded Account Trading Rules](https://daytraders.com/help/articles/14367899-funded-account-trading-rules-pro-s2f)
- S2L live: 80/20 split, daily payout requests, automated approval. — [DayTraders: Live Funded Trading](https://daytraders.com/live-funded-trading)
- There is a step-by-step path from sign-up and payout to Live. — [DayTraders help: From Sign Up & Payout to Live](https://daytraders.com/help/articles/14368892-from-sign-up-payout-to-live-step-by-step)

### Inferences
- **Pro 50K, first payout:** the balance must reach at least $52,600 and stay at or above $52,000 afterwards. That allows a first withdrawal of at most $600, or $500 given the $500 steps, at the minimum level; withdrawing the full $2,000 needs a balance of about $54,000. For Pro Trailing, the trail locks at $50,000 once the peak reaches $52,500, consistent with "payouts once the drawdown has reached the initial balance".
- **S2F 50K, first payout:** +$3,500 profit, 10 qualifying days and the best day at most 20% of profit (so at most about $700 on a $3,500 cycle). Even then only $2,000 can be withdrawn per request.
- A bot with lumpy overnight gains will often fail the 20% (S2F) or 30% (Pro) consistency test rather than the profit test.

### Gaps
- The Pro "profit target required for your account size and cycle" was not given as a figure in any snippet, beyond the $52,600 balance threshold.
- Whether Pro Static uses the same $52,600 / $52,000 thresholds as Pro Trailing (likely, since the FAQ table is per size, but not confirmed).
- Whether the payout floor or lock changes after the first payout.
- S2L live payout minimums and maximums.

## 5. Prices and promo codes in October 2026: which 50K account costs ≤ $30?

### Takeaway
**Only the Static 50K evaluation can be bought for $30 or less.** It costs $20 with code DGT (90% off $200), per DamnPropFirms pages labelled "Verified for October 2026", or $30 at 85% off with codes such as DT or PW, which coupon testers applied successfully in September 2026. Trail 50K costs $37.90 at 90% off or $56.85 at 85% off, both above $30. The cheapest 50K S2F is $57 with DGT (90% off $570), versus $342 at the 40% off that other sources describe. Passing Static then costs the $130 Pro activation, so the cheapest path to a funded 50K is about $150-160 in total.

### Cited Findings
- **List prices (50K):** Trail $379, Static $200, EOD $469, S2F $570, S2L Core $329. — [DamnPropFirms: 24 Cheapest Futures Prop Firms, Verified for October 2026](https://damnpropfirms.com/cheapest-prop-firms/) (Trail, EOD, Static, S2F); [DayTraders: Evaluation Pricing](https://daytraders.com/promo) (S2F $370 / $570 / $825); [PropTradingVibes account types](https://www.proptradingvibes.com/blog/daytraders-account-types) (S2L Core $329, $229 on sale in April 2026)
- **Code DGT (DamnPropFirms affiliate code):** "The lowest $50K evaluation price for DayTraders with code DGT is $20". A search summary of the same site's 50K plans page shows Static $50K at $200 reduced to $20 (90% off), but elsewhere shows "$30*" as the one-time promo price. Also: "the cheapest $50K instant account is DayTraders at $57 with code DGT" (S2F, 90% off $570). Static 150K is $40 with DGT. — [DamnPropFirms DayTraders review](https://damnpropfirms.com/futures-prop-firms/daytraders/); [DamnPropFirms: Best Prop Firms With Instant Funding](https://damnpropfirms.com/best-prop-firms-with-instant-funding/); [DamnPropFirms: Best $50K plans](https://damnpropfirms.com/account-plans/50k/)
- **Static 50K at $30:** listed as "$30.00 (was $200.00)", alongside "50K Trail $56.85 (was $379.00)". Both are 85% off. The search tool did not make clear which result page this came from (candidates: the daytraders.com/?c=PFP affiliate landing page, PropTradingVibes, The Prop Firm Guide). — [DayTraders affiliate landing (?c=PFP)](https://daytraders.com/?c=PFP); [The Prop Firm Guide](https://thepropfirmguide.com/daytraders/)
- **Static 50K at $40 (80% off):** "The cheapest path to a funded DayTraders account is the 50K Static ($40) plus Pro Account activation ($130) for $170 total." Dated April 2026. — [PropTradingVibes: DayTraders Discount Code (April 2026)](https://www.proptradingvibes.com/blog/daytraders-discount-code)
- **Official codes:** "DT" gives "80% off on all evaluation plans", new accounts only, and "always applies the best available promotion at that time". Codes are single-use and tied to the user they were given to. The official promo page says evaluations "start at $40". As rendered by search, it shows Static from $40 (25K) to $90 (150K), Trail from $55 (25K) to $140 (300K), EOD from $80 (25K) to $400 (300K), S2F from $222 and S2L from $179. — [DayTraders: Exclusive Coupon Code](https://daytraders.com/coupon-code); [DayTraders: Evaluation Pricing](https://daytraders.com/promo); [DayTraders help: Coupon Code and Discounted Price](https://daytraders.com/help/articles/10751187-coupon-code-and-discounted-price)
- **Coupon-tester evidence close to October 2026:** code "PW" tested September 22, 2026 gave 85% off storewide. Code "DT" tested September 16, 2026 gave 85% off. — [TechJury: DayTraders promo codes](https://techjury.net/finance-coupons/daytraders-com/). SimplyCodes lists "90% Off Storewide (Members Only)", "last used 16 hours ago" (crawl date unknown; page titled Jul/Sep 2026). — [SimplyCodes](https://simplycodes.com/store/daytraders.com)
- **Trail 50K at 90%:** code FPF gives "90% off Trailing … bringing the price from $379.00 to $37.90", and FPF also gives "80% off Static, and 40% off S2F". — [Funded Program Finder](https://fundedprogramfinder.com/daytraders-up-to-90-off-trailing-static-s2f-accounts/)
- **S2F at 40% off:** "The 50K S2F account with 40% off costs $342.00", described as a smaller discount than on evaluations. The official promo page's "S2F starts at $222" equals 25K $370 at 40% off. — [The Prop Firm Guide](https://thepropfirmguide.com/daytraders/); [DayTraders: Evaluation Pricing](https://daytraders.com/promo)
- **LUMI:** funded.now's page title reads "DayTraders Discount Code - 85% OFF - LUMI". The search summary mixed in Apex/Lucid details, which belong to other firms. — [funded.now](https://funded.now/propfirm/daytraders)
- Other codes seen on coupon sites, with October 2026 status unverified: UCKUOOEA ("up to 90%", said to appear on the official site), DMTDQWVJ, QJPQMJIR, jcdaytrader. — [DontPayFull (title: "October 2026")](https://www.dontpayfull.com/at/daytraders.com); [Funded Program Finder](https://fundedprogramfinder.com/daytraders-unlock-up-to-90-off-limited-time-discounts/)

### Inferences
- **Is Static 50K really about $30 with DGT?** Sources disagree on the exact figure. DamnPropFirms (October 2026) shows $20 (90% off) in one place and "$30*" in another, and other sites show $30 at 85%. Either way it is **≤ $30** and is the only 50K account in budget.
- **Is Trail 50K about $38 at 90% off?** Yes, $37.90, but only when a 90% Trail promo is running (FPF, possibly DGT). At the 85% seen in September 2026 it is $56.85. Both exceed the $30 budget.
- **Is any 50K S2F close to $30-57?** Yes: $57 with DGT per DamnPropFirms (October 2026). It is above budget, but it has no activation fee, so the full cost to a funded account is $57 versus Static's $20-30 plus $130.
- Promo levels appear to rotate between 80%, 85% and 90%, and DayTraders says DT "always applies the best available promotion". Expect $20, $30 or $40 for Static 50K depending on the day.

### Gaps
- No page read verbatim on 2026-10-07 confirms the price at checkout today. All October 2026 evidence is search summaries of DamnPropFirms pages labelled "Verified for October 2026" and the title of DontPayFull's October 2026 page.
- The official promo page's per-size table contradicts "Static 50K $200 list → $40 at 80%". As rendered, it would put Static 25K at $40. Most likely 25K and 50K show the same promo price, or the summary is garbled. Not resolved.
- The 50K EOD and S2L Core promo prices for October 2026 were not found.

## 6. Platforms and data feed: Rithmic? Quantower? NinjaTrader? Aggressor side?

### Takeaway
DayTraders runs on **Rithmic**. Quantower, Sierra Chart, ATAS, Bookmap, MotiveWave, Jigsaw, VolFix, rTrader Pro and the in-house ONYX are supported. NinjaTrader is **officially not supported**; third-party add-ons offer a workaround. ProjectX with API access is reported by one partner. Rithmic's trade messages carry an **aggressor (buy/sell) field**, so trade-side delta can be read from the feed.

### Cited Findings
- "DayTraders uses Rithmic as their data and execution provider". As of April 2026 the supported platforms are ONYX (browser-based, TradingView charts plus Rithmic data), rTrader Pro and rTrader Pro Mobile, **Quantower**, MotiveWave, VolFix, **Sierra Chart**, Jigsaw Daytradr, Finamark, **ATAS**, WealthCharts, **BookMap** and EdgeProX. — [PropTradingVibes: DayTraders Platforms (2026)](https://www.proptradingvibes.com/blog/daytraders-platforms); [DayTraders: Partners & Supported Platforms](https://daytraders.com/partners); [DayTraders help: Connecting to Rithmic Services](https://daytraders.com/help/articles/11506225-connecting-to-rithmic-services)
- NinjaTrader: DayTraders "currently DO NOT support Ninja Trader on any of their accounts". A third-party add-on (PropFirmConnector) supplies the missing Rithmic connection inside NT8. — [DayTraders help: Platform Connection Guides](https://daytraders.com/help/articles/9856562-platform-connection-guides); [PropFirmConnector](https://propfirmconnector.com/connect/daytraders/)
- S2L live: NinjaTrader and Tradovate are not supported; only ONYX, rTrader Pro and select Rithmic platforms work (as of April 2026). — [PropTradingVibes: DayTraders Platforms](https://www.proptradingvibes.com/blog/daytraders-platforms)
- ProjectX at daytraders.projectx.com "with full API support". — [PickMyTrade blog](https://blog.pickmytrade.io/projectx-vs-rithmic-automation-bulenox-daytrader/)
- TradersPost webhook automation is supported. — [TradersPost blog](https://blog.traderspost.io/article/automate-day-traders-with-traderspost)
- **Aggressor side:** in the open-source async-rithmic client (v1.6.6 on PyPI), Rithmic's R|Protocol `LastTrade` protobuf message defines a field `aggressor` of type `rti.LastTrade.TransactionType` (buy/sell). I checked this directly in the downloaded `last_trade_pb2.py`. — [async-rithmic on PyPI](https://pypi.org/project/async-rithmic/). Rithmic provides "real tick-by-tick data" for order flow. — [ThorTradeCopier: what is the Rithmic feed](https://thortradecopier.com/blog/what-is-rithmic-futures-data-feed)
- DayTraders Pro and EOD Pro include a free real-time data feed (a "$55/month value"). — [DayTraders help: EOD Account Rules](https://daytraders.com/help/articles/14473672-eod-account-rules)

### Inferences
- A Quantower-based or Rithmic-API bot that reads trade-by-trade aggressor side (needed for the project's delta filter) is technically compatible with DayTraders accounts. Quantower is on the official partner list.

### Gaps
- Whether DayTraders' Rithmic credentials may be used by a **self-written R|Protocol client**, which needs a Rithmic-conformed app name, rather than an approved platform. Not found.
- Whether ProjectX is still offered in October 2026, and on which account lines.
- Whether any account line (EOD, S2F) runs on a non-Rithmic backend. Nothing suggests it, but it was not checked explicitly.

## 7. 2026 rule changes, complaints, bans of automated traders, reputation

### Takeaway
Reputation is broadly positive: about 4.4-4.5/5 on Trustpilot with roughly 340-350 reviews by April 2026, and fast automated payouts. The recurring complaints are about **rule changes**, including a 30-day "profit goal" activity requirement. No report was found of DayTraders banning a normal-frequency automated trader. Rules have clearly been restructured in 2025-2026: new consolidated rule articles, EOD and S2L lines, and different activation fees.

### Cited Findings
- Trustpilot: 4.4/5 on 352 reviews as of April 2026, 81.82% five-star. Separately 4.5/5 on 336 reviews. Reviewers praise fast payouts and support. "Some customers expressed dissatisfaction with new rules that they felt were counter-intuitive or led to account disqualifications." — [PropTradingVibes review](https://www.proptradingvibes.com/prop-firms/daytraders); [Trustpilot: DayTraders.com](https://www.trustpilot.com/review/daytraders.com)
- One Trustpilot complaint calls it a "terrible prop firm" because of "rule changes requiring arbitrary profit goals every 30 days" that the reviewer felt clashed with good risk management. This matches the official 30-day minimum activity policy. — [Trustpilot (NZ page)](https://nz.trustpilot.com/review/daytraders.com); [DayTraders help: Minimum Activity Policy](https://daytraders.com/help/articles/9854806-keep-your-accounts-active-minimum-activity-policy)
- Product lines as of April 2026: Trail, Static, S2F, S2L. EOD appears separately in the official help center and on DamnPropFirms' October 2026 listing. S2L is described as the "newer offering". — [PropTradingVibes review](https://www.proptradingvibes.com/prop-firms/daytraders); [DayTraders help: EOD Account Rules](https://daytraders.com/help/articles/14473672-eod-account-rules); [DamnPropFirms (Oct 2026)](https://damnpropfirms.com/cheapest-prop-firms/)
- The firm is Las Vegas-based; it describes itself as education, evaluation and simulated trading for non-professional futures traders. — [Benzinga: DayTraders review](https://www.benzinga.com/money/daytraders-review)
- The firm has expanded beyond futures: an ArcTrader crypto demo account, and a "DTG" code for free ArcTrader accounts. — [DayTraders help: ArcTrader Crypto Demo Account](https://daytraders.com/help/articles/15587659-arctrader-crypto-demo-account); [DayTraders: Exclusive Coupon Code](https://daytraders.com/coupon-code)

### Inferences
- The help-center article IDs for the consolidated rule pages (14367899, 14368378, 14363990, 14473672) are much higher than older articles (98xxxxx), which points to a 2025-2026 rewrite. Third-party pages dated 2025 or early 2026 may therefore be stale. That would explain the conflicts on contract limits and activation fees, and PipBack's "auto-close" claim.

### Gaps
- Reddit threads specific to DayTraders could not be retrieved (search returned none).
- No account was found, positive or negative, of an automated, overnight-holding trader being paid or banned at DayTraders.
- No dated change log or announcement of 2026 rule changes was found.
