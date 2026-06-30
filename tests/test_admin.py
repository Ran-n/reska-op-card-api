#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/30
"""

import base64

import pytest


def _auth_header(user: str, pw: str) -> dict:
    token = base64.b64encode(f"{user}:{pw}".encode()).decode()
    return {"Authorization": f"Basic {token}"}


@pytest.fixture
def admin_env(monkeypatch):
    monkeypatch.setenv("ADMIN_USERNAME", "admin")
    monkeypatch.setenv("ADMIN_PASSWORD", "s3cret")
    return _auth_header("admin", "s3cret")


# ── Auth gate ────────────────────────────────────────────────────────────────


def test_admin_dashboard_unconfigured_returns_503(client, monkeypatch):
    monkeypatch.delenv("ADMIN_USERNAME", raising=False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    r = client.get("/admin", headers=_auth_header("x", "y"))
    assert r.status_code == 503


def test_admin_dashboard_missing_credentials_returns_401(client, admin_env):
    r = client.get("/admin")
    assert r.status_code == 401


def test_admin_dashboard_wrong_credentials_returns_401(client, admin_env):
    r = client.get("/admin", headers=_auth_header("admin", "wrong"))
    assert r.status_code == 401


def test_admin_dashboard_correct_credentials_returns_200(client, admin_env):
    r = client.get("/admin", headers=admin_env)
    assert r.status_code == 200
    assert "Key Manager" in r.text


def test_admin_keys_page_correct_credentials_returns_200(client, admin_env):
    r = client.get("/admin/keys", headers=admin_env)
    assert r.status_code == 200


# ── Create key ───────────────────────────────────────────────────────────────


def test_create_key_happy_path(client, admin_env, test_engine):
    r = client.post(
        "/admin/keys",
        data={"label": "admin-test-create", "can_edit": "true"},
        headers=admin_env,
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "new_key=" in r.headers["location"]

    from sqlmodel import Session, select

    from reska_op_card_api.models import ApiKey

    with Session(test_engine) as s:
        record = s.exec(select(ApiKey).where(ApiKey.label == "admin-test-create")).first()
        assert record is not None
        assert record.can_edit is True
        assert record.revoked_ts is None


def test_create_key_duplicate_label_redirects_with_error(client, admin_env):
    client.post(
        "/admin/keys",
        data={"label": "admin-test-dup", "can_edit": "false"},
        headers=admin_env,
        follow_redirects=False,
    )
    r = client.post(
        "/admin/keys",
        data={"label": "admin-test-dup", "can_edit": "false"},
        headers=admin_env,
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert "error=" in r.headers["location"]


def test_create_key_requires_admin_auth(client):
    r = client.post("/admin/keys", data={"label": "no-auth", "can_edit": "false"})
    assert r.status_code in (401, 503)


# ── Reset ────────────────────────────────────────────────────────────────────


def test_reset_key_clears_request_count(client, admin_env, test_engine):
    from sqlmodel import Session, select

    from reska_op_card_api.models import ApiKey

    client.post(
        "/admin/keys",
        data={"label": "admin-test-reset", "can_edit": "false"},
        headers=admin_env,
        follow_redirects=False,
    )
    with Session(test_engine) as s:
        record = s.exec(select(ApiKey).where(ApiKey.label == "admin-test-reset")).first()
        record.request_count = 42
        s.add(record)
        s.commit()
        key_id = record.id

    r = client.post(f"/admin/keys/{key_id}/reset", headers=admin_env, follow_redirects=False)
    assert r.status_code == 303

    with Session(test_engine) as s:
        record = s.get(ApiKey, key_id)
        assert record.request_count == 0


def test_reset_key_not_found_returns_404(client, admin_env):
    r = client.post("/admin/keys/999999/reset", headers=admin_env)
    assert r.status_code == 404


# ── Delete / restore ─────────────────────────────────────────────────────────


def test_delete_then_restore_key(client, admin_env, test_engine):
    from sqlmodel import Session, select

    from reska_op_card_api.models import ApiKey

    client.post(
        "/admin/keys",
        data={"label": "admin-test-revoke", "can_edit": "false"},
        headers=admin_env,
        follow_redirects=False,
    )
    with Session(test_engine) as s:
        record = s.exec(select(ApiKey).where(ApiKey.label == "admin-test-revoke")).first()
        key_id = record.id

    r = client.post(f"/admin/keys/{key_id}/delete", headers=admin_env, follow_redirects=False)
    assert r.status_code == 303
    with Session(test_engine) as s:
        record = s.get(ApiKey, key_id)
        assert record.revoked_ts is not None

    r = client.post(f"/admin/keys/{key_id}/delete", headers=admin_env)
    assert r.status_code == 404

    r = client.post(f"/admin/keys/{key_id}/restore", headers=admin_env, follow_redirects=False)
    assert r.status_code == 303
    with Session(test_engine) as s:
        record = s.get(ApiKey, key_id)
        assert record.revoked_ts is None

    r = client.post(f"/admin/keys/{key_id}/restore", headers=admin_env)
    assert r.status_code == 404


def test_delete_key_not_found_returns_404(client, admin_env):
    r = client.post("/admin/keys/999999/delete", headers=admin_env)
    assert r.status_code == 404


def test_restore_key_not_found_returns_404(client, admin_env):
    r = client.post("/admin/keys/999999/restore", headers=admin_env)
    assert r.status_code == 404


# ── Purge ────────────────────────────────────────────────────────────────────


def test_purge_key_removes_row(client, admin_env, test_engine):
    from sqlmodel import Session, select

    from reska_op_card_api.models import ApiKey

    client.post(
        "/admin/keys",
        data={"label": "admin-test-purge", "can_edit": "false"},
        headers=admin_env,
        follow_redirects=False,
    )
    with Session(test_engine) as s:
        record = s.exec(select(ApiKey).where(ApiKey.label == "admin-test-purge")).first()
        key_id = record.id

    r = client.post(f"/admin/keys/{key_id}/purge", headers=admin_env, follow_redirects=False)
    assert r.status_code == 303

    with Session(test_engine) as s:
        assert s.get(ApiKey, key_id) is None


def test_purge_key_not_found_returns_404(client, admin_env):
    r = client.post("/admin/keys/999999/purge", headers=admin_env)
    assert r.status_code == 404
