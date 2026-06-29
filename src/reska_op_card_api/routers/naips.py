#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/30 00:00:00.000000
Revised: 2026/06/29 08:55:36.299211
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
    _expand_artists_bulk,
    _expand_blocks_bulk,
    _expand_cards_bulk,
    _expand_cardtypes_bulk,
    _expand_languages_bulk,
    _expand_print_variants_bulk,
    _expand_sets_bulk,
    _resolve_text,
    _stripe,
    _upsert_text_fk,
)

router = APIRouter(prefix="/naips", tags=["naips"])


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
    colors: list[LookupItem] = []
    tribes: list[LookupItem] = []
    attrs: list[LookupItem] = []
    keywords: list[LookupItem] = []
    reswords: list[LookupItem] = []


class NaipListItem(BaseModel):
    id: int
    card: int | ExpandedCard
    set: int | ExpandedSet
    print_variant: int | ExpandedPrintVariant
    language: int | ExpandedLanguage | None = None
    artist: int | ExpandedArtist | None = None
    is_default: bool
    is_foil: bool
    is_errata: bool
    name: str | None = None
    image_path: str | None = None


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
    effect = _resolve_text(session, Effect, naip.effect_fk, "effect")
    trigger = _resolve_text(session, Trigger, naip.trigger_fk, "trigger")

    color_rows = session.exec(
        text(
            "SELECT co.id, co.name FROM color co JOIN naip_color nc ON nc.color_fk = co.id WHERE nc.naip_fk = :nid"
        ).bindparams(nid=naip.id)
    ).all()
    tribe_rows = session.exec(
        text(
            "SELECT t.id, t.name FROM tribe t JOIN naip_tribe nt ON nt.tribe_fk = t.id WHERE nt.naip_fk = :nid"
        ).bindparams(nid=naip.id)
    ).all()
    attr_rows = session.exec(
        text(
            "SELECT a.id, a.name FROM attribute a "
            "JOIN naip_attribute na ON na.attribute_fk = a.id WHERE na.naip_fk = :nid"
        ).bindparams(nid=naip.id)
    ).all()
    kw_rows = session.exec(
        text(
            "SELECT k.id, k.name FROM keyword k JOIN naip_keyword nk ON nk.keyword_fk = k.id WHERE nk.naip_fk = :nid"
        ).bindparams(nid=naip.id)
    ).all()
    rw_rows = session.exec(
        text(
            "SELECT r.id, r.name FROM resword r JOIN naip_resword nr ON nr.resword_fk = r.id WHERE nr.naip_fk = :nid"
        ).bindparams(nid=naip.id)
    ).all()

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
        effect=effect,
        trigger=trigger,
        colors=[LookupItem(id=r[0], name=r[1]) for r in color_rows],
        tribes=[LookupItem(id=r[0], name=r[1]) for r in tribe_rows],
        attrs=[LookupItem(id=r[0], name=r[1]) for r in attr_rows],
        keywords=[LookupItem(id=r[0], name=r[1]) for r in kw_rows],
        reswords=[LookupItem(id=r[0], name=r[1]) for r in rw_rows],
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


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/", response_model=NaipListResponse, dependencies=[Depends(require_read_key)])
def list_naips(
    card_fk: int | None = Query(None),
    set_id: int | None = Query(None),
    language_id: int | None = Query(None),
    print_variant_id: int | None = Query(None),
    is_default: bool | None = Query(None),
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

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = session.exec(
        text(
            "SELECT n.id, n.card_fk, n.set_fk, n.print_variant_fk, n.language_fk, "
            "n.is_default, n.is_foil, n.is_errata, "
            "nm.name, img.path, n.artist_fk "
            "FROM naip n "
            "LEFT JOIN name nm ON nm.id = n.name_fk "
            "LEFT JOIN image img ON img.id = n.image_fk "
            f"{where} ORDER BY n.card_fk, n.set_fk, n.sort_order LIMIT :limit OFFSET :offset"
        ).bindparams(**filter_params, limit=limit, offset=offset)
    ).all()
    total = session.exec(text(f"SELECT COUNT(*) FROM naip n {where}").bindparams(**filter_params)).scalar()

    expand_set = {e.strip() for e in expand.split(",")} if expand else set()

    card_map = _expand_cards_bulk([r[1] for r in rows], session) if "card" in expand_set else {}
    set_map = _expand_sets_bulk([r[2] for r in rows], session) if "set" in expand_set else {}
    pv_map = _expand_print_variants_bulk([r[3] for r in rows], session) if "print_variant" in expand_set else {}
    lang_map = _expand_languages_bulk([r[4] for r in rows], session) if "language" in expand_set else {}
    artist_map = _expand_artists_bulk([r[10] for r in rows], session) if "artist" in expand_set else {}

    return NaipListResponse(
        rows=[
            NaipListItem(
                id=r[0],
                card=card_map.get(r[1], r[1]),
                set=set_map.get(r[2], r[2]),
                print_variant=pv_map.get(r[3], r[3]),
                language=_stripe(r[4], "language", expand_set, lang_map),
                artist=_stripe(r[10], "artist", expand_set, artist_map),
                is_default=bool(r[5]),
                is_foil=bool(r[6]),
                is_errata=bool(r[7]),
                name=r[8],
                image_path=r[9],
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
    expand_set = {e.strip() for e in expand.split(",")} if expand else set()
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
