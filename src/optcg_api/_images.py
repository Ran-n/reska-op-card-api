#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/05/30 00:00:00.000000
Revised: 2026/06/12 13:37:30.155951

Shared image-file utilities for routers that manage Naip/NaipSerial images.
"""

from pathlib import Path

import blake3 as _blake3
from sqlmodel import Session, select

from optcg_api.models import Block, Image, Language, Naip, NaipSerial

IMAGES_DIR = Path(__file__).parent.parent.parent / "data" / "images"
CARDS_DIR = IMAGES_DIR / "cards"
CARDS_DIR.mkdir(parents=True, exist_ok=True)

VALID_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp"})


def save_image(raw: bytes, suffix: str, session: Session) -> Image:
    """Persist raw bytes to CARDS_DIR and return the Image row; skips file I/O if row already exists."""
    h = _blake3.blake3(raw).hexdigest()
    path = f"cards/{h}{suffix}"
    existing = session.exec(select(Image).where(Image.path == path)).first()
    if existing:
        return existing
    dest = CARDS_DIR / f"{h}{suffix}"
    if not dest.exists():
        dest.write_bytes(raw)
    img = Image(path=path)
    session.add(img)
    session.flush()
    return img


def cleanup_orphaned_image(img_id: int | None, session: Session) -> None:
    """Delete the Image row and its file if nothing references it anymore."""
    if img_id is None:
        return
    still_used = (
        session.exec(select(Naip).where(Naip.image_fk == img_id)).first()
        or session.exec(select(NaipSerial).where(NaipSerial.image_fk == img_id)).first()
        or session.exec(select(Block).where(Block.image_fk == img_id)).first()
        or session.exec(select(Language).where(Language.image_fk == img_id)).first()
    )
    if still_used:
        return
    img = session.get(Image, img_id)
    if img:
        (IMAGES_DIR / img.path).unlink(missing_ok=True)
        session.delete(img)


def replace_naip_image(naip: Naip, new_img_id: int, session: Session) -> None:
    """Point naip.image_fk at new_img_id and clean up the old image if orphaned."""
    old_fk = naip.image_fk
    naip.image_fk = new_img_id
    session.add(naip)
    session.flush()
    if old_fk is not None and old_fk != new_img_id:
        cleanup_orphaned_image(old_fk, session)
