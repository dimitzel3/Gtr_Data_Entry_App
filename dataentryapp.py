import streamlit as st
import sqlite3
from datetime import date
import pandas as pd
import io  # για Excel export

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
        """
        SELECT
            id,
            plate,
            dt,
            route,
            start_km,
            end_km,
            total_km,
            kilos,
            litres,
            consumption,
            driver
        FROM routes
        ORDER BY id DESC
        """,
        conn,
    )
    conn.close()
    return df


def delete_record(record_id: int):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM routes WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()


# --- APP ---

init_db()
st.set_page_config(page_title="Δρομολόγια Οχημάτων", layout="centered")

st.title("🚚 Καταχώρηση Δρομολογίων")

# ΦΟΡΜΑ ΚΑΤΑΧΩΡΗΣΗΣ
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


# ΠΡΟΒΟΛΗ / ΦΙΛΤΡΑ / EXPORT / DELETE
st.subheader("📄 Τελευταίες εγγραφές & φίλτρα")

df = get_records()
if df is not None and not df.empty:
    # Μετατροπή dt σε datetime.date
    df["dt"] = pd.to_datetime(df["dt"]).dt.date

    # Default τιμές για range ημερομηνίας
    min_date = df["dt"].min()
    max_date = df["dt"].max()

    st.markdown("### 🔍 Φίλτρα")

    colf1, colf2, colf3 = st.columns(3)

    with colf1:
        plate_filter = st.multiselect(
            "Φίλτρο πινακίδας",
            options=sorted(df["plate"].unique())
        )

    with colf2:
        driver_filter = st.multiselect(
            "Φίλτρο οδηγού",
            options=sorted(df["driver"].dropna().unique())
        )

    with colf3:
        date_range = st.date_input(
            "Ημερομηνία από / έως",
            value=(min_date, max_date)
        )

    # Εφαρμογή φίλτρων
    filtered_df = df.copy()

    if plate_filter:
        filtered_df = filtered_df[filtered_df["plate"].isin(plate_filter)]

    if driver_filter:
        filtered_df = filtered_df[filtered_df["driver"].isin(driver_filter)]

    if isinstance(date_range, (tuple, list)):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    if start_date and end_date:
        filtered_df = filtered_df[
            (filtered_df["dt"] >= start_date) & (filtered_df["dt"] <= end_date)
        ]

    st.markdown("### 📊 Αποτελέσματα")
    st.dataframe(filtered_df, use_container_width=True)

    # --- Export σε Excel (φιλτραρισμένα δεδομένα) ---
    if not filtered_df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            filtered_df.to_excel(writer, index=False, sheet_name="Routes")
        output.seek(0)

        st.download_button(
            label="📥 Λήψη σε Excel",
            data=output,
            file_name="routes_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    # --- Διαγραφή εγγραφών ---
    st.markdown("### 🗑️ Διαγραφή εγγραφών (με βάση τα φιλτραρισμένα)")

    if not filtered_df.empty:
        for _, row in filtered_df.iterrows():
            colA, colB = st.columns([6, 1])
            with colA:
                st.write(
                    f"ID: {row['id']} – {row['plate']} – {row['dt']} – {row['driver']}"
                )
            with colB:
                if st.button("🗑️", key=f"del_{row['id']}"):
                    delete_record(int(row["id"]))
                    st.success(f"Η εγγραφή με ID {row['id']} διαγράφηκε.")
                    st.rerun()
else:
    st.info("Δεν υπάρχουν ακόμη εγγραφές.")
