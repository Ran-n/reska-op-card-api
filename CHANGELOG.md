[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:27:41 )
[//]: # (+ Revised: 	2026/05/21 13:17:21.416160 )
[//]: # ( ---------------------------------------------------------------------- )

# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- `Naip.serial_max` nullable integer column — the total print run size for a serialized naip (e.g. 500 for a 1/500 card); migration `d67a59a0943a`
- `NaipSerial` table — records each known revealed copy of a serialized naip (`naip_fk`, `serial_number`, `image_fk`); unique on `(naip_fk, serial_number)` with a `CHECK serial_number >= 1` constraint; migration `d67a59a0943a`
- `trg_naip_serial_update` SQLite trigger to auto-bump `updated_ts` on `naip_serial` row changes; migration `75adbb637f38`
- `Block.image_fk` nullable FK → `image.id`; migration `a3b4c5d6e7f8`
- `Card.block_fk` nullable FK → `block.id` (replaces `card_block` junction); migration `a3b4c5d6e7f8`
- `Naip.block_fk` nullable FK → `block.id` (replaces `naip_block` junction); migration `a3b4c5d6e7f8`
- `Set.block_fk` nullable FK → `block.id` — a set belongs to exactly one block; migration `b4c5d6e7f8a9`
- `CardBan` table — per-card ban scoped to a format or all formats when `format_fk IS NULL`; NULL-safe partial unique index prevents duplicate global bans; `trg_card_ban_update` trigger; migrations `a3b4c5d6e7f8`, `b4c5d6e7f8a9`
- `BannedPair` table — two-card combo ban with `ck_banned_pair_ordered` constraint (`card_a_fk < card_b_fk`) and NULL-safe partial unique index for global pair bans; `trg_banned_pair_update` trigger; migrations `a3b4c5d6e7f8`, `b4c5d6e7f8a9`
- `trg_block_update` SQLite trigger to auto-bump `updated_ts` on `block` row changes; migration `a3b4c5d6e7f8`
- `trg_naip_serial_check_max_insert` / `trg_naip_serial_check_max_update` BEFORE triggers enforce `serial_number ≤ serial_max` on `naip_serial` rows (SQLite `CHECK` cannot reference other tables); migration `b4c5d6e7f8a9`
- `Language` table — BCP-47 language codes (`ja`, `en`, `fr`, `zh-Hans`, `ko`), optional `image_fk`; `trg_language_update` trigger; migration `b5c6d7e8f9a0`
- `Region` table — UN M.49 region codes for 15 tournament regions; `trg_region_update` trigger; migration `b5c6d7e8f9a0`
- `RegionLanguage` junction table — maps permitted languages per region; unique on `(region_fk, language_fk)`; `trg_region_language_update` trigger; migration `b5c6d7e8f9a0`
- `Naip.language_fk` nullable FK → `language.id` — NULL means language unknown; migration `b5c6d7e8f9a0`
- Seed data: 5 languages and 15 regions with their permitted-language mappings per official One Piece TCG rules; migration `b5c6d7e8f9a0`

### Fixed

- `.gitignore`: added `data/` rule so local card images and database files are never tracked
- `init_db()` now runs `alembic upgrade head` instead of `SQLModel.metadata.create_all` + `stamp`; fresh databases are built entirely through migrations, keeping schema and migration history in sync
- Migration `h2i3j4k5l6m7`: expanded to full table-rebuild strategy — all 35 tables recreated with `server_default` timestamps and `AFTER UPDATE` triggers; `PRAGMA foreign_keys` bracketed around the rebuild; downgrade drops triggers cleanly
- Migration `e1a2b3c4d5e6`: table renames now guarded with `_table_exists` check so re-running is idempotent
- Migration `a1b2c3d4e5f7`: adds `is_default` column if missing before adding `is_errata`, preventing column-not-found errors on databases upgraded out of order
- Migration `f1a2b3c4d5e6`: `is_default` dedup and unique-index steps skipped when column is absent; index creation uses `IF NOT EXISTS`
- Migration `b4c5d6e7f8a9`: `naip_format` drop is guarded by a runtime table-existence check, making the migration idempotent on databases that never had the table

### Removed

- `CardBlock` junction model and `card_block` table — replaced by `Card.block_fk` direct FK; migration `a3b4c5d6e7f8`
- `NaipBlock` junction model and `naip_block` table — replaced by `Naip.block_fk` direct FK; migration `a3b4c5d6e7f8`
- `NaipFormat` junction model and `naip_format` table — format legality is card-level only; migration `b4c5d6e7f8a9`

### Added

- `Naip` scalar columns `cardtype_fk`, `power`, `life`, `counter`, `cost` (all nullable) for print-level data parity with `Card`; migration `c3d4e5f6a7b9`
- `NaipColor`, `NaipTribe`, `NaipAttribute`, `NaipKeyword`, `NaipResword`, `NaipBlock`, `NaipFormat` junction tables mirroring their `card_*` counterparts; same migration
- `Set.series` and `Set.ord` nullable columns for grouping sets by release series and ordering within it; migration `b2c3d4e5f6a8`
- `Naip.is_errata` boolean column (default `False`) to flag errata prints; migration `a1b2c3d4e5f7`
- `Naip.sort_order` nullable integer column for explicit display ordering within a set; migration `g1h2i3j4k5l6`
- ER and MR diagrams updated to reflect `is_errata` column on `Naip`
- `Name`, `Effect`, `Trigger`, `Image` dedup tables — shared string values referenced by FK from `Card` and `Naip` to avoid redundancy
- `CardEffectHistory`, `CardTriggerHistory` audit tables with `valid_from` / `valid_to` validity windows
- DB-side timestamp defaults: all tables use `strftime('%Y-%m-%d %H:%M:%f', 'now')` as `server_default` for `created_ts` and `updated_ts`; SQLite `AFTER UPDATE` triggers auto-bump `updated_ts` on every row change; migration `h2i3j4k5l6m7`
- `ingest.py`: name/effect/trigger dedup caches; `Naip` creation with rarity FK; Python 3.12 generic function syntax (`_get_or_create[T]`)
- `ruff` exclusion for `alembic/versions/`; suppressed rules `B008` and `B904`
- `Card` model: `UniqueConstraint("set_fk", "number")` and indexes on `set_fk`, `cardtype_fk`, `name_fk`; migration `d5e6f7a8b9c0`
- `Naip` model: partial unique index `ix_naip_unique_print` on `(card_fk, set_fk, artist_fk, rarity_fk)` where both FKs are non-NULL to deduplicate physical prints; same migration
- `NaipItem` response fields: `rarity_symbol`, `set_code`, `image_fk`, `is_default`, `is_errata`
- `GET /lookups/settypes` endpoint
- Typed Pydantic response models for all lookup endpoints (`LookupResponse`, `LookupWithSymbolResponse`, `SetLookupResponse`)
- `SetResponse` Pydantic model for `GET /sets/` and `GET /sets/{id}`, exposing `series`, `ord`, `desc`, `release_ts`, `type_fk`

### Changed

- Database file relocated from `./optcg.db` to `./data/optcg.db`; images dir relocated from `card_images/` to `data/images/`; static mount renamed `/card_images` → `/images`
- All table names normalised to snake_case: `settype` → `set_type`, `cardtype` → `card_type`, `cardattribute` → `card_attribute`, `cardcolor` → `card_color`, `cardrarity` → `card_rarity`, `cardblock` → `card_block`, `cardformat` → `card_format`, `cardkeywords` → `card_keyword`, `cardreswords` → `card_resword`
- `CardKeywords` / `CardReswords` junction models renamed to `CardKeyword` / `CardResword` for consistency
- `Card` columns `name`, `desc`, `trigger` replaced by FK references `name_fk`, `effect_fk`, `trigger_fk` pointing to the new dedup tables
- Timestamps moved from Python-side `_DateTimeMs` / `_now_ms` to DB-side `server_default` + SQLite triggers; `_ts_col()` replaces the former `_created_col()` / `_updated_col()` helpers; Python `UTC` / `TypeDecorator` imports removed from `models.py`
- `init_db()` now creates `data/` directory before running migrations
- All models updated from `Optional[T]` syntax to `T | None` (Python 3.10+ union style)
- `ingest.py`: removed `CardRarity` direct upsert (rarity now stored on `Naip`); updated card upsert to write `name_fk`, `effect_fk`, `trigger_fk`; removed `Naip` auto-creation during ingest (naip records are managed separately)
- `GET /cards/{id}` enrichment query now joins `set` to populate `NaipItem.set_code` and returns all new `NaipItem` fields
- `routers/lookups.py`: removed generic `LOOKUP_MAP` dict; each endpoint now has an explicit `response_model`

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
