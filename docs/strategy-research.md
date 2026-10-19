# Strategy research: findings and conclusion

*Status: 19 October 2026*

## Question
Is there an indicator-based, long-only swing strategy with clear entry and exit rules on
S&P 500 stocks that is clearly better than simply holding SPY?

## Setup
- **Universe:** S&P 500 (today's members, about 495 stocks), daily bars, adjusted for splits and dividends.
- **Periods:**
  - 2016–2024 for tuning.
  - **2025 to 16 Oct 2026 as holdout**: never used for tuning, looked at once.
- **Execution:** the signal comes at the close, the fill is at the next open. Stops fill at the stop price (or at the open on a gap). 0.05% cost per side.
- **Sizing:** up to 10 equal-weight positions. If there are more signals than free slots, the most oversold get the slots.
- **Honest test:** walk-forward. For each year from 2019 to 2024, pick the best rules on the 3 years before and trade them unchanged in that year. Then chain those years together ("stitched out-of-sample").
- **Benchmarks:**
  - SPY buy & hold.
  - **SPY timing**: hold SPY only while it is above its 200-day average, otherwise cash. This shows how much comes from the trend filter alone.

## What was tested
Several thousand rule sets in total. Each is listed with the command that reproduces it.

| Run | What varied | Command |
|---|---|---|
| Free search | RSI, Williams %R, Stochastic, IBS (lengths 2–14, thresholds), trend/market filter, stop, time stop | `python3 -m backtest.tune --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 600` |
| Filters forced | same, but stock above 100/200-day average and SPY filter always on | `... --only market_ma=200 trend_ma=100,200` |
| Broad pullbacks | only buy when 5–30% of the S&P 500 is oversold the same day, 3/5/10 positions | `... --space breadth --n-iter 500` |
| Exits | trailing stops, close above yesterday's high, time stop only | `... --space exits --n-iter 600` |
| More indicators | MFI, Bollinger %B, Connors RSI, Ultimate Oscillator, MACD, CCI | `... --space indicators --n-iter 800` |

## Results

| | 2019–2024 walk-forward (CAGR / max DD / Sharpe) | 2025–Oct 2026 holdout (CAGR / max DD) |
|---|---|---|
| **SPY buy & hold** | 17.1% / −33.7% / 0.90 | 17.4% / −18.8% |
| **SPY timing (>200-day avg)** | 12.2% / −20.7% / 0.97 | 11.2% / −10.2% |
| Free search | 10.9% / −17.1% / 0.78 | −2.1% / – |
| Filters forced → `strategies/current.json` | 12.4% / −21.5% / 0.92 | 7.3% / −12.8% |
| Broad pullbacks → `strategies/candidate_breadth.json` | 6.2% / −39.3% / 0.42 | 18.3% / −16.8% * |
| Exits | 19.8% / −12.9% / 1.22 ** | −5.4% / −26.3% |
| More indicators (best: CCI) | 6.6% / −26.3% / 0.52 | −3.5% / −23.7% |

\* Its walk-forward result is the worst of all, so the good holdout is most likely luck.
\*\* This space was narrowed using earlier 2016–2024 results, so its walk-forward number is too optimistic. The holdout shows it.

**Verdict against the pass/fail criteria** (`backtest/criteria.py`, set before the final check):

| Criterion | current.json | candidate_breadth | best CCI |
|---|---|---|---|
| Holdout makes money | PASS | PASS | FAIL |
| Holdout ≥ 70% of SPY | FAIL (7.3% vs 17.4%) | PASS | FAIL |
| Sharpe ≥ SPY + 0.2 (2016–now) | PASS (1.13 vs 0.88) | FAIL (1.01) | FAIL |
| Holdout beats SPY timing | FAIL (Sharpe 0.54 vs 0.99) | FAIL (Calmar 1.09 vs 1.10) | FAIL |
| Survives 0.10% costs | PASS (just) | PASS | FAIL |
| Smaller drawdown than SPY | PASS | PASS | PASS |
| **Result** | **4/6 – do not adopt** | **4/6 – do not adopt** | **1/6 – do not adopt** |

## What we learned
1. **The 200-day trend filter does most of the work.** Without it, returns halve and drawdowns double. Holding only SPY above its 200-day average gets a similar Sharpe (0.97) with no stock picking at all.
2. **An oversold reading has no edge on its own.** Trades entered on an oversold signal average +0.49%. Random entries in the same stock, year and holding time average +0.47%. The signal raises the win rate (69% vs 55%) but the losses get bigger, so the average stays the same.
3. **The indicator hardly matters.** All 10 oscillators reach similar in-sample results (13–18% per year, Sharpe about 1.0), because they all measure the same short pullback. The walk-forward picked a different indicator almost every year.
4. **The more we searched, the better the in-sample results and the worse the honest ones.** Best in-sample results of 15–22% per year shrink to 6–12% in walk-forward. The holdout was negative for most winners.
5. **What does show some edge:** buying on broad market pullbacks (many stocks oversold at once), more volatile stocks, and sizing slots toward the most oversold names. All of it is too weak and unstable to trade on its own.
6. **Costs and universe matter.** At 0.20% cost per side, 18% per year becomes 7%. On the Nasdaq-100 and S&P 100 the same rules make 5–7%.
7. **Results are optimistic.** Using today's index members leaves out stocks that fell out of the index (survivorship bias). This favours dip-buying.

## Conclusion
- **No rule set found here is clearly better than SPY.** The best ones roughly match SPY's return per unit of risk (Sharpe) and cut the drawdown by about half. They earn less in total, and in 2025–26 they also lost to the simple "SPY above its 200-day average" rule.
- **A pure "buy the oversold dip" strategy on S&P 500 stocks has no robust edge in 2016–2026.** Its value is lower drawdown, and that comes from the trend filter.
- **Searching more parameters or indicators won't change this.** It only produces more lucky in-sample winners.

## Next steps
1. **Test the trading plan as a fixed hypothesis.** Write its rules into `strategies/coach_plan.json` before looking at any result, then run
   `python3 -m backtest.analyze --params strategies/coach_plan.json` once. The VERDICT section decides. Do not tune afterwards.
2. **Forward test (paper trade) for 3–6 months.** Do this for `current.json` and, if it passes, the coach plan:
   - Daily: `python3 -m backtest.fetch --update && python3 -m backtest.signals --params strategies/current.json`.
   - Monthly: `python3 -m backtest.run --params strategies/current.json --start 2026-10-20` shows exactly what the rules did since today, compared with SPY and SPY timing.
3. **If the drawdown reduction is the goal**, compare honestly with SPY timing. It is simpler, cheaper and shows similar risk-adjusted results.
4. **Before trusting any result**, fix survivorship bias with historical index membership.
5. **Open ideas** (only as fixed hypotheses, not new searches):
   - a cap on positions per sector
   - larger positions on broad-pullback days
   - position size based on volatility

## Reproduce
```sh
python3 -m backtest.fetch
python3 -m backtest.tune --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 600
python3 -m backtest.tune --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 600 --only market_ma=200 trend_ma=100,200
python3 -m backtest.tune --space breadth    --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 500
python3 -m backtest.tune --space exits      --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 600
python3 -m backtest.tune --space indicators --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 800
python3 -m backtest.analyze --params strategies/current.json            # add --quick for verdict only
```
Random search uses `--seed 42`. Numbers can move slightly when the data is re-downloaded, because adjusted prices and index members change.
