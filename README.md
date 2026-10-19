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
| 3. Analyze | `python3 -m backtest.analyze --params output/tuning_<ts>/best_params.json` | changes one parameter at a time, cost sensitivity, ranked vs random slot choice, signal vs random entry, regimes, other indices |
| 4. Backtest | `python3 -m backtest.run --params strategies/current.json --start 2016-01-01` | full report, trades.csv and equity.csv vs SPY |
| 5. Adopt | copy a `best_params.json` to `strategies/current.json` | only if it passes the checks below |
| 6. Trade | `python3 -m backtest.fetch --update && python3 -m backtest.signals --holding AAPL ...` | entry candidates for the next open and exit signals for your holdings |
| Tests | `python3 tests/test_backtest.py` | engine sanity checks |

**Search spaces** live in `backtest/search_space.py`: `default` (all oscillators), `indicators` (only MFI, Bollinger %B, Connors RSI, Ultimate Oscillator, MACD and CCI), `breadth` (only buy when many stocks are oversold at once, with fewer slots) and `exits` (trailing stops, close-above-yesterday's-high exit). Narrow or extend any space with `--only key=v1,v2`, e.g. `--only entry_indicator=willr max_positions=5`.

**Rules** are `StrategyParams` in `backtest/strategy.py`; `describe()` prints them in plain English. Entry oscillators: RSI, Williams %R, Stochastic, IBS, MFI, Bollinger %B, Connors RSI, Ultimate Oscillator, MACD histogram and CCI. MACD and CCI are converted to a percent rank over the last `entry_length` days so they fit the same scale. Formulas are in `backtest/features.py`. Oscillators use a 0..100 scale where low = oversold, so Williams %R −90 is `entry_threshold=10`.

**Execution model:** the signal is taken at the close and filled at the next open. Stops fill at the stop price, or at the open if the price gaps below it. Costs are 5 bps per side. Positions are equal-weight slots.

### Before adopting a rule set
- Walk-forward "Stitched OOS" Sharpe and drawdown are at least as good as SPY's. This is the honest number, not the in-sample top score.
- The holdout result is positive. Look at it once and don't re-tune afterwards.
- In `analyze`, neighboring parameter values perform similarly (a plateau, not a spike), and results survive 10 bps costs.
- Caveat: `symbols/` holds today's index members, so stocks that dropped out are missing (survivorship bias). Expect live results to be lower.

Current findings and open ideas: [docs/strategy-research.md](docs/strategy-research.md).

---

## Status – 19 October 2026

### Where the repo stands
- The `backtest/` package can download data, tune, stress-test, backtest and print daily signals.
- The current rule set is saved in `strategies/current.json`. A second rule set to paper-trade is in `strategies/candidate_breadth.json`.

### Test setup
- **Universe:** S&P 500, using today's members.
- **Period:** daily bars; rules tuned on 2016–2024, then checked once on 2025 to Oct 2026 (never used for tuning).
- **Trade assumptions:** long only, buy at the next open after a signal, 0.05% cost per side, up to 10 equal-sized positions.

### Current rule set
| | Rule |
|---|---|
| Entry | Williams %R(10) closes below −90, stock above its 200-day average, SPY above its 200-day average; buy next open |
| Exit | Williams %R(10) closes above −60 → sell next open, **or** stop loss at entry − 4 × ADR(14), **or** after 20 trading days |
| Sizing | up to 10 positions, 10% of equity each; if more signals than free slots, take the most oversold |

| Result | Strategy | SPY buy & hold |
|---|---|---|
| 2016–2024 (tuning period) | 18.2% / yr, max drawdown −18%, win rate 67%, ~5 days per trade | 14.6% / yr, −34% |
| 2019–2024, rules re-picked each year from the prior 3 years (realistic estimate) | 12.4% / yr, −21% | 17.1% / yr, −34% |
| 2025 – Oct 2026 (unseen) | 8.0% / yr, −13% | 17.4% / yr, −19% |

### Findings
1. **The trend filter matters most.** Only buying stocks above their 200-day average halves the drawdown and doubles the return.
2. **An oversold reading alone gives no edge.** On average, entries on oversold signals earn the same as random entries in the same stocks. The signal raises the win rate but makes the losers bigger.
3. **The edge shows up when the whole market pulls back.** Days with many stocks oversold at once, and volatile stocks, did best.
4. **More trades on broad pullbacks only, with fewer positions, did not hold up.** Good on 2025–26, but unstable when re-tuned each year. This is the paper-trade candidate.
5. **Other exits did not help.** Tight trailing stops and "sell when the close is above yesterday's high" were worse.
6. **Costs and universe matter.** At 0.20% cost per side the yearly return drops from 18% to 7%. On the Nasdaq-100 and S&P 100 the same rules make only 5–7% per year.
7. **The edge is getting weaker.** It has faded since 2022, and in 2025–26 the strategy beats SPY on drawdown but not on return.

### Next steps
- Paper-trade both rule sets with `python3 -m backtest.signals` and compare to the backtest monthly.
- Limit positions per sector (signals often cluster in one sector).
- Use larger positions on broad pullback days.
- Use historical index members to remove survivorship bias.
- Size positions by volatility instead of equal weight.

Details: [docs/strategy-research.md](docs/strategy-research.md)
