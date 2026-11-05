-- Triggers. The first two are the ones the project requires; the others
-- move business rules from the application into the database.
--
--   trg_scan_chronology     (required) ScanEvent BEFORE INSERT
--   trg_scan_status         (required) ScanEvent AFTER INSERT
--   trg_booking_guard       Booking    BEFORE INSERT
--   trg_departure_guard     Departure  BEFORE UPDATE
--   trg_shipment_guard      Shipment   BEFORE UPDATE
--
-- Errors use SQLSTATE 45000; the message text is meant to be shown to the user.

DROP TRIGGER IF EXISTS trg_scan_chronology;
DROP TRIGGER IF EXISTS trg_scan_status;
DROP TRIGGER IF EXISTS trg_booking_guard;
DROP TRIGGER IF EXISTS trg_departure_guard;
DROP TRIGGER IF EXISTS trg_shipment_guard;

DELIMITER $$

-- Required: Enforce Scan Chronology.
-- Rejects a scan that predates the shipment's latest scan or moves its status
-- backwards, and numbers the scan (scan_seq) within the shipment's history.
CREATE TRIGGER trg_scan_chronology
BEFORE INSERT ON ScanEvent
FOR EACH ROW
BEGIN
    DECLARE v_last_seq    INT;
    DECLARE v_last_time   DATETIME;
    DECLARE v_last_status VARCHAR(20);
    DECLARE v_msg         VARCHAR(255);

    IF NOT EXISTS (SELECT 1 FROM Booking WHERE shipment_id = NEW.shipment_id) THEN
        SET v_msg = CONCAT('Shipment ', NEW.shipment_id, ' is not booked on a departure yet.');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;

    SELECT MAX(scan_seq) INTO v_last_seq
      FROM ScanEvent WHERE shipment_id = NEW.shipment_id;

    IF v_last_seq IS NOT NULL THEN
        SELECT `timestamp`, shipment_status INTO v_last_time, v_last_status
          FROM ScanEvent
         WHERE shipment_id = NEW.shipment_id AND scan_seq = v_last_seq;

        IF v_last_status = 'DELIVERED' THEN
            SET v_msg = CONCAT('Shipment ', NEW.shipment_id, ' was already delivered; no more scans allowed.');
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
        END IF;

        IF NEW.`timestamp` < v_last_time THEN
            SET v_msg = CONCAT('Scan time ', NEW.`timestamp`, ' is before the shipment''s latest scan (',
                               v_last_time, ').');
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
        END IF;

        IF FIELD(NEW.shipment_status, 'RECEIVED','IN_TRANSIT','ARRIVED_AT_HUB','OUT_FOR_DELIVERY','DELIVERED')
         < FIELD(v_last_status,       'RECEIVED','IN_TRANSIT','ARRIVED_AT_HUB','OUT_FOR_DELIVERY','DELIVERED') THEN
            SET v_msg = CONCAT('Status cannot go back from ', v_last_status, ' to ', NEW.shipment_status, '.');
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
        END IF;
    END IF;

    -- Number the scan. An explicit scan_seq is accepted only if it is the next one.
    IF NEW.scan_seq IS NULL OR NEW.scan_seq = 0 THEN
        SET NEW.scan_seq = COALESCE(v_last_seq, 0) + 1;
    ELSEIF NEW.scan_seq <> COALESCE(v_last_seq, 0) + 1 THEN
        SET v_msg = CONCAT('scan_seq must be ', COALESCE(v_last_seq, 0) + 1, ' for shipment ', NEW.shipment_id, '.');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;
END $$

-- Required: Maintain Status and Flag Late Delivery.
-- On time = the delivering scan falls on or before the end of the promised date.
CREATE TRIGGER trg_scan_status
AFTER INSERT ON ScanEvent
FOR EACH ROW
BEGIN
    UPDATE Shipment
       SET current_status  = NEW.shipment_status,
           on_time_outcome = CASE
               WHEN NEW.shipment_status = 'DELIVERED' THEN
                   IF(NEW.`timestamp` < promised_delivery + INTERVAL 1 DAY, 'ON_TIME', 'LATE')
               ELSE on_time_outcome
           END
     WHERE shipment_id = NEW.shipment_id;
