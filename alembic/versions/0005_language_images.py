#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/03 00:00:00.000000
Revised: 2026/06/03 16:48:45.935252

seed language.image_fk from data/languages/<code>.svg;
reorganise data/images/ into cards/ and langs/ subdirs

Revision ID: 0005_language_images
Revises: 0004_set_parent_fk
Create Date: 2026-06-03
"""

from collections.abc import Sequence
from pathlib import Path

import sqlalchemy as sa

from alembic import op

revision: str = "0005_language_images"
down_revision: str | Sequence[str] | None = "0004_set_parent_fk"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PROJECT_ROOT = Path(__file__).parent.parent.parent
_IMAGES_DIR = _PROJECT_ROOT / "data" / "images"
_CARDS_DIR = _IMAGES_DIR / "cards"
_LANGS_DIR = _IMAGES_DIR / "langs"
_SEED_DIR = _PROJECT_ROOT / "data" / "languages"


def upgrade() -> None:
    _CARDS_DIR.mkdir(parents=True, exist_ok=True)
    _LANGS_DIR.mkdir(parents=True, exist_ok=True)
    conn = op.get_bind()

    # Move existing card images to data/images/cards/
    # Handles both plain "<hash>.ext" and legacy "images/<hash>.ext" paths
    rows = conn.execute(sa.text("SELECT id, path FROM image")).fetchall()
    for img_id, path in rows:
        if path.startswith(("cards/", "langs/")):
            continue
        filename = path[len("images/") :] if path.startswith("images/") else path
        src = _IMAGES_DIR / filename
        dest = _CARDS_DIR / filename
        if src.exists():
            src.rename(dest)
        conn.execute(
            sa.text("UPDATE image SET path = :p WHERE id = :id"),
            {"p": f"cards/{filename}", "id": img_id},
        )

    # Seed language images
    for row in conn.execute(sa.text("SELECT id, code FROM language ORDER BY id")):
        lang_id, code = row
        src = _SEED_DIR / f"{code}.svg"
        if not src.exists():
            continue

        raw = src.read_bytes()
        filename = f"langs/{code}.svg"
        dest = _LANGS_DIR / f"{code}.svg"
        if not dest.exists():
            dest.write_bytes(raw)

        existing = conn.execute(sa.text("SELECT id FROM image WHERE path = :p"), {"p": filename}).first()
        if existing:
            img_id = existing[0]
        else:
            conn.execute(sa.text("INSERT INTO image (path) VALUES (:p)"), {"p": filename})
            img_id = conn.execute(sa.text("SELECT last_insert_rowid()")).scalar()

        conn.execute(
            sa.text("UPDATE language SET image_fk = :img WHERE id = :lid"),
            {"img": img_id, "lid": lang_id},
        )


def downgrade() -> None:
    conn = op.get_bind()

    # Remove language image links and delete lang rows + files
    lang_rows = conn.execute(
        sa.text(
            "SELECT l.image_fk, i.path FROM language l JOIN image i ON i.id = l.image_fk WHERE l.image_fk IS NOT NULL"
        )
    ).fetchall()
    conn.execute(sa.text("UPDATE language SET image_fk = NULL WHERE image_fk IS NOT NULL"))
    for img_id, path in lang_rows:
        conn.execute(sa.text("DELETE FROM image WHERE id = :id"), {"id": img_id})
        (_IMAGES_DIR / path).unlink(missing_ok=True)

    # Move card images back from data/images/cards/<hash>.ext → data/images/<hash>.ext
    rows = conn.execute(sa.text("SELECT id, path FROM image")).fetchall()
    for img_id, path in rows:
        if not path.startswith("cards/"):
            continue
        filename = path[len("cards/") :]
        src = _CARDS_DIR / filename
        dest = _IMAGES_DIR / filename
        if src.exists():
            src.rename(dest)
        conn.execute(
            sa.text("UPDATE image SET path = :p WHERE id = :id"),
            {"p": filename, "id": img_id},
        )
