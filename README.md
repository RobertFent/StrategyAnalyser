# StrategyAnalyser

Tests indicator-based swing trading rules on S&P 500 stocks over 10+ years, with clear buy and sell rules.
It compares them honestly against simply holding the index.

No programming needed: follow the quick start below. The **[Guide](docs/GUIDE.md)** explains each step in more detail.

## Quick start: step by step

Everything runs in a Terminal opened in this folder. On a Mac: right-click the folder → *Services* →
*New Terminal at Folder*. On Windows: open the folder, type `cmd` in the address bar, press Enter.
You need Python 3.10 or newer ([python.org/downloads](https://www.python.org/downloads/)).

### Step 0 – one-time setup (5 minutes)
```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 tests/test_backtest.py     # prints "ok ..." 15 times if everything works
python3 -m backtest                # lists every command
```
Every later time you open a Terminal here, run only `source .venv/bin/activate` (Windows: `.venv\Scripts\activate`).

### Step 1 – get the price data (2 minutes)
```sh
python3 -m backtest.fetch --historical
```
Downloads ~14 years of daily prices for every stock that was in the S&P 500 since 2016, plus SPY. The last
line, "Member-days with prices: XX%", says how complete the history is. Backtests only buy a stock while it was
in the index, so results are not flattered by today's winners.

### Step 2 – look at the reference result (1 minute)
```sh
python3 -m backtest.report
```
Opens a one-page report in your browser for the reference rule set. Read the **Verdict** first: 7 checks, all
must pass. Then the test-period numbers and the growth chart against SPY.

### Step 3 – build and test your own plan (a few minutes per plan)
```sh
python3 -m backtest.app
```
Opens the Strategy Planner in your browser (it runs only on your computer). Pick the strategy type:
- **Buy the dip:** an oversold indicator (RSI, Williams %R, Stochastic, Connors RSI, CCI, ...), its length and
  level, first day or any day, trend and market filters, exits, number of positions.
- **Follow the trend:** the strongest stocks by 3–12-month performance (top N, weekly or monthly rebalance,
  optional "ignore the last month") or breakouts to a new N-day high; exits by rank, moving average, channel
  low or trailing stop.

Under *More options*, fill in **"Variants tried before this one"** honestly; it raises the bar for the luck check.
Write the rules down before you look at any result, then click **Save & run backtest**. The report opens after
about a minute. Saved plans can be reopened with *Edit* and re-run with *Report*.

### Step 4 – read the result
| Where | What to look for |
|---|---|
| Verdict | all 7 checks must pass before paper trading |
| Test period (2025 – today) | the honest numbers; the rules never saw this data |
| SPY timing | hold SPY only above its 200-day average; if a strategy can't beat this, its stock picking adds nothing |
| Unlikely to be luck | below 90% means chance alone produces results like this |

### Step 5 – stress-test a plan (optional, 1–5 minutes)
```sh
python3 -m backtest.analyze --params strategies/<plan>.json --quick   # verdict + luck checks, ~1 min
python3 -m backtest.analyze --params strategies/<plan>.json           # + neighbors, costs, random entries, ~5 min
```

### Step 6 – search many rule sets (optional, 5–15 minutes)
```sh
python3 -m backtest.tune --space momentum --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 400 --min-trades 20
python3 -m backtest.report --params output/tuning_<timestamp>/best_params.json
```
Spaces: `default` (all oversold indicators), `indicators`, `breadth`, `exits`, `momentum`. Judge a search by
"Stitched OOS" (rules re-picked each year, traded the next) against the SPY lines, not by the best in-sample score.
Remember: the more you search, the more the best result is luck; the report deflates for that.

### Step 7 – paper trade a plan that passed
```sh
python3 -m backtest.fetch --update                                        # daily: latest prices
python3 -m backtest.signals --params strategies/<plan>.json --holding AAPL MSFT   # buy candidates, sell signals
python3 -m backtest.report --params strategies/<plan>.json --start <first day> --holdout-start <first day>  # monthly check
```

Details for every step: **[docs/GUIDE.md](docs/GUIDE.md)**.

## Main finding (status 20 October 2026)
Several thousand rule sets were tested: 10 oversold indicators, momentum and breakout rules, trend and market
filters, stops and exits. They were checked year by year on 2019–2024 and on a 2025–2026 period never used to
choose them, with point-in-time index membership (no survivorship bias) and a check for luck.

**No rule set beats holding SPY.** With survivorship bias removed, the best dip-buying and momentum rules make
about 7.6% a year against SPY's 15%, with similar drawdowns, and none passes the "unlikely to be luck" check.
The 200-day trend filter does most of the work; the indicators add little.

| 2016 – Oct 2026, point-in-time members, 88% of member-days with prices | Return / year | Worst drop | Verdict |
|---|---|---|---|
| SPY buy & hold | 15.1% | −33.7% | – |
| SPY timing (hold SPY only above its 200-day average) | 11.4% | −20.7% | – |
| Reference dip-buying rules (`strategies/current.json`) | 7.6% | −27.4% | 2 of 7, luck check 5% |
| Momentum, best of 400 (`strategies/candidate_momentum.json`) | 7.6% out-of-sample 2019–24 | −29.2% | luck check 0% |

Full results, verdicts and reasoning: **[docs/strategy-research.md](docs/strategy-research.md)**.
Searching, stress tests and engine details: [docs/TECHNICAL.md](docs/TECHNICAL.md).

## What's in here
| Folder | Contents |
|---|---|
| `strategies/` | saved rule sets: `current.json` (reference), `candidate_breadth.json`, `candidate_momentum.json`, `coach_plan.json` (template), plus your own |
| `symbols/` | index lists and `sp500_membership.csv` (who was in the S&P 500 when) |
| `docs/` | guide, findings, technical notes |
| `backtest/` | the code (`python3 -m backtest.<command>`) |
| `output/` | reports and results (created when you run something) |

*Backtests are not a promise. Prices of companies that were delisted after leaving the index are mostly unavailable, so results are still slightly optimistic.*
