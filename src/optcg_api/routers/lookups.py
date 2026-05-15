#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/05/15 13:07:38.682373
"""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from optcg_api.database import get_session
from optcg_api.models import (
    Artist,
    Attribute,
    Block,
    CardType,
    Color,
    Format,
    Keyword,
    Rarity,
    Resword,
    Set,
    SetType,
    Tribe,
)

router = APIRouter(prefix="/lookups", tags=["lookups"])

LOOKUP_MAP = {
    "cardtypes": CardType,
    "colors": Color,
    "tribes": Tribe,
    "attributes": Attribute,
    "rarities": Rarity,
    "blocks": Block,
    "formats": Format,
    "keywords": Keyword,
    "reswords": Resword,
    "artists": Artist,
    "sets": Set,
    "settypes": SetType,
}


@router.get("/cardtypes")
def get_cardtypes(session: Session = Depends(get_session)):
    return session.exec(select(CardType).order_by(CardType.name)).all()


@router.get("/colors")
def get_colors(session: Session = Depends(get_session)):
    return session.exec(select(Color).order_by(Color.name)).all()


@router.get("/tribes")
def get_tribes(session: Session = Depends(get_session)):
    return session.exec(select(Tribe).order_by(Tribe.name)).all()


@router.get("/attributes")
def get_attributes(session: Session = Depends(get_session)):
    return session.exec(select(Attribute).order_by(Attribute.name)).all()


@router.get("/rarities")
def get_rarities(session: Session = Depends(get_session)):
    return session.exec(select(Rarity).order_by(Rarity.name)).all()


@router.get("/blocks")
def get_blocks(session: Session = Depends(get_session)):
    return session.exec(select(Block).order_by(Block.name)).all()


@router.get("/formats")
def get_formats(session: Session = Depends(get_session)):
    return session.exec(select(Format).order_by(Format.name)).all()


@router.get("/keywords")
def get_keywords(session: Session = Depends(get_session)):
    return session.exec(select(Keyword).order_by(Keyword.name)).all()


@router.get("/reswords")
def get_reswords(session: Session = Depends(get_session)):
    return session.exec(select(Resword).order_by(Resword.name)).all()


@router.get("/artists")
def get_artists(session: Session = Depends(get_session)):
    return session.exec(select(Artist).order_by(Artist.name)).all()


@router.get("/sets")
def get_sets(session: Session = Depends(get_session)):
    return session.exec(select(Set).order_by(Set.code)).all()
