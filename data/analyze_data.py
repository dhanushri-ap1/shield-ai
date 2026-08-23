import pandas as pd

df = pd.read_csv("data/raw/transactions.csv")

# Create useful features

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


print("Total transactions:", len(df))

print("\nFraud transactions:", df["is_fraud"].sum())

print("\nFeature summary:")
print(
    df[
        [
            "amount",
            "is_odd_hour",
            "is_foreign",
            "is_unknown_device",
            "is_fraud"
        ]
    ].head(10)
)