END $$

-- Bookings must match the departure's lane and fit its capacity, even if
-- someone inserts into Booking directly instead of calling book_shipment.
CREATE TRIGGER trg_booking_guard
BEFORE INSERT ON Booking
FOR EACH ROW
BEGIN
    DECLARE v_ship_origin CHAR(3);
    DECLARE v_ship_dest   CHAR(3);
    DECLARE v_weight      DECIMAL(10,2);
    DECLARE v_dep_origin  CHAR(3);
    DECLARE v_dep_dest    CHAR(3);
    DECLARE v_max         DECIMAL(10,2);
    DECLARE v_booked      DECIMAL(10,2);
    DECLARE v_msg         VARCHAR(255);

    SELECT origin_hub, destination_hub, weight INTO v_ship_origin, v_ship_dest, v_weight
      FROM Shipment WHERE shipment_id = NEW.shipment_id;
    SELECT origin_hub, destination_hub, max_weight INTO v_dep_origin, v_dep_dest, v_max
      FROM Departure WHERE departure_id = NEW.departure_id;

    IF v_dep_origin <> v_ship_origin OR v_dep_dest <> v_ship_dest THEN
        SET v_msg = CONCAT('Departure ', NEW.departure_id, ' does not run shipment ', NEW.shipment_id, '''s lane.');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;

    SELECT COALESCE(SUM(s.weight), 0) INTO v_booked
      FROM Booking b JOIN Shipment s ON s.shipment_id = b.shipment_id
     WHERE b.departure_id = NEW.departure_id;

    IF v_booked + v_weight > v_max THEN
        SET v_msg = CONCAT('Departure ', NEW.departure_id, ' would be overbooked.');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;
END $$

-- A departure's capacity can't drop below what is already booked, and its
-- lane can't change once shipments are booked on it.
CREATE TRIGGER trg_departure_guard
BEFORE UPDATE ON Departure
FOR EACH ROW
BEGIN
    DECLARE v_booked DECIMAL(10,2);
    DECLARE v_msg    VARCHAR(255);

    SELECT COALESCE(SUM(s.weight), 0) INTO v_booked
      FROM Booking b JOIN Shipment s ON s.shipment_id = b.shipment_id
     WHERE b.departure_id = OLD.departure_id;

    IF NEW.max_weight < v_booked THEN
        SET v_msg = CONCAT('Capacity can''t go below the ', v_booked, ' kg already booked.');
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = v_msg;
    END IF;

    IF v_booked > 0 AND (NEW.origin_hub <> OLD.origin_hub OR NEW.destination_hub <> OLD.destination_hub) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Can''t change the lane of a departure that has bookings.';
    END IF;
END $$

-- Once a shipment is booked, its lane and weight are fixed (they were checked
-- against the departure). The owner never changes, and the promised date is
-- fixed once the shipment is delivered (it decided on-time vs. late).
CREATE TRIGGER trg_shipment_guard
BEFORE UPDATE ON Shipment
FOR EACH ROW
BEGIN
    IF NEW.shipper_id <> OLD.shipper_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A shipment''s owner can''t be changed.';
    END IF;

    IF (NEW.origin_hub <> OLD.origin_hub OR NEW.destination_hub <> OLD.destination_hub
        OR NEW.weight <> OLD.weight)
       AND EXISTS (SELECT 1 FROM Booking WHERE shipment_id = OLD.shipment_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Lane and weight can''t change after the shipment is booked.';
    END IF;

    IF NEW.promised_delivery <> OLD.promised_delivery AND OLD.current_status = 'DELIVERED' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Promised date can''t change after delivery.';
    END IF;
END $$

DELIMITER ;
