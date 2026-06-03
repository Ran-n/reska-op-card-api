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

## `rarity` — migration `0001_initial`, updated by `0003_print_variant`

Abstract rarity tiers as designed on the card. Print-level finishes (Alt Art, Treasure Rare, etc.) live in `print_variant`, not here.

| symbol | name |
|--------|------|
| C | Common |
| UC | Uncommon |
| R | Rare |
| SR | Super Rare |
| SEC | Secret Rare |
| L | Leader |
| P | Promo |
| D | DON!! |

Migration `0003_print_variant` stripped the `is_type` and `is_base` columns and removed all print-level rows (TR, AA, SP, MR, FA, AU, AG, AUD, EMR, PTR) and NFD from this table.

---

## `print_variant` — migration `0003_print_variant`

Physical presentation variants of a print. Variants form a hierarchy via `parent_fk`; traversing upward gives all inherited types.

| symbol | name | parent |
|--------|------|--------|
| STD | Standard | — |
| AA | Alternate Art | — |
| TR | Treasure Rare | AA |
| SP | Special Rare | AA |
| MR | Manga Rare | AA |
| FA | Full Art | AA |
| AUD | Gold DON!! Rare | AA |
| PTR | Pattern Rare | AA |
| MTR | Metallic Rare | AA |
| GR | Ghost Rare | SP |
| EMR | Event Manga Rare | MR |
| RMR | Red Manga Rare | MR |
| AU | Gold Rare | MTR |
| AG | Silver Rare | MTR |

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
