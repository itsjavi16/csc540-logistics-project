# Streamlit front end for the freight tracking application.

# Run from the project root (with your venv/conda env active):
# streamlit run src/ui/app.py

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import pymysql
import streamlit as st

from src.db.helpers import friendly_error
from src.models.auth import login
from src.reports.required_queries import load_queries, run_query
from src.ui import carrier, shipper, viewer
from src.ui.common import LANDING, flash, go, header, nav_buttons, table

st.set_page_config(page_title="Freight Tracking", page_icon="🚚", layout="wide")


# home page


def home():
    header("Freight Tracking and Delivery Management", ["Home"])
    st.write("Choose an option.")
    c = st.columns([2, 3])[0]
    with c:
        st.button(
            "1.  Shipper Login",
            on_click=go,
            args=("login_shipper",),
            width="stretch",
            key="home_1",
        )
        st.button(
            "2.  Carrier Login",
            on_click=go,
            args=("login_carrier",),
            width="stretch",
            key="home_2",
        )
        st.button(
            "3.  Viewer Login",
            on_click=go,
            args=("login_viewer",),
            width="stretch",
            key="home_3",
        )
        st.button(
            "4.  View Queries",
            on_click=go,
            args=("view_queries",),
            width="stretch",
            key="home_4",
        )
        st.button(
            "5.  Exit", on_click=go, args=("exit",), width="stretch", key="home_5"
        )


def exit_screen():
    st.session_state.pop("user", None)
    st.title("Goodbye")
    st.write("You've exited the application. You can close this tab.")
    st.button("Start again", on_click=go, args=("home",))


# login


def login_screen(role):
    label = role.title()
    header(f"{label}: Login", ["Home", f"{label} Login"])
    with st.form("login_form"):
        uid = st.text_input(
            "A. User ID", key="in_uid", help="Your username or numeric user ID."
        )
        pw = st.text_input("B. Password", type="password", key="in_pw")
        signed_in = st.form_submit_button("1. Sign-In", type="primary")
    st.button("2. GoBack", on_click=go, args=("home",))

    if signed_in:
        try:
            u = login(uid, pw, role)
        except pymysql.MySQLError as e:
            st.error(friendly_error(e))
            return
        if u is None:
            st.error("Login Incorrect. Please enter your User ID and password again.")
        else:
            st.session_state["user"] = u
            go(LANDING[role])
            flash(f"Welcome, {u['display_name']}.")
            st.rerun()


# view queries


def view_queries():
    header("View Queries", ["Home", "View Queries"])
    try:
        queries = load_queries()
    except OSError as e:
        st.error(f"Couldn't read db/queries/required_queries.sql: {e}")
        nav_buttons([("Home", "home")])
        return

    st.write("Select a query to run. Queries with a parameter ask for it first.")
    labels = {f"{q['number']}. {q['title']}": q for q in queries}
    choice = st.radio(
        "Queries", list(labels), key="in_query", label_visibility="collapsed"
    )
    q = labels[choice]

    values = {}
    if q["params"]:
        if q["param_help"]:
            st.caption(f"Parameter: {q['param_help']}")
        cols = st.columns(len(q["params"]))
        for col, (name, default) in zip(cols, q["params"].items()):
            with col:
                if isinstance(default, int) or default is None:
                    values[name] = st.number_input(
                        name.replace("_", " ").capitalize(),
                        value=default or 1,
                        min_value=1,
                        step=1,
                        key=f"in_q{q['number']}_{name}",
                    )
                else:
                    values[name] = st.text_input(
                        name.replace("_", " ").capitalize(),
                        value=str(default),
                        key=f"in_q{q['number']}_{name}",
                    )

    c1, c2 = st.columns([1, 5])
    with c1:
        run = st.button("Run query", type="primary")
    with c2:
        show_sql = st.toggle("Show SQL", key="in_show_sql")
    if show_sql:
        st.code(q["sql"], language="sql")
    if run:
        try:
            rows = run_query(q, values)
        except pymysql.MySQLError as e:
            st.error(friendly_error(e))
        else:
            st.caption(f"{len(rows)} row(s)")
            table(rows, empty="The query returned no rows.")
    st.divider()
    nav_buttons([("GoBack", "home")])


#  router

PAGES = {
    "home": home,
    "exit": exit_screen,
    "login_shipper": lambda: login_screen("SHIPPER"),
    "login_carrier": lambda: login_screen("CARRIER"),
    "login_viewer": lambda: login_screen("VIEWER"),
    "view_queries": view_queries,
    **shipper.PAGES,
    **carrier.PAGES,
    **viewer.PAGES,
}


def main():
    page = st.session_state.get("page", "home")
    if page not in PAGES:
        page = "home"
    PAGES[page]()


main()
