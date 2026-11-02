# Carrier screens (Project Application Flow: "Carrier pages")

# A carrier login acts for its company: vehicles and departures "owned by the current carrier" are the company's (CarrierCompany)

import streamlit as st

from src.models import departures, vehicles
from src.models.hubs import list_hubs, list_lanes
from src.models.scans import STATUSES, post_scan
from src.reports import carrier_reports
from src.ui.common import (
    check_range,
    date_range_inputs,
    datetime_inputs,
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
    table,
)

ROLE = "CARRIER"
BASE = ["Carrier"]


def landing():
    require_role(ROLE)
    header("Carrier: Landing", BASE)
    menu(
        [
            ("Manage Vehicles", "carrier_vehicles"),
            ("Manage Departures", "carrier_departures"),
            ("Post Scan Event", "carrier_scan"),
            ("Reports", "carrier_reports"),
            ("Logout", None),
        ]
    )


# Vehicles


def manage_vehicles():
    require_role(ROLE)
    header("Carrier: Manage Vehicles", BASE + ["Manage Vehicles"])
    menu(
        [
            ("Add New Vehicle", "carrier_vehicle_add"),
            ("Update Vehicle", "carrier_vehicle_update"),
            ("View Vehicles", "carrier_vehicle_view"),
            ("GoBack", "carrier_landing"),
            ("LandingPage", "carrier_landing"),
        ]
    )


def add_vehicle():
    u = require_role(ROLE)
    header("Carrier: Add New Vehicle", BASE + ["Manage Vehicles", "Add New Vehicle"])
    reference("Hubs", db_call(list_hubs))
    with st.form("vehicle_common"):
        vid_text = st.text_input(
            "A. Vehicle ID", key="in_vid", help="Leave blank to have one assigned."
        )
        hub = hub_input("B. Home Hub ID", "in_hub")
        vtype = st.selectbox(
            "C. Vehicle Type",
            list(vehicles.TYPES),
            format_func=vehicles.TYPES.get,
            key="in_type",
        )
        cont = st.form_submit_button("1. Continue", type="primary")
    nav_buttons(
        [("2. GoBack", "carrier_vehicles"), ("3. LandingPage", "carrier_landing")]
    )
    if cont:
        vid, err = (
            (None, None) if not vid_text.strip() else parse_id(vid_text, "vehicle ID")
        )
        err = err or db_call(
            vehicles.check_new_vehicle, u["carrier_id"], vid, hub, vtype
        )
        if err:
            st.error(err)
        else:
            st.session_state["pending_vehicle"] = {
                "vehicle_id": vid,
                "home_hub_id": hub,
                "vehicle_type": vtype,
            }
            go("carrier_vehicle_details")
            st.rerun()


def _detail_inputs(vtype, current=None, key_prefix="in_det"):
    current = current or {}
    values = {}
    for col, label in vehicles.TYPE_DETAILS[vtype][1]:
        letter = chr(ord("A") + len(values))
        if col == "axle_count":
            values[col] = st.number_input(
                f"{letter}. {label}",
                min_value=0,
                step=1,
                value=int(current.get(col) or 0),
                key=f"{key_prefix}_{col}",
            )
        else:
            low = None if col in ("temp_min", "temp_max") else 0.0
            values[col] = st.number_input(
                f"{letter}. {label}",
                min_value=low,
                step=1.0,
                value=float(current.get(col) or 0),
                key=f"{key_prefix}_{col}",
            )
    return values


def vehicle_details():
    u = require_role(ROLE)
    pending = st.session_state.get("pending_vehicle")
    if not pending:
        go("carrier_vehicle_add")
        st.rerun()
    name = vehicles.TYPES[pending["vehicle_type"]]
    header(
        f"Carrier: Add {name} Details",
        BASE + ["Manage Vehicles", "Add New Vehicle", f"{name} Details"],
    )
    st.caption(
        f"Vehicle {pending['vehicle_id'] or '(new ID)'} · home hub {pending['home_hub_id']}"
    )
    with st.form("vehicle_details"):
        details = _detail_inputs(pending["vehicle_type"])
        save = st.form_submit_button("1. Save", type="primary")
    c1, c2 = st.columns(2)
    if c1.button("2. Cancel", width="stretch"):
        st.session_state.pop("pending_vehicle", None)
        go("carrier_vehicle_add")
        st.rerun()
    if c2.button("3. LandingPage", width="stretch"):
        st.session_state.pop("pending_vehicle", None)
        go("carrier_landing")
        st.rerun()
    if save:
        res = db_call(
            vehicles.add_vehicle,
            u["carrier_id"],
            pending["vehicle_id"],
            pending["home_hub_id"],
            pending["vehicle_type"],
            details,
        )
        if res.ok:
            st.session_state.pop("pending_vehicle", None)
            flash(res)
            go("carrier_vehicles")
            st.rerun()
        show_result(res)


