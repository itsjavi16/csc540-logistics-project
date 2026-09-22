CREATE TABLE Hub (
    hub_id          INT AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(100) NOT NULL,
    region          ENUM('Northeast','Southeast','Midwest','Southwest','West')
                    NOT NULL,
    address         VARCHAR(255)
);