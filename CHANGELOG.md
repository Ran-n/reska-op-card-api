[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:27:41 )
[//]: # (+ Revised: 	2026/05/16 22:53:20.507971 )
[//]: # ( ---------------------------------------------------------------------- )

# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Fixed

- `.gitignore`: added `data/` rule so local card images and database files are never tracked

### Added

- `Set.series` and `Set.ord` nullable columns for grouping sets by release series and ordering within it; migration `b2c3d4e5f6a8`
- `Naip.is_errata` boolean column (default `False`) to flag errata prints; migration `a1b2c3d4e5f7`
- ER and MR diagrams updated to reflect `is_errata` column on `Naip`
- `Name`, `Effect`, `Trigger`, `Image` dedup tables — shared string values referenced by FK from `Card` and `Naip` to avoid redundancy
- `CardEffectHistory`, `CardTriggerHistory` audit tables with `valid_from` / `valid_to` validity windows
- `_DateTimeMs` custom SQLAlchemy type — stores `datetime` as `YYYY-MM-DD HH:MM:SS.mmm` (millisecond precision) in SQLite
- `ingest.py`: name/effect/trigger dedup caches; `Naip` creation with rarity FK; Python 3.12 generic function syntax (`_get_or_create[T]`)
- `ruff` exclusion for `alembic/versions/`; suppressed rules `B008` and `B904`

### Changed

- Database file relocated from `./optcg.db` to `./data/optcg.db`; images dir relocated from `card_images/` to `data/images/`; static mount renamed `/card_images` → `/images`
- All table names normalised to snake_case: `settype` → `set_type`, `cardtype` → `card_type`, `cardattribute` → `card_attribute`, `cardcolor` → `card_color`, `cardrarity` → `card_rarity`, `cardblock` → `card_block`, `cardformat` → `card_format`, `cardkeywords` → `card_keyword`, `cardreswords` → `card_resword`
- `CardKeywords` / `CardReswords` junction models renamed to `CardKeyword` / `CardResword` for consistency
- `Card` columns `name`, `desc`, `trigger` replaced by FK references `name_fk`, `effect_fk`, `trigger_fk` pointing to the new dedup tables
- Timestamps changed from `date` (SQLite `CURRENT_DATE` server-default) to `datetime` with millisecond precision set in Python; `onupdate` now triggers correctly on every flush
- `init_db()` now creates `data/` directory before calling `create_all`
- All models updated from `Optional[T]` syntax to `T | None` (Python 3.10+ union style)
- `ingest.py`: removed `CardRarity` direct upsert (rarity now stored on `Naip`); updated card upsert to write `name_fk`, `effect_fk`, `trigger_fk`

---

## [0.1.0] - 2026-05-13

### Added

- Full SQLModel + Alembic data model: core tables (`set`, `card`, `naip`), 11 lookup tables, and 8 junction tables for card many-to-many relationships
- `database.py` with SQLite engine, `init_db`, and `get_session`
- `routers/cards.py`: full CRUD with rich enriched responses, image upload (multipart file + URL fetch), and M2M junction sync
- `routers/sets.py`: read-only `GET /sets/` and `GET /sets/{id}`
- `routers/lookups.py`: read-only explicit routes for 11 lookup types (`GET /lookups/cardtypes`, `/colors`, `/tribes`, `/attributes`, `/rarities`, `/blocks`, `/formats`, `/keywords`, `/reswords`, `/artists`, `/sets`)
- `scripts/ingest.py` data ingestion script
- `alembic.ini` and `alembic/` migration environment
- Static file serving for `data/images/` via `GET /images/{filename}`
- CORS middleware allowing all origins
- `alembic`, `sqlmodel`, `httpx`, `python-multipart`, `beautifulsoup4` runtime dependencies

### Changed

- `main.py` refactored: lifespan-based `init_db`, all three routers included, CORS wired up, static mount added
- `pyproject.toml`: `requires-python` bumped to `>=3.14`, `target-version` updated to `py314`, `opapi` script entry removed
- README expanded with stack table, setup/run instructions, full API reference, and data model overview

### Removed

- Root `main.py` entry point (replaced by `src/optcg_api/main.py`)
- `src/optcg_api/app.py` (logic moved into `main.py`)

---

## [0.0.1] - 2026-05-12

### Added

- FastAPI application skeleton with single `GET /` endpoint
- `src/optcg_api/` package structure with `app.py` and `__init__.py`
- setuptools build system with packages discovered under `src/`
- `opapi` CLI script alias mapped to `optcg_api.main:main`
- `uv.lock` tracked in version control
- `CHANGELOG.md`, `CONTRIBUTING.md`, `CONTRIBUTORS`, `README.md`, and `LICENSE` (PBL v2.0)
