import pymysql

# Configuration settings
DB_HOST = "classdb2.csc.ncsu.edu"
DB_USER = "" # your unity id
DB_PASS = "" # you student id


def main():
    try:
        # 1. Connect to the MariaDB server and select your pre-assigned database
        conn = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_USER,
            port=3306,
            autocommit=True  # Automatically commit DDL commands like CREATE TABLE
        )
        print(f"Connected successfully to database '{DB_USER}'!")

        with conn.cursor() as cursor:
            # 2. SQL query to create a table if it doesn't already exist
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS Students (
                student_id INT AUTO_INCREMENT PRIMARY KEY,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL
            );
            """

            print("Executing CREATE TABLE query...")
            cursor.execute(create_table_sql)
            print("Table 'Students' created successfully!")

            # 3. Verify that the table was created by listing all tables
            print("\nCurrent tables in your database:")
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()

            for table in tables:
                print(f" - {table[0]}")

            # Inspect the table schema
            print("\nStructure of 'Students' table:")
            cursor.execute("DESCRIBE Students;")
            columns = cursor.fetchall()

            # Print formatted column details
            for col in columns:
                field_name, data_type, null_allowed, key, default_val, extra = col
                print(f"Column: {field_name:<15} Type: {data_type:<15} Key: {key}")

        # Close the database connection when finished
        conn.close()

    except pymysql.MySQLError as e:
        print(f"Error connecting or executing SQL: {e}")


if __name__ == "__main__":
    main()
