# Guide: testing a trading plan

This tool answers one question: **would these buy and sell rules have made money on S&P 500 stocks,
and would they have done better than simply holding the index?** No coding is needed. You type a few
commands into the Terminal and read the result in your browser.

---

## 0. The short way: the launcher and the Workbench

Double-click **`start.command`** (Mac) or **`start.bat`** (Windows). The first run sets everything up; then the
**Workbench** opens in your browser with one button per step below (download data, reports, planner, stress test,
search). Long steps run in the background and show their progress under *Jobs*. Everything in sections 1–5 can be
done from there; the Terminal commands remain for reference.

**In short:** first time → step 1 *Download all price data* (later only *Add the latest trading days*). Your own rules → step 2
Planner: write them down first, test once, don't tweak until it looks good. See results → step 3 *Report for this plan*
or *Compare all plans with SPY*. Check it holds up → step 4 *Quick* stress test; step 5 only to let the computer search for rules.
Results appear under *Jobs* → *Open report*; read the **test period** and the **verdict** first.

## 1. One-time setup by hand (about 10 minutes)

1. **Install Python.** On a Mac, download it from [python.org/downloads](https://www.python.org/downloads/)
   and run the installer. On Windows, tick *"Add Python to PATH"* in the installer.
2. **Get this folder** onto your computer: download it from GitHub as a ZIP, or get it from Robert, and unzip it.
3. **Open a Terminal in this folder.**
   - Mac: right-click the folder → *Services* → *New Terminal at Folder*.
   - Windows: open the folder, type `cmd` in the address bar and press Enter.
4. **Copy these lines into the Terminal**, pressing Enter after each:
   ```sh
   python3 -m venv .venv
   source .venv/bin/activate          # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   python3 -m backtest.fetch --historical   # ~14 years of prices incl. past index members, 1-2 minutes
   ```

Next time you open a Terminal in the folder, you only need the `source .venv/bin/activate` line
(Windows: `.venv\Scripts\activate`).
To see all commands at any time: `python3 -m backtest`

---

## 2. Test your own trading plan

```sh
python3 -m backtest.app
```
This opens the **Strategy Planner** in your browser. It runs only on your own computer.

1. **Name** the plan.
2. **When to buy:** choose the strategy type first.
   - *Buy the dip:* pick the indicator, e.g. RSI, Williams %R, Stochastic, Connors RSI or CCI. Set its length and
     the oversold level, e.g. RSI(4) below 20, and whether to buy only on the first day or on any day it's there.
   - *Follow the trend:* buy the strongest stocks (top N by performance over 3–12 months, checked weekly or monthly)
     or breakouts to a new N-day high.
3. **Filters:** the stock above its 200-day average, the S&P 500 (SPY) above its 200-day average.
4. **When to sell:** the indicator recovers, close above yesterday's high, stop loss, trailing stop, or a maximum number of days.
5. **Positions:** how many at the same time.

The box on the right shows the rules in plain English while you type. Click **Save & run backtest**. After about a
minute the report opens; *Back to the planner* takes you back. Saved plans can be reopened with **Edit** or **Report**.
When you're done, close the Terminal window or press `Ctrl+C`.

*Prefer the Terminal?* `python3 -m backtest.plan` asks the same questions one by one, and
`python3 -m backtest.report --params strategies/<name>.json` creates the report.

### Ground rules for a fair test
- **Write the plan down before you test it.** Test it once.
- **Don't tweak the numbers until the result looks good.** With enough tweaking every plan looks great on
  past data and then fails with real money. That is the main lesson of this research.
- **Want to compare variants?** Decide them all up front, e.g. RSI(2), RSI(4) and RSI(7), and test all of
  them. Don't keep only the best.
- **The test period** (2025 until today) was never used to pick any rule. It is the most honest number in the report.

---

## 3. See the existing results

```sh
python3 -m backtest.report
```
This opens a one-page report in your browser for the reference rule set. It covers:

- the rules in plain English
- a **verdict** (6 checks, all must pass)
- key numbers
- the growth of $10,000 compared with the S&P 500
- the worst drops
- year-by-year returns

Other saved rule sets are in the `strategies` folder, for example:
```sh
python3 -m backtest.report --params strategies/best_strategy.json
```
To see all of them on one page against SPY:
```sh
python3 -m backtest.compare
```

---

## 4. How to read the report

| In the report | Meaning | Good when |
|---|---|---|
| Return per year | average yearly growth after costs | higher than SPY, or close to it with smaller drops |
| Worst drop | biggest fall from a previous high (−20% = $10,000 became $8,000) | clearly smaller than SPY's |
| Sharpe | return per unit of ups and downs (SPY ≈ 0.9) | above 1.1 |
| Calmar | return per year ÷ worst drop | higher than SPY timing |
| SPY timing | hold the S&P 500 only while it's above its 200-day average | the strategy should beat this, otherwise the stock picking adds nothing |
| Development period | the years used to find the rules | always looks good, so don't trust it alone |
| **Test period** | data the rules have never seen | **this is the honest number** |
| **Verdict** | 7 checks agreed on before testing | **all 7 must pass before paper trading** |
| Unlikely to be luck | probability that the edge over SPY is more than chance; the more variants you tried, the higher the bar | at least 90% |

---

## 5. Paper trade a plan that passed

1. **Every trading day after the US close** (or before the next open):
   ```sh
   python3 -m backtest.fetch --update
   python3 -m backtest.signals --params strategies/<plan>.json --holding AAPL MSFT
   ```
   It lists the buy candidates for the next open, ranked, and for the stocks you hold whether to sell.
   Stop losses are price levels: enter them at your broker.
2. **Once a month**, compare what the rules did since you started with SPY:
   ```sh
   python3 -m backtest.report --params strategies/<plan>.json --start <first day> --holdout-start <first day>
   ```
3. **After 3–6 months**, if paper results are close to the backtest, consider small real positions.

---

## 6. Good to know

- **Survivorship bias:** the backtest knows which stocks were in the S&P 500 on each day and only buys those.
  Prices of companies that were delisted after leaving the index are mostly unavailable, so results are still
  slightly optimistic. `python3 -m backtest.fetch --historical` prints how much history is covered.
- **Costs:** the tests assume 0.05% per buy or sell. The verdict also checks double costs.
- **Long only:** the tool only buys stocks, it never shorts. Daily bars only: buy at the next open after a
  signal at the close.
- **Questions or problems:** ask Robert. Error messages in the Terminal usually say what is missing, for
  example "Run python3 -m backtest.fetch first".

---

## 7. What happens behind each button

All steps share one engine: for every stock and every day the rules say *buy* or *sell*, a signal at the close is
executed at the next day's open, 0.05% cost per buy and per sell, 10% of the account per position, cash earns nothing.
A stock is only tradeable on days it was actually in the index. Everything below is computed on that simulated account.

### Price data (step 1)
Downloads daily open / high / low / close / volume from Yahoo Finance for every ticker that was in the S&P 500 since
2016 (past members included, from the published membership history) plus SPY. Prices are adjusted for splits and
dividends. Indicators (RSI, Williams %R, moving averages, momentum ranks…) are computed from these once and cached.

### Build your own plan (step 2)
No math; it writes the rules to a file in `strategies/`. The plain-English box is the same text the report shows.

### Reports (step 3)
The account's daily value over the whole period is the basis for every number:

| Number | How it is computed |
|---|---|
| Return per year (CAGR) | the constant yearly growth rate that turns the start value into the end value |
| Worst drop (max drawdown) | the largest fall from any previous high of the account, in percent |
| Volatility | standard deviation of daily returns × √252 (yearly) |
| Sharpe | average daily return ÷ its standard deviation, × √252. Return per unit of wobble; SPY ≈ 0.9 |
| Sortino | like Sharpe, but only down days count as wobble |
| Calmar | return per year ÷ worst drop. Return per unit of pain |
| Profit factor | sum of all winning trades ÷ sum of all losing trades |
| Win rate, average trade, days held | straight from the trade list |
| SPY buy & hold | the same account holding only SPY |
| SPY timing | holding SPY only on days it closed above its 200-day average, otherwise cash |
| Verdict | the 7 checks of section 4, each a comparison of these numbers between the plan, SPY and SPY timing; the luck check is the quick stress test (below) |

Development period = backtest start to the test-period start; test period = test-period start to today, computed
separately with the same rules. *Compare* runs the same thing for every plan and adds the correlation of daily
returns between plans (1 = move together, 0 = unrelated).

### Stress test (step 4)
Asks whether the report could be a fluke. **Quick** runs the first two, **Full** all four:

1. **Bootstrap.** Take the plan's daily returns minus SPY's. Build 2,000 alternative histories by re-shuffling
   20-day blocks of those excess returns, and count how often the average stays above zero. 95% means the
   edge over SPY survived in 95% of re-shuffles.
2. **Deflated Sharpe ratio** (Bailey & López de Prado). The probability that the excess Sharpe is above zero,
   after correcting for the number of variants tried: with 400 variants the best one is expected to look good by
   chance alone, so the bar rises with the "variants tried" field. The verdict's *Unlikely to be luck* is the
   smaller of 1 and 2 and must be at least 90%.
3. **Neighbourhood.** Change one setting at a time (RSI length 4 → 3 or 5, threshold 15 → 10 or 20, stop
   3 → 4 × ADR…) and re-run. A real edge degrades gently; a lucky one collapses next door.
4. **Costs and random entries.** Re-run at double costs (0.10% per side). Then keep every trade's stock, year and
   holding time but move its entry to a random day that passes the same filters (trend, market, liquidity),
   30 times. If random days do as well, the indicator's timing adds nothing; the filters did the work.

### Search (step 5)
Tries many rule sets and tells you how good "pick the best" really is:

1. Draw N rule sets at random from the chosen space (e.g. RSI/Williams/Stochastic lengths × thresholds × filters × exits).
2. **Walk-forward.** Split the development period into folds: 3 years to pick, the following 1 year to trade, then
   move forward a year. In each fold every rule set is backtested on the 3 years and ranked by the chosen metric;
   the winner is run on the next year it has never seen. Chaining those unseen years gives the **stitched OOS**
   line: what you would have earned by re-picking the best rules every year. This, not the in-sample score, is
   the honest result of the search.
3. **Best set.** The rule set with the best score over the whole development period is saved as
   `best_params.json` and run once on the test period. Its development-period numbers are in-sample and flattered
   by the search; its test-period and stitched-OOS numbers are not.
4. Constraints: at least 20 trades per window and a worst drop no deeper than 35%, otherwise the set is discarded.

**Rank by** decides what "best" means in step 2 and 3: *Calmar* = most return per unit of worst drop (favours
smooth equity, the default), *Sharpe* = most return per unit of daily wobble, *Return* = highest growth regardless
of drops (tends to pick wild sets). The search also records the number of variants tried, which the stress test
uses to deflate the luck check.
