"""normalize trigger and effect as lookup + junction tables

trigger(id, trigger UNIQUE)
card_trigger(id, card_fk, trigger_fk)

effect(id, effect UNIQUE)
naip_effect(id, naip_fk, effect_fk)

Drops card.trigger_fk, naip.effect_fk, and the old card_trigger/card_effect tables.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: str | Sequence[str] | None = "b2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── trigger → card_trigger ────────────────────────────────────────────────

    # Read existing data from current card_trigger (id, trigger UNIQUE)
    # and card.trigger_fk before we drop them.
    old_triggers = conn.execute(sa.text("SELECT id, trigger FROM card_trigger")).fetchall()
    card_trigger_links = conn.execute(
        sa.text("SELECT id, trigger_fk FROM card WHERE trigger_fk IS NOT NULL")
    ).fetchall()
    trigger_id_to_text = {r[0]: r[1] for r in old_triggers}

    # Drop card.trigger_fk and old card_trigger
    with op.batch_alter_table("card") as batch_op:
        batch_op.drop_constraint("fk_card_trigger", type_="foreignkey")
        batch_op.drop_column("trigger_fk")

    op.drop_table("card_trigger")

    # Create trigger lookup table
    op.create_table(
        "trigger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("trigger", sa.String(), nullable=False, unique=True),
    )

    # Create card_trigger junction table
    op.create_table(
        "card_trigger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("trigger_fk", sa.Integer(), sa.ForeignKey("trigger.id"), nullable=False),
    )

    # Populate trigger lookup (dedup already happened, but re-insert from old data)
    text_to_new_id: dict[str, int] = {}
    for _old_id, trigger_text in old_triggers:
        if trigger_text not in text_to_new_id:
            result = conn.execute(
                sa.text("INSERT INTO trigger (trigger) VALUES (:t)"), {"t": trigger_text}
            )
            text_to_new_id[trigger_text] = result.lastrowid

    # Populate card_trigger junction
    for card_id, old_trigger_fk in card_trigger_links:
        trigger_text = trigger_id_to_text.get(old_trigger_fk)
        if trigger_text and trigger_text in text_to_new_id:
            conn.execute(
                sa.text("INSERT INTO card_trigger (card_fk, trigger_fk) VALUES (:c, :t)"),
                {"c": card_id, "t": text_to_new_id[trigger_text]},
            )

    # ── effect → naip_effect ──────────────────────────────────────────────────

    old_effects = conn.execute(sa.text("SELECT id, effect FROM card_effect")).fetchall()
    naip_effect_links = conn.execute(
        sa.text("SELECT id, effect_fk FROM naip WHERE effect_fk IS NOT NULL")
    ).fetchall()
    effect_id_to_text = {r[0]: r[1] for r in old_effects}

    # Drop naip.effect_fk and old card_effect
    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_constraint("fk_naip_effect", type_="foreignkey")
        batch_op.drop_column("effect_fk")

    op.drop_table("card_effect")

    # Create effect lookup table
    op.create_table(
        "effect",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("effect", sa.String(), nullable=False, unique=True),
    )

    # Create naip_effect junction table
    op.create_table(
        "naip_effect",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("naip_fk", sa.Integer(), sa.ForeignKey("naip.id"), nullable=False),
        sa.Column("effect_fk", sa.Integer(), sa.ForeignKey("effect.id"), nullable=False),
    )

    # Populate effect lookup
    effect_text_to_new_id: dict[str, int] = {}
    for _old_id, effect_text in old_effects:
        if effect_text not in effect_text_to_new_id:
            result = conn.execute(
                sa.text("INSERT INTO effect (effect) VALUES (:e)"), {"e": effect_text}
            )
            effect_text_to_new_id[effect_text] = result.lastrowid

    # Populate naip_effect junction
    for naip_id, old_effect_fk in naip_effect_links:
        effect_text = effect_id_to_text.get(old_effect_fk)
        if effect_text and effect_text in effect_text_to_new_id:
            conn.execute(
                sa.text("INSERT INTO naip_effect (naip_fk, effect_fk) VALUES (:n, :e)"),
                {"n": naip_id, "e": effect_text_to_new_id[effect_text]},
            )


def downgrade() -> None:
    conn = op.get_bind()

    # ── restore card.trigger_fk → card_trigger(id, trigger UNIQUE) ───────────

    junction_rows = conn.execute(
        sa.text("SELECT ct.card_fk, t.trigger FROM card_trigger ct JOIN trigger t ON t.id = ct.trigger_fk")
    ).fetchall()

    op.drop_table("card_trigger")
    op.drop_table("trigger")

    op.create_table(
        "card_trigger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("trigger", sa.String(), nullable=False, unique=True),
    )

    text_to_id: dict[str, int] = {}
    for _card_id, trigger_text in junction_rows:
        if trigger_text not in text_to_id:
            result = conn.execute(
                sa.text("INSERT INTO card_trigger (trigger) VALUES (:t)"), {"t": trigger_text}
            )
            text_to_id[trigger_text] = result.lastrowid

    with op.batch_alter_table("card") as batch_op:
        batch_op.add_column(sa.Column("trigger_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_card_trigger", "card_trigger", ["trigger_fk"], ["id"])

    for card_id, trigger_text in junction_rows:
        new_id = text_to_id.get(trigger_text)
        if new_id:
            conn.execute(
                sa.text("UPDATE card SET trigger_fk = :tid WHERE id = :cid"),
                {"tid": new_id, "cid": card_id},
            )

    # ── restore naip.effect_fk → card_effect(id, effect UNIQUE) ──────────────

    naip_effect_rows = conn.execute(
        sa.text("SELECT ne.naip_fk, e.effect FROM naip_effect ne JOIN effect e ON e.id = ne.effect_fk")
    ).fetchall()

    op.drop_table("naip_effect")
    op.drop_table("effect")

    op.create_table(
        "card_effect",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("effect", sa.String(), nullable=False, unique=True),
    )

    effect_text_to_id: dict[str, int] = {}
    for _naip_id, effect_text in naip_effect_rows:
        if effect_text not in effect_text_to_id:
            result = conn.execute(
                sa.text("INSERT INTO card_effect (effect) VALUES (:e)"), {"e": effect_text}
            )
            effect_text_to_id[effect_text] = result.lastrowid

    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("effect_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_naip_effect", "card_effect", ["effect_fk"], ["id"])

    for naip_id, effect_text in naip_effect_rows:
        new_id = effect_text_to_id.get(effect_text)
        if new_id:
            conn.execute(
                sa.text("UPDATE naip SET effect_fk = :eid WHERE id = :nid"),
                {"eid": new_id, "nid": naip_id},
            )
