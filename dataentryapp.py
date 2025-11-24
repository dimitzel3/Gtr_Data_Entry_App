import streamlit as st
import pandas as pd
from datetime import date, datetime
import io  # για Excel export
from supabase import create_client

# Δρομολόγια (ενδεικτικές επιλογές – άλλαξέ τες όπως θες)
ROUTE_OPTIONS = [
    "Πρωινή διανομή",
    "Απογευματινή διανομή",
    "Επαρχία",
    "Επιστροφή αποθήκης",
]

# Οχήματα
VEHICLE_OPTIONS = [
    "ΕΚΒ 4058", "ΙΑΕ 6034", "ΝΧΥ 3413", "ΙΕΜ 1556", "ΖΝΒ 7991",
    "ΖΝΒ 7971", "XZH1006", "ΝΧΥ 3547", "ΙΤΜ 3656", "ΝΧΥ 3546",
    "ΙΕΜ 1356", "IAE 4351", "ΕΚΒ 3941", "ΒΚΤ 9409"
]

# Οδηγοί
DRIVER_OPTIONS = ["Βακαλφώτης", "Αγγίδου"]


# ---------- SUPABASE CLIENT ----------

@st.cache_resource
def get_supabase_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)


supabase = get_supabase_client()


# ---------- ΒΟΗΘΗΤΙΚΟ ΓΙΑ FLOAT/NULL ----------

def to_float_or_none(x):
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


# ---------- CRUD ΣΥΝΑΡΤΗΣΕΙΣ ----------

def insert_record(
    route,
    vehicle,
    start_km,
    end_km,
    total_km,
    driver,
    started_at,
    # Milk fields
    sheep_conv_kg,
    goat_conv_kg,
    total_conv_kg_scale,
    conv_da_refs,
    sheep_bio_kg,
    goat_bio_kg,
    bio_da_refs,
    total_all_da,
    total_all_scale,
    diff_da_vs_scale,
):
    """
    Δημιουργεί νέο δρομολόγιο (ανοιχτό).
    started_at = datetime (ημερομηνία & ώρα έναρξης)
    """
    data = {
        "route": route if route else None,
        "plate": vehicle,
        "start_km": to_float_or_none(start_km),
        "end_km": to_float_or_none(end_km),           # συνήθως None στην αρχή
        "total_km": to_float_or_none(total_km),       # συνήθως None στην αρχή
        "driver": driver,
        "dt": started_at.date().isoformat(),          # για φίλτρα ημερομηνίας
        "started_at": started_at.isoformat(),         # full datetime έναρξης
        "is_closed": False,
        # milk fields
        "sheep_conv_kg": to_float_or_none(sheep_conv_kg),
        "goat_conv_kg": to_float_or_none(goat_conv_kg),
        "total_conv_kg_scale": to_float_or_none(total_conv_kg_scale),
        "conv_da_refs": conv_da_refs if conv_da_refs else None,
        "sheep_bio_kg": to_float_or_none(sheep_bio_kg),
        "goat_bio_kg": to_float_or_none(goat_bio_kg),
        "bio_da_refs": bio_da_refs if bio_da_refs else None,
        "total_all_da": to_float_or_none(total_all_da),
        "total_all_scale": to_float_or_none(total_all_scale),
        "diff_da_vs_scale": to_float_or_none(diff_da_vs_scale),
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
    route=None,
    vehicle=None,
    start_km=None,
    end_km=None,
    total_km=None,
    driver=None,
    # milk fields
    sheep_conv_kg=None,
    goat_conv_kg=None,
    total_conv_kg_scale=None,
    conv_da_refs=None,
    sheep_bio_kg=None,
    goat_bio_kg=None,
    bio_da_refs=None,
    total_all_da=None,
    total_all_scale=None,
    diff_da_vs_scale=None,
):
    update_data = {}
    if route is not None:
        update_data["route"] = route
    if vehicle is not None:
        update_data["plate"] = vehicle
    if start_km is not None:
        update_data["start_km"] = to_float_or_none(start_km)
    if end_km is not None:
        update_data["end_km"] = to_float_or_none(end_km)
    if total_km is not None:
        update_data["total_km"] = to_float_or_none(total_km)
    if driver is not None:
        update_data["driver"] = driver

    # milk fields
    if sheep_conv_kg is not None:
        update_data["sheep_conv_kg"] = to_float_or_none(sheep_conv_kg)
    if goat_conv_kg is not None:
        update_data["goat_conv_kg"] = to_float_or_none(goat_conv_kg)
    if total_conv_kg_scale is not None:
        update_data["total_conv_kg_scale"] = to_float_or_none(total_conv_kg_scale)
    if conv_da_refs is not None:
        update_data["conv_da_refs"] = conv_da_refs
    if sheep_bio_kg is not None:
        update_data["sheep_bio_kg"] = to_float_or_none(sheep_bio_kg)
    if goat_bio_kg is not None:
        update_data["goat_bio_kg"] = to_float_or_none(goat_bio_kg)
    if bio_da_refs is not None:
        update_data["bio_da_refs"] = bio_da_refs
    if total_all_da is not None:
        update_data["total_all_da"] = to_float_or_none(total_all_da)
    if total_all_scale is not None:
        update_data["total_all_scale"] = to_float_or_none(total_all_scale)
    if diff_da_vs_scale is not None:
        update_data["diff_da_vs_scale"] = to_float_or_none(diff_da_vs_scale)

    if not update_data:
        return

    supabase.table("routes").update(update_data).eq("id", record_id).execute()


