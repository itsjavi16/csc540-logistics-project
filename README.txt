CSC 540 Project 1: Freight Tracking and Delivery Management

Team members
------------
  - Javiera Brito
  - Maggie Poulsen
  - Joe Pottern


What this is
------------
A Python (PyMySQL, no ORM) application on MariaDB 10.5
(classdb2.csc.ncsu.edu). The menu-driven interface is a small Streamlit web
page that runs on your own computer. Every screen follows the Project
Application Flow, with the same numbered options and menus.

The database is defined by three SQL files in the sql folder:

  sql/1_create_tables_triggers_procedures.sql   tables, constraints, views,
                                                stored procedure, triggers
  sql/2_insert_sample_data.sql                  the official sample data
  sql/3_required_queries.sql                    the Queries to be Implemented

The application's own SQL lives in src/models and src/reports; the screens in
src/ui contain no SQL.


Requirements
------------
  - Python 3.10 or newer (tested with Python 3.14)
  - Access to classdb2.csc.ncsu.edu: on campus, or connected to the NCSU VPN
  - A MariaDB account on classdb2 (UnityID / password)
  - Nothing to compile. No mysql command-line client is needed.


Setup (one time)
----------------
Run every command from the project folder (the folder with this file).

1. Install the Python packages. Either:

     conda env create -f environment.yml
     conda activate csc540-logistics

   If conda stops with "Pip failed", the environment was still created.
   Finish it with:

     conda activate csc540-logistics
     pip install -r requirements.txt

   or, with any Python 3.10+ (a virtual environment is recommended):

     pip install -r requirements.txt

2. Enter the database login. Copy the example file:

     Windows:        copy config\db_config.example.ini config\db_config.ini
     macOS / Linux:  cp config/db_config.example.ini config/db_config.ini

   Edit config/db_config.ini and set user, password and database
   (database is usually the same as your UnityID).

3. (Optional) Check the connection:

     python -m tests.manual_connection_test

4. Build the database and load the sample data:

     python -m db.load_database --reset

   WARNING: this drops this project's tables, views, procedure and triggers
   in the database from step 2, then recreates them. It runs, in order:

     sql/1_create_tables_triggers_procedures.sql
     sql/2_insert_sample_data.sql

   It ends by printing row counts. Expected: 11 hubs, 8 users,
   7 vehicles, 10 departures, 23 shipments, 22 bookings, 69 scan events.
   Run it again at any time to reset to the original sample data.

   Alternative with the mysql/mariadb client (same result):

     mysql -h classdb2.csc.ncsu.edu -u <user> -p <db> < sql/1_create_tables_triggers_procedures.sql
     mysql -h classdb2.csc.ncsu.edu -u <user> -p <db> < sql/2_insert_sample_data.sql

   and to run the six required queries:

     mysql -h classdb2.csc.ncsu.edu -u <user> -p <db> < sql/3_required_queries.sql


Running the application
-----------------------
Start it with the launcher for your system:

     Windows:        run_app.bat        (double-click it, or run it from cmd)
     macOS / Linux:  bash run_app.sh

or with the command they run:

     streamlit run src/ui/app.py

Your browser opens http://localhost:8501 (open it yourself if it doesn't).
To stop the application, press Ctrl+C in the terminal.

If port 8501 is busy:  streamlit run src/ui/app.py --server.port 8502


Logins (sample data)
--------------------
Sign in with the account's id from the sample data (SH1, C1, VW1, ...) as
the User ID. All passwords are:  password

     Role      User ID       Name
     Shipper   SH1 .. SH4    Triangle Textiles, Oak City Electronics,
                             Carolina Produce Co, Coastal Furniture
     Carrier   C1 .. C3      Piedmont Freight Lines, Atlantic Coast Haulers,
                             Plains Rail Co
     Viewer    VW1           Fedex

Choose the role on the first screen, then sign in with a matching account.
"4. View Queries" on the first screen runs the six required queries; no login
is needed.


How the sample data was mapped
------------------------------
Accounts: each sample id (C1, SH1, VW1, ...) is stored as User.username,
which is what you type at login. Each account also gets a numeric user_id,
the key the other tables use, numbered in order:

     Sample ids   username     user_id   Also
     C1 .. C3     C1 .. C3     1 .. 3    Carrier.carrier_id 1 .. 3
     SH1 .. SH4   SH1 .. SH4   4 .. 7    Shipper.user_id, Shipment.user_id
     VW1          VW1          8         Viewer.user_id

(The login screen also accepts the numeric user_id, so SH1 and 4 both work.)

Everything else keeps its number and drops its letters:
     V101 -> vehicle_id 101    D1 -> departure_id 1    S1 -> shipment_id 1
"Booked on" became rows in Booking (S14 is unbooked). "Seq" is
ScanEvent.scan_seq. Lanes aren't stored: any two different hubs can be an
origin and destination, and the LaneView view lists the pairs in use.
Shipment status and on-time/late are not inserted: the scan triggers compute
them from the scans. New records created in the app continue after the
sample ids (the next shipment is 24, the next departure is 11).


Project files
-------------
  sql/1_create_tables_triggers_procedures.sql
                                  tables, constraints, views (DepartureLoad,
                                  LaneView, LaneOnTime), stored procedure
                                  book_shipment (atomic booking), triggers
                                  (scan chronology, status/late flag, booking,
                                  departure and shipment guards)
  sql/2_insert_sample_data.sql    sample data inserts
  sql/3_required_queries.sql      the six required queries (the app reads
                                  this file for "View Queries")
  run_app.bat, run_app.sh         start the application
  db/load_database.py             builds the database (setup step 4)
  tests/manual_connection_test.py checks the database login (setup step 3)
  src/ui/                         screens (start: src/ui/app.py)
  src/models/, src/reports/       data layer: every SQL statement the app runs
  src/db/                         connection and helpers


Troubleshooting
---------------
  "Can't reach the database server"  Connect to the NCSU VPN; check host in
                                     config/db_config.ini.
  "Access denied"                    Check user/password/database in
                                     config/db_config.ini.
  Booking or tracking errors such as "PROCEDURE ... does not exist"
                                     Run setup step 4 again.
