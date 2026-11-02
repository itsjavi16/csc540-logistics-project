-- =====================================================================
-- CSC 540 Freight Tracking: official sample data (demo and grading)
-- Source: "Sample Data for Demo and Testing"
--
-- Run this AFTER the schema (tables, view, procedure, triggers) is loaded.
-- It first empties every table, so it can be re-run to reset the demo.
--
-- How the sample ids map to our schema
--   Sample id   Our column(s)                               Value
--   ---------   -----------------------------------------   ---------------
--   C1..C3      CarrierCompany.carrier_id                   1..3
--   SH1..SH4    Shipper.shipper_id                          1..4
--   C1, SH1,    User.username (the login "User ID")         'C1', 'SH1', ...
--   VW1
--   V101 ...    Vehicle.vehicle_id                          101, 102, ...
--   D1..D10     Departure.departure_id                      1..10
--   S1..S23     Shipment.shipment_id                        1..23
--   Booked on   Booking(shipment_id, departure_id)          (S14 has no row)
--   Seq         ScanEvent.scan_seq                          1, 2, 3, 4
--   received... ScanEvent.shipment_status                   'RECEIVED', ...
--
-- The sample data gives no login accounts. Every sample company gets
-- one account whose username is its sample id and whose password is
-- @demo_password below. Passwords are stored as SHA2(password, 256).
--
-- The sample data has no lane list, so Lane holds the five lanes its
-- departures and shipments use.
--
-- Not inserted directly, because the triggers maintain them:
--   Shipment.current_status and Shipment.on_time_outcome come from the
--   scans (trg_scan_status). A shipment is on time if it is delivered by
--   the end of its promised date.
-- =====================================================================

SET @demo_password = 'password';

START TRANSACTION;

-- ---------------------------------------------------------------------
-- Reset (children first, so foreign keys are never violated)
-- ---------------------------------------------------------------------
DELETE FROM ScanEvent;
DELETE FROM Booking;
DELETE FROM Shipment;
DELETE FROM Departure;
DELETE FROM BoxTruck;
DELETE FROM RefrigeratedVan;
DELETE FROM RailCar;
DELETE FROM Vehicle;
DELETE FROM Lane;
DELETE FROM Hub;
DELETE FROM Shipper;
DELETE FROM Carrier;
DELETE FROM Viewer;
DELETE FROM CarrierCompany;
DELETE FROM User;

-- ---------------------------------------------------------------------
-- Hubs and regions
-- ---------------------------------------------------------------------
INSERT INTO Hub (hub_id, name, region) VALUES
    ('RDU', 'Raleigh Hub',     'Southeast'),
    ('ATL', 'Atlanta Hub',     'Southeast'),
    ('MIA', 'Miami Hub',       'Southeast'),
    ('JFK', 'New York Hub',    'Northeast'),
    ('BOS', 'Boston Hub',      'Northeast'),
    ('ORD', 'Chicago Hub',     'Midwest'),
    ('STL', 'St. Louis Hub',   'Midwest'),
    ('DFW', 'Dallas Hub',      'Southwest'),
    ('PHX', 'Phoenix Hub',     'Southwest'),
    ('LAX', 'Los Angeles Hub', 'West'),
    ('SEA', 'Seattle Hub',     'West');

-- Lanes used by the sample departures and shipments
INSERT INTO Lane (origin_hub, destination_hub) VALUES
    ('RDU', 'ATL'),
    ('ATL', 'MIA'),
    ('JFK', 'BOS'),
    ('ORD', 'DFW'),
    ('DFW', 'LAX');

-- ---------------------------------------------------------------------
-- Carriers, shippers and viewers
-- ---------------------------------------------------------------------
INSERT INTO CarrierCompany (carrier_id, company_name) VALUES
    (1, 'Piedmont Freight Lines'),   -- C1
    (2, 'Atlantic Coast Haulers'),   -- C2
    (3, 'Plains Rail Co');           -- C3

