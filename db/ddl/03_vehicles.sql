CREATE TABLE Vehicle (
    vehicle_id      INT AUTO_INCREMENT PRIMARY KEY,
    carrier_id      INT NOT NULL,
    home_hub_id     INT NOT NULL,
    vehicle_type    ENUM('BOX_TRUCK','REFRIGERATED_VAN','RAIL_CAR') NOT NULL,
    CONSTRAINT fk_vehicle_carrier
        FOREIGN KEY (carrier_id) REFERENCES Carrier(account_id),
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