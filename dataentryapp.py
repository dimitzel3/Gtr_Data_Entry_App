import streamlit as st
import sqlite3
from datetime import date
import pandas as pd

DB_NAME = "data.db"

PLATE_OPTIONS = [
    "ΕΚΒ 4058", "ΙΑΕ 6034", "ΝΧΥ 3413", "ΙΕΜ 1556", "ΖΝΒ 7991",
    "ΖΝΒ 7971", "XZH1006", "ΝΧΥ 3547", "ΙΤΜ 3656", "ΝΧΥ 3546",
    "ΙΕΜ 1356", "IAE 4351", "ΕΚΒ 3941", "ΒΚΤ 9409"
]

DRIVER_OPTIONS = ["Βακαλφώτης", "Αγγίδου"]


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT NOT NULL,
            dt TEXT NOT NULL,
            route TEXT,
            start_km REAL,
            end_km REAL,
            total_km REAL,
            kilos REAL,
            litres REAL,
            consumption TEXT,
            driver TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def insert_record(
    plate, dt, route, start_km, end_km, total_km, kilos, litres, consumption, driver
):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO routes
        (plate, dt, route, start_km, end_km, total_km, kilos, litres, consumption, driver)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (plate, dt, route, start_km, end_km, total_km, kilos, litres, consumption, driver),
    )
    conn.commit()
    conn.close()


def get_records():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query(
        "SELECT id, plate, dt, route, start_km, end_km, total_km, kilos, litres, consumption, driver "
        "FROM routes ORDER BY id DESC",
        conn,
    )
    conn.close()
    return df


# --- APP ---

init_db()
st.set_page_config(page_title="Δρομολόγια Οχημάτων", layout="centered")

st.title("🚚 Καταχώρηση Δρομολογίων")

with st.form("route_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
        plate = st.selectbox("Αριθμός πινακίδας", PLATE_OPTIONS)
    with col2:
        dt = st.date_input("Ημερομηνία", value=date.today())

    route = st.text_input("Δρομολόγιο")

    col3, col4 = st.columns(2)
    with col3:
        start_km = st.number_input("Start Km", min_value=0.0, step=1.0, format="%.0f")
    with col4:
        end_km = st.number_input("End Km", min_value=0.0, step=1.0, format="%.0f")

    # Υπολογισμός Total Km
    total_km = None
    if end_km >= start_km:
        total_km = end_km - start_km
    else:
        total_km = 0

    st.number_input(
        "Total Km (υπολογίζεται αυτόματα)",
        value=float(total_km),
        disabled=True
    )

    col5, col6 = st.columns(2)
    with col5:
        kilos = st.number_input("Κιλά", min_value=0.0, step=10.0, format="%.2f")
    with col6:
        litres = st.number_input("Λίτρα", min_value=0.0, step=1.0, format="%.2f")

    consumption = st.text_input("Κατανάλωση")

    driver = st.selectbox("Οδηγός", DRIVER_OPTIONS)

    submitted = st.form_submit_button("✅ Αποθήκευση")

    if submitted:
        # Μικροί έλεγχοι
        if end_km < start_km:
            st.error("Το End Km δεν μπορεί να είναι μικρότερο από το Start Km.")
        else:
            insert_record(
                plate=plate,
                dt=str(dt),
                route=route,
                start_km=float(start_km),
                end_km=float(end_km),
                total_km=float(total_km),
                kilos=float(kilos),
                litres=float(litres),
                consumption=consumption,
                driver=driver,
            )
            st.success("Η εγγραφή αποθηκεύτηκε με επιτυχία ✅")


st.subheader("📄 Τελευταίες εγγραφές")

df = get_records()
if df is not None and not df.empty:
    st.dataframe(df, use_container_width=True)
else:
    st.info("Δεν υπάρχουν ακόμη εγγραφές.")
