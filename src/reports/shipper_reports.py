"""Shipper reports. Every query is limited to the logged-in shipper's shipments.

"In transit" follows the spec: a shipment with no delivering scan yet is
still in transit, so it means any status other than DELIVERED."""

from datetime import date

from src.db.helpers import fetch_all, fetch_one
from src.reports.common import pct


def on_time_summary(shipper_id, start_date, end_date):
    """Counts and percentages of on-time vs. late deliveries, by delivery date."""
    row = fetch_one(
        """SELECT COUNT(*) AS delivered,
                  COALESCE(SUM(s.on_time_outcome = 'ON_TIME'), 0) AS on_time,
                  COALESCE(SUM(s.on_time_outcome = 'LATE'), 0) AS late
           FROM Shipment s
           JOIN ScanEvent e ON e.shipment_id = s.shipment_id AND e.shipment_status = 'DELIVERED'
           WHERE s.shipper_id = %s AND DATE(e.`timestamp`) BETWEEN %s AND %s""",
        (shipper_id, start_date, end_date),
    )
    row["on_time_pct"] = pct(row["on_time"], row["delivered"])
    row["late_pct"] = pct(row["late"], row["delivered"])
    return row


def in_transit(shipper_id):
    return fetch_all(
        """SELECT s.shipment_id, s.origin_hub, s.destination_hub, s.weight, s.promised_delivery,
                  s.current_status, b.departure_id
           FROM Shipment s LEFT JOIN Booking b ON b.shipment_id = s.shipment_id
           WHERE s.shipper_id = %s AND s.current_status <> 'DELIVERED'
           ORDER BY s.promised_delivery, s.shipment_id""",
        (shipper_id,),
    )


def near_promise_date(shipper_id, n_days, as_of=None):
    """In-transit shipments whose promised date has passed or is within the next n days."""
    as_of = as_of or date.today()
    return fetch_all(
        """SELECT s.shipment_id, s.origin_hub, s.destination_hub, s.promised_delivery,
                  DATEDIFF(s.promised_delivery, %s) AS days_left, s.current_status, b.departure_id
           FROM Shipment s LEFT JOIN Booking b ON b.shipment_id = s.shipment_id
           WHERE s.shipper_id = %s AND s.current_status <> 'DELIVERED'
             AND s.promised_delivery <= %s + INTERVAL %s DAY
           ORDER BY s.promised_delivery, s.shipment_id""",
        (as_of, shipper_id, as_of, int(n_days)),
    )
