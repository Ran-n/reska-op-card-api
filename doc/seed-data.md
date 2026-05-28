# Seed Data

All rows listed here are inserted by Alembic migrations. Do not remove them from the database; update the corresponding migration and add a new migration to rename/remove rows if a value needs to change.

---

## `card_type` — migration `0001_initial`

| symbol | name |
|--------|------|
| LEADER | Leader |
| CHARACTER | Character |
| EVENT | Event |
| STAGE | Stage |
| DON | DON!! |

---

## `rarity` — migration `0001_initial`

The `rarity` table has two boolean classifier columns:

- `is_type` (added `e8f9a0b1c2d3`) — row represents a card type that also appears in the `card_type` table (L = Leader, D = DON!!); these overlap in name with card types rather than describing a distinct rarity tier.
- `is_base` (added `a1b2c3d4e5f8`) — row is a base rarity that describes a card's pull weight. Rows where `is_base = FALSE` are print-level finishes (TR, AA, PTR, etc.) that apply to a specific naip rather than the card itself.

| symbol | name | is_type | is_base |
|--------|------|---------|---------|
| C | Common | false | **true** |
| UC | Uncommon | false | **true** |
| R | Rare | false | **true** |
| SR | Super Rare | false | **true** |
| SEC | Secret Rare | false | **true** |
| L | Leader | **true** | **true** |
| P | Promo | false | **true** |
| D | DON!! | **true** | **true** |
| NFD | Non-Foil DON!! | false | **true** |
| TR | Treasure Rare | false | false |
| AA | Alternate Art | false | false |
| SP | Special Rare | false | false |
| MR | Manga Rare | false | false |
| FA | Full Art | false | false |
| AU | Gold Rare | false | false |
| AG | Silver Rare | false | false |
| AUD | Gold DON!! Rare | false | false |
| EMR | Event Manga Rare | false | false |
| PTR | Pattern Rare | false | false |
| FD | Foil DON!! Rare | false | false |

---

## `language` — migration `0001_initial`

Uses BCP-47 codes.

| code | name |
|------|------|
| ja | Japanese |
| en | English |
| fr | French |
| zh-Hans | Simplified Chinese |
| ko | Korean |

---

## `region` — migration `0001_initial`

Uses UN M.49 numeric codes.

| code | name |
|------|------|
| 392 | Japan |
| 003 | North America |
| 150 | Europe |
| 419 | Latin America and the Caribbean |
| 009 | Oceania |
| 145 | Western Asia |
| 156 | China (Mainland) |
| 410 | Korea (Republic of) |
| 702 | Singapore |
| 458 | Malaysia |
| 360 | Indonesia |
| 608 | Philippines |
| 158 | Taiwan |
| 764 | Thailand |
| 344 | Hong Kong S.A.R. |

---

## `region_language` — migration `0001_initial`

Maps regions to the languages used in official OPTCG releases for that region.

| region | language |
|--------|----------|
| Japan (392) | Japanese |
| North America (003) | English |
| Europe (150) | English |
| Europe (150) | French |
| Latin America (419) | English |
| Oceania (009) | English |
| Western Asia (145) | English |
| China Mainland (156) | Simplified Chinese |
| Korea (410) | Korean |
| Singapore (702) | English |
| Singapore (702) | Japanese |
| Malaysia (458) | English |
| Malaysia (458) | Japanese |
| Indonesia (360) | English |
| Indonesia (360) | Japanese |
| Philippines (608) | English |
| Philippines (608) | Japanese |
| Taiwan (158) | Japanese |
| Taiwan (158) | English |
| Thailand (764) | Japanese |
| Thailand (764) | English |
| Hong Kong (344) | Japanese |
| Hong Kong (344) | English |
