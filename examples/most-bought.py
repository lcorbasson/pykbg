# -*- coding: UTF-8 -*-
# SPDX-License-Identifier: MIT

import configparser
from kbg import Kbg

# Load the config file
config = configparser.ConfigParser()
config.read('parameters.ini')

# Authenticate
k = Kbg(config['Authentication']['email'], config['Authentication']['password'])

# Print your most-bought products
from collections import Counter

top_products = Counter()
top_producers = Counter()
store_products = dict()

for order in k.get_all_customer_orders():
    store = order["store"]
    if store not in store_products:
        try:
            store_products[store] = k.get_store_offer_dicts(store)["products"]
        except KeyError:
            # store has been closed in the meantime, e.g. "BOB" aka "Borrégo BIS"
            store_products[store] = dict()
    for product in order["products"]:
        product_id = product["id"]
        if product_id in store_products[store]:
            product = store_products[store][product_id]
            top_products[product["product_name"]] += 1
            top_producers[product["producer_name"]] += 1

print("Top products:")
for product, n in top_products.most_common(5):
    print("%3d - %s" % (n, product))

print("\nTop producers:")
for producer, n in top_producers.most_common(5):
    print("%3d - %s" % (n, producer))
