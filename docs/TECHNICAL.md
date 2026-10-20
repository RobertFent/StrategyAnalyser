# Technical notes

For anyone who wants to go beyond `backtest.plan` and `backtest.report`: searching rule sets,
stress tests and how the engine works. Non-technical guide: [GUIDE.md](GUIDE.md).

```
backtest/
  fetch.py, symbols.py      data download (Yahoo Finance, Wikipedia index lists)
  features.py               indicators, all oscillators on a 0..100 scale (low = oversold)
  strategy.py               StrategyParams: the rule set + plain-English describe()
  engine.py                 trade generation (numba) and portfolio simulation
  metrics.py, benchmarks.py CAGR, drawdown, Sharpe, Calmar; SPY buy & hold, SPY timing
  criteria.py               the 6 pass/fail checks used by the verdict
  app.py, plan.py, report.py  planner web app (stdlib http.server, 127.0.0.1 only), terminal questionnaire, HTML report
  run.py, analyze.py, tune.py, signals.py
  search_space.py           what tune searches
strategies/                 rule sets as JSON
tests/                      python3 tests/test_backtest.py (no network)
```

## Research workflow
All commands run from the repo root. Each command prints a report and writes it to `output/<command>_<timestamp>/`.

| Step | Command | What it does |
|---|---|---|
| 1. Data | `python3 -m backtest.fetch` / `--update` | ~14 years of adjusted daily OHLCV + SPY/QQQ into `data/` |
| 2. Tune | `python3 -m backtest.tune --space default --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar` | random/grid search with walk-forward validation (train 3y, test 1y), then one run on the untouched holdout |
| 3. Analyze | `python3 -m backtest.analyze --params output/tuning_<ts>/best_params.json` (`--quick` = verdict only) | **pass/fail verdict**, comparison with SPY and SPY timing, one parameter changed at a time, cost sensitivity, ranked vs random slot choice, signal vs random entry, regimes, other indices |
| 4. Backtest | `python3 -m backtest.run --params strategies/current.json --start 2016-01-01` | full report, trades.csv and equity.csv vs SPY and SPY timing |
| 5. Adopt | copy a `best_params.json` to `strategies/current.json` | only if the analyze verdict passes |
| 6. Paper trade | daily `python3 -m backtest.fetch --update && python3 -m backtest.signals --holding AAPL ...`, monthly `python3 -m backtest.run --params strategies/current.json --start <first paper day>` | entry candidates and exit signals; monthly check of what the rules did since you started |
| Own plan | edit `strategies/coach_plan.json`, then `python3 -m backtest.analyze --params strategies/coach_plan.json` | test a trading plan as a fixed hypothesis |
| Tests | `python3 tests/test_backtest.py` | engine sanity checks |

**Search spaces** live in `backtest/search_space.py`: `default` (all oscillators), `indicators` (only MFI, Bollinger %B, Connors RSI, Ultimate Oscillator, MACD and CCI), `breadth` (only buy when many stocks are oversold at once, with fewer slots) and `exits` (trailing stops, close-above-yesterday's-high exit). Narrow or extend any space with `--only key=v1,v2`, e.g. `--only entry_indicator=willr max_positions=5`.

**Rules** are `StrategyParams` in `backtest/strategy.py`; `describe()` prints them in plain English. Entry oscillators: RSI, Williams %R, Stochastic, IBS, MFI, Bollinger %B, Connors RSI, Ultimate Oscillator, MACD histogram and CCI. MACD and CCI are converted to a percent rank over the last `entry_length` days so they fit the same scale. Formulas are in `backtest/features.py`. Oscillators use a 0..100 scale where low = oversold, so Williams %R −90 is `entry_threshold=10`.

**Execution model:** the signal is taken at the close and filled at the next open. Stops fill at the stop price, or at the open if the price gaps below it. Costs are 5 bps per side. Positions are equal-weight slots.

### Before adopting a rule set
- **Walk-forward:** for a tuned set, the "Stitched OOS" result in the tune report must be at least as good as SPY and SPY timing. This is the honest number, not the in-sample top score.
- **Verdict:** `backtest.analyze` must pass all criteria in `backtest/criteria.py`. Set the thresholds before looking at results.
- **Neighborhood:** values next to the chosen parameters must perform similarly (a plateau, not a spike).
- **Caveat:** `symbols/` holds today's index members, so stocks that dropped out are missing (survivorship bias). Expect live results to be lower.

**Benchmarks:** "SPY timing" means holding SPY only while it is above its 200-day average, otherwise cash. A stock-picking strategy that can't beat it gets its edge from the trend filter, not from picking stocks.

## How the engine works
- **Signals** are computed at the close of day t from data up to t only. A test checks that changing future prices never changes past trades.
- **Trades:** one position per stock at a time. Exits are checked in this order: exits scheduled for the open, entries at the open, intraday stop or trailing stop, then close-based exits for the next open.
- **Portfolio:** equal-weight slots, marked to market daily. When there are more signals than slots, `rank_by` decides which get them. Positions still open at the end of a window are closed at that day's close.
- **Walk-forward** (`tune`): train 3 years, test the next year, roll forward. The stitched test years are the honest estimate. The `--holdout-start` period is evaluated once at the end.
