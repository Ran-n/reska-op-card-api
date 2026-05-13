[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:27:41 )
[//]: # (+ Revised: 	2026/05/13 13:16:54.935173 )
[//]: # ( ---------------------------------------------------------------------- )

# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [0.1.0] - 2026-05-13

### Added

- Full SQLModel + Alembic data model: core tables (`set`, `card`, `naip`), 11 lookup tables, and 8 junction tables for card many-to-many relationships
- `database.py` with SQLite engine, `init_db`, and `get_session`
- `routers/cards.py`: full CRUD with rich enriched responses, image upload (multipart file + URL fetch), and M2M junction sync
- `routers/sets.py`: read-only `GET /sets/` and `GET /sets/{id}`
- `routers/lookups.py`: read-only `GET /lookups/{resource}` for all 12 lookup types
- `scripts/ingest.py` data ingestion script
- `alembic.ini` and `alembic/` migration environment
- Static file serving for `card_images/` via `GET /card_images/{filename}`
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
