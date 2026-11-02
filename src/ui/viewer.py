# Viewer screens (Project Application Flow: "Viewer pages")

import streamlit as st

from src.reports import viewer_reports
from src.ui.common import (
    check_range,
    date_range_inputs,
    db_call,
    header,
    menu,
    nav_buttons,
    parse_id,
    require_role,
    table,
)
from src.ui.shipper import show_history

ROLE = "VIEWER"
BASE = ["Viewer"]


def landing():
    require_role(ROLE)
    header("Viewer: Landing", BASE)
    menu(
        [
            ("Track Shipment", "viewer_track"),
            ("Published Performance Reports", "viewer_reports"),
            ("Logout", None),
        ]
    )


def track():
    require_role(ROLE)
    header("Viewer: Track Shipment", BASE + ["Track Shipment"])
    sid_text = st.text_input("A. Shipment ID", key="in_sid")
    if st.button("1. View History", type="primary"):
        sid, err = parse_id(sid_text, "shipment ID")
        if err:
            st.error(err)
        else:
            show_history(sid)
    nav_buttons([("2. GoBack", "viewer_landing"), ("3. LandingPage", "viewer_landing")])


def reports():
    require_role(ROLE)
    header("Viewer: Published Performance Reports", BASE + ["Reports"])
    menu(
        [
            ("On-Time Rates by Lane", "viewer_rep_lane"),
            ("On-Time Rates by Carrier", "viewer_rep_carrier"),
            ("Lane Volume Ranking", "viewer_rep_volume"),
            ("Top Departures per Lane", "viewer_rep_top"),
            ("Shipment Dwell Time", "viewer_rep_dwell"),
            ("Running Total Deliveries by Carrier", "viewer_rep_running"),
            ("At-Risk In-Transit Shipments", "viewer_rep_risk"),
            ("GoBack", "viewer_landing"),
            ("LandingPage", "viewer_landing"),
        ]
    )


def _report_nav():
    nav_buttons([("2. GoBack", "viewer_reports"), ("3. LandingPage", "viewer_landing")])


def rep_lane():
    require_role(ROLE)
    header("Viewer: On-Time Rates by Lane", BASE + ["Reports", "On-Time by Lane"])
    st.caption("Shipments delivered in the selected range, grouped by lane.")
    start, end = date_range_inputs()
    if st.button("1. View Report", type="primary") and check_range(start, end):
        table(
            db_call(viewer_reports.on_time_by_lane, start, end),
            {
                "origin_hub": "Origin",
                "destination_hub": "Destination",
                "delivered": "Delivered",
                "on_time": "On time",
                "late": "Late",
                "on_time_pct": "On-time %",
                "late_pct": "Late %",
            },
            empty="No deliveries in this range.",
        )
    _report_nav()


def rep_carrier():
    require_role(ROLE)
    header("Viewer: On-Time Rates by Carrier", BASE + ["Reports", "On-Time by Carrier"])
    st.caption(
        "Carriers ranked by on-time rate for shipments delivered in the selected range."
    )
    start, end = date_range_inputs()
    if st.button("1. View Report", type="primary") and check_range(start, end):
        table(
            db_call(viewer_reports.on_time_by_carrier, start, end),
            {
                "carrier_rank": "Rank",
                "carrier_id": "Carrier",
                "company_name": "Company",
                "delivered": "Delivered",
                "on_time": "On time",
                "late": "Late",
                "on_time_pct": "On-time %",
            },
            empty="No deliveries in this range.",
        )
    _report_nav()


def rep_volume():
    require_role(ROLE)
    header("Viewer: Lane Volume Ranking", BASE + ["Reports", "Lane Volume"])
    st.caption(
        "Lanes ranked by total weight of shipments booked on departures in the selected range."
    )
    start, end = date_range_inputs()
    if st.button("1. View Report", type="primary") and check_range(start, end):
        table(
            db_call(viewer_reports.lane_volume_ranking, start, end),
            {
                "lane_rank": "Rank",
                "origin_hub": "Origin",
                "destination_hub": "Destination",
                "shipments": "Shipments",
                "total_kg": "Total (kg)",
            },
            empty="No booked shipments in this range.",
        )
    _report_nav()


