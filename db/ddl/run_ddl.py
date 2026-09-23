import os
import re
import sys
 
# Allow running as `python -m db.ddl.run_ddl` from the project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
 
from src.db.connection import get_connection
 
DDL_DIR = os.path.dirname(__file__)
 
FILES_IN_ORDER = [
    "01_accounts.sql",
    "02_hubs.sql",
    "03_vehicles.sql",
    "04_departures.sql",
    "05_shipments.sql",
    "06_scan_events.sql",
]
 
 
def strip_line_comments(sql_text: str) -> str:
    
    return re.sub(r"--[^\n]*", "", sql_text)
 
 
def split_statements(sql_text: str):
    sql_text = strip_line_comments(sql_text)
    statements = [s.strip() for s in sql_text.split(";")]
    return [s for s in statements if s]
 
 
def main():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            for filename in FILES_IN_ORDER:
                path = os.path.join(DDL_DIR, filename)
                print(f"Running {filename} ...")
                with open(path, "r") as f:
                    sql_text = f.read()
                for statement in split_statements(sql_text):
                    cur.execute(statement)
                conn.commit()
                print(f"  OK")
 
            cur.execute("SHOW TABLES;")
            tables = cur.fetchall()
            print(f"\nDone. {len(tables)} tables now in your database:")
            for t in tables:
                print(f"  - {list(t.values())[0]}")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
 
 
if __name__ == "__main__":
    main()