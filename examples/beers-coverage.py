# -*- coding: UTF-8 -*-
# SPDX-License-Identifier: MIT

from more_itertools import unique_everseen
from kbg import Config, Kbg

# Load the config file
config = Config()

# Authenticate
k = Kbg.from_config(config)

# Find your beers coverage
my_store = config.get_favorite_store()

offer = k.get_store_offer(my_store)

# Get the id of the family 'Bières' ("Beers")
beer_family_id = None

def find_family(offer, family_name):
    for family in offer["families"]:
        if family["name"] == family_name:
            return family["id"]
    raise Exception(f"Can't find the {family_name} family! :(")

try:
    beer_family_id = find_family(offer, "Bières")
except Exception as e:
    print(f"{e} -- giving it another try")
    beer_family_id = find_family(offer, "Boissons") # "Beverages"

# Collect all products in that family
beers = {}
for product in offer["products"]:
    if product["family_id"] == beer_family_id:
        beers[product["id"]] = "%-40s (%s)" % (
                product["product_name"], product["producer_name"])

known_beers = set()

# Collect all *bought* products in that family
for order in k.get_all_customer_orders():
    for product in order["products"]:
        product_id = product["id"]
        if product_id in beers:
            known_beers.add(product_id)

print("You have tasted %d beers out of %d." % (len(known_beers), len(beers)))
if len(known_beers) != len(beers):
    print("Other beers you might want to try:")
    for beer_id, beer in beers.items():
        if beer_id not in known_beers:
            print("*", beer)

