CREATE TABLE Vehicle (
    vehicle_id   INT AUTO_INCREMENT PRIMARY KEY,
    carrier_id   INT     NOT NULL,
    home_hub_id  CHAR(3) NOT NULL,
    vehicle_type ENUM('BOX_TRUCK','REFRIGERATED_VAN','RAIL_CAR') NOT NULL,
    CONSTRAINT fk_vehicle_carrier
        FOREIGN KEY (carrier_id) REFERENCES Carrier(carrier_id),
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
