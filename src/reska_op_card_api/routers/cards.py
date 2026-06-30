#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/06/30 14:36:29.648947
"""

from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, text

from reska_op_card_api._images import (
    MAX_IMAGE_BYTES,
    VALID_SUFFIXES,
    cleanup_orphaned_image,
    replace_naip_image,
    save_image,
)
from reska_op_card_api.auth import require_edit_key, require_read_key
from reska_op_card_api.database import get_session
from reska_op_card_api.models import (
    BannedPair,
    Card,
    CardAttribute,
    CardBan,
    CardColor,
    CardEffectHistory,
    CardFormat,
    CardKeyword,
    CardResword,
    CardTribe,
    CardTriggerHistory,
    Effect,
    Naip,
    NaipAttribute,
    NaipColor,
    NaipKeyword,
    NaipResword,
    NaipSerial,
    NaipTribe,
    Name,
    PrintVariant,
    Trigger,
)
from reska_op_card_api.routers._common import (
    ExpandedBlock,
    ExpandedCardType,
    ExpandedRarity,
    ExpandedSet,
    ImageUrlPayload,
    LookupItem,
    _bulk_naip_extras,
    _expand_blocks_bulk,
    _expand_cardtypes_bulk,
    _expand_rarities_bulk,
    _expand_sets_bulk,
    _in_filter,
    _parse_csv,
    _parse_expand,
    _resolve_text,
    _stripe,
    _upsert_text_fk,
)

router = APIRouter(prefix="/cards", tags=["cards"])

_JUNCTION_EXPAND_FIELDS = {"colors", "tribes", "attrs", "formats", "keywords", "reswords"}
_DETAIL_EXPAND_FIELDS = {"set", "cardtype", "rarity", "block", "naips"} | _JUNCTION_EXPAND_FIELDS
_LIST_EXPAND_FIELDS = {"set", "cardtype", "rarity", "naips"} | _JUNCTION_EXPAND_FIELDS


# ── Rich response models ─────────────────────────────────────────────────────


class NaipItem(BaseModel):
    id: int
    name: str
    artist_name: str | None = None
    print_variant_name: str | None = None
    print_variant_symbol: str | None = None
    set_code: str | None = None
    image_fk: int | None = None
    image_path: str | None = None
    is_default: bool = False
    is_errata: bool = False
    is_foil: bool = False
    language: int | None = None
    cardtype: int | None = None
    block: int | None = None
    sort_order: int | None = None
    serial_max: int | None = None
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None
    effect: str | None = None
    trigger: str | None = None
    colors: list[int] | list[LookupItem] = []
    tribes: list[int] | list[LookupItem] = []
    attrs: list[int] | list[LookupItem] = []
    keywords: list[int] | list[LookupItem] = []
    reswords: list[int] | list[LookupItem] = []


class CardDetail(BaseModel):
    id: int
    set: int | ExpandedSet
    cardtype: int | ExpandedCardType
    rarity: int | ExpandedRarity | None = None
    block: int | ExpandedBlock | None = None
    number: int
    name: str
    effect: str | None = None
    trigger: str | None = None
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None
    colors: list[int] | list[LookupItem] = []
    tribes: list[int] | list[LookupItem] = []
    attrs: list[int] | list[LookupItem] = []
    formats: list[int] | list[LookupItem] = []
    keywords: list[int] | list[LookupItem] = []
    reswords: list[int] | list[LookupItem] = []
    naips: list[int] | list[NaipItem] = []


class CardListItem(BaseModel):
    id: int
    set: int | ExpandedSet
    cardtype: int | ExpandedCardType
    rarity: int | ExpandedRarity | None = None
    block: int | None = None
    number: int
    name: str
    effect: str | None = None
    trigger: str | None = None
    cost: int | None = None
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    image_path: str | None = None
    colors: list[int] | list[LookupItem] = []
    tribes: list[int] | list[LookupItem] = []
    attrs: list[int] | list[LookupItem] = []
    formats: list[int] | list[LookupItem] = []
    keywords: list[int] | list[LookupItem] = []
    reswords: list[int] | list[LookupItem] = []
    naips: list[int] | list[NaipItem] = []


class CardListResponse(BaseModel):
    rows: list[CardListItem]
    total: int


class CardWrite(BaseModel):
    set_fk: int
    cardtype_fk: int
    rarity_fk: int | None = None
    number: int = Field(ge=1)
    name: str = Field(min_length=1)
    effect: str | None = None
    trigger: str | None = None
    power: int | None = Field(default=None, ge=0)
    life: int | None = Field(default=None, ge=0)
    counter: int | None = Field(default=None, ge=0)
    cost: int | None = Field(default=None, ge=0)
    colors: list[int] = []
    tribes: list[int] = []
    attrs: list[int] = []
    blocks: list[int] = []
    formats: list[int] = []
    keywords: list[int] = []
    reswords: list[int] = []

    @field_validator("blocks")
    @classmethod
    def one_block_max(cls, v: list[int]) -> list[int]:
        if len(v) > 1:
            raise ValueError("a card can have at most one block")
        return v


# ── Helpers ──────────────────────────────────────────────────────────────────

_CARD_JUNCTION_SPECS = [
    ("card_color", "card_fk", "color_fk", "color", "colors"),
    ("card_tribe", "card_fk", "tribe_fk", "tribe", "tribes"),
    ("card_attribute", "card_fk", "attribute_fk", "attribute", "attrs"),
    ("card_format", "card_fk", "format_fk", "format", "formats"),
    ("card_keyword", "card_fk", "keyword_fk", "keyword", "keywords"),
    ("card_resword", "card_fk", "resword_fk", "resword", "reswords"),
]


def _bulk_card_extras(card_ids: list[int], session: Session, expand: set[str] | None = None) -> dict[int, dict]:
    """Batch-resolve block_fk, effect/trigger text, and junction tags for a set of card ids.

    Junction tag lists contain FK ids only unless the corresponding key is present in
    ``expand``, in which case they contain the full ``LookupItem`` objects — mirroring the
    FK-field expand convention (never an empty list as a stand-in for "not expanded").
    """
    expand = expand or set()
    extras: dict[int, dict] = {
        cid: {
            "block": None,
            "effect": None,
            "trigger": None,
            "colors": [],
            "tribes": [],
            "attrs": [],
            "formats": [],
            "keywords": [],
            "reswords": [],
        }
        for cid in card_ids
    }
    if not card_ids:
        return extras
    id_list = ",".join(str(i) for i in card_ids)

    fk_rows = session.exec(text(f"SELECT id, block_fk, effect_fk, trigger_fk FROM card WHERE id IN ({id_list})")).all()
    effect_fks = [r[2] for r in fk_rows if r[2]]
    trigger_fks = [r[3] for r in fk_rows if r[3]]
    effect_map: dict[int, str] = {}
    trigger_map: dict[int, str] = {}
    if effect_fks:
        fk_str = ",".join(str(i) for i in set(effect_fks))
        for r in session.exec(text(f"SELECT id, effect FROM effect WHERE id IN ({fk_str})")).all():
            effect_map[r[0]] = r[1]
    if trigger_fks:
        fk_str = ",".join(str(i) for i in set(trigger_fks))
        for r in session.exec(text(f'SELECT id, "trigger" FROM "trigger" WHERE id IN ({fk_str})')).all():
            trigger_map[r[0]] = r[1]
    for cid, block_fk, efk, tfk in fk_rows:
        extras[cid]["block"] = block_fk
        extras[cid]["effect"] = effect_map.get(efk) if efk else None
        extras[cid]["trigger"] = trigger_map.get(tfk) if tfk else None

    for junc_table, fk_col, item_fk_col, item_table, attr_name in _CARD_JUNCTION_SPECS:
        if attr_name in expand:
            rows = session.exec(
                text(
                    f"SELECT j.{fk_col}, t.id, t.name FROM {item_table} t "
                    f"JOIN {junc_table} j ON j.{item_fk_col} = t.id "
                    f"WHERE j.{fk_col} IN ({id_list})"
                )
            ).all()
            for card_fk_val, item_id, item_name in rows:
                extras[card_fk_val][attr_name].append(LookupItem(id=item_id, name=item_name))
        else:
            rows = session.exec(
                text(f"SELECT j.{fk_col}, j.{item_fk_col} FROM {junc_table} j WHERE j.{fk_col} IN ({id_list})")
            ).all()
            for card_fk_val, item_id in rows:
                extras[card_fk_val][attr_name].append(item_id)

    return extras


def _enrich(card: Card, session: Session, expand: set[str] | None = None) -> CardDetail:
    expand = expand or set()

    card_name = _resolve_text(session, Name, card.name_fk, "name") or ""
    extras = _bulk_card_extras([card.id], session, expand)[card.id]

    naips: list[int] | list[NaipItem]
    if "naips" in expand:
        naip_rows = session.exec(
            text(
                "SELECT n.id, COALESCE(nm.name, ''), a.name, pv.name, pv.symbol, s.code, "
                "n.image_fk, n.is_default, n.is_errata, n.is_foil, img.path, "
                "n.language_fk, n.cardtype_fk, n.block_fk, n.sort_order, n.serial_max, "
                "n.power, n.life, n.counter, n.cost "
                "FROM naip n "
                "LEFT JOIN name nm ON nm.id = n.name_fk "
                "LEFT JOIN artist a ON a.id = n.artist_fk "
                "LEFT JOIN print_variant pv ON pv.id = n.print_variant_fk "
                'LEFT JOIN "set" s ON s.id = n.set_fk '
                "LEFT JOIN image img ON img.id = n.image_fk "
                "WHERE n.card_fk = :cid"
            ).bindparams(cid=card.id)
        ).all()
        naip_extras = _bulk_naip_extras([r[0] for r in naip_rows], session, expand)
        naips = [
            NaipItem(
                id=r[0],
                name=r[1],
                artist_name=r[2],
                print_variant_name=r[3],
                print_variant_symbol=r[4],
                set_code=r[5],
                image_fk=r[6],
                is_default=bool(r[7]),
                is_errata=bool(r[8]),
                is_foil=bool(r[9]),
                image_path=r[10],
                language=r[11],
                cardtype=r[12],
                block=r[13],
                sort_order=r[14],
                serial_max=r[15],
                power=r[16],
                life=r[17],
                counter=r[18],
                cost=r[19],
                **naip_extras[r[0]],
            )
            for r in naip_rows
        ]
    else:
        naips = [
            r[0] for r in session.exec(text("SELECT id FROM naip WHERE card_fk = :cid").bindparams(cid=card.id)).all()
        ]

    set_map = _expand_sets_bulk([card.set_fk], session) if "set" in expand else {}
    ct_map = _expand_cardtypes_bulk([card.cardtype_fk], session) if "cardtype" in expand else {}
    rarity_map = _expand_rarities_bulk([card.rarity_fk], session) if "rarity" in expand else {}
    block_map = _expand_blocks_bulk([card.block_fk], session) if "block" in expand else {}

    return CardDetail(
        id=card.id,
        set=set_map.get(card.set_fk, card.set_fk),
        cardtype=ct_map.get(card.cardtype_fk, card.cardtype_fk),
        rarity=_stripe(card.rarity_fk, "rarity", expand, rarity_map),
        block=_stripe(extras["block"], "block", expand, block_map),
        number=card.number,
        name=card_name,
        effect=extras["effect"],
        trigger=extras["trigger"],
        power=card.power,
        life=card.life,
        counter=card.counter,
        cost=card.cost,
        colors=extras["colors"],
        tribes=extras["tribes"],
        attrs=extras["attrs"],
        formats=extras["formats"],
        keywords=extras["keywords"],
        reswords=extras["reswords"],
        naips=naips,
    )


def _bulk_naips(
    card_ids: list[int], session: Session, full: bool, expand: set[str] | None = None
) -> dict[int, list[int]] | dict[int, list[NaipItem]]:
    if not card_ids:
        return {}
    id_list = ",".join(str(i) for i in card_ids)
    result: dict[int, list] = {cid: [] for cid in card_ids}
    if not full:
        rows = session.exec(text(f"SELECT card_fk, id FROM naip WHERE card_fk IN ({id_list})")).all()
        for card_fk, naip_id in rows:
            result[card_fk].append(naip_id)
        return result
    rows = session.exec(
        text(
            "SELECT n.card_fk, n.id, COALESCE(nm.name, ''), a.name, pv.name, pv.symbol, s.code, "
            "n.image_fk, n.is_default, n.is_errata, n.is_foil, img.path, "
            "n.language_fk, n.cardtype_fk, n.block_fk, n.sort_order, n.serial_max, "
            "n.power, n.life, n.counter, n.cost "
            "FROM naip n "
            "LEFT JOIN name nm ON nm.id = n.name_fk "
            "LEFT JOIN artist a ON a.id = n.artist_fk "
            "LEFT JOIN print_variant pv ON pv.id = n.print_variant_fk "
            'LEFT JOIN "set" s ON s.id = n.set_fk '
            "LEFT JOIN image img ON img.id = n.image_fk "
            f"WHERE n.card_fk IN ({id_list})"
        )
    ).all()
    naip_extras = _bulk_naip_extras([r[1] for r in rows], session, expand)
    for r in rows:
        result[r[0]].append(
            NaipItem(
                id=r[1],
                name=r[2],
                artist_name=r[3],
                print_variant_name=r[4],
                print_variant_symbol=r[5],
                set_code=r[6],
                image_fk=r[7],
                is_default=bool(r[8]),
                is_errata=bool(r[9]),
                is_foil=bool(r[10]),
                image_path=r[11],
                language=r[12],
                cardtype=r[13],
                block=r[14],
                sort_order=r[15],
                serial_max=r[16],
                power=r[17],
                life=r[18],
                counter=r[19],
                cost=r[20],
                **naip_extras[r[1]],
            )
        )
    return result


def _sync_junctions(card: Card, data: CardWrite, session: Session):
    pairs = [
        (CardColor, "color_fk", data.colors),
        (CardTribe, "tribe_fk", data.tribes),
        (CardAttribute, "attribute_fk", data.attrs),
        (CardFormat, "format_fk", data.formats),
        (CardKeyword, "keyword_fk", data.keywords),
        (CardResword, "resword_fk", data.reswords),
    ]
    for model, fk_field, ids in pairs:
        existing = session.exec(select(model).where(model.card_fk == card.id)).all()
        for row in existing:
            session.delete(row)
        session.flush()
        for fk_id in ids:
            session.add(model(**{"card_fk": card.id, fk_field: fk_id}))
    card.block_fk = data.blocks[0] if data.blocks else None
    session.add(card)


# ── Faceted filtering (mirrors logpiece's FilterSpec semantics) ───────────────

# is_foil / print_variant are always-false for a card-level row (the card row only ever
# reflects its default naip's serial/artist, never foil or print_variant — see logpiece's
# fetch_cards()). Filtering on either therefore excludes everything, exactly like the client.
_CARD_ALWAYS_FALSE_FIELDS = ("foil", "print_variant_symbols")


def _build_card_filters(
    search: str | None,
    color_names_any: str | None,
    color_names_exact: str | None,
    card_type_names: str | None,
    rarity_symbols: str | None,
    set_type_names: str | None,
    set_codes: str | None,
    tribe_names: str | None,
    attribute_names: str | None,
    keyword_names: str | None,
    resword_names: str | None,
    format_names: str | None,
    artist_names: str | None,
    block_names: str | None,
    language_names: str | None,
    cost_min: int | None,
    cost_max: int | None,
    power_min: int | None,
    power_max: int | None,
    counter_min: int | None,
    counter_max: int | None,
    life_min: int | None,
    life_max: int | None,
    number_min: int | None,
    number_max: int | None,
    errata: bool | None,
    serial: bool | None,
    foil: bool | None,
    print_variant_symbols: str | None,
) -> tuple[list[str], dict]:
    conditions: list[str] = []
    params: dict = {}

    if search:
        conditions.append(
            "(nm.name LIKE :search "
            'OR EXISTS (SELECT 1 FROM "set" s2 WHERE s2.id = c.set_fk AND s2.code LIKE :search) '
            "OR EXISTS (SELECT 1 FROM card_type ct2 WHERE ct2.id = c.cardtype_fk AND ct2.name LIKE :search) "
            "OR EXISTS (SELECT 1 FROM card_color cc2 JOIN color co2 ON co2.id = cc2.color_fk "
            "WHERE cc2.card_fk = c.id AND co2.name LIKE :search))"
        )
        params["search"] = f"%{search}%"

    any_names = _parse_csv(color_names_any)
    if any_names:
        sql, p = _in_filter("co.name", any_names, "canyc")
        conditions.append(
            "EXISTS (SELECT 1 FROM card_color cc JOIN color co ON co.id = cc.color_fk "
            f"WHERE cc.card_fk = c.id AND {sql})"
        )
        params.update(p)

    exact_names = _parse_csv(color_names_exact)
    if exact_names:
        sql, p = _in_filter("co3.name", exact_names, "cexc")
        conditions.append(
            "(SELECT COUNT(DISTINCT cc3.color_fk) FROM card_color cc3 WHERE cc3.card_fk = c.id) = :n_exact_colors "
            "AND NOT EXISTS (SELECT 1 FROM card_color cc4 JOIN color co3 ON co3.id = cc4.color_fk "
            f"WHERE cc4.card_fk = c.id AND NOT {sql})"
        )
        params.update(p)
        params["n_exact_colors"] = len(exact_names)

    type_names = _parse_csv(card_type_names)
    if type_names:
        sql, p = _in_filter("name", type_names, "ctn")
        conditions.append(f"c.cardtype_fk IN (SELECT id FROM card_type WHERE {sql})")
        params.update(p)

    rarities = _parse_csv(rarity_symbols)
    if rarities:
        sql, p = _in_filter("symbol", rarities, "rar")
        conditions.append(f"c.rarity_fk IN (SELECT id FROM rarity WHERE {sql})")
        params.update(p)

    set_types = _parse_csv(set_type_names)
    if set_types:
        sql, p = _in_filter("name", set_types, "stn")
        conditions.append(f'c.set_fk IN (SELECT id FROM "set" WHERE type_fk IN (SELECT id FROM set_type WHERE {sql}))')
        params.update(p)

    codes = _parse_csv(set_codes)
    if codes:
        sql, p = _in_filter("code", codes, "setc")
        conditions.append(f'c.set_fk IN (SELECT id FROM "set" WHERE {sql})')
        params.update(p)

    for csv_param, junction, item_fk, item_table, prefix in (
        (tribe_names, "card_tribe", "tribe_fk", "tribe", "trb"),
        (attribute_names, "card_attribute", "attribute_fk", "attribute", "atb"),
        (keyword_names, "card_keyword", "keyword_fk", "keyword", "kwd"),
        (resword_names, "card_resword", "resword_fk", "resword", "rwd"),
        (format_names, "card_format", "format_fk", "format", "fmt"),
    ):
        names = _parse_csv(csv_param)
        if not names:
            continue
        sql, p = _in_filter("t.name", names, prefix)
        conditions.append(
            f"EXISTS (SELECT 1 FROM {junction} j JOIN {item_table} t ON t.id = j.{item_fk} "
            f"WHERE j.card_fk = c.id AND {sql})"
        )
        params.update(p)

    artists = _parse_csv(artist_names)
    if artists:
        sql, p = _in_filter("a.name", artists, "art")
        conditions.append(
            "EXISTS (SELECT 1 FROM naip n2 JOIN artist a ON a.id = n2.artist_fk "
            f"WHERE n2.card_fk = c.id AND n2.is_default = 1 AND {sql})"
        )
        params.update(p)

    blocks = _parse_csv(block_names)
    if blocks:
        sql, p = _in_filter("name", blocks, "blk")
        conditions.append(f"c.block_fk IN (SELECT id FROM block WHERE {sql})")
        params.update(p)

    languages = _parse_csv(language_names)
    if languages:
        sql, p = _in_filter("name", languages, "lng")
        conditions.append(
            f'c.set_fk IN (SELECT id FROM "set" WHERE language_fk IN (SELECT id FROM language WHERE {sql}))'
        )
        params.update(p)

    for col, lo, hi in (
        ("c.cost", cost_min, cost_max),
        ("c.power", power_min, power_max),
        ("c.counter", counter_min, counter_max),
        ("c.life", life_min, life_max),
        ("c.number", number_min, number_max),
    ):
        if lo is not None:
            key = f"{col.replace('.', '_')}_min"
            conditions.append(f"{col} >= :{key}")
            params[key] = lo
        if hi is not None:
            key = f"{col.replace('.', '_')}_max"
            conditions.append(f"{col} <= :{key}")
            params[key] = hi

    if errata:
        conditions.append("EXISTS (SELECT 1 FROM naip n3 WHERE n3.card_fk = c.id AND n3.is_errata = 1)")
    if serial:
        conditions.append(
            "EXISTS (SELECT 1 FROM naip n4 WHERE n4.card_fk = c.id AND n4.is_default = 1 AND n4.serial_max IS NOT NULL)"
        )
    if foil or _parse_csv(print_variant_symbols):
        conditions.append("0 = 1")

    return conditions, params


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/", response_model=CardListResponse, dependencies=[Depends(require_read_key)])
def list_cards(
    name: str | None = Query(None),
    set_id: int | None = Query(None),
    cardtype_id: int | None = Query(None),
    search: str | None = Query(None),
    color_names_any: str | None = Query(None),
    color_names_exact: str | None = Query(None),
    card_type_names: str | None = Query(None),
    rarity_symbols: str | None = Query(None),
    set_type_names: str | None = Query(None),
    set_codes: str | None = Query(None),
    tribe_names: str | None = Query(None),
    attribute_names: str | None = Query(None),
    keyword_names: str | None = Query(None),
    resword_names: str | None = Query(None),
    format_names: str | None = Query(None),
    artist_names: str | None = Query(None),
    block_names: str | None = Query(None),
    language_names: str | None = Query(None),
    cost_min: int | None = Query(None),
    cost_max: int | None = Query(None),
    power_min: int | None = Query(None),
    power_max: int | None = Query(None),
    counter_min: int | None = Query(None),
    counter_max: int | None = Query(None),
    life_min: int | None = Query(None),
    life_max: int | None = Query(None),
    number_min: int | None = Query(None),
    number_max: int | None = Query(None),
    errata: bool | None = Query(None),
    serial: bool | None = Query(None),
    foil: bool | None = Query(None),
    print_variant_symbols: str | None = Query(None),
    expand: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=200),
    session: Session = Depends(get_session),
):
    conditions = []
    filter_params: dict = {}
    if name:
        conditions.append("nm.name LIKE :name")
        filter_params["name"] = f"%{name}%"
    if set_id is not None:
        conditions.append("c.set_fk = :set_id")
        filter_params["set_id"] = set_id
    if cardtype_id is not None:
        conditions.append("c.cardtype_fk = :cardtype_id")
        filter_params["cardtype_id"] = cardtype_id
    extra_conditions, extra_params = _build_card_filters(
        search,
        color_names_any,
        color_names_exact,
        card_type_names,
        rarity_symbols,
        set_type_names,
        set_codes,
        tribe_names,
        attribute_names,
        keyword_names,
        resword_names,
        format_names,
        artist_names,
        block_names,
        language_names,
        cost_min,
        cost_max,
        power_min,
        power_max,
        counter_min,
        counter_max,
        life_min,
        life_max,
        number_min,
        number_max,
        errata,
        serial,
        foil,
        print_variant_symbols,
    )
    conditions.extend(extra_conditions)
    filter_params.update(extra_params)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = session.exec(
        text(
            f"SELECT c.id, c.set_fk, c.cardtype_fk, c.rarity_fk, c.number, nm.name, "
            f"c.cost, c.power, c.counter, c.life, "
            f"(SELECT img.path FROM naip n LEFT JOIN image img ON img.id = n.image_fk "
            f" WHERE n.card_fk = c.id AND n.is_default = 1 LIMIT 1) "
            f"FROM card c "
            f"LEFT JOIN name nm ON nm.id = c.name_fk "
            f"{where} ORDER BY c.set_fk, c.number LIMIT :limit OFFSET :offset"
        ).bindparams(**filter_params, limit=limit, offset=offset)
    ).all()
    total = session.exec(
        text(f"SELECT COUNT(*) FROM card c LEFT JOIN name nm ON nm.id = c.name_fk {where}").bindparams(**filter_params)
    ).scalar()

    expand_set = _parse_expand(expand, _LIST_EXPAND_FIELDS)

    set_map = _expand_sets_bulk([r[1] for r in rows], session) if "set" in expand_set else {}
    ct_map = _expand_cardtypes_bulk([r[2] for r in rows], session) if "cardtype" in expand_set else {}
    rarity_map = _expand_rarities_bulk([r[3] for r in rows], session) if "rarity" in expand_set else {}
    naips_map = _bulk_naips([r[0] for r in rows], session, full="naips" in expand_set, expand=expand_set)
    card_extras = _bulk_card_extras([r[0] for r in rows], session, expand_set)

    return CardListResponse(
        rows=[
            CardListItem(
                id=r[0],
                set=set_map.get(r[1], r[1]),
                cardtype=ct_map.get(r[2], r[2]),
                rarity=_stripe(r[3], "rarity", expand_set, rarity_map),
                number=r[4],
                name=r[5] or "",
                cost=r[6],
                power=r[7],
                counter=r[8],
                life=r[9],
                image_path=r[10],
                naips=naips_map.get(r[0], []),
                **card_extras[r[0]],
            )
            for r in rows
        ],
        total=total or 0,
    )


@router.get("/{card_id}", response_model=CardDetail, dependencies=[Depends(require_read_key)])
def get_card(card_id: int, expand: str | None = Query(None), session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    expand_set = _parse_expand(expand, _DETAIL_EXPAND_FIELDS)
    return _enrich(card, session, expand_set)


@router.post("/", response_model=CardDetail, status_code=201, dependencies=[Depends(require_edit_key)])
def create_card(data: CardWrite, session: Session = Depends(get_session)):
    name_fk = _upsert_text_fk(session, Name, "name", data.name)
    effect_fk = _upsert_text_fk(session, Effect, "effect", data.effect)
    trigger_fk = _upsert_text_fk(session, Trigger, "trigger", data.trigger)
    card = Card(
        set_fk=data.set_fk,
        cardtype_fk=data.cardtype_fk,
        rarity_fk=data.rarity_fk,
        number=data.number,
        name_fk=name_fk,
        effect_fk=effect_fk,
        trigger_fk=trigger_fk,
        power=data.power,
        life=data.life,
        counter=data.counter,
        cost=data.cost,
    )
    session.add(card)
    session.flush()
    _sync_junctions(card, data, session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="A card with this number already exists in this set")
    session.refresh(card)
    return _enrich(card, session)


@router.put("/{card_id}", response_model=CardDetail, dependencies=[Depends(require_edit_key)])
def update_card(card_id: int, data: CardWrite, session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.set_fk = data.set_fk
    card.cardtype_fk = data.cardtype_fk
    card.rarity_fk = data.rarity_fk
    card.number = data.number
    card.name_fk = _upsert_text_fk(session, Name, "name", data.name)
    card.effect_fk = _upsert_text_fk(session, Effect, "effect", data.effect)
    card.trigger_fk = _upsert_text_fk(session, Trigger, "trigger", data.trigger)
    card.power = data.power
    card.life = data.life
    card.counter = data.counter
    card.cost = data.cost
    session.add(card)
    session.flush()
    _sync_junctions(card, data, session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="A card with this number already exists in this set")
    session.refresh(card)
    return _enrich(card, session)


@router.delete("/{card_id}", status_code=204, dependencies=[Depends(require_edit_key)])
def delete_card(card_id: int, session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    naips = session.exec(select(Naip).where(Naip.card_fk == card_id)).all()
    old_img_fks = [n.image_fk for n in naips if n.image_fk]
    for naip in naips:
        for naip_junc in (NaipColor, NaipTribe, NaipAttribute, NaipKeyword, NaipResword):
            for row in session.exec(select(naip_junc).where(naip_junc.naip_fk == naip.id)).all():
                session.delete(row)
        for serial in session.exec(select(NaipSerial).where(NaipSerial.naip_fk == naip.id)).all():
            if serial.image_fk:
                old_img_fks.append(serial.image_fk)
            session.delete(serial)
        session.delete(naip)
    for model in (
        CardColor,
        CardTribe,
        CardAttribute,
        CardFormat,
        CardKeyword,
        CardResword,
        CardBan,
        CardEffectHistory,
        CardTriggerHistory,
    ):
        for row in session.exec(select(model).where(model.card_fk == card_id)).all():
            session.delete(row)
    for row in session.exec(
        select(BannedPair).where((BannedPair.card_a_fk == card_id) | (BannedPair.card_b_fk == card_id))
    ).all():
        session.delete(row)
    session.delete(card)
    session.flush()
    for img_fk in old_img_fks:
        cleanup_orphaned_image(img_fk, session)
    session.commit()


def _set_card_image(card: Card, raw: bytes, suffix: str, session: Session) -> None:
    """Save image bytes and link to the card's default Naip (creating one if absent)."""
    img = save_image(raw, suffix, session)
    naip = session.exec(select(Naip).where(Naip.card_fk == card.id, Naip.is_default == True)).first()  # noqa: E712
    if naip:
        replace_naip_image(naip, img.id, session)
    else:
        std = session.exec(select(PrintVariant).where(PrintVariant.symbol == "STD")).first()
        if std is None:
            raise HTTPException(status_code=500, detail="STD print_variant seed row missing")
        session.add(
            Naip(card_fk=card.id, set_fk=card.set_fk, image_fk=img.id, is_default=True, print_variant_fk=std.id)
        )


@router.post("/{card_id}/image-url", response_model=CardDetail, dependencies=[Depends(require_edit_key)])
async def upload_card_image_from_url(card_id: int, payload: ImageUrlPayload, session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    url = payload.url.strip()
    suffix = Path(url.split("?")[0]).suffix.lower() or ".jpg"
    if suffix not in VALID_SUFFIXES:
        suffix = ".jpg"
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            raw = resp.content
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {e}")
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MB limit")
    _set_card_image(card, raw, suffix, session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Conflict setting default naip image; retry")
    session.refresh(card)
    return _enrich(card, session)


@router.post("/{card_id}/image", response_model=CardDetail, dependencies=[Depends(require_edit_key)])
async def upload_card_image(card_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    suffix = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if suffix not in VALID_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only jpg, png, webp images are accepted")
    raw = await file.read()
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MB limit")
    _set_card_image(card, raw, suffix, session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Conflict setting default naip image; retry")
    session.refresh(card)
    return _enrich(card, session)
