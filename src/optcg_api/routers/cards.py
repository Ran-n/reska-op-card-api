import shutil
import urllib.request
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlmodel import Session, select, text

from optcg_api.database import get_session
from optcg_api.models import (
    Card, CardAttribute, CardBlock, CardColor, CardFormat,
    CardKeywords, CardRarity, CardReswords, CardTribe, Naip,
)

IMAGES_DIR = Path(__file__).parent.parent.parent.parent / "card_images"
IMAGES_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/cards", tags=["cards"])


# ── Rich response models ─────────────────────────────────────────────────────

class LookupItem(BaseModel):
    id: int
    name: str
    symbol: Optional[str] = None

class NaipItem(BaseModel):
    id: int
    name: str
    artist_name: Optional[str] = None
    rarity_name: Optional[str] = None

class CardDetail(BaseModel):
    id: int
    set_fk: int
    cardtype_fk: int
    number: int
    name: str
    desc: Optional[str] = None
    trigger: Optional[str] = None
    power: Optional[int] = None
    life: Optional[int] = None
    counter: Optional[int] = None
    cost: Optional[int] = None
    image_path: Optional[str] = None
    set_code: Optional[str] = None
    set_name: Optional[str] = None
    cardtype_name: Optional[str] = None
    cardtype_symbol: Optional[str] = None
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
    cost: Optional[int] = None
    power: Optional[int] = None
    counter: Optional[int] = None
    set_code: Optional[str] = None
    cardtype_name: Optional[str] = None

class CardListResponse(BaseModel):
    rows: list[CardListItem]
    total: int

class CardWrite(BaseModel):
    set_fk: int
    cardtype_fk: int
    number: int
    name: str
    desc: Optional[str] = None
    trigger: Optional[str] = None
    power: Optional[int] = None
    life: Optional[int] = None
    counter: Optional[int] = None
    cost: Optional[int] = None
    colors: list[int] = []
    tribes: list[int] = []
    attrs: list[int] = []
    rarities: list[int] = []
    blocks: list[int] = []
    formats: list[int] = []
    keywords: list[int] = []
    reswords: list[int] = []


# ── Helpers ──────────────────────────────────────────────────────────────────

