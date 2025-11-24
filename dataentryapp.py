import streamlit as st
import pandas as pd
from datetime import date, datetime
import io  # για Excel export
from supabase import create_client

PLATE_OPTIONS = [
    "ΕΚΒ 4058", "ΙΑΕ 6034", "ΝΧΥ 3413", "ΙΕΜ 1556", "ΖΝΒ 7991",
    "ΖΝΒ 7971", "XZH1006", "ΝΧΥ 3547", "ΙΤΜ 3656", "ΝΧΥ 3546",
    "ΙΕΜ 1356", "IAE 4351", "ΕΚΒ 3941", "ΒΚΤ 9409"
]

DRIVER_OPTIONS = ["Βακαλφώτης", "Αγγίδου"]


# ---------- SUPABASE CLIENT ----------

@st.cache_resource
def get_supabase_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)


supabase = get_supabase_client()


# ---------- CRUD ΣΥΝΑΡΤΗΣΕΙΣ ----------

def insert_record(
    plate, dt, route, start_km, end_km, total_km, kilos, litres, consumption, driver
):
    data = {
        "plate": plate,
        "dt": str(dt),  # ISO date string (yyyy-mm-dd)
        "route": route if route else None,
        "start_km": float(start_km),
        "end_km": float(end_km),
        "total_km": float(total_km),
        "kilos": float(kilos),
        "litres": float(litres),
        "consumption": consumption if consumption else None,
        "driver": driver,
        # ΥΠΟΘΕΤΟΥΜΕ ότι θα υπάρχει πεδίο is_closed στη βάση
        "is_closed": False,
    }

    supabase.table("routes").insert(data).execute()


def get_all_records() -> pd.DataFrame:
    res = (
        supabase.table("routes")
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    data = res.data or []
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def get_open_records() -> pd.DataFrame:
    """
    Επιστρέφει μόνο τα δρομολόγια που δεν έχουν κλείσει (is_closed = false).
    ΥΠΟΘΕΤΕΙ ότι το πεδίο is_closed υπάρχει στη βάση.
    """
    res = (
        supabase.table("routes")
        .select("*")
        .eq("is_closed", False)
        .order("id", desc=True)
        .execute()
    )
    data = res.data or []
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)


def update_record(
    record_id,
    plate=None,
    dt=None,
    route=None,
    start_km=None,
    end_km=None,
    total_km=None,
    kilos=None,
    litres=None,
    consumption=None,
    driver=None,
):
    update_data = {}
    if plate is not None:
        update_data["plate"] = plate
    if dt is not None:
        update_data["dt"] = str(dt)
    if route is not None:
        update_data["route"] = route
    if start_km is not None:
        update_data["start_km"] = float(start_km)
    if end_km is not None:
        update_data["end_km"] = float(end_km)
    if total_km is not None:
        update_data["total_km"] = float(total_km)
    if kilos is not None:
        update_data["kilos"] = float(kilos)
    if litres is not None:
        update_data["litres"] = float(litres)
    if consumption is not None:
        update_data["consumption"] = consumption
    if driver is not None:
        update_data["driver"] = driver

    if not update_data:
        return

    supabase.table("routes").update(update_data).eq("id", record_id).execute()


def close_record(record_id):
    """
    Θέτει is_closed = true και κλειδώνει το δρομολόγιο.
    ΥΠΟΘΕΤΕΙ πεδία is_closed, closed_at.
    """
    supabase.table("routes").update(
        {
            "is_closed": True,
            "closed_at": datetime.utcnow().isoformat()
        }
    ).eq("id", record_id).execute()


def delete_record(record_id: int):
    supabase.table("routes").delete().eq("id", record_id).execute()


# ---------- STREAMLIT APP ----------

st.set_page_config(page_title="Δρομολόγια Οχημάτων", layout="centered")

st.title("🚚 Καταχώρηση Δρομολογίων (Supabase)")

tab_new, tab_open, tab_all = st.tabs(["🆕 Νέο Δρομολόγιο", "✏️ Ανοιχτά Δρομολόγια", "📄 Όλα & Αναφορές"])


# =========================
# TAB 1: ΝΕΟ ΔΡΟΜΟΛΟΓΙΟ
# =========================
with tab_new:
    st.subheader("🆕 Καταχώρηση νέου δρομολογίου")

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

        submitted = st.form_submit_button("✅ Έναρξη / Αποθήκευση")

        if submitted:
            if end_km < start_km:
                st.error("Το End Km δεν μπορεί να είναι μικρότερο από το Start Km.")
            else:
                try:
                    insert_record(
                        plate=plate,
                        dt=dt,
                        route=route,
                        start_km=start_km,
                        end_km=end_km,
                        total_km=total_km,
                        kilos=kilos,
                        litres=litres,
                        consumption=consumption,
                        driver=driver,
                    )
                    st.success("Το δρομολόγιο καταχωρήθηκε ως ανοιχτό ✅")
                except Exception as e:
                    st.error("Σφάλμα κατά την αποθήκευση στην Supabase.")
                    st.exception(e)


