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
