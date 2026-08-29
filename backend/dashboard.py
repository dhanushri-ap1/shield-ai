"""
Investigator dashboard: a single place to see every transaction that
has already been reviewed and where it landed — Safe, Needs Review,
or Confirmed Fraud — instead of losing track of decisions once a
transaction scrolls out of the priority queue.
"""

from backend.fraud_engine import MODEL_DATA
from backend import case_store


STATUS_LABELS = {
    "safe": "Marked Safe",
    "needs_review": "Needs Review",
    "confirmed_fraud": "Confirmed Fraud",
}


def _row_for(transaction_id):
    matches = MODEL_DATA[
        MODEL_DATA["transaction_id"] == transaction_id
    ]

    if matches.empty:
        return None

    return matches.iloc[0]


def get_dashboard(status_filter=None):
    """
    Every reviewed case (status != unreviewed), merged with its
    transaction summary, newest decision first.
    """

    cases = case_store.all_cases()

    items = []

    for transaction_id, case in cases.items():

        status = case.get("status", "unreviewed")

        if status == "unreviewed":
            continue

        if status_filter and status_filter != "all" and status != status_filter:
            continue

        row = _row_for(transaction_id)

        if row is None:
            continue

        items.append({
            "transaction_id": transaction_id,
            "customer_id": row["customer_id"],
            "amount": float(row["amount"]),
            "merchant_category": row["merchant_category"],
            "risk_score": round(float(row["risk_score"]), 1),
            "risk_level": row["risk_level"],
            "status": status,
            "status_label": STATUS_LABELS.get(status, status),
            "note_count": len(case.get("notes", [])),
            "last_note": case["notes"][-1]["text"] if case.get("notes") else "",
            "updated_at": case.get("updated_at"),
        })

    items.sort(
        key=lambda item: item["updated_at"] or "",
        reverse=True,
    )

    return items


def get_dashboard_summary():
    """
    Counts per status, for the dashboard's stat cards.
    """

    cases = case_store.all_cases()

    counts = {
        "safe": 0,
        "needs_review": 0,
        "confirmed_fraud": 0,
    }

    for case in cases.values():
        status = case.get("status", "unreviewed")
        if status in counts:
            counts[status] += 1

    counts["total_handled"] = sum(counts.values())

    return counts