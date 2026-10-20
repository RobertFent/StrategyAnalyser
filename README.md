# StrategyAnalyser

## Quick start

**You need:** Python 3.10 or newer ([python.org/downloads](https://www.python.org/downloads/)) and a Terminal opened in this folder.

**First time** (about 5 minutes):
```sh
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python3 -m backtest.fetch          # downloads ~14 years of daily prices (about 1 minute)
python3 -m backtest.app            # opens the Strategy Planner in your browser
```

**Every next time:**
```sh
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python3 -m backtest.fetch --update # optional: add the latest trading days
python3 -m backtest.app
```

In the planner: describe your rules, click **Save & run backtest** and the report opens after about a minute.
Other useful commands:

| Command | What it does |
|---|---|
| `python3 -m backtest.report` | report for the reference rule set (`strategies/current.json`) |
| `python3 -m backtest.signals --params strategies/<plan>.json` | today's buy candidates for a plan (for paper trading) |
| `python3 -m backtest` | list of all commands |

New to this? The **[Guide](docs/GUIDE.md)** explains every step, how to read the report and how to paper trade.

## What this is
Tests indicator-based swing trading rules on S&P 500 stocks over 10+ years, with clear buy and sell rules.
It compares them honestly against simply holding the index.

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
