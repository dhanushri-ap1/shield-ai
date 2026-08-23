import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

df = pd.read_csv(
    "data/raw/transactions.csv"
)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)


# --------------------------------------------------
# BASIC TIME FEATURES
# --------------------------------------------------

df["hour"] = df["timestamp"].dt.hour

df["is_odd_hour"] = (
    (df["hour"] >= 0) &
    (df["hour"] <= 5)
).astype(int)


# --------------------------------------------------
# CUSTOMER NORMAL BEHAVIOR
# --------------------------------------------------

customer_avg = (
    df[df["is_fraud"] == 0]
    .groupby("customer_id")["amount"]
    .mean()
)

df["customer_avg_amount"] = (
    df["customer_id"].map(customer_avg)
)

df["customer_avg_amount"] = (
    df["customer_avg_amount"]
    .fillna(df["amount"].mean())
)


# --------------------------------------------------
# 1. AMOUNT RATIO
# --------------------------------------------------

df["amount_ratio"] = (
    df["amount"] /
    df["customer_avg_amount"]
)


# --------------------------------------------------
# CUSTOMER USUAL DEVICE
# --------------------------------------------------

usual_devices = (
    df[df["is_fraud"] == 0]
    .groupby("customer_id")["device_id"]
    .agg(lambda x: x.mode().iloc[0])
)

df["usual_device"] = (
    df["customer_id"].map(usual_devices)
)

df["is_new_device"] = (
    df["device_id"] != df["usual_device"]
).astype(int)


# --------------------------------------------------
# CUSTOMER USUAL LOCATION
# --------------------------------------------------

usual_locations = (
    df[df["is_fraud"] == 0]
    .groupby("customer_id")["ip_country"]
    .agg(lambda x: x.mode().iloc[0])
)

df["usual_location"] = (
    df["customer_id"].map(usual_locations)
)

df["is_new_location"] = (
    df["ip_country"] != df["usual_location"]
).astype(int)


# --------------------------------------------------
# CUSTOMER USUAL CATEGORY
# --------------------------------------------------

usual_categories = (
    df[df["is_fraud"] == 0]
    .groupby("customer_id")["merchant_category"]
    .agg(lambda x: x.mode().iloc[0])
)

df["usual_category"] = (
    df["customer_id"].map(usual_categories)
)

df["is_new_category"] = (
    df["merchant_category"] !=
    df["usual_category"]
).astype(int)


# --------------------------------------------------
# CUSTOMER USUAL PAYMENT METHOD
# --------------------------------------------------

usual_payment = (
    df[df["is_fraud"] == 0]
    .groupby("customer_id")["payment_method"]
    .agg(lambda x: x.mode().iloc[0])
)

df["usual_payment_method"] = (
    df["customer_id"].map(usual_payment)
)

df["is_new_payment_method"] = (
    df["payment_method"] !=
    df["usual_payment_method"]
).astype(int)


# --------------------------------------------------
# TIME DEVIATION
# --------------------------------------------------

df["time_deviation"] = abs(
    df["hour"] - df["usual_hour"]
)

df["time_deviation"] = df[
    "time_deviation"
].apply(
    lambda x: min(x, 24 - x)
)


# --------------------------------------------------
# TRANSACTION VELOCITY
# --------------------------------------------------

df["transactions_last_10min"] = 0

df["amount_spent_last_1h"] = 0.0

for customer_id, group in df.groupby(
    "customer_id"
):

    indices = group.index

    for index in indices:

        current_time = df.loc[
            index,
            "timestamp"
        ]

        previous = df.loc[
            indices,
            "timestamp"
        ]

        time_difference = (
            current_time - previous
        )

        last_10_min = (
            (time_difference >= pd.Timedelta(0)) &
            (time_difference <= pd.Timedelta(minutes=10))
        )

        last_1_hour = (
            (time_difference >= pd.Timedelta(0)) &
            (time_difference <= pd.Timedelta(hours=1))
        )

        df.loc[
            index,
            "transactions_last_10min"
        ] = max(
            int(last_10_min.sum()) - 1,
            0
        )

        df.loc[
            index,
            "amount_spent_last_1h"
        ] = df.loc[
            indices[last_1_hour],
            "amount"
        ].sum() - df.loc[
            index,
            "amount"
        ]


# --------------------------------------------------
# FAILED ATTEMPTS
# --------------------------------------------------

df["failed_attempts_before_success"] = 0

for customer_id, group in df.groupby(
    "customer_id"
):

    group = group.sort_values(
        "timestamp"
    )

    failed_count = 0

    for index in group.index:

        if df.loc[
            index,
            "transaction_status"
        ] == "failed":

            failed_count += 1

        else:

            df.loc[
                index,
                "failed_attempts_before_success"
            ] = failed_count

            failed_count = 0


# --------------------------------------------------
# DEVICE SHARING
# --------------------------------------------------

device_accounts = (
    df.groupby("device_id")["customer_id"]
    .nunique()
)

df["device_account_count"] = (
    df["device_id"].map(device_accounts)
)


# --------------------------------------------------
# BEHAVIOR DEVIATION SCORE
# --------------------------------------------------

df["behavior_deviation_score"] = (
    df["amount_ratio"].clip(upper=10) * 5
    + df["is_new_device"] * 15
    + df["is_new_location"] * 15
    + df["is_new_category"] * 10
    + df["is_new_payment_method"] * 10
    + df["is_odd_hour"] * 10
    + df["transactions_last_10min"].clip(upper=5) * 5
)

df["behavior_deviation_score"] = (
    df["behavior_deviation_score"]
    .clip(upper=100)
)


# --------------------------------------------------
# MODEL FEATURES
# --------------------------------------------------

features = [
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


X = df[features]

y = df["is_fraud"]


# --------------------------------------------------
# TRAIN / TEST SPLIT
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# --------------------------------------------------
# RANDOM FOREST
# --------------------------------------------------

model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    class_weight="balanced"
)


model.fit(
    X_train,
    y_train
)


# --------------------------------------------------
# PREDICTION
# --------------------------------------------------

predictions = model.predict(
    X_test
)


fraud_probabilities = (
    model.predict_proba(X_test)[:, 1]
)


risk_scores = (
    fraud_probabilities * 100
)


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

print("\nMODEL RESULTS")
print("=" * 50)

print(
    classification_report(
        y_test,
        predictions
    )
)


# --------------------------------------------------
# FEATURE IMPORTANCE
# --------------------------------------------------

importance = pd.DataFrame({
    "feature": features,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print("\nTOP FRAUD SIGNALS")
print("=" * 50)

print(
    importance.head(10).to_string(
        index=False
    )
)


# --------------------------------------------------
# SAMPLE RISK SCORES
# --------------------------------------------------

print("\nSAMPLE RISK SCORES")
print("=" * 50)

for score in risk_scores[:10]:

    print(
        f"Risk Score: {score:.2f}/100"
    )