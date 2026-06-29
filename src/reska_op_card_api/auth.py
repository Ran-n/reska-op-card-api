#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28
"""

import logging

import blake3
from fastapi import Depends, HTTPException, Query, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy import func, update
from sqlmodel import Session, select

from reska_op_card_api.database import get_session
from reska_op_card_api.models import ApiKey

_log = logging.getLogger(__name__)
_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _resolve_key(
    request: Request,
    header_key: str | None = Security(_key_header),
    query_key: str | None = Query(default=None, alias="api_key"),
    session: Session = Depends(get_session),
) -> ApiKey:
    key = header_key or query_key
    if not key:
        raise HTTPException(status_code=401, detail="API key required")

    key_hash = blake3.blake3(key.encode()).hexdigest()
    record = session.exec(select(ApiKey).where(ApiKey.key == key_hash)).first()
    if not record or record.revoked_ts is not None:
        _log.warning("auth rejected: %s %s", request.method, request.url.path)
        raise HTTPException(status_code=401, detail="Invalid API key")
    session.execute(
        update(ApiKey)
        .where(ApiKey.id == record.id)
        .values(request_count=ApiKey.request_count + 1, last_used_ts=func.strftime("%Y-%m-%d %H:%M:%f", "now"))
    )
    session.commit()
    session.refresh(record)
    request.state.api_key_id = record.id
    return record


def require_read_key(key: ApiKey = Depends(_resolve_key)) -> ApiKey:
    return key


def require_edit_key(key: ApiKey = Depends(_resolve_key)) -> ApiKey:
    if not key.can_edit:
        raise HTTPException(status_code=403, detail="This key does not have edit permissions")
    return key
