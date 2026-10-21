"""SPY bull call spreads: backtest and tune a debit-spread routine without options data.

    python3 -m backtest.spreads --fetch            # SPY (unadjusted) + VIX -> data/options_underlying.csv.gz
    python3 -m backtest.spreads                    # backtest the default setup (below), prints a report
    python3 -m backtest.spreads --offset 0.017 --width 10 --dte 60 --target 0.99 --cadence monthly --trend-ma 200
    python3 -m backtest.spreads --debit 4.95       # scale the model so your setup costs what you really pay
    python3 -m backtest.spreads --tune             # grid over offsets, widths, expiries, targets, stops, filters

How it works
  - No option quotes exist for 14 years, so every spread is priced with Black-Scholes using the VIX of the
    day as implied volatility (times --iv-mult, default 1.0; OTM calls usually trade a bit below VIX).
    The entry debit, the daily mark and the early close all come from that model; the payoff at expiry
    is exact (intrinsic value from the SPY close). SPY is unadjusted so dividends hit the calls like real life.
  - A spread: buy the call at strike round(SPY * (1 + offset)), sell the call `width` dollars higher, expiring
    on the Friday closest to `dte` calendar days ahead. Close when the spread is worth at least
    target * width (e.g. 9.90 on a 10-wide), at a stop (value <= debit * (1 - stop)), or at expiry.
  - Cadence: a new spread on the first trading day of each month / week, or the day after the last one closed;
    only when SPY is above its --trend-ma day average (0 = always).
  - Sizing: --risk of the account is at risk in total (debit * contracts), split over the spreads that overlap
    (a 60-day spread opened monthly = 2 open at once = half of --risk each). Costs: --slip dollars per spread
    per side (bid-ask) and --commission dollars per contract per side.
  - Returns are reported on the whole account (cash sits idle) and per trade on the debit.
"""
from __future__ import annotations

import argparse
import itertools
import math
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np
import pandas as pd

from backtest.data import DATA_DIR, OUTPUT_DIR
from backtest.metrics import compute_metrics, yearly_returns, fmt_pct

UNDERLYING = DATA_DIR / 'options_underlying.csv.gz'


# ----------------------------------------------------------------------------- data
def fetch(start: str = '2010-01-01') -> pd.DataFrame:
    import yfinance as yf
    spy = yf.download('SPY', start=start, auto_adjust=False, progress=False)
    vix = yf.download('^VIX', start=start, auto_adjust=False, progress=False)
    if isinstance(spy.columns, pd.MultiIndex):
        spy.columns = spy.columns.get_level_values(0)
        vix.columns = vix.columns.get_level_values(0)
    df = pd.DataFrame({'Date': spy.index, 'Close': spy['Close'].to_numpy(), 'AdjClose': spy['Adj Close'].to_numpy()})
    df['VIX'] = vix['Close'].reindex(spy.index).ffill().to_numpy()
    df['Date'] = pd.to_datetime(df['Date']).dt.tz_localize(None).dt.normalize()
    DATA_DIR.mkdir(exist_ok=True)
    df.to_csv(UNDERLYING, index=False, compression='gzip')
    return df


def load() -> pd.DataFrame:
    if not UNDERLYING.exists():
        raise FileNotFoundError(f'{UNDERLYING} missing. Run `python3 -m backtest.spreads --fetch` first.')
    df = pd.read_csv(UNDERLYING, parse_dates=['Date']).dropna()
    return df.sort_values('Date').reset_index(drop=True)


# ----------------------------------------------------------------------------- pricing
def _ncdf(x: np.ndarray) -> np.ndarray:
    return 0.5 * (1.0 + np.vectorize(math.erf)(x / math.sqrt(2.0)))


