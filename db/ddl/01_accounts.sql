CREATE TABLE Account (
    account_id INT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Shipper (
    account_id INT PRIMARY KEY,
    FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE
);

CREATE TABLE Carrier (
    account_id   INT PRIMARY KEY,
    company_name VARCHAR(100) NOT NULL,
    FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE
);

CREATE TABLE Viewer (
    account_id INT PRIMARY KEY,
    FOREIGN KEY (account_id) REFERENCES Account(account_id) ON DELETE CASCADE
);