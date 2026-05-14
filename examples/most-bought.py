# -*- coding: UTF-8 -*-
# SPDX-License-Identifier: MIT

from typing import Counter as CounterType, Any, List

from kbg import Kbg

# Authenticate using the config file
k = Kbg.from_config()

# Print your most-bought products
from collections import Counter

top_items_to_show = 5
top_product_ids: CounterType[Any] = Counter()
top_products: CounterType[str] = Counter()
top_producers: CounterType[str] = Counter()
top_weights: CounterType[str] = Counter()
top_purchases: CounterType[str] = Counter()
store_products = {}
all_stores: List[str] = []
all_products = {}


def get_store_products(store):
    if store not in store_products:
        try:
            store_products[store] = k.get_store_offer_dicts(store)["products"]
        except KeyError:
            # store has been closed in the meantime, e.g. "BOB" aka "Borrégo BIS"
            store_products[store] = {}
    all_products.update(store_products[store])
    return store_products[store]


def get_product(product_id, refresh_cache=True):
    for store in store_products:
        if product_id in store_products[store]:
            return store_products[store][product_id]
    if len(store_products) != len(all_stores):
        if len(all_stores) == 0:
            all_stores.extend(s["code"] for s in k.get_stores())
        if refresh_cache:
            for store in all_stores:
                get_store_products(store)
            return get_product(product_id, refresh_cache=False)
    raise KeyError(f"Product ID {product_id} not found in stores {all_stores}")


for order in k.get_all_customer_orders():
    store = order["store"]
    get_store_products(store)
    for product in order["products"]:
        product_id = product["id"]
        top_product_ids[product_id] += 1

for product_id, quantity in top_product_ids.items():
    try:
        product = get_product(product_id)
    except KeyError:
        continue
    top_products[product["product_name"]] += quantity
    top_producers[product["producer_name"]] += quantity
    top_weights[product["product_name"]] += quantity * product["unit_weight"]
    top_purchases[product["product_name"]] += quantity * product["consumer_price"]

print("Top products:")
for product, n in top_products.most_common(top_items_to_show):
    print(f"{n:3d}x - {product}")
print()

print("Top producers:")
for producer, n in top_producers.most_common(top_items_to_show):
    print(f"{n:3d}x - {producer}")
print()

print("Top weights:")
for product, n in top_weights.most_common(top_items_to_show):
    print(f"{n:5.1f} kg - {product}")
print()

print("Top purchases:")
for product, n in top_purchases.most_common(top_items_to_show):
    amount = n / 100
    print(f"{amount: >7.2f}€ - {product}")
print()
