#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/05/18 09:30:43.993928
"""

from datetime import UTC, date, datetime

import sqlalchemy as sa
from sqlalchemy import Index, UniqueConstraint
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, SQLModel


class _DateTimeMs(TypeDecorator):
    """Stores datetime as 'YYYY-MM-DD HH:MM:SS.mmm' (3 decimal places)."""

    impl = sa.String
    cache_ok = True

    def process_bind_param(self, value, _dialect):
        if value is None:
            return None
        return value.strftime("%Y-%m-%d %H:%M:%S.") + f"{value.microsecond // 1000:03d}"

    def process_result_value(self, value, _dialect):
        if value is None:
            return None
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f")


def _now_ms() -> datetime:
    dt = datetime.now(UTC)
    return dt.replace(tzinfo=None, microsecond=(dt.microsecond // 1000) * 1000)


def _created_col() -> sa.Column:
    return sa.Column(_DateTimeMs, nullable=True, default=_now_ms)


def _updated_col() -> sa.Column:
    return sa.Column(_DateTimeMs, nullable=True, default=_now_ms, onupdate=_now_ms)


# ── Lookup tables ────────────────────────────────────────────────────────────


class SetType(SQLModel, table=True):
    __tablename__ = "set_type"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


class CardType(SQLModel, table=True):
    __tablename__ = "card_type"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    symbol: str
    name: str
    desc: str | None = None


class Artist(SQLModel, table=True):
    __tablename__ = "artist"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


class Rarity(SQLModel, table=True):
    __tablename__ = "rarity"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    symbol: str
    name: str
    desc: str | None = None


class Tribe(SQLModel, table=True):
    __tablename__ = "tribe"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


class Attribute(SQLModel, table=True):
    __tablename__ = "attribute"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


class Color(SQLModel, table=True):
    __tablename__ = "color"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


class Block(SQLModel, table=True):
    __tablename__ = "block"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


class Format(SQLModel, table=True):
    __tablename__ = "format"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


class Keyword(SQLModel, table=True):
    __tablename__ = "keyword"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


class Resword(SQLModel, table=True):
    __tablename__ = "resword"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str
    desc: str | None = None


# ── Core tables ──────────────────────────────────────────────────────────────


class Set(SQLModel, table=True):
    __tablename__ = "set"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    type_fk: int | None = Field(default=None, foreign_key="set_type.id")
    code: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))
    name: str
    series: str | None = None
    ord: int | None = None
    desc: str | None = None
    release_ts: date | None = None


class Name(SQLModel, table=True):
    __tablename__ = "name"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    name: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))


class Image(SQLModel, table=True):
    __tablename__ = "image"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    path: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))


class Effect(SQLModel, table=True):
    __tablename__ = "effect"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    effect: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))


class Trigger(SQLModel, table=True):
    __tablename__ = "trigger"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    trigger: str = Field(sa_column=sa.Column(sa.String, nullable=False, unique=True))


class Card(SQLModel, table=True):
    __tablename__ = "card"
    __table_args__ = (
        UniqueConstraint("set_fk", "number"),
        Index("ix_card_set_fk", "set_fk"),
        Index("ix_card_cardtype_fk", "cardtype_fk"),
        Index("ix_card_name_fk", "name_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    set_fk: int = Field(foreign_key="set.id")
    cardtype_fk: int = Field(foreign_key="card_type.id")
    name_fk: int = Field(foreign_key="name.id")
    effect_fk: int | None = Field(default=None, foreign_key="effect.id")
    trigger_fk: int | None = Field(default=None, foreign_key="trigger.id")
    number: int
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None


class Naip(SQLModel, table=True):
    """A specific physical print of a card (card + set + artist + rarity)."""

    __tablename__ = "naip"
    __table_args__ = (
        # at most one default print per card
        Index("ix_naip_one_default_per_card", "card_fk", unique=True, sqlite_where=sa.text("is_default = 1")),
        # deduplicate physical prints (NULLs excluded — NULL != NULL in SQLite UNIQUE)
        Index(
            "ix_naip_unique_print",
            "card_fk",
            "set_fk",
            "artist_fk",
            "rarity_fk",
            unique=True,
            sqlite_where=sa.text("artist_fk IS NOT NULL AND rarity_fk IS NOT NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    set_fk: int = Field(foreign_key="set.id")
    artist_fk: int | None = Field(default=None, foreign_key="artist.id")
    rarity_fk: int | None = Field(default=None, foreign_key="rarity.id")
    name_fk: int | None = Field(default=None, foreign_key="name.id")
    image_fk: int | None = Field(default=None, foreign_key="image.id")
    effect_fk: int | None = Field(default=None, foreign_key="effect.id")
    trigger_fk: int | None = Field(default=None, foreign_key="trigger.id")
    is_default: bool = Field(default=False)
    is_errata: bool = Field(default=False)
    sort_order: int | None = Field(default=None)
    cardtype_fk: int | None = Field(default=None, foreign_key="card_type.id")
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None


class CardEffectHistory(SQLModel, table=True):
    __tablename__ = "card_effect_history"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    effect_fk: int = Field(foreign_key="effect.id")
    valid_from: date
    valid_to: date | None = None


class CardTriggerHistory(SQLModel, table=True):
    __tablename__ = "card_trigger_history"

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    color_fk: int = Field(foreign_key="color.id")


class CardRarity(SQLModel, table=True):
    __tablename__ = "card_rarity"
    __table_args__ = (
        UniqueConstraint("card_fk", "rarity_fk"),
        Index("ix_card_rarity_card_fk", "card_fk"),
        Index("ix_card_rarity_rarity_fk", "rarity_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    rarity_fk: int = Field(foreign_key="rarity.id")


class CardBlock(SQLModel, table=True):
    __tablename__ = "card_block"
    __table_args__ = (
        UniqueConstraint("card_fk", "block_fk"),
        Index("ix_card_block_card_fk", "card_fk"),
        Index("ix_card_block_block_fk", "block_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    block_fk: int = Field(foreign_key="block.id")


class CardFormat(SQLModel, table=True):
    __tablename__ = "card_format"
    __table_args__ = (
        UniqueConstraint("card_fk", "format_fk"),
        Index("ix_card_format_card_fk", "card_fk"),
        Index("ix_card_format_format_fk", "format_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
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
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    naip_fk: int = Field(foreign_key="naip.id")
    resword_fk: int = Field(foreign_key="resword.id")


class NaipBlock(SQLModel, table=True):
    __tablename__ = "naip_block"
    __table_args__ = (
        UniqueConstraint("naip_fk", "block_fk"),
        Index("ix_naip_block_naip_fk", "naip_fk"),
        Index("ix_naip_block_block_fk", "block_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    naip_fk: int = Field(foreign_key="naip.id")
    block_fk: int = Field(foreign_key="block.id")


class NaipFormat(SQLModel, table=True):
    __tablename__ = "naip_format"
    __table_args__ = (
        UniqueConstraint("naip_fk", "format_fk"),
        Index("ix_naip_format_naip_fk", "naip_fk"),
        Index("ix_naip_format_format_fk", "format_fk"),
    )

    id: int | None = Field(default=None, primary_key=True)
    created_ts: datetime | None = Field(default=None, sa_column=_created_col())
    updated_ts: datetime | None = Field(default=None, sa_column=_updated_col())
    naip_fk: int = Field(foreign_key="naip.id")
    format_fk: int = Field(foreign_key="format.id")
