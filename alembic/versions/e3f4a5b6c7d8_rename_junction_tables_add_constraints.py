"""rename keywords/reswords tables+junctions to singular; add unique constraints and FK indexes

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-05-15
"""

from collections.abc import Sequence  # noqa: I001

import sqlalchemy as sa
from alembic import op

revision: str = "e3f4a5b6c7d8"
down_revision: str | Sequence[str] | None = "d2e3f4a5b6c7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Rename lookup tables ─────────────────────────────────────────────────
    op.rename_table("keywords", "keyword")
    op.rename_table("reswords", "resword")

    # ── Rename junction tables (rebuild required in SQLite for FK references) ─
    # card_keywords -> card_keyword
    op.create_table(
        "card_keyword",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_ts", sa.DateTime, nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_ts", sa.DateTime, nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("keyword_fk", sa.Integer, sa.ForeignKey("keyword.id"), nullable=False),
        sa.UniqueConstraint("card_fk", "keyword_fk"),
    )
    op.execute(
        "INSERT INTO card_keyword (id, created_ts, updated_ts, card_fk, keyword_fk) "
        "SELECT id, created_ts, updated_ts, card_fk, keywords_fk FROM card_keywords"
    )
    op.drop_table("card_keywords")

    # card_reswords -> card_resword
    op.create_table(
        "card_resword",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_ts", sa.DateTime, nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_ts", sa.DateTime, nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("resword_fk", sa.Integer, sa.ForeignKey("resword.id"), nullable=False),
        sa.UniqueConstraint("card_fk", "resword_fk"),
    )
    op.execute(
        "INSERT INTO card_resword (id, created_ts, updated_ts, card_fk, resword_fk) "
        "SELECT id, created_ts, updated_ts, card_fk, reswords_fk FROM card_reswords"
    )
    op.drop_table("card_reswords")

    # ── Add unique constraints to remaining junction tables ──────────────────
    # SQLite does not support ADD CONSTRAINT on existing tables; rebuild each one.

    _rebuild_junction(
        "card_tribe",
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("tribe_fk", sa.Integer, sa.ForeignKey("tribe.id"), nullable=False),
        unique=("card_fk", "tribe_fk"),
    )
    _rebuild_junction(
        "card_attribute",
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("attribute_fk", sa.Integer, sa.ForeignKey("attribute.id"), nullable=False),
        unique=("card_fk", "attribute_fk"),
    )
    _rebuild_junction(
        "card_color",
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("color_fk", sa.Integer, sa.ForeignKey("color.id"), nullable=False),
        unique=("card_fk", "color_fk"),
    )
    _rebuild_junction(
        "card_rarity",
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("rarity_fk", sa.Integer, sa.ForeignKey("rarity.id"), nullable=False),
        unique=("card_fk", "rarity_fk"),
    )
    _rebuild_junction(
        "card_block",
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("block_fk", sa.Integer, sa.ForeignKey("block.id"), nullable=False),
        unique=("card_fk", "block_fk"),
    )
    _rebuild_junction(
        "card_format",
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("format_fk", sa.Integer, sa.ForeignKey("format.id"), nullable=False),
        unique=("card_fk", "format_fk"),
    )

    # ── Indexes on all junction FK columns ───────────────────────────────────
    for table, cols in [
        ("card_tribe", ("card_fk", "tribe_fk")),
        ("card_attribute", ("card_fk", "attribute_fk")),
        ("card_color", ("card_fk", "color_fk")),
        ("card_rarity", ("card_fk", "rarity_fk")),
        ("card_block", ("card_fk", "block_fk")),
        ("card_format", ("card_fk", "format_fk")),
        ("card_keyword", ("card_fk", "keyword_fk")),
        ("card_resword", ("card_fk", "resword_fk")),
    ]:
        for col in cols:
            op.create_index(f"ix_{table}_{col}", table, [col])


def _rebuild_junction(table: str, *fk_cols: sa.Column, unique: tuple[str, str]) -> None:
    """Rebuild a junction table in-place to add a UniqueConstraint (SQLite limitation)."""
    tmp = f"_tmp_{table}"
    op.rename_table(table, tmp)
    op.create_table(
        table,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_ts", sa.DateTime, nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_ts", sa.DateTime, nullable=True, server_default=sa.text("CURRENT_TIMESTAMP")),
        *fk_cols,
        sa.UniqueConstraint(*unique),
    )
    cols = ", ".join(["id", "created_ts", "updated_ts"] + [c.name for c in fk_cols])
    op.execute(f"INSERT INTO {table} ({cols}) SELECT {cols} FROM {tmp}")
    op.drop_table(tmp)


def downgrade() -> None:
    # Drop indexes
    for table, cols in [
        ("card_tribe", ("card_fk", "tribe_fk")),
        ("card_attribute", ("card_fk", "attribute_fk")),
        ("card_color", ("card_fk", "color_fk")),
        ("card_rarity", ("card_fk", "rarity_fk")),
        ("card_block", ("card_fk", "block_fk")),
        ("card_format", ("card_fk", "format_fk")),
        ("card_keyword", ("card_fk", "keyword_fk")),
        ("card_resword", ("card_fk", "resword_fk")),
    ]:
        for col in cols:
            op.drop_index(f"ix_{table}_{col}", table_name=table)

    # Restore card_keywords
    op.create_table(
        "card_keywords",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_ts", sa.DateTime, nullable=True),
        sa.Column("updated_ts", sa.DateTime, nullable=True),
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("keywords_fk", sa.Integer, sa.ForeignKey("keywords.id"), nullable=False),
    )
    op.execute(
        "INSERT INTO card_keywords (id, created_ts, updated_ts, card_fk, keywords_fk) "
        "SELECT id, created_ts, updated_ts, card_fk, keyword_fk FROM card_keyword"
    )
    op.drop_table("card_keyword")

    # Restore card_reswords
    op.create_table(
        "card_reswords",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("created_ts", sa.DateTime, nullable=True),
        sa.Column("updated_ts", sa.DateTime, nullable=True),
        sa.Column("card_fk", sa.Integer, sa.ForeignKey("card.id"), nullable=False),
        sa.Column("reswords_fk", sa.Integer, sa.ForeignKey("reswords.id"), nullable=False),
    )
    op.execute(
        "INSERT INTO card_reswords (id, created_ts, updated_ts, card_fk, reswords_fk) "
        "SELECT id, created_ts, updated_ts, card_fk, resword_fk FROM card_resword"
    )
    op.drop_table("card_resword")

    # Restore lookup table names
    op.rename_table("keyword", "keywords")
    op.rename_table("resword", "reswords")
