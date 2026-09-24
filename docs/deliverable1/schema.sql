-- CSC 540 Project 1: Deliverable 1: Relational Schema (DDL)
-- Freight Tracking and Delivery Management for a Regional Logistics Carrier

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
    shipper_id INT NOT NULL UNIQUE,
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
    address VARCHAR(255),
    CONSTRAINT chk_hub_id_format
        CHECK (BINARY hub_id REGEXP '^[A-Z]{3}$')
);

CREATE TABLE Lane (
    origin_hub      CHAR(3) NOT NULL,
    destination_hub CHAR(3) NOT NULL,
    PRIMARY KEY (origin_hub, destination_hub),
    CONSTRAINT fk_lane_origin_hub
        FOREIGN KEY (origin_hub) REFERENCES Hub(hub_id),
    CONSTRAINT fk_lane_destination_hub
        FOREIGN KEY (destination_hub) REFERENCES Hub(hub_id),
    CONSTRAINT chk_lane_hubs_distinct
        CHECK (origin_hub <> destination_hub)
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
        ON DELETE CASCADE
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
        CHECK (temp_min <= temp_max)
);

CREATE TABLE RailCar (
    vehicle_id  INT PRIMARY KEY,
    axle_count  INT          NOT NULL,
    track_gauge DECIMAL(8,2) NOT NULL,
    CONSTRAINT fk_railcar_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id)
        ON DELETE CASCADE
);

CREATE TABLE Departure (
    departure_id       INT AUTO_INCREMENT PRIMARY KEY,
    vehicle_id         INT           NOT NULL,
    origin_hub         CHAR(3)       NOT NULL,
    destination_hub    CHAR(3)       NOT NULL,
    departure_datetime DATETIME      NOT NULL,
    max_weight         DECIMAL(10,2) NOT NULL,
    booked_weight      DECIMAL(10,2) NOT NULL DEFAULT 0,
    remaining_weight   DECIMAL(10,2) AS (max_weight - booked_weight) VIRTUAL,
    CONSTRAINT fk_departure_vehicle
        FOREIGN KEY (vehicle_id) REFERENCES Vehicle(vehicle_id),
    CONSTRAINT fk_departure_lane
        FOREIGN KEY (origin_hub, destination_hub)
        REFERENCES Lane(origin_hub, destination_hub),
    CONSTRAINT chk_departure_max_weight_positive
        CHECK (max_weight > 0),
    CONSTRAINT chk_departure_booked_weight_range
        CHECK (booked_weight >= 0 AND booked_weight <= max_weight)
);

CREATE TABLE Shipment (
    shipment_id       INT AUTO_INCREMENT PRIMARY KEY,
    shipper_id        INT           NOT NULL,
    origin_hub        CHAR(3)       NOT NULL,
    destination_hub   CHAR(3)       NOT NULL,
    weight            DECIMAL(10,2) NOT NULL,
    promised_delivery DATE          NOT NULL,
    departure_id      INT           NULL,
    CONSTRAINT fk_shipment_shipper
        FOREIGN KEY (shipper_id) REFERENCES Shipper(shipper_id),
    CONSTRAINT fk_shipment_lane
        FOREIGN KEY (origin_hub, destination_hub)
        REFERENCES Lane(origin_hub, destination_hub),
    CONSTRAINT fk_shipment_departure
        FOREIGN KEY (departure_id) REFERENCES Departure(departure_id),
    CONSTRAINT chk_shipment_weight_positive
        CHECK (weight > 0)
);

CREATE TABLE ScanEvent (
    shipment_id     INT      NOT NULL,
    timestamp       DATETIME NOT NULL,
    hub_id          CHAR(3)  NOT NULL,
    shipment_status ENUM('RECEIVED','IN_TRANSIT','ARRIVED_AT_HUB',
                         'OUT_FOR_DELIVERY','DELIVERED') NOT NULL,
    PRIMARY KEY (shipment_id, timestamp),
    CONSTRAINT fk_scanevent_shipment
        FOREIGN KEY (shipment_id) REFERENCES Shipment(shipment_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_scanevent_hub
        FOREIGN KEY (hub_id) REFERENCES Hub(hub_id)
        ON UPDATE CASCADE
);

