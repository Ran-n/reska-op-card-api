[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:26:17 )
[//]: # (+ Revised: 	2026/06/29 10:20:02.220056 )
[//]: # ( ---------------------------------------------------------------------- )

# reska-op-card-api

REST API for One Piece TCG card information.

## Stack

| Layer | Technology |
|-------|-----------|
| API   | FastAPI (REST) |
| DB    | SQLite + SQLModel + Alembic |
| Server | uvicorn |

## Requirements

- Python ≥ 3.14
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
uv sync
```

Copy the example env file and fill in values:

```sh
cp .env.example .env
```

Apply database migrations:

```sh
uv run alembic upgrade head
```

The database and images are stored under `data/` (`data/optcg.db`, `data/images/cards/`, `data/images/langs/`).

## HTTPS (local dev)

The API serves HTTPS when `SSL_CERTFILE` and `SSL_KEYFILE` are set in `.env`. If they are unset, it falls back to plain HTTP.

Generate locally-trusted certs with [mkcert](https://github.com/FiloSottile/mkcert):

```sh
mkcert -install          # once — installs local CA into OS/browser trust store
mkcert localhost 127.0.0.1
```

Move the generated files into `certs/` and set the paths in `.env` (see `.env.example`). The `certs/` directory is gitignored — never commit private keys.

## Run

```sh
uv run api
```

The port is controlled by the `PORT` env var (default `8443` with TLS, `8000` without). Interactive docs at `https://localhost:8443/docs` (or `http://localhost:8000/docs` without TLS).

## Authentication

All endpoints require an `X-API-Key` header or `?api_key=` query parameter. There are two key types:

| Type | `can_edit` | Allowed operations |
|------|-----------|-------------------|
| Read | `false` | `GET` endpoints only |
| Edit | `true` | All endpoints |

### Key management (CLI)

```sh
uv run create-key --label ingest         # read-only key
uv run create-key --label ci --edit      # edit key
uv run list-keys                         # list all keys with usage stats
uv run delete-key --label ingest         # revoke a key (soft-delete)
```

The raw key is printed once to stdout on creation. Store it securely — only the BLAKE3 hash is stored in the database.

### Key management (Admin UI)

The web UI at `/admin/keys` lets you create, revoke, restore, and purge keys without the CLI. It requires HTTP Basic auth — set `ADMIN_USERNAME` and `ADMIN_PASSWORD` in `.env`.

## Data ingestion

Populate the database by scraping the official card list:

```sh
uv run scripts/ingest.py              # all sets
uv run scripts/ingest.py --set OP-01  # single set (also accepts op01)
```

Fetches every series from `en.onepiece-cardgame.com/cardlist/` and writes sets, cards, and a default `naip` print record per card. Safe to re-run — all writes are upserts.

## API

All endpoints (except `GET /`) require `X-API-Key`. Edit endpoints additionally require a key with `can_edit = true`.

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /` | — | Health check |
| `GET /admin` | Basic | Admin dashboard |
| `GET /admin/keys` | Basic | Key manager UI — list, create, revoke, restore, purge |
| `POST /admin/keys` | Basic | Create a key (form submission) |
| `POST /admin/keys/{id}/delete` | Basic | Revoke a key (soft-delete) |
| `POST /admin/keys/{id}/restore` | Basic | Restore a revoked key |
| `POST /admin/keys/{id}/purge` | Basic | Permanently delete a key and its logs |
| `GET /cards/` | read | List cards (filter: `name`, `set_id`, `cardtype_id`; paginate: `offset`, `limit`; expand: `set`, `cardtype`, `rarity`) |
| `POST /cards/` | edit | Create a card |
| `GET /cards/{id}` | read | Get card detail (expand: `set`, `cardtype`, `rarity`, `block`) |
| `PUT /cards/{id}` | edit | Update a card |
| `DELETE /cards/{id}` | edit | Delete a card |
| `POST /cards/{id}/image` | edit | Upload card image (multipart file, max 10 MB) |
| `POST /cards/{id}/image-url` | edit | Fetch and store card image from URL (max 10 MB) |
| `GET /naips/` | read | List naips (filter: `card_fk`, `set_id`, `language_id`, `print_variant_id`, `is_default`; paginate: `offset`, `limit`; expand: `card`, `set`, `print_variant`, `language`, `artist`) |
| `GET /naips/{id}` | read | Get naip detail (expand: `card`, `set`, `artist`, `print_variant`, `language`, `cardtype`, `block`) |
| `POST /naips/` | edit | Create a naip |
| `PUT /naips/{id}` | edit | Update a naip |
| `DELETE /naips/{id}` | edit | Delete a naip |
| `POST /naips/{id}/image` | edit | Upload naip image (multipart file, max 10 MB) |
| `POST /naips/{id}/image-url` | edit | Fetch and store naip image from URL (max 10 MB) |
| `GET /sets/` | read | List all sets (expand: `language`, `parent`, `type`) |
| `GET /sets/{id}` | read | Get a set (expand: `language`, `parent`, `type`) |
| `GET /images/{filename}` | — | Serve stored images (static) |
| `GET /lookups/cardtypes` | read | Card types |
| `GET /lookups/colors` | read | Colors |
| `GET /lookups/tribes` | read | Tribes |
| `GET /lookups/attributes` | read | Attributes |
| `GET /lookups/rarities` | read | Rarities |
| `GET /lookups/print-variants` | read | Print variants (STD, AA, TR, SP, GR, …) |
| `GET /lookups/blocks` | read | Blocks |
| `GET /lookups/formats` | read | Formats |
| `GET /lookups/keywords` | read | Keywords |
| `GET /lookups/reswords` | read | Restricted words |
| `GET /lookups/artists` | read | Artists |
| `GET /lookups/sets` | read | Sets (code + name) |
| `GET /lookups/settypes` | read | Set types |
| `GET /lookups/languages` | read | Languages |
| `GET /lookups/regions` | read | Regions |

### Expand parameter

FK fields in list and detail responses default to bare integers. Pass `?expand=field1,field2,...` to inline the related object instead:

```sh
GET /cards/42?expand=set,cardtype,rarity
GET /naips/?expand=card,set,print_variant&card_fk=1
GET /sets/?expand=language,parent,type
```

Expanded fields return an object (`{ "id": ..., "code": ..., "name": ... }`) instead of a plain `int`. Fields not listed in `expand` remain as integers.

## Data model

Core tables: `set` (with `parent_fk` self-referential FK linking a set to its canonical counterpart or parent product), `card`, `naip` (physical print — card + set + artist + print variant; holds per-print overrides for name, effect, trigger, and image; `is_default` flags the canonical print; `is_foil`, `is_errata`, `serial_max`), `naip_serial` (each known revealed copy of a serialized naip, keyed by `serial_number`).

Text dedup tables: `name`, `effect`, `trigger`, `image` — shared string values referenced by FK to avoid redundancy.

History tables: `card_effect_history`, `card_trigger_history` — audit log of text changes with validity windows.

Lookup tables: `set_type`, `card_type`, `artist`, `rarity`, `print_variant` (hierarchy of print-level finishes via `parent_fk`), `tribe`, `attribute`, `color`, `block`, `format`, `keyword`, `resword`, `language`, `region`.

Region mapping: `region_language` — which languages are officially used in each region.

Junction tables (card level): `card_color`, `card_tribe`, `card_attribute`, `card_format`, `card_keyword`, `card_resword`.

Junction tables (naip level): `naip_color`, `naip_tribe`, `naip_attribute`, `naip_keyword`, `naip_resword` — per-print overrides for many-to-many attributes.

Ban tables: `card_ban` (card banned in a format or globally), `banned_pair` (two cards that cannot coexist in a deck).

## Development

```sh
uv sync --group dev
uv run ruff format src/
uv run ruff check src/
uv run pytest
```

## License

[PayBack License (PBL) v2.0](LICENSE)