def update_vehicle():
    u = require_role(ROLE)
    header("Carrier: Update Vehicle", BASE + ["Manage Vehicles", "Update Vehicle"])
    reference("Your vehicles", db_call(vehicles.list_vehicles, u["carrier_id"]))
    vid_text = st.text_input("A. Vehicle ID", key="in_vid")
    v = None
    if vid_text:
        vid, err = parse_id(vid_text, "vehicle ID")
        v = None if err else db_call(vehicles.get_owned_vehicle, u["carrier_id"], vid)
        if err:
            st.error(err)
        elif v is None:
            st.error(f"Vehicle {vid} doesn't exist or isn't yours.")

    if v:
        st.write(
            f"**{vehicles.TYPES[v['vehicle_type']]} {v['vehicle_id']}**, home hub {v['home_hub_id']}"
        )
        tab_common, tab_type = st.tabs(
            ["1. Update Common Details", "2. Update Type Details"]
        )
        with tab_common:
            with st.form(f"common_{v['vehicle_id']}"):
                hub = hub_input(
                    "Home Hub ID", f"in_hub_{v['vehicle_id']}", v["home_hub_id"]
                )
                if st.form_submit_button("Save common details", type="primary"):
                    res = db_call(
                        vehicles.update_home_hub, u["carrier_id"], v["vehicle_id"], hub
                    )
                    if res.ok:
                        flash(res)
                        go("carrier_vehicles")
                        st.rerun()
                    show_result(res)
        with tab_type:
            with st.form(f"type_{v['vehicle_id']}"):
                details = _detail_inputs(
                    v["vehicle_type"],
                    v["details"],
                    key_prefix=f"in_det_{v['vehicle_id']}",
                )
                if st.form_submit_button("Save type details", type="primary"):
                    res = db_call(
                        vehicles.update_type_details,
                        u["carrier_id"],
                        v["vehicle_id"],
                        details,
                    )
                    if res.ok:
                        flash(res)
                        go("carrier_vehicles")
                        st.rerun()
                    show_result(res)
    nav_buttons(
        [("3. GoBack", "carrier_vehicles"), ("4. LandingPage", "carrier_landing")]
    )


def view_vehicles():
    u = require_role(ROLE)
    header("Carrier: View Vehicles", BASE + ["Manage Vehicles", "View Vehicles"])
    table(
        db_call(vehicles.list_vehicles, u["carrier_id"]),
        empty="Your company has no vehicles yet.",
    )
    nav_buttons(
        [("1. GoBack", "carrier_vehicles"), ("2. LandingPage", "carrier_landing")]
    )


#  Departures


def manage_departures():
    require_role(ROLE)
    header("Carrier: Manage Departures", BASE + ["Manage Departures"])
    menu(
        [
            ("Schedule Departure", "carrier_dep_schedule"),
            ("Update Departure", "carrier_dep_update"),
            ("View Departures", "carrier_dep_view"),
            ("GoBack", "carrier_landing"),
            ("LandingPage", "carrier_landing"),
        ]
    )


def _departure_refs(u):
    reference("Your vehicles", db_call(vehicles.list_vehicles, u["carrier_id"]))
    reference("Lanes (valid origin -> destination pairs)", db_call(list_lanes))


def schedule_departure():
    u = require_role(ROLE)
    header(
        "Carrier: Schedule Departure",
        BASE + ["Manage Departures", "Schedule Departure"],
    )
    _departure_refs(u)
    with st.form("schedule_form"):
        vid_text = st.text_input("A. Vehicle ID", key="in_vid")
        origin = hub_input("B. Origin Hub ID", "in_origin")
        dest = hub_input("C. Destination Hub ID", "in_dest")
        when = datetime_inputs("D. Departure", "in_when")
        cap = st.number_input(
            "E. Capacity (kg)", min_value=0.0, step=100.0, key="in_cap"
        )
        save = st.form_submit_button("1. Save", type="primary")
    nav_buttons(
        [("2. Cancel", "carrier_departures"), ("3. LandingPage", "carrier_landing")]
    )
    if save:
        vid, err = parse_id(vid_text, "vehicle ID")
        if err:
            st.error(err)
            return
        res = db_call(
            departures.schedule_departure, u["carrier_id"], vid, origin, dest, when, cap
        )
        if res.ok:
            flash(res)
            go("carrier_departures")
            st.rerun()
        show_result(res)


