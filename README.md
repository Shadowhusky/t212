# t212

A terminal dashboard for your Trading 212 account. Read-only by design: it can
show you everything and touch nothing.

```
 t212  ● live · LIVE · GBP                                Wed 10 Jun 2026 · 14:32:05
 Portfolio value  £24,813.07   Today ▲ +£86.20   Free £312.40
 ──────────────────────────────────────────────────────────────────────────────
  1 Dashboard    2 Positions    3 Pies    4 History    5 Search
 ──────────────────────────────────────────────────────────────────────────────
 INVESTMENTS                       CASH
 Value      £24,395.17             Available   £312.40
 Cost       £23,190.84             In pies     £105.50
 Unrealised ▲ +£1,204.33  +5.19%   Reserved    £0.00
 Realised   ▲ +£430.11

 INCOME                            DEPOSITS
 Dividends  £16.30                 Net deposits  £23,300.00
 Interest   £1.95                  Gain vs in    ▲ +£1,513.07

 EQUITY · since first run
 ▁▂▂▃▃▄▄▅▅▆▆▇▇████▇▇▆▆▇▇████
```

I wanted to check my portfolio without opening the app or a browser tab, and
without ever worrying that a stray keypress could place an order. So: a TUI
that polls the public API politely, renders everything worth knowing, and has
no code path that can mutate the account. The only HTTP verb in the client
is `GET`.

## What it shows

- **Dashboard** – account value, unrealised and realised P&L, cash breakdown
  (available / in pies / reserved), pending orders, dividend & interest income,
  net deposits vs. current value, allocation, top movers, equity curve.
- **Positions** – sortable table with value, P&L, FX impact and weight, plus a
  detail view per holding. Quantity held inside pies is marked.
- **Pies** – each AutoInvest pie with its return, dividends and goal progress;
  drill in for target-vs-actual drift per instrument and any flagged issues.
- **History** – orders with realised P&L and fees, dividends with running
  totals (cash interest included), deposits and withdrawals with a running
  balance. `m` pages further back.
- **Search** – the full tradeable universe, filtered as you type. Holdings are
  flagged; the detail view shows market hours.
- **Equity curve** – the API exposes no account-value history, so t212 records
  a snapshot locally (SQLite) each time it polls. The chart grows the longer
  you use it and is labelled "since first run"; nothing is back-filled.

Three themes (dark, light, high-contrast), a privacy blur (`z`) for
screen-sharing, and gains/losses always carry an arrow and a sign, never
colour alone.

## Install

Needs Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```sh
git clone https://github.com/Shadowhusky/t212.git
cd t212
uv sync
uv run t212
```

First run opens a guided setup: paste your API key ID and secret, pick live or
demo, and it validates against the API before saving. There's also a
"browse sample data" mode if you just want to poke around the UI first.

To get a key: Trading 212 app → **Settings → API (Beta)** → generate. Enable
the read scopes (Account, Portfolio, Pies, Metadata, History). *Orders read*
is optional — it powers the pending-orders panel. t212 works with Invest and
Stocks ISA accounts.

Prefer configuring outside the TUI? Both of these work too:

```sh
export TRADING212_API_KEY="<keyId>:<secret>"   # env var
uv run t212 config set-key                     # prompt, saved chmod 600
```

## Usage

```sh
uv run t212              # live account
uv run t212 --demo       # practice account
uv run t212 --mock       # sample data, no key needed
uv run t212 --once       # plain-text summary to stdout, then exit
uv run t212 --refresh 15 # poll interval in seconds
```

| Key | Action |
| --- | --- |
| `1`–`5` | Switch tab |
| `↑`/`↓`, `j`/`k` | Move |
| `Enter` / `Esc` | Open / close detail |
| `←` `→` | History section |
| `m` | Load more (History) |
| `s` | Sort (Positions) |
| `z` | Privacy blur |
| `t` | Theme |
| `r` | Refresh now |
| `?` | Help |
| `q` | Quit |

## Notes on behaviour

- Talks to the current `/api/v0` surface (account summary, positions, pies,
  orders, equity history) with HTTP Basic `keyId:secret` auth.
- The API is REST-only, so prices are polled — each endpoint on its own
  cadence within its documented rate limit, with jitter, and automatic
  back-off on `429`.
- Only the active tab's data is polled.
- Credentials live in `~/.config/t212/config.toml` (chmod 600) and are sent
  nowhere except trading212.com. They are never logged or rendered.
- Snapshots are stored per account in `~/.local/share/t212/`.

## Development

```sh
uv run pytest -q     # 109 tests, fixture-driven, no network
uv run t212 --mock   # full UI offline
```

```
src/t212/
  models.py     pydantic models for the API
  api/          client protocol · httpx client · mock client · rate limiter
  scheduler.py  per-tab polling
  store.py      sqlite snapshots + instrument cache
  app.py        Textual app shell
  screens/      dashboard · positions · pies · history · search · setup · details
  widgets/      header · tab bar · render primitives
```

## Disclaimer

Unofficial, not affiliated with Trading 212. The API is in beta and may
change. Not financial advice; use at your own risk.

[MIT](LICENSE) © shadowhusky
