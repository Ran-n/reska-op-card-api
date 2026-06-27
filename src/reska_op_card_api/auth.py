#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28
"""

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlmodel import Session, select

from reska_op_card_api.database import get_session
from reska_op_card_api.models import ApiKey

_key_header = APIKeyHeader(name="X-API-Key")


def _resolve_key(key: str = Security(_key_header), session: Session = Depends(get_session)) -> ApiKey:
    record = session.exec(select(ApiKey).where(ApiKey.key == key)).first()
    if not record:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return record


def require_read_key(key: ApiKey = Depends(_resolve_key)) -> ApiKey:
    return key


def require_edit_key(key: ApiKey = Depends(_resolve_key)) -> ApiKey:
    if not key.can_edit:
        raise HTTPException(status_code=403, detail="This key does not have edit permissions")
    return key
