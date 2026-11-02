# Shipper screens (Project Application Flow: "Shipper pages")

import streamlit as st

from src.models import shipments
from src.models.hubs import list_hubs, list_lanes
from src.reports import shipper_reports
from src.ui.common import (
    check_range,
    date_range_inputs,
    db_call,
    flash,
    go,
    header,
    hub_input,
    menu,
    nav_buttons,
    parse_id,
    reference,
    require_role,
    show_result,
    status_label,
    table,
)

ROLE = "SHIPPER"
BASE = ["Shipper"]


def landing():
    require_role(ROLE)
    header("Shipper: Landing", BASE)
    menu(
        [
            ("Manage Shipments", "shipper_manage"),
            ("Reports", "shipper_reports"),
            ("Logout", None),
        ]
    )


def manage():
    require_role(ROLE)
    header("Shipper: Manage Shipments", BASE + ["Manage Shipments"])
    menu(
        [
            ("Create Shipment", "shipper_create"),
            ("Update Shipment", "shipper_update"),
            ("Book Shipment onto Departure", "shipper_book"),
            ("Track Shipment", "shipper_track"),
            ("GoBack", "shipper_landing"),
            ("LandingPage", "shipper_landing"),
        ]
    )


def _lane_reference():
    reference("Hubs", db_call(list_hubs))
    reference("Lanes (valid origin -> destination pairs)", db_call(list_lanes))


def _my_shipments(u):
    reference(
        "Your shipments", db_call(shipments.list_shipper_shipments, u["shipper_id"])
    )


def create():
    u = require_role(ROLE)
    header("Shipper: Create Shipment", BASE + ["Manage Shipments", "Create Shipment"])
    _lane_reference()
    with st.form("create_form"):
        origin = hub_input("A. Origin Hub ID", "in_origin")
        dest = hub_input("B. Destination Hub ID", "in_dest")
        weight = st.number_input(
            "C. Weight (kg)", min_value=0.0, step=10.0, key="in_weight"
        )
        promised = st.date_input("D. Promised Delivery Date", key="in_promised")
        save = st.form_submit_button("1. Save", type="primary")
    nav_buttons(
        [("2. Cancel", "shipper_manage"), ("3. LandingPage", "shipper_landing")]
    )
    if save:
        res = db_call(
            shipments.create_shipment, u["shipper_id"], origin, dest, weight, promised
        )
        if res.ok:
            flash(res)
            go("shipper_manage")
            st.rerun()
        show_result(res)


def update():
    u = require_role(ROLE)
    header("Shipper: Update Shipment", BASE + ["Manage Shipments", "Update Shipment"])
    st.caption(
        "Lane and weight can't change once a shipment is booked; the promised date can't change after delivery."
    )
    _my_shipments(u)
    _lane_reference()

    sid_text = st.text_input("A. Shipment ID", key="in_sid")
    sid, err = parse_id(sid_text, "shipment ID") if sid_text else (None, None)
    current = (
        db_call(shipments.get_owned_shipment, u["shipper_id"], sid) if sid else None
    )
    if sid_text and err:
        st.error(err)
    elif sid and current is None:
        st.error(f"Shipment {sid} doesn't exist or isn't yours.")

    if current:
        with st.form(f"update_form_{sid}"):
            origin = hub_input(
                "B. Origin Hub ID", f"in_origin_{sid}", current["origin_hub"]
            )
            dest = hub_input(
                "C. Destination Hub ID", f"in_dest_{sid}", current["destination_hub"]
            )
            weight = st.number_input(
                "D. Weight (kg)",
                min_value=0.0,
                step=10.0,
                value=float(current["weight"]),
                key=f"in_weight_{sid}",
            )
            promised = st.date_input(
                "E. Promised Delivery Date",
                value=current["promised_delivery"],
                key=f"in_promised_{sid}",
            )
            save = st.form_submit_button("1. Save", type="primary")
        if save:
            res = db_call(
                shipments.update_shipment,
                u["shipper_id"],
                sid,
                origin,
                dest,
                weight,
                promised,
            )
            if res.ok:
                flash(res)
                go("shipper_manage")
                st.rerun()
            show_result(res)
    nav_buttons(
        [("2. Cancel", "shipper_manage"), ("3. LandingPage", "shipper_landing")]
    )


def book():
    u = require_role(ROLE)
    header(
        "Shipper: Book Shipment onto Departure",
        BASE + ["Manage Shipments", "Book Shipment"],
    )
    st.caption(
        "A departure is eligible when its origin and destination match the shipment's and it has room "
        "for the shipment's weight. The capacity check and the booking happen in one transaction."
    )
    _my_shipments(u)

    sid_text = st.text_input("A. Shipment ID", key="in_sid")
    sid, err = parse_id(sid_text, "shipment ID") if sid_text else (None, None)
    if sid_text and err:
        st.error(err)
    elif sid:
        owned = db_call(shipments.get_owned_shipment, u["shipper_id"], sid)
        if owned is None:
            st.error(f"Shipment {sid} doesn't exist or isn't yours.")
        else:
            st.write(
                f"Shipment {sid}: {owned['origin_hub']} → {owned['destination_hub']}, {owned['weight']} kg"
            )
            reference(
                "Eligible departures for this shipment",
                db_call(shipments.eligible_departures, sid),
            )

    did_text = st.text_input("B. Departure ID", key="in_did")
    if st.button("1. Book", type="primary"):
        did, err2 = parse_id(did_text, "departure ID")
        if err or err2 or sid is None:
            st.error(err or err2 or "Enter the shipment ID.")
        else:
            res = db_call(shipments.book_shipment, u["shipper_id"], sid, did)
            if res.ok:
                flash(res)
                go("shipper_manage")
                st.rerun()
            show_result(res)
    nav_buttons(
        [("2. Cancel", "shipper_manage"), ("3. LandingPage", "shipper_landing")]
    )


