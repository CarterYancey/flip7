# Flip7

A lightweight simulator for the Flip 7 card game. You can play a single verbose game from the command line or run many quiet simulations to compare strategy win rates.

## Requirements
- Python 3.10+

## Installation
No external packages are required. Clone the repository and run the CLI directly:

```bash
python flip7.py --help
```

## Usage
The CLI supports single games (verbose) and multi-game simulations (quiet). Key options:

- `--games`: Number of games to run. Defaults to 1.
- `--simulate`: Run silent simulations and print a win-rate summary.
- `--players`: One or more `Name:strategy` specs.
- `--winning-score`: Target game score. Defaults to 200.

Supported strategies:
- `aggressive`: Always hit.
- `conservative[=stay]`: Stay once the round score reaches `stay` (default 40).
- `flip7[=safe]`: Chase Flip 7; stay if score reaches `safe` (default 50).
- `perfect`: Card-counting expected-value strategy.

### Play a single game
```bash
python flip7.py --games 1 --players "Alice:flip7" "Bob:conservative=35" "Charlie:aggressive"
```

### Run simulations with a summary
```bash
python flip7.py --games 50 --simulate --players "Alice:flip7" "Bob:conservative=35" "Charlie:aggressive"
```

Example summary output:
```
=== Simulation Summary ===
Alice (flip7)                 | Win Rate: 38.00% | Avg Score: 201.4 | Avg Rounds: 6.12
Bob (conservative=35)         | Win Rate: 32.00% | Avg Score: 189.7 | Avg Rounds: 6.10
Charlie (aggressive)          | Win Rate: 30.00% | Avg Score: 177.3 | Avg Rounds: 6.05
```

### Customize starting conditions
Change the winning score or the player lineup:
```bash
python flip7.py --games 20 --simulate --winning-score 250 --players "Dana:perfect" "Eli:flip7" "Finn:conservative"
```
