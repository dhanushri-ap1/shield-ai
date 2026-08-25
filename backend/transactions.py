import pandas as pd


DATA_PATH = "data/raw/transactions.csv"


def load_transactions():

    return pd.read_csv(
        DATA_PATH
    )


def get_recent_transactions(
    limit=20
):

    df = load_transactions()

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df = df.sort_values(
        "timestamp",
        ascending=False
    )

    transactions = []

    for _, row in df.head(limit).iterrows():

        transactions.append({

            "transaction_id":
                row["transaction_id"],

            "customer_id":
                row["customer_id"],

            "amount":
                float(row["amount"]),

            "payment_method":
                row["payment_method"],

            "merchant_category":
                row["merchant_category"],

            "country":
                row["ip_country"],

            "timestamp":
                str(row["timestamp"]),

            "fraud_type":
                row["fraud_type"],

            "is_fraud":
                int(row["is_fraud"])
        })

    return transactions


def search_transactions(
    query,
    limit=20
):

    df = load_transactions()

    query = str(query).lower()

    mask = (

        df["transaction_id"]
        .astype(str)
        .str.lower()
        .str.contains(query)

        |

        df["customer_id"]
        .astype(str)
        .str.lower()
        .str.contains(query)
    )

    results = df[mask].head(
        limit
    )

    transactions = []

    for _, row in results.iterrows():

        transactions.append({

            "transaction_id":
                row["transaction_id"],

            "customer_id":
                row["customer_id"],

            "amount":
                float(row["amount"]),

            "payment_method":
                row["payment_method"],

            "merchant_category":
                row["merchant_category"],

            "country":
                row["ip_country"],

            "timestamp":
                str(row["timestamp"]),

            "fraud_type":
                row["fraud_type"],

            "is_fraud":
                int(row["is_fraud"])
        })

    return transactions