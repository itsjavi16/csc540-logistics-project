"""
DB connection helper for the departmental MariaDB server.

Reads credentials from config/db_config.ini (gitignored). Copy
config/db_config.example.ini to config/db_config.ini and fill in your
own unityid/password before running anything.

Uses PyMySQL directly -- no ORM, per project requirements. All SQL
(including calls to stored procedures) is written explicitly in the
data-access layer under src/models/.
"""

import configparser
import os

import pymysql
import pymysql.cursors

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "db_config.ini"
)


def _load_config():
    if not os.path.exists(_CONFIG_PATH):
        raise FileNotFoundError(
            f"Missing {_CONFIG_PATH}. Copy config/db_config.example.ini to "
            "config/db_config.ini and fill in your credentials."
        )
    parser = configparser.ConfigParser()
    parser.read(_CONFIG_PATH)
    return parser["database"]


def get_connection():
    """
    Return a new PyMySQL connection to the departmental MariaDB server.

    Each caller is responsible for closing the connection (or use it as
    a context manager: `with get_connection() as conn:`).
    """
    cfg = _load_config()
    return pymysql.connect(
        host=cfg.get("host", "classdb2.csc.ncsu.edu"),
        port=cfg.getint("port", fallback=3306),
        user=cfg["user"],
        password=cfg["password"],
        database=cfg["database"],
        ssl_disabled=cfg.getboolean("ssl_disabled", fallback=True),
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,  # explicit commit/rollback -- important for the
                            # atomic booking procedure and trigger-driven writes
    )


if __name__ == "__main__":
    # Quick connectivity smoke test: python -m src.db.connection
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS version;")
            row = cur.fetchone()
            print(f"Connected. Server reports: {row['version']}")

            cur.execute("SHOW TABLES;")
            tables = cur.fetchall()
            print(f"Tables in your database: {len(tables)}")
            for t in tables:
                print(f"  - {list(t.values())[0]}")
    finally:
        conn.close()
