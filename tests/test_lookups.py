#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/29
"""

import pytest

_LOOKUP_ROUTES = [
    "/lookups/cardtypes",
    "/lookups/colors",
    "/lookups/tribes",
    "/lookups/attributes",
    "/lookups/rarities",
    "/lookups/print-variants",
    "/lookups/blocks",
    "/lookups/formats",
    "/lookups/keywords",
    "/lookups/reswords",
    "/lookups/artists",
    "/lookups/sets",
    "/lookups/settypes",
    "/lookups/languages",
    "/lookups/regions",
]


@pytest.mark.parametrize("route", _LOOKUP_ROUTES)
def test_lookup_returns_list(client, read_key, route):
    r = client.get(route, headers={"X-API-Key": read_key})
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_cardtypes_have_symbol(client, read_key):
    r = client.get("/lookups/cardtypes", headers={"X-API-Key": read_key})
    data = r.json()
    assert len(data) > 0
    assert all("symbol" in item for item in data)


def test_languages_have_code(client, read_key):
    r = client.get("/lookups/languages", headers={"X-API-Key": read_key})
    data = r.json()
    assert len(data) > 0
    codes = {item["code"] for item in data}
    assert "en" in codes


def test_print_variants_have_std(client, read_key):
    r = client.get("/lookups/print-variants", headers={"X-API-Key": read_key})
    data = r.json()
    symbols = {item["symbol"] for item in data}
    assert "STD" in symbols
