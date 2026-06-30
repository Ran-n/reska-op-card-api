#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/30 00:00:00.000000
Revised: 2026/06/30 12:51:50.528531
"""

from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
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
    Effect,
    Naip,
    NaipAttribute,
    NaipColor,
    NaipKeyword,
    NaipResword,
    NaipSerial,
    NaipTribe,
    Name,
    Trigger,
)
from reska_op_card_api.routers._common import (
    ExpandedArtist,
    ExpandedBlock,
    ExpandedCard,
    ExpandedCardType,
    ExpandedLanguage,
    ExpandedPrintVariant,
    ExpandedSet,
    ImageUrlPayload,
    LookupItem,
    _bulk_naip_extras,
    _expand_artists_bulk,
    _expand_blocks_bulk,
    _expand_cards_bulk,
    _expand_cardtypes_bulk,
    _expand_languages_bulk,
    _expand_print_variants_bulk,
    _expand_sets_bulk,
    _in_filter,
    _parse_csv,
    _parse_expand,
    _resolve_text,
    _stripe,
    _upsert_text_fk,
)

router = APIRouter(prefix="/naips", tags=["naips"])

_JUNCTION_EXPAND_FIELDS = {"colors", "tribes", "attrs", "keywords", "reswords"}
_DETAIL_EXPAND_FIELDS = {
    "card",
    "set",
    "artist",
    "print_variant",
    "language",
    "cardtype",
    "block",
} | _JUNCTION_EXPAND_FIELDS
_LIST_EXPAND_FIELDS = {"card", "set", "print_variant", "language", "artist"} | _JUNCTION_EXPAND_FIELDS


# ── Response / write models ──────────────────────────────────────────────────


class NaipDetail(BaseModel):
    id: int
    card: int | ExpandedCard
    set: int | ExpandedSet
    artist: int | ExpandedArtist | None = None
    print_variant: int | ExpandedPrintVariant
    language: int | ExpandedLanguage | None = None
    image_fk: int | None = None
    image_path: str | None = None
    cardtype: int | ExpandedCardType | None = None
    block: int | ExpandedBlock | None = None
    is_default: bool = False
    is_errata: bool = False
    is_foil: bool = False
    sort_order: int | None = None
    serial_max: int | None = None
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None
    name: str | None = None
    effect: str | None = None
    trigger: str | None = None
    colors: list[int] | list[LookupItem] = []
    tribes: list[int] | list[LookupItem] = []
    attrs: list[int] | list[LookupItem] = []
    keywords: list[int] | list[LookupItem] = []
    reswords: list[int] | list[LookupItem] = []


class NaipListItem(BaseModel):
    id: int
    card: int | ExpandedCard
    set: int | ExpandedSet
    print_variant: int | ExpandedPrintVariant
    language: int | ExpandedLanguage | None = None
    artist: int | ExpandedArtist | None = None
    cardtype: int | None = None
    block: int | None = None
    is_default: bool
    is_foil: bool
    is_errata: bool
    sort_order: int | None = None
    serial_max: int | None = None
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None
    name: str | None = None
    effect: str | None = None
    trigger: str | None = None
    image_path: str | None = None
    colors: list[int] | list[LookupItem] = []
    tribes: list[int] | list[LookupItem] = []
    attrs: list[int] | list[LookupItem] = []
    keywords: list[int] | list[LookupItem] = []
    reswords: list[int] | list[LookupItem] = []


class NaipListResponse(BaseModel):
    rows: list[NaipListItem]
    total: int


class NaipWrite(BaseModel):
    card_fk: int
    set_fk: int
    artist_fk: int | None = None
    print_variant_fk: int
    language_fk: int | None = None
    cardtype_fk: int | None = None
    block_fk: int | None = None
    is_default: bool = False
    is_errata: bool = False
    is_foil: bool = False
    sort_order: int | None = None
    serial_max: int | None = None
    power: int | None = Field(default=None, ge=0)
    life: int | None = Field(default=None, ge=0)
    counter: int | None = Field(default=None, ge=0)
    cost: int | None = Field(default=None, ge=0)
    name: str | None = None
    effect: str | None = None
    trigger: str | None = None
    colors: list[int] = []
    tribes: list[int] = []
    attrs: list[int] = []
    keywords: list[int] = []
    reswords: list[int] = []


# ── Helpers ──────────────────────────────────────────────────────────────────


def _clear_existing_default(card_fk: int, exclude_id: int | None, session: Session) -> None:
    existing = session.exec(select(Naip).where(Naip.card_fk == card_fk, Naip.is_default == True)).first()  # noqa: E712
    if existing and existing.id != exclude_id:
        existing.is_default = False
        session.add(existing)


def _sync_naip_junctions(naip: Naip, data: NaipWrite, session: Session) -> None:
    pairs = [
        (NaipColor, "color_fk", data.colors),
        (NaipTribe, "tribe_fk", data.tribes),
        (NaipAttribute, "attribute_fk", data.attrs),
        (NaipKeyword, "keyword_fk", data.keywords),
        (NaipResword, "resword_fk", data.reswords),
    ]
    for model, fk_field, ids in pairs:
        for row in session.exec(select(model).where(model.naip_fk == naip.id)).all():
            session.delete(row)
        session.flush()
        for fk_id in ids:
            session.add(model(**{"naip_fk": naip.id, fk_field: fk_id}))


def _enrich_naip(naip: Naip, session: Session, expand: set[str] | None = None) -> NaipDetail:
    expand = expand or set()

    image_path: str | None = None
    if naip.image_fk:
        row = session.exec(text("SELECT path FROM image WHERE id = :id").bindparams(id=naip.image_fk)).first()
        image_path = row[0] if row else None

    name = _resolve_text(session, Name, naip.name_fk, "name")
    extras = _bulk_naip_extras([naip.id], session, expand)[naip.id]

    card_map = _expand_cards_bulk([naip.card_fk], session) if "card" in expand else {}
    set_map = _expand_sets_bulk([naip.set_fk], session) if "set" in expand else {}
    artist_map = _expand_artists_bulk([naip.artist_fk], session) if "artist" in expand else {}
    pv_map = _expand_print_variants_bulk([naip.print_variant_fk], session) if "print_variant" in expand else {}
    lang_map = _expand_languages_bulk([naip.language_fk], session) if "language" in expand else {}
    ct_map = _expand_cardtypes_bulk([naip.cardtype_fk], session) if "cardtype" in expand else {}
    block_map = _expand_blocks_bulk([naip.block_fk], session) if "block" in expand else {}

    return NaipDetail(
        id=naip.id,
        card=card_map.get(naip.card_fk, naip.card_fk),
        set=set_map.get(naip.set_fk, naip.set_fk),
        artist=_stripe(naip.artist_fk, "artist", expand, artist_map),
        print_variant=pv_map.get(naip.print_variant_fk, naip.print_variant_fk),
        language=_stripe(naip.language_fk, "language", expand, lang_map),
        image_fk=naip.image_fk,
        image_path=image_path,
        cardtype=_stripe(naip.cardtype_fk, "cardtype", expand, ct_map),
        block=_stripe(naip.block_fk, "block", expand, block_map),
        is_default=naip.is_default,
        is_errata=naip.is_errata,
        is_foil=naip.is_foil,
        sort_order=naip.sort_order,
        serial_max=naip.serial_max,
        power=naip.power,
        life=naip.life,
        counter=naip.counter,
        cost=naip.cost,
        name=name,
        effect=extras["effect"],
        trigger=extras["trigger"],
        colors=extras["colors"],
        tribes=extras["tribes"],
        attrs=extras["attrs"],
        keywords=extras["keywords"],
        reswords=extras["reswords"],
    )


def _apply_write(naip: Naip, data: NaipWrite, session: Session) -> None:
    naip.card_fk = data.card_fk
    naip.set_fk = data.set_fk
    naip.artist_fk = data.artist_fk
    naip.print_variant_fk = data.print_variant_fk
    naip.language_fk = data.language_fk
    naip.cardtype_fk = data.cardtype_fk
    naip.block_fk = data.block_fk
    naip.is_errata = data.is_errata
    naip.is_foil = data.is_foil
    naip.sort_order = data.sort_order
    naip.serial_max = data.serial_max
    naip.power = data.power
    naip.life = data.life
    naip.counter = data.counter
    naip.cost = data.cost
    naip.name_fk = _upsert_text_fk(session, Name, "name", data.name)
    naip.effect_fk = _upsert_text_fk(session, Effect, "effect", data.effect)
    naip.trigger_fk = _upsert_text_fk(session, Trigger, "trigger", data.trigger)
    if data.is_default:
        _clear_existing_default(data.card_fk, naip.id, session)
    naip.is_default = data.is_default
    session.add(naip)


# ── Faceted filtering (mirrors logpiece's FilterSpec semantics, naip-flat view) ───────────────


def _build_naip_filters(
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
            "(COALESCE(nm.name, cnm.name) LIKE :search "
            'OR EXISTS (SELECT 1 FROM "set" s2 WHERE s2.id = n.set_fk AND s2.code LIKE :search) '
            "OR EXISTS (SELECT 1 FROM card_type ct2 WHERE ct2.id = c.cardtype_fk AND ct2.name LIKE :search) "
            "OR EXISTS (SELECT 1 FROM naip_color nc2 JOIN color co2 ON co2.id = nc2.color_fk "
            "WHERE nc2.naip_fk = n.id AND co2.name LIKE :search))"
        )
        params["search"] = f"%{search}%"

    any_names = _parse_csv(color_names_any)
    if any_names:
        sql, p = _in_filter("co.name", any_names, "canyn")
        conditions.append(
            "EXISTS (SELECT 1 FROM naip_color nc JOIN color co ON co.id = nc.color_fk "
            f"WHERE nc.naip_fk = n.id AND {sql})"
        )
        params.update(p)

    exact_names = _parse_csv(color_names_exact)
    if exact_names:
        sql, p = _in_filter("co3.name", exact_names, "cexn")
        conditions.append(
            "(SELECT COUNT(DISTINCT nc3.color_fk) FROM naip_color nc3 WHERE nc3.naip_fk = n.id) = :n_exact_colors "
            "AND NOT EXISTS (SELECT 1 FROM naip_color nc4 JOIN color co3 ON co3.id = nc4.color_fk "
            f"WHERE nc4.naip_fk = n.id AND NOT {sql})"
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
        conditions.append(f'n.set_fk IN (SELECT id FROM "set" WHERE type_fk IN (SELECT id FROM set_type WHERE {sql}))')
        params.update(p)

    codes = _parse_csv(set_codes)
    if codes:
        sql, p = _in_filter("code", codes, "setc")
        conditions.append(f'n.set_fk IN (SELECT id FROM "set" WHERE {sql})')
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
            f"WHERE j.card_fk = n.card_fk AND {sql})"
        )
        params.update(p)

    artists = _parse_csv(artist_names)
    if artists:
        sql, p = _in_filter("name", artists, "art")
        conditions.append(f"n.artist_fk IN (SELECT id FROM artist WHERE {sql})")
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
            f'n.set_fk IN (SELECT id FROM "set" WHERE language_fk IN (SELECT id FROM language WHERE {sql}))'
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
        conditions.append("n.is_errata = 1")
    if serial:
        conditions.append("n.serial_max IS NOT NULL")
    if foil:
        conditions.append("n.is_foil = 1")

    pvs = _parse_csv(print_variant_symbols)
    if pvs:
        sql, p = _in_filter("symbol", pvs, "pvs")
        conditions.append(f"n.print_variant_fk IN (SELECT id FROM print_variant WHERE {sql})")
        params.update(p)

    return conditions, params


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/", response_model=NaipListResponse, dependencies=[Depends(require_read_key)])
def list_naips(
    card_fk: int | None = Query(None),
    set_id: int | None = Query(None),
    language_id: int | None = Query(None),
    print_variant_id: int | None = Query(None),
    is_default: bool | None = Query(None),
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
    if card_fk is not None:
        conditions.append("n.card_fk = :card_fk")
        filter_params["card_fk"] = card_fk
    if set_id is not None:
        conditions.append("n.set_fk = :set_id")
        filter_params["set_id"] = set_id
    if language_id is not None:
        conditions.append("n.language_fk = :language_id")
        filter_params["language_id"] = language_id
    if print_variant_id is not None:
        conditions.append("n.print_variant_fk = :print_variant_id")
        filter_params["print_variant_id"] = print_variant_id
    if is_default is not None:
        conditions.append("n.is_default = :is_default")
        filter_params["is_default"] = int(is_default)
    extra_conditions, extra_params = _build_naip_filters(
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
    # The card + card-name joins only feed the new faceted filters above (cardtype/rarity/cost/
    # block/etc. and the search fallback) — always present so `where` can reference c.*/cnm.* freely.
    joins = (
        "LEFT JOIN name nm ON nm.id = n.name_fk "
        "LEFT JOIN image img ON img.id = n.image_fk "
        "LEFT JOIN card c ON c.id = n.card_fk "
        "LEFT JOIN name cnm ON cnm.id = c.name_fk "
    )
    rows = session.exec(
        text(
            "SELECT n.id, n.card_fk, n.set_fk, n.print_variant_fk, n.language_fk, "
            "n.is_default, n.is_foil, n.is_errata, "
            "nm.name, img.path, n.artist_fk, n.cardtype_fk, n.block_fk, "
            "n.sort_order, n.serial_max, n.power, n.life, n.counter, n.cost "
            f"FROM naip n {joins}"
            f"{where} ORDER BY n.card_fk, n.set_fk, n.sort_order LIMIT :limit OFFSET :offset"
        ).bindparams(**filter_params, limit=limit, offset=offset)
    ).all()
    total = session.exec(text(f"SELECT COUNT(*) FROM naip n {joins}{where}").bindparams(**filter_params)).scalar()

    expand_set = _parse_expand(expand, _LIST_EXPAND_FIELDS)

    card_map = _expand_cards_bulk([r[1] for r in rows], session) if "card" in expand_set else {}
    set_map = _expand_sets_bulk([r[2] for r in rows], session) if "set" in expand_set else {}
    pv_map = _expand_print_variants_bulk([r[3] for r in rows], session) if "print_variant" in expand_set else {}
    lang_map = _expand_languages_bulk([r[4] for r in rows], session) if "language" in expand_set else {}
    artist_map = _expand_artists_bulk([r[10] for r in rows], session) if "artist" in expand_set else {}
    naip_extras = _bulk_naip_extras([r[0] for r in rows], session, expand_set)

    return NaipListResponse(
        rows=[
            NaipListItem(
                id=r[0],
                card=card_map.get(r[1], r[1]),
                set=set_map.get(r[2], r[2]),
                print_variant=pv_map.get(r[3], r[3]),
                language=_stripe(r[4], "language", expand_set, lang_map),
                artist=_stripe(r[10], "artist", expand_set, artist_map),
                cardtype=r[11],
                block=r[12],
                is_default=bool(r[5]),
                is_foil=bool(r[6]),
                is_errata=bool(r[7]),
                sort_order=r[13],
                serial_max=r[14],
                power=r[15],
                life=r[16],
                counter=r[17],
                cost=r[18],
                name=r[8],
                image_path=r[9],
                **naip_extras[r[0]],
            )
            for r in rows
        ],
        total=total or 0,
    )


@router.get("/{naip_id}", response_model=NaipDetail, dependencies=[Depends(require_read_key)])
def get_naip(naip_id: int, expand: str | None = Query(None), session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
    expand_set = _parse_expand(expand, _DETAIL_EXPAND_FIELDS)
    return _enrich_naip(naip, session, expand_set)


@router.post("/", response_model=NaipDetail, status_code=201, dependencies=[Depends(require_edit_key)])
def create_naip(data: NaipWrite, session: Session = Depends(get_session)):
    naip = Naip()
    _apply_write(naip, data, session)
    session.flush()
    _sync_naip_junctions(naip, data, session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="A default naip already exists for this card")
    session.refresh(naip)
    return _enrich_naip(naip, session)


@router.put("/{naip_id}", response_model=NaipDetail, dependencies=[Depends(require_edit_key)])
def update_naip(naip_id: int, data: NaipWrite, session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
    _apply_write(naip, data, session)
    session.flush()
    _sync_naip_junctions(naip, data, session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="A default naip already exists for this card")
    session.refresh(naip)
    return _enrich_naip(naip, session)


@router.delete("/{naip_id}", status_code=204, dependencies=[Depends(require_edit_key)])
def delete_naip(naip_id: int, session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
    old_img_fk = naip.image_fk
    for model in (NaipColor, NaipTribe, NaipAttribute, NaipKeyword, NaipResword):
        for row in session.exec(select(model).where(model.naip_fk == naip_id)).all():
            session.delete(row)
    serial_img_fks = []
    for serial in session.exec(select(NaipSerial).where(NaipSerial.naip_fk == naip_id)).all():
        if serial.image_fk:
            serial_img_fks.append(serial.image_fk)
        session.delete(serial)
    session.delete(naip)
    session.flush()
    for fk in serial_img_fks:
        cleanup_orphaned_image(fk, session)
    cleanup_orphaned_image(old_img_fk, session)
    session.commit()


@router.post("/{naip_id}/image-url", response_model=NaipDetail, dependencies=[Depends(require_edit_key)])
async def upload_naip_image_from_url(naip_id: int, payload: ImageUrlPayload, session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
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
    img = save_image(raw, suffix, session)
    replace_naip_image(naip, img.id, session)
    session.commit()
    session.refresh(naip)
    return _enrich_naip(naip, session)


@router.post("/{naip_id}/image", response_model=NaipDetail, dependencies=[Depends(require_edit_key)])
async def upload_naip_image(naip_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
    suffix = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if suffix not in VALID_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only jpg, png, webp images are accepted")
    raw = await file.read()
    if len(raw) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MB limit")
    img = save_image(raw, suffix, session)
    replace_naip_image(naip, img.id, session)
    session.commit()
    session.refresh(naip)
    return _enrich_naip(naip, session)
