#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/06/30 12:51:50.611715
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from reska_op_card_api.auth import require_read_key
from reska_op_card_api.database import get_session
from reska_op_card_api.models import Set
from reska_op_card_api.routers._common import (
    ExpandedLanguage,
    ExpandedSet,
    ExpandedSetType,
    _expand_languages_bulk,
    _expand_sets_bulk,
    _expand_settypes_bulk,
    _parse_expand,
    _stripe,
)

router = APIRouter(prefix="/sets", tags=["sets"], dependencies=[Depends(require_read_key)])

_EXPAND_FIELDS = {"language", "parent", "type"}


class SetResponse(BaseModel):
    id: int
    code: str
    name: str
    language: int | ExpandedLanguage
    parent: int | ExpandedSet | None = None
    desc: str | None = None
    release_ts: date | None = None
    type: int | ExpandedSetType | None = None


def _build_set_response(s: Set, expand_set: set[str], lang_map: dict, parent_map: dict, type_map: dict) -> SetResponse:
    return SetResponse(
        id=s.id,
        code=s.code,
        name=s.name,
        language=lang_map.get(s.language_fk, s.language_fk) if "language" in expand_set else s.language_fk,
        parent=_stripe(s.parent_fk, "parent", expand_set, parent_map),
        desc=s.desc,
        release_ts=s.release_ts,
        type=_stripe(s.type_fk, "type", expand_set, type_map),
    )


@router.get("/", response_model=list[SetResponse])
def list_sets(expand: str | None = Query(None), session: Session = Depends(get_session)):
    sets = session.exec(select(Set)).all()
    expand_set = _parse_expand(expand, _EXPAND_FIELDS)

    lang_map = _expand_languages_bulk([s.language_fk for s in sets], session) if "language" in expand_set else {}
    parent_map = _expand_sets_bulk([s.parent_fk for s in sets], session) if "parent" in expand_set else {}
    type_map = _expand_settypes_bulk([s.type_fk for s in sets], session) if "type" in expand_set else {}

    return [_build_set_response(s, expand_set, lang_map, parent_map, type_map) for s in sets]


@router.get("/{set_id}", response_model=SetResponse)
def get_set(set_id: int, expand: str | None = Query(None), session: Session = Depends(get_session)):
    s = session.get(Set, set_id)
    if not s:
        raise HTTPException(status_code=404, detail="Set not found")
    expand_set = _parse_expand(expand, _EXPAND_FIELDS)

    lang_map = _expand_languages_bulk([s.language_fk], session) if "language" in expand_set else {}
    parent_map = _expand_sets_bulk([s.parent_fk], session) if "parent" in expand_set else {}
    type_map = _expand_settypes_bulk([s.type_fk], session) if "type" in expand_set else {}

    return _build_set_response(s, expand_set, lang_map, parent_map, type_map)
