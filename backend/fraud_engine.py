import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ml.explanation_engine import (
    FEATURE_LABELS,
    generate_explanations,
)
from ml.behavior_comparison import create_behavior_comparison


DATA_PATH = "data/raw/transactions.csv"


FEATURES = [
    "amount",
    "amount_ratio",
    "is_new_device",
    "is_new_location",
    "is_odd_hour",
    "transactions_last_10min",
    "amount_spent_last_1h",
    "failed_attempts_before_success",
    "is_new_category",
    "is_new_payment_method",
    "device_account_count",
    "account_age_days",
    "time_deviation",
    "behavior_deviation_score"
]


def prepare_data():

    df = pd.read_csv(DATA_PATH)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df = df.sort_values(
        ["customer_id", "timestamp"]
    ).reset_index(drop=True)

    # ------------------------------------------
    # TIME FEATURES
    # ------------------------------------------

    df["hour"] = (
        df["timestamp"].dt.hour
    )

    df["is_odd_hour"] = (
        (df["hour"] >= 0) &
        (df["hour"] <= 5)
    ).astype(int)

    # ------------------------------------------
    # CUSTOMER PROFILE
    # ------------------------------------------

    normal = df[
        df["is_fraud"] == 0
    ]

    customer_avg = (
        normal
        .groupby("customer_id")["amount"]
        .mean()
    )

    df["customer_avg_amount"] = (
        df["customer_id"]
        .map(customer_avg)
        .fillna(df["amount"].mean())
    )

    customer_usual_hour = (
        normal
        .groupby("customer_id")["hour"]
        .mean()
    )

    df["usual_hour"] = (
        df["customer_id"]
        .map(customer_usual_hour)
        .fillna(df["hour"].mean())
    )

    # ------------------------------------------
    # AMOUNT ANOMALY
    # ------------------------------------------

    df["amount_ratio"] = (
        df["amount"] /
        df["customer_avg_amount"]
    )

    # ------------------------------------------
    # DEVICE ANOMALY
    # ------------------------------------------

    usual_device = (
        normal
        .groupby("customer_id")["device_id"]
        .agg(
            lambda x: x.mode().iloc[0]
        )
    )

    df["usual_device"] = (
        df["customer_id"]
        .map(usual_device)
    )

    df["is_new_device"] = (
        df["device_id"] !=
        df["usual_device"]
    ).astype(int)

    # ------------------------------------------
    # LOCATION ANOMALY
    # ------------------------------------------

    usual_location = (
        normal
        .groupby("customer_id")["ip_country"]
        .agg(
            lambda x: x.mode().iloc[0]
        )
    )

    df["usual_location"] = (
        df["customer_id"]
        .map(usual_location)
    )

    df["is_new_location"] = (
        df["ip_country"] !=
        df["usual_location"]
    ).astype(int)

    # ------------------------------------------
    # MERCHANT CATEGORY ANOMALY
    # ------------------------------------------

    usual_category = (
        normal
        .groupby("customer_id")[
            "merchant_category"
        ]
        .agg(
            lambda x: x.mode().iloc[0]
        )
    )

    df["usual_category"] = (
        df["customer_id"]
        .map(usual_category)
    )

    df["is_new_category"] = (
        df["merchant_category"] !=
        df["usual_category"]
    ).astype(int)

    # ------------------------------------------
    # PAYMENT METHOD ANOMALY
    # ------------------------------------------

    usual_payment = (
        normal
        .groupby("customer_id")[
            "payment_method"
        ]
        .agg(
            lambda x: x.mode().iloc[0]
        )
    )

    df["usual_payment_method"] = (
        df["customer_id"]
        .map(usual_payment)
    )

    df["is_new_payment_method"] = (
        df["payment_method"] !=
        df["usual_payment_method"]
    ).astype(int)

    # ------------------------------------------
    # TIME DEVIATION
    # ------------------------------------------

    df["time_deviation"] = (
        df["hour"] -
        df["usual_hour"]
    ).abs()

    df["time_deviation"] = (
        df["time_deviation"]
        .apply(
            lambda x:
            min(x, 24 - x)
        )
    )

    # ------------------------------------------
    # TRANSACTION VELOCITY
    # ------------------------------------------

    df["transactions_last_10min"] = (

        df
        .groupby("customer_id")
        .rolling(
            "10min",
            on="timestamp"
        )["transaction_id"]
        .count()
        .reset_index(
            level=[0, 1],
            drop=True
        )
        .sub(1)
        .clip(lower=0)
        .values
    )

    # ------------------------------------------
    # SPENDING VELOCITY
    # ------------------------------------------

    df["amount_spent_last_1h"] = (

        df
        .groupby("customer_id")
        .rolling(
            "1h",
            on="timestamp"
        )["amount"]
        .sum()
        .reset_index(
            level=[0, 1],
            drop=True
        )
        .values
        -
        df["amount"]
    )

    # ------------------------------------------
    # FAILED ATTEMPTS
    # ------------------------------------------

    df["failed_flag"] = (
        df["transaction_status"] ==
        "failed"
    ).astype(int)

    df[
        "failed_attempts_before_success"
    ] = (

        df
        .groupby("customer_id")[
            "failed_flag"
        ]
        .transform(
            lambda x:
            x.shift(1)
            .fillna(0)
            .groupby(
                (x == 0).cumsum()
            )
            .cumsum()
        )
    )

    # ------------------------------------------
    # DEVICE SHARING
    # ------------------------------------------

    device_accounts = (
        df
        .groupby("device_id")[
            "customer_id"
        ]
        .nunique()
    )

    df["device_account_count"] = (
        df["device_id"]
        .map(device_accounts)
    )

    # ------------------------------------------
    # BEHAVIOR DEVIATION SCORE
    # ------------------------------------------

    df["behavior_deviation_score"] = (

        df["amount_ratio"]
        .clip(upper=10)
        * 5

        + df["is_new_device"] * 15

        + df["is_new_location"] * 15

        + df["is_new_category"] * 10

        + df["is_new_payment_method"] * 10

        + df["is_odd_hour"] * 10

        + df["transactions_last_10min"]
        .clip(upper=5)
        * 5
    )

    df["behavior_deviation_score"] = (
        df["behavior_deviation_score"]
        .clip(upper=100)
    )

    return df


