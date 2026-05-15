#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/13 13:13:00.000000
Revised: 2026/05/15 13:13:30.594717
"""

from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

_DB_DIR = Path("data")
_DB_PATH = _DB_DIR / "optcg.db"
DATABASE_URL = f"sqlite:///{_DB_PATH}"

engine = create_engine(DATABASE_URL)


def init_db():
    _DB_DIR.mkdir(exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
