import streamlit as st
import sqlite3
import random
from datetime import date, datetime, time as dtime

# ------------------------------------------------------------------------------
# ▶ Page configuration
# ------------------------------------------------------------------------------
st.set_page_config(
    page_title="Plant-Based Assignment Tracker",
    page_icon="🌿",
    layout="wide"
)

# ------------------------------------------------------------------------------
# ▶ Custom CSS: forest green background and white accents
# ------------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* App background and text */
        [data-testid="stAppViewContainer"] {
            background-color: #228B22 !important;
            color: #FFFFFF;
        }
        /* Title */
        h1 {
            color: #FFFFFF;
            font-size: 80px;
            text-align: center;
            margin-bottom: 20px;
        }
        /* Card styling with white border */
        .card {
            background-color: #FFFFFF;
            color: #1B4332;
            border: 2px solid #FFFFFF;
            border-radius: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            padding: 16px;
            margin-bottom: 16px;
        }
        /* Buttons with white accent border */
        button {
            border: 2px solid #FFFFFF !important;
            border-radius: 8px !important;
        }
        /* Horizontal rules (---) as white lines */
        hr {
            border-top: 2px solid #FFFFFF !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------------------
# ▶ Database setup & migration
# ------------------------------------------------------------------------------
conn = sqlite3.connect('assignments.db', check_same_thread=False)
c = conn.cursor()
for col, props in [
    ('type',      "TEXT NOT NULL DEFAULT 'Assignment'"),
    ('due_time',  "TEXT NOT NULL DEFAULT '23:59:00'"),
    ('completed', "INTEGER NOT NULL DEFAULT 0")
]:
    try:
        c.execute(f"ALTER TABLE assignments ADD COLUMN {col} {props}")
    except sqlite3.OperationalError:
        pass
c.execute(
    """
    CREATE TABLE IF NOT EXISTS assignments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        course      TEXT    NOT NULL,
        assignment  TEXT    NOT NULL,
        type        TEXT    NOT NULL,
        due_date    TEXT    NOT NULL,
        due_time    TEXT    NOT NULL,
        completed   INTEGER NOT NULL DEFAULT 0
    )
    """
)
c.execute(
    """
    CREATE TABLE IF NOT EXISTS plants (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        awarded_at  TEXT    NOT NULL
    )
    """
)
conn.commit()

# ------------------------------------------------------------------------------
# ▶ Plant breeds and corresponding emojis
# ------------------------------------------------------------------------------
PLANT_BREEDS = [
    "Monstera deliciosa",
    "Ficus lyrata",
    "Golden Pothos",
    "Snake Plant",
    "Dragon Tree",
    "ZZ Plant",
    "Peace Lily",
    "Red Apple",
    "Green Apple",
    "Rose",
    "Tulip",
    "Sunflower",
    "Daisy",
    "Cherry Blossom",
    "Banana",
    "Grapes",
    "Strawberry",
    "Cactus",
    "Four Leaf Clover",
    "Herb",
    "Maple Leaf"
]
EMOJIS = [
    "🌱","🌿","🍃","🌱","🌴","🌿","🌼",
    "🍎","🍏","🌹","🌷","🌻","🌼","🌸",
    "🍌","🍇","🍓","🌵","🍀","🌾","🍁"
]
EMOJI_MAP = {PLANT_BREEDS[i]: EMOJIS[i] for i in range(len(PLANT_BREEDS))}

# ------------------------------------------------------------------------------
# ▶ Award a new plant for every 5 completed assignments
# ------------------------------------------------------------------------------
def award_plant():
    # count completed assignments
    total_completed = c.execute("SELECT COUNT(*) FROM assignments WHERE completed=1").fetchone()[0]
    # determine how many awards
    awards = total_completed // 5
    owned = [row[0] for row in c.execute("SELECT name FROM plants").fetchall()]
    while len(owned) < awards:
        choices = [b for b in PLANT_BREEDS if b not in owned]
        if not choices:
            break
        breed = random.choice(choices)
        c.execute("INSERT INTO plants (name, awarded_at) VALUES (?,?)", (breed, datetime.now().isoformat()))
        conn.commit()
        owned.append(breed)
        st.balloons()
        st.success(f"Unlocked: {EMOJI_MAP[breed]} {breed}")

# ------------------------------------------------------------------------------
# ▶ Load assignments helper
# ------------------------------------------------------------------------------
def load_assignments(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed=? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# ------------------------------------------------------------------------------
# ▶ App header and navigation tabs
# ------------------------------------------------------------------------------
st.markdown('<h1>🌱 Plant-Based Assignment Tracker 🌱</h1>', unsafe_allow_html=True)
tabs = st.tabs(["Add","Upcoming","Completed","Plant Catalog","Collected Plants"])

# Add tab
with tabs[0]:
    st.subheader("➕ Add a New Assignment")
    with st.form("add_form", clear_on_submit=True):
        course = st.text_input("Course Name")
        assignment = st.text_input("Assignment Title")
        a_type = st.selectbox("Assignment Type", ["Quiz","Mid-Term","Final","Test","Project","Paper"])
        due_date = st.date_input("Due Date", value=date.today())
        due_time = st.time_input("Due Time", value=dtime(23,59))
        if st.form_submit_button("Add Assignment"):
            if course and assignment:
                c.execute(
                    "INSERT INTO assignments (course,assignment,type,due_date,due_time,completed) VALUES (?,?,?,?,?,0)",
                    (course, assignment, a_type, due_date.isoformat(), due_time.isoformat())
                )
                conn.commit()
                st.success("Assignment added!")
            else:
                st.error("Please fill in both Course Name and Assignment Title.")

# Upcoming tab
with tabs[1]:
    st.subheader("⏳ Upcoming Assignments")
    rows = load_assignments(0)
    if not rows:
        st.info("No upcoming assignments!")
    else:
        for id_, course, assign, a_type, d_date, d_time in rows:
            dt = datetime.fromisoformat(f"{d_date}T{d_time}")
            diff = dt - datetime.now()
            parts = []
            if diff.days // 7: parts.append(f"{diff.days//7}w")
            if diff.days % 7: parts.append(f"{diff.days%7}d")
            h = diff.seconds // 3600
            if h: parts.append(f"{h}h")
            m = (diff.seconds % 3600) // 60
            if m: parts.append(f"{m}m")
            rem = " ".join(parts) if parts else "Now"
            st.markdown(f"**{course} - {assign} ({a_type})**  ")
            st.markdown(f"Due: {dt.strftime('%Y-%m-%d %H:%M')} | Remaining: {rem}")
            c1, c2 = st.columns([5,1])
            if c1.button("✅ Done", key=f"done_{id_}"):
                c.execute("UPDATE assignments SET completed=1 WHERE id=?", (id_,))
                conn.commit()
                award_plant()
                st.experimental_rerun()
            if c2.button("❌", key=f"del_{id_}"):
                c.execute("DELETE FROM assignments WHERE id=?", (id_,))
                conn.commit()
                st.experimental_rerun()
            st.markdown("---")

# Completed tab
with tabs[2]:
    st.subheader("✅ Completed Assignments")
    rows = load_assignments(1)
    if not rows:
        st.info("No completed assignments.")
    else:
        for id_, course, assign, a_type, d_date, d_time in rows:
            st.markdown(f"~~{course} - {assign}~~ ({a_type})   Completed: {d_date} {d_time}")
            if st.button("🗑️ Remove", key=f"rem_{id_}"):
                c.execute("DELETE FROM assignments WHERE id=?", (id_,))
                conn.commit()
                st.experimental_rerun()

# Plant Catalog tab: list breeds with emojis
with tabs[3]:
    st.subheader("🌿 Plant Catalog")
    for breed in PLANT_BREEDS:
        st.markdown(f"{EMOJI_MAP[breed]} {breed}")

# Collected Plants tab: list earned emojis and names
with tabs[4]:
    st.subheader("🌳 Collected Plants")
    earned = [r[0] for r in c.execute("SELECT name FROM plants").fetchall()]
    if not earned:
        st.info("Complete assignments to earn plants!")
    else:
        for name in earned:
            st.markdown(f"### {EMOJI_MAP.get(name,'🌱')} {name}")

# Footer
st.markdown("---")
st.caption("Made with ❤️ and plants 🌿")