def call_price(s: np.ndarray, k: float, t_years: np.ndarray, iv: np.ndarray, r: float = 0.0) -> np.ndarray:
    """Black-Scholes call; at t=0 returns intrinsic value."""
    s, t, iv = np.asarray(s, float), np.maximum(np.asarray(t_years, float), 0.0), np.maximum(np.asarray(iv, float), 1e-4)
    out = np.maximum(s - k, 0.0)
    live = t > 0
    if live.any():
        st, tt, vt = s[live], t[live], iv[live]
        d1 = (np.log(st / k) + (r + 0.5 * vt ** 2) * tt) / (vt * np.sqrt(tt))
        d2 = d1 - vt * np.sqrt(tt)
        out[live] = st * _ncdf(d1) - k * np.exp(-r * tt) * _ncdf(d2)
    return out


def spread_value(s, k1, k2, t_years, iv, r=0.0):
    return call_price(s, k1, t_years, iv, r) - call_price(s, k2, t_years, iv, r)


# ----------------------------------------------------------------------------- strategy
@dataclass
class SpreadParams:
    offset: float = 0.017      # long strike = SPY * (1 + offset); 0.017 ~ 767 -> 780
    width: float = 10.0        # dollars between the strikes
    dte: int = 60              # calendar days to expiry (nearest Friday)
    target: float = 0.99       # close when the spread is worth target * width (9.90 on a 10-wide)
    stop: float = 0.0          # close when the spread lost this share of the debit (0 = never)
    cadence: str = 'monthly'   # monthly | weekly | next (the day after the last one closed)
    trend_ma: int = 200        # open only when SPY > its N-day average (0 = always)
    risk: float = 0.10         # share of the account at risk across all open spreads (split by how many overlap)
    iv_mult: float = 1.0       # implied vol = VIX/100 * iv_mult
    slip: float = 0.05         # dollars per spread per side
    commission: float = 0.65   # dollars per contract per leg per side
    rate: float = 0.0

    def concurrent(self) -> int:
        """How many spreads are normally open at once (expiry / cadence)."""
        step = {'monthly': 30, 'weekly': 7}.get(self.cadence)
        return max(1, math.ceil(self.dte / step)) if step else 1

    def describe(self) -> str:
        where = ('out of the money' if self.offset > 0 else 'in the money' if self.offset < 0 else 'at the money')
        cad = {'monthly': 'first trading day of each month', 'weekly': 'first trading day of each week',
               'next': 'the day after the previous one closed'}[self.cadence]
        lines = [f'OPEN on {cad}' + (f', only while SPY is above its {self.trend_ma}-day average' if self.trend_ma else '') + ':',
                 f'  buy the SPY call {self.offset * 100:+.1f}% from the price ({where}), sell the call ${self.width:g} higher, '
                 f'expiring in about {self.dte} days',
                 f'CLOSE when the spread is worth {self.target * 100:.0f}% of its width (${self.target * self.width:.2f} on a ${self.width:g}-wide)'
                 + (f', when it has lost {self.stop * 100:.0f}% of the debit' if self.stop else '') + ', or at expiry',
                 f'SIZE: {self.risk * 100:.0f}% of the account at risk in total, about {self.concurrent()} spread(s) open at once '
                 f'({self.risk / self.concurrent() * 100:.1f}% each); ${self.slip:.2f} slippage per side, '
                 f'${self.commission:.2f} commission per contract and leg']
        return '\n'.join(lines)


def _expiry(d: pd.Timestamp, dte: int) -> pd.Timestamp:
    target = d + pd.Timedelta(days=dte)
    shift = (4 - target.weekday()) % 7          # next Friday
    nxt = target + pd.Timedelta(days=shift)
    prv = nxt - pd.Timedelta(days=7)
    return nxt if (nxt - target) <= (target - prv) else prv