def get_model(df):

    X = df[FEATURES]

    y = df["is_fraud"]

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    model.fit(
        X,
        y
    )

    return model


def _to_native(value):
    try:
        return value.item()
    except AttributeError:
        return value


def model_risk_drivers(model, X_transaction, medians):
    """
    Approximate how much each feature raised the fraud
    probability by replacing it with the training median.
    """

    baseline = float(
        model.predict_proba(X_transaction)[0][1]
    )

    drivers = []

    for feature in FEATURES:
        altered = X_transaction.copy()
        altered[feature] = medians[feature]
        swapped = float(
            model.predict_proba(altered)[0][1]
        )
        delta = baseline - swapped
        drivers.append({
            "feature": feature,
            "label": FEATURE_LABELS.get(feature, feature),
            "delta": round(delta, 4),
            "raises_risk": delta > 0.005,
        })

    drivers.sort(
        key=lambda item: abs(item["delta"]),
        reverse=True,
    )

    return drivers


def build_score_breakdown(model_drivers, risk_score):
    """
    Turn raw model-driver probability deltas into investigator-facing
    "contributing signal" points that roughly add up to the risk score,
    e.g. New Device +30, Unusual Time +25, New Location +15.
    """

    positive = [
        driver for driver in model_drivers
        if driver.get("raises_risk") and driver.get("delta", 0) > 0
    ]

    if not positive:
        return []

    total_delta = sum(driver["delta"] for driver in positive)

    breakdown = []

    for driver in positive[:5]:

        share = driver["delta"] / total_delta if total_delta else 0

        points = round(share * risk_score)

        if points <= 0:
            continue

        if points >= 20:
            weight = "HIGH"
        elif points >= 10:
            weight = "MEDIUM"
        else:
            weight = "LOW"

        breakdown.append({
            "label": driver["label"],
            "points": int(points),
            "weight": weight,
        })

    return breakdown


