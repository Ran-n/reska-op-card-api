#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/12 13:37:30.058204
Revised: 2026/06/29 08:55:36.299211
"""

from pydantic import BaseModel, field_validator
from sqlmodel import Session, select, text


class LookupItem(BaseModel):
    id: int
    name: str
    symbol: str | None = None


class ImageUrlPayload(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def _validate_scheme(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped.lower().startswith(("http://", "https://")):
            raise ValueError("URL must use http or https scheme")
        return stripped


# ── Expandable resource models ────────────────────────────────────────────────


class ExpandedSet(BaseModel):
    id: int
    code: str
    name: str


class ExpandedCardType(BaseModel):
    id: int
    name: str
    symbol: str | None = None


class ExpandedRarity(BaseModel):
    id: int
    name: str
    symbol: str | None = None


class ExpandedPrintVariant(BaseModel):
    id: int
    name: str
    symbol: str | None = None


class ExpandedLanguage(BaseModel):
    id: int
    code: str
    name: str


class ExpandedBlock(BaseModel):
    id: int
    name: str


class ExpandedSetType(BaseModel):
    id: int
    name: str


class ExpandedArtist(BaseModel):
    id: int
    name: str
    desc: str | None = None


class ExpandedCard(BaseModel):
    """Flat card snapshot embedded inside a naip — no nested expansion."""

    id: int
    number: int
    name: str | None = None
    effect: str | None = None
    trigger: str | None = None
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None
    set_code: str | None = None
    set_name: str | None = None
    cardtype_name: str | None = None
    cardtype_symbol: str | None = None
    rarity_name: str | None = None
    rarity_symbol: str | None = None
    colors: list[LookupItem] = []
    tribes: list[LookupItem] = []
    attrs: list[LookupItem] = []
    keywords: list[LookupItem] = []
    reswords: list[LookupItem] = []


# ── Text FK helpers ───────────────────────────────────────────────────────────


def _resolve_text(session: Session, model, pk: int | None, field: str) -> str | None:
    if pk is None:
        return None
    obj = session.get(model, pk)
    return getattr(obj, field, None) if obj else None


def _upsert_text_fk(session: Session, model, field: str, value: str | None) -> int | None:
    if not value:
        return None
    value = value.strip()
    if not value:
        return None
    existing = session.exec(select(model).where(getattr(model, field) == value)).first()
    if existing:
        return existing.id
    obj = model(**{field: value})
    session.add(obj)
    session.flush()
    return obj.id


# ── Bulk expand helpers ───────────────────────────────────────────────────────


def _unique_nonnull(fks: list[int | None]) -> list[int]:
    return list({f for f in fks if f is not None})


def _expand_sets_bulk(set_fks: list[int | None], session: Session) -> dict[int, ExpandedSet]:
    unique = _unique_nonnull(set_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)
    rows = session.exec(text(f'SELECT id, code, name FROM "set" WHERE id IN ({id_list})')).all()
    return {r[0]: ExpandedSet(id=r[0], code=r[1], name=r[2]) for r in rows}


def _expand_cardtypes_bulk(ct_fks: list[int | None], session: Session) -> dict[int, ExpandedCardType]:
    unique = _unique_nonnull(ct_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)
    rows = session.exec(text(f"SELECT id, name, symbol FROM card_type WHERE id IN ({id_list})")).all()
    return {r[0]: ExpandedCardType(id=r[0], name=r[1], symbol=r[2]) for r in rows}


def _expand_rarities_bulk(rarity_fks: list[int | None], session: Session) -> dict[int, ExpandedRarity]:
    unique = _unique_nonnull(rarity_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)
    rows = session.exec(text(f"SELECT id, name, symbol FROM rarity WHERE id IN ({id_list})")).all()
    return {r[0]: ExpandedRarity(id=r[0], name=r[1], symbol=r[2]) for r in rows}


def _expand_print_variants_bulk(pv_fks: list[int | None], session: Session) -> dict[int, ExpandedPrintVariant]:
    unique = _unique_nonnull(pv_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)
    rows = session.exec(text(f"SELECT id, name, symbol FROM print_variant WHERE id IN ({id_list})")).all()
    return {r[0]: ExpandedPrintVariant(id=r[0], name=r[1], symbol=r[2]) for r in rows}


def _expand_languages_bulk(lang_fks: list[int | None], session: Session) -> dict[int, ExpandedLanguage]:
    unique = _unique_nonnull(lang_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)
    rows = session.exec(text(f"SELECT id, code, name FROM language WHERE id IN ({id_list})")).all()
    return {r[0]: ExpandedLanguage(id=r[0], code=r[1], name=r[2]) for r in rows}


def _expand_blocks_bulk(block_fks: list[int | None], session: Session) -> dict[int, ExpandedBlock]:
    unique = _unique_nonnull(block_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)
    rows = session.exec(text(f"SELECT id, name FROM block WHERE id IN ({id_list})")).all()
    return {r[0]: ExpandedBlock(id=r[0], name=r[1]) for r in rows}


def _expand_settypes_bulk(st_fks: list[int | None], session: Session) -> dict[int, ExpandedSetType]:
    unique = _unique_nonnull(st_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)
    rows = session.exec(text(f"SELECT id, name FROM set_type WHERE id IN ({id_list})")).all()
    return {r[0]: ExpandedSetType(id=r[0], name=r[1]) for r in rows}


def _expand_artists_bulk(artist_fks: list[int | None], session: Session) -> dict[int, ExpandedArtist]:
    unique = _unique_nonnull(artist_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)
    rows = session.exec(text(f'SELECT id, name, "desc" FROM artist WHERE id IN ({id_list})')).all()
    return {r[0]: ExpandedArtist(id=r[0], name=r[1], desc=r[2]) for r in rows}


def _expand_cards_bulk(card_fks: list[int | None], session: Session) -> dict[int, ExpandedCard]:
    unique = _unique_nonnull(card_fks)
    if not unique:
        return {}
    id_list = ",".join(str(i) for i in unique)

    card_rows = session.exec(
        text(
            f"SELECT c.id, c.number, c.power, c.life, c.counter, c.cost, "
            f"c.name_fk, c.effect_fk, c.trigger_fk, "
            f"s.code, s.name, ct.name, ct.symbol, r.name, r.symbol "
            f"FROM card c "
            f'LEFT JOIN "set" s ON s.id = c.set_fk '
            f"LEFT JOIN card_type ct ON ct.id = c.cardtype_fk "
            f"LEFT JOIN rarity r ON r.id = c.rarity_fk "
            f"WHERE c.id IN ({id_list})"
        )
    ).all()

    text_fks: dict[int, tuple] = {}
    partials: dict[int, dict] = {}
    for r in card_rows:
        text_fks[r[0]] = (r[6], r[7], r[8])
        partials[r[0]] = dict(
            id=r[0],
            number=r[1],
            power=r[2],
            life=r[3],
            counter=r[4],
            cost=r[5],
            set_code=r[9],
            set_name=r[10],
            cardtype_name=r[11],
            cardtype_symbol=r[12],
            rarity_name=r[13],
            rarity_symbol=r[14],
        )

    name_fks = [v[0] for v in text_fks.values() if v[0]]
    effect_fks = [v[1] for v in text_fks.values() if v[1]]
    trigger_fks = [v[2] for v in text_fks.values() if v[2]]

    name_map: dict[int, str] = {}
    effect_map: dict[int, str] = {}
    trigger_map: dict[int, str] = {}

    if name_fks:
        fk_str = ",".join(str(i) for i in name_fks)
        for r in session.exec(text(f'SELECT id, "name" FROM "name" WHERE id IN ({fk_str})')).all():
            name_map[r[0]] = r[1]
    if effect_fks:
        fk_str = ",".join(str(i) for i in effect_fks)
        for r in session.exec(text(f"SELECT id, effect FROM effect WHERE id IN ({fk_str})")).all():
            effect_map[r[0]] = r[1]
    if trigger_fks:
        fk_str = ",".join(str(i) for i in trigger_fks)
        for r in session.exec(text(f'SELECT id, "trigger" FROM "trigger" WHERE id IN ({fk_str})')).all():
            trigger_map[r[0]] = r[1]

    cards: dict[int, ExpandedCard] = {}
    for card_id, p in partials.items():
        nfk, efk, tfk = text_fks[card_id]
        cards[card_id] = ExpandedCard(
            **p,
            name=name_map.get(nfk) if nfk else None,
            effect=effect_map.get(efk) if efk else None,
            trigger=trigger_map.get(tfk) if tfk else None,
        )

    junction_specs = [
        ("card_color", "card_fk", "color_fk", "color", "colors"),
        ("card_tribe", "card_fk", "tribe_fk", "tribe", "tribes"),
        ("card_attribute", "card_fk", "attribute_fk", "attribute", "attrs"),
        ("card_keyword", "card_fk", "keyword_fk", "keyword", "keywords"),
        ("card_resword", "card_fk", "resword_fk", "resword", "reswords"),
    ]
    for junc_table, fk_col, item_fk_col, item_table, attr_name in junction_specs:
        rows = session.exec(
            text(
                f"SELECT j.{fk_col}, t.id, t.name FROM {item_table} t "
                f"JOIN {junc_table} j ON j.{item_fk_col} = t.id "
                f"WHERE j.{fk_col} IN ({id_list})"
            )
        ).all()
        for card_fk_val, item_id, item_name in rows:
            if card_fk_val in cards:
                getattr(cards[card_fk_val], attr_name).append(LookupItem(id=item_id, name=item_name))

    return cards


def _stripe(fk: int | None, key: str, expand_set: set[str], expand_map: dict):
    """Return the FK int or its expanded object, or None if fk is None."""
    if fk is None:
        return None
    return expand_map.get(fk, fk) if key in expand_set else fk
