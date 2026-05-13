[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:26:17 )
[//]: # (+ Revised: 	2026/05/13 )
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

## Run

```sh
uv run uvicorn optcg_api.main:app --reload
```

Interactive docs available at `http://localhost:8000/docs`.

## API

| Prefix | Description |
|--------|-------------|
| `GET /` | Health check |
| `GET/POST /cards/` | List or create cards |
| `GET/PUT/DELETE /cards/{id}` | Get, update, or delete a card |
| `GET /sets/` | List all sets |
| `GET /sets/{id}` | Get a set |
| `GET /lookups/{resource}` | Lookup table values |

Lookup resources: `cardtypes`, `colors`, `tribes`, `attributes`, `rarities`, `blocks`, `formats`, `keywords`, `reswords`, `artists`, `sets`, `settypes`.

## Data model

Core tables: `set`, `card`, `naip` (physical print — card + set + artist + rarity).

Lookup tables: `settype`, `cardtype`, `artist`, `rarity`, `tribe`, `attribute`, `color`, `block`, `format`, `keywords`, `reswords`.

Junction tables link cards to their many-to-many attributes: `cardcolor`, `cardtribe`, `cardattribute`, `cardrarity`, `cardblock`, `cardformat`, `cardkeywords`, `cardreswords`.

## Development

```sh
uv sync --group dev
uv run ruff format src/
uv run ruff check src/
uv run pytest
```

## License

[PayBack License (PBL) v2.0](LICENSE)
