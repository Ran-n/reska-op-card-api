#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/06/02 18:44:11.849285
"""

from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, SQLModel

_TS_SERVER_DEFAULT = sa.text("(strftime('%Y-%m-%d %H:%M:%f', 'now'))")


def _ts_col() -> sa.Column:
    return sa.Column(sa.String, nullable=True, server_default=_TS_SERVER_DEFAULT)


# ── Lookup tables ────────────────────────────────────────────────────────────


class SetType(SQLModel, table=True):
    __tablename__ = "set_type"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None


class CardType(SQLModel, table=True):
    __tablename__ = "card_type"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    symbol: str
    name: str
    desc: str | None = None


class Artist(SQLModel, table=True):
    __tablename__ = "artist"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None


class Rarity(SQLModel, table=True):
    __tablename__ = "rarity"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    symbol: str
    name: str
    desc: str | None = None


class PrintVariant(SQLModel, table=True):
    __tablename__ = "print_variant"
    __table_args__ = (Index("ix_print_variant_parent_fk", "parent_fk"),)

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    symbol: str
    name: str
    desc: str | None = None
    parent_fk: int | None = Field(default=None, foreign_key="print_variant.id")


class Tribe(SQLModel, table=True):
    __tablename__ = "tribe"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None


class Attribute(SQLModel, table=True):
    __tablename__ = "attribute"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None


class Color(SQLModel, table=True):
    __tablename__ = "color"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None


class Block(SQLModel, table=True):
    __tablename__ = "block"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None
    image_fk: int | None = Field(default=None, foreign_key="image.id")


class Format(SQLModel, table=True):
    __tablename__ = "format"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None


class Keyword(SQLModel, table=True):
    __tablename__ = "keyword"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None


class Resword(SQLModel, table=True):
    __tablename__ = "resword"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str
    desc: str | None = None


class Language(SQLModel, table=True):
    __tablename__ = "language"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    code: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))
    name: str
    desc: str | None = None
    image_fk: int | None = Field(default=None, foreign_key="image.id")


class Region(SQLModel, table=True):
    __tablename__ = "region"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    code: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))
    name: str
    desc: str | None = None


class RegionLanguage(SQLModel, table=True):
    __tablename__ = "region_language"
    __table_args__ = (
        UniqueConstraint("region_fk", "language_fk"),
        Index("ix_region_language_region_fk", "region_fk"),
        Index("ix_region_language_language_fk", "language_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    region_fk: int = Field(foreign_key="region.id")
    language_fk: int = Field(foreign_key="language.id")


# ── Core tables ──────────────────────────────────────────────────────────────


class Set(SQLModel, table=True):
    __tablename__ = "set"
    __table_args__ = (
        UniqueConstraint("code", "language_fk"),
        Index("ix_set_type_fk", "type_fk"),
        Index("ix_set_language_fk", "language_fk"),
        Index("ix_set_parent_fk", "parent_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    type_fk: int | None = Field(default=None, foreign_key="set_type.id")
    language_fk: int = Field(foreign_key="language.id")
    code: str = Field(sa_column=sa.Column(sa.String, nullable=False))
    name: str
    parent_fk: int | None = Field(default=None, foreign_key="set.id")
    desc: str | None = None
    release_ts: date | None = None


class Name(SQLModel, table=True):
    __tablename__ = "name"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    name: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))


class Image(SQLModel, table=True):
    __tablename__ = "image"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    path: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))


class Effect(SQLModel, table=True):
    __tablename__ = "effect"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    effect: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))


class Trigger(SQLModel, table=True):
    __tablename__ = "trigger"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    trigger: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))


class Card(SQLModel, table=True):
    __tablename__ = "card"
    __table_args__ = (
        UniqueConstraint("set_fk", "number"),
        Index("ix_card_set_fk", "set_fk"),
        Index("ix_card_cardtype_fk", "cardtype_fk"),
        Index("ix_card_name_fk", "name_fk"),
        Index("ix_card_rarity_fk", "rarity_fk"),
        Index("ix_card_effect_fk", "effect_fk"),
        Index("ix_card_trigger_fk", "trigger_fk"),
        Index("ix_card_block_fk", "block_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    set_fk: int = Field(foreign_key="set.id")
    cardtype_fk: int = Field(foreign_key="card_type.id")
    name_fk: int = Field(foreign_key="name.id")
    rarity_fk: int | None = Field(default=None, foreign_key="rarity.id")
    effect_fk: int | None = Field(default=None, foreign_key="effect.id")
    trigger_fk: int | None = Field(default=None, foreign_key="trigger.id")
    block_fk: int | None = Field(default=None, foreign_key="block.id")
    number: int
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None


class Naip(SQLModel, table=True):
    """A specific physical print of a card (card + set + artist + print_variant)."""

    __tablename__ = "naip"
    __table_args__ = (
        # at most one default print per card
        Index("ix_naip_one_default_per_card", "card_fk", unique=True, sqlite_where=sa.text("is_default = 1")),
        # deduplicate physical prints (artist_fk NULL excluded — NULL != NULL in SQLite UNIQUE)
        Index(
            "ix_naip_unique_print",
            "card_fk",
            "set_fk",
            "artist_fk",
            "print_variant_fk",
            "is_foil",
            unique=True,
            sqlite_where=sa.text("artist_fk IS NOT NULL"),
        ),
        Index("ix_naip_card_fk", "card_fk"),
        Index("ix_naip_set_fk", "set_fk"),
        Index("ix_naip_print_variant_fk", "print_variant_fk"),
        Index("ix_naip_artist_fk", "artist_fk"),
        Index("ix_naip_language_fk", "language_fk"),
        Index("ix_naip_cardtype_fk", "cardtype_fk"),
        Index("ix_naip_block_fk", "block_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    set_fk: int = Field(foreign_key="set.id")
    artist_fk: int | None = Field(default=None, foreign_key="artist.id")
    print_variant_fk: int = Field(foreign_key="print_variant.id")
    name_fk: int | None = Field(default=None, foreign_key="name.id")
    image_fk: int | None = Field(default=None, foreign_key="image.id")
    effect_fk: int | None = Field(default=None, foreign_key="effect.id")
    trigger_fk: int | None = Field(default=None, foreign_key="trigger.id")
    is_default: bool = Field(default=False)
    is_errata: bool = Field(default=False)
    is_foil: bool = Field(default=False)
    sort_order: int | None = Field(default=None)
    serial_max: int | None = Field(default=None)
    cardtype_fk: int | None = Field(default=None, foreign_key="card_type.id")
    block_fk: int | None = Field(default=None, foreign_key="block.id")
    language_fk: int | None = Field(default=None, foreign_key="language.id")
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None


class NaipSerial(SQLModel, table=True):
    """A known revealed copy of a serialized naip."""

    __tablename__ = "naip_serial"
    __table_args__ = (
        UniqueConstraint("naip_fk", "serial_number"),
        Index("ix_naip_serial_naip_fk", "naip_fk"),
        sa.CheckConstraint("serial_number >= 1", name="ck_naip_serial_number_positive"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    naip_fk: int = Field(foreign_key="naip.id")
    serial_number: int
    image_fk: int | None = Field(default=None, foreign_key="image.id")


class CardEffectHistory(SQLModel, table=True):
    __tablename__ = "card_effect_history"
    __table_args__ = (
        Index("ix_card_effect_history_card_fk", "card_fk"),
        Index("ix_card_effect_history_effect_fk", "effect_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    effect_fk: int = Field(foreign_key="effect.id")
    valid_from: date
    valid_to: date | None = None


class CardTriggerHistory(SQLModel, table=True):
    __tablename__ = "card_trigger_history"
    __table_args__ = (
        Index("ix_card_trigger_history_card_fk", "card_fk"),
        Index("ix_card_trigger_history_trigger_fk", "trigger_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    trigger_fk: int = Field(foreign_key="trigger.id")
    valid_from: date
    valid_to: date | None = None


# ── Junction tables ──────────────────────────────────────────────────────────


class CardTribe(SQLModel, table=True):
    __tablename__ = "card_tribe"
    __table_args__ = (
        UniqueConstraint("card_fk", "tribe_fk"),
        Index("ix_card_tribe_card_fk", "card_fk"),
        Index("ix_card_tribe_tribe_fk", "tribe_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    tribe_fk: int = Field(foreign_key="tribe.id")


class CardAttribute(SQLModel, table=True):
    __tablename__ = "card_attribute"
    __table_args__ = (
        UniqueConstraint("card_fk", "attribute_fk"),
        Index("ix_card_attribute_card_fk", "card_fk"),
        Index("ix_card_attribute_attribute_fk", "attribute_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    attribute_fk: int = Field(foreign_key="attribute.id")


class CardColor(SQLModel, table=True):
    __tablename__ = "card_color"
    __table_args__ = (
        UniqueConstraint("card_fk", "color_fk"),
        Index("ix_card_color_card_fk", "card_fk"),
        Index("ix_card_color_color_fk", "color_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    color_fk: int = Field(foreign_key="color.id")


class CardFormat(SQLModel, table=True):
    __tablename__ = "card_format"
    __table_args__ = (
        UniqueConstraint("card_fk", "format_fk"),
        Index("ix_card_format_card_fk", "card_fk"),
        Index("ix_card_format_format_fk", "format_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    format_fk: int = Field(foreign_key="format.id")


class CardKeyword(SQLModel, table=True):
    __tablename__ = "card_keyword"
    __table_args__ = (
        UniqueConstraint("card_fk", "keyword_fk"),
        Index("ix_card_keyword_card_fk", "card_fk"),
        Index("ix_card_keyword_keyword_fk", "keyword_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    keyword_fk: int = Field(foreign_key="keyword.id")


class CardResword(SQLModel, table=True):
    __tablename__ = "card_resword"
    __table_args__ = (
        UniqueConstraint("card_fk", "resword_fk"),
        Index("ix_card_resword_card_fk", "card_fk"),
        Index("ix_card_resword_resword_fk", "resword_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    resword_fk: int = Field(foreign_key="resword.id")


# ── Naip junction tables ─────────────────────────────────────────────────────


class NaipColor(SQLModel, table=True):
    __tablename__ = "naip_color"
    __table_args__ = (
        UniqueConstraint("naip_fk", "color_fk"),
        Index("ix_naip_color_naip_fk", "naip_fk"),
        Index("ix_naip_color_color_fk", "color_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    naip_fk: int = Field(foreign_key="naip.id")
    color_fk: int = Field(foreign_key="color.id")


class NaipTribe(SQLModel, table=True):
    __tablename__ = "naip_tribe"
    __table_args__ = (
        UniqueConstraint("naip_fk", "tribe_fk"),
        Index("ix_naip_tribe_naip_fk", "naip_fk"),
        Index("ix_naip_tribe_tribe_fk", "tribe_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    naip_fk: int = Field(foreign_key="naip.id")
    tribe_fk: int = Field(foreign_key="tribe.id")


class NaipAttribute(SQLModel, table=True):
    __tablename__ = "naip_attribute"
    __table_args__ = (
        UniqueConstraint("naip_fk", "attribute_fk"),
        Index("ix_naip_attribute_naip_fk", "naip_fk"),
        Index("ix_naip_attribute_attribute_fk", "attribute_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    naip_fk: int = Field(foreign_key="naip.id")
    attribute_fk: int = Field(foreign_key="attribute.id")


class NaipKeyword(SQLModel, table=True):
    __tablename__ = "naip_keyword"
    __table_args__ = (
        UniqueConstraint("naip_fk", "keyword_fk"),
        Index("ix_naip_keyword_naip_fk", "naip_fk"),
        Index("ix_naip_keyword_keyword_fk", "keyword_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    naip_fk: int = Field(foreign_key="naip.id")
    keyword_fk: int = Field(foreign_key="keyword.id")


class NaipResword(SQLModel, table=True):
    __tablename__ = "naip_resword"
    __table_args__ = (
        UniqueConstraint("naip_fk", "resword_fk"),
        Index("ix_naip_resword_naip_fk", "naip_fk"),
        Index("ix_naip_resword_resword_fk", "resword_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    naip_fk: int = Field(foreign_key="naip.id")
    resword_fk: int = Field(foreign_key="resword.id")


# ── Ban tables ───────────────────────────────────────────────────────────────


class CardBan(SQLModel, table=True):
    """A card banned in a specific format, or all formats when format_fk is NULL."""

    __tablename__ = "card_ban"
    __table_args__ = (
        UniqueConstraint("card_fk", "format_fk"),
        # NULL-safe guard: only one global ban row per card
        Index("ix_card_ban_global_unique", "card_fk", unique=True, sqlite_where=sa.text("format_fk IS NULL")),
        Index("ix_card_ban_card_fk", "card_fk"),
        Index("ix_card_ban_format_fk", "format_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_fk: int = Field(foreign_key="card.id")
    format_fk: int | None = Field(default=None, foreign_key="format.id")


class BannedPair(SQLModel, table=True):
    """Two cards that cannot coexist in the same deck, optionally scoped to a format."""

    __tablename__ = "banned_pair"
    __table_args__ = (
        UniqueConstraint("card_a_fk", "card_b_fk", "format_fk"),
        # NULL-safe guard: only one global ban row per pair
        Index(
            "ix_banned_pair_global_unique",
            "card_a_fk",
            "card_b_fk",
            unique=True,
            sqlite_where=sa.text("format_fk IS NULL"),
        ),
        Index("ix_banned_pair_card_a_fk", "card_a_fk"),
        Index("ix_banned_pair_card_b_fk", "card_b_fk"),
        Index("ix_banned_pair_format_fk", "format_fk"),
        sa.CheckConstraint("card_a_fk < card_b_fk", name="ck_banned_pair_ordered"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_ts_col())
    card_a_fk: int = Field(foreign_key="card.id")
    card_b_fk: int = Field(foreign_key="card.id")
    format_fk: int | None = Field(default=None, foreign_key="format.id")
