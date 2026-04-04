# -*- coding: UTF-8 -*-

import json
import re

import pytest
import responses

import kbg as k


def test_strip_mongodb_id():
    assert k._strip_mongodb_id({}) == {}
    assert k._strip_mongodb_id({"_id": "yo"}) == {"id": "yo"}


def test_strip_mongodb_ids():
    xs = [{"id": 1}, {"id": 2}, {"id": 3}]
    assert xs == k._strip_mongodb_ids(xs)

    xs_id = []
    for x in xs:
        x = dict(x)
        x["_id"] = "something123"
        xs_id.append(x)

    assert xs == k._strip_mongodb_ids(xs_id)
    assert k._strip_mongodb_ids([{"id": 1, "_id": "xx"}, {"_id": 2}, {"id": 3}]) == [
        {"id": 1},
        {"id": 2},
        {"id": 3},
    ]


@pytest.fixture
def unauthenticated_kbg():
    return k.UnauthenticatedKbg()


def test_unauthenticated_logged_in(unauthenticated_kbg):
    assert not unauthenticated_kbg.logged_in()


def test_get_stores(unauthenticated_kbg):
    stores = {"locales": [{"code": "ABC"}, {"code": "DEF"}]}
    with responses.RequestsMock() as resps:
        resps.add(responses.GET, k.API_ENDPOINT + "/locales", json={"locales": stores})
        got_stores = unauthenticated_kbg.get_stores()
    assert stores == got_stores


def test_get_store(unauthenticated_kbg):
    store1 = {"code": "ABC", "some": "attr1"}
    store2 = {"code": "DEF", "some": "attr2"}
    with responses.RequestsMock() as resps:
        resps.add(
            responses.GET,
            k.API_ENDPOINT + "/locales",
            json={"locales": [store1, store2]},
        )

        assert store1 == unauthenticated_kbg.get_store("ABC")
        assert store2 == unauthenticated_kbg.get_store("DEF")
        assert unauthenticated_kbg.get_store("GHI") is None


def test_get_store_availabilities(unauthenticated_kbg):
    store = "XYZ"
    availabilities = {"id1": 1, "id2": 3, "id3": 2000, "id4": 0}

    with responses.RequestsMock() as resps:
        resps.add(responses.GET, k.API_ENDPOINT + "/available", json={"available": availabilities})
        got_availabilities = unauthenticated_kbg.get_store_availabilities(store)
        assert len(resps.calls) == 1
        assert re.search(rf"\?locale={store}$", resps.calls[0].request.url)

    assert availabilities == got_availabilities


def test_get_store_offer(unauthenticated_kbg):
    store = "XYZ"
    offer = {
        "products": [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}],
        "categories": [{"id": "c1"}, {"id": "c2"}],
        "promogroups": [],
        "families": [{"id": "f1"}, {"id": "f2"}, {"id": "f3"}],
        "producers": [{"id": "P1"}],
    }

    with responses.RequestsMock() as resps:
        resps.add(responses.GET, k.API_ENDPOINT + "/init", json=offer)
        got_offer = unauthenticated_kbg.get_store_offer(store)
        assert len(resps.calls) == 1
        assert re.search(rf"\?locale={store}$", resps.calls[0].request.url)

    assert offer == got_offer

    with responses.RequestsMock() as resps:
        assert offer == unauthenticated_kbg.get_store_offer(store)
        assert len(resps.calls) == 0

        resps.add(responses.GET, k.API_ENDPOINT + "/init", json=offer)
        assert offer == unauthenticated_kbg.get_store_offer("DEF")
        assert len(resps.calls) == 1

    with responses.RequestsMock() as resps:
        resps.add(responses.GET, k.API_ENDPOINT + "/init", json=offer)
        assert offer == unauthenticated_kbg.get_store_offer(store, force=True)
        assert len(resps.calls) == 1

        assert offer == unauthenticated_kbg.get_store_offer(store, force=True)
        assert len(resps.calls) == 2

        assert offer == unauthenticated_kbg.get_store_offer(store)
        assert len(resps.calls) == 2


