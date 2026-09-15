"""
Manual connectivity smoke test -- run this after setting up config/db_config.ini
to confirm your account can reach the department server and create a table.

    python -m tests.manual_connection_test

This mirrors the professor's example.py (see docs/professor-examples/) but
reads credentials from the shared config file instead of hardcoding them,
so every teammate can run it without editing source.
"""

from src.db.connection import get_connection


def main():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS SmokeTest (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    note VARCHAR(100) NOT NULL
                );
                """
            )
            conn.commit()
            print("SmokeTest table created (or already existed).")

            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"\nCurrent tables ({len(tables)}):")
            for t in tables:
                print(f"  - {list(t.values())[0]}")

            cursor.execute("DESCRIBE SmokeTest;")
            print("\nSmokeTest schema:")
            for col in cursor.fetchall():
                print(f"  {col['Field']:<15} {col['Type']:<15} Key={col['Key']}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
