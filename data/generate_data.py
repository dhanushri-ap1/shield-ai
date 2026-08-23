import pandas as pd
import numpy as np
import random
from faker import Faker
from datetime import datetime, timedelta


fake = Faker("en_IN")

# --------------------------------------------------
# SETTINGS
# --------------------------------------------------

NUM_CUSTOMERS = 5000
TRANSACTIONS_PER_CUSTOMER = 10
FRAUD_RATE = 0.05

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

COUNTRIES = [
    "India",
    "USA",
    "UK",
    "Singapore",
    "UAE"
]


# --------------------------------------------------
# CREATE CUSTOMERS
# --------------------------------------------------

customers = []

for i in range(NUM_CUSTOMERS):

    customer_id = f"CUST_{i + 1:05d}"

    usual_device = f"DEV_{i + 1:05d}"

    customer = {
        "customer_id": customer_id,
        "age": random.randint(18, 70),
        "account_age_days": random.randint(30, 1500),
        "home_country": "India",
        "usual_device": usual_device,
        "avg_amount": round(
            np.random.lognormal(mean=7, sigma=0.7),
            2
        ),
        "usual_category": random.choice(MERCHANT_CATEGORIES),
        "usual_payment_method": random.choice(PAYMENT_METHODS),
        "usual_hour": random.randint(9, 20)
    }

    customers.append(customer)


# --------------------------------------------------
# GENERATE NORMAL TRANSACTIONS
# --------------------------------------------------

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
                customer["avg_amount"] * 0.30
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
            "ip_country": customer["home_country"],
            "transaction_status": "success",
            "account_age_days": customer["account_age_days"],
            "usual_hour": customer["usual_hour"]
        }

        transactions.append(transaction)


df = pd.DataFrame(transactions)


# --------------------------------------------------
# INITIAL LABELS
# --------------------------------------------------

df["is_fraud"] = 0
df["fraud_type"] = "normal"


# --------------------------------------------------
# FRAUD TYPES
# --------------------------------------------------

fraud_types = [
    "unusual_amount",
    "new_device",
    "location_anomaly",
    "odd_hour",
    "velocity_attack",
    "spending_burst",
    "card_testing",
    "merchant_anomaly",
    "payment_method_change",
    "account_takeover"
]


num_fraud = int(len(df) * FRAUD_RATE)

fraud_indices = random.sample(
    list(df.index),
    num_fraud
)


# --------------------------------------------------
# INJECT FRAUD
# --------------------------------------------------

