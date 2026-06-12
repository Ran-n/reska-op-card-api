#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/05/13 13:13:00.000000
"""

from pathlib import Path

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, text

from optcg_api._images import (
    VALID_SUFFIXES,
    cleanup_orphaned_image,
    replace_naip_image,
    save_image,
)
from optcg_api.database import get_session
from optcg_api.models import (
    BannedPair,
    Block,
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
from optcg_api.routers._common import ImageUrlPayload, LookupItem, _resolve_text, _upsert_text_fk

router = APIRouter(prefix="/cards", tags=["cards"])


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


class CardDetail(BaseModel):
    id: int
    set_fk: int
    cardtype_fk: int
    rarity_fk: int | None = None
    number: int
    name: str
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
    blocks: list[LookupItem] = []
    formats: list[LookupItem] = []
    keywords: list[LookupItem] = []
    reswords: list[LookupItem] = []
    naips: list[NaipItem] = []


class CardListItem(BaseModel):
    id: int
    set_fk: int
    cardtype_fk: int
    number: int
    name: str
    cost: int | None = None
    power: int | None = None
    counter: int | None = None
    set_code: str | None = None
    cardtype_name: str | None = None
    colors: str | None = None
    rarity_symbol: str | None = None
    image_path: str | None = None


class CardListResponse(BaseModel):
    rows: list[CardListItem]
    total: int


class CardWrite(BaseModel):
    set_fk: int
    cardtype_fk: int
    rarity_fk: int | None = None
    number: int = Field(ge=1)
    name: str
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


def _enrich(card: Card, session: Session) -> CardDetail:
    row = session.exec(
        text(
            "SELECT s.code, s.name, ct.name, ct.symbol, r.name, r.symbol "
            'FROM "set" s '
            "JOIN card_type ct ON ct.id = :ct "
            "LEFT JOIN rarity r ON r.id = :rid "
            "WHERE s.id = :s"
        ).bindparams(ct=card.cardtype_fk, s=card.set_fk, rid=card.rarity_fk)
    ).first()
    set_code, set_name, ct_name, ct_sym, rarity_name, rarity_sym = row if row else (None, None, None, None, None, None)

    card_name = _resolve_text(session, Name, card.name_fk, "name") or ""
    effect = _resolve_text(session, Effect, card.effect_fk, "effect")
    trigger = _resolve_text(session, Trigger, card.trigger_fk, "trigger")

    naip_rows = session.exec(
        text(
            "SELECT n.id, COALESCE(nm.name, ''), a.name, pv.name, pv.symbol, s.code, "
            "n.image_fk, n.is_default, n.is_errata, n.is_foil, img.path "
            "FROM naip n "
            "LEFT JOIN name nm ON nm.id = n.name_fk "
            "LEFT JOIN artist a ON a.id = n.artist_fk "
            "LEFT JOIN print_variant pv ON pv.id = n.print_variant_fk "
            'LEFT JOIN "set" s ON s.id = n.set_fk '
            "LEFT JOIN image img ON img.id = n.image_fk "
            "WHERE n.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
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
        )
        for r in naip_rows
    ]

    color_rows = session.exec(
        text(
            "SELECT co.id, co.name FROM color co JOIN card_color cc ON cc.color_fk = co.id WHERE cc.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
    tribe_rows = session.exec(
        text(
            "SELECT t.id, t.name FROM tribe t JOIN card_tribe ct ON ct.tribe_fk = t.id WHERE ct.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
    attr_rows = session.exec(
        text(
            "SELECT a.id, a.name FROM attribute a "
            "JOIN card_attribute ca ON ca.attribute_fk = a.id WHERE ca.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
    block_obj = session.get(Block, card.block_fk) if card.block_fk else None
    block_rows = [(block_obj.id, block_obj.name)] if block_obj else []
    format_rows = session.exec(
        text(
            "SELECT f.id, f.name FROM format f JOIN card_format cf ON cf.format_fk = f.id WHERE cf.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
    kw_rows = session.exec(
        text(
            "SELECT k.id, k.name FROM keyword k JOIN card_keyword ck ON ck.keyword_fk = k.id WHERE ck.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
    rw_rows = session.exec(
        text(
            "SELECT r.id, r.name FROM resword r JOIN card_resword cr ON cr.resword_fk = r.id WHERE cr.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()

    return CardDetail(
        id=card.id,
        set_fk=card.set_fk,
        cardtype_fk=card.cardtype_fk,
        rarity_fk=card.rarity_fk,
        number=card.number,
        name=card_name,
        effect=effect,
        trigger=trigger,
        power=card.power,
        life=card.life,
        counter=card.counter,
        cost=card.cost,
        set_code=set_code,
        set_name=set_name,
        cardtype_name=ct_name,
        cardtype_symbol=ct_sym,
        rarity_name=rarity_name,
        rarity_symbol=rarity_sym,
        colors=[LookupItem(id=r[0], name=r[1]) for r in color_rows],
        tribes=[LookupItem(id=r[0], name=r[1]) for r in tribe_rows],
        attrs=[LookupItem(id=r[0], name=r[1]) for r in attr_rows],
        blocks=[LookupItem(id=r[0], name=r[1]) for r in block_rows],
        formats=[LookupItem(id=r[0], name=r[1]) for r in format_rows],
        keywords=[LookupItem(id=r[0], name=r[1]) for r in kw_rows],
        reswords=[LookupItem(id=r[0], name=r[1]) for r in rw_rows],
        naips=naips,
    )


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


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.get("/", response_model=CardListResponse)
def list_cards(
    name: str | None = Query(None),
    set_id: int | None = Query(None),
    cardtype_id: int | None = Query(None),
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

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = session.exec(
        text(
            f"SELECT c.id, c.set_fk, c.cardtype_fk, c.number, nm.name, c.cost, c.power, c.counter, "
            f"s.code, ct.name, "
            f"(SELECT GROUP_CONCAT(co.name, ',') FROM color co "
            f" JOIN card_color cc ON cc.color_fk = co.id WHERE cc.card_fk = c.id), "
            f"r.symbol, "
            f"(SELECT img.path FROM naip n LEFT JOIN image img ON img.id = n.image_fk "
            f" WHERE n.card_fk = c.id AND n.is_default = 1 LIMIT 1) "
            f"FROM card c "
            f"LEFT JOIN name nm ON nm.id = c.name_fk "
            f'LEFT JOIN "set" s ON s.id = c.set_fk '
            f"LEFT JOIN card_type ct ON ct.id = c.cardtype_fk "
            f"LEFT JOIN rarity r ON r.id = c.rarity_fk "
            f"{where} ORDER BY s.code, c.number LIMIT :limit OFFSET :offset"
        ).bindparams(**filter_params, limit=limit, offset=offset)
    ).all()
    total = session.exec(
        text(f"SELECT COUNT(*) FROM card c LEFT JOIN name nm ON nm.id = c.name_fk {where}").bindparams(**filter_params)
    ).scalar()

    return CardListResponse(
        rows=[
            CardListItem(
                id=r[0],
                set_fk=r[1],
                cardtype_fk=r[2],
                number=r[3],
                name=r[4] or "",
                cost=r[5],
                power=r[6],
                counter=r[7],
                set_code=r[8],
                cardtype_name=r[9],
                colors=r[10],
                rarity_symbol=r[11],
                image_path=r[12],
            )
            for r in rows
        ],
        total=total or 0,
    )


@router.get("/{card_id}", response_model=CardDetail)
def get_card(card_id: int, session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return _enrich(card, session)


@router.post("/", response_model=CardDetail, status_code=201)
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
    session.commit()
    session.refresh(card)
    return _enrich(card, session)


@router.put("/{card_id}", response_model=CardDetail)
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
    session.commit()
    session.refresh(card)
    return _enrich(card, session)


@router.delete("/{card_id}", status_code=204)
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


@router.post("/{card_id}/image-url", response_model=CardDetail)
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
    _set_card_image(card, raw, suffix, session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Conflict setting default naip image; retry")
    session.refresh(card)
    return _enrich(card, session)


@router.post("/{card_id}/image", response_model=CardDetail)
async def upload_card_image(card_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    suffix = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if suffix not in VALID_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only jpg, png, webp images are accepted")
    raw = await file.read()
    _set_card_image(card, raw, suffix, session)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Conflict setting default naip image; retry")
    session.refresh(card)
    return _enrich(card, session)
