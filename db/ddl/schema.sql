-- CSC 540 Project 1: tables, constraints and the DepartureLoad view.


CREATE TABLE User (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name  VARCHAR(100) NOT NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    role_type     ENUM('SHIPPER','CARRIER','VIEWER') NOT NULL
);

CREATE TABLE Shipper (
    user_id    INT PRIMARY KEY,
    CONSTRAINT fk_shipper_user
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

CREATE TABLE CarrierCompany (
    carrier_id   INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL
);

CREATE TABLE Carrier (
    user_id    INT PRIMARY KEY,
    carrier_id INT NOT NULL,
    CONSTRAINT fk_carrier_user
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_carrier_company
        FOREIGN KEY (carrier_id) REFERENCES CarrierCompany(carrier_id)
);

CREATE TABLE Viewer (
    user_id INT PRIMARY KEY,
    CONSTRAINT fk_viewer_user
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

CREATE TABLE Hub (
    hub_id  CHAR(3)      PRIMARY KEY,
    name    VARCHAR(100) NOT NULL,
    region  ENUM('Northeast','Southeast','Midwest','Southwest','West') NOT NULL,
    CONSTRAINT chk_hub_id_format
        CHECK (BINARY hub_id REGEXP '^[A-Z]{3}$')
);

CREATE TABLE Vehicle (
    vehicle_id   INT AUTO_INCREMENT PRIMARY KEY,
    carrier_id   INT     NOT NULL,
    home_hub_id  CHAR(3) NOT NULL,
    vehicle_type ENUM('BOX_TRUCK','REFRIGERATED_VAN','RAIL_CAR') NOT NULL,
    CONSTRAINT fk_vehicle_carrier_company
        FOREIGN KEY (carrier_id) REFERENCES CarrierCompany(carrier_id),
    CONSTRAINT fk_vehicle_home_hub
        FOREIGN KEY (home_hub_id) REFERENCES Hub(hub_id)
        ON UPDATE CASCADE
);

CREATE TABLE BoxTruck (
    vehicle_id          INT PRIMARY KEY,
    cargo_volume        DECIMAL(8,2)  NOT NULL,
    gross_weight_rating DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_boxtruck_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_boxtruck_positive
        CHECK (cargo_volume > 0 AND gross_weight_rating > 0)
);

CREATE TABLE RefrigeratedVan (
    vehicle_id    INT PRIMARY KEY,
    temp_min      DECIMAL(5,2)  NOT NULL,
    temp_max      DECIMAL(5,2)  NOT NULL,
    payload_limit DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_refrigeratedvan_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_refrigeratedvan_temp_range
        CHECK (temp_min <= temp_max),
    CONSTRAINT chk_refrigeratedvan_payload_positive
        CHECK (payload_limit > 0)
);

CREATE TABLE RailCar (
    vehicle_id  INT PRIMARY KEY,
    axle_count  INT          NOT NULL,
    track_gauge DECIMAL(8,2) NOT NULL,
    CONSTRAINT fk_railcar_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_railcar_positive
        CHECK (axle_count > 0 AND track_gauge > 0)
);

CREATE TABLE Departure (
    departure_id       INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id         INT           NOT NULL,
    origin_hub         CHAR(3)       NOT NULL,
    destination_hub    CHAR(3)       NOT NULL,
    departure_datetime DATETIME      NOT NULL,
    max_weight         DECIMAL(10,2) NOT NULL,  -- kilograms; booked weight comes from DepartureLoad
    CONSTRAINT fk_departure_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id),
    CONSTRAINT fk_departure_origin_hub
        FOREIGN KEY (origin_hub) REFERENCES Hub(hub_id),
    CONSTRAINT fk_departure_destination_hub
        FOREIGN KEY (destination_hub) REFERENCES Hub(hub_id),
    CONSTRAINT chk_departure_hubs_distinct
        CHECK (origin_hub <> destination_hub),
    CONSTRAINT chk_departure_max_weight_positive
        CHECK (max_weight > 0)
);

CREATE TABLE Shipment (
    shipment_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id           INT           NOT NULL,  -- owning shipper account (Shipper.user_id)
    origin_hub        CHAR(3)       NOT NULL,
    destination_hub   CHAR(3)       NOT NULL,
    weight            DECIMAL(10,2) NOT NULL,
    promised_delivery DATE          NOT NULL,
    current_status    ENUM('CREATED','RECEIVED','IN_TRANSIT','ARRIVED_AT_HUB',
                           'OUT_FOR_DELIVERY','DELIVERED') NOT NULL DEFAULT 'CREATED',
    on_time_outcome   ENUM('ON_TIME','LATE') NULL,
    CONSTRAINT fk_shipment_shipper
        FOREIGN KEY (user_id) REFERENCES Shipper(user_id),
    CONSTRAINT fk_shipment_origin_hub
        FOREIGN KEY (origin_hub) REFERENCES Hub(hub_id),
    CONSTRAINT fk_shipment_destination_hub
        FOREIGN KEY (destination_hub) REFERENCES Hub(hub_id),
    CONSTRAINT chk_shipment_hubs_distinct
        CHECK (origin_hub <> destination_hub),
    CONSTRAINT chk_shipment_weight_positive
        CHECK (weight > 0),
    CONSTRAINT chk_shipment_outcome_only_when_delivered
        CHECK (on_time_outcome IS NULL OR current_status = 'DELIVERED')
);

-- One booking per shipment: shipment_id is the key.
CREATE TABLE Booking (
    shipment_id  INT PRIMARY KEY,
    departure_id INT NOT NULL,
    CONSTRAINT fk_booking_shipment
        FOREIGN KEY (shipment_id) REFERENCES Shipment(shipment_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_booking_departure
        FOREIGN KEY (departure_id) REFERENCES Departure(departure_id)
        ON DELETE NO ACTION
);

-- Weak entity: identified by (shipment_id, scan_seq) and deleted with its shipment.
CREATE TABLE ScanEvent (
    shipment_id     INT      NOT NULL,
    scan_seq        INT      NOT NULL DEFAULT 0,  -- the trigger fills in the next number
    timestamp       DATETIME NOT NULL,
    hub_id          CHAR(3)  NOT NULL,
    shipment_status ENUM('RECEIVED','IN_TRANSIT','ARRIVED_AT_HUB',
                         'OUT_FOR_DELIVERY','DELIVERED') NOT NULL,
    PRIMARY KEY (shipment_id, scan_seq),
    CONSTRAINT fk_scanevent_shipment
        FOREIGN KEY (shipment_id) REFERENCES Shipment(shipment_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_scanevent_hub
        FOREIGN KEY (hub_id) REFERENCES Hub(hub_id)
        ON UPDATE CASCADE
);

CREATE VIEW DepartureLoad AS
SELECT d.departure_id,
       d.max_weight,
       COALESCE(SUM(s.weight), 0)                AS booked_weight,
       d.max_weight - COALESCE(SUM(s.weight), 0) AS remaining_weight
FROM Departure d
LEFT JOIN Booking  b ON b.departure_id = d.departure_id
LEFT JOIN Shipment s ON s.shipment_id  = b.shipment_id
GROUP BY d.departure_id, d.max_weight;

-- Lanes are not stored: any two different hubs can be an origin and a
-- destination. This view lists the origin -> destination pairs in use.
CREATE VIEW LaneView AS
SELECT origin_hub, destination_hub FROM Departure
UNION
SELECT origin_hub, destination_hub FROM Shipment;

-- On-time rate per lane (origin -> destination), per delivery date.
-- Only delivered shipments count: a shipment without a DELIVERED scan is
-- neither on time nor late, so it is left out of the rate.
-- on_time_pct = shipments with on_time_outcome = 'ON_TIME' / delivered shipments.
-- The "On-Time Rates by Lane" report sums the rows in its date range.
CREATE VIEW LaneOnTime AS
SELECT s.origin_hub,
       s.destination_hub,
       DATE(e.`timestamp`)                                        AS delivery_date,
       COUNT(*)                                                   AS delivered,
       SUM(s.on_time_outcome = 'ON_TIME')                         AS on_time,
       SUM(s.on_time_outcome = 'LATE')                            AS late,
       ROUND(100 * SUM(s.on_time_outcome = 'ON_TIME') / COUNT(*), 1) AS on_time_pct
FROM Shipment s
JOIN ScanEvent e ON e.shipment_id = s.shipment_id
                AND e.shipment_status = 'DELIVERED'
GROUP BY s.origin_hub, s.destination_hub, DATE(e.`timestamp`);
