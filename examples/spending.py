# -*- coding: UTF-8 -*-
# SPDX-License-Identifier: MIT

import configparser
from kbg import Kbg

# Load the config file
config = configparser.ConfigParser()
config.read('parameters.ini')

# Authenticate
k = Kbg(config['Authentication']['email'], config['Authentication']['password'])

# Compute your total spending
total_spent = 0

for order in k.get_all_customer_orders():
    for product in order["products"]:
        total_spent += product["consumer_price"]

# get a price in euros rather than cents
total_spent /= 100

print("You spent a total of %.2f€ at Kelbongoo!" % total_spent)

