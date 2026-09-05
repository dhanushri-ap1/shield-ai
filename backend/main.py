import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.fraud_engine import (
    investigate_with_model,
    get_priority_queue,
)

from backend.transactions import (
    get_recent_transactions,
    search_transactions
)

from backend.customer_profile import (
    get_customer_profile,
    get_customer_timeline,
)

from backend.dashboard import (
    get_dashboard,
    get_dashboard_summary,
)

from backend import case_store


class StatusUpdate(BaseModel):
    status: str


class NoteCreate(BaseModel):
    note: str


app = FastAPI(
    title="Shield-AI",
    description=(
        "Explainable AI Fraud "
        "Investigation API"
    ),
    version="1.0.0"
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {

        "application":
            "Shield-AI",

        "status":
            "online",

        "message":
            "Explainable AI Fraud "
            "Investigation API"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ============================================================
# RECENT TRANSACTIONS
# ============================================================

@app.get(
    "/api/transactions"
)
def recent_transactions(
    limit: int = 20
):

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    return {

        "success":
            True,

        "count":
            limit,

        "transactions":
            get_recent_transactions(
                limit
            )
    }


# ============================================================
# SEARCH TRANSACTIONS
# ============================================================

@app.get(
    "/api/transactions/search"
)
def search(
    query: str,
    limit: int = 20
):

    if not query.strip():

        raise HTTPException(
            status_code=400,
            detail="Search query is required"
        )

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    results = search_transactions(
        query,
        limit
    )

    return {

        "success":
            True,

        "count":
            len(results),

        "transactions":
            results
    }


# ============================================================
# AI INVESTIGATION
# ============================================================

@app.get(
    "/api/investigate/{transaction_id}"
)
def investigate(
    transaction_id: str
):

    result = (
        investigate_with_model(
            transaction_id
        )
    )

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    transaction = (
        result["transaction"]
    )

    case = case_store.get_case(
        transaction_id
    )

    return {

        "success":
            True,

        "transaction_id":
            transaction_id,

        "risk_score":
            result["risk_score"],

        "risk_level":
            result["risk_level"],

        "recommended_action":
            result[
                "recommended_action"
            ],

        "flag_summary":
            result.get(
                "flag_summary",
                ""
            ),

        "transaction": {

            "amount":
                float(
                    transaction["amount"]
                ),

            "customer_id":
                transaction[
                    "customer_id"
                ],

            "payment_method":
                transaction[
                    "payment_method"
                ],

            "merchant_category":
                transaction[
                    "merchant_category"
                ],

            "country":
                transaction[
                    "ip_country"
                ],

            "timestamp":
                str(
                    transaction[
                        "timestamp"
                    ]
                )
        },

        "explanations":
            result[
                "explanations"
            ],

        "behavior_comparison":
            result[
                "behavior_comparison"
            ],

        "score_breakdown":
            result.get(
                "score_breakdown",
                []
            ),

        "model_drivers":
            result.get(
                "model_drivers",
                []
            ),

        "case":
            case,
    }


# ============================================================
# INVESTIGATOR ACTIONS — status + notes
# ============================================================

@app.get(
    "/api/cases/{transaction_id}"
)
def get_case(transaction_id: str):

    return {
        "success": True,
        "case": case_store.get_case(transaction_id),
    }


@app.post(
    "/api/cases/{transaction_id}/status"
)
def update_case_status(
    transaction_id: str,
    payload: StatusUpdate,
):

    try:
        case = case_store.set_status(
            transaction_id,
            payload.status,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "success": True,
        "case": case,
    }


@app.post(
    "/api/cases/{transaction_id}/notes"
)
def add_case_note(
    transaction_id: str,
    payload: NoteCreate,
):

    try:
        case = case_store.add_note(
            transaction_id,
            payload.note,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    return {
        "success": True,
        "case": case,
    }


# ============================================================
# PRIORITY QUEUE
# ============================================================

@app.get(
    "/api/queue"
)
def priority_queue(limit: int = 30):

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    items = get_priority_queue(limit)

    cases = case_store.all_cases()

    for item in items:
        case = cases.get(
            item["transaction_id"],
            {"status": "unreviewed"},
        )
        item["case_status"] = case["status"]

    return {
        "success": True,
        "count": len(items),
        "queue": items,
    }


# ============================================================
# CUSTOMER RISK PROFILE + TIMELINE
# ============================================================

@app.get(
    "/api/customers/{customer_id}/profile"
)
def customer_profile(customer_id: str):

    profile = get_customer_profile(customer_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail="Customer not found",
        )

    return {
        "success": True,
        "profile": profile,
    }


@app.get(
    "/api/customers/{customer_id}/timeline"
)
def customer_timeline(
    customer_id: str,
    limit: int = 15,
):

    if limit < 1:
        limit = 1

    if limit > 50:
        limit = 50

    timeline = get_customer_timeline(
        customer_id,
        limit,
    )

    return {
        "success": True,
        "count": len(timeline),
        "timeline": timeline,
    }


# ============================================================
# DASHBOARD — handled / reviewed transactions
# ============================================================

@app.get(
    "/api/dashboard"
)
def dashboard(status: str = "all"):

    items = get_dashboard(status)
    summary = get_dashboard_summary()

    return {
        "success": True,
        "count": len(items),
        "summary": summary,
        "cases": items,
    }