#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/29
"""


def test_missing_key_returns_401(client):
    r = client.get("/sets/")
    assert r.status_code == 401


def test_invalid_key_returns_401(client):
    r = client.get("/sets/", headers={"X-API-Key": "notavalidkey"})
    assert r.status_code == 401


def test_valid_read_key_via_header(client, read_key):
    r = client.get("/sets/", headers={"X-API-Key": read_key})
    assert r.status_code == 200


def test_valid_read_key_via_query_param(client, read_key):
    r = client.get(f"/sets/?api_key={read_key}")
    assert r.status_code == 200


def test_read_key_cannot_edit(client, read_key, seed):
    payload = {
        "set_fk": 1,
        "cardtype_fk": seed["cardtype_fk"],
        "number": 1,
        "name": "Test Card",
    }
    r = client.post("/cards/", json=payload, headers={"X-API-Key": read_key})
    assert r.status_code == 403


def test_revoked_key_returns_401(client, test_engine):
    import secrets

    import blake3
    from sqlmodel import Session

    from reska_op_card_api.models import ApiKey

    raw = secrets.token_urlsafe(32)
    key_hash = blake3.blake3(raw.encode()).hexdigest()
    with Session(test_engine) as s:
        record = ApiKey(key=key_hash, label="test-revoked", can_edit=False)
        s.add(record)
        s.commit()
        s.refresh(record)
        from sqlalchemy import func

        record.revoked_ts = func.strftime("%Y-%m-%d %H:%M:%f", "now")
        s.add(record)
        s.commit()

    r = client.get("/sets/", headers={"X-API-Key": raw})
    assert r.status_code == 401
