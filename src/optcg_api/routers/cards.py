#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/05/15 13:07:38.600229
"""

import shutil
import urllib.request
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlmodel import Session, select, text

from optcg_api.database import get_session
from optcg_api.models import (
    Card,
    CardAttribute,
    CardBlock,
    CardColor,
    CardFormat,
    CardKeyword,
    CardRarity,
    CardResword,
    CardTribe,
    Effect,
    Image,
    Naip,
    Name,
    Trigger,
)

IMAGES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(prefix="/cards", tags=["cards"])


# ── Rich response models ─────────────────────────────────────────────────────


class LookupItem(BaseModel):
    id: int
    name: str
    symbol: str | None = None


class NaipItem(BaseModel):
    id: int
    name: str
    artist_name: str | None = None
    rarity_name: str | None = None


class CardDetail(BaseModel):
    id: int
    set_fk: int
    cardtype_fk: int
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
    colors: list[LookupItem] = []
    tribes: list[LookupItem] = []
    attrs: list[LookupItem] = []
    rarities: list[LookupItem] = []
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


class CardListResponse(BaseModel):
    rows: list[CardListItem]
    total: int


class CardWrite(BaseModel):
    set_fk: int
    cardtype_fk: int
    number: int
    name: str
    effect: str | None = None
    trigger: str | None = None
    power: int | None = None
    life: int | None = None
    counter: int | None = None
    cost: int | None = None
    colors: list[int] = []
    tribes: list[int] = []
    attrs: list[int] = []
    rarities: list[int] = []
    blocks: list[int] = []
    formats: list[int] = []
    keywords: list[int] = []
    reswords: list[int] = []


# ── Helpers ──────────────────────────────────────────────────────────────────


def _resolve_text(session: Session, model, pk: int | None, field: str) -> str | None:
    if pk is None:
        return None
    obj = session.get(model, pk)
    return getattr(obj, field, None) if obj else None


def _enrich(card: Card, session: Session) -> CardDetail:
    row = session.exec(
        text(
            'SELECT s.code, s.name, ct.name, ct.symbol FROM "set" s JOIN card_type ct ON ct.id = :ct WHERE s.id = :s'
        ).bindparams(ct=card.cardtype_fk, s=card.set_fk)
    ).first()
    set_code, set_name, ct_name, ct_sym = row if row else (None, None, None, None)

    card_name = _resolve_text(session, Name, card.name_fk, "name") or ""
    effect = _resolve_text(session, Effect, card.effect_fk, "effect")
    trigger = _resolve_text(session, Trigger, card.trigger_fk, "trigger")

    naip_rows = session.exec(
        text(
            "SELECT n.id, COALESCE(nm.name, ''), a.name, r.name FROM naip n "
            "LEFT JOIN name nm ON nm.id = n.name_fk "
            "LEFT JOIN artist a ON a.id = n.artist_fk "
            "LEFT JOIN rarity r ON r.id = n.rarity_fk "
            "WHERE n.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
    naips = [NaipItem(id=r[0], name=r[1], artist_name=r[2], rarity_name=r[3]) for r in naip_rows]

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
    rarity_rows = session.exec(
        text(
            "SELECT r.id, r.name, r.symbol FROM rarity r "
            "JOIN card_rarity cr ON cr.rarity_fk = r.id WHERE cr.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
    block_rows = session.exec(
        text(
            "SELECT b.id, b.name FROM block b JOIN card_block cb ON cb.block_fk = b.id WHERE cb.card_fk = :cid"
        ).bindparams(cid=card.id)
    ).all()
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
        colors=[LookupItem(id=r[0], name=r[1]) for r in color_rows],
        tribes=[LookupItem(id=r[0], name=r[1]) for r in tribe_rows],
        attrs=[LookupItem(id=r[0], name=r[1]) for r in attr_rows],
        rarities=[LookupItem(id=r[0], name=r[1], symbol=r[2]) for r in rarity_rows],
        blocks=[LookupItem(id=r[0], name=r[1]) for r in block_rows],
        formats=[LookupItem(id=r[0], name=r[1]) for r in format_rows],
        keywords=[LookupItem(id=r[0], name=r[1]) for r in kw_rows],
        reswords=[LookupItem(id=r[0], name=r[1]) for r in rw_rows],
        naips=naips,
    )


def _sync_junctions(card_id: int, data: CardWrite, session: Session):
    pairs = [
        (CardColor, "color_fk", data.colors),
        (CardTribe, "tribe_fk", data.tribes),
        (CardAttribute, "attribute_fk", data.attrs),
        (CardRarity, "rarity_fk", data.rarities),
        (CardBlock, "block_fk", data.blocks),
        (CardFormat, "format_fk", data.formats),
        (CardKeyword, "keyword_fk", data.keywords),
        (CardResword, "resword_fk", data.reswords),
    ]
    for model, fk_field, ids in pairs:
        existing = session.exec(select(model).where(model.card_fk == card_id)).all()
        for row in existing:
            session.delete(row)
        session.flush()
        for fk_id in ids:
            session.add(model(**{"card_fk": card_id, fk_field: fk_id}))


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
    params: dict = {"offset": offset, "limit": limit}
    if name:
        conditions.append("nm.name LIKE :name")
        params["name"] = f"%{name}%"
    if set_id is not None:
        conditions.append("c.set_fk = :set_id")
        params["set_id"] = set_id
    if cardtype_id is not None:
        conditions.append("c.cardtype_fk = :cardtype_id")
        params["cardtype_id"] = cardtype_id

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    rows = session.exec(
        text(
            f"SELECT c.id, c.set_fk, c.cardtype_fk, c.number, nm.name, c.cost, c.power, c.counter, "
            f"s.code, ct.name "
            f"FROM card c "
            f"LEFT JOIN name nm ON nm.id = c.name_fk "
            f'LEFT JOIN "set" s ON s.id = c.set_fk '
            f"LEFT JOIN card_type ct ON ct.id = c.cardtype_fk "
            f"{where} ORDER BY s.code, c.number LIMIT :limit OFFSET :offset"
        ).bindparams(**params)
    ).all()
    total = session.exec(
        text(f"SELECT COUNT(*) FROM card c LEFT JOIN name nm ON nm.id = c.name_fk {where}").bindparams(
            **{k: v for k, v in params.items() if k not in ("limit", "offset")}
        )
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


@router.post("/", response_model=CardDetail, status_code=201)
def create_card(data: CardWrite, session: Session = Depends(get_session)):
    name_fk = _upsert_text_fk(session, Name, "name", data.name)
    effect_fk = _upsert_text_fk(session, Effect, "effect", data.effect)
    trigger_fk = _upsert_text_fk(session, Trigger, "trigger", data.trigger)
    card = Card(
        set_fk=data.set_fk,
        cardtype_fk=data.cardtype_fk,
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
    _sync_junctions(card.id, data, session)
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
    _sync_junctions(card_id, data, session)
    session.commit()
    session.refresh(card)
    return _enrich(card, session)


@router.delete("/{card_id}", status_code=204)
def delete_card(card_id: int, session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    for naip in session.exec(select(Naip).where(Naip.card_fk == card_id)).all():
        if naip.image_fk:
            img = session.get(Image, naip.image_fk)
            if img:
                old = IMAGES_DIR / img.path
                if old.exists():
                    old.unlink()
                session.delete(img)
        session.delete(naip)
    for model in (CardColor, CardTribe, CardAttribute, CardRarity, CardBlock, CardFormat, CardKeyword, CardResword):
        for row in session.exec(select(model).where(model.card_fk == card_id)).all():
            session.delete(row)
    session.delete(card)
    session.commit()


class ImageUrlPayload(BaseModel):
    url: str


def _set_card_image(card: Card, filename: str, session: Session) -> None:
    """Upsert an Image row and link it to the card's default Naip."""
    existing_img = session.exec(select(Image).where(Image.path == filename)).first()
    if existing_img:
        img = existing_img
    else:
        img = Image(path=filename)
        session.add(img)
        session.flush()

    naip = session.exec(select(Naip).where(Naip.card_fk == card.id, Naip.is_default == True)).first()  # noqa: E712
    if naip:
        naip.image_fk = img.id
        session.add(naip)
    else:
        session.add(Naip(card_fk=card.id, set_fk=card.set_fk, image_fk=img.id, is_default=True))


@router.post("/{card_id}/image-url", response_model=CardDetail)
async def upload_card_image_from_url(card_id: int, payload: ImageUrlPayload, session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    url = payload.url.strip()
    suffix = Path(url.split("?")[0]).suffix.lower() or ".jpg"
    if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        suffix = ".jpg"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {e}")
    filename = f"{card_id}{suffix}"
    (IMAGES_DIR / filename).write_bytes(raw)
    _set_card_image(card, filename, session)
    session.commit()
    session.refresh(card)
    return _enrich(card, session)


@router.post("/{card_id}/image", response_model=CardDetail)
async def upload_card_image(card_id: int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    card = session.get(Card, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    suffix = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if suffix not in (".jpg", ".jpeg", ".png", ".webp"):
        raise HTTPException(status_code=400, detail="Only jpg, png, webp images are accepted")
    filename = f"{card_id}{suffix}"
    dest = IMAGES_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    _set_card_image(card, filename, session)
    session.commit()
    session.refresh(card)
    return _enrich(card, session)