PRIMARY_REASON_RULES = [
    ("is_new_device", "New Device"),
    ("is_new_location", "Unusual Location"),
    ("is_odd_hour", "Odd Hour Activity"),
    ("transactions_last_10min_high", "Velocity Burst"),
    ("failed_attempts_before_success", "Failed Attempts"),
    ("amount_ratio_high", "High Amount"),
    ("is_new_payment_method", "New Payment Method"),
    ("is_new_category", "New Merchant Category"),
    ("device_account_count_high", "Shared Device"),
    ("account_age_low", "New Account"),
]


def primary_reason_for_row(row):
    """
    Cheap, rule-based "why this is in the queue" label — used for the
    priority queue where we don't want to run the full model-driver
    explanation for every row.
    """

    if _to_native(row.get("is_new_device", 0)) == 1:
        return "New Device"

    if _to_native(row.get("is_new_location", 0)) == 1:
        return "Unusual Location"

    if _to_native(row.get("is_odd_hour", 0)) == 1:
        return "Odd Hour Activity"

    if _to_native(row.get("time_deviation", 0)) >= 6:
        return "Time Deviation"

    if _to_native(row.get("transactions_last_10min", 0)) >= 3:
        return "Velocity Burst"

    if _to_native(row.get("failed_attempts_before_success", 0)) >= 1:
        return "Failed Attempts"

    if _to_native(row.get("amount_ratio", 1)) >= 1.8:
        return "High Amount"

    if _to_native(row.get("is_new_payment_method", 0)) == 1:
        return "New Payment Method"

    if _to_native(row.get("is_new_category", 0)) == 1:
        return "New Merchant Category"

    if _to_native(row.get("device_account_count", 1)) >= 3:
        return "Shared Device"

    if _to_native(row.get("account_age_days", 999)) <= 30:
        return "New Account"

    return "Behaviour Pattern"