# =========================
# TAB 2: ΑΝΟΙΧΤΑ ΔΡΟΜΟΛΟΓΙΑ (EDIT / LOCK)
# =========================
with tab_open:
    st.subheader("✏️ Ανοιχτά δρομολόγια (σε εξέλιξη)")

    try:
        open_df = get_open_records()
    except Exception as e:
        st.error("Πρόβλημα ανάκτησης ανοιχτών δρομολογίων από Supabase.")
        st.exception(e)
        open_df = pd.DataFrame()

    if open_df is not None and not open_df.empty:
        # Μετατροπή dt σε date αν υπάρχει
        if "dt" in open_df.columns:
            open_df["dt"] = pd.to_datetime(open_df["dt"]).dt.date

        # Φίλτρα
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            plate_filter = st.multiselect(
                "Φίλτρο πινακίδας",
                options=sorted(open_df["plate"].dropna().unique())
            )
        with colf2:
            driver_filter = st.multiselect(
                "Φίλτρο οδηγού",
                options=sorted(open_df["driver"].dropna().unique())
            )
        with colf3:
            if "dt" in open_df.columns and not open_df["dt"].isna().all():
                min_date = open_df["dt"].min()
                max_date = open_df["dt"].max()
            else:
                min_date = date.today()
                max_date = date.today()
            date_range = st.date_input(
                "Ημερομηνία από / έως",
                value=(min_date, max_date)
            )

        filtered_open = open_df.copy()

        if plate_filter:
            filtered_open = filtered_open[filtered_open["plate"].isin(plate_filter)]

        if driver_filter:
            filtered_open = filtered_open[filtered_open["driver"].isin(driver_filter)]

        if isinstance(date_range, (tuple, list)):
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range

        if "dt" in filtered_open.columns and start_date and end_date:
            filtered_open = filtered_open[
                (filtered_open["dt"] >= start_date) & (filtered_open["dt"] <= end_date)
            ]

        st.markdown("### 📋 Ανοιχτά δρομολόγια")
        st.dataframe(filtered_open, use_container_width=True)

        # Επιλογή δρομολογίου για επεξεργασία
        st.markdown("### ✏️ Επιλογή δρομολογίου για επεξεργασία")

        if not filtered_open.empty:
            ids = filtered_open["id"].tolist()
            id_labels = [
                f"ID {row['id']} – {row['plate']} – {row['dt']} – {row['driver']}"
                for _, row in filtered_open.iterrows()
            ]
            selected_label = st.selectbox(
                "Διάλεξε δρομολόγιο",
                options=id_labels,
                index=0,
            )

            # Βρίσκουμε το αντίστοιχο ID
            selected_id_str = selected_label.split(" ")[1]  # "ID 123 – ..."
            try:
                selected_id = int(selected_id_str)
            except ValueError:
                selected_id = None

            if selected_id is not None:
                row = filtered_open[filtered_open["id"] == selected_id].iloc[0]

                st.markdown("#### ✏️ Επεξεργασία δρομολογίου")

                with st.form(f"edit_form_{selected_id}"):
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        e_plate = st.selectbox(
                            "Αριθμός πινακίδας",
                            PLATE_OPTIONS,
                            index=PLATE_OPTIONS.index(row["plate"]) if row["plate"] in PLATE_OPTIONS else 0
                        )
                    with ecol2:
                        e_dt = st.date_input(
                            "Ημερομηνία",
                            value=row["dt"] if isinstance(row["dt"], date) else date.today()
                        )

                    e_route = st.text_input("Δρομολόγιο", value=row.get("route", "") or "")

                    ecol3, ecol4 = st.columns(2)
                    with ecol3:
                        e_start_km = st.number_input(
                            "Start Km",
                            min_value=0.0,
                            step=1.0,
                            format="%.0f",
                            value=float(row.get("start_km") or 0),
                            key=f"start_{selected_id}",
                        )
                    with ecol4:
                        e_end_km = st.number_input(
                            "End Km",
                            min_value=0.0,
                            step=1.0,
                            format="%.0f",
                            value=float(row.get("end_km") or 0),
                            key=f"end_{selected_id}",
                        )

                    if e_end_km >= e_start_km:
                        e_total_km = e_end_km - e_start_km
                    else:
                        e_total_km = 0

                    st.number_input(
                        "Total Km (υπολογίζεται αυτόματα)",
                        value=float(e_total_km),
                        disabled=True,
                        key=f"total_{selected_id}",
                    )

                    ecol5, ecol6 = st.columns(2)
                    with ecol5:
                        e_kilos = st.number_input(
                            "Κιλά",
                            min_value=0.0,
                            step=10.0,
                            format="%.2f",
                            value=float(row.get("kilos") or 0),
                            key=f"kilos_{selected_id}",
                        )
                    with ecol6:
                        e_litres = st.number_input(
                            "Λίτρα",
                            min_value=0.0,
                            step=1.0,
                            format="%.2f",
                            value=float(row.get("litres") or 0),
                            key=f"litres_{selected_id}",
                        )

                    e_consumption = st.text_input(
                        "Κατανάλωση",
                        value=row.get("consumption", "") or "",
                        key=f"cons_{selected_id}",
                    )

                    e_driver = st.selectbox(
                        "Οδηγός",
                        DRIVER_OPTIONS,
                        index=DRIVER_OPTIONS.index(row["driver"]) if row["driver"] in DRIVER_OPTIONS else 0,
                        key=f"driver_{selected_id}",
                    )

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        save_changes = st.form_submit_button("💾 Αποθήκευση αλλαγών")
                    with col_btn2:
                        close_trip = st.form_submit_button("✅ Λήξη & Κλείδωμα")

                    if save_changes:
                        try:
                            update_record(
                                record_id=selected_id,
                                plate=e_plate,
                                dt=e_dt,
                                route=e_route,
                                start_km=e_start_km,
                                end_km=e_end_km,
                                total_km=e_total_km,
                                kilos=e_kilos,
                                litres=e_litres,
                                consumption=e_consumption,
                                driver=e_driver,
                            )
                            st.success("Οι αλλαγές αποθηκεύτηκαν ✅")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error("Σφάλμα κατά την ενημέρωση του δρομολογίου.")
                            st.exception(e)

                    if close_trip:
                        try:
                            # Πρώτα σώζουμε τις τελευταίες τιμές
                            update_record(
                                record_id=selected_id,
                                plate=e_plate,
                                dt=e_dt,
                                route=e_route,
                                start_km=e_start_km,
                                end_km=e_end_km,
                                total_km=e_total_km,
                                kilos=e_kilos,
                                litres=e_litres,
                                consumption=e_consumption,
                                driver=e_driver,
                            )
                            # Μετά κλειδώνουμε
                            close_record(selected_id)
                            st.success("Το δρομολόγιο έκλεισε και κλειδώθηκε ✅")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error("Σφάλμα κατά το κλείδωμα του δρομολογίου.")
                            st.exception(e)
    else:
        st.info("Δεν υπάρχουν ανοιχτά δρομολόγια.")


