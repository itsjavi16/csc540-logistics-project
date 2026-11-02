"""Report pieces shared by several roles."""

from src.db.helpers import fetch_all


def dwell_time(shipment_id):
    """Time between each consecutive pair of scans for one shipment (window function LAG)."""
    return fetch_all(
        """SELECT scan_seq,
                  `timestamp`,
                  hub_id,
                  shipment_status,
                  LAG(`timestamp`) OVER (ORDER BY scan_seq) AS previous_scan,
                  TIMESTAMPDIFF(MINUTE, LAG(`timestamp`) OVER (ORDER BY scan_seq), `timestamp`)
                      AS minutes_since_previous
           FROM ScanEvent
           WHERE shipment_id = %s
           ORDER BY scan_seq""",
        (shipment_id,),
    )


def pct(part, whole):
    return round(100.0 * float(part) / float(whole), 1) if whole else None
