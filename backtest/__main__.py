"""python3 -m backtest  ->  overview of all commands."""

COMMANDS = [
    ('Getting data', [
        ('python3 -m backtest.fetch', 'download ~14 years of daily prices (first time, ~1 min)'),
        ('python3 -m backtest.fetch --update', 'add the latest days (run before signals)'),
        ('python3 -m backtest.symbols', 'refresh the index member lists from Wikipedia'),
    ]),
    ('Testing a plan (no coding)', [
        ('python3 -m backtest.app', 'planner in your browser: build a plan, save it, run the report'),
        ('python3 -m backtest.plan', 'same in the Terminal: answer questions -> strategies/<name>.json'),
        ('python3 -m backtest.report --params strategies/<name>.json', 'one-page HTML report with verdict and charts'),
    ]),
    ('Daily use', [
        ('python3 -m backtest.signals --params strategies/<name>.json', "today's buy candidates (add --holding AAPL MSFT for sell signals)"),
    ]),
    ('Research (for the curious)', [
        ('python3 -m backtest.run --params ...', 'detailed text backtest, trades.csv, equity.csv'),
        ('python3 -m backtest.analyze --params ... [--quick]', 'stress tests: verdict, costs, neighbors, random entries'),
        ('python3 -m backtest.tune --space default', 'search many rule sets with walk-forward validation'),
    ]),
]

if __name__ == '__main__':
    print('StrategyAnalyser - commands (run from this folder)\n')
    for title, rows in COMMANDS:
        print(title)
        for cmd, what in rows:
            print(f'  {cmd}\n      {what}')
        print()
    print('Guide: docs/GUIDE.md   Findings: docs/strategy-research.md')