for index in fraud_indices:

    fraud_type = random.choice(fraud_types)

    df.loc[index, "is_fraud"] = 1
    df.loc[index, "fraud_type"] = fraud_type


    # ----------------------------------------------
    # 1. UNUSUAL AMOUNT
    # ----------------------------------------------

    if fraud_type == "unusual_amount":

        df.loc[index, "amount"] *= random.uniform(5, 12)


    # ----------------------------------------------
    # 2. NEW DEVICE
    # ----------------------------------------------

    elif fraud_type == "new_device":

        df.loc[index, "device_id"] = (
            f"UNKNOWN_{random.randint(10000, 99999)}"
        )


    # ----------------------------------------------
    # 3. LOCATION ANOMALY
    # ----------------------------------------------

    elif fraud_type == "location_anomaly":

        df.loc[index, "ip_country"] = random.choice([
            "USA",
            "UK",
            "Singapore",
            "UAE"
        ])


    # ----------------------------------------------
    # 4. ODD HOUR
    # ----------------------------------------------

    elif fraud_type == "odd_hour":

        timestamp = df.loc[index, "timestamp"]

        df.loc[index, "timestamp"] = timestamp.replace(
            hour=random.randint(0, 4)
        )


    # ----------------------------------------------
    # 5. VELOCITY ATTACK
    # ----------------------------------------------

    elif fraud_type == "velocity_attack":

        customer_id = df.loc[index, "customer_id"]

        customer_transactions = df[
            df["customer_id"] == customer_id
        ].index.tolist()

        fraud_time = df.loc[index, "timestamp"]

        for transaction_index in customer_transactions[:5]:

            df.loc[
                transaction_index,
                "timestamp"
            ] = fraud_time + timedelta(
                seconds=random.randint(10, 500)
            )


    # ----------------------------------------------
    # 6. SPENDING BURST
    # ----------------------------------------------

    elif fraud_type == "spending_burst":

        df.loc[index, "amount"] *= random.uniform(3, 8)

        customer_id = df.loc[index, "customer_id"]

        customer_transactions = df[
            df["customer_id"] == customer_id
        ].index.tolist()

        fraud_time = df.loc[index, "timestamp"]

        for transaction_index in customer_transactions[:4]:

            df.loc[
                transaction_index,
                "timestamp"
            ] = fraud_time + timedelta(
                minutes=random.randint(1, 40)
            )

            df.loc[
                transaction_index,
                "amount"
            ] *= random.uniform(1.5, 4)


    # ----------------------------------------------
    # 7. CARD TESTING
    # ----------------------------------------------

    elif fraud_type == "card_testing":

        df.loc[index, "payment_method"] = "card"

        df.loc[index, "amount"] = random.uniform(
            10,
            500
        )

        customer_id = df.loc[index, "customer_id"]

        customer_transactions = df[
            df["customer_id"] == customer_id
        ].index.tolist()

        fraud_time = df.loc[index, "timestamp"]

        for transaction_index in customer_transactions[:4]:

            df.loc[
                transaction_index,
                "timestamp"
            ] = fraud_time + timedelta(
                seconds=random.randint(10, 120)
            )

            df.loc[
                transaction_index,
                "transaction_status"
            ] = "failed"


    # ----------------------------------------------
    # 8. MERCHANT ANOMALY
    # ----------------------------------------------

    elif fraud_type == "merchant_anomaly":

        usual_category = df.loc[
            index,
            "merchant_category"
        ]

        new_category = random.choice([
            category
            for category in MERCHANT_CATEGORIES
            if category != usual_category
        ])

        df.loc[
            index,
            "merchant_category"
        ] = new_category

        df.loc[index, "amount"] *= random.uniform(
            2,
            6
        )


    # ----------------------------------------------
    # 9. PAYMENT METHOD CHANGE
    # ----------------------------------------------

    elif fraud_type == "payment_method_change":

        usual_method = df.loc[
            index,
            "payment_method"
        ]

        new_method = random.choice([
            method
            for method in PAYMENT_METHODS
            if method != usual_method
        ])

        df.loc[
            index,
            "payment_method"
        ] = new_method


    # ----------------------------------------------
    # 10. ACCOUNT TAKEOVER
    # ----------------------------------------------

    elif fraud_type == "account_takeover":

        df.loc[index, "amount"] *= random.uniform(
            4,
            10
        )

        df.loc[index, "device_id"] = (
            f"UNKNOWN_{random.randint(10000, 99999)}"
        )

        df.loc[index, "ip_country"] = random.choice([
            "USA",
            "UK",
            "Singapore",
            "UAE"
        ])

        df.loc[
            index,
            "merchant_category"
        ] = random.choice(
            MERCHANT_CATEGORIES
        )

        timestamp = df.loc[index, "timestamp"]

        df.loc[index, "timestamp"] = timestamp.replace(
            hour=random.randint(0, 4)
        )


# --------------------------------------------------
# SORT BY TIME
# --------------------------------------------------

df = df.sort_values("timestamp").reset_index(drop=True)


# --------------------------------------------------
# SAVE DATASET
# --------------------------------------------------

output_path = "data/raw/transactions.csv"

df.to_csv(
    output_path,
    index=False
)


# --------------------------------------------------
# OUTPUT
# --------------------------------------------------

print("Dataset generated!")

print(
    "Number of transactions:",
    len(df)
)

print(
    "\nFraud count:",
    df["is_fraud"].sum()
)

print(
    "\nFraud types:"
)

print(
    df["fraud_type"].value_counts()
)

print(
    f"\nDataset saved to: {output_path}"
)