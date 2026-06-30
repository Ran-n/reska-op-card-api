#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/29
"""

import pytest
from sqlmodel import Session

from reska_op_card_api.models import Card, Color, Name, Set


@pytest.fixture(scope="module")
def naip_set(test_engine, seed):
    with Session(test_engine) as s:
        row = Set(code="OP-NAIP", name="Naip Test Set", language_fk=seed["language_fk"])
        s.add(row)
        s.commit()
        s.refresh(row)
        return row.id


@pytest.fixture(scope="module")
def naip_card(test_engine, naip_set, seed):
    with Session(test_engine) as s:
        name_row = Name(name="Nami Test")
        s.add(name_row)
        s.flush()
        card = Card(
            set_fk=naip_set,
            cardtype_fk=seed["cardtype_fk"],
            name_fk=name_row.id,
            number=1,
        )
        s.add(card)
        s.commit()
        s.refresh(card)
        return card.id


@pytest.fixture(scope="module")
def naip_payload(naip_card, naip_set, seed):
    return {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "is_default": True,
    }


@pytest.fixture(scope="module")
def created_naip(client, edit_key, naip_payload):
    r = client.post("/naips/", json=naip_payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 201
    return r.json()


# ── List ─────────────────────────────────────────────────────────────────────


def test_list_naips_200(client, read_key):
    r = client.get("/naips/", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert "rows" in data
    assert "total" in data


def test_list_naips_filter_card(client, read_key, created_naip):
    card_fk = created_naip["card"]
    r = client.get(f"/naips/?card_fk={card_fk}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert all(row["card"] == card_fk for row in data["rows"])


def test_list_naips_filter_is_default(client, read_key, created_naip):
    r = client.get("/naips/?is_default=true", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert all(row["is_default"] for row in data["rows"])


def test_list_naips_search_filter(client, read_key, created_naip, naip_card):
    r = client.get(f"/naips/?card_fk={naip_card}&search=Nami", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert any(row["id"] == created_naip["id"] for row in r.json()["rows"])


def test_list_naips_foil_filter(test_engine, client, edit_key, read_key, naip_set, naip_card, seed):
    payload = {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "is_foil": True,
    }
    r = client.post("/naips/", json=payload, headers={"X-API-Key": edit_key})
    foil_naip_id = r.json()["id"]

    r = client.get(f"/naips/?card_fk={naip_card}&foil=true", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    rows = r.json()["rows"]
    assert any(row["id"] == foil_naip_id for row in rows)
    assert all(row["is_foil"] for row in rows)


def test_list_naips_color_names_any_filter(test_engine, client, edit_key, read_key, naip_set, naip_card, seed):
    with Session(test_engine) as s:
        color = Color(name="Naip Filter Color")
        s.add(color)
        s.commit()
        s.refresh(color)
        color_id = color.id

    payload = {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "colors": [color_id],
    }
    r = client.post("/naips/", json=payload, headers={"X-API-Key": edit_key})
    naip_id = r.json()["id"]

    r = client.get(f"/naips/?card_fk={naip_card}&color_names_any=Naip Filter Color", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert any(row["id"] == naip_id for row in r.json()["rows"])

    r = client.get(f"/naips/?card_fk={naip_card}&color_names_any=Nonexistent Color", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert all(row["id"] != naip_id for row in r.json()["rows"])


def test_list_cards_expand_naips(client, read_key, created_naip, naip_card):
    r = client.get(f"/cards/?set_id={created_naip['set']}&expand=naips", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    card_row = next(row for row in data["rows"] if row["id"] == naip_card)
    assert any(n["id"] == created_naip["id"] for n in card_row["naips"])


def test_list_cards_without_expand_lists_naip_ids(client, read_key, created_naip, naip_card):
    r = client.get(f"/cards/?set_id={created_naip['set']}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    card_row = next(row for row in data["rows"] if row["id"] == naip_card)
    assert created_naip["id"] in card_row["naips"]


def test_get_card_expand_naips_includes_naip_detail_fields(
    test_engine, client, read_key, edit_key, naip_card, naip_set, seed
):
    with Session(test_engine) as s:
        color = Color(name="Red Test")
        s.add(color)
        s.commit()
        s.refresh(color)
        color_id = color.id

    payload = {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "power": 5000,
        "life": 3,
        "counter": 1000,
        "cost": 2,
        "sort_order": 7,
        "serial_max": 100,
        "effect": "Test naip effect",
        "trigger": "Test naip trigger",
        "colors": [color_id],
    }
    r = client.post("/naips/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 201
    naip_id = r.json()["id"]

    r = client.get(f"/cards/{naip_card}?expand=naips", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    naip_row = next(n for n in r.json()["naips"] if n["id"] == naip_id)
    assert naip_row["power"] == 5000
    assert naip_row["life"] == 3
    assert naip_row["counter"] == 1000
    assert naip_row["cost"] == 2
    assert naip_row["sort_order"] == 7
    assert naip_row["serial_max"] == 100
    assert naip_row["effect"] == "Test naip effect"
    assert naip_row["trigger"] == "Test naip trigger"
    assert naip_row["colors"] == [color_id]

    r = client.get(f"/cards/{naip_card}?expand=naips,colors", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    naip_row = next(n for n in r.json()["naips"] if n["id"] == naip_id)
    assert any(c["id"] == color_id for c in naip_row["colors"])


def test_list_naips_includes_naip_detail_fields(client, read_key, edit_key, naip_card, naip_set, seed):
    payload = {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "power": 4000,
        "effect": "List endpoint effect",
    }
    r = client.post("/naips/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 201
    naip_id = r.json()["id"]

    r = client.get(f"/naips/?card_fk={naip_card}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    row = next(n for n in r.json()["rows"] if n["id"] == naip_id)
    assert row["power"] == 4000
    assert row["effect"] == "List endpoint effect"
    assert row["colors"] == []  # no colors were assigned to this naip


# ── Create ───────────────────────────────────────────────────────────────────


def test_create_naip_201(client, edit_key, naip_card, naip_set, seed):
    payload = {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "is_default": False,
        "is_foil": True,
    }
    r = client.post("/naips/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 201
    data = r.json()
    assert data["card"] == naip_card
    assert data["is_foil"] is True


def test_create_naip_negative_cost(client, edit_key, naip_card, naip_set, seed):
    payload = {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "cost": -5,
    }
    r = client.post("/naips/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 422


# ── Get ──────────────────────────────────────────────────────────────────────


def test_get_naip_found(client, read_key, created_naip):
    r = client.get(f"/naips/{created_naip['id']}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == created_naip["id"]


def test_get_naip_not_found(client, read_key):
    r = client.get("/naips/999999", headers={"X-API-Key": read_key})
    assert r.status_code == 404


def test_get_naip_expand_all(client, read_key, created_naip):
    r = client.get(f"/naips/{created_naip['id']}?expand=all", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["card"], dict)
    assert isinstance(data["set"], dict)
    assert isinstance(data["print_variant"], dict)


def test_get_naip_junction_lists_ids_unless_expanded(
    test_engine, client, read_key, edit_key, naip_card, naip_set, seed
):
    with Session(test_engine) as s:
        color = Color(name="Yellow Test")
        s.add(color)
        s.commit()
        s.refresh(color)
        color_id = color.id

    payload = {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "colors": [color_id],
    }
    r = client.post("/naips/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 201
    naip_id = r.json()["id"]

    r = client.get(f"/naips/{naip_id}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert r.json()["colors"] == [color_id]

    r = client.get(f"/naips/{naip_id}?expand=colors", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert any(c["id"] == color_id for c in r.json()["colors"])


def test_list_naips_expand_all(client, read_key, created_naip):
    r = client.get(f"/naips/?card_fk={created_naip['card']}&expand=all", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    row = next(row for row in r.json()["rows"] if row["id"] == created_naip["id"])
    assert isinstance(row["card"], dict)
    assert isinstance(row["set"], dict)


# ── Update ───────────────────────────────────────────────────────────────────


def test_update_naip(client, edit_key, created_naip, seed):
    payload = {
        "card_fk": created_naip["card"],
        "set_fk": created_naip["set"],
        "print_variant_fk": seed["print_variant_fk"],
        "is_default": True,
        "sort_order": 5,
    }
    r = client.put(f"/naips/{created_naip['id']}", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 200
    assert r.json()["sort_order"] == 5


def test_update_naip_not_found(client, edit_key, seed):
    payload = {
        "card_fk": 1,
        "set_fk": 1,
        "print_variant_fk": seed["print_variant_fk"],
    }
    r = client.put("/naips/999999", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 404


# ── Delete ───────────────────────────────────────────────────────────────────


def test_delete_naip(client, read_key, edit_key, naip_card, naip_set, seed):
    payload = {
        "card_fk": naip_card,
        "set_fk": naip_set,
        "print_variant_fk": seed["print_variant_fk"],
        "is_default": False,
    }
    r = client.post("/naips/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 201
    naip_id = r.json()["id"]

    del_r = client.delete(f"/naips/{naip_id}", headers={"X-API-Key": edit_key})
    assert del_r.status_code == 204

    get_r = client.get(f"/naips/{naip_id}", headers={"X-API-Key": read_key})
    assert get_r.status_code == 404


def test_delete_naip_not_found(client, edit_key):
    r = client.delete("/naips/999999", headers={"X-API-Key": edit_key})
    assert r.status_code == 404
