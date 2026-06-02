#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/30 00:00:00.000000
Revised: 2026/05/30 00:00:00.000000
"""

from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select, text

from optcg_api._images import (
    VALID_SUFFIXES,
    cleanup_orphaned_image,
    replace_naip_image,
    save_image_bytes,
    upsert_image_row,
)
from optcg_api.database import get_session
from optcg_api.models import (
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

router = APIRouter(prefix="/naips", tags=["naips"])


# ── Response / write models ──────────────────────────────────────────────────


class LookupItem(BaseModel):
    id: int
    name: str
    symbol: str | None = None


class NaipDetail(BaseModel):
    id: int
    card_fk: int
    set_fk: int
    artist_fk: int | None = None
    print_variant_fk: int
    language_fk: int | None = None
    image_fk: int | None = None
    cardtype_fk: int | None = None
    block_fk: int | None = None
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
    artist_name: str | None = None
    print_variant_name: str | None = None
    print_variant_symbol: str | None = None
    set_code: str | None = None
    cardtype_name: str | None = None
    cardtype_symbol: str | None = None
    language_code: str | None = None
    colors: list[LookupItem] = []
    tribes: list[LookupItem] = []
    attrs: list[LookupItem] = []
    keywords: list[LookupItem] = []
    reswords: list[LookupItem] = []


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
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None
    name: str | None = None
    effect: str | None = None
    trigger: str | None = None
    colors: list[int] = []
    tribes: list[int] = []
    attrs: list[int] = []
    keywords: list[int] = []
    reswords: list[int] = []


class ImageUrlPayload(BaseModel):
    url: str


# ── Helpers ──────────────────────────────────────────────────────────────────


def _resolve_text(session: Session, model, pk: int | None, field: str) -> str | None:
    if pk is None:
        return None
    obj = session.get(model, pk)
    return getattr(obj, field, None) if obj else None


def _upsert_text_fk(session: Session, model, field: str, value: str | None) -> int | None:
    if not value:
        return None
    existing = session.exec(select(model).where(getattr(model, field) == value)).first()
    if existing:
        return existing.id
    obj = model(**{field: value})
    session.add(obj)
    session.flush()
    return obj.id


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


def _enrich_naip(naip: Naip, session: Session) -> NaipDetail:
    row = session.exec(
        text(
            "SELECT a.name, pv.name, pv.symbol, s.code, ct.name, ct.symbol, l.code "
            "FROM naip n "
            "LEFT JOIN artist a ON a.id = n.artist_fk "
            "LEFT JOIN print_variant pv ON pv.id = n.print_variant_fk "
            'LEFT JOIN "set" s ON s.id = n.set_fk '
            "LEFT JOIN card_type ct ON ct.id = n.cardtype_fk "
            "LEFT JOIN language l ON l.id = n.language_fk "
            "WHERE n.id = :nid"
        ).bindparams(nid=naip.id)
    ).first()
    artist_name, pv_name, pv_symbol, set_code, ct_name, ct_sym, lang_code = (
        row if row else (None, None, None, None, None, None, None)
    )

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

    return NaipDetail(
        id=naip.id,
        card_fk=naip.card_fk,
        set_fk=naip.set_fk,
        artist_fk=naip.artist_fk,
        print_variant_fk=naip.print_variant_fk,
        language_fk=naip.language_fk,
        image_fk=naip.image_fk,
        cardtype_fk=naip.cardtype_fk,
        block_fk=naip.block_fk,
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
        artist_name=artist_name,
        print_variant_name=pv_name,
        print_variant_symbol=pv_symbol,
        set_code=set_code,
        cardtype_name=ct_name,
        cardtype_symbol=ct_sym,
        language_code=lang_code,
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


@router.get("/{naip_id}", response_model=NaipDetail)
def get_naip(naip_id: int, session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
    return _enrich_naip(naip, session)


@router.post("/", response_model=NaipDetail, status_code=201)
def create_naip(data: NaipWrite, session: Session = Depends(get_session)):
    naip = Naip()
    _apply_write(naip, data, session)
    session.flush()
    _sync_naip_junctions(naip, data, session)
    session.commit()
    session.refresh(naip)
    return _enrich_naip(naip, session)


@router.put("/{naip_id}", response_model=NaipDetail)
def update_naip(naip_id: int, data: NaipWrite, session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
    _apply_write(naip, data, session)
    session.flush()
    _sync_naip_junctions(naip, data, session)
    session.commit()
    session.refresh(naip)
    return _enrich_naip(naip, session)


@router.delete("/{naip_id}", status_code=204)
def delete_naip(naip_id: int, session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
    old_img_fk = naip.image_fk
    for model in (NaipColor, NaipTribe, NaipAttribute, NaipKeyword, NaipResword):
        for row in session.exec(select(model).where(model.naip_fk == naip_id)).all():
            session.delete(row)
    for serial in session.exec(select(NaipSerial).where(NaipSerial.naip_fk == naip_id)).all():
        serial_img_fk = serial.image_fk
        session.delete(serial)
        session.flush()
        cleanup_orphaned_image(serial_img_fk, session)
    session.delete(naip)
    session.flush()
    cleanup_orphaned_image(old_img_fk, session)
    session.commit()


@router.post("/{naip_id}/image-url", response_model=NaipDetail)
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
    filename = save_image_bytes(raw, suffix)
    img = upsert_image_row(filename, session)
    replace_naip_image(naip, img.id, session)
    session.commit()
    session.refresh(naip)
    return _enrich_naip(naip, session)


@router.post("/{naip_id}/image", response_model=NaipDetail)
async def upload_naip_image(naip_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    naip = session.get(Naip, naip_id)
    if not naip:
        raise HTTPException(status_code=404, detail="Naip not found")
    suffix = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if suffix not in VALID_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only jpg, png, webp images are accepted")
    raw = await file.read()
    filename = save_image_bytes(raw, suffix)
    img = upsert_image_row(filename, session)
    replace_naip_image(naip, img.id, session)
    session.commit()
    session.refresh(naip)
    return _enrich_naip(naip, session)
