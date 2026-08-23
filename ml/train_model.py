import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report


# Load dataset
df = pd.read_csv("data/raw/transactions.csv")


# Create features
df["hour"] = pd.to_datetime(df["timestamp"]).dt.hour

df["is_odd_hour"] = (
    (df["hour"] >= 0) &
    (df["hour"] <= 5)
).astype(int)

df["is_foreign"] = (
    df["ip_country"] != "India"
).astype(int)

df["is_unknown_device"] = (
    df["device_id"].str.startswith("UNKNOWN")
).astype(int)


# Features used by the model
features = [
    "amount",
    "is_odd_hour",
    "is_foreign",
    "is_unknown_device"
]


X = df[features]
y = df["is_fraud"]


# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)


# Create model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)


# Train
model.fit(X_train, y_train)


# Predict
predictions = model.predict(X_test)


# Evaluate
print("\nModel Results:")
print(classification_report(y_test, predictions))