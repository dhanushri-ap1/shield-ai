import pandas as pd


DATA_PATH = "data/raw/transactions.csv"


def load_transactions():

    df = pd.read_csv(DATA_PATH)

    return df


def investigate_transaction(transaction_id):

    df = load_transactions()

    transaction = df[
        df["transaction_id"] == transaction_id
    ]

    if transaction.empty:

        return {
            "success": False,
            "message": "Transaction not found"
        }

    row = transaction.iloc[0]

    return {
        "success": True,

        "transaction_id": row["transaction_id"],

        "amount": float(row["amount"]),

        "customer_id": row["customer_id"],

        "payment_method": row["payment_method"],

        "merchant_category": row["merchant_category"],

        "country": row["ip_country"],

        "fraud_type": row["fraud_type"]
    }