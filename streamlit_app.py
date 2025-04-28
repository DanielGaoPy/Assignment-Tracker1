import streamlit as st
import sqlite3
import random
from datetime import date, datetime, time as dtime

# ------------------------------------------------------------------------------
# ▶ Custom CSS for plant-based theme
# ------------------------------------------------------------------------------
st.markdown("""
<style>
.stApp { background-color: #F0FBF3; }
.stButton>button {
    background-color: #A8D5BA;
    color: #1B4332;
    border: none;
    border-radius: 10px;
    padding: 5px 10px;
}
.stMetric {
    background-color: #D8F3DC;
    border-radius: 10px;
    padding: 5px 10px;
    color: #1B4332;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# ▶ Database setup & migration (runs once)
# ------------------------------------------------------------------------------
conn = sqlite3.connect('assignments.db', check_same_thread=False)
c = conn.cursor()

# Migration: Add columns if they don't exist
for column, props in [
    ("type",     "TEXT NOT NULL DEFAULT 'Assignment'"),
    ("due_time", "TEXT NOT NULL DEFAULT '00:00:00'"),
    ("completed","INTEGER NOT NULL DEFAULT 0")
]:
    try:
        c.execute(f"ALTER TABLE assignments ADD COLUMN {column} {props}")
    except sqlite3.OperationalError:
        pass

# Create main assignments table if not exists
c.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        course       TEXT    NOT NULL,
        assignment   TEXT    NOT NULL,
        type         TEXT    NOT NULL,
        due_date     TEXT    NOT NULL,
        due_time     TEXT    NOT NULL DEFAULT '00:00:00',
        completed    INTEGER NOT NULL DEFAULT 0
    )
""")
# Create plants table for awarded plants
table_sql = """
    CREATE TABLE IF NOT EXISTS plants (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        image_url   TEXT    NOT NULL,
        awarded_at  TEXT    NOT NULL
    )
"""
c.execute(table_sql)
conn.commit()

# Hardcoded catalog of real-life plant breeds
PLANT_CATALOG = [
    {"name": "Monstera deliciosa", "image": "https://images.unsplash.com/photo-1579370318442-73a6ff72b0a0?auto=format&fit=crop&w=400&q=80"},
    {"name": "Ficus lyrata (Fiddle Leaf Fig)", "image": "https://images.unsplash.com/photo-1534081333815-ae5019106622?auto=format&fit=crop&w=400&q=80"},
    {"name": "Epipremnum aureum (Golden Pothos)", "image": "https://images.unsplash.com/photo-1556912167-f556f1f39d6b?auto=format&fit=crop&w=400&q=80"},
    {"name": "Sansevieria trifasciata (Snake Plant)", "image": "https://images.unsplash.com/photo-1590254074496-c36d4871eaf5?auto=format&fit=crop&w=400&q=80"},
    {"name": "Dracaena marginata (Dragon Tree)", "image": "https://images.unsplash.com/photo-1600607689867-020a729b3d4d?auto=format&fit=crop&w=400&q=80"},
    {"name": "Zamioculcas zamiifolia (ZZ Plant)", "image": "https://images.unsplash.com/photo-1592423492834-77e6ec2ffc3e?auto=format&fit=crop&w=400&q=80"},
    {"name": "Spathiphyllum (Peace Lily)", "image": "https://images.unsplash.com/photo-1602524815465-f2b36bb874f9?auto=format&fit=crop&w=400&q=80"},
    {"name": "Haworthia attenuata (Zebra Haworthia)", "image": "https://images.unsplash.com/photo-1560844517-08c756ab6b27?auto=format&fit=crop&w=400&q=80"},
    {"name": "Aloe vera", "image": "https://images.unsplash.com/photo-1542219550-2ab3012dff5e?auto=format&fit=crop&w=400&q=80"},
    {"name": "Philodendron hederaceum (Heartleaf Philodendron)", "image": "https://images.unsplash.com/photo-1556886564-6a2053850d29?auto=format&fit=crop&w=400&q=80"},
    {"name": "Boston Fern", "image": "https://images.unsplash.com/photo-1501004318641-b39e6451bec6?auto=format&fit=crop&w=400&q=80"},
    {"name": "String of Pearls", "image": "https://images.unsplash.com/photo-1542831371-29b0f74f9713?auto=format&fit=crop&w=400&q=80"},
    {"name": "Rubber Plant", "image": "https://images.unsplash.com/photo-1587285133999-32d66b2655de?auto=format&fit=crop&w=400&q=80"},
    {"name": "Spider Plant", "image": "https://images.unsplash.com/photo-1493927732325-8a15479f4d49?auto=format&fit=crop&w=400&q=80"},
]

# Function to award a random plant upon completion
def award_plant():
    existing = [row[0] for row in c.execute("SELECT name FROM plants").fetchall()]
    available = [p for p in PLANT_CATALOG if p["name"] not in existing]
    if not available:
        st.info("You've collected all available plants! 🌱")
        return
    chosen = random.choice(available)
    c.execute(
        "INSERT INTO plants (name, image_url, awarded_at) VALUES (?, ?, ?)",
        (chosen["name"], chosen["image"], datetime.now().isoformat())
    )
    conn.commit()
    st.balloons()
    st.success(f"You earned a new plant: {chosen['name']} 🌿")