def rep_top():
    require_role(ROLE)
    header("Viewer: Top Departures per Lane", BASE + ["Reports", "Top Departures"])
    st.caption(
        "Within each lane, departures in the selected range ranked by booked load."
    )
    start, end = date_range_inputs()
    n = st.number_input("C. Top N", min_value=1, value=3, step=1, key="in_n")
    if st.button("1. View Report", type="primary") and check_range(start, end):
        table(
            db_call(viewer_reports.top_departures_per_lane, start, end, n),
            {
                "origin_hub": "Origin",
                "destination_hub": "Destination",
                "lane_rank": "Rank in lane",
                "departure_id": "Departure",
                "departure_datetime": "Scheduled",
                "booked_weight": "Booked (kg)",
                "max_weight": "Capacity (kg)",
            },
            empty="No departures in this range.",
        )
    _report_nav()


def rep_dwell():
    require_role(ROLE)
    header("Viewer: Shipment Dwell Time", BASE + ["Reports", "Dwell Time"])
    sid_text = st.text_input("A. Shipment ID", key="in_sid")
    if st.button("1. View Report", type="primary"):
        sid, err = parse_id(sid_text, "shipment ID")
        if err:
            st.error(err)
        else:
            table(
                db_call(viewer_reports.dwell_time, sid),
                {
                    "scan_seq": "#",
                    "timestamp": "Timestamp",
                    "hub_id": "Hub",
                    "shipment_status": "Status",
                    "previous_scan": "Previous scan",
                    "minutes_since_previous": "Minutes since previous",
                },
                empty=f"Shipment {sid} has no scans (or doesn't exist).",
            )
    _report_nav()


def rep_running():
    require_role(ROLE)
    header(
        "Viewer: Running Total Deliveries by Carrier",
        BASE + ["Reports", "Running Total"],
    )
    st.caption(
        "Cumulative delivered shipments (and kilograms) per carrier, by delivery date."
    )
    start, end = date_range_inputs()
    cid_text = st.text_input("C. Carrier ID (optional)", key="in_cid")
    if st.button("1. View Report", type="primary") and check_range(start, end):
        cid, err = (
            (None, None) if not cid_text.strip() else parse_id(cid_text, "carrier ID")
        )
        if err:
            st.error(err)
        else:
            table(
                db_call(viewer_reports.running_total_deliveries, start, end, cid),
                {
                    "carrier_id": "Carrier",
                    "company_name": "Company",
                    "delivery_date": "Date",
                    "delivered": "Delivered that day",
                    "kg": "Kg that day",
                    "cumulative_delivered": "Cumulative shipments",
                    "cumulative_kg": "Cumulative kg",
                },
                empty="No deliveries in this range.",
            )
    _report_nav()


def rep_risk():
    require_role(ROLE)
    header("Viewer: At-Risk In-Transit Shipments", BASE + ["Reports", "At-Risk"])
    n = st.number_input("A. N Days", min_value=0, value=3, step=1, key="in_n")
    if st.button("1. View Report", type="primary"):
        st.caption(
            f"In-transit shipments whose promised date has passed or is within {n} day(s)."
        )
        table(
            db_call(viewer_reports.at_risk_in_transit, n), empty="No shipments at risk."
        )
    _report_nav()


PAGES = {
    "viewer_landing": landing,
    "viewer_track": track,
    "viewer_reports": reports,
    "viewer_rep_lane": rep_lane,
    "viewer_rep_carrier": rep_carrier,
    "viewer_rep_volume": rep_volume,
    "viewer_rep_top": rep_top,
    "viewer_rep_dwell": rep_dwell,
    "viewer_rep_running": rep_running,
    "viewer_rep_risk": rep_risk,
}
