"""
Application Flow test: walks the app through every page of
"CSC 540 - Project Application Flow" and checks each page's Output rule
against what the screen actually shows (titles, messages, metrics, tables).

    python -m tests.test_application_flow --reset

!! --reset rebuilds the database in config/db_config.ini from the sample data
   (python -m db.load_database --reset) before the test, and again after it,
   so the database ends up back at the sample data. Without --reset nothing runs.

It drives the real screens in src/ui (Streamlit's built-in test runner, no
browser needed), so every accept/reject comes from the real database: the
book_shipment procedure, the triggers, the foreign keys and CHECK constraints.
Prints PASS/FAIL per check; exits with status 1 if any check fails.
"""

import os
import re
import subprocess
import sys
from datetime import date, time, timedelta

from streamlit.testing.v1 import AppTest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP = os.path.join(ROOT, "src", "ui", "app.py")
TIMEOUT = 120  # seconds per screen; the class server is remote
TODAY = date.today()
LATER = TODAY + timedelta(days=30)  # future date for new shipments/departures
results = []  # (flow page, check, passed, detail)


def reset_database():
    print("Resetting the database to the sample data ...")
    subprocess.run([sys.executable, "-m", "db.load_database", "--reset"], cwd=ROOT, check=True,
                   stdout=subprocess.DEVNULL)


def check(page, what, ok, detail=""):
    results.append((page, what, bool(ok), detail))
    line = ("PASS" if ok else "FAIL") + " | " + page + " | " + what
    if not ok:
        line += " | got: " + str(detail)[:200]
    print(line)


def title(at):
    return at.title[0].value if at.title else ""


def msgs(at, kind):
    return " ".join(str(m.value) for m in getattr(at, kind))


def press(at, label):
    # Click the button whose label is `label`, with or without its menu number ("1. Save" or "Save").
    pat = re.compile(r"^\s*(\d+\.\s+)?" + re.escape(label) + r"\s*$")
    for b in at.button:
        if pat.match(b.label):
            b.click().run()
            return at
    raise AssertionError(f"No button {label!r} on '{title(at)}': {[b.label for b in at.button]}")


def has_button(at, label):
    pat = re.compile(r"^\s*(\d+\.\s+)?" + re.escape(label) + r"\s*$")
    return any(pat.match(b.label) for b in at.button)


def menu_labels(at):
    return [re.sub(r"^\s*\d+\.\s+", "", b.label) for b in at.button if re.match(r"^\s*\d+\.", b.label)]


def type_in(at, key, value):
    at.text_input(key=key).input(value).run()


def df(at, i=-1):
    return at.dataframe[i].value if at.dataframe else None


def login(at, role_button, uid, pw):
    press(at, role_button)
    at.text_input(key="in_uid").input(uid)
    at.text_input(key="in_pw").input(pw)
    return press(at, "Sign-In")


