"""add card_effect and card_trigger tables; migrate effect/trigger off card and naip

Revision ID: f3a9b2c1d4e5
Revises: c3f8a1d92e74
Create Date: 2026-05-14 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa  # noqa: I001
from alembic import op

revision: str = "f3a9b2c1d4e5"
down_revision: str | Sequence[str] | None = "c3f8a1d92e74"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "card_effect",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("created_ts", sa.Date(), nullable=True, server_default=sa.text("CURRENT_DATE")),
        sa.Column("updated_ts", sa.Date(), nullable=True, server_default=sa.text("CURRENT_DATE")),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("effect", sa.String(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "card_trigger",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("created_ts", sa.Date(), nullable=True, server_default=sa.text("CURRENT_DATE")),
        sa.Column("updated_ts", sa.Date(), nullable=True, server_default=sa.text("CURRENT_DATE")),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("trigger", sa.String(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    # Migrate naip.effect → card_effect (one row per naip that has an effect,
    # marked is_current=True; card_fk taken from naip.card_fk)
    conn = op.get_bind()
    naips = conn.execute(sa.text("SELECT id, card_fk, effect, trigger FROM naip")).fetchall()

    effect_naip_map: dict[int, int] = {}  # naip.id → card_effect.id
    trigger_naip_map: dict[int, int] = {}  # naip.id → card_trigger.id

    for naip_id, card_fk, effect, trigger in naips:
        if effect:
            result = conn.execute(
                sa.text("INSERT INTO card_effect (card_fk, effect, is_current) VALUES (:c, :e, 1)"),
                {"c": card_fk, "e": effect},
            )
            effect_naip_map[naip_id] = result.lastrowid
        if trigger:
            result = conn.execute(
                sa.text("INSERT INTO card_trigger (card_fk, trigger, is_current) VALUES (:c, :t, 1)"),
                {"c": card_fk, "t": trigger},
            )
            trigger_naip_map[naip_id] = result.lastrowid

    # Migrate card.trigger → card_trigger (cards that have a trigger not already
    # covered by a naip row for that card)
    cards = conn.execute(sa.text("SELECT id, trigger FROM card WHERE trigger IS NOT NULL")).fetchall()
    card_trigger_map: dict[int, int] = {}  # card.id → card_trigger.id

    covered_cards = {
        conn.execute(sa.text("SELECT card_fk FROM card_trigger WHERE id = :i"), {"i": ct_id}).scalar()
        for ct_id in trigger_naip_map.values()
    }
    for card_id, trigger in cards:
        if card_id not in covered_cards:
            result = conn.execute(
                sa.text("INSERT INTO card_trigger (card_fk, trigger, is_current) VALUES (:c, :t, 1)"),
                {"c": card_id, "t": trigger},
            )
            card_trigger_map[card_id] = result.lastrowid

    # Add FK columns to naip
    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("effect_fk", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("trigger_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_naip_effect", "card_effect", ["effect_fk"], ["id"])
        batch_op.create_foreign_key("fk_naip_trigger", "card_trigger", ["trigger_fk"], ["id"])

    # Populate the FK columns
    for naip_id, ce_id in effect_naip_map.items():
        conn.execute(sa.text("UPDATE naip SET effect_fk = :v WHERE id = :i"), {"v": ce_id, "i": naip_id})
    for naip_id, ct_id in trigger_naip_map.items():
        conn.execute(sa.text("UPDATE naip SET trigger_fk = :v WHERE id = :i"), {"v": ct_id, "i": naip_id})

    # Drop old text columns
    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_column("effect")
        batch_op.drop_column("trigger")

    with op.batch_alter_table("card") as batch_op:
        batch_op.drop_column("trigger")


def downgrade() -> None:
    with op.batch_alter_table("card") as batch_op:
        batch_op.add_column(sa.Column("trigger", sa.String(), nullable=True))

    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("effect", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("trigger", sa.String(), nullable=True))

    conn = op.get_bind()

    # Restore naip.effect and naip.trigger from FK rows
    naips = conn.execute(sa.text("SELECT id, effect_fk, trigger_fk FROM naip")).fetchall()
    for naip_id, effect_fk, trigger_fk in naips:
        if effect_fk:
            effect = conn.execute(sa.text("SELECT effect FROM card_effect WHERE id = :i"), {"i": effect_fk}).scalar()
            conn.execute(sa.text("UPDATE naip SET effect = :v WHERE id = :i"), {"v": effect, "i": naip_id})
        if trigger_fk:
            trigger = conn.execute(sa.text("SELECT trigger FROM card_trigger WHERE id = :i"), {"i": trigger_fk}).scalar()
            conn.execute(sa.text("UPDATE naip SET trigger = :v WHERE id = :i"), {"v": trigger, "i": naip_id})

    # Restore card.trigger from is_current card_trigger rows
    card_triggers = conn.execute(sa.text("SELECT card_fk, trigger FROM card_trigger WHERE is_current = 1")).fetchall()
    for card_id, trigger in card_triggers:
        conn.execute(sa.text("UPDATE card SET trigger = :v WHERE id = :i"), {"v": trigger, "i": card_id})

    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_constraint("fk_naip_effect", type_="foreignkey")
        batch_op.drop_constraint("fk_naip_trigger", type_="foreignkey")
        batch_op.drop_column("effect_fk")
        batch_op.drop_column("trigger_fk")

    op.drop_table("card_trigger")
    op.drop_table("card_effect")
