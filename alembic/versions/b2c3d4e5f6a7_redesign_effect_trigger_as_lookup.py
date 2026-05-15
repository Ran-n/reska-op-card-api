"""redesign card_effect and card_trigger as unique-text lookup tables

card_effect(id, effect UNIQUE) — deduplicated effect texts; naip.effect_fk points here
card_trigger(id, trigger UNIQUE) — deduplicated trigger texts; card.trigger_fk points here

Drops card_fk and is_current from both tables.
Adds trigger_fk to card.

Revision ID: b2c3d4e5f6a7
Revises: e1a2b3c4d5e6
Create Date: 2026-05-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "e1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()

    # ── card_trigger ──────────────────────────────────────────────────────────
    # Rebuild as a lookup: id, trigger UNIQUE.
    # Existing rows already have one trigger text per card; deduplicate them,
    # then wire card.trigger_fk to the new lookup id.

    old_triggers = conn.execute(sa.text("SELECT id, trigger FROM card_trigger")).fetchall()

    # Build dedup map: trigger_text → new_id
    trigger_text_to_id: dict[str, int] = {}
    # old card_trigger.id → card_fk (so we can set card.trigger_fk)
    old_id_to_card_fk: dict[int, int] = {
        r[0]: r[1]
        for r in conn.execute(sa.text("SELECT id, card_fk FROM card_trigger")).fetchall()
    }

    op.drop_table("card_trigger")
    op.create_table(
        "card_trigger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("trigger", sa.String(), nullable=False, unique=True),
    )

    for old_id, trigger_text in old_triggers:
        if trigger_text not in trigger_text_to_id:
            result = conn.execute(
                sa.text("INSERT INTO card_trigger (trigger) VALUES (:t)"),
                {"t": trigger_text},
            )
            trigger_text_to_id[trigger_text] = result.lastrowid

    # Add trigger_fk to card
    with op.batch_alter_table("card") as batch_op:
        batch_op.add_column(sa.Column("trigger_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_card_trigger", "card_trigger", ["trigger_fk"], ["id"])

    # Populate card.trigger_fk from old card_trigger rows
    for old_id, trigger_text in old_triggers:
        card_fk = old_id_to_card_fk[old_id]
        new_trigger_id = trigger_text_to_id[trigger_text]
        conn.execute(
            sa.text("UPDATE card SET trigger_fk = :tid WHERE id = :cid"),
            {"tid": new_trigger_id, "cid": card_fk},
        )

    # ── card_effect ───────────────────────────────────────────────────────────
    # naip.effect_fk already points to card_effect rows (though table is empty).
    # Rebuild card_effect as a lookup: id, effect UNIQUE.
    # naip.effect_fk FKs need to be rewired after the rebuild.

    old_effects = conn.execute(sa.text("SELECT id, effect FROM card_effect")).fetchall()

    # naip rows that reference old card_effect ids
    naip_effect_rows = conn.execute(
        sa.text("SELECT id, effect_fk FROM naip WHERE effect_fk IS NOT NULL")
    ).fetchall()
    old_effect_id_to_text: dict[int, str] = {r[0]: r[1] for r in old_effects}

    # Drop naip FK to card_effect first (batch rebuild)
    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_constraint("fk_naip_effect", type_="foreignkey")
        batch_op.drop_column("effect_fk")

    op.drop_table("card_effect")
    op.create_table(
        "card_effect",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("effect", sa.String(), nullable=False, unique=True),
    )

    effect_text_to_id: dict[str, int] = {}
    for old_id, effect_text in old_effects:
        if effect_text not in effect_text_to_id:
            result = conn.execute(
                sa.text("INSERT INTO card_effect (effect) VALUES (:e)"),
                {"e": effect_text},
            )
            effect_text_to_id[effect_text] = result.lastrowid

    # Re-add effect_fk to naip pointing at new card_effect
    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("effect_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_naip_effect", "card_effect", ["effect_fk"], ["id"])

    # Restore naip.effect_fk via old id → text → new id
    for naip_id, old_effect_fk in naip_effect_rows:
        text = old_effect_id_to_text.get(old_effect_fk)
        if text and text in effect_text_to_id:
            conn.execute(
                sa.text("UPDATE naip SET effect_fk = :eid WHERE id = :nid"),
                {"eid": effect_text_to_id[text], "nid": naip_id},
            )

    # ── drop naip.trigger_fk (trigger lives on card now) ─────────────────────
    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_constraint("fk_naip_trigger", type_="foreignkey")
        batch_op.drop_column("trigger_fk")


def downgrade() -> None:
    # Restore card_effect and card_trigger with card_fk and is_current columns.
    # Data fidelity is best-effort: one row per card/naip, is_current=True.
    conn = op.get_bind()

    # ── restore naip.trigger_fk ───────────────────────────────────────────────
    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("trigger_fk", sa.Integer(), nullable=True))

    # ── rebuild card_trigger with card_fk + is_current ────────────────────────
    triggers = conn.execute(
        sa.text("SELECT id, trigger FROM card_trigger")
    ).fetchall()
    card_trigger_rows = conn.execute(
        sa.text("SELECT id, trigger_fk FROM card WHERE trigger_fk IS NOT NULL")
    ).fetchall()
    trigger_id_to_text = {r[0]: r[1] for r in triggers}

    with op.batch_alter_table("card") as batch_op:
        batch_op.drop_constraint("fk_card_trigger", type_="foreignkey")
        batch_op.drop_column("trigger_fk")

    op.drop_table("card_trigger")
    op.create_table(
        "card_trigger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("created_ts", sa.Date(), nullable=True, server_default=sa.text("CURRENT_DATE")),
        sa.Column("updated_ts", sa.Date(), nullable=True, server_default=sa.text("CURRENT_DATE")),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("trigger", sa.String(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    card_trigger_id_map: dict[int, int] = {}  # old trigger id → new row id
    for card_id, old_trigger_fk in card_trigger_rows:
        text = trigger_id_to_text.get(old_trigger_fk)
        if text:
            result = conn.execute(
                sa.text("INSERT INTO card_trigger (card_fk, trigger, is_current) VALUES (:c, :t, 1)"),
                {"c": card_id, "t": text},
            )
            card_trigger_id_map[old_trigger_fk] = result.lastrowid

    # ── rebuild card_effect with card_fk + is_current ─────────────────────────
    naip_effect_rows = conn.execute(
        sa.text("SELECT id, effect_fk FROM naip WHERE effect_fk IS NOT NULL")
    ).fetchall()
    effects = conn.execute(sa.text("SELECT id, effect FROM card_effect")).fetchall()
    effect_id_to_text = {r[0]: r[1] for r in effects}

    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_constraint("fk_naip_effect", type_="foreignkey")
        batch_op.drop_column("effect_fk")

    op.drop_table("card_effect")
    op.create_table(
        "card_effect",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("created_ts", sa.Date(), nullable=True, server_default=sa.text("CURRENT_DATE")),
        sa.Column("updated_ts", sa.Date(), nullable=True, server_default=sa.text("CURRENT_DATE")),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("effect", sa.String(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    effect_id_map: dict[int, int] = {}
    for naip_id, old_effect_fk in naip_effect_rows:
        text = effect_id_to_text.get(old_effect_fk)
        if text:
            naip_card = conn.execute(
                sa.text("SELECT card_fk FROM naip WHERE id = :i"), {"i": naip_id}
            ).scalar()
            if naip_card and old_effect_fk not in effect_id_map:
                result = conn.execute(
                    sa.text("INSERT INTO card_effect (card_fk, effect, is_current) VALUES (:c, :e, 1)"),
                    {"c": naip_card, "e": text},
                )
                effect_id_map[old_effect_fk] = result.lastrowid

    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("effect_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_naip_effect", "card_effect", ["effect_fk"], ["id"])

    for naip_id, old_effect_fk in naip_effect_rows:
        new_id = effect_id_map.get(old_effect_fk)
        if new_id:
            conn.execute(
                sa.text("UPDATE naip SET effect_fk = :eid WHERE id = :nid"),
                {"eid": new_id, "nid": naip_id},
            )
