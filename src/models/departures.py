"""Carrier actions on departures. A carrier operates a departure when the
departure's vehicle belongs to the carrier's company."""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from src.db.helpers import Result, fetch_all, fetch_one, run_write
from src.models.hubs import check_lane


def _owns_vehicle(carrier_id, vehicle_id):
    return fetch_one("SELECT 1 AS x FROM Vehicle WHERE vehicle_id = %s AND carrier_id = %s",
                     (vehicle_id, carrier_id)) is not None


def _check(carrier_id, vehicle_id, origin_hub, destination_hub, departure_datetime, max_weight):
    if vehicle_id is None or not _owns_vehicle(carrier_id, vehicle_id):
        return f"Vehicle {vehicle_id} doesn't exist or isn't yours.", None
    err = check_lane(origin_hub, destination_hub)
    if err:
        return err, None
    if not isinstance(departure_datetime, datetime):
        return "Enter a valid departure date and time.", None
    try:
        cap = Decimal(str(max_weight))
    except (InvalidOperation, ValueError):
        return "Capacity must be a number.", None
    if cap <= 0:
        return "Capacity must be greater than 0.", None
    return None, cap


def schedule_departure(carrier_id, vehicle_id, origin_hub, destination_hub, departure_datetime, max_weight):
    err, cap = _check(carrier_id, vehicle_id, origin_hub, destination_hub, departure_datetime, max_weight)
    if err:
        return Result(False, err)
    res = run_write(
        [("""INSERT INTO Departure (vehicle_id, origin_hub, destination_hub, departure_datetime, max_weight)
             VALUES (%s, %s, %s, %s, %s)""",
          (vehicle_id, origin_hub, destination_hub, departure_datetime, cap))],
        "Departure scheduled.",
    )
    if res.ok:
        res.message = f"Departure {res.data} scheduled: {origin_hub} -> {destination_hub}, {cap} kg capacity."
    return res


def get_owned_departure(carrier_id, departure_id):
    return fetch_one(
        """SELECT d.departure_id, d.vehicle_id, d.origin_hub, d.destination_hub,
                  d.departure_datetime, d.max_weight, dl.booked_weight, dl.remaining_weight
           FROM Departure d
           JOIN Vehicle v        ON v.vehicle_id = d.vehicle_id
           JOIN DepartureLoad dl ON dl.departure_id = d.departure_id
           WHERE d.departure_id = %s AND v.carrier_id = %s""",
        (departure_id, carrier_id),
    )


def update_departure(carrier_id, departure_id, vehicle_id, origin_hub, destination_hub,
                     departure_datetime, max_weight):
    """trg_departure_guard rejects capacity below the booked load and lane
    changes once shipments are booked; its message comes back in the Result."""
    if get_owned_departure(carrier_id, departure_id) is None:
        return Result(False, f"Departure {departure_id} doesn't exist or isn't yours.")
    err, cap = _check(carrier_id, vehicle_id, origin_hub, destination_hub, departure_datetime, max_weight)
    if err:
        return Result(False, err)
    return run_write(
        [("""UPDATE Departure
             SET vehicle_id = %s, origin_hub = %s, destination_hub = %s,
                 departure_datetime = %s, max_weight = %s
             WHERE departure_id = %s""",
          (vehicle_id, origin_hub, destination_hub, departure_datetime, cap, departure_id))],
        f"Departure {departure_id} updated.",
    )


def list_departures(carrier_id):
    return fetch_all(
        """SELECT d.departure_id, d.vehicle_id, v.vehicle_type, d.origin_hub, d.destination_hub,
                  d.departure_datetime, dl.max_weight, dl.booked_weight, dl.remaining_weight
           FROM Departure d
           JOIN Vehicle v        ON v.vehicle_id = d.vehicle_id
           JOIN DepartureLoad dl ON dl.departure_id = d.departure_id
           WHERE v.carrier_id = %s
           ORDER BY d.departure_datetime""",
        (carrier_id,),
    )
