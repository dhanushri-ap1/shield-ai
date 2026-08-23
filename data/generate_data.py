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

# Add fraud labels

FRAUD_RATE = 0.05

df["is_fraud"] = 0
df["fraud_type"] = "normal"

num_fraud = int(len(df) * FRAUD_RATE)

fraud_indices = random.sample(
    list(df.index),
    num_fraud
)

for index in fraud_indices:

    fraud_type = random.choice([
        "unusual_amount",
        "new_device",
        "location_anomaly",
        "odd_hour"
    ])

    df.loc[index, "is_fraud"] = 1
    df.loc[index, "fraud_type"] = fraud_type

    # 1. Unusually large transaction
    if fraud_type == "unusual_amount":
        df.loc[index, "amount"] *= random.uniform(5, 10)

    # 2. Transaction from a new device
    elif fraud_type == "new_device":
        df.loc[index, "device_id"] = (
            f"UNKNOWN_{random.randint(10000, 99999)}"
        )

    # 3. Transaction from another country
    elif fraud_type == "location_anomaly":
        df.loc[index, "ip_country"] = random.choice([
            "USA",
            "UK",
            "Singapore",
            "UAE"
        ])

    # 4. Transaction at an unusual time
    elif fraud_type == "odd_hour":
        timestamp = df.loc[index, "timestamp"]

        df.loc[index, "timestamp"] = timestamp.replace(
            hour=random.randint(0, 4)
        )

print("\nFraud count:", df["is_fraud"].sum())
print("\nFraud types:")
print(df["fraud_type"].value_counts())

df.to_csv("data/raw/transactions.csv", index=False)

print("\nDataset saved successfully!")