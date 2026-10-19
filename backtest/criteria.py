"""Pass/fail criteria for adopting a rule set - decided BEFORE looking at results.

Used by `python3 -m backtest.analyze` (section VERDICT). Edit the thresholds here,
not after seeing a result. Meant for a rule set chosen in advance (e.g. your trading
plan or strategies/current.json); for a freshly tuned set the tuning period is in-sample,
so judge it by the walk-forward result of `backtest.tune` first.
"""

HOLDOUT_MIN_CAGR = 0.0              # holdout must make money
HOLDOUT_MIN_SHARE_OF_SPY = 0.7      # ... and at least 70% of SPY's holdout CAGR
SHARPE_MARGIN_OVER_SPY = 0.2        # full-period Sharpe >= SPY buy & hold Sharpe + 0.2
STRESS_COST_BPS = 10                # at this cost per side Sharpe must still be >= SPY's


def evaluate(full: dict, holdout: dict, stressed: dict,
             spy_full: dict, spy_holdout: dict, timing_holdout: dict) -> list[tuple[str, bool, str]]:
    """Returns (criterion, passed, detail) rows."""
    pct = lambda x: f'{x * 100:.1f}%'
    return [
        ('Holdout makes money', holdout['cagr'] > HOLDOUT_MIN_CAGR,
         f'holdout CAGR {pct(holdout["cagr"])}'),
        (f'Holdout >= {HOLDOUT_MIN_SHARE_OF_SPY:.0%} of SPY', holdout['cagr'] >= HOLDOUT_MIN_SHARE_OF_SPY * spy_holdout['cagr'],
         f'{pct(holdout["cagr"])} vs SPY {pct(spy_holdout["cagr"])}'),
        (f'Sharpe >= SPY + {SHARPE_MARGIN_OVER_SPY}', full['sharpe'] >= spy_full['sharpe'] + SHARPE_MARGIN_OVER_SPY,
         f'{full["sharpe"]:.2f} vs SPY {spy_full["sharpe"]:.2f}'),
        ('Holdout beats SPY timing (Sharpe+Calmar)',
         holdout['sharpe'] > timing_holdout['sharpe'] and holdout['calmar'] > timing_holdout['calmar'],
         f'Sharpe {holdout["sharpe"]:.2f} vs {timing_holdout["sharpe"]:.2f}, '
         f'Calmar {holdout["calmar"]:.2f} vs {timing_holdout["calmar"]:.2f}'),
        (f'Survives {STRESS_COST_BPS} bps costs', stressed['sharpe'] >= spy_full['sharpe'],
         f'Sharpe at {STRESS_COST_BPS} bps {stressed["sharpe"]:.2f} vs SPY {spy_full["sharpe"]:.2f}'),
        ('Smaller drawdown than SPY', full['max_drawdown'] > spy_full['max_drawdown'],
         f'{pct(full["max_drawdown"])} vs SPY {pct(spy_full["max_drawdown"])}'),
    ]


def format_verdict(rows: list[tuple[str, bool, str]]) -> list[str]:
    lines = [f'  [{"PASS" if ok else "FAIL"}] {name:<36} {detail}' for name, ok, detail in rows]
    passed = sum(ok for _, ok, _ in rows)
    lines.append(f'  => {passed}/{len(rows)} passed: '
                 + ('ADOPT (then paper-trade first)' if passed == len(rows) else 'DO NOT ADOPT'))
    return lines