INSERT INTO User (user_id, username, password_hash, display_name, role_type) VALUES
    (1, 'C1',  SHA2(@demo_password, 256), 'Piedmont Freight Lines', 'CARRIER'),
    (2, 'C2',  SHA2(@demo_password, 256), 'Atlantic Coast Haulers', 'CARRIER'),
    (3, 'C3',  SHA2(@demo_password, 256), 'Plains Rail Co',         'CARRIER'),
    (4, 'SH1', SHA2(@demo_password, 256), 'Triangle Textiles',      'SHIPPER'),
    (5, 'SH2', SHA2(@demo_password, 256), 'Oak City Electronics',   'SHIPPER'),
    (6, 'SH3', SHA2(@demo_password, 256), 'Carolina Produce Co',    'SHIPPER'),
    (7, 'SH4', SHA2(@demo_password, 256), 'Coastal Furniture',      'SHIPPER'),
    (8, 'VW1', SHA2(@demo_password, 256), 'Fedex',                  'VIEWER');

INSERT INTO Carrier (user_id, carrier_id) VALUES
    (1, 1),
    (2, 2),
    (3, 3);

INSERT INTO Shipper (user_id, shipper_id) VALUES
    (4, 1),   -- SH1
    (5, 2),   -- SH2
    (6, 3),   -- SH3
    (7, 4);   -- SH4

INSERT INTO Viewer (user_id) VALUES
    (8);      -- VW1

-- ---------------------------------------------------------------------
-- Vehicles (supertype row, then the subtype row with its attributes)
-- ---------------------------------------------------------------------
INSERT INTO Vehicle (vehicle_id, carrier_id, home_hub_id, vehicle_type) VALUES
    (101, 1, 'RDU', 'BOX_TRUCK'),
    (102, 1, 'ATL', 'REFRIGERATED_VAN'),
    (103, 1, 'RDU', 'BOX_TRUCK'),
    (201, 2, 'JFK', 'BOX_TRUCK'),
    (202, 2, 'ORD', 'BOX_TRUCK'),
    (203, 2, 'ORD', 'REFRIGERATED_VAN'),
    (301, 3, 'DFW', 'RAIL_CAR');

-- cargo_volume in m3, gross_weight_rating in kg
INSERT INTO BoxTruck (vehicle_id, cargo_volume, gross_weight_rating) VALUES
    (101, 45.0, 12000),
    (103, 30.0,  8000),
    (201, 40.0, 10000),
    (202, 50.0, 14000);

-- temperatures in C, payload_limit in kg
INSERT INTO RefrigeratedVan (vehicle_id, temp_min, temp_max, payload_limit) VALUES
    (102, -18.0,   4.0, 4000),
    (203, -25.0, -10.0, 3000);

-- track_gauge in mm
INSERT INTO RailCar (vehicle_id, axle_count, track_gauge) VALUES
    (301, 4, 1435);

-- ---------------------------------------------------------------------
-- Departures (max_weight = sample "Capacity (kg)")
-- The carrier comes from the vehicle (Vehicle.carrier_id).
-- ---------------------------------------------------------------------
INSERT INTO Departure (departure_id, vehicle_id, origin_hub, destination_hub, departure_datetime, max_weight) VALUES
    ( 1, 101, 'RDU', 'ATL', '2026-03-01 22:00:00', 10000),
    ( 2, 102, 'ATL', 'MIA', '2026-03-04 06:00:00',  4000),
    ( 3, 201, 'JFK', 'BOS', '2026-03-02 09:00:00',  8000),
    ( 4, 202, 'ORD', 'DFW', '2026-03-02 20:00:00', 12000),
    ( 5, 301, 'DFW', 'LAX', '2026-03-03 08:00:00',  9000),
    ( 6, 101, 'RDU', 'ATL', '2026-03-07 22:00:00', 10000),
    ( 7, 103, 'RDU', 'ATL', '2026-10-29 09:00:00',  2000),
    ( 8, 101, 'RDU', 'ATL', '2026-10-30 09:00:00',  8000),
    ( 9, 101, 'RDU', 'ATL', '2026-01-10 09:00:00', 10000),
    (10, 101, 'RDU', 'ATL', '2026-02-10 09:00:00', 10000);

