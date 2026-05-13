"""
Populate the optcg.db database by scraping en.onepiece-cardgame.com/cardlist/.

For each series in the site's dropdown, fetches the card list page and parses
all card data directly from the HTML (no third-party APIs).

Usage:
    uv run scripts/ingest.py [--set OP-01]
"""

import asyncio
import logging
import re
import sys
from pathlib import Path
from typing import Any, Optional, Type, TypeVar

import httpx
from bs4 import BeautifulSoup, Tag
from sqlmodel import Session, SQLModel, select

# Add src/ to path so we can import the package without installing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from optcg_api.database import engine, init_db  # noqa: E402
from optcg_api.models import (  # noqa: E402
    Attribute,
    Card,
    CardAttribute,
    CardColor,
    CardRarity,
    CardTribe,
    CardType,
    Color,
    Rarity,
    Set,
    SetType,
    Tribe,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DB_PATH = Path(__file__).parent.parent / "optcg.db"
OFFICIAL_BASE = "https://en.onepiece-cardgame.com"
CARDLIST_URL = f"{OFFICIAL_BASE}/cardlist/"

log = logging.getLogger("ingest")

# Maps option text prefix -> SetType name
_SET_TYPE_MAP = {
    "BOOSTER PACK": "Booster",
    "EXTRA BOOSTER": "Extra Booster",
    "PREMIUM BOOSTER": "Premium Booster",
    "STARTER DECK EX": "Starter Deck",
    "STARTER DECK": "Starter Deck",
    "ULTRA DECK": "Starter Deck",
    "Promotion card": "Promo",
    "Other Product Card": "Other",
}

# Maps card category text -> CardType symbol
_CARD_TYPE_MAP = {
    "Leader": ("LEADER", "Leader"),
    "Character": ("CHARACTER", "Character"),
    "Event": ("EVENT", "Event"),
    "Stage": ("STAGE", "Stage"),
}

_SET_ID_RE = re.compile(r"\[([A-Z0-9\-]+)\]")
_CARD_NUM_RE = re.compile(r"-(\d+)")

T = TypeVar("T", bound=SQLModel)


def _get_or_create(session: Session, model: Type[T], **kwargs) -> T:
    """Fetch an existing row matching kwargs, or create and flush a new one."""
    stmt = select(model)
    for k, v in kwargs.items():
        stmt = stmt.where(getattr(model, k) == v)
    existing = session.exec(stmt).first()
    if existing:
        return existing
    obj = model(**kwargs)
    session.add(obj)
    session.flush()
    return obj


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------


def _set_code_from_text(text: str) -> str | None:
    m = _SET_ID_RE.search(text)
    return m.group(1) if m else None


def _set_type_from_text(text: str) -> str:
    for prefix, name in _SET_TYPE_MAP.items():
        if text.startswith(prefix):
            return name
    return "Other"


def _clean_name(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).strip()
    return text


def _int(val: Any) -> int | None:
    if val is None:
        return None
    s = str(val).strip().replace(",", "")
    if s in ("-", "", "–"):
        return None
    try:
        return int(s)
    except (ValueError, TypeError):
        return None


def _card_number(card_id: str) -> int | None:
    m = _CARD_NUM_RE.search(card_id)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Scraping
# ---------------------------------------------------------------------------


async def _fetch_series_list(client: httpx.AsyncClient) -> list[tuple[str, str, str, str]]:
    """Return list of (series_value, set_code, set_name, set_type_name)."""
    r = await client.get(CARDLIST_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    sel = soup.select_one("select#series")
    if not sel:
        raise RuntimeError("Could not find series select on card list page")

    results = []
    for opt in sel.find_all("option"):
        value = opt.get("value", "").strip()
        if not value:
            continue
        raw_text = opt.get_text(separator=" ", strip=True)
        set_code = _set_code_from_text(raw_text)
        if not set_code:
            set_code = f"SERIES-{value}"
        set_name = _clean_name(raw_text)
        set_type_name = _set_type_from_text(raw_text)
        results.append((value, set_code, set_name, set_type_name))
    return results


async def _fetch_series_cards(
    client: httpx.AsyncClient, series_value: str, set_code: str
) -> list[dict]:
    r = await client.get(CARDLIST_URL, params={"series": series_value})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    result_col = soup.select_one(".resultCol")
    if not result_col:
        return []

    cards = []
    for dl in result_col.select("dl.modalCol"):
        card = _parse_card_dl(dl, set_code)
        if card:
            cards.append(card)
    return cards


def _parse_card_dl(dl: Tag, set_code: str) -> dict | None:
    card_id = dl.get("id", "").strip()
    if not card_id:
        return None

    info_spans = [s.get_text(strip=True) for s in dl.select("dt .infoCol span")]
    rarity_text = info_spans[1] if len(info_spans) > 1 else None
    category_text = info_spans[2] if len(info_spans) > 2 else None
    name_el = dl.select_one("dt .cardName")
    name = name_el.get_text(strip=True) if name_el else card_id

    back = dl.select_one(".backCol")
    if not back:
        return None

    def _field(css: str) -> str | None:
        el = back.select_one(css)
        if not el:
            return None
        h3 = el.select_one("h3")
        if h3:
            h3.decompose()
        return el.get_text(strip=True) or None

    cost_label = back.select_one(".cost h3")
    cost_label_text = cost_label.get_text(strip=True) if cost_label else ""
    cost_val = _field(".cost")
    is_leader = cost_label_text == "Life"
    life = _int(cost_val) if is_leader else None
    cost = None if is_leader else _int(cost_val)

    attr_i = back.select_one(".attribute i")
    attribute = attr_i.get_text(strip=True) if attr_i else None
    if attribute in ("-", ""):
        attribute = None

    power = _int(_field(".power"))
    counter = _int(_field(".counter"))

    color_text = _field(".color")
    colors = [c.strip() for c in color_text.split("/")] if color_text else []

    subtypes_text = _field(".feature")
    subtypes = [t.strip() for t in subtypes_text.split("/")] if subtypes_text else []

    effect_el = back.select_one(".text")
    effect = None
    if effect_el:
        h3 = effect_el.select_one("h3")
        if h3:
            h3.decompose()
        effect = effect_el.get_text(strip=True) or None

    trigger_el = back.select_one(".trigger")
    trigger = None
    if trigger_el:
        h3 = trigger_el.select_one("h3")
        if h3:
            h3.decompose()
        trigger = trigger_el.get_text(strip=True) or None

    return {
        "card_id": card_id,
        "set_code": set_code,
        "name": name,
        "rarity": rarity_text,
        "category": category_text,
        "colors": colors,
        "cost": cost,
        "power": power,
        "counter": counter,
        "life": life,
        "attribute": attribute,
        "subtypes": subtypes,
        "desc": effect,
        "trigger": trigger,
    }


# ---------------------------------------------------------------------------
# DB persistence
# ---------------------------------------------------------------------------


def _persist(session: Session, sets_data: list[dict], cards_data: list[dict]) -> tuple[int, int]:
    # Pre-populate SetType rows
    set_type_cache: dict[str, SetType] = {}
    card_type_cache: dict[str, CardType] = {}

    # Ensure all CardType rows exist up front
    for symbol, name in _CARD_TYPE_MAP.values():
        existing = session.exec(select(CardType).where(CardType.symbol == symbol)).first()
        if existing:
            ct = existing
        else:
            ct = CardType(symbol=symbol, name=name)
            session.add(ct)
            session.flush()
        card_type_cache[symbol] = ct

    # Upsert sets
    set_pk_by_code: dict[str, int] = {}
    for sd in sets_data:
        st_name = sd["set_type_name"]
        if st_name not in set_type_cache:
            set_type_cache[st_name] = _get_or_create(session, SetType, name=st_name)
        st = set_type_cache[st_name]

        existing = session.exec(select(Set).where(Set.code == sd["code"])).first()
        if existing:
            existing.name = sd["name"]
            existing.type_fk = st.id
            s = existing
        else:
            s = Set(code=sd["code"], name=sd["name"], type_fk=st.id)
            session.add(s)
            session.flush()
        set_pk_by_code[sd["code"]] = s.id

    # Upsert cards + junction rows
    color_cache: dict[str, Color] = {}
    rarity_cache: dict[str, Rarity] = {}
    attribute_cache: dict[str, Attribute] = {}
    tribe_cache: dict[str, Tribe] = {}
    upserted = 0

    for cd in cards_data:
        set_pk = set_pk_by_code.get(cd["set_code"])
        if set_pk is None:
            continue

        number = _card_number(cd["card_id"])
        cat = cd.get("category") or ""
        symbol, _ = _CARD_TYPE_MAP.get(cat, ("CHARACTER", "Character"))
        ct = card_type_cache.get(symbol) or _get_or_create(session, CardType, symbol=symbol)

        existing = session.exec(
            select(Card).where(Card.set_fk == set_pk, Card.number == number)
        ).first()
        if existing:
            existing.name = cd["name"]
            existing.desc = cd.get("desc")
            existing.trigger = cd.get("trigger")
            existing.power = cd.get("power")
            existing.life = cd.get("life")
            existing.counter = cd.get("counter")
            existing.cost = cd.get("cost")
            existing.cardtype_fk = ct.id
            card = existing
        else:
            card = Card(
                set_fk=set_pk,
                cardtype_fk=ct.id,
                number=number,
                name=cd["name"],
                desc=cd.get("desc"),
                trigger=cd.get("trigger"),
                power=cd.get("power"),
                life=cd.get("life"),
                counter=cd.get("counter"),
                cost=cd.get("cost"),
            )
            session.add(card)
            session.flush()

        card_pk = card.id

        # Colors
        existing_colors = {
            row.color_fk
            for row in session.exec(select(CardColor).where(CardColor.card_fk == card_pk)).all()
        }
        for color_name in cd.get("colors", []):
            if not color_name:
                continue
            if color_name not in color_cache:
                color_cache[color_name] = _get_or_create(session, Color, name=color_name)
            color_pk = color_cache[color_name].id
            if color_pk not in existing_colors:
                session.add(CardColor(card_fk=card_pk, color_fk=color_pk))

        # Rarity
        rarity_text = cd.get("rarity")
        if rarity_text:
            if rarity_text not in rarity_cache:
                existing_r = session.exec(
                    select(Rarity).where(Rarity.symbol == rarity_text)
                ).first()
                if existing_r:
                    rarity_cache[rarity_text] = existing_r
                else:
                    r = Rarity(symbol=rarity_text, name=rarity_text)
                    session.add(r)
                    session.flush()
                    rarity_cache[rarity_text] = r
            rarity = rarity_cache[rarity_text]
            existing_rarities = {
                row.rarity_fk
                for row in session.exec(
                    select(CardRarity).where(CardRarity.card_fk == card_pk)
                ).all()
            }
            if rarity.id not in existing_rarities:
                session.add(CardRarity(card_fk=card_pk, rarity_fk=rarity.id))

        # Attribute
        attribute_text = cd.get("attribute")
        if attribute_text:
            if attribute_text not in attribute_cache:
                attribute_cache[attribute_text] = _get_or_create(
                    session, Attribute, name=attribute_text
                )
            attr_pk = attribute_cache[attribute_text].id
            existing_attrs = {
                row.attribute_fk
                for row in session.exec(
                    select(CardAttribute).where(CardAttribute.card_fk == card_pk)
                ).all()
            }
            if attr_pk not in existing_attrs:
                session.add(CardAttribute(card_fk=card_pk, attribute_fk=attr_pk))

        # Tribes (subtypes)
        existing_tribes = {
            row.tribe_fk
            for row in session.exec(select(CardTribe).where(CardTribe.card_fk == card_pk)).all()
        }
        for tribe_name in cd.get("subtypes", []):
            if not tribe_name:
                continue
            if tribe_name not in tribe_cache:
                tribe_cache[tribe_name] = _get_or_create(session, Tribe, name=tribe_name)
            tribe_pk = tribe_cache[tribe_name].id
            if tribe_pk not in existing_tribes:
                session.add(CardTribe(card_fk=card_pk, tribe_fk=tribe_pk))

        upserted += 1

    session.commit()
    return len(sets_data), upserted


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


async def run(only_set: str | None = None) -> None:
    init_db()

    def _normalise(s: str) -> str:
        s = s.upper().replace("-", "")
        m = re.match(r"^([A-Z]+)(\d+)$", s)
        return f"{m.group(1)}-{m.group(2)}" if m else s

    target = _normalise(only_set) if only_set else None

    async with httpx.AsyncClient(
        timeout=30, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0"}
    ) as client:
        log.info("Fetching series list...")
        series_list = await _fetch_series_list(client)
        log.info("Found %d series", len(series_list))

        if target:
            series_list = [s for s in series_list if s[1].upper() == target]
            if not series_list:
                log.error("No series found matching %r", target)
                return
            log.info("Filtering to %s", target)

        sets_data: list[dict] = []
        cards_data: list[dict] = []
        seen_card_ids: set[str] = set()

        for series_value, set_code, set_name, set_type_name in series_list:
            sets_data.append(
                {"code": set_code, "name": set_name, "set_type_name": set_type_name}
            )
            log.info("Fetching %s (%s)...", set_code, set_name[:50])
            try:
                series_cards = await _fetch_series_cards(client, series_value, set_code)
                for card in series_cards:
                    cid = card["card_id"]
                    if cid not in seen_card_ids:
                        seen_card_ids.add(cid)
                        cards_data.append(card)
                log.info("  -> %d cards", len(series_cards))
            except Exception as e:
                log.warning("  -> failed: %s", e)

    with Session(engine) as session:
        n_sets, n_cards = _persist(session, sets_data, cards_data)

    log.info("Done: %d sets, %d cards written to %s", n_sets, n_cards, DB_PATH)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ingest One Piece TCG card data from the official site."
    )
    parser.add_argument(
        "--set",
        metavar="SET_ID",
        dest="set_id",
        help="Only ingest one set, e.g. --set OP-01 or --set op01",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s", stream=sys.stdout)
    asyncio.run(run(only_set=args.set_id))
