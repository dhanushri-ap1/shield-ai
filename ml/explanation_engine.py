import pandas as pd


# ==================================================
# HUMAN-READABLE EXPLANATION ENGINE
# ==================================================

def generate_explanations(transaction):
    """
    Convert transaction features into
    human-readable fraud explanations.
    """

    explanations = []


    # ----------------------------------------------
    # AMOUNT ANOMALY
    # ----------------------------------------------

    amount_ratio = transaction["amount_ratio"]

    if amount_ratio >= 3:

        explanations.append({
            "feature": "amount_ratio",
            "severity": "HIGH",
            "title": "Unusual transaction amount",
            "message": (
                f"The transaction amount is "
                f"{amount_ratio:.1f}× the customer's "
                f"normal transaction amount."
            )
        })

    elif amount_ratio >= 1.8:

        explanations.append({
            "feature": "amount_ratio",
            "severity": "MEDIUM",
            "title": "Above-normal transaction amount",
            "message": (
                f"The transaction amount is "
                f"{amount_ratio:.1f}× the customer's "
                f"normal transaction amount."
            )
        })


    # ----------------------------------------------
    # NEW DEVICE
    # ----------------------------------------------

    if transaction["is_new_device"] == 1:

        explanations.append({
            "feature": "is_new_device",
            "severity": "HIGH",
            "title": "New device detected",
            "message": (
                "This transaction was made from a "
                "device not previously associated "
                "with this customer."
            )
        })


    # ----------------------------------------------
    # NEW LOCATION
    # ----------------------------------------------

    if transaction["is_new_location"] == 1:

        explanations.append({
            "feature": "is_new_location",
            "severity": "HIGH",
            "title": "Unusual location",
            "message": (
                "The transaction originated from a "
                "location not normally associated "
                "with this customer."
            )
        })


    # ----------------------------------------------
    # ODD HOUR
    # ----------------------------------------------

    if transaction["is_odd_hour"] == 1:

        explanations.append({
            "feature": "is_odd_hour",
            "severity": "MEDIUM",
            "title": "Unusual transaction time",
            "message": (
                "The transaction occurred during "
                "an unusual hour for this customer."
            )
        })


    # ----------------------------------------------
    # TRANSACTION VELOCITY
    # ----------------------------------------------

    velocity = transaction[
        "transactions_last_10min"
    ]

    if velocity >= 5:

        explanations.append({
            "feature": "transactions_last_10min",
            "severity": "HIGH",
            "title": "High transaction velocity",
            "message": (
                f"{int(velocity)} transactions were "
                "detected within the previous 10 minutes."
            )
        })

    elif velocity >= 3:

        explanations.append({
            "feature": "transactions_last_10min",
            "severity": "MEDIUM",
            "title": "Elevated transaction velocity",
            "message": (
                f"{int(velocity)} transactions occurred "
                "within the previous 10 minutes."
            )
        })


    # ----------------------------------------------
# SPENDING BURST
# ----------------------------------------------

    spending = transaction[
        "amount_spent_last_1h"
    ]

    normal_amount = (
        transaction["amount"] /
        max(transaction["amount_ratio"], 0.01)
    )

    if spending > normal_amount * 5:

        explanations.append({
            "feature": "amount_spent_last_1h",
            "severity": "HIGH",
            "title": "Sudden spending burst",
            "message": (
                "The customer has spent significantly "
                "more than their normal amount within "
                "the last hour."
            )
        })

    # ----------------------------------------------
    # FAILED ATTEMPTS
    # ----------------------------------------------

    failed = transaction[
        "failed_attempts_before_success"
    ]

    if failed >= 3:

        explanations.append({
            "feature": "failed_attempts_before_success",
            "severity": "HIGH",
            "title": "Repeated failed attempts",
            "message": (
                f"{int(failed)} failed payment attempts "
                "occurred before this successful transaction."
            )
        })


    # ----------------------------------------------
    # NEW MERCHANT CATEGORY
    # ----------------------------------------------

    if transaction["is_new_category"] == 1:

        explanations.append({
            "feature": "is_new_category",
            "severity": "MEDIUM",
            "title": "Unfamiliar merchant category",
            "message": (
                "This merchant category is unusual "
                "for this customer."
            )
        })


    # ----------------------------------------------
    # NEW PAYMENT METHOD
    # ----------------------------------------------

    if transaction[
        "is_new_payment_method"
    ] == 1:

        explanations.append({
            "feature": "is_new_payment_method",
            "severity": "MEDIUM",
            "title": "New payment method",
            "message": (
                "The customer is using a payment "
                "method not normally associated "
                "with their account."
            )
        })


    # ----------------------------------------------
    # DEVICE SHARING
    # ----------------------------------------------

    device_accounts = transaction[
        "device_account_count"
    ]

    if device_accounts >= 3:

        explanations.append({
            "feature": "device_account_count",
            "severity": "MEDIUM",
            "title": "Shared device detected",
            "message": (
                f"This device is associated with "
                f"{int(device_accounts)} customer accounts."
            )
        })


    # ----------------------------------------------
    # ACCOUNT AGE
    # ----------------------------------------------

    account_age = transaction[
        "account_age_days"
    ]

    if account_age <= 30:

        explanations.append({
            "feature": "account_age_days",
            "severity": "MEDIUM",
            "title": "Recently created account",
            "message": (
                f"The customer account is only "
                f"{int(account_age)} days old."
            )
        })


    # ----------------------------------------------
    # TIME DEVIATION
    # ----------------------------------------------

    deviation = transaction[
        "time_deviation"
    ]

    if deviation >= 6:

        explanations.append({
            "feature": "time_deviation",
            "severity": "MEDIUM",
            "title": "Activity time deviation",
            "message": (
                f"The transaction occurred approximately "
                f"{deviation:.0f} hours away from the "
                "customer's usual transaction time."
            )
        })


    return explanations


# ==================================================
# PRINT EXPLANATIONS
# ==================================================

def print_explanations(explanations):

    print("\nWHY WAS THIS TRANSACTION FLAGGED?")
    print("=" * 60)


    if not explanations:

        print(
            "No significant behavioral anomalies detected."
        )

        return


    for number, explanation in enumerate(
        explanations,
        start=1
    ):

        severity = explanation["severity"]

        print(
            f"\n{number}. "
            f"[{severity}] "
            f"{explanation['title']}"
        )

        print(
            f"   {explanation['message']}"
        )