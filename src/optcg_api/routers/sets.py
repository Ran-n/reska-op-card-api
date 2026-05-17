#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/05/17 20:26:56.885669
"""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from optcg_api.database import get_session
from optcg_api.models import Set

router = APIRouter(prefix="/sets", tags=["sets"])


class SetResponse(BaseModel):
    id: int
    code: str
    name: str
    series: str | None = None
    ord: int | None = None
    desc: str | None = None
    release_ts: date | None = None
    type_fk: int | None = None


@router.get("/", response_model=list[SetResponse])
def list_sets(session: Session = Depends(get_session)):
    return session.exec(select(Set)).all()


@router.get("/{set_id}", response_model=SetResponse)
def get_set(set_id: int, session: Session = Depends(get_session)):
    s = session.get(Set, set_id)
    if not s:
        raise HTTPException(status_code=404, detail="Set not found")
    return s
