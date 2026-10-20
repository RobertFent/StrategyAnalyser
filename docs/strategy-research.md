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
| Filters forced → `strategies/willr.json` | 12.4% / −21.5% / 0.92 | 7.3% / −12.8% |
| Broad pullbacks → `strategies/candidate_breadth.json` | 6.2% / −39.3% / 0.42 | 18.3% / −16.8% * |
| Exits | 19.8% / −12.9% / 1.22 ** | −5.4% / −26.3% |
| More indicators (best: CCI) | 6.6% / −26.3% / 0.52 | −3.5% / −23.7% |
| Momentum family, point-in-time members (20 Oct) | 7.6% / −29.2% / 0.42 | +22.0% / −30.5% * |

All rows except the last use today's index members (survivorship bias, see the update below); the reference
set drops to 7.6% / yr over 2016–2026 with point-in-time members.

\* Its walk-forward result is the worst of all, so the good holdout is most likely luck.
\*\* This space was narrowed using earlier 2016–2024 results, so its walk-forward number is too optimistic. The holdout shows it.

**Verdict against the pass/fail criteria** (`backtest/criteria.py`, set before the final check):

| Criterion | willr.json | candidate_breadth | best CCI |
|---|---|---|---|
| Makes money in the test period | PASS | PASS | FAIL |
| Test period: at least 70% of SPY's return | FAIL (7.3% vs 17.4%) | PASS | FAIL |
| Clearly smoother ride than SPY (Sharpe +0.2, 2016–now) | PASS (1.13 vs 0.88) | FAIL (1.01) | FAIL |
| Test period: beats simple SPY timing | FAIL (Sharpe 0.54 vs 0.99) | FAIL (Calmar 1.09 vs 1.10) | FAIL |
| Still works with double trading costs | PASS (just) | PASS | FAIL |
| Smaller worst drop than SPY | PASS | PASS | PASS |
| **Result** | **4/6 – do not adopt** | **4/6 – do not adopt** | **1/6 – do not adopt** |

## Update 20 October 2026: survivorship bias fixed, momentum tested, luck check added

### 1. Survivorship bias is now (mostly) fixed
The backtest knows who was in the S&P 500 on every day since 1996 (`symbols/sp500_membership.csv`, built by
`python3 -m backtest.membership` from a public daily membership history) and only buys a stock while it was
a member. Effect on the reference rule set, 2016 – Oct 2026, same rules, same data:

| | Today's members (old) | Point-in-time members (new) |
|---|---|---|
| Return / year | 16.4% | **7.6%** |
| Worst drop | −18.1% | −27.4% |
| Sharpe | 1.15 | 0.60 |
| Luck check (edge over SPY real?) | 55% | 5% |
| Verdict | 4 of 6 | **2 of 7 – do not adopt** |

Half of the "edge" was buying dips in stocks that we only knew in hindsight would make it into the index.
`python3 -m backtest.fetch --historical` added prices for 115 of the 270 companies that left the index since
2016; 88.4% of all member-days now have prices. The remaining gap is mostly companies that were taken over or
renamed (Yahoo serves the history under the new ticker only). Remaining bias: small, and in the strategy's favour.

### 2. Momentum / trend following does not beat SPY here either
New strategy family: buy the strongest stocks (top N by 3–12-month performance, rebalanced weekly or monthly,
with rank / moving-average / trailing-stop exits) and breakouts (new 50–252-day high). 400 rule sets, same
walk-forward, point-in-time membership:

| 2019–2024 walk-forward | CAGR | Worst drop | Sharpe |
|---|---|---|---|
| Momentum family (rules re-picked each year) | 7.6% | −29.2% | 0.42 |
| SPY buy & hold | 17.1% | −33.7% | 0.90 |
| SPY timing | 12.2% | −20.7% | 0.97 |

The best in-sample set (top 30 by 3-month performance, weekly, exit below the 50-day average: 12% / yr on
2016–2024) made +22% / yr in the 2025–26 holdout with a −31% drop, but its excess over SPY across 2016–2026 is
−0.4% / yr and the deflated luck check is 0%: the holdout is one good year of a rule that failed its walk-forward. With today's members instead of point-in-time ones the
same family showed 36% / yr out-of-sample: momentum is the family that survivorship bias flatters most.
Concentrated momentum in large caps had two bad reversal years (2022, 2024) and 10–20 trades a year is too
few to be stable.

