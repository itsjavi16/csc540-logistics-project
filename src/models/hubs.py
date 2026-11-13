# Hubs and lanes: lookups used to validate input and fill reference tables.

# Lanes are not stored: any two different hubs form a valid origin -> destination
# pair. LaneView lists the pairs currently used by departures and shipments.


from src.db.helpers import fetch_all, fetch_one


def list_hubs():
    return fetch_all("SELECT hub_id, name, region FROM Hub ORDER BY hub_id")


def hub_exists(hub_id):
    return fetch_one("SELECT 1 AS x FROM Hub WHERE hub_id = %s", (hub_id,)) is not None


def list_lanes():
    return fetch_all(
        "SELECT origin_hub, destination_hub FROM LaneView ORDER BY origin_hub, destination_hub"
    )


def check_lane(origin_hub, destination_hub):
    if not origin_hub or not destination_hub:
        return "Choose both an origin and a destination hub."
    if origin_hub == destination_hub:
        return "Origin and destination must be different hubs."
    for h in (origin_hub, destination_hub):
        if not hub_exists(h):
            return f"Hub {h} doesn't exist."
    return None
