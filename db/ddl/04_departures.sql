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
