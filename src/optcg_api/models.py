from datetime import date
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


def _created_col() -> sa.Column:
    return sa.Column(sa.Date, nullable=True, server_default=sa.text("CURRENT_DATE"))


def _updated_col() -> sa.Column:
    return sa.Column(
        sa.Date,
        nullable=True,
        server_default=sa.text("CURRENT_DATE"),
        onupdate=sa.func.current_date(),
    )


# ── Lookup tables ────────────────────────────────────────────────────────────


class SetType(SQLModel, table=True):
    __tablename__ = "settype"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


class CardType(SQLModel, table=True):
    __tablename__ = "cardtype"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    symbol: str
    name: str
    desc: Optional[str] = None


class Artist(SQLModel, table=True):
    __tablename__ = "artist"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


class Rarity(SQLModel, table=True):
    __tablename__ = "rarity"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    symbol: str
    name: str
    desc: Optional[str] = None


class Tribe(SQLModel, table=True):
    __tablename__ = "tribe"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


class Attribute(SQLModel, table=True):
    __tablename__ = "attribute"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


class Color(SQLModel, table=True):
    __tablename__ = "color"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


class Block(SQLModel, table=True):
    __tablename__ = "block"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


class Format(SQLModel, table=True):
    __tablename__ = "format"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


class Keywords(SQLModel, table=True):
    __tablename__ = "keywords"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


class Reswords(SQLModel, table=True):
    __tablename__ = "reswords"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    name: str
    desc: Optional[str] = None


# ── Core tables ──────────────────────────────────────────────────────────────


class Set(SQLModel, table=True):
    __tablename__ = "set"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    type_fk: Optional[int] = Field(default=None, foreign_key="settype.id")
    code: str
    name: str
    desc: Optional[str] = None
    release_ts: Optional[date] = None


class Card(SQLModel, table=True):
    __tablename__ = "card"

    id: Optional[int] = Field(default=None, primary_key=True)
    set_fk: int = Field(foreign_key="set.id")
    cardtype_fk: int = Field(foreign_key="cardtype.id")
    number: int
    name: str
    desc: Optional[str] = None
    trigger: Optional[str] = None
    power: Optional[int] = None
    life: Optional[int] = None
    counter: Optional[int] = None
    cost: Optional[int] = None
    image_path: Optional[str] = None


class Naip(SQLModel, table=True):
    """A specific physical print of a card (card + set + artist + rarity)."""

    __tablename__ = "naip"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    set_fk: int = Field(foreign_key="set.id")
    artist_fk: Optional[int] = Field(default=None, foreign_key="artist.id")
    rarity_fk: Optional[int] = Field(default=None, foreign_key="rarity.id")
    name: str
    desc: Optional[str] = None


# ── Junction tables ──────────────────────────────────────────────────────────


class CardTribe(SQLModel, table=True):
    __tablename__ = "cardtribe"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    tribe_fk: int = Field(foreign_key="tribe.id")


class CardAttribute(SQLModel, table=True):
    __tablename__ = "cardattribute"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    attribute_fk: int = Field(foreign_key="attribute.id")


class CardColor(SQLModel, table=True):
    __tablename__ = "cardcolor"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    color_fk: int = Field(foreign_key="color.id")


class CardRarity(SQLModel, table=True):
    __tablename__ = "cardrarity"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    rarity_fk: int = Field(foreign_key="rarity.id")


class CardBlock(SQLModel, table=True):
    __tablename__ = "cardblock"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    block_fk: int = Field(foreign_key="block.id")


class CardFormat(SQLModel, table=True):
    __tablename__ = "cardformat"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    format_fk: int = Field(foreign_key="format.id")


class CardKeywords(SQLModel, table=True):
    __tablename__ = "cardkeywords"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    keywords_fk: int = Field(foreign_key="keywords.id")


class CardReswords(SQLModel, table=True):
    __tablename__ = "cardreswords"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_ts: Optional[date] = Field(default=None, sa_column=_created_col())
    updated_ts: Optional[date] = Field(default=None, sa_column=_updated_col())
    card_fk: int = Field(foreign_key="card.id")
    reswords_fk: int = Field(foreign_key="reswords.id")
