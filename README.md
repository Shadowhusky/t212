<div align="center">

# t212

**Your Trading 212 portfolio in the terminal — clear, fast, read-only.**

A professional TUI for monitoring your Trading 212 account: live P&L, positions,
AutoInvest pies, history & dividends, a locally‑recorded equity curve, and a
searchable instrument universe. No browser, no spreadsheets — just your numbers,
in plain text.

![Python](https://img.shields.io/badge/python-3.11+-blue)
![Built with Textual](https://img.shields.io/badge/built%20with-Textual-5a4fcf)
![Read-only](https://img.shields.io/badge/access-read--only-3fb950)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

</div>

```
 t212  ● live · LIVE · GBP                                Thu 5 Jun 2026 · 14:32:05
 Portfolio value  £24,813.07   Today ▲ +£86.20   Free £312.40
 ────────────────────────────────────────────────────────────────────────────────
  1 Dashboard    2 Positions    3 Pies    4 History    5 Search
 ────────────────────────────────────────────────────────────────────────────────
 OPEN P&L                    ALLOCATION · by type        TOP MOVERS
 ▲ +£1,204.33  +5.12%        Stocks ▰▰▰▰▰▰▰▱▱▱  68%       NVDA  ▲ +3.2%
 Realised   +£430.11         ETFs   ▰▰▰▱▱▱▱▱▱▱  29%       AAPL  ▲ +2.1%
 Invested   £23,500.00       Cash   ▰▱▱▱▱▱▱▱▱▱   3%       TSLA  ▼ −1.8%

 EQUITY · since first run
 ▁▂▂▃▃▄▄▅▅▆▆▇▇████▇▇▆▆▇▇████
```

> [!NOTE]
> Read‑only by design. `t212` **never** places, modifies, or cancels orders — it
> only reads. The only HTTP verb it uses is `GET`.

## Features

- **Dashboard** — hero account value, today's change, open/realised P&L, allocation by type, top movers, and a recorded equity curve.
- **Pending orders** — your open limit / stop / market orders at a glance (requires the *Orders* scope on your API key; the dashboard tells you if it's missing).
- **Income & deposits** — all‑time dividends and cash interest (plus last 12 months), and net deposits with your total gain versus what you've put in.
- **Positions** — sortable, colour‑coded holdings table (value, P&L £/%, weight) with a per‑position detail view. Adapts columns to your terminal width.
- **Pies** — every AutoInvest pie's value, return and dividends, plus a per‑pie breakdown with target‑vs‑actual **drift** and any instrument **issues** flagged.
- **History** — orders (with realised P&L and fees), dividends (with running total) and cash transactions (with running balance), switchable in place and pageable with `m`.
- **Instrument search** — fuzzy‑search the full tradeable universe; instruments you hold are flagged, with market hours in the detail view.
- **Local equity curve** — the API has no history‑of‑value endpoint, so `t212` records snapshots to a local SQLite database and charts them, honestly labelled *“since first run.”*
- **Polite by default** — REST polling tuned to each endpoint's rate limit, with jitter and automatic `429` back‑off.
- **Built for the eyes** — three themes (dark / light / high‑contrast), gain/loss never relies on colour alone (always an arrow + sign), and a **privacy blur** to hide balances when you're sharing your screen.

## Install

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11+.

```sh
git clone https://github.com/<you>/t212.git
cd t212
uv sync
```

## Get an API key

The easy way: just run `uv run t212` — on first run it walks you through
connecting, right in the TUI: paste your key ID and secret, pick live or demo,
and it validates against Trading 212 before saving (to
`~/.config/t212/config.toml`, chmod 600). Or press *Browse sample data* to
explore offline without a key.

To generate a key, in the Trading 212 app: **Settings → API (Beta)** and create
one for the account you want to watch (live or demo). Read‑only scopes are
enough. You'll get a **key ID** and a **secret** — t212 sends them as HTTP
Basic auth.

Prefer to set credentials yourself? Both still work:

```sh
# environment variable — join as keyId:secret
export TRADING212_API_KEY="<keyId>:<secret>"

# …or prompt + save to ~/.config/t212/config.toml (chmod 600)
uv run t212 config set-key
```

## Usage

```sh
uv run t212                 # live account, interactive TUI
uv run t212 --demo          # practice account
uv run t212 --mock          # offline demo on bundled fixtures (no key needed)
uv run t212 --once          # one-shot text summary, then exit (scriptable)
uv run t212 --refresh 15    # override the portfolio poll interval (seconds)
```

### Keys

| Key | Action |
| --- | --- |
| `1`–`5` | Switch tab (Dashboard / Positions / Pies / History / Search) |
| `↑` `↓` | Move selection |
| `Enter` | Open detail (position / pie / instrument) |
| `Esc` | Close detail |
| `←` `→` | Switch History section (Orders / Dividends / Transactions) |
| `m` | Load more (History) |
| `s` | Cycle sort (Positions) |
| `z` | Privacy blur — hide all amounts |
| `t` | Cycle theme |
| `r` | Refresh now |
| `?` | Help |
| `Ctrl+P` | Command palette |
| `q` | Quit |

On the **Search** tab, just start typing to filter by ticker, name or ISIN.

## How it works

- **Read‑only.** The HTTP client exposes only `GET` methods; there is no code path that can mutate your account.
- **Current API surface.** `t212` talks to Trading 212's `/api/v0` endpoints (account summary, positions, pies, orders, history) authenticated with HTTP Basic `keyId:secret`.
- **No price stream.** Trading 212's public API is REST‑only, so “live” P&L is polled. `t212` only polls what the active screen needs, on a per‑endpoint cadence (portfolio ≈ 10 s, account ≈ 30 s, history 6/min) with ±25 % jitter, and backs off automatically when the API returns `429`.
- **Equity curve.** On each successful poll, an account snapshot `(total, free, invested, P&L)` and per‑position values are appended to `~/.local/share/t212/<env>-<account>.sqlite`. The curve therefore grows the more you run it — it is labelled *“since first run”* and never back‑filled with invented data.
- **Credentials** are read from `--api-key`, then `$TRADING212_API_KEY`, then `~/.config/t212/config.toml`. They are never logged or rendered.

## Development

```sh
uv run pytest -q     # 101 tests, no network — runs entirely on fixtures
uv run t212 --mock   # drive the full UI offline
```

```
src/t212/
  cli.py            click entry (--once / --mock / config set-key)
  config.py         credential + settings resolution
  models.py         pydantic models for every API resource
  formatting.py     money / percent / delta / privacy formatting
  charts.py         equity-curve windowing
  store.py          sqlite snapshots + instrument cache
  resolve.py        ticker → name / exchange
  summary.py        headless --once summary
  app.py            Textual app: header, tabs, scheduler
  scheduler.py      per-tab smart polling
  api/              base protocol · http client · mock client · rate-limit governor
  widgets/          summary header · render primitives (bar/sparkline/pnl)
  screens/          dashboard · positions · pies · history · search · detail screens
```

## Disclaimer

`t212` is an independent, unofficial tool and is **not affiliated with, endorsed
by, or connected to Trading 212**. The Trading 212 API is in beta and may change.
This software is provided as‑is, for informational purposes only, and is **not
financial advice**. Use at your own risk.

## License

[MIT](LICENSE) © shadowhusky