def update_departure():
    u = require_role(ROLE)
    header(
        "Carrier: Update Departure", BASE + ["Manage Departures", "Update Departure"]
    )
    st.caption(
        "Capacity can't go below the weight already booked, and the lane can't change once shipments are booked."
    )
    reference("Your departures", db_call(departures.list_departures, u["carrier_id"]))
    _departure_refs(u)
    did_text = st.text_input("A. Departure ID", key="in_did")
    d = None
    if did_text:
        did, err = parse_id(did_text, "departure ID")
        d = (
            None
            if err
            else db_call(departures.get_owned_departure, u["carrier_id"], did)
        )
        if err:
            st.error(err)
        elif d is None:
            st.error(f"Departure {did} doesn't exist or isn't yours.")
    if d:
        k = d["departure_id"]
        st.caption(f"Booked so far: {d['booked_weight']} kg of {d['max_weight']} kg")
        with st.form(f"dep_update_{k}"):
            vid_text = st.text_input(
                "B. Vehicle ID", value=str(d["vehicle_id"]), key=f"in_vid_{k}"
            )
            origin = hub_input("C. Origin Hub ID", f"in_origin_{k}", d["origin_hub"])
            dest = hub_input(
                "D. Destination Hub ID", f"in_dest_{k}", d["destination_hub"]
            )
            when = datetime_inputs(
                "E. Departure", f"in_when_{k}", d["departure_datetime"]
            )
            cap = st.number_input(
                "F. Capacity (kg)",
                min_value=0.0,
                step=100.0,
                value=float(d["max_weight"]),
                key=f"in_cap_{k}",
            )
            save = st.form_submit_button("1. Save", type="primary")
        if save:
            vid, err = parse_id(vid_text, "vehicle ID")
            if err:
                st.error(err)
            else:
                res = db_call(
                    departures.update_departure,
                    u["carrier_id"],
                    k,
                    vid,
                    origin,
                    dest,
                    when,
                    cap,
                )
                if res.ok:
                    flash(res)
                    go("carrier_departures")
                    st.rerun()
                show_result(res)
    nav_buttons(
        [("2. Cancel", "carrier_departures"), ("3. LandingPage", "carrier_landing")]
    )


def view_departures():
    u = require_role(ROLE)
    header("Carrier: View Departures", BASE + ["Manage Departures", "View Departures"])
    table(
        db_call(departures.list_departures, u["carrier_id"]),
        {
            "departure_id": "Departure",
            "vehicle_id": "Vehicle",
            "vehicle_type": "Type",
            "origin_hub": "Origin",
            "destination_hub": "Destination",
            "departure_datetime": "Scheduled",
            "max_weight": "Capacity (kg)",
            "booked_weight": "Booked (kg)",
            "remaining_weight": "Remaining (kg)",
        },
        empty="Your company has no departures yet.",
    )
    nav_buttons(
        [("1. GoBack", "carrier_departures"), ("2. LandingPage", "carrier_landing")]
    )


# ------------------------------------------------------------------ Scans


def post_scan_screen():
    u = require_role(ROLE)
    header("Carrier: Post Scan Event", BASE + ["Post Scan Event"])
    st.caption(
        "Scans must be in time order and the status can only move forward: "
        "Received → In Transit → Arrived at Hub → Out for Delivery → Delivered."
    )
    reference("Your departures", db_call(departures.list_departures, u["carrier_id"]))
    with st.form("scan_form"):
        sid_text = st.text_input("A. Shipment ID", key="in_sid")
        did_text = st.text_input("B. Departure ID", key="in_did")
        when = datetime_inputs("C. Timestamp", "in_when")
        hub = hub_input("D. Hub ID", "in_hub")
        status = st.selectbox(
            "E. Status", list(STATUSES), format_func=STATUSES.get, key="in_status"
        )
        save = st.form_submit_button("1. Save", type="primary")
    nav_buttons(
        [("2. Cancel", "carrier_landing"), ("3. LandingPage", "carrier_landing")]
    )
    if save:
        sid, e1 = parse_id(sid_text, "shipment ID")
        did, e2 = parse_id(did_text, "departure ID")
        if e1 or e2:
            st.error(e1 or e2)
            return
        res = db_call(post_scan, u["carrier_id"], sid, did, when, hub, status)
        if res.ok:
            flash(res)
            go("carrier_landing")
            st.rerun()
        show_result(res)


