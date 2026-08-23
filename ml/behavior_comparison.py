def create_behavior_comparison(transaction):

    comparison = []

    # ----------------------------------------------
    # TRANSACTION AMOUNT
    # ----------------------------------------------

    normal_amount = (
        transaction["amount"] /
        max(transaction["amount_ratio"], 0.01)
    )

    comparison.append({

        "signal": "Transaction Amount",

        "normal": f"₹{normal_amount:.0f}",

        "current": f"₹{transaction['amount']:.0f}",

        "status": (
            "ANOMALY"
            if transaction["amount_ratio"] >= 3
            else "NORMAL"
        )
    })

    # ----------------------------------------------
    # DEVICE
    # ----------------------------------------------

    comparison.append({

        "signal": "Device",

        "normal": "Known device",

        "current": (
            "New device"
            if transaction["is_new_device"] == 1
            else "Known device"
        ),

        "status": (
            "ANOMALY"
            if transaction["is_new_device"] == 1
            else "NORMAL"
        )
    })

    # ----------------------------------------------
    # LOCATION
    # ----------------------------------------------

    comparison.append({

        "signal": "Location",

        "normal": "Usual location",

        "current": (
            "New location"
            if transaction["is_new_location"] == 1
            else "Usual location"
        ),

        "status": (
            "ANOMALY"
            if transaction["is_new_location"] == 1
            else "NORMAL"
        )
    })

    # ----------------------------------------------
    # TRANSACTION TIME
    # ----------------------------------------------

    comparison.append({

        "signal": "Transaction Time",

        "normal": (
            f"Around {int(transaction['usual_hour'])}:00"
        ),

        "current": (
            f"{int(transaction['hour'])}:00"
        ),

        "status": (
            "ANOMALY"
            if transaction["is_odd_hour"] == 1
            else "NORMAL"
        )
    })

    # ----------------------------------------------
    # MERCHANT CATEGORY
    # ----------------------------------------------

    comparison.append({

        "signal": "Merchant Category",

        "normal": "Usual category",

        "current": (
            "New category"
            if transaction["is_new_category"] == 1
            else "Usual category"
        ),

        "status": (
            "ANOMALY"
            if transaction["is_new_category"] == 1
            else "NORMAL"
        )
    })

    # ----------------------------------------------
    # PAYMENT METHOD
    # ----------------------------------------------

    comparison.append({

        "signal": "Payment Method",

        "normal": "Usual method",

        "current": (
            "New method"
            if transaction["is_new_payment_method"] == 1
            else "Usual method"
        ),

        "status": (
            "ANOMALY"
            if transaction["is_new_payment_method"] == 1
            else "NORMAL"
        )
    })

    # ----------------------------------------------
    # TRANSACTION VELOCITY
    # ----------------------------------------------

    velocity = transaction[
        "transactions_last_10min"
    ]

    comparison.append({

        "signal": "10-Minute Activity",

        "normal": "Low activity",

        "current": (
            f"{int(velocity)} transactions"
        ),

        "status": (
            "ANOMALY"
            if velocity >= 3
            else "NORMAL"
        )
    })

    return comparison


def print_behavior_comparison(comparison):

    print()
    print("=" * 80)
    print("                    BEHAVIOR COMPARISON")
    print("=" * 80)

    print(
        f"{'SIGNAL':<25}"
        f"{'NORMAL':<20}"
        f"{'CURRENT':<20}"
        f"STATUS"
    )

    print("-" * 80)

    for item in comparison:

        print(
            f"{item['signal']:<25}"
            f"{item['normal']:<20}"
            f"{item['current']:<20}"
            f"{item['status']}"
        )

    print("=" * 80)