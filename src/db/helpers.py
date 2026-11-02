"""
Small helpers every data-layer module uses.

- fetch_all / fetch_one: run a SELECT and return rows as dicts.
- run_write: run one or more statements in a single transaction.
- Result: what every write function returns, so the UI can show
  `result.message` without knowing anything about SQL.
- friendly_error: turns MariaDB errors (including the plain-English
  messages our triggers raise) into text a user can read.
"""

from dataclasses import dataclass, field
from typing import Any

import pymysql

from src.db.connection import get_connection


@dataclass
class Result:
    ok: bool
    message: str
    data: Any = field(default=None)


def fetch_all(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return list(cur.fetchall())
    finally:
        conn.close()


def fetch_one(sql, params=None):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def run_write(statements, success_message):
    """Run [(sql, params), ...] in one transaction. Returns a Result."""
    conn = get_connection()
    try:
        last_id = None
        with conn.cursor() as cur:
            for sql, params in statements:
                cur.execute(sql, params)
                last_id = cur.lastrowid or last_id
        conn.commit()
        return Result(True, success_message, last_id)
    except pymysql.MySQLError as e:
        conn.rollback()
        return Result(False, friendly_error(e))
    finally:
        conn.close()


# Constraint names from the DDL -> what to tell the user.
_CHECK_MESSAGES = {
    "chk_hub_id_format": "Hub IDs are three capital letters, e.g. RDU.",
    "chk_lane_hubs_distinct": "Origin and destination must be different hubs.",
    "chk_departure_max_weight_positive": "Capacity must be greater than 0.",
    "chk_shipment_weight_positive": "Weight must be greater than 0.",
    "chk_refrigeratedvan_temp_range": "Minimum temperature can't be above the maximum.",
    "chk_scanevent_seq_positive": "Scan sequence numbers start at 1.",
    "chk_shipment_outcome_only_when_delivered": "On-time/late is only recorded for delivered shipments.",
}

_FK_MESSAGES = {
    "fk_shipment_lane": "That origin/destination pair isn't a lane in the network.",
    "fk_departure_lane": "That origin/destination pair isn't a lane in the network.",
    "fk_vehicle_home_hub": "That home hub doesn't exist.",
    "fk_scanevent_hub": "That hub doesn't exist.",
    "fk_departure_vehicle": "That vehicle doesn't exist.",
    "fk_booking_departure": "That departure doesn't exist.",
}


def friendly_error(e):
    code = e.args[0] if e.args else None
    text = str(e.args[1]) if len(e.args) > 1 else str(e)
    if code == 1644:  # SIGNAL from one of our triggers: message is already user-facing
        return text
    if code == 4025:  # CHECK constraint
        for name, msg in _CHECK_MESSAGES.items():
            if name in text:
                return msg
        return "That value isn't allowed."
    if code == 1452:  # foreign key: referenced row missing
        for name, msg in _FK_MESSAGES.items():
            if name in text:
                return msg
        return "That refers to something that doesn't exist."
    if code == 1451:
        return "That record is still in use and can't be changed or removed."
    if code == 1062:
        if "uq_departure_vehicle_time" in text:
            return "That vehicle already has a departure at that date and time."
        if "PRIMARY" in text:
            return "That ID is already taken."
        return "That value is already taken."
    if code in (1265, 1366):
        return "One of the values has the wrong format."
    if code in (2003, 2013):
        return "Can't reach the database server (are you on the campus VPN?)."
    return f"Database error {code}: {text}"
