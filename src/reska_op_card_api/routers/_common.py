#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/12 13:37:30.058204
Revised: 2026/06/12 13:37:30.058204
"""

from pydantic import BaseModel
from sqlmodel import Session, select


class LookupItem(BaseModel):
    id: int
    name: str
    symbol: str | None = None


class ImageUrlPayload(BaseModel):
    url: str


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
