#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/29
"""

import pytest
from sqlmodel import Session

from reska_op_card_api.models import Card, Name, Set


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
    card_fk = created_naip["card_fk"]
    r = client.get(f"/naips/?card_fk={card_fk}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    assert all(row["card_fk"] == card_fk for row in data["rows"])


def test_list_naips_filter_is_default(client, read_key, created_naip):
    r = client.get("/naips/?is_default=true", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert all(row["is_default"] for row in data["rows"])


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
    assert data["card_fk"] == naip_card
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


# ── Update ───────────────────────────────────────────────────────────────────


def test_update_naip(client, edit_key, created_naip, seed):
    payload = {
        "card_fk": created_naip["card_fk"],
        "set_fk": created_naip["set_fk"],
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
