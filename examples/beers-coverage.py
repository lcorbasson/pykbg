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

# Find your beers coverage
my_store = config['Stores']['favorite']

offer = k.get_store_offer(my_store)

# Get the id of the family 'Bières' ("Beers")
beer_family_id = None
for family in offer["families"]:
    if family["name"] == "Bières":
        beer_family_id = family["id"]
        break
else:
    raise Exception("Can't find the beer family! :(")

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

