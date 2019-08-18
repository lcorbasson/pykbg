# -*- coding: UTF-8 -*-

import re
import json
import responses
import unittest

import kbg as k


class TestUtilities(unittest.TestCase):
    def test_strip_mongodb_id(self):
        self.assertEqual({}, k._strip_mongodb_id({}))
        self.assertEqual({}, k._strip_mongodb_id({"_id": "yo"}))

    def test_strip_mongodb_ids(self):
        xs = [{"id": 1}, {"id": 2}, {"id": 3}]
        self.assertSequenceEqual(xs, k._strip_mongodb_ids(xs))

        xs_id = []
        for x in xs:
            x = dict(x)
            x["_id"] = "something123"
            xs_id.append(x)

        self.assertSequenceEqual(xs, k._strip_mongodb_ids(xs_id))


class TestUnauthenticatedKbg(unittest.TestCase):
    def setUp(self):
        with responses.RequestsMock() as resps:
            self.k = k.UnauthenticatedKbg()
            self.assertEqual(0, len(resps.calls))

    @responses.activate
    def test_logged_in(self):
        self.assertFalse(self.k.logged_in())

    def test_get_stores(self):
        stores = {"locales": [{"code": "ABC"}, {"code": "DEF"}]}
        with responses.RequestsMock() as resps:
            resps.add(responses.GET, k.API_ENDPOINT + "/locales",
                    json={"locales": stores})
            got_stores = self.k.get_stores()
        self.assertSequenceEqual(stores, got_stores)

    def test_get_store_availabilities(self):
        store = "XYZ"
        availabilities = {"id1": 1, "id2": 3, "id3": 2000, "id4": 0}

        with responses.RequestsMock() as resps:
            resps.add(responses.GET, k.API_ENDPOINT + "/available",
                    json={"available": availabilities})
            got_availabilities = self.k.get_store_availabilities(store)
            self.assertEqual(1, len(resps.calls))
            self.assertRegexpMatches(resps.calls[0].request.url,
                    r"\?locale=%s$" % store)

        self.assertSequenceEqual(availabilities, got_availabilities)

    def test_get_store_offer(self):
        store = "XYZ"
        offer = {
            "products": [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}],
            "categories": [{"id": "c1"}, {"id": "c2"}],
            "promogroups": [],
            "families": [{"id": "f1"}, {"id": "f2"}, {"id": "f3"}],
            "producers": [{"id": "P1"}],
        }

        with responses.RequestsMock() as resps:
            resps.add(responses.GET, k.API_ENDPOINT + "/init",
                    json=offer)
            got_offer = self.k.get_store_offer(store)
            self.assertEqual(1, len(resps.calls))
            self.assertRegexpMatches(resps.calls[0].request.url,
                    r"\?locale=%s$" % store)

        self.assertSequenceEqual(offer, got_offer)


class TestKbg(unittest.TestCase):
    def setUp(self):
        self.email = "yo@example.com"
        self.password = "topsecret"
        self.token = "secret-token"

        with responses.RequestsMock() as resps:
            resps.add(responses.POST, k.API_ENDPOINT + "/login",
                    json={"token": self.token})

            self.k = k.Kbg(self.email, self.password)

            self.assertEqual(1, len(resps.calls))

    @responses.activate
    def test_internals_token(self):
        self.assertEqual(self.token, self.k._token)

    @responses.activate
    def test_logged_in(self):
        self.assertTrue(self.k.logged_in())

    def test_get_customer_information(self):
        customer = {
            "email": self.email,
            "some": "field",
            "another": "one",
            "yes": True,
            "no": False,
        }

        with responses.RequestsMock() as resps:
            resps.add(responses.GET, k.API_ENDPOINT + "/api/consumer",
                    json={"consumer": customer})

            got_customer = self.k.get_customer_information()

            self.assertEqual(1, len(resps.calls))
            headers = resps.calls[0].request.headers
            self.assertIn("Authorization", headers)
            self.assertEqual("Bearer %s" % self.token,
                    headers["Authorization"])

        self.assertEqual(customer, got_customer)

    def test_get_customer_orders(self):
        with responses.RequestsMock() as resps:
            resps.add(responses.GET,
                    k.API_ENDPOINT + "/api/orders/fetch-for-consumer",
                    json={
                        "items": [
                            {"_id": "xx",
                             "items": [
                                 {"_id": "xy", "id": 42},
                                 {"_id": "xp", "id": 43},
                             ]
                            },
                            {"_id": "xz",
                             "items": [
                                 {"_id": "xm", "id": 42},
                                 {"_id": "xn", "id": 44},
                             ]
                            },
                        ],
                        "count": 2,
                    })

            resp = self.k.get_customer_orders()
            self.assertEqual({
                "orders": [
                    {"products": [{"id": 42}, {"id": 43}]},
                    {"products": [{"id": 42}, {"id": 44}]},
                ],
                "count": 2,
                "page": 1,
                "next_page": None,
            }, resp)

    def test_get_all_customer_orders(self):
        mock_orders = {
            1: [{"_id": "xx",
                "items": [
                    {"_id": "xy", "id": 42},
                    {"_id": "xp", "id": 43},
                    ]
                }],
            2: [{"_id": "xz",
                "items": [
                    {"_id": "xm", "id": 42},
                    {"_id": "xn", "id": 44},
                    ]
                }],
        }

        def get_orders(request):
            m = re.match(r".*\?page=(\d+)", request.url)
            self.assertIsNotNone(m)
            page = int(m.group(1))
            self.assertIn(page, mock_orders)
            orders = mock_orders[page]
            resp_body = {
                "items": orders,
                "count": 2,
            }
            return (200, {}, json.dumps(resp_body))

        with responses.RequestsMock() as resps:
            resps.add_callback(
                    responses.GET,
                    k.API_ENDPOINT + "/api/orders/fetch-for-consumer",
                    content_type="application/json",
                    callback=get_orders)

            all_orders = self.k.get_all_customer_orders()
            self.assertEqual(0, len(resps.calls))

            order1 = next(all_orders)
            self.assertEqual({"products": [{"id": 42}, {"id": 43}]}, order1)
            self.assertEqual(1, len(resps.calls))

            order2 = next(all_orders)
            self.assertEqual({"products": [{"id": 42}, {"id": 44}]}, order2)
            self.assertEqual(2, len(resps.calls))

            self.assertRaises(StopIteration, lambda: next(all_orders))
            self.assertEqual(2, len(resps.calls))