def track():
    u = require_role(ROLE)
    header("Shipper: Track Shipment", BASE + ["Manage Shipments", "Track Shipment"])
    _my_shipments(u)
    sid_text = st.text_input("A. Shipment ID", key="in_sid")
    if st.button("1. View History", type="primary"):
        sid, err = parse_id(sid_text, "shipment ID")
        if err:
            st.error(err)
        elif db_call(shipments.get_owned_shipment, u["shipper_id"], sid) is None:
            st.error(f"Shipment {sid} doesn't exist or isn't yours.")
        else:
            show_history(sid)
    nav_buttons(
        [("2. GoBack", "shipper_manage"), ("3. LandingPage", "shipper_landing")]
    )


def show_history(sid):
    # Current status and full scan history (also used by the Viewer)
    s = db_call(shipments.get_shipment, sid)
    if s is None:
        st.error(f"Shipment {sid} doesn't exist.")
        return
    c = st.columns(4)
    c[0].metric("Current status", status_label(s["current_status"]))
    c[1].metric("Lane", f"{s['origin_hub']} → {s['destination_hub']}")
    c[2].metric("Promised delivery", str(s["promised_delivery"]))
    c[3].metric(
        "Outcome", status_label(s["on_time_outcome"]) if s["on_time_outcome"] else "—"
    )
    st.caption(
        f"Departure: {s['departure_id'] or 'not booked yet'}  ·  Weight: {s['weight']} kg"
    )
    table(
        db_call(shipments.scan_history, sid),
        {
            "scan_seq": "#",
            "timestamp": "Timestamp",
            "hub_id": "Hub",
            "hub_name": "Hub name",
            "shipment_status": "Status",
        },
        empty="No scans recorded yet.",
    )


# Reports


def reports():
    require_role(ROLE)
    header("Shipper: Reports", BASE + ["Reports"])
    menu(
        [
            ("On-Time vs Late Summary", "shipper_rep_ontime"),
            ("In-Transit Shipments", "shipper_rep_transit"),
            ("Shipments Near Promise Date", "shipper_rep_near"),
            ("GoBack", "shipper_landing"),
            ("LandingPage", "shipper_landing"),
        ]
    )


def rep_ontime():
    u = require_role(ROLE)
    header("Shipper: On-Time vs Late Summary", BASE + ["Reports", "On-Time vs Late"])
    st.caption(
        "Counts your shipments delivered (by delivery date) in the selected range."
    )
    start, end = date_range_inputs()
    if st.button("1. View Report", type="primary") and check_range(start, end):
        r = db_call(shipper_reports.on_time_summary, u["shipper_id"], start, end)
        c = st.columns(3)
        c[0].metric("Delivered", r["delivered"])
        c[1].metric(
            "On time",
            r["on_time"],
            f"{r['on_time_pct']}%" if r["on_time_pct"] is not None else None,
            delta_color="off",
        )
        c[2].metric(
            "Late",
            r["late"],
            f"{r['late_pct']}%" if r["late_pct"] is not None else None,
            delta_color="off",
        )
        if not r["delivered"]:
            st.info("No deliveries in this range.")
    nav_buttons(
        [("2. GoBack", "shipper_reports"), ("3. LandingPage", "shipper_landing")]
    )


def rep_transit():
    u = require_role(ROLE)
    header("Shipper: In-Transit Shipments", BASE + ["Reports", "In-Transit"])
    st.caption("Your shipments that have not reached Delivered.")
    table(
        db_call(shipper_reports.in_transit, u["shipper_id"]),
        empty="None of your shipments are in transit.",
    )
    nav_buttons(
        [("1. GoBack", "shipper_reports"), ("2. LandingPage", "shipper_landing")]
    )


def rep_near():
    u = require_role(ROLE)
    header(
        "Shipper: Shipments Near Promise Date", BASE + ["Reports", "Near Promise Date"]
    )
    n = st.number_input("A. N Days", min_value=0, value=3, step=1, key="in_n")
    if st.button("1. View Report", type="primary"):
        st.caption(
            f"In-transit shipments whose promised date has passed or is within {n} day(s)."
        )
        table(
            db_call(shipper_reports.near_promise_date, u["shipper_id"], n),
            empty="No in-transit shipments are near their promised date.",
        )
    nav_buttons(
        [("2. GoBack", "shipper_reports"), ("3. LandingPage", "shipper_landing")]
    )


PAGES = {
    "shipper_landing": landing,
    "shipper_manage": manage,
    "shipper_create": create,
    "shipper_update": update,
    "shipper_book": book,
    "shipper_track": track,
    "shipper_reports": reports,
    "shipper_rep_ontime": rep_ontime,
    "shipper_rep_transit": rep_transit,
    "shipper_rep_near": rep_near,
}
