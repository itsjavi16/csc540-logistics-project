CREATE TABLE Shipment (
    shipment_id       INT AUTO_INCREMENT PRIMARY KEY,
    shipper_id        INT           NOT NULL,
    lane_id           INT           NOT NULL,
    weight            DECIMAL(10,2) NOT NULL,
    promised_delivery DATE          NOT NULL,
    departure_id      INT           NULL,
    CONSTRAINT fk_shipment_shipper
        FOREIGN KEY (shipper_id) REFERENCES Shipper(shipper_id),
    CONSTRAINT fk_shipment_lane
        FOREIGN KEY (lane_id) REFERENCES Lane(lane_id),
    CONSTRAINT fk_shipment_departure
        FOREIGN KEY (departure_id) REFERENCES Departure(departure_id),
    CONSTRAINT chk_shipment_weight_positive
        CHECK (weight > 0)
);