def backtest(df: pd.DataFrame, p: SpreadParams, start: str, end: str | None = None, capital: float = 100000.0):
    d = df[(df['Date'] >= start) & ((df['Date'] <= end) if end else True)].reset_index(drop=True)
    full = df.set_index('Date')['Close']
    ma = full.rolling(p.trend_ma, min_periods=p.trend_ma).mean() if p.trend_ma else None
    dates = d['Date']
    if p.cadence == 'monthly':
        sched = dates.dt.to_period('M').ne(dates.dt.to_period('M').shift(1)).fillna(True).to_numpy().astype(bool)
    elif p.cadence == 'weekly':
        wk = dates.dt.isocalendar().week.astype(int)
        sched = wk.ne(wk.shift(1)).fillna(True).to_numpy().astype(bool)
    else:
        sched = np.ones(len(d), bool)
    trend_ok = (full.reindex(dates) > ma.reindex(dates)).fillna(False).to_numpy().astype(bool) if ma is not None else np.ones(len(d), bool)
    close = d['Close'].to_numpy(); iv = d['VIX'].to_numpy() / 100.0 * p.iv_mult
    all_dates = full.index; n_days = len(d)
    # 1) every spread's daily mark until it closes (vectorised per spread)
    legs = []
    i = 0
    while i < n_days - 1:
        if not (sched[i] and trend_ok[i]) or np.isnan(iv[i]):
            i += 1; continue
        day = dates.iloc[i]
        expiry = _expiry(day, p.dte)
        if expiry <= all_dates[-1]:
            expiry = all_dates[all_dates <= expiry][-1]
        j_end = int(np.searchsorted(dates.to_numpy(), np.datetime64(expiry), side='right'))   # exclusive
        j_end = min(max(j_end, i + 2), n_days)
        k1 = float(round(close[i] * (1 + p.offset))); k2 = k1 + p.width
        t_years = np.maximum((expiry - dates.iloc[i:j_end]).dt.days.to_numpy(), 0) / 365.0
        if expiry > all_dates[-1]:
            t_years = np.maximum(t_years, 1 / 365)
        marks = spread_value(close[i:j_end], k1, k2, t_years, iv[i:j_end], p.rate)
        debit = float(marks[0]) + p.slip
        hit_t = np.where(marks[1:] >= p.target * p.width)[0]
        hit_s = np.where(marks[1:] <= debit * (1 - p.stop))[0] if p.stop else np.array([], int)
        j_close = j_end - 1; reason = 'expiry' if expiry <= all_dates[-1] else 'open'
        if len(hit_t) and (i + hit_t[0] + 1 < j_close or reason == 'open'):
            j_close, reason = i + hit_t[0] + 1, 'target'
        if len(hit_s) and i + hit_s[0] + 1 < j_close:
            j_close, reason = i + hit_s[0] + 1, 'stop'
        val = float(marks[j_close - i])
        exit_px = val if reason in ('expiry', 'open') else max(val - p.slip, 0.0)
        legs.append({'i': i, 'j': j_close, 'reason': reason, 'entry': day, 'expiry': expiry, 'k1': k1, 'k2': k2,
                     'debit': debit, 'exit': exit_px, 'marks': marks[: j_close - i + 1]})
        i = j_close + 1 if p.cadence == 'next' else i + 1
    # 2) account: size each spread at entry, mark open ones daily
    concurrent = p.concurrent()
    flow = np.zeros(n_days); trades = []          # cash in/out per day
    open_marks = np.zeros(n_days)                 # dollar value of open spreads per day
    for leg in sorted(legs, key=lambda l: l['i']):
        i, j = leg['i'], leg['j']
        cash_now = capital + flow[:i + 1].sum()   # only flows up to today count
        equity_now = cash_now + open_marks[i]
        n = int(equity_now * p.risk / concurrent // (leg['debit'] * 100)) if leg['debit'] > 0 else 0
        cost = leg['debit'] * 100 * n + p.commission * 2 * n
        if n <= 0 or cost > cash_now:
            continue
        expired_worthless = leg['reason'] == 'expiry' and leg['exit'] == 0
        proceeds = leg['exit'] * 100 * n - (0 if expired_worthless or leg['reason'] == 'open' else p.commission * 2 * n)
        flow[i] -= cost; flow[j] += proceeds
        open_marks[i:j] += leg['marks'][:-1] * 100 * n
        pnl = proceeds - cost
        trades.append({'ticker': 'SPY', 'entry_date': leg['entry'], 'exit_date': dates.iloc[j], 'expiry': leg['expiry'],
                       'spy_entry': close[i], 'k1': leg['k1'], 'k2': leg['k2'], 'contracts': n, 'debit': leg['debit'],
                       'exit': leg['exit'], 'pnl': pnl, 'net_return': pnl / cost, 'bars_held': j - i, 'exit_reason': leg['reason']})
    equity = capital + np.cumsum(flow) + open_marks
    eq = pd.Series(equity, index=pd.DatetimeIndex(dates), name='equity')
    tr = pd.DataFrame(trades)
    if len(tr):
        tr['pnl_1'] = (tr['exit'] - tr['debit']) * 100 - p.commission * 4   # one contract, constant size
    return eq, tr


# ----------------------------------------------------------------------------- reporting
def _spy_lines(df: pd.DataFrame, index: pd.DatetimeIndex) -> dict:
    from backtest.benchmarks import benchmark_metrics
    bench = df[['Date', 'AdjClose']].rename(columns={'AdjClose': 'Close'})
    return benchmark_metrics(bench, index)


def _max_buying_power(tr: pd.DataFrame) -> float:
    """Largest sum of debits (one contract each) open at the same time."""
    ev = []
    for r in tr.itertuples():
        ev.append((r.entry_date, r.debit * 100)); ev.append((r.exit_date, -r.debit * 100))
    cur = best = 0.0
    for _, v in sorted(ev, key=lambda x: (x[0], x[1])):
        cur += v; best = max(best, cur)
    return best


def calibrate_iv(df: pd.DataFrame, p: SpreadParams, start: str, debit: float) -> float:
    """Find iv_mult so that the average entry debit of the setup matches `debit` (what you actually pay)."""
    lo, hi = 0.3, 3.0
    for _ in range(18):
        mid = (lo + hi) / 2
        _, tr = backtest(df, SpreadParams(**{**asdict(p), 'iv_mult': mid}), start)
        if len(tr) == 0 or tr['debit'].mean() < debit:
            lo = mid
        else:
            hi = mid
    return round((lo + hi) / 2, 3)


def report(df: pd.DataFrame, p: SpreadParams, start: str, holdout: str, capital: float = 100000.0) -> tuple[list[str], dict]:
    eq, tr = backtest(df, p, start, None, capital)
    out = {}
    lines = [p.describe(), '']
    periods = [('Full period', start, None), ('Development period', start, holdout), ('Test period', holdout, None)]
    for name, a, b in periods:
        e = eq[(eq.index >= a) & ((eq.index < b) if b else True)]
        t = tr[(tr['exit_date'] >= a) & ((tr['exit_date'] < b) if b else True)] if len(tr) else tr
        if len(e) < 30:
            continue
        m = compute_metrics(e / e.iloc[0] * capital, t)
        spy = _spy_lines(df, e.index)
        out[name] = {'strategy': m, **spy}
        lines += [f'{name} {e.index[0].date()} .. {e.index[-1].date()}',
                  f'  {"":28s} {"return/yr":>10s} {"worst drop":>11s} {"Sharpe":>7s} {"Calmar":>7s} {"trades":>7s} {"win":>5s}']
        for label, mm in [('Call spreads (whole account)', m)] + list(spy.items()):
            lines.append(f'  {label:28s} {fmt_pct(mm["cagr"]):>10s} {fmt_pct(mm["max_drawdown"]):>11s} '
                         f'{mm["sharpe"]:7.2f} {mm["calmar"]:7.2f} {mm["trades"]:7d} {fmt_pct(mm["win_rate"]) if mm["trades"] else "":>5s}')
        if len(t):
            closed = t[t['exit_reason'] != 'open']
            yrs = max((e.index[-1] - e.index[0]).days / 365.25, 1e-9)
            bp = _max_buying_power(t)
            lines.append(f'  one contract per spread, constant size: P&L ${closed["pnl_1"].sum():,.0f} in {yrs:.1f} years '
                         f'on at most ${bp:,.0f} tied up at once = {closed["pnl_1"].sum() / yrs / bp * 100 if bp else 0:+.0f}% per year on that buying power'
                         + (f' ({len(t) - len(closed)} still open)' if len(t) > len(closed) else ''))
            rs = t['exit_reason'].value_counts()
            lines.append(f'  per spread: avg {t["net_return"].mean() * 100:+.1f}% of the debit, '
                         f'avg win {t.loc[t.pnl > 0, "net_return"].mean() * 100 if (t.pnl > 0).any() else 0:+.0f}%, '
                         f'avg loss {t.loc[t.pnl <= 0, "net_return"].mean() * 100 if (t.pnl <= 0).any() else 0:+.0f}%, '
                         f'debit ${t["debit"].mean():.2f} avg, closed at target {rs.get("target", 0)}, '
                         f'expiry {rs.get("expiry", 0)}, stop {rs.get("stop", 0)}; '
                         f'total P&L ${t["pnl"].sum():,.0f} on ${(t["debit"] * 100 * t["contracts"]).mean():,.0f} avg at risk')
        lines.append('')
    lines.append(f'Position size (whole account of ${capital:,.0f}, full period): the same spreads with a different share of the account at risk in total')
    for risk in (0.02, 0.05, 0.10, 0.20):
        e2, t2 = backtest(df, SpreadParams(**{**asdict(p), 'risk': risk}), start, None, capital)
        m2 = compute_metrics(e2 / e2.iloc[0] * capital, t2)
        lines.append(f'  {risk * 100:3.0f}% at risk: {fmt_pct(m2["cagr"]):>8s} per year, worst drop {fmt_pct(m2["max_drawdown"])}, Sharpe {m2["sharpe"]:.2f}')
    lines.append('')
    if len(eq) > 252:
        yr = yearly_returns(eq)
        spy_yr = yearly_returns(df.set_index('Date')['AdjClose'].reindex(eq.index).ffill())
        lines.append('Year by year (account vs SPY): ' + ', '.join(f'{y}: {fmt_pct(v)} / {fmt_pct(spy_yr.get(y, float("nan")))}' for y, v in yr.items()))
        lines.append('')
    if len(tr):
        lines.append('Last trades:')
        show = tr.tail(8)[['entry_date', 'spy_entry', 'k1', 'k2', 'debit', 'exit_date', 'exit', 'net_return', 'exit_reason']].copy()
        show['entry_date'] = show['entry_date'].dt.date; show['exit_date'] = show['exit_date'].dt.date
        show['net_return'] = (show['net_return'] * 100).round(0)
        lines += ['  ' + l for l in show.round(2).to_string(index=False).split('\n')]
    return lines, {'equity': eq, 'trades': tr, 'metrics': out}


GRID = {
    'offset': [-0.01, 0.0, 0.01, 0.017, 0.03],
    'width': [5.0, 10.0, 20.0],
    'dte': [30, 60, 90],
    'target': [0.8, 0.99],
    'stop': [0.0, 0.5],
    'cadence': ['monthly', 'weekly'],
    'trend_ma': [0, 200],
}


def tune(df: pd.DataFrame, base: SpreadParams, start: str, holdout: str, metric: str = 'calmar') -> pd.DataFrame:
    rows = []
    keys = list(GRID)
    combos = list(itertools.product(*GRID.values()))
    for i, vals in enumerate(combos):
        p = SpreadParams(**{**asdict(base), **dict(zip(keys, vals))})
        eq, tr = backtest(df, p, start)
        dev = eq[eq.index < holdout]; hold = eq[eq.index >= holdout]
        m_dev = compute_metrics(dev / dev.iloc[0], tr[tr['exit_date'] < holdout] if len(tr) else tr)
        m_hold = compute_metrics(hold / hold.iloc[0], tr[tr['exit_date'] >= holdout] if len(tr) else tr) if len(hold) > 30 else {}
        rows.append({**dict(zip(keys, vals)), 'dev_cagr': m_dev['cagr'], 'dev_dd': m_dev['max_drawdown'], 'dev_sharpe': m_dev['sharpe'],
                     'dev_calmar': m_dev['calmar'], 'trades': m_dev['trades'], 'win': m_dev['win_rate'],
                     'hold_cagr': m_hold.get('cagr', np.nan), 'hold_dd': m_hold.get('max_drawdown', np.nan)})
        if (i + 1) % 100 == 0:
            print(f'  {i + 1}/{len(combos)}', flush=True)
    res = pd.DataFrame(rows)
    res = res[res['trades'] >= 20].sort_values('dev_' + metric, ascending=False)
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--tune', action='store_true')
    ap.add_argument('--metric', default='calmar', choices=['calmar', 'sharpe', 'cagr'])
    ap.add_argument('--start', default='2016-01-01')
    ap.add_argument('--holdout-start', default='2025-01-01')
    ap.add_argument('--capital', type=float, default=100000, help='account size; contracts are whole, so small accounts cannot size small risks')
    ap.add_argument('--debit', type=float, default=0.0,
                    help='what you actually pay for this setup, e.g. 4.95: scales the implied vol so the model matches it')
    for f, v in asdict(SpreadParams()).items():
        ap.add_argument('--' + f.replace('_', '-'), type=type(v), default=v)
    a = ap.parse_args()
    if a.fetch:
        df = fetch(); print(f'Saved {UNDERLYING}: {df.Date.iloc[0].date()} .. {df.Date.iloc[-1].date()}, {len(df)} days'); return
    df = load()
    p = SpreadParams(**{f: getattr(a, f) for f in asdict(SpreadParams())})
    if a.debit:
        p.iv_mult = calibrate_iv(df, p, a.start, a.debit)
        print(f'Calibrated: implied vol = VIX x {p.iv_mult} gives an average debit of ${a.debit:.2f} for this setup')
    out_dir = OUTPUT_DIR / f'spreads_{datetime.now():%Y%m%d_%H%M%S}'
    out_dir.mkdir(parents=True, exist_ok=True)
    if a.tune:
        print(f'Tuning {int(np.prod([len(v) for v in GRID.values()]))} setups on {a.start}..{a.holdout_start}, ranked by {a.metric} (development period)')
        res = tune(df, p, a.start, a.holdout_start, a.metric)
        res.to_csv(out_dir / 'leaderboard.csv', index=False)
        lines = ['SPY CALL SPREADS - TUNING', f'Development {a.start}..{a.holdout_start}, test period {a.holdout_start}..today. '
                 'Development numbers are in-sample (the best of many); trust the test period and the spread of results more than the top row.', '',
                 'Top 15 by development ' + a.metric + ':']
        show = res.head(15).copy()
        for c in ('dev_cagr', 'dev_dd', 'win', 'hold_cagr', 'hold_dd'):
            show[c] = (show[c] * 100).round(1)
        lines += ['  ' + l for l in show.round(2).to_string(index=False).split('\n')]
        yours = res[(res.offset == 0.017) & (res.width == 10) & (res.dte == 60) & (res.target == 0.99) & (res.stop == 0) & (res.cadence == 'monthly') & (res.trend_ma == 200)]
        if len(yours):
            r = yours.iloc[0]; rank = int((res['dev_' + a.metric] > r['dev_' + a.metric]).sum()) + 1
            lines += ['', f'Your setup (OTM +1.7%, $10 wide, 60 days, close at 99%, monthly, SPY > 200 MA): rank {rank} of {len(res)}, '
                          f'development {r.dev_cagr * 100:.1f}%/yr, test period {r.hold_cagr * 100:.1f}%/yr']
        lines += ['', 'Share of setups that made money in the test period: '
                  f'{(res.hold_cagr > 0).mean() * 100:.0f}%; median test-period return {res.hold_cagr.median() * 100:.1f}%/yr']
        spy = _spy_lines(df, df[df.Date >= a.holdout_start].set_index('Date').index)
        lines.append(f'SPY buy & hold in the test period: {spy["SPY buy & hold"]["cagr"] * 100:.1f}%/yr')
    else:
        lines, res = report(df, p, a.start, a.holdout_start, a.capital)
        res['trades'].to_csv(out_dir / 'trades.csv', index=False)
        res['equity'].to_csv(out_dir / 'equity.csv')
        lines = ['SPY CALL SPREADS - BACKTEST (Black-Scholes marks with VIX as implied vol; payoff at expiry exact)', ''] + lines
    text = '\n'.join(lines)
    (out_dir / 'report.txt').write_text(text)
    print(text); print(f'\nSaved to {out_dir}')


if __name__ == '__main__':
    main()
