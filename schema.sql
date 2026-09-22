-- CSC 540 Project 1: Deliverable 1: Relational Schema (DDL)
-- Freight Tracking and Delivery Management for a Regional Logistics Carrier

CREATE TABLE Account (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Shipper (
    account_id INT PRIMARY KEY,
    FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE
);

CREATE TABLE CarrierOrg (
    carrier_org_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name   VARCHAR(100) NOT NULL
);

CREATE TABLE Carrier (
    account_id     INT PRIMARY KEY,
    carrier_org_id INT NOT NULL,
    CONSTRAINT fk_carrier_account
        FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE,
    CONSTRAINT fk_carrier_carrierorg
        FOREIGN KEY (carrier_org_id) REFERENCES CarrierOrg(carrier_org_id)
);

CREATE TABLE Viewer (
    account_id INT PRIMARY KEY,
    FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE
);

CREATE TABLE Hub (
    hub_id          INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    region          ENUM('Northeast','Southeast','Midwest','Southwest','West')
                    NOT NULL,
    address         VARCHAR(255)
);

CREATE TABLE Vehicle (
    vehicle_id      INT AUTO_INCREMENT PRIMARY KEY,
    carrier_org_id  INT NOT NULL,
    home_hub_id     INT NOT NULL,
    vehicle_type    ENUM('BOX_TRUCK','REFRIGERATED_VAN','RAIL_CAR') NOT NULL,
    CONSTRAINT fk_vehicle_carrierorg
        FOREIGN KEY (carrier_org_id) REFERENCES CarrierOrg(carrier_org_id),
    CONSTRAINT fk_vehicle_home_hub
        FOREIGN KEY (home_hub_id) REFERENCES Hub(hub_id)
);

CREATE TABLE BoxTruck (
    vehicle_id              INT PRIMARY KEY,
    cargo_volume_m3         DECIMAL(8,2) NOT NULL,
    gross_weight_rating_kg  DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_boxtruck_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        ON DELETE CASCADE
);

CREATE TABLE RefrigeratedVan (
    vehicle_id      INT PRIMARY KEY,
    temp_min_c      DECIMAL(5,2) NOT NULL,
    temp_max_c      DECIMAL(5,2) NOT NULL,
    payload_limit_kg DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_refrigeratedvan_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_refrigeratedvan_temp_range
        CHECK (temp_min_c <= temp_max_c)
);

CREATE TABLE RailCar (
    vehicle_id      INT PRIMARY KEY,
    axle_count      INT NOT NULL,
    track_gauge_mm  DECIMAL(8,2) NOT NULL,
    CONSTRAINT fk_railcar_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        ON DELETE CASCADE
);

CREATE TABLE Departure (
    departure_id        INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id           INT NOT NULL,
    origin_hub_id         INT NOT NULL,
    destination_hub_id    INT NOT NULL,
    departure_datetime    DATETIME NOT NULL,
    max_weight_kg         DECIMAL(10,2) NOT NULL,
    CONSTRAINT fk_departure_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id),
    CONSTRAINT fk_departure_origin_hub
        FOREIGN KEY (origin_hub_id) REFERENCES Hub(hub_id),
    CONSTRAINT fk_departure_destination_hub
        FOREIGN KEY (destination_hub_id) REFERENCES Hub(hub_id),
    CONSTRAINT chk_departure_max_weight_positive
        CHECK (max_weight_kg > 0),
    CONSTRAINT chk_departure_hubs_distinct
        CHECK (origin_hub_id <> destination_hub_id)
);

CREATE INDEX idx_departure_lane
    ON Departure (origin_hub_id, destination_hub_id);

CREATE TABLE Shipment (
    shipment_id             INT AUTO_INCREMENT PRIMARY KEY,
    shipper_id               INT NOT NULL,
    origin_hub_id             INT NOT NULL,
    destination_hub_id        INT NOT NULL,
    weight_kg                 DECIMAL(10,2) NOT NULL,
    promised_delivery_date    DATE NOT NULL,
    departure_id              INT NULL,
    booked_at                 DATETIME NULL,
    current_status ENUM('CREATED','RECEIVED','IN_TRANSIT','ARRIVED_AT_HUB',
                         'OUT_FOR_DELIVERY','DELIVERED')
                    NOT NULL DEFAULT 'CREATED',
    on_time_outcome ENUM('ON_TIME','LATE') NULL,
    CONSTRAINT fk_shipment_shipper
        FOREIGN KEY (shipper_id) REFERENCES Shipper(account_id),
    CONSTRAINT fk_shipment_origin_hub
        FOREIGN KEY (origin_hub_id) REFERENCES Hub(hub_id),
    CONSTRAINT fk_shipment_destination_hub
        FOREIGN KEY (destination_hub_id) REFERENCES Hub(hub_id),
    CONSTRAINT fk_shipment_departure
        FOREIGN KEY (departure_id) REFERENCES Departure(departure_id),
    CONSTRAINT chk_shipment_weight_positive
        CHECK (weight_kg > 0),
    CONSTRAINT chk_shipment_hubs_distinct
        CHECK (origin_hub_id <> destination_hub_id)
);

CREATE INDEX idx_shipment_lane
    ON Shipment (origin_hub_id, destination_hub_id);

CREATE INDEX idx_shipment_departure
    ON Shipment (departure_id);

CREATE TABLE ScanEvent (
    shipment_id     INT NOT NULL,
    scan_seq        INT NOT NULL,
    scanned_at      DATETIME NOT NULL,
    hub_id          INT NOT NULL,
    status ENUM('RECEIVED','IN_TRANSIT','ARRIVED_AT_HUB',
                'OUT_FOR_DELIVERY','DELIVERED') NOT NULL,
    PRIMARY KEY (shipment_id, scan_seq),
    CONSTRAINT fk_scanevent_shipment
        FOREIGN KEY (shipment_id) REFERENCES Shipment(shipment_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_scanevent_hub
        FOREIGN KEY (hub_id) REFERENCES Hub(hub_id),
    CONSTRAINT chk_scanevent_seq_positive
        CHECK (scan_seq > 0)
);
