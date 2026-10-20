# Guide: testing a trading plan

This tool answers one question: **would these buy and sell rules have made money on S&P 500 stocks,
and would they have done better than simply holding the index?** No coding is needed. You type a few
commands into the Terminal and read the result in your browser.

---

## 1. One-time setup (about 10 minutes)

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

## 2. See the existing results

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

## 3. Test your own trading plan

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