# ------------------------------------------------------------------------------
# ▶ Page layout & main tabs
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Assignment Tracker", page_icon="🌿", layout="wide")
st.title("🌱 Plant-Based Assignment Tracker 🌱")

tabs = st.tabs(["➕ Add", "⏳ Upcoming", "✅ Completed", "🌿 Garden"])

# ------------------------------------------------------------------------------
# ▶ Tab 1: Add Assignment
# ------------------------------------------------------------------------------
with tabs[0]:
    with st.form("add_form", clear_on_submit=True):
        st.subheader("➕ Add a New Assignment")
        course     = st.text_input("Course Name")
        assignment = st.text_input("Assignment Title")
        a_type     = st.selectbox("Assignment Type", ["Quiz", "Mid-Term", "Final", "Test", "Project", "Paper"], index=0)
        due_date   = st.date_input("Due Date", value=date.today())
        due_time   = st.time_input("Due Time", value=dtime(hour=23, minute=59))
        if st.form_submit_button("Add Assignment"):
            if course and assignment:
                c.execute(
                    "INSERT INTO assignments (course, assignment, type, due_date, due_time) VALUES (?, ?, ?, ?, ?)",
                    (course, assignment, a_type, due_date.isoformat(), due_time.isoformat())
                )
                conn.commit()
                st.success(f"Added **{assignment}** ({a_type}) for **{course}**, due {due_date} at {due_time}")
            else:
                st.error("Please fill in Course Name and Assignment Title.")

# ------------------------------------------------------------------------------
# ▶ Helper: load assignments
# ------------------------------------------------------------------------------
def load_assignments(flag):
    return c.execute(
        "SELECT id, course, assignment, type, due_date, due_time FROM assignments WHERE completed = ? ORDER BY due_date, due_time",
        (flag,)
    ).fetchall()

# ------------------------------------------------------------------------------
# ▶ Tab 2: Upcoming Assignments
# ------------------------------------------------------------------------------
with tabs[1]:
    st.subheader("⏳ Upcoming Assignments")
    upcoming = load_assignments(0)
    if not upcoming:
        st.info("No upcoming assignments! 🎉")
    else:
        for id, course, assignment, a_type, due_date, due_time in upcoming:
            due_dt = datetime.fromisoformat(f"{due_date}T{due_time}")
            now = datetime.now()
            delta = due_dt - now
            weeks   = delta.days // 7
            days    = delta.days % 7
            hours   = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60

            with st.container():
                cols = st.columns([2, 4, 2, 2, 1, 1])
                cols[0].markdown(f"**{course}**")
                cols[1].markdown(f"**{assignment}** ({a_type})")
                cols[2].markdown(f"Due: {due_dt.strftime('%Y-%m-%d %H:%M')}")
                cols[3].metric("Time Remaining", f"{weeks}w {days}d {hours}h {minutes}m")
                if cols[4].button("✅ Done", key=f"done_{id}"):
                    c.execute("UPDATE assignments SET completed = 1 WHERE id = ?", (id,))
                    conn.commit()
                    award_plant()
                    st.experimental_rerun()
                if cols[5].button("❌", key=f"del_up_{id}"):
                    c.execute("DELETE FROM assignments WHERE id = ?", (id,))
                    conn.commit()
                    st.experimental_rerun()
            st.divider()

# ------------------------------------------------------------------------------
# ▶ Tab 3: Completed Assignments
# ------------------------------------------------------------------------------
with tabs[2]:
    st.subheader("✅ Completed Assignments")
    completed = load_assignments(1)
    if not completed:
        st.info("No assignments marked as completed.")
    else:
        for id, course, assignment, a_type, due_date, due_time in completed:
            with st.container():
                cols = st.columns([2, 4, 2, 1])
                cols[0].markdown(f"~~{course}~~")
                cols[1].markdown(f"~~{assignment}~~ ({a_type})")
                cols[2].markdown(f"Due: {due_date} {due_time}")
                if cols[3].button("🗑️", key=f"del_comp_{id}"):
                    c.execute("DELETE FROM assignments WHERE id = ?", (id,))
                    conn.commit()
                    st.experimental_rerun()
            st.divider()

# ------------------------------------------------------------------------------
# ▶ Tab 4: Garden (Your Plants)
# ------------------------------------------------------------------------------
with tabs[3]:
    st.subheader("🌿 Your Plant Collection")
    plants = c.execute("SELECT name, image_url FROM plants").fetchall()
    if not plants:
        st.info("Complete assignments to earn plants!")
    else:
        cols = st.columns(3)
        for idx, (name, img) in enumerate(plants):
            col = cols[idx % 3]
            col.image(img, use_column_width=True, caption=name)

# ------------------------------------------------------------------------------
# ▶ Footer
# ------------------------------------------------------------------------------
st.markdown("---")
st.caption("Built with 🌱 by Streamlit")
