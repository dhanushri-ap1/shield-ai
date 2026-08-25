from fastapi import FastAPI, HTTPException

from backend.fraud_engine import (
    investigate_with_model
)


app = FastAPI(
    title="Shield-AI",
    description=(
        "Explainable AI Fraud "
        "Investigation API"
    ),
    version="1.0.0"
)


@app.get("/")
def home():

    return {
        "application": "Shield-AI",
        "status": "online",
        "message": (
            "Explainable AI Fraud "
            "Investigation API"
        )
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


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

    return {

        "success": True,

        "transaction_id":
            transaction_id,

        "risk_score":
            result["risk_score"],

        "risk_level":
            result["risk_level"],

        "recommended_action":
            result["recommended_action"],

        "transaction": {

            "amount":
                float(transaction["amount"]),

            "customer_id":
                transaction["customer_id"],

            "payment_method":
                transaction["payment_method"],

            "merchant_category":
                transaction[
                    "merchant_category"
                ],

            "country":
                transaction[
                    "ip_country"
                ],

            "timestamp":
                str(transaction[
                    "timestamp"
                ])
        },

        "explanations":
            result["explanations"],

        "behavior_comparison":
            result[
                "behavior_comparison"
            ]
    }