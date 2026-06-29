#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/29
"""

import secrets

import blake3
import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, text


@pytest.fixture(scope="session")
def test_engine(tmp_path_factory):
    db_dir = tmp_path_factory.mktemp("db")
    engine = create_engine(
        f"sqlite:///{db_dir / 'test.db'}",
        connect_args={"check_same_thread": False},
    )

    @sa.event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys = ON")

    # Create schema from models (avoids SQLite batch-alter migration issues)
    import reska_op_card_api.models  # noqa: F401 — registers all SQLModel tables

    SQLModel.metadata.create_all(engine)
    _seed(engine)
    return engine


def _seed(engine) -> None:
    """Insert the lookup rows that migrations normally provide."""
    with Session(engine) as s:
        s.exec(
            text(
                "INSERT OR IGNORE INTO language (code, name) VALUES "
                "('en','English'),('ja','Japanese'),('fr','French'),"
                "('zh-Hans','Chinese (Simplified)'),('ko','Korean')"
            )
        )
        s.exec(
            text(
                "INSERT OR IGNORE INTO card_type (symbol, name) VALUES "
                "('L','Leader'),('C','Character'),('E','Event'),('S','Stage'),('D','DON!!')"
            )
        )
        s.exec(
            text(
                "INSERT OR IGNORE INTO rarity (symbol, name) VALUES "
                "('C','Common'),('UC','Uncommon'),('R','Rare'),('SR','Super Rare'),"
                "('SEC','Secret'),('L','Leader'),('P','Promo')"
            )
        )
        s.exec(
            text(
                "INSERT OR IGNORE INTO print_variant (symbol, name) VALUES "
                "('STD','Standard'),('AA','Alternate Art'),('TR','Token Rare'),"
                "('SP','Special'),('GR','Golden Rare')"
            )
        )
        s.commit()


@pytest.fixture(scope="session")
def app(test_engine):
    import reska_op_card_api.database as _db
    from reska_op_card_api.database import get_session
    from reska_op_card_api.main import app as _app

    # Patch engine references so the access-log middleware also uses the test DB.
    # main.py imports `engine` directly at module load, so both modules need patching.
    _db.engine = test_engine
    import reska_op_card_api.main as _main

    _main.engine = test_engine

    def _override():
        with Session(test_engine) as s:
            yield s

    _app.dependency_overrides[get_session] = _override
    return _app


@pytest.fixture(scope="session")
def client(app):
    return TestClient(app, raise_server_exceptions=True)


def _make_key(engine, label: str, can_edit: bool) -> str:
    raw = secrets.token_urlsafe(32)
    key_hash = blake3.blake3(raw.encode()).hexdigest()
    from reska_op_card_api.models import ApiKey

    with Session(engine) as s:
        s.add(ApiKey(key=key_hash, label=label, can_edit=can_edit))
        s.commit()
    return raw


@pytest.fixture(scope="session")
def read_key(test_engine):
    return _make_key(test_engine, "test-read", can_edit=False)


@pytest.fixture(scope="session")
def edit_key(test_engine):
    return _make_key(test_engine, "test-edit", can_edit=True)


@pytest.fixture(scope="session")
def seed(test_engine):
    """Return IDs of seed rows needed by tests."""
    with Session(test_engine) as s:
        lang_id = s.exec(text("SELECT id FROM language WHERE code = 'en'")).scalar()
        pv_id = s.exec(text("SELECT id FROM print_variant WHERE symbol = 'STD'")).scalar()
        ct_id = s.exec(text("SELECT id FROM card_type LIMIT 1")).scalar()
        return {"language_fk": lang_id, "print_variant_fk": pv_id, "cardtype_fk": ct_id}
