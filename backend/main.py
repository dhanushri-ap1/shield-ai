from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.fraud_engine import investigate_with_model
from backend.operations import (
    analytics_risk,
    dashboard_summary,
    get_transaction,
    list_transactions
)


app = FastAPI(
    title="SHIELD-AI",
    description=(
        "Fraud & Risk Intelligence Platform"
    ),
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
def home():

    return {
        "application": "SHIELD-AI",
        "status": "online",
        "message": "Fraud & Risk Intelligence Platform"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.get("/api/dashboard/summary")
def dashboard():

    return {
        "success": True,
        **dashboard_summary()
    }


@app.get("/api/analytics/risk")
def analytics():

    return {
        "success": True,
        **analytics_risk()
    }


@app.get("/api/transactions")
def transactions(
    query: str = "",
    risk: str = "ALL",
    limit: int = 25,
    offset: int = 0
):

    if limit < 1:
        limit = 1

    if limit > 100:
        limit = 100

    if offset < 0:
        offset = 0

    result = list_transactions(
        query=query,
        risk=risk,
        limit=limit,
        offset=offset
    )

    return {
        "success": True,
        **result
    }


@app.get("/api/transactions/search")
def search(
    query: str,
    limit: int = 20
):

    if not query.strip():

        raise HTTPException(
            status_code=400,
            detail="Search query is required"
        )

    result = list_transactions(
        query=query,
        risk="ALL",
        limit=limit,
        offset=0
    )

    return {
        "success": True,
        "count": result["count"],
        "transactions": result["transactions"]
    }


@app.get("/api/transactions/{transaction_id}")
def transaction_detail(transaction_id: str):

    result = get_transaction(transaction_id)

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    return {
        "success": True,
        "transaction": result
    }


@app.get("/api/investigate/{transaction_id}")
def investigate(transaction_id: str):

    result = investigate_with_model(transaction_id)

    if result is None:

        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    transaction = result["transaction"]

    return {

        "success": True,

        "transaction_id": transaction_id,

        "risk_score": result["risk_score"],

        "risk_level": result["risk_level"],

        "recommended_action": result["recommended_action"],

        "transaction": {

            "amount": float(transaction["amount"]),

            "customer_id": transaction["customer_id"],

            "payment_method": transaction["payment_method"],

            "merchant_category": transaction["merchant_category"],

            "country": transaction["ip_country"],

            "timestamp": str(transaction["timestamp"]),

            "device_id": str(transaction.get("device_id", ""))
        },

        "explanations": result["explanations"],

        "behavior_comparison": result["behavior_comparison"]
    }