def test_get_store_offer_dicts(unauthenticated_kbg):
    store = "XYZ"
    offer = {
        "products": [
            {"producerproduct_id": "p1", "_id": "x"},
            {"producerproduct_id": "p2", "_id": "y"},
        ],
        "categories": [{"id": "c1"}, {"id": "c2"}],
        "promogroups": [],
        "families": [{"id": "f1"}, {"id": "f2"}],
        "producers": [{"id": "P1", "name": "A"}],
    }

    with responses.RequestsMock() as resps:
        resps.add(responses.GET, k.API_ENDPOINT + "/init", json=offer)
        offer_dict = unauthenticated_kbg.get_store_offer_dicts(store)
        assert len(resps.calls) == 1
        assert re.search(rf"\?locale={store}$", resps.calls[0].request.url)

    assert offer_dict == {
        "products": {
            "p1": {"id": "p1"},
            "p2": {"id": "p2"},
        },
        "categories": {"c1": {"id": "c1"}, "c2": {"id": "c2"}},
        "promogroups": {},
        "families": {"f1": {"id": "f1"}, "f2": {"id": "f2"}},
        "producers": {"P1": {"id": "P1", "name": "A"}},
    }


@pytest.fixture
def authenticated_kbg():
    email = "yo@example.com"
    password = "topsecret"
    token = "secret-token"

    with responses.RequestsMock() as resps:
        resps.add(responses.POST, k.API_ENDPOINT + "/login", json={"token": token})
        client = k.Kbg(email, password)
        assert len(resps.calls) == 1

    return client, email, token


def test_internals_token(authenticated_kbg):
    client, _, token = authenticated_kbg
    assert token == client._token


def test_logged_in(authenticated_kbg):
    client, _, _ = authenticated_kbg
    assert client.logged_in()


def test_get_customer_information(authenticated_kbg):
    client, email, token = authenticated_kbg
    customer = {
        "email": email,
        "some": "field",
        "another": "one",
        "yes": True,
        "no": False,
    }

    with responses.RequestsMock() as resps:
        resps.add(responses.GET, k.API_ENDPOINT + "/api/consumer", json={"consumer": customer})

        got_customer = client.get_customer_information()

        assert len(resps.calls) == 1
        headers = resps.calls[0].request.headers
        assert "Authorization" in headers
        assert f"Bearer {token}" == headers["Authorization"]

    assert customer == got_customer


def test_get_customer_orders(authenticated_kbg):
    client, _, _ = authenticated_kbg

    with responses.RequestsMock() as resps:
        resps.add(
            responses.GET,
            k.API_ENDPOINT + "/api/orders/fetch-for-consumer",
            json={
                "items": [
                    {
                        "_id": "xx",
                        "locale": "XYZ",
                        "status": 0,
                        "items": [
                            {"_id": "xy", "id": 42},
                            {"_id": "xp", "id": 43},
                        ],
                    },
                    {
                        "_id": "xz",
                        "locale": "XYZ",
                        "status": 0,
                        "items": [
                            {"_id": "xm", "id": 42},
                            {"_id": "xn", "id": 44},
                        ],
                    },
                ],
                "count": 2,
            },
        )

        resp = client.get_customer_orders()
        assert resp == {
            "orders": [
                {"id": "xx", "store": "XYZ",
                 "status": 0,
                 "status_title": "créée",
                 "products": [{"id": 42}, {"id": 43}]},
                {"id": "xz", "store": "XYZ",
                 "status": 0,
                 "status_title": "créée",
                 "products": [{"id": 42}, {"id": 44}]},
            ],
            "count": 2,
            "page": 1,
            "next_page": None,
        }


def test_get_all_customer_orders(authenticated_kbg):
    client, _, _ = authenticated_kbg

    mock_orders = {
        1: [
            {
                "_id": "xx",
                "locale": "ABC",
                "status": 0,
                "items": [
                    {"_id": "xy", "id": 42},
                    {"_id": "xp", "id": 43},
                ],
            }
        ],
        2: [
            {
                "_id": "xz",
                "locale": "XYZ",
                "status": 0,
                "items": [
                    {"_id": "xm", "id": 42},
                    {"_id": "xn", "id": 44},
                ],
            }
        ],
    }

    def get_mock_orders(request):
        m = re.match(r".*\?page=(\d+)", request.url)
        assert m is not None
        page = int(m.group(1))
        assert page in mock_orders
        orders = mock_orders[page]
        resp_body = {"items": orders, "count": 2}
        return (200, {}, json.dumps(resp_body))

    with responses.RequestsMock() as resps:
        resps.add_callback(
            responses.GET,
            k.API_ENDPOINT + "/api/orders/fetch-for-consumer",
            content_type="application/json",
            callback=get_mock_orders,
        )

        all_orders = client.get_all_customer_orders()
        assert len(resps.calls) == 0

        order1 = next(all_orders)
        assert order1 == {"id": "xx", "store": "ABC",
                          "status": 0,
                          "status_title": "créée",
                          "products": [{"id": 42}, {"id": 43}]}
        assert len(resps.calls) == 1

        order2 = next(all_orders)
        assert order2 == {"id": "xz", "store": "XYZ",
                          "status": 0,
                          "status_title": "créée",
                          "products": [{"id": 42}, {"id": 44}]}
        assert len(resps.calls) == 2

        with pytest.raises(StopIteration):
            next(all_orders)
        assert len(resps.calls) == 2


