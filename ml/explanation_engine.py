import math


FEATURE_LABELS = {
    "amount": "Transaction amount",
    "amount_ratio": "Spend vs this customer's usual amount",
    "is_new_device": "New or unknown device",
    "is_new_location": "Unusual location",
    "is_odd_hour": "Late-night / early-morning activity",
    "transactions_last_10min": "Burst of transactions in 10 minutes",
    "amount_spent_last_1h": "Spend in the last hour",
    "failed_attempts_before_success": "Failed attempts before this payment",
    "is_new_category": "Unfamiliar merchant category",
    "is_new_payment_method": "New payment method",
    "device_account_count": "Device linked to multiple accounts",
    "account_age_days": "Young account",
    "time_deviation": "Time of day vs usual habit",
    "behavior_deviation_score": "Combined behaviour deviation",
}


def _num(transaction, key, default=0.0):
    try:
        value = transaction[key]
    except Exception:
        return default

    if value is None:
        return default

    try:
        if math.isnan(float(value)):
            return default
    except (TypeError, ValueError):
        return default

    return float(value)


def _int(transaction, key, default=0):
    return int(_num(transaction, key, default))


def generate_explanations(
    transaction,
    risk_score=None,
    risk_level=None,
    model_drivers=None,
):
    """
    Convert transaction features into investigator-facing
    reasons. Always returns at least one explanation so the
    UI never shows a blank "Why was this flagged?" panel.
    """

    explanations = []

    amount = _num(transaction, "amount")
    amount_ratio = _num(transaction, "amount_ratio", 1.0)
    usual_amount = amount / max(amount_ratio, 0.01)

    if amount_ratio >= 3:
        explanations.append({
            "feature": "amount_ratio",
            "severity": "HIGH",
            "title": "Spend is far above this customer's normal",
            "message": (
                f"This payment is ₹{amount:,.0f}, about "
                f"{amount_ratio:.1f}× their usual amount of "
                f"₹{usual_amount:,.0f}. Large spikes like this "
                "are a common fraud pattern."
            ),
        })
    elif amount_ratio >= 1.8:
        explanations.append({
            "feature": "amount_ratio",
            "severity": "MEDIUM",
            "title": "Spend is above this customer's normal",
            "message": (
                f"This payment is ₹{amount:,.0f} versus a typical "
                f"₹{usual_amount:,.0f} ({amount_ratio:.1f}×). "
                "Worth checking if the purchase matches recent activity."
            ),
        })

    if _int(transaction, "is_new_device") == 1:
        explanations.append({
            "feature": "is_new_device",
            "severity": "HIGH",
            "title": "Paid from a device this customer does not usually use",
            "message": (
                "The device on this transaction is not the one "
                "this customer normally pays from. Combined with "
                "other changes, that often indicates account takeover."
            ),
        })

    if _int(transaction, "is_new_location") == 1:
        explanations.append({
            "feature": "is_new_location",
            "severity": "HIGH",
            "title": "Location does not match this customer's pattern",
            "message": (
                "The payment originated from a country or network "
                "this customer does not normally use."
            ),
        })

    hour = _int(transaction, "hour")
    usual_hour = _num(transaction, "usual_hour")
    time_deviation = _num(transaction, "time_deviation")

    if _int(transaction, "is_odd_hour") == 1:
        explanations.append({
            "feature": "is_odd_hour",
            "severity": "MEDIUM",
            "title": "Payment happened in a high-risk overnight window",
            "message": (
                f"The transaction was at {hour:02d}:00, between "
                "midnight and 5am — a window this model treats as "
                "elevated risk."
            ),
        })
    elif time_deviation >= 6:
        explanations.append({
            "feature": "time_deviation",
            "severity": "MEDIUM",
            "title": "Paid at a very different time of day",
            "message": (
                f"This customer usually transacts around "
                f"{int(round(usual_hour)):02d}:00. This one is at "
                f"{hour:02d}:00, about {time_deviation:.0f} hours off "
                "their normal window."
            ),
        })
    elif time_deviation >= 3:
        explanations.append({
            "feature": "time_deviation",
            "severity": "LOW",
            "title": "Slightly outside their usual hours",
            "message": (
                f"Usual time is around {int(round(usual_hour)):02d}:00; "
                f"this payment is at {hour:02d}:00 "
                f"({time_deviation:.0f} hours later or earlier). "
                "On its own this is weak evidence."
            ),
        })

    velocity = _int(transaction, "transactions_last_10min")

    if velocity >= 5:
        explanations.append({
            "feature": "transactions_last_10min",
            "severity": "HIGH",
            "title": "Rapid burst of transactions",
            "message": (
                f"{velocity} other payments from this customer were "
                "seen in the 10 minutes before this one. That velocity "
                "is typical of card testing or a compromised session."
            ),
        })
    elif velocity >= 3:
        explanations.append({
            "feature": "transactions_last_10min",
            "severity": "MEDIUM",
            "title": "More activity than usual in a short window",
            "message": (
                f"{velocity} other transactions occurred in the previous "
                "10 minutes — faster than a normal browsing session."
            ),
        })

    spending = _num(transaction, "amount_spent_last_1h")

    if spending > usual_amount * 5 and spending > 0:
        explanations.append({
            "feature": "amount_spent_last_1h",
            "severity": "HIGH",
            "title": "Sudden spending burst in the last hour",
            "message": (
                f"About ₹{spending:,.0f} was spent in the hour before "
                f"this ₹{amount:,.0f} payment — several times this "
                "customer's typical ticket size."
            ),
        })

    failed = _int(transaction, "failed_attempts_before_success")

    if failed >= 3:
        explanations.append({
            "feature": "failed_attempts_before_success",
            "severity": "HIGH",
            "title": "Several failures immediately before this success",
            "message": (
                f"{failed} failed attempts preceded this payment. "
                "That pattern often appears in credential stuffing "
                "or card testing."
            ),
        })
    elif failed >= 1:
        explanations.append({
            "feature": "failed_attempts_before_success",
            "severity": "LOW",
            "title": "Failed attempt(s) before this payment went through",
            "message": (
                f"{failed} failed attempt(s) happened just before this "
                "successful transaction."
            ),
        })

    if _int(transaction, "is_new_category") == 1:
        explanations.append({
            "feature": "is_new_category",
            "severity": "MEDIUM",
            "title": "Merchant category is new for this customer",
            "message": (
                "This spend category is not one this customer usually "
                "pays in. Harmless if they are trying a new merchant; "
                "riskier if paired with a new device or location."
            ),
        })

    if _int(transaction, "is_new_payment_method") == 1:
        explanations.append({
            "feature": "is_new_payment_method",
            "severity": "MEDIUM",
            "title": "Payment method is new for this account",
            "message": (
                "This customer is using a card or method they do not "
                "normally use."
            ),
        })

    device_accounts = _int(transaction, "device_account_count")

    if device_accounts >= 3:
        explanations.append({
            "feature": "device_account_count",
            "severity": "MEDIUM",
            "title": "This device is tied to several customer accounts",
            "message": (
                f"The same device has been seen on {device_accounts} "
                "accounts, which can indicate a mule device or shared "
                "fraud infrastructure."
            ),
        })

    account_age = _int(transaction, "account_age_days", 365)

    if account_age <= 7:
        explanations.append({
            "feature": "account_age_days",
            "severity": "HIGH",
            "title": "Very new account",
            "message": (
                f"The account is only {account_age} day(s) old. "
                "Fresh accounts have a higher fraud rate."
            ),
        })
    elif account_age <= 30:
        explanations.append({
            "feature": "account_age_days",
            "severity": "MEDIUM",
            "title": "Recently created account",
            "message": (
                f"The account is {account_age} days old, still in "
                "the window where synthetic and mule accounts are common."
            ),
        })

    hard_reasons = [
        item for item in explanations
        if item["severity"] in ("HIGH", "MEDIUM")
    ]

    level = (risk_level or "").upper()
    score = None if risk_score is None else float(risk_score)
    flagged = level in ("HIGH", "MEDIUM") or (
        score is not None and score >= 40
    )

    if flagged and not hard_reasons:
        driver_lines = _driver_sentences(model_drivers)
        if driver_lines:
            message = (
                "No single behaviour crossed a hard rule "
                "(amount, device, location, and so on all look "
                "close to normal). The model still raised risk "
                f"to {score:.1f}/100 because of a mix of weaker "
                f"signals: {driver_lines}"
            )
        else:
            message = (
                "No single obvious anomaly was found — amount, "
                "device, location, and merchant all look close to "
                "this customer's baseline. The score comes from "
                "the combined pattern across several weaker features, "
                "not one smoking gun."
            )

        explanations.insert(0, {
            "feature": "model_combination",
            "severity": "MEDIUM" if level != "HIGH" else "HIGH",
            "title": "Flagged by the combined risk model, not one red flag",
            "message": message,
        })
    elif not flagged and not explanations:
        explanations.append({
            "feature": "baseline",
            "severity": "LOW",
            "title": "Behaviour is consistent with this customer",
            "message": (
                "Amount, device, location, timing, merchant, and "
                "payment method all sit close to this customer's "
                "usual pattern. The model does not treat this as "
                "a strong fraud case."
                + (
                    f" Risk score is {score:.1f}/100."
                    if score is not None
                    else ""
                )
            ),
        })
    elif flagged and hard_reasons and model_drivers:
        extras = _unused_driver_sentences(
            model_drivers,
            {item["feature"] for item in explanations},
        )
        if extras:
            explanations.append({
                "feature": "model_combination",
                "severity": "LOW",
                "title": "Other model signals that added to the score",
                "message": extras,
            })

    severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    explanations.sort(
        key=lambda item: severity_rank.get(item["severity"], 3)
    )

    return explanations


