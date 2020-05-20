# -*- coding: UTF-8 -*-
# SPDX-License-Identifier: MIT

from configparser import ConfigParser
from more_itertools import unique_everseen
from kbg import Kbg

# Load the config file
config = ConfigParser()
config.read('parameters.ini')

# Authenticate
k = Kbg(config['Authentication']['email'], config['Authentication']['password'])

# Print your most-bought products
from collections import Counter

top_product_ids = Counter()
top_products = Counter()
top_producers = Counter()
top_weights = Counter()
top_purchases = Counter()
store_products = dict()
all_stores = tuple()
all_products = dict()

def get_store_products(store):
    global store_products
    if store not in store_products:
        try:
            store_products[store] = k.get_store_offer_dicts(store)["products"]
        except KeyError:
            # store has been closed in the meantime, e.g. "BOB" aka "Borrégo BIS"
            store_products[store] = dict()
    all_products.update(store_products[store])
    return store_products[store]

def get_product(product_id):
    global all_stores
    global store_products
    for store in store_products:
        if product_id in store_products[store]:
            return store_products[store][product_id]
    if len(store_products) != len(all_stores):
        if len(all_stores) == 0:
            all_stores = tuple(s["code"] for s in k.get_stores())
        for store in all_stores:
            get_store_products(store)
        return get_product(product_id)
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
    except KeyError as err:
#        print(err)
        continue
    top_products[product["product_name"]] += quantity
    top_producers[product["producer_name"]] += quantity
    top_weights[product["product_name"]] += quantity * product["unit_weight"]
    top_purchases[product["product_name"]] += quantity * product["consumer_price"]

print("Top products:")
for product, n in top_products.most_common(5):
    print(f"{n:3d}x - {product}")
print()

print("Top producers:")
for producer, n in top_producers.most_common(5):
    print(f"{n:3d}x - {producer}")
print()

print("Top weights:")
for product, n in top_weights.most_common(5):
    print(f"{n:5.1f} kg - {product}")
print()

print("Top purchases:")
for product, n in top_purchases.most_common(5):
    amount = n / 100
    print(f"{amount: >7.2f}€ - {product}")
print()
