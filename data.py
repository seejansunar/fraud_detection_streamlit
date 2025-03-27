
import random
import pandas as pd

from datetime import datetime, timedelta

from faker import Faker

faker = Faker()


def generate_transaction_row(
    timestamp: datetime,
    amount_min: float,
    amount_max: float,
    purposes: list,
    countries: list
):
    row = {
      "timestamp": timestamp,
      "amount": float("{0:.2f}".format(random.uniform(amount_min, amount_max))),
      "purpose": (
        random.choice(purposes)
        if purposes
        else random.choice(('Entertainment', 'Holiday', 'Transportation', 'Bills', 'Medical', 'Misc'))
      ),
      "country": random.choice(countries) if countries else faker.country_code('alpha-3')
    }
    return row


def generate_timeseries_data(num_rows: int, start_timestamp: datetime, **kwargs):
    data = []
    now = datetime.now()
    timestamp = start_timestamp or datetime.now()
    for _ in range(num_rows):
        timestamp += timedelta(seconds=random.randint(1, 3600))
        params = dict(timestamp=timestamp, **kwargs)
        data.append(generate_transaction_row(**params))
    return pd.DataFrame(data)