def get_priority_queue(limit=30, max_per_reason=None):
    """
    Rank transactions the way an investigator's queue would: worst risk
    first, with a short human-readable reason and a relative timestamp.

    The raw data has a large cluster of transactions that all trip the
    exact same combination of rules (new device + new location + odd
    hour + new category) and saturate the score at 100 — sorting by
    score alone would flood the queue with dozens of near-identical
    "New Device" rows and bury every other case type. We cap how many
    queue slots any single reason can take so investigators see a
    genuinely varied worklist, still ordered worst-first within that
    constraint.
    """

    if max_per_reason is None:
        max_per_reason = max(3, limit // 5)

    df = MODEL_DATA[
        MODEL_DATA["risk_level"].isin(["HIGH", "MEDIUM"])
    ].copy()

    if df.empty:
        df = MODEL_DATA.copy()

    df = df.sort_values("risk_score", ascending=False)

    df["reason"] = df.apply(primary_reason_for_row, axis=1)

    selected = []
    reason_counts = {}
    overflow = []

    for _, row in df.iterrows():

        reason = row["reason"]
        count = reason_counts.get(reason, 0)

        if count >= max_per_reason:
            overflow.append(row)
            continue

        selected.append(row)
        reason_counts[reason] = count + 1

        if len(selected) >= limit:
            break

    # If capping reasons left us short (e.g. almost everything shares
    # one reason), backfill from the overflow pile so we still return
    # `limit` items.
    if len(selected) < limit:
        for row in overflow:
            selected.append(row)
            if len(selected) >= limit:
                break

    selected.sort(key=lambda row: row["risk_score"], reverse=True)

    import datetime

    now = datetime.datetime.now()

    items = []

    for row in selected:

        timestamp = row["timestamp"]

        delta = now - timestamp.to_pydatetime().replace(tzinfo=None)
        minutes = int(delta.total_seconds() // 60)

        if minutes < 1:
            time_ago = "just now"
        elif minutes < 60:
            time_ago = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif minutes < 60 * 24:
            hours = minutes // 60
            time_ago = f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = minutes // (60 * 24)
            time_ago = f"{days} day{'s' if days != 1 else ''} ago"

        items.append({
            "transaction_id": row["transaction_id"],
            "customer_id": row["customer_id"],
            "amount": float(row["amount"]),
            "risk_score": round(float(row["risk_score"]), 1),
            "risk_level": row["risk_level"],
            "reason": row["reason"],
            "timestamp": str(timestamp),
            "time_ago": time_ago,
        })

    return items


def investigate_with_model(
    transaction_id
):

    matches = MODEL_DATA[
        MODEL_DATA["transaction_id"]
        == transaction_id
    ]

    if matches.empty:
        return None

    transaction = (
        matches.iloc[0]
    )

    X_transaction = (
        transaction[FEATURES]
        .to_frame()
        .T
    )

    probability = (
        MODEL
        .predict_proba(
            X_transaction
        )[0][1]
    )

    risk_score = (
        probability * 100
    )

    if risk_score >= 70:

        risk_level = "HIGH"

        recommended_action = (
            "MANUAL_REVIEW"
        )

    elif risk_score >= 40:

        risk_level = "MEDIUM"

        recommended_action = (
            "STEP_UP_VERIFICATION"
        )

    else:

        risk_level = "LOW"

        recommended_action = (
            "ALLOW"
        )

    model_drivers = model_risk_drivers(
        MODEL,
        X_transaction,
        FEATURE_MEDIANS,
    )

    explanations = generate_explanations(
        transaction,
        risk_score=risk_score,
        risk_level=risk_level,
        model_drivers=model_drivers,
    )

    behavior_comparison = create_behavior_comparison(
        transaction
    )

    score_breakdown = build_score_breakdown(
        model_drivers,
        risk_score,
    )

    if explanations:
        hard = [
            item for item in explanations
            if item["severity"] in ("HIGH", "MEDIUM")
        ]
        lead = (hard or explanations)[0]
        extra = max(len(hard) - 1, 0)
        if risk_level in ("HIGH", "MEDIUM"):
            flag_summary = lead["title"]
            if extra:
                flag_summary += (
                    f" — plus {extra} other risk signal"
                    f"{'s' if extra != 1 else ''}."
                )
            elif lead["feature"] == "model_combination":
                flag_summary += (
                    f" Model score {round(risk_score, 1)}/100."
                )
        else:
            flag_summary = lead["title"]
    elif risk_level in ("HIGH", "MEDIUM"):
        flag_summary = (
            f"The model scored this {risk_level} "
            f"({round(risk_score, 1)}/100) from a mix of "
            "weaker signals rather than one obvious anomaly."
        )
    else:
        flag_summary = (
            "Behaviour is close to this customer's baseline. "
            "The model does not treat this as a strong fraud case."
        )

    return {

        "transaction":
            transaction,

        "risk_score":
            round(
                risk_score,
                2
            ),

        "risk_level":
            risk_level,

        "recommended_action":
            recommended_action,

        "flag_summary":
            flag_summary,

        "explanations":
            explanations,

        "behavior_comparison":
            behavior_comparison,

        "score_breakdown":
            score_breakdown,

        "model_drivers": [
            driver
            for driver in model_drivers[:5]
            if abs(driver["delta"]) >= 0.005
        ],
    }


# ============================================================
# LOAD AND TRAIN MODEL ONCE
# ============================================================

print(
    "Loading Shield-AI fraud engine..."
)

MODEL_DATA = prepare_data()

FEATURE_MEDIANS = {
    feature: _to_native(
        MODEL_DATA[feature].median()
    )
    for feature in FEATURES
}

print(
    "Training Shield-AI fraud model..."
)

MODEL = get_model(
    MODEL_DATA
)

print(
    "Scoring transaction history..."
)

_ALL_PROBABILITIES = MODEL.predict_proba(
    MODEL_DATA[FEATURES]
)[:, 1]

MODEL_DATA["risk_score"] = _ALL_PROBABILITIES * 100

MODEL_DATA["risk_level"] = MODEL_DATA["risk_score"].apply(
    lambda score:
        "HIGH" if score >= 70 else
        "MEDIUM" if score >= 40 else
        "LOW"
)

print(
    "Shield-AI fraud engine ready!"
)