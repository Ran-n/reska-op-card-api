#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/29
"""

import pytest
from sqlmodel import Session

from reska_op_card_api.models import Set


@pytest.fixture(scope="module")
def test_set(test_engine, seed):
    with Session(test_engine) as s:
        row = Set(code="OP-CARD", name="Card Test Set", language_fk=seed["language_fk"])
        s.add(row)
        s.commit()
        s.refresh(row)
        return row.id


@pytest.fixture(scope="module")
def card_payload(test_set, seed):
    return {
        "set_fk": test_set,
        "cardtype_fk": seed["cardtype_fk"],
        "number": 1,
        "name": "Monkey D. Luffy",
    }


@pytest.fixture(scope="module")
def created_card(client, edit_key, card_payload):
    r = client.post("/cards/", json=card_payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 201
    return r.json()


# ── List ─────────────────────────────────────────────────────────────────────


def test_list_cards_200(client, read_key):
    r = client.get("/cards/", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert "rows" in data
    assert "total" in data


def test_list_cards_paginate(client, read_key):
    r = client.get("/cards/?limit=1&offset=0", headers={"X-API-Key": read_key})
    assert r.status_code == 200


def test_list_cards_name_filter(client, read_key, created_card):
    name = created_card["name"]
    r = client.get(f"/cards/?name={name[:5]}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert r.json()["total"] >= 1


# ── Create ───────────────────────────────────────────────────────────────────


def test_create_card_201(client, edit_key, test_set, seed):
    payload = {
        "set_fk": test_set,
        "cardtype_fk": seed["cardtype_fk"],
        "number": 99,
        "name": "Roronoa Zoro",
        "cost": 4,
        "power": 6000,
    }
    r = client.post("/cards/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Roronoa Zoro"
    assert data["cost"] == 4
    assert data["power"] == 6000


def test_create_card_invalid_number(client, edit_key, test_set, seed):
    payload = {
        "set_fk": test_set,
        "cardtype_fk": seed["cardtype_fk"],
        "number": 0,
        "name": "Invalid",
    }
    r = client.post("/cards/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 422


def test_create_card_negative_cost(client, edit_key, test_set, seed):
    payload = {
        "set_fk": test_set,
        "cardtype_fk": seed["cardtype_fk"],
        "number": 2,
        "name": "Invalid",
        "cost": -1,
    }
    r = client.post("/cards/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 422


def test_create_card_too_many_blocks(client, edit_key, test_set, seed):
    payload = {
        "set_fk": test_set,
        "cardtype_fk": seed["cardtype_fk"],
        "number": 3,
        "name": "Invalid",
        "blocks": [1, 2],
    }
    r = client.post("/cards/", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 422


# ── Get ──────────────────────────────────────────────────────────────────────


def test_get_card_found(client, read_key, created_card):
    r = client.get(f"/cards/{created_card['id']}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == created_card["id"]
    assert "naips" in data


def test_get_card_not_found(client, read_key):
    r = client.get("/cards/999999", headers={"X-API-Key": read_key})
    assert r.status_code == 404


# ── Update ───────────────────────────────────────────────────────────────────


def test_update_card(client, edit_key, created_card, test_set, seed):
    payload = {
        "set_fk": test_set,
        "cardtype_fk": seed["cardtype_fk"],
        "number": created_card["number"],
        "name": "Monkey D. Luffy (Updated)",
        "power": 7000,
    }
    r = client.put(f"/cards/{created_card['id']}", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 200
    assert r.json()["name"] == "Monkey D. Luffy (Updated)"
    assert r.json()["power"] == 7000


def test_update_card_not_found(client, edit_key, test_set, seed):
    payload = {
        "set_fk": test_set,
        "cardtype_fk": seed["cardtype_fk"],
        "number": 1,
        "name": "Ghost",
    }
    r = client.put("/cards/999999", json=payload, headers={"X-API-Key": edit_key})
    assert r.status_code == 404


# ── Delete ───────────────────────────────────────────────────────────────────


def test_delete_card(client, edit_key, test_set, seed):
    payload = {
        "set_fk": test_set,
        "cardtype_fk": seed["cardtype_fk"],
        "number": 50,
        "name": "Temporary Card",
    }
    create_r = client.post("/cards/", json=payload, headers={"X-API-Key": edit_key})
    assert create_r.status_code == 201
    card_id = create_r.json()["id"]

    del_r = client.delete(f"/cards/{card_id}", headers={"X-API-Key": edit_key})
    assert del_r.status_code == 204

    get_r = client.get(f"/cards/{card_id}", headers={"X-API-Key": edit_key})
    assert get_r.status_code == 404


def test_delete_card_not_found(client, edit_key):
    r = client.delete("/cards/999999", headers={"X-API-Key": edit_key})
    assert r.status_code == 404
