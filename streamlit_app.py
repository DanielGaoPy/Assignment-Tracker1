import streamlit as st
import sqlite3
from datetime import date

# ------------------------------------------------------------------------------
# ▶ Database setup (runs once)
# ------------------------------------------------------------------------------
conn = sqlite3.connect('assignments.db', check_same_thread=False)
c = conn.cursor()
c.execute("""
    CREATE TABLE IF NOT EXISTS assignments (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        course      TEXT NOT NULL,
        assignment  TEXT NOT NULL,
        due_date    TEXT NOT NULL
    )
""")
conn.commit()

# ------------------------------------------------------------------------------
# ▶ Page layout
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Assignment Tracker", layout="wide")
st.title("🗓️ Assignment Tracker")

# ------------------------------------------------------------------------------
# ▶ Add new assignment
# ------------------------------------------------------------------------------
with st.form("add_form", clear_on_submit=True):
    st.subheader("Add a New Assignment")
    course       = st.text_input("Course Name")
    assignment   = st.text_input("Assignment Title")
    due_date     = st.date_input("Due Date", value=date.today())
    submitted    = st.form_submit_button("➕ Add Assignment")
    if submitted:
        if course and assignment:
            c.execute(
                "INSERT INTO assignments (course, assignment, due_date) VALUES (?, ?, ?)",
                (course, assignment, due_date.isoformat())
            )
            conn.commit()
            st.success(f"Added **{assignment}** for **{course}**, due {due_date}")
        else:
            st.error("Please fill in both Course and Assignment fields.")

st.markdown("---")

# ------------------------------------------------------------------------------
# ▶ List & delete assignments
# ------------------------------------------------------------------------------
st.subheader("Your Assignments")
rows = c.execute(
    "SELECT id, course, assignment, due_date FROM assignments ORDER BY due_date"
).fetchall()

if not rows:
    st.info("No assignments logged yet.")
else:
    for id, course, assignment, due in rows:
        cols = st.columns([3, 5, 3, 1])
        cols[0].write(f"**{course}**")
        cols[1].write(assignment)
        cols[2].write(f"Due: {due}")
        if cols[3].button("🗑️", key=f"del_{id}"):
            c.execute("DELETE FROM assignments WHERE id = ?", (id,))
            conn.commit()
            st.experimental_rerun()
