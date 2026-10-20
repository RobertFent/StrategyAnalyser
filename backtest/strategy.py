"""Rule-based long-only swing strategy definition.

ENTRY (evaluated at the close of day t, executed at next open by default)
    oscillator(entry_length) < entry_threshold
        entry_mode='cross': and it was >= threshold the day before (first day below)
        entry_mode='level': any day below while flat
    AND Close > SMA(trend_ma)            if trend_ma > 0
    AND SPY Close > SPY SMA(market_ma)   if market_ma > 0
    AND Close >= min_price AND 20d avg dollar volume >= min_dollar_volume
    AND (optional) >= breadth_min of the universe oversold the same day

EXIT (first that triggers)
    stop:   Low <= entry - stop_adr_mult * ADR(14)          -> filled at the stop (or open on a gap)
    trail:  Low <= highest high - trail_adr_mult * ADR(14)  -> filled at the stop (or open on a gap)
    signal: exit_rule 'osc' (oscillator > exit_threshold) or 'prev_high' (close > yesterday's high)
            at close -> next open
    time:   held >= max_hold_days at close                    -> next open

PORTFOLIO
    max_positions equal-weight slots; when more signals than free slots the best
    `rank_by` (oversold | volatility) get them.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, fields, replace
from pathlib import Path

import numpy as np

from backtest.features import FeatureStore

ADR_LENGTH = 14
DOLLAR_VOLUME_LENGTH = 20


@dataclass(frozen=True)
class StrategyParams:
    entry_indicator: str = 'willr'      # rsi | willr | stoch | ibs | mfi | bbp | crsi | uo | macd | cci
    entry_length: int = 4
    entry_threshold: float = 15.0       # 0..100 scale, low = oversold (WILLR -85 == 15)
    entry_mode: str = 'cross'           # cross | level
    exit_rule: str = 'osc'              # osc: oscillator > exit_threshold | prev_high: close > yesterday's high
                                        # | none: only stops / time exit
    exit_indicator: str = ''            # '' = same as entry
    exit_length: int = 0                # 0 = same as entry
    exit_threshold: float = 50.0
    trend_ma: int = 0                   # 0 = off, e.g. 200 -> Close > SMA200
    market_ma: int = 0                  # 0 = off, e.g. 200 -> SPY > SMA200
    stop_adr_mult: float = 0.0          # 0 = no stop
    trail_adr_mult: float = 0.0         # 0 = off; trailing stop = highest high since entry - mult * ADR(14)
    max_hold_days: int = 0              # 0 = no time stop
    min_price: float = 5.0
    min_dollar_volume: float = 5_000_000
    execution: str = 'next_open'        # next_open | close
    breadth_min: float = 0.0            # 0 = off; e.g. 0.10 -> only buy when >= 10% of the universe
                                        # is oversold the same day (broad pullback, not a single-stock dip)
    rank_by: str = 'oversold'           # which signals get the free slots: oversold | volatility
    max_positions: int = 10             # equal-weight slots, each gets equity / max_positions

    @property
    def exit_ind(self) -> str:
        return self.exit_indicator or self.entry_indicator

    @property
    def exit_len(self) -> int:
        return self.exit_length or self.entry_length

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> 'StrategyParams':
        names = {f.name for f in fields(cls)}
        clean = {k: v for k, v in d.items() if k in names and v is not None
                 and not (isinstance(v, float) and np.isnan(v))}
        types = {f.name: f.type for f in fields(cls)}
        for k, v in clean.items():
            t = types[k]
            if t == 'int' or t is int:
                clean[k] = int(v)
            elif t == 'float' or t is float:
                clean[k] = float(v)
            elif t == 'str' or t is str:
                clean[k] = '' if v is None else str(v)
        return cls(**clean)

    @classmethod
    def load(cls, path: str | Path) -> 'StrategyParams':
        data = json.loads(Path(path).read_text())
        return cls.from_dict(data.get('params', data))

    def with_(self, **kw) -> 'StrategyParams':
        return replace(self, **kw)

    def describe(self) -> str:
        """The rules in plain English."""
        name = {'rsi': 'RSI', 'willr': 'Williams %R', 'stoch': 'Stochastic %K', 'ibs': 'IBS (close within the day\'s range)',
                'mfi': 'Money Flow Index', 'bbp': 'Bollinger %B', 'crsi': 'Connors RSI', 'uo': 'Ultimate Oscillator',
                'macd': 'MACD histogram rank', 'cci': 'CCI rank'}

        def lvl(ind: str, v: float) -> str:
            return f'{v - 100:g}' if ind == 'willr' else f'{v:g}'

        def label(ind: str, n: int) -> str:
            if ind in ('ibs', 'uo'):
                return name[ind]
            if ind in ('macd', 'cci', 'crsi'):
                return f'{name[ind]} ({n}-day window)'
            return f'{name[ind]}({n})'

        ind, xind = self.entry_indicator, self.exit_ind
        nxt = 'next day\'s open' if self.execution == 'next_open' else 'same close'
        how = 'drops below' if self.entry_mode == 'cross' else 'is below'
        buy = [f'{label(ind, self.entry_length)} {how} {lvl(ind, self.entry_threshold)}']
        if self.breadth_min:
            buy.append(f'at least {self.breadth_min * 100:g}% of all stocks are that oversold on the same day')
        if self.trend_ma:
            buy.append(f'the stock is above its {self.trend_ma}-day average')
        if self.market_ma:
            buy.append(f'SPY is above its {self.market_ma}-day average')
        buy.append(f'price at least ${self.min_price:g}, average daily trading value at least '
                   f'${self.min_dollar_volume / 1e6:g}M')
        sell = []
        if self.exit_rule == 'osc':
            sell.append(f'{label(xind, self.exit_len)} rises above {lvl(xind, self.exit_threshold)} '
                        f'-> sell at the {nxt}')
        elif self.exit_rule == 'prev_high':
            sell.append(f"the close is above yesterday's high -> sell at the {nxt}")
        if self.stop_adr_mult:
            sell.append(f'stop loss: entry price - {self.stop_adr_mult:g} x average daily range ({ADR_LENGTH} days)')
        if self.trail_adr_mult:
            sell.append(f'trailing stop: highest high since entry - {self.trail_adr_mult:g} x average daily range')
        if self.max_hold_days:
            sell.append(f'after {self.max_hold_days} trading days -> sell at the {nxt}')
        pick = 'the most oversold' if self.rank_by == 'oversold' else 'the most volatile'
        lines = ['BUY when all of these are true at the close:']
        lines += [f'  - {b}' for b in buy]
        lines.append(f'  -> buy at the {nxt}')
        lines.append('SELL at the first of:')
        lines += [f'  - {x}' for x in (sell or ['never (no exit rule set)'])]
        lines.append(f'POSITIONS: up to {self.max_positions} at once, {100 / self.max_positions:g}% of the account each; '
                     f'if there are more signals than free spots, take {pick}')
        return '\n'.join(lines)


def build_signals(fs: FeatureStore, p: StrategyParams) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Returns (entry_signal, exit_signal, rank) arrays aligned with fs rows.
    rank: lower = better candidate when more signals than free slots (most oversold first)."""
    osc = fs.oscillator(p.entry_indicator, p.entry_length)
    below = osc < p.entry_threshold
    if p.entry_mode == 'cross':
        prev = fs.shift(osc)
        entry = below & (prev >= p.entry_threshold)
    elif p.entry_mode == 'level':
        entry = below.copy()
    else:
        raise ValueError(f'unknown entry_mode {p.entry_mode!r}')

    if p.trend_ma:
        entry &= fs.close > fs.get('sma', p.trend_ma)  # NaN compares False -> no trade during warm-up
    if p.market_ma:
        entry &= fs.get('market_ok', p.market_ma)
    if p.min_price:
        entry &= fs.close >= p.min_price
    if p.min_dollar_volume:
        entry &= fs.get('dollar_volume', DOLLAR_VOLUME_LENGTH) >= p.min_dollar_volume
    entry &= ~np.isnan(fs.get('adr', ADR_LENGTH))
    if p.breadth_min:
        entry &= fs.breadth(p.entry_indicator, p.entry_length, p.entry_threshold) >= p.breadth_min

    if p.exit_rule == 'osc':
        exit_ = fs.oscillator(p.exit_ind, p.exit_len) > p.exit_threshold
    elif p.exit_rule == 'prev_high':
        exit_ = fs.close > fs.shift(fs.high)
    elif p.exit_rule == 'none':
        exit_ = np.zeros(len(fs), dtype=bool)
    else:
        raise ValueError(f'unknown exit_rule {p.exit_rule!r}')
    if p.rank_by == 'volatility':
        rank = -(fs.get('adr', ADR_LENGTH) / fs.close)
    elif p.rank_by == 'oversold':
        rank = osc
    else:
        raise ValueError(f'unknown rank_by {p.rank_by!r}')
    return entry, exit_, rank
