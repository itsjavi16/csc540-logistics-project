CREATE TABLE Shipment (
    shipment_id       INT AUTO_INCREMENT PRIMARY KEY,
    shipper_id        INT           NOT NULL,
    origin_hub        CHAR(3)       NOT NULL,
    destination_hub   CHAR(3)       NOT NULL,
    weight            DECIMAL(10,2) NOT NULL,
    promised_delivery DATE          NOT NULL,
    departure_id      INT           NULL,
    CONSTRAINT fk_shipment_shipping_company
        FOREIGN KEY (shipper_id) REFERENCES ShippingCompany(shipper_id),
    CONSTRAINT fk_shipment_lane
        FOREIGN KEY (origin_hub, destination_hub)
        REFERENCES Lane(origin_hub, destination_hub),
    CONSTRAINT fk_shipment_departure
        FOREIGN KEY (departure_id) REFERENCES Departure(departure_id),
    CONSTRAINT chk_shipment_weight_positive
        CHECK (weight > 0)
);
