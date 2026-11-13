-- Queries to be Implemented

-- 1. Show the number of vehicles of each type owned by each carrier.

SELECT cc.carrier_id,
       cc.company_name,
       v.vehicle_type,
       COUNT(*) AS vehicles
FROM CarrierCompany cc
JOIN Vehicle v ON v.carrier_id = cc.carrier_id
GROUP BY cc.carrier_id, cc.company_name, v.vehicle_type
ORDER BY cc.carrier_id, v.vehicle_type;

-- 2. For each lane, rank departures by weight utilization (booked weight as a percentage of maximum weight), and list the most heavily loaded departures per lane.

SET @top_n = 3;

WITH dep_load AS (
    SELECT d.departure_id, d.origin_hub, d.destination_hub, d.departure_datetime,
           d.max_weight, dl.booked_weight,
           ROUND(100 * dl.booked_weight / d.max_weight, 2) AS utilization_pct
    FROM Departure d
    JOIN DepartureLoad dl ON dl.departure_id = d.departure_id
), ranked AS (
    SELECT dep_load.*,
           RANK() OVER (PARTITION BY origin_hub, destination_hub
                        ORDER BY utilization_pct DESC) AS lane_rank
    FROM dep_load
)
SELECT origin_hub, destination_hub, lane_rank, departure_id, departure_datetime,
       booked_weight, max_weight, utilization_pct
FROM ranked
WHERE lane_rank <= @top_n
ORDER BY origin_hub, destination_hub, lane_rank, departure_id;

-- 3. For a given shipment, compute the time elapsed between each consecutive pair of scan events (the dwell time at each step of its journey).

SET @shipment_id = 1;

SELECT scan_seq,
       `timestamp`,
       hub_id,
       shipment_status,
       LAG(`timestamp`) OVER (ORDER BY scan_seq) AS previous_scan,
       TIMEDIFF(`timestamp`, LAG(`timestamp`) OVER (ORDER BY scan_seq)) AS time_since_previous
FROM ScanEvent
WHERE shipment_id = @shipment_id
ORDER BY scan_seq;

-- 4. For each carrier, compute a running total of shipment weight delivered over time (for example, cumulative delivered kilograms by week).

WITH delivered AS (
    SELECT v.carrier_id, s.weight, e.`timestamp` AS delivered_at
    FROM ScanEvent e
    JOIN Shipment  s ON s.shipment_id  = e.shipment_id
    JOIN Booking   b ON b.shipment_id  = s.shipment_id
    JOIN Departure d ON d.departure_id = b.departure_id
    JOIN Vehicle   v ON v.vehicle_id   = d.vehicle_id
    WHERE e.shipment_status = 'DELIVERED'
), weekly AS (
    SELECT carrier_id,
           DATE(delivered_at) - INTERVAL WEEKDAY(delivered_at) DAY AS week_start,
           SUM(weight) AS kg_delivered
    FROM delivered
    GROUP BY carrier_id, week_start
)
SELECT cc.carrier_id,
       cc.company_name,
       w.week_start,
       w.kg_delivered,
       SUM(w.kg_delivered) OVER (PARTITION BY w.carrier_id ORDER BY w.week_start
                                 ROWS UNBOUNDED PRECEDING) AS cumulative_kg
FROM weekly w
JOIN CarrierCompany cc ON cc.carrier_id = w.carrier_id
ORDER BY cc.carrier_id, w.week_start;

-- 5. Find departures carrying shipments belonging to at least two different shippers. Show the departure ID and the number of distinct shippers. 
SELECT b.departure_id,
       COUNT(DISTINCT s.user_id) AS distinct_shippers
FROM Booking b
JOIN Shipment s ON s.shipment_id = b.shipment_id
GROUP BY b.departure_id
HAVING COUNT(DISTINCT s.user_id) >= 2
ORDER BY b.departure_id;

-- 6. List shipments that have no scan events recorded. Include the shipment ID, owning shipper, origin hub, destination hub, and promised delivery date.

SELECT s.shipment_id,
       s.user_id AS shipper_user_id,
       u.display_name AS shipper_name,
       s.origin_hub,
       s.destination_hub,
       s.promised_delivery
FROM Shipment s
JOIN User u ON u.user_id = s.user_id
WHERE NOT EXISTS (SELECT 1 FROM ScanEvent e WHERE e.shipment_id = s.shipment_id)
ORDER BY s.shipment_id;
