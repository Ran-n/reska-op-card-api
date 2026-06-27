[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:26:17 )
[//]: # (+ Revised: 	2026/06/28 01:21:47.313085 )
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

Apply database migrations:

```sh
uv run alembic upgrade head
```

The database and images are stored under `data/` (`data/optcg.db`, `data/images/cards/`, `data/images/langs/`).

## Run

```sh
uv run api                        # localhost:8000, reload enabled
uv run api --port 8001            # custom port
uv run api --host 0.0.0.0         # bind all interfaces
uv run api --help                 # all uvicorn options
```

Interactive docs available at `http://localhost:8000/docs`.

## Authentication

All endpoints require an `X-API-Key` header. There are two key types:

| Type | `can_edit` | Allowed operations |
|------|-----------|-------------------|
| Read | `false` | `GET` endpoints only |
| Edit | `true` | All endpoints |

Generate a key with the `create-key` CLI:

```sh
uv run create-key                        # read-only key
uv run create-key --edit                 # edit key
uv run create-key --edit --label ingest  # with a label
```

The key is printed once to stdout. Store it securely — it is not recoverable from the database.

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
| `GET /cards/` | read | List cards (filter: `name`, `set_id`, `cardtype_id`; paginate: `offset`, `limit`) |
| `POST /cards/` | edit | Create a card |
| `GET /cards/{id}` | read | Get card with enriched detail |
| `PUT /cards/{id}` | edit | Update a card |
| `DELETE /cards/{id}` | edit | Delete a card |
| `POST /cards/{id}/image` | edit | Upload card image (multipart file) |
| `POST /cards/{id}/image-url` | edit | Fetch and store card image from URL |
| `GET /naips/{id}` | read | Get naip with enriched detail |
| `POST /naips/` | edit | Create a naip |
| `PUT /naips/{id}` | edit | Update a naip |
| `DELETE /naips/{id}` | edit | Delete a naip |
| `POST /naips/{id}/image` | edit | Upload naip image (multipart file) |
| `POST /naips/{id}/image-url` | edit | Fetch and store naip image from URL |
| `GET /sets/` | read | List all sets |
| `GET /sets/{id}` | read | Get a set |
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