def _enrich(card: Card, session: Session) -> CardDetail:
    row = session.exec(text(
        "SELECT s.code, s.name, ct.name, ct.symbol "
        "FROM \"set\" s JOIN cardtype ct ON ct.id = :ct "
        "WHERE s.id = :s"
    ).bindparams(ct=card.cardtype_fk, s=card.set_fk)).first()
    set_code, set_name, ct_name, ct_sym = row if row else (None, None, None, None)

    def m2m(join_table, fk_col, target_table, target_fk):
        rows = session.exec(text(
            f'SELECT t.id, t.name, t.symbol FROM "{target_table}" t '
            f'JOIN "{join_table}" j ON j.{target_fk} = t.id '
            f'WHERE j.card_fk = :cid'
        ).bindparams(cid=card.id)).all()
        return [LookupItem(id=r[0], name=r[1], symbol=r[2] if len(r) > 2 else None) for r in rows]

    def m2m_no_sym(join_table, fk_col, target_table, target_fk):
        rows = session.exec(text(
            f'SELECT t.id, t.name FROM "{target_table}" t '
            f'JOIN "{join_table}" j ON j.{target_fk} = t.id '
            f'WHERE j.card_fk = :cid'
        ).bindparams(cid=card.id)).all()
        return [LookupItem(id=r[0], name=r[1]) for r in rows]

    naip_rows = session.exec(text(
        'SELECT n.id, n.name, a.name, r.name FROM naip n '
        'LEFT JOIN artist a ON a.id = n.artist_fk '
        'LEFT JOIN rarity r ON r.id = n.rarity_fk '
        'WHERE n.card_fk = :cid'
    ).bindparams(cid=card.id)).all()
    naips = [NaipItem(id=r[0], name=r[1], artist_name=r[2], rarity_name=r[3]) for r in naip_rows]

    # colors and rarities have symbol, rest don't
    color_rows = session.exec(text(
        'SELECT co.id, co.name FROM color co JOIN cardcolor cc ON cc.color_fk = co.id WHERE cc.card_fk = :cid'
    ).bindparams(cid=card.id)).all()
    tribe_rows = session.exec(text(
        'SELECT t.id, t.name FROM tribe t JOIN cardtribe ct ON ct.tribe_fk = t.id WHERE ct.card_fk = :cid'
    ).bindparams(cid=card.id)).all()
    attr_rows = session.exec(text(
        'SELECT a.id, a.name FROM attribute a JOIN cardattribute ca ON ca.attribute_fk = a.id WHERE ca.card_fk = :cid'
    ).bindparams(cid=card.id)).all()
    rarity_rows = session.exec(text(
        'SELECT r.id, r.name, r.symbol FROM rarity r JOIN cardrarity cr ON cr.rarity_fk = r.id WHERE cr.card_fk = :cid'
    ).bindparams(cid=card.id)).all()
    block_rows = session.exec(text(
        'SELECT b.id, b.name FROM block b JOIN cardblock cb ON cb.block_fk = b.id WHERE cb.card_fk = :cid'
    ).bindparams(cid=card.id)).all()
    format_rows = session.exec(text(
        'SELECT f.id, f.name FROM format f JOIN cardformat cf ON cf.format_fk = f.id WHERE cf.card_fk = :cid'
    ).bindparams(cid=card.id)).all()
    kw_rows = session.exec(text(
        'SELECT k.id, k.name FROM keywords k JOIN cardkeywords ck ON ck.keywords_fk = k.id WHERE ck.card_fk = :cid'
    ).bindparams(cid=card.id)).all()
    rw_rows = session.exec(text(
        'SELECT r.id, r.name FROM reswords r JOIN cardreswords cr ON cr.reswords_fk = r.id WHERE cr.card_fk = :cid'
    ).bindparams(cid=card.id)).all()

    return CardDetail(
        **card.model_dump(),
        set_code=set_code, set_name=set_name,
        cardtype_name=ct_name, cardtype_symbol=ct_sym,
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
        (CardColor, 'color_fk', data.colors),
        (CardTribe, 'tribe_fk', data.tribes),
        (CardAttribute, 'attribute_fk', data.attrs),
        (CardRarity, 'rarity_fk', data.rarities),
        (CardBlock, 'block_fk', data.blocks),
        (CardFormat, 'format_fk', data.formats),
        (CardKeywords, 'keywords_fk', data.keywords),
        (CardReswords, 'reswords_fk', data.reswords),
    ]
    for model, fk_field, ids in pairs:
        existing = session.exec(select(model).where(model.card_fk == card_id)).all()
        for row in existing:
            session.delete(row)
        session.flush()
        for fk_id in ids:
            session.add(model(**{'card_fk': card_id, fk_field: fk_id}))


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", response_model=CardListResponse)
def list_cards(
    name: Optional[str] = Query(None),
    set_id: Optional[int] = Query(None),
    cardtype_id: Optional[int] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(60, ge=1, le=200),
    session: Session = Depends(get_session),
):
    conditions = []
    params: dict = {'offset': offset, 'limit': limit}
    if name:
        conditions.append("c.name LIKE :name")
        params['name'] = f'%{name}%'
    if set_id is not None:
        conditions.append("c.set_fk = :set_id")
        params['set_id'] = set_id
    if cardtype_id is not None:
        conditions.append("c.cardtype_fk = :cardtype_id")
        params['cardtype_id'] = cardtype_id

    where = ('WHERE ' + ' AND '.join(conditions)) if conditions else ''
    rows = session.exec(text(
        f'SELECT c.id, c.set_fk, c.cardtype_fk, c.number, c.name, c.cost, c.power, c.counter, '
        f's.code, ct.name '
        f'FROM card c '
        f'LEFT JOIN "set" s ON s.id = c.set_fk '
        f'LEFT JOIN cardtype ct ON ct.id = c.cardtype_fk '
        f'{where} ORDER BY s.code, c.number LIMIT :limit OFFSET :offset'
    ).bindparams(**params)).all()
    total = session.exec(text(f'SELECT COUNT(*) FROM card c {where}').bindparams(**{k: v for k, v in params.items() if k not in ('limit', 'offset')})).scalar()

    return CardListResponse(
        rows=[CardListItem(id=r[0], set_fk=r[1], cardtype_fk=r[2], number=r[3], name=r[4], cost=r[5], power=r[6], counter=r[7], set_code=r[8], cardtype_name=r[9]) for r in rows],
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
    card = Card(
        set_fk=data.set_fk, cardtype_fk=data.cardtype_fk, number=data.number,
        name=data.name, desc=data.desc, trigger=data.trigger,
        power=data.power, life=data.life, counter=data.counter, cost=data.cost,
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
    for field in ('set_fk', 'cardtype_fk', 'number', 'name', 'desc', 'trigger', 'power', 'life', 'counter', 'cost'):
        setattr(card, field, getattr(data, field))
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
    for model in (CardColor, CardTribe, CardAttribute, CardRarity, CardBlock, CardFormat, CardKeywords, CardReswords, Naip):
        for row in session.exec(select(model).where(model.card_fk == card_id)).all():
            session.delete(row)
    if card.image_path:
        old = IMAGES_DIR / card.image_path
        if old.exists():
            old.unlink()
    session.delete(card)
    session.commit()


class ImageUrlPayload(BaseModel):
    url: str

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
            data = resp.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch image: {e}")
    if card.image_path:
        old = IMAGES_DIR / card.image_path
        if old.exists():
            old.unlink()
    filename = f"{card_id}{suffix}"
    dest = IMAGES_DIR / filename
    dest.write_bytes(data)
    card.image_path = filename
    session.add(card)
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
    if card.image_path:
        old = IMAGES_DIR / card.image_path
        if old.exists():
            old.unlink()
    filename = f"{card_id}{suffix}"
    dest = IMAGES_DIR / filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    card.image_path = filename
    session.add(card)
    session.commit()
    session.refresh(card)
    return _enrich(card, session)
