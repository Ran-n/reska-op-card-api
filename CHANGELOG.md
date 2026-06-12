[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/05/12 16:27:41 )
[//]: # (+ Revised: 	2026/06/12 17:19:23.164379 )
[//]: # ( ---------------------------------------------------------------------- )

# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added

- `routers/_common.py` shared module: `LookupItem`, `ImageUrlPayload`, `_resolve_text`, `_upsert_text_fk` — eliminates identical copy-paste between `cards.py` and `naips.py`
- `CardWrite.number` validates `ge=1`; `CardWrite` and `NaipWrite` stats (`power`, `life`, `counter`, `cost`) validate `ge=0` — rejects negative card numbers and stats at the API boundary
- FK indexes on `set` (`type_fk`, `language_fk`), `card` (`effect_fk`, `trigger_fk`, `block_fk`), `naip` (`card_fk`, `set_fk`, `artist_fk`, `language_fk`, `cardtype_fk`, `block_fk`), `print_variant` (`parent_fk`), `card_effect_history` (`card_fk`, `effect_fk`), and `card_trigger_history` (`card_fk`, `trigger_fk`); migration `0006_add_missing_indexes`
- `CardDetail.naips[].image_path` and `NaipDetail.image_path` — resolved `image.path` for the print's `image_fk`
- `CardListItem` response fields: `colors` (comma-joined `color.name` list), `rarity_symbol`, `image_path` (from the card's default `naip`)
- `Language.image_fk` seeded from `data/languages/<code>.svg` on `alembic upgrade head`; flag images copied to `data/images/langs/`; migration `0005_language_images`
- `PrintVariant` table with `parent_fk` self-reference encoding a hierarchy of print-level variants (STD, AA, TR, SP, GR, MR, EMR, RMR, FA, AUD, PTR, MTR, AU, AG); `trg_print_variant_update` trigger; migration `0003_print_variant`
- `Card.rarity_fk` nullable FK → `rarity.id` — the canonical base rarity the card was designed as (C, UC, R, SR, SEC, L, D, P), independent of any specific print; `ix_card_rarity_fk` index; migration `0003_print_variant`
- `Naip.print_variant_fk` NOT NULL FK → `print_variant.id` — the specific print variant of this physical print (STD for standard prints, AA/TR/SP/etc. for special prints); `ix_naip_print_variant_fk` index; migration `0003_print_variant`
- `ix_naip_unique_print` partial unique index now covers `(card_fk, set_fk, artist_fk, print_variant_fk, is_foil)` where `artist_fk IS NOT NULL`; migration `0003_print_variant`
- `CardDetail` response fields: `rarity_fk`, `rarity_name`, `rarity_symbol` (card-level canonical rarity)
- `NaipItem` response fields: `print_variant_name`, `print_variant_symbol`, `is_foil`
- `NaipDetail` response fields: `print_variant_fk`, `print_variant_name`, `print_variant_symbol`
- `CardWrite` and `NaipWrite` accept `rarity_fk` / `print_variant_fk` respectively
- `ingest.py` now sets `card.rarity_fk` from scraped rarity symbol; print_variant symbols reported by the site are recognised and skipped (no naip rows yet)
- `GET /lookups/print-variants` endpoint returning all `PrintVariant` rows with `symbol`, `name`, `desc`, `parent_fk`
- `Set.parent_fk` nullable FK → `set.id` self-referential — links a set to its parent (e.g. starter deck → booster set of the same series); `ix_set_parent_fk` index; migration `0004_set_parent_fk`
- `docs/schema.md` — tabular database schema reference covering all tables, columns, constraints, and triggers

### Changed

- `_images.py`: `save_image_bytes` + `upsert_image_row` merged into `save_image(raw, suffix, session) → Image`; DB row is checked before writing the file, avoiding wasted I/O on duplicate uploads
- `routers/cards.py`: `list_cards` uses a dedicated `filter_params` dict for the COUNT query, eliminating a potential param-name collision with `limit`/`offset`
- `routers/naips.py`: `delete_naip` collects all serial image FKs upfront and performs a single `session.flush()` before orphan cleanup (was one flush per serial)
- `data/images/` reorganised into `cards/` and `langs/` subdirectories; all `image.path` values now prefixed with `cards/` (card art) or `langs/` (language flags); migration `0005_language_images`
- `Naip.rarity_fk` removed — rarity is now exclusively on `Card.rarity_fk`; print-level variant is `Naip.print_variant_fk`
- `Rarity` table: `is_type` and `is_base` columns removed — card-type classification lives on `card_type`, print-variant classification lives on `print_variant`; `NFD` (Non-Foil DON!!) row removed (foil distinction is `Naip.is_foil`)
- `CardDetail.rarities` list removed — replaced by single `rarity_fk`/`rarity_name`/`rarity_symbol` fields on the card itself
- `Set.series` (str) and `Set.ord` (int) replaced by `Set.parent_fk` self-referential FK; `SetResponse` updated accordingly; migration `0004_set_parent_fk`
- `doc/` directory renamed to `docs/`

### Previous entries

- `_images.py` shared image utility module: `save_image_bytes` (BLAKE3 content-addressed filenames), `upsert_image_row`, `cleanup_orphaned_image`, `replace_naip_image`
- `routers/naips.py`: full CRUD (`GET /naips/{id}`, `POST /naips/`, `PUT /naips/{id}`, `DELETE /naips/{id}`) with enriched `NaipDetail` response, per-naip junction sync for colors/tribes/attrs/keywords/reswords, and orphaned-image cleanup on delete
- `POST /naips/{id}/image-url` and `POST /naips/{id}/image` image upload endpoints on the naips router
- `GET /lookups/languages` and `GET /lookups/regions` endpoints
- `blake3 >=1.0.8` runtime dependency
- `CardWrite.one_block_max` validator — rejects `blocks` lists longer than 1
- `Naip.serial_max` nullable integer column — the total print run size for a serialized naip (e.g. 500 for a 1/500 card); migration `0001_initial`
- `NaipSerial` table — records each known revealed copy of a serialized naip (`naip_fk`, `serial_number`, `image_fk`); unique on `(naip_fk, serial_number)` with a `CHECK serial_number >= 1` constraint; migration `0001_initial`
- `trg_naip_serial_update` SQLite trigger to auto-bump `updated_ts` on `naip_serial` row changes; migration `0001_initial`
- `Block.image_fk` nullable FK → `image.id`; migration `0001_initial`
- `Card.block_fk` nullable FK → `block.id` (replaces `card_block` junction); migration `0001_initial`
- `Naip.block_fk` nullable FK → `block.id` (replaces `naip_block` junction); migration `0001_initial`
- `CardBan` table — per-card ban scoped to a format or all formats when `format_fk IS NULL`; NULL-safe partial unique index prevents duplicate global bans; `trg_card_ban_update` trigger; migration `0001_initial`
- `BannedPair` table — two-card combo ban with `ck_banned_pair_ordered` constraint (`card_a_fk < card_b_fk`) and NULL-safe partial unique index for global pair bans; `trg_banned_pair_update` trigger; migration `0001_initial`
- `trg_block_update` SQLite trigger to auto-bump `updated_ts` on `block` row changes; migration `0001_initial`
- `trg_naip_serial_check_max_insert` / `trg_naip_serial_check_max_update` BEFORE triggers enforce `serial_number ≤ serial_max` on `naip_serial` rows (SQLite `CHECK` cannot reference other tables); migration `0001_initial`
- `Language` table — BCP-47 language codes (`ja`, `en`, `fr`, `zh-Hans`, `ko`), optional `image_fk`; `trg_language_update` trigger; migration `0001_initial`
- `Region` table — UN M.49 region codes for 15 tournament regions; `trg_region_update` trigger; migration `0001_initial`
- `RegionLanguage` junction table — maps permitted languages per region; unique on `(region_fk, language_fk)`; `trg_region_language_update` trigger; migration `0001_initial`
- `Naip.language_fk` nullable FK → `language.id` — NULL means language unknown; migration `0001_initial`
- `Set.language_fk` NOT NULL FK → `language.id` — every set is issued in a specific language; unique constraint on `(code, language_fk)` replaces the former `code`-only unique; migration `0001_initial`
- `Rarity.is_type` and `Rarity.is_base` boolean columns to distinguish card-type pseudo-rarities (L, D) from base pull-weight rarities and print-level finishes; migration `0001_initial`
- Seed data: 5 languages and 15 regions with their permitted-language mappings per official One Piece TCG rules; migration `0001_initial`
- `Naip` scalar columns `cardtype_fk`, `power`, `life`, `counter`, `cost` (all nullable) for print-level data parity with `Card`; migration `0001_initial`
- `NaipColor`, `NaipTribe`, `NaipAttribute`, `NaipKeyword`, `NaipResword` junction tables mirroring their `card_*` counterparts; migration `0001_initial`
- `Set.series` and `Set.ord` nullable columns for grouping sets by release series and ordering within it; migration `0001_initial`
- `Naip.is_errata` boolean column (default `False`) to flag errata prints; migration `0001_initial`
- `Naip.sort_order` nullable integer column for explicit display ordering within a set; migration `0001_initial`
- `Name`, `Effect`, `Trigger`, `Image` dedup tables — shared string values referenced by FK from `Card` and `Naip` to avoid redundancy; migration `0001_initial`
- `CardEffectHistory`, `CardTriggerHistory` audit tables with `valid_from` / `valid_to` validity windows; migration `0001_initial`
- DB-side timestamp defaults: all tables use `strftime('%Y-%m-%d %H:%M:%f', 'now')` as `server_default` for `created_ts` and `updated_ts`; SQLite `AFTER UPDATE` triggers auto-bump `updated_ts` on every row change; migration `0001_initial`
- `Card` model: `UniqueConstraint("set_fk", "number")` and indexes on `set_fk`, `cardtype_fk`, `name_fk`; migration `0001_initial`
- `Naip.is_foil` boolean column (default `False`) to distinguish foil from non-foil prints; migration `0002_naip_is_foil`
- `Naip` model: partial unique index `ix_naip_unique_print` on `(card_fk, set_fk, artist_fk, rarity_fk, is_foil)` where both FKs are non-NULL to deduplicate physical prints; migration `0001_initial`
- `NaipItem` response fields: `rarity_symbol`, `set_code`, `image_fk`, `is_default`, `is_errata`
- `GET /lookups/settypes` endpoint
- Typed Pydantic response models for all lookup endpoints (`LookupResponse`, `LookupWithSymbolResponse`, `SetLookupResponse`)
- `SetResponse` Pydantic model for `GET /sets/` and `GET /sets/{id}`, exposing `series`, `ord`, `desc`, `release_ts`, `type_fk`

### Fixed

- `ingest.py`: `except ValueError, TypeError:` (Python 2 syntax, `SyntaxError` in Python 3) corrected to `except (ValueError, TypeError):`
- `ingest.py`: `_card_number()` returning `None` (regex miss on non-standard card IDs) now logs a warning and skips the card instead of writing `None` to the non-nullable `Card.number` and hitting a DB constraint error
- `ingest.py`: `_persist()` now uses `.first()` instead of `.one()` for the `en` language lookup, with a descriptive `RuntimeError` if the seed row is absent
- `_images.py`: `cleanup_orphaned_image` and `replace_naip_image` use `is None` guards instead of falsy `not` checks, correctly handling any integer FK value
- `routers/naips.py`: `create_naip` and `update_naip` catch `IntegrityError` on commit and return 409 instead of 500 when the `ix_naip_one_default_per_card` unique index is violated under concurrent writes
- `.gitignore`: added `data/` rule so local card images and database files are never tracked
- `init_db()` now runs `alembic upgrade head` instead of `SQLModel.metadata.create_all` + `stamp`; fresh databases are built entirely through migrations, keeping schema and migration history in sync
- `ingest.py`: card types and rarities now loaded from DB seed at startup; unknown symbols raise `RuntimeError` instead of silently creating unsanctioned rows; `L` and `D` rarity symbols skipped as they are card-type pseudo-rarities
- `ingest.py`: set lookup and upsert now filter and assign `language_fk` using the `en` language row; `Set` unique lookup uses `(code, language_fk)` instead of `code` alone

### Changed

- Image files now stored with BLAKE3-derived hex filenames (content-addressed) instead of `{card_id}{suffix}`; deduplicates identical art across naips automatically
- `routers/cards.py` image upload refactored to delegate to `_images` helpers; `urllib.request` replaced by `httpx.AsyncClient`; orphaned images cleaned up on card delete
- All 28 incremental migrations squashed into single `0001_initial` migration covering the full schema, all triggers, and all seed data; migration history restarted
- `Set.block_fk` removed; sets are no longer linked to blocks directly
- Database file relocated from `./optcg.db` to `./data/optcg.db`; images dir relocated from `card_images/` to `data/images/`; static mount renamed `/card_images` → `/images`
- All table names normalised to snake_case: `settype` → `set_type`, `cardtype` → `card_type`, `cardattribute` → `card_attribute`, `cardcolor` → `card_color`, `cardrarity` → `card_rarity`, `cardblock` → `card_block`, `cardformat` → `card_format`, `cardkeywords` → `card_keyword`, `cardreswords` → `card_resword`
- `CardKeywords` / `CardReswords` junction models renamed to `CardKeyword` / `CardResword` for consistency
- `Card` columns `name`, `desc`, `trigger` replaced by FK references `name_fk`, `effect_fk`, `trigger_fk` pointing to the new dedup tables
- Timestamps moved from Python-side `_DateTimeMs` / `_now_ms` to DB-side `server_default` + SQLite triggers; `_ts_col()` replaces the former `_created_col()` / `_updated_col()` helpers; Python `UTC` / `TypeDecorator` imports removed from `models.py`
- `init_db()` now creates `data/` directory before running migrations
- All models updated from `Optional[T]` syntax to `T | None` (Python 3.10+ union style)
- `ingest.py`: `_CARD_TYPE_MAP` keys uppercased to match site HTML; removed `CardRarity` direct upsert (rarity now stored on `Naip`); updated card upsert to write `name_fk`, `effect_fk`, `trigger_fk`; removed `Naip` auto-creation during ingest (naip records are managed separately)
- `GET /cards/{id}` enrichment query now joins `set` to populate `NaipItem.set_code` and returns all new `NaipItem` fields
- `routers/lookups.py`: removed generic `LOOKUP_MAP` dict; each endpoint now has an explicit `response_model`
- `routers/cards.py`: block enrichment now reads `card.block_fk` direct FK instead of joining `card_block` junction; `_sync_junctions` receives the `Card` object instead of `card_id` to support direct FK writes

### Removed

- `FD` (Foil DON!! Rare) rarity seed row — foil status is now tracked via `Naip.is_foil`; migration `0002_naip_is_foil`
- `CardRarity` junction model and `card_rarity` table — rarities are sourced from `Naip.rarity_fk` directly; `GET /cards/{id}` rarity enrichment now joins via `naip`; migration `0001_initial`
- `CardBlock` junction model and `card_block` table — replaced by `Card.block_fk` direct FK; migration `0001_initial`
- `NaipBlock` junction model and `naip_block` table — replaced by `Naip.block_fk` direct FK; migration `0001_initial`
- `NaipFormat` junction model and `naip_format` table — format legality is card-level only; migration `0001_initial`
- `Set.block_fk` column — sets are no longer linked to blocks

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
