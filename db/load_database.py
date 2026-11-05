"""
Build the project database from scratch and load the official sample data.

    python -m db.load_database --reset

Runs, in order:
    db/ddl/schema.sql                  tables + DepartureLoad view
    db/procedures/book_shipment.sql    booking procedure
    db/triggers/triggers.sql           scan + guard triggers
    db/seed/sample_data.sql            official sample data

!! --reset first DROPS this project's tables, view, procedure and triggers in
   the database config/db_config.ini points at, so all their data is lost.
   Without --reset nothing runs.

Uses the same connection settings as the app, so no mysql client is needed.
DELIMITER blocks in the procedure/trigger files are handled by
src/db/sql_split.py.
"""

import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, ROOT)

from src.db.connection import get_connection  # noqa: E402
from src.db.sql_split import split_statements  # noqa: E402

FILES_IN_ORDER = [
    "db/ddl/schema.sql",
    "db/procedures/book_shipment.sql",
    "db/triggers/triggers.sql",
    "db/seed/sample_data.sql",
]

TABLES = [
    "ScanEvent", "Booking", "Shipment", "Departure",
    "BoxTruck", "RefrigeratedVan", "RailCar", "Vehicle",
    "Shipper", "Carrier", "Viewer", "CarrierCompany", "User",
    "Lane", "Hub",
]


def reset(cur):
    cur.execute("SET FOREIGN_KEY_CHECKS = 0")
    cur.execute("DROP VIEW IF EXISTS DepartureLoad")
    cur.execute("DROP PROCEDURE IF EXISTS book_shipment")
    for t in TABLES:  # dropping a table also drops its triggers
        cur.execute(f"DROP TABLE IF EXISTS `{t}`")
    cur.execute("SET FOREIGN_KEY_CHECKS = 1")


def main():
    if "--reset" not in sys.argv:
        print(__doc__)
        sys.exit(1)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT DATABASE() AS db")
            print(f"Database: {cur.fetchone()['db']}")
            reset(cur)
            print("Dropped the old tables, view, procedure and triggers.")

            for rel in FILES_IN_ORDER:
                with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
                    statements = split_statements(f.read())
                for stmt in statements:
                    cur.execute(stmt)
                    if cur.description:  # the seed's row-count check at the end
                        rows = cur.fetchall()
                conn.commit()
                print(f"Loaded {rel}")

            print("\nRow counts:")
            for r in rows:
                print(f"  {r['table_name']:<10} {r['row_count']}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
