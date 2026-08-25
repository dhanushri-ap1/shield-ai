import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from ml.explanation_engine import generate_explanations
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

    # ------------------------------------------
    # HUMAN EXPLANATIONS
    # ------------------------------------------

    explanations = (
        generate_explanations(
            transaction
        )
    )

    # ------------------------------------------
    # BEHAVIOR COMPARISON
    # ------------------------------------------

    behavior_comparison = (
        create_behavior_comparison(
            transaction
        )
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

        "explanations":
            explanations,

        "behavior_comparison":
            behavior_comparison
    }


# ============================================================
# LOAD AND TRAIN MODEL ONCE
# ============================================================

print(
    "Loading Shield-AI fraud engine..."
)

MODEL_DATA = prepare_data()

print(
    "Training Shield-AI fraud model..."
)

MODEL = get_model(
    MODEL_DATA
)

print(
    "Shield-AI fraud engine ready!"
)