-- ---------------------------------------------------------------------
-- Shipments (weight in kg; promised_delivery = sample "Promised")
-- ---------------------------------------------------------------------
INSERT INTO Shipment (shipment_id, shipper_id, origin_hub, destination_hub, weight, promised_delivery) VALUES
    ( 1, 1, 'RDU', 'ATL', 3000, '2026-03-04'),
    ( 2, 2, 'JFK', 'BOS', 2500, '2026-03-02'),
    ( 3, 3, 'RDU', 'ATL', 2000, '2026-03-02'),
    ( 4, 1, 'JFK', 'BOS', 1500, '2026-03-05'),
    ( 5, 2, 'ATL', 'MIA', 2000, '2026-03-07'),
    ( 6, 3, 'ATL', 'MIA', 1700, '2026-03-06'),
    ( 7, 3, 'ORD', 'DFW', 3000, '2026-03-05'),
    ( 8, 3, 'ORD', 'DFW', 4000, '2026-03-03'),
    ( 9, 1, 'RDU', 'ATL', 2500, '2026-03-05'),
    (10, 3, 'RDU', 'ATL', 2800, '2026-03-11'),
    (11, 2, 'DFW', 'LAX', 3500, '2026-03-05'),
    (12, 1, 'RDU', 'ATL', 1000, '2026-11-02'),
    (13, 1, 'RDU', 'ATL', 1000, '2026-11-02'),
    (14, 1, 'RDU', 'ATL',  500, '2026-11-03'),
    (15, 1, 'RDU', 'ATL',  500, '2026-11-02'),
    (16, 1, 'RDU', 'ATL',  500, '2026-10-30'),
    (17, 1, 'RDU', 'ATL', 1000, '2026-10-31'),
    (18, 1, 'RDU', 'ATL', 1000, '2026-11-02'),
    (19, 1, 'RDU', 'ATL', 1000, '2026-11-03'),
    (20, 1, 'RDU', 'ATL', 1000, '2026-01-11'),
    (21, 1, 'RDU', 'ATL', 1000, '2026-01-12'),
    (22, 1, 'RDU', 'ATL', 1000, '2026-02-11'),
    (23, 1, 'RDU', 'ATL', 1000, '2026-02-12');

-- ---------------------------------------------------------------------
-- Bookings (sample "Booked on"). S14 is unbooked, so it has no row.
-- trg_booking_guard checks each one: same lane, within capacity.
-- ---------------------------------------------------------------------
INSERT INTO Booking (shipment_id, departure_id) VALUES
    ( 1,  1), ( 2,  3), ( 3,  1), ( 4,  3), ( 5,  2), ( 6,  2),
    ( 7,  4), ( 8,  4), ( 9,  1), (10,  6), (11,  5), (12,  7),
    (13,  7), (15,  8), (16,  8), (17,  8), (18,  8), (19,  8),
    (20,  9), (21,  9), (22, 10), (23, 10);

