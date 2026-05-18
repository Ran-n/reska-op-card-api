#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/05/18 14:15:44.416879
"""

from pathlib import Path

from alembic.config import Config as AlembicConfig
from sqlmodel import Session, create_engine

from alembic import command as alembic_command

_DB_DIR = Path("data")
_DB_PATH = _DB_DIR / "optcg.db"
DATABASE_URL = f"sqlite:///{_DB_PATH}"
_ALEMBIC_INI = Path(__file__).parent.parent.parent / "alembic.ini"

engine = create_engine(DATABASE_URL)


def init_db():
    _DB_DIR.mkdir(exist_ok=True)
    alembic_cfg = AlembicConfig(str(_ALEMBIC_INI))
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
    alembic_command.upgrade(alembic_cfg, "head")


def get_session():
    with Session(engine) as session:
        yield session
