# Backlog

## Index

| # | Item | Section |
|---|---|---|
| 1 | Add colour and rarity filters to `GET /cards/` | [Cards router](#cards-router) |
| 2 | Add `Promo` set type seed row | [Data](#data) |

---

## Data

### 2 — Add `Promo` set type seed row

Reska's Collection tab has Promo and Other sub-tabs. `Promo` and `Other` rows need to exist in the `set_type` table.

---

## Cards router

### 1 — Add colour and rarity filters to `GET /cards/`

`GET /cards/` currently accepts `name`, `set_id`, and `cardtype_id` only.
Reska's Browse tab needs to filter by colour and rarity as well.

**Required query params to add:**
- `color_id: int | None` — filter by colour (via `card_color` junction)
- `rarity_id: int | None` — filter by rarity (via `card.rarity_fk`)

Both should be optional and composable with existing filters.

---