def run_checks():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT).run()

    # ======================================================================== Home
    P = "Home"
    check(P, "menu shows Shipper/Carrier/Viewer Login and Exit",
          all(has_button(at, l) for l in ["Shipper Login", "Carrier Login", "Viewer Login", "Exit"]),
          [b.label for b in at.button])
    check(P, "extra option not in the flow: 'View Queries' (needed to run the required queries)",
          has_button(at, "View Queries"), "")
    press(at, "Exit")
    check(P, "Exit ends the session", title(at) == "Goodbye", title(at))
    press(at, "Start again")

    # ======================================================================== Logins
    for role, button, uid in [("Shipper", "Shipper Login", "SH1"), ("Carrier", "Carrier Login", "C1"),
                              ("Viewer", "Viewer Login", "VW1")]:
        P = f"{role}: Login"
        press(at, button)
        check(P, "asks for A. User ID and B. Password",
              [t.label for t in at.text_input] == ["A. User ID", "B. Password"], [t.label for t in at.text_input])
        at.text_input(key="in_uid").input(uid); at.text_input(key="in_pw").input("wrong"); press(at, "Sign-In")
        check(P, "wrong password -> 'Login Incorrect', stays on login",
              "Login Incorrect" in msgs(at, "error") and title(at) == f"{role}: Login", msgs(at, "error"))
        other = "SH1" if role != "Shipper" else "C1"
        at.text_input(key="in_uid").input(other); at.text_input(key="in_pw").input("password"); press(at, "Sign-In")
        check(P, f"wrong role ({other}) -> 'Login Incorrect'", "Login Incorrect" in msgs(at, "error"), msgs(at, "error"))
        press(at, "GoBack")
        check(P, "GoBack returns to Home", has_button(at, "Shipper Login"), title(at))

    # ======================================================================== Shipper
    login(at, "Shipper Login", "SH1", "password")
    P = "Shipper: Login"
    check(P, "SH1 + correct password -> Shipper: Landing", title(at) == "Shipper: Landing", title(at))

    P = "Shipper: Landing"
    check(P, "menu = Shipments, Reports, Logout", menu_labels(at) == ["Shipments", "Reports", "Logout"],
          menu_labels(at))
    press(at, "Shipments")
    P = "Shipper: Shipments"
    check(P, "menu order matches the flow",
          menu_labels(at) == ["Create Shipment", "Update Shipment", "Book Shipment onto Departure", "Track Shipment",
                              "GoBack", "LandingPage"], menu_labels(at))
    press(at, "GoBack"); check(P, "GoBack -> Shipper: Landing", title(at) == "Shipper: Landing", title(at))
    press(at, "Shipments"); press(at, "LandingPage")
    check(P, "LandingPage -> Shipper: Landing", title(at) == "Shipper: Landing", title(at))

    # ---- Create
    press(at, "Shipments"); press(at, "Create Shipment")
    P = "Shipper: Create Shipment"
    check(P, "asks for A. Origin, B. Destination, C. Weight, D. Promised Date",
          [w.label for w in at.selectbox] == ["A. Origin Hub ID", "B. Destination Hub ID"]
          and at.number_input[0].label.startswith("C. Weight") and at.date_input[0].label == "D. Promised Delivery Date")
    opts = at.selectbox(key="in_origin").options
    check(P, "origin/destination are hub dropdowns listing all 11 hubs",
          len(opts) == 11 and "RDU - Raleigh Hub (Southeast)" in opts, opts)
    press(at, "Save")
    check(P, "no hubs chosen -> 'Choose both an origin and a destination hub.'",
          "Choose both" in msgs(at, "error") and title(at) == P, msgs(at, "error"))
    at.selectbox(key="in_origin").select("RDU"); at.selectbox(key="in_dest").select("RDU")
    at.number_input(key="in_weight").set_value(300); press(at, "Save")
    check(P, "origin = destination (RDU->RDU) -> failure shown",
          "different hubs" in msgs(at, "error") and title(at) == P, msgs(at, "error"))
    at.selectbox(key="in_origin").select("RDU"); at.selectbox(key="in_dest").select("ATL")
    at.number_input(key="in_weight").set_value(0); press(at, "Save")
    check(P, "weight 0 -> failure shown", msgs(at, "error") != "", msgs(at, "error"))
    at.number_input(key="in_weight").set_value(300); at.date_input(key="in_promised").set_value(LATER)
    press(at, "Save")
    check(P, "valid shipment -> success, back to Shipments",
          title(at) == "Shipper: Shipments" and "24" in msgs(at, "success"), msgs(at, "success") or msgs(at, "error"))
    press(at, "Create Shipment"); press(at, "Cancel")
    check(P, "Cancel -> Shipments", title(at) == "Shipper: Shipments", title(at))
    press(at, "Create Shipment"); press(at, "LandingPage")
    check(P, "LandingPage -> Shipper: Landing", title(at) == "Shipper: Landing", title(at))

    # ---- Update
    press(at, "Shipments"); press(at, "Update Shipment")
    P = "Shipper: Update Shipment"
    type_in(at, "in_sid", "2")
    check(P, "shipment 2 (owned by SH2) -> rejected", "isn't yours" in msgs(at, "error"), msgs(at, "error"))
    type_in(at, "in_sid", "24")
    check(P, "shipment 24 -> B-E shown pre-filled", at.selectbox(key="in_origin_24").value == "RDU", "")
    at.number_input(key="in_weight_24").set_value(400); press(at, "Save")
    check(P, "valid update -> success, back to Shipments",
          title(at) == "Shipper: Shipments" and msgs(at, "success") != "", msgs(at, "success") or msgs(at, "error"))
    press(at, "Update Shipment"); type_in(at, "in_sid", "1")
    at.number_input(key="in_weight_1").set_value(3500); press(at, "Save")
    check(P, "shipment 1 is booked: weight change refused (shipment state)",
          "can't change after the shipment is booked" in msgs(at, "error"), msgs(at, "error"))
    press(at, "Cancel"); check(P, "Cancel -> Shipments", title(at) == "Shipper: Shipments", title(at))

    # ---- Book
    press(at, "Book Shipment onto Departure")
    P = "Shipper: Book Shipment onto Departure"
    check(P, "asks for A. Shipment ID, B. Departure ID",
          [t.label for t in at.text_input] == ["A. Shipment ID", "B. Departure ID"], [t.label for t in at.text_input])
    type_in(at, "in_sid", "14")
    el = next((d.value for d in at.dataframe if "Departs" in d.value.columns), None)
    check(P, "S14 eligible departures listed earliest first: D9, D10, D1, D6, D8 (full D7 left out)",
          el is not None and list(el["Departure"]) == [9, 10, 1, 6, 8]
          and list(el["Departs"]) == sorted(el["Departs"]), None if el is None else list(el["Departure"]))
    type_in(at, "in_sid", "5"); type_in(at, "in_did", "2"); press(at, "Book")
    check(P, "shipment 5 (owned by SH2) -> rejected", "isn't yours" in msgs(at, "error"), msgs(at, "error"))
    type_in(at, "in_sid", "14"); type_in(at, "in_did", "7"); press(at, "Book")
    check(P, "S14 on D7 (full) -> 'Not enough capacity'", "Not enough capacity" in msgs(at, "error"), msgs(at, "error"))
    type_in(at, "in_sid", "24"); type_in(at, "in_did", "3"); press(at, "Book")
    check(P, "S24 (RDU->ATL) on D3 (JFK->BOS) -> not eligible", msgs(at, "error") != "" and title(at) == P,
          msgs(at, "error"))
    type_in(at, "in_sid", "14"); type_in(at, "in_did", "8"); press(at, "Book")
    check(P, "S14 on D8 -> booked, back to Shipments",
          title(at) == "Shipper: Shipments" and "booked" in msgs(at, "success"), msgs(at, "success"))
    press(at, "Book Shipment onto Departure"); type_in(at, "in_sid", "14"); type_in(at, "in_did", "8"); press(at, "Book")
    check(P, "S14 again -> 'already booked'", "already booked" in msgs(at, "error"), msgs(at, "error"))
    press(at, "LandingPage"); check(P, "LandingPage -> Shipper: Landing", title(at) == "Shipper: Landing", title(at))

    # ---- Track
    press(at, "Shipments"); press(at, "Track Shipment")
    P = "Shipper: Track Shipment"
    type_in(at, "in_sid", "1"); press(at, "View History")
    h = df(at)
    status = [m.value for m in at.metric if m.label == "Current status"]
    check(P, "S1 -> current status Delivered", status == ["Delivered"], status)
    check(P, "S1 -> 4 scans in chronological order",
          h is not None and len(h) == 4 and list(h["Timestamp"]) == sorted(h["Timestamp"]), None if h is None else len(h))
    type_in(at, "in_sid", "2"); press(at, "View History")
    check(P, "S2 (not owned) -> error", "isn't yours" in msgs(at, "error"), msgs(at, "error"))
    type_in(at, "in_sid", "999"); press(at, "View History")
    check(P, "S999 (doesn't exist) -> error", "doesn't exist" in msgs(at, "error"), msgs(at, "error"))
    press(at, "GoBack"); check(P, "GoBack -> Shipments", title(at) == "Shipper: Shipments", title(at))

    # ---- Reports
    press(at, "GoBack"); press(at, "Reports")
    P = "Shipper: Reports"
    check(P, "menu order matches the flow",
          menu_labels(at) == ["On-Time vs Late Summary", "In-Transit Shipments", "Shipments Near Promise Date",
                              "GoBack", "LandingPage"], menu_labels(at))
    press(at, "On-Time vs Late Summary")
    P = "Shipper: On-Time vs Late Summary"
    press(at, "View Report")
    m = {x.label: (x.value, x.delta) for x in at.metric}
    check(P, "SH1 2026: 6 delivered, 5 on time (83.3%), 1 late (16.7%)",
          m.get("Delivered", (None,))[0] == "6" and m["On time"] == ("5", "83.3%") and m["Late"] == ("1", "16.7%"), m)
    at.date_input(key="in_start").set_value(date(2026, 3, 1)); at.date_input(key="in_end").set_value(date(2026, 3, 31))
    press(at, "View Report")
    m = {x.label: (x.value, x.delta) for x in at.metric}
    check(P, "date range March only: 2 delivered (S1, S9), both on time", m.get("Delivered", (None,))[0] == "2", m)
    press(at, "GoBack"); check(P, "GoBack -> Shipper: Reports", title(at) == "Shipper: Reports", title(at))

    press(at, "In-Transit Shipments")
    P = "Shipper: In-Transit Shipments"
    t = df(at)
    ids = sorted(int(x) for x in t.iloc[:, 0]) if t is not None else []
    statuses = set(t["Current status"]) if t is not None else set()
    check(P, "lists only SH1's shipments with status In Transit (4, 16, 17, 18, 19)",
          ids == [4, 16, 17, 18, 19] and statuses == {"In Transit"}, (ids, statuses))
    press(at, "GoBack")

    press(at, "Shipments Near Promise Date")
    P = "Shipper: Shipments Near Promise Date"
    at.number_input(key="in_n").set_value(3); press(at, "View Report")
    t = df(at)
    ids = sorted(int(x) for x in t.iloc[:, 0]) if t is not None else []
    check(P, "N=3: in-transit with promise passed or within 3 days (excludes S24, due in 30 days)",
          24 not in ids and 4 in ids and 19 in ids, ids)
    press(at, "LandingPage"); press(at, "Logout")
    check("Shipper: Landing", "Logout -> Home", has_button(at, "Shipper Login") and "user" not in at.session_state,
          title(at))

    # ======================================================================== Carrier
    login(at, "Carrier Login", "C1", "password")
    P = "Carrier: Login"
    check(P, "C1 + correct password -> Carrier: Landing", title(at) == "Carrier: Landing", title(at))
    P = "Carrier: Landing"
    check(P, "menu order matches the flow",
          menu_labels(at) == ["Vehicles", "Departures", "Post Scan Event", "Reports", "Logout"],
          menu_labels(at))

    press(at, "Vehicles")
    P = "Carrier: Vehicles"
    check(P, "menu order matches the flow",
          menu_labels(at) == ["Add New Vehicle", "Update Vehicle", "View Vehicles", "GoBack", "LandingPage"],
          menu_labels(at))

    for vtype, title_word, fields, values in [
            ("BOX_TRUCK", "Box Truck", ["cargo_volume", "gross_weight_rating"], [20, 5000]),
            ("REFRIGERATED_VAN", "Refrigerated Van", ["temp_min", "temp_max", "payload_limit"], [-20, 0, 2500]),
            ("RAIL_CAR", "Rail Car", ["axle_count", "track_gauge"], [4, 1435])]:
        press(at, "Add New Vehicle")
        P = "Carrier: Add New Vehicle"
        at.selectbox(key="in_hub").select("RDU"); at.selectbox(key="in_type").select(vtype); press(at, "Continue")
        P2 = f"Carrier: Add {title_word} Details"
        check(P, f"{title_word} -> routes to '{P2}'", title(at) == P2, title(at))
        for f, v in zip(fields, values):
            at.number_input(key=f"in_det_{f}").set_value(v)
        press(at, "Save")
        check(P2, "Save -> success, back to Vehicles",
              title(at) == "Carrier: Vehicles" and "added" in msgs(at, "success"), msgs(at, "success") or msgs(at, "error"))

    press(at, "Add New Vehicle")
    P = "Carrier: Add New Vehicle"
    at.text_input(key="in_vid").input("101"); at.selectbox(key="in_hub").select("RDU"); press(at, "Continue")
    check(P, "vehicle ID 101 already exists -> rejected", msgs(at, "error") != "" and title(at) == P, msgs(at, "error"))
    press(at, "GoBack"); press(at, "Add New Vehicle")
    press(at, "Continue")
    check(P, "no home hub chosen -> 'Choose a home hub.'", "Choose a home hub" in msgs(at, "error"), msgs(at, "error"))
    at.selectbox(key="in_hub").select("RDU"); press(at, "Continue")
    press(at, "Cancel")
    check("Carrier: Add Box Truck Details", "Cancel discards and returns to Add New Vehicle",
          title(at) == "Carrier: Add New Vehicle" and "pending_vehicle" not in at.session_state, title(at))
    press(at, "GoBack")

    press(at, "Update Vehicle")
    P = "Carrier: Update Vehicle"
    type_in(at, "in_vid", "201")
    check(P, "vehicle 201 (C2's) -> rejected", "isn't yours" in msgs(at, "error"), msgs(at, "error"))
    type_in(at, "in_vid", "103")
    at.selectbox(key="in_hub_103").select("ATL"); press(at, "Save common details")
    check(P, "Update Common Details: home hub -> ATL, success, back to Vehicles",
          title(at) == "Carrier: Vehicles" and msgs(at, "success") != "", msgs(at, "success") or msgs(at, "error"))
    press(at, "Update Vehicle"); type_in(at, "in_vid", "102")
    labels = [n.label for n in at.number_input]
    check(P, "Update Type Details: refrigerated van shows only its own attributes",
          labels == ["A. Minimum temperature (°C)", "B. Maximum temperature (°C)", "C. Payload limit (kg)"]
          or (len(labels) == 3 and "temp" in labels[0].lower()), labels)
    at.number_input(key="in_det_102_payload_limit").set_value(4500); press(at, "Save type details")
    check(P, "type details saved -> success", msgs(at, "success") != "", msgs(at, "success") or msgs(at, "error"))
    press(at, "Update Vehicle"); type_in(at, "in_vid", "101"); press(at, "Delete vehicle 101")
    check(P, "delete vehicle 101 (assigned to departures) -> refused",
          "can't be deleted" in msgs(at, "error") and title(at) == P, msgs(at, "error"))
    type_in(at, "in_vid", "304"); press(at, "Delete vehicle 304")
    check(P, "delete vehicle 304 (rail car, no departures) -> deleted, back to Vehicles",
          title(at) == "Carrier: Vehicles" and "deleted" in msgs(at, "success"),
          msgs(at, "success") or msgs(at, "error"))
    press(at, "View Vehicles")
    P = "Carrier: View Vehicles"
    t = df(at)
    check(P, "shows only C1's vehicles (101, 102, 103, 302, 303; 304 was deleted)",
          t is not None and sorted(t.iloc[:, 0]) == [101, 102, 103, 302, 303],
          None if t is None else list(t.columns))
    check(P, "includes type and type-specific attributes",
          t is not None and any("type" in c.lower() for c in t.columns) and len(t.columns) >= 4,
          None if t is None else list(t.columns))
    press(at, "LandingPage"); check(P, "LandingPage -> Carrier: Landing", title(at) == "Carrier: Landing", title(at))

    press(at, "Departures")
    P = "Carrier: Departures"
    check(P, "menu order matches the flow",
          menu_labels(at) == ["Schedule Departure", "Update Departure", "View Departures", "GoBack", "LandingPage"],
          menu_labels(at))
    press(at, "Schedule Departure")
    P = "Carrier: Schedule Departure"


    def sched(vid, o, d, cap):
        at.text_input(key="in_vid").input(vid); at.selectbox(key="in_origin").select(o)
        at.selectbox(key="in_dest").select(d); at.number_input(key="in_cap").set_value(cap)
        at.date_input(key="in_when_d").set_value(LATER); at.time_input(key="in_when_t").set_value(time(9, 0))
        press(at, "Save")


    sched("201", "RDU", "ATL", 5000)
    check(P, "vehicle 201 (C2's) -> rejected", msgs(at, "error") != "" and title(at) == P, msgs(at, "error"))
    sched("101", "RDU", "RDU", 5000)
    check(P, "origin = destination -> rejected", msgs(at, "error") != "", msgs(at, "error"))
    check(P, "origin/destination are hub dropdowns listing all 11 hubs",
          len(at.selectbox(key="in_dest").options) == 11, at.selectbox(key="in_dest").options)
    sched("101", "RDU", "ATL", 0)
    check(P, "capacity 0 -> rejected", msgs(at, "error") != "", msgs(at, "error"))
    sched("101", "RDU", "ATL", 5000)
    check(P, "valid -> success, back to Departures",
          title(at) == "Carrier: Departures" and msgs(at, "success") != "", msgs(at, "success") or msgs(at, "error"))

    press(at, "Update Departure")
    P = "Carrier: Update Departure"
    type_in(at, "in_did", "3")
    check(P, "departure 3 (C2's) -> rejected", "isn't yours" in msgs(at, "error"), msgs(at, "error"))
    type_in(at, "in_did", "1")
    at.number_input(key="in_cap_1").set_value(5000); press(at, "Save")
    check(P, "D1 capacity 5000 < 7500 booked -> rejected", msgs(at, "error") != "" and title(at) == P, msgs(at, "error"))
    at.number_input(key="in_cap_1").set_value(10000); at.text_input(key="in_vid_1").input("201"); press(at, "Save")
    check(P, "D1 with vehicle 201 (C2's) -> rejected", msgs(at, "error") != "", msgs(at, "error"))
    at.text_input(key="in_vid_1").input("101"); at.number_input(key="in_cap_1").set_value(12000); press(at, "Save")
    check(P, "D1 capacity 12000 -> success, back to Departures",
          title(at) == "Carrier: Departures" and msgs(at, "success") != "", msgs(at, "success") or msgs(at, "error"))

    press(at, "View Departures")
    P = "Carrier: View Departures"
    t = df(at)
    cols = [] if t is None else list(t.columns)
    check(P, "only C1's departures (D1,D2,D6-D10 + new D11 = 8)", t is not None and len(t) == 8, None if t is None else len(t))
    check(P, "shows vehicle, lane, time, capacity, booked, remaining",
          all(c in cols for c in ["Vehicle", "Origin", "Destination", "Scheduled", "Capacity (kg)", "Booked (kg)",
                                  "Remaining (kg)"]), cols)
    press(at, "LandingPage")

    press(at, "Post Scan Event")
    P = "Carrier: Post Scan Event"
    bk = next((d.value for d in at.dataframe if {"Departure", "Shipment"} <= set(d.value.columns)), None)
    deps = set() if bk is None else set(bk["Departure"])
    check(P, "shows the shipments booked on C1's departures (D1, D2, D6-D10 only)",
          bk is not None and deps <= {1, 2, 6, 7, 8, 9, 10} and (16 in set(bk["Shipment"])), sorted(deps))


    def scan(sid, did, d, tm, hub, status):
        at.text_input(key="in_sid").input(sid); at.text_input(key="in_did").input(did)
        at.date_input(key="in_when_d").set_value(d); at.time_input(key="in_when_t").set_value(tm)
        at.selectbox(key="in_hub").select(hub); at.selectbox(key="in_status").select(status)
        press(at, "Save")


    scan("2", "3", TODAY, time(10, 0), "BOS", "DELIVERED")
    check(P, "departure 3 is C2's -> rejected", msgs(at, "error") != "" and title(at) == P, msgs(at, "error"))
    scan("16", "7", TODAY, time(10, 0), "ATL", "OUT_FOR_DELIVERY")
    check(P, "S16 is not booked on D7 -> rejected", msgs(at, "error") != "", msgs(at, "error"))
    scan("16", "8", TODAY, time(10, 0), "RDU", "RECEIVED")
    check(P, "S16 In Transit -> Received (status goes back) -> rejected", "back" in msgs(at, "error").lower(),
          msgs(at, "error"))
    scan("16", "8", date(2026, 10, 30), time(8, 0), "ATL", "OUT_FOR_DELIVERY")
    check(P, "timestamp before the last scan -> rejected", "before" in msgs(at, "error").lower(), msgs(at, "error"))
    scan("16", "8", TODAY, time(10, 0), "ATL", "OUT_FOR_DELIVERY")
    check(P, "valid scan -> success, back to Carrier: Landing",
          title(at) == "Carrier: Landing" and msgs(at, "success") != "", msgs(at, "success") or msgs(at, "error"))
    press(at, "Post Scan Event")
    scan("16", "8", TODAY, time(11, 0), "ATL", "DELIVERED")
    check(P, "S16 delivered after its 10-30 promise -> recorded as Late",
          "late" in msgs(at, "success").lower(), msgs(at, "success") or msgs(at, "error"))
    press(at, "Post Scan Event")
    scan("16", "8", TODAY, time(12, 0), "ATL", "DELIVERED")
    check(P, "scan after Delivered -> rejected", msgs(at, "error") != "", msgs(at, "error"))
    press(at, "Cancel"); check(P, "Cancel -> Carrier: Landing", title(at) == "Carrier: Landing", title(at))

    press(at, "Reports")
    P = "Carrier: Reports"
    check(P, "menu order matches the flow",
          menu_labels(at) == ["Load per Departure", "Carrier On-Time Rate", "Carrier Shipment Dwell Time", "GoBack",
                              "LandingPage"], menu_labels(at))
    press(at, "Load per Departure")
    P = "Carrier: Load per Departure"
    press(at, "View Report")
    t = df(at)
    cols = [] if t is None else list(t.columns)
    check(P, "capacity, booked, remaining, % full per departure",
          all(c in cols for c in ["Capacity (kg)", "Booked (kg)", "Remaining (kg)", "% full"]), cols)
    d7 = t[t["Departure"] == 7] if t is not None else None
    check(P, "D7 shows 100% full", d7 is not None and len(d7) == 1 and float(d7["% full"].iloc[0]) == 100.0,
          None if d7 is None else d7.to_dict("records"))
    press(at, "GoBack")
    press(at, "Carrier On-Time Rate")
    P = "Carrier: Carrier On-Time Rate"
    press(at, "View Report")
    m = {x.label: x.value for x in at.metric}
    check(P, "C1: 11 delivered (10 sample + S16), 8 on time, 3 late, 72.7%",
          m == {"Delivered": "11", "On time": "8", "Late": "3", "On-time rate": "72.7%"}, m)
    press(at, "GoBack")
    press(at, "Carrier Shipment Dwell Time")
    P = "Carrier: Carrier Shipment Dwell Time"
    type_in(at, "in_sid", "1"); press(at, "View Report")
    t = df(at)
    check(P, "S1 -> 4 scans with minutes between each (65, 865, 90)",
          t is not None and [x for x in t["Minutes since previous"].tolist()[1:]] == [65, 865, 90],
          None if t is None else t["Minutes since previous"].tolist())
    type_in(at, "in_sid", "2"); press(at, "View Report")
    check(P, "S2 (carried by C2) -> refused", "didn't handle" in msgs(at, "error"), msgs(at, "error"))
    press(at, "LandingPage"); press(at, "Logout")

    # ======================================================================== Viewer
    login(at, "Viewer Login", "VW1", "password")
    P = "Viewer: Login"
    check(P, "VW1 + correct password -> Viewer: Landing", title(at) == "Viewer: Landing", title(at))
    P = "Viewer: Landing"
    check(P, "menu = Track Shipment, Published Performance Reports, Logout",
          menu_labels(at) == ["Track Shipment", "Published Performance Reports", "Logout"], menu_labels(at))
    press(at, "Track Shipment")
    P = "Viewer: Track Shipment"
    type_in(at, "in_sid", "2"); press(at, "View History")
    st_ = [x.value for x in at.metric if x.label == "Current status"]
    t = df(at)
    check(P, "any shipment (S2) -> status + full history", st_ == ["Delivered"] and t is not None and len(t) == 4,
          (st_, None if t is None else len(t)))
    check(P, "read-only: no Save/Book/Update buttons on the page",
          not any(has_button(at, l) for l in ["Save", "Book", "Update"]), [b.label for b in at.button])
    press(at, "GoBack")
    press(at, "Published Performance Reports")
    P = "Viewer: Published Performance Reports"
    check(P, "menu order matches the flow",
          menu_labels(at) == ["On-Time Rates by Lane", "On-Time Rates by Carrier", "Lane Volume Ranking",
                              "Top Departures per Lane", "Shipment Dwell Time", "Running Total Deliveries by Carrier",
                              "At-Risk In-Transit Shipments", "GoBack", "LandingPage"], menu_labels(at))

    press(at, "On-Time Rates by Lane"); P = "Viewer: On-Time Rates by Lane"
    press(at, "View Report"); t = df(at)
    check(P, "on-time and late rates grouped by lane (5 lanes)",
          t is not None and len(t) == 5 and "On-time %" in t.columns and "Late %" in t.columns,
          None if t is None else (len(t), list(t.columns)))
    press(at, "GoBack")

    press(at, "On-Time Rates by Carrier"); P = "Viewer: On-Time Rates by Carrier"
    press(at, "View Report"); t = df(at)
    rank = [] if t is None else list(zip(t["Rank"], t["Company"], t["On-time %"]))
    check(P, "carriers ranked by rate: Piedmont 72.7, Atlantic 33.3, Plains 0",
          [(int(a), b, float(c)) for a, b, c in rank] == [(1, "Piedmont Freight Lines", 72.7),
                                                          (2, "Atlantic Coast Haulers", 33.3), (3, "Plains Rail Co", 0.0)],
          rank)
    press(at, "GoBack")

    press(at, "Lane Volume Ranking"); P = "Viewer: Lane Volume Ranking"
    press(at, "View Report"); t = df(at)
    check(P, "lanes ranked by volume, RDU->ATL first",
          t is not None and t.iloc[0]["Origin"] == "RDU" and t.iloc[0]["Destination"] == "ATL" and int(t.iloc[0]["Rank"]) == 1,
          None if t is None else t.head(2).to_dict("records"))
    press(at, "GoBack")

    press(at, "Top Departures per Lane"); P = "Viewer: Top Departures per Lane"
    at.number_input(key="in_n").set_value(2); press(at, "View Report"); t = df(at)
    check(P, "Top N=2: at most 2 departures per lane",
          t is not None and t.groupby(["Origin", "Destination"]).size().max() <= 2,
          None if t is None else t.groupby(["Origin", "Destination"]).size().to_dict())
    press(at, "GoBack")

    press(at, "Shipment Dwell Time"); P = "Viewer: Shipment Dwell Time"
    type_in(at, "in_sid", "2"); press(at, "View Report"); t = df(at)
    check(P, "S2 -> time between consecutive scans (4 scans)", t is not None and len(t) == 4,
          None if t is None else len(t))
    press(at, "GoBack")

    press(at, "Running Total Deliveries by Carrier"); P = "Viewer: Running Total Deliveries by Carrier"
    press(at, "View Report"); t = df(at)
    check(P, "all carriers: cumulative totals per carrier",
          t is not None and set(t["Company"]) == {"Piedmont Freight Lines", "Atlantic Coast Haulers", "Plains Rail Co"},
          None if t is None else set(t["Company"]))
    c1 = t[t["Carrier"] == 1]["Cumulative shipments"].tolist() if t is not None else []
    check(P, "running total only increases and ends at C1's total (11)", c1 == sorted(c1) and c1[-1] == 11, c1)
    at.text_input(key="in_cid").input("2"); press(at, "View Report"); t = df(at)
    check(P, "optional Carrier ID 2 -> only Atlantic Coast Haulers",
          t is not None and set(t["Carrier"]) == {2}, None if t is None else set(t["Carrier"]))
    press(at, "GoBack")

    press(at, "At-Risk In-Transit Shipments"); P = "Viewer: At-Risk In-Transit Shipments"
    at.number_input(key="in_n").set_value(3); press(at, "View Report"); t = df(at)
    ids = sorted(int(x) for x in t.iloc[:, 0]) if t is not None else []
    check(P, "N=3: all in-transit shipments past/near promise (all shippers), S24 (due in 30 days) excluded",
          4 in ids and 24 not in ids and 16 not in ids, ids)
    press(at, "LandingPage"); press(at, "Logout")
    check("Viewer: Landing", "Logout -> Home", has_button(at, "Viewer Login"), title(at))

    # ==================================================================== any two hubs form a lane
    # Lanes aren't stored: a pair no sample departure uses (RDU -> SEA) works end to end.
    login(at, "Shipper Login", "SH1", "password")
    press(at, "Shipments"); press(at, "Create Shipment")
    P = "Shipper: Create Shipment"
    at.selectbox(key="in_origin").select("RDU"); at.selectbox(key="in_dest").select("SEA")
    at.number_input(key="in_weight").set_value(200); at.date_input(key="in_promised").set_value(LATER)
    press(at, "Save")
    check(P, "new pair RDU->SEA (no Lane table) -> shipment 25 created", "25" in msgs(at, "success"),
          msgs(at, "success") or msgs(at, "error"))
    press(at, "Book Shipment onto Departure")
    P = "Shipper: Book Shipment onto Departure"
    type_in(at, "in_sid", "25")
    check(P, "S25 with no RDU->SEA departure -> 'No departures available ...' message",
          "No departures available with a matching route and sufficient weight capacity for this shipment."
          in msgs(at, "warning"), msgs(at, "warning"))
    press(at, "LandingPage"); press(at, "Logout")
    login(at, "Carrier Login", "C1", "password")
    press(at, "Departures"); press(at, "Schedule Departure")
    P = "Carrier: Schedule Departure"
    sched("103", "RDU", "SEA", 3000)
    check(P, "new pair RDU->SEA -> scheduled as departure 12",
          title(at) == "Carrier: Departures" and "Departure 12" in msgs(at, "success"),
          msgs(at, "success") or msgs(at, "error"))
    press(at, "LandingPage"); press(at, "Logout")
    login(at, "Shipper Login", "SH1", "password")
    press(at, "Shipments"); press(at, "Book Shipment onto Departure")
    P = "Shipper: Book Shipment onto Departure"
    type_in(at, "in_sid", "25"); type_in(at, "in_did", "12"); press(at, "Book")
    check(P, "S25 RDU->SEA on D12 RDU->SEA -> booked", "booked" in msgs(at, "success"),
          msgs(at, "success") or msgs(at, "error"))
    press(at, "GoBack"); press(at, "Logout")

    # ==================================================================== View Queries
    P = "View Queries"
    press(at, "View Queries")
    labels = at.radio(key="in_query").options
    check(P, "numbered list of the 6 required queries, in order",
          [l.split(".")[0] for l in labels] == ["1", "2", "3", "4", "5", "6"], labels)
    at.radio(key="in_query").set_value(labels[2]).run()
    press(at, "Run query")
    q3 = df(at)
    times = [] if q3 is None else list(q3.iloc[1:, -1])
    check(P, "Q3 (shipment 1): time since previous shown as hours:minutes 1:05, 14:25, 1:30",
          times == ["1:05", "14:25", "1:30"], times)



def main():
    # Windows consoles may not print every character in the app's messages (e.g. arrows).
    sys.stdout.reconfigure(errors="replace")
    if "--reset" not in sys.argv:
        print(__doc__)
        sys.exit(1)
    reset_database()
    try:
        run_checks()
    finally:
        reset_database()
    failed = [r for r in results if not r[2]]
    print(f"\n{len(results) - len(failed)}/{len(results)} checks passed")
    for page, what, _, detail in failed:
        print(f"  FAILED: {page}: {what}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
