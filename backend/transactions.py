from backend.fraud_engine import MODEL_DATA
from backend import case_store


def _status_label(risk_level):
    if risk_level == "HIGH":
        return "Suspicious"
    if risk_level == "MEDIUM":
        return "Needs Review"
    return "Normal"


def _row_to_dict(row, cases):

    risk_level = row["risk_level"]
    case = cases.get(row["transaction_id"], {"status": "unreviewed"})

    return {
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

        "risk_score":
            round(float(row["risk_score"]), 1),

        "risk_level":
            risk_level,

        "status_label":
            _status_label(risk_level),

        "case_status":
            case["status"],
    }


def get_recent_transactions(limit=20):

    df = MODEL_DATA.sort_values(
        "timestamp", ascending=False
    ).head(limit)

    cases = case_store.all_cases()

    return [_row_to_dict(row, cases) for _, row in df.iterrows()]


def search_transactions(query, limit=20):

    query = str(query).lower()

    mask = (
        MODEL_DATA["transaction_id"]
        .astype(str)
        .str.lower()
        .str.contains(query)

        |

        MODEL_DATA["customer_id"]
        .astype(str)
        .str.lower()
        .str.contains(query)
    )

    results = MODEL_DATA[mask].sort_values(
        "timestamp", ascending=False
    ).head(limit)

    cases = case_store.all_cases()

    return [_row_to_dict(row, cases) for _, row in results.iterrows()]
