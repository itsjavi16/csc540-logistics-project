"""
Drops every table this project's DDL creates, plus any earlier leftovers
(like SmokeTest), so you can re-run db/ddl/run_ddl.py from a clean slate.

DESTRUCTIVE -- this deletes all data in these tables on whatever database
your config/db_config.ini points at. Double-check that's your intended
target (your own class account) before running.

Usage (from the project root, with your venv/conda env active):
    python -m db.ddl.drop_all
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.db.connection import get_connection

# Order doesn't actually matter here because we disable FK checks below,
# but listed in reverse-dependency order anyway for readability.
TABLES = [
    "ScanEvent",
    "Shipment",
    "Departure",
    "BoxTruck",
    "RefrigeratedVan",
    "RailCar",
    "Vehicle",
    "Shipper",
    "Carrier",
    "Viewer",
    "User",
    "Lane",
    "Hub",
    "SmokeTest",
]


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Temporarily disable FK constraint checking so we don't have
            # to drop tables in exact dependency order -- standard
            # technique for a full reset during development. Re-enabled
            # right after, so it doesn't silently stay off for anything
            # else in the same session.
            cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            for table in TABLES:
                cur.execute(f"DROP TABLE IF EXISTS {table};")
                print(f"Dropped {table} (if it existed)")
            cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
            conn.commit()

            cur.execute("SHOW TABLES;")
            remaining = cur.fetchall()
            print(f"\nDone. {len(remaining)} tables remain: {remaining}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
