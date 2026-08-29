"""
Customer-level context for investigators: "is this normal for THIS
person", not just "is this transaction risky in isolation".
"""

from backend.fraud_engine import MODEL_DATA


def _fmt_hour(hour):
    hour = int(round(hour)) % 24
    suffix = "AM" if hour < 12 else "PM"
    display = hour % 12
    if display == 0:
        display = 12
    return f"{display} {suffix}"


def get_customer_profile(customer_id):

    subset = MODEL_DATA[
        MODEL_DATA["customer_id"] == customer_id
    ]

    if subset.empty:
        return None

    normal = subset[subset["is_fraud"] == 0]
    typical = normal if not normal.empty else subset

    avg_amount = float(typical["amount"].mean())

    low_hour = typical["hour"].quantile(0.1)
    high_hour = typical["hour"].quantile(0.9)

    account_age_days = int(subset["account_age_days"].max())

    if account_age_days >= 365:
        account_age_display = f"{account_age_days // 365} yr {account_age_days % 365 // 30} mo"
    elif account_age_days >= 30:
        account_age_display = f"{account_age_days // 30} months"
    else:
        account_age_display = f"{account_age_days} days"

    return {
        "customer_id": customer_id,
        "account_age_days": account_age_days,
        "account_age_display": account_age_display,
        "total_transactions": int(len(subset)),
        "average_transaction": round(avg_amount, 2),
        "typical_activity": f"{_fmt_hour(low_hour)} - {_fmt_hour(high_hour)}",
        "known_devices": int(subset["device_id"].nunique()),
        "usual_locations": int(subset["ip_country"].nunique()),
        "previous_fraud_cases": int(subset["is_fraud"].sum()),
        "average_risk_score": round(float(subset["risk_score"].mean()), 1),
    }


def get_customer_timeline(customer_id, limit=15):

    subset = MODEL_DATA[
        MODEL_DATA["customer_id"] == customer_id
    ].sort_values("timestamp", ascending=False).head(limit)

    timeline = []

    for _, row in subset.iterrows():

        risk_level = row["risk_level"]

        if risk_level == "HIGH":
            status = "SUSPICIOUS"
        elif risk_level == "MEDIUM":
            status = "WATCH"
        else:
            status = "NORMAL"

        timeline.append({
            "transaction_id": row["transaction_id"],
            "timestamp": str(row["timestamp"]),
            "amount": float(row["amount"]),
            "merchant_category": row["merchant_category"],
            "risk_score": round(float(row["risk_score"]), 1),
            "status": status,
        })

    return timeline