def _driver_sentences(model_drivers, limit=3):
    if not model_drivers:
        return ""

    parts = []
    for driver in model_drivers[:limit]:
        if driver.get("delta", 0) <= 0:
            continue
        label = driver.get("label") or driver.get("feature")
        parts.append(label)

    if not parts:
        for driver in model_drivers[:limit]:
            label = driver.get("label") or driver.get("feature")
            parts.append(label)

    if not parts:
        return ""

    if len(parts) == 1:
        return f"{parts[0]}."

    return f"{', '.join(parts[:-1])}, and {parts[-1]}."


def _unused_driver_sentences(model_drivers, used_features):
    extras = []
    for driver in model_drivers:
        feature = driver.get("feature")
        if feature in used_features or feature == "model_combination":
            continue
        if driver.get("delta", 0) <= 0:
            continue
        extras.append(driver.get("label") or feature)
        if len(extras) >= 3:
            break

    if not extras:
        return ""

    return (
        "The model also increased risk from: "
        + ", ".join(extras)
        + "."
    )


def print_explanations(explanations):

    print("\nWHY WAS THIS TRANSACTION FLAGGED?")
    print("=" * 60)

    if not explanations:
        print("No significant behavioral anomalies detected.")
        return

    for number, explanation in enumerate(explanations, start=1):
        severity = explanation["severity"]
        print(f"\n{number}. [{severity}] {explanation['title']}")
        print(f"   {explanation['message']}")
