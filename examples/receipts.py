# -*- coding: UTF-8 -*-
# SPDX-License-Identifier: MIT

from configparser import ConfigParser
from datetime import datetime
from decimal import Decimal
from kbg import Config, Kbg
from numbers import Number
from zoneinfo import ZoneInfo


# Authenticate using the config file
k = Kbg.from_config()

##
# Generate receipts
##
receipts = dict()
fields = [
    'producer_name',
    'product_name',
    'quantity',
    'unit_display',
    'consumer_price',
    'tva',
]

# Prepare field formatting
field_func = {
        field: (lambda x: '{:,.2f}'.format(x / Decimal('100.00'))) if field.endswith('_price') # cents to euros
        else str
    for field in fields
}
field_lengths = [0 for field in fields]
field_justs = [' <' for field in fields]
field_units = ['' for field in fields]
for idx, field in enumerate(fields):
    if field.endswith('_price'):
        field_units[idx] = ' €'
    elif field == 'tva':
        field_units[idx] = '%'

# Get the data
for order in k.get_all_customer_orders(full=True):
    receipt_name = ' - '.join([
        datetime.fromisoformat(order['distribution_date']).astimezone(ZoneInfo("Europe/Paris")).strftime('%Y-%m-%d %Hh%M'),
        "Kelbongoo " + order['store'],
        order['id'],
        f"{order['status']}-{order['status_title']}",
    ])
    receipt = sorted([
        tuple(field_func[field](product[field]) for field in fields)
            for product in order['products']
    ])
    receipts[receipt_name] = receipt

    # Align numeric fields to the right
    for idx, field in enumerate(fields):
        field_lengths[idx] = max([field_lengths[idx]] + [len(str(line[idx])) for line in receipt])
        if len(order['products']) > 0:
            if isinstance(order['products'][0][field], Number):
                field_justs[idx] = ' >'

# Finalize field formatting
field_formats = ['{:' + field_justs[idx] + str(field_lengths[idx]) + '}' + field_units[idx] for idx, field in enumerate(fields)]

def layout(receipt, field_formats):
    lines = [
        '\t'.join([
            field_formats[idx].format(value)
                for idx, value in enumerate(line)
        ]) for line in receipt
    ]

    return '\n'.join(lines)

# Export receipts
for receipt_name in sorted(receipts.keys()):
    receipt = receipts[receipt_name]
    with open(receipt_name + '.txt', 'wt') as receipt_file:
        receipt_file.write(layout(receipt, field_formats))

