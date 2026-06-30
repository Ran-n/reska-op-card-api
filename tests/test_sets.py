#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/29
"""

import pytest
from sqlmodel import Session

from reska_op_card_api.models import Set


@pytest.fixture(scope="module")
def a_set(test_engine, seed):
    with Session(test_engine) as s:
        row = Set(code="OP-TST", name="Test Set", language_fk=seed["language_fk"])
        s.add(row)
        s.commit()
        s.refresh(row)
        return row.id


def test_list_sets_200(client, read_key):
    r = client.get("/sets/", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_get_set_found(client, read_key, a_set):
    r = client.get(f"/sets/{a_set}", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == a_set
    assert data["code"] == "OP-TST"


def test_get_set_not_found(client, read_key):
    r = client.get("/sets/999999", headers={"X-API-Key": read_key})
    assert r.status_code == 404


def test_get_set_expand_all(client, read_key, a_set):
    r = client.get(f"/sets/{a_set}?expand=all", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert isinstance(r.json()["language"], dict)


def test_list_sets_expand_all(client, read_key, a_set):
    r = client.get("/sets/?expand=all", headers={"X-API-Key": read_key})
    assert r.status_code == 200
    row = next(row for row in r.json() if row["id"] == a_set)
    assert isinstance(row["language"], dict)
