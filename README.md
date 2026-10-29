# backend

Django API bridge for Nika Optimizer.

The backend sits between the React frontend and the existing Python repositories. It owns web/API concerns such as routing, request validation, response shapes, auth-ready workflow state, and future background job dispatch. It should not reimplement domain logic from `data-manager`, `no-calculator`, `strategist`, or `fisher`.

## Current API template

Strategy storage is intentionally not implemented yet. These strategy endpoints exist so the frontend and backend can agree on routes before the strategy schema is created:

- `GET /api/strategies/` — strategy list placeholder
- `GET /api/strategies/<strategy_id>/` — strategy detail placeholder
- `PUT /api/strategies/` — create strategy placeholder

Each endpoint returns `501 Not Implemented` with a JSON body explaining that database setup is pending.

## Local commands

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
set -a
source ~/.config/nika/postgres.env
set +a
python manage.py check
python manage.py test --keepdb
python manage.py runserver
```

## QuestDB candle API

`GET /api/instruments/` discovers finalized raw one-minute streams through
`DataManager.get_instruments()`. Each entry includes `instrument_id`, `provider`,
`venue`, `candle_count`, `first_ts`, and `last_ts`. Results are ordered by candle
count (up to 1000 streams). Instrument UUIDs are shown until a symbol metadata
catalog is integrated; do not substitute unrelated placeholder tickers.

`GET /api/candles/?symbol=<instrument_id>&provider=databento&timeframe=15m&period=1M&limit=500`
returns `{symbol, provider, timeframe, period, limit, candles}`. Each candle has
`time` (UTC Unix seconds), `open`, `high`, `low`, `close`, and `volume`, ordered
oldest first. `symbol` is the stored instrument ID, not a display ticker.

Supported timeframes: `1m`, `5m`, `15m`, `1h`, `4h`, `1d`.
Periods: `1D`, `1W`, `1M` (30 days), `3M` (90 days), `1Y` (365 days), relative to
the selected stream's latest stored minute. Limit defaults to 500, maximum 2000;
when a period contains more bars, only its newest bars are returned.
Empty selections return 200 with an empty array; invalid parameters return 400;
storage failures return a sanitized 503. Both endpoints are read-only GETs.

Django performs HTTP validation/orchestration only. `data-manager` owns the
connection, SQL, OHLCV aggregation and timestamp conversion. Configure its
`NIKA_QUESTDB_*` environment variables as described in the data-manager README.
The strategy routes above remain placeholders; these candle routes are live.

## Debug API

When Django DEBUG is true, `/api/debug/datasets/` and `/api/debug/inspection/`
serve read-only Data Inspector diagnostics from `NIKA_INSPECTOR_ARCHIVE`.
Generate the archive with data-manager before starting Django. No archive path
or table name is accepted from the browser. Endpoints are disabled with 404
outside DEBUG. See `../documentation/debug-dashboard.md` for the complete contract.

## Chart drawings API

Chart drawings (long/short position tools and markers) persist through Django.
They are UI annotations for research, not strategy rules or orders.

- `GET /api/drawings/?strategy=<key>&provider=<provider>&instrument=<instrument_id>`
  returns `{drawings: [...]}` for one strategy view of one instrument stream,
  oldest first. All three parameters are required.
- `PUT /api/drawings/<uuid>/` creates (201) or updates (200) one drawing. The
  browser generates the UUID. Body: `{strategy, provider, instrument, tool,
  schema_version: 1, revision, data}`. `revision` must increase on every save;
  a stale revision returns 409 with the stored `drawing`, so the client can
  adopt it. Scope and tool cannot change after creation.
- `DELETE /api/drawings/<uuid>/` returns 204 and is idempotent.

`tool` is `long_position`, `short_position` or `marker`. Position `data` holds
`entry {time, price}`, `end_time`, `target_price`, `stop_price`,
`account {size, lot_size, risk_mode: percent|amount, risk}` and
`style {line_color, profit_color, stop_color}`; long positions require
stop < entry < target and short positions target < entry < stop. Marker
`data` is `{time, label, color}`. Times are UTC Unix seconds anchored to bar
open times, so drawings appear on every timeframe.

`strategy` is the frontend strategy key stored as text; strategies have no
model yet, so it is not a foreign key. The `Drawing` model uses native PostgreSQL UUID/JSONB through Django
(UUID key, JSONField). PostgreSQL is now the application database default.

This is the first database-backed table. Container startup runs Django migrations
before serving; host-side development should run `python manage.py migrate`.

## PostgreSQL application database

The backend defaults to PostgreSQL on localhost port 13070, database/user `nika`.
Configure `NIKA_POSTGRES_PASSWORD_FILE` and the variables in
`postgres.env.example`. There is no silent SQLite fallback. The local protected
settings file is `~/.config/nika/postgres.env`; container settings and read-only
secret mounting are handled by no-deploy. Tests use a separate pre-created
`test_nika` database with `python manage.py test tests --keepdb`.

`python manage.py import_sqlite --help` describes the backup-first legacy import
command. See `../documentation/postgresql-migration.md` for setup, the verified
cutover, lifecycle, migration and backup details. Candles remain in QuestDB.
