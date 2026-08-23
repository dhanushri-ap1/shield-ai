import pandas as pd
import shap

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

from explanation_engine import (
    generate_explanations,
    print_explanations
)

from behavior_comparison import (
    create_behavior_comparison,
    print_behavior_comparison
)


# ==================================================
# 1. LOAD DATA
# ==================================================

print("Loading dataset...")

df = pd.read_csv(
    "data/raw/transactions.csv"
)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

df = df.sort_values(
    ["customer_id", "timestamp"]
).reset_index(drop=True)


# ==================================================
# 2. TIME FEATURES
# ==================================================

print("Creating time features...")

df["hour"] = (
    df["timestamp"].dt.hour
)

df["is_odd_hour"] = (
    (df["hour"] >= 0) &
    (df["hour"] <= 5)
).astype(int)


# ==================================================
# 3. CUSTOMER NORMAL BEHAVIOR
# ==================================================

print("Creating customer profiles...")

normal = df[
    df["is_fraud"] == 0
]


# Average transaction amount

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


# Usual hour

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


# ==================================================
# 4. AMOUNT ANOMALY
# ==================================================

df["amount_ratio"] = (
    df["amount"] /
    df["customer_avg_amount"]
)


# ==================================================
# 5. DEVICE ANOMALY
# ==================================================

usual_device = (
    normal
    .groupby("customer_id")["device_id"]
    .agg(
        lambda x:
        x.mode().iloc[0]
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


# ==================================================
# 6. LOCATION ANOMALY
# ==================================================

usual_location = (
    normal
    .groupby("customer_id")["ip_country"]
    .agg(
        lambda x:
        x.mode().iloc[0]
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


# ==================================================
# 7. CATEGORY ANOMALY
# ==================================================

usual_category = (
    normal
    .groupby("customer_id")["merchant_category"]
    .agg(
        lambda x:
        x.mode().iloc[0]
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


# ==================================================
# 8. PAYMENT METHOD ANOMALY
# ==================================================

usual_payment = (
    normal
    .groupby("customer_id")["payment_method"]
    .agg(
        lambda x:
        x.mode().iloc[0]
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


# ==================================================
# 9. TIME DEVIATION
# ==================================================

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


# ==================================================
# 10. TRANSACTION VELOCITY
# ==================================================

print(
    "Calculating transaction velocity..."
)

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


# ==================================================
# 11. SPENDING VELOCITY
# ==================================================

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


# ==================================================
# 12. FAILED ATTEMPTS
# ==================================================

print(
    "Calculating failed attempts..."
)

df["failed_flag"] = (
    df["transaction_status"]
    == "failed"
).astype(int)


df[
    "failed_attempts_before_success"
] = (

    df
    .groupby("customer_id")["failed_flag"]
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


# ==================================================
# 13. DEVICE SHARING
# ==================================================

print(
    "Calculating device sharing..."
)

device_accounts = (
    df
    .groupby("device_id")["customer_id"]
    .nunique()
)

df["device_account_count"] = (
    df["device_id"]
    .map(device_accounts)
)


# ==================================================
# 14. BEHAVIOR DEVIATION SCORE
# ==================================================

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


# ==================================================
# 15. MODEL FEATURES
# ==================================================

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


# ==================================================
# 16. TRAIN / TEST
# ==================================================

X_train, X_test, y_train, y_test = (

    train_test_split(

        X,

        y,

        test_size=0.2,

        random_state=42,

        stratify=y
    )
)


# ==================================================
# 17. MODEL
# ==================================================

print("Training model...")

model = RandomForestClassifier(

    n_estimators=100,

    max_depth=10,

    random_state=42,

    class_weight="balanced",

    n_jobs=-1
)


model.fit(
    X_train,
    y_train
)


# ==================================================
# 18. FIND HIGH-RISK TRANSACTION
# ==================================================

print(
    "Finding interesting transaction..."
)

probabilities = (

    model
    .predict_proba(X_test)[:, 1]
)


highest_risk_position = (
    probabilities.argmax()
)


# Model-only transaction

transaction = (
    X_test
    .iloc[highest_risk_position]
)


# Get original dataframe row

transaction_index = (
    X_test.index[
        highest_risk_position
    ]
)


# Full transaction information

full_transaction = (
    df.loc[
        transaction_index
    ].copy()
)


risk_probability = (
    probabilities[
        highest_risk_position
    ]
)


risk_score = (
    risk_probability * 100
)


# ==================================================
# 19. SHAP
# ==================================================

print(
    "Running SHAP explanation..."
)

explainer = shap.TreeExplainer(
    model
)

shap_values = (
    explainer.shap_values(
        transaction.to_frame().T
    )
)


# ==================================================
# 20. SHAP OUTPUT
# ==================================================

if isinstance(
    shap_values,
    list
):

    values = (
        shap_values[1][0]
    )

else:

    values = (
        shap_values[0]
    )

    if len(values.shape) > 1:

        values = values[:, 1]


# ==================================================
# 21. EXPLANATION TABLE
# ==================================================

explanation = pd.DataFrame({

    "feature": features,

    "value": transaction.values,

    "impact": values

})


explanation[
    "absolute_impact"
] = (
    explanation["impact"]
    .abs()
)


explanation = (
    explanation
    .sort_values(
        "absolute_impact",
        ascending=False
    )
)


# ==================================================
# 22. INVESTIGATION OUTPUT
# ==================================================

print()

print("=" * 60)

print(
    "        SHIELD-AI TRANSACTION INVESTIGATION"
)

print("=" * 60)

print(
    f"\nRisk Score: "
    f"{risk_score:.2f}/100"
)


if risk_score >= 70:

    print(
        "Risk Level: HIGH"
    )

elif risk_score >= 40:

    print(
        "Risk Level: MEDIUM"
    )

else:

    print(
        "Risk Level: LOW"
    )


print()

print(
    "TOP MODEL EXPLANATIONS"
)

print("-" * 60)


for _, row in (
    explanation.head(5).iterrows()
):

    if row["impact"] > 0:

        direction = (
            "INCREASES RISK"
        )

    else:

        direction = (
            "REDUCES RISK"
        )


    print(

        f"{row['feature']:<35}"

        f"{row['value']:.2f}   "

        f"{direction}"

    )


# ==================================================
# 23. HUMAN-READABLE EXPLANATION
# ==================================================

explanations = (
    generate_explanations(
        full_transaction
    )
)

print_explanations(
    explanations
)


# ==================================================
# 24. BEHAVIOR COMPARISON
# ==================================================

comparison = (
    create_behavior_comparison(
        full_transaction
    )
)

print_behavior_comparison(
    comparison
)


# ==================================================
# 25. COMPLETE
# ==================================================

print()

print(
    "Investigation complete."
)