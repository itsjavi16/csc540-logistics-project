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