# =========================
# TAB 3: ΟΛΑ ΤΑ ΔΡΟΜΟΛΟΓΙΑ / ΑΝΑΦΟΡΕΣ
# =========================
with tab_all:
    st.subheader("📄 Όλα τα δρομολόγια & αναφορές")

    try:
        df = get_all_records()
    except Exception as e:
        st.error("Πρόβλημα σύνδεσης με Supabase. Έλεγξε URL / anon key & table 'routes'.")
        st.exception(e)
        st.stop()

    if df is not None and not df.empty:
        if "dt" in df.columns:
            df["dt"] = pd.to_datetime(df["dt"]).dt.date

        if "is_closed" in df.columns:
            df["status"] = df["is_closed"].apply(lambda x: "Κλειστό" if x else "Ανοιχτό")

        min_date = df["dt"].min()
        max_date = df["dt"].max()

        st.markdown("### 🔍 Φίλτρα")

        colf1, colf2, colf3 = st.columns(3)

        with colf1:
            plate_filter = st.multiselect(
                "Φίλτρο πινακίδας",
                options=sorted(df["plate"].dropna().unique())
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

        # Export σε Excel
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

        # Διαγραφή εγγραφών
        st.markdown("### 🗑️ Διαγραφή εγγραφών (με βάση τα φιλτραρισμένα)")

        if not filtered_df.empty:
            for _, row in filtered_df.iterrows():
                colA, colB = st.columns([6, 1])
                with colA:
                    st.write(
                        f"ID: {row['id']} – {row['plate']} – {row['dt']} – {row.get('driver', '')}"
                    )
                with colB:
                    if st.button("🗑️", key=f"del_{row['id']}"):
                        try:
                            delete_record(int(row["id"]))
                            st.success(f"Η εγγραφή με ID {row['id']} διαγράφηκε.")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error("Σφάλμα κατά τη διαγραφή από Supabase.")
                            st.exception(e)
    else:
        st.info("Δεν υπάρχουν ακόμη εγγραφές.")
