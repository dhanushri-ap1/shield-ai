from fastapi import FastAPI

from backend.investigation import (
    investigate_transaction
)


app = FastAPI(
    title="Shield-AI",
    description="Explainable AI Fraud Investigation API",
    version="1.0.0"
)


@app.get("/")
def home():

    return {
        "application": "Shield-AI",
        "status": "online",
        "message": "Explainable AI Fraud Investigation API"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.get("/api/investigate/{transaction_id}")
def investigate(transaction_id: str):

    return investigate_transaction(
        transaction_id
    )