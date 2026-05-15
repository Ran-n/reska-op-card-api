[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:26:17 )
[//]: # (+ Revised: 	2026/05/15 13:47:35.194951 )
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

The database and images are stored under `data/` (`data/optcg.db`, `data/images/`).

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
| `GET /images/{filename}` | Serve stored card images (static) |
| `GET /sets/` | List all sets |
| `GET /sets/{id}` | Get a set |
| `GET /lookups/{resource}` | Lookup table values |

Lookup resources: `cardtypes`, `colors`, `tribes`, `attributes`, `rarities`, `blocks`, `formats`, `keywords`, `reswords`, `artists`, `sets`.

## Data model

Core tables: `set`, `card`, `naip` (physical print — card + set + artist + rarity; holds per-print overrides for name, effect, trigger, and image; `is_default` flags the canonical print).

Text dedup tables: `name`, `effect`, `trigger`, `image` — shared string values referenced by FK to avoid redundancy.

History tables: `card_effect_history`, `card_trigger_history` — audit log of text changes with validity windows.

Lookup tables: `set_type`, `card_type`, `artist`, `rarity`, `tribe`, `attribute`, `color`, `block`, `format`, `keyword`, `resword`.

Junction tables link cards to their many-to-many attributes: `card_color`, `card_tribe`, `card_attribute`, `card_rarity`, `card_block`, `card_format`, `card_keyword`, `card_resword`.

## Development

```sh
uv sync --group dev
uv run ruff format src/
uv run ruff check src/
uv run pytest
```

## License

[PayBack License (PBL) v2.0](LICENSE)
