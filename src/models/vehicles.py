"""Carrier actions on vehicles. "Owned by the carrier" means owned by the
logged-in carrier's company (Vehicle.carrier_id = CarrierCompany.carrier_id)."""

import pymysql

from src.db.connection import get_connection
from src.db.helpers import Result, fetch_all, fetch_one, friendly_error, run_write
from src.models.hubs import hub_exists

TYPES = {
    "BOX_TRUCK": "Box Truck",
    "REFRIGERATED_VAN": "Refrigerated Van",
    "RAIL_CAR": "Rail Car",
}

# Type-specific table and columns: (column, label)
TYPE_DETAILS = {
    "BOX_TRUCK": ("BoxTruck", [("cargo_volume", "Cargo volume (m³)"),
                               ("gross_weight_rating", "Gross weight rating (kg)")]),
    "REFRIGERATED_VAN": ("RefrigeratedVan", [("temp_min", "Minimum temperature (°C)"),
                                             ("temp_max", "Maximum temperature (°C)"),
                                             ("payload_limit", "Payload limit (kg)")]),
    "RAIL_CAR": ("RailCar", [("axle_count", "Axle count"),
                             ("track_gauge", "Track gauge (mm)")]),
}


def check_new_vehicle(carrier_id, vehicle_id, home_hub_id, vehicle_type):
    """Validate the common details (first Add Vehicle page). Returns an error or None."""
    if vehicle_id is not None:
        if vehicle_id <= 0:
            return "Vehicle ID must be a positive number."
        if fetch_one("SELECT 1 AS x FROM Vehicle WHERE vehicle_id = %s", (vehicle_id,)):
            return f"Vehicle ID {vehicle_id} is already taken."
    if not hub_exists(home_hub_id):
        return f"Hub {home_hub_id} doesn't exist."
    if vehicle_type not in TYPES:
        return "Choose a vehicle type."
    return None


def _check_details(vehicle_type, details):
    for col, label in TYPE_DETAILS[vehicle_type][1]:
        v = details.get(col)
        if v is None:
            return f"Enter {label.lower()}."
        if col not in ("temp_min", "temp_max") and v <= 0:
            return f"{label} must be greater than 0."
    if vehicle_type == "RAIL_CAR" and int(details["axle_count"]) != details["axle_count"]:
        return "Axle count must be a whole number."
    return None


def add_vehicle(carrier_id, vehicle_id, home_hub_id, vehicle_type, details):
    """Insert the common row and the type-specific row in one transaction.
    vehicle_id may be None to let the database assign one."""
    err = check_new_vehicle(carrier_id, vehicle_id, home_hub_id, vehicle_type) or _check_details(vehicle_type, details)
    if err:
        return Result(False, err)
    table, cols = TYPE_DETAILS[vehicle_type]
    col_names = [c for c, _ in cols]

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO Vehicle (vehicle_id, carrier_id, home_hub_id, vehicle_type) VALUES (%s, %s, %s, %s)",
                (vehicle_id, carrier_id, home_hub_id, vehicle_type),
            )
            new_id = vehicle_id or cur.lastrowid
            cur.execute(
                f"INSERT INTO {table} (vehicle_id, {', '.join(col_names)}) "
                f"VALUES (%s, {', '.join(['%s'] * len(col_names))})",
                (new_id, *[details[c] for c in col_names]),
            )
        conn.commit()
        return Result(True, f"{TYPES[vehicle_type]} {new_id} added.", new_id)
    except pymysql.MySQLError as e:
        conn.rollback()
        return Result(False, friendly_error(e))
    finally:
        conn.close()


def get_owned_vehicle(carrier_id, vehicle_id):
    """Common + type-specific attributes, or None if not this carrier's vehicle."""
    v = fetch_one(
        "SELECT vehicle_id, carrier_id, home_hub_id, vehicle_type FROM Vehicle WHERE vehicle_id = %s AND carrier_id = %s",
        (vehicle_id, carrier_id),
    )
    if v is None:
        return None
    table, cols = TYPE_DETAILS[v["vehicle_type"]]
    details = fetch_one(
        f"SELECT {', '.join(c for c, _ in cols)} FROM {table} WHERE vehicle_id = %s", (vehicle_id,)
    ) or {}
    v["details"] = details
    return v


def update_home_hub(carrier_id, vehicle_id, home_hub_id):
    if get_owned_vehicle(carrier_id, vehicle_id) is None:
        return Result(False, f"Vehicle {vehicle_id} doesn't exist or isn't yours.")
    if not hub_exists(home_hub_id):
        return Result(False, f"Hub {home_hub_id} doesn't exist.")
    return run_write(
        [("UPDATE Vehicle SET home_hub_id = %s WHERE vehicle_id = %s AND carrier_id = %s",
          (home_hub_id, vehicle_id, carrier_id))],
        f"Vehicle {vehicle_id} now homed at {home_hub_id}.",
    )


def update_type_details(carrier_id, vehicle_id, details):
    v = get_owned_vehicle(carrier_id, vehicle_id)
    if v is None:
        return Result(False, f"Vehicle {vehicle_id} doesn't exist or isn't yours.")
    err = _check_details(v["vehicle_type"], details)
    if err:
        return Result(False, err)
    table, cols = TYPE_DETAILS[v["vehicle_type"]]
    col_names = [c for c, _ in cols]
    return run_write(
        [(f"UPDATE {table} SET {', '.join(f'{c} = %s' for c in col_names)} WHERE vehicle_id = %s",
          (*[details[c] for c in col_names], vehicle_id))],
        f"{TYPES[v['vehicle_type']]} {vehicle_id} details updated.",
    )


def list_vehicles(carrier_id):
    """All of the carrier's vehicles with their type-specific attributes."""
    return fetch_all(
        """SELECT v.vehicle_id, v.vehicle_type, v.home_hub_id,
                  bt.cargo_volume, bt.gross_weight_rating,
                  rv.temp_min, rv.temp_max, rv.payload_limit,
                  rc.axle_count, rc.track_gauge
           FROM Vehicle v
           LEFT JOIN BoxTruck bt        ON bt.vehicle_id = v.vehicle_id
           LEFT JOIN RefrigeratedVan rv ON rv.vehicle_id = v.vehicle_id
           LEFT JOIN RailCar rc         ON rc.vehicle_id = v.vehicle_id
           WHERE v.carrier_id = %s
           ORDER BY v.vehicle_id""",
        (carrier_id,),
    )
