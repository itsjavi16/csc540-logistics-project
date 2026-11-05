-- Book Shipment onto Departure (required procedure).
--
-- Usage:
--   CALL book_shipment(shipment_id, departure_id, shipper_id, @ok, @msg);
--   SELECT @ok, @msg;
-- Pass NULL as shipper_id to skip the ownership check (admin / data loading).
--
-- Everything happens in one transaction. The departure row is locked first
-- (SELECT ... FOR UPDATE), so two bookings competing for the same departure
-- run one after the other: the second one waits, then sums the bookings
-- including the first one's, so the departure can never be overbooked.
-- Note: START TRANSACTION commits any transaction the caller left open.

DROP PROCEDURE IF EXISTS book_shipment;

DELIMITER $$

CREATE PROCEDURE book_shipment(
    IN  p_shipment_id  INT,
    IN  p_departure_id INT,
    IN  p_shipper_id   INT,
    OUT p_success      BOOLEAN,
    OUT p_message      VARCHAR(255)
)
proc: BEGIN
    DECLARE v_max_weight     DECIMAL(10,2);
    DECLARE v_dep_origin     CHAR(3);
    DECLARE v_dep_dest       CHAR(3);
    DECLARE v_owner          INT;
    DECLARE v_ship_origin    CHAR(3);
    DECLARE v_ship_dest      CHAR(3);
    DECLARE v_weight         DECIMAL(10,2);
    DECLARE v_status         VARCHAR(20);
    DECLARE v_booked         DECIMAL(10,2);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    SET p_success = FALSE;
    START TRANSACTION;

    -- 1. Lock the departure. Competing bookings for it wait here.
    SELECT max_weight, origin_hub, destination_hub
      INTO v_max_weight, v_dep_origin, v_dep_dest
      FROM Departure
     WHERE departure_id = p_departure_id
       FOR UPDATE;

    IF v_max_weight IS NULL THEN
        ROLLBACK;
        SET p_message = CONCAT('Departure ', p_departure_id, ' does not exist.');
        LEAVE proc;
    END IF;

    -- 2. Lock and read the shipment.
    SELECT shipper_id, origin_hub, destination_hub, weight, current_status
      INTO v_owner, v_ship_origin, v_ship_dest, v_weight, v_status
      FROM Shipment
     WHERE shipment_id = p_shipment_id
       FOR UPDATE;

    IF v_weight IS NULL THEN
        ROLLBACK;
        SET p_message = CONCAT('Shipment ', p_shipment_id, ' does not exist.');
        LEAVE proc;
    END IF;

    IF p_shipper_id IS NOT NULL AND v_owner <> p_shipper_id THEN
        ROLLBACK;
        SET p_message = CONCAT('Shipment ', p_shipment_id, ' does not belong to this shipper.');
        LEAVE proc;
    END IF;

    IF EXISTS (SELECT 1 FROM Booking WHERE shipment_id = p_shipment_id) THEN
        ROLLBACK;
        SET p_message = CONCAT('Shipment ', p_shipment_id, ' is already booked.');
        LEAVE proc;
    END IF;

    IF v_status = 'DELIVERED' THEN
        ROLLBACK;
        SET p_message = CONCAT('Shipment ', p_shipment_id, ' has already been delivered.');
        LEAVE proc;
    END IF;

    -- 3. Eligibility: the departure must run the shipment's lane.
    IF v_dep_origin <> v_ship_origin OR v_dep_dest <> v_ship_dest THEN
        ROLLBACK;
        SET p_message = CONCAT('Departure ', p_departure_id, ' runs ', v_dep_origin, '->', v_dep_dest,
                               ' but shipment ', p_shipment_id, ' goes ', v_ship_origin, '->', v_ship_dest, '.');
        LEAVE proc;
    END IF;

    -- 4. Sum what is already booked (locking read: sees the latest committed bookings).
    SELECT COALESCE(SUM(s.weight), 0)
      INTO v_booked
      FROM Booking b
      JOIN Shipment s ON s.shipment_id = b.shipment_id
     WHERE b.departure_id = p_departure_id
      LOCK IN SHARE MODE;

    IF v_booked + v_weight > v_max_weight THEN
        ROLLBACK;
        SET p_message = CONCAT('Not enough capacity: departure ', p_departure_id, ' has ',
                               v_max_weight - v_booked, ' kg left, shipment weighs ', v_weight, ' kg.');
        LEAVE proc;
    END IF;

    -- 5. Record the booking.
    INSERT INTO Booking (shipment_id, departure_id) VALUES (p_shipment_id, p_departure_id);
    COMMIT;

    SET p_success = TRUE;
    SET p_message = CONCAT('Shipment ', p_shipment_id, ' booked on departure ', p_departure_id, '. ',
                           v_max_weight - v_booked - v_weight, ' kg left on this departure.');
END proc $$

DELIMITER ;