def close_record(record_id):
    """
    Θέτει is_closed = true και κλειδώνει το δρομολόγιο.
    Χρησιμοποιούμε closed_at σαν ημερομηνία/ώρα λήξης.
    """
    now = datetime.utcnow().isoformat()
    supabase.table("routes").update(
        {
            "is_closed": True,
            "closed_at": now
        }
    ).eq("id", record_id).execute()


def delete_record(record_id: int):
    supabase.table("routes").delete().eq("id", record_id).execute()


# ---------- STREAMLIT APP ----------

st.set_page_config(page_title="Δρομολόγια Οχημάτων", layout="centered")

st.title("🚚 Καταχώρηση Δρομολογίων & Συλλογή Γάλακτος")

tab_new, tab_open, tab_all = st.tabs([
    "🆕 Νέο Δρομολόγιο",
    "✏️ Ανοιχτά Δρομολόγια",
    "📄 Όλα & Αναφορές"
])


# =========================
# TAB 1: ΝΕΟ ΔΡΟΜΟΛΟΓΙΟ
# =========================
with tab_new:
    st.subheader("🆕 Έναρξη νέου δρομολογίου")

    st.info("Η ημερομηνία & ώρα έναρξης θα καταγραφεί αυτόματα με την αποθήκευση.")

    with st.form("route_form", clear_on_submit=True):
        # 2) Δρομολόγιο (dropdown)
        route = st.selectbox("Δρομολόγιο", ROUTE_OPTIONS)

        # 3) Όχημα (dropdown)
        vehicle = st.selectbox("Όχημα", VEHICLE_OPTIONS)

        # 4) Χιλιομετρική ένδειξη έναρξης
        start_km = st.number_input(
            "Χιλιομετρική ένδειξη ΕΝΑΡΞΗΣ",
            min_value=0.0,
            step=1.0,
            format="%.0f"
        )

        # 5) Χιλιομετρική ένδειξη λήξης (προαιρετικά σε αυτή τη φάση)
        end_km = st.number_input(
            "Χιλιομετρική ένδειξη ΛΗΞΗΣ (προαιρετικά, μπορεί να συμπληρωθεί αργότερα)",
            min_value=0.0,
            step=1.0,
            format="%.0f"
        )

        # 6) Συνολικά χιλιόμετρα (End - Start, μόνο αν End > Start)
        if end_km > 0 and end_km >= start_km:
            total_km = end_km - start_km
        else:
            total_km = 0

        st.number_input(
            "Συνολικά διανυθέντα χιλιόμετρα (υπολογίζονται αυτόματα)",
            value=float(total_km),
            disabled=True
        )

        # Ονοματεπώνυμο οδηγού (dropdown)
        driver = st.selectbox("Ονοματεπώνυμο οδηγού", DRIVER_OPTIONS)

        st.markdown("---")
        st.subheader("🥛 Συλλογή Γάλακτος")

        col_m1, col_m2 = st.columns(2)
        with col_m1:
            sheep_conv_kg = st.number_input(
                "Πρόβειο Συμβατικό Γάλα (κιλά)",
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )
        with col_m2:
            goat_conv_kg = st.number_input(
                "Γίδινο Συμβατικό Γάλα (κιλά)",
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )

        total_conv_kg_scale = st.number_input(
            "Σύνολο Συμβατικό Γάλα (Ζυγολόγιο)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
        )

        conv_da_refs = st.text_area(
            "Σχετικά Δελτία Αποστολής (Συμβατικό)",
            placeholder="π.χ. ΔΑ 123, ΔΑ 124..."
        )

        col_m3, col_m4 = st.columns(2)
        with col_m3:
            sheep_bio_kg = st.number_input(
                "Πρόβειο Βιολογικό Γάλα (κιλά)",
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )
        with col_m4:
            goat_bio_kg = st.number_input(
                "Γίδινο Βιολογικό Γάλα (κιλά)",
                min_value=0.0,
                step=1.0,
                format="%.2f",
            )

        bio_da_refs = st.text_area(
            "Σχετικά Δελτία Αποστολής (Βιολογικό)",
            placeholder="π.χ. ΔΑ ΒΙΟ 10, ΔΑ ΒΙΟ 11..."
        )

        total_all_da = st.number_input(
            "Σύνολο Συμβατικό + Βιολογικό (ΔΑ)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
        )

        total_all_scale = st.number_input(
            "Σύνολο Συμβατικό + Βιολογικό (Ζυγολόγιο)",
            min_value=0.0,
            step=1.0,
            format="%.2f",
        )

        # Διαφορά = ΔΑ - Ζυγολόγιο
        diff_da_vs_scale = total_all_da - total_all_scale

        st.number_input(
            "Διαφορά (ΔΑ - Ζυγολόγιο)",
            value=float(diff_da_vs_scale),
            disabled=True,
        )

        submitted = st.form_submit_button("✅ Έναρξη / Αποθήκευση")

        if submitted:
            # Αν δεν έχουμε end_km ακόμη, τα αφήνουμε None
            end_km_db = end_km if end_km > 0 else None
            total_km_db = total_km if end_km_db is not None else None

            started_at = datetime.now()  # ημερομηνία & ώρα έναρξης

            try:
                insert_record(
                    route=route,
                    vehicle=vehicle,
                    start_km=start_km,
                    end_km=end_km_db,
                    total_km=total_km_db,
                    driver=driver,
                    started_at=started_at,
                    sheep_conv_kg=sheep_conv_kg,
                    goat_conv_kg=goat_conv_kg,
                    total_conv_kg_scale=total_conv_kg_scale,
                    conv_da_refs=conv_da_refs,
                    sheep_bio_kg=sheep_bio_kg,
                    goat_bio_kg=goat_bio_kg,
                    bio_da_refs=bio_da_refs,
                    total_all_da=total_all_da,
                    total_all_scale=total_all_scale,
                    diff_da_vs_scale=diff_da_vs_scale,
                )
                st.success(
                    f"Δρομολόγιο ξεκίνησε στις {started_at.strftime('%d/%m/%Y %H:%M:%S')} ✅"
                )
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

        # Αν έχουμε started_at, κρατάμε και τις ώρες
        if "started_at" in open_df.columns:
            open_df["started_at_dt"] = pd.to_datetime(open_df["started_at"], errors="coerce")
        else:
            open_df["started_at_dt"] = pd.NaT

        # Φίλτρα με μοναδικά keys
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            plate_filter = st.multiselect(
                "Φίλτρο οχήματος",
                options=sorted(open_df["plate"].dropna().unique()),
                key="plate_filter_open",
            )
        with colf2:
            driver_filter = st.multiselect(
                "Φίλτρο οδηγού",
                options=sorted(open_df["driver"].dropna().unique()),
                key="driver_filter_open",
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
                value=(min_date, max_date),
                key="date_range_open",
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
        show_cols = [
            "id", "dt", "started_at_dt", "route", "plate",
            "start_km", "end_km", "total_km", "driver"
        ]
        show_cols = [c for c in show_cols if c in filtered_open.columns]
        st.dataframe(filtered_open[show_cols], use_container_width=True)

        # Επιλογή δρομολογίου για επεξεργασία
        st.markdown("### ✏️ Επιλογή δρομολογίου για συμπλήρωση / λήξη")

        if not filtered_open.empty:
            id_labels = []
            for _, r in filtered_open.iterrows():
                start_str = ""
                if pd.notna(r.get("started_at_dt")):
                    start_str = r["started_at_dt"].strftime("%d/%m %H:%M")
                id_labels.append(
                    f"ID {r['id']} – {r['plate']} – {r['driver']} – {start_str}"
                )

            selected_label = st.selectbox(
                "Διάλεξε δρομολόγιο",
                options=id_labels,
                index=0,
            )

            # Βρίσκουμε το αντίστοιχο ID
            try:
                selected_id = int(selected_label.split(" ")[1])
            except ValueError:
                selected_id = None

            if selected_id is not None:
                row = filtered_open[filtered_open["id"] == selected_id].iloc[0]

                st.markdown("#### ✏️ Συμπλήρωση / ενημέρωση δρομολογίου & συλλογής γάλακτος")

                with st.form(f"edit_form_{selected_id}"):
                    ecol1, ecol2 = st.columns(2)
                    with ecol1:
                        e_route = st.selectbox(
                            "Δρομολόγιο",
                            ROUTE_OPTIONS,
                            index=ROUTE_OPTIONS.index(row["route"]) if row.get("route") in ROUTE_OPTIONS else 0,
                            key=f"route_{selected_id}",
                        )
                    with ecol2:
                        e_vehicle = st.selectbox(
                            "Όχημα",
                            VEHICLE_OPTIONS,
                            index=VEHICLE_OPTIONS.index(row["plate"]) if row.get("plate") in VEHICLE_OPTIONS else 0,
                            key=f"veh_{selected_id}",
                        )

                    ecol3, ecol4 = st.columns(2)
                    with ecol3:
                        e_start_km = st.number_input(
                            "Χιλιομετρική ένδειξη ΕΝΑΡΞΗΣ",
                            min_value=0.0,
                            step=1.0,
                            format="%.0f",
                            value=float(row.get("start_km") or 0),
                            key=f"start_{selected_id}",
                        )
                    with ecol4:
                        e_end_km = st.number_input(
                            "Χιλιομετρική ένδειξη ΛΗΞΗΣ",
                            min_value=0.0,
                            step=1.0,
                            format="%.0f",
                            value=float(row.get("end_km") or 0),
                            key=f"end_{selected_id}",
                        )

                    if e_end_km > 0 and e_end_km >= e_start_km:
                        e_total_km = e_end_km - e_start_km
                    else:
                        e_total_km = 0

                    st.number_input(
                        "Συνολικά διανυθέντα χιλιόμετρα (υπολογίζονται αυτόματα)",
                        value=float(e_total_km),
                        disabled=True,
                        key=f"total_{selected_id}",
                    )

                    e_driver = st.selectbox(
                        "Ονοματεπώνυμο οδηγού",
                        DRIVER_OPTIONS,
                        index=DRIVER_OPTIONS.index(row["driver"]) if row.get("driver") in DRIVER_OPTIONS else 0,
                        key=f"driver_{selected_id}",
                    )

                    st.markdown("---")
                    st.subheader("🥛 Συλλογή Γάλακτος")

                    em1, em2 = st.columns(2)
                    with em1:
                        e_sheep_conv_kg = st.number_input(
                            "Πρόβειο Συμβατικό Γάλα (κιλά)",
                            min_value=0.0,
                            step=1.0,
                            format="%.2f",
                            value=float(row.get("sheep_conv_kg") or 0),
                            key=f"sheep_conv_{selected_id}",
                        )
                    with em2:
                        e_goat_conv_kg = st.number_input(
                            "Γίδινο Συμβατικό Γάλα (κιλά)",
                            min_value=0.0,
                            step=1.0,
                            format="%.2f",
                            value=float(row.get("goat_conv_kg") or 0),
                            key=f"goat_conv_{selected_id}",
                        )

                    e_total_conv_kg_scale = st.number_input(
                        "Σύνολο Συμβατικό Γάλα (Ζυγολόγιο)",
                        min_value=0.0,
                        step=1.0,
                        format="%.2f",
                        value=float(row.get("total_conv_kg_scale") or 0),
                        key=f"total_conv_scale_{selected_id}",
                    )

                    e_conv_da_refs = st.text_area(
                        "Σχετικά Δελτία Αποστολής (Συμβατικό)",
                        value=row.get("conv_da_refs", "") or "",
                        key=f"conv_da_refs_{selected_id}",
                    )

                    em3, em4 = st.columns(2)
                    with em3:
                        e_sheep_bio_kg = st.number_input(
                            "Πρόβειο Βιολογικό Γάλα (κιλά)",
                            min_value=0.0,
                            step=1.0,
                            format="%.2f",
                            value=float(row.get("sheep_bio_kg") or 0),
                            key=f"sheep_bio_{selected_id}",
                        )
                    with em4:
                        e_goat_bio_kg = st.number_input(
                            "Γίδινο Βιολογικό Γάλα (κιλά)",
                            min_value=0.0,
                            step=1.0,
                            format="%.2f",
                            value=float(row.get("goat_bio_kg") or 0),
                            key=f"goat_bio_{selected_id}",
                        )

                    e_bio_da_refs = st.text_area(
                        "Σχετικά Δελτία Αποστολής (Βιολογικό)",
                        value=row.get("bio_da_refs", "") or "",
                        key=f"bio_da_refs_{selected_id}",
                    )

                    e_total_all_da = st.number_input(
                        "Σύνολο Συμβατικό + Βιολογικό (ΔΑ)",
                        min_value=0.0,
                        step=1.0,
                        format="%.2f",
                        value=float(row.get("total_all_da") or 0),
                        key=f"total_all_da_{selected_id}",
                    )

                    e_total_all_scale = st.number_input(
                        "Σύνολο Συμβατικό + Βιολογικό (Ζυγολόγιο)",
                        min_value=0.0,
                        step=1.0,
                        format="%.2f",
                        value=float(row.get("total_all_scale") or 0),
                        key=f"total_all_scale_{selected_id}",
                    )

                    e_diff_da_vs_scale = e_total_all_da - e_total_all_scale

                    st.number_input(
                        "Διαφορά (ΔΑ - Ζυγολόγιο)",
                        value=float(e_diff_da_vs_scale),
                        disabled=True,
                        key=f"diff_{selected_id}",
                    )

                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        save_changes = st.form_submit_button("💾 Αποθήκευση αλλαγών")
                    with col_btn2:
                        close_trip = st.form_submit_button("✅ Λήξη & Κλείδωμα")

                    def validate_km():
                        if e_end_km > 0 and e_end_km < e_start_km:
                            st.error("Η χιλιομετρική ένδειξη λήξης δεν μπορεί να είναι μικρότερη από την έναρξη.")
                            return False
                        return True

                    if save_changes:
                        if validate_km():
                            try:
                                update_record(
                                    record_id=selected_id,
                                    route=e_route,
                                    vehicle=e_vehicle,
                                    start_km=e_start_km,
                                    end_km=e_end_km if e_end_km > 0 else None,
                                    total_km=e_total_km if e_end_km > 0 else None,
                                    driver=e_driver,
                                    sheep_conv_kg=e_sheep_conv_kg,
                                    goat_conv_kg=e_goat_conv_kg,
                                    total_conv_kg_scale=e_total_conv_kg_scale,
                                    conv_da_refs=e_conv_da_refs,
                                    sheep_bio_kg=e_sheep_bio_kg,
                                    goat_bio_kg=e_goat_bio_kg,
                                    bio_da_refs=e_bio_da_refs,
                                    total_all_da=e_total_all_da,
                                    total_all_scale=e_total_all_scale,
                                    diff_da_vs_scale=e_diff_da_vs_scale,
                                )
                                st.success("Οι αλλαγές αποθηκεύτηκαν ✅")
                                st.experimental_rerun()
                            except Exception as e:
                                st.error("Σφάλμα κατά την ενημέρωση του δρομολογίου.")
                                st.exception(e)

                    if close_trip:
                        if validate_km():
                            try:
                                # Πρώτα σώζουμε τις τελευταίες τιμές
                                update_record(
                                    record_id=selected_id,
                                    route=e_route,
                                    vehicle=e_vehicle,
                                    start_km=e_start_km,
                                    end_km=e_end_km if e_end_km > 0 else None,
                                    total_km=e_total_km if e_end_km > 0 else None,
                                    driver=e_driver,
                                    sheep_conv_kg=e_sheep_conv_kg,
                                    goat_conv_kg=e_goat_conv_kg,
                                    total_conv_kg_scale=e_total_conv_kg_scale,
                                    conv_da_refs=e_conv_da_refs,
                                    sheep_bio_kg=e_sheep_bio_kg,
                                    goat_bio_kg=e_goat_bio_kg,
                                    bio_da_refs=e_bio_da_refs,
                                    total_all_da=e_total_all_da,
                                    total_all_scale=e_total_all_scale,
                                    diff_da_vs_scale=e_diff_da_vs_scale,
                                )
                                # Μετά κλειδώνουμε (βάζει και ώρα λήξης)
                                close_record(selected_id)
                                st.success("Το δρομολόγιο έκλεισε & κλειδώθηκε ✅")
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

        if "started_at" in df.columns:
            df["started_at_dt"] = pd.to_datetime(df["started_at"], errors="coerce")
        else:
            df["started_at_dt"] = pd.NaT

        if "closed_at" in df.columns:
            df["closed_at_dt"] = pd.to_datetime(df["closed_at"], errors="coerce")
        else:
            df["closed_at_dt"] = pd.NaT

        if "is_closed" in df.columns:
            df["status"] = df["is_closed"].apply(lambda x: "Κλειστό" if x else "Ανοιχτό")

        min_date = df["dt"].min()
        max_date = df["dt"].max()

        st.markdown("### 🔍 Φίλτρα")

        colf1, colf2, colf3 = st.columns(3)

        with colf1:
            plate_filter = st.multiselect(
                "Φίλτρο οχήματος",
                options=sorted(df["plate"].dropna().unique()),
                key="plate_filter_all",
            )

        with colf2:
            driver_filter = st.multiselect(
                "Φίλτρο οδηγού",
                options=sorted(df["driver"].dropna().unique()),
                key="driver_filter_all",
            )

        with colf3:
            date_range = st.date_input(
                "Ημερομηνία από / έως",
                value=(min_date, max_date),
                key="date_range_all",
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
        show_cols = [
            "id", "dt", "started_at_dt", "closed_at_dt",
            "route", "plate", "start_km", "end_km", "total_km",
            "driver",
            "sheep_conv_kg", "goat_conv_kg", "total_conv_kg_scale",
            "conv_da_refs",
            "sheep_bio_kg", "goat_bio_kg", "bio_da_refs",
            "total_all_da", "total_all_scale", "diff_da_vs_scale",
            "status",
        ]
        show_cols = [c for c in show_cols if c in filtered_df.columns]
        st.dataframe(filtered_df[show_cols], use_container_width=True)

        # Export σε Excel – όλα ως string για να μη σκάει
        if not filtered_df.empty:
            df_export = filtered_df.copy()
            df_export = df_export.astype(str)

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Routes")
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
                    start_str = ""
                    if pd.notna(row.get("started_at_dt")):
                        start_str = row["started_at_dt"].strftime("%d/%m %H:%M")
                    st.write(
                        f"ID: {row['id']} – {row['plate']} – {row.get('driver', '')} – {start_str}"
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