# Reports


def reports():
    require_role(ROLE)
    header("Carrier: Reports", BASE + ["Reports"])
    menu(
        [
            ("Load per Departure", "carrier_rep_load"),
            ("Carrier On-Time Rate", "carrier_rep_ontime"),
            ("Carrier Shipment Dwell Time", "carrier_rep_dwell"),
            ("GoBack", "carrier_landing"),
            ("LandingPage", "carrier_landing"),
        ]
    )


def rep_load():
    u = require_role(ROLE)
    header("Carrier: Load per Departure", BASE + ["Reports", "Load per Departure"])
    st.caption("Your departures scheduled in the selected range.")
    start, end = date_range_inputs()
    if st.button("1. View Report", type="primary") and check_range(start, end):
        table(
            db_call(carrier_reports.load_per_departure, u["carrier_id"], start, end),
            {
                "departure_id": "Departure",
                "vehicle_id": "Vehicle",
                "origin_hub": "Origin",
                "destination_hub": "Destination",
                "departure_datetime": "Scheduled",
                "max_weight": "Capacity (kg)",
                "booked_weight": "Booked (kg)",
                "remaining_weight": "Remaining (kg)",
                "pct_full": "% full",
            },
            empty="No departures in this range.",
        )
    nav_buttons(
        [("2. GoBack", "carrier_reports"), ("3. LandingPage", "carrier_landing")]
    )


def rep_ontime():
    u = require_role(ROLE)
    header("Carrier: Carrier On-Time Rate", BASE + ["Reports", "On-Time Rate"])
    st.caption("Shipments on your departures delivered in the selected range.")
    start, end = date_range_inputs()
    if st.button("1. View Report", type="primary") and check_range(start, end):
        r = db_call(carrier_reports.on_time_rate, u["carrier_id"], start, end)
        c = st.columns(4)
        c[0].metric("Delivered", r["delivered"])
        c[1].metric("On time", r["on_time"])
        c[2].metric("Late", r["late"])
        c[3].metric(
            "On-time rate",
            f"{r['on_time_rate_pct']}%" if r["on_time_rate_pct"] is not None else "—",
        )
    nav_buttons(
        [("2. GoBack", "carrier_reports"), ("3. LandingPage", "carrier_landing")]
    )


def rep_dwell():
    u = require_role(ROLE)
    header("Carrier: Carrier Shipment Dwell Time", BASE + ["Reports", "Dwell Time"])
    sid_text = st.text_input("A. Shipment ID", key="in_sid")
    if st.button("1. View Report", type="primary"):
        sid, err = parse_id(sid_text, "shipment ID")
        if err:
            st.error(err)
        else:
            rows = db_call(carrier_reports.carrier_dwell_time, u["carrier_id"], sid)
            if rows is None:
                st.error(f"Your company didn't handle shipment {sid}.")
            else:
                table(
                    rows,
                    {
                        "scan_seq": "#",
                        "timestamp": "Timestamp",
                        "hub_id": "Hub",
                        "shipment_status": "Status",
                        "previous_scan": "Previous scan",
                        "minutes_since_previous": "Minutes since previous",
                    },
                    empty="No scans recorded yet.",
                )
    nav_buttons(
        [("2. GoBack", "carrier_reports"), ("3. LandingPage", "carrier_landing")]
    )


PAGES = {
    "carrier_landing": landing,
    "carrier_vehicles": manage_vehicles,
    "carrier_vehicle_add": add_vehicle,
    "carrier_vehicle_details": vehicle_details,
    "carrier_vehicle_update": update_vehicle,
    "carrier_vehicle_view": view_vehicles,
    "carrier_departures": manage_departures,
    "carrier_dep_schedule": schedule_departure,
    "carrier_dep_update": update_departure,
    "carrier_dep_view": view_departures,
    "carrier_scan": post_scan_screen,
    "carrier_reports": reports,
    "carrier_rep_load": rep_load,
    "carrier_rep_ontime": rep_ontime,
    "carrier_rep_dwell": rep_dwell,
}
