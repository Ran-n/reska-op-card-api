[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:26:17 )
[//]: # (+ Revised: 	2026/06/03 16:48:45.793043 )
[//]: # ( ---------------------------------------------------------------------- )

# optcg_api

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
uv run uvicorn optcg_api.main:app --reload
```

Interactive docs available at `http://localhost:8000/docs`.

## Data ingestion

Populate the database by scraping the official card list:

```sh
uv run scripts/ingest.py              # all sets
uv run scripts/ingest.py --set OP-01  # single set (also accepts op01)
```

Fetches every series from `en.onepiece-cardgame.com/cardlist/` and writes sets, cards, and a default `naip` print record per card. Safe to re-run — all writes are upserts.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /` | Health check |
| `GET /cards/` | List cards (filter: `name`, `set_id`, `cardtype_id`; paginate: `offset`, `limit`) |
| `POST /cards/` | Create a card |
| `GET /cards/{id}` | Get card with enriched detail |
| `PUT /cards/{id}` | Update a card |
| `DELETE /cards/{id}` | Delete a card |
| `POST /cards/{id}/image` | Upload card image (multipart file) |
| `POST /cards/{id}/image-url` | Fetch and store card image from URL |
| `GET /naips/{id}` | Get naip with enriched detail |
| `POST /naips/` | Create a naip |
| `PUT /naips/{id}` | Update a naip |
| `DELETE /naips/{id}` | Delete a naip |
| `POST /naips/{id}/image` | Upload naip image (multipart file) |
| `POST /naips/{id}/image-url` | Fetch and store naip image from URL |
| `GET /sets/` | List all sets |
| `GET /sets/{id}` | Get a set |
| `GET /images/{filename}` | Serve stored images (static) |
| `GET /lookups/cardtypes` | Card types |
| `GET /lookups/colors` | Colors |
| `GET /lookups/tribes` | Tribes |
| `GET /lookups/attributes` | Attributes |
| `GET /lookups/rarities` | Rarities |
| `GET /lookups/print-variants` | Print variants (STD, AA, TR, SP, GR, …) |
| `GET /lookups/blocks` | Blocks |
| `GET /lookups/formats` | Formats |
| `GET /lookups/keywords` | Keywords |
| `GET /lookups/reswords` | Restricted words |
| `GET /lookups/artists` | Artists |
| `GET /lookups/sets` | Sets (code + name) |
| `GET /lookups/settypes` | Set types |
| `GET /lookups/languages` | Languages |
| `GET /lookups/regions` | Regions |

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
