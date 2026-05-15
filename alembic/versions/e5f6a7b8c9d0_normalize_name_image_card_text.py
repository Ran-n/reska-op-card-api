"""normalize name and image as lookup tables; add card.effect_fk/trigger_fk; add history tables; drop card.desc and card_trigger junction

New tables:
  name(id, name UNIQUE)
  image(id, path UNIQUE)
  card_effect_history(id, card_fk, effect_fk, valid_from, valid_to)
  card_trigger_history(id, card_fk, trigger_fk, valid_from, valid_to)

card changes:
  name -> name_fk
  drop desc
  add effect_fk -> effect
  add trigger_fk -> trigger

naip changes:
  name -> name_fk
  image_path -> image_fk

drop:
  card_trigger junction

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-05-15 00:00:00.000000

"""

from collections.abc import Sequence
from datetime import date

import sqlalchemy as sa
from alembic import op

revision: str = "e5f6a7b8c9d0"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TODAY = str(date.today())


def upgrade() -> None:
    conn = op.get_bind()

    # ── create name lookup ────────────────────────────────────────────────────
    op.create_table(
        "name",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False, unique=True),
    )

    # ── create image lookup ───────────────────────────────────────────────────
    op.create_table(
        "image",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("path", sa.String(), nullable=False, unique=True),
    )

    # ── create history tables ─────────────────────────────────────────────────
    op.create_table(
        "card_effect_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("effect_fk", sa.Integer(), sa.ForeignKey("effect.id"), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
    )

    op.create_table(
        "card_trigger_history",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("trigger_fk", sa.Integer(), sa.ForeignKey("trigger.id"), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_to", sa.Date(), nullable=True),
    )

    # ── populate name from card ───────────────────────────────────────────────
    card_rows = conn.execute(sa.text("SELECT id, name FROM card")).fetchall()
    name_to_id: dict[str, int] = {}
    for _card_id, name in card_rows:
        if name and name not in name_to_id:
            result = conn.execute(
                sa.text("INSERT INTO name (name) VALUES (:n)"), {"n": name}
            )
            name_to_id[name] = result.lastrowid

    # populate name from naip (may add new entries)
    naip_rows = conn.execute(sa.text("SELECT id, name, image_path FROM naip")).fetchall()
    for _naip_id, name, _img in naip_rows:
        if name and name not in name_to_id:
            result = conn.execute(
                sa.text("INSERT INTO name (name) VALUES (:n)"), {"n": name}
            )
            name_to_id[name] = result.lastrowid

    # ── populate image from naip ──────────────────────────────────────────────
    image_to_id: dict[str, int] = {}
    for _naip_id, _name, image_path in naip_rows:
        if image_path and image_path not in image_to_id:
            result = conn.execute(
                sa.text("INSERT INTO image (path) VALUES (:p)"), {"p": image_path}
            )
            image_to_id[image_path] = result.lastrowid

    # ── migrate card ──────────────────────────────────────────────────────────
    # read card trigger data from card_trigger junction before dropping it
    card_trigger_rows = conn.execute(
        sa.text("SELECT card_fk, trigger_fk FROM card_trigger")
    ).fetchall()
    card_trigger_map = {r[0]: r[1] for r in card_trigger_rows}

    # read current effect_fk from naip (per-card, pick first naip's effect as card's)
    # card has no effect_fk yet — seed history from naip data where available
    card_effect_map: dict[int, int] = {}
    naip_effects = conn.execute(
        sa.text("SELECT card_fk, effect_fk FROM naip WHERE effect_fk IS NOT NULL")
    ).fetchall()
    for card_fk, effect_fk in naip_effects:
        if card_fk not in card_effect_map:
            card_effect_map[card_fk] = effect_fk

    with op.batch_alter_table("card") as batch_op:
        batch_op.add_column(sa.Column("name_fk", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("effect_fk", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("trigger_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_card_name", "name", ["name_fk"], ["id"])
        batch_op.create_foreign_key("fk_card_effect", "effect", ["effect_fk"], ["id"])
        batch_op.create_foreign_key("fk_card_trigger", "trigger", ["trigger_fk"], ["id"])

    for card_id, name in card_rows:
        name_id = name_to_id.get(name)
        effect_id = card_effect_map.get(card_id)
        trigger_id = card_trigger_map.get(card_id)
        conn.execute(
            sa.text(
                "UPDATE card SET name_fk = :n, effect_fk = :e, trigger_fk = :t WHERE id = :id"
            ),
            {"n": name_id, "e": effect_id, "t": trigger_id, "id": card_id},
        )

    # seed history for cards that have effect/trigger
    for card_id, effect_fk in card_effect_map.items():
        conn.execute(
            sa.text(
                "INSERT INTO card_effect_history (card_fk, effect_fk, valid_from) VALUES (:c, :e, :d)"
            ),
            {"c": card_id, "e": effect_fk, "d": TODAY},
        )
    for card_id, trigger_fk in card_trigger_map.items():
        conn.execute(
            sa.text(
                "INSERT INTO card_trigger_history (card_fk, trigger_fk, valid_from) VALUES (:c, :t, :d)"
            ),
            {"c": card_id, "t": trigger_fk, "d": TODAY},
        )

    with op.batch_alter_table("card") as batch_op:
        batch_op.drop_column("name")
        batch_op.drop_column("desc")

    # ── drop card_trigger junction ────────────────────────────────────────────
    op.drop_table("card_trigger")

    # ── migrate naip ──────────────────────────────────────────────────────────
    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("name_fk", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("image_fk", sa.Integer(), nullable=True))
        batch_op.create_foreign_key("fk_naip_name", "name", ["name_fk"], ["id"])
        batch_op.create_foreign_key("fk_naip_image", "image", ["image_fk"], ["id"])

    for naip_id, name, image_path in naip_rows:
        name_id = name_to_id.get(name)
        image_id = image_to_id.get(image_path) if image_path else None
        conn.execute(
            sa.text("UPDATE naip SET name_fk = :n, image_fk = :i WHERE id = :id"),
            {"n": name_id, "i": image_id, "id": naip_id},
        )

    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_column("name")
        batch_op.drop_column("image_path")


def downgrade() -> None:
    conn = op.get_bind()

    # ── restore naip.name and naip.image_path ─────────────────────────────────
    naip_rows = conn.execute(
        sa.text("SELECT n.id, nm.name, i.path FROM naip n "
                "LEFT JOIN name nm ON nm.id = n.name_fk "
                "LEFT JOIN image i ON i.id = n.image_fk")
    ).fetchall()

    with op.batch_alter_table("naip") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("image_path", sa.String(), nullable=True))

    for naip_id, name, image_path in naip_rows:
        conn.execute(
            sa.text("UPDATE naip SET name = :n, image_path = :i WHERE id = :id"),
            {"n": name, "i": image_path, "id": naip_id},
        )

    with op.batch_alter_table("naip") as batch_op:
        batch_op.drop_constraint("fk_naip_name", type_="foreignkey")
        batch_op.drop_constraint("fk_naip_image", type_="foreignkey")
        batch_op.drop_column("name_fk")
        batch_op.drop_column("image_fk")

    # ── restore card_trigger junction ─────────────────────────────────────────
    op.create_table(
        "card_trigger",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("card_fk", sa.Integer(), sa.ForeignKey("card.id"), nullable=False),
        sa.Column("trigger_fk", sa.Integer(), sa.ForeignKey("trigger.id"), nullable=False),
    )

    card_rows = conn.execute(
        sa.text("SELECT c.id, nm.name, c.effect_fk, c.trigger_fk FROM card c "
                "LEFT JOIN name nm ON nm.id = c.name_fk")
    ).fetchall()

    for card_id, _name, _effect_fk, trigger_fk in card_rows:
        if trigger_fk:
            conn.execute(
                sa.text("INSERT INTO card_trigger (card_fk, trigger_fk) VALUES (:c, :t)"),
                {"c": card_id, "t": trigger_fk},
            )

    # ── restore card.name and card.desc ───────────────────────────────────────
    with op.batch_alter_table("card") as batch_op:
        batch_op.add_column(sa.Column("name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("desc", sa.String(), nullable=True))

    for card_id, name, _effect_fk, _trigger_fk in card_rows:
        conn.execute(
            sa.text("UPDATE card SET name = :n WHERE id = :id"),
            {"n": name, "id": card_id},
        )

    with op.batch_alter_table("card") as batch_op:
        batch_op.drop_constraint("fk_card_name", type_="foreignkey")
        batch_op.drop_constraint("fk_card_effect", type_="foreignkey")
        batch_op.drop_constraint("fk_card_trigger", type_="foreignkey")
        batch_op.drop_column("name_fk")
        batch_op.drop_column("effect_fk")
        batch_op.drop_column("trigger_fk")

    op.drop_table("card_trigger_history")
    op.drop_table("card_effect_history")
    op.drop_table("image")
    op.drop_table("name")
