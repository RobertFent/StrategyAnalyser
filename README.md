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
python3 -m backtest.report          # opens the report for the reference rule set
python3 -m backtest.plan            # write down your own plan by answering questions
python3 -m backtest                 # list of all commands
```

## Main finding (status October 2026)
Several thousand rule sets were tested: 10 indicators, trend and market filters, stops and exits. They were checked on 2019–2024
year by year and on a 2025–2026 period never used to choose them. The result:

**No rule set clearly beats holding SPY.** The best ones match SPY's return per unit of risk and roughly halve the worst drop,
but earn less. An oversold signal on its own has no edge; the 200-day trend filter does most of the work.

| 2025 – Oct 2026 (never used to choose the rules) | Return / year | Worst drop |
|---|---|---|
| SPY buy & hold | 17.4% | −18.8% |
| SPY timing (hold SPY only above its 200-day average) | 11.2% | −10.2% |
| Reference rule set (Williams %R dip-buying + trend filter) | 7.3% | −12.8% |

Full results, verdicts and reasoning: **[docs/strategy-research.md](docs/strategy-research.md)**.
Searching, stress tests and engine details: [docs/TECHNICAL.md](docs/TECHNICAL.md).

## What's in here
| Folder | Contents |
|---|---|
| `strategies/` | saved rule sets: `current.json` (reference), `candidate_breadth.json`, `coach_plan.json` (template), plus your own |
| `docs/` | guide, findings, technical notes |
| `backtest/` | the code (`python3 -m backtest.<command>`) |
| `output/` | reports and results (created when you run something) |

*Backtests are not a promise. Results use today's index members (survivorship bias) and are therefore somewhat optimistic.*
