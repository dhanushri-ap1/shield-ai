from backend.fraud_engine import MODEL_DATA


def _serialize_transaction(row):

    return {

        "transaction_id":
            str(row["transaction_id"]),

        "customer_id":
            str(row["customer_id"]),

        "amount":
            float(row["amount"]),

        "payment_method":
            str(row["payment_method"]),

        "merchant_category":
            str(row["merchant_category"]),

        "country":
            str(row["ip_country"]),

        "timestamp":
            str(row["timestamp"]),

        "fraud_type":
            str(row["fraud_type"]),

        "is_fraud":
            int(row["is_fraud"]),

        "risk_score":
            float(row["risk_score"]),

        "risk_level":
            str(row["risk_level"]),

        "status":
            str(row["review_status"]),

        "reason":
            str(row["primary_reason"]),

        "recommended_action":
            str(row["recommended_action"])
    }


def dashboard_summary():

    df = MODEL_DATA

    total = int(len(df))

    high = int(
        (df["risk_level"] == "HIGH").sum()
    )

    medium = int(
        (df["risk_level"] == "MEDIUM").sum()
    )

    low = int(
        (df["risk_level"] == "LOW").sum()
    )

    flagged = high + medium

    under_review = int(
        (df["recommended_action"] == "MANUAL_REVIEW").sum()
    )

    flagged_rows = df[df["risk_score"] >= 40]

    if len(flagged_rows) == 0:
        false_positive_rate = 0.0
    else:
        false_positive_rate = round(
            float(
                (flagged_rows["is_fraud"] == 0).mean()
                * 100
            ),
            1
        )

    queue = (
        df.sort_values(
            ["risk_score", "timestamp"],
            ascending=[False, False]
        )
        .head(8)
    )

    return {

        "total_transactions": total,

        "flagged_transactions": flagged,

        "high_risk": high,

        "medium_risk": medium,

        "low_risk": low,

        "under_review": under_review,

        "false_positive_rate": false_positive_rate,

        "risk_distribution": {

            "LOW": round(low / total * 100, 1) if total else 0,

            "MEDIUM": round(medium / total * 100, 1) if total else 0,

            "HIGH": round(high / total * 100, 1) if total else 0
        },

        "recent_suspicious": [
            _serialize_transaction(row)
            for _, row in queue.iterrows()
        ]
    }


def list_transactions(
    query="",
    risk="ALL",
    limit=25,
    offset=0
):

    df = MODEL_DATA

    risk = str(risk or "ALL").upper()

    if risk in {"HIGH", "MEDIUM", "LOW"}:
        df = df[df["risk_level"] == risk]

    query = str(query or "").strip().lower()

    if query:

        mask = (

            df["transaction_id"]
            .astype(str)
            .str.lower()
            .str.contains(query, regex=False)

            |

            df["customer_id"]
            .astype(str)
            .str.lower()
            .str.contains(query, regex=False)
        )

        df = df[mask]

    df = df.sort_values(
        "timestamp",
        ascending=False
    )

    total = int(len(df))

    page = df.iloc[offset:offset + limit]

    return {

        "total": total,

        "count": int(len(page)),

        "offset": offset,

        "limit": limit,

        "transactions": [
            _serialize_transaction(row)
            for _, row in page.iterrows()
        ]
    }


def get_transaction(transaction_id):

    matches = MODEL_DATA[
        MODEL_DATA["transaction_id"] == transaction_id
    ]

    if matches.empty:
        return None

    return _serialize_transaction(
        matches.iloc[0]
    )


def analytics_risk():

    df = MODEL_DATA

    total = int(len(df))

    counts = (
        df["risk_level"]
        .value_counts()
        .to_dict()
    )

    reasons = (
        df[df["risk_level"] != "LOW"]
        ["primary_reason"]
        .value_counts()
        .head(6)
    )

    categories = (
        df.groupby("merchant_category")["risk_score"]
        .mean()
        .sort_values(ascending=False)
        .head(6)
    )

    return {

        "total_transactions": total,

        "counts": {
            "LOW": int(counts.get("LOW", 0)),
            "MEDIUM": int(counts.get("MEDIUM", 0)),
            "HIGH": int(counts.get("HIGH", 0))
        },

        "flagged_reasons": [
            {
                "reason": str(reason),
                "count": int(count)
            }
            for reason, count in reasons.items()
        ],

        "categories": [
            {
                "category": str(category),
                "avg_risk": round(float(score), 1)
            }
            for category, score in categories.items()
        ]
    }