-- ---------------------------------------------------------------------
-- Scan events, in order within each shipment.
-- trg_scan_chronology checks the order; trg_scan_status updates
-- Shipment.current_status and sets on_time_outcome on delivery.
-- ---------------------------------------------------------------------
INSERT INTO ScanEvent (shipment_id, scan_seq, shipment_status, hub_id, `timestamp`) VALUES
    ( 1, 1, 'RECEIVED',         'RDU', '2026-03-01 21:00:00'),
    ( 1, 2, 'IN_TRANSIT',       'RDU', '2026-03-01 22:05:00'),
    ( 1, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-03-02 12:30:00'),
    ( 1, 4, 'DELIVERED',        'ATL', '2026-03-02 14:00:00'),

    ( 2, 1, 'RECEIVED',         'JFK', '2026-03-01 15:00:00'),
    ( 2, 2, 'IN_TRANSIT',       'JFK', '2026-03-02 09:10:00'),
    ( 2, 3, 'OUT_FOR_DELIVERY', 'BOS', '2026-03-03 08:00:00'),
    ( 2, 4, 'DELIVERED',        'BOS', '2026-03-03 11:30:00'),

    ( 3, 1, 'RECEIVED',         'RDU', '2026-03-01 19:15:00'),
    ( 3, 2, 'IN_TRANSIT',       'RDU', '2026-03-01 22:05:00'),
    ( 3, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-03-02 18:00:00'),
    ( 3, 4, 'DELIVERED',        'ATL', '2026-03-02 20:45:00'),

    ( 4, 1, 'RECEIVED',         'JFK', '2026-03-01 16:00:00'),
    ( 4, 2, 'IN_TRANSIT',       'JFK', '2026-03-02 09:10:00'),

    ( 5, 1, 'RECEIVED',         'ATL', '2026-03-03 15:00:00'),
    ( 5, 2, 'IN_TRANSIT',       'ATL', '2026-03-04 06:10:00'),
    ( 5, 3, 'OUT_FOR_DELIVERY', 'MIA', '2026-03-06 08:00:00'),
    ( 5, 4, 'DELIVERED',        'MIA', '2026-03-06 12:15:00'),

    ( 6, 1, 'RECEIVED',         'ATL', '2026-03-03 16:30:00'),
    ( 6, 2, 'IN_TRANSIT',       'ATL', '2026-03-04 06:10:00'),
    ( 6, 3, 'OUT_FOR_DELIVERY', 'MIA', '2026-03-07 09:00:00'),
    ( 6, 4, 'DELIVERED',        'MIA', '2026-03-07 16:20:00'),

    ( 7, 1, 'RECEIVED',         'ORD', '2026-03-02 11:00:00'),
    ( 7, 2, 'IN_TRANSIT',       'ORD', '2026-03-02 20:15:00'),
    ( 7, 3, 'OUT_FOR_DELIVERY', 'DFW', '2026-03-04 07:30:00'),
    ( 7, 4, 'DELIVERED',        'DFW', '2026-03-04 11:00:00'),

    ( 8, 1, 'RECEIVED',         'ORD', '2026-03-02 12:30:00'),
    ( 8, 2, 'IN_TRANSIT',       'ORD', '2026-03-02 20:15:00'),
    ( 8, 3, 'OUT_FOR_DELIVERY', 'DFW', '2026-03-05 07:00:00'),
    ( 8, 4, 'DELIVERED',        'DFW', '2026-03-05 09:45:00'),

    ( 9, 1, 'RECEIVED',         'RDU', '2026-03-01 18:40:00'),
    ( 9, 2, 'IN_TRANSIT',       'RDU', '2026-03-01 22:05:00'),
    ( 9, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-03-03 09:00:00'),
    ( 9, 4, 'DELIVERED',        'ATL', '2026-03-03 12:00:00'),

    (10, 1, 'RECEIVED',         'RDU', '2026-03-07 15:00:00'),
    (10, 2, 'IN_TRANSIT',       'RDU', '2026-03-07 22:10:00'),
    (10, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-03-10 08:00:00'),
    (10, 4, 'DELIVERED',        'ATL', '2026-03-10 10:30:00'),

    (11, 1, 'RECEIVED',         'DFW', '2026-03-02 19:00:00'),
    (11, 2, 'IN_TRANSIT',       'DFW', '2026-03-03 08:30:00'),
    (11, 3, 'OUT_FOR_DELIVERY', 'LAX', '2026-03-07 06:00:00'),
    (11, 4, 'DELIVERED',        'LAX', '2026-03-07 08:30:00'),

    (12, 1, 'RECEIVED',         'RDU', '2026-10-28 16:00:00'),

    (13, 1, 'RECEIVED',         'RDU', '2026-10-28 16:30:00'),

    (15, 1, 'RECEIVED',         'RDU', '2026-10-29 16:00:00'),

    (16, 1, 'RECEIVED',         'RDU', '2026-10-29 17:00:00'),
    (16, 2, 'IN_TRANSIT',       'RDU', '2026-10-30 09:10:00'),

    (17, 1, 'RECEIVED',         'RDU', '2026-10-29 17:15:00'),
    (17, 2, 'IN_TRANSIT',       'RDU', '2026-10-30 09:10:00'),

    (18, 1, 'RECEIVED',         'RDU', '2026-10-29 17:30:00'),
    (18, 2, 'IN_TRANSIT',       'RDU', '2026-10-30 09:10:00'),

    (19, 1, 'RECEIVED',         'RDU', '2026-10-29 17:45:00'),
    (19, 2, 'IN_TRANSIT',       'RDU', '2026-10-30 09:10:00'),

    (20, 1, 'RECEIVED',         'RDU', '2026-01-09 16:00:00'),
    (20, 2, 'IN_TRANSIT',       'RDU', '2026-01-10 09:10:00'),
    (20, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-01-11 08:00:00'),
    (20, 4, 'DELIVERED',        'ATL', '2026-01-11 10:00:00'),

    (21, 1, 'RECEIVED',         'RDU', '2026-01-09 16:30:00'),
    (21, 2, 'IN_TRANSIT',       'RDU', '2026-01-10 09:10:00'),
    (21, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-01-11 08:15:00'),
    (21, 4, 'DELIVERED',        'ATL', '2026-01-11 11:00:00'),

    (22, 1, 'RECEIVED',         'RDU', '2026-02-09 16:00:00'),
    (22, 2, 'IN_TRANSIT',       'RDU', '2026-02-10 09:10:00'),
    (22, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-02-11 08:00:00'),
    (22, 4, 'DELIVERED',        'ATL', '2026-02-11 10:00:00'),

    (23, 1, 'RECEIVED',         'RDU', '2026-02-09 16:30:00'),
    (23, 2, 'IN_TRANSIT',       'RDU', '2026-02-10 09:10:00'),
    (23, 3, 'OUT_FOR_DELIVERY', 'ATL', '2026-02-13 08:00:00'),
    (23, 4, 'DELIVERED',        'ATL', '2026-02-13 11:00:00');

-- New rows the app creates (new shipments, departures, vehicles, users)
-- continue after the sample ids.
ALTER TABLE User           AUTO_INCREMENT = 9;
ALTER TABLE CarrierCompany AUTO_INCREMENT = 4;
ALTER TABLE Vehicle        AUTO_INCREMENT = 302;
ALTER TABLE Departure      AUTO_INCREMENT = 11;
ALTER TABLE Shipment       AUTO_INCREMENT = 24;

COMMIT;

-- ---------------------------------------------------------------------
-- Quick check: expected counts are 11 hubs, 5 lanes, 8 users, 7 vehicles,
-- 10 departures, 23 shipments, 22 bookings, 69 scans.
-- ---------------------------------------------------------------------
SELECT 'Hub' AS table_name, COUNT(*) AS row_count FROM Hub
UNION ALL SELECT 'Lane',      COUNT(*) FROM Lane
UNION ALL SELECT 'User',      COUNT(*) FROM User
UNION ALL SELECT 'Vehicle',   COUNT(*) FROM Vehicle
UNION ALL SELECT 'Departure', COUNT(*) FROM Departure
UNION ALL SELECT 'Shipment',  COUNT(*) FROM Shipment
UNION ALL SELECT 'Booking',   COUNT(*) FROM Booking
UNION ALL SELECT 'ScanEvent', COUNT(*) FROM ScanEvent;
