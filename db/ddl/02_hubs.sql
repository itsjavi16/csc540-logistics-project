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
