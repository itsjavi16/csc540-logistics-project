CREATE TABLE Account (
    account_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Shipper (
    account_id INT PRIMARY KEY,
    FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE
);

CREATE TABLE CarrierOrg (
    carrier_org_id INT AUTO_INCREMENT PRIMARY KEY,
    company_name   VARCHAR(100) NOT NULL
);

CREATE TABLE Carrier (
    account_id     INT PRIMARY KEY,
    carrier_org_id INT NOT NULL,
    CONSTRAINT fk_carrier_account
        FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE,
    CONSTRAINT fk_carrier_carrierorg
        FOREIGN KEY (carrier_org_id) REFERENCES CarrierOrg(carrier_org_id)
);

CREATE TABLE Viewer (
    account_id INT PRIMARY KEY,
    FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE
);
