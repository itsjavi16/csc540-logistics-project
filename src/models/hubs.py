"""Hubs and lanes: lookups used to validate input and fill drop-downs."""

from src.db.helpers import fetch_all, fetch_one


def list_hubs():
    return fetch_all("SELECT hub_id, name, region FROM Hub ORDER BY hub_id")


def hub_exists(hub_id):
    return fetch_one("SELECT 1 AS x FROM Hub WHERE hub_id = %s", (hub_id,)) is not None


def list_lanes():
    return fetch_all("SELECT origin_hub, destination_hub FROM Lane ORDER BY origin_hub, destination_hub")


def lane_exists(origin_hub, destination_hub):
    return fetch_one(
        "SELECT 1 AS x FROM Lane WHERE origin_hub = %s AND destination_hub = %s",
        (origin_hub, destination_hub),
    ) is not None


def check_lane(origin_hub, destination_hub):
    """Return an error message, or None if the pair is a valid lane."""
    if not origin_hub or not destination_hub:
        return "Enter both an origin and a destination hub."
    if origin_hub == destination_hub:
        return "Origin and destination must be different hubs."
    for h in (origin_hub, destination_hub):
        if not hub_exists(h):
            return f"Hub {h} doesn't exist."
    if not lane_exists(origin_hub, destination_hub):
        return f"{origin_hub} -> {destination_hub} isn't a lane in the network."
    return None
