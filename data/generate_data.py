import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta


fake = Faker("en_IN")


NUM_CUSTOMERS = 5000
TRANSACTIONS_PER_CUSTOMER = 10


MERCHANT_CATEGORIES = [
    "grocery",
    "food",
    "electronics",
    "travel",
    "fashion",
    "utilities",
    "entertainment",
    "healthcare"
]


PAYMENT_METHODS = [
    "upi",
    "card",
    "netbanking",
    "wallet"
]


customers = []

for i in range(NUM_CUSTOMERS):
    customer = {
        "customer_id": f"CUST_{i+1:05d}",
        "age": random.randint(18, 70),
        "home_country": "India",
        "usual_device": f"DEV_{random.randint(1, 15000):05d}",
        "avg_amount": round(np.random.lognormal(mean=7, sigma=0.7), 2),
        "usual_category": random.choice(MERCHANT_CATEGORIES),
        "usual_payment_method": random.choice(PAYMENT_METHODS)
    }

    customers.append(customer)


transactions = []

for customer in customers:
    for _ in range(TRANSACTIONS_PER_CUSTOMER):

        timestamp = datetime.now() - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59)
        )

        amount = round(
            np.random.normal(
                customer["avg_amount"],
                customer["avg_amount"] * 0.3
            ),
            2
        )

        amount = max(amount, 50)

        transaction = {
            "transaction_id": fake.uuid4(),
            "customer_id": customer["customer_id"],
            "timestamp": timestamp,
            "amount": amount,
            "merchant_category": customer["usual_category"],
            "payment_method": customer["usual_payment_method"],
            "device_id": customer["usual_device"],
            "ip_country": customer["home_country"]
        }

        transactions.append(transaction)


df = pd.DataFrame(transactions)

print("Dataset generated!")
print("Number of transactions:", len(df))

print("\nFirst 5 transactions:")
print(df.head())