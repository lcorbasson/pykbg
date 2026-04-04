# -*- coding: UTF-8 -*-
# SPDX-License-Identifier: MIT

from kbg import Kbg

# Authenticate using the config file
k = Kbg.from_config()

# Compute your total spending
total_spent: float = 0

for order in k.get_all_customer_orders():
    for product in order["products"]:
        total_spent += product["consumer_price"]

# get a price in euros rather than cents
total_spent /= 100

print(f"You spent a total of {total_spent:.2f}€ at Kelbongoo!")
