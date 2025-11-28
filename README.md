# Flip7

CLI options are available for both playing a single verbose game or running multiple silent simulations with strategy summaries.

Examples:

- Play a single game with the default strategies and winning score 200:

  ```bash
  python flip7.py --games 1
  ```

- Run 50 silent simulations and view win rates:

  ```bash
  python flip7.py --games 50 --simulate
  ```

- Customize players and strategies (supports `aggressive`, `conservative[=stay]`, `flip7[=safe]`):

  ```bash
  python flip7.py --games 25 --simulate --players "Alice:flip7" "Bob:conservative=35" "Charlie:aggressive"
  ```
