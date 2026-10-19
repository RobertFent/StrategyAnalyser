# StrategyAnalyser

Research for rule-based, long-only swing strategies on US index stocks (S&P 500, Nasdaq-100, S&P 100):
backtest, tune with walk-forward validation, stress-test, and print daily signals.

Self-contained: everything needed (symbol lists, data download, research tools) is in this repo.

```
backtest/              research package (python3 -m backtest.<command>)
strategies/            chosen rule sets as JSON (current.json = the one to trade)
symbols/               index constituents (refresh with python3 -m backtest.symbols)
docs/                  research log and findings
tests/                 engine sanity tests (no network)
data/, output/         downloaded history / run results (git-ignored)
```

## Setup
```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 -m backtest.fetch          # first run: ~14 years of daily data into data/
```

When index members change: `python3 -m backtest.symbols` (Wikipedia), then `python3 -m backtest.fetch`.

## Workflow
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

Current findings and open ideas: [docs/strategy-research.md](docs/strategy-research.md).

---

## Status – 19 October 2026

### Where the repo stands
- The `backtest/` package can download data, tune, stress-test with a pass/fail verdict, compare against SPY and SPY timing, backtest and print daily signals.
- Saved rule sets:
  - `strategies/current.json`: the reference rule set.
  - `strategies/candidate_breadth.json`: broad-pullback variant.
  - `strategies/coach_plan.json`: template for testing a trading plan.

### Conclusion in one paragraph
Several thousand rule sets were tested on the S&P 500 (2016–2024), with 10 different oscillators, trend and market filters, stops and exits. The honest tests were walk-forward 2019–2024 and an untouched 2025–2026 holdout. **No rule set is clearly better than holding SPY.** The best ones match SPY's return per unit of risk and roughly halve the drawdown, but earn less. In 2025–26 they also lost to the simple rule "hold SPY only above its 200-day average". The oversold signal on its own has no edge: random entries in the same stocks earn the same on average. The 200-day trend filter does most of the work.

| 2025 – Oct 2026 (never used for tuning) | CAGR | Max drawdown |
|---|---|---|
| SPY buy & hold | 17.4% | −18.8% |
| SPY timing (>200-day average) | 11.2% | −10.2% |
| current.json (Williams %R(10) dip-buying, trend + market filter) | 7.3% | −12.8% |
| Best of the new indicators (CCI) | −3.5% | −23.7% |

### Next steps
1. Test the trading plan as a fixed hypothesis via `strategies/coach_plan.json` and the analyze verdict.
2. Paper-trade for 3–6 months and compare with the backtest each month.
3. Fix survivorship bias with historical index membership before trusting any result.

Full results, verdict table and reasoning: [docs/strategy-research.md](docs/strategy-research.md)
