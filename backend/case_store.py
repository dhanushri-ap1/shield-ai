"""
Lightweight persistence for investigator actions.

Shield-AI's model tells an investigator *why* a transaction was flagged.
This module stores what the investigator *did* about it: a status
(Mark Safe / Needs Review / Confirm Fraud) plus free-text notes, keyed
by transaction_id. Backed by a JSON file so decisions survive a
backend restart, with an in-memory fallback if the file can't be read.
"""

import json
import os
import threading
import datetime


STORE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "case_store.json",
)

VALID_STATUSES = {
    "unreviewed",
    "safe",
    "needs_review",
    "confirmed_fraud",
}

_lock = threading.Lock()


def _now():
    return datetime.datetime.now().isoformat(timespec="seconds")


def _empty_case(transaction_id):
    return {
        "transaction_id": transaction_id,
        "status": "unreviewed",
        "notes": [],
        "updated_at": None,
    }


def _load():
    if not os.path.exists(STORE_PATH):
        return {}

    try:
        with open(STORE_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(store):
    try:
        os.makedirs(os.path.dirname(STORE_PATH), exist_ok=True)
        with open(STORE_PATH, "w", encoding="utf-8") as handle:
            json.dump(store, handle, indent=2)
    except OSError:
        # Best-effort persistence — an investigator's in-session
        # actions should still work even if the disk write fails.
        pass


def get_case(transaction_id):
    with _lock:
        store = _load()
        return store.get(transaction_id, _empty_case(transaction_id))


def set_status(transaction_id, status):
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")

    with _lock:
        store = _load()
        case = store.get(transaction_id, _empty_case(transaction_id))
        case["status"] = status
        case["updated_at"] = _now()
        store[transaction_id] = case
        _save(store)
        return case


def add_note(transaction_id, note_text):
    note_text = (note_text or "").strip()

    if not note_text:
        raise ValueError("Note text is required")

    with _lock:
        store = _load()
        case = store.get(transaction_id, _empty_case(transaction_id))
        case["notes"].append({
            "text": note_text,
            "created_at": _now(),
        })
        case["updated_at"] = _now()
        store[transaction_id] = case
        _save(store)
        return case


def all_cases():
    with _lock:
        return _load()
