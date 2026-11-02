"""Carrier reports, limited to departures run by the carrier's company and
the shipments booked on them."""

from src.db.helpers import fetch_all, fetch_one
from src.reports.common import dwell_time, pct


def load_per_departure(carrier_id, start_date, end_date):
    rows = fetch_all(
        """SELECT d.departure_id, d.vehicle_id, d.origin_hub, d.destination_hub, d.departure_datetime,
                  dl.max_weight, dl.booked_weight, dl.remaining_weight,
                  ROUND(100 * dl.booked_weight / dl.max_weight, 1) AS pct_full
           FROM Departure d
           JOIN Vehicle v        ON v.vehicle_id = d.vehicle_id
           JOIN DepartureLoad dl ON dl.departure_id = d.departure_id
           WHERE v.carrier_id = %s AND DATE(d.departure_datetime) BETWEEN %s AND %s
           ORDER BY d.departure_datetime""",
        (carrier_id, start_date, end_date),
    )
    return rows


def on_time_rate(carrier_id, start_date, end_date):
    """Delivered, on-time and late counts for shipments delivered in the period."""
    row = fetch_one(
        """SELECT COUNT(*) AS delivered,
                  COALESCE(SUM(s.on_time_outcome = 'ON_TIME'), 0) AS on_time,
                  COALESCE(SUM(s.on_time_outcome = 'LATE'), 0) AS late
           FROM Shipment s
           JOIN Booking b   ON b.shipment_id = s.shipment_id
           JOIN Departure d ON d.departure_id = b.departure_id
           JOIN Vehicle v   ON v.vehicle_id = d.vehicle_id
           JOIN ScanEvent e ON e.shipment_id = s.shipment_id AND e.shipment_status = 'DELIVERED'
           WHERE v.carrier_id = %s AND DATE(e.`timestamp`) BETWEEN %s AND %s""",
        (carrier_id, start_date, end_date),
    )
    row["on_time_rate_pct"] = pct(row["on_time"], row["delivered"])
    return row


def handled_shipment(carrier_id, shipment_id):
    """True if the shipment is booked on one of this carrier's departures."""
    return fetch_one(
        """SELECT 1 AS x FROM Booking b
           JOIN Departure d ON d.departure_id = b.departure_id
           JOIN Vehicle v   ON v.vehicle_id = d.vehicle_id
           WHERE b.shipment_id = %s AND v.carrier_id = %s""",
        (shipment_id, carrier_id),
    ) is not None


def carrier_dwell_time(carrier_id, shipment_id):
    """None if the carrier didn't handle the shipment, else the dwell rows."""
    if not handled_shipment(carrier_id, shipment_id):
        return None
    return dwell_time(shipment_id)
