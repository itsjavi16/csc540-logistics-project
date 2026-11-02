"""Published, read-only performance reports (Viewer).

Date ranges filter on:
  - delivery date (the DELIVERED scan) for on-time and running-total reports
  - departure date for lane volume and top departures
"""

from datetime import date

from src.db.helpers import fetch_all
from src.reports.common import dwell_time  # noqa: F401  (re-exported for the Viewer page)

_DELIVERED = """
    SELECT s.shipment_id, s.origin_hub, s.destination_hub, s.weight, s.on_time_outcome,
           e.`timestamp` AS delivered_at, v.carrier_id
    FROM Shipment s
    JOIN ScanEvent e ON e.shipment_id = s.shipment_id AND e.shipment_status = 'DELIVERED'
    JOIN Booking b   ON b.shipment_id = s.shipment_id
    JOIN Departure d ON d.departure_id = b.departure_id
    JOIN Vehicle v   ON v.vehicle_id = d.vehicle_id
    WHERE DATE(e.`timestamp`) BETWEEN %s AND %s
"""


def on_time_by_lane(start_date, end_date):
    return fetch_all(
        f"""WITH delivered AS ({_DELIVERED})
            SELECT origin_hub, destination_hub,
                   COUNT(*) AS delivered,
                   SUM(on_time_outcome = 'ON_TIME') AS on_time,
                   SUM(on_time_outcome = 'LATE') AS late,
                   ROUND(100 * SUM(on_time_outcome = 'ON_TIME') / COUNT(*), 1) AS on_time_pct,
                   ROUND(100 * SUM(on_time_outcome = 'LATE') / COUNT(*), 1) AS late_pct
            FROM delivered
            GROUP BY origin_hub, destination_hub
            ORDER BY origin_hub, destination_hub""",
        (start_date, end_date),
    )


def on_time_by_carrier(start_date, end_date):
    """Each carrier's on-time rate, ranked best first."""
    return fetch_all(
        f"""WITH delivered AS ({_DELIVERED}),
            rates AS (
                SELECT carrier_id, COUNT(*) AS delivered,
                       SUM(on_time_outcome = 'ON_TIME') AS on_time,
                       SUM(on_time_outcome = 'LATE') AS late,
                       ROUND(100 * SUM(on_time_outcome = 'ON_TIME') / COUNT(*), 1) AS on_time_pct
                FROM delivered GROUP BY carrier_id
            )
            SELECT RANK() OVER (ORDER BY r.on_time_pct DESC) AS carrier_rank,
                   cc.carrier_id, cc.company_name, r.delivered, r.on_time, r.late, r.on_time_pct
            FROM rates r JOIN CarrierCompany cc ON cc.carrier_id = r.carrier_id
            ORDER BY carrier_rank, cc.carrier_id""",
        (start_date, end_date),
    )


def lane_volume_ranking(start_date, end_date):
    """Lanes ranked by total booked shipment weight on departures in the period."""
    return fetch_all(
        """WITH carried AS (
               SELECT d.origin_hub, d.destination_hub,
                      COUNT(*) AS shipments, SUM(s.weight) AS total_kg
               FROM Booking b
               JOIN Departure d ON d.departure_id = b.departure_id
               JOIN Shipment s  ON s.shipment_id = b.shipment_id
               WHERE DATE(d.departure_datetime) BETWEEN %s AND %s
               GROUP BY d.origin_hub, d.destination_hub
           )
           SELECT RANK() OVER (ORDER BY total_kg DESC) AS lane_rank,
                  origin_hub, destination_hub, shipments, total_kg
           FROM carried
           ORDER BY lane_rank, origin_hub, destination_hub""",
        (start_date, end_date),
    )


def top_departures_per_lane(start_date, end_date, top_n):
    """Within each lane, departures ranked by booked load; top N per lane."""
    return fetch_all(
        """WITH ranked AS (
               SELECT d.origin_hub, d.destination_hub, d.departure_id, d.departure_datetime,
                      dl.booked_weight, dl.max_weight,
                      RANK() OVER (PARTITION BY d.origin_hub, d.destination_hub
                                   ORDER BY dl.booked_weight DESC) AS lane_rank
               FROM Departure d
               JOIN DepartureLoad dl ON dl.departure_id = d.departure_id
               WHERE DATE(d.departure_datetime) BETWEEN %s AND %s
           )
           SELECT origin_hub, destination_hub, lane_rank, departure_id, departure_datetime,
                  booked_weight, max_weight
           FROM ranked
           WHERE lane_rank <= %s
           ORDER BY origin_hub, destination_hub, lane_rank, departure_id""",
        (start_date, end_date, int(top_n)),
    )


def running_total_deliveries(start_date, end_date, carrier_id=None):
    """Cumulative delivered shipments (and kg) per carrier, day by day."""
    return fetch_all(
        f"""WITH delivered AS ({_DELIVERED}),
            daily AS (
                SELECT carrier_id, DATE(delivered_at) AS delivery_date,
                       COUNT(*) AS delivered, SUM(weight) AS kg
                FROM delivered
                WHERE (%s IS NULL OR carrier_id = %s)
                GROUP BY carrier_id, delivery_date
            )
            SELECT cc.carrier_id, cc.company_name, d.delivery_date, d.delivered, d.kg,
                   SUM(d.delivered) OVER w AS cumulative_delivered,
                   SUM(d.kg)        OVER w AS cumulative_kg
            FROM daily d JOIN CarrierCompany cc ON cc.carrier_id = d.carrier_id
            WINDOW w AS (PARTITION BY d.carrier_id ORDER BY d.delivery_date ROWS UNBOUNDED PRECEDING)
            ORDER BY cc.carrier_id, d.delivery_date""",
        (start_date, end_date, carrier_id, carrier_id),
    )


def at_risk_in_transit(n_days, as_of=None):
    """All in-transit shipments whose promised date has passed or is within n days."""
    as_of = as_of or date.today()
    return fetch_all(
        """SELECT s.shipment_id, s.shipper_id, s.origin_hub, s.destination_hub, s.promised_delivery,
                  DATEDIFF(s.promised_delivery, %s) AS days_left, s.current_status, b.departure_id
           FROM Shipment s LEFT JOIN Booking b ON b.shipment_id = s.shipment_id
           WHERE s.current_status <> 'DELIVERED'
             AND s.promised_delivery <= %s + INTERVAL %s DAY
           ORDER BY s.promised_delivery, s.shipment_id""",
        (as_of, as_of, int(n_days)),
    )
