# Shipper actions: create, update, book and track shipments

from decimal import Decimal, InvalidOperation

import pymysql

from src.db.connection import get_connection
from src.db.helpers import Result, fetch_all, fetch_one, friendly_error, run_write
from src.models.hubs import check_lane


def _check_weight(weight):
    try:
        w = Decimal(str(weight))
    except (InvalidOperation, ValueError):
        return None, "Weight must be a number."
    if w <= 0:
        return None, "Weight must be greater than 0."
    return w, None


def create_shipment(shipper_id, origin_hub, destination_hub, weight, promised_delivery):
    err = check_lane(origin_hub, destination_hub)
    if err:
        return Result(False, err)
    w, err = _check_weight(weight)
    if err:
        return Result(False, err)
    if promised_delivery is None:
        return Result(False, "Enter a promised delivery date.")
    res = run_write(
        [
            (
                """INSERT INTO Shipment (user_id, origin_hub, destination_hub, weight, promised_delivery)
             VALUES (%s, %s, %s, %s, %s)""",
                (shipper_id, origin_hub, destination_hub, w, promised_delivery),
            )
        ],
        "Shipment created.",
    )
    if res.ok:
        res.message = f"Shipment {res.data} created."
    return res


def get_owned_shipment(shipper_id, shipment_id):
    return fetch_one(
        """SELECT shipment_id, user_id, origin_hub, destination_hub, weight,
                  promised_delivery, current_status, on_time_outcome
           FROM Shipment WHERE shipment_id = %s AND user_id = %s""",
        (shipment_id, shipper_id),
    )


def update_shipment(
    shipper_id, shipment_id, origin_hub, destination_hub, weight, promised_delivery
):
    if get_owned_shipment(shipper_id, shipment_id) is None:
        return Result(False, f"Shipment {shipment_id} doesn't exist or isn't yours.")
    err = check_lane(origin_hub, destination_hub)
    if err:
        return Result(False, err)
    w, err = _check_weight(weight)
    if err:
        return Result(False, err)
    if promised_delivery is None:
        return Result(False, "Enter a promised delivery date.")
    return run_write(
        [
            (
                """UPDATE Shipment
             SET origin_hub = %s, destination_hub = %s, weight = %s, promised_delivery = %s
             WHERE shipment_id = %s AND user_id = %s""",
                (
                    origin_hub,
                    destination_hub,
                    w,
                    promised_delivery,
                    shipment_id,
                    shipper_id,
                ),
            )
        ],
        f"Shipment {shipment_id} updated.",
    )


def list_shipper_shipments(shipper_id):
    return fetch_all(
        """SELECT s.shipment_id, s.origin_hub, s.destination_hub, s.weight, s.promised_delivery,
                  s.current_status, s.on_time_outcome, b.departure_id
           FROM Shipment s
           LEFT JOIN Booking b ON b.shipment_id = s.shipment_id
           WHERE s.user_id = %s
           ORDER BY s.shipment_id""",
        (shipper_id,),
    )


def eligible_departures(shipment_id):
    return fetch_all(
        """SELECT d.departure_id, d.origin_hub, d.destination_hub, d.departure_datetime,
                  dl.max_weight, dl.booked_weight, dl.remaining_weight
           FROM Shipment s
           JOIN Departure d      ON d.origin_hub = s.origin_hub AND d.destination_hub = s.destination_hub
           JOIN DepartureLoad dl ON dl.departure_id = d.departure_id
           WHERE s.shipment_id = %s AND dl.remaining_weight >= s.weight
           ORDER BY d.departure_datetime""",
        (shipment_id,),
    )


def book_shipment(shipper_id, shipment_id, departure_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "CALL book_shipment(%s, %s, %s, @ok, @msg)",
                (shipment_id, departure_id, shipper_id),
            )
            cur.execute("SELECT @ok AS ok, @msg AS msg")
            row = cur.fetchone()
        if row is None:
            conn.rollback()
            return Result(False, "Booking failed: no result returned.")
        conn.commit()
        return Result(bool(row.get("ok")), row.get("msg", "Booking failed."))
    except pymysql.MySQLError as e:
        conn.rollback()
        return Result(False, friendly_error(e))
    finally:
        conn.close()


def get_shipment(shipment_id):
    return fetch_one(
        """SELECT s.shipment_id, s.user_id, s.origin_hub, s.destination_hub, s.weight,
                  s.promised_delivery, s.current_status, s.on_time_outcome, b.departure_id
           FROM Shipment s LEFT JOIN Booking b ON b.shipment_id = s.shipment_id
           WHERE s.shipment_id = %s""",
        (shipment_id,),
    )


def scan_history(shipment_id):
    return fetch_all(
        """SELECT e.scan_seq, e.`timestamp`, e.hub_id, h.name AS hub_name, e.shipment_status
           FROM ScanEvent e JOIN Hub h ON h.hub_id = e.hub_id
           WHERE e.shipment_id = %s
           ORDER BY e.scan_seq""",
        (shipment_id,),
    )
