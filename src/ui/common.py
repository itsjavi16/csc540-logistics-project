# Navigation and shared widgets for the Streamlit app.

# Navigation follows "Project Application Flow": each screen is a page name in st.session_state["page"], and the buttons on a screen (GoBack, LandingPage,
# Cancel, Logout) move between them. No SQL lives in the UI; every screen calls functions in src/models or src/reports.

from datetime import date, datetime
from decimal import Decimal

import pandas as pd
import pymysql
import streamlit as st

from src.db.helpers import friendly_error

STATUS_LABELS = {
    "CREATED": "Created",
    "RECEIVED": "Received",
    "IN_TRANSIT": "In Transit",
    "ARRIVED_AT_HUB": "Arrived at Hub",
    "OUT_FOR_DELIVERY": "Out for Delivery",
    "DELIVERED": "Delivered",
    "ON_TIME": "On time",
    "LATE": "Late",
}

LANDING = {
    "SHIPPER": "shipper_landing",
    "CARRIER": "carrier_landing",
    "VIEWER": "viewer_landing",
}


# navigation


def go(page, **params):
    # Move to another screen. Used as a button on_click callback
    st.session_state["page"] = page
    st.session_state["params"] = params
    # Each screen starts with fresh input boxes.
    for k in [k for k in st.session_state if k.startswith("in_")]:
        del st.session_state[k]


def flash(result_or_text, ok=True):
    # Message to show at the top of the next screen
    if hasattr(result_or_text, "ok"):
        st.session_state["flash"] = (result_or_text.ok, result_or_text.message)
    else:
        st.session_state["flash"] = (ok, result_or_text)


def show_flash():
    msg = st.session_state.pop("flash", None)
    if msg:
        (st.success if msg[0] else st.error)(msg[1])


def user():
    return st.session_state.get("user")


def require_role(role):
    # Stop rendering unless someone with this role is logged in
    u = user()
    if not u or u["role"] != role:
        st.warning("Please log in first.")
        st.button("Home", on_click=go, args=("home",))
        st.stop()
    return u


def logout():
    st.session_state.pop("user", None)
    go("home")


def header(title, crumbs=None):
    # Page title, where you are, and who is logged in
    u = user()
    top = st.columns([3, 1])
    with top[0]:
        if crumbs:
            st.caption(" › ".join(crumbs))
        st.title(title)
    with top[1]:
        if u:
            who = u["display_name"]
            extra = u.get("company_name") or (
                f"Shipper {u['shipper_id']}" if u.get("shipper_id") else ""
            )
            st.caption(
                f"Logged in as **{who}**"
                + (f"  \n{extra}" if extra else "")
                + f"  \n{u['role'].title()}"
            )
    show_flash()


def nav_buttons(buttons):
    # Row of navigation buttons: [(label, page), ...]. A page of None logs out
    cols = st.columns(len(buttons))
    for col, (label, page) in zip(cols, buttons):
        with col:
            if page is None:
                st.button(label, on_click=logout, width="stretch", key=f"nav_{label}")
            else:
                st.button(
                    label,
                    on_click=go,
                    args=(page,),
                    width="stretch",
                    key=f"nav_{label}",
                )


def menu(items):
    # A landing/menu screen: one big button per numbered option, like the flow's menus
    for i, (label, page) in enumerate(items, start=1):
        if page is None:
            st.button(
                f"{i}.  {label}", on_click=logout, width="stretch", key=f"menu_{i}"
            )
        else:
            st.button(
                f"{i}.  {label}",
                on_click=go,
                args=(page,),
                width="stretch",
                key=f"menu_{i}",
            )


# input helpers


def parse_id(text, what):
    # Positive integer from a text box, or (None, error message)
    t = (text or "").strip()
    if not t:
        return None, f"Enter the {what}."
    if not t.isdigit() or int(t) <= 0:
        return None, f"The {what} must be a positive whole number."
    return int(t), None


def hub_input(label, key, value=""):
    return (
        st.text_input(label, key=key, value=value, max_chars=3, placeholder="e.g. RDU")
        .strip()
        .upper()
    )


def date_range_inputs():
    c1, c2 = st.columns(2)
    with c1:
        start = st.date_input(
            "A. Start Date", value=date(date.today().year, 1, 1), key="in_start"
        )
    with c2:
        end = st.date_input("B. End Date", value=date.today(), key="in_end")
    return start, end


def check_range(start, end):
    if start > end:
        st.error("The start date must be on or before the end date.")
        return False
    return True


def datetime_inputs(label, key, default=None):
    default = default or datetime.now().replace(second=0, microsecond=0)
    c1, c2 = st.columns(2)
    with c1:
        d = st.date_input(f"{label} (date)", value=default.date(), key=f"{key}_d")
    with c2:
        t = st.time_input(
            f"{label} (time)", value=default.time(), key=f"{key}_t", step=60
        )
    return datetime.combine(d, t)


# output helpers


def _clean(v):
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, str) and v in STATUS_LABELS:
        return STATUS_LABELS[v]
    return v


def table(rows, rename=None, empty="Nothing to show."):
    if not rows:
        st.info(empty)
        return
    df = pd.DataFrame([{k: _clean(v) for k, v in r.items()} for r in rows])
    if rename:
        df = df.rename(columns=rename)
    else:
        df.columns = [c.replace("_", " ").capitalize() for c in df.columns]
    st.dataframe(df, hide_index=True, width="stretch")


def show_result(result):
    (st.success if result.ok else st.error)(result.message)


def db_call(fn, *args, **kwargs):
    # Run a data-layer read; on a database error show it and stop the screen
    try:
        return fn(*args, **kwargs)
    except pymysql.MySQLError as e:
        st.error(friendly_error(e))
        st.stop()


def reference(title, rows, rename=None):
    # Collapsible lookup table (valid hubs, lanes, your shipments...)
    with st.expander(title):
        table(rows, rename)


def status_label(code):
    return STATUS_LABELS.get(code, code)
