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