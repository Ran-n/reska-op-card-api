[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:27:41 )
[//]: # (+ Revised: 	2026/05/12 16:27:56.099637 )
[//]: # ( ---------------------------------------------------------------------- )

# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- Full SQLModel + Alembic data model: core tables (`set`, `card`, `naip`), 11 lookup tables, and 8 junction tables for card many-to-many relationships
- `database.py` with SQLite engine, `init_db`, and `get_session`
- `routers/cards.py`: CRUD endpoints with rich enriched responses, image upload (file + URL), and M2M junction sync
- `routers/sets.py` and `routers/lookups.py` routers
- `scripts/ingest.py` data ingestion script
- `alembic.ini` and `alembic/` migration environment
- Static file serving for `card_images/` via `/card_images` mount
- CORS middleware allowing all origins
- `alembic`, `sqlmodel`, `httpx`, `python-multipart`, `beautifulsoup4` runtime dependencies
- CONTRIBUTORS file updated to full PBL v2.0 format with SUMMARY and DETAILS blocks
- README expanded with stack table, setup/run instructions, API reference, and data model overview
- FastAPI application skeleton with single `GET /` endpoint returning `{"message": "Hello World!"}`
- `src/optcg_api/` package structure with `app.py` and `__init__.py`
- Root `main.py` entry point importing `optcg_api.app:app`
- `opapi` CLI script alias mapped to `optcg_api.main:main`
- setuptools build system with packages discovered under `src/`
- `uv.lock` tracked in version control
- `CHANGELOG.md`, `CONTRIBUTING.md`, `CONTRIBUTORS`, and `README.md` License section
- Updated LICENSE to PBL v2.0

### Changed

- `main.py` refactored: lifespan-based `init_db`, routers included, CORS wired up, `app.py` removed
- `pyproject.toml`: `requires-python` bumped to `>=3.14`, `target-version` updated to `py314`, `opapi` script entry removed

### Removed

- Root `main.py` entry point (replaced by `src/optcg_api/main.py` directly)
- `src/optcg_api/app.py` (logic moved into `main.py`)
