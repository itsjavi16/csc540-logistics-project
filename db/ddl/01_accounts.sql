CREATE TABLE User (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name  VARCHAR(100) NOT NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    role_type     ENUM('SHIPPER','CARRIER','VIEWER') NOT NULL
);

CREATE TABLE Shipper (
    user_id    INT PRIMARY KEY,
    shipper_id INT NOT NULL UNIQUE,
    CONSTRAINT fk_shipper_user
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);

CREATE TABLE CarrierCompany (
    carrier_id   INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL
);

CREATE TABLE Carrier (
    user_id    INT PRIMARY KEY,
    carrier_id INT NOT NULL,
    CONSTRAINT fk_carrier_user
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    CONSTRAINT fk_carrier_company
        FOREIGN KEY (carrier_id) REFERENCES CarrierCompany(carrier_id)
);

CREATE TABLE Viewer (
    user_id INT PRIMARY KEY,
    CONSTRAINT fk_viewer_user
        FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE
);