### 3. "Could this be luck?" is now part of the verdict
Every report checks whether the edge over SPY is distinguishable from chance:
- a block bootstrap of the daily difference to SPY gives the probability that the yearly excess return is really positive;
- a deflated Sharpe ratio raises the bar for the number of variants tried before the chosen one (`--trials`, and
  automatically in `tune`): a lucky best-of-400 looks like Sharpe 0.9 by itself.
- `analyze` also runs a random-entry test: the same trades with random entry days under the same filters.

Results: reference set 5% (excess −7.3% / yr), best momentum set 0% after 400 variants. Nothing tested so far
clears the 90% bar.

### 4. Corrected finding on the oversold signal
Earlier we wrote that an oversold entry earns the same as a random entry. Conditioning on the filters, the
picture is: days that pass the trend filter (stock and SPY above their 200-day average) are calm days with
*below*-average 5-day returns (0.27% vs 0.35% for all days); oversold signals on those days return 0.46%.
So the indicator does add about +0.2% per trade *given* the filter, and the filter gives it back. Net ≈ SPY,
and after survivorship bias, below SPY.

### 5. Comparison page and the RSI(4) rule book (20 Oct, evening)
`python3 -m backtest.compare` puts several rule sets and SPY on one page. First run on the current data
(2016 – Oct 2026, 5 bps per side; RSI(4) variants on S&P 100 + Nasdaq-100 with today's members):

| | Return / yr | Worst drop | Sharpe | Test period return / yr | Verdict | Not luck |
|---|---|---|---|---|---|---|
| SPY buy & hold | 15.1% | −33.7% | 0.88 | 17.6% | – | – |
| SPY timing | 11.4% | −20.7% | 0.97 | 11.4% | – | – |
| Williams %R dip-buying (`willr.json`) | 7.6% | −27.4% | 0.60 | 8.0% | 2 / 7 | 5% |
| Momentum, best of 400 (`best_strategy.json`) | 18.5% | −28.6% | 0.81 | 26.4% | 3 / 7 | 1% |
| RSI(4) classic rule book (`rsi4_classic.json`) | 4.4% | −14.9% | 0.46 | 4.7% | 2 / 7 | 1% |
| RSI(4) + OBE 2% entries | 1.6% | −8.7% | 0.40 | 0.4% | 2 / 7 | 0% |
| RSI(4) + 5% adds | 7.1% | −16.3% | 0.62 | 9.9% | 2 / 7 | 3% |
| RSI(4) + OBE + 5% adds | 1.8% | −12.8% | 0.34 | 0.5% | 2 / 7 | 0% |

Notes:
- The RSI(4) rule book (S&P 100 / Nasdaq-100, $5–$250, above the 200-day average, RSI(4) below 15, max 3 new
  trades a day, 10 positions, prioritised by each symbol's past ROI, stop loss = entry − 4 × ADR(20)) is implemented
  as written, **but the profit exit was not in the excerpt**. The files use a placeholder (sell when RSI(4) closes
  back above 55). Replace it with the real rule before reading anything into these numbers.
- OBE entries (only buy if the open is 2%+ below the signal close) cut the trades from ~1,600 to ~145 and the
  return with them; 5% adds raise the return (7.1% vs 4.4%) with the 4 × ADR stop capping the damage of averaging down.
- The momentum set's 18.5% / yr includes its own tuning period; its honest number is the 7.6% / yr walk-forward above.
- The daily returns of the dip-buying and momentum rules correlate only ~0.5, so mixing them would smooth the ride,
  but none of them earns more than SPY.

### 6. The momentum plan in practice (21 Oct)
`best_strategy.json` is the best of 400 momentum / breakout rule sets. The rules:

- **Buy:** on the first trading day of each month, every S&P 500 stock that newly entered the top 30 by 6-month
  performance (price ≥ $5, ≥ $5M traded per day). Buy at the next open, 10% of the account each, max 10 positions;
  with more signals than free slots, take the strongest.
- **Sell:** when the close is below the 200-day average, at the next open. No stop loss, no target.
- In practice: one look per month, ~15 trades a year, median hold about 6 months, 46% of trades win; the few big
  winners (STX +363%, AMD +204%, FIX +45% in 2025–26) pay for many −20…−30% losers (HOOD, LUV, DOW, SMCI).

| | Return / yr | Worst drop | Not luck |
|---|---|---|---|
| 2016 – Oct 2026 incl. the years the rules were picked on | 18.5% | −28.6% | 1% |
| Walk-forward 2019–24 (rules re-picked each year, traded the next) | 6.8% | −38% | – |
| Test period 2025 – today (never used to pick rules) | −4.6% | −21.8% | – |
| SPY buy & hold, same periods | 15.1% / 17.1% / 17.6% | −33.7% | – |

Verdict 3 / 7. The 18.5% is the number that made it "best", and it is the one not to trust: it was selected on
that data. Every honest view (walk-forward, test period, luck check) is below SPY. Fit for paper trading as an
exercise in following rules, not for real money yet.

## What we learned
1. **The 200-day trend filter does most of the work.** Without it, returns halve and drawdowns double. Holding only SPY above its 200-day average gets a similar Sharpe (0.97) with no stock picking at all.
2. **An oversold reading has no edge on its own.** Trades entered on an oversold signal average +0.49%. Random entries in the same stock, year and holding time average +0.47%. The signal raises the win rate (69% vs 55%) but the losses get bigger, so the average stays the same.
3. **The indicator hardly matters.** All 10 oscillators reach similar in-sample results (13–18% per year, Sharpe about 1.0), because they all measure the same short pullback. The walk-forward picked a different indicator almost every year.
4. **The more we searched, the better the in-sample results and the worse the honest ones.** Best in-sample results of 15–22% per year shrink to 6–12% in walk-forward. The holdout was negative for most winners.
5. **What does show some edge:** buying on broad market pullbacks (many stocks oversold at once), more volatile stocks, and sizing slots toward the most oversold names. All of it is too weak and unstable to trade on its own.
6. **Costs and universe matter.** At 0.20% cost per side, 18% per year becomes 7%. On the Nasdaq-100 and S&P 100 the same rules make 5–7%.
7. **Results are optimistic.** Using today's index members leaves out stocks that fell out of the index (survivorship bias). This favours dip-buying.

## Conclusion
- **No rule set found here is clearly better than SPY, and with survivorship bias removed the best ones are clearly worse.** The best ones roughly match SPY's return per unit of risk (Sharpe) and cut the drawdown by about half. They earn less in total, and in 2025–26 they also lost to the simple "SPY above its 200-day average" rule.
- **A pure "buy the oversold dip" strategy on S&P 500 stocks has no robust edge in 2016–2026.** Its value is lower drawdown, and that comes from the trend filter.
- **Searching more parameters or indicators won't change this.** It only produces more lucky in-sample winners.

## Next steps
1. **Test the coach's trading plan as a fixed hypothesis.** Run `python3 -m backtest.plan`, answer the questions
   before looking at any result, then run `python3 -m backtest.report --params strategies/<plan>.json` once.
   The verdict decides. Don't tweak afterwards. To compare variants, decide all of them up front and report every one.
2. **Paper trade for 3–6 months** whatever passes, and `willr.json` for comparison. How to do it is in [GUIDE.md](GUIDE.md), section 5.
3. **If smaller drops are the goal**, compare honestly with SPY timing. It is simpler, cheaper and shows similar risk-adjusted results.
4. **Open ideas** (only as fixed hypotheses, not new searches):
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
python3 -m backtest.tune --space momentum   --start 2016-01-01 --holdout-start 2025-01-01 --metric calmar --n-iter 400 --min-trades 20
python3 -m backtest.analyze --params strategies/willr.json            # add --quick for verdict only
python3 -m backtest.report  --params strategies/willr.json            # one-page HTML report
```
Random search uses `--seed 42`. Numbers can move slightly when the data is re-downloaded, because adjusted prices and index members change.