def test_get_all_full_customer_orders(authenticated_kbg):
    client, _, _ = authenticated_kbg

    with responses.RequestsMock() as resps:
        resps.add(
            responses.GET,
            k.API_ENDPOINT + "/api/orders/fetch-for-consumer",
            json={
                "items": [
                    {
                        "_id": "xx",
                        "locale": "ABC",
                        "status": 0,
                        "items": [{"_id": "p1"}, {"_id": "p2"}],
                    }
                ],
                "count": 1,
            },
        )

        resps.add(
            responses.GET,
            k.API_ENDPOINT + "/api/orders/fetch-detail",
            json={
                "order": {
                    "_id": "xx",
                    "locale": "ABC",
                    "status": 0,
                    "items": [
                        {"producerproduct_id": "p1", "quantity": 1},
                        {"producerproduct_id": "p2", "quantity": 2},
                    ],
                    "producerproducts": [
                        {"_id": "p1", "product_name": "product 1"},
                        {"_id": "p2", "product_name": "product 2"},
                    ],
                }
            },
        )

        all_orders = client.get_all_customer_orders(full=True)
        assert len(resps.calls) == 0

        order1 = next(all_orders)
        assert order1 == {
            "id": "xx",
            "store": "ABC",
            "status": 0,
            "status_title": "créée",
            "products": [
                {"id": "p1", "product_name": "product 1", "quantity": 1},
                {"id": "p2", "product_name": "product 2", "quantity": 2},
            ],
        }
        assert len(resps.calls) == 2

        with pytest.raises(StopIteration):
            next(all_orders)
        assert len(resps.calls) == 2


def test_get_customer_order(authenticated_kbg):
    client, _, _ = authenticated_kbg

    with responses.RequestsMock() as resps:
        resps.add(
            responses.GET,
            k.API_ENDPOINT + "/api/orders/fetch-detail",
            json={
                "order": {
                    "_id": "xxx",
                    "locale": "XYZ",
                    "status": 0,
                    "items": [
                        {"producerproduct_id": "p1", "_id": "x", "quantity": 1},
                        {"producerproduct_id": "p2", "_id": "y", "quantity": 2},
                    ],
                    "producerproducts": [
                        {"_id": "p1", "product_name": "product 1"},
                        {"_id": "p2", "product_name": "product 2"},
                    ],
                }
            },
        )

        order = client.get_customer_order("xxx")
        assert order == {
            "id": "xxx",
            "store": "XYZ",
            "status": 0,
            "status_title": "créée",
            "products": [
                {"id": "p1", "product_name": "product 1", "quantity": 1},
                {"id": "p2", "product_name": "product 2", "quantity": 2},
            ],
        }


def test_get_store_status(authenticated_kbg):
    client, _, _ = authenticated_kbg

    with responses.RequestsMock() as resps:
        closed_tags = ["FRAIS", "ORDERS"]
        availability = {
            "available": {},
            "globalorder": {"status": 2},
            "globalorderlocales": [
                {
                    "_id": "abc",
                    "id": "abc",
                    "locale": "BIC",
                    "closed_tags": closed_tags,
                    "distributions": [],
                }
            ],
        }

        resps.add(responses.GET, k.API_ENDPOINT + "/available?locale=BIC", json=availability)

        assert {
                   "is_active": True,
                   "is_full": True,
                   "full_tags": closed_tags,
               } == client.get_store_status("BIC")

        resps.add(
            responses.GET,
            k.API_ENDPOINT + "/available?locale=DEF",
            json={"message": "globalorder-not-found"},
        )

        assert client.get_store_status("DEF") == {
            "is_active": False,
            "is_full": False,
            "full_tags": [],
        }
