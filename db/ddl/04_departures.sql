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