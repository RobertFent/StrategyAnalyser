# StrategyAnalyser

Tests indicator-based swing trading rules on S&P 500 stocks over 10+ years, with clear buy and sell rules.
It compares them honestly against simply holding the index.

No programming needed: double-click the launcher and click through the Workbench. The **[Guide](docs/GUIDE.md)** explains each step in more detail.

## Quick start

**No Terminal needed.** You need Python 3.10 or newer ([python.org/downloads](https://www.python.org/downloads/);
on Windows tick *"Add Python to PATH"* in the installer). Then:

1. **Double-click `start.command`** (Mac) or **`start.bat`** (Windows) in this folder.
   The first run installs the Python packages (1–2 minutes). Keep the window open while you work.
   *Mac: if it says the file can't be opened, right-click → Open once. If it opens in a text editor instead,
   open the Terminal in this folder and run `bash start.command`.*
2. Your browser opens the **Strategy Workbench**. Every step is a button, in order:

| Step | Button | What happens |
|---|---|---|
| 1 | **Download all price data** | ~14 years of daily prices for every stock that was in the S&P 500 since 2016, plus SPY (1–2 min). The status line then shows the date range and how much of the index history has prices. Backtests only buy a stock while it was in the index. |
| 2 | **Open the Planner** | describe your own rules (dip buying or trend following), save, run. Write the rules down before you look at any result. |
| 3 | **Report for this plan** | one-page report for the selected rule set: verdict (7 checks, all must pass), key numbers, growth of $10,000 vs SPY, drawdowns, year by year |
| 3 | **Compare all plans with SPY** | every saved rule set on one page against SPY buy & hold and SPY timing |
| 4 | **Quick / Full** stress test | verdict and luck checks (1 min), or also neighbouring settings, costs and a random-entry test (5 min); text report |
| 5 | **Start search** | tries hundreds of rule sets with walk-forward validation (5–15 min); then *Report of the best set* or *Save best set as a plan* |

**In short:** first time → step 1 *Download all price data* (later only *Add the latest trading days*). Your own rules → step 2
Planner: write them down first, test once, don't tweak until it looks good. See results → step 3 *Report for this plan*
or *Compare all plans with SPY*. Check it holds up → step 4 *Quick* stress test; step 5 only to let the computer search for rules.
Results appear under *Jobs* → *Open report*; read the **test period** and the **verdict** first.

The switch at the top chooses **Stocks** (the steps above) or **Options: SPY call spreads** (its own four steps: *Download SPY + VIX*, *Build your spread routine* with width, expiry, the debit you pay and the close rule → *Save as a plan*, *Reports* with the same one-page report, *Try 720 setups*).

Long steps run in the background; their progress and results appear under *Jobs* on the right. You can close the
browser tab; the jobs keep running while the launcher window is open.

### How to read a result
| Where | What to look for |
|---|---|
| Verdict | all 7 checks must pass before paper trading |
| Test period (2025 – today) | the honest numbers; the rules never saw this data |
| SPY timing | hold SPY only above its 200-day average; if a strategy can't beat this, its stock picking adds nothing |
| Unlikely to be luck | below 90% means chance alone produces results like this; each variant you tried raises the bar |
| Stitched OOS (searches) | rules re-picked each year and traded the next; compare with the SPY lines below it, not with the in-sample score |

### Paper trading (after a plan passed)
In a Terminal in this folder, with the environment on (`source .venv/bin/activate`, Windows `.venv\Scripts\activate`):
```sh
python3 -m backtest.fetch --update                                        # daily: latest prices
python3 -m backtest.signals --params strategies/<plan>.json --holding AAPL MSFT   # buy candidates, sell signals
python3 -m backtest.report --params strategies/<plan>.json --start <first day> --holdout-start <first day>  # monthly check
```

### The same steps in the Terminal
```sh
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
python3 -m backtest.fetch --historical       # step 1
python3 -m backtest.app                      # step 2, planner + workbench
python3 -m backtest.report                   # step 3 (strategies/willr.json)
python3 -m backtest.compare                  # step 3, all plans
python3 -m backtest.analyze --params strategies/<plan>.json --quick       # step 4
python3 -m backtest.tune --space momentum --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 400 --min-trades 20   # step 5
python3 -m backtest.spreads                  # step 6, SPY call spreads (--fetch once; --params strategies/bcs_495.json for the HTML report; --tune)
python3 -m backtest                          # list of all commands
```
Details for every step, and the math behind each button: **[docs/GUIDE.md](docs/GUIDE.md)** (section 7).

## Main finding (status 21 October 2026)
Several thousand rule sets were tested: 10 oversold indicators, momentum and breakout rules, trend and market
filters, stops and exits. They were checked year by year on 2019–2024 and on a 2025–2026 period never used to
choose them, with point-in-time index membership (no survivorship bias) and a check for luck.

**No rule set beats holding SPY.** With survivorship bias removed, the best dip-buying and momentum rules make
about 7.6% a year against SPY's 15%, with similar drawdowns, and none passes the "unlikely to be luck" check.
The 200-day trend filter does most of the work; the indicators add little.

**One plan passes every check: a SPY bull call spread routine** (every third Friday, the $10-wide spread that costs $4.95, two
monthly expirations out, only above the 200-day average). 23.8% a year with a −22% worst drop in the backtest, but the option
prices are modelled from the VIX and six months of real trading were flat; paper-trade and log the fills before believing it
(research doc, section 7.3).

| 2016 – Oct 2026, point-in-time members, 88% of member-days with prices | Return / year | Worst drop | Verdict |
|---|---|---|---|
| SPY buy & hold | 15.1% | −33.7% | – |
| SPY timing (hold SPY only above its 200-day average) | 11.4% | −20.7% | – |
| Reference dip-buying rules (`strategies/willr.json`) | 7.6% | −27.4% | 2 of 7, luck check 5% |
| Momentum, best of 400 (`strategies/best_strategy.json`) | 7.6% out-of-sample 2019–24 | −29.2% | luck check 0% |
| RSI(4) rule book, best variant: deep below the 200-day average (`strategies/rsi4_deep.json`) | 8.6% | −30.7% | 3 of 7, luck check 4% |
| **SPY bull call spread, $4.95 on $10, 2 monthly expirations (`strategies/bcs_495.json`)** | **23.8%** | **−22.2%** | **7 of 7, luck check 93%**, option prices modelled: not confirmed by real trades yet |

Full results, verdicts and reasoning: **[docs/strategy-research.md](docs/strategy-research.md)**.
Searching, stress tests and engine details: [docs/TECHNICAL.md](docs/TECHNICAL.md).

## What's in here
| Folder | Contents |
|---|---|
| `strategies/` | saved rule sets: `willr.json` (dip-buying reference), `best_strategy.json` (best of the momentum search), `rsi4_*.json` (RSI(4) rule book: classic, OBE, 5% adds, deep below the average), `bcs_*.json` (SPY call spread routine and three tuned variants), `candidate_breadth.json`, `coach_plan.json` (template), plus your own |
| `symbols/` | index lists and `sp500_membership.csv` (who was in the S&P 500 when) |
| `docs/` | guide, findings, technical notes |
| `backtest/` | the code (`python3 -m backtest.<command>`) |
| `output/` | reports and results (created when you run something) |

*Backtests are not a promise. Prices of companies that were delisted after leaving the index are mostly unavailable, so results are still slightly optimistic.*
