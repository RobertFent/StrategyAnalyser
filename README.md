# StrategyAnalyser

Tests indicator-based swing trading rules on S&P 500 stocks over 10+ years, with clear buy and sell rules.
It compares them honestly against simply holding the index.

**Not a programmer?** Start with the **[Guide](docs/GUIDE.md)**. It covers setup, testing your own plan without
coding, reading the report and paper trading.

## Quick start
```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m backtest.fetch           # ~14 years of daily prices (1 min)
python3 -m backtest.app             # planner in your browser: build a plan and test it with one click
python3 -m backtest.report          # report for the reference rule set
python3 -m backtest                 # list of all commands
```

## Main finding (status 20 October 2026)
Several thousand rule sets were tested: 10 oversold indicators, momentum and breakout rules, trend and market
filters, stops and exits. They were checked year by year on 2019–2024 and on a 2025–2026 period never used to
choose them, with point-in-time index membership (no survivorship bias) and a check for luck.

**No rule set beats holding SPY.** With survivorship bias removed, the best dip-buying and momentum rules make
7–8% a year against SPY's 15%, with similar or worse drawdowns, and none passes the "unlikely to be luck" check.
The 200-day trend filter does most of the work; the indicators add little.

| 2016 – Oct 2026, point-in-time members | Return / year | Worst drop | Verdict |
|---|---|---|---|
| SPY buy & hold | 15.0% | −33.7% | – |
| SPY timing (hold SPY only above its 200-day average) | 11.4% | −20.7% | – |
| Reference dip-buying rules (`strategies/current.json`) | 8.1% | −22.8% | 2 of 7 |
| Momentum, best of 400 (`strategies/candidate_momentum.json`) | 6.8% out-of-sample | −37.5% | luck check 1% |

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
