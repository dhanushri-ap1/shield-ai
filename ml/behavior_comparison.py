def _num(transaction, key, default=0.0):
    try:
        value = transaction[key]
    except Exception:
        return default

    if value is None:
        return default

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _text(transaction, key, default="Unknown"):
    try:
        value = transaction[key]
    except Exception:
        return default

    if value is None:
        return default

    text = str(value).strip()
    return text if text and text.lower() != "nan" else default


def _signal(signal, normal, current, status, insight):
    return {
        "signal": signal,
        "normal": normal,
        "current": current,
        "status": status,
        "insight": insight,
    }


def create_behavior_comparison(transaction):
    """
    Investigator-facing comparison of this payment vs the
    customer's usual pattern. Includes insight copy so the
    UI is not a dump of raw JSON-like rows.
    """

    signals = []

    amount = _num(transaction, "amount")
    amount_ratio = max(_num(transaction, "amount_ratio", 1.0), 0.01)
    usual_amount = amount / amount_ratio
    amount_delta = amount - usual_amount
    amount_pct = (amount_ratio - 1) * 100

    if amount_ratio >= 3:
        amount_status = "ANOMALY"
        amount_insight = (
            f"₹{amount:,.0f} is {amount_ratio:.1f}× the usual "
            f"₹{usual_amount:,.0f} — a sharp spike."
        )
    elif amount_ratio >= 1.8:
        amount_status = "WATCH"
        amount_insight = (
            f"₹{amount:,.0f} is {amount_ratio:.1f}× typical spend "
            f"(₹{usual_amount:,.0f}). Elevated, not extreme."
        )
    elif amount_ratio <= 0.4 and amount > 0:
        amount_status = "WATCH"
        amount_insight = (
            f"₹{amount:,.0f} is well below the usual ₹{usual_amount:,.0f}. "
            "Small tickets can be card-testing."
        )
    else:
        amount_status = "NORMAL"
        direction = "above" if amount_delta >= 0 else "below"
        amount_insight = (
            f"₹{abs(amount_delta):,.0f} {direction} typical spend "
            f"({abs(amount_pct):.0f}%). Within normal variation."
        )

    signals.append(_signal(
        "Transaction amount",
        f"Usually about ₹{usual_amount:,.0f}",
        f"₹{amount:,.0f} this time",
        amount_status,
        amount_insight,
    ))

    is_new_device = _num(transaction, "is_new_device") == 1
    usual_device = _text(transaction, "usual_device", "their usual device")
    current_device = _text(transaction, "device_id", "this device")

    if is_new_device:
        signals.append(_signal(
            "Device",
            f"Usually {usual_device}",
            f"New device {current_device}",
            "ANOMALY",
            "This device has not been this customer's normal checkout device.",
        ))
    else:
        signals.append(_signal(
            "Device",
            "Known device",
            current_device,
            "NORMAL",
            "Paid from a device already associated with this customer.",
        ))

    is_new_location = _num(transaction, "is_new_location") == 1
    usual_location = _text(transaction, "usual_location", "their usual country")
    current_location = _text(
        transaction,
        "ip_country",
        _text(transaction, "country", "Unknown"),
    )

    if is_new_location:
        signals.append(_signal(
            "Location",
            f"Usually {usual_location}",
            current_location,
            "ANOMALY",
            f"Country/network jumped from {usual_location} to {current_location}.",
        ))
    else:
        signals.append(_signal(
            "Location",
            f"Usually {usual_location}",
            current_location,
            "NORMAL",
            "Location matches this customer's established geography.",
        ))

    hour = int(_num(transaction, "hour"))
    usual_hour = int(round(_num(transaction, "usual_hour")))
    time_deviation = _num(transaction, "time_deviation")
    is_odd_hour = _num(transaction, "is_odd_hour") == 1

    if is_odd_hour:
        time_status = "ANOMALY"
        time_insight = (
            f"Overnight payment at {hour:02d}:00 (high-risk window). "
            f"This customer is usually active around {usual_hour:02d}:00."
        )
    elif time_deviation >= 6:
        time_status = "ANOMALY"
        time_insight = (
            f"{time_deviation:.0f} hours away from their usual "
            f"{usual_hour:02d}:00 window."
        )
    elif time_deviation >= 3:
        time_status = "WATCH"
        time_insight = (
            f"About {time_deviation:.0f} hours off their usual "
            f"{usual_hour:02d}:00 habit — notable, not decisive."
        )
    else:
        time_status = "NORMAL"
        time_insight = (
            f"{hour:02d}:00 is close to their usual {usual_hour:02d}:00 window."
        )

    signals.append(_signal(
        "Time of day",
        f"Usually around {usual_hour:02d}:00",
        f"{hour:02d}:00 this time",
        time_status,
        time_insight,
    ))

    is_new_category = _num(transaction, "is_new_category") == 1
    usual_category = _text(transaction, "usual_category", "their usual category")
    current_category = _text(transaction, "merchant_category")

    if is_new_category:
        signals.append(_signal(
            "Merchant category",
            usual_category,
            current_category,
            "WATCH",
            f"First time (or rare) spend in {current_category}; they usually pay for {usual_category}.",
        ))
    else:
        signals.append(_signal(
            "Merchant category",
            usual_category,
            current_category,
            "NORMAL",
            f"In line with the categories this customer already uses ({current_category}).",
        ))

    is_new_method = _num(transaction, "is_new_payment_method") == 1
    usual_method = _text(
        transaction,
        "usual_payment_method",
        "their usual method",
    )
    current_method = _text(transaction, "payment_method")

    if is_new_method:
        signals.append(_signal(
            "Payment method",
            usual_method,
            current_method,
            "WATCH",
            f"Switched from {usual_method} to {current_method}.",
        ))
    else:
        signals.append(_signal(
            "Payment method",
            usual_method,
            current_method,
            "NORMAL",
            f"Using {current_method}, which they already use.",
        ))

    velocity = int(_num(transaction, "transactions_last_10min"))

    if velocity >= 5:
        velocity_status = "ANOMALY"
        velocity_insight = (
            f"{velocity} other payments in 10 minutes — a burst, not browsing."
        )
    elif velocity >= 3:
        velocity_status = "WATCH"
        velocity_insight = (
            f"{velocity} other payments in the last 10 minutes."
        )
    elif velocity == 0:
        velocity_status = "NORMAL"
        velocity_insight = (
            "No other payments in the last 10 minutes. Not a velocity attack."
        )
    else:
        velocity_status = "NORMAL"
        velocity_insight = (
            f"{velocity} nearby payment(s) in 10 minutes — still a quiet session."
        )

    signals.append(_signal(
        "Last 10 minutes",
        "Typically quiet",
        (
            "No other transactions"
            if velocity == 0
            else f"{velocity} other transaction(s)"
        ),
        velocity_status,
        velocity_insight,
    ))

    failed = int(_num(transaction, "failed_attempts_before_success"))
    if failed >= 3:
        signals.append(_signal(
            "Failed attempts",
            "Clean checkout",
            f"{failed} failures before success",
            "ANOMALY",
            "Repeated failures then a success often means testing stolen credentials.",
        ))
    elif failed >= 1:
        signals.append(_signal(
            "Failed attempts",
            "Clean checkout",
            f"{failed} failure(s) before success",
            "WATCH",
            "There was friction immediately before this payment went through.",
        ))
    else:
        signals.append(_signal(
            "Failed attempts",
            "Clean checkout",
            "Succeeded first time",
            "NORMAL",
            "No failed attempts immediately before this payment.",
        ))

    anomaly_count = sum(1 for item in signals if item["status"] == "ANOMALY")
    watch_count = sum(1 for item in signals if item["status"] == "WATCH")

    if anomaly_count:
        summary = (
            f"{anomaly_count} clear break(s) from this customer's normal "
            f"behaviour"
            + (
                f", plus {watch_count} weaker difference(s)."
                if watch_count
                else "."
            )
        )
    elif watch_count:
        summary = (
            f"No hard red flags. {watch_count} milder difference(s) from "
            "baseline — review in context of the model score."
        )
    else:
        summary = (
            "This payment looks like this customer's usual pattern. "
            "If it was still scored as risky, the model is using a mix "
            "of weaker signals rather than one obvious anomaly."
        )

    return {
        "summary": summary,
        "anomaly_count": anomaly_count,
        "watch_count": watch_count,
        "signals": signals,
    }


def print_behavior_comparison(comparison):

    print()
    print("=" * 80)
    print("                    BEHAVIOR COMPARISON")
    print("=" * 80)

    if isinstance(comparison, dict):
        summary = comparison.get("summary", "")
        rows = comparison.get("signals", [])
        if summary:
            print(summary)
            print("-" * 80)
    else:
        rows = comparison or []

    print(
        f"{'SIGNAL':<22}"
        f"{'NORMAL':<28}"
        f"{'CURRENT':<28}"
        f"STATUS"
    )
    print("-" * 80)

    for item in rows:
        print(
            f"{item['signal']:<22}"
            f"{str(item['normal'])[:26]:<28}"
            f"{str(item['current'])[:26]:<28}"
            f"{item['status']}"
        )
        insight = item.get("insight")
        if insight:
            print(f"  → {insight}")

    print("=" * 80)
