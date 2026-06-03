[//]: # ( ---------------------------------------------------------------------- )
[//]: # (+ Authors: 	Ran# <ran.hash@proton.me> )
[//]: # (+ Created: 	2026/06/02 18:44:20.175705 )
[//]: # (+ Revised: 	2026/06/03 16:48:45.650664 )
[//]: # ( ---------------------------------------------------------------------- )

# Database Schema Reference

This document explains every table and column in the optcg-api database. Tables are grouped into five sections: **lookup**, **core**, **junction (card-level)**, **junction (naip-level)**, and **ban** tables.

---

## Index

- [Common columns](#common-columns)
- [Lookup tables](#lookup-tables)
  - [set\_type](#set_type)
  - [card\_type](#card_type)
  - [artist](#artist)
  - [rarity](#rarity)
  - [print\_variant](#print_variant)
  - [tribe](#tribe)
  - [attribute](#attribute)
  - [color](#color)
  - [block](#block)
  - [format](#format)
  - [keyword](#keyword)
  - [resword](#resword)
  - [language](#language)
  - [region](#region)
  - [region\_language](#region_language)
- [Core tables](#core-tables)
  - [name](#name)
  - [image](#image)
  - [effect](#effect)
  - [trigger](#trigger)
  - [set](#set)
  - [card](#card)
  - [naip](#naip)
  - [naip\_serial](#naip_serial)
  - [card\_effect\_history](#card_effect_history)
  - [card\_trigger\_history](#card_trigger_history)
- [Junction tables — card level](#junction-tables--card-level)
- [Junction tables — naip level](#junction-tables--naip-level)
- [Ban tables](#ban-tables)
  - [card\_ban](#card_ban)
  - [banned\_pair](#banned_pair)

---

## Common columns

Every table carries these three columns:

| Column | Type | Meaning |
|---|---|---|
| `id` | integer PK | Auto-assigned surrogate key. |
| `created_ts` | datetime | Set by the DB on first `INSERT`; never updated. |
| `updated_ts` | datetime | Set by the DB on `INSERT`; refreshed automatically by an `AFTER UPDATE` trigger on every write. |

---

## Lookup tables

These are small, mostly-static reference lists. All have `name` and an optional `desc` (human-readable description). Some also carry a `symbol` — a short, canonical code used in official card notation (e.g. `C` for Common, `R` for Rare).

### `set_type`

What kind of product a set is (Booster Pack, Starter Deck, Premium, Promo, etc.).

| Column | Meaning |
|---|---|
| `name` | Display name of the set type. |
| `desc` | Optional explanation. |

### `card_type`

The card's functional type in the game — Leader, Character, Event, Stage, Don!!.

| Column | Meaning |
|---|---|
| `symbol` | Short official code printed on cards (e.g. `L`, `C`, `E`, `S`). |
| `name` | Full name of the card type. |
| `desc` | Optional explanation. |

### `artist`

A card illustrator. One artist can illustrate many cards and naips.

| Column | Meaning |
|---|---|
| `name` | Artist's credited name. |
| `desc` | Optional biographical note. |

### `rarity`

The abstract rarity tier a card was designed at. This is a property of the **card**, not of any specific print. Defined values: C (Common), UC (Uncommon), R (Rare), SR (Super Rare), SEC (Secret Rare), L (Leader), D (Don!!), P (Promo).

| Column | Meaning |
|---|---|
| `symbol` | Official rarity code (e.g. `C`, `SR`, `SEC`). |
| `name` | Full rarity name. |
| `desc` | Optional explanation. |

Print-level variants (Alt Art, Treasure Rare, etc.) live in `print_variant`, not here.

### `print_variant`

A specific physical presentation variant of a print — Standard, Alt Art, Treasure Rare, Special Rare, Ghost Rare, etc. Variants form a hierarchy: a Ghost Rare (`GR`) is a subtype of Special (`SP`), which is a subtype of Alt Art (`AA`). Traversing `parent_fk` upward gives all inherited types.

| Column | Meaning |
|---|---|
| `symbol` | Short variant code (e.g. `STD`, `AA`, `TR`, `SP`, `GR`). |
| `name` | Full variant name. |
| `desc` | Optional explanation. |
| `parent_fk` | FK to `print_variant.id`. Points to this variant's parent type, or NULL for root variants (`STD`, `AA`). |

Every `naip` row stores the **most specific** variant. To find all Special prints, query the variant and all its descendants via `parent_fk`.

### `tribe`

A creature tribe / type group that appears on a card's type line (e.g. "Straw Hat Crew", "Navy", "Fish-Man"). One card can belong to multiple tribes.

| Column | Meaning |
|---|---|
| `name` | Tribe name as printed. |
| `desc` | Optional note. |

### `attribute`

An elemental or combat attribute (e.g. "Strike", "Slash", "Special"). One card can have multiple attributes.

| Column | Meaning |
|---|---|
| `name` | Attribute name as printed. |
| `desc` | Optional note. |

### `color`

A deck-building color (Red, Blue, Green, Yellow, Purple, Black). One card can be multi-color.

| Column | Meaning |
|---|---|
| `name` | Color name. |
| `desc` | Optional note. |

### `block`

A rules-era block. Cards printed under different block rules may have slightly different mechanics. Blocks also carry an optional logo image.

| Column | Meaning |
|---|---|
| `name` | Block name (e.g. "Block 1"). |
| `desc` | Optional note. |
| `image_fk` | FK to `image.id`. The block's official logo image, if any. |

### `format`

A sanctioned play format (Standard, Block, etc.). Used for legality checks via `card_format` and ban tables.

| Column | Meaning |
|---|---|
| `name` | Format name. |
| `desc` | Optional note. |

### `keyword`

A rules keyword that grants or modifies abilities (e.g. "Rush", "Blocker", "Banish"). One card can have multiple keywords.

| Column | Meaning |
|---|---|
| `name` | Keyword as printed. |
| `desc` | Rules explanation of what this keyword does. |

### `resword`

A restricted word — a term that appears in effect text and carries a specific rules meaning, but is not a formal keyword (e.g. "KO", "Attach", "Return"). Used to tag and search cards by mechanic.

| Column | Meaning |
|---|---|
| `name` | Term as it appears in text. |
| `desc` | Rules explanation. |

### `language`

A language in which sets are officially printed (Japanese, English, Simplified Chinese, etc.).

| Column | Meaning |
|---|---|
| `code` | BCP-47-style language code, unique (e.g. `ja`, `en`, `zh-Hans`). |
| `name` | Display name of the language. |
| `desc` | Optional note. |
| `image_fk` | FK to `image.id`. A flag or icon associated with this language, if any. |

### `region`

A market region (Japan, International, etc.). A region can be officially served in multiple languages via `region_language`.

| Column | Meaning |
|---|---|
| `code` | Short region code, unique (e.g. `JP`, `INT`). |
| `name` | Display name. |
| `desc` | Optional note. |

### `region_language`

Maps which languages are officially used in each region. A region can have multiple languages; a language can appear in multiple regions.

| Column | Meaning |
|---|---|
| `region_fk` | FK to `region.id`. |
| `language_fk` | FK to `language.id`. |

Unique constraint: `(region_fk, language_fk)` — each pairing is recorded once.

---

## Core tables

### `name`

A deduplicated string table for card names. Every distinct name string has exactly one row. `Card.name_fk` and `Naip.name_fk` (for misprints) both point here, so the same name is never stored twice.

| Column | Meaning |
|---|---|
| `name` | The name string, globally unique. |

### `image`

A deduplicated table of image file paths. One row per unique path. Referenced by `Block`, `Language`, `Naip`, and `NaipSerial`.

| Column | Meaning |
|---|---|
| `path` | Relative file path within `data/images/`, globally unique. Card art paths are prefixed `cards/`; language flag paths are prefixed `langs/`. |

### `effect`

A deduplicated table of card effect text blocks. One row per unique effect string. Both `Card` and `Naip` reference this table so the same text is stored once.

| Column | Meaning |
|---|---|
| `effect` | The full effect text as printed, globally unique. |

### `trigger`

A deduplicated table of Trigger effect text blocks (the secondary effect revealed when a card is discarded as a Trigger). Same dedup pattern as `effect`.

| Column | Meaning |
|---|---|
| `trigger` | The full trigger text as printed, globally unique. |

### `set`

A released product (booster set, starter deck, promo set, etc.) in a specific language. The same product released in English and Japanese produces two separate `set` rows.

| Column | Meaning |
|---|---|
| `type_fk` | FK to `set_type.id`. What kind of product this is. |
| `language_fk` | FK to `language.id`. The language of this release. |
| `code` | Official set code (e.g. `OP-01`). Combined with `language_fk`, this is unique. |
| `name` | Full set name. |
| `parent_fk` | FK to `set.id`. Points to the canonical (usually English) counterpart of this set, or the base product for a promo/special set. NULL for root sets. Used for grouping and sorting across languages. |
| `desc` | Optional description. |
| `release_ts` | Official release date. |

### `card`

An **abstract card** — the logical card as designed, independent of any specific print. One `card` row represents the card's canonical identity: its type, name, rarity, stats, and text as officially defined at creation. Physical prints of the card are in `naip`.

| Column | Meaning |
|---|---|
| `set_fk` | FK to `set.id`. The set this card was originally released in. |
| `cardtype_fk` | FK to `card_type.id`. The card's functional type (Leader, Character, etc.). |
| `name_fk` | FK to `name.id`. The card's canonical name. |
| `rarity_fk` | FK to `rarity.id`. The card's abstract rarity tier (C, R, SR, etc.). Nullable — some cards are unclassified. |
| `effect_fk` | FK to `effect.id`. The **current canonical** effect text (may be updated by errata). |
| `trigger_fk` | FK to `trigger.id`. The current canonical trigger text. |
| `block_fk` | FK to `block.id`. Which rules-era block governs this card. |
| `number` | The card's number within its set (e.g. `1` for card `OP01-001`). Unique within a set. |
| `power` | Combat power value. NULL for card types that have no power (Events, Stages). |
| `life` | Life points. Leaders only; NULL otherwise. |
| `counter` | Counter value. NULL for card types that have no counter. |
| `cost` | Play cost. NULL for Leaders and Don!!. |

### `naip`

**N**umber · **A**rtist · **I**mage · **P**rint — a specific physical print of a card. One abstract `card` can have many `naip` rows: the base print in OP-01, an alt-art reprint in OP-07, a treasure rare in a premium set, etc.

`naip` records everything that varies between physical prints: which set the print appeared in, who drew the art, what variant it is, whether it's foil, and what's written on the card face. The `Card` table holds what's canonical; `naip` holds what's printed.

| Column | Meaning |
|---|---|
| `card_fk` | FK to `card.id`. The abstract card this is a print of. |
| `set_fk` | FK to `set.id`. The set this specific print appeared in. May differ from `card.set_fk` for reprints. |
| `artist_fk` | FK to `artist.id`. The illustrator credited on this print. NULL when not known. |
| `print_variant_fk` | FK to `print_variant.id`. The most specific variant of this print (STD, AA, TR, etc.). NOT NULL. |
| `name_fk` | FK to `name.id`. Only set if this print has a name that differs from `card.name_fk` (e.g. a misprint). NULL in normal cases. |
| `image_fk` | FK to `image.id`. The card art image for this print. |
| `effect_fk` | FK to `effect.id`. The effect text **as physically printed** on this card. Set at creation, never updated — even if the card is later errata'd. |
| `trigger_fk` | FK to `trigger.id`. The trigger text as physically printed. Same immutability rule. |
| `cardtype_fk` | FK to `card_type.id`. Overrides `card.cardtype_fk` for this print. NULL means "same as card". |
| `block_fk` | FK to `block.id`. Overrides `card.block_fk` for this print. NULL means "same as card". |
| `language_fk` | FK to `language.id`. The language of this print. NULL if not tracked separately from the set's language. |
| `is_default` | Whether this is the canonical/primary display print for the card. At most one `naip` per card can have `is_default = true`. |
| `is_errata` | Whether this print's effect/trigger text was later officially changed by errata. Set for display purposes; the actual current ruling lives on `Card` via `CardEffectHistory`. |
| `is_foil` | Whether this print has a foil/holo finish. |
| `sort_order` | Optional display ordering among prints of the same card. |
| `serial_max` | Total print run for serialized cards (e.g. `500` for a 1-of-500). NULL means not serialized. |
| `power` | Overrides `card.power` for this print. NULL means "same as card". |
| `life` | Overrides `card.life`. NULL means "same as card". |
| `counter` | Overrides `card.counter`. NULL means "same as card". |
| `cost` | Overrides `card.cost`. NULL means "same as card". |

### `naip_serial`

A known, individually revealed copy of a serialized `naip`. When a player publicly reveals their serial number (e.g. serial #42 of 500), that entry is recorded here.

| Column | Meaning |
|---|---|
| `naip_fk` | FK to `naip.id`. The serialized print this copy belongs to. |
| `serial_number` | The specific serial number on this copy. Must be ≥ 1. Unique per `naip`. |
| `image_fk` | FK to `image.id`. Photo of the card showing the serial number, if available. |

### `card_effect_history`

Tracks the history of a card's effect text over time when official errata change it. The current ruling is always the row with `valid_to IS NULL`. The original printed text is preserved in `naip.effect_fk`.

| Column | Meaning |
|---|---|
| `card_fk` | FK to `card.id`. |
| `effect_fk` | FK to `effect.id`. The effect text that was canonical during this period. |
| `valid_from` | Date this text became the official ruling. |
| `valid_to` | Date this text was superseded. NULL means still current. |

### `card_trigger_history`

Same structure as `card_effect_history`, but for trigger text.

| Column | Meaning |
|---|---|
| `card_fk` | FK to `card.id`. |
| `trigger_fk` | FK to `trigger.id`. |
| `valid_from` | Date this trigger text became official. |
| `valid_to` | Date superseded. NULL means still current. |

---

## Junction tables — card level

These link an abstract `card` to one or more lookup values. Each table has a unique constraint on `(card_fk, <other>_fk)`.

| Table | Links |
|---|---|
| `card_tribe` | `card` ↔ `tribe` — tribes/type groups on the card's type line. |
| `card_attribute` | `card` ↔ `attribute` — elemental/combat attributes. |
| `card_color` | `card` ↔ `color` — deck colors the card belongs to. |
| `card_format` | `card` ↔ `format` — formats where this card is legal. |
| `card_keyword` | `card` ↔ `keyword` — keywords that appear on the card. |
| `card_resword` | `card` ↔ `resword` — restricted terms in the card's effect text. |

All carry only `id`, `created_ts`, `updated_ts`, `card_fk`, and `<other>_fk`.

---

## Junction tables — naip level

Mirror the card-level junction tables but for a specific physical print. Used when a reprint or variant has different attributes from the abstract card (e.g. a promo print that adds a tribe, or an alt art with different coloring).

| Table | Links |
|---|---|
| `naip_color` | `naip` ↔ `color` |
| `naip_tribe` | `naip` ↔ `tribe` |
| `naip_attribute` | `naip` ↔ `attribute` |
| `naip_keyword` | `naip` ↔ `keyword` |
| `naip_resword` | `naip` ↔ `resword` |

Note: there is no `naip_format` — format legality applies to the abstract card, never to a specific print. There is also no `naip_block` — block is a direct FK column on `naip`.

---

## Ban tables

Bans always apply to the abstract `card`. If a card is banned, all its physical prints (`naip` rows) are banned.

### `card_ban`

A card that is banned in a specific format, or in all formats.

| Column | Meaning |
|---|---|
| `card_fk` | FK to `card.id`. The banned card. |
| `format_fk` | FK to `format.id`. The format in which it is banned. NULL means banned in every format globally. |

Unique constraint: `(card_fk, format_fk)`. A partial unique index on `card_fk WHERE format_fk IS NULL` prevents duplicate global-ban rows (SQLite UNIQUE does not treat NULL = NULL).

### `banned_pair`

Two cards that cannot coexist in the same deck, optionally scoped to a format. The pair is always stored in ascending ID order (`card_a_fk < card_b_fk`) to avoid duplicates.

| Column | Meaning |
|---|---|
| `card_a_fk` | FK to `card.id`. Lower-ID card of the pair. |
| `card_b_fk` | FK to `card.id`. Higher-ID card of the pair. |
| `format_fk` | FK to `format.id`. Format scope. NULL means banned in all formats. |

Unique constraint: `(card_a_fk, card_b_fk, format_fk)`. Partial index on `(card_a_fk, card_b_fk) WHERE format_fk IS NULL` guards the global case. `CHECK (card_a_fk < card_b_fk)` enforces canonical ordering.
