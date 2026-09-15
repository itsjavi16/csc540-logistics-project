import mariadb
import sys

try:
    conn = mariadb.connect(
        user="",       #  your unity id
        password="",   # # you student id
        host="classdb2.csc.ncsu.edu",
        port=3306,
        database="mpoulse"    # Usually matches your account name
    )
    print("Connected to MariaDB successfully!")

except mariadb.Error as e:
    print(f"Error connecting to MariaDB: {e}")
    sys.exit(1)

cursor = conn.cursor()

# Test query: lists all tables in your database
cursor.execute("SHOW TABLES;")

for row in cursor:
    print(row)

cursor.close()
conn.close()
