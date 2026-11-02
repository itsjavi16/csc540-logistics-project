"""Posting scan events (carrier). Chronology, status order and the
shipment's current status / on-time flag are enforced by the ScanEvent
triggers; this module checks the carrier is allowed to post the scan."""

from datetime import datetime

from src.db.helpers import Result, fetch_one, run_write

STATUSES = {
    "RECEIVED": "Received",
    "IN_TRANSIT": "In Transit",
    "ARRIVED_AT_HUB": "Arrived at Hub",
    "OUT_FOR_DELIVERY": "Out for Delivery",
    "DELIVERED": "Delivered",
}


def post_scan(carrier_id, shipment_id, departure_id, timestamp, hub_id, status):
    if status not in STATUSES:
        return Result(False, "Choose a valid status.")
    if not isinstance(timestamp, datetime):
        return Result(False, "Enter a valid timestamp.")

    dep = fetch_one(
        """SELECT d.departure_id FROM Departure d JOIN Vehicle v ON v.vehicle_id = d.vehicle_id
           WHERE d.departure_id = %s AND v.carrier_id = %s""",
        (departure_id, carrier_id),
    )
    if dep is None:
        return Result(False, f"Departure {departure_id} doesn't exist or isn't operated by your company.")

    booking = fetch_one("SELECT departure_id FROM Booking WHERE shipment_id = %s", (shipment_id,))
    if booking is None or booking["departure_id"] != departure_id:
        return Result(False, f"Shipment {shipment_id} isn't booked on departure {departure_id}.")

    res = run_write(
        [("""INSERT INTO ScanEvent (shipment_id, `timestamp`, hub_id, shipment_status)
             VALUES (%s, %s, %s, %s)""",
          (shipment_id, timestamp, hub_id, status))],
        "Scan recorded.",
    )
    if res.ok:
        s = fetch_one("SELECT current_status, on_time_outcome FROM Shipment WHERE shipment_id = %s", (shipment_id,))
        res.message = f"Scan recorded. Shipment {shipment_id} is now {STATUSES[s['current_status']]}"
        if s["on_time_outcome"]:
            res.message += f" ({'on time' if s['on_time_outcome'] == 'ON_TIME' else 'late'})"
        res.message += "."
    return res
