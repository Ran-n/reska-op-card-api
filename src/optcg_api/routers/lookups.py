#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/05/17 20:26:56.997290
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
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
    Language,
    PrintVariant,
    Rarity,
    Region,
    Resword,
    Set,
    SetType,
    Tribe,
)

router = APIRouter(prefix="/lookups", tags=["lookups"])


class LookupResponse(BaseModel):
    id: int
    name: str
    desc: str | None = None


class LookupWithSymbolResponse(LookupResponse):
    symbol: str | None = None


class SetLookupResponse(BaseModel):
    id: int
    code: str
    name: str


class SetTypeLookupResponse(LookupResponse):
    pass


class LanguageLookupResponse(BaseModel):
    id: int
    code: str
    name: str
    desc: str | None = None


class RegionLookupResponse(BaseModel):
    id: int
    code: str
    name: str
    desc: str | None = None


@router.get("/cardtypes", response_model=list[LookupWithSymbolResponse])
def get_cardtypes(session: Session = Depends(get_session)):
    return session.exec(select(CardType).order_by(CardType.name)).all()


@router.get("/colors", response_model=list[LookupResponse])
def get_colors(session: Session = Depends(get_session)):
    return session.exec(select(Color).order_by(Color.name)).all()


@router.get("/tribes", response_model=list[LookupResponse])
def get_tribes(session: Session = Depends(get_session)):
    return session.exec(select(Tribe).order_by(Tribe.name)).all()


@router.get("/attributes", response_model=list[LookupResponse])
def get_attributes(session: Session = Depends(get_session)):
    return session.exec(select(Attribute).order_by(Attribute.name)).all()


@router.get("/rarities", response_model=list[LookupWithSymbolResponse])
def get_rarities(session: Session = Depends(get_session)):
    return session.exec(select(Rarity).order_by(Rarity.name)).all()


class PrintVariantLookupResponse(LookupWithSymbolResponse):
    parent_fk: int | None = None


@router.get("/print-variants", response_model=list[PrintVariantLookupResponse])
def get_print_variants(session: Session = Depends(get_session)):
    return session.exec(select(PrintVariant).order_by(PrintVariant.name)).all()


@router.get("/blocks", response_model=list[LookupResponse])
def get_blocks(session: Session = Depends(get_session)):
    return session.exec(select(Block).order_by(Block.name)).all()


@router.get("/formats", response_model=list[LookupResponse])
def get_formats(session: Session = Depends(get_session)):
    return session.exec(select(Format).order_by(Format.name)).all()


@router.get("/keywords", response_model=list[LookupResponse])
def get_keywords(session: Session = Depends(get_session)):
    return session.exec(select(Keyword).order_by(Keyword.name)).all()


@router.get("/reswords", response_model=list[LookupResponse])
def get_reswords(session: Session = Depends(get_session)):
    return session.exec(select(Resword).order_by(Resword.name)).all()


@router.get("/artists", response_model=list[LookupResponse])
def get_artists(session: Session = Depends(get_session)):
    return session.exec(select(Artist).order_by(Artist.name)).all()


@router.get("/sets", response_model=list[SetLookupResponse])
def get_sets(session: Session = Depends(get_session)):
    return session.exec(select(Set).order_by(Set.code)).all()


@router.get("/settypes", response_model=list[SetTypeLookupResponse])
def get_settypes(session: Session = Depends(get_session)):
    return session.exec(select(SetType).order_by(SetType.name)).all()


@router.get("/languages", response_model=list[LanguageLookupResponse])
def get_languages(session: Session = Depends(get_session)):
    return session.exec(select(Language).order_by(Language.code)).all()


@router.get("/regions", response_model=list[RegionLookupResponse])
def get_regions(session: Session = Depends(get_session)):
    return session.exec(select(Region).order_by(Region.code)).all()
